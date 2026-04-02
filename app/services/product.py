from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc
from fastapi import HTTPException, status
from typing import List, Optional
from decimal import Decimal

from app.models.product import (
    Product, Category, Brand,
    ProductVariant, ProductImage,
    ProductSpecification, Inventory,
)
from app.schemas.product import (
    ProductCreate, ProductUpdate,
    CategoryCreate, BrandCreate,
    VariantCreate, SpecificationCreate,
    InventoryUpdate,
)


# ─── Category ─────────────────────────────────────────────────────────────────

def get_all_categories(db: Session) -> List[Category]:
    return db.query(Category).filter(
        Category.is_active == True,
        Category.parent_id == None,
    ).order_by(Category.display_order).all()


def get_category_by_slug(db: Session, slug: str) -> Category:
    category = db.query(Category).filter(Category.slug == slug).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


def create_category(db: Session, data: CategoryCreate) -> Category:
    existing = db.query(Category).filter(Category.slug == data.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Category slug already exists")

    level = 1
    if data.parent_id:
        parent = db.query(Category).filter(Category.id == data.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent category not found")
        level = parent.level + 1

    category = Category(**data.model_dump(), level=level)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# ─── Brand ────────────────────────────────────────────────────────────────────

def get_all_brands(db: Session) -> List[Brand]:
    return db.query(Brand).filter(Brand.is_active == True).order_by(Brand.name).all()


def create_brand(db: Session, data: BrandCreate) -> Brand:
    existing = db.query(Brand).filter(Brand.slug == data.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Brand slug already exists")

    brand = Brand(**data.model_dump())
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


# ─── Product ──────────────────────────────────────────────────────────────────

def get_products(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    category_id: Optional[str] = None,
    brand_id: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> dict:
    query = db.query(Product).filter(Product.status == "active")

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if brand_id:
        query = query.filter(Product.brand_id == brand_id)

    if min_price:
        query = query.filter(Product.selling_price >= min_price)

    if max_price:
        query = query.filter(Product.selling_price <= max_price)

    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
            )
        )

    # sorting
    sort_column = getattr(Product, sort_by, Product.created_at)
    if sort_order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


def get_product_by_id(db: Session, product_id: str) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def get_product_by_slug(db: Session, slug: str) -> Product:
    product = db.query(Product).filter(Product.slug == slug).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def create_product(db: Session, seller_id: str, data: ProductCreate) -> Product:
    existing = db.query(Product).filter(Product.slug == data.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Product slug already exists")

    # discount calculate karo
    discount = 0.0
    if data.mrp > 0:
        discount = float(((data.mrp - data.selling_price) / data.mrp) * 100)

    product = Product(
        seller_id=seller_id,
        discount_percent=round(discount, 2),
        **data.model_dump()
    )

    db.add(product)
    db.flush()  # ID generate ho jaaye — inventory ke liye chahiye

    # inventory banao
    inventory = Inventory(
        product_id=product.id,
        total_stock=0,
        reserved_stock=0,
        available_stock=0,
    )
    db.add(inventory)
    db.commit()
    db.refresh(product)
    return product


def update_product(
    db: Session,
    product_id: str,
    seller_id: str,
    data: ProductUpdate
) -> Product:
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.seller_id == seller_id,
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = data.model_dump(exclude_unset=True)

    # selling_price update hua toh discount recalculate karo
    if "selling_price" in update_data:
        new_price = update_data["selling_price"]
        discount = float(((product.mrp - new_price) / product.mrp) * 100)
        update_data["discount_percent"] = round(discount, 2)

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: str, seller_id: str) -> None:
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.seller_id == seller_id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.status = "inactive"
    db.commit()


# ─── Variants ─────────────────────────────────────────────────────────────────

def add_variant(
    db: Session,
    product_id: str,
    seller_id: str,
    data: VariantCreate
) -> ProductVariant:
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.seller_id == seller_id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing_sku = db.query(ProductVariant).filter(
        ProductVariant.sku == data.sku
    ).first()
    if existing_sku:
        raise HTTPException(status_code=409, detail="SKU already exists")

    variant = ProductVariant(product_id=product_id, **data.model_dump())
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


# ─── Images ───────────────────────────────────────────────────────────────────

def add_product_image(
    db: Session,
    product_id: str,
    image_url: str,
    is_primary: bool = False,
    alt_text: Optional[str] = None,
) -> ProductImage:
    if is_primary:
        db.query(ProductImage).filter(
            ProductImage.product_id == product_id,
            ProductImage.is_primary == True,
        ).update({"is_primary": False})

    count = db.query(ProductImage).filter(
        ProductImage.product_id == product_id
    ).count()

    image = ProductImage(
        product_id=product_id,
        image_url=image_url,
        is_primary=is_primary if count > 0 else True,
        alt_text=alt_text,
        display_order=count,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def delete_product_image(db: Session, image_id: str, product_id: str) -> None:
    image = db.query(ProductImage).filter(
        ProductImage.id == image_id,
        ProductImage.product_id == product_id,
    ).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    db.delete(image)
    db.commit()


# ─── Specifications ───────────────────────────────────────────────────────────

def add_specification(
    db: Session,
    product_id: str,
    data: SpecificationCreate
) -> ProductSpecification:
    spec = ProductSpecification(product_id=product_id, **data.model_dump())
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


def delete_specification(db: Session, spec_id: str, product_id: str) -> None:
    spec = db.query(ProductSpecification).filter(
        ProductSpecification.id == spec_id,
        ProductSpecification.product_id == product_id,
    ).first()
    if not spec:
        raise HTTPException(status_code=404, detail="Specification not found")
    db.delete(spec)
    db.commit()


# ─── Inventory ────────────────────────────────────────────────────────────────

def update_inventory(
    db: Session,
    product_id: str,
    seller_id: str,
    data: InventoryUpdate
) -> Inventory:
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.seller_id == seller_id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    inventory = db.query(Inventory).filter(
        Inventory.product_id == product_id
    ).first()

    inventory.total_stock = data.total_stock
    inventory.available_stock = data.total_stock - inventory.reserved_stock
    inventory.low_stock_threshold = data.low_stock_threshold
    inventory.warehouse_location = data.warehouse_location

    # product status update
    if inventory.available_stock <= 0:
        product.status = "out_of_stock"
    elif product.status == "out_of_stock":
        product.status = "active"

    db.commit()
    db.refresh(inventory)
    return inventory