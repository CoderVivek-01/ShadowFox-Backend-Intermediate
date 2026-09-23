"""
Product Catalog & Inventory Tests
Validates filtering, searching, pagination, stock adjustments, and boundary conditions.
"""


def test_list_products_public(client, sample_catalog):
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 3
    assert data["meta"]["total"] >= 3


def test_search_products_by_keyword(client, sample_catalog):
    response = client.get("/api/v1/products?search=Mouse")
    assert response.status_code == 200
    items = response.json()["data"]
    assert len(items) == 1
    assert items[0]["title"] == "Wireless Mouse"


def test_filter_products_by_price(client, sample_catalog):
    # in_stock is 25.50, low_stock is 99.99
    response = client.get("/api/v1/products?min_price=20&max_price=30")
    assert response.status_code == 200
    items = response.json()["data"]
    assert len(items) == 1
    assert items[0]["title"] == "Wireless Mouse"


def test_filter_products_in_stock_only(client, sample_catalog):
    response = client.get("/api/v1/products?in_stock_only=true")
    assert response.status_code == 200
    items = response.json()["data"]
    # Should exclude sold_out_keyboard (stock 0)
    titles = [item["title"] for item in items]
    assert "Wireless Mouse" in titles
    assert "Sold Out Keyboard" not in titles


def test_admin_adjust_stock_increase(client, admin_headers, sample_catalog):
    prod = sample_catalog["in_stock"]
    response = client.post(
        f"/api/v1/products/{prod.id}/adjust-stock",
        headers=admin_headers,
        json={"adjustment": 15, "reason": "Restocked shipment #104"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["stock_quantity"] == 25  # 10 + 15


def test_admin_adjust_stock_decrease(client, admin_headers, sample_catalog):
    prod = sample_catalog["in_stock"]
    response = client.post(
        f"/api/v1/products/{prod.id}/adjust-stock",
        headers=admin_headers,
        json={"adjustment": -3, "reason": "Damaged goods discard"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["stock_quantity"] == 7  # 10 - 3


def test_admin_adjust_stock_below_zero_rejected(client, admin_headers, sample_catalog):
    prod = sample_catalog["in_stock"]
    response = client.post(
        f"/api/v1/products/{prod.id}/adjust-stock",
        headers=admin_headers,
        json={"adjustment": -50, "reason": "Invalid reduction"}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"
