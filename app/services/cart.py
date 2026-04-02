from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional

from app.models.product import Cart, CartItem, Product, ProductVariant, Inventory
from app.models.promo import Coupon, CouponUsage
from app.schemas.cart import CartItemAdd, CartItemUpdate


# ─── Helper ───────────────────────────────────────────────────────────────────

def get_or_create_cart(db: Session, user_id: str) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def calculate_cart_summary(cart: Cart, coupon_discount: Decimal = Decimal("0.00")) -> dict:
    subtotal = Decimal("0.00")
    total_discount = Decimal("0.00")
    item_count = 0

    for item in cart.items:
        product = item.product
        if not product:
            continue

        mrp = product.mrp
        selling_price = product.selling_price
        qty = item.quantity

        subtotal += selling_price * qty
        total_discount += (mrp - selling_price) * qty
        item_count += qty

    # delivery charge
    delivery_charge = Decimal("0.00") if subtotal >= 500 else Decimal("40.00")

    total_amount = subtotal - coupon_discount + delivery_charge
    total_saved = total_discount + coupon_discount

    return {
        "subtotal": subtotal,
        "total_discount": total_discount,
        "coupon_discount": coupon_discount,
        "delivery_charge": delivery_charge,
        "total_amount": max(total_amount, Decimal("0.00")),
        "total_saved": total_saved,
        "item_count": item_count,
    }


def build_cart_response(db: Session, cart: Cart) -> dict:
    # coupon discount calculate karo
    coupon_discount = Decimal("0.00")
    coupon_code = None

    if cart.coupon_id:
        coupon = db.query(Coupon).filter(Coupon.id == cart.coupon_id).first()
        if coupon and coupon.is_active:
            coupon_code = coupon.code
            summary_temp = calculate_cart_summary(cart)
            coupon_discount = calculate_coupon_discount(coupon, summary_temp["subtotal"])
        else:
            cart.coupon_id = None
            db.commit()

    summary = calculate_cart_summary(cart, coupon_discount)

    # items build karo
    items = []
    for item in cart.items:
        product = item.product
        if not product:
            continue

        inventory = db.query(Inventory).filter(
            Inventory.product_id == product.id
        ).first()

        available_stock = inventory.available_stock if inventory else 0
        is_available = product.status == "active" and available_stock > 0

        item_data = {
            "id": item.id,
            "product_id": item.product_id,
            "variant_id": item.variant_id,
            "quantity": item.quantity,
            "saved_price": item.saved_price,
            "product_name": product.name,
            "product_image": product.images[0].image_url if product.images else None,
            "mrp": product.mrp,
            "selling_price": product.selling_price,
            "discount_percent": product.discount_percent,
            "is_available": is_available,
            "stock_left": available_stock if available_stock <= 5 else None,
        }
        items.append(item_data)

    return {
        "id": cart.id,
        "items": items,
        "coupon_code": coupon_code,
        "coupon_discount": coupon_discount,
        "summary": summary,
    }


def calculate_coupon_discount(coupon: Coupon, subtotal: Decimal) -> Decimal:
    if subtotal < coupon.min_order_amount:
        return Decimal("0.00")

    if coupon.discount_type.value == "percentage":
        discount = subtotal * Decimal(str(coupon.discount_value)) / 100
        if coupon.max_discount_amount:
            discount = min(discount, coupon.max_discount_amount)
    else:
        discount = Decimal(str(coupon.discount_value))

    return min(discount, subtotal)


# ─── Get Cart ─────────────────────────────────────────────────────────────────

def get_cart(db: Session, user_id: str) -> dict:
    cart = get_or_create_cart(db, user_id)
    return build_cart_response(db, cart)


# ─── Add Item ─────────────────────────────────────────────────────────────────

def add_item_to_cart(db: Session, user_id: str, data: CartItemAdd) -> dict:
    # product exist karta hai?
    product = db.query(Product).filter(
        Product.id == data.product_id,
        Product.status == "active",
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or unavailable"
        )

    # stock check
    inventory = db.query(Inventory).filter(
        Inventory.product_id == data.product_id
    ).first()

    if not inventory or inventory.available_stock < data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock"
        )

    # variant check
    if data.variant_id:
        variant = db.query(ProductVariant).filter(
            ProductVariant.id == data.variant_id,
            ProductVariant.product_id == data.product_id,
            ProductVariant.is_active == True,
        ).first()
        if not variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Variant not found"
            )

    cart = get_or_create_cart(db, user_id)

    # already cart mein hai?
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == data.product_id,
        CartItem.variant_id == data.variant_id,
    ).first()

    if existing_item:
        # quantity update karo
        new_qty = existing_item.quantity + data.quantity
        if new_qty > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 items allowed per product"
            )
        if new_qty > inventory.available_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {inventory.available_stock} items available"
            )
        existing_item.quantity = new_qty
        existing_item.saved_price = product.selling_price
    else:
        item = CartItem(
            cart_id=cart.id,
            product_id=data.product_id,
            variant_id=data.variant_id,
            quantity=data.quantity,
            saved_price=product.selling_price,
        )
        db.add(item)

    db.commit()
    db.refresh(cart)
    return build_cart_response(db, cart)


# ─── Update Item ──────────────────────────────────────────────────────────────

def update_cart_item(
    db: Session,
    user_id: str,
    item_id: str,
    data: CartItemUpdate
) -> dict:
    cart = get_or_create_cart(db, user_id)

    item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id,
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )

    # stock check
    inventory = db.query(Inventory).filter(
        Inventory.product_id == item.product_id
    ).first()

    if inventory and data.quantity > inventory.available_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {inventory.available_stock} items available"
        )

    item.quantity = data.quantity
    db.commit()
    db.refresh(cart)
    return build_cart_response(db, cart)


# ─── Remove Item ──────────────────────────────────────────────────────────────

def remove_cart_item(db: Session, user_id: str, item_id: str) -> dict:
    cart = get_or_create_cart(db, user_id)

    item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id,
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )

    db.delete(item)
    db.commit()
    db.refresh(cart)
    return build_cart_response(db, cart)


# ─── Clear Cart ───────────────────────────────────────────────────────────────

def clear_cart(db: Session, user_id: str) -> dict:
    cart = get_or_create_cart(db, user_id)

    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    cart.coupon_id = None
    db.commit()
    db.refresh(cart)
    return build_cart_response(db, cart)


# ─── Apply Coupon ─────────────────────────────────────────────────────────────

def apply_coupon(db: Session, user_id: str, code: str) -> dict:
    cart = get_or_create_cart(db, user_id)

    if not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )

    # coupon exist karta hai?
    coupon = db.query(Coupon).filter(
        Coupon.code == code.upper(),
        Coupon.is_active == True,
    ).first()

    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid coupon code"
        )

    # expiry check
    now = datetime.now(timezone.utc)
    if now < coupon.valid_from.replace(tzinfo=timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon is not yet active"
        )
    if now > coupon.valid_until.replace(tzinfo=timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon has expired"
        )

    # total usage check
    if coupon.total_usage_limit and coupon.used_count >= coupon.total_usage_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon usage limit reached"
        )

    # per user limit check
    user_usage = db.query(CouponUsage).filter(
        CouponUsage.coupon_id == coupon.id,
        CouponUsage.user_id == user_id,
    ).count()

    if user_usage >= coupon.per_user_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already used this coupon"
        )

    # min order check
    summary = calculate_cart_summary(cart)
    if summary["subtotal"] < coupon.min_order_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum order amount is ₹{coupon.min_order_amount}"
        )

    cart.coupon_id = coupon.id
    db.commit()
    db.refresh(cart)
    return build_cart_response(db, cart)


# ─── Remove Coupon ────────────────────────────────────────────────────────────

def remove_coupon(db: Session, user_id: str) -> dict:
    cart = get_or_create_cart(db, user_id)
    cart.coupon_id = None
    db.commit()
    db.refresh(cart)
    return build_cart_response(db, cart)