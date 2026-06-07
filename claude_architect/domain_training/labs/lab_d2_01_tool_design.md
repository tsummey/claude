# Lab D2-01: Tool Design & MCP Configuration
### Domain 2 | Task Statements 2.1, 2.3, 2.4 | Estimated Time: 50 minutes

---

## Objective

Design and test effective tool interfaces. You will start with broken tool descriptions
that cause misrouting, diagnose the failures, then fix them. You will also configure
a multi-tool agent with scoped toolsets and implement a `.mcp.json` configuration.

---

## Setup

Create: `C:\Users\tsummey\projects\claude\claude_architect\labs\lab_d2_01_work.py`

---

## Part 1: Diagnose and Fix Ambiguous Tool Descriptions (20 minutes)

The following system has two tools with overlapping descriptions. Claude
frequently calls the wrong one.

### The Broken System

```python
import anthropic
import json

client = anthropic.Anthropic()

# These descriptions are deliberately broken — they cause misrouting
BROKEN_TOOLS = [
    {
        "name": "analyze_content",
        "description": "Analyzes content and returns structured results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Content to analyze"}
            },
            "required": ["content"]
        }
    },
    {
        "name": "analyze_document",
        "description": "Analyzes document content and returns structured results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Document content to analyze"}
            },
            "required": ["content"]
        }
    }
]

# Mock implementations
def analyze_content(content: str) -> dict:
    """Processes web search results."""
    return {
        "type": "web_analysis",
        "urls_found": 3,
        "titles": ["Article 1", "Article 2", "Article 3"],
        "summary": f"Found 3 web results for: {content[:50]}"
    }

def analyze_document(content: str) -> dict:
    """Processes PDF/document content."""
    return {
        "type": "document_analysis",
        "pages_analyzed": 12,
        "key_sections": ["Introduction", "Methods", "Results"],
        "summary": f"Document analysis of {len(content)} characters"
    }

def execute_tool_broken(tool_name: str, tool_input: dict) -> str:
    if tool_name == "analyze_content":
        return json.dumps(analyze_content(tool_input.get("content", "")))
    elif tool_name == "analyze_document":
        return json.dumps(analyze_document(tool_input.get("content", "")))
    return json.dumps({"error": "unknown tool"})


def test_tool_selection(query: str, tools: list, label: str) -> str:
    """Send a query and report which tool Claude selected."""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=512,
        tools=tools,
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": query}]
    )

    for block in response.content:
        if block.type == "tool_use":
            print(f"  [{label}] Query: '{query[:60]}...' → Tool selected: {block.name}")
            return block.name

    return "no_tool_called"
```

### Test the Broken System

```python
# These queries have OBVIOUS correct answers — but broken descriptions cause misrouting
test_queries = [
    "Here are the web search results I got: [title: 'AI News', url: 'example.com', excerpt: '...']",
    "Please analyze this PDF document: [Introduction: This paper examines...]",
    "I have search results from Google about climate change: result 1, result 2, result 3",
    "This academic paper from NBER discusses economic impacts: Abstract: We find that..."
]

print("=== BROKEN TOOL DESCRIPTIONS ===")
broken_selections = {}
for query in test_queries:
    selected = test_tool_selection(query, BROKEN_TOOLS, "BROKEN")
    broken_selections[query[:40]] = selected

print(f"\nMisrouting analysis: {broken_selections}")
```

### Fix the Tool Descriptions

Write improved descriptions for both tools using the 5-element framework
(what, when, inputs, outputs, edge cases):

```python
# YOUR TASK: Rewrite these descriptions to eliminate misrouting
FIXED_TOOLS = [
    {
        "name": "extract_web_results",  # Renamed to reflect actual purpose
        "description": """[YOUR IMPROVED DESCRIPTION HERE]
        
        Hint: Include:
        - What it does (processes web search output specifically)
        - When to use it (vs. the document tool)
        - What input format it expects (raw search API output)
        - What it returns (list of title/url/excerpt objects)
        - What NOT to use it for (PDF documents, database records)
        """,
        "input_schema": {
            "type": "object",
            "properties": {
                "raw_search_output": {
                    "type": "string",
                    "description": "[YOUR INPUT DESCRIPTION]"
                }
            },
            "required": ["raw_search_output"]
        }
    },
    {
        "name": "analyze_pdf_document",  # Renamed to reflect actual purpose
        "description": """[YOUR IMPROVED DESCRIPTION HERE]
        
        Hint: Include:
        - What it does (deep analysis of document/paper content)
        - When to use it (for PDFs, papers, reports — not web search)
        - What input format it expects
        - What it returns (sections, key findings, methodology)
        - What NOT to use it for
        """,
        "input_schema": {
            "type": "object",
            "properties": {
                "document_content": {
                    "type": "string",
                    "description": "[YOUR INPUT DESCRIPTION]"
                }
            },
            "required": ["document_content"]
        }
    }
]

# Update mock implementations to match new names
def execute_tool_fixed(tool_name: str, tool_input: dict) -> str:
    if tool_name == "extract_web_results":
        return json.dumps(analyze_content(tool_input.get("raw_search_output", "")))
    elif tool_name == "analyze_pdf_document":
        return json.dumps(analyze_document(tool_input.get("document_content", "")))
    return json.dumps({"error": "unknown tool"})
```

### Test the Fixed System

```python
print("\n=== FIXED TOOL DESCRIPTIONS ===")
fixed_selections = {}
for query in test_queries:
    selected = test_tool_selection(query, FIXED_TOOLS, "FIXED")
    fixed_selections[query[:40]] = selected

# Compare: how many misroutings were eliminated?
print("\n=== COMPARISON ===")
for key in broken_selections:
    broken = broken_selections[key]
    fixed = fixed_selections.get(key, "N/A")
    status = "✅ Fixed" if broken != fixed else "⚠️ Still misrouting"
    print(f"  {status}: '{key}'")
    print(f"    Before: {broken} | After: {fixed}")
```

---

## Part 2: Scoped Toolsets Per Agent (15 minutes)

Build a coordinator that gives each subagent only the tools it needs.

```python
# Full tool catalog
ALL_TOOLS = [
    # Search tools
    {"name": "web_search", "description": "Search the web for information",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "fetch_url", "description": "Fetch the content of a specific URL",
     "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
    # Analysis tools
    {"name": "extract_data_points", "description": "Extract structured data points from document",
     "input_schema": {"type": "object", "properties": {"document": {"type": "string"}}, "required": ["document"]}},
    {"name": "summarize_content", "description": "Generate a summary of document content",
     "input_schema": {"type": "object", "properties": {"content": {"type": "string"}}, "required": ["content"]}},
    {"name": "verify_claim", "description": "Verify a specific claim against a source document",
     "input_schema": {"type": "object", "properties": {"claim": {"type": "string"}, "source": {"type": "string"}}, "required": ["claim", "source"]}},
    # Synthesis tools
    {"name": "verify_fact", "description": "Quick fact verification for synthesis (dates, names, statistics)",
     "input_schema": {"type": "object", "properties": {"fact": {"type": "string"}}, "required": ["fact"]}},
    {"name": "compile_report", "description": "Compile final research report from findings",
     "input_schema": {"type": "object", "properties": {"findings": {"type": "string"}}, "required": ["findings"]}},
    # Coordinator tools
    {"name": "Task", "description": "Spawn a subagent to handle a specific task",
     "input_schema": {"type": "object", "properties": {"agent": {"type": "string"}, "instructions": {"type": "string"}}, "required": ["agent", "instructions"]}},
    {"name": "evaluate_coverage", "description": "Evaluate if research covers all required topics",
     "input_schema": {"type": "object", "properties": {"research": {"type": "string"}, "required_topics": {"type": "array", "items": {"type": "string"}}}, "required": ["research", "required_topics"]}},
]

# YOUR TASK: Build scoped toolsets following the principle of least privilege
# Each agent should have ONLY the tools it needs

AGENT_TOOLSETS = {
    "coordinator": [
        # Should have: Task (to spawn subagents), evaluate_coverage
        # Should NOT have: web_search, extract_data_points (those are for subagents)
        # YOUR CODE HERE
    ],
    "search_agent": [
        # Should have: web_search, fetch_url
        # Should NOT have: compile_report, Task, verify_claim (not its job)
        # YOUR CODE HERE
    ],
    "analysis_agent": [
        # Should have: extract_data_points, summarize_content, verify_claim
        # Should NOT have: web_search, Task, compile_report
        # YOUR CODE HERE
    ],
    "synthesis_agent": [
        # Should have: verify_fact (for 85% of simple verifications), compile_report
        # Should NOT have: web_search (complex searches go through coordinator)
        # YOUR CODE HERE
    ]
}

def get_agent_tools(agent_name: str) -> list:
    """Return scoped toolset for an agent."""
    tool_names = AGENT_TOOLSETS.get(agent_name, [])
    return [t for t in ALL_TOOLS if t["name"] in tool_names]

# Verify your scoping
print("\n=== AGENT TOOLSETS ===")
for agent, tool_names in AGENT_TOOLSETS.items():
    tools = get_agent_tools(agent)
    print(f"  {agent}: {[t['name'] for t in tools]}")
    print(f"    Tool count: {len(tools)} (ideal: 2-5)")
```

---

## Part 3: Configure .mcp.json (15 minutes)

Create a `.mcp.json` for a team project that uses GitHub, a custom internal API,
and a Postgres database MCP server.

```json
// Create: C:\Users\tsummey\projects\claude\claude_architect\labs\sample.mcp.json
// (Review only — don't actually run this without real credentials)
```

```python
import json

# Build the .mcp.json configuration
mcp_config = {
    "mcpServers": {
        # YOUR TASK 1: Configure the GitHub MCP server
        # - Uses community server: @modelcontextprotocol/server-github
        # - Requires GITHUB_TOKEN environment variable
        # - Command: npx -y
        "github": {
            # YOUR CODE HERE
        },

        # YOUR TASK 2: Configure a custom internal API server
        # - Local Python script: ./tools/internal_api_server.py
        # - Requires API_BASE_URL and API_KEY environment variables
        "internal-api": {
            # YOUR CODE HERE
        },

        # YOUR TASK 3: Configure Postgres MCP server
        # - Community server: @modelcontextprotocol/server-postgres
        # - Requires DATABASE_URL environment variable
        # - This should be PROJECT-scoped (shared with team) not user-scoped
        "database": {
            # YOUR CODE HERE
        }
    }
}

# Validate your config structure
print("\n=== MCP CONFIG VALIDATION ===")
for server_name, config in mcp_config["mcpServers"].items():
    has_command = "command" in config
    has_env_expansion = any("${" in str(v) for v in config.get("env", {}).values())
    has_no_plaintext_secrets = not any(
        len(str(v)) > 20 and "${" not in str(v)
        for v in config.get("env", {}).values()
    )

    print(f"\n  {server_name}:")
    print(f"    Has command: {has_command}")
    print(f"    Uses env expansion: {has_env_expansion}")
    print(f"    No plaintext secrets: {has_no_plaintext_secrets}")

    if not has_env_expansion:
        print(f"    ⚠️  WARNING: Credentials should use ${{VAR}} syntax, not plaintext!")

# Print the final config
print("\n=== FINAL .mcp.json ===")
print(json.dumps(mcp_config, indent=2))
```

---

## Reflection Questions

```python
"""
REFLECTION:

1. What specifically made the broken tool descriptions cause misrouting?
   What was the key difference in your fixed descriptions?
   Answer:

2. The synthesis agent gets verify_fact but routes complex verifications through
   the coordinator. Why is this better than either:
   a) giving it all web search tools, OR
   b) routing ALL verifications through the coordinator?
   Answer:

3. In .mcp.json, you used ${GITHUB_TOKEN} instead of the actual token.
   What would happen if you committed the actual token to the repo?
   What's the correct way to set up the environment variable?
   Answer:

4. Should the .mcp.json you created be committed to version control? Why?
   What about a developer's personal Postgres connection to their local dev database?
   Answer:

5. If you add a new MCP server tomorrow and a teammate pulls the repo,
   do they automatically get access to the new server? What do they need?
   Answer:
"""
```

---

## Completion Criteria

✅ Broken tool misrouting identified and fixed with improved descriptions
✅ Agent toolsets are scoped — each agent has only what it needs
✅ .mcp.json configured with env variable expansion (no plaintext credentials)
✅ All reflection questions answered

---

*Next Lab: D2-02 — Structured Error Responses*
