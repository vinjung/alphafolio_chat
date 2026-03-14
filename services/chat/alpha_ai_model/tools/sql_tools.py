# services/chat/alpha_ai_model/tools/sql_tools.py
"""
SQL Tools for Alpha AI

Provides SQL-related utilities:
- SQL validation
- Query execution
- Result formatting
"""
from typing import List, Dict, Any, Optional
from config import logger
from database import db


class SQLTools:
    """SQL utility tools for Alpha AI"""

    # Blocked keywords for security
    BLOCKED_KEYWORDS = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE",
        "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE"
    ]

    @staticmethod
    def security_check(sql: str) -> tuple[bool, str]:
        """
        Check SQL for dangerous keywords

        Args:
            sql: SQL query to check

        Returns:
            Tuple of (is_safe, error_message)
        """
        sql_upper = sql.upper()
        for keyword in SQLTools.BLOCKED_KEYWORDS:
            if f" {keyword} " in f" {sql_upper} " or sql_upper.startswith(f"{keyword} "):
                return False, f"Blocked keyword: {keyword}"
        return True, ""

    @staticmethod
    async def validate_syntax(sql: str) -> tuple[bool, Optional[str]]:
        """
        Validate SQL syntax using EXPLAIN

        Args:
            sql: SQL query to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not db.pool:
            return False, "Database not connected"

        try:
            async with db.pool.acquire() as conn:
                await conn.execute(f"EXPLAIN {sql}")
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    async def execute_query(sql: str, timeout: int = 30) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Execute SQL query with timeout

        Args:
            sql: SQL query to execute
            timeout: Query timeout in seconds

        Returns:
            Tuple of (results, error_message)
        """
        if not db.pool:
            return [], "Database not connected"

        try:
            async with db.pool.acquire() as conn:
                rows = await conn.fetch(sql, timeout=timeout)
                return [dict(row) for row in rows], None
        except Exception as e:
            logger.error(f"[SQLTools] Query execution error: {str(e)}")
            return [], str(e)

    @staticmethod
    def format_as_markdown_table(results: List[Dict[str, Any]], max_rows: int = 50) -> str:
        """
        Format results as markdown table

        Args:
            results: Query results
            max_rows: Maximum rows to display

        Returns:
            Markdown table string
        """
        if not results:
            return "No results."

        columns = list(results[0].keys())

        # Header
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"

        # Rows
        rows = []
        for row in results[:max_rows]:
            values = []
            for col in columns:
                val = row.get(col, "")
                if isinstance(val, float):
                    val = f"{val:,.2f}"
                elif isinstance(val, int):
                    val = f"{val:,}"
                else:
                    val = str(val) if val is not None else ""
                values.append(val)
            rows.append("| " + " | ".join(values) + " |")

        table = "\n".join([header, separator] + rows)

        if len(results) > max_rows:
            table += f"\n\n... {len(results) - max_rows} more rows"

        return table
