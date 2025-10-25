# Core Concepts

This section explains the fundamental ideas behind AgentHelm.

## The Tracer: The Heart of Observability

The `ExecutionTracer` is the central component for running tools and recording their behavior. It acts as a wrapper around every tool call, ensuring that no action goes unrecorded.

Its primary responsibilities are:

1.  **Execution**: It takes a tool function and its arguments and executes it.
2.  **Tracing**: It records the inputs, outputs, execution time, and any errors that occur during the execution.
3.  **Event Creation**: It creates a structured `Event` object for every execution, which is then saved to a storage backend (like a JSON file).

By routing all tool calls through the tracer, we gain a complete and auditable log of everything the agent does.

## The Agent: The Brain of the Operation

The `Agent` class is responsible for orchestrating the entire workflow. It uses a **Reason-Act (ReAct)** loop to achieve a user's goal.

Here's how it works:

1.  **Reason**: The agent takes the user's task and the history of previous steps and presents them to a Large Language Model (LLM). It asks the LLM to decide on the single next best action.
2.  **Act**: The agent parses the LLM's response, which includes the tool to use and the arguments to use it with. It then uses the `ExecutionTracer` to execute that tool.
3.  **Observe**: The result of the tool execution (the "observation") is added to the history.
4.  **Repeat**: The loop repeats, feeding the new observation back into the LLM for the next reasoning step.

This loop continues until the LLM decides the task is complete and calls the special `finish` tool.

## The Event Model

Every action in AgentHelm is recorded as an `Event`. This is a Pydantic model that provides a consistent structure for our logs. The key fields are:

-   `timestamp`: When the event happened.
-   `tool_name`: The name of the tool that was called.
-   `inputs` & `outputs`: The arguments the tool was called with and what it returned.
-   `error_state`: Any error that occurred.
-   `llm_reasoning_trace`: The "thought" process from the LLM that led to this tool call.
-   `confidence_score`: The LLM's confidence in its decision.

This structured logging is what makes true observability possible.

## Reliability Features

Reliability is a core tenet of AgentHelm. The `ExecutionTracer` implements several key features to make agents more robust:

-   **Human-in-the-Loop (`requires_approval`)**: You can mark any tool as requiring human approval. The tracer will pause execution and wait for confirmation before proceeding.
-   **Retries**: For tools that might be flaky (e.g., due to network issues), you can specify a number of retries. The tracer will automatically re-run the tool on failure.
-   **Rollbacks (`compensating_tool`)**: You can link a tool to a "compensating" tool that can undo its action. If a step in a multi-step workflow fails, the `Agent` will instruct the `Tracer` to execute the compensating tools for all previously completed steps in reverse order, ensuring the system doesn't get left in an inconsistent state.