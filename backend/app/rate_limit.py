from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _get_key(request: Request) -> str:
    """Use Clerk user ID if available, otherwise fall back to IP."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            import jwt
            token = auth_header.split(" ", 1)[1]
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=_get_key)
