# Lab D2-02: Structured Error Responses for MCP Tools
### Domain 2 | Task Statement 2.2 | Estimated Time: 40 minutes

---

## Objective

Build MCP tools with structured error responses and observe how the agent behaves
differently with generic vs. structured errors. You will implement all four error
categories, demonstrate the empty-results-vs-access-failure distinction, and
build local recovery logic.

---

## Setup

Create: `C:\Users\tsummey\projects\claude\claude_architect\labs\lab_d2_02_work.py`

---

## Part 1: Generic vs. Structured Errors (20 minutes)

```python
import anthropic
import json
import time
import random
from datetime import datetime

client = anthropic.Anthropic()

# ============================================================
# TOOLS WITH GENERIC ERRORS (broken version)
# ============================================================

def search_database_generic(query: str) -> dict:
    """Generic error — tells the agent nothing useful."""
    # Simulate various failure modes
    failure_type = random.choice(["timeout", "not_found", "permission", "success"])

    if failure_type == "timeout":
        return {"error": "Operation failed"}          # What kind? Retryable?
    elif failure_type == "not_found":
        return {"error": "Operation failed"}          # Same error! Indistinguishable!
    elif failure_type == "permission":
        return {"error": "Operation failed"}          # Agent can't make decisions
    else:
        return {"results": [{"id": 1, "name": "Result A"}]}

# ============================================================
# TOOLS WITH STRUCTURED ERRORS (correct version)
# ============================================================

def search_database_structured(query: str, simulate_failure: str = None) -> dict:
    """
    Structured errors enable intelligent agent recovery.
    The agent can decide: retry? fix input? escalate? use partial results?
    """
    failure = simulate_failure or random.choice(
        ["timeout", "timeout", "not_found", "permission", "success", "success", "success"]
    )

    if failure == "timeout":
        return {
            "isError": True,
            "errorCategory": "transient",       # Temporary — worth retrying
            "isRetryable": True,
            "retryAfterSeconds": 2,
            "message": "Database query timed out after 30 seconds",
            "attemptedQuery": query,
            "partialResults": [],
            "suggestedAction": "Retry the query. If timeout persists, try a more specific query."
        }

    elif failure == "not_found":
        # NOT an error — this is valid empty results
        return {
            "isError": False,
            "status": "success",
            "results": [],
            "count": 0,
            "query": query,
            "message": "Query completed successfully. No records match the search criteria."
            # This is very different from an access failure!
        }

    elif failure == "permission":
        return {
            "isError": True,
            "errorCategory": "permission",      # Auth failure — DO NOT retry
            "isRetryable": False,
            "message": "Access denied: insufficient permissions for customer_records table",
            "attemptedQuery": query,
            "requiredPermission": "customer_records:read",
            "suggestedAction": "Escalate to administrator to grant required permissions."
        }

    else:  # success
        return {
            "isError": False,
            "status": "success",
            "results": [
                {"id": 1, "name": "Customer A", "email": "a@example.com"},
                {"id": 2, "name": "Customer B", "email": "b@example.com"}
            ],
            "count": 2,
            "query": query
        }


# Tool definitions
GENERIC_TOOL = {
    "name": "search_database",
    "description": "Search the customer database",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"}
        },
        "required": ["query"]
    }
}

STRUCTURED_TOOL = {
    "name": "search_database",
    "description": (
        "Search the customer database for records matching a query. "
        "Returns either: success with results array (possibly empty if no matches), "
        "or an error with errorCategory (transient/permission), isRetryable flag, "
        "and specific recovery guidance. "
        "Empty results (count: 0) indicate a successful query with no matches — "
        "this is different from an error response."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Customer search query (name, email, or ID)"}
        },
        "required": ["query"]
    }
}
```

### Run Both Versions

```python
SYSTEM_PROMPT = """You are a customer support agent. When searching the database:
- If you get an error, describe what happened and what you tried
- If you get an empty result, tell the customer no records were found
- If a tool suggests retrying, retry once
- If retrying fails or the error is not retryable, explain what happened"""


def run_agent_with_error_type(query: str, tool_fn, tool_def: dict,
                               failure_mode: str, label: str) -> str:
    """Run agent and observe how it handles the error."""

    def execute(tool_name: str, tool_input: dict) -> str:
        result = tool_fn(tool_input.get("query", ""), simulate_failure=failure_mode)
        print(f"    Tool returned: {json.dumps(result)[:150]}")
        return json.dumps(result)

    messages = [{"role": "user", "content": query}]

    print(f"\n[{label}] Failure mode: {failure_mode}")

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            tools=[tool_def],
            messages=messages
        )

        if response.stop_reason == "end_turn":
            text = next((b.text for b in response.content if hasattr(b, "text")), "")
            print(f"  Agent response: {text[:200]}")
            return text

        elif response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute(block.name, block.input)
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "user", "content": results})


# Test each failure mode with both generic and structured error tools
failure_modes = ["timeout", "not_found", "permission"]

for failure in failure_modes:
    print(f"\n{'='*60}")
    print(f"FAILURE MODE: {failure.upper()}")
    print("="*60)

    generic_response = run_agent_with_error_type(
        "Find customer John Smith",
        search_database_generic,
        GENERIC_TOOL,
        failure,
        "GENERIC"
    )

    structured_response = run_agent_with_error_type(
        "Find customer John Smith",
        search_database_structured,
        STRUCTURED_TOOL,
        failure,
        "STRUCTURED"
    )

    print(f"\n  --- Comparison for {failure} ---")
    print(f"  Generic: {generic_response[:100]}")
    print(f"  Structured: {structured_response[:100]}")
```

---

## Part 2: Local Recovery Before Propagation (20 minutes)

```python
class SearchAgentWithRecovery:
    """
    Subagent that implements local recovery for transient failures.
    Only propagates errors it cannot resolve locally.
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.attempts_log = []

    def search(self, query: str) -> dict:
        """
        Try locally, recover if possible, propagate if not.
        """
        last_error = None

        for attempt in range(self.max_retries):
            # Simulate intermittent failures (succeeds ~60% of attempts)
            result = search_database_structured(
                query,
                simulate_failure="timeout" if random.random() < 0.4 else "success"
            )

            self.attempts_log.append({
                "attempt": attempt + 1,
                "result_type": "error" if result.get("isError") else "success"
            })

            if not result.get("isError"):
                print(f"  ✅ Succeeded on attempt {attempt + 1}")
                return result  # Success — return to coordinator

            if result.get("isRetryable") and attempt < self.max_retries - 1:
                wait_time = result.get("retryAfterSeconds", 1) * (2 ** attempt)
                print(f"  ⏳ Transient error, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(min(wait_time, 2))  # Cap at 2s for lab purposes
                last_error = result
                continue
            else:
                # Not retryable or exhausted retries
                last_error = result
                break

        # Could not recover locally — propagate with full context
        print(f"  ❌ Local recovery exhausted after {self.max_retries} attempts")
        return {
            "isError": True,
            "errorCategory": last_error.get("errorCategory", "transient"),
            "isRetryable": True,  # Coordinator might have different retry strategy
            "message": f"Search failed after {self.max_retries} local retry attempts",
            "originalError": last_error.get("message"),
            "attemptedQuery": query,
            "attemptsCount": self.max_retries,
            "partialResults": [],
            "suggestedAlternatives": [
                "Try a more specific query",
                "Try searching by email instead of name",
                "Check if the database service is experiencing issues"
            ]
        }


# Run the recovery agent
print("\n=== LOCAL RECOVERY DEMONSTRATION ===")
agent = SearchAgentWithRecovery(max_retries=3)

for trial in range(3):
    agent.attempts_log = []
    print(f"\nTrial {trial + 1}:")
    result = agent.search("John Smith")
    print(f"  Final result: {'SUCCESS' if not result.get('isError') else 'PROPAGATED ERROR'}")
    print(f"  Attempts made: {agent.attempts_log}")
```

---

## Reflection Questions

```python
"""
REFLECTION:

1. When the generic error tool returned "Operation failed" for both timeout and
   permission failures, what did the agent do in each case?
   Was the behavior appropriate for each failure type?
   Answer:

2. When the structured error tool returned a 'not_found' response (isError: False,
   results: []), vs when it returned a 'timeout' error — how did the agent respond
   differently? Why is this distinction critical?
   Answer:

3. In the local recovery agent, when should isRetryable be True in the propagated
   error even though the local retries failed?
   Answer:

4. A permission error has isRetryable: false. The agent receives it.
   What should it do? What would happen if isRetryable were true for a permission error?
   Answer:

5. A subagent returns partial results (2 out of 5 records retrieved before timeout).
   Why is it better to return the partial results with the error rather than returning
   just the error?
   Answer:
"""
```

---

## Completion Criteria

✅ Agent behavior is observably different for generic vs. structured errors
✅ Not-found result (isError: False, results: []) is distinguished from access failure
✅ Local recovery retries transient errors with backoff before propagating
✅ Permission errors (isRetryable: False) are never retried
✅ All reflection questions answered

---

*Next Lab: D3-01 — CLAUDE.md Configuration and Claude Code Workflows*
