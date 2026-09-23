"""
Order Processing & Inventory Checkout Tests
Validates atomic checkout, inventory deductions, unauthorized access prevention,
and cancellation restock workflows.
"""


def test_checkout_empty_cart_fails(client, customer_headers):
    response = client.post(
        "/api/v1/orders/checkout",
        headers=customer_headers,
        json={
            "shipping_address": "123 Tech Way, Suite 400",
            "contact_phone": "+1-555-0100"
        }
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"


def test_checkout_success_and_stock_deduction(client, customer_headers, sample_catalog):
    prod = sample_catalog["in_stock"]  # Initial stock = 10, price = 25.50

    # Add 3 items to cart
    client.post("/api/v1/cart/items", headers=customer_headers, json={"product_id": prod.id, "quantity": 3})

    # Checkout
    response = client.post(
        "/api/v1/orders/checkout",
        headers=customer_headers,
        json={
            "shipping_address": "452 Innovation Blvd, Austin, TX",
            "contact_phone": "+1-555-0199",
            "notes": "Gate code #4012"
        }
    )
    assert response.status_code == 201
    order_data = response.json()["data"]
    assert order_data["order_number"].startswith("ORD-")
    assert order_data["status"] == "PENDING"
    assert order_data["total_amount"] == 76.50
    assert len(order_data["items"]) == 1
    assert order_data["items"][0]["quantity"] == 3

    # Verify cart is now empty
    cart_res = client.get("/api/v1/cart", headers=customer_headers)
    assert cart_res.json()["data"]["items"] == []

    # Verify warehouse stock was decremented from 10 to 7
    prod_res = client.get(f"/api/v1/products/{prod.id}")
    assert prod_res.json()["data"]["stock_quantity"] == 7


def test_cancel_order_restocks_inventory(client, customer_headers, sample_catalog):
    prod = sample_catalog["in_stock"]  # Initial stock = 10

    # Add 4 items and checkout
    client.post("/api/v1/cart/items", headers=customer_headers, json={"product_id": prod.id, "quantity": 4})
    checkout_res = client.post(
        "/api/v1/orders/checkout",
        headers=customer_headers,
        json={"shipping_address": "789 Pine St", "contact_phone": "+1-555-4321"}
    )
    order_id = checkout_res.json()["data"]["id"]

    # Stock should be 6
    assert client.get(f"/api/v1/products/{prod.id}").json()["data"]["stock_quantity"] == 6

    # Customer cancels their PENDING order
    cancel_res = client.post(f"/api/v1/orders/{order_id}/cancel", headers=customer_headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "CANCELLED"

    # Verify inventory was restocked back to 10!
    assert client.get(f"/api/v1/products/{prod.id}").json()["data"]["stock_quantity"] == 10


def test_customer_cannot_view_others_order(client, customer_headers, other_customer_headers, sample_catalog):
    prod = sample_catalog["in_stock"]

    # Customer places order
    client.post("/api/v1/cart/items", headers=customer_headers, json={"product_id": prod.id, "quantity": 1})
    order_res = client.post(
        "/api/v1/orders/checkout",
        headers=customer_headers,
        json={"shipping_address": "Private Lane", "contact_phone": "+1-555-9999"}
    )
    order_id = order_res.json()["data"]["id"]

    # Other customer tries to view it
    intruder_res = client.get(f"/api/v1/orders/{order_id}", headers=other_customer_headers)
    assert intruder_res.status_code == 403
    assert intruder_res.json()["error"]["code"] == "FORBIDDEN"


def test_admin_can_view_and_update_order_status(client, customer_headers, admin_headers, sample_catalog):
    prod = sample_catalog["in_stock"]

    client.post("/api/v1/cart/items", headers=customer_headers, json={"product_id": prod.id, "quantity": 1})
    order_res = client.post(
        "/api/v1/orders/checkout",
        headers=customer_headers,
        json={"shipping_address": "100 Broadway", "contact_phone": "+1-555-8888"}
    )
    order_id = order_res.json()["data"]["id"]

    # Admin views order
    admin_view = client.get(f"/api/v1/orders/{order_id}", headers=admin_headers)
    assert admin_view.status_code == 200

    # Admin updates status to CONFIRMED
    update_res = client.put(
        f"/api/v1/orders/admin/{order_id}/status",
        headers=admin_headers,
        json={"status": "CONFIRMED"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["status"] == "CONFIRMED"
