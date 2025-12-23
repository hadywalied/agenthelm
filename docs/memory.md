# Memory Hub

AgentHelm's Memory Hub provides a **pluggable memory system** with an SDK-first design. Zero Docker required for basic
usage.

## Quick Start

```python
from agenthelm import MemoryHub, MemoryContext

# In-memory (default, ephemeral)
hub = MemoryHub()

# Short-term memory (key-value)
await hub.short_term.set("user:123:name", "Alice", ttl=3600)
name = await hub.short_term.get("user:123:name")

# Semantic memory (vector search)
await hub.semantic.store("User prefers dark mode.", metadata={"category": "preferences"})
results = await hub.semantic.search("What are the user's UI preferences?")
```

## Architecture

The Memory Hub offers three tiers, automatically selected based on configuration:

| Tier           | Short-Term   | Semantic          | Use Case               |
|----------------|--------------|-------------------|------------------------|
| **In-Memory**  | `dict` + TTL | Qdrant `:memory:` | Development, testing   |
| **Local File** | SQLite       | Qdrant local      | Single-node, no Docker |
| **Network**    | Redis        | Qdrant server     | Production, scaling    |

## Configuration

### In-Memory (Default)

```python
hub = MemoryHub()  # Zero config, ephemeral
```

### Local Persistence

```python
hub = MemoryHub(data_dir="./data")
# Creates:
#   ./data/short_term.db  (SQLite)
#   ./data/qdrant/        (Qdrant local)
```

### Network (Production)

```python
hub = MemoryHub(
    redis_url="redis://localhost:6379",
    qdrant_url="http://localhost:6333"
)
```

## Session Context

Use `MemoryContext` for session-scoped operations with automatic key namespacing:

```python
async with MemoryContext(hub, session_id="user-123") as ctx:
    # Keys are automatically prefixed with session ID
    await ctx.set("last_query", "What is AI?")
    
    # Store memories tagged with session
    await ctx.store_memory("User asked about AI basics.")
    
    # Search within session or globally
    results = await ctx.recall("AI questions", session_only=True)

# Session keys are cleaned up on exit (configurable)
```

## Short-Term Memory API

::: agenthelm.memory.base.BaseShortTermMemory
options:
show_source: false
members:
- get
- set
- delete
- exists
- keys

## Semantic Memory API

::: agenthelm.memory.base.BaseSemanticMemory
options:
show_source: false
members:
- store
- search
- delete
- store_many

## Backend Selection

AgentHelm automatically selects the appropriate backend:

```python
# Explicit backend usage
from agenthelm.memory import InMemoryShortTermMemory, SqliteShortTermMemory, SemanticMemory

# In-memory short-term
memory = InMemoryShortTermMemory()

# SQLite short-term
memory = SqliteShortTermMemory(db_path="./data/cache.db")

# Semantic with mode selection
semantic = SemanticMemory(mode="memory")  # or "local" or "network"
```
