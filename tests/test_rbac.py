"""
Role-Based Access Control (RBAC) Integration Tests
Verifies that customer accounts cannot perform admin-only actions, and admins have full privileges.
"""


def test_customer_cannot_create_category(client, customer_headers):
    response = client.post(
        "/api/v1/categories",
        headers=customer_headers,
        json={"name": "Forbidden Category", "description": "Should fail"}
    )
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "FORBIDDEN"


def test_admin_can_create_category(client, admin_headers):
    response = client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Office Supplies", "description": "Stationery and furniture"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Office Supplies"


def test_customer_cannot_create_product(client, customer_headers, sample_catalog):
    cat_id = sample_catalog["category"].id
    response = client.post(
        "/api/v1/products",
        headers=customer_headers,
        json={
            "category_id": cat_id,
            "title": "Hacked Product",
            "sku": "HACK-01",
            "price": 10.0,
            "stock_quantity": 5
        }
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_can_create_product(client, admin_headers, sample_catalog):
    cat_id = sample_catalog["category"].id
    response = client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={
            "category_id": cat_id,
            "title": "Ergonomic Desk Mat",
            "sku": "DESK-MAT-99",
            "description": "Faux leather desk mat",
            "price": 29.99,
            "stock_quantity": 40
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["sku"] == "DESK-MAT-99"


def test_customer_cannot_access_analytics(client, customer_headers):
    response = client.get("/api/v1/admin/analytics", headers=customer_headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_can_access_analytics(client, admin_headers, sample_catalog):
    response = client.get("/api/v1/admin/analytics", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "total_products" in data["data"]
    assert "total_revenue" in data["data"]
