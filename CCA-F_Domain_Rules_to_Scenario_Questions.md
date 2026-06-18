# CCA-F: Domain Rules → Scenario Question Map

A study reference distilling every decision rule from the five exam domains, then mapping each of the 12 sample questions to the specific rule it tests. The value for the team: once you internalize the rule, the three distractors become predictable — they almost always (a) substitute a probabilistic fix where a deterministic one is required, (b) over-engineer with ML/infrastructure when prompt/config solves it, or (c) blame a downstream component that is working correctly.

> **How to read the tables:** *Rule* = what to do. *The trap it rules out* = the wrong answer pattern, in exam language. *In plain English* = the same trap explained without jargon.

---

## Part A — The Rules, by Domain

### Domain 1: Agentic Architecture & Orchestration (27%)

| ID | Rule | The trap it rules out | In plain English |
|----|------|----------------------|------------------|
| 1.1 | Loop control is driven by `stop_reason`: continue on `"tool_use"`, terminate on `"end_turn"`. | Parsing natural-language signals, checking for assistant text, or using an iteration cap as the *primary* stop. | Don't guess whether the agent is finished by reading its words or capping the rounds — check the actual "I'm done" flag. |
| 1.2 | Append tool results to conversation history every iteration so the model reasons over new info. | Discarding or summarizing results before the next turn. | Don't throw away or shrink what a tool just returned before the agent gets to use it. |
| 1.3 | Prefer model-driven tool selection over pre-configured decision trees / fixed sequences. | Hard-coded routing that bypasses Claude's reasoning. | Don't lock the agent into a fixed script — let it decide the next move. |
| 1.4 | Hub-and-spoke: the coordinator owns all inter-subagent comms, error handling, and routing. | Subagents talking directly to each other. | Don't let the helpers chatter among themselves; everything goes through the manager. |
| 1.5 | Subagents have isolated context — they do **not** inherit coordinator history. Pass context explicitly in the prompt. | Assuming automatic context inheritance. | A helper starts with a blank slate — you have to spell out what it needs to know. |
| 1.6 | Coordinator decomposes, delegates, aggregates, and *dynamically* selects which subagents to invoke by query complexity. | Always running the full pipeline regardless of need. | Don't run every step every time; only call the helpers the job actually needs. |
| 1.7 | Overly narrow coordinator decomposition → incomplete coverage of broad topics. | Blaming downstream agents that executed their (wrong) assignment correctly. | If the manager hands out a too-narrow to-do list, the work comes back incomplete — and that's the manager's fault, not the workers'. |
| 1.8 | Partition scope across subagents to minimize duplication (distinct subtopics/source types). | Overlapping assignments. | Give each helper its own slice so two aren't doing the same work. |
| 1.9 | Use iterative refinement loops: coordinator evaluates synthesis for gaps, re-delegates, re-synthesizes. | One-shot pipeline with no gap check. | Check the draft for holes and send people back to fill them, instead of shipping the first pass. |
| 1.10 | The `Task` tool spawns subagents; `allowedTools` must include `"Task"`. | Forgetting Task in allowedTools. | The manager literally can't summon helpers unless it's been given permission to. |
| 1.11 | Spawn parallel subagents by emitting multiple `Task` calls in **one** coordinator response. | Spawning across separate turns (serial). | Launch the helpers all at once, not one after another. |
| 1.12 | Coordinator prompts should specify goals + quality criteria, not step-by-step procedures. | Procedural micromanagement that blocks adaptability. | Tell helpers what "good" looks like, not every keystroke — so they can adapt. |
| 1.13 | Use programmatic enforcement (hooks, prerequisite gates) — not prompts — when deterministic compliance is required. Prompts have a non-zero failure rate. | Relying on system-prompt mandates or few-shot for safety-critical ordering. | For anything where a slip costs money or safety, don't just *tell* the agent to be careful — put up a hard gate it can't skip. |
| 1.14 | Block downstream tool calls until prerequisites complete (e.g., block `process_refund` until `get_customer` returns a verified ID). | Trusting the model to self-order critical steps. | Don't let it pay a refund before it's confirmed who the customer is — block that path in code. |
| 1.15 | Compile structured handoff summaries on escalation (customer ID, root cause, amount, recommended action). | Escalating with raw transcript or nothing. | When handing a case to a human, give them a clean summary, not the whole chat log or a shrug. |
| 1.16 | Hooks: `PostToolUse` to normalize data before the model sees it; tool-call interception to block policy violations and redirect. | Doing normalization/compliance via prompt. | Use code that intercepts the data or the action to clean it up or stop it — don't just ask nicely in the prompt. |
| 1.17 | Choose hooks over prompt-based enforcement when business rules require *guaranteed* compliance. | "Be careful to…" instructions for hard limits. | Hard limits need a hard wall, not a polite reminder. |
| 1.18 | Prompt chaining (fixed sequential) for predictable multi-aspect reviews; dynamic adaptive decomposition for open-ended investigation. | Using one pattern for both. | Use a fixed checklist for predictable jobs; let the plan grow as you learn for open-ended ones. |
| 1.19 | Split large reviews into per-file local passes + a separate cross-file integration pass to avoid attention dilution. | Single all-files-at-once pass. | Reviewing 14 files in one go spreads attention thin — do one file at a time, then one pass for how they fit together. |
| 1.20 | Session: `--resume <name>` to continue; `fork_session` for divergent branches off a shared baseline; start fresh with a structured summary when prior tool results are stale; inform a resumed session of file changes. | Resuming with stale results; full re-exploration. | Pick up a saved session only if it's still accurate; otherwise start fresh with a summary, and tell it which files changed. |

### Domain 2: Tool Design & MCP Integration (18%)

| ID | Rule | The trap it rules out | In plain English |
|----|------|----------------------|------------------|
| 2.1 | Tool descriptions are the **primary** mechanism for tool selection — include input formats, example queries, edge cases, and boundaries. | "Fixing" selection with few-shot, routing layers, or consolidation when the real issue is thin descriptions. | If the agent picks the wrong tool, the description is usually too vague — fix that before building anything fancy. |
| 2.2 | Eliminate functional overlap by renaming + differentiating, or splitting a generic tool into purpose-specific ones with defined I/O contracts. | Two near-identical descriptions left as-is. | Two tools that sound the same will get confused — rename or split them so each has a clear job. |
| 2.3 | Audit system prompts for keyword-sensitive instructions that override good tool descriptions. | Ignoring the prompt as a source of misrouting. | Sometimes a stray word in the system prompt is steering the agent wrong — check there too. |
| 2.4 | Return structured error metadata: `errorCategory` (transient/validation/business/permission), `isRetryable`, human-readable description; use the MCP `isError` flag. | Generic "Operation failed." | When a tool fails, say *what kind* of failure and *whether retrying helps* — not just "it broke." |
| 2.5 | Distinguish retryable vs non-retryable so the agent doesn't waste retries. | Uniform error responses. | Label errors so the agent doesn't keep retrying something that will never work. |
| 2.6 | Subagents recover locally for transient failures; propagate only unresolved errors + partial results + what was attempted. | Propagating everything, or nothing. | A helper should quietly fix small hiccups itself and only escalate the real problems, along with what it tried. |
| 2.7 | Distinguish access failures (need retry) from valid empty results (success, no matches). | Treating "no matches" as an error or vice-versa. | "Found nothing" is a successful search, not a failure — don't confuse the two. |
| 2.8 | Too many tools (e.g., 18 vs 4–5) degrades selection; scope tools to each agent's role. | Giving every agent every tool. | Hand an agent 18 tools and it'll fumble the choice; give it the 4–5 it actually needs. |
| 2.9 | Provide scoped cross-role tools for high-frequency needs (least privilege); route complex cases through the coordinator. | Over-provisioning an agent with the full toolset. | Give an agent a small tool for its common need, and send the rare hard cases back to the manager. |
| 2.10 | `tool_choice`: `"auto"` (may return text), `"any"` (must call some tool), forced `{"type":"tool","name":...}` (must call a specific tool). | Confusing "any" with forced selection. | Know the three settings: let it choose whether to use a tool, make it use *some* tool, or make it use *one specific* tool. |
| 2.11 | MCP scope: project `.mcp.json` (shared, version-controlled) vs user `~/.claude.json` (personal); use env-var expansion (`${GITHUB_TOKEN}`) for secrets. | Committing secrets; wrong scope for sharing. | Team tools go in the shared project file (with secrets pulled from env vars); personal experiments stay in your own file. |
| 2.12 | Tools from all configured MCP servers are discovered at connection time and available simultaneously. | Assuming servers are mutually exclusive. | All your connected servers' tools are available at once — they don't take turns. |
| 2.13 | Expose content catalogs as MCP **resources** to cut exploratory tool calls. | Forcing discovery via repeated tool calls. | Hand the agent a menu of what's available so it doesn't have to poke around to find it. |
| 2.14 | Prefer community MCP servers for standard integrations (e.g., Jira); custom servers only for team-specific workflows. | Building custom for a solved problem. | If a ready-made connector exists (like Jira), use it; only build your own for genuinely custom needs. |
| 2.15 | Built-in tools: Grep (content search), Glob (path patterns), Read/Write (full file), Edit (unique-match). Edit fails on non-unique text → Read+Write fallback. Build understanding incrementally (Grep → Read → trace). | Reading all files upfront; using Edit on ambiguous anchors. | Search to find the starting point, then read and follow the thread — don't load the whole codebase. If an edit target isn't unique, rewrite the file instead. |

### Domain 3: Claude Code Configuration & Workflows (20%)

| ID | Rule | The trap it rules out | In plain English |
|----|------|----------------------|------------------|
| 3.1 | CLAUDE.md hierarchy: user (`~/.claude/CLAUDE.md`), project (`.claude/CLAUDE.md` or root), directory (subdir). User-level is **not** shared via version control. | A teammate missing instructions that live only in user-level config. | If a rule lives in your personal settings, your teammates never get it — put shared rules in the project. |
| 3.2 | Keep CLAUDE.md modular with `@import`; use `.claude/rules/` for topic files; `/memory` to verify loaded files. | A monolithic, hard-to-diagnose CLAUDE.md. | Break a giant rules file into smaller topic files, and use `/memory` to check what's actually loaded. |
| 3.3 | Slash commands: project `.claude/commands/` (shared via VC) vs user `~/.claude/commands/` (personal). | Putting a team command in user scope (or in CLAUDE.md / a non-existent config.json). | A command everyone should have goes in the shared project folder, not your personal one. |
| 3.4 | Skills live in `.claude/skills/` with SKILL.md frontmatter: `context: fork` (isolated subagent context), `allowed-tools` (restrict), `argument-hint` (prompt for params); personal variants in `~/.claude/skills/`. | Letting verbose skill output pollute the main session. | Run a noisy skill in its own sandbox so its output doesn't clutter the main conversation, and lock down which tools it can touch. |
| 3.5 | Skills = on-demand task workflows; CLAUDE.md = always-loaded universal standards. | Using skills where you need automatic, always-on behavior. | Skills run only when called; CLAUDE.md is always on — pick based on whether you need it every time. |
| 3.6 | Path-specific rules: `.claude/rules/` with YAML `paths:` globs load only when editing matching files — superior to directory CLAUDE.md when files (e.g., tests) are spread across dirs. | Per-directory CLAUDE.md for cross-cutting file types; relying on inference. | When the same file type (like tests) is scattered everywhere, use a pattern-matched rule — not a folder-by-folder file, and not hoping the agent guesses. |
| 3.7 | Plan mode for complex/large-scale/architectural/multi-file/multiple-valid-approach tasks; direct execution for simple, well-scoped changes. Don't defer to "switch later" when complexity is already stated. | Starting direct and hoping to pivot; assuming you know the structure. | Big, multi-way decisions deserve a plan first; tiny fixes you just do. Don't dive in and hope to course-correct later. |
| 3.8 | Use the Explore subagent for verbose discovery → returns summaries, preserves main context. | Letting discovery exhaust the context window. | Send the messy exploration off to a helper that hands back a clean summary, so the main session stays focused. |
| 3.9 | Iterative refinement: concrete input/output examples beat prose; test-driven iteration; interview pattern; bundle interacting issues in one message, fix independent issues sequentially. | Vague prose specs; fixing interacting issues piecemeal. | Show examples instead of describing; if two bugs affect each other, fix them together in one go. |
| 3.10 | CI: `-p`/`--print` for non-interactive; `--output-format json` + `--json-schema` for structured output; CLAUDE.md supplies CI context; an **independent** review instance beats self-review. | Interactive hangs; self-reviewing generated code. | In a pipeline, use the non-interactive flag so it doesn't sit waiting, and have a fresh instance review code — not the one that wrote it. |

### Domain 4: Prompt Engineering & Structured Output (20%)

| ID | Rule | The trap it rules out | In plain English |
|----|------|----------------------|------------------|
| 4.1 | Explicit categorical criteria beat vague instructions; "be conservative" / "only high-confidence" don't improve precision. High false-positive categories erode trust — disable them temporarily while you fix the prompt. | Confidence-based filtering as a precision fix. | Telling it to "only flag what you're sure about" doesn't work — spell out exactly which things count as problems. |
| 4.2 | Few-shot examples (2–4, showing the *reasoning* for the choice) are the most effective lever for consistent format, ambiguous-case handling, generalization, and reduced hallucination. | Adding more prose instructions. | When instructions aren't landing, show a few worked examples — that beats writing more rules. |
| 4.3 | `tool_use` + JSON schema is the most reliable structured output — eliminates syntax errors (not semantic ones). Use `tool_choice` (auto/any/forced); make absent-info fields nullable/optional to prevent fabrication; use enum `"other"`+detail and `"unclear"` for ambiguity. | Required fields that force the model to invent values. | Use a schema to guarantee clean structure, and make optional info optional so it won't make up an answer just to fill a blank. |
| 4.4 | Retry-with-error-feedback (append the specific validation error). Retries help format/structural errors but **not** when the info is absent from the source. Add `detected_pattern` for FP analysis; self-correction flows (`calculated_total` vs `stated_total`, `conflict_detected`). | Retrying when the data simply isn't there. | Retrying fixes formatting slip-ups, but it can't conjure information that was never in the document. |
| 4.5 | Message Batches API: 50% savings, up to 24h window, no latency SLA, no multi-turn tool calling, `custom_id` correlation. Use for non-blocking/latency-tolerant work only. | Batching a blocking pre-merge check. | Batch jobs are cheap but can take hours — great for overnight reports, useless when someone's waiting to merge. |
| 4.6 | Self-review is weak (the model keeps its generation reasoning); an independent instance catches more than self-review or extended thinking. Multi-pass = per-file + cross-file. | Bigger context window / "review your own work" / 2-of-3 consensus. | Code reviews itself poorly — bring in a fresh set of eyes. A bigger window doesn't fix attention; splitting the work does. |

### Domain 5: Context Management & Reliability (15%)

| ID | Rule | The trap it rules out | In plain English |
|----|------|----------------------|------------------|
| 5.1 | Don't let progressive summarization condense numbers/dates/expectations. Mitigate "lost in the middle" by placing key findings at start/end. Trim verbose tool outputs to relevant fields; persist a "case facts" block outside summarized history; pass full conversation history. | Vague summaries that drop transactional facts. | When you compress the chat history, keep the hard facts (amounts, dates) — those are exactly what summaries tend to lose. |
| 5.2 | Escalation triggers: explicit human request (honor immediately), policy gaps/silence, inability to progress. Sentiment and self-reported confidence are unreliable proxies for complexity. Multiple matches → ask for identifiers, don't guess. | Sentiment- or confidence-threshold routing; heuristic match selection. | Escalate when a human is asked for, the policy is silent, or you're stuck — not because the customer sounds annoyed or the agent "feels unsure." If two people match, ask which one. |
| 5.3 | Propagate structured error context (failure type, attempted query, partial results, alternatives). Distinguish access failures vs valid empty results. Never silently suppress; never terminate the whole workflow on a single failure. | Generic "search unavailable"; empty-as-success; global abort. | When a helper fails, report what happened and what it tried — don't paper over it, fake success, or blow up the whole job. |
| 5.4 | Large codebases degrade in extended sessions — use scratchpad files, subagent delegation, structured state exports/manifests for crash recovery, and `/compact`. | One long session that starts citing "typical patterns." | Long sessions drift and start giving generic answers — jot key findings to a file, use helpers, and compact the context. |
| 5.5 | Aggregate accuracy masks per-type/field weakness. Use stratified random sampling, field-level confidence calibrated on labeled sets, and segment accuracy by doc type/field before automating. | Trusting a single 97% headline number. | One overall accuracy number can hide that it's terrible on certain document types — check each segment before trusting it. |
| 5.6 | Preserve claim-source mappings through synthesis; annotate conflicting stats with attribution (don't pick one); require publication/collection dates (temporal ≠ contradiction); render content types appropriately. | Compressing away provenance; arbitrating conflicts silently. | Keep track of which source each claim came from; when sources disagree, show both with attribution instead of quietly picking one. |

---

## Part B — Rules Exemplified in the Sample Questions, by Scenario

> The doc supplies 12 sample questions across **4 of the 6** scenarios. Each is mapped below to the primary rule it tests.

### Scenario: Customer Support Resolution Agent

| Q | What it tests | Rule(s) | Answer | Why the rule applies |
|---|---------------|---------|--------|----------------------|
| 1 | Agent skips `get_customer` 12% of the time → wrong refunds. Fix? | **1.13 / 1.14** | A — programmatic prerequisite gate | Critical ordering needs deterministic enforcement; B (system-prompt mandate) and C (few-shot) are probabilistic; D fixes tool *availability*, not *ordering*. |
| 2 | Agent calls `get_customer` for order queries; both tools have minimal descriptions. First step? | **2.1** | B — expand each tool's description | Descriptions are the primary selection mechanism; few-shot (A) adds tokens without fixing root cause; routing layer (C) over-engineers; consolidation (D) is bigger than a "first step." |
| 3 | 55% resolution; escalates easy cases, attempts hard ones. Fix calibration? | **5.2** | A — explicit escalation criteria + few-shot | Root cause is unclear decision boundaries. B fails (self-reported confidence is mis-calibrated — already wrongly confident on hard cases); C over-engineers; D uses sentiment, which doesn't track complexity. |

### Scenario: Code Generation with Claude Code

| Q | What it tests | Rule(s) | Answer | Why the rule applies |
|---|---------------|---------|--------|----------------------|
| 4 | Team `/review` command for every developer on clone/pull. Where? | **3.3** | A — `.claude/commands/` in the repo | Project scope is version-controlled and shared. B is personal/user scope; C (CLAUDE.md) is for context not commands; D references a non-existent config mechanism. |
| 5 | Monolith → microservices, dozens of files, architectural decisions. Approach? | **3.7** | A — plan mode | Large-scale, multiple valid approaches, architectural = exactly plan mode. B/C assume the structure; D ignores that complexity is already stated, not emergent. |
| 6 | Different conventions per area; tests spread throughout; want auto-applied conventions. | **3.6** | A — `.claude/rules/` with glob frontmatter | Glob path-scoping applies regardless of directory — essential for spread-out test files. B relies on inference; C needs manual/loaded invocation; D is directory-bound. |

### Scenario: Multi-Agent Research System

| Q | What it tests | Rule(s) | Answer | Why the rule applies |
|---|---------------|---------|--------|----------------------|
| 7 | Reports cover only visual arts; coordinator log shows it split into digital art / graphic design / photography. Root cause? | **1.7** | B — coordinator decomposition too narrow | Subagents executed correctly within their (wrong) scope; A/C/D blame downstream agents that are working fine. |
| 8 | Web-search subagent times out. Best error flow to coordinator? | **5.3** (with 2.5–2.7) | A — structured error context | Gives the coordinator what it needs to recover. B's generic status hides context; C suppresses the failure; D aborts the whole workflow. |
| 9 | Synthesis agent's verification round-trips add 40% latency; 85% are simple fact-checks. Reduce overhead? | **2.9** | A — scoped `verify_fact` tool, complex cases still routed | Least privilege: equip the agent for the common case, keep coordination for the 15%. B blocks on dependencies; C over-provisions; D relies on speculative caching. |

### Scenario: Claude Code for Continuous Integration

| Q | What it tests | Rule(s) | Answer | Why the rule applies |
|---|---------------|---------|--------|----------------------|
| 10 | `claude "Analyze…"` hangs waiting for interactive input in CI. Fix? | **3.10** | A — `-p` / `--print` | The documented non-interactive flag. B/D reference non-existent features; C is a Unix workaround that doesn't address Claude Code's syntax. |
| 11 | Move both a blocking pre-merge check and an overnight debt report to the Batches API for 50% savings? | **4.5** | A — batch the overnight report only | No latency SLA (up to 24h) disqualifies blocking workflows; B relies on "often faster"; C misbelieves batch results can't be correlated (they can, via `custom_id`); D adds needless complexity. |
| 12 | 14-file PR; single-pass review is inconsistent and self-contradictory. Restructure? | **4.6 / 1.19** | A — per-file passes + cross-file integration pass | Root cause is attention dilution. B shifts burden to devs; C misreads larger context as an attention fix; D suppresses real bugs by requiring consensus. |

---

## Coverage note: the two scenarios without sample questions

The sample set omits **Scenario 4 (Developer Productivity)** and **Scenario 6 (Structured Data Extraction)**, though both appear on the live exam. Expect them to draw on:

- **Developer Productivity** → built-in tool selection (**2.15**: Grep → Read → trace; Edit→Read/Write fallback), MCP integration (**2.11–2.14**), and incremental codebase understanding / context management (**5.4**: scratchpads, Explore subagent, `/compact`).
- **Structured Data Extraction** → schema-enforced output (**4.3**: nullable fields, `tool_choice`), validation-retry limits (**4.4**: retries fail when info is absent), few-shot for varied formats (**4.2**), batch design (**4.5**), and human-review calibration (**5.5**: stratified sampling, field-level confidence).

**Part C below supplies original practice questions for both scenarios, targeting exactly these rules.**

---

## Part C — Practice Questions for the Uncovered Scenarios

> Original, exam-format questions written to fill the two scenario gaps. Each names the rule(s) it tests and follows the same distractor logic as the official samples. Answer key is inline; if you want a quiz version with answers hidden, see the note at the end.

### Scenario: Developer Productivity with Claude

**Q13.** Your agent must find every call site of a deprecated function `legacyAuth()` across a large, unfamiliar codebase before refactoring the callers. What is the most effective first tool to use? *(Rule 2.15)*

A) Use **Glob** for `**/*.{js,ts}` to list all source files, then **Read** each one to locate the calls.
B) Use **Grep** to search file *contents* for `legacyAuth` across the codebase, then **Read** the matching files to understand each call site.
C) **Read** the entire `src/` directory into context so the agent has full visibility before refactoring.
D) Use **Bash** `find . -name "*.js"` to enumerate files, then have the agent infer which ones likely contain the function.

**Correct: B.** Grep searches file *contents* for the symbol — the right tool for locating callers. Glob (A) matches file *paths*, not contents, and reading every file wastes context. Option C exhausts the context window with irrelevant files and violates incremental exploration (Grep → Read → trace). Option D enumerates files but never searches their contents, forcing the agent to guess.

**Q14.** The agent is updating a config value that appears identically in twelve places within one file. Its `Edit` calls keep failing because the target text isn't unique. What is the correct way to make the change reliably? *(Rule 2.15)*

A) Retry the same **Edit** repeatedly and hope one instance resolves uniquely.
B) Split the file into twelve smaller files so each occurrence becomes unique, then Edit each.
C) Bypass Claude's file tools and use **Bash** `sed -i` to do the replacement.
D) **Read** the full file, apply all twelve changes in memory, and **Write** the updated file back.

**Correct: D.** When Edit can't find a unique anchor, Read + Write is the documented fallback for reliable modification. A repeats the failing approach; B is destructive over-engineering; C is a Unix workaround that strips Claude's awareness of the change and the surrounding file state.

**Q15.** Every developer should get an internal Postgres MCP server when they open the repo, with each developer's connection string supplied without committing secrets to version control. How should you configure it? *(Rule 2.11)*

A) In project-scoped `.mcp.json`, referencing the credential via environment-variable expansion (e.g., `${DATABASE_URL}`).
B) In each developer's user-scoped `~/.claude.json`, with their connection string hardcoded.
C) In the project `CLAUDE.md`, with the connection string in a fenced code block.
D) In project-scoped `.mcp.json` with the connection string written inline so it's identical for everyone.

**Correct: A.** Project scope shares the server with the whole team via version control, and env-var expansion keeps the secret out of the committed file. B isn't shared automatically (user scope); C puts server config — and a secret — in the wrong file; D commits a secret and wrongly assumes one shared credential.

**Q16.** Engineers waste many tool calls exploring which database tables exist before they can write queries. Your MCP server already knows the schema. What's the most efficient way to give the agent visibility? *(Rule 2.13)*

A) Add a `list_all_tables` tool and instruct the system prompt to always call it first.
B) Paste the full schema into `CLAUDE.md` so it loads into every session.
C) Expose the schema as an **MCP resource** so the agent sees available tables/columns without exploratory tool calls.
D) Have the agent **Grep** the migration files to reconstruct the schema each session.

**Correct: C.** Resources are the mechanism for exposing content catalogs (schemas, issue summaries, docs) to cut exploratory calls. A still spends a tool call every session and relies on prompt compliance; B bloats every session's context whether or not the schema is needed; D wastefully reconstructs data that's already available.

**Q17.** During a long session mapping a legacy monolith, the agent starts giving inconsistent answers and referencing "typical patterns" instead of the specific classes it identified earlier. What most effectively preserves accuracy as exploration continues? *(Rule 5.4)*

A) Increase `max_tokens` so the agent can hold more of the conversation in each response.
B) Have the agent record key findings (class names, dependencies, entry points) in a **scratchpad file** and reference it for later questions.
C) Restart from scratch and re-explore the entire codebase for each new question.
D) Instruct the agent to "remember everything important and never generalize."

**Correct: B.** Context degradation in extended sessions is countered by persisting findings to a scratchpad (alongside subagent delegation and `/compact`). A confuses output length with context retention; C is wasteful re-exploration; D is a prompt-based plea against a mechanical limit.

**Q18.** You need Jira integration for the agent (a maintained community Jira MCP server exists with the tools you need) and integration with an internal proprietary deployment system that has no existing connector. How should you proceed? *(Rules 2.14, 2.12)*

A) Use the community Jira MCP server, and build a custom MCP server only for the proprietary deployment system.
B) Build custom MCP servers for both so they share one codebase and coding style.
C) Extend the community Jira server with the proprietary deployment tools so everything lives in one server.
D) Skip MCP for Jira and have the agent use **Bash** with the Jira CLI instead.

**Correct: A.** Prefer community servers for standard integrations (Jira) and reserve custom builds for team-specific workflows (the proprietary system). Both servers' tools are available simultaneously anyway. B rebuilds a solved problem; C shoehorns unrelated functionality into the wrong server; D abandons the better-integrated path for a workaround.

### Scenario: Structured Data Extraction

**Q19.** Your system extracts invoice fields, but some invoices omit a PO number entirely, and in production the model fabricates plausible-looking PO numbers when the field is absent. Which schema change best prevents this? *(Rule 4.3)*

A) Add a system-prompt instruction: "Never guess a PO number; leave it blank if missing."
B) Mark the PO-number field **required** so the model is forced to locate it.
C) Make the PO-number field **optional/nullable** so the model can return `null` when it's absent.
D) Add a post-processing regex that strips any PO number not matching the expected format.

**Correct: C.** Designing absent-info fields as nullable lets the model return null instead of fabricating to satisfy a required field. A is a probabilistic prompt instruction; B makes it worse by forcing a value; D removes some bad values but neither stops fabrication nor recovers the genuinely missing ones.

**Q20.** Your pipeline receives documents of unknown type (invoice, receipt, or contract), each with its own extraction tool/schema. You must guarantee structured output rather than conversational text while letting the model pick the right schema. Which `tool_choice` setting fits? *(Rule 4.3)*

A) `tool_choice: "auto"` — lets the model decide whether to call a tool at all.
B) `tool_choice: {"type":"tool","name":"extract_invoice"}` — forces the invoice schema every time.
C) Omit `tool_choice` and rely on a detailed system prompt describing each schema.
D) `tool_choice: "any"` — forces a tool call but lets the model choose which schema applies.

**Correct: D.** `"any"` guarantees a tool call (structured output) while leaving schema selection to the model — exactly right when the document type is unknown. A permits a text response; B forces the wrong schema on non-invoices; C relies on prompt compliance with no guarantee.

**Q21.** Your validation-retry loop appends the validation error and resubmits on failure. It reliably fixes some failures but never succeeds on one category no matter how many times it loops. Which category is that? *(Rule 4.4)*

A) Required information that is simply **absent from the source document**.
B) Dates returned in the wrong format (DD/MM vs ISO 8601).
C) Numeric fields returned as strings instead of numbers.
D) Line items placed in the wrong array position.

**Correct: A.** Retries fix format and structural errors (B, C, D) because the information exists and only needs reshaping. When the data isn't in the source at all, no amount of retrying conjures it — detect this and route differently rather than loop.

**Q22.** Some invoices have a stated total that doesn't equal the sum of their line items — a real data-quality issue you must flag, not silently "fix." Strict JSON schema via tool use guarantees valid syntax but won't catch this. What's the most effective design? *(Rules 4.4, 4.3)*

A) Add "make sure the totals add up" to the extraction prompt.
B) Extract a `calculated_total` (summed from line items) alongside the document's `stated_total`, and set a `conflict_detected` boolean on any discrepancy.
C) Tighten the JSON schema so the total field only accepts the correct value.
D) Reject and retry any extraction where the totals don't match until they agree.

**Correct: B.** Semantic errors survive schema validation, so design self-correction flows that surface the conflict (calculated vs stated, `conflict_detected`) for downstream handling. A is a prompt plea; C can't express a cross-field arithmetic constraint in JSON schema; D destroys the real signal by forcing agreement on genuinely inconsistent source data.

**Q23.** Accuracy drops on academic papers depending on layout: the model misses citations when they're inline (Smith 2020) in some documents and when they're in an end-of-document bibliography in others. Detailed prose instructions haven't fixed it. What's the most effective next step? *(Rule 4.2)*

A) Add a longer, more explicit paragraph to the prompt describing both citation styles.
B) Split into two pipelines and use a classifier to route documents by citation style first.
C) Switch to a larger model with a longer context window.
D) Add **2–4 few-shot examples** demonstrating correct extraction from both inline-citation and bibliography-style documents.

**Correct: D.** Few-shot examples are the most effective lever for handling varied document structures when prose instructions produce inconsistent results. A is more prose (already shown not to work); B over-engineers with a classifier before trying examples; C throws compute at a prompt-design problem.

**Q24.** You run two extraction workloads: (1) a real-time API that extracts fields the moment a user uploads a document and shows results on screen, and (2) an overnight job that re-extracts your entire historical archive for a quarterly audit. You want to cut costs. How should you apply the Message Batches API? *(Rule 4.5)*

A) Use the Batches API for both, polling for status on the live flow and showing a spinner until results return.
B) Keep both synchronous to avoid `custom_id` correlation overhead.
C) Use the Batches API for the overnight archive job only; keep synchronous calls for the live upload flow.
D) Use the Batches API for both, with a timeout fallback to synchronous on the live flow.

**Correct: C.** The Batches API offers 50% savings but has up to a 24-hour window and no latency SLA — fine for the overnight audit, unacceptable for a user waiting on screen. A makes users wait an unbounded time; B foregoes savings on a workload that's an ideal batch fit; D adds complexity to paper over the wrong tool for a blocking flow.

**Q25.** Your extraction system reports 97% overall field accuracy, and a manager proposes removing human review entirely. Before automating, what's the most important validation to perform? *(Rule 5.5)*

A) **Segment accuracy by document type and field**, using stratified random sampling, to confirm no specific type or field performs poorly.
B) Re-run the whole test set and confirm the aggregate is still ~97%.
C) Increase the sample size until the overall accuracy confidence interval is narrow.
D) Have the model self-report a confidence score per extraction and trust the high-confidence ones.

**Correct: A.** An aggregate number can mask poor performance on a specific document type or field; stratified sampling and per-segment analysis catch that before you reduce review. B and C only refine the same aggregate that's hiding the problem; D relies on self-reported confidence, which must be calibrated against labeled data before it can be trusted.

> **Quiz mode:** to run these as a team self-test, cover the **Correct: X** line and the explanation under each question. Answer key — 13:B · 14:D · 15:A · 16:C · 17:B · 18:A · 19:C · 20:D · 21:A · 22:B · 23:D · 24:C · 25:A. (Positions are shuffled and balanced across A–D — 4×A, 3×B, 3×C, 3×D.)

---

## The three recurring distractor patterns (drill these)

1. **Probabilistic where deterministic is required** — system-prompt mandates or few-shot offered for hard business/safety ordering (Q1). The correct answer uses a hook or prerequisite gate.
2. **Over-engineering** — a classifier, ML model, routing layer, or bigger model proposed where a description, prompt criterion, or config change is the proportionate fix (Q2, Q3, Q12).
3. **Blaming a working component** — pinning the failure on a downstream agent/tool that executed its assignment correctly (Q7, Q8).

When two answers both "work," prefer the lowest-effort fix that addresses the **root cause** and the one that follows **least privilege**.

---

## Part D — Pattern-Recognition Drills

> These questions are built to train the three distractor patterns above, plus the "both answers work" tiebreaker. Same difficulty as the official samples. Correct-answer positions are varied; key at the end. The skill being drilled is naming *why the wrong answers are wrong* before you read the explanation.

### Pattern 1 — Probabilistic where deterministic is required

**Q26.** A refund agent must never issue a refund above $500 without human approval, yet production logs show it occasionally processes refunds of $600+. Which change provides a guarantee rather than a probability?

A) Add a sentence to the `process_refund` tool description noting the $500 ceiling.
B) Implement a tool-call interception hook that blocks `process_refund` for amounts over $500 and redirects to human escalation.
C) Add few-shot examples to the system prompt showing the agent escalating high-value refunds.
D) Instruct the system prompt: "Never process refunds over $500; always escalate them."

**Correct: B.** *(Rules 1.16/1.17)* A, C, and D are all probabilistic LLM-compliance mechanisms with a non-zero failure rate. Only the interception hook deterministically blocks the policy-violating call — and a financial consequence is exactly when you choose code enforcement over prompting.

**Q27.** Identity verification must complete *successfully* before any account-modification tool runs. Which design gives a deterministic guarantee?

A) A `PostToolUse` hook attached to `verify_identity`.
B) A system prompt mandating that verification happens first.
C) A prerequisite gate that blocks all account-modification tools until `verify_identity` has returned a verified status.
D) `tool_choice` forcing `verify_identity` on the first turn.

**Correct: C.** *(Rule 1.14)* The trap is that two options *look* deterministic. A `PostToolUse` hook (A) intercepts the *result* of verification but doesn't block *downstream* tools, so a modification can still run if verification failed. D forces verification to run first but doesn't block modifications if it comes back **unverified**. Only the prerequisite gate ties downstream execution to a *successful* verification. B is probabilistic.

**Q28.** A clinical-intake agent must record patient consent before calling `store_health_record`. Occasionally it stores the record first. The team needs guaranteed ordering. Best approach?

A) Reorder the system prompt so the consent instruction appears before the storage instruction.
B) Implement a prerequisite gate that blocks `store_health_record` until `record_consent` has returned success.
C) Add 3–4 few-shot examples demonstrating consent-before-storage.
D) Have the agent self-report, before each storage call, that it collected consent.

**Correct: B.** *(Rules 1.13/1.14)* Ordering that carries legal/safety weight needs programmatic enforcement. A, C, and D all depend on probabilistic model behavior — a non-zero failure rate that's unacceptable for protected health information.

### Pattern 2 — Over-engineering

**Q29.** A CI code-review agent produces many false positives on minor style nits, eroding developer trust. The team has never written down what counts as a reportable issue. What's the proportionate first step?

A) Write explicit review criteria defining which issues to report (bugs, security) versus skip (minor style, local patterns).
B) Fine-tune a custom model on the team's history of accepted versus dismissed review comments.
C) Add a downstream classifier that predicts developer acceptance and filters findings below a threshold.
D) Switch to a larger, higher-tier model to improve review judgment.

**Correct: A.** *(Rule 4.1)* The root cause is undefined criteria; explicit categorical criteria are the low-effort fix. B is over-engineered *and* out of scope (fine-tuning isn't part of the toolkit); C builds ML infrastructure before prompt optimization is tried; D throws compute at a specification problem.

**Q30.** Two MCP tools, `search_docs` and `search_kb`, are frequently confused by the agent. Each has a one-line description. What's the lowest-effort effective fix?

A) Merge them into a single `search_all` tool that internally decides which backend to query.
B) Train an embedding-based router that scores tool relevance for each incoming query.
C) Add a deterministic routing layer that parses the query and pre-selects a tool before each turn.
D) Expand each description with input formats, example queries, and explicit when-to-use-versus-the-other boundaries.

**Correct: D.** *(Rule 2.1)* Descriptions are the primary selection mechanism and the proportionate fix. A is a larger architectural change than warranted as a first step; B and C build routing infrastructure that bypasses the model's own selection and isn't justified before improving descriptions.

**Q31.** Your extraction prompt returns dates in inconsistent formats. You've already tried adding more detailed prose instructions, without success. What's the proportionate next step?

A) Build a fine-tuned date-normalization model trained on your historical outputs.
B) Add 2–3 few-shot examples showing the exact desired format, plus a normalization rule in the prompt.
C) Stand up a downstream microservice that reparses every emitted date through a dozen format heuristics.
D) Switch to a larger model with stronger formatting behavior.

**Correct: B.** *(Rules 4.2/4.3)* Few-shot examples with an explicit normalization rule are the documented lever when prose alone is inconsistent. A is over-engineering and out of scope; C adds standing infrastructure for a prompt-design problem; D throws compute at it.

### Pattern 3 — Blaming a working component

**Q32.** A research system's report on "impact of climate policy on agriculture" omits livestock, fisheries, and land use entirely. Logs show the coordinator created two subtasks — "carbon taxes on crop farms" and "fertilizer subsidies" — and every subagent completed its assigned subtask correctly, with synthesis combining them faithfully. Root cause?

A) The web search subagent's queries weren't broad enough.
B) The synthesis agent failed to flag the missing coverage areas.
C) The coordinator's task decomposition was too narrow, so whole domains of the topic were never assigned.
D) The document analysis agent filtered out livestock and fisheries sources.

**Correct: C.** *(Rule 1.7)* Every downstream agent did its job within the scope it was given; the failure is in the assignment itself. A, B, and D blame components that executed correctly.

**Q33.** A support request asks to (1) refund an order, (2) update the billing address, and (3) redeem loyalty points. Only the refund is completed. Logs show the agent processed the refund correctly, and both the address-update and points-redemption tools returned success on the rare occasions they were called. Most likely root cause?

A) The agent didn't decompose the multi-concern request into distinct items, so it acted on only the first issue.
B) The address-update tool silently failed despite reporting success.
C) The loyalty-points tool needs a more detailed description.
D) A refund hook blocked the other two operations.

**Correct: A.** *(Task Statement 1.4 — multi-concern decomposition)* The tools worked when invoked; the gap is that the agent never broke the request into separate items to investigate. B contradicts the logged success; C and D blame components that aren't the cause.

**Q34.** A subagent returns the status `"search unavailable"` and the coordinator immediately terminates the entire research workflow. You're diagnosing why no recovery occurred. Where is the actual design flaw?

A) The coordinator's model isn't capable enough to recover from failures.
B) The underlying web-search API is unreliable and should be swapped out.
C) The synthesis agent should have detected and compensated for the missing data.
D) The subagent returned a generic status instead of structured error context (failure type, attempted query, partial results, alternatives), leaving the coordinator nothing to act on.

**Correct: D.** *(Rule 5.3)* The recovery failure is caused by lossy error reporting, not by the model, the API, or synthesis. A, B, and C blame components that aren't the root cause.

### Tiebreaker — when two answers both "work"

**Q35.** Tool misselection between two similar tools is degrading reliability. In testing, two fixes both resolve it: rewriting the two descriptions to differentiate them, or consolidating them into one tool with internal routing. As the immediate fix, which should you prefer, and why?

A) Rewrite the descriptions — the lowest-effort change that addresses the root cause (inadequate descriptions).
B) Consolidate into one tool — it removes the choice the model was getting wrong.
C) Add a routing classifier in front of both tools.
D) Add few-shot examples of correct selection.

**Correct: A.** When multiple options work, prefer the lowest-effort fix that targets the root cause. Consolidation (B) is a valid architectural option but heavier than a first step; C over-engineers; D adds token overhead without fixing the thin descriptions.

**Q36.** A synthesis agent occasionally needs to verify a date or name mid-task. Two designs both eliminate the latency problem in testing: give it a scoped `verify_fact` tool, or give it full access to the web-search toolset. Which is the better choice, and on what principle?

A) Full web-search access — maximum flexibility to handle any verification it encounters.
B) The scoped `verify_fact` tool — it meets the need under least privilege, preventing cross-specialization misuse.
C) Route every verification back through the coordinator regardless of how simple it is.
D) Give it both, for redundancy.

**Correct: B.** *(Rule 2.9)* Both reduce latency, so the tiebreaker is least privilege: the narrow tool satisfies the common case without letting a synthesis agent drift into web-search behavior it should never own. A over-provisions; C reintroduces the latency the change was meant to remove; D maximizes privilege — the opposite of the principle.

---

**Part D answer key:** 26:B · 27:C · 28:B · 29:A · 30:D · 31:B · 32:C · 33:A · 34:D · 35:A · 36:B

**How to use these as a drill:** for each question, before checking the key, write one phrase naming *which pattern each wrong option commits* — "probabilistic," "over-engineered," "blames working component," or "over-provisions." Engineers who can label the distractors reliably tend to clear the scenario questions even on unfamiliar surface details, because the exam recycles these three traps far more than it recycles specific facts.
