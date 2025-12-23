# API Reference

This section provides a detailed API reference for all public classes and functions in AgentHelm.

## Core

### The `@tool` Decorator

::: agenthelm.tool

### Tool Registry

::: agenthelm.TOOL_REGISTRY

### Execution Tracer

::: agenthelm.ExecutionTracer
    options:
        members:
            - __init__
            - set_trace_context
- execute
- increment_retry

### Event Model

::: agenthelm.Event

### Token Usage

::: agenthelm.TokenUsage

---

## Cost Tracking

### CostTracker

::: agenthelm.CostTracker
options:
members:
- __init__
- record
- get_summary
- get_model_costs

### Factory Function

::: agenthelm.get_cost_tracker

---

## Approval Handlers

::: agenthelm.ApprovalHandler
options:
members:
- request_approval

::: agenthelm.CliHandler

::: agenthelm.AutoApproveHandler

::: agenthelm.AutoDenyHandler

---

## Storage

### BaseStorage

::: agenthelm.core.storage.BaseStorage
options:
members:
- save
- load
- query

### JsonStorage

::: agenthelm.core.storage.JsonStorage

### SqliteStorage

::: agenthelm.core.storage.SqliteStorage

---

## Memory Hub

### MemoryHub

::: agenthelm.MemoryHub
    options:
        members:
            - __init__
- short_term
- semantic
- close

### MemoryContext

::: agenthelm.MemoryContext
    options:
        members:
            - __init__
- get
- set
- delete
- store_memory
- recall
- cleanup

### Short-Term Memory

::: agenthelm.InMemoryShortTermMemory

::: agenthelm.SqliteShortTermMemory

### Semantic Memory

::: agenthelm.SemanticMemory

### Search Results

::: agenthelm.SearchResult
