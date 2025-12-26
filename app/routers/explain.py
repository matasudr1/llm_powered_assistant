"""
Explain endpoint - AI-powered SQL query explanation.
POST /api/explain
"""

from fastapi import APIRouter, HTTPException, Depends
import logging
import re

from ..models import ExplainRequest, ExplainResponse, ErrorResponse
from ..services import get_llm_service
from ..config import get_settings

router = APIRouter(prefix="/api", tags=["Explain"])
logger = logging.getLogger(__name__)


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


def extract_tables_from_sql(sql: str) -> list:
    """Extract table names from SQL query using regex."""
    # Common patterns for table references
    patterns = [
        r'FROM\s+(\w+)',
        r'JOIN\s+(\w+)',
        r'INTO\s+(\w+)',
        r'UPDATE\s+(\w+)',
    ]
    
    tables = set()
    sql_upper = sql.upper()
    sql_original = sql
    
    for pattern in patterns:
        matches = re.findall(pattern, sql_upper)
        for match in matches:
            # Find the actual case from original
            idx = sql_upper.find(match)
            if idx != -1:
                tables.add(sql_original[idx:idx+len(match)])
    
    return list(tables)


@router.post(
    "/explain",
    response_model=ExplainResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="Explain a SQL query in natural language",
    description="""
    Get a detailed explanation of what a SQL query does, broken down by components.
    
    **Detail levels:**
    - **beginner**: Simple explanations with analogies, no technical jargon
    - **intermediate**: Balanced explanation with SQL concepts explained
    - **advanced**: Technical deep-dive with performance considerations
    
    Optionally includes optimization tips and identifies potential issues.
    """
)
async def explain_query(
    request: ExplainRequest,
    llm=Depends(get_llm)
):
    """
    Explain a SQL query with AI-powered analysis.
    
    - **sql_query**: The SQL query to explain
    - **detail_level**: beginner, intermediate, or advanced
    - **include_optimization_tips**: Include performance suggestions (default: True)
    """
    try:
        logger.info(f"Explaining SQL query at {request.detail_level} level")
        
        # Basic validation - check if it looks like SQL
        sql_upper = request.sql_query.upper().strip()
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'WITH']
        
        if not any(sql_upper.startswith(kw) for kw in sql_keywords):
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_SQL",
                    "message": "The provided text does not appear to be a valid SQL query",
                    "details": {"hint": "SQL queries typically start with SELECT, INSERT, UPDATE, etc."}
                }
            )
        
        # Extract tables using regex (basic extraction before LLM analysis)
        tables = extract_tables_from_sql(request.sql_query)
        
        # Get LLM explanation
        result = await llm.explain_query(
            sql=request.sql_query,
            detail_level=request.detail_level,
            include_tips=request.include_optimization_tips
        )
        
        # Use LLM-extracted tables if available, otherwise use our regex extraction
        llm_tables = result.get("tables", [])
        final_tables = llm_tables if llm_tables else tables
        
        response = ExplainResponse(
            success=True,
            original_query=request.sql_query,
            explanation=result.get("explanation", ""),
            query_components=result.get("components", {}),
            tables_involved=final_tables,
            estimated_complexity=result.get("complexity", "moderate"),
            optimization_tips=result.get("optimization_tips") if request.include_optimization_tips else None,
            potential_issues=result.get("potential_issues")
        )
        
        logger.info("Query explanation generated successfully")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in explain endpoint")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": f"An unexpected error occurred: {str(e)}"
            }
        )
