"""
ORM models.

Schema notes:
- amount stored in the smallest currency unit's decimal form as a Float is
  "good enough" for a take-home; for real money handling I'd store integer
  cents (see README "what I'd do differently").
- date is the expense date (when the money was spent), separate from
  created_at (when the row was inserted) so backdated entries don't skew
  audit history.
- category is a plain string column with an index, not a separate table.
  A normalized categories table would be more "correct" long-term but adds
  a join for very little benefit at this scale, and free-text categories
  are actually more forgiving for a v1 UI.
"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(120), nullable=False)
    last_name = Column(String(120), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expenses = relationship("Expense", back_populates="user", cascade="all, delete-orphan")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String(64), nullable=False, index=True)
    note = Column(String(255), nullable=True, default="")
    date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="expenses")

    __table_args__ = (
        # Most queries filter by category + date range together.
        Index("ix_expenses_category_date", "category", "date"),
    )
