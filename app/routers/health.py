"""
Health check endpoint.
GET /health
"""

from fastapi import APIRouter, Depends
from datetime import datetime

from ..models import HealthResponse
from ..services import get_database_service
from ..config import get_settings

router = APIRouter(tags=["Health"])


def get_db():
    """Dependency to get database service."""
    settings = get_settings()
    db_path = settings.database_url.replace("sqlite:///", "")
    return get_database_service(db_path)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
    description="Check the health status of the API and its dependencies."
)
async def health_check(db=Depends(get_db)):
    """
    Check API health status.
    
    Returns:
    - Service status
    - API version
    - Active LLM provider
    - Database connection status
    """
    settings = get_settings()
    
    # Test database connection
    try:
        db.get_table_names()
        db_connected = True
    except Exception:
        db_connected = False
    
    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        version=settings.app_version,
        llm_provider=settings.llm_provider,
        database_connected=db_connected,
        timestamp=datetime.utcnow()
    )


@router.get(
    "/",
    summary="Root endpoint",
    description="Welcome message and API information."
)
async def root():
    """Root endpoint with API information."""
    settings = get_settings()
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "LLM-Powered Data Assistant API",
        "docs_url": "/docs",
        "endpoints": {
            "query": "POST /api/query - Natural language to SQL",
            "summarize": "POST /api/summarize - Dataset summarization",
            "explain": "POST /api/explain - SQL query explanation",
            "health": "GET /health - Health check"
        }
    }


@router.get(
    "/schema",
    summary="Get database schema",
    description="Retrieve the complete database schema information."
)
async def get_schema(db=Depends(get_db)):
    """Get the database schema for reference."""
    return db.get_schema()
