"""
LLM Service - Handles interactions with OpenAI or Ollama.
Provides natural language to SQL conversion, query explanation, and data summarization.
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import json
import re


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a response from the LLM."""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client
    
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate response using OpenAI API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,  # Low temperature for more deterministic SQL
            max_tokens=2000
        )
        
        return response.choices[0].message.content


class OllamaProvider(BaseLLMProvider):
    """Ollama (local LLM) provider."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
    
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate response using Ollama API."""
        import httpx
        
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1
                    }
                }
            )
            response.raise_for_status()
            return response.json()["response"]


class LLMService:
    """
    High-level LLM service for data assistant operations.
    Supports both OpenAI and Ollama backends.
    """
    
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider
    
    async def generate_sql(self, question: str, schema: str, table_hint: Optional[str] = None) -> Dict[str, str]:
        """
        Convert natural language question to SQL query.
        
        Args:
            question: Natural language question
            schema: Database schema description
            table_hint: Optional hint about which table to query
            
        Returns:
            Dict with 'sql' and 'explanation' keys
        """
        system_prompt = """You are an expert SQL query generator. Your task is to convert natural language questions into valid SQLite SQL queries.

RULES:
1. Generate ONLY valid SQLite SQL syntax
2. Always use proper table and column names from the provided schema
3. Use appropriate JOINs when querying related tables
4. Include reasonable LIMIT clauses for potentially large result sets
5. Handle edge cases with COALESCE or IFNULL when appropriate
6. Never use DROP, DELETE, UPDATE, INSERT, or any data-modifying statements

OUTPUT FORMAT:
Return a JSON object with exactly these keys:
{
    "sql": "YOUR SQL QUERY HERE",
    "explanation": "Brief explanation of what the query does"
}

Return ONLY the JSON object, no additional text."""

        table_context = f"\nHint: Focus on the '{table_hint}' table if relevant." if table_hint else ""
        
        prompt = f"""DATABASE SCHEMA:
{schema}
{table_context}

USER QUESTION: {question}

Generate the SQL query:"""

        response = await self.provider.generate(prompt, system_prompt)
        
        # Parse JSON response
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "sql": result.get("sql", ""),
                    "explanation": result.get("explanation", "Query generated from natural language")
                }
        except json.JSONDecodeError:
            pass
        
        # Fallback: try to extract SQL directly
        sql_match = re.search(r'(SELECT[^;]+;?)', response, re.IGNORECASE | re.DOTALL)
        if sql_match:
            return {
                "sql": sql_match.group(1).strip(),
                "explanation": "Query generated from natural language"
            }
        
        return {
            "sql": "",
            "explanation": "Could not generate a valid SQL query"
        }
    
    async def explain_query(
        self, 
        sql: str, 
        detail_level: str = "intermediate",
        include_tips: bool = True
    ) -> Dict[str, Any]:
        """
        Explain a SQL query in natural language.
        
        Args:
            sql: SQL query to explain
            detail_level: beginner, intermediate, or advanced
            include_tips: Whether to include optimization tips
            
        Returns:
            Dict with explanation details
        """
        system_prompt = f"""You are an expert SQL educator. Explain SQL queries clearly at a {detail_level} level.

OUTPUT FORMAT:
Return a JSON object with these keys:
{{
    "explanation": "Detailed explanation of what the query does",
    "components": {{
        "SELECT": "explanation of selected columns",
        "FROM": "explanation of source table(s)",
        "JOIN": "explanation of joins (if any)",
        "WHERE": "explanation of filters (if any)",
        "GROUP BY": "explanation of grouping (if any)",
        "ORDER BY": "explanation of sorting (if any)",
        "LIMIT": "explanation of row limit (if any)"
    }},
    "tables": ["list", "of", "tables"],
    "complexity": "simple|moderate|complex",
    "optimization_tips": ["tip1", "tip2"],
    "potential_issues": ["issue1", "issue2"]
}}

Only include components that exist in the query.
Return ONLY the JSON object."""

        prompt = f"""SQL QUERY:
{sql}

Explain this query:"""

        response = await self.provider.generate(prompt, system_prompt)
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # Ensure required fields
                if not include_tips:
                    result.pop("optimization_tips", None)
                
                return {
                    "explanation": result.get("explanation", ""),
                    "components": result.get("components", {}),
                    "tables": result.get("tables", []),
                    "complexity": result.get("complexity", "moderate"),
                    "optimization_tips": result.get("optimization_tips") if include_tips else None,
                    "potential_issues": result.get("potential_issues")
                }
        except json.JSONDecodeError:
            pass
        
        # Fallback
        return {
            "explanation": response,
            "components": {},
            "tables": [],
            "complexity": "moderate",
            "optimization_tips": None,
            "potential_issues": None
        }
    
    async def summarize_data(
        self,
        table_name: str,
        statistics: List[Dict[str, Any]],
        quality_metrics: Dict[str, Any],
        sample_data: List[Dict[str, Any]],
        row_count: int,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a natural language summary of a dataset.
        
        Args:
            table_name: Name of the table
            statistics: Column statistics
            quality_metrics: Data quality metrics
            sample_data: Sample rows from the table
            row_count: Total row count
            focus_areas: Specific areas to focus on
            
        Returns:
            Dict with summary and insights
        """
        focus_context = ""
        if focus_areas:
            focus_context = f"\nFocus especially on: {', '.join(focus_areas)}"
        
        system_prompt = """You are a data analyst expert. Analyze datasets and provide clear, actionable insights.

OUTPUT FORMAT:
Return a JSON object with these keys:
{
    "summary": "A comprehensive 2-3 paragraph summary of the data",
    "insights": ["insight1", "insight2", "insight3", "insight4", "insight5"]
}

Focus on:
- Data patterns and distributions
- Data quality observations
- Potential anomalies or issues
- Business-relevant insights
- Recommendations for data usage

Return ONLY the JSON object."""

        prompt = f"""DATASET ANALYSIS REQUEST

Table: {table_name}
Total Rows: {row_count}
{focus_context}

COLUMN STATISTICS:
{json.dumps(statistics, indent=2)}

DATA QUALITY METRICS:
{json.dumps(quality_metrics, indent=2)}

SAMPLE DATA:
{json.dumps(sample_data, indent=2)}

Provide your analysis:"""

        response = await self.provider.generate(prompt, system_prompt)
        
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "summary": result.get("summary", ""),
                    "insights": result.get("insights", [])
                }
        except json.JSONDecodeError:
            pass
        
        # Fallback
        return {
            "summary": response,
            "insights": []
        }


# Factory function for creating LLM service
_llm_service: Optional[LLMService] = None


def get_llm_service(
    provider: str = "openai",
    openai_api_key: str = "",
    openai_model: str = "gpt-3.5-turbo",
    ollama_base_url: str = "http://localhost:11434",
    ollama_model: str = "llama2"
) -> LLMService:
    """
    Get or create LLM service singleton.
    
    Args:
        provider: "openai" or "ollama"
        openai_api_key: OpenAI API key (required for openai provider)
        openai_model: OpenAI model name
        ollama_base_url: Ollama server URL
        ollama_model: Ollama model name
    """
    global _llm_service
    
    if _llm_service is None:
        if provider == "openai":
            llm_provider = OpenAIProvider(api_key=openai_api_key, model=openai_model)
        else:
            llm_provider = OllamaProvider(base_url=ollama_base_url, model=ollama_model)
        
        _llm_service = LLMService(llm_provider)
    
    return _llm_service


def reset_llm_service():
    """Reset LLM service singleton (useful for testing)."""
    global _llm_service
    _llm_service = None
