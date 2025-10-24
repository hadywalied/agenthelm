from orchestrator.core.storage import FileStorage
from orchestrator.core.tool import tool
from orchestrator.core.tracer import ExecutionTracer
import json

storage = FileStorage('trace.json')
executor = ExecutionTracer(storage)


@tool(inputs={'filepath': str}, outputs={'content': str})
def read_file(filepath: str):
    with open(filepath, 'r') as f:
        content = f.read()
    return content


@tool(inputs={'filepath': str, 'content': str},
      outputs={'success': bool},
      side_effects=['writing file'],
      requires_approval=True)
def write_file(filepath: str, content: str):
    with open(filepath, 'w') as f:
        f.write(content)
    return {"success": True}


if __name__ == "__main__":
    # Define a test filepath
    test_file = "my_test_file.txt"

    # Create a dummy file to work with
    print(f"--- Creating initial file: {test_file} ---")
    # We don't trace this initial setup
    with open(test_file, "w") as f:
        f.write("Hello from the test file!")

    # Use the tracer to read the file
    print("\n--- Tracing 'read_file' tool ---")
    read_content = executor.trace_and_execute(read_file, filepath=test_file)
    print(f"Read content: '{read_content}'")

    # Modify the content
    modified_content = read_content + "\nThis line was added by the agent."
    print(f"\n--- Modified content in memory ---")
    print(f"'{modified_content}'")

    # Use the tracer to write the file
    print("\n--- Tracing 'write_file' tool ---")
    write_result = executor.trace_and_execute(
        write_file,
        filepath=test_file,
        content=modified_content
    )
    print(f"Write successful: {write_result}")

    # Verify the trace log
    print("\n--- Final Trace Log (from trace.json) ---")
    trace_log = storage.load()

    print(json.dumps(trace_log, indent=2, default=str))
