from pydantic import BaseModel, field_validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


# ─── Place Order ──────────────────────────────────────────────────────────────

class PlaceOrderRequest(BaseModel):
    address_id: str
    payment_mode: str
    delivery_instructions: Optional[str] = None

    @field_validator("payment_mode")
    @classmethod
    def validate_payment_mode(cls, v):
        allowed = ["cod", "upi", "credit_card", "debit_card", "net_banking", "emi", "wallet", "pay_later"]
        if v not in allowed:
            raise ValueError(f"Invalid payment mode. Allowed: {', '.join(allowed)}")
        return v


# ─── Cancel Order ─────────────────────────────────────────────────────────────

class CancelOrderRequest(BaseModel):
    reason: str

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v):
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Please provide a valid cancellation reason")
        return v


# ─── Return Order ─────────────────────────────────────────────────────────────

class ReturnItemRequest(BaseModel):
    order_item_id: str
    quantity: int
    condition: Optional[str] = None
    images: Optional[List[str]] = None


class ReturnOrderRequest(BaseModel):
    reason: str
    description: Optional[str] = None
    pickup_address_id: Optional[str] = None
    items: List[ReturnItemRequest]

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v):
        allowed = [
            "defective", "wrong_item", "not_as_described",
            "damaged_in_shipping", "changed_mind",
            "size_issue", "quality_issue", "other"
        ]
        if v not in allowed:
            raise ValueError(f"Invalid return reason")
        return v


# ─── Responses ────────────────────────────────────────────────────────────────

class OrderItemResponse(BaseModel):
    id: str
    product_id: Optional[str] = None
    product_name: str
    product_image_url: Optional[str] = None
    variant_name: Optional[str] = None
    sku: Optional[str] = None
    quantity: int
    mrp: Decimal
    selling_price: Decimal
    discount_amount: Decimal
    total_price: Decimal
    is_reviewed: bool

    model_config = {"from_attributes": True}


class OrderStatusHistoryResponse(BaseModel):
    id: str
    status: str
    message: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: str
    order_number: str
    status: str
    payment_mode: str
    subtotal: Decimal
    discount_amount: Decimal
    coupon_discount: Decimal
    delivery_charge: Decimal
    total_amount: Decimal
    saved_amount: Decimal
    snapshot_address: dict
    delivery_instructions: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    items: List[OrderItemResponse] = []
    status_history: List[OrderStatusHistoryResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    id: str
    order_number: str
    status: str
    payment_mode: str
    total_amount: Decimal
    item_count: int
    created_at: datetime
    first_item_name: Optional[str] = None
    first_item_image: Optional[str] = None

    model_config = {"from_attributes": True}


class PaginatedOrders(BaseModel):
    items: List[OrderListResponse]
    total: int
    page: int
    per_page: int
    pages: int


# ─── Return Response ──────────────────────────────────────────────────────────

class ReturnItemResponse(BaseModel):
    id: str
    order_item_id: str
    quantity: int
    condition: Optional[str] = None

    model_config = {"from_attributes": True}


class ReturnResponse(BaseModel):
    id: str
    return_number: str
    reason: str
    description: Optional[str] = None
    status: str
    refund_amount: Optional[Decimal] = None
    pickup_scheduled_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    items: List[ReturnItemResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}