"""
Database service for SQLite operations.
Provides schema introspection, query execution, and sample data management.
"""

import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import os
from pathlib import Path


class DatabaseService:
    """Service class for database operations."""
    
    def __init__(self, db_path: str = "./data/sample.db"):
        """Initialize database service with path."""
        self.db_path = db_path
        self._ensure_db_directory()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def get_schema(self) -> Dict[str, Any]:
        """Get complete database schema information."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            schema = {"tables": []}
            
            for table_name in tables:
                table_info = self._get_table_info(cursor, table_name)
                schema["tables"].append(table_info)
            
            return schema
    
    def _get_table_info(self, cursor, table_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific table."""
        # Get column information
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                "name": row[1],
                "type": row[2],
                "nullable": not row[3],  # notnull flag is inverted
                "primary_key": bool(row[5]),
                "default": row[4]
            })
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        return {
            "name": table_name,
            "columns": columns,
            "row_count": row_count
        }
    
    def get_schema_as_text(self) -> str:
        """Get schema as formatted text for LLM context."""
        schema = self.get_schema()
        lines = ["DATABASE SCHEMA:", "=" * 50]
        
        for table in schema["tables"]:
            lines.append(f"\nTable: {table['name']} ({table['row_count']} rows)")
            lines.append("-" * 30)
            for col in table["columns"]:
                pk = " [PRIMARY KEY]" if col["primary_key"] else ""
                nullable = " (nullable)" if col["nullable"] else " (not null)"
                lines.append(f"  - {col['name']}: {col['type']}{nullable}{pk}")
        
        return "\n".join(lines)
    
    def execute_query(self, sql: str, params: tuple = ()) -> Tuple[List[Dict[str, Any]], float]:
        """
        Execute a SQL query and return results with execution time.
        
        Returns:
            Tuple of (results list, execution time in ms)
        """
        import time
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            start_time = time.perf_counter()
            cursor.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]
            execution_time = (time.perf_counter() - start_time) * 1000
            
            return results, execution_time
    
    def get_table_sample(self, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample rows from a table."""
        results, _ = self.execute_query(
            f"SELECT * FROM {table_name} LIMIT ?",
            (limit,)
        )
        return results
    
    def get_column_statistics(self, table_name: str) -> List[Dict[str, Any]]:
        """Get statistics for each column in a table."""
        schema = self.get_schema()
        table_info = next(
            (t for t in schema["tables"] if t["name"] == table_name),
            None
        )
        
        if not table_info:
            return []
        
        stats = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for col in table_info["columns"]:
                col_stats = {
                    "name": col["name"],
                    "type": col["type"],
                    "nullable": col["nullable"]
                }
                
                # Count nulls
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col['name']} IS NULL")
                col_stats["null_count"] = cursor.fetchone()[0]
                
                # Count distinct values
                cursor.execute(f"SELECT COUNT(DISTINCT {col['name']}) FROM {table_name}")
                col_stats["distinct_count"] = cursor.fetchone()[0]
                
                # For numeric columns, get min/max/avg
                if col["type"].upper() in ["INTEGER", "REAL", "NUMERIC", "FLOAT", "DOUBLE"]:
                    cursor.execute(f"""
                        SELECT MIN({col['name']}), MAX({col['name']}), AVG({col['name']})
                        FROM {table_name}
                    """)
                    row = cursor.fetchone()
                    col_stats["min"] = row[0]
                    col_stats["max"] = row[1]
                    col_stats["avg"] = round(row[2], 2) if row[2] else None
                
                stats.append(col_stats)
        
        return stats
    
    def get_data_quality_metrics(self, table_name: str) -> Dict[str, Any]:
        """Calculate data quality metrics for a table."""
        schema = self.get_schema()
        table_info = next(
            (t for t in schema["tables"] if t["name"] == table_name),
            None
        )
        
        if not table_info:
            return {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            total_cells = table_info["row_count"] * len(table_info["columns"])
            
            # Count total nulls
            null_count = 0
            for col in table_info["columns"]:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col['name']} IS NULL")
                null_count += cursor.fetchone()[0]
            
            # Calculate completeness
            completeness = ((total_cells - null_count) / total_cells * 100) if total_cells > 0 else 100
            
            # Count duplicates (approximate by checking all columns)
            col_names = ", ".join([col["name"] for col in table_info["columns"]])
            cursor.execute(f"""
                SELECT COUNT(*) FROM (
                    SELECT {col_names}, COUNT(*) as cnt 
                    FROM {table_name} 
                    GROUP BY {col_names} 
                    HAVING cnt > 1
                )
            """)
            duplicate_count = cursor.fetchone()[0]
            
            # Calculate unique ratio based on first column (usually ID)
            first_col = table_info["columns"][0]["name"]
            cursor.execute(f"SELECT COUNT(DISTINCT {first_col}) FROM {table_name}")
            distinct = cursor.fetchone()[0]
            unique_ratio = (distinct / table_info["row_count"]) if table_info["row_count"] > 0 else 1
            
            return {
                "completeness": round(completeness, 2),
                "null_count": null_count,
                "duplicate_count": duplicate_count,
                "unique_ratio": round(unique_ratio, 4)
            }
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            return cursor.fetchone() is not None
    
    def get_table_names(self) -> List[str]:
        """Get list of all table names."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            return [row[0] for row in cursor.fetchall()]


# Singleton instance
_db_service: Optional[DatabaseService] = None


def get_database_service(db_path: str = "./data/sample.db") -> DatabaseService:
    """Get or create database service singleton."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService(db_path)
    return _db_service
