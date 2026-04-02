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

class OrderStatus(enum.Enum):
    pending             = "pending"
    confirmed           = "confirmed"
    processing          = "processing"
    packed              = "packed"
    shipped             = "shipped"
    out_for_delivery    = "out_for_delivery"
    delivered           = "delivered"
    cancelled           = "cancelled"
    return_requested    = "return_requested"
    return_picked       = "return_picked"
    return_received     = "return_received"
    refund_initiated    = "refund_initiated"
    refunded            = "refunded"

class PaymentMode(enum.Enum):
    cod             = "cod"
    upi             = "upi"
    credit_card     = "credit_card"
    debit_card      = "debit_card"
    net_banking     = "net_banking"
    emi             = "emi"
    wallet          = "wallet"
    pay_later       = "pay_later"

class ReturnReason(enum.Enum):
    defective           = "defective"
    wrong_item          = "wrong_item"
    not_as_described    = "not_as_described"
    damaged_in_shipping = "damaged_in_shipping"
    changed_mind        = "changed_mind"
    size_issue          = "size_issue"
    quality_issue       = "quality_issue"
    other               = "other"

class ReturnStatus(enum.Enum):
    requested   = "requested"
    approved    = "approved"
    rejected    = "rejected"
    picked_up   = "picked_up"
    received    = "received"
    refunded    = "refunded"


# ─── Order ────────────────────────────────────────────────────────────────────

class Order(Base):
    __tablename__ = "orders"

    id                      = Column(String(36), primary_key=True, default=generate_uuid)
    order_number            = Column(String(20), unique=True, nullable=False, index=True)
    user_id                 = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    address_id              = Column(String(36), ForeignKey("user_addresses.id", ondelete="SET NULL"), nullable=True)
    coupon_id               = Column(String(36), ForeignKey("coupons.id", ondelete="SET NULL"), nullable=True)
    status                  = Column(Enum(OrderStatus), default=OrderStatus.pending, nullable=False)
    payment_mode            = Column(Enum(PaymentMode), nullable=False)
    subtotal                = Column(Numeric(12, 2), nullable=False)
    discount_amount         = Column(Numeric(12, 2), default=0.00, nullable=False)
    coupon_discount         = Column(Numeric(12, 2), default=0.00, nullable=False)
    delivery_charge         = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_amount            = Column(Numeric(12, 2), nullable=False)
    saved_amount            = Column(Numeric(12, 2), default=0.00, nullable=False)
    snapshot_address        = Column(JSON, nullable=False)
    delivery_instructions   = Column(Text, nullable=True)
    expected_delivery_date  = Column(DateTime, nullable=True)
    delivered_at            = Column(DateTime, nullable=True)
    cancelled_at            = Column(DateTime, nullable=True)
    cancellation_reason     = Column(Text, nullable=True)
    created_at              = Column(DateTime, server_default=func.now())
    updated_at              = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user            = relationship("User", back_populates="orders")
    address         = relationship("UserAddress")
    coupon          = relationship("Coupon")
    items           = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    status_history  = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")
    payment         = relationship("Payment", back_populates="order", uselist=False)
    shipment        = relationship("Shipment", back_populates="order", uselist=False)
    returns         = relationship("Return", back_populates="order")


# ─── Order Item ───────────────────────────────────────────────────────────────

class OrderItem(Base):
    __tablename__ = "order_items"

    id                  = Column(String(36), primary_key=True, default=generate_uuid)
    order_id            = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id          = Column(String(36), ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    variant_id          = Column(String(36), ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    seller_id           = Column(String(36), ForeignKey("sellers.id", ondelete="SET NULL"), nullable=True)
    product_name        = Column(String(255), nullable=False)
    product_image_url   = Column(String(500), nullable=True)
    variant_name        = Column(String(100), nullable=True)
    sku                 = Column(String(100), nullable=True)
    quantity            = Column(Integer, nullable=False)
    mrp                 = Column(Numeric(12, 2), nullable=False)
    selling_price       = Column(Numeric(12, 2), nullable=False)
    discount_amount     = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_price         = Column(Numeric(12, 2), nullable=False)
    is_reviewed         = Column(Boolean, default=False, nullable=False)
    created_at          = Column(DateTime, server_default=func.now())

    # Relationships
    order   = relationship("Order", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    seller  = relationship("Seller")
    returns = relationship("ReturnItem", back_populates="order_item")


# ─── Order Status History ─────────────────────────────────────────────────────

class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id          = Column(String(36), primary_key=True, default=generate_uuid)
    order_id    = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    status      = Column(Enum(OrderStatus), nullable=False)
    message     = Column(String(255), nullable=True)
    location    = Column(String(255), nullable=True)
    changed_by  = Column(String(36), nullable=True)
    created_at  = Column(DateTime, server_default=func.now())

    # Relationships
    order = relationship("Order", back_populates="status_history")


# ─── Return ───────────────────────────────────────────────────────────────────

class Return(Base):
    __tablename__ = "returns"

    id                  = Column(String(36), primary_key=True, default=generate_uuid)
    order_id            = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id             = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    return_number       = Column(String(20), unique=True, nullable=False, index=True)
    reason              = Column(Enum(ReturnReason), nullable=False)
    description         = Column(Text, nullable=True)
    status              = Column(Enum(ReturnStatus), default=ReturnStatus.requested, nullable=False)
    refund_amount       = Column(Numeric(12, 2), nullable=True)
    pickup_address_id   = Column(String(36), ForeignKey("user_addresses.id", ondelete="SET NULL"), nullable=True)
    pickup_scheduled_at = Column(DateTime, nullable=True)
    picked_up_at        = Column(DateTime, nullable=True)
    received_at         = Column(DateTime, nullable=True)
    refunded_at         = Column(DateTime, nullable=True)
    admin_notes         = Column(Text, nullable=True)
    created_at          = Column(DateTime, server_default=func.now())
    updated_at          = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    order           = relationship("Order", back_populates="returns")
    user            = relationship("User")
    pickup_address  = relationship("UserAddress")
    items           = relationship("ReturnItem", back_populates="return_order", cascade="all, delete-orphan")


# ─── Return Item ──────────────────────────────────────────────────────────────

class ReturnItem(Base):
    __tablename__ = "return_items"

    id              = Column(String(36), primary_key=True, default=generate_uuid)
    return_id       = Column(String(36), ForeignKey("returns.id", ondelete="CASCADE"), nullable=False, index=True)
    order_item_id   = Column(String(36), ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False)
    quantity        = Column(Integer, nullable=False)
    condition       = Column(String(50), nullable=True)
    images          = Column(JSON, nullable=True)
    created_at      = Column(DateTime, server_default=func.now())

    # Relationships
    return_order    = relationship("Return", back_populates="items")
    order_item      = relationship("OrderItem", back_populates="returns")