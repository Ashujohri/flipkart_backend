from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_admin
from app.models.user import User
from app.schemas.delivery import (
    ShipmentCreate,
    TrackingEventCreate,
    ShipmentResponse,
    PincodeCheckResponse,
)
from app.services import delivery as delivery_service

router = APIRouter(tags=["Delivery"])


@router.get("/pincode/{pincode}", response_model=PincodeCheckResponse)
def check_pincode(
    pincode: str,
    db: Session = Depends(get_db),
):
    return delivery_service.check_pincode(db, pincode)


@router.get("/orders/{order_id}/shipment")
def get_shipment(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    shipment = delivery_service.get_shipment_by_order(db, order_id)
    return delivery_service.build_shipment_response(shipment)


@router.post("/admin/shipments")
def create_shipment(
    data: ShipmentCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    shipment = delivery_service.create_shipment(db, data, current_user.id)
    return delivery_service.build_shipment_response(shipment)


@router.post("/admin/shipments/{shipment_id}/tracking")
def add_tracking_event(
    shipment_id: str,
    data: TrackingEventCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    shipment = delivery_service.add_tracking_event(db, shipment_id, data)
    return delivery_service.build_shipment_response(shipment)