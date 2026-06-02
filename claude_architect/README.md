# CCAF Exam Preparation — Study Guide

**Claude Certified Architect – Foundations**
Passing score: 720/1000 | Format: Multiple choice | 4 of 6 scenarios tested

---

## How to Use This Material

**Recommended order:**

| Step | Action | Goal |
|------|--------|------|
| 1 | Read domain training doc | Understand concepts deeply |
| 2 | Complete labs in order | Feel the concepts through code |
| 3 | Take practice questions cold | Verify understanding |
| 4 | Score < 90%? Re-read + re-test | Close gaps before moving on |
| 5 | Repeat for all 5 domains | Full coverage |

**Do not skip the labs.** The exam tests judgment, not memorization.
Judgment comes from building and breaking things.

---

## Domain Map

| Domain | Weight | Training Doc | Labs | Practice Q's |
|--------|--------|-------------|------|-------------|
| 1: Agentic Architecture & Orchestration | **27%** | domain_1_agentic_architecture.md | lab_d1_01, 02, 03 | domain_1_questions.md (30 Q) |
| 2: Tool Design & MCP Integration | 18% | domain_2_tool_design_mcp.md | lab_d2_01, 02 | domain_2_questions.md (25 Q) |
| 3: Claude Code Configuration & Workflows | 20% | domain_3_claude_code_workflows.md | lab_d3_01 | domain_3_questions.md (25 Q) |
| 4: Prompt Engineering & Structured Output | 20% | domain_4_prompt_engineering.md | lab_d4_01 | domain_4_questions.md (25 Q) |
| 5: Context Management & Reliability | 15% | domain_5_context_management.md | lab_d5_01 | domain_5_questions.md (25 Q) |

---

## The 6 Exam Scenarios (4 will appear on your exam)

| Scenario | Primary Domains | Key Concepts |
|----------|----------------|--------------|
| 1: Customer Support Resolution Agent | D1, D2, D5 | Agentic loops, programmatic enforcement, escalation, context preservation |
| 2: Code Generation with Claude Code | D3, D5 | CLAUDE.md hierarchy, plan mode, skills, CI/CD |
| 3: Multi-Agent Research System | D1, D2, D5 | Coordinator-subagent, context passing, error propagation, provenance |
| 4: Developer Productivity with Claude | D2, D3, D1 | Built-in tools, MCP integration, task decomposition |
| 5: Claude Code for CI/CD | D3, D4 | Non-interactive mode, structured output, multi-pass review |
| 6: Structured Data Extraction | D4, D5 | tool_use schemas, validation-retry, batch API, confidence calibration |

---

## The Concepts That Appear Most Frequently

**1. Programmatic vs. Prompt-Based Enforcement**
When business rules require 100% compliance (financial thresholds, identity verification),
use hooks/prerequisite gates. Prompts are probabilistic — unacceptable for compliance.

**2. stop_reason is the ONLY correct loop termination signal**
Never use text parsing, content type checking, or iteration caps as primary stop mechanisms.

**3. Subagents have isolated context — pass everything explicitly**
They do not inherit the coordinator's conversation history. If you don't pass it, they don't have it.

**4. Structured errors enable intelligent recovery**
Generic "operation failed" messages prevent coordinators from making recovery decisions.
Always include: errorCategory, isRetryable, attemptedAction, partialResults, alternatives.

**5. Empty results ≠ access failure**
Must be distinguishable. Same `{"results": []}` for both = coordinator cannot recover.

**6. Nullable fields prevent hallucination**
Non-nullable required fields force Claude to fabricate values when data is absent.

**7. Multi-pass review beats single-pass for large reviews**
Per-file focused passes + cross-file integration pass avoids attention dilution.

**8. CLAUDE.md hierarchy: user → project → directory**
Team standards MUST be in project-level config (version controlled).
User-level config is personal and never shared.

**9. tool_choice: "auto" vs "any" vs forced**
auto = optional; any = required tool call (any); forced = required specific tool.

**10. Batch API: latency-tolerant workloads only**
24-hour window, no SLA — never for blocking pre-merge checks.

---

## Quick Reference: Exam Traps

The exam uses these patterns to catch candidates with incomplete knowledge:

| The Trap | The Wrong Answer | The Correct Answer |
|----------|-----------------|-------------------|
| Agent skips verification 1% of time | "Improve the prompt" | Programmatic prerequisite gate |
| Research system misses subtopics | "Subagents have bugs" | Coordinator's decomposition is too narrow |
| Multi-file review is inconsistent | "Use a larger model" | Per-file passes + integration pass |
| Structured output is inconsistent | "Add more instructions" | tool_use with JSON schema |
| New developer misses team standards | "They need to run /memory" | Standards are in user-level config; move to project-level |
| Generic error prevents recovery | "Error handling is fine" | Structured error with errorCategory, isRetryable, alternatives |
| Customer requests human agent | "Offer to resolve first" | Escalate immediately — honor explicit requests |
| Subagent context isolation bug | "Fix the subagent" | Pass complete findings explicitly in coordinator's subagent call |

---

## Lab Completion Checklist

- [ ] Lab D1-01: Correct agentic loop + 3 broken variants
- [ ] Lab D1-02: Multi-agent coordinator with context isolation demo
- [ ] Lab D1-03: Programmatic enforcement + PostToolUse normalization
- [ ] Lab D2-01: Tool description fixes + scoped toolsets + .mcp.json
- [ ] Lab D2-02: Structured error responses + local recovery
- [ ] Lab D3-01: CLAUDE.md hierarchy + slash commands + path rules (in Claude Code)
- [ ] Lab D4-01: Full extraction pipeline with schema + validation-retry
- [ ] Lab D5-01: Case facts pattern + escalation logic + error propagation

## Practice Question Scores

| Domain | Score | Date | Pass? |
|--------|-------|------|-------|
| D1 (30 Q, need 27) | /30 | | |
| D2 (25 Q, need 23) | /25 | | |
| D3 (25 Q, need 23) | /25 | | |
| D4 (25 Q, need 23) | /25 | | |
| D5 (25 Q, need 23) | /25 | | |

When all rows show ✅ Pass, you are ready for the exam.
