# Domain 5: Context Management & Reliability
### CCAF Exam Weight: 15%

---

## Overview

Context is Claude's working memory. Everything it knows in a session lives in the context
window — and that window is finite. This domain tests whether you can design systems that
preserve critical information across long interactions, escalate correctly, propagate
errors intelligently, and build human review workflows that actually scale.

The exam presents systems that are losing information, escalating incorrectly, or silently
failing — and asks you to diagnose and fix them.

**Scenarios this domain covers:**
- Scenario 1: Customer Support Resolution Agent
- Scenario 3: Multi-Agent Research System
- Scenario 6: Structured Data Extraction

---

## Task Statement 5.1 — Manage Conversation Context

### How Context Gets Destroyed

Three common ways critical information disappears from long conversations:

**1. Progressive summarization losing precision**
```
Original: "Customer paid $1,247.83 on March 15th for order #ORD-98234"
After summarization: "Customer had a payment issue last month"
→ Amount, date, and order ID are gone — cannot be recovered
```

**2. The "lost in the middle" effect**
Models reliably process information at the beginning and end of long contexts.
Information in the middle gets less attention. In a 40-source research report,
sources 15-25 may be underrepresented in the synthesis.

**3. Tool result accumulation**
Every tool call appends a result to the context. An order lookup that returns
40 fields (most irrelevant) consumes significant tokens for every subsequent call.

### The Case Facts Pattern

Extract transactional facts into a persistent block outside the summarized history:

```python
class CaseFacts:
    """Critical facts that must not be lost to summarization."""
    def __init__(self):
        self.customer_id: str = None
        self.customer_name: str = None
        self.order_ids: list = []
        self.amounts: dict = {}      # {order_id: amount}
        self.issue_types: list = []
        self.dates: dict = {}        # {event: date}
        self.resolution_status: str = "open"

    def to_context_block(self) -> str:
        """Format as a structured block included at the top of every prompt."""
        return f"""
=== CASE FACTS (DO NOT LOSE THESE) ===
Customer ID: {self.customer_id}
Customer: {self.customer_name}
Orders: {', '.join(self.order_ids)}
Amounts: {json.dumps(self.amounts)}
Issues: {', '.join(self.issue_types)}
Status: {self.resolution_status}
=====================================
"""

def build_message_with_facts(facts: CaseFacts, conversation_history: list,
                              new_message: str) -> list:
    """
    Build a message that preserves facts outside summarized history.
    Facts are at the BEGINNING (high attention position).
    """
    system_with_facts = f"{BASE_SYSTEM_PROMPT}\n\n{facts.to_context_block()}"

    return {
        "system": system_with_facts,
        "messages": conversation_history + [
            {"role": "user", "content": new_message}
        ]
    }
```

### Trimming Verbose Tool Outputs

Before appending a tool result to the conversation, trim it to relevant fields:

```python
def trim_order_result(raw_order: dict, context: str = "refund") -> dict:
    """
    Return only the fields relevant to the current context.
    A 40-field order record reduced to 8 relevant fields saves significant context.
    """
    if context == "refund":
        return {
            "order_id": raw_order.get("order_id"),
            "amount": raw_order.get("total_amount"),
            "status": raw_order.get("fulfillment_status"),
            "items": raw_order.get("line_items", []),
            "purchase_date": raw_order.get("created_at"),
            "return_window_days": raw_order.get("return_policy_days"),
            "return_eligible": raw_order.get("return_eligible"),
            "refund_amount_possible": raw_order.get("refundable_amount")
        }
        # Excluded: warehouse_id, shipping_carrier_id, packing_station_id,
        # inventory_allocation_id, ... (32 other irrelevant fields)
```

### Position-Aware Input Organization

For multi-source research synthesis, organize inputs to mitigate "lost in the middle":

```python
def build_synthesis_prompt(findings: list) -> str:
    """
    High-attention positions: beginning and end.
    Key summaries at beginning, detailed results in middle, quality criteria at end.
    """
    key_summaries = extract_key_summaries(findings)
    detailed_results = format_detailed_findings(findings)
    quality_criteria = get_synthesis_criteria()

    return f"""
# KEY FINDINGS SUMMARY (read this first)
{key_summaries}

---

# DETAILED SOURCE FINDINGS
{detailed_results}

---

# SYNTHESIS REQUIREMENTS (follow these carefully)
{quality_criteria}
"""
    # Summary at start: high attention → sets context correctly
    # Details in middle: lower attention → fine for supporting information
    # Requirements at end: high attention → Claude follows instructions carefully
```

---

## Task Statement 5.2 — Escalation and Ambiguity Resolution

### When to Escalate — The Correct Triggers

```
ALWAYS escalate immediately:
├── Customer explicitly requests a human agent
│   (even if you could resolve it — honor the request)
├── Policy is silent or ambiguous on this specific request
│   (you lack authority to decide unilaterally)
└── You cannot make meaningful progress after genuine attempts

CONSIDER escalating:
├── High-value transaction with unusual circumstances
└── Customer has made the same complaint 3+ times

DO NOT escalate based on:
├── Customer sentiment / frustration level alone
│   (frustrated ≠ complex; many simple issues cause frustration)
├── Your own confidence score
│   (self-reported confidence is poorly calibrated)
└── General "complexity" — many complex-seeming requests are routine
```

### Explicit Escalation Criteria with Few-Shot Examples

```python
ESCALATION_SYSTEM = """You are a customer support agent. Resolve issues when you can.
Escalate when you must.

ESCALATION TRIGGERS (always escalate for these):
1. Customer explicitly asks for a human: "I want to speak to a person" → escalate immediately
2. Policy gap: request falls outside documented policy (e.g., competitor price matching
   when policy only covers own-site price adjustments) → escalate
3. No progress after 3 tool call attempts → escalate

DO NOT escalate for:
- Customer frustration alone (frustrated customers still deserve automated resolution
  when the issue is straightforward)
- High-dollar amounts per se (high-dollar refunds within policy = process normally)

EXAMPLES:

Customer: "Your system charged me twice. I want my money back."
→ RESOLVE: Straightforward duplicate charge. lookup_order → process_refund.

Customer: "I've been a customer for 10 years and this is unacceptable. I want to talk to someone."
→ ESCALATE IMMEDIATELY: Customer explicitly requested human. Honor it without attempting resolution first.

Customer: "Your competitor is selling this for $50 less. Match the price."
→ ESCALATE: Policy covers own-site price adjustments, not competitor matching. Policy gap.

Customer: "I don't know my order number but I want a refund for something I bought."
→ ASK FOR CLARIFIERS: Request order number or email to look up the order.
  Do not guess which order they mean."""
```

### Handling Ambiguous Customer Matches

When `get_customer` returns multiple matches (common names), do not guess:

```python
def handle_multiple_customer_matches(matches: list, original_query: str) -> str:
    """
    When multiple customers match, ask for additional identifiers.
    Never select based on heuristics (most recent, highest-value, etc.)
    """
    if len(matches) == 1:
        return f"Found customer: {matches[0]['customer_id']}"

    # Multiple matches — request disambiguation
    match_summary = "\n".join([
        f"- Account ending in {m['email'][-8:]} | Created: {m['created_date']}"
        for m in matches
    ])

    return f"""Multiple accounts match '{original_query}'. 
To protect account security, please provide additional verification:
- Email address associated with the account, OR
- Order number from a recent purchase, OR  
- Last 4 digits of payment method on file

Matching accounts (partial info for privacy):
{match_summary}"""
```

---

## Task Statement 5.3 — Error Propagation Across Multi-Agent Systems

### The Structured Error Contract

Every error a subagent returns must enable the coordinator to make a decision.
A coordinator that receives `{"error": "search failed"}` has nothing to work with.

```python
def create_structured_error(
    error_type: str,
    message: str,
    attempted: str,
    partial_results: list = None,
    alternatives: list = None,
    is_retryable: bool = True
) -> dict:
    """
    Standard error structure for all subagents.
    Every field serves a purpose for coordinator recovery.
    """
    return {
        "isError": True,
        "errorType": error_type,          # transient/validation/permission/business
        "message": message,               # Human-readable description
        "attemptedAction": attempted,     # What was tried
        "isRetryable": is_retryable,      # Should coordinator retry?
        "partialResults": partial_results or [],  # Any results before failure
        "suggestedAlternatives": alternatives or [],  # Other approaches to try
        "timestamp": datetime.utcnow().isoformat()
    }

# Example: Search timeout after retries
create_structured_error(
    error_type="transient",
    message="Web search API timed out after 3 retry attempts",
    attempted="search query: 'remote work real estate impact 2024'",
    partial_results=[],  # Nothing retrieved
    alternatives=[
        "Try a more specific query",
        "Search for individual subtopics separately",
        "Use document analysis agent with pre-loaded sources"
    ],
    is_retryable=True  # Coordinator can try again or use alternatives
)
```

### Coverage Annotations in Synthesis

When a subagent fails, the synthesis output should mark which areas lack coverage:

```python
def build_synthesis_with_coverage(findings: dict, errors: dict) -> dict:
    """
    Synthesis output annotated with coverage quality.
    Coordinators and end users know what's well-supported vs. uncertain.
    """
    coverage = {}
    for topic in findings.keys():
        if topic in errors:
            coverage[topic] = {
                "status": "incomplete",
                "reason": errors[topic]["message"],
                "confidence": "low"
            }
        elif len(findings[topic]) >= 3:
            coverage[topic] = {"status": "well-covered", "confidence": "high"}
        else:
            coverage[topic] = {"status": "limited-sources", "confidence": "medium"}

    return {
        "synthesis": generate_synthesis(findings),
        "coverage_map": coverage,
        "well_supported_topics": [t for t, c in coverage.items()
                                   if c["status"] == "well-covered"],
        "coverage_gaps": [t for t, c in coverage.items()
                          if c["status"] == "incomplete"],
        "note": "Topics in coverage_gaps had source failures. Treat claims in these areas with caution."
    }
```

---

## Task Statement 5.4 — Context in Large Codebase Exploration

### Scratchpad Files

When context fills up during extended exploration, scratchpad files persist findings
across context boundaries:

```python
SCRATCHPAD_PATH = ".claude/investigation_scratchpad.md"

def update_scratchpad(finding_category: str, findings: str):
    """Persist findings to file — survives context window limits."""
    with open(SCRATCHPAD_PATH, "a") as f:
        f.write(f"\n## {finding_category}\n{findings}\n")

def read_scratchpad() -> str:
    """Load all findings from previous exploration phases."""
    try:
        with open(SCRATCHPAD_PATH) as f:
            return f.read()
    except FileNotFoundError:
        return ""
```

In practice, instruct Claude to maintain this file:
```
"As you explore the codebase, maintain a scratchpad file at .claude/scratchpad.md.
After each investigation phase, summarize key findings there. Before starting
each new phase, read the scratchpad to refresh your memory of prior findings."
```

### Crash Recovery with Manifests

For long multi-agent workflows that might fail partway through:

```python
MANIFEST_PATH = ".claude/agent_state_manifest.json"

def save_agent_state(agent_id: str, state: dict):
    """Each agent exports state to known location after completing its work."""
    try:
        with open(MANIFEST_PATH) as f:
            manifest = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        manifest = {}

    manifest[agent_id] = {
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat(),
        "output_location": state.get("output_path"),
        "summary": state.get("summary"),
        "key_findings": state.get("key_findings", [])
    }

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)


def resume_from_manifest() -> dict:
    """
    On resume after crash: load manifest, inject state into agent prompts.
    Agents that already completed don't need to re-run.
    """
    try:
        with open(MANIFEST_PATH) as f:
            manifest = json.load(f)
        return manifest
    except FileNotFoundError:
        return {}  # Fresh start
```

### The /compact Command

Use `/compact` during extended exploration sessions to reduce context usage when
verbose discovery output accumulates. Claude summarizes the conversation before
continuing, freeing context for more exploration.

**When to use /compact:**
- Context window is > 70% full during multi-phase exploration
- You've completed one phase and are starting another
- Verbose tool outputs are dominating the context

---

## Task Statement 5.5 — Human Review Workflows and Confidence Calibration

### The Aggregate Accuracy Trap

Overall 97% accuracy sounds good. But if accuracy breaks down by segment:
```
Invoices from Vendor A: 99.5% accuracy  ✓
Invoices from Vendor B: 81% accuracy    ✗ (not acceptable)
Invoices with line items: 94% accuracy  
Invoices without line items: 99% accuracy

Overall: 97% — masks the Vendor B problem entirely
```

**Always validate accuracy by document type AND field before automating.**

### Stratified Random Sampling

Don't audit only low-confidence extractions — you'll miss errors in extractions Claude
was incorrectly confident about.

```python
def build_review_queue(extractions: list, sample_config: dict) -> list:
    """
    Stratified sampling ensures every segment gets reviewed.
    """
    review_queue = []

    # All low-confidence extractions → human review
    review_queue.extend([
        e for e in extractions
        if e.get("extraction_confidence") == "low"
        or e.get("extraction_notes")  # Model flagged something
    ])

    # Random sample of HIGH-confidence extractions
    # (to catch errors Claude was incorrectly confident about)
    high_confidence = [e for e in extractions
                       if e.get("extraction_confidence") == "high"]
    sample_size = max(10, int(len(high_confidence) * sample_config.get("rate", 0.05)))
    import random
    review_queue.extend(random.sample(high_confidence, min(sample_size, len(high_confidence))))

    # All extractions from document types with historically high error rates
    high_risk_vendors = sample_config.get("high_risk_vendors", [])
    review_queue.extend([
        e for e in extractions
        if e.get("vendor_name") in high_risk_vendors
        and e not in review_queue
    ])

    return review_queue
```

### Field-Level Confidence

Schema-level confidence is too coarse. Field-level confidence lets you route review
attention precisely:

```python
EXTRACTION_TOOL_WITH_CONFIDENCE = {
    "name": "extract_invoice_data",
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_number": {"type": ["string", "null"]},
            "invoice_number_confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "high: explicitly labeled in document; medium: inferred from context; low: ambiguous"
            },
            "amount_usd": {"type": ["number", "null"]},
            "amount_usd_confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"]
            }
            # ... same pattern for each field
        }
    }
}

def route_for_review(extraction: dict, thresholds: dict) -> str:
    """Route extraction based on field-level confidence."""
    low_confidence_fields = [
        field for field in ["invoice_number", "amount_usd", "invoice_date", "vendor_name"]
        if extraction.get(f"{field}_confidence") == "low"
    ]

    if not low_confidence_fields:
        return "auto_process"
    elif len(low_confidence_fields) <= 1:
        return "spot_check"  # Human reviews just the flagged field
    else:
        return "full_review"  # Human reviews entire extraction
```

---

## Task Statement 5.6 — Information Provenance in Multi-Source Synthesis

### Claim-Source Mappings

Source attribution is lost when findings are summarized without preserving claim-source
mappings. The synthesis agent must receive explicit mappings, not summaries.

```python
# WRONG: Attribution lost in summarization
search_findings = "Remote work has caused urban office vacancies to rise"
# Which source? Publication date? Methodology? All lost.

# RIGHT: Structured claim-source mapping preserved
search_findings = [
    {
        "claim": "Office vacancy rates in major CBDs hit 22% in Q4 2023",
        "source_url": "https://realestate-journal.com/remote-work-exodus",
        "source_title": "Remote Work Exodus: Cities Losing Downtown Tenants",
        "publication_date": "2024-02-15",
        "confidence": "high",
        "excerpt": "office vacancy rates in major CBDs hit 22% in Q4 2023, highest since 2008"
    },
    {
        "claim": "San Francisco leads with 31% vacancy rate",
        "source_url": "https://realestate-journal.com/remote-work-exodus",
        "source_title": "Remote Work Exodus: Cities Losing Downtown Tenants",
        "publication_date": "2024-02-15",
        "confidence": "high",
        "excerpt": "San Francisco leads with 31% vacancy"
    }
]
```

### Handling Conflicting Statistics

When two credible sources report different numbers, do NOT pick one — annotate both:

```python
def handle_conflicting_data(claim_a: dict, claim_b: dict) -> dict:
    """
    When sources conflict, preserve both with attribution.
    Let the coordinator or human decide how to reconcile.
    """
    return {
        "claim_type": "conflicting_statistics",
        "conflict_detected": True,
        "value_a": {
            "value": claim_a["value"],
            "source": claim_a["source_url"],
            "date": claim_a["publication_date"],
            "methodology": claim_a.get("methodology")
        },
        "value_b": {
            "value": claim_b["value"],
            "source": claim_b["source_url"],
            "date": claim_b["publication_date"],
            "methodology": claim_b.get("methodology")
        },
        "possible_explanation": check_temporal_difference(claim_a, claim_b),
        "resolution": "human_review_required"
    }

def check_temporal_difference(claim_a: dict, claim_b: dict) -> str:
    """Check if the conflict might be explained by different time periods."""
    from datetime import datetime
    date_a = datetime.fromisoformat(claim_a["publication_date"])
    date_b = datetime.fromisoformat(claim_b["publication_date"])
    diff_months = abs((date_b - date_a).days / 30)

    if diff_months > 6:
        return f"Sources are {diff_months:.0f} months apart — values may reflect different time periods"
    return "Sources are contemporaneous — likely a genuine discrepancy"
```

### Temporal Data — Require Dates

Require publication or data collection dates in all structured outputs.
What looks like a conflict may be a trend:

```python
# Without dates: looks like a contradiction
# Source A: "Office vacancy 18%"
# Source B: "Office vacancy 22%"

# With dates: a clear trend
# Source A: "Office vacancy 18% [Q1 2023]"
# Source B: "Office vacancy 22% [Q4 2023]"
# → Vacancy increased 4 points over the year — not a conflict
```

---

## Key Concepts Summary — Domain 5

| Concept | What to Know |
|---|---|
| Case facts block | Extract transactional specifics outside summarized history |
| Progressive summarization risk | Precision values (amounts, dates, IDs) lost in summaries |
| Lost in the middle | Information in middle of long context gets less attention |
| Tool result trimming | Keep only relevant fields before appending to context |
| Position-aware prompts | Key info at start + end; details in middle |
| Escalation triggers | Explicit customer request; policy gap; inability to progress |
| Escalation anti-patterns | Sentiment-based, confidence-based |
| Multiple matches | Always ask for additional identifiers — never select by heuristic |
| Structured error propagation | failure_type, attempted, partial_results, alternatives, isRetryable |
| Coverage annotations | Mark which findings are well-supported vs. gap areas |
| Scratchpad files | Persist findings across context boundaries |
| Crash recovery | Agent state manifests loaded on resume |
| Aggregate accuracy trap | 97% overall may mask poor performance on specific segments |
| Stratified sampling | Sample high-confidence extractions too — catch miscalibrated confidence |
| Claim-source mappings | Must be preserved through synthesis; not summarized away |
| Conflicting statistics | Annotate both values with source; don't arbitrarily choose one |
| Temporal data | Always require publication dates to distinguish conflicts from trends |

---

## What the Exam Will Test You On

- *"After summarizing a long support conversation, the agent forgot the refund amount. Why?"*
  → Progressive summarization lost precision values; fix: case facts block outside summarized history

- *"Your multi-source report presents 22% vacancy rate when one source says 18% and another says 22%. How should it have handled this?"*
  → Both values preserved with source attribution; conflict annotated; reader decides

- *"Overall extraction accuracy is 97% but stakeholders aren't satisfied. What might they be seeing?"*
  → Accuracy by segment reveals poor performance on specific document types or fields

- *"A subagent returns `{results: []}` after a database timeout. Why is this dangerous?"*
  → Coordinator treats it as "no results found" (success) instead of "query failed" (error); cannot recover

- *"A customer says 'I've been charged twice, fix it' then says 'actually I just want to talk to someone.' What should the agent do?"*
  → Escalate immediately — explicit customer request for a human overrides resolution attempts
