"""Response models for API endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ColumnInfo(BaseModel):
    """Information about a database column."""
    
    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Column data type")
    nullable: bool = Field(..., description="Whether column allows NULL values")
    primary_key: bool = Field(default=False, description="Whether column is a primary key")
    default: Optional[str] = Field(default=None, description="Default value if any")


class TableInfo(BaseModel):
    """Information about a database table."""
    
    name: str = Field(..., description="Table name")
    columns: List[ColumnInfo] = Field(..., description="List of columns in the table")
    row_count: int = Field(..., description="Number of rows in the table")


class SchemaInfo(BaseModel):
    """Complete database schema information."""
    
    tables: List[TableInfo] = Field(..., description="List of tables in the database")
    database_name: str = Field(default="sample.db", description="Database name")


class QueryResponse(BaseModel):
    """Response model for natural language to SQL query endpoint."""
    
    success: bool = Field(..., description="Whether the query was successful")
    original_question: str = Field(..., description="The original natural language question")
    generated_sql: str = Field(..., description="The generated SQL query")
    explanation: str = Field(..., description="Brief explanation of the generated query")
    results: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Query results if execution was requested"
    )
    row_count: Optional[int] = Field(
        default=None,
        description="Number of rows returned"
    )
    execution_time_ms: Optional[float] = Field(
        default=None,
        description="Query execution time in milliseconds"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "original_question": "Show me top 10 customers by total orders",
                "generated_sql": "SELECT c.name, COUNT(o.id) as order_count FROM customers c LEFT JOIN orders o ON c.id = o.customer_id GROUP BY c.id ORDER BY order_count DESC LIMIT 10",
                "explanation": "This query joins customers with their orders and counts the total orders per customer, returning the top 10.",
                "results": [{"name": "John Doe", "order_count": 15}],
                "row_count": 10,
                "execution_time_ms": 12.5
            }
        }


class DataQualityMetrics(BaseModel):
    """Data quality metrics for a table."""
    
    completeness: float = Field(..., description="Percentage of non-null values")
    unique_ratio: float = Field(..., description="Ratio of unique values")
    null_count: int = Field(..., description="Number of null values")
    duplicate_count: int = Field(default=0, description="Number of duplicate rows")


class SummarizeResponse(BaseModel):
    """Response model for dataset summarization endpoint."""
    
    success: bool = Field(..., description="Whether summarization was successful")
    table_name: str = Field(..., description="Name of the summarized table")
    row_count: int = Field(..., description="Total number of rows")
    column_count: int = Field(..., description="Total number of columns")
    columns: List[Dict[str, Any]] = Field(..., description="Column statistics")
    data_quality: DataQualityMetrics = Field(..., description="Data quality metrics")
    summary: str = Field(..., description="LLM-generated natural language summary")
    sample_data: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Sample rows from the table"
    )
    insights: List[str] = Field(
        default_factory=list,
        description="Key insights about the data"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )


class ExplainResponse(BaseModel):
    """Response model for SQL query explanation endpoint."""
    
    success: bool = Field(..., description="Whether explanation was successful")
    original_query: str = Field(..., description="The original SQL query")
    explanation: str = Field(..., description="Detailed explanation of the query")
    query_components: Dict[str, str] = Field(
        ...,
        description="Breakdown of query components (SELECT, FROM, WHERE, etc.)"
    )
    tables_involved: List[str] = Field(..., description="Tables referenced in the query")
    estimated_complexity: str = Field(
        ...,
        pattern="^(simple|moderate|complex)$",
        description="Estimated query complexity"
    )
    optimization_tips: Optional[List[str]] = Field(
        default=None,
        description="Suggestions for query optimization"
    )
    potential_issues: Optional[List[str]] = Field(
        default=None,
        description="Potential issues or concerns with the query"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    success: bool = Field(default=False, description="Always false for errors")
    error_code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error_code": "INVALID_QUERY",
                "message": "Could not generate a valid SQL query from the provided question",
                "details": {"reason": "Ambiguous table reference"}
            }
        }


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    llm_provider: str = Field(..., description="Active LLM provider")
    database_connected: bool = Field(..., description="Database connection status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )
