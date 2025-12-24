import pytest
import os
import json
import sqlite3
from agenthelm.core.storage.json_storage import JsonStorage
from agenthelm.core.storage.sqlite_storage import SqliteStorage


# --- Fixtures for JSON Storage ---
@pytest.fixture
def json_storage_file(tmp_path):
    file = tmp_path / "test_trace.json"
    yield str(file)
    if os.path.exists(file):
        os.remove(file)


@pytest.fixture
def json_storage(json_storage_file):
    return JsonStorage(json_storage_file)


# --- Tests for JSON Storage ---
def test_json_storage_init_creates_file(json_storage_file):
    JsonStorage(json_storage_file)
    assert os.path.exists(json_storage_file)
    with open(json_storage_file, "r") as f:
        assert json.load(f) == []


def test_json_storage_save_and_load(json_storage):
    event1 = {"id": 1, "tool_name": "tool_a", "inputs": {"param": "value"}}
    event2 = {"id": 2, "tool_name": "tool_b", "outputs": {"result": "success"}}
    json_storage.save(event1)
    json_storage.save(event2)
    loaded_events = json_storage.load()
    assert len(loaded_events) == 2
    assert loaded_events[0]["tool_name"] == "tool_a"
    assert loaded_events[1]["tool_name"] == "tool_b"


def test_json_storage_save_override(json_storage, json_storage_file):
    event1 = {"id": 1, "tool_name": "tool_a"}
    event2 = {"id": 2, "tool_name": "tool_b"}
    json_storage.save(event1)
    json_storage.save(event2, override=True)
    loaded_events = json_storage.load()
    assert len(loaded_events) == 1
    assert loaded_events[0]["tool_name"] == "tool_b"


def test_json_storage_load_non_existent_file(json_storage_file):
    # Ensure file does not exist
    if os.path.exists(json_storage_file):
        os.remove(json_storage_file)
    storage = JsonStorage(json_storage_file)
    assert storage.load() == []


def test_json_storage_load_corrupted_file(json_storage_file):
    with open(json_storage_file, "w") as f:
        f.write("this is not json")
    storage = JsonStorage(json_storage_file)
    assert storage.load() == []


# --- Fixtures for SQLite Storage ---
@pytest.fixture
def sqlite_storage_file(tmp_path):
    file = tmp_path / "test_trace.db"
    yield str(file)
    if os.path.exists(file):
        os.remove(file)


@pytest.fixture
def sqlite_storage(sqlite_storage_file):
    return SqliteStorage(sqlite_storage_file)


# --- Tests for SQLite Storage ---
def test_sqlite_storage_init_creates_table(sqlite_storage_file):
    SqliteStorage(sqlite_storage_file)
    conn = sqlite3.connect(sqlite_storage_file)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='traces';"
    )
    assert cursor.fetchone() is not None
    conn.close()


def test_sqlite_storage_save_and_load(sqlite_storage):
    event1 = {
        "timestamp": "2025-11-03T10:00:00Z",
        "tool_name": "tool_a",
        "inputs": {"param1": "value1"},
        "outputs": {"result": "output1"},
        "execution_time": 0.5,
        "error_state": None,
        "llm_reasoning_trace": "reasoning1",
        "confidence_score": 0.9,
    }
    event2 = {
        "timestamp": "2025-11-03T10:01:00Z",
        "tool_name": "tool_b",
        "inputs": {"param2": "value2"},
        "outputs": {"result": "output2"},
        "execution_time": 1.2,
        "error_state": "Error message",
        "llm_reasoning_trace": "reasoning2",
        "confidence_score": 0.7,
    }
    sqlite_storage.save(event1)
    sqlite_storage.save(event2)
    loaded_events = sqlite_storage.load()
    assert len(loaded_events) == 2
    assert loaded_events[0]["tool_name"] == "tool_b"  # Most recent first
    assert loaded_events[1]["tool_name"] == "tool_a"
    assert loaded_events[0]["inputs"] == {"param2": "value2"}
    assert loaded_events[1]["outputs"] == {"result": "output1"}


def test_sqlite_storage_query_by_tool_name(sqlite_storage):
    event1 = {
        "timestamp": "2025-11-03T10:00:00Z",
        "tool_name": "tool_a",
        "inputs": {"param1": "value1"},
        "outputs": {"result": "output1"},
        "execution_time": 0.5,
        "error_state": None,
        "llm_reasoning_trace": "reasoning1",
        "confidence_score": 0.9,
    }
    event2 = {
        "timestamp": "2025-11-03T10:01:00Z",
        "tool_name": "tool_b",
        "inputs": {"param2": "value2"},
        "outputs": {"result": "output2"},
        "execution_time": 1.2,
        "error_state": None,
        "llm_reasoning_trace": "reasoning2",
        "confidence_score": 0.7,
    }
    sqlite_storage.save(event1)
    sqlite_storage.save(event2)

    filtered_events = sqlite_storage.query(filters={"tool_name": "tool_a"})
    assert len(filtered_events) == 1
    assert filtered_events[0]["tool_name"] == "tool_a"


def test_sqlite_storage_query_no_filters(sqlite_storage):
    event1 = {
        "timestamp": "2025-11-03T10:00:00Z",
        "tool_name": "tool_a",
        "inputs": {"param1": "value1"},
        "outputs": {"result": "output1"},
        "execution_time": 0.5,
        "error_state": None,
        "llm_reasoning_trace": "reasoning1",
        "confidence_score": 0.9,
    }
    sqlite_storage.save(event1)
    loaded_events = sqlite_storage.query()
    assert len(loaded_events) == 1
    assert loaded_events[0]["tool_name"] == "tool_a"
