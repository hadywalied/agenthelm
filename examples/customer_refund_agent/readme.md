# Customer Refund Agent Example

This example demonstrates a comprehensive customer refund agent that showcases AgentHelm's capabilities in a real-world business scenario. The agent handles the entire refund workflow from verification to processing and notification, with proper error handling and audit trail capabilities.

## Business Scenario

In e-commerce and retail businesses, processing customer refunds is a critical operation that involves multiple steps and systems:

1. **Verification**: Checking if the order and customer are eligible for a refund
2. **Validation**: Ensuring the refund amount is valid and determining if approval is needed
3. **Processing**: Executing the actual refund transaction through a payment gateway
4. **Notification**: Informing the customer about the refund status
5. **Audit**: Maintaining detailed records of all actions for compliance and tracking

This agent automates the entire workflow while providing robust error handling, approval workflows for high-value refunds, and comprehensive audit trails.

## Workflow Diagram

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Verify Order   │────▶│Verify Customer  │────▶│Validate Refund  │
│    Status       │     │  Eligibility    │     │    Amount       │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
│
▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Send Refund    │◀────│  Process Refund │◀────│ Approval Check  │
│  Confirmation   │     │  Transaction    │     │  (if needed)    │
└────────┬────────┘     └────────┬────────┘     └─────────────────┘
│                       │
▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│   Log Audit     │     │ Error Handling  │
│    Record       │     │   & Rollback    │
└─────────────────┘     └─────────────────┘


## Key Features

1. **Multi-step Workflow Implementation**
   - Verification of order status and customer eligibility
   - Validation of refund amount against order total
   - Processing of refund transaction through payment gateway
   - Sending confirmation email to customer

2. **Error Handling and Rollback**
   - Automatic transaction reversal if email notification fails
   - Compensating actions for each critical operation
   - Proper state management throughout the workflow

3. **Business Logic Enforcement**
   - Approval requirement for refunds exceeding $100 threshold
   - Validation of refund amount against order total
   - Customer account status verification

4. **Audit Trail Capabilities**
   - Detailed logging of all actions and decisions
   - Timestamped records of each workflow step
   - Storage of approval records when required

## Setup Instructions

1. **Environment Setup**
   ```bash
   # Set your API key for the LLM service
   set MISTRAL_API_KEY=your_api_key_here