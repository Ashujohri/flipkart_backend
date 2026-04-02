from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.user import (
    UpdateProfile,
    AddressCreate,
    AddressUpdate,
    AddressResponse,
    UserProfileResponse,
    SessionResponse,
)
from app.schemas.auth import ChangePasswordRequest
from app.services import user as user_service

router = APIRouter(prefix="/user", tags=["User"])

# ─── Profile Picture ──────────────────────────────────────────────────────────

@router.post("/profile/picture", response_model=UserProfileResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from app.utils.file_upload import upload_image, delete_image

    # purani picture delete karo
    if current_user.profile_picture_url:
        await delete_image(current_user.profile_picture_url)

    # nayi upload karo
    url = await upload_image(file, "profile")

    # DB update karo
    current_user.profile_picture_url = url
    db.commit()
    db.refresh(current_user)
    return current_user

# ─── Profile ──────────────────────────────────────────────────────────────────

@router.get("/profile", response_model=UserProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return user_service.get_user_profile(db, current_user.id)


@router.patch("/profile", response_model=UserProfileResponse)
def update_profile(
    data: UpdateProfile,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return user_service.update_user_profile(db, current_user, data)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    user_service.change_password(
        db, current_user,
        data.current_password,
        data.new_password,
    )


@router.delete("/deactivate", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_account(
    password: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    user_service.deactivate_account(db, current_user, password)


# ─── Addresses ────────────────────────────────────────────────────────────────

@router.get("/addresses", response_model=List[AddressResponse])
def get_addresses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return user_service.get_addresses(db, current_user.id)


@router.post("/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(
    data: AddressCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return user_service.create_address(db, current_user.id, data)


@router.get("/addresses/{address_id}", response_model=AddressResponse)
def get_address(
    address_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return user_service.get_address_by_id(db, address_id, current_user.id)


@router.patch("/addresses/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: str,
    data: AddressUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return user_service.update_address(db, address_id, current_user.id, data)


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(
    address_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    user_service.delete_address(db, address_id, current_user.id)


@router.patch("/addresses/{address_id}/set-default", response_model=AddressResponse)
def set_default_address(
    address_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return user_service.set_default_address(db, address_id, current_user.id)


# ─── Sessions ─────────────────────────────────────────────────────────────────

@router.get("/sessions", response_model=List[SessionResponse])
def get_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return user_service.get_active_sessions(db, current_user.id)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    user_service.revoke_session(db, session_id, current_user.id)