# Domain 2: Tool Design & MCP Integration
### CCAF Exam Weight: 18%

---

## Overview

Tools are how Claude interacts with the world. A Claude agent without well-designed tools
is like a brilliant engineer with no hands — it can reason perfectly but cannot act
effectively. This domain tests whether you can design tools that Claude will use correctly,
configure MCP servers properly, and build error responses that enable intelligent recovery.

The exam will present broken tool setups — misrouted calls, ambiguous descriptions,
unhelpful error responses — and ask you to diagnose and fix them.

**Scenarios this domain covers:**
- Scenario 1: Customer Support Resolution Agent
- Scenario 3: Multi-Agent Research System
- Scenario 4: Developer Productivity with Claude

---

## Task Statement 2.1 — Design Effective Tool Interfaces

### Tool Descriptions Are Everything

The model has no way to know what a tool does except by reading its description.
A minimal description like `"Retrieves customer information"` forces Claude to guess.
A rich description tells Claude exactly when to use the tool, what to pass, and what
it will get back.

**The five elements of a great tool description:**
1. **What it does** — the primary action
2. **When to use it** — vs. similar tools
3. **What inputs it expects** — formats, constraints, examples
4. **What it returns** — structure and key fields
5. **Edge cases** — what happens with unusual inputs

### Bad vs. Good Tool Descriptions

**Bad (causes misrouting):**
```python
{
    "name": "analyze_content",
    "description": "Analyzes content and returns results.",
    "input_schema": {
        "type": "object",
        "properties": {"content": {"type": "string"}},
        "required": ["content"]
    }
}
```

**Good (precise routing):**
```python
{
    "name": "extract_web_results",
    "description": (
        "Analyzes raw web search result HTML or JSON to extract structured data: "
        "titles, URLs, publication dates, and content excerpts. "
        "Use ONLY for web search output — not for PDF documents or database records. "
        "Input: raw web search response string. "
        "Returns: list of {title, url, date, excerpt} objects. "
        "If input is not web search format, returns an error rather than guessing."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "raw_search_output": {
                "type": "string",
                "description": "The raw output from a web search API call"
            }
        },
        "required": ["raw_search_output"]
    }
}
```

### Splitting Generic Tools — A Key Exam Pattern

A generic `analyze_document` tool that does everything is a reliability liability.
Claude cannot select the right behavior for the right situation. Split it:

```python
# BEFORE: One generic tool (Claude guesses what to do)
analyze_document(document, instruction="do whatever seems right")

# AFTER: Three purpose-specific tools (Claude selects precisely)
extract_data_points(document)       # Pull out structured facts, numbers, entities
summarize_content(document)         # Generate narrative summary
verify_claim_against_source(        # Check if a claim is supported by the document
    document, claim
)
```

### Overlapping Tool Names — The Misrouting Trap

When two tools have similar names AND similar descriptions, Claude will misroute calls.
This is especially common in systems that evolved organically.

**Problematic pair:**
- `analyze_content` — "Analyzes content"
- `analyze_document` — "Analyzes document content"

Claude cannot reliably distinguish these. Fix: rename one to reflect its specific domain.

```python
# Rename to reflect actual purpose
"analyze_content"  →  "extract_web_results"   # web-specific
"analyze_document" →  "analyze_pdf_document"  # document-specific
```

### System Prompt Keyword Sensitivity

System prompts can accidentally override good tool descriptions. Be careful with phrases
that create tool associations:

```
# Dangerous system prompt wording:
"When processing documents, use document tools."
# This keyword matching can cause 'analyze_document' to be called for web content
# if the system prompt uses 'document' broadly

# Better:
"Use extract_web_results for web search output and analyze_pdf_document for PDF files."
```

---

## Task Statement 2.2 — Structured Error Responses for MCP Tools

### The Four Error Categories

Every MCP tool error must specify its category. This determines how Claude (and the
coordinator) should respond.

| Category | Cause | Claude's Response |
|---|---|---|
| `transient` | Timeout, service unavailable, rate limit | Retry with backoff |
| `validation` | Invalid input format, missing required field | Fix the input and retry |
| `permission` | Auth failure, insufficient access | Do not retry; escalate |
| `business` | Policy violation, threshold exceeded | Do not retry; follow business logic |

### The isRetryable Flag

This is the single most important field in an error response. It tells Claude whether
retrying will help.

```python
# Transient error — retrying may succeed
{
    "isError": True,
    "errorCategory": "transient",
    "isRetryable": True,
    "retryAfterSeconds": 5,
    "message": "Search service temporarily unavailable. Retry in 5 seconds.",
    "partialResults": []  # Include any partial results
}

# Business rule violation — retrying will NOT help
{
    "isError": True,
    "errorCategory": "business",
    "isRetryable": False,
    "message": "Refund amount $750 exceeds automated processing limit of $500.",
    "requiredAction": "Call escalate_to_human with refund details.",
    "customerFriendlyMessage": "This refund requires manager approval."
}
```

### Empty Results vs. Access Failures

This distinction trips up many implementations — and appears on the exam.

```python
# WRONG: Both look the same to the coordinator
def search_orders(customer_id):
    try:
        results = db.query(customer_id)
        return {"results": results}  # Could be empty if no orders
    except DatabaseError:
        return {"results": []}  # Looks like "no orders" but is actually a failure!

# RIGHT: Distinguish the two cases
def search_orders(customer_id):
    try:
        results = db.query(customer_id)
        return {
            "status": "success",
            "results": results,
            "count": len(results)
            # Empty list here = legitimately no orders found
        }
    except DatabaseError as e:
        return {
            "isError": True,
            "errorCategory": "transient",
            "isRetryable": True,
            "message": f"Database query failed: {str(e)}",
            "partialResults": None
            # This = actual access failure, not "no results"
        }
```

### Local Recovery Before Propagation

Subagents should try to recover from transient failures locally before escalating
to the coordinator. Only propagate errors that cannot be resolved locally.

```python
def search_with_recovery(query: str, max_retries: int = 3) -> dict:
    last_error = None

    for attempt in range(max_retries):
        try:
            result = search_api.call(query)
            return {"status": "success", "results": result}
        except TimeoutError as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                continue

    # Local recovery exhausted — propagate with full context
    return {
        "isError": True,
        "errorCategory": "transient",
        "isRetryable": True,  # Coordinator can try again later
        "message": f"Search failed after {max_retries} attempts: {str(last_error)}",
        "attemptedQuery": query,
        "attemptsCount": max_retries,
        "partialResults": [],
        "alternativeApproach": "Try a more specific query or different search terms"
    }
```

---

## Task Statement 2.3 — Distribute Tools Across Agents

### The Principle of Least Tool Access

More tools = worse tool selection. This is counterintuitive but well-established.
When an agent has 18 tools, the decision complexity for Claude increases dramatically.
Tool selection reliability drops. Agents with specialized toolsets outperform
generalist agents on their specialization.

**Rule:** Give each agent the minimum tools required for its role.

```python
# WRONG: Give all agents all tools
coordinator_tools = all_18_tools
search_agent_tools = all_18_tools
synthesis_agent_tools = all_18_tools

# RIGHT: Scoped toolsets
coordinator_tools = ["Task", "summarize", "evaluate_coverage"]
search_agent_tools = ["web_search", "fetch_url", "filter_results"]
analysis_agent_tools = ["read_document", "extract_data", "verify_claim"]
synthesis_agent_tools = ["verify_fact", "compile_report", "format_output"]
# Note: synthesis agent gets verify_fact for 85% common case
# Complex verifications route through coordinator
```

### The tool_choice Configuration

Three modes — know each one cold:

```python
# AUTO: Claude decides whether to use a tool or respond with text
# Risk: Claude may respond conversationally when you need structured output
client.messages.create(tools=tools, tool_choice={"type": "auto"})

# ANY: Claude must call a tool — won't return plain text
# Use when: you need guaranteed structured output
client.messages.create(tools=tools, tool_choice={"type": "any"})

# FORCED: Claude must call this specific tool
# Use when: you need a specific operation first (e.g., extract_metadata before enrichment)
client.messages.create(
    tools=tools,
    tool_choice={"type": "tool", "name": "extract_metadata"}
)
```

### When to Force Tool Selection

Force tool selection when you have a required first step:

```python
# Step 1: Force metadata extraction before any other enrichment
response = client.messages.create(
    model="claude-opus-4-5",
    tools=extraction_tools,
    tool_choice={"type": "tool", "name": "extract_metadata"},
    messages=[{"role": "user", "content": document}]
)
metadata = get_tool_result(response)

# Step 2: Now allow free tool selection for enrichment steps
response = client.messages.create(
    model="claude-opus-4-5",
    tools=enrichment_tools,
    tool_choice={"type": "auto"},
    messages=build_enrichment_messages(metadata, document)
)
```

---

## Task Statement 2.4 — MCP Server Integration

### Project vs. User Scope

| Config Location | Scope | Use Case |
|---|---|---|
| `.mcp.json` (project root) | All team members who clone the repo | Shared team tooling: GitHub, Jira, internal APIs |
| `~/.claude.json` (user home) | Only that developer | Personal tools, experimental servers, dev credentials |

**Critical rule:** Team tooling goes in `.mcp.json` (version controlled).
Personal/experimental servers go in `~/.claude.json` (never committed).

### Configuring .mcp.json

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "jira": {
      "command": "node",
      "args": ["./tools/jira-mcp-server.js"],
      "env": {
        "JIRA_URL": "${JIRA_URL}",
        "JIRA_API_TOKEN": "${JIRA_API_TOKEN}"
      }
    },
    "internal-api": {
      "command": "python",
      "args": ["-m", "internal_tools.mcp_server"],
      "env": {
        "API_BASE_URL": "${INTERNAL_API_URL}",
        "API_KEY": "${INTERNAL_API_KEY}"
      }
    }
  }
}
```

**Key points:**
- `${VARIABLE_NAME}` expands from environment — never commit actual credentials
- All configured servers are discovered at connection time and available simultaneously
- Use `npx -y` for community servers (auto-install)

### Community vs. Custom MCP Servers

| Situation | Recommendation |
|---|---|
| Standard integration (GitHub, Jira, Slack, Postgres) | Use existing community server |
| Team-specific workflow, proprietary system | Build custom server |
| Existing community server doesn't quite fit | Contribute to community server; only fork as last resort |

### MCP Resources

Resources expose content catalogs — lists of available data — without requiring
exploratory tool calls. Instead of Claude calling `list_issues()` to discover what's
available, an MCP resource pre-exposes the catalog.

```python
# Without resources: Claude must explore
# Claude calls: list_projects() → list_repos() → list_issues() → finally reads issue

# With resources: catalog is pre-exposed
# Claude sees: Resource "issues" → [{id: 123, title: "Bug in auth"}, ...]
# Claude reads: read_issue(123) directly — skips 3 exploratory calls
```

Use MCP resources for: issue summaries, documentation hierarchies, database schemas,
API endpoint catalogs.

---

## Task Statement 2.5 — Built-in Tools: Read, Write, Edit, Bash, Grep, Glob

### Tool Selection Matrix

| Task | Correct Tool | Why |
|---|---|---|
| Search file contents for a pattern | **Grep** | Content search across files |
| Find files by name/extension | **Glob** | Path pattern matching |
| Read a full file | **Read** | Full file content |
| Make a targeted change to a file | **Edit** | Unique text match → replace |
| Edit fails (non-unique text) | **Read + Write** | Full file rewrite fallback |
| Run a shell command | **Bash** | Execution environment |

### The Grep vs. Glob Decision

This trips people up. Remember:
- **Grep**: searching *inside* files (content)
- **Glob**: searching *for* files (names/paths)

```python
# Find all callers of process_payment() → GREP (searching content)
# grep pattern="process_payment" glob="**/*.py"

# Find all test files → GLOB (searching paths)
# glob pattern="**/*.test.tsx"

# Find all files that import 'stripe' → GREP (searching content)
# grep pattern="import.*stripe" type="py"

# Find all Python files in the src directory → GLOB (searching paths)
# glob pattern="src/**/*.py"
```

### Edit vs. Read+Write

```python
# Edit: use when you have unique anchor text
# edit(file="auth.py", old_string="def verify_token(token):", new_string="def verify_token(token: str) -> bool:")

# Read+Write: use when Edit fails due to non-unique text
# If the file has 3 functions all starting with "def verify_"
# Read the full file, modify in memory, Write the complete new version
```

### Incremental Codebase Understanding

Don't read all files upfront — it floods context. Build understanding incrementally:

```
1. Grep for entry points (e.g., "if __name__ == '__main__'" or "app.run")
2. Read the entry point file
3. Grep for imports to find dependencies
4. Read key dependency files
5. Trace the specific flow you need to understand
```

---

## Key Concepts Summary — Domain 2

| Concept | What to Know |
|---|---|
| Tool description quality | 5 elements: what, when, inputs, outputs, edge cases |
| Overlapping tools | Rename + clarify descriptions to eliminate ambiguity |
| Splitting tools | Generic → purpose-specific tools with defined contracts |
| Error categories | transient/validation/permission/business |
| isRetryable | Most important error field — determines recovery strategy |
| Empty results vs. failure | Must be distinguishable in error response |
| Local recovery | Subagents recover transient errors locally before propagating |
| Tool count | Fewer tools per agent = better selection reliability |
| tool_choice | auto / any / forced — know when to use each |
| MCP scope | .mcp.json = team (committed); ~/.claude.json = personal (not committed) |
| MCP resources | Pre-expose content catalogs to reduce exploratory calls |
| Grep vs. Glob | Grep = content search; Glob = path/name search |

---

## What the Exam Will Test You On

- *"Tool calls are being misrouted between two tools with similar names. Fix it."*
  → Rename tools and rewrite descriptions to eliminate overlap

- *"A subagent returns `{results: []}` for both empty queries AND access failures. Why is this a problem?"*
  → Coordinator cannot distinguish "no data" from "query failed" — cannot make recovery decisions

- *"You need guaranteed structured output from Claude. Which tool_choice setting?"*
  → `"any"` (must call a tool) or forced (must call specific tool)

- *"Where do you configure a shared GitHub MCP server for your team?"*
  → `.mcp.json` in the project root with `${GITHUB_TOKEN}` env expansion

- *"Claude keeps using Grep to find test files instead of Glob. What's wrong?"*
  → Glob is for path/name matching; Grep is for content. Wrong tool for the task.
