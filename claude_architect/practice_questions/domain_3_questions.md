# Domain 3 Practice Questions: Claude Code Configuration & Workflows
### 25 Questions | CCAF Exam Preparation

**Pass threshold: 23/25 (90%)**

---

**Q1.** A new developer cloned the team repository and found that Claude Code doesn't follow the team's testing conventions. Other developers see the conventions applied correctly. The most likely cause is:

A) The developer's Claude Code version is outdated  
B) Testing conventions are in `~/.claude/CLAUDE.md` on one developer's machine rather than in the project-level `.claude/CLAUDE.md` committed to the repo  
C) The developer needs to run `/memory` to load the conventions  
D) Testing conventions require a directory-level CLAUDE.md in the test directory  

---

**Q2.** You want to create a `/security-review` slash command available to all developers when they clone the repository. Where should this command file be created?

A) `~/.claude/commands/security-review.md`  
B) `.claude/commands/security-review.md` in the project repository  
C) `CLAUDE.md` with a `COMMANDS:` section  
D) `.claude/settings.json` with a commands array  

---

**Q3.** Your codebase has test files scattered throughout multiple directories (`src/auth/auth_test.py`, `src/payments/payment_test.py`, `src/api/endpoint_test.py`). You want one set of test conventions applied to ALL test files. The BEST approach is:

A) Create a directory-level CLAUDE.md in `src/` with test conventions  
B) Create a `.claude/rules/` file with YAML frontmatter `paths: ["**/*_test.py"]`  
C) Add test conventions to the root CLAUDE.md and note they apply to test files  
D) Create a CLAUDE.md in each directory containing test files  

---

**Q4.** A skill file has this frontmatter:
```yaml
---
context: fork
allowed-tools: Read, Grep, Glob
argument-hint: "module name to analyze"
---
```
What does `context: fork` accomplish?

A) Creates a git branch before executing the skill  
B) Runs the skill in an isolated sub-agent context so verbose output doesn't pollute the main conversation  
C) Enables concurrent execution of multiple skill invocations  
D) Forks the current session to allow rollback after the skill completes  

---

**Q5.** You are refactoring a monolith into microservices. This involves 50+ files, multiple architectural decisions about service boundaries, and will take several days. Which Claude Code mode should you use initially?

A) Direct execution — start making changes and let implementation reveal architecture  
B) Plan mode — explore the codebase, understand dependencies, design the approach before making any changes  
C) A combination: plan mode to map the system, then direct execution for each service  
D) Plan mode is only needed for tasks over 100 files — direct execution is fine here  

---

**Q6.** A developer places personal workflow preferences (specific code style they prefer) in `~/.claude/CLAUDE.md`. A teammate wants the same preferences. What must the teammate do?

A) Copy the file to their own `~/.claude/CLAUDE.md`  
B) Nothing — user-level settings are automatically shared across the team  
C) Ask the first developer to move the settings to project-level config  
D) Create a symlink to the first developer's config file  

---

**Q7.** The `@import` syntax in CLAUDE.md is used to:

A) Import code libraries Claude can reference during generation  
B) Reference external markdown files to keep CLAUDE.md modular — the imported content is loaded as if it were inline  
C) Import project configuration from package.json or similar files  
D) Include MCP server configurations in the CLAUDE.md  

---

**Q8.** Your CI/CD pipeline runs `claude "Review this PR for security vulnerabilities"` but the job hangs indefinitely. What is the fix?

A) Add `--timeout 300` to the command  
B) Set `CLAUDE_INTERACTIVE=false` environment variable  
C) Use `claude -p "Review this PR for security vulnerabilities"` — the -p flag enables non-interactive mode  
D) Redirect stdin: `claude "Review this PR" < /dev/null`  

---

**Q9.** You need Claude Code CI reviews to output machine-parseable JSON that can be automatically posted as inline PR comments. The correct flags are:

A) `--format json --schema review.json`  
B) `--output-format json --json-schema ./review-schema.json`  
C) `--json --validate-schema review-schema.json`  
D) `--structured-output --schema review.json`  

---

**Q10.** Why is using the same Claude Code session that generated code less effective for reviewing that code?

A) The session has too many tokens used up to perform quality analysis  
B) The model retains reasoning context from generation, making it less likely to question its own decisions  
C) Code review requires a specialized model configuration not available in the generation session  
D) The generation session lacks access to the review-specific tools  

---

**Q11.** Which scenario is BEST suited for plan mode rather than direct execution?

A) Fixing a null pointer exception with a clear stack trace pointing to line 47  
B) Adding input validation to a single form field  
C) Migrating from React 17 to React 18 across a 200-file codebase with breaking API changes  
D) Updating a configuration constant from `30` to `60`  

---

**Q12.** A skill produces 8,000 tokens of verbose codebase exploration output that fills the main conversation context. The fix is:

A) Reduce the skill's `max_tokens` setting  
B) Add `context: fork` to the skill's YAML frontmatter — exploration runs in isolated context, only the summary returns  
C) Break the skill into smaller steps that each produce less output  
D) Use `/compact` after running the skill to reduce context usage  

---

**Q13.** The `allowed-tools` frontmatter in a skill file:

A) Lists tools the skill is allowed to REQUEST from the user  
B) Restricts which tools are available during skill execution, preventing unintended actions  
C) Specifies which MCP servers to connect to during skill execution  
D) Defines tools that should be automatically called before the skill starts  

---

**Q14.** You want test conventions that span `src/` AND `tests/` directories plus any `__tests__` subdirectory anywhere in the codebase. Directory-level CLAUDE.md files cannot easily handle this. The correct solution uses:

A) A root CLAUDE.md with a section header "For Test Files:"  
B) `.claude/rules/` file with `paths: ["src/**/*_test.*", "tests/**/*", "**/__tests__/**/*"]`  
C) Three separate directory-level CLAUDE.md files (src/, tests/, and a global one for __tests__)  
D) A skill that loads test conventions when invoked with `/test`  

---

**Q15.** Your team generates automated PR reviews that are re-run on every new commit. Developers complain about duplicate comments on issues already reported. The fix is:

A) Clear all existing comments before each review run  
B) Include prior review findings in the context and instruct Claude to report only new or unaddressed issues  
C) Run reviews only on files that changed since the last review  
D) Add a deduplication post-processing script that removes duplicate comments  

---

**Q16.** The `argument-hint` frontmatter field in a skill:

A) Provides Claude with hints about how to interpret the skill's arguments  
B) Displays a prompt to the developer asking for required parameters when they invoke the skill without arguments  
C) Validates that the argument matches a specific format before execution  
D) Sets default argument values when the skill is invoked without parameters  

---

**Q17.** When using the interview pattern before implementing a feature, you ask Claude to "interview" you about requirements. The PRIMARY benefit is:

A) Claude generates more detailed code when it understands the requirements fully  
B) It surfaces design considerations, edge cases, and constraints you may not have anticipated, preventing incorrect implementations  
C) It reduces the number of API calls needed for the implementation  
D) It creates documentation automatically from the interview responses  

---

**Q18.** You have multiple interacting bugs where fix A changes the behavior that fix B depends on. How should you submit these to Claude for fixing?

A) Fix them one at a time — always iterate sequentially for safety  
B) Provide both issues in a single message since they interact — fixing them separately may cause regressions  
C) Fix the root cause first (whichever is lower-level), then fix the dependent issue  
D) Use plan mode to map the interactions before fixing either  

---

**Q19.** The Explore subagent in Claude Code is used to:

A) Search the internet for relevant information about the task  
B) Isolate verbose codebase discovery output so it doesn't fill the main conversation context  
C) Explore multiple implementation approaches in parallel  
D) Execute shell commands in an isolated environment  

---

**Q20.** CLAUDE.md should contain which type of content?

A) One-time instructions specific to the current task  
B) Project standards, conventions, and context that should always apply across all sessions  
C) Personal workflow preferences specific to each developer  
D) Dynamic information like current sprint goals and team availability  

---

**Q21.** A `.claude/rules/` file with `paths: ["terraform/**/*"]` will activate:

A) For all files when working in a project that contains a terraform directory  
B) Only when Claude is editing files within the `terraform/` directory tree  
C) Whenever the word "terraform" appears in any file being edited  
D) For all infrastructure-related files regardless of location  

---

**Q22.** During a multi-phase codebase investigation, your context window is filling up with verbose file analysis outputs. The BEST Claude Code command to use at this point is:

A) `/clear` — clears the context and starts fresh  
B) `/compact` — summarizes the conversation to reduce context usage while preserving key findings  
C) `/save` — saves the session to disk and resumes fresh  
D) `/memory` — refreshes the memory files  

---

**Q23.** A developer wants a personal variant of the team's `/review` skill that applies stricter checks — but only for their sessions, without affecting teammates. Where should they create the personal variant?

A) Override `.claude/skills/review.md` with their stricter version  
B) Create `~/.claude/skills/my-strict-review.md` with a different name — user-scoped skills don't affect team members  
C) Create `.claude/skills/strict-review.md` in the project repo  
D) Modify `~/.claude/CLAUDE.md` to add stricter review criteria  

---

**Q24.** Providing concrete input/output examples is more effective than prose descriptions when:

A) The task is too complex to explain in prose  
B) Prose descriptions produce inconsistent interpretations — examples demonstrate the exact transformation expected  
C) The task involves multiple steps and sequence matters  
D) Claude lacks domain knowledge about the subject  

---

**Q25.** The `/memory` command is used to:

A) Save the current conversation to permanent memory  
B) Verify which memory files (CLAUDE.md files) are loaded in the current session to diagnose configuration issues  
C) Load a previously saved memory snapshot  
D) Clear the conversation history while retaining CLAUDE.md instructions  

---

## Answer Key

| Q | Answer | Key Concept |
|---|--------|-------------|
| 1 | B | User-level vs project-level CLAUDE.md scope |
| 2 | B | Project commands in .claude/commands/ (version controlled) |
| 3 | B | .claude/rules/ with glob paths for cross-directory conventions |
| 4 | B | context:fork = isolated sub-agent, output doesn't pollute main session |
| 5 | B | Plan mode for architectural, multi-file, high-complexity tasks |
| 6 | A | User-level settings are personal — teammates must configure separately |
| 7 | B | @import for modular, externally-referenced CLAUDE.md sections |
| 8 | C | -p / --print flag for non-interactive CI mode |
| 9 | B | --output-format json --json-schema for structured CI output |
| 10 | B | Session retains reasoning context — self-review bias |
| 11 | C | Multi-file migration with architectural decisions = plan mode |
| 12 | B | context:fork isolates verbose skill output |
| 13 | B | allowed-tools restricts tool access during skill execution |
| 14 | B | .claude/rules/ with multi-path glob patterns |
| 15 | B | Include prior findings, report only new/unaddressed issues |
| 16 | B | argument-hint prompts for required parameters |
| 17 | B | Surfaces unanticipated considerations before implementation |
| 18 | B | Interacting bugs → single message with both issues |
| 19 | B | Explore = isolate verbose discovery from main context |
| 20 | B | Universal project standards — always loaded |
| 21 | B | Path-scoped rules activate only for matching files |
| 22 | B | /compact summarizes without losing key findings |
| 23 | B | Personal skill variants in ~/.claude/skills/ |
| 24 | B | Examples > prose when prose produces inconsistency |
| 25 | B | /memory verifies which config files are loaded |
