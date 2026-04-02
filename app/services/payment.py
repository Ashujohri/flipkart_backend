from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, List
import hmac
import hashlib

from app.models.payment import Payment, Refund, Wallet, WalletTransaction, PaymentMethod
from app.models.order import Order, OrderStatusHistory
from app.schemas.payment import (
    InitiatePaymentRequest,
    VerifyPaymentRequest,
)
from app.core.config import settings


# ─── Helper ───────────────────────────────────────────────────────────────────

def get_or_create_wallet(db: Session, user_id: str) -> Wallet:
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=Decimal("0.00"))
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return wallet


def add_wallet_transaction(
    db: Session,
    wallet: Wallet,
    type_: str,
    reason: str,
    amount: Decimal,
    description: Optional[str] = None,
    reference_id: Optional[str] = None,
) -> WalletTransaction:
    balance_before = wallet.balance

    if type_ == "credit":
        wallet.balance += amount
    else:
        wallet.balance -= amount

    transaction = WalletTransaction(
        wallet_id=wallet.id,
        type=type_,
        reason=reason,
        amount=amount,
        balance_before=balance_before,
        balance_after=wallet.balance,
        description=description,
        reference_id=reference_id,
    )
    db.add(transaction)
    return transaction


def verify_razorpay_signature(
    gateway_order_id: str,
    gateway_payment_id: str,
    signature: str,
) -> bool:
    message = f"{gateway_order_id}|{gateway_payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ─── Initiate Payment ─────────────────────────────────────────────────────────

def initiate_payment(
    db: Session,
    user_id: str,
    data: InitiatePaymentRequest,
) -> dict:
    # order check
    order = db.query(Order).filter(
        Order.id == data.order_id,
        Order.user_id == user_id,
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.status.value != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is not in pending state"
        )

    # wallet payment
    if data.gateway == "wallet":
        wallet = get_or_create_wallet(db, user_id)
        if wallet.balance < order.total_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient wallet balance. Available: ₹{wallet.balance}"
            )

        payment = Payment(
            order_id=order.id,
            user_id=user_id,
            gateway="wallet",
            status="success",
            amount=order.total_amount,
            currency="INR",
            paid_at=datetime.now(timezone.utc),
        )
        db.add(payment)
        db.flush()

        # wallet se deduct karo
        add_wallet_transaction(
            db, wallet,
            type_="debit",
            reason="order_payment",
            amount=order.total_amount,
            description=f"Payment for order {order.order_number}",
            reference_id=order.id,
        )

        # order confirm karo
        order.status = "confirmed"
        history = OrderStatusHistory(
            order_id=order.id,
            status="confirmed",
            message="Payment successful via wallet"
        )
        db.add(history)
        db.commit()

        return {
            "payment_id": payment.id,
            "gateway_order_id": payment.id,
            "amount": order.total_amount,
            "currency": "INR",
            "gateway": "wallet",
            "key_id": "",
        }

    # Razorpay payment — abhi mock karenge
    # TODO: real Razorpay API call
    # import razorpay
    # client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))
    # razorpay_order = client.order.create({
    #     "amount": int(order.total_amount * 100),  # paise mein
    #     "currency": "INR",
    #     "receipt": order.order_number,
    # })
    # gateway_order_id = razorpay_order["id"]

    mock_gateway_order_id = f"order_mock_{order.id[:8]}"

    payment = Payment(
        order_id=order.id,
        user_id=user_id,
        gateway=data.gateway,
        status="initiated",
        amount=order.total_amount,
        currency="INR",
        gateway_order_id=mock_gateway_order_id,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {
        "payment_id": payment.id,
        "gateway_order_id": mock_gateway_order_id,
        "amount": order.total_amount,
        "currency": "INR",
        "gateway": data.gateway,
        "key_id": settings.RAZORPAY_KEY_ID,
    }


# ─── Verify Payment ───────────────────────────────────────────────────────────

def verify_payment(
    db: Session,
    user_id: str,
    data: VerifyPaymentRequest,
) -> Payment:
    order = db.query(Order).filter(
        Order.id == data.order_id,
        Order.user_id == user_id,
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    payment = db.query(Payment).filter(
        Payment.order_id == order.id,
        Payment.gateway_order_id == data.gateway_order_id,
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    # signature verify karo — mock mein skip
    # real mein:
    # if not verify_razorpay_signature(
    #     data.gateway_order_id,
    #     data.gateway_payment_id,
    #     data.gateway_signature
    # ):
    #     payment.status = "failed"
    #     db.commit()
    #     raise HTTPException(400, "Payment verification failed")

    # payment success
    payment.status = "success"
    payment.gateway_payment_id = data.gateway_payment_id
    payment.gateway_signature = data.gateway_signature
    payment.paid_at = datetime.now(timezone.utc)

    # order confirm karo
    order.status = "confirmed"
    history = OrderStatusHistory(
        order_id=order.id,
        status="confirmed",
        message="Payment verified successfully"
    )
    db.add(history)

    db.commit()
    db.refresh(payment)
    return payment


# ─── Get Payment ──────────────────────────────────────────────────────────────

def get_payment_by_order(db: Session, order_id: str, user_id: str) -> Payment:
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user_id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


# ─── Refund ───────────────────────────────────────────────────────────────────

def process_refund(
    db: Session,
    order_id: str,
    user_id: str,
    refund_to: str = "wallet",
) -> Refund:
    payment = get_payment_by_order(db, order_id, user_id)

    if payment.status.value != "success":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment is not in success state"
        )

    # existing refund check
    existing = db.query(Refund).filter(
        Refund.payment_id == payment.id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Refund already initiated"
        )

    refund = Refund(
        payment_id=payment.id,
        order_id=order_id,
        user_id=user_id,
        amount=payment.amount,
        status="processing",
        refund_to=refund_to,
        initiated_at=datetime.now(timezone.utc),
    )
    db.add(refund)

    # wallet mein refund
    if refund_to == "wallet":
        wallet = get_or_create_wallet(db, user_id)
        add_wallet_transaction(
            db, wallet,
            type_="credit",
            reason="refund",
            amount=payment.amount,
            description=f"Refund for order {order_id[:8]}",
            reference_id=order_id,
        )
        refund.status = "completed"
        refund.completed_at = datetime.now(timezone.utc)
        payment.status = "refunded"

    db.commit()
    db.refresh(refund)
    return refund


# ─── Wallet ───────────────────────────────────────────────────────────────────

def get_wallet(db: Session, user_id: str) -> Wallet:
    return get_or_create_wallet(db, user_id)


def get_wallet_transactions(
    db: Session,
    user_id: str,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    wallet = get_or_create_wallet(db, user_id)

    query = db.query(WalletTransaction).filter(
        WalletTransaction.wallet_id == wallet.id
    ).order_by(WalletTransaction.created_at.desc())

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


# ─── Payment Methods ──────────────────────────────────────────────────────────

def get_payment_methods(db: Session, user_id: str) -> List[PaymentMethod]:
    return db.query(PaymentMethod).filter(
        PaymentMethod.user_id == user_id
    ).order_by(PaymentMethod.is_default.desc()).all()


def delete_payment_method(
    db: Session,
    method_id: str,
    user_id: str,
) -> None:
    method = db.query(PaymentMethod).filter(
        PaymentMethod.id == method_id,
        PaymentMethod.user_id == user_id,
    ).first()
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    db.delete(method)
    db.commit()