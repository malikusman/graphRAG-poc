"""
SageWrite GraphRAG Application
Main FastAPI application entry point
"""

import logging
import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import connect_to_mongo, close_mongo_connection
from app.database.models import initialize_database
from app.api import documents, queries
from app.api.endpoints import api_integration, embeddings, notes
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set specific logger levels
logging.getLogger("app.services").setLevel(logging.INFO)
logging.getLogger("app.tasks").setLevel(logging.INFO)
logging.getLogger("app.pipelines").setLevel(logging.INFO)

# Create FastAPI application
app = FastAPI(
    title="SageWrite GraphRAG API",
    description="Graph-based Retrieval-Augmented Generation system for scientific papers",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(queries.router, prefix="/api/v1/queries", tags=["queries"])
app.include_router(api_integration.router, prefix="/api/v1", tags=["API Integration"])
app.include_router(embeddings.router, prefix="/api/v1", tags=["Embeddings"])
app.include_router(notes.router, prefix="/api/v1", tags=["Notes"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to SageWrite GraphRAG API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "SageWrite GraphRAG API is running"}


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Configure LangSmith tracing
    if settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = str(settings.LANGCHAIN_TRACING_V2).lower()
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
        logging.info(f"LangSmith tracing enabled for project: {settings.LANGCHAIN_PROJECT}")
    
    # Initialize database
    await connect_to_mongo()
    await initialize_database()


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await close_mongo_connection()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )