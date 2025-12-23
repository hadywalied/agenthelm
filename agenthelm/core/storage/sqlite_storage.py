import sqlite3
import json
from typing import Any, Dict, List, Optional
from .base import BaseStorage


class SqliteStorage(BaseStorage):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                inputs TEXT,
                outputs TEXT,
                execution_time REAL,
                error_state TEXT,
                llm_reasoning_trace TEXT,
                confidence_score REAL,
                -- New v0.3.0 fields
                token_usage TEXT,
                estimated_cost_usd REAL DEFAULT 0.0,
                retry_count INTEGER DEFAULT 0,
                agent_name TEXT,
                session_id TEXT,
                trace_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_name ON traces(tool_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON traces(timestamp)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_error_state ON traces(error_state)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_session_id ON traces(session_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_name ON traces(agent_name)"
        )
        conn.commit()
        conn.close()

    def save(self, event: Dict[str, Any]) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO traces (
                timestamp, tool_name, inputs, outputs, execution_time, 
                error_state, llm_reasoning_trace, confidence_score,
                token_usage, estimated_cost_usd, retry_count,
                agent_name, session_id, trace_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                event.get("timestamp"),
                event.get("tool_name"),
                json.dumps(event.get("inputs", {})),
                json.dumps(event.get("outputs", {})),
                event.get("execution_time"),
                event.get("error_state"),
                event.get("llm_reasoning_trace"),
                event.get("confidence_score"),
                json.dumps(event.get("token_usage"))
                if event.get("token_usage")
                else None,
                event.get("estimated_cost_usd", 0.0),
                event.get("retry_count", 0),
                event.get("agent_name"),
                event.get("session_id"),
                event.get("trace_id"),
            ),
        )
        conn.commit()
        conn.close()

    def load(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM traces ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()

        # Convert rows to a list of dictionaries
        columns = [description[0] for description in cursor.description]
        results = []
        for row in rows:
            item = dict(zip(columns, row))
            # Parse JSON fields
            if item.get("inputs"):
                item["inputs"] = json.loads(item["inputs"])
            if item.get("outputs"):
                item["outputs"] = json.loads(item["outputs"])
            if item.get("token_usage"):
                item["token_usage"] = json.loads(item["token_usage"])
            results.append(item)
        return results

    def query(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query traces with SQL-level filtering for better performance."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM traces WHERE 1=1"
        params = []

        if filters:
            if "tool_name" in filters:
                query += " AND tool_name = ?"
                params.append(filters["tool_name"])
            if "agent_name" in filters:
                query += " AND agent_name = ?"
                params.append(filters["agent_name"])
            if "session_id" in filters:
                query += " AND session_id = ?"
                params.append(filters["session_id"])
            if "status" in filters:
                if filters["status"].lower() == "success":
                    query += " AND error_state IS NULL"
                else:
                    query += " AND error_state IS NOT NULL"

        query += " ORDER BY timestamp DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Convert rows to dictionaries
        columns = [description[0] for description in cursor.description]
        results = []
        for row in rows:
            item = dict(zip(columns, row))
            # Parse JSON fields
            if item.get("inputs"):
                item["inputs"] = json.loads(item["inputs"])
            if item.get("outputs"):
                item["outputs"] = json.loads(item["outputs"])
            if item.get("token_usage"):
                item["token_usage"] = json.loads(item["token_usage"])
            results.append(item)
        return results
