# NovaMart E-Commerce & Inventory Management API
### *ShadowFox Backend Developer Internship — Intermediate Level Task*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg?style=flat&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063.svg?style=flat&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📌 Project Overview
**NovaMart API** is a modular, production-ready RESTful backend built for an e-commerce and warehouse inventory product. It fulfills all requirements specified in the **ShadowFox Backend Developer Internship Task (Intermediate Level)**:

* **Authentication & Authorization**: Salted Bcrypt password hashing and JWT access tokens (HS256) with 24-hour expiry.
* **Role-Based Access Control (RBAC)**: Declarative role guards separating `customer` actions (cart, checkout, personal orders) from `admin` actions (catalog creation, stock adjustment, fulfillment, audit logs).
* **Product & Inventory Management**: Full catalog CRUD with category associations, SKU constraints, keyword search, price/stock filters, and paginated responses.
* **Shopping Cart & Stock Business Rules**: Enforces warehouse availability rules preventing users from adding more items than available in stock.
* **Transactional Order Flow**: Atomic database checkout ensuring stock is never over-allocated. Order cancellation automatically restocks inventory.
* **Inventory Audit Log**: Complete audit trail tracking all stock movements (`INITIAL_STOCK`, `RESTOCK`, `PURCHASE_DEDUCTION`, `CANCELLATION_RESTOCK`, `MANUAL_ADJUSTMENT`).
* **Clean Architecture**: 4-tier separation: **Controllers (Routers)** $\rightarrow$ **Services** $\rightarrow$ **Repositories** $\rightarrow$ **Models/Schemas**.
* **Interactive API Testing**: Built-in Swagger UI (`/docs`), ReDoc (`/redoc`), and a complete exportable Postman Collection.
* **Automated Integration Testing**: Pytest suite verifying auth, RBAC, inventory limits, and atomic order transactions with an in-memory database.

---

## 🏗️ System Architecture

```
                               HTTP Client
                       (Swagger / Postman / Web)
                                  │
                                  ▼
           ┌──────────────────────────────────────────────┐
           │        Routing & Controller Layer            │
           │  - /api/v1/auth                              │
           │  - /api/v1/categories                        │
           │  - /api/v1/products                          │
           │  - /api/v1/cart                              │
           │  - /api/v1/orders                            │
           │  - /api/v1/admin                             │
           └──────────────────────┬───────────────────────┘
                                  │
                                  ▼
           ┌──────────────────────────────────────────────┐
           │          Middlewares & Dependencies          │
           │  - JWT Verification (get_current_user)       │
           │  - Role Guards (require_roles([ADMIN]))      │
           │  - Global Error Handling (AppException)      │
           │  - Performance Timing (X-Process-Time)       │
           └──────────────────────┬───────────────────────┘
                                  │
                                  ▼
           ┌──────────────────────────────────────────────┐
           │             Service Business Logic           │
           │  - AuthService, ProductService, CartService  │
           │  - OrderService (Atomic Checkout & Restock)  │
           └──────────────────────┬───────────────────────┘
                                  │
                                  ▼
           ┌──────────────────────────────────────────────┐
           │               Repository Layer               │
           │  - Data queries & database atomic locks      │
           └──────────────────────┬───────────────────────┘
                                  │
                                  ▼
           ┌──────────────────────────────────────────────┐
           │               Database Engine                │
           │  SQLite (Zero-config local) / PostgreSQL     │
           └──────────────────────────────────────────────┘
```

---

## ⚡ Quickstart Guide

### 1. Prerequisites
* Python 3.10+ (Python 3.12 recommended)
* `pip` package manager

### 2. Setup & Installation (Windows PowerShell / CMD)
```powershell
# Navigate into the project folder
cd "C:\Users\Vivek Yadav\OneDrive\Desktop\INTERNSHIP"

# Create a virtual environment
py -m venv .venv

# Activate the virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.\.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### 3. Seed Database with Initial Data
Run the included seeder script to initialize tables, categories, 12+ realistic products, and pre-configured Admin and Customer accounts:
```powershell
py scripts/seed_data.py
```

### 4. Run the Development Server
```powershell
py -m uvicorn app.main:app --reload --port 8000
```
The server will start at: `http://127.0.0.1:8000`

---

## 🔑 Default Test Credentials

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@novamart.com` | `Admin@123456` | Full catalog CRUD, stock adjustments, view all orders, change fulfillment status, view audit logs, business analytics |
| **Customer** | `customer@novamart.com` | `Customer@123456` | Browse catalog, manage personal cart, place orders, cancel pending orders, view personal order history |

---

## 📖 API Documentation & Testing

### Interactive Swagger UI
Open your browser and navigate to:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
* Click the **Authorize** button at the top right.
* Login via `/api/v1/auth/login` to get an `access_token`, paste it as `Bearer <token>`, and test all protected endpoints directly in the browser!

### Alternative ReDoc UI
👉 **[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)**

---

## 📮 Postman Collection
A complete Postman collection is included in the project under:
📁 `docs/postman_collection.json`

### How to Import & Run in Postman:
1. Open Postman.
2. Click **Import** (top left) and select `docs/postman_collection.json`.
3. In the imported collection, run **1. Authentication > Login Admin** or **Login Customer**.
   * *A built-in test script automatically saves the `access_token` into collection variables!*
4. Execute any endpoint in the collection without manually copying and pasting tokens.

---

## 🧪 Running Automated Tests

Run the full integration test suite with Pytest:
```powershell
py -m pytest -v
```
All tests run against an isolated **in-memory SQLite database** (`sqlite:///:memory:`) so local files are never modified.

### Test Coverage Highlights:
* `tests/test_auth.py`: User registration, duplicate email handling, login validation, token expiration, profile retrieval.
* `tests/test_rbac.py`: Customer attempts to access admin endpoints (403 Forbidden), admin privilege validation.
* `tests/test_products.py`: Keyword search, category filtering, price range filter, stock filters, stock adjustments up/down, boundary checks.
* `tests/test_cart.py`: Cart item calculation, adding out-of-stock items (409 Conflict), quantity limits, item removal.
* `tests/test_orders.py`: Atomic checkout transaction, warehouse inventory deduction, unauthorized order access prevention, and order cancellation restocking.

---

## 📋 API Endpoints Reference

### 🔐 Authentication (`/api/v1/auth`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Public | Register customer or admin |
| `POST` | `/api/v1/auth/login` | Public | Authenticate and receive JWT token |
| `GET` | `/api/v1/auth/me` | Protected | Get authenticated user profile |

### 📂 Categories (`/api/v1/categories`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/categories` | Public | List all active categories |
| `GET` | `/api/v1/categories/{id}` | Public | Get category details |
| `POST` | `/api/v1/categories` | Admin Only | Create new category |
| `PUT` | `/api/v1/categories/{id}` | Admin Only | Update category |
| `DELETE` | `/api/v1/categories/{id}` | Admin Only | Delete category |

### 📦 Products & Inventory (`/api/v1/products`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/products` | Public | Search, filter (category, price, in-stock), and paginate |
| `GET` | `/api/v1/products/{id}` | Public | Get single product specifications |
| `POST` | `/api/v1/products` | Admin Only | Create new product and log initial stock |
| `PUT` | `/api/v1/products/{id}` | Admin Only | Update product details |
| `DELETE` | `/api/v1/products/{id}` | Admin Only | Delete product |
| `POST` | `/api/v1/products/{id}/adjust-stock` | Admin Only | Manually adjust inventory with reason and audit log |

### 🛒 Shopping Cart (`/api/v1/cart`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/cart` | Customer | View current cart, subtotals, and total price |
| `POST` | `/api/v1/cart/items` | Customer | Add item to cart (validates available stock) |
| `PUT` | `/api/v1/cart/items/{product_id}` | Customer | Update item quantity (0 removes item) |
| `DELETE` | `/api/v1/cart/items/{product_id}` | Customer | Remove specific item from cart |
| `DELETE` | `/api/v1/cart` | Customer | Clear all items from cart |

### 💳 Orders & Checkout (`/api/v1/orders`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/orders/checkout` | Customer | **Atomic transaction**: checks stock, decrements inventory, snapshots prices, creates order, clears cart |
| `GET` | `/api/v1/orders` | Customer | List authenticated customer's order history |
| `GET` | `/api/v1/orders/{order_id}` | Customer/Admin | View order details |
| `POST` | `/api/v1/orders/{order_id}/cancel` | Customer/Admin | Cancel order and **automatically restock warehouse** |
| `GET` | `/api/v1/orders/admin/all` | Admin Only | List all orders with status filter & pagination |
| `PUT` | `/api/v1/orders/admin/{order_id}/status` | Admin Only | Update fulfillment status (`CONFIRMED`, `SHIPPED`, `DELIVERED`, `CANCELLED`) |

### 📊 Admin Operations & Analytics (`/api/v1/admin`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/admin/analytics` | Admin Only | Total users, products, orders, revenue, low/out-of-stock counts |
| `GET` | `/api/v1/admin/inventory-logs` | Admin Only | Audit trail of all warehouse stock movements |
| `GET` | `/api/v1/admin/users` | Admin Only | List all registered user accounts |

---

## 🐳 Docker Deployment

To build and run the entire application using Docker Compose:
```bash
docker-compose up --build -d
```
The application will automatically run the database seeder and serve the API on port `8000`.

---

## 🚀 Free Cloud Deployment (Render / Railway)
The project includes a ready-to-deploy `Dockerfile`.
1. Push this repository to GitHub.
2. In [Render.com](https://render.com) or [Railway.app](https://railway.app):
   * Select **New Web Service** $\rightarrow$ Connect GitHub Repo.
   * Select Environment: **Docker** or **Python**.
   * Build Command: `pip install -r requirements.txt`
   * Start Command: `python scripts/seed_data.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Copy your live deployed link (e.g. `https://novamart-backend.onrender.com/docs`) and submit it to `g1doubts@shadowfox.in`.

---

## 📄 License
This project was developed for the ShadowFox Backend Developer Internship evaluation. Licensed under the MIT License.
