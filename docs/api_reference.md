# API Reference

This section provides a detailed API reference for all public classes and functions in the AgentHelm framework.

## Agent

::: orchestrator.Agent
    options:
        members:
            - __init__
            - run
            - run_react

## Tools

### The `@tool` decorator

::: orchestrator.tool

### Tool Registry

::: orchestrator.TOOL_REGISTRY

## Tracer

::: orchestrator.ExecutionTracer
    options:
        members:
            - __init__
            - set_trace_context
            - trace_and_execute

## Event Model

::: orchestrator.Event

## Storage

### BaseStorage (Abstract Base Class)

::: orchestrator.BaseStorage
options:
members:
- save
- load
- query

### JsonStorage

::: orchestrator.JsonStorage
options:
members:
- __init__
- save
- load
- exists

### SqliteStorage

::: orchestrator.SqliteStorage
options:
members:
- __init__
- save
- load
- query

## LLM Clients

::: orchestrator.LLMClient
    options:
        members:
            - __init__
            - predict

::: orchestrator.MistralClient
    options:
        members:
            - __init__
            - predict

::: orchestrator.OpenAIClient
    options:
        members:
            - __init__
            - predict

## Approval Handlers

::: orchestrator.ApprovalHandler
    options:
        members:
            - request_approval

::: orchestrator.CliHandler

