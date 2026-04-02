from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, List

from app.models.promo import (
    Coupon, CouponUsage,
    FlashSale, FlashSaleProduct,
    Banner,
)
from app.models.product import Product
from app.schemas.promo import (
    FlashSaleCreate, FlashSaleProductAdd,
    BannerCreate, BannerUpdate,
)


# ─── Flash Sale ───────────────────────────────────────────────────────────────

def get_active_flash_sales(db: Session) -> List[FlashSale]:
    now = datetime.now(timezone.utc)
    sales = db.query(FlashSale).filter(
        FlashSale.is_active == True,
        FlashSale.starts_at <= now,
        FlashSale.ends_at >= now,
    ).all()

    result = []
    for sale in sales:
        sale_dict = {
            "id": sale.id,
            "title": sale.title,
            "description": sale.description,
            "banner_url": sale.banner_url,
            "starts_at": sale.starts_at,
            "ends_at": sale.ends_at,
            "is_active": sale.is_active,
            "is_live": True,
            "products": build_flash_sale_products(db, sale),
        }
        result.append(sale_dict)
    return result


def build_flash_sale_products(db: Session, sale: FlashSale) -> list:
    items = []
    for fp in sale.products:
        if not fp.is_active:
            continue
        product = db.query(Product).filter(Product.id == fp.product_id).first()
        items.append({
            "id": fp.id,
            "product_id": fp.product_id,
            "sale_price": fp.sale_price,
            "original_price": fp.original_price,
            "discount_percent": fp.discount_percent,
            "total_quantity": fp.total_quantity,
            "sold_quantity": fp.sold_quantity,
            "per_user_limit": fp.per_user_limit,
            "is_active": fp.is_active,
            "product_name": product.name if product else None,
            "product_image": product.images[0].image_url if product and product.images else None,
        })
    return items


def create_flash_sale(db: Session, data: FlashSaleCreate, admin_id: str) -> FlashSale:
    sale = FlashSale(
        title=data.title,
        description=data.description,
        banner_url=data.banner_url,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        created_by=admin_id,
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def add_product_to_flash_sale(
    db: Session,
    sale_id: str,
    data: FlashSaleProductAdd,
) -> FlashSaleProduct:
    sale = db.query(FlashSale).filter(FlashSale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Flash sale not found")

    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # discount calculate
    original_price = product.selling_price
    discount = float(((original_price - data.sale_price) / original_price) * 100)

    existing = db.query(FlashSaleProduct).filter(
        FlashSaleProduct.flash_sale_id == sale_id,
        FlashSaleProduct.product_id == data.product_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Product already in flash sale")

    fp = FlashSaleProduct(
        flash_sale_id=sale_id,
        product_id=data.product_id,
        variant_id=data.variant_id,
        sale_price=data.sale_price,
        original_price=original_price,
        discount_percent=round(discount, 2),
        total_quantity=data.total_quantity,
        per_user_limit=data.per_user_limit,
    )
    db.add(fp)
    db.commit()
    db.refresh(fp)
    return fp


def toggle_flash_sale(db: Session, sale_id: str) -> FlashSale:
    sale = db.query(FlashSale).filter(FlashSale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Flash sale not found")
    sale.is_active = not sale.is_active
    db.commit()
    db.refresh(sale)
    return sale


# ─── Banner ───────────────────────────────────────────────────────────────────

def get_banners_by_position(db: Session, position: str) -> List[Banner]:
    now = datetime.now(timezone.utc)
    return db.query(Banner).filter(
        Banner.position == position,
        Banner.is_active == True,
        (Banner.starts_at == None) | (Banner.starts_at <= now),
        (Banner.ends_at == None) | (Banner.ends_at >= now),
    ).order_by(Banner.display_order).all()


def get_all_banners(db: Session) -> List[Banner]:
    return db.query(Banner).order_by(
        Banner.position, Banner.display_order
    ).all()


def create_banner(db: Session, data: BannerCreate, admin_id: str) -> Banner:
    banner = Banner(
        created_by=admin_id,
        **data.model_dump()
    )
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return banner


def update_banner(db: Session, banner_id: str, data: BannerUpdate) -> Banner:
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(banner, field, value)

    db.commit()
    db.refresh(banner)
    return banner


def delete_banner(db: Session, banner_id: str) -> None:
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    db.delete(banner)
    db.commit()


# ─── Homepage ─────────────────────────────────────────────────────────────────

def get_homepage_data(db: Session) -> dict:
    from app.models.product import Product

    featured_products_raw = db.query(Product).filter(
        Product.is_featured == True,
        Product.status == "active",
    ).limit(10).all()

    featured = []
    for p in featured_products_raw:
        featured.append({
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "mrp": p.mrp,
            "selling_price": p.selling_price,
            "discount_percent": p.discount_percent,
            "rating_avg": p.rating_avg,
            "primary_image": p.images[0].image_url if p.images else None,
        })

    return {
        "hero_banners": get_banners_by_position(db, "hero"),
        "mid_banners": get_banners_by_position(db, "mid_page"),
        "deals_banners": get_banners_by_position(db, "deals_of_day"),
        "active_flash_sales": get_active_flash_sales(db),
        "featured_products": featured,
    }