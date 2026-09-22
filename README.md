# Spend Tracker

A FastAPI service and lightweight frontend for logging expenses and reviewing spend trends.

Built with FastAPI, SQLAlchemy, PostgreSQL, and a minimal HTML/JavaScript UI.

## Features included

- Create expenses with validation for amount, category, date, and note
- List expenses with optional filters by category and date range
- Get a total spend summary with category breakdown
- Show month-over-month change and category-level spike insights
- Verify users with one-time passwords sent through Gmail SMTP
- Authenticate users with JWT bearer tokens
- Scope expenses and summaries to the authenticated user
- Run the project in Docker with PostgreSQL and Alembic migrations

## How to run

### Option 1: Docker (recommended)

```bash
# 1. Copy the example environment file
cp .env.example .env

# 2. Fill in the values for your local setup
#    Example:
#    DATABASE_URL=postgresql+psycopg://spend_tracker:spend_tracker@db:5432/spend_tracker
#    POSTGRES_DB=spend_tracker
#    POSTGRES_USER=spend_tracker
#    POSTGRES_PASSWORD=spend_tracker
#    SMTP_HOST=smtp.gmail.com
#    SMTP_PORT=465
#    SMTP_USERNAME=your-gmail-address@gmail.com
#    SMTP_PASSWORD=your-gmail-app-password
#    SMTP_FROM_EMAIL=your-gmail-address@gmail.com
#    OTP_EXPIRE_MINUTES=10
#    OTP_MAX_ATTEMPTS=5

# 3. Start the full stack
docker compose up --build
```

The API container runs `alembic upgrade head` before starting Gunicorn. Do not
commit `.env`; use `.env.example` as the configuration template.

For Gmail SMTP, enable two-step verification on the sender account and create
a Google App Password. Use that App Password as `SMTP_PASSWORD`; do not use
the normal Gmail account password.

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
```

## API

`GET /health` is public. Request an email OTP, verify it, and use the returned
JWT bearer token for protected endpoints:

`POST /auth/request-otp`:

```json
{
  "email": "user@example.com",
  "first_name": "Jane",
  "last_name": "Doe"
}
```

`POST /auth/verify-otp`:

```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

Use the returned token on protected requests:

```text
Authorization: Bearer <access_token>
```

| Method | Path | Description |
|---|---|---|
| GET | /health | Service health check |
| POST | /auth/request-otp | Send an email verification code |
| POST | /auth/verify-otp | Verify the code and return a JWT |
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

Examples:

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
- Expense and summary data are scoped to the authenticated user's `user_id`
- Month-over-month comparison is computed using calendar months, not the arbitrary filtered date window
- Category insight flags trigger only when a category had a valid previous-month baseline and grew by more than 20%

## Project structure

```text
spend_tracker/
├── app/
│   ├── auth.py
│   ├── crud.py
│   ├── database.py
│   ├── email.py
│   ├── main.py
│   ├── models.py
│   ├── otp.py
│   └── schemas.py
├── tests/
│   ├── conftest.py
│   ├── test_expenses.py
│   └── test_summary.py
├── migrations/
│   ├── env.py
│   └── versions/
├── alembic.ini
├── README.md
├── docker-compose.yml
├── Dockerfile
├── .dockerignore 
├── requirements.txt
└── .gitignore
```

## Testing

The project includes automated verification for validation, JWT auth, user
scoping, OTP authentication, date filtering, category filtering,
invalid-range handling, and summary calculations.

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

The current migrations create user-scoped expenses and the `otp_challenges`
table. The API container applies pending migrations automatically before
starting the application.

Do not use `Base.metadata.create_all()` to update an existing database. Existing
databases must be changed through Alembic migrations.

## AI usage note

GitHub Copilot was used to review the project structure, help implement the
implementation, and update the documentation. The final design decisions were
reviewed against the project requirements.

## Future improvements

- Store money as Decimal or integer cents rather than Float
- Add pagination for large expense lists
- Add a production secret manager and rotated JWT signing keys
