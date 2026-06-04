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
# MULTI-AGENT ORCHESTRATION — COORDINATOR + SUBAGENT PATTERN
# =============================================================================
#
# Architecture: Hub-and-spoke
#
#           ┌─────────────────────┐
#           │   COORDINATOR AGENT │
#           │  - Decomposes task  │
#           │  - Routes to agents │
#           │  - Aggregates results│
#           │  - Handles errors   │
#           └──────────┬──────────┘
#                      │
#      ┌───────────────┼───────────────┐
#      │               │               │
# ┌────▼─────┐   ┌─────▼────┐   ┌─────▼────┐
# │  SEARCH  │   │ DOCUMENT │   │SYNTHESIS │
# │  AGENT   │   │  AGENT   │   │  AGENT   │
# └──────────┘   └──────────┘   └──────────┘
#
# Four critical rules:
#   Rule 1 — Subagents have ISOLATED context. They start fresh every time.
#             They do NOT inherit the coordinator's messages history.
#             Everything a subagent needs MUST be passed explicitly in its prompt.
#             This is the single most common mistake in multi-agent systems.
#
#   Rule 2 — All communication routes through the coordinator.
#             Subagents NEVER talk to each other directly.
#             This gives you observability, consistent error handling,
#             and controlled information flow.
#
#   Rule 3 — The coordinator owns task decomposition.
#             If the coordinator decomposes too narrowly, subagents will
#             execute perfectly and still produce wrong/incomplete output.
#             Garbage decomposition in → garbage report out.
#
#   Rule 4 — The coordinator owns error handling.
#             Subagents handle transient failures locally (retry with backoff).
#             Everything else propagates back to the coordinator to decide:
#             retry, use partial results, skip and annotate, or escalate.
# =============================================================================


# =============================================================================
# SUBAGENT SYSTEM PROMPTS
# Each subagent has a focused role and clear instructions.
# System prompts define what the subagent does — context passed at
# invocation time defines what it works on.
# =============================================================================

SEARCH_AGENT_SYSTEM = """You are a web search specialist.
Search thoroughly for information on the given topic.
Return structured findings with source URLs and publication dates.
Do not synthesize or editorialize — return what the sources say."""

DOCUMENT_AGENT_SYSTEM = """You are a document analysis specialist.
Extract structured facts, data points, and key claims from documents.
Preserve source attribution for every claim.
Do not summarize — return structured findings."""

SYNTHESIS_AGENT_SYSTEM = """You are a research synthesis specialist.
Combine findings from multiple sources into a comprehensive report.
Cite every claim with its source. Flag conflicting findings.
Note any coverage gaps where sources were unavailable."""

COORDINATOR_SYSTEM = """You are a research coordinator.
Your job is to:
1. Analyze the research query and identify ALL relevant subtopics
2. Delegate each subtopic to the appropriate specialized subagent
3. Aggregate and synthesize results from all subagents
4. Identify coverage gaps and re-delegate targeted follow-up queries
5. Produce a comprehensive, well-cited final report

Always ensure your task decomposition covers the FULL scope of the query.
Do not proceed to synthesis until all major subtopics have been researched."""


def execute_subagent_tool(tool_name: str, tool_input: dict):
    """
    Placeholder for subagent tool execution.
    Each subagent only has access to its scoped toolset —
    not all tools in the system. Fewer tools = better tool selection.
    Replace with actual tool logic per subagent role.
    """
    pass


def invoke_subagent(agent_name: str, system_prompt: str,
                    context: dict, tools: list = None) -> dict:
    """
    Invoke a subagent with explicit context injection.

    WHY explicit context (Rule 1): Subagents have zero memory of the
    coordinator's conversation. They start completely fresh every time.
    If you don't pass the context here, the subagent has no idea what
    has been discussed or found so far. This is the single most common
    mistake in multi-agent systems.

    The context dict must contain EVERYTHING the subagent needs.
    Ask yourself: "If this subagent just walked in the door knowing
    nothing, does it have everything it needs?" If no — add more.

    Args:
        agent_name:    Human-readable name for logging/debugging
        system_prompt: The subagent's role and instructions
        context:       Everything the subagent needs — query, prior results,
                       quality criteria, source metadata, etc.
        tools:         Scoped toolset for this subagent only.
                       Never pass all tools — only what this agent needs.

    Returns:
        dict with "status" and either "result" or structured error fields.
        Never returns empty results for failures — coordinator needs
        structured errors to make intelligent recovery decisions.
    """
    if tools is None:
        tools = []

    # Build the subagent's prompt from the context dict.
    # Every key/value from the coordinator's context becomes part of
    # the subagent's prompt. Nothing is inherited automatically —
    # it must all be written here explicitly.
    prompt_parts = []
    for key, value in context.items():
        prompt_parts.append(f"{key.upper()}:\n{value}")
    subagent_prompt = "\n\n".join(prompt_parts)

    # Subagent has its OWN isolated messages list.
    # This is NOT the coordinator's messages list — it's a brand new one.
    # The subagent loop runs independently and returns a single result
    # back to the coordinator. It never reads or writes the coordinator's
    # messages list.
    messages = [{"role": "user", "content": subagent_prompt}]

    # Subagent runs its own agentic loop — same pattern as agentic_loop_base.py.
    # It loops until stop_reason == "end_turn" then returns its result.
    # The coordinator stores that result in a variable and decides what to do next.
    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=system_prompt,
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            # Subagent finished — extract result and return to coordinator.
            # The coordinator stores this in a variable, NOT in its messages.
            # The coordinator decides when and how to use this result.
            for block in response.content:
                if hasattr(block, "text"):
                    return {"status": "success", "result": block.text,
                            "agent": agent_name}
            return {"status": "success", "result": "", "agent": agent_name}

        elif response.stop_reason == "tool_use":
            # Subagent tool handling — same two-append pattern as base loop.
            # ✅ Step 1 — append subagent's tool call REQUEST to messages FIRST.
            # WHY: Without this, the subagent's messages list has a tool result
            # with no preceding request — broken history, repeated tool calls.
            messages.append({"role": "assistant", "content": response.content})

            # ✅ Step 2 — execute all tool calls and collect results.
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_subagent_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,  # Links result back to the
                                                   # specific tool call request.
                        "content": str(result)
                    })

            # ✅ Step 3 — append all tool results SECOND.
            # WHY: Subagent needs to see what tools returned before deciding
            # what to do next. Without this, it sees frozen messages and
            # repeats the same tool call forever.
            messages.append({"role": "user", "content": tool_results})

        else:
            # Subagent hit an unexpected stop_reason.
            # NEVER return empty results for failures — empty results look
            # like "no data found" (success) to the coordinator instead of
            # "subagent failed" (error). The coordinator cannot recover from
            # what it cannot distinguish.
            # Return a structured error so the coordinator can decide:
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


def run_coordinator(research_query: str) -> str:
    """
    The coordinator agent — hub of the hub-and-spoke architecture.

    Owns:
      - Task decomposition (Rule 3) — breaks query into subtopics
      - Context passing (Rule 1)    — explicitly passes all context to subagents
      - Communication routing (Rule 2) — all results flow through here
      - Error handling (Rule 4)     — decides retry/skip/escalate on failures
    """

    # Coordinator's own messages list.
    # Subagents have their OWN separate messages lists — they never
    # share or append to this list. This list only grows when the
    # coordinator itself produces output.
    coordinator_messages = [{"role": "user", "content": research_query}]

    # =========================================================================
    # STEP 1 — PARALLEL SUBAGENT SPAWNING (Rule 3 + parallel pattern)
    #
    # Independent subtopics run in parallel — in a real SDK implementation
    # this would be multiple Task tool calls in a SINGLE coordinator response.
    #
    # Sequential (❌ slow): one subagent per turn, each waits for previous
    # Parallel  (✅ fast):  all independent subagents invoked at once
    #
    # Use parallel when: subagents don't depend on each other's results
    # Use sequential when: subagent B needs subagent A's results to work
    # =========================================================================

    # Both search agents run independently — parallel is correct here.
    # Each gets ONLY the context relevant to its subtopic (Rule 1).
    # Results stored in coordinator variables — NOT in coordinator_messages yet.
    search_result_1 = invoke_subagent(
        agent_name="search_agent_topic_1",
        system_prompt=SEARCH_AGENT_SYSTEM,
        context={
            # Explicit context injection — the subagent cannot infer any of
            # this. If research_query is missing, it has no idea what to search.
            "research_query": research_query,
            "subtopic": "First major subtopic of the research query",
            "instructions": (
                "Search for current information on this subtopic. "
                "Return structured findings with source URLs and dates."
            )
        }
    )

    search_result_2 = invoke_subagent(
        agent_name="search_agent_topic_2",
        system_prompt=SEARCH_AGENT_SYSTEM,
        context={
            "research_query": research_query,
            "subtopic": "Second major subtopic of the research query",
            "instructions": (
                "Search for current information on this subtopic. "
                "Return structured findings with source URLs and dates."
            )
        }
    )

    # =========================================================================
    # STEP 2 — ERROR HANDLING (Rule 4)
    #
    # Coordinator decides what to do when a subagent fails.
    # Options: retry, use partial results, skip and annotate, escalate.
    # Never silently ignore errors — that turns failures into empty results
    # which look like "no data found" instead of "subagent failed."
    # =========================================================================

    if search_result_1.get("isError"):
        if search_result_1.get("isRetryable"):
            # Transient failure (timeout, rate limit) — retry once
            search_result_1 = invoke_subagent(
                agent_name="search_agent_topic_1_retry",
                system_prompt=SEARCH_AGENT_SYSTEM,
                context={
                    "research_query": research_query,
                    "subtopic": "First major subtopic — retry attempt",
                    "instructions": (
                        "Previous attempt failed. Try again with "
                        "a more specific query."
                    )
                }
            )
        else:
            # Non-retryable (permission error, business rule) — skip and annotate.
            # Synthesis agent will note this as a coverage gap in the report.
            search_result_1 = {
                "status": "unavailable",
                "result": "Search unavailable for this subtopic.",
                "coverage_note": "Source failure — treat claims in this area with caution."
            }

    # =========================================================================
    # STEP 3 — SEQUENTIAL SYNTHESIS (depends on search results)
    #
    # Synthesis MUST run after search — it depends on search results.
    # Cannot be parallel. Running synthesis before search results exist
    # means it has nothing to synthesize and will produce generic output.
    #
    # Pass ALL prior results explicitly (Rule 1).
    # If search_result_1 or search_result_2 are omitted here, the synthesis
    # agent produces a generic report with no sources — even though the
    # coordinator has the results sitting in variables.
    # =========================================================================

    synthesis_result = invoke_subagent(
        agent_name="synthesis_agent",
        system_prompt=SYNTHESIS_AGENT_SYSTEM,
        context={
            # Original query — subagent needs to know what it's answering
            "research_query": research_query,

            # Results from ALL prior subagents — explicitly passed.
            # This is the most commonly missed step. The coordinator has
            # these in variables but the synthesis agent cannot see them
            # unless they are explicitly included here.
            "search_findings_topic_1": search_result_1.get("result", "unavailable"),
            "search_findings_topic_2": search_result_2.get("result", "unavailable"),

            # Quality criteria — defines what a good synthesis looks like
            "quality_criteria": (
                "Cite every claim with its source. "
                "Flag conflicting findings between sources. "
                "Note any coverage gaps where sources were unavailable. "
                "Do not present uncited claims as facts."
            )
        }
    )

    # =========================================================================
    # STEP 4 — COORDINATOR APPENDS FINAL RESULT TO ITS OWN MESSAGES
    #
    # Only NOW does the result enter the coordinator's messages list.
    # Subagent results live in variables until the coordinator is ready.
    # They never append themselves — the coordinator owns that decision.
    # =========================================================================

    final_report = synthesis_result.get("result", "Research could not be completed.")
    coordinator_messages.append({
        "role": "assistant",
        "content": final_report
    })

    return final_report


# Sanity check — only runs when this file is executed directly.
# Will NOT run if this file is imported by another module.
# Runs a simple research query to verify the multi-agent pipeline works.
# Expected output: a short synthesized report on AI and music.
if __name__ == "__main__":
    result = run_coordinator("Research the impact of AI on the music industry.")
    print(result)
