"""
Clerk JWT verification for FastAPI.
Fetches Clerk's JWKS, verifies tokens, and provides dependency functions
for protected and optionally-protected endpoints.
"""

import os
import time
import logging
from typing import Optional

import httpx
import jwt
from fastapi import Depends, HTTPException, Request

logger = logging.getLogger("auth")

_jwks_cache: dict = {}
_jwks_fetched_at: float = 0
_JWKS_TTL = 3600  # re-fetch JWKS every hour


def _get_clerk_issuer() -> str:
    """Return the Clerk issuer URL, e.g. https://your-instance.clerk.accounts.dev"""
    raw = os.getenv("CLERK_ISSUER", "")
    if raw:
        return raw.rstrip("/")
    secret = os.getenv("CLERK_SECRET_KEY", "")
    if secret:
        # extract instance id from sk_test_xxxx or sk_live_xxxx isn't reliable,
        # so CLERK_ISSUER env var is preferred
        pass
    return ""


async def _fetch_jwks() -> dict:
    global _jwks_cache, _jwks_fetched_at
    now = time.time()
    if _jwks_cache and (now - _jwks_fetched_at) < _JWKS_TTL:
        return _jwks_cache

    issuer = _get_clerk_issuer()
    if not issuer:
        logger.warning("CLERK_ISSUER not set — auth disabled")
        return {}

    url = f"{issuer}/.well-known/jwks.json"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            _jwks_fetched_at = now
            logger.info("Fetched Clerk JWKS from %s (%d keys)", url, len(_jwks_cache.get("keys", [])))
            return _jwks_cache
    except Exception as e:
        logger.error("Failed to fetch Clerk JWKS: %s", e)
        return _jwks_cache  # return stale cache if available


def _get_signing_key(jwks: dict, token: str) -> Optional[jwt.algorithms.RSAAlgorithm]:
    """Find the matching public key from JWKS for the given JWT."""
    try:
        unverified = jwt.get_unverified_header(token)
    except jwt.exceptions.DecodeError:
        return None

    kid = unverified.get("kid")
    for key_data in jwks.get("keys", []):
        if key_data.get("kid") == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
    return None


async def _verify_token(token: str) -> Optional[dict]:
    """Verify a Clerk JWT and return the claims, or None on failure."""
    issuer = _get_clerk_issuer()
    if not issuer:
        return None

    jwks = await _fetch_jwks()
    if not jwks:
        return None

    public_key = _get_signing_key(jwks, token)
    if not public_key:
        logger.warning("No matching JWKS key for token")
        return None

    try:
        claims = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=issuer,
            options={"verify_aud": False},
        )
        return claims
    except jwt.ExpiredSignatureError:
        logger.debug("Clerk token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid Clerk token: %s", e)
        return None


def _extract_bearer(request: Request) -> Optional[str]:
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


async def get_current_user(request: Request) -> dict:
    """
    Dependency: requires a valid Clerk JWT.
    Returns dict with at least 'clerk_user_id' (the Clerk `sub` claim).
    """
    token = _extract_bearer(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    claims = await _verify_token(token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {
        "clerk_user_id": claims.get("sub"),
        "email": claims.get("email"),
        "claims": claims,
    }


async def get_optional_user(request: Request) -> Optional[dict]:
    """
    Dependency: optionally extracts user from Clerk JWT.
    Returns None if no token or invalid token (doesn't raise).
    """
    token = _extract_bearer(request)
    if not token:
        return None

    claims = await _verify_token(token)
    if not claims:
        return None

    return {
        "clerk_user_id": claims.get("sub"),
        "email": claims.get("email"),
        "claims": claims,
    }
