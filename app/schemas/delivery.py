from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


class ShipmentCreate(BaseModel):
    order_id: str
    delivery_partner_code: str
    weight_kg: Optional[float] = None
    dimensions: Optional[dict] = None

    @field_validator("weight_kg")
    @classmethod
    def validate_weight(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Weight must be greater than 0")
        return v


class TrackingEventCreate(BaseModel):
    event_type: str
    message: str
    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    coordinates: Optional[dict] = None
    operator_name: Optional[str] = None
    event_time: datetime

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v):
        allowed = [
            "pickup_scheduled", "picked_up", "reached_facility",
            "departed_facility", "in_transit", "out_for_delivery",
            "delivery_attempted", "delivered", "delivery_failed",
            "returned_to_origin"
        ]
        if v not in allowed:
            raise ValueError(f"Invalid event type")
        return v


class PincodeCheckResponse(BaseModel):
    pincode: str
    city: str
    state: str
    is_serviceable: bool
    is_cod_available: bool
    delivery_days: int
    estimated_delivery_date: str


class TrackingEventResponse(BaseModel):
    id: str
    event_type: str
    message: str
    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    coordinates: Optional[dict] = None
    event_time: datetime

    model_config = {"from_attributes": True}


class ShipmentResponse(BaseModel):
    id: str
    order_id: str
    tracking_number: Optional[str] = None
    status: str
    delivery_partner_name: Optional[str] = None
    tracking_url: Optional[str] = None
    weight_kg: Optional[float] = None
    shipping_charge: float
    estimated_delivery_date: Optional[datetime] = None
    pickup_scheduled_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    tracking_events: List[TrackingEventResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}