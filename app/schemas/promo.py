from pydantic import BaseModel, field_validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


# ─── Flash Sale ───────────────────────────────────────────────────────────────

class FlashSaleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    banner_url: Optional[str] = None
    starts_at: datetime
    ends_at: datetime

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if len(v.strip()) < 3:
            raise ValueError("Title must be at least 3 characters")
        return v.strip()


class FlashSaleProductAdd(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    sale_price: Decimal
    total_quantity: int
    per_user_limit: int = 1

    @field_validator("sale_price")
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Sale price must be greater than 0")
        return v

    @field_validator("total_quantity")
    @classmethod
    def validate_qty(cls, v):
        if v < 1:
            raise ValueError("Quantity must be at least 1")
        return v


class FlashSaleProductResponse(BaseModel):
    id: str
    product_id: str
    sale_price: Decimal
    original_price: Decimal
    discount_percent: float
    total_quantity: int
    sold_quantity: int
    per_user_limit: int
    is_active: bool
    product_name: Optional[str] = None
    product_image: Optional[str] = None

    model_config = {"from_attributes": True}


class FlashSaleResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    banner_url: Optional[str] = None
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    is_live: bool = False
    products: List[FlashSaleProductResponse] = []

    model_config = {"from_attributes": True}


# ─── Banner ───────────────────────────────────────────────────────────────────

class BannerCreate(BaseModel):
    title: str
    subtitle: Optional[str] = None
    image_url: str
    mobile_image_url: Optional[str] = None
    redirect_url: Optional[str] = None
    position: str
    display_order: int = 0
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    target_category_id: Optional[str] = None

    @field_validator("position")
    @classmethod
    def validate_position(cls, v):
        allowed = ["hero", "mid_page", "sidebar", "category_top", "deals_of_day"]
        if v not in allowed:
            raise ValueError(f"Invalid position")
        return v


class BannerUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    image_url: Optional[str] = None
    redirect_url: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class BannerResponse(BaseModel):
    id: str
    title: str
    subtitle: Optional[str] = None
    image_url: str
    mobile_image_url: Optional[str] = None
    redirect_url: Optional[str] = None
    position: str
    display_order: int
    is_active: bool

    model_config = {"from_attributes": True}


# ─── Homepage ─────────────────────────────────────────────────────────────────

class HomepageResponse(BaseModel):
    hero_banners: List[BannerResponse]
    mid_banners: List[BannerResponse]
    deals_banners: List[BannerResponse]
    active_flash_sales: List[FlashSaleResponse]
    featured_products: list