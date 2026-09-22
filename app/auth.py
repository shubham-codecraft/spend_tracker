"""
Minimal API-key auth (bonus requirement).

Kept intentionally simple: a single shared key read from an env var,
checked via a header. This is NOT meant to be production-grade multi-user
auth — see README for what I'd do differently with more time (per-user
JWTs, hashed keys, etc.).
"""
import os
from fastapi import Header, HTTPException, status
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "demo-secret-key")
API_KEY_HEADER = "X-API-Key"


def require_api_key(x_api_key: str = Header(default=None, alias=API_KEY_HEADER)) -> None:
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key",
        )
