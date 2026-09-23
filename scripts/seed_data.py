"""
Database Seeder Script
Populates the database with realistic sample categories, products, inventory counts,
and default Admin and Customer accounts for instant testing and demonstration.

Run via: py scripts/seed_data.py
"""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.product import Product
from app.models.cart import Cart
from app.models.inventory_log import InventoryLog, InventoryChangeType
from app.repositories.category_repository import slugify as cat_slugify
from app.repositories.product_repository import slugify as prod_slugify


def seed():
    print("[*] Ensuring database tables are created...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("[*] Checking existing data...")
        if db.query(User).filter(User.email == "admin@novamart.com").first():
            print("[!] Database is already seeded! Exiting seeder.")
            return

        print("[*] Creating default users...")
        admin_user = User(
            full_name="Administrator",
            email="admin@novamart.com",
            hashed_password=get_password_hash("Admin@123456"),
            role=UserRole.ADMIN,
            is_active=True
        )
        customer_user = User(
            full_name="Alex Johnson",
            email="customer@novamart.com",
            hashed_password=get_password_hash("Customer@123456"),
            role=UserRole.CUSTOMER,
            is_active=True
        )
        db.add_all([admin_user, customer_user])
        db.flush()

        # Initialize carts
        db.add_all([
            Cart(user_id=admin_user.id),
            Cart(user_id=customer_user.id)
        ])
        db.flush()
        print(f"    [+] Created Admin: {admin_user.email} (Password: Admin@123456)")
        print(f"    [+] Created Customer: {customer_user.email} (Password: Customer@123456)")

        print("[*] Creating categories...")
        categories_data = [
            ("Electronics & Gadgets", "Laptops, audio equipment, peripherals, and smart accessories."),
            ("Home & Kitchen", "Cookware, coffee makers, smart home utilities, and decor."),
            ("Apparel & Accessories", "Comfortable streetwear, hoodies, and ergonomic backpacks."),
            ("Books & Learning", "Software architecture books, system design guides, and developer notes.")
        ]

        categories_map = {}
        for name, desc in categories_data:
            cat = Category(name=name, slug=cat_slugify(name), description=desc, is_active=True)
            db.add(cat)
            db.flush()
            categories_map[name] = cat.id
            print(f"    [+] Added Category: {name}")

        print("[*] Creating products & inventory stock...")
        products_data = [
            # Electronics
            (
                "Mechanical Gaming Keyboard",
                "TECH-KB-001",
                "Custom RGB mechanical keyboard with hot-swappable tactile switches and aluminum chassis.",
                129.99,
                45,
                categories_map["Electronics & Gadgets"]
            ),
            (
                "Wireless Noise-Cancelling Headphones",
                "TECH-HP-002",
                "Over-ear bluetooth headphones with 40-hour battery life and high-fidelity drivers.",
                199.50,
                30,
                categories_map["Electronics & Gadgets"]
            ),
            (
                "Ultra-Wide 34-Inch Curved Monitor",
                "TECH-MN-003",
                "144Hz WQHD IPS curved gaming and productivity monitor with USB-C 90W power delivery.",
                499.00,
                12,
                categories_map["Electronics & Gadgets"]
            ),
            (
                "Precision Wireless Ergonomic Mouse",
                "TECH-MS-004",
                "Ergonomic rechargeable mouse with dual Bluetooth & 2.4GHz wireless connectivity.",
                79.99,
                60,
                categories_map["Electronics & Gadgets"]
            ),
            (
                "Limited Edition Retro Keycap Set (Out of Stock Demo)",
                "TECH-KC-005",
                "Double-shot PBT keycaps with vintage color palette. Currently sold out to test stock validation.",
                49.99,
                0,  # Zero stock to test out-of-stock validation
                categories_map["Electronics & Gadgets"]
            ),
            # Home & Kitchen
            (
                "Smart Temperature Control Mug",
                "HOME-MG-101",
                "App-controlled ceramic coated mug that maintains beverage temperature up to 145F.",
                119.00,
                25,
                categories_map["Home & Kitchen"]
            ),
            (
                "Pour-Over Glass Coffee Dripper Station",
                "HOME-CF-102",
                "Barista-grade heat-resistant borosilicate glass carafe with permanent stainless filter.",
                39.95,
                40,
                categories_map["Home & Kitchen"]
            ),
            (
                "Aroma Essential Oil Diffuser",
                "HOME-DF-103",
                "Ultrasonic cool mist aromatherapy diffuser with ambient warm light and timer.",
                29.99,
                3,  # Low stock demo
                categories_map["Home & Kitchen"]
            ),
            # Apparel
            (
                "Heavyweight Cotton Developer Hoodie",
                "APRL-HD-201",
                "450 GSM fleece-lined oversized hoodie with minimalist binary print on sleeve.",
                68.00,
                50,
                categories_map["Apparel & Accessories"]
            ),
            (
                "Water-Resistant Commuter Tech Backpack",
                "APRL-BP-202",
                "Roll-top 24L backpack with dedicated padded 16-inch laptop compartment and hidden luggage strap.",
                89.50,
                35,
                categories_map["Apparel & Accessories"]
            ),
            # Books
            (
                "Designing Data-Intensive Applications",
                "BOOK-DDIA-301",
                "The definitive guide to the architecture of reliable, scalable, and maintainable systems.",
                48.00,
                80,
                categories_map["Books & Learning"]
            ),
            (
                "System Design Interview Survival Guide",
                "BOOK-SDI-302",
                "Comprehensive patterns for high-concurrency microservices, caching, and database sharding.",
                34.99,
                65,
                categories_map["Books & Learning"]
            )
        ]

        for title, sku, desc, price, stock, cat_id in products_data:
            prod = Product(
                title=title,
                slug=prod_slugify(title),
                sku=sku,
                description=desc,
                price=price,
                stock_quantity=stock,
                category_id=cat_id,
                is_active=True
            )
            db.add(prod)
            db.flush()

            if stock > 0:
                log = InventoryLog(
                    product_id=prod.id,
                    change_type=InventoryChangeType.INITIAL_STOCK,
                    quantity_changed=stock,
                    previous_quantity=0,
                    new_quantity=stock,
                    reference_id="Initial database seeding"
                )
                db.add(log)

            print(f"    [+] Added Product: '{title}' (SKU: {sku}, Stock: {stock}, Price: ${price:.2f})")

        db.commit()
        print("\n[SUCCESS] Database successfully seeded with test accounts, categories, products, and inventory logs!")
        print("--------------------------------------------------------------------------------")
        print("Credentials for testing:")
        print("  Admin:    admin@novamart.com    | Password: Admin@123456")
        print("  Customer: customer@novamart.com | Password: Customer@123456")
        print("--------------------------------------------------------------------------------")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Database seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
