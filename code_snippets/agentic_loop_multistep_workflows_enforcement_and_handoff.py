import anthropic
from datetime import datetime
from dotenv import load_dotenv

# Load ANTHROPIC_API_KEY from .env file into the environment.
# Without this, client = anthropic.Anthropic() won't find the key.
load_dotenv()

# Create the Anthropic client. It automatically reads ANTHROPIC_API_KEY
# from the environment loaded above.
client = anthropic.Anthropic()

# stop_reason      When it fires
#-----------------------------------------------------------------------
# "end_turn"       Claude finished normally — your primary exit signal
# "tool_use"       Claude wants to call a tool — execute it and loop again
# "max_tokens"     Response hit the max_tokens limit and got cut off
# "stop_sequence"  Claude generated a custom stop sequence you defined

# =============================================================================
# MULTI-STEP WORKFLOWS — ENFORCEMENT AND HANDOFF PATTERNS
# =============================================================================
#
# This file covers Task Statement 1.4:
#   1. Programmatic enforcement — state gates in execute_tool
#   2. Structured handoff protocols — self-contained escalation packages
#
# Core insight:
#   PROMPTS ARE PROBABILISTIC. CODE IS DETERMINISTIC.
#
#   Approach               Compliance    Use When
#   ─────────────────────────────────────────────────────────────────
#   Prompt instruction     ~95-99%       Style preferences, guidelines
#   Few-shot examples      ~97-99%       Moderate consistency needs
#   Programmatic enforcement  100%       Financial, identity, compliance
#
# A 0.8% failure rate on payment verification sounds small.
# At 10,000 transactions/day that is 80 payments processed without
# identity verification every single day. That is not acceptable.
#
# Rule: If a business rule needs 100% compliance — enforce it in code,
# not in a prompt. Prompts cannot guarantee it. Code can.
# =============================================================================


# =============================================================================
# ESCALATION TRIGGERS
# =============================================================================
#
# Two types of gates in execute_tool:
#
# 1. PREREQUISITE GATES — Claude fixes it itself, no human needed
#    state.verified_customer_id is None → "Call get_customer first"
#    state.verified_order_id is None    → "Call lookup_order first"
#    Claude reads the required_action, calls the right tool, continues.
#
# 2. ESCALATION TRIGGERS — Claude cannot resolve, human intervention required
#    amount > 500                       → "Call escalate_to_human"
#    Customer requests a human          → escalate immediately
#    Policy gap                         → escalate immediately
#    No progress after 3+ attempts      → escalate
#    Claude's job ends here — human takes over.
#
# The handoff summary exists for escalation triggers only.
# Prerequisite gates never reach a human — Claude resolves them itself.
# =============================================================================


# =============================================================================
# AGENT STATE — TRACKS WHAT HAS BEEN VERIFIED
# =============================================================================

class AgentState:
    """
    Tracks verification state for the current session.

    State starts as None for everything — nothing is verified until
    the corresponding tool runs successfully. Gates check this state
    before allowing sensitive tool calls to proceed.

    WHY state lives here and not in the prompt:
    Prompts rely on Claude remembering and following instructions.
    State in code is checked programmatically — Claude has no say in it.
    The gate either passes or it doesn't. 100% of the time.
    """
    def __init__(self):
        # None until get_customer runs successfully
        self.verified_customer_id = None

        # None until lookup_order runs successfully
        self.verified_order_id = None

        # Populated after get_customer succeeds — used in handoff summary
        self.customer_data = {}

        # Full messages history — included in handoff summary
        self.messages = []

# Single state instance shared across execute_tool calls
state = AgentState()


# =============================================================================
# PROGRAMMATIC ENFORCEMENT — STATE GATES IN EXECUTE_TOOL
# =============================================================================

def execute_tool(tool_name: str, tool_input: dict) -> dict:
    """
    Every tool call passes through here before executing.
    Gates check state BEFORE the tool runs — Claude cannot bypass them.

    Two types of responses from a gate:
      - Prerequisite not met → error with required_action (Claude fixes itself)
      - Escalation trigger   → error with escalate_to_human (human takes over)

    isRetryable: False on all gate errors because:
      - Retrying won't fix a missing prerequisite — Claude must call the right tool
      - Retrying won't fix a threshold violation — human must handle it
    """

    # =========================================================================
    # PREREQUISITE GATE 1 — Customer must be verified before order lookup
    # =========================================================================
    if tool_name == "lookup_order":
        if state.verified_customer_id is None:
            # Claude cannot proceed — must verify customer first.
            # required_action tells Claude exactly what to do next.
            # Claude reads this error, calls get_customer, then retries lookup_order.
            # No human involved — Claude resolves this itself.
            return {
                "error": "Cannot lookup order: customer identity not verified.",
                "required_action": "Call get_customer first to verify identity.",
                "isRetryable": False  # Don't retry lookup_order — call get_customer
            }

    # =========================================================================
    # PREREQUISITE GATE 2 — Both customer AND order must be verified for refund
    # =========================================================================
    if tool_name == "process_refund":

        if state.verified_customer_id is None:
            # Customer not verified — Claude must call get_customer first.
            # Gate blocks the refund completely until identity is confirmed.
            return {
                "error": "Cannot process refund: customer identity not verified.",
                "required_action": "Call get_customer first.",
                "isRetryable": False
            }

        if state.verified_order_id is None:
            # Order not verified — Claude must call lookup_order first.
            # Prevents refunds being processed against the wrong order.
            return {
                "error": "Cannot process refund: order not verified.",
                "required_action": "Call lookup_order first.",
                "isRetryable": False
            }

        # =====================================================================
        # ESCALATION TRIGGER — Financial threshold exceeded
        # =====================================================================
        if tool_input.get("amount", 0) > 500:
            # This is NOT a prerequisite gate — Claude cannot fix this itself.
            # The business rule requires human approval for refunds over $500.
            # Claude must escalate — it cannot process this refund at all.
            # call_actual_tool never runs — gate returns before reaching it.
            return {
                "error": f"Refund ${tool_input.get('amount')} exceeds $500 automated limit.",
                "required_action": "Call escalate_to_human with refund details.",
                "isRetryable": False  # Retrying won't change the amount — escalate
            }

    # =========================================================================
    # ALL GATES PASSED — Execute the actual tool
    # =========================================================================
    # Only reaches here if all prerequisite checks above passed.
    # call_actual_tool is never reached if any gate returns early.
    result = call_actual_tool(tool_name, tool_input)

    # =========================================================================
    # UPDATE STATE AFTER SUCCESSFUL TOOL CALLS
    # =========================================================================
    # State updates AFTER the tool succeeds — gates open only when
    # prerequisites are actually met, not just attempted.
    # This is what future gate checks read.
    if tool_name == "get_customer":
        state.verified_customer_id = result.get("customer_id")
        state.customer_data = result  # Store full customer data for handoff

    if tool_name == "lookup_order":
        state.verified_order_id = result.get("order_id")

    return result


def call_actual_tool(tool_name: str, tool_input: dict) -> dict:
    """
    Placeholder for actual tool execution.
    Only called after all gates have passed.
    Replace with real database lookups, API calls, etc.
    """
    # Example responses for illustration
    if tool_name == "get_customer":
        return {
            "customer_id": "CUST-001",
            "name": "Jane Smith",
            "email": "jane@example.com"
        }
    if tool_name == "lookup_order":
        return {
            "order_id": "ORD-12345",
            "amount": 150.00,
            "status": "delivered"
        }
    return {"status": "success"}


# =============================================================================
# STRUCTURED HANDOFF PROTOCOL
# =============================================================================

def compile_handoff_summary(issue: dict) -> dict:
    """
    Build a self-contained handoff package for the human agent.

    WHY self-contained: The human agent does not have access to the
    conversation transcript. They pick up a ticket cold and need
    everything in one place to act immediately.

    A missing field means the human has to go hunting for information —
    slowing resolution and frustrating the customer further.

    The handoff is triggered by escalation triggers only:
      - Financial threshold exceeded (amount > $500)
      - Customer explicitly requests a human
      - Policy gap — request outside documented policy
      - No progress after genuine attempts (3+ failures)
    """
    return {
        # ── WHO IS THE CUSTOMER ──────────────────────────────────────────────
        # Human needs to know who they're dealing with immediately.
        # Pulled from state — verified by get_customer earlier in the session.
        "customer_id": state.verified_customer_id,
        "customer_name": state.customer_data.get("name"),
        "contact_email": state.customer_data.get("email"),

        # ── WHAT ORDER IS INVOLVED ───────────────────────────────────────────
        # Verified by lookup_order — human can pull full order details if needed.
        "order_id": state.verified_order_id,

        # ── WHAT HAPPENED ────────────────────────────────────────────────────
        # Root cause and steps already taken — human doesn't repeat work
        # that Claude already did. Saves time and avoids customer frustration
        # of having to repeat themselves.
        "issue_type": issue["type"],
        "root_cause": issue["root_cause"],
        "resolution_attempted": issue["steps_taken"],

        # ── WHAT THE HUMAN NEEDS TO DO ───────────────────────────────────────
        # Clear recommended action — human knows exactly where to start.
        # policy_exception_required flags if manager approval is needed.
        "recommended_action": issue["recommendation"],
        "refund_amount_requested": issue.get("refund_amount"),
        "policy_exception_required": issue.get("policy_exception", False),

        # ── CONTEXT ──────────────────────────────────────────────────────────
        # Conversation summary — full transcript is too long, summary captures
        # key points. Why escalated — human understands the trigger immediately.
        # Timestamp — for SLA tracking and audit purposes.
        "conversation_summary": summarize_conversation(state.messages),
        "escalation_reason": issue["escalation_reason"],
        "timestamp": datetime.utcnow().isoformat()
    }


def summarize_conversation(messages: list) -> str:
    """
    Placeholder — summarize conversation history for the handoff package.
    In production, this would call Claude to generate a concise summary
    of the key points from the conversation.
    """
    return f"Conversation with {len(messages)} messages. Customer contacted support."


# =============================================================================
# FULL WORKFLOW EXAMPLE — ENFORCEMENT + HANDOFF
# =============================================================================

def run_support_agent(user_message: str, tools: list) -> str:
    """
    Support agent with programmatic enforcement and handoff.

    Flow:
    1. Claude calls tools in whatever order it decides
    2. execute_tool gates check state before each tool runs
    3. If gate blocks → Claude reads error → calls correct tool or escalates
    4. If escalation triggered → compile_handoff_summary → human takes over
    5. If all gates pass → task completes normally
    """
    state.messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            tools=tools,
            messages=state.messages
        )

        if response.stop_reason == "end_turn":
            # Claude finished normally — no escalation needed
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text

        elif response.stop_reason == "tool_use":
            # ✅ Step 1 — append Claude's tool call request first
            state.messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":

                    # Check if this is an escalation call
                    if block.name == "escalate_to_human":
                        # Build self-contained handoff package
                        # Human agent receives everything they need in one place
                        handoff = compile_handoff_summary({
                            "type": block.input.get("issue_type", "unknown"),
                            "root_cause": block.input.get("root_cause", "unknown"),
                            "steps_taken": block.input.get("steps_taken", []),
                            "recommendation": block.input.get("recommendation", ""),
                            "refund_amount": block.input.get("refund_amount"),
                            "policy_exception": block.input.get("policy_exception", False),
                            "escalation_reason": block.input.get("reason", "unknown")
                        })
                        # In production: submit handoff to ticketing system
                        return f"Escalated to human agent. Ticket created. Reference: {handoff['timestamp']}"

                    # All other tools pass through execute_tool gates
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })

            # ✅ Step 3 — append tool results second
            state.messages.append({"role": "user", "content": tool_results})

        else:
            raise RuntimeError(f"Unexpected stop_reason: {response.stop_reason}")


# Sanity check — only runs when this file is executed directly.
# Demonstrates the gate pattern with a simulated refund request.
# Expected behavior: gates enforce correct tool call order.
if __name__ == "__main__":

    # Simulate what happens when Claude tries to skip prerequisites
    print("Testing prerequisite gate — process_refund before get_customer:")
    result = execute_tool("process_refund", {"amount": 150})
    print(result)
    # Expected: error — customer not verified

    print("\nTesting prerequisite gate — lookup_order before get_customer:")
    result = execute_tool("lookup_order", {"order_id": "ORD-12345"})
    print(result)
    # Expected: error — customer not verified

    print("\nRunning get_customer to satisfy Gate 1:")
    result = execute_tool("get_customer", {"email": "jane@example.com"})
    print(result)
    # Expected: success — state.verified_customer_id now set

    print("\nTesting escalation trigger — refund over $500:")
    result = execute_tool("process_refund", {"amount": 750})
    print(result)
    # Expected: escalation error — amount exceeds $500 limit
