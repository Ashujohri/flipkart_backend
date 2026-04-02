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

class ShipmentStatus(enum.Enum):
    pending             = "pending"
    pickup_scheduled    = "pickup_scheduled"
    picked_up           = "picked_up"
    in_transit          = "in_transit"
    out_for_delivery    = "out_for_delivery"
    delivered           = "delivered"
    delivery_failed     = "delivery_failed"
    returned_to_origin  = "returned_to_origin"

class TrackingEventType(enum.Enum):
    pickup_scheduled    = "pickup_scheduled"
    picked_up           = "picked_up"
    reached_facility    = "reached_facility"
    departed_facility   = "departed_facility"
    in_transit          = "in_transit"
    out_for_delivery    = "out_for_delivery"
    delivery_attempted  = "delivery_attempted"
    delivered           = "delivered"
    delivery_failed     = "delivery_failed"
    returned_to_origin  = "returned_to_origin"

class DeliveryPartnerStatus(enum.Enum):
    active      = "active"
    inactive    = "inactive"
    suspended   = "suspended"


# ─── Delivery Partner ─────────────────────────────────────────────────────────

class DeliveryPartner(Base):
    __tablename__ = "delivery_partners"

    id                  = Column(String(36), primary_key=True, default=generate_uuid)
    name                = Column(String(100), nullable=False)
    code                = Column(String(20), unique=True, nullable=False, index=True)
    api_base_url        = Column(String(255), nullable=True)
    api_key             = Column(String(255), nullable=True)
    api_secret          = Column(String(255), nullable=True)
    tracking_url_format = Column(String(500), nullable=True)
    status              = Column(Enum(DeliveryPartnerStatus), default=DeliveryPartnerStatus.active)
    supported_pincodes  = Column(JSON, nullable=True)
    max_weight_kg       = Column(Float, nullable=True)
    per_kg_rate         = Column(Numeric(8, 2), nullable=True)
    base_rate           = Column(Numeric(8, 2), nullable=True)
    cod_charge          = Column(Numeric(8, 2), default=0.00, nullable=False)
    created_at          = Column(DateTime, server_default=func.now())
    updated_at          = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    shipments = relationship("Shipment", back_populates="delivery_partner")


# ─── Shipment ─────────────────────────────────────────────────────────────────

class Shipment(Base):
    __tablename__ = "shipments"

    id                      = Column(String(36), primary_key=True, default=generate_uuid)
    order_id                = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    delivery_partner_id     = Column(String(36), ForeignKey("delivery_partners.id", ondelete="SET NULL"), nullable=True, index=True)
    tracking_number         = Column(String(100), unique=True, nullable=True, index=True)
    status                  = Column(Enum(ShipmentStatus), default=ShipmentStatus.pending, nullable=False)
    pickup_address          = Column(JSON, nullable=False)
    delivery_address        = Column(JSON, nullable=False)
    weight_kg               = Column(Float, nullable=True)
    dimensions              = Column(JSON, nullable=True)
    shipping_charge         = Column(Numeric(8, 2), default=0.00, nullable=False)
    cod_amount              = Column(Numeric(12, 2), default=0.00, nullable=False)
    label_url               = Column(String(500), nullable=True)
    estimated_delivery_date = Column(DateTime, nullable=True)
    pickup_scheduled_at     = Column(DateTime, nullable=True)
    picked_up_at            = Column(DateTime, nullable=True)
    delivered_at            = Column(DateTime, nullable=True)
    delivery_signature      = Column(String(500), nullable=True)
    delivery_photo_url      = Column(String(500), nullable=True)
    delivery_notes          = Column(Text, nullable=True)
    created_at              = Column(DateTime, server_default=func.now())
    updated_at              = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    order               = relationship("Order", back_populates="shipment")
    delivery_partner    = relationship("DeliveryPartner", back_populates="shipments")
    tracking_events     = relationship("TrackingEvent", back_populates="shipment", cascade="all, delete-orphan")


# ─── Tracking Event ───────────────────────────────────────────────────────────

class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id              = Column(String(36), primary_key=True, default=generate_uuid)
    shipment_id     = Column(String(36), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type      = Column(Enum(TrackingEventType), nullable=False)
    message         = Column(String(255), nullable=False)
    location        = Column(String(255), nullable=True)
    city            = Column(String(100), nullable=True)
    state           = Column(String(100), nullable=True)
    pincode         = Column(String(10), nullable=True)
    coordinates     = Column(JSON, nullable=True)
    operator_name   = Column(String(100), nullable=True)
    raw_response    = Column(JSON, nullable=True)
    event_time      = Column(DateTime, nullable=False)
    created_at      = Column(DateTime, server_default=func.now())

    # Relationships
    shipment = relationship("Shipment", back_populates="tracking_events")


# ─── Pincode ──────────────────────────────────────────────────────────────────

class Pincode(Base):
    __tablename__ = "pincodes"

    id              = Column(String(36), primary_key=True, default=generate_uuid)
    pincode         = Column(String(10), unique=True, nullable=False, index=True)
    city            = Column(String(100), nullable=False)
    district        = Column(String(100), nullable=False)
    state           = Column(String(100), nullable=False)
    country         = Column(String(60), default="India", nullable=False)
    is_cod_available = Column(Boolean, default=True, nullable=False)
    is_serviceable  = Column(Boolean, default=True, nullable=False)
    delivery_days   = Column(Integer, default=5, nullable=False)
    latitude        = Column(Float, nullable=True)
    longitude       = Column(Float, nullable=True)
    created_at      = Column(DateTime, server_default=func.now())
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now())