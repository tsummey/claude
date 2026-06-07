"""
Scenario 1: Customer Support Resolution Agent
==============================================
Production-grade simulation of the CCAF exam scenario.

Demonstrates:
- Programmatic prerequisite gates (100% enforcement)
- Structured MCP tool error responses
- Escalation calibration via explicit criteria + few-shot examples
- PostToolUse hook for data normalization
- PreToolUse hook for policy enforcement (refund threshold)
- Case facts extraction to prevent context loss
- Multi-issue decomposition

Run: python agent.py
Requires: pip install anthropic
Set env var: ANTHROPIC_API_KEY
"""

import json
import os
from dataclasses import dataclass, field
from typing import Optional
import anthropic

# ──────────────────────────────────────────────
# 1. SESSION STATE — programmatic gate lives here
# ──────────────────────────────────────────────

@dataclass
class SessionState:
    """
    Holds verified state for this customer interaction.
    The prerequisite gate reads from this — NOT from conversation history.
    This is what makes enforcement deterministic.
    """
    verified_customer_id: Optional[str] = None
    verified_customer_name: Optional[str] = None
    looked_up_orders: list = field(default_factory=list)
    total_refunded: float = 0.0
    escalated: bool = False
    resolution_notes: list = field(default_factory=list)


# ──────────────────────────────────────────────
# 2. MOCK BACKEND DATA
# ──────────────────────────────────────────────

with open(os.path.join(os.path.dirname(__file__), "dataset.json")) as f:
    DATASET = json.load(f)

CUSTOMER_DB = DATASET["customer_db"]
ORDER_DB = DATASET["order_db"]


# ──────────────────────────────────────────────
# 3. MCP TOOL IMPLEMENTATIONS
#    Real tools would call actual backends.
#    Notice: rich error responses, not just raises.
# ──────────────────────────────────────────────

def mcp_get_customer(name: str = None, email: str = None, customer_id: str = None) -> dict:
    """
    Lookup and verify customer identity.
    Returns structured error if multiple matches found — agent must clarify.
    """
    if customer_id and customer_id in CUSTOMER_DB:
        cust = CUSTOMER_DB[customer_id]
        if cust.get("name") == "MULTIPLE_MATCH":
            return {
                "isError": True,
                "errorCategory": "validation",
                "isRetryable": False,
                "error": "Multiple accounts found with that name.",
                "action_required": "Request additional identifier (email address or order number) from customer.",
                "match_count": len(cust.get("matches", []))
            }
        return {
            "isError": False,
            "customer_id": customer_id,
            "name": cust["name"],
            "email": cust["email"],
            "account_standing": cust["account_standing"],
            "verified": cust["verified"]
        }

    # Simulate name-based lookup — may return multiple
    matches = [k for k, v in CUSTOMER_DB.items()
               if name and name.lower() in v.get("name", "").lower()]
    if len(matches) > 1:
        return {
            "isError": True,
            "errorCategory": "validation",
            "isRetryable": False,
            "error": f"Found {len(matches)} accounts matching '{name}'.",
            "action_required": "Request email address or order number to uniquely identify the customer."
        }
    if len(matches) == 1:
        cust = CUSTOMER_DB[matches[0]]
        return {
            "isError": False,
            "customer_id": matches[0],
            "name": cust["name"],
            "email": cust["email"],
            "account_standing": cust["account_standing"],
            "verified": cust["verified"]
        }

    return {
        "isError": True,
        "errorCategory": "validation",
        "isRetryable": False,
        "error": "No customer found matching the provided information.",
        "action_required": "Ask customer to verify their account email or order number."
    }


def mcp_lookup_order(order_id: str) -> dict:
    """
    Retrieve order details.
    Note: Returns only relevant fields — 5 fields, not 40.
    Trimming at the source prevents context accumulation.
    """
    if order_id not in ORDER_DB:
        return {
            "isError": True,
            "errorCategory": "validation",
            "isRetryable": False,
            "error": f"Order {order_id} not found.",
            "action_required": "Verify the order number with the customer."
        }
    order = ORDER_DB[order_id]
    # Return ONLY relevant fields — verbose tool output is a context anti-pattern
    return {
        "isError": False,
        "order_id": order_id,
        "item": order["item"],
        "amount": order["amount"],
        "status": order["status"],
        "days_since_order": order["days_since_order"],
        "within_return_window": order["days_since_order"] <= order["return_window_days"]
    }


def mcp_process_refund(order_id: str, amount: float, reason: str) -> dict:
    """
    Process a refund.
    NOTE: The $500 threshold is enforced by PreToolUse hook BEFORE this runs.
    This function should never be called with amount > 500.
    """
    if order_id not in ORDER_DB:
        return {
            "isError": True,
            "errorCategory": "validation",
            "isRetryable": False,
            "error": f"Cannot refund: order {order_id} not found."
        }
    return {
        "isError": False,
        "refund_id": f"REF-{order_id}-{int(amount*100)}",
        "order_id": order_id,
        "amount_refunded": amount,
        "status": "processed",
        "estimated_days": 3,
        "reason": reason
    }


def mcp_escalate_to_human(
    customer_id: str,
    reason: str,
    root_cause: str,
    recommended_action: str,
    refund_amount: float = 0.0,
    order_id: str = None
) -> dict:
    """
    Structured handoff to human agent.
    Includes all context a human needs WITHOUT reading the full transcript.
    """
    return {
        "isError": False,
        "escalation_id": f"ESC-{customer_id}-001",
        "status": "human_agent_notified",
        "handoff_summary": {
            "customer_id": customer_id,
            "reason": reason,
            "root_cause": root_cause,
            "order_id": order_id,
            "refund_amount_requested": refund_amount,
            "recommended_action": recommended_action
        },
        "message_to_customer": "I'm connecting you with a specialist who will have full context of our conversation."
    }


# ──────────────────────────────────────────────
# 4. HOOKS
#    PreToolUse: policy enforcement (threshold blocking)
#    PostToolUse: data normalization
# ──────────────────────────────────────────────

def pre_tool_use_hook(tool_name: str, tool_input: dict, state: SessionState) -> Optional[dict]:
    """
    Returns a blocked-error dict if the call should be intercepted.
    Returns None if the call should proceed.

    This is PreToolUse — it fires BEFORE the tool executes.
    Hook enforcement = 100% guaranteed, unlike prompts.
    """
    if tool_name == "process_refund":
        amount = tool_input.get("amount", 0)
        if amount > 500:
            return {
                "isError": True,
                "errorCategory": "business_rule",
                "isRetryable": False,
                "blocked_by": "PreToolUse hook — automated refund threshold",
                "error": f"Refund of ${amount:.2f} exceeds the $500 automated threshold.",
                "action_required": "Call escalate_to_human with full context for manager approval."
            }
    return None


def post_tool_use_hook(tool_name: str, tool_result: dict, state: SessionState) -> dict:
    """
    PostToolUse fires AFTER a tool returns, BEFORE the model sees the result.
    Use to: normalize formats, extract key facts, enrich results.

    Here we update session state so the prerequisite gate stays current.
    """
    if tool_name == "get_customer" and not tool_result.get("isError"):
        # Update the gate state
        state.verified_customer_id = tool_result.get("customer_id")
        state.verified_customer_name = tool_result.get("name")

        # Normalize: add a human-friendly verification status field
        tool_result["verification_status"] = "VERIFIED" if tool_result.get("verified") else "UNVERIFIED"

    if tool_name == "lookup_order" and not tool_result.get("isError"):
        state.looked_up_orders.append(tool_result.get("order_id"))

    if tool_name == "process_refund" and not tool_result.get("isError"):
        state.total_refunded += tool_result.get("amount_refunded", 0)
        state.resolution_notes.append(f"Refunded ${tool_result['amount_refunded']:.2f} for {tool_result['order_id']}")

    if tool_name == "escalate_to_human" and not tool_result.get("isError"):
        state.escalated = True
        state.resolution_notes.append(f"Escalated: {tool_result['handoff_summary']['reason']}")

    return tool_result


# ──────────────────────────────────────────────
# 5. PREREQUISITE GATE
#    Called inside execute_tool() BEFORE dispatching.
#    This is NOT a hook — it's a sequential ordering enforcer.
# ──────────────────────────────────────────────

def prerequisite_gate(tool_name: str, state: SessionState) -> Optional[dict]:
    """
    Blocks tool calls that require prior verified state.

    Critical distinction:
    - Hooks intercept calls for policy enforcement (amount thresholds, format normalization)
    - Prerequisite gates enforce ORDERING (must do X before Y)

    Both are deterministic. Neither relies on the LLM to comply.
    """
    if tool_name in ("lookup_order", "process_refund", "escalate_to_human"):
        if state.verified_customer_id is None:
            return {
                "isError": True,
                "errorCategory": "prerequisite_not_met",
                "isRetryable": False,
                "error": f"Cannot call {tool_name}: customer identity not yet verified.",
                "required_action": "Call get_customer first to verify customer identity.",
                "reason": "Identity verification is required before any account operations to prevent misidentified refunds."
            }
    return None


# ──────────────────────────────────────────────
# 6. TOOL EXECUTOR — wires everything together
# ──────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict, state: SessionState) -> dict:
    """
    Execution order:
    1. Prerequisite gate (ordering enforcement)
    2. PreToolUse hook (policy enforcement)
    3. Actual tool execution
    4. PostToolUse hook (normalization + state update)
    """
    # Step 1: Ordering gate
    gate_error = prerequisite_gate(tool_name, state)
    if gate_error:
        return gate_error

    # Step 2: Pre-execution hook
    hook_error = pre_tool_use_hook(tool_name, tool_input, state)
    if hook_error:
        return hook_error

    # Step 3: Execute
    dispatch = {
        "get_customer": mcp_get_customer,
        "lookup_order": mcp_lookup_order,
        "process_refund": mcp_process_refund,
        "escalate_to_human": mcp_escalate_to_human,
    }
    if tool_name not in dispatch:
        return {"isError": True, "error": f"Unknown tool: {tool_name}"}

    result = dispatch[tool_name](**tool_input)

    # Step 4: Post-execution hook
    result = post_tool_use_hook(tool_name, result, state)

    return result


# ──────────────────────────────────────────────
# 7. TOOL DEFINITIONS (what Claude sees)
#    Notice: rich descriptions with boundaries,
#    example inputs, and "when NOT to use"
# ──────────────────────────────────────────────

TOOLS = [
    {
        "name": "get_customer",
        "description": (
            "Look up and verify a customer's identity before any account operation. "
            "REQUIRED as the first call in every interaction — no other tool may be called until this returns a verified customer ID. "
            "Input: provide name AND email when available; name alone works if unambiguous. "
            "Returns: customer_id, account standing, verification status. "
            "If multiple accounts match, this tool returns an error requesting additional identifiers — ask the customer. "
            "Do NOT use lookup_order as a substitute for identity verification."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Customer's full name"},
                "email": {"type": "string", "description": "Customer's account email — preferred for unique identification"},
                "customer_id": {"type": "string", "description": "Direct customer ID if already known"}
            }
        }
    },
    {
        "name": "lookup_order",
        "description": (
            "Retrieve details for a specific ORDER — not customer account details. "
            "Use when the customer references an order number, shipment, delivery, or purchase. "
            "Input: order_id (format: ORD-XXXX). "
            "Returns: item name, amount, status, days since order, whether within return window. "
            "REQUIRES: get_customer must have been called first. "
            "Do NOT use to look up customer account info — use get_customer for that."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order identifier in format ORD-XXXX"}
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "process_refund",
        "description": (
            "Issue a refund for a verified order. "
            "Use when: item was damaged, wrong item received, non-delivery confirmed, duplicate charge confirmed. "
            "Automated limit: $500. Amounts above $500 require human approval — use escalate_to_human instead. "
            "REQUIRES: get_customer and lookup_order must have been called first. "
            "Do NOT use for policy exceptions (return window exceeded, competitor price matching) — escalate those."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount": {"type": "number", "description": "Refund amount in USD"},
                "reason": {"type": "string", "description": "Brief reason for refund (e.g., 'damaged on arrival', 'non-delivery')"}
            },
            "required": ["order_id", "amount", "reason"]
        }
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Transfer this case to a human agent. "
            "REQUIRED when: (1) customer explicitly requests a human, (2) refund exceeds $500, "
            "(3) return window has been exceeded, (4) policy is silent on the customer's request, "
            "(5) account access issues, (6) agent cannot make meaningful progress. "
            "Always call get_customer first so the human receives a verified customer ID. "
            "Provide complete context in the handoff — the human will not have this conversation history."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "reason": {"type": "string", "description": "Why escalation is needed"},
                "root_cause": {"type": "string", "description": "Root cause of the customer's issue"},
                "recommended_action": {"type": "string", "description": "What the human agent should do"},
                "refund_amount": {"type": "number", "description": "Amount requested, if applicable"},
                "order_id": {"type": "string", "description": "Relevant order ID, if applicable"}
            },
            "required": ["customer_id", "reason", "root_cause", "recommended_action"]
        }
    }
]


# ──────────────────────────────────────────────
# 8. SYSTEM PROMPT
#    Escalation criteria are explicit with examples.
#    This handles the 45% → 80%+ FCR improvement.
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are a customer support resolution agent. Your goal is 80%+ first-contact resolution.

IDENTITY VERIFICATION: Always call get_customer first. You may not call any other tool until customer identity is verified.

RESOLVE AUTONOMOUSLY when:
- Damage/defect with evidence → process_refund
- Non-delivery confirmed in system → process_refund
- Duplicate charge confirmed → process_refund
- Wrong item received → process_refund
- Return confirmed in system, refund not processed → process_refund

ESCALATE IMMEDIATELY (do not attempt to resolve first) when:
- Customer explicitly asks for a human: honor immediately, no investigation first
- Refund amount exceeds $500: the system will block you — escalate proactively
- Return window exceeded: policy exception required, always escalate
- Policy is silent on the request (e.g., competitor price matching): escalate, do not interpret
- Account access/security issues: outside your scope

MULTI-ISSUE REQUESTS: Decompose into separate items. Address each. Synthesize one response.

MULTIPLE CUSTOMER MATCHES: If get_customer returns multiple matches, ask for email or order number. Never select heuristically.

ESCALATION HANDOFF: Always include customer_id, root cause, what you found, and recommended action.

FEW-SHOT EXAMPLES:

Example 1 — Damaged item (RESOLVE):
Customer: "My order ORD-5521 arrived with a cracked screen."
→ get_customer → lookup_order → process_refund (item delivered, within window, damage evident)

Example 2 — Explicit human request (ESCALATE IMMEDIATELY):
Customer: "I want to speak to a real person."
→ get_customer → escalate_to_human (do NOT investigate first)

Example 3 — Policy exception (ESCALATE):
Customer: "I want to return something from 3 months ago."
→ get_customer → lookup_order → escalate_to_human (outside return window = policy exception)

Example 4 — Policy gap (ESCALATE):
Customer: "Can you match the price from CompetitorX?"
→ get_customer → escalate_to_human (policy silent on competitor matching)
"""


# ──────────────────────────────────────────────
# 9. AGENT LOOP
# ──────────────────────────────────────────────

def run_agent(case: dict, verbose: bool = True) -> dict:
    """
    Run the customer support agent on a single case.
    Returns outcome dict for test runner to evaluate.
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    state = SessionState()
    messages = [{"role": "user", "content": case["request"]}]
    tools_called = []

    if verbose:
        print(f"\n{'='*60}")
        print(f"Case {case['id']}: {case['request'][:70]}...")
        print(f"Expected: {case['expected_resolution']}")
        print(f"{'='*60}")

    max_iterations = 10  # Safety cap — not primary stop mechanism
    for iteration in range(max_iterations):
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        # Append assistant response to history
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Extract final text response
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text = block.text
                    break
            if verbose:
                print(f"  Final response: {final_text[:150]}...")
                print(f"  Tools called: {tools_called}")
                print(f"  Escalated: {state.escalated}")
                print(f"  Total refunded: ${state.total_refunded:.2f}")
            break

        elif response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tools_called.append(block.name)
                    if verbose:
                        print(f"  → {block.name}({json.dumps(block.input)[:80]})")

                    result = execute_tool(block.name, block.input, state)

                    if verbose and result.get("isError"):
                        print(f"    ← ERROR: {result.get('error', '')[:80]}")
                    elif verbose:
                        print(f"    ← OK: {str(result)[:80]}")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })

            messages.append({"role": "user", "content": tool_results})

    # Determine actual resolution
    if state.escalated:
        actual_resolution = "escalated"
    elif state.total_refunded > 0 or state.looked_up_orders:
        actual_resolution = "resolved"
    else:
        actual_resolution = "pending_clarification"

    return {
        "case_id": case["id"],
        "expected_resolution": case["expected_resolution"],
        "actual_resolution": actual_resolution,
        "tools_called": tools_called,
        "total_refunded": state.total_refunded,
        "escalated": state.escalated,
        "correct": actual_resolution == case["expected_resolution"]
    }


# ──────────────────────────────────────────────
# 10. DEMO — run a single case
# ──────────────────────────────────────────────

if __name__ == "__main__":
    # Run Case C001: simple damage refund
    test_case = DATASET["cases"][0]
    result = run_agent(test_case, verbose=True)
    print(f"\nResult: {'PASS' if result['correct'] else 'FAIL'}")
    print(f"Expected: {result['expected_resolution']} | Got: {result['actual_resolution']}")
