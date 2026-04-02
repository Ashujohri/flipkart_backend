from pydantic import BaseModel, field_validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


# ─── Payment Initiate ─────────────────────────────────────────────────────────

class InitiatePaymentRequest(BaseModel):
    order_id: str
    gateway: str = "razorpay"

    @field_validator("gateway")
    @classmethod
    def validate_gateway(cls, v):
        allowed = ["razorpay", "paytm", "phonepe", "wallet"]
        if v not in allowed:
            raise ValueError(f"Invalid gateway. Allowed: {', '.join(allowed)}")
        return v


class InitiatePaymentResponse(BaseModel):
    payment_id: str
    gateway_order_id: str
    amount: Decimal
    currency: str
    gateway: str
    key_id: str


# ─── Payment Verify ───────────────────────────────────────────────────────────

class VerifyPaymentRequest(BaseModel):
    order_id: str
    gateway_order_id: str
    gateway_payment_id: str
    gateway_signature: str


# ─── Payment Response ─────────────────────────────────────────────────────────

class PaymentResponse(BaseModel):
    id: str
    order_id: str
    gateway: str
    status: str
    amount: Decimal
    currency: str
    gateway_order_id: Optional[str] = None
    gateway_payment_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Refund ───────────────────────────────────────────────────────────────────

class RefundResponse(BaseModel):
    id: str
    payment_id: str
    order_id: str
    amount: Decimal
    status: str
    refund_to: str
    gateway_refund_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Wallet ───────────────────────────────────────────────────────────────────

class WalletResponse(BaseModel):
    id: str
    balance: Decimal
    is_active: bool

    model_config = {"from_attributes": True}


class WalletTransactionResponse(BaseModel):
    id: str
    type: str
    reason: str
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedWalletTransactions(BaseModel):
    items: List[WalletTransactionResponse]
    total: int
    page: int
    per_page: int
    pages: int


# ─── Payment Method ───────────────────────────────────────────────────────────

class PaymentMethodResponse(BaseModel):
    id: str
    gateway: str
    card_type: Optional[str] = None
    card_last4: Optional[str] = None
    card_brand: Optional[str] = None
    card_expiry: Optional[str] = None
    upi_id: Optional[str] = None
    bank_name: Optional[str] = None
    is_default: bool

    model_config = {"from_attributes": True}