from orchestrator.core.tool import tool

# Note: This file only contains tool definitions.
# The CLI (`main.py`) is responsible for loading these tools and running the agent.

@tool()
def read_file(filepath: str) -> str:
    """Reads the entire content of a file and returns it as a string."""
    with open(filepath, 'r') as f:
        content = f.read()
    return content

@tool(requires_approval=True)
def append_to_file(filepath: str, content_to_add: str) -> dict:
    """Appends a string to the end of a file."""
    with open(filepath, 'a') as f:
        f.write(f"\n{content_to_add}")
    return {"success": True}
