# Domain 2 Practice Questions: Tool Design & MCP Integration
### 25 Questions | CCAF Exam Preparation

**Pass threshold: 23/25 (90%)**

---

**Q1.** A tool named `analyze_content` has description: "Analyzes content and returns structured results." A similar tool named `analyze_document` has: "Analyzes document content and returns structured results." Production logs show 40% misrouting between these tools. What is the root cause?

A) The tool names are too similar and must be renamed  
B) Minimal descriptions lack the context for Claude to differentiate tools — Claude cannot reliably distinguish their purposes  
C) The model needs few-shot examples showing which tool to call for each input type  
D) The tools should be merged into one and internally route based on input format  

---

**Q2.** Which elements should be included in a well-designed tool description? (Select the BEST answer)

A) Tool name, parameter types, and return value type  
B) What the tool does, when to use it vs. similar tools, expected input formats, what it returns, and edge case behavior  
C) A brief description of the tool's purpose and an example API call  
D) The tool's underlying implementation and performance characteristics  

---

**Q3.** Your MCP tool for customer lookup returns: `{"results": []}` both when no customers match the query AND when the database times out. What is the problem?

A) The tool should throw an exception on database timeout instead of returning a dict  
B) The coordinator cannot distinguish a successful query with no results from a failed query — both look identical  
C) Empty results should return `null` instead of an empty array  
D) The tool needs to implement retry logic before returning  

---

**Q4.** A `process_refund` tool needs to block refunds above $500 and redirect to human escalation. This rule must have 100% compliance. The BEST implementation is:

A) Add to the system prompt: "Never process refunds above $500 — always escalate these"  
B) Add few-shot examples showing the agent always escalating refunds above $500  
C) Implement a PreToolUse hook that intercepts the tool call and returns a structured redirect error when amount > 500  
D) Add validation in the tool description explaining the $500 limit  

---

**Q5.** A synthesis agent has access to 18 tools including all web search, document analysis, database query, report compilation, and coordinator tools. The agent frequently uses web search tools when it should be synthesizing from already-gathered findings. The BEST fix is:

A) Improve the tool descriptions to explain when NOT to use web search  
B) Restrict the synthesis agent to only the tools needed for its role (verify_fact, compile_report) — remove tools outside its specialization  
C) Add instructions to the synthesis agent's system prompt to avoid web searching  
D) Create a separate routing layer that pre-filters which tools are available per task  

---

**Q6.** The difference between `tool_choice: "auto"` and `tool_choice: "any"` is:

A) "auto" selects tools automatically; "any" requires manual tool specification  
B) "auto" allows Claude to choose whether to call a tool or respond with text; "any" requires Claude to call a tool (but any of the available ones)  
C) "auto" is for single-turn requests; "any" is for multi-turn agentic workflows  
D) "auto" allows parallel tool calls; "any" requires sequential calls  

---

**Q7.** You are extracting structured data from documents of unknown type (invoices, receipts, contracts). Multiple extraction tools exist, one for each document type. You need guaranteed structured output regardless of which tool Claude selects. Which tool_choice setting is correct?

A) `{"type": "auto"}` — Claude will select the appropriate extraction tool  
B) `{"type": "any"}` — Claude must call a tool (any of the extraction tools)  
C) `{"type": "tool", "name": "extract_invoice"}` — force the invoice extractor  
D) No tool_choice needed — the descriptions will guide selection  

---

**Q8.** Team shared tooling (GitHub MCP server, internal API server) should be configured in:

A) `~/.claude.json` on each team member's machine  
B) `.mcp.json` in the project root, committed to version control  
C) `~/.claude/CLAUDE.md` with MCP server configuration syntax  
D) A separate `mcp-config.yaml` file excluded from version control  

---

**Q9.** An MCP server configuration uses `"GITHUB_TOKEN": "${GITHUB_TOKEN}"` in the env section. What does this syntax do and why is it correct?

A) It creates a new environment variable; it's correct because it namespaces the token  
B) It expands the value from the system environment at runtime; it's correct because credentials are never committed to the repo  
C) It references a GitHub Actions secret; it's correct for CI/CD environments only  
D) It uses template syntax that requires a `.env` file at the project root  

---

**Q10.** You need to find all Python files that contain a call to `process_payment()`. Which built-in tool is correct?

A) Glob with pattern `**/*.py` — finds all Python files  
B) Grep with pattern `process_payment` and file type `py` — searches file contents  
C) Read on each Python file and search for the pattern manually  
D) Bash with `find . -name "*.py"` — finds Python files  

---

**Q11.** You need to find all files matching the pattern `**/*.test.tsx`. Which built-in tool is correct?

A) Grep with pattern `*.test.tsx` — searches for the file extension  
B) Glob with pattern `**/*.test.tsx` — matches files by path pattern  
C) Bash with `ls -la **/*.test.tsx`  
D) Read with a wildcard path  

---

**Q12.** An Edit tool call fails because the text to replace appears 4 times in the file. What is the correct fallback?

A) Make the old_string longer to create a unique match  
B) Use Bash with `sed` to replace all occurrences  
C) Use Read to get the full file content, modify it in the prompt, then use Write to save the complete new version  
D) Call Edit four times with different unique_match parameters  

---

**Q13.** A subagent's web search times out after 3 retry attempts. It should propagate this to the coordinator. Which error response enables the best coordinator recovery?

A) `{"error": "search failed"}`  
B) `{"isError": True, "errorCategory": "transient", "isRetryable": True, "message": "Search timed out after 3 attempts", "attemptedQuery": "AI in education 2024", "partialResults": [], "suggestedAlternatives": ["Try narrower query", "Use document analysis instead"]}`  
C) `{"success": False, "code": 504}`  
D) Raise a Python exception that the coordinator's try/except handles  

---

**Q14.** A customer records tool returns `{"error": "Database connection failed"}` when the database is down, and `{"results": [], "count": 0}` when a customer doesn't exist. A developer argues both cases should return the same response structure. Why is this WRONG?

A) It's not wrong — both represent failure to return customer data  
B) The coordinator cannot distinguish "customer doesn't exist" (no retry needed) from "database down" (should retry) — they require different recovery actions  
C) Empty results should throw an exception, not return a dict  
D) The error case should return null instead of an error object  

---

**Q15.** For a multi-agent research system, the analysis agent is given tools: web_search, fetch_url, extract_data_points, summarize_content, verify_claim, compile_report, Task, verify_fact. Which tools should be removed?

A) verify_claim and verify_fact — analysis agents should not verify  
B) web_search, fetch_url, compile_report, Task, verify_fact — outside the analysis agent's specialization  
C) extract_data_points and summarize_content — too similar to web search tools  
D) All tools except extract_data_points — analysis should only extract  

---

**Q16.** MCP resources (as opposed to MCP tools) are BEST used for:

A) Executing actions on backend systems (creating issues, sending messages)  
B) Exposing content catalogs (available documents, issue summaries, schemas) to reduce exploratory tool calls  
C) Providing real-time streaming data from external services  
D) Authenticating the agent with external services  

---

**Q17.** Your team wants to integrate with Jira for ticket management. The recommended approach is:

A) Build a custom MCP server from scratch — no existing solutions are reliable  
B) Use the existing community Jira MCP server — reserve custom development for team-specific workflows  
C) Use the Claude API's built-in Jira integration  
D) Configure Jira webhooks to post updates directly to Claude's context  

---

**Q18.** When building codebase understanding, the recommended tool usage pattern is:

A) Read all files upfront to ensure comprehensive context  
B) Start with Grep to find entry points, use Read to follow imports and trace flows, building understanding incrementally  
C) Use Glob to find all files, then Read each one  
D) Use Bash to run code analysis tools before reading files  

---

**Q19.** A tool description for `get_customer` reads: "Gets customer." Claude frequently calls it for order lookups because orders include customer IDs. What's happening and how do you fix it?

A) Rename the tool to `fetch_customer_only` and add a warning about order IDs in the description  
B) The system prompt likely contains wording that associates "customer" with order operations — expand the description to clarify it only returns account-level data, not order data, and update system prompt wording  
C) This is expected behavior — Claude is correctly using available tools  
D) Add a required `purpose` parameter so Claude must specify why it's calling the tool  

---

**Q20.** You need to ensure `extract_metadata` runs before any enrichment tools. The correct configuration is:

A) List `extract_metadata` first in the tools array  
B) Add "always call extract_metadata first" to the system prompt  
C) First call with `tool_choice: {"type": "tool", "name": "extract_metadata"}`, then subsequent calls with `tool_choice: "auto"` for enrichment  
D) Use `tool_choice: "any"` and trust Claude to call extract_metadata first  

---

**Q21.** A transient error (database timeout) should have `isRetryable: true`. A permission error should have `isRetryable: false`. Why does this distinction matter?

A) It affects API rate limiting — retryable errors count toward quota differently  
B) It tells the coordinator whether attempting the same call again will succeed — retrying a permission error wastes API calls and delays the workflow  
C) It determines whether the error is logged — transient errors don't create permanent records  
D) It controls whether the agent displays the error to the user  

---

**Q22.** Your synthesis agent occasionally performs web searches instead of synthesizing. It has access to verify_fact (quick facts) and the full web_search tool. Logs show it uses web_search for queries verify_fact could handle. The BEST fix is:

A) Remove web_search from the synthesis agent entirely  
B) Improve the descriptions of both tools to clearly differentiate when each should be used, with examples of appropriate queries for each  
C) Add a routing instruction to the system prompt: "Use verify_fact for simple facts, web_search for complex research"  
D) Lower the synthesis agent's temperature to reduce deviation from expected behavior  

---

**Q23.** All configured MCP servers are discovered at:

A) Each time a tool is called — lazy loading  
B) Session start/connection time — all servers available simultaneously from the first turn  
C) When the first tool call is made in a session  
D) When explicitly activated using the `/mcp connect` command  

---

**Q24.** A subagent returns partial results plus a structured error after a partial failure. Why is returning partial results better than returning only the error?

A) Partial results reduce the error's HTTP status code severity  
B) The coordinator can proceed with available information and only re-delegate the failed portion, rather than rerunning the entire task  
C) Partial results prevent the coordinator from logging the error  
D) It reduces token usage in subsequent coordinator calls  

---

**Q25.** You are reviewing an MCP tool description: "Processes data and returns output." Three other tools have similar minimal descriptions. Tool selection reliability is 60%. Which single change has the highest impact?

A) Add examples of correct tool calls to the system prompt  
B) Rewrite all four tool descriptions to include purpose, input format, output structure, and differentiation from the other three tools  
C) Rename the tools to have more distinct names  
D) Reduce the number of tools available to the agent  

---

## Answer Key

| Q | Answer | Key Concept |
|---|--------|-------------|
| 1 | B | Minimal descriptions → unreliable selection |
| 2 | B | 5 elements of good tool descriptions |
| 3 | B | Empty results vs access failure must be distinguishable |
| 4 | C | PreToolUse hook = 100% enforcement |
| 5 | B | Restrict agent to role-specific tools |
| 6 | B | auto = optional tool call; any = required tool call |
| 7 | B | "any" for guaranteed output when document type unknown |
| 8 | B | Team tooling in .mcp.json (version controlled) |
| 9 | B | ${VAR} expands from environment — no credentials in repo |
| 10 | B | Grep = content search (searching inside files) |
| 11 | B | Glob = path/name pattern matching |
| 12 | C | Read + Write fallback when Edit fails |
| 13 | B | Structured error with all recovery context |
| 14 | B | Different failures require different recovery actions |
| 15 | B | Analysis agent needs only analysis tools |
| 16 | B | Resources expose catalogs; tools execute actions |
| 17 | B | Use community servers for standard integrations |
| 18 | B | Incremental understanding: Grep → Read → trace |
| 19 | B | Description + system prompt keyword sensitivity |
| 20 | C | Forced tool_choice for required first step |
| 21 | B | Prevents wasted retries on non-recoverable errors |
| 22 | B | Better descriptions differentiate when to use each |
| 23 | B | All servers available at connection time |
| 24 | B | Coordinator can partially proceed; avoids full re-run |
| 25 | B | Rewriting all descriptions is highest-impact single change |
