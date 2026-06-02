# Domain 4 Practice Questions: Prompt Engineering & Structured Output
### 25 Questions | CCAF Exam Preparation

**Pass threshold: 23/25 (90%)**

---

**Q1.** A code review tool produces too many false positives on style issues. Adding "only report high-confidence findings" to the prompt has no effect. The BEST fix is:

A) Increase the model's temperature to make it more selective  
B) Define explicit categories: what to ALWAYS report (bugs, security) and what to NEVER report (style, naming, formatting)  
C) Add examples of high-confidence findings to demonstrate what the threshold should be  
D) Switch to a larger model with better judgment about confidence  

---

**Q2.** Few-shot examples are MOST valuable when:

A) The task is complex and requires extensive reasoning  
B) Detailed prose instructions produce inconsistent output format or ambiguous-case handling  
C) The model lacks knowledge of a specialized domain  
D) The task involves real-time data that cannot be included in training  

---

**Q3.** Using `tool_use` with a JSON schema to enforce structured output is more reliable than prompt-based JSON instructions because:

A) tool_use is faster and uses fewer tokens  
B) The API validates the schema, eliminating JSON syntax errors — Claude cannot return malformed JSON  
C) tool_use allows the model to stream structured output progressively  
D) tool_use schemas support more complex data types than JSON  

---

**Q4.** A strict JSON schema via tool_use eliminates syntax errors but does NOT prevent:

A) Missing required fields  
B) Wrong data types  
C) Semantic errors (line items that don't sum to total, values in wrong fields)  
D) Null values in required fields  

---

**Q5.** An invoice extraction tool has `"invoice_number": {"type": "string"}` (not nullable). The source document has no invoice number. What will the model likely do?

A) Return an error indicating the required field is missing  
B) Return null despite the non-nullable type constraint  
C) Fabricate an invoice number to satisfy the required schema field  
D) Omit the invoice_number field entirely  

---

**Q6.** The Message Batches API has a processing window of up to 24 hours. This makes it UNSUITABLE for:

A) Overnight technical debt reports (reviewed next morning)  
B) Weekly security audit reports  
C) Pre-merge checks where developers are waiting for results before they can proceed  
D) Nightly test generation for review at next day's stand-up  

---

**Q7.** Your CI/CD pipeline uses the Message Batches API for code analysis. The SLA requires analysis within 30 hours. Batch processing takes up to 24 hours. How often should you submit batches?

A) Every 24 hours — same as the batch processing window  
B) Every 6 hours — leaves 24 hours for processing within the 30-hour SLA  
C) Every 12 hours — conservative estimate with buffer  
D) Every hour — ensures maximum freshness  

---

**Q8.** The `custom_id` field in the Message Batches API is used to:

A) Assign a unique identifier to each batch job for billing purposes  
B) Correlate each request to its response and identify specific failed requests for resubmission  
C) Tag requests by content type for priority processing  
D) Link batch requests to specific GitHub commits or PRs  

---

**Q9.** The Message Batches API does NOT support:

A) Multiple requests in a single batch  
B) Multi-turn tool calling within a single batch request  
C) JSON schema validation of outputs  
D) Custom request identifiers  

---

**Q10.** Why is an independent Claude instance more effective for code review than asking the generating instance to self-review?

A) Independent instances have access to more recent training data  
B) The generating session retains reasoning context, making it less likely to question its own decisions — independent instance has no such bias  
C) Independent instances can be configured with different system prompts  
D) Self-review is limited by the session's context window size  

---

**Q11.** A 14-file pull request review produces inconsistent results: detailed feedback for some files, superficial for others, and contradictory findings (same pattern flagged in one file, approved in another). The root cause is:

A) The model's context window is too small for 14 files  
B) The review prompt lacks specificity about which issues to flag  
C) Attention dilution when processing too many files simultaneously in a single pass  
D) The files are in different languages and require different review criteria  

---

**Q12.** The multi-pass review architecture that addresses attention dilution uses:

A) Multiple model instances each reviewing a random subset of files  
B) Per-file local analysis passes (one focused call per file) followed by a separate cross-file integration pass  
C) A weighted review that gives more attention to larger files  
D) Sequential review where each file's analysis includes context from the previous file  

---

**Q13.** When should you retry an extraction after a validation failure?

A) Always — retrying improves output quality regardless of the error type  
B) When the error is a format issue (wrong date format, number as string) — but NOT when the field is simply absent from the source document  
C) When confidence is below 80% — retry until confidence reaches the threshold  
D) Never — retrying produces identical results  

---

**Q14.** The retry-with-error-feedback pattern requires including in the retry prompt:

A) A different system prompt with stricter instructions  
B) The original document, the failed extraction, and the specific validation errors to correct  
C) The previous extraction only — Claude will identify the errors itself  
D) Instructions to ignore the previous attempt and start fresh  

---

**Q15.** A review tool consistently generates false positives for `string_concatenation_in_query` patterns in test files (where test data concatenation is intentional). Adding a `detected_pattern` field to findings would help because:

A) It allows the model to avoid flagging that pattern in future sessions  
B) It enables systematic analysis of which patterns have high dismissal rates — allowing targeted prompt improvements  
C) It creates a lookup table of approved patterns that overrides the review  
D) It reduces token usage by skipping previously-seen patterns  

---

**Q16.** A developer instructs: "Review this code carefully and only report issues you're very confident about." This instruction will:

A) Significantly reduce false positives by raising the reporting threshold  
B) Have minimal effect — "confidence" is not well-calibrated; explicit category criteria are more effective  
C) Increase latency as the model spends more time evaluating confidence  
D) Improve precision but reduce recall  

---

**Q17.** You are extracting data from documents with varying structures: some have explicit invoice numbers, some reference "our invoice ref INV-123", and some use a different numbering system. The BEST technique to improve extraction consistency across formats is:

A) Write a more detailed description of what constitutes an invoice number  
B) Add few-shot examples showing correct extraction from each document structure variant  
C) Use a stricter JSON schema that validates invoice number format  
D) Pre-process documents to normalize structure before extraction  

---

**Q18.** A batch of 500 invoice extractions has 23 failures. The correct handling is:

A) Re-run the entire batch — partial batches cannot be submitted  
B) Identify the 23 failed documents by custom_id, analyze each failure type, and resubmit with appropriate modifications (e.g., chunking for context-exceeded documents)  
C) Accept the 477 successes and discard the 23 failures  
D) Wait 24 hours and retry automatically — the batch API handles retries  

---

**Q19.** An extraction schema has `"amount": {"type": "number"}` as a required field. You process a document that says "amount varies by usage." What is the correct schema design change?

A) Change the type to `string` to accommodate non-numeric amounts  
B) Change to `{"type": ["number", "null"]}` — nullable allows honest null when amount is genuinely absent or indeterminate  
C) Add a validation rule that maps "varies" to 0  
D) Add an `amount_notes` field and leave `amount` required  

---

**Q20.** Few-shot examples for ambiguous scenarios should demonstrate:

A) The most common case — edge cases should be documented separately  
B) Both what was chosen AND the reasoning for choosing it over plausible alternatives  
C) As many examples as possible to maximize coverage  
D) Only negative examples (what NOT to do) to constrain the model  

---

**Q21.** `tool_choice: {"type": "tool", "name": "extract_metadata"}` is used in the first API call. What is the correct tool_choice for subsequent enrichment steps?

A) Continue forcing `extract_metadata` — consistency reduces errors  
B) Switch to `{"type": "auto"}` — allow Claude to select appropriate enrichment tools for each document  
C) Use `{"type": "any"}` — guarantee a tool is called but allow flexibility  
D) Remove tool_choice entirely for enrichment steps  

---

**Q22.** High false positive rates in one review category can undermine the entire review system because:

A) They consume API quota that could be used for accurate detections  
B) Developers who dismiss alerts from the high-FP category learn to dismiss all alerts, including accurate ones from other categories  
C) They cause the model to become less accurate in subsequent review sessions  
D) They increase review latency and slow down the PR merge process  

---

**Q23.** The most reliable method to guarantee structured JSON output from Claude is:

A) Instructing Claude in the system prompt to always respond in valid JSON  
B) Using a regex post-processor to extract JSON from Claude's response  
C) Defining an extraction tool with a JSON schema and using tool_choice to force the call  
D) Using extended thinking mode which forces structured reasoning  

---

**Q24.** You need to process 10,000 documents for a weekly report. Documents are submitted Monday morning and the report is needed by end of day Friday. Should you use synchronous API or batch API?

A) Synchronous — 10,000 documents requires guaranteed processing time  
B) Batch API — non-blocking, latency-tolerant workload with 50% cost savings; 5 days >> 24-hour processing window  
C) Batch API — but only if documents can be processed in parallel  
D) Synchronous with rate limiting to stay within quota  

---

**Q25.** The `"other"` + detail pattern in an enum schema (e.g., `enum: ["travel", "software", "hardware", "other"]` plus `detail` field) is used to:

A) Provide a fallback for when the model is uncertain about the category  
B) Allow extensible categorization where new categories appear — "other" handles unknown values without forcing fabrication of a predefined category  
C) Flag items for human review by categorizing them as other  
D) Reduce schema size by collapsing rare categories into one  

---

## Answer Key

| Q | Answer | Key Concept |
|---|--------|-------------|
| 1 | B | Explicit categories beat confidence-based filtering |
| 2 | B | Few-shot for inconsistent outputs and ambiguous cases |
| 3 | B | tool_use eliminates syntax errors via API validation |
| 4 | C | Schema validates syntax; semantic errors still possible |
| 5 | C | Non-nullable required fields → fabricated values |
| 6 | C | Batch = no latency SLA; unsuitable for blocking workflows |
| 7 | B | SLA (30h) - batch window (24h) = submit every 6 hours |
| 8 | B | custom_id correlates requests to responses and identifies failures |
| 9 | B | Batch API does not support multi-turn tool calling |
| 10 | B | Session retains reasoning context → self-review bias |
| 11 | C | Attention dilution in single-pass multi-file review |
| 12 | B | Per-file local passes + cross-file integration pass |
| 13 | B | Retry fixes format errors; can't fix absent information |
| 14 | B | Include document + failed extraction + specific errors |
| 15 | B | detected_pattern enables systematic FP analysis |
| 16 | B | "Confidence" instruction ineffective vs explicit categories |
| 17 | B | Few-shot for varied document structure handling |
| 18 | B | Identify by custom_id, analyze failure, resubmit modified |
| 19 | B | Nullable when value may be absent — prevents fabrication |
| 20 | B | Show choice AND reasoning for why alternative was rejected |
| 21 | B | Switch to "auto" after forced first step |
| 22 | B | FP in one category erodes trust in all categories |
| 23 | C | tool_use + JSON schema = most reliable structured output |
| 24 | B | Latency-tolerant weekly report → batch API |
| 25 | B | "other" + detail for extensible categorization |
