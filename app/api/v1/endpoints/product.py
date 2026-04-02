from fastapi import APIRouter, Depends, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from app.core.database import get_db
from app.core.dependencies import (
    get_current_active_user,
    get_current_seller,
    get_optional_user,
)
from app.models.user import User
from app.schemas.product import (
    CategoryCreate, CategoryResponse,
    BrandCreate, BrandResponse,
    ProductCreate, ProductUpdate, ProductResponse,
    ProductListResponse, PaginatedProducts,
    VariantCreate, VariantResponse,
    SpecificationCreate, SpecificationResponse,
    InventoryUpdate, InventoryResponse,
    ProductImageResponse,
)
from app.services import product as product_service

router = APIRouter(prefix="/products", tags=["Products"])


# ─── Categories ───────────────────────────────────────────────────────────────

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return product_service.get_all_categories(db)


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return product_service.create_category(db, data)


# ─── Brands ───────────────────────────────────────────────────────────────────

@router.get("/brands", response_model=List[BrandResponse])
def get_brands(db: Session = Depends(get_db)):
    return product_service.get_all_brands(db)


@router.post("/brands", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
def create_brand(
    data: BrandCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return product_service.create_brand(db, data)


# ─── Products ─────────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedProducts)
def get_products(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    category_id: Optional[str] = Query(default=None),
    brand_id: Optional[str] = Query(default=None),
    min_price: Optional[Decimal] = Query(default=None),
    max_price: Optional[Decimal] = Query(default=None),
    search: Optional[str] = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    return product_service.get_products(
        db, page, per_page, category_id,
        brand_id, min_price, max_price,
        search, sort_by, sort_order,
    )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    from app.models.seller import Seller
    seller = db.query(Seller).filter(Seller.user_id == current_user.id).first()
    if not seller:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Seller profile not found")
    return product_service.create_product(db, seller.id, data)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
):
    return product_service.get_product_by_id(db, product_id)


@router.get("/slug/{slug}", response_model=ProductResponse)
def get_product_by_slug(
    slug: str,
    db: Session = Depends(get_db),
):
    return product_service.get_product_by_slug(db, slug)


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: str,
    data: ProductUpdate,
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    from app.models.seller import Seller
    seller = db.query(Seller).filter(Seller.user_id == current_user.id).first()
    return product_service.update_product(db, product_id, seller.id, data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    from app.models.seller import Seller
    seller = db.query(Seller).filter(Seller.user_id == current_user.id).first()
    product_service.delete_product(db, product_id, seller.id)


# ─── Variants ─────────────────────────────────────────────────────────────────

@router.post("/{product_id}/variants", response_model=VariantResponse, status_code=status.HTTP_201_CREATED)
def add_variant(
    product_id: str,
    data: VariantCreate,
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    from app.models.seller import Seller
    seller = db.query(Seller).filter(Seller.user_id == current_user.id).first()
    return product_service.add_variant(db, product_id, seller.id, data)


# ─── Images ───────────────────────────────────────────────────────────────────

@router.post("/{product_id}/images", response_model=ProductImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_product_image(
    product_id: str,
    file: UploadFile = File(...),
    is_primary: bool = False,
    alt_text: Optional[str] = None,
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    from app.utils.file_upload import upload_image
    url = await upload_image(file, "product")
    return product_service.add_product_image(db, product_id, url, is_primary, alt_text)


@router.delete("/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_image(
    product_id: str,
    image_id: str,
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    product_service.delete_product_image(db, image_id, product_id)


# ─── Specifications ───────────────────────────────────────────────────────────

@router.post("/{product_id}/specifications", response_model=SpecificationResponse, status_code=status.HTTP_201_CREATED)
def add_specification(
    product_id: str,
    data: SpecificationCreate,
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    return product_service.add_specification(db, product_id, data)


@router.delete("/{product_id}/specifications/{spec_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_specification(
    product_id: str,
    spec_id: str,
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    product_service.delete_specification(db, spec_id, product_id)


# ─── Inventory ────────────────────────────────────────────────────────────────

@router.patch("/{product_id}/inventory", response_model=InventoryResponse)
def update_inventory(
    product_id: str,
    data: InventoryUpdate,
    current_user: User = Depends(get_current_seller),
    db: Session = Depends(get_db),
):
    from app.models.seller import Seller
    seller = db.query(Seller).filter(Seller.user_id == current_user.id).first()
    return product_service.update_inventory(db, product_id, seller.id, data)