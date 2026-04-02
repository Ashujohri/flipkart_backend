from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal

from app.core.database import get_db
from app.schemas.search import (
    SearchFilters,
    PaginatedSearch,
    SearchSuggestion,
)
from app.services import search as search_service

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=PaginatedSearch)
def search(
    q: str = Query(min_length=1),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="relevance"),
    category_id: Optional[str] = Query(default=None),
    brand_id: Optional[str] = Query(default=None),
    min_price: Optional[Decimal] = Query(default=None),
    max_price: Optional[Decimal] = Query(default=None),
    min_rating: Optional[float] = Query(default=None),
    is_cod_available: Optional[bool] = Query(default=None),
    discount_min: Optional[float] = Query(default=None),
    in_stock_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    filters = SearchFilters(
        category_id=category_id,
        brand_id=brand_id,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        is_cod_available=is_cod_available,
        discount_min=discount_min,
        in_stock_only=in_stock_only,
    )
    return search_service.search_products(db, q, filters, page, per_page, sort_by)


@router.get("/suggestions", response_model=SearchSuggestion)
def get_suggestions(
    q: str = Query(min_length=2),
    db: Session = Depends(get_db),
):
    suggestions = search_service.get_suggestions(db, q)
    return {"suggestions": suggestions, "query": q}