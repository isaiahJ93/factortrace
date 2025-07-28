from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.core.config import settings
from app.core.database import Base, engine

app = FastAPI(title="FactorTrace API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)
Path("uploads").mkdir(exist_ok=True)

# Include API router
try:
    from app.api.v1.api import api_router
    app.include_router(api_router, prefix="/api/v1")
except Exception as e:
    print(f"Could not load API router: {e}")

@app.get("/")
async def root():
    return {"status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
