from sqlalchemy import (
    Column, String, Boolean, Enum, Text,
    ForeignKey, DateTime, Integer, Float,
    Numeric, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum


def generate_uuid():
    return str(uuid.uuid4())


# ─── Enums ────────────────────────────────────────────────────────────────────

class DiscountType(enum.Enum):
    percentage  = "percentage"
    flat        = "flat"

class CouponType(enum.Enum):
    public      = "public"
    private     = "private"
    referral    = "referral"

class CouponApplicableOn(enum.Enum):
    all             = "all"
    specific_products = "specific_products"
    specific_categories = "specific_categories"
    specific_brands = "specific_brands"

class BannerPosition(enum.Enum):
    hero            = "hero"
    mid_page        = "mid_page"
    sidebar         = "sidebar"
    category_top    = "category_top"
    deals_of_day    = "deals_of_day"


# ─── Coupon ───────────────────────────────────────────────────────────────────

class Coupon(Base):
    __tablename__ = "coupons"

    id                  = Column(String(36), primary_key=True, default=generate_uuid)
    code                = Column(String(20), unique=True, nullable=False, index=True)
    title               = Column(String(255), nullable=False)
    description         = Column(Text, nullable=True)
    coupon_type         = Column(Enum(CouponType), default=CouponType.public, nullable=False)
    discount_type       = Column(Enum(DiscountType), nullable=False)
    discount_value      = Column(Numeric(10, 2), nullable=False)
    max_discount_amount = Column(Numeric(10, 2), nullable=True)
    min_order_amount    = Column(Numeric(10, 2), default=0.00, nullable=False)
    applicable_on       = Column(Enum(CouponApplicableOn), default=CouponApplicableOn.all)
    applicable_ids      = Column(JSON, nullable=True)
    total_usage_limit   = Column(Integer, nullable=True)
    per_user_limit      = Column(Integer, default=1, nullable=False)
    used_count          = Column(Integer, default=0, nullable=False)
    is_active           = Column(Boolean, default=True, nullable=False)
    valid_from          = Column(DateTime, nullable=False)
    valid_until         = Column(DateTime, nullable=False)
    created_by          = Column(String(36), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    created_at          = Column(DateTime, server_default=func.now())
    updated_at          = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    usage = relationship("CouponUsage", back_populates="coupon", cascade="all, delete-orphan")


# ─── Coupon Usage ─────────────────────────────────────────────────────────────

class CouponUsage(Base):
    __tablename__ = "coupon_usage"

    id              = Column(String(36), primary_key=True, default=generate_uuid)
    coupon_id       = Column(String(36), ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id         = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id        = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    discount_given  = Column(Numeric(10, 2), nullable=False)
    used_at         = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("coupon_id", "order_id", name="unique_coupon_order"),
    )

    # Relationships
    coupon  = relationship("Coupon", back_populates="usage")
    user    = relationship("User")


# ─── Flash Sale ───────────────────────────────────────────────────────────────

class FlashSale(Base):
    __tablename__ = "flash_sales"

    id              = Column(String(36), primary_key=True, default=generate_uuid)
    title           = Column(String(255), nullable=False)
    description     = Column(Text, nullable=True)
    banner_url      = Column(String(500), nullable=True)
    starts_at       = Column(DateTime, nullable=False)
    ends_at         = Column(DateTime, nullable=False)
    is_active       = Column(Boolean, default=True, nullable=False)
    created_by      = Column(String(36), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    created_at      = Column(DateTime, server_default=func.now())
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    products = relationship("FlashSaleProduct", back_populates="flash_sale", cascade="all, delete-orphan")


# ─── Flash Sale Product ───────────────────────────────────────────────────────

class FlashSaleProduct(Base):
    __tablename__ = "flash_sale_products"

    id                  = Column(String(36), primary_key=True, default=generate_uuid)
    flash_sale_id       = Column(String(36), ForeignKey("flash_sales.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id          = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id          = Column(String(36), ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    sale_price          = Column(Numeric(12, 2), nullable=False)
    original_price      = Column(Numeric(12, 2), nullable=False)
    discount_percent    = Column(Float, nullable=False)
    total_quantity      = Column(Integer, nullable=False)
    sold_quantity       = Column(Integer, default=0, nullable=False)
    per_user_limit      = Column(Integer, default=1, nullable=False)
    is_active           = Column(Boolean, default=True, nullable=False)
    created_at          = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("flash_sale_id", "product_id", name="unique_flash_sale_product"),
    )

    # Relationships
    flash_sale  = relationship("FlashSale", back_populates="products")
    product     = relationship("Product")
    variant     = relationship("ProductVariant")


# ─── Banner ───────────────────────────────────────────────────────────────────

class Banner(Base):
    __tablename__ = "banners"

    id              = Column(String(36), primary_key=True, default=generate_uuid)
    title           = Column(String(255), nullable=False)
    subtitle        = Column(String(255), nullable=True)
    image_url       = Column(String(500), nullable=False)
    mobile_image_url = Column(String(500), nullable=True)
    redirect_url    = Column(String(500), nullable=True)
    position        = Column(Enum(BannerPosition), nullable=False)
    display_order   = Column(Integer, default=0, nullable=False)
    is_active       = Column(Boolean, default=True, nullable=False)
    starts_at       = Column(DateTime, nullable=True)
    ends_at         = Column(DateTime, nullable=True)
    target_category_id = Column(String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    created_by      = Column(String(36), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    created_at      = Column(DateTime, server_default=func.now())
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    category = relationship("Category")