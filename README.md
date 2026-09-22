# Spend Tracker

A small REST API and minimal frontend for logging expenses and viewing a spend summary.

Built with FastAPI, SQLAlchemy, SQLite, and a lightweight HTML/JavaScript UI.

## Features included

- Create expenses with validation for amount, category, date, and note
- List expenses with optional filters by category and date range
- Get a total spend summary with category breakdown
- Show month-over-month change and category-level spike insights
- Protect API routes with a simple API-key check
- Support a minimal browser UI for quick manual testing

## How to run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Optional: create a .env file with a custom API key
#    Default is demo-secret-key if no value is set.
echo API_KEY=your-secret-key > .env

# 3. Start the API
uvicorn app.main:app --reload
```

Then open:
- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

To use the frontend, open the file in the frontend folder in a browser or serve it locally:

```bash
cd frontend
python -m http.server 8001
```

Then open http://localhost:8001 and set the API key to match the value in the .env file or use the default demo-secret-key.

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
├── frontend/
│   └── index.html
├── tests/
│   ├── conftest.py
│   ├── test_expenses.py
│   └── test_summary.py
├── .gitignore
├── README.md
├── requirements.txt
├── spend_tracker.db
└── .env
```

## Testing

The project includes automated verification for validation, auth, date filtering, category filtering, invalid-range handling, and summary calculations.

```bash
pytest -q
```

Current result: 21 tests passing.

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
