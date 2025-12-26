"""Request models for API endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, List


class QueryRequest(BaseModel):
    """Request model for natural language to SQL query endpoint."""
    
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Natural language question to convert to SQL",
        examples=["Show me top 10 customers by total orders"]
    )
    table_name: Optional[str] = Field(
        default=None,
        description="Specific table to query (optional, will auto-detect if not provided)"
    )
    execute: bool = Field(
        default=True,
        description="Whether to execute the generated SQL and return results"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of rows to return"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Show me top 10 customers by total orders",
                "execute": True,
                "limit": 10
            }
        }


class SummarizeRequest(BaseModel):
    """Request model for dataset summarization endpoint."""
    
    table_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the table to summarize"
    )
    include_sample_data: bool = Field(
        default=True,
        description="Whether to include sample rows in the summary"
    )
    sample_size: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of sample rows to include"
    )
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Specific aspects to focus on (e.g., ['data quality', 'distributions', 'outliers'])"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "table_name": "customers",
                "include_sample_data": True,
                "sample_size": 5,
                "focus_areas": ["data quality", "distributions"]
            }
        }


class ExplainRequest(BaseModel):
    """Request model for SQL query explanation endpoint."""
    
    sql_query: str = Field(
        ...,
        min_length=5,
        max_length=5000,
        description="SQL query to explain"
    )
    detail_level: str = Field(
        default="intermediate",
        pattern="^(beginner|intermediate|advanced)$",
        description="Level of detail for explanation"
    )
    include_optimization_tips: bool = Field(
        default=True,
        description="Whether to include query optimization suggestions"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sql_query": "SELECT c.name, COUNT(o.id) as order_count FROM customers c LEFT JOIN orders o ON c.id = o.customer_id GROUP BY c.id ORDER BY order_count DESC LIMIT 10",
                "detail_level": "intermediate",
                "include_optimization_tips": True
            }
        }
