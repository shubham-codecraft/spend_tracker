"""One-time password generation and verification helpers."""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from . import models
from .email import send_otp_email

OTP_EXPIRE_MINUTES = int(os.getenv("OTP_EXPIRE_MINUTES", "10"))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))


def _hash_otp(email: str, otp: str) -> str:
    secret = os.environ["JWT_SECRET_KEY"].encode()
    value = f"{email}:{otp}".encode()
    return hmac.new(secret, value, hashlib.sha256).hexdigest()


def request_otp(
    db: Session,
    *,
    email: str,
    first_name: str,
    last_name: str,
) -> None:
    normalized_email = email.strip().lower()
    otp = f"{secrets.randbelow(1_000_000):06d}"
    challenge = models.OTPChallenge(
        email=normalized_email,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        code_hash=_hash_otp(normalized_email, otp),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES),
    )
    db.add(challenge)
    db.flush()
    try:
        send_otp_email(
            recipient=normalized_email,
            otp=otp,
            expires_in_minutes=OTP_EXPIRE_MINUTES,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise


def verify_otp(db: Session, *, email: str, otp: str) -> models.OTPChallenge:
    normalized_email = email.strip().lower()
    challenge = (
        db.query(models.OTPChallenge)
        .filter(
            models.OTPChallenge.email == normalized_email,
            models.OTPChallenge.used_at.is_(None),
        )
        .order_by(models.OTPChallenge.created_at.desc(), models.OTPChallenge.id.desc())
        .first()
    )
    now = datetime.now(timezone.utc)
    expires_at = challenge.expires_at.replace(tzinfo=timezone.utc) if challenge and challenge.expires_at.tzinfo is None else challenge.expires_at if challenge else None
    if not challenge or expires_at <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired or invalid")
    if challenge.attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many OTP attempts")

    challenge.attempts += 1
    if not hmac.compare_digest(challenge.code_hash, _hash_otp(normalized_email, otp)):
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired or invalid")

    challenge.used_at = now
    db.commit()
    db.refresh(challenge)
    return challenge