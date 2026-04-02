from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    PaginatedNotifications,
    MarkReadRequest,
)
from app.services import notification as notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=PaginatedNotifications)
def get_notifications(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return notification_service.get_notifications(
        db, current_user.id, page, per_page, unread_only
    )


@router.patch("/mark-read", status_code=status.HTTP_204_NO_CONTENT)
def mark_read(
    data: MarkReadRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    notification_service.mark_as_read(
        db, current_user.id, data.notification_ids
    )


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    notification_service.delete_notification(db, notification_id, current_user.id)


@router.delete("/clear/read", status_code=status.HTTP_204_NO_CONTENT)
def clear_read_notifications(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    notification_service.delete_all_read(db, current_user.id)