import os
import json
from orchestrator.core.storage import FileStorage
from orchestrator.core.tool import tool
from orchestrator.core.tracer import ExecutionTracer
from orchestrator.agent import Agent
from orchestrator.llm.mistral_client import MistralClient


@tool(inputs={'filepath': str}, outputs={'content': str})
def read_file(filepath: str):
    """Reads the entire content of a file and returns it as a string."""
    with open(filepath, 'r') as f:
        content = f.read()
    return content


@tool(inputs={'filepath': str, 'content_to_add': str}, outputs={'success': bool})
def append_to_file(filepath: str, content_to_add: str):
    """Appends a string to the end of a file."""
    with open(filepath, 'a') as f:
        f.write(content_to_add)
    return {"success": True}


if __name__ == "__main__":
    # 1. Setup the components
    storage = FileStorage('trace.json')
    tracer = ExecutionTracer(storage)

    # Get API key from environment variable.
    # Make sure to set this in your terminal, e.g., export MISTRAL_API_KEY='your_key_here'
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable not set.")

    client = MistralClient(model_name="mistral-small-latest", api_key=api_key)

    # Define the list of tools for the agent
    agent_tools = [read_file, append_to_file]

    # Instantiate the Agent
    agent = Agent(tools=agent_tools, tracer=tracer, client=client)

    # 2. Create a test file
    test_file = "my_test_file.txt"
    with open(test_file, "w") as f:
        f.write("This is a test of the intelligent agent.\n")
    print(f"--- Initial content of {test_file} ---\nThis is a test of the intelligent agent.\n")

    # 3. Run the agent with a prompt to read the file
    print("\n--- Running Agent to read the file ---")
    agent.run(f"read the content of the file named {test_file}")

    # 4. Run the agent with another prompt to write to the file
    print("\n--- Running Agent to append to the file ---")
    agent.run(f"append the line 'This was added by the agent.' to the file named {test_file}")
    
    # 5. Verify the final content
    final_content = read_file(test_file)
    print(f"\n--- Final content of {test_file} ---\n{final_content}")

    # 6. Print the final trace log
    print("\n--- Final Trace Log ---")
    trace_log = storage.load()
    print(json.dumps(trace_log, indent=2, default=str))
