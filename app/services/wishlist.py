from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List

from app.models.user import Wishlist, WishlistItem
from app.models.product import Product, ProductVariant
from app.schemas.wishlist import WishlistCreate, WishlistItemAdd


def get_or_create_default_wishlist(db: Session, user_id: str) -> Wishlist:
    wishlist = db.query(Wishlist).filter(
        Wishlist.user_id == user_id
    ).first()
    if not wishlist:
        wishlist = Wishlist(
            user_id=user_id,
            name="My Wishlist",
            is_public=False,
        )
        db.add(wishlist)
        db.commit()
        db.refresh(wishlist)
    return wishlist


def get_wishlists(db: Session, user_id: str) -> List[Wishlist]:
    return db.query(Wishlist).filter(
        Wishlist.user_id == user_id
    ).all()


def get_wishlist_by_id(db: Session, wishlist_id: str, user_id: str) -> Wishlist:
    wishlist = db.query(Wishlist).filter(
        Wishlist.id == wishlist_id,
        Wishlist.user_id == user_id,
    ).first()
    if not wishlist:
        raise HTTPException(status_code=404, detail="Wishlist not found")
    return wishlist


def create_wishlist(db: Session, user_id: str, data: WishlistCreate) -> Wishlist:
    wishlist = Wishlist(
        user_id=user_id,
        name=data.name,
        is_public=data.is_public,
    )
    db.add(wishlist)
    db.commit()
    db.refresh(wishlist)
    return wishlist


def delete_wishlist(db: Session, wishlist_id: str, user_id: str) -> None:
    wishlist = get_wishlist_by_id(db, wishlist_id, user_id)
    db.delete(wishlist)
    db.commit()


def build_wishlist_response(db: Session, wishlist: Wishlist) -> dict:
    items = []
    for item in wishlist.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            continue
        items.append({
            "id": item.id,
            "product_id": item.product_id,
            "variant_id": item.variant_id,
            "product_name": product.name,
            "product_image": product.images[0].image_url if product.images else None,
            "mrp": product.mrp,
            "selling_price": product.selling_price,
            "discount_percent": product.discount_percent,
            "is_available": product.status == "active",
            "added_at": item.added_at,
        })
    return {
        "id": wishlist.id,
        "name": wishlist.name,
        "is_public": wishlist.is_public,
        "item_count": len(items),
        "items": items,
        "created_at": wishlist.created_at,
    }


def add_item(db: Session, wishlist_id: str, user_id: str, data: WishlistItemAdd) -> dict:
    wishlist = get_wishlist_by_id(db, wishlist_id, user_id)

    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(WishlistItem).filter(
        WishlistItem.wishlist_id == wishlist_id,
        WishlistItem.product_id == data.product_id,
        WishlistItem.variant_id == data.variant_id,
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product already in wishlist"
        )

    item = WishlistItem(
        wishlist_id=wishlist_id,
        product_id=data.product_id,
        variant_id=data.variant_id,
    )
    db.add(item)
    db.commit()
    db.refresh(wishlist)
    return build_wishlist_response(db, wishlist)


def remove_item(db: Session, wishlist_id: str, item_id: str, user_id: str) -> dict:
    wishlist = get_wishlist_by_id(db, wishlist_id, user_id)

    item = db.query(WishlistItem).filter(
        WishlistItem.id == item_id,
        WishlistItem.wishlist_id == wishlist_id,
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    db.refresh(wishlist)
    return build_wishlist_response(db, wishlist)


def move_to_cart(db: Session, wishlist_id: str, item_id: str, user_id: str) -> None:
    wishlist = get_wishlist_by_id(db, wishlist_id, user_id)

    item = db.query(WishlistItem).filter(
        WishlistItem.id == item_id,
        WishlistItem.wishlist_id == wishlist_id,
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    from app.services.cart import add_item_to_cart
    from app.schemas.cart import CartItemAdd

    cart_data = CartItemAdd(
        product_id=item.product_id,
        variant_id=item.variant_id,
        quantity=1,
    )
    add_item_to_cart(db, user_id, cart_data)

    db.delete(item)
    db.commit()