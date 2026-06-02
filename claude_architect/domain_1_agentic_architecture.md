# Domain 1: Agentic Architecture & Orchestration
### CCAF Exam Weight: 27% — Highest Priority Domain

---

## Overview

This domain is the foundation of everything Claude can do autonomously. An **agent** is not
just a model that answers questions — it is a model that *acts*: calling tools, observing
results, reasoning about what to do next, and continuing until the task is complete.

You must understand this domain deeply because the exam will present broken or poorly
designed agentic systems and ask you to diagnose and fix them. Surface knowledge will not
pass this exam. You need to *feel* the difference between a well-designed agent and a fragile one.

**Scenarios this domain covers:**
- Scenario 1: Customer Support Resolution Agent
- Scenario 3: Multi-Agent Research System
- Scenario 4: Developer Productivity with Claude

---

## Task Statement 1.1 — The Agentic Loop

### What It Is

The agentic loop is the heartbeat of every agent. It is the cycle of:
1. Send a request to Claude
2. Inspect the response's `stop_reason`
3. If `stop_reason == "tool_use"` → execute the tool → append result → go back to step 1
4. If `stop_reason == "end_turn"` → the agent is done → return the final response

That's it. Everything else in agentic architecture is built on top of this loop.

### The Two Stop Reasons You Must Know

| `stop_reason` | Meaning | Your Action |
|---|---|---|
| `"tool_use"` | Claude wants to call a tool | Execute the tool, append result to messages, loop again |
| `"end_turn"` | Claude is finished | Return the response to the user |

### How the Conversation History Works

Every iteration of the loop, you append two things to the messages array:
1. The **assistant message** containing the tool call request
2. A **tool result message** containing the output of executing that tool

Claude sees the entire history on every API call. This is how it "remembers" what it has
already done and reasons about what to do next. Without this, Claude would repeat the same
tool call forever.

### The Correct Loop in Python

```python
import anthropic

client = anthropic.Anthropic()

def run_agent(user_message: str, tools: list) -> str:
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            tools=tools,
            messages=messages
        )

        # Always check stop_reason first
        if response.stop_reason == "end_turn":
            # Extract the text response and return it
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text

        elif response.stop_reason == "tool_use":
            # Append the assistant's response (contains tool call) to history
            messages.append({"role": "assistant", "content": response.content})

            # Find and execute all tool calls in this response
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Append all tool results to history
            messages.append({"role": "user", "content": tool_results})
            # Loop continues — Claude sees the results and decides next action

        else:
            # Handle unexpected stop reasons (max_tokens, stop_sequence)
            raise RuntimeError(f"Unexpected stop_reason: {response.stop_reason}")
```

### Anti-Patterns to Avoid — These Will Be on the Exam

The exam will present broken agent implementations. Know these failure modes cold:

**Anti-Pattern 1: Parsing natural language to detect loop termination**
```python
# WRONG — never do this
if "I have completed" in response.text or "task is done" in response.text:
    break
```
Why it fails: Claude might say "I have completed the first step" mid-task. Natural language
is ambiguous. `stop_reason` is deterministic.

**Anti-Pattern 2: Arbitrary iteration caps as the primary stop mechanism**
```python
# WRONG — iteration cap as primary stop
for i in range(10):
    response = call_claude(messages)
    # no stop_reason check
```
Why it fails: Complex tasks may legitimately need more iterations. Simple tasks terminate in
one. The correct stopping mechanism is `stop_reason == "end_turn"`, not a counter.
A *safety* cap (e.g., 50 iterations as a runaway guard) is acceptable alongside proper
`stop_reason` checking — but never as the *primary* mechanism.

**Anti-Pattern 3: Checking for assistant text as completion indicator**
```python
# WRONG
if response.content[0].type == "text":
    return response.content[0].text  # assumes text = done
```
Why it fails: Claude can return a mix of text and tool_use blocks in the same response.
Always check `stop_reason`, not content type.

**Anti-Pattern 4: Not appending tool results to history**
```python
# WRONG — executing tool but not appending result
result = execute_tool(tool_name, tool_input)
# calling Claude again without the result in messages
response = call_claude(messages)  # Claude doesn't know what happened!
```
Why it fails: Claude has no memory between API calls. If the tool result is not in the
messages array, Claude will either repeat the tool call or hallucinate an answer.

---

## Task Statement 1.2 — Multi-Agent Orchestration: Coordinator-Subagent Pattern

### The Architecture

When a task is too complex for a single agent, you decompose it across multiple specialized
agents. The standard pattern is **hub-and-spoke**:

```
                    ┌─────────────────────┐
                    │   COORDINATOR AGENT │
                    │                     │
                    │  - Decomposes task  │
                    │  - Routes to agents │
                    │  - Aggregates results│
                    │  - Handles errors   │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼──────┐ ┌───────▼──────┐ ┌──────▼───────┐
    │  WEB SEARCH    │ │   DOCUMENT   │ │  SYNTHESIS   │
    │    AGENT       │ │   ANALYSIS   │ │    AGENT     │
    │                │ │    AGENT     │ │              │
    └────────────────┘ └──────────────┘ └──────────────┘
```

### Critical Rules of This Pattern

**Rule 1: Subagents have isolated context.**
Subagents do NOT inherit the coordinator's conversation history. They start fresh.
You must explicitly pass everything a subagent needs in its prompt.

**Rule 2: All communication routes through the coordinator.**
Subagents never talk to each other directly. This is not a limitation — it is a design
feature. It gives you observability, consistent error handling, and controlled information flow.

**Rule 3: The coordinator owns task decomposition.**
If the coordinator decomposes a task too narrowly (e.g., "AI in creative industries" → only
visual arts subtasks), the subagents will execute perfectly and still produce wrong output.
The coordinator is responsible for coverage.

**Rule 4: The coordinator owns error handling.**
When a subagent fails, the coordinator decides: retry? use partial results? skip and annotate?
escalate? Subagents should handle *transient* failures locally and only propagate errors
they cannot resolve.

### Coordinator Design in Python (Agent SDK)

```python
from anthropic import Anthropic

client = Anthropic()

COORDINATOR_SYSTEM = """You are a research coordinator. Your job is to:
1. Analyze the research query and identify all relevant subtopics
2. Delegate each subtopic to the appropriate specialized subagent
3. Aggregate and synthesize results from all subagents
4. Identify coverage gaps and re-delegate targeted follow-up queries
5. Produce a comprehensive, well-cited final report

Always ensure your task decomposition covers the full scope of the query.
Do not proceed to synthesis until all major subtopics have been researched."""

def run_coordinator(research_query: str) -> str:
    messages = [{"role": "user", "content": research_query}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=8096,
            system=COORDINATOR_SYSTEM,
            tools=[web_search_tool, document_analysis_tool,
                   synthesis_tool, report_tool],
            messages=messages
        )

        if response.stop_reason == "end_turn":
            return extract_text(response)

        elif response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    # Each "tool call" here actually spawns a subagent
                    result = invoke_subagent(block.name, block.input)
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "user", "content": results})
```

### Iterative Refinement — The Coordinator's Secret Weapon

A one-pass coordinator misses things. A good coordinator evaluates the synthesis output
for gaps and re-delegates:

```
Pass 1: Coordinator → Search Agent (broad query) → Analysis Agent → Synthesis Agent
         ↓
Coordinator evaluates synthesis: "Missing coverage of Topic X"
         ↓
Pass 2: Coordinator → Search Agent (targeted query on Topic X) → Analysis Agent
         ↓
Coordinator re-invokes Synthesis with complete findings
         ↓
Final Report
```

---

## Task Statement 1.3 — Subagent Invocation, Context Passing, and Spawning

### The Task Tool

In the Claude Agent SDK, subagents are spawned using the **Task tool**. The coordinator's
`allowedTools` must explicitly include `"Task"` or subagent spawning will fail silently.

```python
# AgentDefinition for a subagent
web_search_agent = AgentDefinition(
    name="web_search_agent",
    description="Searches the web for current information on a given topic",
    system_prompt="""You are a web search specialist. Search thoroughly for information
    on the given topic. Return structured findings with source URLs and publication dates.
    Do not synthesize or editorialize — return what the sources say.""",
    allowed_tools=["web_search", "fetch_url"]  # scoped, not all tools
)
```

### Passing Context to Subagents — The Most Common Exam Topic

Because subagents have no memory of the coordinator's conversation, you must inject
everything they need into their prompt. This is the single most common mistake in
multi-agent systems.

**Wrong — relying on implicit context:**
```python
# WRONG: subagent has no idea what prior agents found
invoke_subagent("synthesis_agent", {
    "instruction": "Synthesize the research findings"
    # What findings? The subagent has no idea.
})
```

**Correct — explicit context injection:**
```python
# RIGHT: pass everything the subagent needs
invoke_subagent("synthesis_agent", {
    "instruction": "Synthesize the following research findings into a comprehensive report",
    "web_search_results": web_search_findings,    # actual content
    "document_analysis_results": doc_findings,    # actual content
    "source_metadata": {                          # attribution preserved
        "sources": [
            {"url": "https://...", "title": "...", "date": "2024-01-15"},
        ]
    },
    "research_query": original_query,
    "quality_criteria": "Cite every claim. Flag conflicting findings. Note coverage gaps."
})
```

### Parallel Subagent Spawning

To run subagents in parallel, emit **multiple Task tool calls in a single coordinator
response** — not across separate turns. This is a critical performance optimization.

```python
# The coordinator's response content includes multiple tool calls simultaneously:
# [
#   ToolUseBlock(id="tu_1", name="Task", input={"agent": "web_search", "query": "AI music"}),
#   ToolUseBlock(id="tu_2", name="Task", input={"agent": "web_search", "query": "AI film"}),
#   ToolUseBlock(id="tu_3", name="Task", input={"agent": "doc_analysis", "docs": [...]}),
# ]
# All three run in parallel. The coordinator waits for all results before continuing.
```

Sequential spawning (one Task call per turn) means subagent B waits for subagent A
to finish before starting. For independent tasks, this is wasted time.

### Coordinator Prompt Design

Coordinator prompts should specify **goals and quality criteria**, not step-by-step procedures.
This enables subagent adaptability.

```python
# WEAK coordinator prompt (procedural):
"""Step 1: Call web_search with query X. Step 2: Call doc_analysis with result.
Step 3: Call synthesis. Step 4: Generate report."""

# STRONG coordinator prompt (goal-oriented):
"""Research the given topic comprehensively. Ensure coverage spans all relevant subtopics.
Each claim in the final report must be traceable to a specific source.
Flag any areas where sources conflict or where coverage is thin."""
```

---

## Task Statement 1.4 — Multi-Step Workflows with Enforcement and Handoff Patterns

### The Core Insight: Prompts Are Probabilistic, Code Is Deterministic

This is arguably the most important concept in the entire exam.

When you need a specific sequence of operations to happen — especially for operations with
financial, legal, or safety consequences — **you cannot rely on a prompt to enforce it**.

| Approach | Compliance Rate | Use When |
|---|---|---|
| Prompt instruction | ~95-99% | Low-stakes guidance |
| Few-shot examples | ~97-99% | Moderate consistency needs |
| Programmatic enforcement | 100% | Business-critical sequences |

A 1% failure rate on `process_refund` without `get_customer` verification means real
customers get refunds processed against the wrong account. That is not acceptable.

### Programmatic Prerequisites

```python
# State tracker — enforced in code, not prompt
class AgentState:
    def __init__(self):
        self.verified_customer_id = None
        self.verified_order_id = None

state = AgentState()

def execute_tool(tool_name: str, tool_input: dict) -> dict:
    # Programmatic gate — cannot be bypassed by the model
    if tool_name == "lookup_order":
        if state.verified_customer_id is None:
            return {
                "error": "Cannot lookup order: customer identity not verified.",
                "required_action": "Call get_customer first to verify identity.",
                "isRetryable": False
            }

    if tool_name == "process_refund":
        if state.verified_customer_id is None or state.verified_order_id is None:
            return {
                "error": "Cannot process refund: prerequisite verification incomplete.",
                "required_steps": ["get_customer", "lookup_order"],
                "isRetryable": False
            }
        # Amount threshold enforcement
        if tool_input.get("amount", 0) > 500:
            return {
                "error": "Refund amount exceeds automated threshold ($500).",
                "action": "escalate_to_human",
                "isRetryable": False
            }

    # Proceed with actual tool execution
    return call_actual_tool(tool_name, tool_input)
```

### Structured Handoff Protocols

When escalating to a human agent, the handoff package must be self-contained. The human
agent does not have access to the conversation transcript.

```python
def compile_handoff_summary(state: AgentState, issue: dict) -> dict:
    return {
        "customer_id": state.verified_customer_id,
        "customer_name": state.customer_data.get("name"),
        "contact_email": state.customer_data.get("email"),
        "order_id": state.verified_order_id,
        "issue_type": issue["type"],
        "root_cause": issue["root_cause"],
        "resolution_attempted": issue["steps_taken"],
        "recommended_action": issue["recommendation"],
        "refund_amount_requested": issue.get("refund_amount"),
        "policy_exception_required": issue.get("policy_exception", False),
        "conversation_summary": summarize_conversation(state.messages),
        "escalation_reason": issue["escalation_reason"],
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Decomposing Multi-Concern Requests

Customers often present multiple issues in one message. The agent must decompose these,
investigate in parallel (sharing context), then synthesize a unified resolution.

```
Customer: "My order #12345 arrived damaged AND I was charged twice for order #12346"

Agent decomposition:
├── Issue A: Damaged item — Order #12345
│   └── Actions: lookup_order(12345) → verify damage → process_replacement
└── Issue B: Duplicate charge — Order #12346
    └── Actions: lookup_order(12346) → verify charges → process_refund

Both investigated in parallel using shared customer context.
Single unified response: "I've arranged a replacement for #12345 and refunded the
duplicate charge of $X for #12346. Expect..."
```

---

## Task Statement 1.5 — Agent SDK Hooks

### What Hooks Are

Hooks are interception points in the agent's execution pipeline. They let you run code
**before or after** tool calls — programmatically, not probabilistically.

The key hook types:

| Hook | Fires When | Use Case |
|---|---|---|
| `PreToolUse` | Before a tool call executes | Block policy violations, validate inputs |
| `PostToolUse` | After a tool call returns | Normalize data formats, enrich results |

### PostToolUse: Data Normalization

Different MCP tools return data in different formats. The agent should see clean,
normalized data — not a mix of Unix timestamps, ISO 8601, and MM/DD/YYYY strings.

```python
def post_tool_use_hook(tool_name: str, tool_result: dict) -> dict:
    """Normalize heterogeneous data formats before the model processes them."""

    if tool_name == "get_customer":
        # Normalize timestamp formats
        if "created_at" in tool_result:
            tool_result["created_at"] = normalize_to_iso8601(tool_result["created_at"])

        # Normalize status codes to human-readable
        status_map = {1: "active", 2: "suspended", 3: "closed", 0: "pending"}
        if "status_code" in tool_result:
            tool_result["account_status"] = status_map.get(
                tool_result["status_code"], "unknown"
            )

    if tool_name == "lookup_order":
        # Convert Unix timestamp to ISO 8601
        if "order_date_unix" in tool_result:
            tool_result["order_date"] = datetime.utcfromtimestamp(
                tool_result["order_date_unix"]
            ).isoformat()

    return tool_result
```

### PreToolUse: Policy Enforcement

```python
def pre_tool_use_hook(tool_name: str, tool_input: dict) -> dict | None:
    """
    Returns None to allow the tool call to proceed.
    Returns an error dict to block it and return the error to the model.
    """
    if tool_name == "process_refund":
        amount = tool_input.get("amount", 0)

        if amount > 500:
            # Block the call — redirect to human escalation
            return {
                "blocked": True,
                "reason": f"Refund amount ${amount} exceeds automated limit of $500.",
                "required_action": "Call escalate_to_human with refund details.",
                "isRetryable": False
            }

    return None  # Allow all other tool calls
```

### Hooks vs. Prompts — Know This for the Exam

The exam will give you scenarios where a business rule is being violated some percentage
of the time. The answer is **always hooks** when:
- The rule involves financial thresholds
- The rule involves identity verification before sensitive operations
- The rule is a compliance requirement
- You need 100% enforcement, not ~99%

The answer is **prompt-based** when:
- The rule is a style preference
- Occasional non-compliance is acceptable
- The "rule" is more of a guideline

---

## Task Statement 1.6 — Task Decomposition Strategies

### Two Patterns — Know When to Use Each

**Pattern 1: Prompt Chaining (Fixed Sequential Pipeline)**

Use when: The task has a predictable structure, each step's output is a clear input to
the next, and the sequence never changes.

```
Document → [Extract Issues] → [Assess Severity] → [Generate Fix] → [Format Report]
```

Best for: Code review pipelines, document processing, structured analysis workflows.

```python
# Prompt chaining: each step is a separate Claude call
def review_pipeline(code: str) -> dict:
    # Step 1: Local analysis per file
    local_issues = []
    for file in parse_files(code):
        issues = claude_call(
            f"Analyze {file.name} for bugs, security issues, and anti-patterns. "
            f"Do not consider cross-file dependencies at this stage.\n\n{file.content}"
        )
        local_issues.append(issues)

    # Step 2: Cross-file integration pass (separate call with full context)
    integration_issues = claude_call(
        f"Given these per-file analyses:\n{format_issues(local_issues)}\n\n"
        f"Identify cross-file issues: data flow bugs, inconsistent interfaces, "
        f"circular dependencies, and violations of architectural patterns."
    )

    return combine(local_issues, integration_issues)
```

**Pattern 2: Dynamic Adaptive Decomposition**

Use when: The task is open-ended, intermediate findings determine next steps, and you
cannot know the full plan upfront.

Best for: Codebase investigation, open-ended research, debugging unknown systems.

```python
# Dynamic decomposition: plan evolves based on findings
def investigate_codebase(task: str) -> dict:
    # Phase 1: Map the territory
    structure = claude_call(
        f"Map the structure of this codebase. Identify: entry points, core modules, "
        f"test coverage, key dependencies. Return a structured analysis."
    )

    # Phase 2: Generate investigation plan based on what we found
    plan = claude_call(
        f"Given this codebase structure:\n{structure}\n\n"
        f"For the task: '{task}'\n"
        f"Generate a prioritized investigation plan. Identify the 5 highest-impact "
        f"areas to examine and why."
    )

    # Phase 3: Execute plan — each step may reveal new subtasks
    findings = []
    for step in parse_plan(plan):
        result = claude_call(f"Investigate: {step}\nContext: {findings_so_far()}")
        findings.append(result)
        # New subtasks may emerge from findings

    return synthesize(findings)
```

### The Code Review Split — A Specific Exam Pattern

Large code reviews fail when all files are analyzed together (attention dilution).
The correct pattern:

```
Step 1: Per-file local analysis (N parallel calls, one per file)
         → Each call sees only one file → focused, deep analysis
Step 2: Cross-file integration pass (one call with all per-file summaries)
         → Looks for: data flow bugs, interface mismatches, architectural violations
```

---

## Task Statement 1.7 — Session State, Resumption, and Forking

### Named Session Resumption

```bash
# Start a named session
claude --session-name "refund-system-investigation"

# Resume it later (even after closing terminal)
claude --resume "refund-system-investigation"
```

When resuming after code changes, **tell the agent explicitly what changed**:
```
"Since our last session, I modified PaymentProcessor.process() to add idempotency
checking. Please re-analyze that method specifically — the rest of the analysis
from our last session is still valid."
```

Do not just resume and ask the same question — Claude will reason from stale tool results.

### Fork Sessions

`fork_session` creates a branch from a shared analysis baseline, letting you explore
two approaches without contaminating either:

```bash
# After analyzing a codebase, fork to explore two refactoring strategies
fork_session("compare-strategies")
# Branch A: Try approach 1 (e.g., extract microservice)
# Branch B: Try approach 2 (e.g., modularize monolith)
# Compare results, choose the better approach
```

### When to Resume vs. Start Fresh

| Situation | Best Approach |
|---|---|
| Prior context still valid, continuing same investigation | Resume session |
| Code has changed significantly since last session | New session + inject summary |
| Prior tool results are stale | New session + structured summary |
| Exploring a divergent approach | fork_session |
| Context window is nearly full | New session + /compact first |

---

## Key Concepts Summary — Domain 1

| Concept | What to Know |
|---|---|
| `stop_reason` | The ONLY correct loop termination signal |
| Tool result in history | Must be appended or Claude repeats tool calls |
| Subagent context isolation | Must pass everything explicitly in prompt |
| Parallel spawning | Multiple Task calls in ONE coordinator response |
| Programmatic enforcement | Use for 100% compliance (financial, identity, safety) |
| Hooks | PreToolUse (block/validate), PostToolUse (normalize/enrich) |
| Prompt chaining | Fixed structure, predictable tasks |
| Dynamic decomposition | Open-ended, findings-driven tasks |
| Session resumption | Tell Claude what changed since last session |
| fork_session | Explore divergent approaches from shared baseline |

---

## What the Exam Will Test You On

The exam does not ask "what is an agentic loop." It presents scenarios like:

- *"Your agent skips identity verification 12% of the time. What do you do?"*
  → Programmatic prerequisite gate (not a better prompt)

- *"Your multi-agent research system covers only visual arts when asked about creative industries. Why?"*
  → Coordinator's task decomposition is too narrow

- *"Your code review produces contradictory feedback across files. How do you fix it?"*
  → Split into per-file passes + separate integration pass

- *"A subagent times out. What error structure enables the coordinator to make intelligent recovery decisions?"*
  → Structured error with failure_type, attempted_query, partial_results, alternatives

Practice answering these by reasoning about the *root cause*, not the *symptom*.

---

## Next Step

Complete **Lab D1-01** through **Lab D1-05** before moving to Domain 2.
The labs build on each other — do them in order.

Then complete the **Domain 1 Practice Questions** to verify your understanding.

Passing threshold for Domain 1 practice questions: **90%+**
If below 90%, re-read the section covering the questions you missed, then re-test.
