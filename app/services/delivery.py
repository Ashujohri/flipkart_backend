from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import random
import string

from app.models.delivery import DeliveryPartner, Shipment, TrackingEvent, Pincode
from app.models.order import Order, OrderStatusHistory
from app.schemas.delivery import ShipmentCreate, TrackingEventCreate

def generate_tracking_number(partner_code: str) -> str:
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"{partner_code[:3]}{random_part}"

def check_pincode(db:Session, pincode: str) -> dict:
    pin = db.query(Pincode).filter(Pincode.pincode == pincode).first()
    if not pin:
        return{
            "pincode": pincode,
            "city": "Unknown",
            "state": "Unknown",
            "is_servicable": False,
            "is_cod_available": False,
            "delivery_days": 0,
            "estimated_delivery_date": "Not serviceable",
        }
    from datetime import date
    estimated = datetime.now(timezone.utc) + timedelta(days=pin.delivery_days)
    
    return{
        "pincode": pin.pincode,
        "city": pin.city,
        "state": pin.state,
        "is_servicable": pin.is_serviceable,
        "is_cod_available": pin.is_cod_available,
        "delivery_days": pin.delivery_days,
        "estimated_delivery_date": estimated.strftime("%d %b %Y"),
    }

def create_shipment(db: Session, data: ShipmentCreate, admin_id: str,) -> Shipment:
    order = db.query(Order).filter(Order.id == data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status.value not in ["confirmed", "processing"]:
        raise HTTPException(
            status_code=400,
            detail="Order must be confirmed or processing to create shipment"
        )
    
    existing = db.query(Shipment).filter(Shipment.order_id == data.order_id).first()
    if existing:
        raise HTTPException(
            status_code=409, detail="Shipment already exists"
        )
    
    partner = db.query(DeliveryPartner).filter(
        DeliveryPartner.code == data.delivery_partner_code,
        DeliveryPartner.status == "active",
    ).first()
    
    if not partner:
        raise HTTPException(
            status_code=404, detail="Delivery partner not found"
        )
    
    tracking_number = generate_tracking_number(partner.code)
    
    # Shipping charge claculate
    shipping_charge = float(partner.base_rate or 0)
    if data.weight_kg and partner.per_kg_rate:
        shipping_charge += data.weight_kg * float(partner.per_kg_rate)
    
    # COD charge
    if order.payment_mode.value == "cod" and partner.cod_charge:
        shipping_charge += float(partner.cod_charge)
    
    # Getting pincode from address
    delivery_picode = order.snapshot_address.get("pincode", "")
    pin_info = check_pincode(db, delivery_picode)
    delivery_days = pin_info.get("delivery_days", 5)
    
    shipment = Shipment(
        order_id = data.order_id,
        delivery_partner_id = partner.id,
        tracking_number = tracking_number,
        status = "pending",
        pickup_address = {"address": "Seller warehouse"},
        delivery_address = order.snapshot_address,
        weight_kg = data.weight_kg,
        dimensions=data.dimensions,
        shipping_charge = shipping_charge,
        cod_amount = order.total_amount if order.payment_mode.value == "cod" else 0,
        estimated_delivery_date = datetime.now(timezone.utc) + timedelta(days=delivery_days),
    )
    db.add(shipment)
    
    # order status update
    order.status = "processing"
    history = OrderStatusHistory(
        order_id = order.id,
        status = "processing",
        message = f"Shipment created - {partner.name} | {tracking_number}",
    )
    db.add(history)
    
    db.commit()
    db.refresh(shipment)
    return shipment

def get_shipment_by_order(db: Session, order_id: str) -> Shipment:
    shipment = db.query(Shipment).filter(
        Shipment.order_id == order_id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment

def add_tracking_event(db: Session, shipment_id: str, data: TrackingEventCreate,) -> Shipment:
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    event = TrackingEvent(
        shipment_id=shipment_id,
        event_type = data.event_type,
        message = data.message,
        location = data.location,
        city = data.city,
        state = data.state,
        pincode = data.pincode,
        coordinates = data.coordinates,
        operator_name = data.operator_name,
        event_time = data.event_time,
    )
    db.add(event)
    
    # shipment status update
    status_map = {
        "pickup_scheduled": "pickup_scheduled",
        "picked_up": "picked_up",
        "in_transit": "in_transit",
        "out_for_delivery": "out_for_delivery",
        "delivered": "delivered",
        "delivered_failed": "delivered_failed",
        "returned_to_origin": "returned_to_origin",
    }
    
    if data.event_type in status_map:
        shipment.status = status_map[data.event_type]
        
        order = db.query(Order).filter(Order.id == shipment.order_id).first()
        if order:
            order_status_map = {
                "picked_up":"packed",
                "in_transit":"shipped",
                "out_for_delivery": "out_for_delivery",
                "delivered": "delivered",
            }
            if data.event_type in order_status_map:
                order.status = order_status_map[data.event_type]
                
                if data.event_type == "delivered":
                    order.delivered_at = data.event_time
                    shipment.delivered_at = data.event_time
                
                history = OrderStatusHistory(
                    order_id = order.id,
                    status=order_status_map[data.event_type],
                    message=data.message,
                    location = data.location,
                )
                db.add(history)
    db.commit()
    db.refresh(shipment)
    return shipment

def build_shipment_response(shipment: Shipment) -> dict:
    partner = shipment.delivery_partner
    tracking_url = None
    if partner and partner.tracking_url_format and shipment.tracking_number:
        tracking_url = partner.tracking_url_format.replace(
            "{tracking_number}", shipment.tracking_number
        )

    return {
        "id": shipment.id,
        "order_id": shipment.order_id,
        "tracking_number": shipment.tracking_number,
        "status": shipment.status.value,
        "delivery_partner_name": partner.name if partner else None,
        "tracking_url": tracking_url,
        "weight_kg": shipment.weight_kg,
        "shipping_charge": float(shipment.shipping_charge),
        "estimated_delivery_date": shipment.estimated_delivery_date,
        "pickup_scheduled_at": shipment.pickup_scheduled_at,
        "picked_up_at": shipment.picked_up_at,
        "delivered_at": shipment.delivered_at,
        "tracking_events": shipment.tracking_events,
        "created_at": shipment.created_at,
    }