# API Reference

This section provides a detailed API reference for all public classes and functions in the AgentHelm framework.

## Agent

::: orchestrator.agent.Agent
    options:
        members:
            - __init__
            - run
            - run_react

## Tools

### The `@tool` decorator

::: orchestrator.core.tool.tool

### Tool Registry

::: orchestrator.core.tool.TOOL_REGISTRY

## Tracer

::: orchestrator.core.tracer.ExecutionTracer
    options:
        members:
            - __init__
            - set_trace_context
            - trace_and_execute

## Event Model

::: orchestrator.core.event.Event

## Storage

::: orchestrator.core.storage.FileStorage

## LLM Clients

::: orchestrator.llm.base.LLMClient
    options:
        members:
            - __init__
            - predict

::: orchestrator.llm.mistral_client.MistralClient
    options:
        members:
            - __init__
            - predict

::: orchestrator.llm.openai_client.OpenAIClient
    options:
        members:
            - __init__
            - predict

## Approval Handlers

::: orchestrator.core.handlers.ApprovalHandler
    options:
        members:
            - request_approval

::: orchestrator.core.handlers.CliHandler

