from sqlalchemy import (
    Column, String, Boolean, Enum, Text,
    ForeignKey, DateTime, Integer, Float,
    Numeric, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum


def generate_uuid():
    return str(uuid.uuid4())


# ─── Enums ────────────────────────────────────────────────────────────────────

class PaymentStatus(enum.Enum):
    pending     = "pending"
    initiated   = "initiated"
    processing  = "processing"
    success     = "success"
    failed      = "failed"
    cancelled   = "cancelled"
    refunded    = "refunded"
    partially_refunded = "partially_refunded"

class PaymentGateway(enum.Enum):
    razorpay    = "razorpay"
    paytm       = "paytm"
    phonepe     = "phonepe"
    stripe      = "stripe"
    cod         = "cod"
    wallet      = "wallet"

class RefundStatus(enum.Enum):
    pending     = "pending"
    processing  = "processing"
    completed   = "completed"
    failed      = "failed"

class WalletTransactionType(enum.Enum):
    credit  = "credit"
    debit   = "debit"

class WalletTransactionReason(enum.Enum):
    refund          = "refund"
    cashback        = "cashback"
    order_payment   = "order_payment"
    admin_credit    = "admin_credit"
    withdrawal      = "withdrawal"
    referral_bonus  = "referral_bonus"

class CardType(enum.Enum):
    credit  = "credit"
    debit   = "debit"


# ─── Payment ──────────────────────────────────────────────────────────────────

class Payment(Base):
    __tablename__ = "payments"

    id                      = Column(String(36), primary_key=True, default=generate_uuid)
    order_id                = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    user_id                 = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    gateway                 = Column(Enum(PaymentGateway), nullable=False)
    status                  = Column(Enum(PaymentStatus), default=PaymentStatus.pending, nullable=False)
    amount                  = Column(Numeric(12, 2), nullable=False)
    currency                = Column(String(5), default="INR", nullable=False)
    gateway_order_id        = Column(String(100), nullable=True, index=True)
    gateway_payment_id      = Column(String(100), nullable=True, index=True)
    gateway_signature       = Column(String(500), nullable=True)
    gateway_response        = Column(JSON, nullable=True)
    payment_method_id       = Column(String(36), ForeignKey("payment_methods.id", ondelete="SET NULL"), nullable=True)
    failure_reason          = Column(String(255), nullable=True)
    paid_at                 = Column(DateTime, nullable=True)
    created_at              = Column(DateTime, server_default=func.now())
    updated_at              = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    order           = relationship("Order", back_populates="payment")
    user            = relationship("User")
    payment_method  = relationship("PaymentMethod")
    refund          = relationship("Refund", back_populates="payment", uselist=False)


# ─── Payment Method ───────────────────────────────────────────────────────────

class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id              = Column(String(36), primary_key=True, default=generate_uuid)
    user_id         = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    gateway         = Column(Enum(PaymentGateway), nullable=False)
    card_type       = Column(Enum(CardType), nullable=True)
    card_last4      = Column(String(4), nullable=True)
    card_brand      = Column(String(20), nullable=True)
    card_expiry     = Column(String(7), nullable=True)
    upi_id          = Column(String(100), nullable=True)
    bank_name       = Column(String(100), nullable=True)
    gateway_token   = Column(String(255), nullable=True)
    is_default      = Column(Boolean, default=False, nullable=False)
    created_at      = Column(DateTime, server_default=func.now())
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User")


# ─── Refund ───────────────────────────────────────────────────────────────────

class Refund(Base):
    __tablename__ = "refunds"

    id                  = Column(String(36), primary_key=True, default=generate_uuid)
    payment_id          = Column(String(36), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    order_id            = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id             = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    amount              = Column(Numeric(12, 2), nullable=False)
    status              = Column(Enum(RefundStatus), default=RefundStatus.pending, nullable=False)
    gateway_refund_id   = Column(String(100), nullable=True, index=True)
    gateway_response    = Column(JSON, nullable=True)
    refund_to           = Column(String(50), nullable=False)
    failure_reason      = Column(String(255), nullable=True)
    initiated_at        = Column(DateTime, nullable=True)
    completed_at        = Column(DateTime, nullable=True)
    created_at          = Column(DateTime, server_default=func.now())
    updated_at          = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    payment = relationship("Payment", back_populates="refund")
    user    = relationship("User")


# ─── Wallet ───────────────────────────────────────────────────────────────────

class Wallet(Base):
    __tablename__ = "wallet"

    id          = Column(String(36), primary_key=True, default=generate_uuid)
    user_id     = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    balance     = Column(Numeric(12, 2), default=0.00, nullable=False)
    is_active   = Column(Boolean, default=True, nullable=False)
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user            = relationship("User", back_populates="wallet")
    transactions    = relationship("WalletTransaction", back_populates="wallet", cascade="all, delete-orphan")


# ─── Wallet Transaction ───────────────────────────────────────────────────────

class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id              = Column(String(36), primary_key=True, default=generate_uuid)
    wallet_id       = Column(String(36), ForeignKey("wallet.id", ondelete="CASCADE"), nullable=False, index=True)
    type            = Column(Enum(WalletTransactionType), nullable=False)
    reason          = Column(Enum(WalletTransactionReason), nullable=False)
    amount          = Column(Numeric(12, 2), nullable=False)
    balance_before  = Column(Numeric(12, 2), nullable=False)
    balance_after   = Column(Numeric(12, 2), nullable=False)
    reference_id    = Column(String(36), nullable=True)
    description     = Column(String(255), nullable=True)
    created_at      = Column(DateTime, server_default=func.now())

    # Relationships
    wallet = relationship("Wallet", back_populates="transactions")