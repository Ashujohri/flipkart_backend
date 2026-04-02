from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import Optional, List
from decimal import Decimal

from app.models.product import Product, Category, Brand, Inventory
from app.schemas.search import SearchFilters


def search_products(
    db: Session,
    query: str,
    filters: SearchFilters,
    page: int = 1,
    per_page: int = 20,
    sort_by: str = "relevance",
) -> dict:
    base_query = db.query(Product).filter(
        Product.status == "active",
        or_(
            Product.name.ilike(f"%{query}%"),
            Product.description.ilike(f"%{query}%"),
            Product.tags.cast(db.bind.dialect.name == "mysql" and
                              __import__('sqlalchemy').String or
                              __import__('sqlalchemy').String).ilike(f"%{query}%"),
        )
    )

    # filters apply karo
    if filters.category_id:
        base_query = base_query.filter(Product.category_id == filters.category_id)

    if filters.brand_id:
        base_query = base_query.filter(Product.brand_id == filters.brand_id)

    if filters.min_price:
        base_query = base_query.filter(Product.selling_price >= filters.min_price)

    if filters.max_price:
        base_query = base_query.filter(Product.selling_price <= filters.max_price)

    if filters.min_rating:
        base_query = base_query.filter(Product.rating_avg >= filters.min_rating)

    if filters.is_cod_available is not None:
        base_query = base_query.filter(Product.is_cod_available == filters.is_cod_available)

    if filters.discount_min:
        base_query = base_query.filter(Product.discount_percent >= filters.discount_min)

    if filters.in_stock_only:
        base_query = base_query.join(Inventory).filter(
            Inventory.available_stock > 0
        )

    # sorting
    if sort_by == "price_low":
        base_query = base_query.order_by(Product.selling_price.asc())
    elif sort_by == "price_high":
        base_query = base_query.order_by(Product.selling_price.desc())
    elif sort_by == "rating":
        base_query = base_query.order_by(Product.rating_avg.desc())
    elif sort_by == "discount":
        base_query = base_query.order_by(Product.discount_percent.desc())
    elif sort_by == "newest":
        base_query = base_query.order_by(Product.created_at.desc())
    else:
        # relevance — rating + rating_count
        base_query = base_query.order_by(
            Product.rating_count.desc(),
            Product.rating_avg.desc(),
        )

    total = base_query.count()
    products = base_query.offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for product in products:
        items.append({
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "mrp": product.mrp,
            "selling_price": product.selling_price,
            "discount_percent": product.discount_percent,
            "rating_avg": product.rating_avg,
            "rating_count": product.rating_count,
            "is_cod_available": product.is_cod_available,
            "primary_image": product.images[0].image_url if product.images else None,
            "brand_name": product.brand.name if product.brand else None,
            "category_name": product.category.name if product.category else None,
        })

    filters_applied = {k: v for k, v in filters.model_dump().items() if v is not None}

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "query": query,
        "filters_applied": filters_applied,
    }


def get_suggestions(db: Session, query: str, limit: int = 8) -> List[str]:
    if len(query) < 2:
        return []

    products = db.query(Product.name).filter(
        Product.status == "active",
        Product.name.ilike(f"{query}%"),
    ).limit(limit).all()

    return [p.name for p in products]