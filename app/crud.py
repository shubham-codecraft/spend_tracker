"""
Data-access and business logic, kept out of the route handlers so it's
independently testable and the route layer stays thin.
"""
from datetime import date as date_type
from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models, schemas


def create_expense(db: Session, expense: schemas.ExpenseCreate) -> models.Expense:
    db_expense = models.Expense(
        amount=expense.amount,
        category=expense.category,
        note=expense.note or "",
        date=expense.date,
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


def list_expenses(
    db: Session,
    category: Optional[str] = None,
    start_date: Optional[date_type] = None,
    end_date: Optional[date_type] = None,
) -> list[models.Expense]:
    query = db.query(models.Expense)
    if category:
        query = query.filter(models.Expense.category == category)
    if start_date:
        query = query.filter(models.Expense.date >= start_date)
    if end_date:
        query = query.filter(models.Expense.date <= end_date)
    return query.order_by(models.Expense.date.desc(), models.Expense.id.desc()).all()


def _month_key(d: date_type) -> tuple[int, int]:
    return (d.year, d.month)


def _previous_month_key(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def build_summary(
    db: Session,
    category: Optional[str] = None,
    start_date: Optional[date_type] = None,
    end_date: Optional[date_type] = None,
    today: Optional[date_type] = None,
    insight_threshold_pct: float = 20.0,
) -> schemas.SummaryOut:
    """
    Builds the summary payload.

    Design decision: `category`/`start_date`/`end_date` scope the
    `total_spend` and `spend_by_category` figures (so the summary respects
    the same filters as GET /expenses). Month-over-month comparison and the
    per-category insight flags, however, are always computed against the
    *full* dataset (optionally narrowed by `category` only) because they're
    inherently about calendar months, not an arbitrary filtered slice —
    date-range filtering both months would usually leave nothing to compare.
    """
    today = today or date_type.today()

    filtered = list_expenses(db, category=category, start_date=start_date, end_date=end_date)
    total_spend = round(sum(e.amount for e in filtered), 2)

    by_category: dict[str, float] = defaultdict(float)
    for e in filtered:
        by_category[e.category] += e.amount
    spend_by_category = [
        schemas.CategoryTotal(category=cat, total=round(total, 2))
        for cat, total in sorted(by_category.items(), key=lambda kv: -kv[1])
    ]

    # For MoM + insights, pull the (optionally category-scoped) full history.
    all_for_trend = list_expenses(db, category=category)
    monthly_category_totals: dict[tuple[int, int], dict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    for e in all_for_trend:
        monthly_category_totals[_month_key(e.date)][e.category] += e.amount

    current_key = _month_key(today)
    previous_key = _previous_month_key(*current_key)

    current_month_by_cat = monthly_category_totals.get(current_key, {})
    previous_month_by_cat = monthly_category_totals.get(previous_key, {})

    current_month_total = round(sum(current_month_by_cat.values()), 2)
    previous_month_total = round(sum(previous_month_by_cat.values()), 2)

    if previous_month_total > 0:
        mom_change = round(
            (current_month_total - previous_month_total) / previous_month_total * 100, 2
        )
    elif current_month_total > 0:
        mom_change = None  # no baseline to compare against (previous month had no spend)
    else:
        mom_change = None

    insights: list[schemas.CategoryInsight] = []
    all_categories = set(current_month_by_cat) | set(previous_month_by_cat)
    for cat in all_categories:
        prev = previous_month_by_cat.get(cat, 0.0)
        curr = current_month_by_cat.get(cat, 0.0)
        if prev <= 0:
            continue  # no baseline for this category last month; skip rather than div/0
        pct = (curr - prev) / prev * 100
        if pct > insight_threshold_pct:
            insights.append(
                schemas.CategoryInsight(
                    category=cat,
                    previous_month_total=round(prev, 2),
                    current_month_total=round(curr, 2),
                    percent_change=round(pct, 2),
                )
            )
    insights.sort(key=lambda i: -i.percent_change)

    return schemas.SummaryOut(
        total_spend=total_spend,
        spend_by_category=spend_by_category,
        current_month_total=current_month_total,
        previous_month_total=previous_month_total,
        month_over_month_percent_change=mom_change,
        insights=insights,
    )
