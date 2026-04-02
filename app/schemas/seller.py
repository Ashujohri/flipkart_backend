from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime, date
import re


# ─── Seller Register ──────────────────────────────────────────────────────────

class SellerRegister(BaseModel):
    business_name: str
    business_type: Optional[str] = None
    business_email: EmailStr
    business_phone: str
    business_address: str
    business_city: str
    business_state: str
    business_pincode: str
    gstin: Optional[str] = None
    pan_number: Optional[str] = None

    @field_validator("business_name")
    @classmethod
    def validate_business_name(cls, v):
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Business name must be at least 3 characters")
        return v

    @field_validator("business_phone")
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r'^[6-9]\d{9}$', v):
            raise ValueError("Enter a valid 10 digit Indian mobile number")
        return v

    @field_validator("business_pincode")
    @classmethod
    def validate_pincode(cls, v):
        if not re.match(r'^\d{6}$', v):
            raise ValueError("Pincode must be 6 digits")
        return v

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v):
        if v is None:
            return v
        v = v.strip().upper()
        if not re.match(r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$', v):
            raise ValueError("Invalid GSTIN format")
        return v

    @field_validator("pan_number")
    @classmethod
    def validate_pan(cls, v):
        if v is None:
            return v
        v = v.strip().upper()
        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', v):
            raise ValueError("Invalid PAN format")
        return v


class SellerUpdate(BaseModel):
    business_name: Optional[str] = None
    business_phone: Optional[str] = None
    business_address: Optional[str] = None
    business_city: Optional[str] = None
    business_state: Optional[str] = None
    business_pincode: Optional[str] = None
    support_email: Optional[EmailStr] = None
    support_phone: Optional[str] = None
    pickup_address: Optional[str] = None
    return_address: Optional[str] = None


# ─── Bank Details ─────────────────────────────────────────────────────────────

class BankDetailsCreate(BaseModel):
    account_holder_name: str
    account_number: str
    ifsc_code: str
    bank_name: str
    branch_name: Optional[str] = None
    account_type: str = "savings"

    @field_validator("ifsc_code")
    @classmethod
    def validate_ifsc(cls, v):
        v = v.strip().upper()
        if not re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', v):
            raise ValueError("Invalid IFSC code format")
        return v

    @field_validator("account_number")
    @classmethod
    def validate_account(cls, v):
        v = v.strip()
        if not re.match(r'^\d{9,18}$', v):
            raise ValueError("Invalid account number")
        return v

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, v):
        if v not in ["savings", "current"]:
            raise ValueError("Account type must be savings or current")
        return v


# ─── Responses ────────────────────────────────────────────────────────────────

class BankDetailsResponse(BaseModel):
    id: str
    account_holder_name: str
    account_number: str
    ifsc_code: str
    bank_name: str
    branch_name: Optional[str] = None
    account_type: str
    is_verified: bool

    model_config = {"from_attributes": True}


class SellerResponse(BaseModel):
    id: str
    user_id: str
    business_name: str
    business_type: Optional[str] = None
    business_email: str
    business_phone: str
    business_city: str
    business_state: str
    gstin: Optional[str] = None
    status: str
    is_verified: bool
    rating_avg: float
    rating_count: int
    total_sales: Decimal
    commission_rate: float
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SellerDashboard(BaseModel):
    seller: SellerResponse
    today_orders: int
    today_revenue: Decimal
    pending_orders: int
    total_products: int
    low_stock_products: int
    pending_payouts: Decimal
    recent_orders: list


class PayoutResponse(BaseModel):
    id: str
    amount: Decimal
    commission_deducted: Decimal
    tds_deducted: Decimal
    net_amount: Decimal
    status: str
    utr_number: Optional[str] = None
    payout_date: Optional[datetime] = None
    period_start: date
    period_end: date
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalyticsResponse(BaseModel):
    period: str
    period_date: date
    total_orders: int
    total_revenue: Decimal
    total_units_sold: int
    total_returns: int
    total_cancelled: int
    avg_order_value: Decimal
    page_views: int
    conversion_rate: float

    model_config = {"from_attributes": True}


class PaginatedPayouts(BaseModel):
    items: List[PayoutResponse]
    total: int
    page: int
    per_page: int
    pages: int