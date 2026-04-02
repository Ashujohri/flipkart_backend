from pydantic import BaseModel, field_validator
from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal


# ─── Category ─────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    icon_url: Optional[str] = None
    parent_id: Optional[str] = None
    display_order: int = 0
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v):
        import re
        v = v.strip().lower()
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError("Slug can only contain lowercase letters, numbers and hyphens")
        return v


class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    icon_url: Optional[str] = None
    parent_id: Optional[str] = None
    level: int
    is_active: bool
    display_order: int
    children: List["CategoryResponse"] = []

    model_config = {"from_attributes": True}

CategoryResponse.model_rebuild()


class CategorySimple(BaseModel):
    id: str
    name: str
    slug: str
    level: int

    model_config = {"from_attributes": True}


# ─── Brand ────────────────────────────────────────────────────────────────────

class BrandCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v


class BrandResponse(BaseModel):
    id: str
    name: str
    slug: str
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    is_active: bool
    is_verified: bool

    model_config = {"from_attributes": True}


# ─── Product ──────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    highlights: Optional[List[str]] = None
    category_id: Optional[str] = None
    brand_id: Optional[str] = None
    mrp: Decimal
    selling_price: Decimal
    condition: str = "new"
    is_returnable: bool = True
    return_days: int = 7
    is_cod_available: bool = True
    warranty_summary: Optional[str] = None
    warranty_details: Optional[str] = None
    tags: Optional[List[str]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

    @field_validator("mrp", "selling_price")
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v

    @field_validator("selling_price")
    @classmethod
    def validate_selling_price(cls, v, info):
        if hasattr(info, 'data') and 'mrp' in info.data:
            if v > info.data['mrp']:
                raise ValueError("Selling price cannot be greater than MRP")
        return v

    @field_validator("return_days")
    @classmethod
    def validate_return_days(cls, v):
        if v not in [0, 7, 10, 15, 30]:
            raise ValueError("Return days must be 0, 7, 10, 15 or 30")
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    highlights: Optional[List[str]] = None
    selling_price: Optional[Decimal] = None
    is_returnable: Optional[bool] = None
    return_days: Optional[int] = None
    is_cod_available: Optional[bool] = None
    is_featured: Optional[bool] = None
    warranty_summary: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


# ─── Product Variant ──────────────────────────────────────────────────────────

class VariantCreate(BaseModel):
    name: str
    value: str
    sku: str
    mrp: Decimal
    selling_price: Decimal
    stock: int = 0

    @field_validator("stock")
    @classmethod
    def validate_stock(cls, v):
        if v < 0:
            raise ValueError("Stock cannot be negative")
        return v


class VariantResponse(BaseModel):
    id: str
    name: str
    value: str
    sku: str
    mrp: Decimal
    selling_price: Decimal
    stock: int
    is_active: bool

    model_config = {"from_attributes": True}


# ─── Product Specification ────────────────────────────────────────────────────

class SpecificationCreate(BaseModel):
    group_name: str
    key: str
    value: str
    display_order: int = 0


class SpecificationResponse(BaseModel):
    id: str
    group_name: str
    key: str
    value: str
    display_order: int

    model_config = {"from_attributes": True}


# ─── Product Image ────────────────────────────────────────────────────────────

class ProductImageResponse(BaseModel):
    id: str
    image_url: str
    thumbnail_url: Optional[str] = None
    alt_text: Optional[str] = None
    display_order: int
    is_primary: bool

    model_config = {"from_attributes": True}


# ─── Inventory ────────────────────────────────────────────────────────────────

class InventoryUpdate(BaseModel):
    total_stock: int
    low_stock_threshold: int = 10
    warehouse_location: Optional[str] = None

    @field_validator("total_stock")
    @classmethod
    def validate_stock(cls, v):
        if v < 0:
            raise ValueError("Stock cannot be negative")
        return v


class InventoryResponse(BaseModel):
    total_stock: int
    reserved_stock: int
    available_stock: int
    low_stock_threshold: int
    warehouse_location: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Product Response ─────────────────────────────────────────────────────────

class ProductResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    highlights: Optional[List[str]] = None
    mrp: Decimal
    selling_price: Decimal
    discount_percent: float
    condition: str
    status: str
    is_returnable: bool
    return_days: int
    is_cod_available: bool
    is_featured: bool
    rating_avg: float
    rating_count: int
    warranty_summary: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[CategorySimple] = None
    brand: Optional[BrandResponse] = None
    variants: List[VariantResponse] = []
    images: List[ProductImageResponse] = []
    specifications: List[SpecificationResponse] = []
    inventory: Optional[InventoryResponse] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    id: str
    name: str
    slug: str
    mrp: Decimal
    selling_price: Decimal
    discount_percent: float
    rating_avg: float
    rating_count: int
    is_cod_available: bool
    status: str
    primary_image: Optional[str] = None
    category: Optional[CategorySimple] = None
    brand: Optional[BrandResponse] = None

    model_config = {"from_attributes": True}


# ─── Pagination ───────────────────────────────────────────────────────────────

class PaginatedProducts(BaseModel):
    items: List[ProductListResponse]
    total: int
    page: int
    per_page: int
    pages: int