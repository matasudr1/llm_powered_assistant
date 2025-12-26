"""
Query endpoint - Natural language to SQL conversion and execution.
POST /api/query
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging

from ..models import QueryRequest, QueryResponse, ErrorResponse
from ..services import get_database_service, get_llm_service
from ..config import get_settings

router = APIRouter(prefix="/api", tags=["Query"])
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
    "/query",
    response_model=QueryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="Convert natural language to SQL and execute",
    description="""
    Convert a natural language question into a SQL query and optionally execute it.
    
    **Example questions:**
    - "Show me top 10 customers by total orders"
    - "What are the most popular products?"
    - "List all orders from last month"
    - "Which customers have spent more than $1000?"
    """
)
async def query_data(
    request: QueryRequest,
    db=Depends(get_db),
    llm=Depends(get_llm)
):
    """
    Convert natural language question to SQL and execute.
    
    - **question**: Natural language question about the data
    - **table_name**: Optional hint about which table to query
    - **execute**: Whether to execute the generated SQL (default: True)
    - **limit**: Maximum rows to return (default: 100)
    """
    try:
        # Get database schema for context
        schema_text = db.get_schema_as_text()
        
        # Generate SQL from natural language
        logger.info(f"Generating SQL for question: {request.question}")
        result = await llm.generate_sql(
            question=request.question,
            schema=schema_text,
            table_hint=request.table_name
        )
        
        generated_sql = result.get("sql", "")
        explanation = result.get("explanation", "")
        
        if not generated_sql:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "SQL_GENERATION_FAILED",
                    "message": "Could not generate a valid SQL query from the provided question",
                    "details": {"question": request.question}
                }
            )
        
        # Validate SQL is a SELECT statement (security)
        sql_upper = generated_sql.upper().strip()
        if not sql_upper.startswith("SELECT"):
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_SQL_TYPE",
                    "message": "Only SELECT queries are allowed",
                    "details": {"generated_sql": generated_sql}
                }
            )
        
        # Apply limit if not already present
        if "LIMIT" not in sql_upper:
            generated_sql = f"{generated_sql.rstrip(';')} LIMIT {request.limit}"
        
        response_data = {
            "success": True,
            "original_question": request.question,
            "generated_sql": generated_sql,
            "explanation": explanation,
            "results": None,
            "row_count": None,
            "execution_time_ms": None
        }
        
        # Execute if requested
        if request.execute:
            try:
                results, exec_time = db.execute_query(generated_sql)
                response_data["results"] = results
                response_data["row_count"] = len(results)
                response_data["execution_time_ms"] = round(exec_time, 2)
                logger.info(f"Query executed successfully: {len(results)} rows in {exec_time:.2f}ms")
            except Exception as e:
                logger.error(f"Query execution failed: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error_code": "QUERY_EXECUTION_FAILED",
                        "message": f"Failed to execute generated SQL: {str(e)}",
                        "details": {"sql": generated_sql}
                    }
                )
        
        return QueryResponse(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in query endpoint")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": f"An unexpected error occurred: {str(e)}"
            }
        )
