"""
Pydantic schemas — request/response contracts, separate from ORM models
so the API surface can evolve independently of storage.
"""
from datetime import date as date_type
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ExpenseCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Must be a positive number")
    category: str = Field(..., min_length=1, max_length=64)
    note: Optional[str] = Field(default="", max_length=255)
    date: date_type

    @field_validator("category")
    @classmethod
    def category_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("category cannot be blank")
        return v

    @field_validator("date")
    @classmethod
    def date_not_in_future(cls, v: date_type) -> date_type:
        if v > date_type.today():
            raise ValueError("date cannot be in the future")
        return v

    @field_validator("amount")
    @classmethod
    def amount_finite_and_reasonable(cls, v: float) -> float:
        if v != v or v in (float("inf"), float("-inf")):  # NaN / inf guard
            raise ValueError("amount must be a finite number")
        return round(v, 2)


class ExpenseOut(BaseModel):
    id: int
    amount: float
    category: str
    note: Optional[str]
    date: date_type

    class Config:
        from_attributes = True


class CategoryTotal(BaseModel):
    category: str
    total: float


class CategoryInsight(BaseModel):
    category: str
    previous_month_total: float
    current_month_total: float
    percent_change: float


class SummaryOut(BaseModel):
    total_spend: float
    spend_by_category: list[CategoryTotal]
    current_month_total: float
    previous_month_total: float
    month_over_month_percent_change: Optional[float]
    insights: list[CategoryInsight]
