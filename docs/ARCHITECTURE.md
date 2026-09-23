# NovaMart Architecture & System Design Document
*ShadowFox Backend Developer Internship Task — Intermediate Level*

---

## 1. Executive Summary
**NovaMart API** is a modular, production-ready backend system designed for e-commerce and inventory management products. The architecture was engineered around four key tenets:
1. **Strict Separation of Concerns**: Clear demarcation between presentation (Routers), business domain rules (Services), persistence (Repositories), and database schemas (Models).
2. **Deterministic Data Integrity**: Transactional checkout operations preventing overselling, atomic inventory adjustments, and automatic cancellation restocking.
3. **Defense-in-Depth Security**: Salted Bcrypt password hashing, state-free JWT authorization, and declarative Role-Based Access Control (RBAC).
4. **Contract Uniformity**: Predictable JSON response envelopes (`{success, message, data, meta}`) and standardized error payloads.

---

## 2. Architectural Layers (Separation of Concerns)

```
HTTP Client (Frontend / Postman / Swagger UI)
                  │
                  ▼
┌────────────────────────────────────────────────────────┐
│               Middlewares & Routing Layer              │
│  - RequestLoggingMiddleware (X-Process-Time)           │
│  - CORS Middleware (Cross-Origin Resource Sharing)     │
│  - Global Exception Handlers (AppException formatting) │
│  - FastAPIRouters (Auth, Categories, Products, Cart...) │
└─────────────────────────┬──────────────────────────────┘
                          │ (Validated Pydantic Schemas)
                          ▼
┌────────────────────────────────────────────────────────┐
│                   Dependency Injection                  │
│  - get_db (Session lifecycle management)               │
│  - get_current_user (JWT verification)                 │
│  - require_roles([ADMIN, CUSTOMER]) (RBAC Guard)       │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│                      Service Layer                     │
│  - AuthService: Registration, credential checks        │
│  - ProductService: Catalog rules, stock adjustments    │
│  - CartService: Stock limit validation, price math     │
│  - OrderService: Atomic checkout transaction, restock  │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│                    Repository Layer                    │
│  - Encapsulates raw SQLAlchemy queries                 │
│  - Decouples business logic from persistence engine    │
│  - Provides atomic flush, lock, and commit operations  │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│                 Database & Storage Layer               │
│  - SQLite (Local development / In-Memory testing)      │
│  - PostgreSQL (Production ready via DATABASE_URL)      │
│  - Tables: users, categories, products, carts,         │
│            cart_items, orders, order_items,            │
│            inventory_logs                              │
└────────────────────────────────────────────────────────┘
```

---

## 3. How Authentication & Authorization Were Handled

### 3.1 Authentication Workflow
1. **Registration (`POST /api/v1/auth/register`)**:
   - Client sends full name, email, password (min 6 characters), and optional role.
   - Email is normalized (`lower().strip()`) and checked for uniqueness.
   - Password is never stored in plaintext; hashed using `passlib` configured with `bcrypt` (work factor 12).
   - User entity is created and a dedicated `Cart` is automatically initialized for the user.
2. **Login (`POST /api/v1/auth/login`)**:
   - Validates user existence and verifies supplied plaintext against stored hash via `pwd_context.verify()`.
   - Generates a cryptographically signed JSON Web Token (JWT) using the `HS256` algorithm with a configurable expiration window (default 24 hours).
   - Claims include `sub` (User ID), `email`, `role`, `iat` (issued at), and `exp` (expiration).

### 3.2 Role-Based Access Control (RBAC)
FastAPI's dependency injection system was leveraged to build composable role guards:
* `get_current_user`: Decodes the token, checks token expiry, and verifies user exists and `is_active == True`.
* `require_roles([UserRole.ADMIN])`: Higher-order function that verifies the caller's role against permissible roles. If unauthorized, raises `ForbiddenException` returning an HTTP `403 Forbidden` response.
* **Separation Matrix**:
  - **Public**: Browse categories, search catalog, inspect product details, user register, user login.
  - **Customer**: Manage personal shopping cart, place orders, view personal order history, cancel pending orders.
  - **Admin**: Create/update/delete categories and products, adjust inventory quantities, list all customer orders, transition order fulfillment status, inspect inventory audit logs, view business analytics.

---

## 4. How Business Rules Were Enforced

### 4.1 Stock Availability & Cart Rules
* **Cart Addition Limit**: When a customer adds a product to their cart, `CartService` evaluates:
  $$\text{Current In Cart} + \text{Requested Quantity} \le \text{Product Available Stock}$$
  If the requested quantity exceeds available warehouse stock, the system raises an `InsufficientStockException` returning HTTP `409 Conflict` with explicit details of current stock versus requested quantity.
* **Non-Negative Quantity Constraints**: Database-level check constraints (`stock_quantity >= 0`, `price >= 0`, `quantity > 0`) ensure corrupt data cannot enter the system even under unexpected conditions.

### 4.2 Atomic Checkout Transaction
To prevent race conditions and overselling, checkout in `OrderService` follows strict ACID transaction boundaries:
1. Validates that the customer's cart is not empty.
2. Acquires real-time product records and re-validates stock for every item.
3. If any item is out of stock or requested quantity exceeds warehouse stock, the transaction is **aborted immediately with zero side-effects**.
4. Atomically decrements `product.stock_quantity -= item.quantity`.
5. Snapshots current product prices into immutable `OrderItem` records (protecting order history against future catalog price changes).
6. Creates the `Order` with a unique human-readable tracking number (e.g. `ORD-20260923-A1B2C3`).
7. Clears the customer's cart.
8. Writes an audit entry into `InventoryLog` with `change_type=PURCHASE_DEDUCTION`.
9. Issues a single `db.commit()`. If an unexpected error arises, `db.rollback()` guarantees data integrity.

### 4.3 Order Cancellation & Inventory Restock
* If a customer cancels a `PENDING` order, or an Admin cancels an order prior to delivery:
  - Iterates over all line items.
  - Restores deducted quantity: `product.stock_quantity += item.quantity`.
  - Appends an audit entry in `InventoryLog` (`CANCELLATION_RESTOCK`).
  - Sets order status to `CANCELLED`.
  - Atomically commits the changes.

---

## 5. How the Architecture Supports Maintainability & Scalability

1. **Database Agnostic**: Built on SQLAlchemy 2.0 ORM. Local development runs on zero-configuration SQLite; switching to PostgreSQL in production requires only changing `DATABASE_URL` in `.env`.
2. **Repository Decoupling**: If data persistence changes (e.g., caching hot products in Redis or migrating to async drivers), only the repository classes require modification; zero router or business logic changes are needed.
3. **Standard Envelope Schema**: Frontend clients interact with a unified contract:
   - Success: `{"success": true, "message": "...", "data": ..., "meta": ...}`
   - Error: `{"success": false, "error": {"code": "...", "message": "...", "details": ...}}`
4. **Automated Documentation**: Endpoints automatically expose OpenAPI 3.0 specification, powering interactive Swagger UI (`/docs`), ReDoc (`/redoc`), and the provided Postman collection.
