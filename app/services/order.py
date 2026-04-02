from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import random
import string

from app.models.order import Order, OrderItem, OrderStatusHistory, Return, ReturnItem
from app.models.product import Cart, CartItem, Product, Inventory
from app.models.user import UserAddress
from app.models.promo import Coupon, CouponUsage
from app.schemas.order import PlaceOrderRequest, CancelOrderRequest, ReturnOrderRequest
from app.services.cart import calculate_coupon_discount, calculate_cart_summary


# ─── Helper ───────────────────────────────────────────────────────────────────

def generate_order_number() -> str:
    random_part = ''.join(random.choices(string.digits, k=10))
    return f"OD{random_part}"


def generate_return_number() -> str:
    random_part = ''.join(random.choices(string.digits, k=8))
    return f"RT{random_part}"


def add_status_history(
    db: Session,
    order_id: str,
    status: str,
    message: str,
    location: Optional[str] = None,
) -> None:
    history = OrderStatusHistory(
        order_id=order_id,
        status=status,
        message=message,
        location=location,
    )
    db.add(history)


# ─── Place Order ──────────────────────────────────────────────────────────────

def place_order(db: Session, user_id: str, data: PlaceOrderRequest) -> Order:
    # cart check
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )

    # address check
    address = db.query(UserAddress).filter(
        UserAddress.id == data.address_id,
        UserAddress.user_id == user_id,
    ).first()
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )

    # stock check — saare items ke liye
    for cart_item in cart.items:
        product = cart_item.product
        if not product or product.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{cart_item.product_id}' is no longer available"
            )

        inventory = db.query(Inventory).filter(
            Inventory.product_id == cart_item.product_id
        ).first()

        if not inventory or inventory.available_stock < cart_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.name}'"
            )

    # amounts calculate karo
    summary = calculate_cart_summary(cart)
    subtotal = summary["subtotal"]
    total_discount = summary["total_discount"]
    delivery_charge = summary["delivery_charge"]

    # coupon discount
    coupon_discount = Decimal("0.00")
    coupon = None
    if cart.coupon_id:
        coupon = db.query(Coupon).filter(Coupon.id == cart.coupon_id).first()
        if coupon and coupon.is_active:
            coupon_discount = calculate_coupon_discount(coupon, subtotal)

    total_amount = subtotal - coupon_discount + delivery_charge
    saved_amount = total_discount + coupon_discount

    # address snapshot
    snapshot_address = {
        "full_name": address.full_name,
        "phone": address.phone,
        "address_line1": address.address_line1,
        "address_line2": address.address_line2,
        "city": address.city,
        "state": address.state,
        "pincode": address.pincode,
        "country": address.country,
    }

    # expected delivery
    expected_delivery = datetime.now(timezone.utc) + timedelta(days=5)

    # order banao
    order = Order(
        order_number=generate_order_number(),
        user_id=user_id,
        address_id=data.address_id,
        coupon_id=cart.coupon_id,
        status="pending",
        payment_mode=data.payment_mode,
        subtotal=subtotal,
        discount_amount=total_discount,
        coupon_discount=coupon_discount,
        delivery_charge=delivery_charge,
        total_amount=total_amount,
        saved_amount=saved_amount,
        snapshot_address=snapshot_address,
        delivery_instructions=data.delivery_instructions,
        expected_delivery_date=expected_delivery,
    )
    db.add(order)
    db.flush()  # order ID generate ho jaaye

    # order items banao
    for cart_item in cart.items:
        product = cart_item.product
        variant = cart_item.variant

        item_discount = (product.mrp - product.selling_price) * cart_item.quantity
        total_price = product.selling_price * cart_item.quantity

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            variant_id=cart_item.variant_id,
            seller_id=product.seller_id,
            product_name=product.name,
            product_image_url=product.images[0].image_url if product.images else None,
            variant_name=variant.name if variant else None,
            sku=variant.sku if variant else None,
            quantity=cart_item.quantity,
            mrp=product.mrp,
            selling_price=product.selling_price,
            discount_amount=item_discount,
            total_price=total_price,
        )
        db.add(order_item)

        # stock reserve karo
        inventory = db.query(Inventory).filter(
            Inventory.product_id == product.id
        ).first()
        inventory.reserved_stock += cart_item.quantity
        inventory.available_stock -= cart_item.quantity

        # out of stock?
        if inventory.available_stock <= 0:
            product.status = "out_of_stock"

    # coupon usage record karo
    if coupon and coupon_discount > 0:
        coupon.used_count += 1
        usage = CouponUsage(
            coupon_id=coupon.id,
            user_id=user_id,
            order_id=order.id,
            discount_given=coupon_discount,
        )
        db.add(usage)

    # status history add karo
    add_status_history(
        db, order.id, "pending",
        "Order placed successfully"
    )

    # COD toh confirmed
    if data.payment_mode == "cod":
        order.status = "confirmed"
        add_status_history(
            db, order.id, "confirmed",
            "Order confirmed — Cash on Delivery"
        )

    # cart clear karo
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    cart.coupon_id = None

    db.commit()
    db.refresh(order)
    return order


# ─── Get Orders ───────────────────────────────────────────────────────────────

def get_orders(
    db: Session,
    user_id: str,
    page: int = 1,
    per_page: int = 10,
    status_filter: Optional[str] = None,
) -> dict:
    query = db.query(Order).filter(Order.user_id == user_id)

    if status_filter:
        query = query.filter(Order.status == status_filter)

    query = query.order_by(Order.created_at.desc())

    total = query.count()
    orders = query.offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for order in orders:
        first_item = order.items[0] if order.items else None
        items.append({
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status.value,
            "payment_mode": order.payment_mode.value,
            "total_amount": order.total_amount,
            "item_count": len(order.items),
            "created_at": order.created_at,
            "first_item_name": first_item.product_name if first_item else None,
            "first_item_image": first_item.product_image_url if first_item else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


def get_order_by_id(db: Session, order_id: str, user_id: str) -> Order:
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user_id,
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


# ─── Cancel Order ─────────────────────────────────────────────────────────────

def cancel_order(
    db: Session,
    order_id: str,
    user_id: str,
    data: CancelOrderRequest,
) -> Order:
    order = get_order_by_id(db, order_id, user_id)

    # sirf ye statuses cancel ho sakte hain
    cancellable = ["pending", "confirmed", "processing"]
    if order.status.value not in cancellable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be cancelled in '{order.status.value}' status"
        )

    order.status = "cancelled"
    order.cancelled_at = datetime.now(timezone.utc)
    order.cancellation_reason = data.reason

    # stock wapas karo
    for item in order.items:
        inventory = db.query(Inventory).filter(
            Inventory.product_id == item.product_id
        ).first()
        if inventory:
            inventory.reserved_stock -= item.quantity
            inventory.available_stock += item.quantity

            # product wapas active karo
            product = db.query(Product).filter(
                Product.id == item.product_id
            ).first()
            if product and product.status == "out_of_stock":
                product.status = "active"

    add_status_history(
        db, order.id, "cancelled",
        f"Order cancelled: {data.reason}"
    )

    db.commit()
    db.refresh(order)
    return order


# ─── Return Order ─────────────────────────────────────────────────────────────

def request_return(
    db: Session,
    order_id: str,
    user_id: str,
    data: ReturnOrderRequest,
) -> Return:
    order = get_order_by_id(db, order_id, user_id)

    # sirf delivered orders return ho sakte hain
    if order.status.value != "delivered":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only delivered orders can be returned"
        )

    # return window check — 7 din
    if order.delivered_at:
        days_since_delivery = (datetime.now(timezone.utc) - order.delivered_at.replace(tzinfo=timezone.utc)).days
        if days_since_delivery > 7:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Return window has expired (7 days from delivery)"
            )

    # pickup address
    pickup_address_id = data.pickup_address_id or order.address_id

    # return banao
    return_obj = Return(
        order_id=order_id,
        user_id=user_id,
        return_number=generate_return_number(),
        reason=data.reason,
        description=data.description,
        status="requested",
        pickup_address_id=pickup_address_id,
        refund_amount=order.total_amount,
    )
    db.add(return_obj)
    db.flush()

    # return items
    for item_data in data.items:
        order_item = db.query(OrderItem).filter(
            OrderItem.id == item_data.order_item_id,
            OrderItem.order_id == order_id,
        ).first()

        if not order_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order item not found"
            )

        return_item = ReturnItem(
            return_id=return_obj.id,
            order_item_id=item_data.order_item_id,
            quantity=item_data.quantity,
            condition=item_data.condition,
            images=item_data.images,
        )
        db.add(return_item)

    # order status update
    order.status = "return_requested"
    add_status_history(
        db, order.id, "return_requested",
        f"Return requested: {data.reason}"
    )

    db.commit()
    db.refresh(return_obj)
    return return_obj


# ─── Get Returns ──────────────────────────────────────────────────────────────

def get_order_returns(db: Session, order_id: str, user_id: str) -> List[Return]:
    order = get_order_by_id(db, order_id, user_id)
    return db.query(Return).filter(Return.order_id == order.id).all()