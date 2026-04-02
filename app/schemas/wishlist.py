from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


class WishlistItemAdd(BaseModel):
    product_id: str
    variant_id: Optional[str] = None


class WishlistCreate(BaseModel):
    name: str = "My Wishlist"
    is_public: bool = False


class WishlistItemResponse(BaseModel):
    id: str
    product_id: str
    variant_id: Optional[str] = None
    product_name: Optional[str] = None
    product_image: Optional[str] = None
    mrp: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    discount_percent: Optional[float] = None
    is_available: bool = True
    added_at: datetime

    model_config = {"from_attributes": True}


class WishlistResponse(BaseModel):
    id: str
    name: str
    is_public: bool
    item_count: int
    items: List[WishlistItemResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}