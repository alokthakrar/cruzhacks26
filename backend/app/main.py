from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import connect_to_mongo, close_mongo_connection
from .routers import users, subjects, analyze, pdf
from .services.ocr import ocr_service
from .services.pdf_extractor import pdf_extractor_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - connect/disconnect from MongoDB and load ML models."""
    await connect_to_mongo()
    ocr_service.load_models()
    pdf_extractor_service.load_model()
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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api")
app.include_router(subjects.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
app.include_router(pdf.router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
