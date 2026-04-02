from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta
from typing import Optional
import re

from app.models.user import User, UserSession
from app.schemas.auth import UserRegister, UserLogin
from app.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token, decode_token
)
from app.core.config import settings

# ─── Helper ───────────────────────────────────────────────────────────────────

def is_Email(value: str) -> bool:
    return "@" in value

def is_phone(value: str) -> bool:
    return re.match(r'^[6-9]\d{9}$', value) is not None

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_phone(db: Session, phone: str) -> Optional[User]:
    return db.query(User).filter(User.phone == phone).first()

def get_user_by_id(db:Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

# ─── Register ─────────────────────────────────────────────────────────────────

def register_user(db: Session, data:UserRegister) -> User:
    # email already exists?
    if get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    if get_user_by_phone(db, data.phone):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already registered"
        )
    
    user = User(
        full_name = data.full_name,
        email = data.email.lower().strip(),
        phone = data.phone,
        password_hash = hash_password(data.password),
        gender = data.gender,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return(user)

# ─── Login ────────────────────────────────────────────────────────────────────

def login_user(db: Session, data: UserLogin, device_info: dict) -> dict:
    # Finding user by email or phone
    user = None
    
    if is_Email(data.email_or_phone):
        user = get_user_by_email(db, data.email_or_phone.lower().strip())
    elif is_phone(data.email_or_phone):
        user = get_user_by_phone(db, data.email_or_phone.strip())
    
    # User not found or password is incorrect
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/phone or password"
        )
    
    # Account active?
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has bee suspended"
        )
    
    # Token create
    access_token = create_access_token(data={"sub": user.id, "role": user.role.value})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    # Session save
    session = UserSession(
        user_id = user.id,
        refresh_token = refresh_token,
        device_type = device_info.get("device_type"),
        device_name = device_info.get("device_name"),
        ip_address = device_info.get("ip_address"),
        expires_at = datetime.now(timezone.utc) + timedelta(days = settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    
    # Last login update
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "user": user,
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    }


# ─── Refresh Token ────────────────────────────────────────────────────────────

def refresh_access_token(db: Session, refresh_token: str) -> dict:
    # token decode
    payload = decode_token(refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # type check — access token 
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    # session DB exist?
    session = db.query(UserSession).filter(
        UserSession.refresh_token == refresh_token,
        UserSession.is_active == True,
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or expired"
        )

    # user exist?
    user = get_user_by_id(db, payload.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or suspended"
        )

    # Create new access token
    new_access_token = create_access_token(
        data={"sub": user.id, "role": user.role.value}
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
    }


# ─── Logout ───────────────────────────────────────────────────────────────────

def logout_user(db: Session, refresh_token: str) -> None:
    session = db.query(UserSession).filter(
        UserSession.refresh_token == refresh_token,
        UserSession.is_active == True,
    ).first()

    if session:
        session.is_active = False
        db.commit()


def logout_all_devices(db: Session, user_id: str) -> None:
    db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active == True,
    ).update({"is_active": False})
    db.commit()


# ─── Get Current User ─────────────────────────────────────────────────────────

def get_current_user(db: Session, token: str) -> User:
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    user = get_user_by_id(db, payload.get("sub"))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended"
        )

    return user