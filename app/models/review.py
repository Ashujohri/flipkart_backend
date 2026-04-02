from sqlalchemy import (
    Column, String, Boolean, Enum, Text,
    ForeignKey, DateTime, Integer, Float,
    Numeric, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum


def generate_uuid():
    return str(uuid.uuid4())


# ─── Enums ────────────────────────────────────────────────────────────────────

class ReviewStatus(enum.Enum):
    pending     = "pending"
    approved    = "approved"
    rejected    = "rejected"
    flagged     = "flagged"

class VoteType(enum.Enum):
    helpful     = "helpful"
    not_helpful = "not_helpful"


# ─── Review ───────────────────────────────────────────────────────────────────

class Review(Base):
    __tablename__ = "reviews"

    id                  = Column(String(36), primary_key=True, default=generate_uuid)
    product_id          = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id             = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    order_item_id       = Column(String(36), ForeignKey("order_items.id", ondelete="SET NULL"), nullable=True)
    rating              = Column(Integer, nullable=False)
    title               = Column(String(255), nullable=True)
    body                = Column(Text, nullable=True)
    status              = Column(Enum(ReviewStatus), default=ReviewStatus.pending, nullable=False)
    is_verified_purchase = Column(Boolean, default=False, nullable=False)
    helpful_count       = Column(Integer, default=0, nullable=False)
    not_helpful_count   = Column(Integer, default=0, nullable=False)
    seller_response     = Column(Text, nullable=True)
    seller_responded_at = Column(DateTime, nullable=True)
    created_at          = Column(DateTime, server_default=func.now())
    updated_at          = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("product_id", "user_id", name="unique_user_product_review"),
    )

    # Relationships
    product     = relationship("Product", back_populates="reviews")
    user        = relationship("User", back_populates="reviews")
    order_item  = relationship("OrderItem")
    images      = relationship("ReviewImage", back_populates="review", cascade="all, delete-orphan")
    votes       = relationship("ReviewVote", back_populates="review", cascade="all, delete-orphan")


# ─── Review Image ─────────────────────────────────────────────────────────────

class ReviewImage(Base):
    __tablename__ = "review_images"

    id              = Column(String(36), primary_key=True, default=generate_uuid)
    review_id       = Column(String(36), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url       = Column(String(500), nullable=False)
    thumbnail_url   = Column(String(500), nullable=True)
    display_order   = Column(Integer, default=0, nullable=False)
    created_at      = Column(DateTime, server_default=func.now())

    # Relationships
    review = relationship("Review", back_populates="images")


# ─── Review Vote ──────────────────────────────────────────────────────────────

class ReviewVote(Base):
    __tablename__ = "review_votes"

    id          = Column(String(36), primary_key=True, default=generate_uuid)
    review_id   = Column(String(36), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id     = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    vote_type   = Column(Enum(VoteType), nullable=False)
    created_at  = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("review_id", "user_id", name="unique_user_review_vote"),
    )

    # Relationships
    review  = relationship("Review", back_populates="votes")
    user    = relationship("User")


# ─── Question ─────────────────────────────────────────────────────────────────

class Question(Base):
    __tablename__ = "questions"

    id          = Column(String(36), primary_key=True, default=generate_uuid)
    product_id  = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id     = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    body        = Column(Text, nullable=False)
    is_answered = Column(Boolean, default=False, nullable=False)
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    product = relationship("Product", back_populates="questions")
    user    = relationship("User")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")


# ─── Answer ───────────────────────────────────────────────────────────────────

class Answer(Base):
    __tablename__ = "answers"

    id              = Column(String(36), primary_key=True, default=generate_uuid)
    question_id     = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id         = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    seller_id       = Column(String(36), ForeignKey("sellers.id", ondelete="SET NULL"), nullable=True)
    body            = Column(Text, nullable=False)
    is_seller_answer = Column(Boolean, default=False, nullable=False)
    helpful_count   = Column(Integer, default=0, nullable=False)
    created_at      = Column(DateTime, server_default=func.now())
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    question    = relationship("Question", back_populates="answers")
    user        = relationship("User")
    seller      = relationship("Seller")