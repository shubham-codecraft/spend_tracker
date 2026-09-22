"""
Spend Tracker API.

Run with:
    uvicorn app.main:app --reload
"""
from datetime import date as date_type
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from . import models, schemas, crud
from .database import engine, get_db
from .auth import require_api_key

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Spend Tracker API",
    description="Log expenses and get a spend summary.",
    version="1.0.0",
)

# Wide-open CORS since the bundled frontend is a static file that may be
# opened from a different origin/port than the API during local dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Turn Pydantic's default verbose 422 payload into something a client
    can render directly without inspecting FastAPI internals."""
    errors = [
        {"field": ".".join(str(p) for p in err["loc"] if p != "body"), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": "Validation failed", "errors": errors})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(
    "/expenses",
    response_model=schemas.ExpenseOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    return crud.create_expense(db, expense)


@app.get(
    "/expenses",
    response_model=list[schemas.ExpenseOut],
    dependencies=[Depends(require_api_key)],
)
def get_expenses(
    category: Optional[str] = Query(default=None),
    start_date: Optional[date_type] = Query(default=None),
    end_date: Optional[date_type] = Query(default=None),
    db: Session = Depends(get_db),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be on or before end_date")
    return crud.list_expenses(db, category=category, start_date=start_date, end_date=end_date)


@app.get(
    "/summary",
    response_model=schemas.SummaryOut,
    dependencies=[Depends(require_api_key)],
)
def get_summary(
    category: Optional[str] = Query(default=None),
    start_date: Optional[date_type] = Query(default=None),
    end_date: Optional[date_type] = Query(default=None),
    db: Session = Depends(get_db),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be on or before end_date")
    return crud.build_summary(db, category=category, start_date=start_date, end_date=end_date)
