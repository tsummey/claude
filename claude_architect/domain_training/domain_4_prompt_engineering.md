# Domain 4: Prompt Engineering & Structured Output
### CCAF Exam Weight: 20%

---

## Overview

This domain separates architects who understand how Claude actually works from those
who treat it as a magic box. Prompt engineering at the CCAF level is not about writing
clever instructions — it is about designing systems that produce reliable, consistent,
verifiable output at production scale.

The exam tests: structured output enforcement, few-shot prompting for consistency,
validation-retry loops, batch processing decisions, and multi-pass review architecture.

**Scenarios this domain covers:**
- Scenario 5: Claude Code for CI/CD
- Scenario 6: Structured Data Extraction

---

## Task Statement 4.1 — Explicit Criteria to Reduce False Positives

### The False Positive Problem

In any review or classification system, vague instructions produce inconsistent results.
"Be thorough" means different things on different runs. "Only report high-confidence
findings" is circular — the model's confidence is not calibrated to your standards.

The fix is to specify exactly what to report and exactly what to skip.

### Vague vs. Explicit Criteria

**Vague (produces inconsistent results):**
```
"Review this code for issues. Be conservative and only flag things you're confident about."
```

**Explicit (produces consistent results):**
```
"Review this code and report ONLY the following:

REPORT:
- SQL injection vulnerabilities (user input concatenated into queries without parameterization)
- Hardcoded credentials (API keys, passwords, tokens in source code)
- Missing authentication on endpoints that modify data
- Uncaught exceptions in payment processing paths

DO NOT REPORT:
- Naming convention preferences
- Code style or formatting issues
- Minor refactoring opportunities
- Comments that could be more descriptive
- Performance micro-optimizations in non-critical paths

For each finding: file, line number, vulnerability type, specific code that's problematic,
and a concrete fix."
```

### Why "Only Report High-Confidence Findings" Fails

This instruction is a trap. The model reports what it finds — confidence calibration
is not reliable across runs. The same code may get flagged in one run and not another.

Instead, specify categories:
```
"ALWAYS report: SQL injection, hardcoded secrets, auth bypass
NEVER report: style, naming, minor refactors
SOMETIMES report: potential null pointer exceptions — only when the code path
is reachable from user input"
```

### Managing Trust Through False Positive Rates

High false positives in one category undermine trust in ALL categories.
If developers learn to dismiss security alerts because 70% are false positives,
they'll miss the 30% that are real.

**Tactical fix:** Temporarily disable the high-FP category while improving its prompt.
```
# Week 1: Disable "complexity warnings" (too many FP) while you fix the criteria
# Week 2: Re-enable with more precise criteria
# Developers' trust in the other categories is preserved during the fix
```

---

## Task Statement 4.2 — Few-Shot Prompting

### When to Use Few-Shot Examples

Use few-shot when:
- Detailed prose instructions still produce inconsistent output format
- The task involves ambiguous cases you need to handle a specific way
- You need the model to generalize judgment to patterns you haven't explicitly specified
- Extraction tasks with varied document structures

### Structure of Effective Few-Shot Examples

Each example should show:
1. The input
2. The correct output
3. (For ambiguous cases) Why this was the right choice

```python
FEW_SHOT_SYSTEM = """You are a code review assistant. For each issue found, output a JSON
object with: file, line, severity, category, description, suggested_fix.

Here are examples of correct outputs:

EXAMPLE 1 — SQL Injection (should report):
Input code: `query = "SELECT * FROM users WHERE id = " + user_id`
Output: {
  "file": "user_service.py",
  "line": 47,
  "severity": "CRITICAL",
  "category": "sql_injection",
  "description": "String concatenation used to build SQL query with user input",
  "suggested_fix": "Use parameterized query: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))"
}

EXAMPLE 2 — Local Variable Pattern (should NOT report):
Input code: `query = "SELECT * FROM config WHERE key = " + config_key`
Context: config_key is a validated enum from an internal config file, not user input
Output: null  (not a vulnerability — input is not user-controlled)

EXAMPLE 3 — Ambiguous case (show reasoning):
Input code: `query = "SELECT * FROM products WHERE category = " + category`
Context: category comes from a request parameter
Output: {
  "file": "product_service.py",
  "line": 23,
  "severity": "HIGH",
  "category": "sql_injection",
  "description": "Request parameter concatenated into SQL query",
  "suggested_fix": "Use parameterized query"
}
Reasoning: Even though 'category' sounds like it might be validated, request parameters
are user-controlled and must be treated as untrusted input."""
```

### Few-Shot for Format Consistency

When output format is inconsistent (some responses include all fields, others omit some):

```python
# Before few-shot: Claude sometimes includes "suggested_fix", sometimes omits it
# After few-shot with 3 examples all showing "suggested_fix": consistent output

# The few-shot examples teach the format implicitly through demonstration
# rather than relying on Claude to remember a multi-field spec
```

### Few-Shot for Extraction Variety

Document structures vary. Few-shot examples teach the model how to handle each variant:

```python
EXTRACTION_EXAMPLES = """
EXAMPLE 1 — Structured invoice:
Document: "Invoice #1234 | Date: 2024-01-15 | Amount: $1,250.00 | Vendor: Acme Corp"
Output: {"invoice_number": "1234", "date": "2024-01-15", "amount": 1250.00, "vendor": "Acme Corp"}

EXAMPLE 2 — Narrative description:
Document: "We received a bill from Acme Corp last Tuesday for twelve hundred fifty dollars.
           Their reference number is INV-1234."
Output: {"invoice_number": "INV-1234", "date": null, "amount": 1250.00, "vendor": "Acme Corp"}
Note: date is null because "last Tuesday" is relative and cannot be resolved without context.

EXAMPLE 3 — Missing fields:
Document: "Acme Corp billed us $1,250 for consulting services."
Output: {"invoice_number": null, "date": null, "amount": 1250.00, "vendor": "Acme Corp"}
Note: Return null for absent fields — never fabricate values."""
```

---

## Task Statement 4.3 — Structured Output via Tool Use and JSON Schemas

### Why tool_use for Structured Output

Three approaches exist. Know their tradeoffs:

| Approach | Reliability | Notes |
|---|---|---|
| Ask Claude to "respond in JSON" | Low | Claude may add prose, break format |
| Instruct + system prompt for JSON | Medium | Better but still prone to syntax errors |
| `tool_use` with JSON schema | High | Eliminates JSON syntax errors completely |

The `tool_use` approach works because:
- Claude must populate the tool's input schema
- The schema is validated by the API
- JSON syntax errors cannot occur — the API enforces the schema

### Implementing tool_use for Extraction

```python
import anthropic
import json

client = anthropic.Anthropic()

# Define an extraction "tool" — we're not actually calling a function,
# we're using tool_use as a structured output mechanism
EXTRACTION_TOOL = {
    "name": "extract_invoice_data",
    "description": "Extract structured invoice data from the document",
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_number": {
                "type": ["string", "null"],
                "description": "Invoice or reference number. Null if not found."
            },
            "invoice_date": {
                "type": ["string", "null"],
                "description": "Invoice date in ISO 8601 format (YYYY-MM-DD). Null if not determinable."
            },
            "amount_usd": {
                "type": ["number", "null"],
                "description": "Total amount in USD as a number. Null if not found."
            },
            "vendor_name": {
                "type": ["string", "null"],
                "description": "Vendor or supplier company name. Null if not found."
            },
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "amount": {"type": "number"}
                    },
                    "required": ["description", "amount"]
                },
                "description": "Individual line items. Empty array if none found."
            },
            "payment_terms": {
                "type": ["string", "null"],
                "description": "Payment terms (e.g., 'Net 30'). Null if not specified."
            },
            "extraction_notes": {
                "type": "string",
                "description": "Any ambiguities, conflicts, or uncertainty in the extraction"
            }
        },
        "required": ["invoice_number", "invoice_date", "amount_usd", "vendor_name",
                     "line_items", "extraction_notes"]
    }
}

def extract_invoice(document_text: str) -> dict:
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        tools=[EXTRACTION_TOOL],
        # FORCE the specific tool — don't use "auto" (Claude might respond with text)
        tool_choice={"type": "tool", "name": "extract_invoice_data"},
        messages=[{
            "role": "user",
            "content": f"Extract all invoice data from this document:\n\n{document_text}"
        }]
    )

    # Extract the tool call result
    for block in response.content:
        if block.type == "tool_use" and block.name == "extract_invoice_data":
            return block.input  # Already a parsed dict — schema-compliant

    raise ValueError("Expected tool_use response but got none")
```

### The tool_choice Decision

```python
# "auto" — Claude may or may not call a tool
# Use when: optional enrichment, conversational context
tool_choice={"type": "auto"}

# "any" — Claude MUST call a tool (any of the available ones)
# Use when: multiple extraction schemas, document type unknown
tool_choice={"type": "any"}

# Forced — Claude MUST call THIS specific tool
# Use when: required first step (extract_metadata before enrichment)
tool_choice={"type": "tool", "name": "extract_invoice_data"}
```

### Nullable Fields — Prevent Hallucination

Fields that might not exist in the source document MUST be nullable.
If a required field has no source data, Claude will fabricate a value to satisfy the schema.

```python
# WRONG: Non-nullable field forces fabrication
"invoice_date": {"type": "string"}  # Claude WILL make up a date if none exists

# RIGHT: Nullable field allows honest null return
"invoice_date": {"type": ["string", "null"]}  # Claude returns null when not found
```

### Schema Design Patterns

**Enum with "other" + detail:**
```python
"expense_category": {
    "type": "string",
    "enum": ["travel", "software", "hardware", "consulting", "utilities", "other"]
},
"expense_category_detail": {
    "type": ["string", "null"],
    "description": "Required when expense_category is 'other'. Describe the category."
}
```

**Confidence field:**
```python
"extraction_confidence": {
    "type": "string",
    "enum": ["high", "medium", "low"],
    "description": "high: clear source text; medium: inferred; low: ambiguous or conflicting"
}
```

---

## Task Statement 4.4 — Validation, Retry, and Feedback Loops

### Retry with Error Feedback

When extraction fails validation, don't just retry blindly. Include the specific error:

```python
def extract_with_retry(document: str, max_retries: int = 3) -> dict:
    extraction = extract_invoice(document)

    for attempt in range(max_retries):
        # Validate the extraction
        errors = validate_extraction(extraction)

        if not errors:
            return extraction  # Valid — done

        if attempt == max_retries - 1:
            break  # Max retries reached

        # Retry with specific error feedback
        extraction = extract_invoice_with_feedback(
            document=document,
            prior_extraction=extraction,
            validation_errors=errors
        )

    return extraction  # Return best attempt even if imperfect


def extract_invoice_with_feedback(document: str, prior_extraction: dict,
                                   validation_errors: list) -> dict:
    """Retry extraction with specific error feedback."""
    error_summary = "\n".join([f"- {e}" for e in validation_errors])

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "tool", "name": "extract_invoice_data"},
        messages=[
            {
                "role": "user",
                "content": f"Extract invoice data from this document:\n\n{document}"
            },
            {
                "role": "assistant",
                "content": [{"type": "tool_use", "id": "tu_1",
                             "name": "extract_invoice_data", "input": prior_extraction}]
            },
            {
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": "tu_1",
                             "content": "Extraction has validation errors"}]
            },
            {
                "role": "user",
                "content": f"The previous extraction had these validation errors:\n{error_summary}\n\n"
                          f"Please re-extract the data from the original document, "
                          f"fixing these specific issues."
            }
        ]
    )

    for block in response.content:
        if block.type == "tool_use":
            return block.input

    return prior_extraction


def validate_extraction(extraction: dict) -> list:
    """Semantic validation — catches errors tool_use schema cannot catch."""
    errors = []

    # Semantic validation: line items should sum to total
    if extraction.get("line_items") and extraction.get("amount_usd"):
        line_total = sum(item["amount"] for item in extraction["line_items"])
        stated_total = extraction["amount_usd"]
        if abs(line_total - stated_total) > 0.01:  # Allow for rounding
            errors.append(
                f"Line items sum to ${line_total:.2f} but stated total is ${stated_total:.2f}"
            )

    # Date format validation
    if extraction.get("invoice_date"):
        try:
            from datetime import datetime
            datetime.strptime(extraction["invoice_date"], "%Y-%m-%d")
        except ValueError:
            errors.append(
                f"invoice_date '{extraction['invoice_date']}' is not in YYYY-MM-DD format"
            )

    return errors
```

### When Retries Will NOT Help

Retries only fix format errors and structural mistakes. They cannot fix:

```python
# This retry WILL work: format error
# Error: "date '01/15/2024' is not in YYYY-MM-DD format"
# Retry: Claude reformats to "2024-01-15" ✓

# This retry will NOT work: missing information
# Error: "invoice_number is null but required"
# Retry: There is no invoice number in the document — retrying gets the same null
# → Don't retry; route to human review instead

def should_retry(error: str, document: str) -> bool:
    """Determine if a validation error is fixable by retry."""
    format_errors = ["not in ISO format", "should be a number", "invalid date format"]
    missing_info = ["is null but required", "not found in document", "absent from source"]

    if any(e in error for e in format_errors):
        return True  # Format issues → retry will fix

    if any(e in error for e in missing_info):
        return False  # Missing info → retry won't help → human review

    return True  # Default: try once more
```

### Feedback Loops for Quality Tracking

Add a `detected_pattern` field to extraction outputs to track what code patterns
trigger false positives:

```python
{
    "finding": "potential SQL injection",
    "file": "query_builder.py",
    "line": 45,
    "severity": "HIGH",
    "detected_pattern": "string_concatenation_in_query",  # trackable field
    "dismissed": False
}

# When developers dismiss findings, analyze by detected_pattern:
# "string_concatenation_in_query" has 73% dismissal rate
# → This pattern's detection criteria are too broad → refine the prompt
```

---

## Task Statement 4.5 — Batch Processing

### The Message Batches API

| Property | Value |
|---|---|
| Cost savings | 50% vs. standard API |
| Processing window | Up to 24 hours |
| Latency SLA | None — no guaranteed completion time |
| Multi-turn tool calling | NOT supported within a single batch request |
| Request correlation | `custom_id` field on each request |

### Matching Workflow to API

```
Blocking pre-merge check (developers waiting for result)
→ Synchronous API (real-time, guaranteed latency)

Overnight technical debt report (reviewed next morning)
→ Batch API (50% savings, 24hr window acceptable)

Weekly security audit (reviewed on Monday)
→ Batch API

Nightly test generation (results needed before stand-up)
→ Batch API (24hr window >> 8hr night = fine)

Real-time customer support response
→ Synchronous API (cannot make customer wait 24 hours)
```

### Implementing Batch Processing

```python
import anthropic
import json

client = anthropic.Anthropic()

def submit_batch(documents: list[dict]) -> str:
    """Submit a batch of documents for extraction."""
    requests = []

    for doc in documents:
        requests.append({
            "custom_id": doc["id"],  # For correlating results to inputs
            "params": {
                "model": "claude-opus-4-5",
                "max_tokens": 1024,
                "tools": [EXTRACTION_TOOL],
                "tool_choice": {"type": "tool", "name": "extract_invoice_data"},
                "messages": [{
                    "role": "user",
                    "content": f"Extract invoice data:\n\n{doc['content']}"
                }]
            }
        })

    batch = client.beta.messages.batches.create(requests=requests)
    return batch.id


def poll_batch(batch_id: str) -> dict:
    """Poll batch until complete. Returns results indexed by custom_id."""
    import time

    while True:
        batch = client.beta.messages.batches.retrieve(batch_id)

        if batch.processing_status == "ended":
            break

        print(f"Batch status: {batch.processing_status} | "
              f"Succeeded: {batch.request_counts.succeeded} | "
              f"Errored: {batch.request_counts.errored}")
        time.sleep(60)  # Check every minute

    # Collect results
    results = {}
    failures = []

    for result in client.beta.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            response = result.result.message
            for block in response.content:
                if block.type == "tool_use":
                    results[result.custom_id] = {
                        "status": "success",
                        "extraction": block.input
                    }
        else:
            failures.append({
                "custom_id": result.custom_id,
                "error": result.result.error
            })

    return {"results": results, "failures": failures}


def handle_batch_failures(failures: list, original_docs: list) -> str:
    """Resubmit failed documents with appropriate modifications."""
    failed_ids = {f["custom_id"] for f in failures}
    failed_docs = [d for d in original_docs if d["id"] in failed_ids]

    # For documents that may have exceeded context: chunk them
    chunked_docs = []
    for doc in failed_docs:
        if len(doc["content"]) > 50000:  # Likely too large
            chunks = chunk_document(doc)
            chunked_docs.extend(chunks)
        else:
            chunked_docs.append(doc)

    return submit_batch(chunked_docs)


def calculate_sla_submission_frequency(sla_hours: int, batch_max_hours: int = 24) -> int:
    """
    Calculate how often to submit batches to guarantee SLA.
    
    Example: 30-hour SLA with 24-hour batch processing
    → Must submit every 30 - 24 = 6 hours
    → Each batch has 24 hours to complete, but you have a 30-hour deadline
    → Submitting every 6 hours guarantees any batch completes within SLA
    """
    return sla_hours - batch_max_hours
```

---

## Task Statement 4.6 — Multi-Instance and Multi-Pass Review

### Self-Review Limitations

When Claude reviews code it just wrote, it retains the reasoning that led to those
decisions. It is less likely to question choices it just made — the same cognitive
bias humans have when proofreading their own work.

**The fix:** Use a second, independent Claude instance with no prior context.

```python
def review_with_independent_instance(generated_code: str, spec: str) -> dict:
    """
    Review using a fresh Claude instance that has no knowledge of how the code was generated.
    This is more effective than asking the generating instance to self-review.
    """
    # New client instance — or just a new conversation with no prior messages
    reviewer = anthropic.Anthropic()

    response = reviewer.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        # No system context about how the code was generated
        messages=[{
            "role": "user",
            "content": f"""Review this code against the specification.
            
Specification:
{spec}

Code to review:
{generated_code}

Report: bugs, missing requirements, edge cases not handled, security issues.
Do not report style preferences."""
        }]
    )

    return {"review": response.content[0].text}
```

### Multi-Pass Review Architecture

```python
def multi_pass_review(files: dict[str, str]) -> dict:
    """
    Pass 1: Per-file local analysis (focused, deep)
    Pass 2: Cross-file integration analysis (data flow, interfaces, architecture)
    """
    # Pass 1: Analyze each file individually
    # Each call sees ONLY one file → no attention dilution
    per_file_findings = {}
    for filename, content in files.items():
        findings = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": f"""Analyze {filename} for:
- Logic bugs and edge cases
- Error handling gaps
- Security vulnerabilities within this file
- Performance issues within this file

Do NOT consider cross-file dependencies at this stage.

Code:
{content}"""
            }]
        )
        per_file_findings[filename] = findings.content[0].text

    # Pass 2: Cross-file integration pass
    # This call sees summaries from ALL files + their relationships
    integration_findings = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"""Given these per-file analyses:

{format_per_file_findings(per_file_findings)}

Identify cross-file issues only:
- Data flow bugs (data transformed incorrectly between components)
- Interface mismatches (caller passes X, callee expects Y)
- Missing error propagation across module boundaries
- Architectural violations (dependency direction, coupling issues)
- Race conditions that span multiple files

Do NOT repeat issues already identified in the per-file analyses."""
        }]
    )

    return {
        "per_file": per_file_findings,
        "integration": integration_findings.content[0].text
    }
```

---

## Key Concepts Summary — Domain 4

| Concept | What to Know |
|---|---|
| Explicit criteria | Specify WHAT to report and NOT report — don't rely on "confidence" |
| Few-shot examples | Most effective for format consistency and ambiguous case handling |
| tool_use for structured output | Eliminates JSON syntax errors; doesn't prevent semantic errors |
| Nullable fields | Required for any field that may be absent in source — prevents fabrication |
| tool_choice | auto / any / forced — use forced when specific tool must run first |
| Validation-retry | Include specific errors in retry prompt; retries fix format, not missing info |
| Batch API | 50% savings, 24hr window, no SLA, no multi-turn tool calling |
| Batch vs. sync | Blocking workflows → sync; latency-tolerant → batch |
| custom_id | Correlates batch requests to responses; use for failure resubmission |
| Self-review bias | Independent instance reviews better than self-review |
| Multi-pass review | Per-file passes (depth) + integration pass (cross-file issues) |

---

## What the Exam Will Test You On

- *"Your extraction pipeline returns empty strings for missing fields. Why is this a problem?"*
  → Cannot distinguish "field not in document" from "field is empty string" → use null

- *"Claude is told to 'be conservative' but still reports too many false positives. Fix?"*
  → Replace vague instruction with explicit REPORT/DO NOT REPORT category lists

- *"You need guaranteed structured output. Which is most reliable — JSON instructions, system prompt, or tool_use?"*
  → tool_use with JSON schema is most reliable (eliminates syntax errors)

- *"Your batch job processes 10,000 invoices overnight. One batch has 47 failures. What do you do?"*
  → Use custom_id to identify failures, analyze failure reason, resubmit with fixes (chunk if context exceeded)

- *"Why is reviewing code with the same Claude session that generated it less effective?"*
  → Session retains reasoning context; independent instance reviews without that bias
