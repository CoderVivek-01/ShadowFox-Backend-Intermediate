"""
NovaMart E-Commerce & Inventory Management API
Main Application Factory & Lifecycle Setup
ShadowFox Backend Developer Internship Task - Intermediate Level
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import Base, engine
# Import all models so SQLAlchemy metadata is aware of tables
import app.models  # noqa: F401
from app.middlewares.error_handler import register_exception_handlers
from app.middlewares.logging import RequestLoggingMiddleware
from app.routers import auth, categories, products, cart, orders, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database tables are created
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic (if any)


tags_metadata = [
    {
        "name": "Authentication",
        "description": "User registration, password hashing (bcrypt), and JWT access token issuance.",
    },
    {
        "name": "Categories",
        "description": "Product category management. Public browsing and Admin-only CRUD operations.",
    },
    {
        "name": "Products & Inventory",
        "description": "Product catalog search, price & stock filtering, pagination, and warehouse inventory control.",
    },
    {
        "name": "Shopping Cart",
        "description": "Persistent per-user shopping cart with stock availability validation.",
    },
    {
        "name": "Orders & Checkout",
        "description": "Transactional order checkout with atomic inventory deductions and cancellation restock.",
    },
    {
        "name": "Admin Operations & Analytics",
        "description": "Business performance analytics, revenue tracking, and inventory audit trail logs.",
    },
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="""
# NovaMart E-Commerce & Inventory Management Backend

A production-style backend API designed and built for the **ShadowFox Backend Developer Internship Task (Intermediate Level)**.

### Key Architectural Highlights:
* **Separation of Concerns**: Layered structure with Routers (Controllers), Services (Business Logic), Repositories (Data Access), and Database Models.
* **Security & RBAC**: Password hashing via Bcrypt, JWT tokens (HS256), and role-based permissions (`admin` vs `customer`).
* **Inventory Control & Transactions**: Atomic database checkout ensuring stock is never over-allocated; automated restocking on cancellation.
* **Standard Response Envelope**: Consistent `{success, message, data, meta}` and structured `{success: false, error: {...}}` contracts.
* **Interactive Testing**: Complete Swagger UI (`/docs`), ReDoc (`/redoc`), and downloadable Postman collection.
""",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

# Register Custom Middlewares
app.add_middleware(RequestLoggingMiddleware)

# Register CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Global Error Handlers
register_exception_handlers(app)

# Mount API Routers under /api/v1
api_prefix = settings.API_V1_STR
app.include_router(auth.router, prefix=api_prefix)
app.include_router(categories.router, prefix=api_prefix)
app.include_router(products.router, prefix=api_prefix)
app.include_router(cart.router, prefix=api_prefix)
app.include_router(orders.router, prefix=api_prefix)
app.include_router(admin.router, prefix=api_prefix)


@app.get("/", tags=["Health & Info"], summary="API Root and Documentation Links")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        }
    }


@app.get("/health", tags=["Health & Info"], summary="Health Check Probe")
def health_check():
    return {
        "status": "healthy",
        "service": "NovaMart API",
        "version": "1.0.0"
    }
