"""
Pytest Test Configuration and Fixtures
Configures an isolated in-memory SQLite database and test clients with pre-authenticated tokens.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.main import app
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.product import Product
from app.models.cart import Cart

# In-memory SQLite engine for ultra-fast, isolated test execution
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh database schema for each test, then drops all tables."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency pointing to in-memory DB."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_users(db_session):
    """Creates test Admin and test Customer accounts in the database."""
    admin = User(
        full_name="Admin Test",
        email="admin@test.com",
        hashed_password=get_password_hash("Password123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    customer = User(
        full_name="Customer Test",
        email="customer@test.com",
        hashed_password=get_password_hash("Password123"),
        role=UserRole.CUSTOMER,
        is_active=True
    )
    other_customer = User(
        full_name="Other Customer",
        email="other@test.com",
        hashed_password=get_password_hash("Password123"),
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db_session.add_all([admin, customer, other_customer])
    db_session.flush()

    db_session.add_all([
        Cart(user_id=admin.id),
        Cart(user_id=customer.id),
        Cart(user_id=other_customer.id)
    ])
    db_session.commit()
    db_session.refresh(admin)
    db_session.refresh(customer)
    db_session.refresh(other_customer)

    return {
        "admin": admin,
        "customer": customer,
        "other_customer": other_customer
    }


@pytest.fixture(scope="function")
def admin_headers(seed_users):
    user = seed_users["admin"]
    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def customer_headers(seed_users):
    user = seed_users["customer"]
    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def other_customer_headers(seed_users):
    user = seed_users["other_customer"]
    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def sample_catalog(db_session):
    """Creates a sample category and two products (one in stock, one out of stock)."""
    category = Category(name="Electronics", slug="electronics", description="Gadgets", is_active=True)
    db_session.add(category)
    db_session.flush()

    p_in_stock = Product(
        category_id=category.id,
        title="Wireless Mouse",
        slug="wireless-mouse",
        sku="TEST-MS-01",
        description="A great mouse",
        price=25.50,
        stock_quantity=10,
        is_active=True
    )
    p_out_of_stock = Product(
        category_id=category.id,
        title="Sold Out Keyboard",
        slug="sold-out-keyboard",
        sku="TEST-KB-02",
        description="Out of stock item",
        price=75.00,
        stock_quantity=0,
        is_active=True
    )
    p_low_stock = Product(
        category_id=category.id,
        title="Gaming Headset",
        slug="gaming-headset",
        sku="TEST-HS-03",
        description="Only 2 left",
        price=99.99,
        stock_quantity=2,
        is_active=True
    )
    db_session.add_all([p_in_stock, p_out_of_stock, p_low_stock])
    db_session.commit()
    db_session.refresh(category)
    db_session.refresh(p_in_stock)
    db_session.refresh(p_out_of_stock)
    db_session.refresh(p_low_stock)

    return {
        "category": category,
        "in_stock": p_in_stock,
        "out_of_stock": p_out_of_stock,
        "low_stock": p_low_stock
    }
