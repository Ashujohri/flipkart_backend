from pydantic import BaseModel, field_validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


# ─── Cart Item ────────────────────────────────────────────────────────────────

class CartItemAdd(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = 1

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError("Quantity must be at least 1")
        if v > 10:
            raise ValueError("Maximum 10 items allowed per product")
        return v


class CartItemUpdate(BaseModel):
    quantity: int

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError("Quantity must be at least 1")
        if v > 10:
            raise ValueError("Maximum 10 items allowed per product")
        return v


class CartItemResponse(BaseModel):
    id: str
    product_id: str
    variant_id: Optional[str] = None
    quantity: int
    saved_price: Decimal
    product_name: Optional[str] = None
    product_image: Optional[str] = None
    mrp: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    discount_percent: Optional[float] = None
    is_available: bool = True
    stock_left: Optional[int] = None

    model_config = {"from_attributes": True}


# ─── Coupon ───────────────────────────────────────────────────────────────────

class ApplyCouponRequest(BaseModel):
    code: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        v = v.strip().upper()
        if len(v) < 3:
            raise ValueError("Invalid coupon code")
        return v


# ─── Cart Response ────────────────────────────────────────────────────────────

class CartSummary(BaseModel):
    subtotal: Decimal
    total_discount: Decimal
    coupon_discount: Decimal
    delivery_charge: Decimal
    total_amount: Decimal
    total_saved: Decimal
    item_count: int


class CartResponse(BaseModel):
    id: str
    items: List[CartItemResponse] = []
    coupon_code: Optional[str] = None
    coupon_discount: Decimal = Decimal("0.00")
    summary: CartSummary

    model_config = {"from_attributes": True}