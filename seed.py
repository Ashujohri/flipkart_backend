import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.core.config import settings
from app.core.security import hash_password
import app.models

db = SessionLocal()


def seed_categories():
    from app.models.product import Category
    print("🌱 Seeding categories...")

    categories = [
        # Level 1 — Root
        {"name": "Electronics", "slug": "electronics", "level": 1, "display_order": 1},
        {"name": "Fashion", "slug": "fashion", "level": 1, "display_order": 2},
        {"name": "Home & Kitchen", "slug": "home-kitchen", "level": 1, "display_order": 3},
        {"name": "Sports & Fitness", "slug": "sports-fitness", "level": 1, "display_order": 4},
        {"name": "Beauty & Grooming", "slug": "beauty-grooming", "level": 1, "display_order": 5},
        {"name": "Books", "slug": "books", "level": 1, "display_order": 6},
        {"name": "Toys & Baby", "slug": "toys-baby", "level": 1, "display_order": 7},
        {"name": "Automotive", "slug": "automotive", "level": 1, "display_order": 8},
        {"name": "Grocery", "slug": "grocery", "level": 1, "display_order": 9},
        {"name": "Furniture", "slug": "furniture", "level": 1, "display_order": 10},
    ]

    root_map = {}
    for cat_data in categories:
        existing = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
        if not existing:
            cat = Category(**cat_data)
            db.add(cat)
            db.flush()
            root_map[cat_data["slug"]] = cat.id
        else:
            root_map[cat_data["slug"]] = existing.id

    db.commit()

    # Level 2 — Electronics children
    electronics_id = root_map["electronics"]
    electronics_children = [
        {"name": "Mobiles", "slug": "mobiles", "parent_id": electronics_id, "level": 2},
        {"name": "Laptops", "slug": "laptops", "parent_id": electronics_id, "level": 2},
        {"name": "Tablets", "slug": "tablets", "parent_id": electronics_id, "level": 2},
        {"name": "TVs", "slug": "tvs", "parent_id": electronics_id, "level": 2},
        {"name": "Cameras", "slug": "cameras", "parent_id": electronics_id, "level": 2},
        {"name": "Audio", "slug": "audio", "parent_id": electronics_id, "level": 2},
        {"name": "Wearables", "slug": "wearables", "parent_id": electronics_id, "level": 2},
        {"name": "Gaming", "slug": "gaming", "parent_id": electronics_id, "level": 2},
    ]

    mobile_id = None
    audio_id = None
    for cat_data in electronics_children:
        existing = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
        if not existing:
            cat = Category(**cat_data)
            db.add(cat)
            db.flush()
            if cat_data["slug"] == "mobiles":
                mobile_id = cat.id
            if cat_data["slug"] == "audio":
                audio_id = cat.id
        else:
            if cat_data["slug"] == "mobiles":
                mobile_id = existing.id
            if cat_data["slug"] == "audio":
                audio_id = existing.id

    db.commit()

    # Level 2 — Fashion children
    fashion_id = root_map["fashion"]
    fashion_children = [
        {"name": "Men's Clothing", "slug": "mens-clothing", "parent_id": fashion_id, "level": 2},
        {"name": "Women's Clothing", "slug": "womens-clothing", "parent_id": fashion_id, "level": 2},
        {"name": "Kids' Clothing", "slug": "kids-clothing", "parent_id": fashion_id, "level": 2},
        {"name": "Men's Footwear", "slug": "mens-footwear", "parent_id": fashion_id, "level": 2},
        {"name": "Women's Footwear", "slug": "womens-footwear", "parent_id": fashion_id, "level": 2},
        {"name": "Watches", "slug": "watches", "parent_id": fashion_id, "level": 2},
        {"name": "Sunglasses", "slug": "sunglasses", "parent_id": fashion_id, "level": 2},
        {"name": "Bags & Luggage", "slug": "bags-luggage", "parent_id": fashion_id, "level": 2},
        {"name": "Jewellery", "slug": "jewellery", "parent_id": fashion_id, "level": 2},
    ]

    for cat_data in fashion_children:
        existing = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
        if not existing:
            cat = Category(**cat_data)
            db.add(cat)

    db.commit()

    # Level 2 — Beauty children
    beauty_id = root_map["beauty-grooming"]
    beauty_children = [
        {"name": "Skincare", "slug": "skincare", "parent_id": beauty_id, "level": 2},
        {"name": "Haircare", "slug": "haircare", "parent_id": beauty_id, "level": 2},
        {"name": "Men's Grooming", "slug": "mens-grooming", "parent_id": beauty_id, "level": 2},
        {"name": "Fragrances", "slug": "fragrances", "parent_id": beauty_id, "level": 2},
        {"name": "Makeup", "slug": "makeup", "parent_id": beauty_id, "level": 2},
    ]

    for cat_data in beauty_children:
        existing = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
        if not existing:
            cat = Category(**cat_data)
            db.add(cat)

    db.commit()

    # Level 3 — Mobiles children
    if mobile_id:
        mobile_children = [
            {"name": "Smartphones", "slug": "smartphones", "parent_id": mobile_id, "level": 3},
            {"name": "Feature Phones", "slug": "feature-phones", "parent_id": mobile_id, "level": 3},
            {"name": "Mobile Accessories", "slug": "mobile-accessories", "parent_id": mobile_id, "level": 3},
        ]
        for cat_data in mobile_children:
            existing = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
            if not existing:
                cat = Category(**cat_data)
                db.add(cat)

    # Level 3 — Audio children
    if audio_id:
        audio_children = [
            {"name": "Earphones", "slug": "earphones", "parent_id": audio_id, "level": 3},
            {"name": "Headphones", "slug": "headphones", "parent_id": audio_id, "level": 3},
            {"name": "Speakers", "slug": "speakers", "parent_id": audio_id, "level": 3},
        ]
        for cat_data in audio_children:
            existing = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
            if not existing:
                cat = Category(**cat_data)
                db.add(cat)

    db.commit()
    total = db.query(Category).count()
    print(f"   ✅ {total} categories seeded")


def seed_brands():
    from app.models.product import Brand
    print("🌱 Seeding brands...")

    brands = [
        # Electronics
        {"name": "Samsung", "slug": "samsung", "is_verified": True},
        {"name": "Apple", "slug": "apple", "is_verified": True},
        {"name": "OnePlus", "slug": "oneplus", "is_verified": True},
        {"name": "Xiaomi", "slug": "xiaomi", "is_verified": True},
        {"name": "Realme", "slug": "realme", "is_verified": True},
        {"name": "OPPO", "slug": "oppo", "is_verified": True},
        {"name": "Vivo", "slug": "vivo", "is_verified": True},
        {"name": "Sony", "slug": "sony", "is_verified": True},
        {"name": "LG", "slug": "lg", "is_verified": True},
        {"name": "Boat", "slug": "boat", "is_verified": True},
        {"name": "JBL", "slug": "jbl", "is_verified": True},
        {"name": "Lenovo", "slug": "lenovo", "is_verified": True},
        {"name": "HP", "slug": "hp", "is_verified": True},
        {"name": "Dell", "slug": "dell", "is_verified": True},
        {"name": "Asus", "slug": "asus", "is_verified": True},
        # Fashion
        {"name": "Nike", "slug": "nike", "is_verified": True},
        {"name": "Adidas", "slug": "adidas", "is_verified": True},
        {"name": "Puma", "slug": "puma", "is_verified": True},
        {"name": "Levi's", "slug": "levis", "is_verified": True},
        {"name": "H&M", "slug": "hm", "is_verified": True},
        {"name": "Zara", "slug": "zara", "is_verified": True},
        {"name": "Allen Solly", "slug": "allen-solly", "is_verified": True},
        {"name": "Van Heusen", "slug": "van-heusen", "is_verified": True},
        {"name": "Peter England", "slug": "peter-england", "is_verified": True},
        # Beauty
        {"name": "Lakme", "slug": "lakme", "is_verified": True},
        {"name": "L'Oreal", "slug": "loreal", "is_verified": True},
        {"name": "Himalaya", "slug": "himalaya", "is_verified": True},
        {"name": "Mamaearth", "slug": "mamaearth", "is_verified": True},
        {"name": "Gillette", "slug": "gillette", "is_verified": True},
        {"name": "Nivea", "slug": "nivea", "is_verified": True},
    ]

    for brand_data in brands:
        existing = db.query(Brand).filter(Brand.slug == brand_data["slug"]).first()
        if not existing:
            brand = Brand(**brand_data)
            db.add(brand)

    db.commit()
    total = db.query(Brand).count()
    print(f"   ✅ {total} brands seeded")


def seed_delivery_partners():
    from app.models.delivery import DeliveryPartner
    print("🌱 Seeding delivery partners...")

    partners = [
        {
            "name": "Ekart Logistics",
            "code": "EKART",
            "tracking_url_format": "https://ekart.com/track/{tracking_number}",
            "base_rate": 40.00,
            "per_kg_rate": 15.00,
            "cod_charge": 25.00,
        },
        {
            "name": "Bluedart",
            "code": "BLUEDART",
            "tracking_url_format": "https://www.bluedart.com/tracking?tracknumbers={tracking_number}",
            "base_rate": 60.00,
            "per_kg_rate": 20.00,
            "cod_charge": 30.00,
        },
        {
            "name": "Delhivery",
            "code": "DELHIVERY",
            "tracking_url_format": "https://www.delhivery.com/track/package/{tracking_number}",
            "base_rate": 45.00,
            "per_kg_rate": 15.00,
            "cod_charge": 20.00,
        },
        {
            "name": "DTDC",
            "code": "DTDC",
            "tracking_url_format": "https://www.dtdc.in/tracking.asp?txtwhere={tracking_number}",
            "base_rate": 50.00,
            "per_kg_rate": 18.00,
            "cod_charge": 25.00,
        },
    ]

    for partner_data in partners:
        existing = db.query(DeliveryPartner).filter(
            DeliveryPartner.code == partner_data["code"]
        ).first()
        if not existing:
            partner = DeliveryPartner(**partner_data)
            db.add(partner)

    db.commit()
    total = db.query(DeliveryPartner).count()
    print(f"   ✅ {total} delivery partners seeded")


def seed_pincodes():
    from app.models.delivery import Pincode
    print("🌱 Seeding pincodes (major cities)...")

    pincodes = [
        # Mumbai
        {"pincode": "400001", "city": "Mumbai", "district": "Mumbai", "state": "Maharashtra", "delivery_days": 2},
        {"pincode": "400051", "city": "Mumbai", "district": "Mumbai", "state": "Maharashtra", "delivery_days": 2},
        {"pincode": "400069", "city": "Mumbai", "district": "Mumbai", "state": "Maharashtra", "delivery_days": 2},
        # Delhi
        {"pincode": "110001", "city": "New Delhi", "district": "Central Delhi", "state": "Delhi", "delivery_days": 2},
        {"pincode": "110019", "city": "New Delhi", "district": "South Delhi", "state": "Delhi", "delivery_days": 2},
        {"pincode": "110092", "city": "New Delhi", "district": "East Delhi", "state": "Delhi", "delivery_days": 2},
        # Bangalore
        {"pincode": "560001", "city": "Bangalore", "district": "Bangalore Urban", "state": "Karnataka", "delivery_days": 3},
        {"pincode": "560034", "city": "Bangalore", "district": "Bangalore Urban", "state": "Karnataka", "delivery_days": 3},
        {"pincode": "560066", "city": "Bangalore", "district": "Bangalore Urban", "state": "Karnataka", "delivery_days": 3},
        # Hyderabad
        {"pincode": "500001", "city": "Hyderabad", "district": "Hyderabad", "state": "Telangana", "delivery_days": 3},
        {"pincode": "500032", "city": "Hyderabad", "district": "Hyderabad", "state": "Telangana", "delivery_days": 3},
        # Chennai
        {"pincode": "600001", "city": "Chennai", "district": "Chennai", "state": "Tamil Nadu", "delivery_days": 3},
        {"pincode": "600040", "city": "Chennai", "district": "Chennai", "state": "Tamil Nadu", "delivery_days": 3},
        # Pune
        {"pincode": "411001", "city": "Pune", "district": "Pune", "state": "Maharashtra", "delivery_days": 3},
        {"pincode": "411045", "city": "Pune", "district": "Pune", "state": "Maharashtra", "delivery_days": 3},
        # Kolkata
        {"pincode": "700001", "city": "Kolkata", "district": "Kolkata", "state": "West Bengal", "delivery_days": 4},
        {"pincode": "700091", "city": "Kolkata", "district": "Kolkata", "state": "West Bengal", "delivery_days": 4},
        # Ahmedabad
        {"pincode": "380001", "city": "Ahmedabad", "district": "Ahmedabad", "state": "Gujarat", "delivery_days": 4},
        # Jaipur
        {"pincode": "302001", "city": "Jaipur", "district": "Jaipur", "state": "Rajasthan", "delivery_days": 4},
        # Lucknow
        {"pincode": "226001", "city": "Lucknow", "district": "Lucknow", "state": "Uttar Pradesh", "delivery_days": 4},
        # Remote areas
        {"pincode": "793001", "city": "Shillong", "district": "East Khasi Hills", "state": "Meghalaya", "delivery_days": 7, "is_cod_available": False},
        {"pincode": "737101", "city": "Gangtok", "district": "East Sikkim", "state": "Sikkim", "delivery_days": 7, "is_cod_available": False},
    ]

    for pin_data in pincodes:
        existing = db.query(Pincode).filter(
            Pincode.pincode == pin_data["pincode"]
        ).first()
        if not existing:
            pincode = Pincode(**pin_data)
            db.add(pincode)

    db.commit()
    total = db.query(Pincode).count()
    print(f"   ✅ {total} pincodes seeded")


def seed_admin():
    from app.models.admin import AdminUser
    print("🌱 Seeding admin user...")

    existing = db.query(AdminUser).filter(
        AdminUser.email == "admin@flipkartclone.com"
    ).first()

    if not existing:
        admin = AdminUser(
            email="admin@flipkartclone.com",
            password_hash=hash_password("Admin@1234"),
            full_name="Super Admin",
            role="superadmin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print("   ✅ Admin user created")
        print("   📧 Email: admin@flipkartclone.com")
        print("   🔑 Password: Admin@1234")
    else:
        print("   ⏭️  Admin already exists")


def seed_coupons():
    from app.models.promo import Coupon
    from datetime import datetime, timezone, timedelta
    print("🌱 Seeding coupons...")

    coupons = [
        {
            "code": "WELCOME100",
            "title": "Welcome Offer",
            "description": "Get ₹100 off on your first order",
            "coupon_type": "public",
            "discount_type": "flat",
            "discount_value": 100,
            "min_order_amount": 500,
            "per_user_limit": 1,
            "total_usage_limit": 10000,
            "valid_from": datetime.now(timezone.utc),
            "valid_until": datetime.now(timezone.utc) + timedelta(days=365),
        },
        {
            "code": "SAVE10",
            "title": "10% Off",
            "description": "Get 10% off, max ₹200",
            "coupon_type": "public",
            "discount_type": "percentage",
            "discount_value": 10,
            "max_discount_amount": 200,
            "min_order_amount": 300,
            "per_user_limit": 3,
            "total_usage_limit": 50000,
            "valid_from": datetime.now(timezone.utc),
            "valid_until": datetime.now(timezone.utc) + timedelta(days=365),
        },
        {
            "code": "FLAT500",
            "title": "₹500 Off on ₹2000+",
            "description": "Get ₹500 off on orders above ₹2000",
            "coupon_type": "public",
            "discount_type": "flat",
            "discount_value": 500,
            "min_order_amount": 2000,
            "per_user_limit": 2,
            "total_usage_limit": 5000,
            "valid_from": datetime.now(timezone.utc),
            "valid_until": datetime.now(timezone.utc) + timedelta(days=365),
        },
    ]

    for coupon_data in coupons:
        existing = db.query(Coupon).filter(
            Coupon.code == coupon_data["code"]
        ).first()
        if not existing:
            coupon = Coupon(**coupon_data)
            db.add(coupon)

    db.commit()
    total = db.query(Coupon).count()
    print(f"   ✅ {total} coupons seeded")


def seed_banners():
    from app.models.promo import Banner
    print("🌱 Seeding banners...")

    banners = [
        {
            "title": "Big Billion Days Sale",
            "subtitle": "Up to 80% off on Electronics",
            "image_url": "https://via.placeholder.com/1200x400?text=Big+Billion+Days",
            "mobile_image_url": "https://via.placeholder.com/600x300?text=Big+Billion+Days",
            "redirect_url": "/sale/big-billion-days",
            "position": "hero",
            "display_order": 1,
            "is_active": True,
        },
        {
            "title": "Fashion Week",
            "subtitle": "New arrivals from top brands",
            "image_url": "https://via.placeholder.com/1200x400?text=Fashion+Week",
            "mobile_image_url": "https://via.placeholder.com/600x300?text=Fashion+Week",
            "redirect_url": "/category/fashion",
            "position": "hero",
            "display_order": 2,
            "is_active": True,
        },
        {
            "title": "Electronics Bonanza",
            "subtitle": "Mobiles, Laptops at lowest prices",
            "image_url": "https://via.placeholder.com/800x200?text=Electronics+Bonanza",
            "redirect_url": "/category/electronics",
            "position": "mid_page",
            "display_order": 1,
            "is_active": True,
        },
        {
            "title": "Deal of the Day",
            "subtitle": "Today's best deals",
            "image_url": "https://via.placeholder.com/800x200?text=Deal+of+the+Day",
            "redirect_url": "/deals",
            "position": "deals_of_day",
            "display_order": 1,
            "is_active": True,
        },
    ]

    for banner_data in banners:
        banner = Banner(**banner_data)
        db.add(banner)

    db.commit()
    total = db.query(Banner).count()
    print(f"   ✅ {total} banners seeded")


if __name__ == "__main__":
    print("\n🚀 Starting seed process...\n")
    try:
        seed_categories()
        seed_brands()
        seed_delivery_partners()
        seed_pincodes()
        seed_admin()
        seed_coupons()
        seed_banners()
        print("\n✅ All seed data inserted successfully!\n")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()