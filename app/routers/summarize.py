"""
Summarize endpoint - Generate data quality reports and summaries.
POST /api/summarize
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from ..models import SummarizeRequest, SummarizeResponse, ErrorResponse, DataQualityMetrics
from ..services import get_database_service, get_llm_service
from ..config import get_settings

router = APIRouter(prefix="/api", tags=["Summarize"])
logger = logging.getLogger(__name__)


def get_db():
    """Dependency to get database service."""
    settings = get_settings()
    db_path = settings.database_url.replace("sqlite:///", "")
    return get_database_service(db_path)


def get_llm():
    """Dependency to get LLM service."""
    settings = get_settings()
    return get_llm_service(
        provider=settings.llm_provider,
        openai_api_key=settings.openai_api_key,
        openai_model=settings.openai_model,
        ollama_base_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model
    )


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Table not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="Summarize a dataset with AI-powered insights",
    description="""
    Generate a comprehensive summary of a database table including:
    - Column statistics (types, nulls, distinct values, min/max/avg for numerics)
    - Data quality metrics (completeness, duplicates)
    - AI-generated insights and recommendations
    - Sample data preview
    
    **Focus areas** you can specify:
    - data quality
    - distributions
    - outliers
    - relationships
    - trends
    """
)
async def summarize_data(
    request: SummarizeRequest,
    db=Depends(get_db),
    llm=Depends(get_llm)
):
    """
    Generate AI-powered summary of a database table.
    
    - **table_name**: Name of the table to summarize
    - **include_sample_data**: Include sample rows (default: True)
    - **sample_size**: Number of sample rows (default: 5)
    - **focus_areas**: Specific aspects to analyze
    """
    try:
        # Check if table exists
        if not db.table_exists(request.table_name):
            available_tables = db.get_table_names()
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "TABLE_NOT_FOUND",
                    "message": f"Table '{request.table_name}' not found",
                    "details": {"available_tables": available_tables}
                }
            )
        
        logger.info(f"Generating summary for table: {request.table_name}")
        
        # Gather statistics
        column_stats = db.get_column_statistics(request.table_name)
        quality_metrics = db.get_data_quality_metrics(request.table_name)
        
        # Get schema info for row count
        schema = db.get_schema()
        table_info = next(t for t in schema["tables"] if t["name"] == request.table_name)
        row_count = table_info["row_count"]
        
        # Get sample data if requested
        sample_data = None
        if request.include_sample_data:
            sample_data = db.get_table_sample(request.table_name, request.sample_size)
        
        # Generate AI summary
        llm_result = await llm.summarize_data(
            table_name=request.table_name,
            statistics=column_stats,
            quality_metrics=quality_metrics,
            sample_data=sample_data or [],
            row_count=row_count,
            focus_areas=request.focus_areas
        )
        
        # Build response
        response = SummarizeResponse(
            success=True,
            table_name=request.table_name,
            row_count=row_count,
            column_count=len(column_stats),
            columns=column_stats,
            data_quality=DataQualityMetrics(**quality_metrics),
            summary=llm_result.get("summary", "Summary generation failed"),
            sample_data=sample_data,
            insights=llm_result.get("insights", [])
        )
        
        logger.info(f"Summary generated successfully for {request.table_name}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in summarize endpoint")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": f"An unexpected error occurred: {str(e)}"
            }
        )
