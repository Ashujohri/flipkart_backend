from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List

from app.models.admin import Notification, NotificationType


def create_notification(
    db: Session,
    user_id: str,
    type_: str,
    title: str,
    body: str,
    channel: str = "in_app",
    data: Optional[dict] = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=type_,
        channel=channel,
        title=title,
        body=body,
        data=data,
        is_sent=True,
        sent_at=datetime.now(timezone.utc),
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_notifications(
    db: Session,
    user_id: str,
    page: int = 1,
    per_page: int = 20,
    unread_only: bool = False,
) -> dict:
    query = db.query(Notification).filter(
        Notification.user_id == user_id
    )

    if unread_only:
        query = query.filter(Notification.is_read == False)

    query = query.order_by(Notification.created_at.desc())

    total = query.count()
    unread_count = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False,
    ).count()

    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": items,
        "total": total,
        "unread_count": unread_count,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


def mark_as_read(
    db: Session,
    user_id: str,
    notification_ids: Optional[List[str]] = None,
) -> int:
    query = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False,
    )

    if notification_ids:
        query = query.filter(Notification.id.in_(notification_ids))

    count = query.count()
    query.update({
        "is_read": True,
        "read_at": datetime.now(timezone.utc),
    })
    db.commit()
    return count


def delete_notification(db: Session, notification_id: str, user_id: str) -> None:
    from fastapi import HTTPException
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id,
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(notification)
    db.commit()


def delete_all_read(db: Session, user_id: str) -> int:
    count = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == True,
    ).count()
    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == True,
    ).delete()
    db.commit()
    return count