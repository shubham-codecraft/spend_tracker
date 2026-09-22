"""Spend Tracker FastAPI application."""
import logging
import os
import smtplib
import time
from datetime import date as date_type
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .auth import create_access_token, get_current_user
from .database import get_db
from .otp import request_otp, verify_otp

logger = logging.getLogger("spend_tracker")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

app = FastAPI(
    title="Spend Tracker API",
    description="Log expenses and get a spend summary.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    logger.info("Request started: %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled exception for %s %s", request.method, request.url.path)
        raise
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "Request completed: %s %s status=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return a compact validation payload for the frontend."""
    errors = [
        {"field": ".".join(str(p) for p in err["loc"] if p != "body"), "message": err["msg"]}
        for err in exc.errors()
    ]
    logger.warning("Validation failed for %s %s: %s", request.method, request.url.path, errors)
    return JSONResponse(status_code=422, content={"detail": "Validation failed", "errors": errors})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("HTTP error for %s %s: %s", request.method, request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error for %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def health():
    return {"status": "ok", "service": "spend-tracker"}


@app.post("/auth/request-otp", status_code=status.HTTP_202_ACCEPTED)
def request_login_otp(payload: schemas.OTPRequest, db: Session = Depends(get_db)):
    try:
        request_otp(
            db,
            email=payload.email,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
    except RuntimeError as exc:
        logger.error("OTP email service is not configured: %s", exc)
        raise HTTPException(status_code=503, detail="Email service is not configured") from exc
    except OSError as exc:
        logger.exception("OTP email service connection failed")
        raise HTTPException(status_code=503, detail="Email service is unavailable") from exc
    except smtplib.SMTPException as exc:
        logger.exception("OTP email service rejected the request")
        raise HTTPException(status_code=503, detail="Email service is unavailable") from exc
    return {"detail": "Verification code sent"}


@app.post("/auth/verify-otp", response_model=schemas.Token)
def verify_login_otp(payload: schemas.OTPVerifyRequest, db: Session = Depends(get_db)):
    challenge = verify_otp(db, email=payload.email, otp=payload.otp)
    user = crud.get_or_create_user(
        db,
        email=challenge.email,
        first_name=challenge.first_name,
        last_name=challenge.last_name,
    )
    token = create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
    }


@app.post(
    "/expenses",
    response_model=schemas.ExpenseOut,
    status_code=status.HTTP_201_CREATED,
)
def create_expense(
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.create_expense(db, expense, user_id=current_user.id)


@app.get(
    "/expenses",
    response_model=list[schemas.ExpenseOut],
)
def get_expenses(
    category: Optional[str] = Query(default=None),
    start_date: Optional[date_type] = Query(default=None),
    end_date: Optional[date_type] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be on or before end_date")
    return crud.list_expenses(
        db,
        category=category,
        start_date=start_date,
        end_date=end_date,
        user_id=current_user.id,
    )


@app.get(
    "/summary",
    response_model=schemas.SummaryOut,
)
def get_summary(
    category: Optional[str] = Query(default=None),
    start_date: Optional[date_type] = Query(default=None),
    end_date: Optional[date_type] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be on or before end_date")
    return crud.build_summary(
        db,
        category=category,
        start_date=start_date,
        end_date=end_date,
        user_id=current_user.id,
    )
