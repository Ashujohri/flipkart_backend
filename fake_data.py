import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from faker import Faker
from faker.providers import internet, person, address, phone_number
import random
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserAddress
from app.models.product import Product, ProductVariant, ProductImage, ProductSpecification, Inventory, Cart
from app.models.seller import Seller
from app.models.order import Order, OrderItem, OrderStatusHistory
from app.models.review import Review
import app.models

fake = Faker('en_IN')
db = SessionLocal()


def fake_users(count: int = 50):
    print(f"👤 Creating {count} fake users...")
    users = []

    for i in range(count):
        phone = f"9{random.randint(100000000, 999999999)}"
        existing = db.query(User).filter(User.phone == phone).first()
        if existing:
            continue

        user = User(
            full_name=fake.name(),
            email=fake.unique.email(),
            phone=phone,
            password_hash=hash_password("Test@1234"),
            gender=random.choice(["male", "female", "other"]),
            is_active=True,
            is_verified=random.choice([True, False]),
            is_phone_verified=random.choice([True, False]),
            flipkart_plus=random.choice([True, False, False, False]),
            created_at=fake.date_time_between(
                start_date="-1y",
                end_date="now",
                tzinfo=timezone.utc,
            ),
        )
        db.add(user)
        db.flush()

        # address add karo
        address_obj = UserAddress(
            user_id=user.id,
            full_name=user.full_name,
            phone=user.phone,
            address_line1=fake.street_address(),
            city=random.choice(["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Pune"]),
            state=random.choice(["Maharashtra", "Delhi", "Karnataka", "Telangana", "Tamil Nadu"]),
            pincode=random.choice(["400001", "110001", "560001", "500001", "600001", "411001"]),
            address_type=random.choice(["home", "work"]),
            is_default=True,
        )
        db.add(address_obj)
        users.append(user)

    db.commit()
    print(f"   ✅ {len(users)} users created — password: Test@1234")
    return users


def fake_sellers(count: int = 10):
    print(f"🏪 Creating {count} fake sellers...")
    sellers = []

    for i in range(count):
        phone = f"8{random.randint(100000000, 999999999)}"
        email = fake.unique.email()

        user = User(
            full_name=fake.name(),
            email=email,
            phone=phone,
            password_hash=hash_password("Seller@1234"),
            role="seller",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.flush()

        seller = Seller(
            user_id=user.id,
            business_name=fake.company(),
            business_type=random.choice(["retailer", "manufacturer", "distributor"]),
            business_email=fake.unique.email(),
            business_phone=f"7{random.randint(100000000, 999999999)}",
            business_address=fake.address(),
            business_city=random.choice(["Mumbai", "Delhi", "Bangalore"]),
            business_state=random.choice(["Maharashtra", "Delhi", "Karnataka"]),
            business_pincode=random.choice(["400001", "110001", "560001"]),
            status="active",
            is_verified=True,
            commission_rate=random.choice([5.0, 8.0, 10.0, 12.0]),
            total_sales=Decimal(str(random.randint(10000, 1000000))),
        )
        db.add(seller)
        db.flush()
        sellers.append(seller)

    db.commit()
    print(f"   ✅ {len(sellers)} sellers created — password: Seller@1234")
    return sellers


def fake_products(count: int = 100):
    from app.models.product import Category, Brand
    print(f"📦 Creating {count} fake products...")

    categories = db.query(Category).filter(Category.level == 3).all()
    if not categories:
        categories = db.query(Category).filter(Category.level == 2).all()

    brands = db.query(Brand).all()
    sellers = db.query(Seller).filter(Seller.status == "active").all()

    if not sellers:
        print("   ⚠️  No sellers found — run fake_sellers first")
        return []

    products = []
    product_templates = [
        {"name": "Smartphone Pro", "base_mrp": 15000, "category_hint": "smartphones"},
        {"name": "Wireless Earbuds", "base_mrp": 2500, "category_hint": "earphones"},
        {"name": "Running Shoes", "base_mrp": 3500, "category_hint": "mens-footwear"},
        {"name": "Cotton T-Shirt", "base_mrp": 800, "category_hint": "mens-clothing"},
        {"name": "Face Moisturizer", "base_mrp": 500, "category_hint": "skincare"},
        {"name": "Laptop Bag", "base_mrp": 1500, "category_hint": "bags-luggage"},
        {"name": "Smart Watch", "base_mrp": 8000, "category_hint": "wearables"},
        {"name": "Bluetooth Speaker", "base_mrp": 3000, "category_hint": "speakers"},
        {"name": "Denim Jeans", "base_mrp": 2000, "category_hint": "mens-clothing"},
        {"name": "Sunscreen SPF50", "base_mrp": 400, "category_hint": "skincare"},
    ]

    for i in range(count):
        template = random.choice(product_templates)
        brand = random.choice(brands)
        seller = random.choice(sellers)

        # category match karo
        cat = None
        for c in categories:
            if template["category_hint"] in c.slug:
                cat = c
                break
        if not cat:
            cat = random.choice(categories)

        mrp = Decimal(str(template["base_mrp"] * random.uniform(0.8, 1.5)))
        mrp = mrp.quantize(Decimal("0.01"))
        discount = random.choice([10, 15, 20, 25, 30, 40, 50])
        selling_price = mrp * Decimal(str((100 - discount) / 100))
        selling_price = selling_price.quantize(Decimal("0.01"))

        slug = f"{brand.slug}-{template['name'].lower().replace(' ', '-')}-{i}"

        product = Product(
            seller_id=seller.id,
            category_id=cat.id,
            brand_id=brand.id,
            name=f"{brand.name} {template['name']} {random.randint(100, 999)}",
            slug=slug,
            description=fake.paragraph(nb_sentences=5),
            highlights=[
                fake.sentence(),
                fake.sentence(),
                fake.sentence(),
            ],
            mrp=mrp,
            selling_price=selling_price,
            discount_percent=float(discount),
            status="active",
            is_returnable=True,
            return_days=random.choice([7, 10, 15, 30]),
            is_cod_available=random.choice([True, True, True, False]),
            is_featured=random.choice([True, False, False, False]),
            rating_avg=round(random.uniform(3.0, 5.0), 1),
            rating_count=random.randint(0, 5000),
            warranty_summary=f"{random.randint(1,2)} Year Warranty",
            tags=[brand.slug, cat.slug, template["category_hint"]],
        )
        db.add(product)
        db.flush()

        # inventory
        stock = random.randint(0, 500)
        inventory = Inventory(
            product_id=product.id,
            total_stock=stock,
            reserved_stock=0,
            available_stock=stock,
            low_stock_threshold=10,
        )
        db.add(inventory)

        # image (placeholder)
        image = ProductImage(
            product_id=product.id,
            image_url=f"https://via.placeholder.com/400x400?text={brand.name}",
            is_primary=True,
            display_order=0,
        )
        db.add(image)

        # specifications
        specs = [
            {"group_name": "General", "key": "Brand", "value": brand.name, "display_order": 0},
            {"group_name": "General", "key": "Model", "value": f"Model {random.randint(100, 999)}", "display_order": 1},
            {"group_name": "General", "key": "Color", "value": random.choice(["Black", "White", "Blue", "Red"]), "display_order": 2},
        ]
        for spec_data in specs:
            spec = ProductSpecification(product_id=product.id, **spec_data)
            db.add(spec)

        # variant
        variant = ProductVariant(
            product_id=product.id,
            sku=f"SKU-{product.id[:8].upper()}",
            name="Size",
            value=random.choice(["S", "M", "L", "XL", "One Size"]),
            mrp=mrp,
            selling_price=selling_price,
            stock=stock,
        )
        db.add(variant)
        products.append(product)

    db.commit()
    print(f"   ✅ {len(products)} products created")
    return products


def fake_reviews(count: int = 200):
    print(f"⭐ Creating {count} fake reviews...")

    users = db.query(User).limit(50).all()
    products = db.query(Product).filter(Product.status == "active").limit(50).all()

    if not users or not products:
        print("   ⚠️  No users or products found")
        return

    # pehle se jo combinations exist karte hain track karo
    existing_combinations = set()
    existing_reviews = db.query(Review.product_id, Review.user_id).all()
    for r in existing_reviews:
        existing_combinations.add((r.product_id, r.user_id))

    created = 0
    attempts = 0

    while created < count and attempts < count * 3:
        attempts += 1
        user = random.choice(users)
        product = random.choice(products)

        # already exist karta hai?
        if (product.id, user.id) in existing_combinations:
            continue

        try:
            review = Review(
                product_id=product.id,
                user_id=user.id,
                rating=random.choices([1, 2, 3, 4, 5], weights=[5, 10, 15, 35, 35])[0],
                title=fake.sentence(nb_words=6),
                body=fake.paragraph(nb_sentences=3),
                status="approved",
                is_verified_purchase=random.choice([True, False]),
                helpful_count=random.randint(0, 100),
                created_at=fake.date_time_between(
                    start_date="-6m",
                    end_date="now",
                    tzinfo=timezone.utc,
                ),
            )
            db.add(review)
            db.commit()

            # track karo
            existing_combinations.add((product.id, user.id))
            created += 1

        except Exception:
            db.rollback()
            continue

    print(f"   ✅ {created} reviews created")


if __name__ == "__main__":
    print("\n🎭 Starting fake data generation...\n")
    try:
        fake_users(50)
        fake_sellers(10)
        fake_products(100)
        fake_reviews(200)
        print("\n✅ All fake data generated!\n")
        print("👤 User login: any fake email + Test@1234")
        print("🏪 Seller login: any fake email + Seller@1234")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()