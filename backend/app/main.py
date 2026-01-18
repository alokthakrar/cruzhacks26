from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import connect_to_mongo, close_mongo_connection
from .routers import users, subjects, analyze
from .api import bkt
# from .services.ocr import ocr_service  # Disabled for BKT testing - pyarrow dependency issue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - connect/disconnect from MongoDB and load ML models."""
    await connect_to_mongo()
    # Note: OCR service disabled for BKT demo - re-enable when pyarrow is fixed
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Adaptive AI Tutor API",
    description="Backend API for the Adaptive AI Tutor - manages user profiles, weakness tracking, and learning sessions.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "*"  # Allow all origins for development (file:// protocol support)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api")
app.include_router(subjects.router, prefix="/api")
# app.include_router(analyze.router, prefix="/api")  # Disabled for BKT testing - pyarrow issue
app.include_router(bkt.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
