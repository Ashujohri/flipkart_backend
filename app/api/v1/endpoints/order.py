from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.order import (
    PlaceOrderRequest,
    CancelOrderRequest,
    ReturnOrderRequest,
    OrderResponse,
    OrderListResponse,
    PaginatedOrders,
    ReturnResponse,
)
from app.services import order as order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def place_order(
    data: PlaceOrderRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return order_service.place_order(db, current_user.id, data)


@router.get("", response_model=PaginatedOrders)
def get_orders(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=50),
    status_filter: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return order_service.get_orders(
        db, current_user.id, page, per_page, status_filter
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return order_service.get_order_by_id(db, order_id, current_user.id)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: str,
    data: CancelOrderRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return order_service.cancel_order(db, order_id, current_user.id, data)


@router.post("/{order_id}/return", response_model=ReturnResponse, status_code=status.HTTP_201_CREATED)
def request_return(
    order_id: str,
    data: ReturnOrderRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return order_service.request_return(db, order_id, current_user.id, data)


@router.get("/{order_id}/returns", response_model=list[ReturnResponse])
def get_returns(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return order_service.get_order_returns(db, order_id, current_user.id)