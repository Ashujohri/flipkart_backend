from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.payment import (
    InitiatePaymentRequest,
    InitiatePaymentResponse,
    VerifyPaymentRequest,
    PaymentResponse,
    RefundResponse,
    WalletResponse,
    WalletTransactionResponse,
    PaginatedWalletTransactions,
    PaymentMethodResponse,
)
from app.services import payment as payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


# ─── Payment ──────────────────────────────────────────────────────────────────

@router.post("/initiate", response_model=InitiatePaymentResponse)
def initiate_payment(
    data: InitiatePaymentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return payment_service.initiate_payment(db, current_user.id, data)


@router.post("/verify", response_model=PaymentResponse)
def verify_payment(
    data: VerifyPaymentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return payment_service.verify_payment(db, current_user.id, data)


@router.get("/orders/{order_id}", response_model=PaymentResponse)
def get_payment(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return payment_service.get_payment_by_order(db, order_id, current_user.id)


# ─── Refund ───────────────────────────────────────────────────────────────────

@router.post("/orders/{order_id}/refund", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
def process_refund(
    order_id: str,
    refund_to: str = "wallet",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return payment_service.process_refund(db, order_id, current_user.id, refund_to)


# ─── Wallet ───────────────────────────────────────────────────────────────────

@router.get("/wallet", response_model=WalletResponse)
def get_wallet(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return payment_service.get_wallet(db, current_user.id)


@router.get("/wallet/transactions", response_model=PaginatedWalletTransactions)
def get_wallet_transactions(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return payment_service.get_wallet_transactions(
        db, current_user.id, page, per_page
    )


# ─── Payment Methods ──────────────────────────────────────────────────────────

@router.get("/methods", response_model=List[PaymentMethodResponse])
def get_payment_methods(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return payment_service.get_payment_methods(db, current_user.id)


@router.delete("/methods/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_method(
    method_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    payment_service.delete_payment_method(db, method_id, current_user.id)