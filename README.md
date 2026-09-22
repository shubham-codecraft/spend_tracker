# Spend Tracker

A small REST API + minimal UI for logging expenses and viewing a spend summary.

Built with **FastAPI**, **SQLAlchemy**, and **SQLite**.

## How to run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) create a `.env` file with a custom API key.
#    The app reads this automatically; it defaults to "demo-secret-key".
echo API_KEY=your-secret-key > .env

# 3. Start the API
uvicorn app.main:app --reload
```

The API is now at `http://localhost:8000`. Interactive docs (Swagger UI) are
at `http://localhost:8000/docs`.

Open `frontend/index.html` directly in a browser (double-click it, or serve
it with `python -m http.server` from the `frontend/` folder). Set the "API
key" field in the page to match `API_KEY` (default `demo-secret-key`). The
`.env` file is ignored by Git and should never be committed.

### Running the tests

```bash
pytest -v
```

20 tests covering: input validation (negative/zero amounts, blank category,
missing/malformed dates), auth enforcement, filtering (category, date
range, invalid range), and summary math (totals, category breakdown,
month-over-month in normal/no-data/year-boundary cases, and the >20%
category insight — including that it correctly *doesn't* fire when there's
no prior-month baseline).

## API

All endpoints except `/health` require an `X-API-Key` header.

| Method | Path | Description |
|---|---|---|
| POST | `/expenses` | Create an expense. Body: `{amount, category, note?, date}` |
| GET | `/expenses` | List expenses. Query params: `category`, `start_date`, `end_date` (all optional) |
| GET | `/summary` | Spend summary. Same optional filters as above |

`GET /summary` returns:

```json
{
  "total_spend": 125.50,
  "spend_by_category": [{"category": "Food", "total": 105.5}, ...],
  "current_month_total": 80.0,
  "previous_month_total": 45.5,
  "month_over_month_percent_change": 75.82,
  "insights": [
    {"category": "Food", "previous_month_total": 45.5, "current_month_total": 60.0, "percent_change": 31.87}
  ]
}
```

`insights` lists any category whose spend this month is more than 20% above
last month's spend for that same category (the bonus requirement).

## Key design decisions

- **Filters scope the totals, not the trend.** `total_spend` and
  `spend_by_category` on `/summary` respect the same `category`/date-range
  filters as `/expenses`, so the two endpoints stay consistent. But
  month-over-month and the insight flags are always computed against full
  calendar months — filtering a date range down to, say, 10 days would
  usually leave nothing to compare, so that comparison intentionally
  ignores the date-range filter (it still respects a `category` filter,
  since "how did Food change" is a reasonable question to scope).
- **No baseline is treated as "unknown", not "0% change" or "infinite
  increase".** If a category had zero spend last month, jumping to any
  amount this month isn't flagged as a spike — there's nothing to compare
  it *to*. Same logic applies to the overall MoM figure: it's `null` when
  there's no previous-month data, rather than a misleading number.
- **Free-text category, not a categories table.** A normalized table would
  be the "correct" long-term schema, but it adds a join and an admin UI for
  very little benefit at this scale, and it makes the UI less forgiving for
  a quick add-expense flow. Indexed as a plain string column instead
  (plus a composite index on `category + date`, since that's the most
  common filter combination).
- **`date` (when spent) vs `created_at` (when logged) are separate
  columns.** Letting people log a backdated lunch receipt shouldn't corrupt
  the audit trail of when the row was actually inserted.
- **Custom validation error formatting.** FastAPI's default 422 payload is
  fairly deeply nested; the app flattens it to `{"detail", "errors": [{field,
  message}]}` so a frontend can render field-level errors without knowing
  Pydantic's internals.
- **Business logic lives in `crud.py`, not the route handlers.** This is
  what let me unit-test summary math directly (with an injectable `today`)
  instead of only through HTTP, which made the month-over-month and
  year-boundary tests deterministic regardless of when the suite runs.
- **Auth is a single shared API key**, not per-user accounts — the task
  only asked for "basic" auth, and a shared key was the lightest thing that
  actually gates access on every endpoint.

## What I'd do differently with more time

- **Store money as integer cents**, not `Float`. Floats are fine for a
  take-home demo but are the wrong type for currency in anything real —
  I'd migrate to `Integer` cents or `Decimal` with a fixed scale.
- **Pagination on `GET /expenses`.** Fine for a demo dataset; would need
  `limit`/`offset` or cursor-based paging for anything with real volume.
- **Per-user accounts** instead of one shared API key — expenses aren't
  currently scoped to a user at all, which is fine for a single-user demo
  but wouldn't survive contact with a second user.
- **Alembic migrations** instead of `create_all()` — fine for a fresh
  SQLite file, but `create_all()` won't handle schema changes to an
  existing database.
- **Currency field** — right now every amount is assumed to be the same
  currency; a real tracker would need to store and convert currencies.
- **Deployment** — didn't deploy this to a public URL for the submission;
  it's a straightforward `Dockerfile` + Render/Railway deploy away (the app
  already reads `DATABASE_URL` and `API_KEY` from env vars for exactly
  that reason).

## Project structure

```
spend_tracker/
├── app/
│   ├── main.py        # FastAPI app, routes, error handling
│   ├── models.py       # SQLAlchemy ORM models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── crud.py         # Business logic (DB access + summary math)
│   ├── auth.py         # API key check
│   └── database.py     # Engine/session setup
├── tests/
│   ├── conftest.py     # Test fixtures (isolated in-memory DB per test)
│   ├── test_expenses.py
│   └── test_summary.py
├── frontend/
│   └── index.html      # Minimal vanilla JS UI
└── requirements.txt
```

## Note on AI tool use

*(Fill this in yourself before submitting — see the task's requirement
for a 2–3 line note on how you used AI tools, and what you changed or
rejected from their output. It needs to reflect your own actual process.)*
