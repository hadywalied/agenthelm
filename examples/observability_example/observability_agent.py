import os
import logging
from orchestrator import Agent, tool, ExecutionTracer
from orchestrator.core.storage.json_storage import JsonStorage
from orchestrator.core.storage.sqlite_storage import SqliteStorage
from orchestrator.llm.mistral_client import MistralClient

# Configure logging for the example
logging.basicConfig(level=logging.INFO, format="%(message)s")

# --- Define some example tools ---


@tool()
def get_current_time(timezone: str) -> str:
    """Returns the current time in a specified timezone."""
    logging.info(f"Executing get_current_time for {timezone}")
    # In a real scenario, this would call an external API
    return f"The current time in {timezone} is HH:MM:SS"


@tool()
def search_web(query: str) -> str:
    """Searches the web for the given query and returns a summary."""
    logging.info(f"Executing search_web for query: {query}")
    # Simulate a web search
    if "weather" in query.lower():
        return "Web search result: Weather is sunny."
    return "Web search result: Information found."


@tool(requires_approval=True)
def send_email(recipient: str, subject: str, body: str) -> str:
    """Sends an email to the specified recipient."""
    logging.info(f"Executing send_email to {recipient} with subject {subject}")
    return "Email sent successfully."


@tool(compensating_tool="undo_create_task")
def create_task(task_name: str, due_date: str) -> str:
    """Creates a new task with a given name and due date."""
    logging.info(f"Executing create_task: {task_name} due {due_date}")
    return f"Task '{task_name}' created."


@tool()
def undo_create_task(task_name: str, due_date: str) -> str:
    """Compensating tool: Undoes the creation of a task."""
    logging.info(f"Executing undo_create_task for: {task_name}")
    return f"Task '{task_name}' undone."


# --- Main execution logic ---


def run_example_agent(storage_type: str = "json"):
    logging.info(
        f"\n--- Running AgentHelm Observability Example with {storage_type.upper()} Storage ---"
    )

    # 1. Setup Storage
    if storage_type == "json":
        trace_file = "observability_trace.json"
        # Clean up previous trace file if it exists
        if os.path.exists(trace_file):
            os.remove(trace_file)
        storage = JsonStorage(trace_file)
    elif storage_type == "sqlite":
        trace_file = "observability_trace.db"
        # Clean up previous trace file if it exists
        if os.path.exists(trace_file):
            os.remove(trace_file)
        storage = SqliteStorage(trace_file)
    else:
        logging.error("Invalid storage type. Use 'json' or 'sqlite'.")
        return

    tracer = ExecutionTracer(storage=storage)

    # 2. Setup LLM Client (using Mistral for this example)
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        logging.warning(
            "MISTRAL_API_KEY not set. Using a dummy client to simulate tool calls."
        )

        class DummyLLMClient(MistralClient):
            _responses = [
                # Response for Task 1: Get current time in London.
                """json
                {
                    "thought": "The user wants to know the current time in London. I should use the get_current_time tool.",
                    "confidence": 0.9,
                    "tool_name": "get_current_time",
                    "arguments": {"timezone": "London"}
                }
                """,
                """json
                {
                    "thought": "I have the current time in London. The task is complete.",
                    "confidence": 1.0,
                    "tool_name": "finish",
                    "arguments": {"answer": "The current time in London is HH:MM:SS"}
                }
                """,
                # Response for Task 2: Search for weather in Paris.
                """json
                {
                    "thought": "The user wants to know the weather in Paris. I should use the search_web tool.",
                    "confidence": 0.8,
                    "tool_name": "search_web",
                    "arguments": {"query": "weather in Paris"}
                }
                """,
                """json
                {
                    "thought": "I have the weather information. The task is complete.",
                    "confidence": 1.0,
                    "tool_name": "finish",
                    "arguments": {"answer": "The weather in Paris is sunny."}
                }
                """,
                # Response for Task 3: Create a task and then fail (to demonstrate rollback).
                """json
                {
                    "thought": "The user wants to create a task. I should use the create_task tool.",
                    "confidence": 0.95,
                    "tool_name": "create_task",
                    "arguments": {"task_name": "Buy groceries", "due_date": "tomorrow"}
                }
                """,
                """json
                {
                    "thought": "I need to do something else, but I will simulate a failure here.",
                    "confidence": 0.1,
                    "tool_name": "non_existent_tool",
                    "arguments": {}
                }
                """,
            ]

            def predict(self, system_prompt: str, user_prompt: str) -> str:
                if not self._responses:
                    logging.error(
                        "DummyLLMClient received more requests than expected."
                    )
                    return '{"tool_name": "finish", "arguments": {"answer": "No more dummy responses."}}'
                return self._responses.pop(0)

        client = DummyLLMClient(model_name="dummy", api_key="dummy")
    else:
        client = MistralClient(model_name="mistral-small-latest", api_key=api_key)

    # 3. Instantiate Agent
    agent = Agent(
        tools=[get_current_time, search_web, send_email, create_task, undo_create_task],
        tracer=tracer,
        client=client,
    )

    # 4. Run some tasks
    logging.info("\nTask 1: Get current time in London.")
    agent.run_react("What is the current time in London?")

    logging.info("\nTask 2: Search for weather in Paris.")
    agent.run_react("Search for weather in Paris.")

    logging.info("\nTask 3: Create a task and then fail (to demonstrate rollback).")
    # Simulate a failure by making the LLM choose a non-existent tool after create_task
    # In a real scenario, this would be a tool raising an exception
    agent.client.responses = (
        [
            '{"tool_name": "create_task", "arguments": {"task_name": "Buy groceries", "due_date": "tomorrow"}}',
            '{"tool_name": "non_existent_tool", "arguments": {}}',  # This will cause a failure
        ]
        if isinstance(agent.client, DummyLLMClient)
        else None
    )  # Only for dummy client

    agent.run_react(
        "Create a task to buy groceries due tomorrow, then do something else."
    )

    logging.info("\n--- Example Run Complete ---")
    logging.info(f"Traces saved to: {trace_file}")
    logging.info("You can now use 'agenthelm traces' commands to explore them.")


if __name__ == "__main__":
    # Run with JSON storage
    run_example_agent("json")

    # Run with SQLite storage
    run_example_agent("sqlite")
