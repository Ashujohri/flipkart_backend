from sqlalchemy import (
    Column, String, Boolean, Enum, Text,
    ForeignKey, DateTime, Integer, Float,
    Numeric, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum


def generate_uuid():
    return str(uuid.uuid4())


# ─── Enums ────────────────────────────────────────────────────────────────────

class AdminRole(enum.Enum):
    superadmin          = "superadmin"
    admin               = "admin"
    moderator           = "moderator"
    seller_manager      = "seller_manager"
    order_manager       = "order_manager"
    content_manager     = "content_manager"
    finance_manager     = "finance_manager"

class NotificationType(enum.Enum):
    order_placed        = "order_placed"
    order_confirmed     = "order_confirmed"
    order_shipped       = "order_shipped"
    order_delivered     = "order_delivered"
    order_cancelled     = "order_cancelled"
    payment_success     = "payment_success"
    payment_failed      = "payment_failed"
    refund_initiated    = "refund_initiated"
    refund_completed    = "refund_completed"
    return_approved     = "return_approved"
    return_rejected     = "return_rejected"
    review_approved     = "review_approved"
    price_drop          = "price_drop"
    back_in_stock       = "back_in_stock"
    flash_sale_starting = "flash_sale_starting"
    seller_approved     = "seller_approved"
    seller_suspended    = "seller_suspended"
    payout_processed    = "payout_processed"
    low_stock_alert     = "low_stock_alert"
    dispute_raised      = "dispute_raised"
    dispute_resolved    = "dispute_resolved"

class NotificationChannel(enum.Enum):
    in_app  = "in_app"
    email   = "email"
    sms     = "sms"
    push    = "push"

class DisputeStatus(enum.Enum):
    open        = "open"
    investigating = "investigating"
    resolved    = "resolved"
    closed      = "closed"
    escalated   = "escalated"

class DisputeType(enum.Enum):
    order       = "order"
    payment     = "payment"
    return_     = "return_"
    seller      = "seller"
    product     = "product"
    other       = "other"

class AuditAction(enum.Enum):
    create  = "create"
    update  = "update"
    delete  = "delete"
    login   = "login"
    logout  = "logout"
    approve = "approve"
    reject  = "reject"
    suspend = "suspend"
    restore = "restore"


# ─── Admin User ───────────────────────────────────────────────────────────────

class AdminUser(Base):
    __tablename__ = "admin_users"

    id                  = Column(String(36), primary_key=True, default=generate_uuid)
    email               = Column(String(255), unique=True, nullable=False, index=True)
    password_hash       = Column(String(255), nullable=False)
    full_name           = Column(String(100), nullable=False)
    role                = Column(Enum(AdminRole), default=AdminRole.moderator, nullable=False)
    is_active           = Column(Boolean, default=True, nullable=False)
    permissions         = Column(JSON, nullable=True)
    last_login_at       = Column(DateTime, nullable=True)
    last_login_ip       = Column(String(45), nullable=True)
    two_factor_enabled  = Column(Boolean, default=False, nullable=False)
    two_factor_secret   = Column(String(32), nullable=True)
    created_by          = Column(String(36), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    created_at          = Column(DateTime, server_default=func.now())
    updated_at          = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="admin", cascade="all, delete-orphan")


# ─── Admin Role Permission ────────────────────────────────────────────────────

class AdminRolePermission(Base):
    __tablename__ = "admin_role_permissions"

    id          = Column(String(36), primary_key=True, default=generate_uuid)
    role        = Column(Enum(AdminRole), nullable=False, unique=True)
    permissions = Column(JSON, nullable=False)
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ─── Audit Log ────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id              = Column(String(36), primary_key=True, default=generate_uuid)
    admin_id        = Column(String(36), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True, index=True)
    action          = Column(Enum(AuditAction), nullable=False)
    entity_type     = Column(String(50), nullable=False)
    entity_id       = Column(String(36), nullable=True)
    old_values      = Column(JSON, nullable=True)
    new_values      = Column(JSON, nullable=True)
    description     = Column(Text, nullable=True)
    ip_address      = Column(String(45), nullable=True)
    user_agent      = Column(String(255), nullable=True)
    created_at      = Column(DateTime, server_default=func.now())

    # Relationships
    admin = relationship("AdminUser", back_populates="audit_logs")


# ─── Notification ─────────────────────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id              = Column(String(36), primary_key=True, default=generate_uuid)
    user_id         = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type            = Column(Enum(NotificationType), nullable=False)
    channel         = Column(Enum(NotificationChannel), nullable=False)
    title           = Column(String(255), nullable=False)
    body            = Column(Text, nullable=False)
    data            = Column(JSON, nullable=True)
    is_read         = Column(Boolean, default=False, nullable=False)
    read_at         = Column(DateTime, nullable=True)
    is_sent         = Column(Boolean, default=False, nullable=False)
    sent_at         = Column(DateTime, nullable=True)
    failure_reason  = Column(String(255), nullable=True)
    created_at      = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="notifications")


# ─── Dispute ──────────────────────────────────────────────────────────────────

class Dispute(Base):
    __tablename__ = "disputes"

    id                  = Column(String(36), primary_key=True, default=generate_uuid)
    dispute_number      = Column(String(20), unique=True, nullable=False, index=True)
    type                = Column(Enum(DisputeType), nullable=False)
    status              = Column(Enum(DisputeStatus), default=DisputeStatus.open, nullable=False)
    raised_by_user_id   = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    against_seller_id   = Column(String(36), ForeignKey("sellers.id", ondelete="SET NULL"), nullable=True)
    order_id            = Column(String(36), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    assigned_to         = Column(String(36), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    subject             = Column(String(255), nullable=False)
    description         = Column(Text, nullable=False)
    attachments         = Column(JSON, nullable=True)
    resolution          = Column(Text, nullable=True)
    resolved_at         = Column(DateTime, nullable=True)
    resolved_by         = Column(String(36), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    priority            = Column(Integer, default=2, nullable=False)
    created_at          = Column(DateTime, server_default=func.now())
    updated_at          = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    raised_by       = relationship("User", foreign_keys=[raised_by_user_id])
    against_seller  = relationship("Seller")
    order           = relationship("Order")
    messages        = relationship("DisputeMessage", back_populates="dispute", cascade="all, delete-orphan")


# ─── Dispute Message ──────────────────────────────────────────────────────────

class DisputeMessage(Base):
    __tablename__ = "dispute_messages"

    id              = Column(String(36), primary_key=True, default=generate_uuid)
    dispute_id      = Column(String(36), ForeignKey("disputes.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_type     = Column(String(10), nullable=False)
    sender_id       = Column(String(36), nullable=False)
    message         = Column(Text, nullable=False)
    attachments     = Column(JSON, nullable=True)
    is_internal     = Column(Boolean, default=False, nullable=False)
    created_at      = Column(DateTime, server_default=func.now())

    # Relationships
    dispute = relationship("Dispute", back_populates="messages")