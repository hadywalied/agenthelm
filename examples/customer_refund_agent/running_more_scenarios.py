import os
import logging
from refund_agent import (
    CustomerDatabase,
    EmailApprovalHandler,
    verify_order_status,
    verify_customer_eligibility,
    validate_refund_amount,
    process_refund,
    send_refund_confirmation,
    reverse_refund_transaction,
    send_correction_email,
    log_audit_record,
)
from orchestrator.core.storage import FileStorage
from orchestrator.core.tracer import ExecutionTracer
from orchestrator.agent import Agent
from orchestrator.llm.mistral_client import MistralClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_agent(trace_file):
    """Set up the agent with all necessary components"""
    # Setup storage and tracer
    storage = FileStorage(trace_file)
    tracer = ExecutionTracer(storage)

    # Get API key from environment variable
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable not set.")

    # Initialize LLM client
    client = MistralClient(model_name="mistral-small-latest", api_key=api_key)

    # Define the list of tools for the agent
    agent_tools = [
        verify_order_status,
        verify_customer_eligibility,
        validate_refund_amount,
        process_refund,
        send_refund_confirmation,
        reverse_refund_transaction,
        send_correction_email,
        log_audit_record,
    ]

    # Set up approval handler for tools that require approval
    approval_handler = EmailApprovalHandler()
    tracer.approval_handler = approval_handler

    # Instantiate the Agent
    agent = Agent(tools=agent_tools, tracer=tracer, client=client)

    return agent, storage


def run_scenario(name, task, trace_file):
    """Run a specific test scenario"""
    print(f"\n\n{'=' * 50}")
    print(f"SCENARIO: {name}")
    print(f"{'=' * 50}")

    agent, storage = setup_agent(trace_file)

    print(f"\nTask: {task}")
    print("\n--- Running Refund Agent ---")

    result = agent.run_react(task, max_steps=10)

    print("\n--- Agent Execution Complete ---")
    print(f"Result: {result}")

    # Display the trace for analysis
    print("\n--- Execution Trace Summary ---")
    trace = storage.load()
    print(f"Total steps: {len(trace)}")
    for i, event in enumerate(trace):
        print(f"Step {i + 1}: {event['tool_name']}")
        print(f"  Success: {event['error_state'] is None}")

    return result, trace


if __name__ == "__main__":
    # Scenario 1: Standard Refund Process
    standard_refund_task = """
    Process a refund for order ORD-1001 for customer CUST-001. 
    The refund amount is $50.00 and the reason is 'product not as described'.
    Make sure to verify eligibility, process the refund, and send a confirmation email.
    """

    run_scenario(
        "Standard Refund Process", standard_refund_task, "standard_refund_trace.json"
    )

    # Scenario 2: High-Value Refund with Approval
    high_value_refund_task = """
    Process a refund for order ORD-1002 for customer CUST-002. 
    The refund amount is $120.00 and the reason is 'item damaged during shipping'.
    Make sure to verify eligibility, process the refund, and send a confirmation email.
    """

    run_scenario(
        "High-Value Refund with Approval",
        high_value_refund_task,
        "high_value_refund_trace.json",
    )

    # Scenario 3: Error Recovery Scenario
    error_recovery_task = """
    Process a refund for order ORD-9999 for customer CUST-001. 
    The refund amount is $25.00 and the reason is 'wrong item received'.
    Make sure to verify eligibility, process the refund, and send a confirmation email.
    """

    run_scenario(
        "Error Recovery Scenario", error_recovery_task, "error_recovery_trace.json"
    )

    # Scenario 4: Rollback Demonstration
    # For this scenario, we'll modify the customer email to trigger a failure
    # First, let's get the current customer data
    customer_db = CustomerDatabase()
    customer = customer_db.get_customer("CUST-001")
    original_email = customer["email"]

    # Update with an email that will trigger a failure
    customer["email"] = "fail@example.com"
    customer_db.update_customer("CUST-001", customer)

    rollback_task = """
    Process a refund for order ORD-1001 for customer CUST-001. 
    The refund amount is $30.00 and the reason is 'changed mind'.
    Send the confirmation email to fail@example.com to trigger a rollback.
    """

    run_scenario("Rollback Demonstration", rollback_task, "rollback_trace.json")

    # Restore the original email
    customer["email"] = original_email
    customer_db.update_customer("CUST-001", customer)

    print(
        "\n\nAll scenarios completed. Check the trace files for detailed execution logs."
    )
