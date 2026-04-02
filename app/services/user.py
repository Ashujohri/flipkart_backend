from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from app.models.user import User, UserAddress, UserSession
from app.schemas.user import (
    UpdateProfile, AddressCreate, AddressUpdate
)
from app.core.security import verify_password, hash_password

# ─── Profile ──────────────────────────────────────────────────────────────────

def get_user_profile(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

def update_user_profile(db: Session, user: User, data: UpdateProfile) -> User:
    update_data = data.model_dump(exclude=True)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

def change__password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current passwor is incorrect")
    user.password_hash = hash_password(new_password)
    db.commit()

def deactivate_account(db: Session, user: User, password: str) -> None:
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, details="Password in incorrect")
    user.is_active = False
    db.commit()

# ─── Address ──────────────────────────────────────────────────────────────────

def get_addresses(db: Session, user_id: str) -> List[UserAddress]:
    return(
        db.query(UserAddress).filter(UserAddress.user_id == user_id)
        .order_by(UserAddress.is_default.desc(), UserAddress.created_at.desc())
        .all()
    )

def get_address_by_id(db: Session, address_id: str, user_id: str) -> UserAddress:
    address = db.query(UserAddress).filter(
        UserAddress.id == address_id,
        UserAddress.user_id == user_id,
    ).first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    return address

def create_address(db: Session, user_id: str, data: AddressCreate) -> UserAddress:
    # agar pehla address hai ya is_default=True → baaki sab default=False
    if data.is_default:
        db.query(UserAddress).filter(
            UserAddress.user_id == user_id,
            UserAddress.is_default == True,
        ).update({"is_default": False})
    
    # agar pehla address hai toh automatically default
    existing_count = db.query(UserAddress).filter(
        UserAddress.user_id == user_id
    ).count()
    
    address = UserAddress(
        user_id = user_id,
        full_name = data.full_name,
        phone = data.phone,
        address_line1=data.address_line1,
        address_line2=data.address_line2,
        city=data.city,
        state=data.state,
        pincode=data.pincode,
        country=data.country,
        address_type=data.address_type,
        is_default=data.is_default if existing_count > 0 else True,
        latitude=data.latitude,
        longitude=data.longitude,
    )
    
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def update_address(
    db: Session,
    address_id: str,
    user_id: str,
    data: AddressUpdate
) -> UserAddress:
    address = get_address_by_id(db, address_id, user_id)
    update_data = data.model_dump(exclude_unset=True)

    # agar default banana hai toh baaki sab false karo
    if update_data.get("is_default"):
        db.query(UserAddress).filter(
            UserAddress.user_id == user_id,
            UserAddress.is_default == True,
        ).update({"is_default": False})

    for field, value in update_data.items():
        setattr(address, field, value)

    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, address_id: str, user_id: str) -> None:
    address = get_address_by_id(db, address_id, user_id)

    was_default = address.is_default
    db.delete(address)
    db.commit()

    # agar default address delete hua toh next address ko default banao
    if was_default:
        next_address = db.query(UserAddress).filter(
            UserAddress.user_id == user_id,
        ).order_by(UserAddress.created_at.desc()).first()

        if next_address:
            next_address.is_default = True
            db.commit()


def set_default_address(db: Session, address_id: str, user_id: str) -> UserAddress:
    # pehle saare default false karo
    db.query(UserAddress).filter(
        UserAddress.user_id == user_id,
        UserAddress.is_default == True,
    ).update({"is_default": False})

    # ye wala default karo
    address = get_address_by_id(db, address_id, user_id)
    address.is_default = True
    db.commit()
    db.refresh(address)
    return address


# ─── Sessions ─────────────────────────────────────────────────────────────────

def get_active_sessions(db: Session, user_id: str) -> List[UserSession]:
    return (
        db.query(UserSession)
        .filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
        )
        .order_by(UserSession.created_at.desc())
        .all()
    )


def revoke_session(db: Session, session_id: str, user_id: str) -> None:
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == user_id,
        UserSession.is_active == True,
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session.is_active = False
    db.commit()
