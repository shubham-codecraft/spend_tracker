"""
Summary logic is tested directly against `crud.build_summary` (rather than
only through the HTTP layer) so we can pass an explicit `today` and get
deterministic month-over-month results regardless of when the suite runs.
"""
from datetime import date
from app import crud, schemas


def _add(db_session, amount, category, on_date):
    crud.create_expense(
        db_session,
        schemas.ExpenseCreate(amount=amount, category=category, date=on_date),
    )


def test_total_spend_and_category_breakdown(db_session):
    _add(db_session, 100, "Food", date(2026, 9, 1))
    _add(db_session, 50, "Food", date(2026, 9, 5))
    _add(db_session, 30, "Transport", date(2026, 9, 10))

    summary = crud.build_summary(db_session, today=date(2026, 9, 20))

    assert summary.total_spend == 180
    by_cat = {c.category: c.total for c in summary.spend_by_category}
    assert by_cat == {"Food": 150, "Transport": 30}


def test_summary_respects_category_filter_for_totals(db_session):
    _add(db_session, 100, "Food", date(2026, 9, 1))
    _add(db_session, 30, "Transport", date(2026, 9, 10))

    summary = crud.build_summary(db_session, category="Food", today=date(2026, 9, 20))

    assert summary.total_spend == 100
    assert [c.category for c in summary.spend_by_category] == ["Food"]


def test_month_over_month_increase(db_session):
    _add(db_session, 100, "Food", date(2026, 8, 15))  # previous month
    _add(db_session, 150, "Food", date(2026, 9, 15))  # current month

    summary = crud.build_summary(db_session, today=date(2026, 9, 20))

    assert summary.previous_month_total == 100
    assert summary.current_month_total == 150
    assert summary.month_over_month_percent_change == 50.0


def test_month_over_month_with_no_previous_month_data(db_session):
    _add(db_session, 100, "Food", date(2026, 9, 15))

    summary = crud.build_summary(db_session, today=date(2026, 9, 20))

    assert summary.current_month_total == 100
    assert summary.previous_month_total == 0
    # No baseline to divide by -> None, not a crash or a misleading number.
    assert summary.month_over_month_percent_change is None


def test_month_over_month_with_no_data_at_all(db_session):
    summary = crud.build_summary(db_session, today=date(2026, 9, 20))

    assert summary.current_month_total == 0
    assert summary.previous_month_total == 0
    assert summary.month_over_month_percent_change is None
    assert summary.total_spend == 0
    assert summary.insights == []


def test_insight_flags_category_over_20_percent_increase(db_session):
    _add(db_session, 100, "Entertainment", date(2026, 8, 10))  # prev month
    _add(db_session, 130, "Entertainment", date(2026, 9, 10))  # current: +30%
    _add(db_session, 100, "Food", date(2026, 8, 10))
    _add(db_session, 105, "Food", date(2026, 9, 10))  # current: +5%, should NOT flag

    summary = crud.build_summary(db_session, today=date(2026, 9, 20), insight_threshold_pct=20.0)

    flagged = {i.category for i in summary.insights}
    assert flagged == {"Entertainment"}
    entertainment = next(i for i in summary.insights if i.category == "Entertainment")
    assert entertainment.percent_change == 30.0


def test_insight_skips_category_with_no_previous_month_baseline(db_session):
    _add(db_session, 200, "Travel", date(2026, 9, 10))  # brand new this month

    summary = crud.build_summary(db_session, today=date(2026, 9, 20))

    # No prior-month spend to compare against, so it should not be flagged
    # as an "increase" even though it went from 0 to 200.
    assert summary.insights == []


def test_year_boundary_month_over_month(db_session):
    _add(db_session, 100, "Food", date(2025, 12, 20))  # previous month = Dec 2025
    _add(db_session, 120, "Food", date(2026, 1, 10))  # current month = Jan 2026

    summary = crud.build_summary(db_session, today=date(2026, 1, 15))

    assert summary.previous_month_total == 100
    assert summary.current_month_total == 120
    assert summary.month_over_month_percent_change == 20.0
