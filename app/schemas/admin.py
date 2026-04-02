from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "moderator"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        allowed = ["superadmin", "admin", "moderator", "seller_manager",
                   "order_manager", "content_manager", "finance_manager"]
        if v not in allowed:
            raise ValueError(f"Invalid role")
        return v


class AdminUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedUsers(BaseModel):
    items: List[UserListResponse]
    total: int
    page: int
    per_page: int
    pages: int


class SellerApprovalRequest(BaseModel):
    action: str
    reason: Optional[str] = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if v not in ["approve", "suspend", "ban"]:
            raise ValueError("Action must be approve, suspend or ban")
        return v


class DisputeAssignRequest(BaseModel):
    admin_id: str


class DisputeResolveRequest(BaseModel):
    resolution: str

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, v):
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Resolution must be at least 10 characters")
        return v


class PlatformStats(BaseModel):
    total_users: int
    total_sellers: int
    total_products: int
    total_orders: int
    total_revenue: Decimal
    today_orders: int
    today_revenue: Decimal
    pending_disputes: int
    pending_seller_approvals: int