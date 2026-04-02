from fastapi import APIRouter, Depends, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_admin
from app.models.user import User
from app.schemas.promo import (
    FlashSaleCreate, FlashSaleResponse,
    FlashSaleProductAdd, FlashSaleProductResponse,
    BannerCreate, BannerUpdate, BannerResponse,
    HomepageResponse,
)
from app.services import promo as promo_service

router = APIRouter(tags=["Promotions"])


# ─── Homepage ─────────────────────────────────────────────────────────────────

@router.get("/homepage", response_model=HomepageResponse)
def get_homepage(db: Session = Depends(get_db)):
    return promo_service.get_homepage_data(db)


# ─── Flash Sales ──────────────────────────────────────────────────────────────

@router.get("/flash-sales", response_model=List[FlashSaleResponse])
def get_flash_sales(db: Session = Depends(get_db)):
    return promo_service.get_active_flash_sales(db)


@router.post("/flash-sales", response_model=FlashSaleResponse, status_code=status.HTTP_201_CREATED)
def create_flash_sale(
    data: FlashSaleCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return promo_service.create_flash_sale(db, data, current_user.id)


@router.post("/flash-sales/{sale_id}/products", response_model=FlashSaleProductResponse, status_code=status.HTTP_201_CREATED)
def add_product_to_sale(
    sale_id: str,
    data: FlashSaleProductAdd,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return promo_service.add_product_to_flash_sale(db, sale_id, data)


@router.patch("/flash-sales/{sale_id}/toggle")
def toggle_flash_sale(
    sale_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return promo_service.toggle_flash_sale(db, sale_id)


# ─── Banners ──────────────────────────────────────────────────────────────────

@router.get("/banners", response_model=List[BannerResponse])
def get_banners(
    position: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    if position:
        return promo_service.get_banners_by_position(db, position)
    return promo_service.get_all_banners(db)


@router.post("/banners", response_model=BannerResponse, status_code=status.HTTP_201_CREATED)
def create_banner(
    data: BannerCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return promo_service.create_banner(db, data, current_user.id)


@router.post("/banners/{banner_id}/image", response_model=BannerResponse)
async def upload_banner_image(
    banner_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    from app.utils.file_upload import upload_image
    url = await upload_image(file, "banner")
    return promo_service.update_banner(
        db, banner_id,
        type('obj', (object,), {'model_dump': lambda self, **kw: {"image_url": url}})()
    )


@router.patch("/banners/{banner_id}", response_model=BannerResponse)
def update_banner(
    banner_id: str,
    data: BannerUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return promo_service.update_banner(db, banner_id, data)


@router.delete("/banners/{banner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_banner(
    banner_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    promo_service.delete_banner(db, banner_id)