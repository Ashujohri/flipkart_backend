from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal


class SearchFilters(BaseModel):
    category_id: Optional[str] = None
    brand_id: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_rating: Optional[float] = None
    is_cod_available: Optional[bool] = None
    discount_min: Optional[float] = None
    in_stock_only: bool = False


class SearchResult(BaseModel):
    id: str
    name: str
    slug: str
    mrp: Decimal
    selling_price: Decimal
    discount_percent: float
    rating_avg: float
    rating_count: int
    is_cod_available: bool
    primary_image: Optional[str] = None
    brand_name: Optional[str] = None
    category_name: Optional[str] = None

    model_config = {"from_attributes": True}


class PaginatedSearch(BaseModel):
    items: List[SearchResult]
    total: int
    page: int
    per_page: int
    pages: int
    query: str
    filters_applied: dict


class SearchSuggestion(BaseModel):
    suggestions: List[str]
    query: str