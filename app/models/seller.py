from sqlalchemy import (
    Column, String, Boolean, Enum, Text,
    ForeignKey, DateTime, Integer, Float,
    Numeric, JSON, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum


def generate_uuid():
    return str(uuid.uuid4())


# ─── Enums ────────────────────────────────────────────────────────────────────

class SellerStatus(enum.Enum):
    pending     = "pending"
    active      = "active"
    suspended   = "suspended"
    banned      = "banned"

class DocumentType(enum.Enum):
    gst             = "gst"
    pan             = "pan"
    aadhaar         = "aadhaar"
    bank_statement  = "bank_statement"
    shop_license    = "shop_license"
    trademark       = "trademark"

class DocumentStatus(enum.Enum):
    pending     = "pending"
    approved    = "approved"
    rejected    = "rejected"

class PayoutStatus(enum.Enum):
    pending     = "pending"
    processing  = "processing"
    completed   = "completed"
    failed      = "failed"

class AnalyticsPeriod(enum.Enum):
    daily   = "daily"
    weekly  = "weekly"
    monthly = "monthly"


# ─── Seller ───────────────────────────────────────────────────────────────────

class Seller(Base):
    __tablename__ = "sellers"

    id                      = Column(String(36), primary_key=True, default=generate_uuid)
    user_id                 = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    business_name           = Column(String(255), nullable=False)
    business_type           = Column(String(100), nullable=True)
    business_email          = Column(String(255), unique=True, nullable=False)
    business_phone          = Column(String(15), nullable=False)
    business_address        = Column(Text, nullable=False)
    business_city           = Column(String(100), nullable=False)
    business_state          = Column(String(100), nullable=False)
    business_pincode        = Column(String(10), nullable=False)
    gstin                   = Column(String(15), unique=True, nullable=True, index=True)
    pan_number              = Column(String(10), unique=True, nullable=True)
    status                  = Column(Enum(SellerStatus), default=SellerStatus.pending, nullable=False)
    is_verified             = Column(Boolean, default=False, nullable=False)
    rating_avg              = Column(Float, default=0.0, nullable=False)
    rating_count            = Column(Integer, default=0, nullable=False)
    total_sales             = Column(Numeric(14, 2), default=0.00, nullable=False)
    commission_rate         = Column(Float, default=5.0, nullable=False)
    pickup_address          = Column(Text, nullable=True)
    return_address          = Column(Text, nullable=True)
    support_email           = Column(String(255), nullable=True)
    support_phone           = Column(String(15), nullable=True)
    created_at              = Column(DateTime, server_default=func.now())
    updated_at              = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user            = relationship("User")
    products        = relationship("Product", back_populates="seller")
    documents       = relationship("SellerDocument", back_populates="seller", cascade="all, delete-orphan")
    bank_details    = relationship("SellerBankDetails", back_populates="seller", uselist=False, cascade="all, delete-orphan")
    payouts         = relationship("SellerPayout", back_populates="seller", cascade="all, delete-orphan")
    analytics       = relationship("SellerAnalytics", back_populates="seller", cascade="all, delete-orphan")


# ─── Seller Document ──────────────────────────────────────────────────────────

class SellerDocument(Base):
    __tablename__ = "seller_documents"

    id              = Column(String(36), primary_key=True, default=generate_uuid)
    seller_id       = Column(String(36), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type   = Column(Enum(DocumentType), nullable=False)
    document_number = Column(String(50), nullable=True)
    file_url        = Column(String(500), nullable=False)
    status          = Column(Enum(DocumentStatus), default=DocumentStatus.pending)
    rejection_reason= Column(Text, nullable=True)
    verified_at     = Column(DateTime, nullable=True)
    verified_by     = Column(String(36), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    expires_at      = Column(Date, nullable=True)
    created_at      = Column(DateTime, server_default=func.now())
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    seller = relationship("Seller", back_populates="documents")


# ─── Seller Bank Details ──────────────────────────────────────────────────────

class SellerBankDetails(Base):
    __tablename__ = "seller_bank_details"

    id                  = Column(String(36), primary_key=True, default=generate_uuid)
    seller_id           = Column(String(36), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False, unique=True)
    account_holder_name = Column(String(100), nullable=False)
    account_number      = Column(String(20), nullable=False)
    ifsc_code           = Column(String(11), nullable=False)
    bank_name           = Column(String(100), nullable=False)
    branch_name         = Column(String(100), nullable=True)
    account_type        = Column(String(20), default="savings", nullable=False)
    is_verified         = Column(Boolean, default=False, nullable=False)
    created_at          = Column(DateTime, server_default=func.now())
    updated_at          = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    seller = relationship("Seller", back_populates="bank_details")


# ─── Seller Payout ────────────────────────────────────────────────────────────

class SellerPayout(Base):
    __tablename__ = "seller_payouts"

    id                  = Column(String(36), primary_key=True, default=generate_uuid)
    seller_id           = Column(String(36), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False, index=True)
    amount              = Column(Numeric(12, 2), nullable=False)
    commission_deducted = Column(Numeric(12, 2), nullable=False)
    tds_deducted        = Column(Numeric(12, 2), default=0.00, nullable=False)
    net_amount          = Column(Numeric(12, 2), nullable=False)
    status              = Column(Enum(PayoutStatus), default=PayoutStatus.pending, nullable=False)
    utr_number          = Column(String(50), nullable=True)
    payout_date         = Column(DateTime, nullable=True)
    period_start        = Column(Date, nullable=False)
    period_end          = Column(Date, nullable=False)
    notes               = Column(Text, nullable=True)
    created_at          = Column(DateTime, server_default=func.now())
    updated_at          = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    seller = relationship("Seller", back_populates="payouts")


# ─── Seller Analytics ─────────────────────────────────────────────────────────

class SellerAnalytics(Base):
    __tablename__ = "seller_analytics"

    id                  = Column(String(36), primary_key=True, default=generate_uuid)
    seller_id           = Column(String(36), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False, index=True)
    period              = Column(Enum(AnalyticsPeriod), nullable=False)
    period_date         = Column(Date, nullable=False)
    total_orders        = Column(Integer, default=0, nullable=False)
    total_revenue       = Column(Numeric(14, 2), default=0.00, nullable=False)
    total_units_sold    = Column(Integer, default=0, nullable=False)
    total_returns       = Column(Integer, default=0, nullable=False)
    total_cancelled     = Column(Integer, default=0, nullable=False)
    avg_order_value     = Column(Numeric(12, 2), default=0.00, nullable=False)
    page_views          = Column(Integer, default=0, nullable=False)
    unique_visitors     = Column(Integer, default=0, nullable=False)
    conversion_rate     = Column(Float, default=0.0, nullable=False)
    top_products        = Column(JSON, nullable=True)
    created_at          = Column(DateTime, server_default=func.now())

    # Relationships
    seller = relationship("Seller", back_populates="analytics")