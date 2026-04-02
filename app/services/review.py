from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from typing import Optional, List
from datetime import datetime, timezone

from app.models.review import Review, ReviewImage, ReviewVote, Question, Answer
from app.models.product import Product
from app.models.order import OrderItem
from app.models.seller import Seller
from app.schemas.review import (
    ReviewCreate, ReviewUpdate,
    QuestionCreate, AnswerCreate,
    VoteRequest, SellerResponseRequest,
)


# ─── Review ───────────────────────────────────────────────────────────────────

def get_product_reviews(
    db: Session,
    product_id: str,
    page: int = 1,
    per_page: int = 10,
    rating_filter: Optional[int] = None,
    sort_by: str = "created_at",
) -> dict:
    # product exist karta hai?
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    query = db.query(Review).filter(
        Review.product_id == product_id,
        Review.status == "approved",
    )

    if rating_filter:
        query = query.filter(Review.rating == rating_filter)

    # sorting
    if sort_by == "helpful":
        query = query.order_by(Review.helpful_count.desc())
    elif sort_by == "rating_high":
        query = query.order_by(Review.rating.desc())
    elif sort_by == "rating_low":
        query = query.order_by(Review.rating.asc())
    else:
        query = query.order_by(Review.created_at.desc())

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    # rating summary
    rating_summary = {}
    for i in range(1, 6):
        count = db.query(Review).filter(
            Review.product_id == product_id,
            Review.status == "approved",
            Review.rating == i,
        ).count()
        rating_summary[str(i)] = count

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "rating_summary": rating_summary,
    }


def create_review(db: Session, user_id: str, data: ReviewCreate) -> Review:
    # product exist karta hai?
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # already review diya hai?
    existing = db.query(Review).filter(
        Review.product_id == data.product_id,
        Review.user_id == user_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this product"
        )

    # verified purchase check
    is_verified = False
    if data.order_item_id:
        order_item = db.query(OrderItem).filter(
            OrderItem.id == data.order_item_id,
            OrderItem.product_id == data.product_id,
        ).first()
        if order_item:
            is_verified = True
            order_item.is_reviewed = True

    review = Review(
        product_id=data.product_id,
        user_id=user_id,
        order_item_id=data.order_item_id,
        rating=data.rating,
        title=data.title,
        body=data.body,
        is_verified_purchase=is_verified,
        status="approved",  # real mein "pending" hoga — moderation ke baad approve
    )
    db.add(review)
    db.flush()

    # product rating update karo
    update_product_rating(db, data.product_id)

    db.commit()
    db.refresh(review)
    return review


def update_review(
    db: Session,
    review_id: str,
    user_id: str,
    data: ReviewUpdate,
) -> Review:
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.user_id == user_id,
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)

    db.commit()
    db.refresh(review)

    # rating update karo
    update_product_rating(db, review.product_id)
    return review


def delete_review(db: Session, review_id: str, user_id: str) -> None:
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.user_id == user_id,
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    product_id = review.product_id
    db.delete(review)
    db.commit()
    update_product_rating(db, product_id)


def update_product_rating(db: Session, product_id: str) -> None:
    result = db.query(
        func.avg(Review.rating).label("avg"),
        func.count(Review.id).label("count"),
    ).filter(
        Review.product_id == product_id,
        Review.status == "approved",
    ).first()

    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.rating_avg = round(float(result.avg or 0), 1)
        product.rating_count = result.count or 0
        db.commit()


def add_seller_response(
    db: Session,
    review_id: str,
    seller_user_id: str,
    data: SellerResponseRequest,
) -> Review:
    # seller check
    seller = db.query(Seller).filter(
        Seller.user_id == seller_user_id
    ).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # seller ka product hai?
    product = db.query(Product).filter(
        Product.id == review.product_id,
        Product.seller_id == seller.id,
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only respond to reviews of your own products"
        )

    review.seller_response = data.response
    review.seller_responded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(review)
    return review


# ─── Vote ─────────────────────────────────────────────────────────────────────

def vote_review(
    db: Session,
    review_id: str,
    user_id: str,
    data: VoteRequest,
) -> Review:
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # apni review pe vote nahi kar sakte
    if review.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot vote on your own review"
        )

    # existing vote check
    existing_vote = db.query(ReviewVote).filter(
        ReviewVote.review_id == review_id,
        ReviewVote.user_id == user_id,
    ).first()

    if existing_vote:
        # same vote → remove
        if existing_vote.vote_type.value == data.vote_type:
            if data.vote_type == "helpful":
                review.helpful_count -= 1
            else:
                review.not_helpful_count -= 1
            db.delete(existing_vote)
        else:
            # different vote → change
            if data.vote_type == "helpful":
                review.helpful_count += 1
                review.not_helpful_count -= 1
            else:
                review.helpful_count -= 1
                review.not_helpful_count += 1
            existing_vote.vote_type = data.vote_type
    else:
        # naya vote
        vote = ReviewVote(
            review_id=review_id,
            user_id=user_id,
            vote_type=data.vote_type,
        )
        db.add(vote)
        if data.vote_type == "helpful":
            review.helpful_count += 1
        else:
            review.not_helpful_count += 1

    db.commit()
    db.refresh(review)
    return review


# ─── Review Images ────────────────────────────────────────────────────────────

def add_review_image(
    db: Session,
    review_id: str,
    user_id: str,
    image_url: str,
) -> ReviewImage:
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.user_id == user_id,
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    count = db.query(ReviewImage).filter(
        ReviewImage.review_id == review_id
    ).count()

    if count >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 images allowed per review"
        )

    image = ReviewImage(
        review_id=review_id,
        image_url=image_url,
        display_order=count,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


# ─── Questions ────────────────────────────────────────────────────────────────

def get_product_questions(
    db: Session,
    product_id: str,
    page: int = 1,
    per_page: int = 10,
) -> dict:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    query = db.query(Question).filter(
        Question.product_id == product_id,
    ).order_by(Question.created_at.desc())

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


def create_question(db: Session, user_id: str, data: QuestionCreate) -> Question:
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    question = Question(
        product_id=data.product_id,
        user_id=user_id,
        body=data.body,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def create_answer(
    db: Session,
    question_id: str,
    user_id: str,
    data: AnswerCreate,
    is_seller: bool = False,
) -> Answer:
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    seller_id = None
    if is_seller:
        seller = db.query(Seller).filter(Seller.user_id == user_id).first()
        if seller:
            seller_id = seller.id

    answer = Answer(
        question_id=question_id,
        user_id=user_id,
        seller_id=seller_id,
        body=data.body,
        is_seller_answer=is_seller and seller_id is not None,
    )
    db.add(answer)

    # question answered mark karo
    question.is_answered = True
    db.commit()
    db.refresh(answer)
    return answer