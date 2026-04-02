from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.user import User
from app.schemas.admin import (
    AdminLoginRequest,
    AdminUserCreate,
    AdminUserResponse,
    PaginatedUsers,
    SellerApprovalRequest,
    DisputeResolveRequest,
    PlatformStats,
)
from app.services import admin as admin_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/login")
def admin_login(
    data: AdminLoginRequest,
    db: Session = Depends(get_db),
):
    return admin_service.admin_login(db, data)


@router.get("/stats", response_model=PlatformStats)
def get_stats(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.get_platform_stats(db)


@router.get("/users", response_model=PaginatedUsers)
def get_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    role: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.get_all_users(db, page, per_page, search, role)


@router.patch("/users/{user_id}/toggle-status")
def toggle_user_status(
    user_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.toggle_user_status(db, user_id, current_user.id)


@router.get("/sellers/pending")
def get_pending_sellers(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.get_pending_sellers(db, page, per_page)


@router.patch("/sellers/{seller_id}/approval")
def handle_seller_approval(
    seller_id: str,
    data: SellerApprovalRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.handle_seller_approval(db, seller_id, current_user.id, data)


@router.get("/disputes")
def get_disputes(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.get_disputes(db, page, per_page, status_filter)


@router.patch("/disputes/{dispute_id}/resolve")
def resolve_dispute(
    dispute_id: str,
    data: DisputeResolveRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.resolve_dispute(db, dispute_id, current_user.id, data)


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_admin(
    data: AdminUserCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.create_admin_user(db, data, current_user.id)