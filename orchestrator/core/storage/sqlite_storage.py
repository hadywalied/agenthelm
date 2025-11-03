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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_name ON traces(tool_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON traces(timestamp)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_error_state ON traces(error_state)"
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
                error_state, llm_reasoning_trace, confidence_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                event["timestamp"],
                event["tool_name"],
                json.dumps(event["inputs"]),
                json.dumps(event["outputs"]),
                event["execution_time"],
                event["error_state"],
                event["llm_reasoning_trace"],
                event["confidence_score"],
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
            if item["inputs"]:
                item["inputs"] = json.loads(item["inputs"])
            if item["outputs"]:
                item["outputs"] = json.loads(item["outputs"])
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
            if "status" in filters:
                if filters["status"].lower() == "success":
                    query += " AND error_state IS NULL"
                else:
                    query += " AND error_state IS NOT NULL"
            # Add more filter conditions as needed

        query += " ORDER BY timestamp DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Convert rows to dictionaries (same as load())
        columns = [description[0] for description in cursor.description]
        results = []
        for row in rows:
            item = dict(zip(columns, row))
            if item["inputs"]:
                item["inputs"] = json.loads(item["inputs"])
            if item["outputs"]:
                item["outputs"] = json.loads(item["outputs"])
            results.append(item)
        return results
