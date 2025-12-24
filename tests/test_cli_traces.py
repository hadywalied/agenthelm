import pytest
import os
import json
import sqlite3
from typer.testing import CliRunner
from orchestrator.cli import app
from datetime import datetime, timezone, timedelta

runner = CliRunner()

# --- Fixtures for CLI Tests ---


@pytest.fixture
def dummy_json_trace_file(tmp_path):
    file_path = tmp_path / "dummy_traces.json"
    traces = [
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool_name": "tool_a",
            "inputs": {"param": "value1"},
            "outputs": {"result": "output1"},
            "execution_time": 0.5,
            "error_state": None,
            "llm_reasoning_trace": "reasoning_a",
            "confidence_score": 0.9,
        },
        {
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "tool_name": "tool_b",
            "inputs": {"param": "value2"},
            "outputs": {"result": "output2"},
            "execution_time": 1.2,
            "error_state": "Error occurred",
            "llm_reasoning_trace": "reasoning_b",
            "confidence_score": 0.6,
        },
        {
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "tool_name": "tool_a",
            "inputs": {"param": "value3"},
            "outputs": {"result": "output3"},
            "execution_time": 0.8,
            "error_state": None,
            "llm_reasoning_trace": "reasoning_c",
            "confidence_score": 0.8,
        },
    ]
    with open(file_path, "w") as f:
        json.dump(traces, f, indent=2, default=str)
    return str(file_path)


@pytest.fixture
def dummy_sqlite_trace_file(tmp_path):
    file_path = tmp_path / "dummy_traces.db"
    conn = sqlite3.connect(file_path)
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
    traces = [
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool_name": "tool_a",
            "inputs": {"param": "value1"},
            "outputs": {"result": "output1"},
            "execution_time": 0.5,
            "error_state": None,
            "llm_reasoning_trace": "reasoning_a",
            "confidence_score": 0.9,
        },
        {
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "tool_name": "tool_b",
            "inputs": {"param": "value2"},
            "outputs": {"result": "output2"},
            "execution_time": 1.2,
            "error_state": "Error occurred",
            "llm_reasoning_trace": "reasoning_b",
            "confidence_score": 0.6,
        },
        {
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "tool_name": "tool_a",
            "inputs": {"param": "value3"},
            "outputs": {"result": "output3"},
            "execution_time": 0.8,
            "error_state": None,
            "llm_reasoning_trace": "reasoning_c",
            "confidence_score": 0.8,
        },
    ]
    for event in traces:
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
    return str(file_path)


# --- Tests for `agenthelm traces list` ---


def test_traces_list_json_output(dummy_json_trace_file):
    result = runner.invoke(
        app, ["traces", "list", "--trace-file", dummy_json_trace_file, "--json"]
    )
    assert result.exit_code == 0
    output_json = json.loads(result.stdout)
    assert len(output_json) == 3
    assert output_json[0]["tool_name"] == "tool_a"


def test_traces_list_table_output(dummy_json_trace_file):
    result = runner.invoke(
        app, ["traces", "list", "--trace-file", dummy_json_trace_file]
    )
    assert result.exit_code == 0
    assert "tool_a" in result.stdout
    assert "tool_b" in result.stdout
    assert "SUCCESS" in result.stdout
    assert "FAILED" in result.stdout


def test_traces_list_pagination(dummy_json_trace_file):
    result = runner.invoke(
        app,
        [
            "traces",
            "list",
            "--trace-file",
            dummy_json_trace_file,
            "--limit",
            "1",
            "--offset",
            "1",
            "--json",
        ],
    )
    assert result.exit_code == 0
    output_json = json.loads(result.stdout)
    assert len(output_json) == 1
    assert output_json[0]["tool_name"] == "tool_b"


# --- Tests for `agenthelm traces show` ---


def test_traces_show_json_file(dummy_json_trace_file):
    result = runner.invoke(
        app, ["traces", "show", "0", "--trace-file", dummy_json_trace_file]
    )
    assert result.exit_code == 0
    assert "Tool Name: tool_a" in result.stdout
    assert "Status: SUCCESS" in result.stdout
    assert '"param": "value1"' in result.stdout


def test_traces_show_sqlite_file(dummy_sqlite_trace_file):
    result = runner.invoke(
        app, ["traces", "show", "0", "--trace-file", dummy_sqlite_trace_file]
    )
    assert result.exit_code == 0
    assert "Tool Name: tool_a" in result.stdout
    assert "Status: SUCCESS" in result.stdout
    assert '"param": "value1"' in result.stdout


def test_traces_show_invalid_id(dummy_json_trace_file):
    result = runner.invoke(
        app, ["traces", "show", "99", "--trace-file", dummy_json_trace_file]
    )
    assert result.exit_code == 1
    assert "Error: Trace ID 99 not found." in result.stderr


# --- Tests for `agenthelm traces filter` ---


def test_traces_filter_by_tool_name(dummy_json_trace_file):
    result = runner.invoke(
        app,
        [
            "traces",
            "filter",
            "--tool-name",
            "tool_a",
            "--trace-file",
            dummy_json_trace_file,
            "--json",
        ],
    )
    assert result.exit_code == 0
    output_json = json.loads(result.stdout)
    assert len(output_json) == 2
    assert all(t["tool_name"] == "tool_a" for t in output_json)


def test_traces_filter_by_status(dummy_json_trace_file):
    result = runner.invoke(
        app,
        [
            "traces",
            "filter",
            "--status",
            "failed",
            "--trace-file",
            dummy_json_trace_file,
            "--json",
        ],
    )
    assert result.exit_code == 0
    output_json = json.loads(result.stdout)
    assert len(output_json) == 1
    assert output_json[0]["tool_name"] == "tool_b"
    assert output_json[0]["error_state"] is not None


def test_traces_filter_by_date_range(dummy_json_trace_file):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    result = runner.invoke(
        app,
        [
            "traces",
            "filter",
            "--date-from",
            today,
            "--trace-file",
            dummy_json_trace_file,
            "--json",
        ],
    )
    assert result.exit_code == 0
    output_json = json.loads(result.stdout)
    assert len(output_json) == 2  # tool_a (latest) and tool_a (2 hours ago)
    assert all(
        datetime.fromisoformat(t["timestamp"]).date()
        == datetime.now(timezone.utc).date()
        for t in output_json
    )


# --- Tests for `agenthelm traces export` ---


def test_traces_export_json(dummy_json_trace_file, tmp_path):
    output_file = tmp_path / "exported_traces.json"
    result = runner.invoke(
        app,
        [
            "traces",
            "export",
            "--output",
            str(output_file),
            "--format",
            "json",
            "--trace-file",
            dummy_json_trace_file,
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(output_file)
    with open(output_file, "r") as f:
        exported_data = json.load(f)
    assert len(exported_data) == 3
    assert exported_data[0]["tool_name"] == "tool_a"


def test_traces_export_csv(dummy_json_trace_file, tmp_path):
    output_file = tmp_path / "exported_traces.csv"
    result = runner.invoke(
        app,
        [
            "traces",
            "export",
            "--output",
            str(output_file),
            "--format",
            "csv",
            "--trace-file",
            dummy_json_trace_file,
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(output_file)
    with open(output_file, "r") as f:
        content = f.read()
    assert "tool_a" in content
    assert "tool_b" in content
    assert "Error occurred" in content


def test_traces_export_md(dummy_json_trace_file, tmp_path):
    output_file = tmp_path / "exported_traces.md"
    result = runner.invoke(
        app,
        [
            "traces",
            "export",
            "--output",
            str(output_file),
            "--format",
            "md",
            "--trace-file",
            dummy_json_trace_file,
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(output_file)
    with open(output_file, "r") as f:
        content = f.read()
        assert "# AgentHelm Trace Export" in content
        assert "### Trace ID: 0" in content
        assert "- **Tool Name**: tool_a\n" in content
        assert "**Status**: FAILED" in content
        assert "**Error**: Error occurred" in content
