# Lab D1-02: Multi-Agent Research System
### Domain 1 | Task Statements 1.2, 1.3 | Estimated Time: 60 minutes

---

## Objective

Build the multi-agent research system from Scenario 3. A coordinator agent delegates
to specialized subagents, passes context explicitly, runs subagents in parallel, and
performs iterative refinement. You will experience firsthand why subagent context
isolation is the #1 source of bugs in multi-agent systems.

---

## Prerequisites

- Completed Lab D1-01
- Understanding of the agentic loop
- `ANTHROPIC_API_KEY` in environment

---

## Setup

Create: `C:\Users\tsummey\projects\claude\claude_architect\labs\lab_d1_02_work.py`

---

## The System You're Building

```
User Query: "Impact of remote work on urban real estate markets"
     │
     ▼
┌─────────────────────┐
│    COORDINATOR      │  ← Decomposes, delegates, aggregates
└──────────┬──────────┘
           │  (parallel Task calls)
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌────────┐   ┌──────────┐
│SEARCH  │   │ DOCUMENT │   ← Specialized, scoped tools
│AGENT   │   │ ANALYSIS │
└────────┘   └──────────┘
    │             │
    └──────┬──────┘
           ▼
    ┌─────────────┐
    │  SYNTHESIS  │   ← Receives explicit context from coordinator
    │    AGENT    │
    └─────────────┘
           │
           ▼
     Final Report
```

---

## Part 1: Build the Foundation (20 minutes)

### Mock Data (simulating external sources)

```python
import anthropic
import json
from typing import Optional

client = anthropic.Anthropic()

# Simulated search results
MOCK_SEARCH_RESULTS = {
    "remote work urban real estate": [
        {
            "title": "Remote Work Exodus: Cities Losing Downtown Tenants",
            "url": "https://realestate-journal.com/remote-work-exodus",
            "date": "2024-02-15",
            "excerpt": "Office vacancy rates in major CBDs hit 22% in Q4 2023, "
                      "highest since 2008. San Francisco leads with 31% vacancy."
        },
        {
            "title": "Suburban Migration Accelerates Post-Pandemic",
            "url": "https://urban-studies.org/suburban-migration-2024",
            "date": "2024-01-28",
            "excerpt": "Suburban home prices up 18% since 2020 as remote workers "
                      "prioritize space over commute proximity."
        },
        {
            "title": "Mixed-Use Conversions: Offices Becoming Apartments",
            "url": "https://architecture-today.com/office-conversion-trend",
            "date": "2024-03-01",
            "excerpt": "NYC approved 14 office-to-residential conversions in 2023, "
                      "adding 2,800 units to housing supply."
        }
    ],
    "remote work commercial real estate impact": [
        {
            "title": "CBRE Report: The New Office Landscape 2024",
            "url": "https://cbre.com/research/office-landscape-2024",
            "date": "2024-02-20",
            "excerpt": "Hybrid work (2-3 days office) now standard at 67% of Fortune 500. "
                      "Average office footprint reduced 23% vs 2019."
        }
    ]
}

MOCK_DOCUMENTS = {
    "suburban_housing_study.pdf": {
        "content": "Federal Reserve study (2023): Remote work capability adds $10,000-$25,000 "
                  "premium to suburban home values within 90-minute commute zones. "
                  "Effect strongest in markets with good broadband infrastructure.",
        "date": "2023-11-15",
        "source": "Federal Reserve Bank of Atlanta"
    },
    "urban_density_report.pdf": {
        "content": "Brookings Institution (2024): 18 of top 25 US cities show declining "
                  "population density in core zip codes since 2020. Counter-trend: "
                  "luxury high-rise construction continues in Manhattan and Miami.",
        "date": "2024-01-10",
        "source": "Brookings Institution"
    }
}
```

### Subagent Tool Implementations

```python
def web_search_agent(query: str, num_results: int = 5) -> dict:
    """
    Simulates a web search subagent.
    In production, this would call a real search API.
    """
    results = []
    for key, value in MOCK_SEARCH_RESULTS.items():
        if any(word in query.lower() for word in key.split()):
            results.extend(value)

    if not results:
        return {
            "status": "no_results",
            "query": query,
            "results": []
        }

    return {
        "status": "success",
        "query": query,
        "results": results[:num_results],
        "result_count": len(results[:num_results])
    }


def document_analysis_agent(document_name: str, analysis_focus: str) -> dict:
    """
    Simulates a document analysis subagent.
    """
    doc = MOCK_DOCUMENTS.get(document_name)
    if not doc:
        return {
            "status": "error",
            "error_category": "validation",
            "message": f"Document '{document_name}' not found",
            "isRetryable": False
        }

    # In production: Claude would actually analyze the document
    return {
        "status": "success",
        "document": document_name,
        "source": doc["source"],
        "date": doc["date"],
        "analysis_focus": analysis_focus,
        "key_findings": doc["content"],
        "confidence": "high"
    }


def execute_subagent(agent_name: str, agent_input: dict) -> str:
    """Route tool calls to the appropriate subagent."""
    if agent_name == "web_search_agent":
        result = web_search_agent(
            query=agent_input.get("query", ""),
            num_results=agent_input.get("num_results", 5)
        )
    elif agent_name == "document_analysis_agent":
        result = document_analysis_agent(
            document_name=agent_input.get("document_name", ""),
            analysis_focus=agent_input.get("analysis_focus", "")
        )
    else:
        result = {"error": f"Unknown agent: {agent_name}"}

    return json.dumps(result, indent=2)
```

### Coordinator Tool Definitions

```python
COORDINATOR_TOOLS = [
    {
        "name": "web_search_agent",
        "description": "Searches the web for current news, articles, and data on a topic. "
                      "Returns article titles, URLs, publication dates, and excerpts. "
                      "Use for: finding recent statistics, news coverage, expert opinions, "
                      "market reports. Input must be a specific, focused search query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Specific search query. Be precise — broad queries return noise."
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-10, default 5)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "document_analysis_agent",
        "description": "Analyzes a specific research document or report in depth. "
                      "Returns key findings, methodology notes, and source attribution. "
                      "Use for: academic papers, government reports, industry studies. "
                      "Requires knowing the document name in advance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_name": {
                    "type": "string",
                    "description": "Name of the document to analyze"
                },
                "analysis_focus": {
                    "type": "string",
                    "description": "What aspect to focus the analysis on"
                }
            },
            "required": ["document_name", "analysis_focus"]
        }
    }
]
```

---

## Part 2: The Broken Coordinator — Context Isolation Bug (15 minutes)

Build this version first. It has the most common multi-agent bug.

```python
COORDINATOR_SYSTEM_BROKEN = """You are a research coordinator. Research the given topic
and produce a comprehensive report. Use web_search_agent to find information and
document_analysis_agent for detailed document analysis."""

def run_coordinator_broken(research_query: str) -> str:
    """
    BROKEN: This coordinator does NOT pass findings to the synthesis step.
    The synthesis will have no context — demonstrates context isolation failure.
    """
    messages = [{"role": "user", "content": research_query}]

    # Phase 1: Gather research (this part works)
    all_findings = []
    search_queries = [
        f"remote work urban real estate markets",
        f"remote work commercial real estate impact"
    ]

    for query in search_queries:
        result = web_search_agent(query)
        all_findings.append(result)
        print(f"Search complete: {query}")

    doc_result = document_analysis_agent(
        "suburban_housing_study.pdf",
        "impact on suburban home values"
    )
    all_findings.append(doc_result)
    print(f"Document analysis complete")

    # Phase 2: Ask Claude to synthesize — BUT WITHOUT PASSING THE FINDINGS
    # This is the bug: we gathered findings but never gave them to Claude
    synthesis_prompt = """Based on your research, synthesize the key findings about
    the impact of remote work on urban real estate markets. Include statistics,
    trends, and source citations."""
    # NOTE: all_findings is never included in the messages!

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        system=COORDINATOR_SYSTEM_BROKEN,
        messages=[{"role": "user", "content": synthesis_prompt}]
        # Claude has NO access to all_findings
    )

    return response.content[0].text
```

**Run this and observe:** What does Claude say when asked to synthesize findings
it has never seen? Does it hallucinate statistics? Does it admit it has no data?

**Record your observation:**
```python
"""
OBSERVATION from broken coordinator:
Claude responded with: [paste response here]
The problem: [describe what went wrong]
"""
```

---

## Part 3: The Correct Coordinator — Explicit Context Passing (25 minutes)

```python
COORDINATOR_SYSTEM = """You are a research coordinator managing a multi-agent research pipeline.

Your responsibilities:
1. Decompose the research query into comprehensive subtopics — do not miss major areas
2. Delegate each subtopic to the appropriate specialized agent
3. Collect and review ALL findings before requesting synthesis
4. Evaluate synthesis output for coverage gaps — re-delegate if needed
5. Ensure every claim in the final report has source attribution

Quality standards:
- Every factual claim must cite a specific source with date
- Conflicting data from different sources must be noted, not resolved arbitrarily
- Coverage gaps must be explicitly flagged in the report"""

def run_coordinator_correct(research_query: str) -> str:
    """
    CORRECT: Explicit context passing at every handoff.
    Demonstrates proper multi-agent coordination.
    """
    print(f"\n{'='*70}")
    print(f"COORDINATOR: Starting research on: {research_query}")
    print(f"{'='*70}")

    messages = [{"role": "user", "content": f"Research this topic comprehensively: {research_query}"}]

    iteration = 0
    max_iterations = 15

    while iteration < max_iterations:
        iteration += 1

        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=COORDINATOR_SYSTEM,
            tools=COORDINATOR_TOOLS,
            messages=messages
        )

        print(f"\n[Iteration {iteration}] stop_reason: {response.stop_reason}")

        if response.stop_reason == "end_turn":
            print("\n✅ Coordinator complete")
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        elif response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  → Invoking {block.name}: {json.dumps(block.input)[:100]}")
                    result = execute_subagent(block.name, block.input)
                    print(f"  ← Result preview: {result[:150]}...")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            messages.append({"role": "user", "content": tool_results})

    return "Max iterations reached"
```

### Run and Compare

```python
if __name__ == "__main__":
    query = "What is the impact of remote work on urban real estate markets?"

    print("\n" + "="*70)
    print("RUNNING BROKEN COORDINATOR")
    print("="*70)
    broken_result = run_coordinator_broken(query)
    print(f"\nBroken result:\n{broken_result[:500]}")

    print("\n" + "="*70)
    print("RUNNING CORRECT COORDINATOR")
    print("="*70)
    correct_result = run_coordinator_correct(query)
    print(f"\nCorrect result:\n{correct_result[:1000]}")
```

---

## Part 4: Implement Parallel Subagent Spawning (bonus — 10 minutes)

The coordinator above calls subagents sequentially. Modify the correct coordinator's
system prompt to encourage spawning multiple searches simultaneously:

```python
COORDINATOR_SYSTEM_PARALLEL = COORDINATOR_SYSTEM + """

EFFICIENCY REQUIREMENT: When you have multiple independent search queries to run,
call web_search_agent multiple times IN THE SAME RESPONSE. Do not wait for one
search to complete before starting another if they are independent."""
```

Replace the system prompt and re-run. Observe whether the coordinator now emits
multiple tool calls in a single response (you'll see them grouped in the same iteration).

---

## Part 5: Reflection Questions

```python
"""
REFLECTION:

1. When you ran the broken coordinator, did Claude hallucinate statistics
   or did it acknowledge it had no data? What does this tell you about
   relying on Claude to "figure out" context it doesn't have?
   Answer:

2. In the correct coordinator, how many iterations did it take?
   Trace the message history: what was in each message?
   Answer:

3. In the parallel version, did the coordinator emit multiple tool calls
   in one response? If yes, what did the messages look like at that iteration?
   Answer:

4. If you needed the synthesis to cite which search query produced each result,
   what would you change about the tool result structure?
   Answer:

5. The coordinator's system prompt says "do not miss major areas."
   What would happen if the query was "AI in creative industries" and the
   coordinator decomposed it as: digital art, graphic design, photography?
   What exam concept does this illustrate?
   Answer:
"""
```

---

## Completion Criteria

✅ Broken coordinator runs and you've observed the context isolation failure
✅ Correct coordinator produces a sourced, multi-section research summary
✅ You understand why explicit context passing is non-negotiable
✅ All reflection questions answered
✅ (Bonus) Parallel spawning observed in action

---

*Next Lab: D1-03 — Programmatic Enforcement and Agent SDK Hooks*
