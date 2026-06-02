# Domain 1 Practice Questions: Agentic Architecture & Orchestration
### 30 Questions | CCAF Exam Preparation

**Instructions:** Select the single best answer. After completing all questions,
check your answers at the bottom. Score 27/30 (90%) before moving to Domain 2.

---

## Section A: Agentic Loop Fundamentals (Questions 1-8)

**Q1.** Your agentic loop implementation works correctly for simple queries but
occasionally runs forever on complex tasks. Reviewing the code, you find:

```python
while True:
    response = claude_call(messages)
    if response.stop_reason == "tool_use":
        # handle tools
    # No else clause
```

What is the most likely cause and fix?

A) The loop needs a `break` statement after each tool call  
B) The loop has no handler for `stop_reason == "end_turn"`, so it loops forever after Claude finishes  
C) The `while True` should be replaced with a `for` loop with a fixed iteration count  
D) Claude is not returning `stop_reason` correctly for complex queries  

---

**Q2.** After implementing an agentic loop, you notice Claude always calls the same
tool twice in a row, returning identical results each time. The most likely cause is:

A) The tool description is too vague, causing Claude to retry for better results  
B) Tool results are not being appended to the conversation history between iterations  
C) The `stop_reason` check is incorrect, causing premature loop restart  
D) Claude's temperature setting is too high, causing non-deterministic behavior  

---

**Q3.** Which of the following is the ONLY correct primary mechanism for
terminating an agentic loop?

A) Checking if the response content contains a text block  
B) Detecting completion phrases like "I have finished" in Claude's response  
C) Checking `stop_reason == "end_turn"` in the API response  
D) Counting iterations and stopping after a predetermined maximum  

---

**Q4.** Your agentic loop implementation:

```python
for i in range(25):
    response = claude_call(messages)
    if response.stop_reason == "tool_use":
        results = execute_tools(response)
        messages.append({"role": "user", "content": results})
```

A developer says the iteration cap of 25 is an anti-pattern. Under what condition
is this assessment CORRECT?

A) Always — iteration caps are never acceptable in production agents  
B) When the cap is the primary stopping mechanism and there is no `stop_reason == "end_turn"` check  
C) When the task requires more than 25 tool calls to complete  
D) When the cap is set too low for the expected task complexity  

---

**Q5.** A production agent processes customer requests. Logs show it correctly
handles 99.2% of requests but in 0.8% of cases it calls `process_payment` before
`verify_identity`. The current implementation uses a system prompt instruction:
*"Always verify identity before processing any payment."*

What is the most accurate characterization of this situation?

A) 99.2% compliance is acceptable — no LLM achieves 100% on complex instructions  
B) The system prompt instruction is insufficient; programmatic enforcement is required  
C) The prompt needs more explicit examples of the correct tool call order  
D) The model should be fine-tuned on examples that always verify identity first  

---

**Q6.** Examine this agentic loop:

```python
while True:
    response = claude_call(messages)
    for block in response.content:
        if block.type == "tool_use":
            result = execute_tool(block.name, block.input)
            messages.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": block.id, "content": result}
            ]})
    if response.stop_reason == "end_turn":
        return get_text(response)
```

What is wrong with this implementation?

A) Tool results should be appended after all tool calls, not inside the loop  
B) The assistant response (with tool calls) is never appended to messages before the tool results  
C) `tool_use_id` should reference the message ID, not the block ID  
D) Tool results must be appended as assistant messages, not user messages  

---

**Q7.** Claude returns a response with `stop_reason == "tool_use"` and the
`content` array contains: `[TextBlock("Let me look that up..."), ToolUseBlock(name="search")]`

How should you handle this response?

A) Return the text content as the final answer since Claude already has a response  
B) Ignore the text block and process only the tool call  
C) Append the entire content array as the assistant message, execute all tool calls, append results, and continue the loop  
D) Process the text block first, then make a new API call to handle the tool call  

---

**Q8.** A safety iteration cap is ACCEPTABLE in an agentic loop implementation when:

A) It is never acceptable — `stop_reason` is the only valid termination mechanism  
B) It serves as a safety guard against runaway loops alongside proper `stop_reason` checking  
C) The task complexity is known in advance and the cap matches expected iterations  
D) The model has been observed to occasionally ignore `stop_reason` signals  

---

## Section B: Multi-Agent Orchestration (Questions 9-17)

**Q9.** You are building a multi-agent research system with a coordinator and
three subagents (search, analysis, synthesis). After running, the synthesis agent
produces generic content that doesn't reference any of the specific sources
found by the search agent. What is the most likely cause?

A) The synthesis agent's system prompt is too generic and needs refinement  
B) The synthesis agent does not have access to the search tool it needs  
C) The coordinator is not passing the search agent's findings to the synthesis agent's prompt  
D) The synthesis agent's context window is too small to process search results  

---

**Q10.** In a hub-and-spoke multi-agent architecture, which statement best
describes the correct communication pattern?

A) Subagents can communicate directly with each other to avoid coordinator bottleneck  
B) All inter-subagent communication routes through the coordinator  
C) The coordinator delegates tasks but subagents report results directly to the user  
D) Subagents share a common message queue for asynchronous communication  

---

**Q11.** A coordinator agent is tasked with researching "the impact of AI on
creative industries." It decomposes the task into three subtasks: "AI in digital
art," "AI in graphic design," and "AI in photography." All subagents complete
successfully, but the final report only covers visual arts. What is the root cause?

A) The synthesis agent failed to aggregate findings from all three subagents  
B) The search agent's queries were not comprehensive enough for the broader topic  
C) The coordinator's task decomposition was too narrow, missing music, film, and writing  
D) The subagents' context windows were too small to cover the full topic scope  

---

**Q12.** To spawn subagents in parallel rather than sequentially, a coordinator should:

A) Make separate API calls to Claude for each subagent with the same session ID  
B) Set `parallel: true` in the Task tool configuration  
C) Emit multiple Task tool calls in a single coordinator response turn  
D) Use async/await in the coordinator's Python implementation  

---

**Q13.** A coordinator uses the Task tool to spawn subagents. The system throws
an error: `ToolNotAllowedError: Task tool not permitted`. What configuration
is missing?

A) The `Task` tool must be added to the coordinator's system prompt  
B) `"Task"` must be included in the coordinator's `allowedTools` configuration  
C) The coordinator must use the `spawn_agent` API endpoint instead of the Task tool  
D) Task tool spawning requires an enterprise API plan  

---

**Q14.** When passing context from one subagent to the next in a research pipeline,
what format best preserves source attribution through synthesis?

A) Pass the full raw text output of each subagent  
B) Pass a summary of findings with source metadata (URL, title, date) in a structured format  
C) Pass only the key conclusions, omitting source details to reduce token usage  
D) Pass findings as natural language paragraphs with inline citations  

---

**Q15.** Your multi-agent research system is producing reports that miss entire
subtopics. The coordinator's logs show it always delegates to the same three
subagents regardless of query complexity. The best fix is:

A) Increase the number of specialized subagents in the system  
B) Redesign the coordinator prompt to analyze query requirements and dynamically select which subagents to invoke based on the topic  
C) Add a post-processing step that checks reports for missing topics  
D) Give each subagent access to all tools so they can fill gaps themselves  

---

**Q16.** A synthesis subagent frequently returns to the coordinator to verify
specific facts, adding 2-3 round trips per task. This occurs for 85% simple
fact-checks and 15% complex investigations. The most effective solution is:

A) Give the synthesis agent access to all web search tools to handle any verification  
B) Have the synthesis agent batch all verifications and return them to the coordinator at the end of its pass  
C) Give the synthesis agent a scoped `verify_fact` tool for simple lookups, routing complex verifications through the coordinator  
D) Pre-populate a fact-checking cache before the synthesis agent runs  

---

**Q17.** After a major library update, you need to resume a multi-week codebase
investigation session. The session has valid analysis of most files but the
`PaymentProcessor` class was refactored. The best approach is:

A) Start a completely new session and re-analyze the entire codebase from scratch  
B) Resume the session and tell Claude specifically which files changed and what changed  
C) Resume the session without additional context — Claude will re-read changed files automatically  
D) Fork the session to preserve the old analysis while creating a new branch  

---

## Section C: Hooks and Enforcement (Questions 18-22)

**Q18.** A `PostToolUse` hook is MOST appropriate for which use case?

A) Blocking tool calls that exceed a financial threshold  
B) Normalizing inconsistent date formats from different backend systems before Claude processes the results  
C) Routing tool calls to different backend endpoints based on input parameters  
D) Logging tool calls for audit purposes after execution  

---

**Q19.** Your MCP tools return customer data in three different formats:
- CRM: Unix timestamps, numeric status codes (1=active, 2=suspended)
- Orders: MM/DD/YYYY dates, string status labels
- Billing: ISO 8601 dates, boolean flags

The most effective solution to ensure consistent reasoning is:

A) Update each MCP tool to return a unified format  
B) Add format conversion instructions to the system prompt  
C) Implement a PostToolUse hook that normalizes all results to a standard format before the model processes them  
D) Include a data format reference guide in the system prompt  

---

**Q20.** Which scenario requires hooks over prompt-based enforcement?

A) Instructing the agent to always be polite in customer communications  
B) Ensuring the agent asks clarifying questions before making assumptions  
C) Preventing the agent from processing refunds above $500 without human approval  
D) Encouraging the agent to provide detailed explanations for its actions  

---

**Q21.** A PreToolUse hook intercepts a `process_refund` call with `amount: 750`.
The business rule states automated refunds are capped at $500. What should the
hook return to enable intelligent agent recovery?

A) `None` (let the call proceed — the agent will decide)  
B) Raise an exception that terminates the agent loop  
C) A structured error with the reason, required action (escalate_to_human), and isRetryable: false  
D) An empty dict to silently block the call  

---

**Q22.** The key difference between using hooks for enforcement versus prompt
instructions for enforcement is:

A) Hooks are faster; prompts cause additional API latency  
B) Hooks provide deterministic guarantees; prompts provide probabilistic compliance  
C) Hooks work for all tools; prompts only work for built-in Claude tools  
D) Hooks require enterprise API access; prompts work on all plans  

---

## Section D: Task Decomposition & Session Management (Questions 23-30)

**Q23.** A code review pipeline analyzes a 14-file pull request in a single pass.
Results are inconsistent: some files get detailed analysis, others get superficial
comments, and the same pattern is flagged as a bug in one file but approved in
another. The root cause is:

A) The model's context window is insufficient for 14 files  
B) Attention dilution when processing too many files simultaneously  
C) The review criteria are ambiguous and need clarification  
D) Files at the end of the context window are not being processed  

---

**Q24.** You need to add comprehensive test coverage to a 50,000-line legacy
codebase. The correct task decomposition approach is:

A) Prompt chain: generate tests for all files in a single pass  
B) Dynamic decomposition: first map structure, identify high-impact areas, then create a prioritized plan that adapts as dependencies are discovered  
C) Fixed sequential: analyze test coverage gaps, then generate missing tests in one batch  
D) Parallel execution: spawn one test-generation agent per file simultaneously  

---

**Q25.** When should you use `fork_session` instead of `--resume`?

A) When the prior session ran for more than 2 hours  
B) When prior tool results are stale due to code changes  
C) When you want to explore two different approaches from a shared analysis baseline  
D) When the context window is nearly full and you need to compact  

---

**Q26.** A coordinator agent is tasked with a large code review across 20 files.
The BEST decomposition strategy is:

A) One pass analyzing all 20 files simultaneously  
B) Per-file local analysis passes (focused on each file individually) followed by a separate cross-file integration pass  
C) Alphabetical batches of 5 files each (4 passes total)  
D) One pass for business logic files and one pass for utility files  

---

**Q27.** Which prompt decomposition pattern is BEST suited for an automated
CI/CD pipeline that reviews pull requests for security vulnerabilities?

A) Dynamic adaptive decomposition — security issues are unpredictable  
B) Prompt chaining — the review steps are predictable (scan → classify → report)  
C) Single-pass review — CI/CD pipelines require minimal latency  
D) Multi-agent decomposition — each agent specializes in a vulnerability type  

---

**Q28.** After resuming a session that analyzed a codebase last week, you ask
Claude to "continue the database refactoring." Claude references classes that
were deleted in a recent PR. What should you have done when resuming?

A) Used `fork_session` instead of `--resume` to avoid stale context  
B) Explicitly told Claude which files changed since the last session before asking it to continue  
C) Run `/compact` to clear the stale context before resuming  
D) Started a new session — resumption is unreliable after code changes  

---

**Q29.** A subagent returns the following error to the coordinator:
`{"status": "failed", "message": "search unavailable"}`

What is wrong with this error response?

A) It should use HTTP status codes instead of a status field  
B) It lacks structured context (failure type, attempted query, partial results) the coordinator needs to make intelligent recovery decisions  
C) Failed status responses should raise exceptions, not return dicts  
D) The message field should include a stack trace for debugging  

---

**Q30.** In the multi-agent research system, a subagent encounters a transient
network timeout while searching. What is the CORRECT behavior?

A) Propagate the error immediately to the coordinator  
B) Retry indefinitely until the search succeeds  
C) Attempt local recovery (retry with backoff), then if unresolved propagate structured error context including what was attempted and any partial results  
D) Return empty results marked as successful to avoid disrupting the pipeline  

---

## Answer Key

| Q | Answer | Key Concept |
|---|--------|-------------|
| 1 | B | Missing `end_turn` handler causes infinite loop |
| 2 | B | Tool results not in history → Claude repeats calls |
| 3 | C | `stop_reason == "end_turn"` is the ONLY correct primary stop |
| 4 | B | Cap as primary stop is the anti-pattern; as safety guard is fine |
| 5 | B | 0.8% failure on payment verification = unacceptable; needs programmatic enforcement |
| 6 | B | Assistant response with tool calls must be appended before tool results |
| 7 | C | Entire content array appended; all tools executed; results appended; loop continues |
| 8 | B | Safety cap + `stop_reason` check = correct; cap alone = anti-pattern |
| 9 | C | Context isolation — synthesis never received the search findings |
| 10 | B | Hub-and-spoke: all communication through coordinator |
| 11 | C | Coordinator's narrow decomposition missed non-visual creative industries |
| 12 | C | Multiple Task calls in ONE response turn = parallel execution |
| 13 | B | `"Task"` must be in `allowedTools` |
| 14 | B | Structured format with source metadata preserves attribution |
| 15 | B | Coordinator prompt must analyze and dynamically select subagents |
| 16 | C | Scoped tool for 85% common case; coordinator for 15% complex cases |
| 17 | B | Resume + tell Claude specifically what changed |
| 18 | B | PostToolUse = normalize results; PreToolUse = block/validate calls |
| 19 | C | PostToolUse hook normalizes before model processes |
| 20 | C | Financial threshold enforcement requires 100% → hooks, not prompts |
| 21 | C | Structured error with reason, required action, isRetryable enables recovery |
| 22 | B | Deterministic (hooks) vs probabilistic (prompts) |
| 23 | B | Attention dilution — core cause of inconsistent multi-file reviews |
| 24 | B | Open-ended legacy task → dynamic decomposition |
| 25 | C | fork_session = divergent approaches from shared baseline |
| 26 | B | Per-file passes + cross-file integration pass |
| 27 | B | Predictable pipeline → prompt chaining |
| 28 | B | Tell Claude what changed — stale context is the issue |
| 29 | B | Generic error hides recovery information from coordinator |
| 30 | C | Local recovery first; structured error propagation if unresolved |

---

## Scoring Guide

| Score | Interpretation | Action |
|---|---|---|
| 27-30 (90-100%) | Excellent — Domain 1 mastered | Proceed to Domain 2 |
| 23-26 (76-89%) | Good — minor gaps | Review missed questions, re-test |
| 19-22 (63-75%) | Fair — significant gaps | Re-read training doc, redo labs |
| Below 19 (<63%) | Needs work | Complete labs D1-01 through D1-04, re-test |

---

## Exam Tips for Domain 1

**Watch for these traps on the exam:**

1. **"Improve the prompt" answers** — When the scenario involves financial thresholds,
   identity verification, or compliance, the answer is NEVER "improve the prompt."
   It's always programmatic enforcement.

2. **"The subagent failed"** — When a multi-agent system produces wrong output but all
   subagents "completed successfully," look at the coordinator's task decomposition
   or context passing, not the subagents.

3. **"Generic error messages"** — Any answer that returns a generic error like
   "operation failed" is wrong. Structured errors with failure_type, isRetryable,
   and actionable guidance are always correct.

4. **"Parallel vs sequential"** — Multiple Task calls in ONE response = parallel.
   One Task call per turn = sequential. The exam tests whether you know the difference.

5. **"session resume vs fresh start"** — If prior tool results are stale → fresh start
   with injected summary. If prior context is mostly valid → resume and state what changed.
