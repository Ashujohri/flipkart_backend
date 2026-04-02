from sqlalchemy import (Column, String, Boolean, Enum, Text, ForeignKey, DateTime, Integer, Float, Numeric, JSON)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum

def generate_uuid():
    return str(uuid.uuid4())

# ----------- Enums ---------------
class ProductStatus(enum.Enum):
    draft = "draft"
    active = "active"
    inactive = "inactive"
    out_of_stock = "out_of_stock"
    discontinued = "discontinued"

class ProductCondition(enum.Enum):
    new = "new"
    refurbished = "refurbished"
    used = "used"

#----------- Category -------------
class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    icon_url = Column(String(500), nullable=True)
    parent_id = Column(String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    level = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    #Self referencing relationship
    parent = relationship("Category", remote_side="Category.id", back_populates="children")
    children = relationship("Category", back_populates="parent")
    products = relationship("Product", back_populates="category")

#----------- Brands -------------
class Brand(Base):
    __tablename__ = "brands"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    website_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    #Relationships
    products = relationship("Product", back_populates="brand")

# ----------- Product -------------
class Product(Base):
    __tablename__ = "products"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    seller_id = Column(String(36), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    brand_id = Column(String(36), ForeignKey("brands.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(300), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    highlights = Column(JSON, nullable=True)
    mrp = Column(Numeric(12, 2), nullable=False)
    selling_price = Column(Numeric(12, 2), nullable=False)
    discount_percent = Column(Float, default=0.0, nullable=False)
    condition = Column(Enum(ProductCondition), default=ProductCondition.new)
    status = Column(Enum(ProductStatus), default=ProductStatus.draft)
    is_returnable = Column(Boolean, default=True, nullable=False)
    return_days = Column(Integer, default=7, nullable=False)
    is_cod_available = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    rating_avg = Column(Float, default=0.0, nullable=False)
    rating_count = Column(Integer, default=0, nullable=False)
    warranty_summary = Column(String(255), nullable=True)
    warranty_details = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    #Relationships
    seller = relationship("Seller", back_populates="products")
    category        = relationship("Category", back_populates="products")
    brand           = relationship("Brand", back_populates="products")
    variants        = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    images          = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    specifications  = relationship("ProductSpecification", back_populates="product", cascade="all, delete-orphan")
    inventory       = relationship("Inventory", back_populates="product", uselist=False, cascade="all, delete-orphan")
    reviews         = relationship("Review", back_populates="product")
    questions       = relationship("Question", back_populates="product")

# ─── Product Variant ──────────────────────────────────────────────────────────

class ProductVariant(Base):
    __tablename__ = "product_variants"

    id              = Column(String(36), primary_key=True, default=generate_uuid)
    product_id      = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    sku             = Column(String(100), unique=True, nullable=False, index=True)
    name            = Column(String(100), nullable=False)
    value           = Column(String(100), nullable=False)
    mrp             = Column(Numeric(12, 2), nullable=False)
    selling_price   = Column(Numeric(12, 2), nullable=False)
    stock           = Column(Integer, default=0, nullable=False)
    is_active       = Column(Boolean, default=True, nullable=False)
    created_at      = Column(DateTime, server_default=func.now())
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    product     = relationship("Product", back_populates="variants")
    cart_items  = relationship("CartItem", back_populates="variant")


# ─── Product Image ────────────────────────────────────────────────────────────

class ProductImage(Base):
    __tablename__ = "product_images"

    id              = Column(String(36), primary_key=True, default=generate_uuid)
    product_id      = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url       = Column(String(500), nullable=False)
    thumbnail_url   = Column(String(500), nullable=True)
    alt_text        = Column(String(255), nullable=True)
    display_order   = Column(Integer, default=0, nullable=False)
    is_primary      = Column(Boolean, default=False, nullable=False)
    created_at      = Column(DateTime, server_default=func.now())

    # Relationships
    product = relationship("Product", back_populates="images")


# ─── Product Specification ────────────────────────────────────────────────────

class ProductSpecification(Base):
    __tablename__ = "product_specifications"

    id          = Column(String(36), primary_key=True, default=generate_uuid)
    product_id  = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    group_name  = Column(String(100), nullable=False)
    key         = Column(String(100), nullable=False)
    value       = Column(String(500), nullable=False)
    display_order = Column(Integer, default=0, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="specifications")


# ─── Inventory ────────────────────────────────────────────────────────────────

class Inventory(Base):
    __tablename__ = "inventory"

    id                  = Column(String(36), primary_key=True, default=generate_uuid)
    product_id          = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_stock         = Column(Integer, default=0, nullable=False)
    reserved_stock      = Column(Integer, default=0, nullable=False)
    available_stock     = Column(Integer, default=0, nullable=False)
    low_stock_threshold = Column(Integer, default=10, nullable=False)
    warehouse_location  = Column(String(100), nullable=True)
    updated_at          = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    product = relationship("Product", back_populates="inventory")


# ─── Cart ─────────────────────────────────────────────────────────────────────

class Cart(Base):
    __tablename__ = "carts"

    id          = Column(String(36), primary_key=True, default=generate_uuid)
    user_id     = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    coupon_id   = Column(String(36), ForeignKey("coupons.id", ondelete="SET NULL"), nullable=True)
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user    = relationship("User", back_populates="cart")
    items   = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    coupon  = relationship("Coupon")


# ─── Cart Item ────────────────────────────────────────────────────────────────

class CartItem(Base):
    __tablename__ = "cart_items"

    id          = Column(String(36), primary_key=True, default=generate_uuid)
    cart_id     = Column(String(36), ForeignKey("carts.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id  = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    variant_id  = Column(String(36), ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    quantity    = Column(Integer, default=1, nullable=False)
    saved_price = Column(Numeric(12, 2), nullable=False)
    added_at    = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    cart        = relationship("Cart", back_populates="items")
    product     = relationship("Product")
    variant     = relationship("ProductVariant", back_populates="cart_items")