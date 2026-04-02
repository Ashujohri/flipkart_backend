from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_seller
from app.models.user import User
from app.schemas.seller import (
    SellerRegister,
    SellerUpdate,
    SellerResponse,
    SellerDashboard,
    BankDetailsCreate,
    BankDetailsResponse,
    PayoutResponse,
    PaginatedPayouts,
    AnalyticsResponse,
)
from app.services import seller as seller_service

router = APIRouter(prefix="/seller", tags=["Seller"])


# ─── Register ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=SellerResponse, status_code=status.HTTP_201_CREATED)
def register_seller(
    data: SellerRegister,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return seller_service.register_seller(db, current_user.id, data)


# ─── Profile ──────────────────────────────────────────────────────────────────

@router.get("/profile", response_model=SellerResponse)
def get_seller_profile(
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    return seller_service.get_seller_by_user_id(db, current_user.id)


@router.patch("/profile", response_model=SellerResponse)
def update_seller_profile(
    data: SellerUpdate,
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    return seller_service.update_seller(db, current_user.id, data)


# ─── Dashboard ────────────────────────────────────────────────────────────────

@router.get("/dashboard")
def get_dashboard(
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    return seller_service.get_seller_dashboard(db, current_user.id)


# ─── Orders ───────────────────────────────────────────────────────────────────

@router.get("/orders")
def get_seller_orders(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    return seller_service.get_seller_orders(
        db, current_user.id, page, per_page, status_filter
    )


# ─── Bank Details ─────────────────────────────────────────────────────────────

@router.post("/bank-details", response_model=BankDetailsResponse, status_code=status.HTTP_201_CREATED)
def add_bank_details(
    data: BankDetailsCreate,
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    return seller_service.add_bank_details(db, current_user.id, data)


@router.get("/bank-details", response_model=BankDetailsResponse)
def get_bank_details(
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    return seller_service.get_bank_details(db, current_user.id)


# ─── Payouts ──────────────────────────────────────────────────────────────────

@router.get("/payouts", response_model=PaginatedPayouts)
def get_payouts(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    return seller_service.get_payouts(db, current_user.id, page, per_page)


# ─── Analytics ────────────────────────────────────────────────────────────────

@router.get("/analytics")
def get_analytics(
    period: str = Query(default="monthly"),
    limit: int = Query(default=12, ge=1, le=24),
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    return seller_service.get_analytics(db, current_user.id, period, limit)