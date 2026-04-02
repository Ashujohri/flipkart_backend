from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.wishlist import (
    WishlistCreate,
    WishlistItemAdd,
    WishlistResponse,
)
from app.services import wishlist as wishlist_service

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


@router.get("", response_model=List[WishlistResponse])
def get_wishlists(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    wishlists = wishlist_service.get_wishlists(db, current_user.id)
    return [wishlist_service.build_wishlist_response(db, w) for w in wishlists]


@router.post("", response_model=WishlistResponse, status_code=status.HTTP_201_CREATED)
def create_wishlist(
    data: WishlistCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    wishlist = wishlist_service.create_wishlist(db, current_user.id, data)
    return wishlist_service.build_wishlist_response(db, wishlist)


@router.get("/{wishlist_id}", response_model=WishlistResponse)
def get_wishlist(
    wishlist_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    wishlist = wishlist_service.get_wishlist_by_id(db, wishlist_id, current_user.id)
    return wishlist_service.build_wishlist_response(db, wishlist)


@router.delete("/{wishlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wishlist(
    wishlist_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    wishlist_service.delete_wishlist(db, wishlist_id, current_user.id)


@router.post("/{wishlist_id}/items", response_model=WishlistResponse)
def add_item(
    wishlist_id: str,
    data: WishlistItemAdd,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return wishlist_service.add_item(db, wishlist_id, current_user.id, data)


@router.delete("/{wishlist_id}/items/{item_id}", response_model=WishlistResponse)
def remove_item(
    wishlist_id: str,
    item_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return wishlist_service.remove_item(db, wishlist_id, item_id, current_user.id)


@router.post("/{wishlist_id}/items/{item_id}/move-to-cart", status_code=status.HTTP_204_NO_CONTENT)
def move_to_cart(
    wishlist_id: str,
    item_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    wishlist_service.move_to_cart(db, wishlist_id, item_id, current_user.id)