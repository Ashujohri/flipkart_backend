from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.models.admin import AdminUser
from app.core.security import decode_token

bearer_scheme = HTTPBearer()


# ─── Current User ─────────────────────────────────────────────────────────────

def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    return get_current_user(db, credentials.credentials)


# ─── Role based access ────────────────────────────────────────────────────────

def get_current_buyer(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role.value not in ["buyer", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Buyer access required"
        )
    return current_user


def get_current_seller(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role.value not in ["seller", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller access required"
        )
    return current_user


def get_current_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ─── Optional user — guest bhi access kar sake ────────────────────────────────

def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_db),
) -> User | None:
    if not credentials:
        return None
    try:
        return get_current_user(db, credentials.credentials)
    except HTTPException:
        return None