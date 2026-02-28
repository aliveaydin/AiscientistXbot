import tweepy
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
        self._client = None
        self._oauth = None

    @property
    def client(self) -> tweepy.Client:
        """Twitter API v2 client (for read operations)."""
        if self._client is None:
            self._client = tweepy.Client(
                bearer_token=settings.twitter_bearer_token,
                consumer_key=settings.twitter_api_key,
                consumer_secret=settings.twitter_api_secret,
                access_token=settings.twitter_access_token,
                access_token_secret=settings.twitter_access_token_secret,
                wait_on_rate_limit=True,
            )
        return self._client

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

    def _post_tweet_v2(self, text: str, reply_to_id: Optional[str] = None) -> dict:
        """Post tweet using Twitter API v2."""
        payload = {"text": text}
        if reply_to_id:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to_id}

        resp = requests.post(
            "https://api.twitter.com/2/tweets",
            json=payload,
            auth=self.oauth,
            headers=self._get_headers(),
            timeout=30,
        )

        if resp.status_code in (200, 201):
            data = resp.json()
            return {"success": True, "tweet_id": data["data"]["id"]}
        else:
            return {"success": False, "error": f"v2: {resp.status_code}: {resp.text}"}

    def _post_tweet_v1(self, text: str, reply_to_id: Optional[str] = None) -> dict:
        """Post tweet using Twitter API v1.1 (fallback)."""
        params = {"status": text}
        if reply_to_id:
            params["in_reply_to_status_id"] = reply_to_id
            params["auto_populate_reply_metadata"] = "true"

        resp = requests.post(
            "https://api.twitter.com/1.1/statuses/update.json",
            data=params,
            auth=self.oauth,
            headers={
                "User-Agent": "AiScientistBot/1.0",
                "Accept": "application/json",
            },
            timeout=30,
        )

        if resp.status_code == 200:
            data = resp.json()
            return {"success": True, "tweet_id": str(data["id_str"])}
        else:
            return {"success": False, "error": f"v1.1: {resp.status_code}: {resp.text}"}

    def _post_tweet_bearer(self, text: str, reply_to_id: Optional[str] = None) -> dict:
        """Post tweet using OAuth2 Bearer Token + OAuth1 combo."""
        payload = {"text": text}
        if reply_to_id:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to_id}

        # Use OAuth1 but with explicit session to handle redirects
        session = requests.Session()
        session.auth = self.oauth
        session.headers.update(self._get_headers())

        resp = session.post(
            "https://api.x.com/2/tweets",  # Try x.com domain
            json=payload,
            timeout=30,
            allow_redirects=True,
        )

        if resp.status_code in (200, 201):
            data = resp.json()
            return {"success": True, "tweet_id": data["data"]["id"]}
        else:
            return {"success": False, "error": f"x.com: {resp.status_code}: {resp.text}"}

    def _post_tweet_api(self, text: str, reply_to_id: Optional[str] = None) -> dict:
        """Post tweet with automatic fallback between API versions."""
        import time

        # Try v2 API (api.twitter.com)
        result = self._post_tweet_v2(text, reply_to_id)
        if result["success"]:
            return result

        # If 503 on v2, try x.com domain
        if "503" in result.get("error", ""):
            print(f"[TwitterBot] v2 failed with 503, trying x.com domain...")
            time.sleep(1)
            result = self._post_tweet_bearer(text, reply_to_id)
            if result["success"]:
                return result

        # If still failing, try v1.1 API
        if not result["success"]:
            print(f"[TwitterBot] x.com failed, trying v1.1 API...")
            time.sleep(1)
            result_v1 = self._post_tweet_v1(text, reply_to_id)
            if result_v1["success"]:
                return result_v1
            # Return the most informative error
            return {"success": False, "error": f"{result['error']} | {result_v1['error']}"}

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

    async def get_tweet_metrics(self, tweet_id: str) -> dict:
        """Get engagement metrics for a tweet."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get_tweet(
                    tweet_id,
                    tweet_fields=["public_metrics", "created_at"],
                ),
            )

            if response.data:
                metrics = getattr(response.data, "public_metrics", {}) or {}
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

    async def get_mentions(self, since_id: Optional[str] = None) -> List[Dict]:
        """Get recent mentions/replies to our tweets."""
        try:
            loop = asyncio.get_event_loop()

            me = await loop.run_in_executor(None, lambda: self.client.get_me())
            user_id = me.data.id

            kwargs = {
                "id": user_id,
                "tweet_fields": ["created_at", "in_reply_to_user_id", "referenced_tweets", "author_id"],
                "user_fields": ["username"],
                "expansions": ["author_id", "referenced_tweets.id"],
                "max_results": 50,
            }
            if since_id:
                kwargs["since_id"] = since_id

            response = await loop.run_in_executor(
                None, lambda: self.client.get_users_mentions(**kwargs)
            )

            mentions = []
            if response.data:
                users = {u.id: u for u in (response.includes.get("users", []) if response.includes else [])}
                for tweet in response.data:
                    author = users.get(tweet.author_id)
                    parent_tweet_id = None
                    if tweet.referenced_tweets:
                        for ref in tweet.referenced_tweets:
                            if ref.type == "replied_to":
                                parent_tweet_id = str(ref.id)
                                break

                    mentions.append({
                        "id": str(tweet.id),
                        "text": tweet.text,
                        "author_id": str(tweet.author_id),
                        "author_username": author.username if author else "unknown",
                        "parent_tweet_id": parent_tweet_id,
                        "created_at": tweet.created_at,
                    })

            return mentions

        except Exception as e:
            print(f"Error getting mentions: {e}")
            return []

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
            me = await loop.run_in_executor(None, lambda: self.client.get_me())
            if me.data:
                return {
                    "success": True,
                    "username": me.data.username,
                    "name": me.data.name,
                    "id": str(me.data.id),
                }
            return {"success": False, "error": "No user data returned"}
        except Exception as e:
            return {"success": False, "error": str(e)}


twitter_service = TwitterService()
