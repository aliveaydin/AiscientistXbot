#!/usr/bin/env python3
"""
🐦 AiScientist Local Tweet Poster Agent
========================================
Bu script Mac'te arka planda çalışır.
VPS'deki bot tweet üretir, bu script onları Twitter'a gönderir.

Twitter v2 API cloud IP'lerden bloklandığı için,
tweet göndermek ev/ofis IP'sinden yapılmalı.

Kullanım:
  python3 local_poster.py              # Tek seferlik çalıştır
  python3 local_poster.py --daemon     # Arka planda sürekli çalıştır (2 dk aralıkla)
"""

import requests
from requests_oauthlib import OAuth1
import time
import sys
import json
import os
from datetime import datetime

# ─── CONFIG ─────────────────────────────────────────────────────
VPS_URL = os.getenv("VPS_URL", "http://89.167.114.236")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "120"))  # seconds

# Twitter API keys (same as VPS .env)
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "pdzIHdS0Eu6agAnEtc6RrdM0i")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "dFicCGLjWawcUslszUmtASyhQKN0J28a8Qb4xiDI4ruud3tCRM")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "1201159163327524865-U4ArQOUgGU45VqJIvwPIsFJI3jM2FC")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "y0g52ie61rkNOLzPN0KACCsbxg57txgAlMfHGh88yRQqq")

# ─── SETUP ──────────────────────────────────────────────────────
oauth = OAuth1(TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)


def log(msg: str):
    """Print with timestamp."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def post_tweet_to_twitter(text: str) -> dict:
    """Post a tweet via Twitter v2 API from local machine."""
    payload = {"text": text}

    try:
        resp = requests.post(
            "https://api.twitter.com/2/tweets",
            json=payload,
            auth=oauth,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "AiScientistBot/1.0",
            },
            timeout=30,
        )

        if resp.status_code in (200, 201):
            data = resp.json()
            tweet_id = data["data"]["id"]
            return {"success": True, "tweet_id": tweet_id}
        else:
            return {"success": False, "error": f"{resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_pending_tweets() -> list:
    """Get pending tweets from VPS."""
    try:
        resp = requests.get(f"{VPS_URL}/api/tweets/queue/pending", timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            log(f"⚠️  VPS returned {resp.status_code}")
            return []
    except Exception as e:
        log(f"❌ VPS bağlantı hatası: {e}")
        return []


def confirm_posted(tweet_db_id: int, twitter_tweet_id: str):
    """Tell VPS that tweet was posted successfully."""
    try:
        requests.post(
            f"{VPS_URL}/api/tweets/{tweet_db_id}/confirm-posted",
            json={"tweet_id": twitter_tweet_id},
            timeout=10,
        )
    except Exception as e:
        log(f"⚠️  VPS'e bildirim gönderilemedi: {e}")


def mark_failed(tweet_db_id: int, error: str):
    """Tell VPS that tweet posting failed."""
    try:
        requests.post(
            f"{VPS_URL}/api/tweets/{tweet_db_id}/mark-failed",
            json={"error": error},
            timeout=10,
        )
    except Exception as e:
        log(f"⚠️  VPS'e hata bildirimi gönderilemedi: {e}")


def process_pending_tweets():
    """Main loop: check for pending tweets and post them."""
    pending = get_pending_tweets()

    if not pending:
        return 0

    log(f"📬 {len(pending)} bekleyen tweet bulundu")
    posted = 0

    for tweet in pending:
        tweet_id = tweet["id"]
        content = tweet["content"]
        log(f"📝 Tweet #{tweet_id}: {content[:60]}...")

        result = post_tweet_to_twitter(content)

        if result["success"]:
            log(f"✅ Tweet #{tweet_id} gönderildi! (Twitter ID: {result['tweet_id']})")
            confirm_posted(tweet_id, result["tweet_id"])
            posted += 1
        else:
            log(f"❌ Tweet #{tweet_id} gönderilemedi: {result['error']}")
            mark_failed(tweet_id, result["error"])

        # Rate limit: wait 3 seconds between tweets
        if len(pending) > 1:
            time.sleep(3)

    return posted


def run_daemon():
    """Run as a daemon, checking every CHECK_INTERVAL seconds."""
    log("🤖 AiScientist Local Poster Agent başlatıldı!")
    log(f"📡 VPS: {VPS_URL}")
    log(f"⏰ Kontrol aralığı: {CHECK_INTERVAL} saniye")
    log(f"🐦 Twitter: @{TWITTER_ACCESS_TOKEN.split('-')[0]}...")
    log("─" * 50)

    # Verify Twitter auth on startup
    log("🔐 Twitter bağlantısı test ediliyor...")
    try:
        resp = requests.get(
            "https://api.twitter.com/2/users/me",
            auth=oauth,
            timeout=10,
        )
        if resp.status_code == 200:
            user = resp.json()["data"]
            log(f"✅ Twitter: @{user['username']} ({user['name']})")
        else:
            log(f"⚠️  Twitter auth sorunu: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        log(f"⚠️  Twitter erişilemedi: {e}")

    # Verify VPS connection
    log("📡 VPS bağlantısı test ediliyor...")
    try:
        resp = requests.get(f"{VPS_URL}/api/health", timeout=10)
        if resp.status_code == 200:
            log("✅ VPS erişilebilir")
        else:
            log(f"⚠️  VPS: {resp.status_code}")
    except Exception as e:
        log(f"❌ VPS erişilemedi: {e}")

    log("─" * 50)
    log("🔄 Bekleme döngüsü başlıyor...\n")

    while True:
        try:
            posted = process_pending_tweets()
            if posted > 0:
                log(f"✨ {posted} tweet gönderildi!\n")
        except Exception as e:
            log(f"❌ Hata: {e}\n")

        time.sleep(CHECK_INTERVAL)


def run_once():
    """Run once and exit."""
    log("🤖 AiScientist Local Poster — Tek seferlik çalıştırma")
    log(f"📡 VPS: {VPS_URL}")
    posted = process_pending_tweets()
    if posted == 0:
        log("📭 Bekleyen tweet yok.")
    else:
        log(f"✨ {posted} tweet gönderildi!")


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        run_daemon()
    else:
        run_once()
