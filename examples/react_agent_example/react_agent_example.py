import os
import json
from orchestrator.core.storage import FileStorage
from orchestrator.core.tool import tool
from orchestrator.core.tracer import ExecutionTracer
from orchestrator.agent import Agent
from orchestrator.llm.mistral_client import MistralClient

# --- Tool Definitions ---

@tool(inputs={'filepath': str}, outputs={'content': str})
def read_file(filepath: str):
    """Reads the entire content of a file and returns it as a string."""
    with open(filepath, 'r') as f:
        content = f.read()
    return content

@tool(inputs={'filepath': str}, outputs={'success': bool})
def undo_append(filepath: str):
    """Removes the last line from a file to undo an append operation."""
    print("--- UNDOING APPEND --- ")
    with open(filepath, 'r') as f:
        lines = f.readlines()
    with open(filepath, 'w') as f:
        f.writelines(lines[:-1])
    return {"success": True}

@tool(
    inputs={'filepath': str, 'content_to_add': str},
    outputs={'success': bool},
    compensating_tool='undo_append'  # Linking the compensating tool
)
def append_to_file(filepath: str, content_to_add: str):
    """Appends a string to the end of a file."""
    with open(filepath, 'a') as f:
        # Ensure content is on a new line
        f.write(f"\n{content_to_add}")
    return {"success": True}

@tool(inputs={}, outputs={})
def failing_tool():
    """This tool is designed to always fail, for testing rollbacks."""
    raise RuntimeError("This tool failed as intended.")


if __name__ == "__main__":
    # 1. Setup the components
    storage = FileStorage('react_trace.json')
    tracer = ExecutionTracer(storage)

    # Get API key from environment variable
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable not set.")

    client = MistralClient(model_name="mistral-small-latest", api_key=api_key)

    # Define the list of tools for the agent
    agent_tools = [read_file, append_to_file, undo_append, failing_tool]

    # Instantiate the Agent
    agent = Agent(tools=agent_tools, tracer=tracer, client=client)

    # --- TEST CASE 1: Successful multi-step task ---
    print("""#-------------------------------------------
# TEST CASE 1: Successful Multi-Step Task
#-------------------------------------------""")
    test_file_1 = "my_react_test_1.txt"
    initial_content_1 = "This is a test of the ReAct agent."
    with open(test_file_1, "w") as f:
        f.write(initial_content_1)
    print(f"--- Initial content of {test_file_1} ---\n{initial_content_1}\n")

    task_1 = f"First, read the content of the file named {test_file_1}. Then, append the line 'This was added by the ReAct agent.' to it."
    agent.run_react(task_1)

    # --- TEST CASE 2: Failing task to test rollback ---
    print("""\n\n#-------------------------------------------
# TEST CASE 2: Failing Task to Test Rollback
#-------------------------------------------""")
    test_file_2 = "my_react_test_2.txt"
    initial_content_2 = "This file will be modified and then restored."
    with open(test_file_2, "w") as f:
        f.write(initial_content_2)
    print(f"--- Initial content of {test_file_2} ---\n{initial_content_2}\n")

    task_2 = f"First, append the line 'THIS LINE SHOULD BE ROLLED BACK' to the file {test_file_2}. Then, run the failing_tool."
    agent.run_react(task_2)

    # Verify the final content of the second file
    final_content_2 = read_file(test_file_2)
    print(f"\n--- Final content of {test_file_2} ---\n{final_content_2}")
    if initial_content_2 == final_content_2.strip():
        print("\nSUCCESS: Rollback worked! File content is unchanged.")
    else:
        print("\nFAILURE: Rollback did not work. File content was modified.")

    # Print the final trace log
    print("\n--- Final Trace Log ---")
    trace_log = storage.load()
    print(json.dumps(trace_log, indent=2, default=str))
