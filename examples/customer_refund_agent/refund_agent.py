import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any


from orchestrator.core.storage import FileStorage
from orchestrator.core.tool import tool
from orchestrator.core.tracer import ExecutionTracer
from orchestrator.agent import Agent
from orchestrator.llm.mistral_client import MistralClient
from orchestrator.core.handlers import ApprovalHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# --- Database Simulation ---
# In a real implementation, this would be replaced with actual database connections
class OrderDatabase:
    def __init__(self, db_file="orders_db.json"):
        self.db_file = db_file
        # Initialize with sample data if file doesn't exist
        if not os.path.exists(db_file):
            sample_orders = {
                "ORD-1001": {
                    "customer_id": "CUST-001",
                    "order_date": "2023-05-15",
                    "total_amount": 75.50,
                    "status": "delivered",
                    "items": [
                        {
                            "id": "ITEM-1",
                            "name": "Premium Headphones",
                            "price": 75.50,
                            "quantity": 1,
                        }
                    ],
                    "payment_method": "credit_card",
                },
                "ORD-1002": {
                    "customer_id": "CUST-002",
                    "order_date": "2023-05-20",
                    "total_amount": 125.99,
                    "status": "delivered",
                    "items": [
                        {
                            "id": "ITEM-2",
                            "name": "Wireless Charger",
                            "price": 45.99,
                            "quantity": 1,
                        },
                        {
                            "id": "ITEM-3",
                            "name": "Phone Case",
                            "price": 25.00,
                            "quantity": 2,
                        },
                        {
                            "id": "ITEM-4",
                            "name": "Screen Protector",
                            "price": 15.00,
                            "quantity": 2,
                        },
                    ],
                    "payment_method": "paypal",
                },
                "ORD-1003": {
                    "customer_id": "CUST-003",
                    "order_date": "2023-06-01",
                    "total_amount": 250.00,
                    "status": "processing",
                    "items": [
                        {
                            "id": "ITEM-5",
                            "name": "Smart Watch",
                            "price": 250.00,
                            "quantity": 1,
                        }
                    ],
                    "payment_method": "credit_card",
                },
            }
            with open(db_file, "w") as f:
                json.dump(sample_orders, f, indent=2)

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Retrieve an order by its ID"""
        try:
            with open(self.db_file, "r") as f:
                orders = json.load(f)

            if order_id in orders:
                return orders[order_id]
            return None
        except Exception as e:
            logger.error(f"Error retrieving order {order_id}: {str(e)}")
            return None

    def update_order(self, order_id: str, updated_data: Dict[str, Any]) -> bool:
        """Update an order with new data"""
        try:
            with open(self.db_file, "r") as f:
                orders = json.load(f)

            if order_id in orders:
                orders[order_id].update(updated_data)
                with open(self.db_file, "w") as f:
                    json.dump(orders, f, indent=2)
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {str(e)}")
            return False


class CustomerDatabase:
    def __init__(self, db_file="customers_db.json"):
        self.db_file = db_file
        # Initialize with sample data if file doesn't exist
        if not os.path.exists(db_file):
            sample_customers = {
                "CUST-001": {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "address": "123 Main St, Anytown, USA",
                    "account_status": "active",
                    "refund_history": [],
                },
                "CUST-002": {
                    "name": "Jane Smith",
                    "email": "jane.smith@example.com",
                    "address": "456 Oak Ave, Somewhere, USA",
                    "account_status": "active",
                    "refund_history": [
                        {
                            "order_id": "ORD-999",
                            "amount": 30.00,
                            "date": "2023-04-10",
                            "reason": "damaged item",
                        }
                    ],
                },
                "CUST-003": {
                    "name": "Bob Johnson",
                    "email": "bob.johnson@example.com",
                    "address": "789 Pine Rd, Nowhere, USA",
                    "account_status": "suspended",
                    "refund_history": [],
                },
            }
            with open(db_file, "w") as f:
                json.dump(sample_customers, f, indent=2)

    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Retrieve a customer by their ID"""
        try:
            with open(self.db_file, "r") as f:
                customers = json.load(f)

            if customer_id in customers:
                return customers[customer_id]
            return None
        except Exception as e:
            logger.error(f"Error retrieving customer {customer_id}: {str(e)}")
            return None

    def update_customer(self, customer_id: str, updated_data: Dict[str, Any]) -> bool:
        """Update a customer with new data"""
        try:
            with open(self.db_file, "r") as f:
                customers = json.load(f)

            if customer_id in customers:
                customers[customer_id].update(updated_data)
                with open(self.db_file, "w") as f:
                    json.dump(customers, f, indent=2)
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating customer {customer_id}: {str(e)}")
            return False


class RefundDatabase:
    def __init__(self, db_file="refunds_db.json"):
        self.db_file = db_file
        # Initialize with empty data if file doesn't exist
        if not os.path.exists(db_file):
            with open(db_file, "w") as f:
                json.dump({}, f, indent=2)

    def create_refund(self, refund_data: Dict[str, Any]) -> str:
        """Create a new refund record and return its ID"""
        try:
            with open(self.db_file, "r") as f:
                refunds = json.load(f)

            # Generate a new refund ID
            refund_id = f"REF-{len(refunds) + 1001}"
            refund_data["refund_id"] = refund_id
            refund_data["timestamp"] = datetime.now().isoformat()

            refunds[refund_id] = refund_data

            with open(self.db_file, "w") as f:
                json.dump(refunds, f, indent=2)

            return refund_id
        except Exception as e:
            logger.error(f"Error creating refund: {str(e)}")
            return None

    def get_refund(self, refund_id: str) -> Dict[str, Any]:
        """Retrieve a refund by its ID"""
        try:
            with open(self.db_file, "r") as f:
                refunds = json.load(f)

            if refund_id in refunds:
                return refunds[refund_id]
            return None
        except Exception as e:
            logger.error(f"Error retrieving refund {refund_id}: {str(e)}")
            return None

    def update_refund(self, refund_id: str, updated_data: Dict[str, Any]) -> bool:
        """Update a refund with new data"""
        try:
            with open(self.db_file, "r") as f:
                refunds = json.load(f)

            if refund_id in refunds:
                refunds[refund_id].update(updated_data)
                with open(self.db_file, "w") as f:
                    json.dump(refunds, f, indent=2)
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating refund {refund_id}: {str(e)}")
            return False


# --- Email Service Simulation ---
class EmailService:
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Simulate sending an email"""
        try:
            logger.info(f"Sending email to: {to}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body: {body}")

            # In a real implementation, this would connect to an email service
            # For simulation, we'll just log the email and pretend it was sent

            # Simulate occasional failures for testing error handling
            if to == "fail@example.com":
                raise Exception("Email sending failed")

            return True
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False


# --- Payment Processor Simulation ---
class PaymentProcessor:
    def process_refund(
        self, order_id: str, amount: float, payment_method: str
    ) -> Dict[str, Any]:
        """Simulate processing a refund through a payment gateway"""
        try:
            logger.info(f"Processing refund for order {order_id}")
            logger.info(f"Amount: ${amount:.2f}")
            logger.info(f"Payment method: {payment_method}")

            # In a real implementation, this would connect to a payment gateway
            # For simulation, we'll just log the transaction and generate a fake transaction ID

            # Simulate occasional failures for testing error handling
            if order_id == "ORD-FAIL":
                raise Exception("Payment gateway error")

            transaction_id = f"TXN-{int(time.time())}"

            return {
                "success": True,
                "transaction_id": transaction_id,
                "timestamp": datetime.now().isoformat(),
                "amount": amount,
                "payment_method": payment_method,
            }
        except Exception as e:
            logger.error(f"Error processing refund: {str(e)}")
            return {"success": False, "error": str(e)}

    def reverse_transaction(self, transaction_id: str) -> bool:
        """Simulate reversing a transaction"""
        try:
            logger.info(f"Reversing transaction {transaction_id}")

            # In a real implementation, this would connect to a payment gateway
            # For simulation, we'll just log the reversal

            return True
        except Exception as e:
            logger.error(f"Error reversing transaction: {str(e)}")
            return False


# --- Approval Handler ---
class EmailApprovalHandler(ApprovalHandler):
    def __init__(self, admin_email: str = "admin@example.com"):
        self.admin_email = admin_email
        self.email_service = EmailService()

    def request_approval(self, tool_name: str, arguments: dict) -> bool:
        """
        In a real implementation, this would send an email to an admin and wait for their response.
        For simulation, we'll just log the request and auto-approve after a delay.
        """
        logger.info(f"Requesting approval for {tool_name} with arguments: {arguments}")

        # Simulate sending approval request email
        subject = f"Approval Required: {tool_name}"
        body = f"Please approve the following operation:\n\nTool: {tool_name}\nArguments: {json.dumps(arguments, indent=2)}"
        self.email_service.send_email(self.admin_email, subject, body)

        # Simulate waiting for approval
        logger.info("Waiting for approval...")
        time.sleep(2)  # Simulate delay

        # For simulation, we'll auto-approve unless the amount is over $500
        if tool_name == "process_refund" and arguments.get("refund_amount", 0) > 500:
            logger.info(
                "Approval denied: Amount exceeds maximum allowed for auto-approval"
            )
            return False

        logger.info("Approval granted")
        return True


# Initialize our simulated services
order_db = OrderDatabase()
customer_db = CustomerDatabase()
refund_db = RefundDatabase()
email_service = EmailService()
payment_processor = PaymentProcessor()


# --- Tool Definitions ---
@tool()
def verify_order_status(order_id: str) -> Dict[str, Any]:
    """
    Verify that an order exists and is eligible for refund.
    Returns order details if eligible, or error information if not.
    """
    logger.info(f"Verifying order status for order {order_id}")

    # Get order details
    order = order_db.get_order(order_id)

    if not order:
        return {"success": False, "error": f"Order {order_id} not found"}

    # Check if order status allows refunds
    if order["status"] not in ["delivered", "shipped"]:
        return {
            "success": False,
            "error": f"Order {order_id} has status '{order['status']}' which is not eligible for refund",
        }

    return {"success": True, "order_details": order}


@tool()
def verify_customer_eligibility(customer_id: str) -> Dict[str, Any]:
    """
    Verify that a customer is eligible for refunds.
    Returns customer details if eligible, or error information if not.
    """
    logger.info(f"Verifying customer eligibility for customer {customer_id}")

    # Get customer details
    customer = customer_db.get_customer(customer_id)

    if not customer:
        return {"success": False, "error": f"Customer {customer_id} not found"}

    # Check if customer account is active
    if customer["account_status"] != "active":
        return {
            "success": False,
            "error": f"Customer {customer_id} has account status '{customer['account_status']}' which is not eligible for refund",
        }

    return {"success": True, "customer_details": customer}


@tool()
def validate_refund_amount(order_id: str, refund_amount: float) -> Dict[str, Any]:
    """
    Validate that the refund amount is valid for the given order.
    Returns validation result.
    """
    logger.info(f"Validating refund amount ${refund_amount:.2f} for order {order_id}")

    # Get order details
    order = order_db.get_order(order_id)

    if not order:
        return {"success": False, "error": f"Order {order_id} not found"}

    # Check if refund amount is valid
    if refund_amount <= 0:
        return {"success": False, "error": "Refund amount must be greater than zero"}

    if refund_amount > order["total_amount"]:
        return {
            "success": False,
            "error": f"Refund amount ${refund_amount:.2f} exceeds order total ${order['total_amount']:.2f}",
        }

    # Check if refund requires approval
    requires_approval = refund_amount > 100

    return {
        "success": True,
        "valid_amount": True,
        "requires_approval": requires_approval,
        "order_total": order["total_amount"],
    }


@tool(requires_approval=True, compensating_tool="reverse_refund_transaction")
def process_refund(
    order_id: str, customer_id: str, refund_amount: float, reason: str
) -> Dict[str, Any]:
    """
    Process a refund for an order.
    This is the main action that processes the payment refund.
    Requires approval if the refund amount exceeds $100.
    """
    logger.info(f"Processing refund of ${refund_amount:.2f} for order {order_id}")

    # Get order and customer details
    order = order_db.get_order(order_id)
    customer = customer_db.get_customer(customer_id)

    if not order or not customer:
        return {"success": False, "error": "Invalid order or customer"}

    # Process the refund through the payment processor
    payment_result = payment_processor.process_refund(
        order_id=order_id, amount=refund_amount, payment_method=order["payment_method"]
    )

    if not payment_result["success"]:
        return {
            "success": False,
            "error": f"Payment processing failed: {payment_result.get('error', 'Unknown error')}",
        }

    # Create refund record
    refund_data = {
        "order_id": order_id,
        "customer_id": customer_id,
        "amount": refund_amount,
        "reason": reason,
        "payment_transaction": payment_result,
        "status": "completed",
    }

    refund_id = refund_db.create_refund(refund_data)

    if not refund_id:
        # If refund record creation fails, we should reverse the payment transaction
        payment_processor.reverse_transaction(payment_result["transaction_id"])
        return {"success": False, "error": "Failed to create refund record"}

    # Update customer's refund history
    customer["refund_history"].append(
        {
            "order_id": order_id,
            "amount": refund_amount,
            "date": datetime.now().isoformat(),
            "reason": reason,
            "refund_id": refund_id,
        }
    )

    customer_db.update_customer(customer_id, customer)

    # Update order status
    order["refund_status"] = "refunded"
    order["refund_amount"] = refund_amount
    order["refund_date"] = datetime.now().isoformat()

    order_db.update_order(order_id, order)

    return {
        "success": True,
        "refund_id": refund_id,
        "transaction_id": payment_result["transaction_id"],
        "customer_email": customer["email"],
    }


@tool(retries=2, compensating_tool="send_correction_email")
def send_refund_confirmation(
    customer_email: str, order_id: str, refund_amount: float, refund_id: str
) -> Dict[str, Any]:
    """
    Send a confirmation email to the customer about their refund.
    """
    logger.info(f"Sending refund confirmation email to {customer_email}")

    subject = f"Your Refund for Order {order_id} Has Been Processed"

    body = f"""
Dear Customer,

We're writing to confirm that your refund for Order {order_id} has been processed.

Refund Details:
- Refund ID: {refund_id}
- Amount: ${refund_amount:.2f}
- Date: {datetime.now().strftime("%Y-%m-%d")}

The refund has been issued to your original payment method. Please allow 3-5 business days for the funds to appear in your account.

If you have any questions about this refund, please contact our customer service team and reference your Refund ID.

Thank you for your business.

Best regards,
The Customer Service Team
"""

    email_result = email_service.send_email(customer_email, subject, body)

    if not email_result:
        return {"success": False, "error": "Failed to send confirmation email"}

    return {"success": True, "email_sent": True, "recipient": customer_email}


@tool()
def reverse_refund_transaction(transaction_id: str) -> Dict[str, Any]:
    """
    Compensating action for process_refund.
    Reverses a refund transaction if something goes wrong after the payment processing.
    """
    logger.info(f"Reversing refund transaction {transaction_id}")

    result = payment_processor.reverse_transaction(transaction_id)

    if not result:
        return {"success": False, "error": "Failed to reverse transaction"}

    return {
        "success": True,
        "transaction_reversed": True,
        "transaction_id": transaction_id,
    }


@tool()
def send_correction_email(customer_email: str, order_id: str) -> Dict[str, Any]:
    """
    Compensating action for send_refund_confirmation.
    Sends a correction email if the original confirmation had issues.
    """
    logger.info(f"Sending correction email to {customer_email}")

    subject = f"Important Update About Your Refund for Order {order_id}"

    body = f"""
Dear Customer,

We're writing to inform you about an important update regarding your recent refund for Order {order_id}.

There was a technical issue with our refund processing system. Our team is working to resolve this issue as quickly as possible.

Please disregard any previous communication about this refund. We will send you a new confirmation once the refund has been properly processed.

We apologize for any inconvenience this may cause.

If you have any questions, please contact our customer service team.

Best regards,
The Customer Service Team
"""

    email_result = email_service.send_email(customer_email, subject, body)

    if not email_result:
        return {"success": False, "error": "Failed to send correction email"}

    return {"success": True, "email_sent": True, "recipient": customer_email}


@tool()
def log_audit_record(action: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Log an audit record for compliance and tracking purposes.
    """
    logger.info(f"Logging audit record for action: {action}")

    audit_record = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details,
    }

    # In a real implementation, this would write to a secure audit log
    # For simulation, we'll just log it
    logger.info(f"AUDIT: {json.dumps(audit_record, indent=2)}")

    # Write to an audit log file
    try:
        audit_file = "audit_log.json"

        if os.path.exists(audit_file):
            with open(audit_file, "r") as f:
                audit_log = json.load(f)
        else:
            audit_log = []

        audit_log.append(audit_record)

        with open(audit_file, "w") as f:
            json.dump(audit_log, f, indent=2)

        return {"success": True, "audit_recorded": True}
    except Exception as e:
        logger.error(f"Error writing to audit log: {str(e)}")
        return {"success": False, "error": f"Failed to write audit record: {str(e)}"}


# --- Main Execution ---
if __name__ == "__main__":
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)

    # Setup storage and tracer
    storage = FileStorage("refund_agent_trace.json")
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

    # Example task for the agent
    task = """
    Process a refund for order ORD-1001 for customer CUST-001. 
    The refund amount is $50.00 and the reason is 'product not as described'.
    Make sure to verify eligibility, process the refund, and send a confirmation email.
    """

    # Run the agent
    print("\n--- Running Refund Agent ---")
    result = agent.run_react(task, max_steps=10)

    print("\n--- Agent Execution Complete ---")
    print(f"Result: {result}")

    # Display the trace for analysis
    print("\n--- Execution Trace ---")
    trace = storage.load()
    for event in trace:
        print(f"Tool: {event['tool_name']}")
        print(f"Duration: {event['execution_time']}s")
        print(f"Error: {event['error_state']}")
        print(f"llm_reasoning_trace: {event['llm_reasoning_trace']}")
        print(f"confidence_score: {event['confidence_score']}")
        print("---")
