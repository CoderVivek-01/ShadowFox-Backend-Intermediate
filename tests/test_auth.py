"""
Authentication Integration Tests
Validates registration, login, JWT issuance, password verification, and identity extraction.
"""


def test_register_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "New User",
            "email": "newuser@test.com",
            "password": "Password123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "newuser@test.com"
    assert data["data"]["role"] == "customer"
    assert "hashed_password" not in data["data"]


def test_register_duplicate_email(client, seed_users):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Duplicate User",
            "email": "customer@test.com",  # Already seeded
            "password": "Password123"
        }
    )
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "CONFLICT"


def test_login_success(client, seed_users):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "customer@test.com",
            "password": "Password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"
    assert data["data"]["user"]["email"] == "customer@test.com"


def test_login_invalid_password(client, seed_users):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "customer@test.com",
            "password": "WrongPassword999"
        }
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_get_me_authenticated(client, customer_headers):
    response = client.get("/api/v1/auth/me", headers=customer_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "customer@test.com"


def test_get_me_unauthenticated(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"
