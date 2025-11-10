## 1. Safety & Guardrails

### Can your agent safely fail?

- [ ] **Every state-modifying operation has a rollback procedure**
  - Example: `charge_customer` has corresponding `refund_customer`
  - Rollbacks execute automatically on downstream failures
  - Rollbacks are tested and verified to work

- [ ] **High-risk operations require human approval**
  - Financial transactions above threshold
  - Data deletion or modification
  - External communications to customers
  - Clear approval workflow with full context shown to approver

- [ ] **Agent has hard budget limits**
  - Maximum API tokens per execution
  - Maximum execution time (timeout)
  - Maximum API calls per minute/hour
  - Budget violations halt execution, don't just log

- [ ] **Agent cannot access forbidden resources**
  - Production databases are read-only or require approval
  - Customer PII is redacted in logs
  - Secrets are not exposed to LLM prompts
  - File system access is sandboxed to specific directories

- [ ] **Critical operations are idempotent**
  - Retrying the same operation produces the same result
  - No duplicate charges, emails, or state changes
  - Request IDs or transaction IDs prevent duplicates

---

## 2. Observability & Debugging

### Can you debug a failure in under 60 seconds?

- [ ] **Every LLM call is logged with full context**
  - Complete prompt sent to LLM
  - Complete response received
  - Model name and parameters
  - Timestamp and execution time
  - Cost in tokens and dollars

- [ ] **Every tool execution is traced**
  - Tool name and parameters
  - Return value or error
  - Execution time
  - Success/failure status
  - Stack trace on errors

- [ ] **You can replay any execution from logs**
  - Stored traces include enough information to reproduce the execution
  - You can step through agent reasoning (ReAct pattern)
  - You can see why the LLM chose each action

- [ ] **You can query failures efficiently**
  - Filter by: status, tool name, date range, execution time
  - Find patterns: "Which tools fail most often?"
  - Export for analysis: CSV, JSON, or database format

- [ ] **Logs are structured, not just text**
  - JSON or JSONL format
  - Consistent schema across executions
  - Queryable with standard tools (jq, SQL, Elasticsearch)

---

## 3. Reliability & Resilience

### Does your agent recover gracefully from failures?

- [ ] **Transient failures trigger automatic retries**
  - Network timeouts retry with exponential backoff
  - Rate limit errors wait and retry
  - Configurable max retries per operation
  - Different retry policies for different tools

- [ ] **Partial failures trigger automatic rollback**
  - If step 3 fails, steps 2 and 1 are undone
  - Compensating transactions restore consistent state
  - Rollback failures are logged and alerted

- [ ] **Critical paths have timeout protection**
  - No operation runs indefinitely
  - Timeout values are tuned per operation type
  - Timeouts trigger rollback, not just errors

- [ ] **System degrades gracefully when dependencies fail**
  - Non-critical tools can fail without stopping workflow
  - Agent provides partial results when possible
  - Clear error messages explain what failed and why

- [ ] **Concurrent executions don't interfere**
  - Multiple agent runs don't corrupt shared state
  - Lock mechanisms prevent race conditions
  - Workflow isolation is tested

---

## 4. Compliance & Audit

### Can you prove what your agent did and why?

- [ ] **Full audit trail of agent decisions**
  - Who/what triggered the execution
  - Every decision point with LLM reasoning
  - Every action taken and its result
  - Timestamps for entire chain of events

- [ ] **Human-in-the-loop for regulated operations**
  - GDPR data deletion requires approval
  - Financial transactions require review
  - Approval records stored permanently
  - Approver identity and timestamp logged

- [ ] **Cost tracking per execution**
  - Total API cost (tokens × price per token)
  - Per-model cost breakdown
  - Cost alerts when budget is exceeded
  - Historical cost trends

- [ ] **Reproducible execution from stored traces**
  - Exact LLM version and parameters recorded
  - Tool versions and dependencies captured
  - Can reproduce execution for compliance review
  - Traces stored for required retention period

- [ ] **Sensitive data is handled correctly**
  - PII is redacted in logs
  - Secrets never appear in traces
  - Compliance with GDPR, CCPA, etc.
  - Data retention policies enforced

---

## 5. Testing & Validation

### Have you tested what happens when things break?

- [ ] **Unit tests for every tool**
  - Test success cases
  - Test error cases
  - Test edge cases (empty inputs, null values)
  - Mock external dependencies

- [ ] **Integration tests for multi-step workflows**
  - Test complete end-to-end flows
  - Test with real LLM (not mocked)
  - Test with production-like data
  - Verify rollback works correctly

- [ ] **Failure injection tests**
  - What if step 3 fails? Does rollback work?
  - What if external API is down?
  - What if LLM returns malformed response?
  - What if network timeout occurs?

- [ ] **Cost estimation before production**
  - Run workflow with test data
  - Measure token usage and API costs
  - Project costs at production scale
  - Set up cost alerts

- [ ] **Load testing for expected traffic**
  - Can system handle peak load?
  - Are rate limits respected?
  - Does performance degrade gracefully?
  - Are bottlenecks identified?

---

## 6. Monitoring & Alerting

### Will you know immediately when something goes wrong?

- [ ] **Real-time alerts for critical failures**
  - Agent execution failures
  - Budget overruns
  - Rollback failures
  - Suspicious patterns (unusual cost, repeated failures)

- [ ] **Dashboards for operational visibility**
  - Success/failure rates
  - Average execution time
  - Cost trends over time
  - Most common failure modes

- [ ] **On-call runbooks for common issues**
  - What to do when agent fails
  - How to manually trigger rollback
  - How to disable agent in emergency
  - Escalation paths for different failure types

- [ ] **Regular review of agent behavior**
  - Weekly review of failure patterns
  - Monthly cost analysis
  - Quarterly security audit
  - Continuous improvement based on incidents

---

## 7. Human Oversight

### Can humans intervene when needed?

- [ ] **Clear mechanism to pause/stop execution**
  - Emergency kill switch
  - Graceful shutdown (finish current step, then stop)
  - Preserve state for later resumption

- [ ] **Ability to manually override decisions**
  - Human can approve/reject specific actions
  - Override decisions are logged
  - Override doesn't break workflow

- [ ] **Escalation paths for edge cases**
  - Agent can ask for human help
  - Clear SLAs for human response time
  - Workflow pauses until human responds

- [ ] **Regular human review of agent outputs**
  - Spot checks of decisions
  - Review of edge cases
  - Validation that agent behavior matches intent

---

## 8. Deployment & Operations

### Is your deployment process safe and repeatable?

- [ ] **Staging environment for testing**
  - Separate from production
  - Representative data (but not real customer data)
  - Test all changes in staging first

- [ ] **Gradual rollout strategy**
  - Deploy to 1% of traffic first
  - Monitor for issues before full rollout
  - Easy rollback if problems detected

- [ ] **Version control for prompts and tools**
  - Prompts are versioned
  - Tool definitions are versioned
  - Can roll back to previous versions

- [ ] **Clear deployment documentation**
  - Step-by-step deployment guide
  - Rollback procedures
  - Contact information for incidents

- [ ] **Post-deployment validation**
  - Smoke tests run automatically
  - Verify agent is working as expected
  - Alert if smoke tests fail
