# Lab D5-01: Context Management, Escalation & Error Propagation
### Domain 5 | Task Statements 5.1, 5.2, 5.3 | Estimated Time: 55 minutes

---

## Objective

Build the customer support agent from Scenario 1 with full context management.
You will demonstrate how progressive summarization destroys critical information,
implement the case facts pattern to prevent it, build correct escalation logic,
and wire up structured error propagation across a two-agent system.

---

## Setup

Create: `C:\Users\tsummey\projects\claude\claude_architect\labs\lab_d5_01_work.py`

---

## Part 1: Progressive Summarization Failure (15 minutes)

```python
import anthropic
import json
from datetime import datetime

client = anthropic.Anthropic()

# Simulate a long customer support conversation (already in progress)
LONG_CONVERSATION = [
    {"role": "user", "content": "Hi, I need help with my account."},
    {"role": "assistant", "content": "Happy to help! What's your customer ID?"},
    {"role": "user", "content": "C001. I have two issues."},
    {"role": "assistant", "content": "I can see your account. What are the issues?"},
    {"role": "user", "content": "Order ORD-5001 for $189.99 arrived damaged. I want a refund."},
    {"role": "assistant", "content": "I'm sorry about that. Let me look into order ORD-5001."},
    {"role": "user", "content": "Also, order ORD-5002 had the wrong item. That was $749.00."},
    {"role": "assistant", "content": "I see order ORD-5002 for $749. I'll need to escalate the refund amount. Let me handle ORD-5001 first."},
    {"role": "user", "content": "What's the status on both refunds?"},
    {"role": "assistant", "content": "For ORD-5001 ($189.99 damaged item): I've initiated a refund. For ORD-5002 ($749.00 wrong item): This requires manager approval due to the amount."},
    {"role": "user", "content": "How long will the refund for ORD-5001 take?"},
    {"role": "assistant", "content": "The refund of $189.99 for the damaged jacket should appear in 3-5 business days."},
    {"role": "user", "content": "And what about my complaint reference number?"},
    {"role": "assistant", "content": "Your case has been logged as CMP-2024-7823. You'll receive an email confirmation."},
    {"role": "user", "content": "Let's check on the ORD-5002 escalation."},
]


def summarize_conversation_lossy(conversation: list) -> str:
    """Naive summarization — loses precision values."""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"Summarize this customer support conversation in 2-3 sentences:\n\n"
                      f"{json.dumps(conversation)}"
        }]
    )
    return response.content[0].text


def query_with_lossy_summary(question: str) -> str:
    """Ask a question using a lossy summary as context."""
    summary = summarize_conversation_lossy(LONG_CONVERSATION)
    print(f"\n  Summary used: {summary}")

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=256,
        system="You are a customer support agent. Answer based on the conversation summary provided.",
        messages=[
            {"role": "user", "content": f"Conversation summary: {summary}"},
            {"role": "user", "content": question}
        ]
    )
    return response.content[0].text


print("=== LOSSY SUMMARIZATION TEST ===")
precision_questions = [
    "What is the exact refund amount for order ORD-5001?",
    "What is the customer's complaint reference number?",
    "What is the exact amount of the order that required manager approval?",
    "How many days did we say the refund would take?"
]

for q in precision_questions:
    print(f"\nQ: {q}")
    answer = query_with_lossy_summary(q)
    print(f"A: {answer}")
    # Observe: Does Claude answer with specific values or vague approximations?
    # Are the actual values ($189.99, CMP-2024-7823, $749.00, 3-5 days) preserved?
```

---

## Part 2: Case Facts Pattern — Preserve Precision (15 minutes)

```python
class CustomerCaseFacts:
    """
    Structured container for facts that must not be lost to summarization.
    These are injected into every API call, outside the summarized history.
    """
    def __init__(self):
        self.customer_id: str = None
        self.customer_name: str = None
        self.orders: dict = {}          # {order_id: {amount, status, issue}}
        self.refunds: dict = {}         # {order_id: {amount, status, refund_id}}
        self.complaint_refs: list = []
        self.escalations: list = []
        self.session_start: str = datetime.utcnow().isoformat()

    def add_order(self, order_id: str, amount: float, issue: str, status: str = "open"):
        self.orders[order_id] = {
            "amount": amount,
            "issue": issue,
            "status": status
        }

    def add_refund(self, order_id: str, amount: float, status: str, refund_id: str = None):
        self.refunds[order_id] = {
            "amount": amount,
            "status": status,
            "refund_id": refund_id
        }

    def add_complaint_ref(self, ref: str):
        self.complaint_refs.append(ref)

    def add_escalation(self, order_id: str, reason: str, amount: float):
        self.escalations.append({
            "order_id": order_id,
            "reason": reason,
            "amount": amount,
            "timestamp": datetime.utcnow().isoformat()
        })

    def to_system_block(self) -> str:
        """Format as system prompt block — injected into every API call."""
        orders_text = "\n".join([
            f"  {oid}: ${info['amount']:.2f} | Issue: {info['issue']} | Status: {info['status']}"
            for oid, info in self.orders.items()
        ])

        refunds_text = "\n".join([
            f"  {oid}: ${info['amount']:.2f} | {info['status']}" + 
            (f" | Ref: {info['refund_id']}" if info.get('refund_id') else "")
            for oid, info in self.refunds.items()
        ]) if self.refunds else "  None yet"

        escalations_text = "\n".join([
            f"  {e['order_id']}: ${e['amount']:.2f} | {e['reason']}"
            for e in self.escalations
        ]) if self.escalations else "  None"

        return f"""
╔══════════════════════════════════════════════╗
║  ACTIVE CASE FACTS — DO NOT LOSE THESE       ║
╠══════════════════════════════════════════════╣
║  Customer ID:  {self.customer_id or 'Unknown'}
║  Customer:     {self.customer_name or 'Unknown'}
║  Complaint Refs: {', '.join(self.complaint_refs) or 'None'}
╠══════════════════════════════════════════════╣
║  ORDERS IN THIS CASE:
{orders_text}
╠══════════════════════════════════════════════╣
║  REFUND STATUS:
{refunds_text}
╠══════════════════════════════════════════════╣
║  ESCALATIONS:
{escalations_text}
╚══════════════════════════════════════════════╝
"""


# Initialize case facts from the long conversation
facts = CustomerCaseFacts()
facts.customer_id = "C001"
facts.customer_name = "Jennifer Martinez"
facts.add_order("ORD-5001", 189.99, "Item arrived damaged")
facts.add_order("ORD-5002", 749.00, "Wrong item received")
facts.add_refund("ORD-5001", 189.99, "Processing (3-5 business days)", "REF-5001-1234")
facts.add_refund("ORD-5002", 749.00, "Pending manager approval")
facts.add_complaint_ref("CMP-2024-7823")
facts.add_escalation("ORD-5002", "Amount exceeds $500 automated limit", 749.00)


def query_with_case_facts(question: str) -> str:
    """Ask a question with case facts injected — precision preserved."""
    # Lossy summary of conversation flow (not precision values)
    flow_summary = "Customer C001 reported two order issues. ORD-5001 refund initiated. ORD-5002 escalated for amount."

    system = f"""You are a customer support agent.

{facts.to_system_block()}

Conversation context: {flow_summary}

Answer questions precisely using the exact values in the CASE FACTS above.
Never approximate or vague-ify specific amounts, dates, or reference numbers."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=256,
        system=system,
        messages=[{"role": "user", "content": question}]
    )
    return response.content[0].text


print("\n=== CASE FACTS PATTERN TEST ===")
for q in precision_questions:
    print(f"\nQ: {q}")
    answer = query_with_case_facts(q)
    print(f"A: {answer}")
    # Observe: Are exact values preserved? Compare with lossy version.
```

---

## Part 3: Correct Escalation Logic (15 minutes)

```python
ESCALATION_SYSTEM = """You are a customer support agent handling billing and order issues.

ESCALATION RULES — follow these precisely:

IMMEDIATE ESCALATION (no resolution attempt):
- Customer explicitly requests a human agent: escalate immediately without trying to resolve
- Policy gap: customer request falls outside documented policy → escalate
- Complaint about the agent itself (meta-complaint)

RESOLUTION FIRST, ESCALATE IF INSISTED:
- Customer is frustrated but hasn't explicitly asked for human
- Acknowledge frustration, offer to resolve, escalate only if they repeat the request

DO NOT ESCALATE:
- High-dollar amounts within policy (process normally)
- Complex-sounding issues that are actually routine
- Customer frustration alone

TOOLS AVAILABLE:
- get_customer: retrieve customer account
- lookup_order: get order details
- process_refund: process refund (amounts ≤ $500)
- escalate_to_human: escalate to human agent"""

# Simplified tools for escalation testing
ESCALATION_TOOLS = [
    {"name": "get_customer", "description": "Get customer account by ID",
     "input_schema": {"type": "object", "properties": {"customer_id": {"type": "string"}}, "required": ["customer_id"]}},
    {"name": "process_refund", "description": "Process a refund (amounts ≤ $500 only)",
     "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}, "amount": {"type": "number"}, "reason": {"type": "string"}}, "required": ["order_id", "amount", "reason"]}},
    {"name": "escalate_to_human", "description": "Escalate to human agent with reason",
     "input_schema": {"type": "object", "properties": {"reason": {"type": "string"}, "urgency": {"type": "string", "enum": ["low", "medium", "high"]}}, "required": ["reason", "urgency"]}}
]


def run_escalation_test(customer_message: str, scenario_label: str) -> str:
    """Test escalation behavior for different message types."""
    messages = [{"role": "user", "content": customer_message}]
    tool_calls_made = []

    print(f"\n[{scenario_label}]")
    print(f"Customer: {customer_message}")

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=512,
            system=ESCALATION_SYSTEM,
            tools=ESCALATION_TOOLS,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            text = next((b.text for b in response.content if hasattr(b, "text")), "")
            print(f"Agent: {text[:200]}")
            print(f"Tool calls: {tool_calls_made}")
            return text

        elif response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_calls_made.append(block.name)
                    print(f"  → Called: {block.name}({json.dumps(block.input)[:80]})")
                    # Mock results
                    if block.name == "get_customer":
                        result = {"customer_id": "C001", "name": "Jennifer", "status": "active"}
                    elif block.name == "process_refund":
                        result = {"success": True, "refund_id": "REF-9999", "days": 3}
                    elif block.name == "escalate_to_human":
                        result = {"ticket_id": "ESC-1111", "queue": "tier2", "wait": "2-4 hours"}
                    else:
                        result = {"error": "unknown"}
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)})
            messages.append({"role": "user", "content": results})


# Test scenarios — verify correct escalation behavior
test_scenarios = [
    (
        "I've been charged twice and I want my money back.",
        "Should RESOLVE — routine duplicate charge, no explicit escalation request"
    ),
    (
        "I don't care about automated solutions, I want to speak with a real person right now.",
        "Should ESCALATE IMMEDIATELY — explicit human request"
    ),
    (
        "This is outrageous! I've been waiting three weeks! Fix this NOW!",
        "Should OFFER TO RESOLVE — frustration but no explicit human request"
    ),
    (
        "Your competitor is selling the same item for $200 less. I want you to match their price.",
        "Should ESCALATE — policy gap (competitor price matching not in policy)"
    ),
]

for message, expected in test_scenarios:
    print(f"\nExpected: {expected}")
    run_escalation_test(message, "TEST")
    print()
```

---

## Reflection Questions

```python
"""
REFLECTION:

1. In the lossy summarization test, which specific values were lost or approximated?
   What is the business impact of losing a complaint reference number like CMP-2024-7823?
   Answer:

2. In the case facts test, were all precision values preserved? If any were still lost,
   what would you add to the facts block to capture them?
   Answer:

3. For the frustrated customer who didn't explicitly request a human:
   a) What did the agent do?
   b) Is this the correct behavior? Why?
   c) What should the agent do if the customer then says "no, I really just want a human"?
   Answer:

4. For the competitor price match request:
   Why does "policy gap" trigger escalation even though the agent could just say no?
   Answer:

5. Compare the tool calls made for "duplicate charge" vs "speak to a real person."
   For the human request, did the agent attempt any resolution before escalating?
   Is this correct?
   Answer:
"""
```

---

## Completion Criteria

✅ Lossy summarization demonstrates loss of specific values ($189.99, CMP-2024-7823, etc.)
✅ Case facts pattern preserves all precision values through the conversation
✅ Explicit human requests trigger immediate escalation (no resolution attempt first)
✅ Frustrated customers get resolution offers first; escalation if they insist
✅ Policy gaps trigger escalation correctly
✅ All reflection questions answered

---

*You have now completed all core labs. Proceed to practice questions for each domain.*
