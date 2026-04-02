from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional

from app.models.user import User
from app.models.admin import AdminUser, AuditLog, Dispute
from app.models.seller import Seller
from app.models.product import Product
from app.models.order import Order
from app.core.security import hash_password, verify_password
from app.core.security import create_access_token
from app.schemas.admin import (
    AdminLoginRequest,
    AdminUserCreate,
    SellerApprovalRequest,
    DisputeResolveRequest,
)


def admin_login(db: Session, data: AdminLoginRequest) -> dict:
    admin = db.query(AdminUser).filter(AdminUser.email == data.email).first()
    if not admin or not verify_password(data.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended"
        )

    admin.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(
        data={"sub": admin.id, "role": admin.role.value, "type": "admin"}
    )
    return {"access_token": token, "token_type": "bearer", "admin": admin}


def create_admin_user(
    db: Session,
    data: AdminUserCreate,
    created_by: str,
) -> AdminUser:
    existing = db.query(AdminUser).filter(AdminUser.email == data.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    admin = AdminUser(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        created_by=created_by,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def get_platform_stats(db: Session) -> dict:
    today = datetime.now(timezone.utc).date()

    total_users = db.query(User).count()
    total_sellers = db.query(Seller).filter(Seller.status == "active").count()
    total_products = db.query(Product).filter(Product.status == "active").count()
    total_orders = db.query(Order).count()

    total_revenue = db.query(
        func.sum(Order.total_amount)
    ).filter(
        Order.status.notin_(["cancelled", "refunded"])
    ).scalar() or Decimal("0.00")

    today_orders = db.query(Order).filter(
        func.date(Order.created_at) == today
    ).count()

    today_revenue = db.query(
        func.sum(Order.total_amount)
    ).filter(
        func.date(Order.created_at) == today,
        Order.status.notin_(["cancelled", "refunded"]),
    ).scalar() or Decimal("0.00")

    pending_disputes = db.query(Dispute).filter(
        Dispute.status == "open"
    ).count()

    pending_sellers = db.query(Seller).filter(
        Seller.status == "pending"
    ).count()

    return {
        "total_users": total_users,
        "total_sellers": total_sellers,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "today_orders": today_orders,
        "today_revenue": today_revenue,
        "pending_disputes": pending_disputes,
        "pending_seller_approvals": pending_sellers,
    }


def get_all_users(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    role: Optional[str] = None,
) -> dict:
    query = db.query(User)

    if search:
        query = query.filter(
            User.email.ilike(f"%{search}%") |
            User.full_name.ilike(f"%{search}%") |
            User.phone.ilike(f"%{search}%")
        )

    if role:
        query = query.filter(User.role == role)

    query = query.order_by(User.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


def toggle_user_status(db: Session, user_id: str, admin_id: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = not user.is_active

    log = AuditLog(
        admin_id=admin_id,
        action="update",
        entity_type="user",
        entity_id=user_id,
        description=f"User {'activated' if user.is_active else 'suspended'}",
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    return user


def handle_seller_approval(
    db: Session,
    seller_id: str,
    admin_id: str,
    data: SellerApprovalRequest,
) -> Seller:
    seller = db.query(Seller).filter(Seller.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    old_status = seller.status.value

    if data.action == "approve":
        seller.status = "active"
        seller.is_verified = True
    elif data.action == "suspend":
        seller.status = "suspended"
    elif data.action == "ban":
        seller.status = "banned"

    log = AuditLog(
        admin_id=admin_id,
        action=data.action,
        entity_type="seller",
        entity_id=seller_id,
        old_values={"status": old_status},
        new_values={"status": seller.status.value},
        description=data.reason,
    )
    db.add(log)
    db.commit()
    db.refresh(seller)
    return seller


def get_pending_sellers(db: Session, page: int = 1, per_page: int = 20) -> dict:
    query = db.query(Seller).filter(
        Seller.status == "pending"
    ).order_by(Seller.created_at.asc())

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


def get_disputes(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    status_filter: Optional[str] = None,
) -> dict:
    query = db.query(Dispute)
    if status_filter:
        query = query.filter(Dispute.status == status_filter)
    query = query.order_by(Dispute.created_at.desc())

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


def resolve_dispute(
    db: Session,
    dispute_id: str,
    admin_id: str,
    data: DisputeResolveRequest,
) -> Dispute:
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    dispute.status = "resolved"
    dispute.resolution = data.resolution
    dispute.resolved_by = admin_id
    dispute.resolved_at = datetime.now(timezone.utc)

    log = AuditLog(
        admin_id=admin_id,
        action="resolve",
        entity_type="dispute",
        entity_id=dispute_id,
        description=data.resolution,
    )
    db.add(log)
    db.commit()
    db.refresh(dispute)
    return dispute