# Lab D4-01: Structured Data Extraction Pipeline
### Domain 4 | Task Statements 4.1, 4.2, 4.3, 4.4 | Estimated Time: 60 minutes

---

## Objective

Build a complete structured data extraction pipeline for Scenario 6. You will implement
tool_use-based extraction with a proper JSON schema, add few-shot examples for document
variety, build a validation-retry loop, and demonstrate why nullable fields prevent
hallucination.

---

## Setup

Create: `C:\Users\tsummey\projects\claude\claude_architect\labs\lab_d4_01_work.py`

---

## Sample Documents (varied formats, a realistic test set)

```python
import anthropic
import json
from datetime import datetime

client = anthropic.Anthropic()

# Six sample documents with varying structure, completeness, and format
SAMPLE_DOCUMENTS = {
    "doc_001": """
    INVOICE
    Invoice Number: INV-2024-0892
    Date: January 15, 2024
    Due Date: February 15, 2024
    
    Bill To:
    Acme Corporation
    123 Business Ave, Suite 400
    
    From: TechSupplies LLC
    
    Services Rendered:
    - Cloud Infrastructure Setup: $2,500.00
    - Security Audit: $1,200.00
    - Training Sessions (8 hours): $800.00
    
    Subtotal: $4,500.00
    Tax (8.5%): $382.50
    TOTAL DUE: $4,882.50
    
    Payment Terms: Net 30
    """,

    "doc_002": """
    We got the bill from TechSupplies last Tuesday. They're asking for four thousand
    eight hundred eighty-two dollars and fifty cents for the infrastructure work
    they did in January. Their invoice reference is INV-2024-0892. Need to pay this
    by mid-February.
    """,  # Narrative — tests informal amount extraction

    "doc_003": """
    RECEIPT #RCT-5541
    2024-03-22
    
    TechSupplies LLC
    
    Item: Annual Software License
    Amount: $12,000.00
    
    No line items breakdown available.
    """,  # Minimal structure — some fields absent

    "doc_004": """
    From: billing@techsupplies.com
    Subject: Your invoice INV-2024-1103
    
    Hi,
    
    Please find attached your invoice for April services totaling $3,200.
    Payment is due within 30 days.
    
    Thanks,
    TechSupplies Billing Team
    """,  # Email format — no line items, informal amount

    "doc_005": """
    VENDOR STATEMENT
    TechSupplies LLC
    Statement Date: 2024-05-01
    
    Outstanding Invoices:
    INV-2024-0892: $4,882.50 (OVERDUE)
    INV-2024-1103: $3,200.00 (DUE 2024-05-15)
    
    Total Outstanding: $8,082.50
    """,  # Multi-invoice — tests handling of aggregate documents

    "doc_006": """
    consulting services provided March 2024
    paid already
    """,  # Minimal info — tests null handling
}
```

---

## Part 1: Naive Extraction — The Wrong Way First (10 minutes)

```python
def extract_naive(document: str) -> str:
    """Ask Claude to extract data with no schema — observe inconsistency."""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"Extract the invoice number, date, total amount, and vendor name from this document. Return as JSON.\n\n{document}"
        }]
    )
    return response.content[0].text


print("=== NAIVE EXTRACTION (no schema) ===")
for doc_id, doc in list(SAMPLE_DOCUMENTS.items())[:3]:
    print(f"\n{doc_id}:")
    result = extract_naive(doc)
    print(f"  Result: {result[:300]}")
    # Observe: inconsistent keys, different date formats, inconsistent null representation
```

---

## Part 2: Schema-Enforced Extraction with tool_use (20 minutes)

```python
INVOICE_EXTRACTION_TOOL = {
    "name": "extract_invoice_data",
    "description": (
        "Extract structured invoice or billing data from a document. "
        "Return null for fields that cannot be determined from the document — "
        "never fabricate or estimate missing values. "
        "For amounts, return the TOTAL due (not subtotals). "
        "For dates, use ISO 8601 format (YYYY-MM-DD)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_number": {
                "type": ["string", "null"],
                "description": "Invoice, receipt, or reference number. Null if not present."
            },
            "invoice_date": {
                "type": ["string", "null"],
                "description": "Invoice issue date in YYYY-MM-DD format. Null if not determinable."
            },
            "due_date": {
                "type": ["string", "null"],
                "description": "Payment due date in YYYY-MM-DD format. Null if not stated."
            },
            "vendor_name": {
                "type": ["string", "null"],
                "description": "Company or person issuing the invoice. Null if not identified."
            },
            "total_amount_usd": {
                "type": ["number", "null"],
                "description": "Total amount due in USD as a decimal number (e.g., 4882.50). Null if not determinable."
            },
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "amount_usd": {"type": "number"}
                    },
                    "required": ["description", "amount_usd"]
                },
                "description": "Individual line items if listed. Empty array if not itemized."
            },
            "payment_terms": {
                "type": ["string", "null"],
                "description": "Payment terms (e.g., 'Net 30', 'Due on receipt'). Null if not stated."
            },
            "document_type": {
                "type": "string",
                "enum": ["invoice", "receipt", "statement", "email", "other"],
                "description": "The type of billing document"
            },
            "extraction_confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "high: all key fields clearly stated; medium: some inference required; low: significant ambiguity"
            },
            "extraction_notes": {
                "type": ["string", "null"],
                "description": "Any ambiguities, conflicts, or assumptions made during extraction. Null if none."
            }
        },
        "required": ["invoice_number", "invoice_date", "vendor_name", "total_amount_usd",
                     "line_items", "document_type", "extraction_confidence", "extraction_notes"]
    }
}


# Few-shot examples to handle document variety
FEW_SHOT_SYSTEM = """You are a document data extraction specialist.
Extract invoice data using the extract_invoice_data tool.
Return null for any field not present in the document — never fabricate values.

EXAMPLES OF CORRECT BEHAVIOR:

Example 1 — Informal narrative amount:
"We owe them four thousand five hundred dollars for the consulting work"
→ total_amount_usd: 4500.00 (convert written numbers to digits)

Example 2 — Relative date (cannot resolve):
"Due last Tuesday"
→ due_date: null (relative dates without a reference point → null)

Example 3 — Missing invoice number:
"Please pay $500 for consulting services"
→ invoice_number: null (do not invent a number)

Example 4 — Multi-invoice statement:
"Total outstanding: $8,082.50 (INV-001: $4,000 + INV-002: $4,082.50)"
→ total_amount_usd: 8082.50 (use the stated total)
→ extraction_notes: "Document is a statement covering multiple invoices"

Example 5 — Line items don't sum to total (capture both):
"Item A: $100, Item B: $200, Total: $350"
→ line_items: [{description: "Item A", amount_usd: 100}, {description: "Item B", amount_usd: 200}]
→ total_amount_usd: 350.00
→ extraction_notes: "Line items sum to $300 but stated total is $350 — discrepancy present"
"""


def extract_with_schema(document: str, doc_id: str) -> dict:
    """Extract with schema enforcement and few-shot examples."""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=FEW_SHOT_SYSTEM,
        tools=[INVOICE_EXTRACTION_TOOL],
        tool_choice={"type": "tool", "name": "extract_invoice_data"},
        messages=[{
            "role": "user",
            "content": f"Extract invoice data from this document (ID: {doc_id}):\n\n{document}"
        }]
    )

    for block in response.content:
        if block.type == "tool_use":
            return block.input

    raise ValueError(f"No tool_use response for {doc_id}")


print("\n=== SCHEMA-ENFORCED EXTRACTION ===")
extractions = {}
for doc_id, doc in SAMPLE_DOCUMENTS.items():
    print(f"\n{doc_id}:")
    result = extract_with_schema(doc, doc_id)
    extractions[doc_id] = result
    print(f"  invoice_number: {result.get('invoice_number')}")
    print(f"  total_amount:   {result.get('total_amount_usd')}")
    print(f"  confidence:     {result.get('extraction_confidence')}")
    print(f"  notes:          {result.get('extraction_notes', 'none')[:80] if result.get('extraction_notes') else 'none'}")
```

---

## Part 3: Validation and Retry Loop (20 minutes)

```python
def validate_extraction(extraction: dict, doc_id: str) -> list:
    """
    Semantic validation — catches errors schema cannot prevent.
    Returns list of error strings.
    """
    errors = []

    # Validation 1: Line items should sum to total (within rounding tolerance)
    line_items = extraction.get("line_items", [])
    total = extraction.get("total_amount_usd")

    if line_items and total is not None:
        line_sum = sum(item.get("amount_usd", 0) for item in line_items)
        if abs(line_sum - total) > 1.00:  # $1 tolerance for tax/rounding
            errors.append(
                f"Line items sum to ${line_sum:.2f} but total_amount_usd is ${total:.2f}. "
                f"Either the line items are incomplete, or the total includes unreported charges."
            )

    # Validation 2: Date format check
    for date_field in ["invoice_date", "due_date"]:
        date_val = extraction.get(date_field)
        if date_val is not None:
            try:
                datetime.strptime(date_val, "%Y-%m-%d")
            except ValueError:
                errors.append(
                    f"{date_field} '{date_val}' is not in required YYYY-MM-DD format."
                )

    # Validation 3: Negative amounts
    if total is not None and total < 0:
        errors.append(f"total_amount_usd is negative (${total}). Invoices should be positive.")

    for item in line_items:
        if item.get("amount_usd", 0) < 0:
            errors.append(f"Line item '{item.get('description')}' has negative amount.")

    return errors


def extract_with_retry(document: str, doc_id: str, max_retries: int = 2) -> dict:
    """Full extraction pipeline with validation-retry loop."""
    extraction = extract_with_schema(document, doc_id)

    for attempt in range(max_retries):
        errors = validate_extraction(extraction, doc_id)

        if not errors:
            print(f"  ✅ {doc_id}: Valid on attempt {attempt + 1}")
            return extraction

        print(f"  ⚠️  {doc_id}: Validation errors on attempt {attempt + 1}: {errors}")

        # Check if retry will help
        fixable_errors = [e for e in errors if "format" in e.lower() or "sum" in e.lower()]
        unfixable_errors = [e for e in errors if e not in fixable_errors]

        if unfixable_errors and not fixable_errors:
            print(f"  ⏭️  {doc_id}: Errors are not fixable by retry — routing to human review")
            extraction["requires_human_review"] = True
            extraction["review_reason"] = unfixable_errors[0]
            return extraction

        if attempt < max_retries - 1:
            # Retry with specific error feedback
            error_text = "\n".join([f"- {e}" for e in errors])
            retry_response = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1024,
                system=FEW_SHOT_SYSTEM,
                tools=[INVOICE_EXTRACTION_TOOL],
                tool_choice={"type": "tool", "name": "extract_invoice_data"},
                messages=[
                    {"role": "user", "content": f"Extract invoice data from this document (ID: {doc_id}):\n\n{document}"},
                    {"role": "assistant", "content": [
                        {"type": "tool_use", "id": "tu_retry", "name": "extract_invoice_data", "input": extraction}
                    ]},
                    {"role": "user", "content": [
                        {"type": "tool_result", "tool_use_id": "tu_retry", "content": "Validation failed"}
                    ]},
                    {"role": "user", "content": (
                        f"The previous extraction had validation errors. Please re-extract, "
                        f"fixing these specific issues:\n{error_text}\n\n"
                        f"Re-read the original document carefully before re-extracting."
                    )}
                ]
            )

            for block in retry_response.content:
                if block.type == "tool_use":
                    extraction = block.input
                    break

    # Final validation check
    final_errors = validate_extraction(extraction, doc_id)
    if final_errors:
        extraction["requires_human_review"] = True
        extraction["review_reason"] = f"Failed validation after {max_retries} retries: {final_errors[0]}"

    return extraction


print("\n=== EXTRACTION WITH VALIDATION-RETRY ===")
final_results = {}
for doc_id, doc in SAMPLE_DOCUMENTS.items():
    print(f"\nProcessing {doc_id}:")
    result = extract_with_retry(doc, doc_id)
    final_results[doc_id] = result

# Summary report
print("\n=== PIPELINE SUMMARY ===")
needs_review = [doc_id for doc_id, r in final_results.items() if r.get("requires_human_review")]
auto_processed = [doc_id for doc_id in final_results if doc_id not in needs_review]

print(f"Auto-processed: {auto_processed}")
print(f"Needs human review: {needs_review}")
print(f"Success rate: {len(auto_processed)}/{len(final_results)} ({100*len(auto_processed)//len(final_results)}%)")
```

---

## Part 4: Demonstrate Nullable Field Hallucination Prevention (10 minutes)

```python
# Test: What happens with required (non-nullable) fields when data is absent?
TOOL_WITHOUT_NULLABLE = {
    "name": "extract_no_nullable",
    "description": "Extract invoice data",
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string"},   # NOT nullable — forces fabrication
            "invoice_date": {"type": "string"},     # NOT nullable — forces fabrication
            "total_amount_usd": {"type": "number"}, # NOT nullable — forces fabrication
            "vendor_name": {"type": "string"}       # NOT nullable — forces fabrication
        },
        "required": ["invoice_number", "invoice_date", "total_amount_usd", "vendor_name"]
    }
}

print("\n=== NULLABLE vs NON-NULLABLE FIELD COMPARISON ===")
sparse_doc = SAMPLE_DOCUMENTS["doc_006"]  # "consulting services provided March 2024\npaid already\n"
print(f"\nDocument: '{sparse_doc.strip()}'")

# Non-nullable extraction (forced fabrication)
response_forced = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=512,
    tools=[TOOL_WITHOUT_NULLABLE],
    tool_choice={"type": "tool", "name": "extract_no_nullable"},
    messages=[{"role": "user", "content": f"Extract data:\n\n{sparse_doc}"}]
)
for block in response_forced.content:
    if block.type == "tool_use":
        print(f"\nNon-nullable result (fabricated missing fields):")
        print(f"  invoice_number: {block.input.get('invoice_number')}")
        print(f"  invoice_date: {block.input.get('invoice_date')}")
        print(f"  total_amount_usd: {block.input.get('total_amount_usd')}")
        print(f"  ⚠️  Are these values real or fabricated?")

# Nullable extraction (honest nulls)
response_nullable = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=512,
    tools=[INVOICE_EXTRACTION_TOOL],
    tool_choice={"type": "tool", "name": "extract_invoice_data"},
    messages=[{"role": "user", "content": f"Extract data:\n\n{sparse_doc}"}]
)
for block in response_nullable.content:
    if block.type == "tool_use":
        print(f"\nNullable result (honest null for absent fields):")
        print(f"  invoice_number: {block.input.get('invoice_number')}")
        print(f"  invoice_date: {block.input.get('invoice_date')}")
        print(f"  total_amount_usd: {block.input.get('total_amount_usd')}")
        print(f"  ✅ Null = field absent (honest), not fabricated")
```

---

## Reflection Questions

```python
"""
REFLECTION:

1. Compare the naive extraction output with the schema-enforced output.
   What were the specific inconsistencies in the naive version?
   (Different field names? Different date formats? Inconsistent null representation?)
   Answer:

2. For doc_002 (narrative format), how did the extraction handle
   "four thousand eight hundred eighty-two dollars and fifty cents"?
   Did the few-shot example help?
   Answer:

3. When you tested the non-nullable schema on doc_006 (minimal content),
   what values did Claude fabricate for the missing fields?
   Why is this dangerous in a production system?
   Answer:

4. In the retry loop, which types of errors could be fixed by retry?
   Which could not? What did the system do for non-fixable errors?
   Answer:

5. The FEW_SHOT_SYSTEM includes an example of line items not summing to total.
   What should the extraction do in this case — fix the discrepancy or report it?
   Why?
   Answer:
"""
```

---

## Completion Criteria

✅ Schema-enforced extraction produces consistent output across all 6 document types
✅ Nullable fields return null for absent data (not fabricated values)
✅ Validation-retry loop catches and attempts to fix format errors
✅ Non-fixable errors (missing information) route to human review without endless retries
✅ Non-nullable field hallucination demonstrated and understood
✅ All reflection questions answered

---

*Next Lab: D5-01 — Context Management and Error Propagation*
