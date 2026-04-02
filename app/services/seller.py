from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from decimal import Decimal
from datetime import datetime, timezone, date
from typing import Optional, List

from app.models.seller import Seller, SellerBankDetails, SellerPayout, SellerAnalytics
from app.models.product import Product, Inventory
from app.models.order import Order, OrderItem
from app.models.user import User
from app.schemas.seller import SellerRegister, SellerUpdate, BankDetailsCreate


# ─── Register ─────────────────────────────────────────────────────────────────

def register_seller(db: Session, user_id: str, data: SellerRegister) -> Seller:
    # already seller hai?
    existing = db.query(Seller).filter(Seller.user_id == user_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already registered as a seller"
        )

    # GSTIN unique check
    if data.gstin:
        gstin_exists = db.query(Seller).filter(Seller.gstin == data.gstin).first()
        if gstin_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="GSTIN already registered"
            )

    # PAN unique check
    if data.pan_number:
        pan_exists = db.query(Seller).filter(Seller.pan_number == data.pan_number).first()
        if pan_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="PAN already registered"
            )

    seller = Seller(
        user_id=user_id,
        **data.model_dump()
    )
    db.add(seller)

    # user role update karo
    user = db.query(User).filter(User.id == user_id).first()
    user.role = "seller"

    db.commit()
    db.refresh(seller)
    return seller


def get_seller_by_user_id(db: Session, user_id: str) -> Seller:
    seller = db.query(Seller).filter(Seller.user_id == user_id).first()
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller profile not found"
        )
    return seller


def update_seller(db: Session, user_id: str, data: SellerUpdate) -> Seller:
    seller = get_seller_by_user_id(db, user_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(seller, field, value)
    db.commit()
    db.refresh(seller)
    return seller


# ─── Dashboard ────────────────────────────────────────────────────────────────

def get_seller_dashboard(db: Session, user_id: str) -> dict:
    seller = get_seller_by_user_id(db, user_id)

    today = datetime.now(timezone.utc).date()

    # aaj ke orders
    today_orders = db.query(OrderItem).join(Order).filter(
        OrderItem.seller_id == seller.id,
        func.date(Order.created_at) == today,
    ).count()

    # aaj ki revenue
    today_revenue = db.query(
        func.sum(OrderItem.total_price)
    ).join(Order).filter(
        OrderItem.seller_id == seller.id,
        func.date(Order.created_at) == today,
        Order.status.notin_(["cancelled", "return_requested"]),
    ).scalar() or Decimal("0.00")

    # pending orders
    pending_orders = db.query(OrderItem).join(Order).filter(
        OrderItem.seller_id == seller.id,
        Order.status.in_(["confirmed", "processing", "packed"]),
    ).count()

    # total products
    total_products = db.query(Product).filter(
        Product.seller_id == seller.id,
        Product.status != "inactive",
    ).count()

    # low stock products
    low_stock = db.query(Inventory).join(Product).filter(
        Product.seller_id == seller.id,
        Inventory.available_stock <= Inventory.low_stock_threshold,
        Inventory.available_stock > 0,
    ).count()

    # pending payouts
    pending_payouts = db.query(
        func.sum(SellerPayout.net_amount)
    ).filter(
        SellerPayout.seller_id == seller.id,
        SellerPayout.status == "pending",
    ).scalar() or Decimal("0.00")

    # recent orders
    recent_order_items = db.query(OrderItem).join(Order).filter(
        OrderItem.seller_id == seller.id,
    ).order_by(Order.created_at.desc()).limit(5).all()

    recent_orders = []
    for item in recent_order_items:
        recent_orders.append({
            "order_number": item.order.order_number,
            "product_name": item.product_name,
            "quantity": item.quantity,
            "total_price": item.total_price,
            "status": item.order.status.value,
            "created_at": item.order.created_at,
        })

    return {
        "seller": seller,
        "today_orders": today_orders,
        "today_revenue": today_revenue,
        "pending_orders": pending_orders,
        "total_products": total_products,
        "low_stock_products": low_stock,
        "pending_payouts": pending_payouts,
        "recent_orders": recent_orders,
    }


# ─── Seller Orders ────────────────────────────────────────────────────────────

def get_seller_orders(
    db: Session,
    user_id: str,
    page: int = 1,
    per_page: int = 20,
    status_filter: Optional[str] = None,
) -> dict:
    seller = get_seller_by_user_id(db, user_id)

    query = db.query(OrderItem).join(Order).filter(
        OrderItem.seller_id == seller.id,
    )

    if status_filter:
        query = query.filter(Order.status == status_filter)

    query = query.order_by(Order.created_at.desc())

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    result = []
    for item in items:
        result.append({
            "order_item_id": item.id,
            "order_number": item.order.order_number,
            "order_id": item.order_id,
            "product_name": item.product_name,
            "variant_name": item.variant_name,
            "quantity": item.quantity,
            "total_price": item.total_price,
            "status": item.order.status.value,
            "payment_mode": item.order.payment_mode.value,
            "delivery_address": item.order.snapshot_address,
            "created_at": item.order.created_at,
        })

    return {
        "items": result,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


# ─── Bank Details ─────────────────────────────────────────────────────────────

def add_bank_details(
    db: Session,
    user_id: str,
    data: BankDetailsCreate,
) -> SellerBankDetails:
    seller = get_seller_by_user_id(db, user_id)

    existing = db.query(SellerBankDetails).filter(
        SellerBankDetails.seller_id == seller.id
    ).first()

    if existing:
        # update karo
        update_data = data.model_dump()
        for field, value in update_data.items():
            setattr(existing, field, value)
        existing.is_verified = False  # reverify hogi
        db.commit()
        db.refresh(existing)
        return existing

    bank = SellerBankDetails(
        seller_id=seller.id,
        **data.model_dump()
    )
    db.add(bank)
    db.commit()
    db.refresh(bank)
    return bank


def get_bank_details(db: Session, user_id: str) -> SellerBankDetails:
    seller = get_seller_by_user_id(db, user_id)
    bank = db.query(SellerBankDetails).filter(
        SellerBankDetails.seller_id == seller.id
    ).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank details not found")
    return bank


# ─── Payouts ──────────────────────────────────────────────────────────────────

def get_payouts(
    db: Session,
    user_id: str,
    page: int = 1,
    per_page: int = 10,
) -> dict:
    seller = get_seller_by_user_id(db, user_id)

    query = db.query(SellerPayout).filter(
        SellerPayout.seller_id == seller.id
    ).order_by(SellerPayout.created_at.desc())

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


# ─── Analytics ────────────────────────────────────────────────────────────────

def get_analytics(
    db: Session,
    user_id: str,
    period: str = "monthly",
    limit: int = 12,
) -> List[SellerAnalytics]:
    seller = get_seller_by_user_id(db, user_id)

    return db.query(SellerAnalytics).filter(
        SellerAnalytics.seller_id == seller.id,
        SellerAnalytics.period == period,
    ).order_by(SellerAnalytics.period_date.desc()).limit(limit).all()