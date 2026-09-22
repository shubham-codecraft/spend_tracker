# Spend Tracker

A small REST API and lightweight frontend for logging expenses and reviewing spend trends.

Built with FastAPI, SQLAlchemy, PostgreSQL, and a minimal HTML/JavaScript UI.

## Features included

- Create expenses with validation for amount, category, date, and note
- List expenses with optional filters by category and date range
- Get a total spend summary with category breakdown
- Show month-over-month change and category-level spike insights
- Protect API routes with user-specific JWT bearer tokens
- Run the project in Docker with a PostgreSQL service for a more production-like setup

## How to run

### Option 1: Docker (recommended)

```bash
# 1. Copy the example environment file
cp .env.example .env

# 2. Fill in the values for your local setup
#    Example:
#    API_KEY=demo-secret-key
#    DATABASE_URL=postgresql+psycopg://spend_tracker:spend_tracker@db:5432/spend_tracker
#    POSTGRES_DB=spend_tracker
#    POSTGRES_USER=spend_tracker
#    POSTGRES_PASSWORD=spend_tracker

# 3. Start the full stack
docker compose up --build
```

The API container runs `alembic upgrade head` before starting Gunicorn.

Then open:
- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

### Option 2: Local Python environment

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create a local .env file with your settings
#    Make sure DATABASE_URL points to your local PostgreSQL instance

# 3. Start the API directly
uvicorn app.main:app --reload

## API

All routes except /health require the X-API-Key header.

| Method | Path | Description |
|---|---|---|
| POST | /expenses | Create an expense |
| GET | /expenses | List expenses with optional category/date filters |
| GET | /summary | Get total spend, category totals, and month-over-month summary |

Request body for creating an expense:

```json
{
  "amount": 45.5,
  "category": "Food",
  "note": "Lunch with team",
  "date": "2026-09-22"
}
```

Optional filters for expense and summary lists:

```text
/category=Food
&start_date=2026-09-01
&end_date=2026-09-30
```

Example:

```text
GET /expenses?category=Food&start_date=2026-09-01&end_date=2026-09-30
GET /summary?category=Food&start_date=2026-09-01&end_date=2026-09-30
```

## Validation and business rules

- Amount must be greater than 0
- Category cannot be blank after trimming whitespace
- Date cannot be in the future
- If start_date is after end_date, the API returns a 400 error
- Summary totals are scoped by category/date filter
- Month-over-month comparison is computed using calendar months, not the arbitrary filtered date window
- Category insight flags trigger only when a category had a valid previous-month baseline and grew by more than 20%

## Project structure

```text
spend_tracker/
├── app/
│   ├── auth.py
│   ├── crud.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
├── tests/
│   ├── conftest.py
│   ├── test_expenses.py
│   └── test_summary.py
├── README.md
├── docker-compose.yml
├── Dockerfile
├── .dockerignore 
├── requirements.txt
└── .gitignore
```

## Testing

The project includes automated verification for validation, auth, date filtering, category filtering, invalid-range handling, and summary calculations.

```bash
pytest -q
```

## Database migrations

Apply migrations manually from the project root with:

```bash
alembic upgrade head
```

Create a new migration after changing the SQLAlchemy models with:

```bash
alembic revision -m "describe the schema change"
```

Do not use `Base.metadata.create_all()` to update an existing database. Existing
databases must be changed through Alembic migrations.

## AI usage note

I used GitHub Copilot to review the project structure, sanity-check the API design, and help clean up the README and implementation notes. I accepted the parts that matched the assignment requirements and rejected suggestions that would add complexity beyond the scope of this small demo, such as per-user authentication or production-grade migration tooling.

## Notes for future improvement

This is a strong demo implementation, but a production version would benefit from:

- storing money as Decimal or integer cents rather than Float
- stronger auth than a shared API key
- structured logging and request tracking
- database migrations instead of create_all()
- pagination for large expense lists
- currency support and multi-user scoping
