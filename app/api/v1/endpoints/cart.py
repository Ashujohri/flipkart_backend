from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.cart import (
    CartItemAdd,
    CartItemUpdate,
    CartResponse,
    ApplyCouponRequest,
)
from app.services import cart as cart_service

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=CartResponse)
def get_cart(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return cart_service.get_cart(db, current_user.id)


@router.post("/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
def add_item(
    data: CartItemAdd,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return cart_service.add_item_to_cart(db, current_user.id, data)


@router.patch("/items/{item_id}", response_model=CartResponse)
def update_item(
    item_id: str,
    data: CartItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return cart_service.update_cart_item(db, current_user.id, item_id, data)


@router.delete("/items/{item_id}", response_model=CartResponse)
def remove_item(
    item_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return cart_service.remove_cart_item(db, current_user.id, item_id)


@router.delete("/clear", response_model=CartResponse)
def clear_cart(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return cart_service.clear_cart(db, current_user.id)


@router.post("/coupon", response_model=CartResponse)
def apply_coupon(
    data: ApplyCouponRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return cart_service.apply_coupon(db, current_user.id, data.code)


@router.delete("/coupon", response_model=CartResponse)
def remove_coupon(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return cart_service.remove_coupon(db, current_user.id)