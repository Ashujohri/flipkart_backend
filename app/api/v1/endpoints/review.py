from fastapi import APIRouter, Depends, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_optional_user
from app.models.user import User
from app.schemas.review import (
    ReviewCreate, ReviewUpdate,
    ReviewResponse, PaginatedReviews,
    ReviewImageResponse,
    VoteRequest,
    SellerResponseRequest,
    QuestionCreate, AnswerCreate,
    QuestionResponse, PaginatedQuestions,
    AnswerResponse,
)
from app.services import review as review_service

router = APIRouter(tags=["Reviews & Questions"])


# ─── Product Reviews ──────────────────────────────────────────────────────────

@router.get("/products/{product_id}/reviews", response_model=PaginatedReviews)
def get_reviews(
    product_id: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=50),
    rating: Optional[int] = Query(default=None, ge=1, le=5),
    sort_by: str = Query(default="created_at"),
    db: Session = Depends(get_db),
):
    return review_service.get_product_reviews(
        db, product_id, page, per_page, rating, sort_by
    )


@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    data: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return review_service.create_review(db, current_user.id, data)


@router.patch("/reviews/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: str,
    data: ReviewUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return review_service.update_review(db, review_id, current_user.id, data)


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    review_service.delete_review(db, review_id, current_user.id)


@router.post("/reviews/{review_id}/vote", response_model=ReviewResponse)
def vote_review(
    review_id: str,
    data: VoteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return review_service.vote_review(db, review_id, current_user.id, data)


@router.post("/reviews/{review_id}/seller-response", response_model=ReviewResponse)
def add_seller_response(
    review_id: str,
    data: SellerResponseRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return review_service.add_seller_response(db, review_id, current_user.id, data)


@router.post("/reviews/{review_id}/images", response_model=ReviewImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_review_image(
    review_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from app.utils.file_upload import upload_image
    url = await upload_image(file, "review")
    return review_service.add_review_image(db, review_id, current_user.id, url)


# ─── Questions ────────────────────────────────────────────────────────────────

@router.get("/products/{product_id}/questions", response_model=PaginatedQuestions)
def get_questions(
    product_id: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return review_service.get_product_questions(db, product_id, page, per_page)


@router.post("/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    data: QuestionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return review_service.create_question(db, current_user.id, data)


@router.post("/questions/{question_id}/answers", response_model=AnswerResponse, status_code=status.HTTP_201_CREATED)
def create_answer(
    question_id: str,
    data: AnswerCreate,
    is_seller: bool = Query(default=False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return review_service.create_answer(
        db, question_id, current_user.id, data, is_seller
    )