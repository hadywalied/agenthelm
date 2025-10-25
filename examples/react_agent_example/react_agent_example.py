import os
import json
import logging
from orchestrator.core.storage import FileStorage
from orchestrator.core.tool import tool
from orchestrator.core.tracer import ExecutionTracer
from orchestrator.agent import Agent
from orchestrator.llm.mistral_client import MistralClient

# --- Tool Definitions ---

@tool()
def read_file(filepath: str):
    """Reads the entire content of a file and returns it as a string."""
    with open(filepath, 'r') as f:
        content = f.read()
    return content

@tool()
def undo_append(filepath: str):
    """Removes the last line from a file to undo an append operation."""
    logging.warning("--- UNDOING APPEND --- ")
    with open(filepath, 'r') as f:
        lines = f.readlines()
    with open(filepath, 'w') as f:
        f.writelines(lines[:-1])
    return {"success": True}

@tool(
    compensating_tool='undo_append'
)
def append_to_file(filepath: str, content_to_add: str):
    """Appends a string to the end of a file."""
    with open(filepath, 'a') as f:
        f.write(f"\n{content_to_add}")
    return {"success": True}

@tool()
def failing_tool():
    """This tool is designed to always fail, for testing rollbacks."""
    raise RuntimeError("This tool failed as intended.")


if __name__ == "__main__":
    # Note: The logging level is configured by the main CLI in main.py
    # If running this script directly, you may want to add:
    # logging.basicConfig(level=logging.INFO, format="%(message)s")

    # 1. Setup the components
    storage = FileStorage('react_trace.json')
    tracer = ExecutionTracer(storage)

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        logging.error("MISTRAL_API_KEY environment variable not set.")
        exit(1)

    client = MistralClient(model_name="mistral-small-latest", api_key=api_key)
    agent_tools = [read_file, append_to_file, undo_append, failing_tool]
    agent = Agent(tools=agent_tools, tracer=tracer, client=client)

    # --- TEST CASE 1: Successful multi-step task ---
    logging.info("""#-------------------------------------------
# TEST CASE 1: Successful Multi-Step Task
#-------------------------------------------""")
    test_file_1 = "my_react_test_1.txt"
    initial_content_1 = "This is a test of the ReAct agent."
    with open(test_file_1, "w") as f:
        f.write(initial_content_1)
    logging.info(f"--- Initial content of {test_file_1} ---\n{initial_content_1}\n")

    task_1 = f"First, read the content of the file named {test_file_1}. Then, append the line 'This was added by the ReAct agent.' to it."
    agent.run_react(task_1)

    # --- TEST CASE 2: Failing task to test rollback ---
    logging.info("""\n\n#-------------------------------------------
# TEST CASE 2: Failing Task to Test Rollback
#-------------------------------------------""")
    test_file_2 = "my_react_test_2.txt"
    initial_content_2 = "This file will be modified and then restored."
    with open(test_file_2, "w") as f:
        f.write(initial_content_2)
    logging.info(f"--- Initial content of {test_file_2} ---\n{initial_content_2}\n")

    task_2 = f"First, append the line 'THIS LINE SHOULD BE ROLLED BACK' to the file {test_file_2}. Then, run the failing_tool."
    agent.run_react(task_2)

    # Verify the final content of the second file
    final_content_2 = read_file(test_file_2)
    logging.info(f"\n--- Final content of {test_file_2} ---\n{final_content_2}")
    if initial_content_2 == final_content_2.strip():
        logging.info("\nSUCCESS: Rollback worked! File content is unchanged.")
    else:
        logging.error("\nFAILURE: Rollback did not work. File content was modified.")

    # Print the final trace log
    logging.info("\n--- Final Trace Log ---")
    trace_log = storage.load()
    logging.info(json.dumps(trace_log, indent=2, default=str))
