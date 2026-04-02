from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.user import router as user_router
from app.api.v1.endpoints.product import router as product_router
from app.api.v1.endpoints.cart import router as cart_router
from app.api.v1.endpoints.order import router as order_router
from app.api.v1.endpoints.payment import router as payment_router
from app.api.v1.endpoints.review import router as review_router
from app.api.v1.endpoints.seller import router as seller_router
from app.api.v1.endpoints.wishlist import router as wishlist_router
from app.api.v1.endpoints.search import router as search_router
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.delivery import router as delivery_router
from app.api.v1.endpoints.notification import router as notification_router
from app.api.v1.endpoints.promo import router as promo_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(product_router)
api_router.include_router(cart_router)
api_router.include_router(order_router)
api_router.include_router(payment_router)
api_router.include_router(review_router)
api_router.include_router(seller_router)
api_router.include_router(wishlist_router)
api_router.include_router(search_router)
api_router.include_router(admin_router)
api_router.include_router(delivery_router)
api_router.include_router(notification_router)
api_router.include_router(promo_router)