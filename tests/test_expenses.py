from datetime import date, timedelta


def test_create_expense_success(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={"amount": 25.50, "category": "Food", "note": "Lunch", "date": "2026-09-10"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["amount"] == 25.5
    assert body["category"] == "Food"
    assert "id" in body


def test_login_returns_jwt_token(client):
    resp = client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "first_name": "Login",
            "last_name": "User",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "login@example.com"


def test_create_expense_requires_valid_jwt(client):
    resp = client.post(
        "/expenses",
        json={"amount": 10, "category": "Food", "date": "2026-09-10"},
    )
    assert resp.status_code == 401


def test_create_expense_rejects_negative_amount(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={"amount": -5, "category": "Food", "date": "2026-09-10"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_expense_rejects_zero_amount(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={"amount": 0, "category": "Food", "date": "2026-09-10"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_expense_rejects_blank_category(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={"amount": 10, "category": "   ", "date": "2026-09-10"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_expense_rejects_missing_date(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={"amount": 10, "category": "Food"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_expense_rejects_malformed_date(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={"amount": 10, "category": "Food", "date": "not-a-date"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_expense_rejects_future_date(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={"amount": 10, "category": "Food", "date": str(date.today() + timedelta(days=1))},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_list_expenses_returns_created_items(client, auth_headers):
    client.post(
        "/expenses",
        json={"amount": 10, "category": "Food", "date": "2026-09-10"},
        headers=auth_headers,
    )
    client.post(
        "/expenses",
        json={"amount": 20, "category": "Transport", "date": "2026-09-11"},
        headers=auth_headers,
    )
    resp = client.get("/expenses", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_expenses_filters_by_category(client, auth_headers):
    client.post(
        "/expenses",
        json={"amount": 10, "category": "Food", "date": "2026-09-10"},
        headers=auth_headers,
    )
    client.post(
        "/expenses",
        json={"amount": 20, "category": "Transport", "date": "2026-09-11"},
        headers=auth_headers,
    )
    resp = client.get("/expenses", params={"category": "Food"}, headers=auth_headers)
    body = resp.json()
    assert len(body) == 1
    assert body[0]["category"] == "Food"


def test_list_expenses_filters_by_date_range(client, auth_headers):
    client.post(
        "/expenses",
        json={"amount": 10, "category": "Food", "date": "2026-08-01"},
        headers=auth_headers,
    )
    client.post(
        "/expenses",
        json={"amount": 20, "category": "Food", "date": "2026-09-15"},
        headers=auth_headers,
    )
    resp = client.get(
        "/expenses",
        params={"start_date": "2026-09-01", "end_date": "2026-09-30"},
        headers=auth_headers,
    )
    body = resp.json()
    assert len(body) == 1
    assert body[0]["date"] == "2026-09-15"


def test_list_expenses_rejects_inverted_date_range(client, auth_headers):
    resp = client.get(
        "/expenses",
        params={"start_date": "2026-09-30", "end_date": "2026-09-01"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_list_expenses_empty_when_no_data(client, auth_headers):
    resp = client.get("/expenses", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []
