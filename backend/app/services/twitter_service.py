import requests
from requests_oauthlib import OAuth1
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.models import Tweet, Reply, ActivityLog
import asyncio
import json


class TwitterService:
    def __init__(self):
        self._oauth = None

    @property
    def oauth(self) -> OAuth1:
        """OAuth1 auth for direct API calls (write operations)."""
        if self._oauth is None:
            self._oauth = OAuth1(
                settings.twitter_api_key,
                settings.twitter_api_secret,
                settings.twitter_access_token,
                settings.twitter_access_token_secret,
            )
        return self._oauth

    def _get_headers(self) -> dict:
        """Standard headers to avoid cloud IP blocks."""
        return {
            "Content-Type": "application/json",
            "User-Agent": "AiScientistBot/1.0",
            "Accept": "application/json",
        }

    def _post_tweet_api(self, text: str, reply_to_id: Optional[str] = None) -> dict:
        """Post tweet via Twitter v2 API with multiple endpoint fallbacks."""
        import time

        payload = {"text": text}
        if reply_to_id:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to_id}

        endpoints = [
            "https://api.twitter.com/2/tweets",
            "https://api.x.com/2/tweets",
        ]

        last_error = ""
        for endpoint in endpoints:
            # OAuth must be re-generated per endpoint (signature includes URL)
            for attempt in range(2):
                try:
                    resp = requests.post(
                        endpoint,
                        json=payload,
                        auth=self.oauth,
                        headers=self._get_headers(),
                        timeout=30,
                    )

                    if resp.status_code in (200, 201):
                        data = resp.json()
                        return {"success": True, "tweet_id": data["data"]["id"]}
                    elif resp.status_code == 429:
                        time.sleep(10)
                        continue
                    elif resp.status_code == 503:
                        last_error = f"{endpoint}: 503 Service Unavailable"
                        print(f"[TwitterBot] {last_error} (attempt {attempt+1})")
                        time.sleep(3)
                        continue
                    else:
                        last_error = f"{endpoint}: {resp.status_code}: {resp.text[:200]}"
                        break  # Non-retryable error, try next endpoint
                except requests.exceptions.RequestException as e:
                    last_error = f"{endpoint}: {str(e)}"
                    time.sleep(2)

        return {"success": False, "error": last_error}

    async def post_tweet(self, content: str, db: AsyncSession, tweet_db_id: Optional[int] = None) -> dict:
        """Post a tweet to Twitter."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: self._post_tweet_api(content)
            )

            if result["success"]:
                tweet_id = result["tweet_id"]

                if tweet_db_id:
                    db_result = await db.execute(select(Tweet).where(Tweet.id == tweet_db_id))
                    tweet = db_result.scalar_one_or_none()
                    if tweet:
                        tweet.tweet_id = tweet_id
                        tweet.status = "posted"
                        tweet.posted_at = datetime.utcnow()

                log = ActivityLog(
                    action="tweet_posted",
                    details=f"Posted tweet: {content[:100]}... (ID: {tweet_id})",
                    status="success",
                )
                db.add(log)
                await db.commit()
                return {"success": True, "tweet_id": tweet_id}
            else:
                raise Exception(result["error"])

        except Exception as e:
            if tweet_db_id:
                db_result = await db.execute(select(Tweet).where(Tweet.id == tweet_db_id))
                tweet = db_result.scalar_one_or_none()
                if tweet:
                    tweet.status = "failed"

            log = ActivityLog(
                action="tweet_failed",
                details=f"Failed to post tweet: {str(e)}",
                status="error",
            )
            db.add(log)
            await db.commit()

            return {"success": False, "error": str(e)}

    async def post_reply(self, content: str, in_reply_to_id: str, db: AsyncSession, reply_db_id: Optional[int] = None) -> dict:
        """Post a reply to a tweet."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: self._post_tweet_api(content, reply_to_id=in_reply_to_id)
            )

            if result["success"]:
                reply_id = result["tweet_id"]

                if reply_db_id:
                    db_result = await db.execute(select(Reply).where(Reply.id == reply_db_id))
                    reply = db_result.scalar_one_or_none()
                    if reply:
                        reply.reply_id = reply_id
                        reply.status = "replied"
                        reply.replied_at = datetime.utcnow()

                log = ActivityLog(
                    action="reply_posted",
                    details=f"Posted reply: {content[:100]}... (Reply to: {in_reply_to_id})",
                    status="success",
                )
                db.add(log)
                await db.commit()
                return {"success": True, "reply_id": reply_id}
            else:
                raise Exception(result["error"])

        except Exception as e:
            if reply_db_id:
                db_result = await db.execute(select(Reply).where(Reply.id == reply_db_id))
                reply = db_result.scalar_one_or_none()
                if reply:
                    reply.status = "failed"

            log = ActivityLog(
                action="reply_failed",
                details=f"Failed to post reply: {str(e)}",
                status="error",
            )
            db.add(log)
            await db.commit()

            return {"success": False, "error": str(e)}

    def _get_tweet_metrics_api(self, tweet_id: str) -> dict:
        """Get tweet metrics via direct v2 API with OAuth1."""
        try:
            resp = requests.get(
                f"https://api.twitter.com/2/tweets/{tweet_id}",
                params={"tweet.fields": "public_metrics,created_at"},
                auth=self.oauth,
                headers=self._get_headers(),
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                metrics = data.get("public_metrics", {})
                return {
                    "likes": metrics.get("like_count", 0),
                    "retweets": metrics.get("retweet_count", 0),
                    "replies": metrics.get("reply_count", 0),
                    "impressions": metrics.get("impression_count", 0),
                    "bookmarks": metrics.get("bookmark_count", 0),
                }
            return {}
        except Exception:
            return {}

    async def get_tweet_metrics(self, tweet_id: str) -> dict:
        """Get engagement metrics for a tweet."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._get_tweet_metrics_api(tweet_id)
        )

    def _get_user_id_api(self) -> Optional[str]:
        """Get authenticated user's ID via direct API."""
        try:
            resp = requests.get(
                "https://api.twitter.com/2/users/me",
                auth=self.oauth,
                headers=self._get_headers(),
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json().get("data", {}).get("id")
            return None
        except Exception:
            return None

    def _get_mentions_api(self, since_id: Optional[str] = None) -> List[Dict]:
        """Get mentions via direct v2 API with OAuth1."""
        try:
            user_id = self._get_user_id_api()
            if not user_id:
                print("[TwitterBot] Could not get user ID for mentions")
                return []

            params = {
                "tweet.fields": "created_at,in_reply_to_user_id,referenced_tweets,author_id",
                "user.fields": "username",
                "expansions": "author_id,referenced_tweets.id",
                "max_results": 50,
            }
            if since_id:
                params["since_id"] = since_id

            resp = requests.get(
                f"https://api.twitter.com/2/users/{user_id}/mentions",
                params=params,
                auth=self.oauth,
                headers=self._get_headers(),
                timeout=15,
            )

            if resp.status_code != 200:
                print(f"[TwitterBot] Mentions API returned {resp.status_code}: {resp.text[:200]}")
                return []

            data = resp.json()
            tweets = data.get("data", [])
            includes = data.get("includes", {})
            users_list = includes.get("users", [])
            users = {u["id"]: u for u in users_list}

            mentions = []
            for tweet in tweets:
                author = users.get(tweet.get("author_id"))
                parent_tweet_id = None
                for ref in tweet.get("referenced_tweets", []):
                    if ref.get("type") == "replied_to":
                        parent_tweet_id = str(ref["id"])
                        break

                mentions.append({
                    "id": str(tweet["id"]),
                    "text": tweet.get("text", ""),
                    "author_id": str(tweet.get("author_id", "")),
                    "author_username": author.get("username", "unknown") if author else "unknown",
                    "parent_tweet_id": parent_tweet_id,
                    "created_at": tweet.get("created_at"),
                })

            return mentions
        except Exception as e:
            print(f"[TwitterBot] Error getting mentions: {e}")
            return []

    async def get_mentions(self, since_id: Optional[str] = None) -> List[Dict]:
        """Get recent mentions/replies to our tweets."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._get_mentions_api(since_id)
        )

    def _like_tweet_api(self, tweet_id: str) -> dict:
        """Like a tweet via Twitter v2 API."""
        try:
            user_id = self._get_user_id_api()
            if not user_id:
                return {"success": False, "error": "Could not get user ID"}

            resp = requests.post(
                f"https://api.twitter.com/2/users/{user_id}/likes",
                json={"tweet_id": tweet_id},
                auth=self.oauth,
                headers=self._get_headers(),
                timeout=15,
            )
            if resp.status_code in (200, 201):
                return {"success": True}
            else:
                return {"success": False, "error": f"{resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def like_tweet(self, tweet_id: str) -> dict:
        """Like a tweet."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._like_tweet_api(tweet_id)
        )

    async def update_tweet_metrics(self, db: AsyncSession):
        """Update metrics for all posted tweets."""
        result = await db.execute(
            select(Tweet).where(Tweet.status == "posted", Tweet.tweet_id.isnot(None))
        )
        tweets = result.scalars().all()

        for tweet in tweets:
            metrics = await self.get_tweet_metrics(tweet.tweet_id)
            if metrics:
                tweet.likes = metrics.get("likes", tweet.likes)
                tweet.retweets = metrics.get("retweets", tweet.retweets)
                tweet.replies_count = metrics.get("replies", tweet.replies_count)
                tweet.impressions = metrics.get("impressions", tweet.impressions)
                tweet.bookmarks = metrics.get("bookmarks", tweet.bookmarks)

        await db.commit()

    async def test_connection(self) -> dict:
        """Test Twitter API connection."""
        try:
            loop = asyncio.get_event_loop()

            def _test():
                resp = requests.get(
                    "https://api.twitter.com/2/users/me",
                    auth=self.oauth,
                    headers=self._get_headers(),
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    return {
                        "success": True,
                        "username": data.get("username"),
                        "name": data.get("name"),
                        "id": data.get("id"),
                    }
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}

            return await loop.run_in_executor(None, _test)
        except Exception as e:
            return {"success": False, "error": str(e)}


twitter_service = TwitterService()
