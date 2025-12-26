"""
Data Assistant API - Main Application Entry Point

An LLM-powered API for natural language to SQL conversion,
data quality reporting, and schema documentation Q&A.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os

from .config import get_settings
from .routers import query_router, summarize_router, explain_router, health_router
from .services.init_db import create_sample_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - startup and shutdown events."""
    # Startup
    logger.info("Starting Data Assistant API...")
    settings = get_settings()
    
    # Initialize database if it doesn't exist
    db_path = settings.database_url.replace("sqlite:///", "")
    if not os.path.exists(db_path):
        logger.info("Creating sample database...")
        create_sample_database(db_path)
    else:
        logger.info(f"Using existing database: {db_path}")
    
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info("API is ready to serve requests!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Data Assistant API...")


def create_app() -> FastAPI:
    """Application factory function."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="""
# LLM-Powered Data Assistant API

Transform natural language into SQL queries, get AI-powered data summaries, 
and understand complex SQL with intelligent explanations.

## Features

- **Natural Language to SQL**: Ask questions in plain English, get SQL queries
- **Data Summarization**: AI-generated insights about your data
- **Query Explanation**: Understand what any SQL query does

## Quick Start

1. **Query your data**: POST to `/api/query` with a natural language question
2. **Summarize tables**: POST to `/api/summarize` with a table name
3. **Explain SQL**: POST to `/api/explain` with any SQL query

## Tech Stack

- FastAPI + Pydantic for robust API design
- OpenAI / Ollama for LLM capabilities  
- SQLite for demo database
        """,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=[
            {"name": "Query", "description": "Natural language to SQL conversion"},
            {"name": "Summarize", "description": "Dataset analysis and summarization"},
            {"name": "Explain", "description": "SQL query explanation"},
            {"name": "Health", "description": "API health and metadata"},
        ]
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routers
    app.include_router(health_router)
    app.include_router(query_router)
    app.include_router(summarize_router)
    app.include_router(explain_router)
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"type": type(exc).__name__}
            }
        )
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
