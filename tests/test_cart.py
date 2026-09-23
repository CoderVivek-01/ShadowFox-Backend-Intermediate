"""
Shopping Cart Integration Tests
Validates adding items, stock constraints, subtotal calculations, and item updates.
"""


def test_get_empty_cart(client, customer_headers):
    response = client.get("/api/v1/cart", headers=customer_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["items"] == []
    assert data["data"]["total_items"] == 0
    assert data["data"]["total_amount"] == 0.0


def test_add_item_to_cart_success(client, customer_headers, sample_catalog):
    prod = sample_catalog["in_stock"]  # stock is 10, price is 25.50
    response = client.post(
        "/api/v1/cart/items",
        headers=customer_headers,
        json={"product_id": prod.id, "quantity": 2}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["subtotal"] == 51.0
    assert data["total_items"] == 2
    assert data["total_amount"] == 51.0


def test_add_out_of_stock_item_rejected(client, customer_headers, sample_catalog):
    prod = sample_catalog["out_of_stock"]  # stock is 0
    response = client.post(
        "/api/v1/cart/items",
        headers=customer_headers,
        json={"product_id": prod.id, "quantity": 1}
    )
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INSUFFICIENT_STOCK"


def test_add_exceeding_stock_rejected(client, customer_headers, sample_catalog):
    prod = sample_catalog["low_stock"]  # stock is 2
    response = client.post(
        "/api/v1/cart/items",
        headers=customer_headers,
        json={"product_id": prod.id, "quantity": 5}
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INSUFFICIENT_STOCK"


def test_update_cart_item_quantity(client, customer_headers, sample_catalog):
    prod = sample_catalog["in_stock"]
    # Add 2 items first
    client.post("/api/v1/cart/items", headers=customer_headers, json={"product_id": prod.id, "quantity": 2})

    # Update to 4
    response = client.put(
        f"/api/v1/cart/items/{prod.id}",
        headers=customer_headers,
        json={"quantity": 4}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["items"][0]["quantity"] == 4
    assert data["total_amount"] == 102.0


def test_update_cart_quantity_zero_removes_item(client, customer_headers, sample_catalog):
    prod = sample_catalog["in_stock"]
    client.post("/api/v1/cart/items", headers=customer_headers, json={"product_id": prod.id, "quantity": 2})

    response = client.put(
        f"/api/v1/cart/items/{prod.id}",
        headers=customer_headers,
        json={"quantity": 0}
    )
    assert response.status_code == 200
    assert response.json()["data"]["items"] == []


def test_clear_cart(client, customer_headers, sample_catalog):
    prod = sample_catalog["in_stock"]
    client.post("/api/v1/cart/items", headers=customer_headers, json={"product_id": prod.id, "quantity": 1})

    response = client.delete("/api/v1/cart", headers=customer_headers)
    assert response.status_code == 200
    assert response.json()["data"]["items"] == []
    assert response.json()["data"]["total_items"] == 0
