from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import engine, Base

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME}...")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down...")
    engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Try to import api router but don't fail if it's broken
try:
    from app.api.v1.api import api_router
    app.include_router(api_router, prefix=settings.API_V1_STR)
    logger.info("API router loaded successfully")
except Exception as e:
    logger.error(f"Failed to load API router: {e}")
    logger.info("Running in minimal mode")
