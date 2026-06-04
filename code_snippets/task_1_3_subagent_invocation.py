import anthropic
from dotenv import load_dotenv

# Load ANTHROPIC_API_KEY from .env file into the environment.
# Without this, client = anthropic.Anthropic() won't find the key.
load_dotenv()

# Create the Anthropic client. It automatically reads ANTHROPIC_API_KEY
# from the environment loaded above.
client = anthropic.Anthropic()

# stop_reason      When it fires
#-----------------------------------------------------------------------
# "end_turn"       Claude finished normally — your primary exit signal
# "tool_use"       Claude wants to call a tool — execute it and loop again
# "max_tokens"     Response hit the max_tokens limit and got cut off
# "stop_sequence"  Claude generated a custom stop sequence you defined

# =============================================================================
# SUBAGENT INVOCATION — CONTEXT PASSING AND SPAWNING
# =============================================================================
#
# This file focuses on Task Statement 1.3:
#   1. The Task tool     — how subagents are spawned
#   2. Context passing   — the right and wrong way
#   3. Parallel spawning — multiple Task calls in one coordinator response
#
# The single most important rule:
#   Subagents have ISOLATED context. They start completely fresh.
#   They cannot see the coordinator's messages history.
#   Everything they need MUST be passed explicitly in their prompt.
#
# Diagnostic question to always ask before invoking a subagent:
#   "If this subagent just walked in the door knowing nothing,
#    does it have everything it needs to do its job?"
#   If the answer is no — add more context.
# =============================================================================


# =============================================================================
# THE TASK TOOL — CRITICAL REQUIREMENT
# =============================================================================
#
# In the Claude Agent SDK, subagents are spawned using the Task tool.
# The coordinator's allowedTools MUST explicitly include "Task".
# Without it, subagent spawning fails silently — no error is thrown,
# it simply doesn't work.
#
# ❌ BROKEN — coordinator cannot spawn subagents
# coordinator_tools = ["summarize", "evaluate_coverage"]
#
# ✅ CORRECT — "Task" enables subagent spawning
# coordinator_tools = ["Task", "summarize", "evaluate_coverage"]
#
# Rule: Give each agent the MINIMUM tools required for its role.
# More tools = worse tool selection reliability.
# Fewer tools per agent = better, more focused decisions.
# =============================================================================

# Coordinator tool list — "Task" must be present to spawn subagents
COORDINATOR_TOOLS = ["Task", "summarize", "evaluate_coverage"]

# Subagent tool lists — scoped to each agent's specific role only
# Search agent only needs search-related tools
SEARCH_AGENT_TOOLS = ["web_search", "fetch_url", "filter_results"]

# Analysis agent only needs document analysis tools
ANALYSIS_AGENT_TOOLS = ["read_document", "extract_data", "verify_claim"]

# Synthesis agent gets verify_fact for 85% of simple lookups.
# Complex verifications (15%) still route through the coordinator.
# This eliminates unnecessary round trips for the common case.
SYNTHESIS_AGENT_TOOLS = ["verify_fact", "compile_report", "format_output"]


# =============================================================================
# CONTEXT PASSING — RIGHT VS WRONG
# =============================================================================

def invoke_subagent_WRONG(synthesis_agent_fn, prior_results: dict) -> dict:
    """
    ❌ WRONG — implicit context passing.

    The coordinator has all the context but passes none of it.
    The synthesis agent receives "Synthesize the research findings"
    with no actual findings attached. It has no idea what findings
    exist, what the original query was, or what quality standard to meet.

    Result: generic output, hallucinated sources, or empty report.
    This is the single most common mistake in multi-agent systems.
    """
    return synthesis_agent_fn({
        "instruction": "Synthesize the research findings"
        # ❌ What findings? The subagent has no idea.
        # ❌ What was the original query? Unknown.
        # ❌ What quality criteria? Unknown.
        # ❌ What sources were found? Unknown.
    })


def invoke_subagent_CORRECT(synthesis_agent_fn,
                             original_query: str,
                             web_search_findings: str,
                             doc_findings: str,
                             source_metadata: list) -> dict:
    """
    ✅ CORRECT — explicit context injection.

    Everything the synthesis agent needs is explicitly passed.
    It can walk in the door knowing nothing and still do its job
    because all required context is provided upfront.

    Args:
        synthesis_agent_fn:   The function that runs the synthesis subagent
        original_query:       The user's original research question
        web_search_findings:  Results returned by the web search subagent
        doc_findings:         Results returned by the document analysis subagent
        source_metadata:      Attribution data — URLs, titles, publication dates
    """
    return synthesis_agent_fn({
        "instruction": "Synthesize the following research findings into a comprehensive report",

        # ✅ Original query — subagent knows what question it's answering
        "research_query": original_query,

        # ✅ Actual findings — passed from coordinator variables where they
        # were stored after the search and analysis agents completed.
        # These exist in coordinator memory but mean NOTHING to the subagent
        # unless explicitly included here.
        "web_search_results": web_search_findings,
        "document_analysis_results": doc_findings,

        # ✅ Source metadata — attribution preserved through synthesis.
        # Without this, the synthesis agent cannot cite sources correctly.
        "source_metadata": {
            "sources": source_metadata
            # Example entry:
            # {"url": "https://...", "title": "...", "date": "2024-01-15"}
        },

        # ✅ Quality criteria — defines what a good output looks like.
        # Without this the subagent decides for itself what "good" means.
        "quality_criteria": (
            "Cite every claim with its source. "
            "Flag conflicting findings between sources. "
            "Note coverage gaps where sources were unavailable."
        )
    })


# =============================================================================
# PARALLEL VS SEQUENTIAL SPAWNING
# =============================================================================
#
# Parallel:   Multiple Task tool calls in ONE coordinator response turn.
#             All subagents run simultaneously.
#             Use when: subagents are independent (don't need each other's results)
#
# Sequential: One Task tool call per coordinator response turn.
#             Each subagent waits for the previous to finish.
#             Use when: subagent B depends on subagent A's results.
#
# The exam trap: parallel is NOT always better.
# If synthesis needs search results, they MUST be sequential.
# Running them in parallel means synthesis has nothing to work with.
# =============================================================================

def demonstrate_parallel_spawning():
    """
    ✅ PARALLEL — independent subtopics run simultaneously.

    In the Claude Agent SDK, this means emitting multiple Task tool calls
    in a SINGLE coordinator response. The coordinator waits for ALL results
    before proceeding.

    Use when: subtopics are independent of each other.
    """

    # In the SDK, the coordinator's response.content would look like this —
    # multiple Task tool calls emitted in ONE response turn:
    parallel_task_calls = [
        # All three run simultaneously — coordinator waits for all
        {"type": "tool_use", "name": "Task",
         "input": {"agent": "web_search_agent", "query": "AI in music"}},

        {"type": "tool_use", "name": "Task",
         "input": {"agent": "web_search_agent", "query": "AI in film"}},

        {"type": "tool_use", "name": "Task",
         "input": {"agent": "web_search_agent", "query": "AI in writing"}},
    ]

    # WHY parallel works here:
    # "AI in music" search doesn't need "AI in film" results to run.
    # "AI in film" search doesn't need "AI in writing" results to run.
    # All three are completely independent — parallel saves time.
    return parallel_task_calls


def demonstrate_sequential_spawning():
    """
    ✅ SEQUENTIAL — synthesis depends on search, must run after.

    Search and synthesis CANNOT run in parallel because synthesis
    needs search results to exist before it can do anything useful.

    Running them in parallel means synthesis starts with no data
    and produces a generic report — same failure as wrong context passing.
    """

    # Step 1 — Search runs first, result stored in variable
    # (In real code this would be an actual invoke_subagent call)
    search_result = {
        "status": "success",
        "result": "Search findings about AI in music...",
        "agent": "web_search_agent"
    }
    # search_result is now in coordinator memory

    # Step 2 — Synthesis runs AFTER search, receives search result explicitly
    # Cannot run until Step 1 is complete and search_result exists
    synthesis_input = {
        "instruction": "Synthesize the research into a comprehensive report",

        # ✅ search_result explicitly passed — subagent isolation means
        # synthesis has no other way to know this exists
        "search_findings": search_result.get("result"),
        "research_query": "AI in music",
        "quality_criteria": "Cite every claim. Flag conflicting findings."
    }

    return synthesis_input


# =============================================================================
# COMPLETE SUBAGENT INVOCATION EXAMPLE
# =============================================================================

def run_subagent(agent_name: str, system_prompt: str,
                 context: dict, tools: list = None) -> dict:
    """
    Invoke a subagent with its own isolated agentic loop.

    Key points:
    - Subagent has its OWN messages list — separate from coordinator
    - Subagent loop runs until stop_reason == "end_turn"
    - Result returned to coordinator as a dict stored in a variable
    - Subagent never appends to coordinator's messages list
    - Subagent never communicates with other subagents directly (Rule 2)

    Args:
        agent_name:    Name for logging/debugging
        system_prompt: Defines the subagent's role
        context:       Everything the subagent needs — explicitly passed
        tools:         Scoped toolset — only what this agent needs

    Returns:
        dict — success with result, or structured error for coordinator to handle
    """
    if tools is None:
        tools = []

    # Build prompt from context dict — explicit context injection.
    # Every key/value becomes part of the subagent's starting prompt.
    # This replaces the implicit shared history that doesn't exist.
    prompt_parts = []
    for key, value in context.items():
        prompt_parts.append(f"{key.upper()}:\n{value}")
    subagent_prompt = "\n\n".join(prompt_parts)

    # ✅ Subagent's OWN isolated messages list — starts fresh every time.
    # NOT the coordinator's messages list. Has no knowledge of prior
    # conversations unless that knowledge is passed via context above.
    messages = [{"role": "user", "content": subagent_prompt}]

    # Subagent's own agentic loop — same stop_reason pattern as base loop.
    # Exits when Claude sets stop_reason == "end_turn".
    # Returns result to coordinator — never touches coordinator's messages.
    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=system_prompt,
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            # Subagent done — return result to coordinator.
            # Coordinator stores this in a variable.
            # Coordinator decides what to do with it next.
            for block in response.content:
                if hasattr(block, "text"):
                    return {
                        "status": "success",
                        "result": block.text,
                        "agent": agent_name
                    }
            return {"status": "success", "result": "", "agent": agent_name}

        elif response.stop_reason == "tool_use":
            # Same two-append pattern as agentic_loop_base.py.
            # ✅ Step 1 — append subagent's tool call REQUEST first
            messages.append({"role": "assistant", "content": response.content})

            # ✅ Step 2 — execute tools and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    # Subagent only has access to its scoped tools —
                    # not all tools in the system
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })

            # ✅ Step 3 — append tool results SECOND
            messages.append({"role": "user", "content": tool_results})

        else:
            # Structured error — never return empty results for failures.
            # Empty results look like "no data" to the coordinator.
            # Structured errors let the coordinator make recovery decisions:
            # retry, skip and annotate, or escalate.
            return {
                "status": "error",
                "agent": agent_name,
                "isError": True,
                "errorType": "unexpected_stop",
                "message": f"Unexpected stop_reason: {response.stop_reason}",
                "isRetryable": False,
                "partialResults": []
            }


def execute_tool(tool_name: str, tool_input: dict):
    """
    Placeholder for tool execution.
    Replace with actual tool logic per subagent role.
    Each subagent only calls tools from its own scoped toolset.
    """
    pass


# Sanity check — only runs when this file is executed directly.
# Demonstrates context passing by invoking a simple subagent
# with explicit context and printing the result.
if __name__ == "__main__":

    SIMPLE_AGENT_SYSTEM = "You are a helpful research assistant. Answer the question provided."

    result = run_subagent(
        agent_name="test_agent",
        system_prompt=SIMPLE_AGENT_SYSTEM,
        context={
            # ✅ Explicit context — everything the subagent needs
            "research_query": "What is the impact of AI on the music industry?",
            "instructions": "Provide a 2-3 sentence summary answer.",
            "quality_criteria": "Be concise and factual."
        },
        tools=[]
    )

    print(f"Agent: {result['agent']}")
    print(f"Status: {result['status']}")
    print(f"Result: {result['result']}")
