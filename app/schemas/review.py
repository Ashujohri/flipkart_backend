from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


# ─── Review ───────────────────────────────────────────────────────────────────

class ReviewCreate(BaseModel):
    product_id: str
    order_item_id: Optional[str] = None
    rating: int
    title: Optional[str] = None
    body: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if v is None:
            return v
        v = v.strip()
        if len(v) > 255:
            raise ValueError("Title must be less than 255 characters")
        return v

    @field_validator("body")
    @classmethod
    def validate_body(cls, v):
        if v is None:
            return v
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Review must be at least 10 characters")
        return v


class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    title: Optional[str] = None
    body: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v):
        if v is None:
            return v
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class SellerResponseRequest(BaseModel):
    response: str

    @field_validator("response")
    @classmethod
    def validate_response(cls, v):
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Response must be at least 10 characters")
        if len(v) > 1000:
            raise ValueError("Response must be less than 1000 characters")
        return v


# ─── Vote ─────────────────────────────────────────────────────────────────────

class VoteRequest(BaseModel):
    vote_type: str

    @field_validator("vote_type")
    @classmethod
    def validate_vote_type(cls, v):
        if v not in ["helpful", "not_helpful"]:
            raise ValueError("Vote type must be helpful or not_helpful")
        return v


# ─── Question ─────────────────────────────────────────────────────────────────

class QuestionCreate(BaseModel):
    product_id: str
    body: str

    @field_validator("body")
    @classmethod
    def validate_body(cls, v):
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Question must be at least 10 characters")
        if len(v) > 500:
            raise ValueError("Question must be less than 500 characters")
        return v


class AnswerCreate(BaseModel):
    body: str

    @field_validator("body")
    @classmethod
    def validate_body(cls, v):
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Answer must be at least 5 characters")
        return v


# ─── Responses ────────────────────────────────────────────────────────────────

class ReviewImageResponse(BaseModel):
    id: str
    image_url: str
    display_order: int

    model_config = {"from_attributes": True}


class ReviewUserResponse(BaseModel):
    id: str
    full_name: str
    profile_picture_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ReviewResponse(BaseModel):
    id: str
    product_id: str
    rating: int
    title: Optional[str] = None
    body: Optional[str] = None
    status: str
    is_verified_purchase: bool
    helpful_count: int
    not_helpful_count: int
    seller_response: Optional[str] = None
    seller_responded_at: Optional[datetime] = None
    user: Optional[ReviewUserResponse] = None
    images: List[ReviewImageResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedReviews(BaseModel):
    items: List[ReviewResponse]
    total: int
    page: int
    per_page: int
    pages: int
    rating_summary: dict


class AnswerResponse(BaseModel):
    id: str
    body: str
    is_seller_answer: bool
    helpful_count: int
    user: Optional[ReviewUserResponse] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionResponse(BaseModel):
    id: str
    product_id: str
    body: str
    is_answered: bool
    answers: List[AnswerResponse] = []
    user: Optional[ReviewUserResponse] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedQuestions(BaseModel):
    items: List[QuestionResponse]
    total: int
    page: int
    per_page: int
    pages: int