from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import engine, Base, create_database_if_not_exist
from app.api.v1.router import api_router
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.core.exceptions import register_exception_handlers
import app.models

Path("uploads").mkdir(exist_ok=True)
Path("uploads/profiles").mkdir(parents=True, exist_ok=True)
Path("uploads/products").mkdir(parents=True, exist_ok=True)
Path("uploads/reviews").mkdir(parents=True, exist_ok=True)
Path("uploads/documents").mkdir(parents=True, exist_ok=True)
Path("uploads/banners").mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Server start hone pe ye chalega
    create_database_if_not_exist()
    print(f"✅ Database connected")
    print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} started")
    yield
    # Server band hone pe ye chalega
    print(f"🛑 {settings.APP_NAME} shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

register_exception_handlers(app)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Static files — uploads folder serve karo    ← add
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(api_router)


# Health check
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
    }