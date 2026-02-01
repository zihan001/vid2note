"""
Vid2Note FastAPI Application
Main entry point for the backend server
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.api import jobs, upload, chat, versions
from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Vid2Note backend...")
    logger.info(f"Environment: {settings.APP_ENV}")
    
    # Startup: Initialize services, check dependencies
    # TODO: Check ffmpeg availability
    # TODO: Initialize database
    # TODO: Verify storage directories
    
    yield
    
    # Shutdown: Cleanup
    logger.info("Shutting down Vid2Note backend...")


app = FastAPI(
    title="Vid2Note API",
    description="AI-powered video to study PDF converter with interactive tutor",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.APP_ENV
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Vid2Note API",
        "version": "0.1.0",
        "docs": "/docs"
    }


# Include routers
app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(versions.router, prefix="/api/v1", tags=["Versions"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
