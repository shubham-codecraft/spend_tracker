"""
Database engine/session setup.

Uses SQLite by default (file-based, so data survives restarts), but the
connection string is read from an env var so swapping to Postgres later
is a one-line change.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./spend_tracker.db")

# check_same_thread is only needed for SQLite (FastAPI runs each request
# in a thread, and SQLite connections are not thread-safe by default).
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
