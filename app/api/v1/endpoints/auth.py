from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    LoginResponse,
    UserResponse,
    Token,
    RefreshTokenRequest,
    AccessTokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
)
from app.services.auth import (
    register_user,
    login_user,
    refresh_access_token,
    logout_user,
    logout_all_devices,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["Auth"])
bearer_scheme = HTTPBearer()


# ─── Register ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    return register_user(db, data)


# ─── Login ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
def login(data: UserLogin, request: Request, db: Session = Depends(get_db)):
    device_info = {
        "ip_address": request.client.host,
        "device_type": request.headers.get("X-Device-Type", "web"),
        "device_name": request.headers.get("X-Device-Name", "Unknown"),
    }
    return login_user(db, data, device_info)


# ─── Refresh Token ────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    return refresh_access_token(db, data.refresh_token)


# ─── Logout ───────────────────────────────────────────────────────────────────

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    data: RefreshTokenRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    logout_user(db, data.refresh_token)


# ─── Logout All Devices ───────────────────────────────────────────────────────

@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    user = get_current_user(db, credentials.credentials)
    logout_all_devices(db, user.id)


# ─── Me — current logged in user ──────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    return get_current_user(db, credentials.credentials)