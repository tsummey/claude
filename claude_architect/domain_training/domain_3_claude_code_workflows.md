# Domain 3: Claude Code Configuration & Workflows
### CCAF Exam Weight: 20%

---

## Overview

Claude Code is not just a coding assistant — it is a configurable, extensible development
platform. This domain tests whether you understand the full configuration hierarchy, can
design team workflows that scale, know when to use plan mode vs. direct execution, and can
integrate Claude Code into automated pipelines.

These concepts are highly practical. Every question in this domain tests judgment about
real configuration decisions you would make building a team's Claude Code setup.

**Scenarios this domain covers:**
- Scenario 2: Code Generation with Claude Code
- Scenario 4: Developer Productivity with Claude
- Scenario 5: Claude Code for CI/CD

---

## Task Statement 3.1 — CLAUDE.md Configuration Hierarchy

### The Three Levels

```
~/.claude/CLAUDE.md          ← USER level: personal only, NOT version controlled
                                 Only applies to YOUR sessions
                                 Teammates never see this

project/.claude/CLAUDE.md    ← PROJECT level: version controlled, team-wide
  OR                            All developers who clone the repo get this
project/CLAUDE.md              This is where team standards live

project/src/CLAUDE.md        ← DIRECTORY level: applies when working in that directory
project/api/CLAUDE.md          Overrides project-level for files in that subdirectory
```

### The #1 Team Configuration Mistake

A developer puts team standards in `~/.claude/CLAUDE.md` on their machine.
New teammates join. They clone the repo. They don't get the standards.
Claude behaves differently for every developer on the team.

**Diagnosis:** Use `/memory` command to see which memory files are loaded.
If team standards only appear in one developer's session, they're in user-level config.

**Fix:** Move standards to project-level `.claude/CLAUDE.md` so they're version controlled.

### What Goes in CLAUDE.md

```markdown
# Project: PaymentService API

## Architecture
- REST API built with FastAPI
- PostgreSQL database via SQLAlchemy ORM
- Redis for session caching
- All monetary values stored as integers (cents), never floats

## Code Standards
- Type hints required on all function signatures
- All database operations must be wrapped in try/except with rollback
- Never log PII (customer names, emails, payment info)
- Use Pydantic models for all request/response schemas

## Testing
- pytest with fixtures in conftest.py
- Mock external services with pytest-mock
- Test files live adjacent to source files (payment.py → payment_test.py)
- Minimum coverage: 80% for new code

## Commands
- Run tests: `pytest tests/ -v`
- Start dev server: `uvicorn app.main:app --reload`
- Format code: `black . && isort .`

@import ./docs/api-conventions.md
@import ./docs/database-patterns.md
```

### The @import Syntax

Use `@import` to keep CLAUDE.md modular. Instead of one monolithic file, each package
maintainer includes only the standards relevant to their domain:

```markdown
# In packages/billing/CLAUDE.md
@import ../../docs/shared-standards.md
@import ../../docs/billing-specific-rules.md
@import ../../docs/pci-compliance-rules.md
# Note: NOT importing frontend-standards.md — not relevant here
```

### .claude/rules/ — Topic-Specific Organization

For large codebases, split conventions into focused files:

```
.claude/rules/
├── testing.md          # Test conventions, fixture patterns, coverage requirements
├── api-conventions.md  # REST design, versioning, error response formats
├── database.md         # ORM patterns, migration rules, query optimization
├── security.md         # Auth, input validation, secret handling
└── deployment.md       # CI/CD standards, environment config, rollback procedures
```

Rules files use YAML frontmatter to scope when they load (see Task 3.3).

---

## Task Statement 3.2 — Custom Slash Commands and Skills

### Commands vs. Skills — Know the Difference

| Feature | Commands (`.claude/commands/`) | Skills (`.claude/skills/`) |
|---|---|---|
| Invocation | `/command-name` | `/skill-name` |
| Isolation | Runs in main conversation | Can run isolated (`context: fork`) |
| Tool restriction | No | Yes (`allowed-tools`) |
| Argument hint | No | Yes (`argument-hint`) |
| Best for | Simple prompts, one-off tasks | Complex workflows, reusable processes |

### Project vs. User Scope

```
.claude/commands/review.md      ← Project-scoped: shared via version control
.claude/commands/deploy-check.md    All team members get these automatically

~/.claude/commands/my-workflow.md ← User-scoped: personal, not shared
```

### Creating a Project-Scoped Slash Command

```markdown
<!-- .claude/commands/review.md -->
Review the staged changes in this PR against our team standards:

1. Check for type hints on all new function signatures
2. Verify database operations have proper error handling and rollback
3. Confirm no PII is being logged
4. Check test coverage for new code paths
5. Verify Pydantic models are used for all new endpoints

For each issue found, provide: file, line, issue description, suggested fix.
Format as a markdown table.
```

Usage: `/review` — available to all developers after cloning.

### Skills with Frontmatter

```markdown
---
context: fork
allowed-tools: Read, Grep, Glob
argument-hint: "component name or 'all'"
---

# Skill: Analyze Component

Analyze the component specified: $ARGUMENTS

1. Use Glob to find all files related to this component
2. Use Read to examine each file
3. Use Grep to find all callers and consumers
4. Produce a dependency map and complexity assessment
5. Return a structured summary

Do NOT write any files during this analysis.
```

### The `context: fork` Option

When a skill runs in `context: fork`:
- It executes in an isolated sub-agent context
- Its verbose output (file reads, tool calls, intermediate thinking) does NOT appear in your main conversation
- Only the final summary is returned to the main session

**Use `context: fork` when:**
- The skill does a lot of exploratory work (reading many files, running many searches)
- You don't want the exploration to fill your context window
- The skill output is intermediate data, not the final answer

```markdown
---
context: fork          # Isolated — exploration stays out of main context
allowed-tools: Read, Grep, Glob, Bash   # Only these tools available during skill
argument-hint: "ticket number (e.g., PROJ-1234)"
---

# Skill: Investigate Ticket

Research the codebase for context on ticket: $ARGUMENTS
...
```

### Choosing Skills vs. CLAUDE.md

| Use | Mechanism |
|---|---|
| Standards that always apply (coding style, test patterns) | CLAUDE.md |
| Workflows invoked on-demand (code review, investigation, deployment check) | Skills/Commands |
| Personal workflow variants | `~/.claude/skills/` with different name |

---

## Task Statement 3.3 — Path-Specific Rules

### The Problem CLAUDE.md Can't Solve

CLAUDE.md files are directory-bound. If your test files are scattered throughout the
codebase (`src/auth/auth.test.ts`, `src/payments/payment.test.ts`, etc.) and you want
a single set of test conventions applied to ALL of them, you'd need a CLAUDE.md in every
directory — or you use path-specific rules.

### .claude/rules/ with YAML Frontmatter

```markdown
---
paths:
  - "**/*.test.tsx"
  - "**/*.test.ts"
  - "**/__tests__/**/*"
---

# Testing Conventions

All test files must follow these conventions:

## Structure
- One `describe` block per component/function being tested
- Use `it()` not `test()` for consistency
- Arrange-Act-Assert pattern for all test cases

## Mocking
- Use `jest.spyOn()` not manual assignment for mocking methods
- Always restore mocks in `afterEach()`
- Never mock the module under test — test real behavior

## Coverage
- Happy path: required
- Error paths: required for all try/catch blocks
- Edge cases: empty arrays, null values, boundary conditions
```

```markdown
---
paths:
  - "terraform/**/*"
  - "infrastructure/**/*.tf"
---

# Terraform Conventions

- Use variables for all environment-specific values
- Never hardcode region — use var.aws_region
- Tag all resources with: Environment, Project, Owner, CostCenter
- Run `terraform fmt` before committing
- State files: never commit, always use remote state (S3 + DynamoDB lock)
```

### Path Rules vs. Directory CLAUDE.md

| Scenario | Use |
|---|---|
| Convention applies to files in ONE directory | Directory `CLAUDE.md` |
| Convention applies to files by TYPE across many directories | `.claude/rules/` with glob |
| Convention applies to all test files regardless of location | `.claude/rules/` with `**/*.test.*` |
| Convention applies to all Terraform files regardless of location | `.claude/rules/` with `**/*.tf` |

---

## Task Statement 3.4 — Plan Mode vs. Direct Execution

### The Decision Framework

```
Is the task well-understood with clear scope?
├── YES → Direct execution
│         Examples: Fix this specific bug (stack trace provided)
│                   Add input validation to this one function
│                   Update this config value
│
└── NO → Plan mode
          Examples: Restructure monolith into microservices
                    Migrate from library A to library B (45+ files affected)
                    Add comprehensive test coverage to legacy codebase
                    New feature with multiple valid implementation approaches
```

### What Plan Mode Does

In plan mode, Claude:
1. Explores the codebase (reads files, traces dependencies)
2. Identifies all affected areas
3. Considers multiple approaches
4. Presents a structured implementation plan
5. **Does NOT make any changes** until you approve

This prevents the worst outcome in agentic coding: making 47 changes based on a
misunderstanding of the architecture, then having to revert everything.

### The Explore Subagent

For tasks requiring extensive codebase discovery before planning, use the Explore subagent:

```
Without Explore: Discovery output fills your main context window
                 → You hit context limits before implementation begins

With Explore:    Exploration runs in isolated context
                 → Returns a structured summary
                 → Your main context only gets the summary
                 → Plenty of room left for implementation
```

**When to use Explore:**
- Analyzing a large codebase before deciding how to proceed
- Mapping all usages of a function/pattern before changing it
- Understanding a legacy system before touching it

### Combining Plan Mode + Direct Execution

The expert workflow:
```
1. Enter plan mode → understand the codebase and design the approach
2. Approve the plan
3. Switch to direct execution → implement the approved plan
4. Each implementation step has clear scope because the plan defined it
```

This is better than either mode alone. Plan mode prevents bad architectural decisions.
Direct execution keeps implementation fast once the plan is clear.

---

## Task Statement 3.5 — Iterative Refinement Techniques

### When Prose Instructions Fail, Use Examples

If Claude keeps misunderstanding what you want, stop writing better descriptions.
Write 2-3 concrete input/output examples instead.

```python
# WEAK: Prose description (interpreted inconsistently)
"Normalize the phone number to a standard format"

# STRONG: Concrete examples (unambiguous)
"""
Normalize phone numbers to E.164 format:

Input: "555-123-4567"        → Output: "+15551234567"
Input: "(555) 123-4567"      → Output: "+15551234567"
Input: "+1 555 123 4567"     → Output: "+15551234567"
Input: "5551234567"          → Output: "+15551234567"
Input: "not a phone number"  → Output: null
"""
```

### Test-Driven Iteration

Write the test suite BEFORE asking Claude to implement. Then share test failures
as feedback for each iteration:

```
Iteration 1: Claude implements function
Iteration 2: You run tests → 3 failures → share failures with Claude
Iteration 3: Claude fixes failures → 1 failure remains → share it
Iteration 4: All tests pass
```

This is dramatically more efficient than describing what's wrong in prose.

### The Interview Pattern

Before implementing a complex feature, ask Claude to interview you:

```
"Before implementing this caching layer, ask me questions about requirements,
edge cases, and constraints that you need to know to implement it correctly."
```

Claude will surface considerations you hadn't thought of:
- "What should happen when the cache is full?"
- "Should cache keys be case-sensitive?"
- "What's the TTL strategy for different data types?"

Answer these questions FIRST. Then implement. This avoids the common failure mode of
getting 80% done and discovering a fundamental assumption was wrong.

### Sequential vs. Parallel Issue Resolution

```python
# Issues that INTERACT → fix all in ONE message
# Example: Auth bug + session bug are related
"Fix these two issues together. They interact: [issue 1] [issue 2]"

# Issues that are INDEPENDENT → fix sequentially
# Example: unrelated typo + unrelated performance issue
"Fix issue 1 first."
# (After fix) "Now fix issue 2."
# Sequential iteration lets you verify each fix before the next
```

---

## Task Statement 3.6 — CI/CD Integration

### The -p Flag — Non-Interactive Mode

```bash
# WRONG: Hangs forever in CI waiting for user input
claude "Review this PR for security issues"

# CORRECT: Non-interactive, outputs to stdout, exits
claude -p "Review this PR for security issues"
# Alias: --print
```

This is the #1 thing to know for CI/CD integration. Without `-p`, the job hangs.

### Structured Output in CI

```bash
# Get machine-parseable JSON output for automated processing
claude -p "Analyze the diff for security vulnerabilities" \
  --output-format json \
  --json-schema ./schemas/security-review-schema.json

# Output can be piped to a script that posts inline PR comments
claude -p "..." --output-format json | python post_pr_comments.py
```

### CLAUDE.md for CI Context

CI runs Claude in a fresh session with no project knowledge. CLAUDE.md provides
the context it needs:

```markdown
# CI Review Context

## This is an automated review session

## What to review:
- Security vulnerabilities (SQL injection, XSS, auth bypass, secrets in code)
- Logic errors that would cause test failures
- Missing error handling in new code paths

## What NOT to report:
- Style issues (handled by linter)
- Minor naming conventions (handled by linter)
- Formatting (handled by formatter)
- Subjective architectural opinions

## Severity definitions:
- CRITICAL: Will cause production incident or security breach
- HIGH: Likely to cause bugs in production
- MEDIUM: Could cause issues under certain conditions
- LOW: Minor improvement opportunity

## Output format:
Return findings as a JSON array matching the schema provided.
```

### Session Isolation for Code Review

A key insight for CI review quality:

```
WRONG: Use same Claude session that wrote the code to review it
       → Claude retains reasoning context → less likely to question its own decisions

RIGHT: Use a FRESH Claude instance with no prior context
       → Independent review → more likely to catch subtle issues
```

In CI, this happens naturally — every job starts fresh.

### Avoiding Duplicate Comments on Re-runs

When a PR gets new commits, re-running the review can flood the PR with duplicate
comments on issues already reported:

```bash
# Pass prior findings when re-running
claude -p "Review the NEW changes in this PR. 
Prior review findings are provided below — only report NEW issues 
or PREVIOUSLY REPORTED issues that have not been fixed.

Prior findings:
$(cat prior_findings.json)

New diff:
$(git diff main...HEAD)" \
  --output-format json \
  --json-schema ./schemas/review-schema.json
```

---

## Key Concepts Summary — Domain 3

| Concept | What to Know |
|---|---|
| CLAUDE.md hierarchy | user (personal) → project (team) → directory (local) |
| @import | Keeps CLAUDE.md modular; includes domain-specific standards |
| .claude/rules/ | Path-scoped rules with YAML frontmatter glob patterns |
| Project commands | `.claude/commands/` → version controlled, team-wide |
| Skills | `.claude/skills/` → frontmatter: context:fork, allowed-tools, argument-hint |
| context: fork | Skill runs isolated; verbose output doesn't pollute main session |
| Plan mode | Complex tasks with architectural implications; no changes until approved |
| Direct execution | Well-understood, clear-scope tasks |
| Explore subagent | Isolates verbose discovery; prevents context window exhaustion |
| -p / --print | Non-interactive mode for CI/CD — without it, jobs hang |
| --output-format json | Machine-parseable output for automated processing |
| Session isolation | Fresh session reviews code better than the session that wrote it |

---

## What the Exam Will Test You On

- *"A new developer cloned the repo but Claude doesn't follow team coding standards. Why?"*
  → Standards are in `~/.claude/CLAUDE.md` (user-level), not project-level

- *"You want test conventions applied to all test files regardless of directory. Best approach?"*
  → `.claude/rules/` with `paths: ["**/*.test.*"]` glob pattern

- *"Your CI job hangs when running Claude Code. What's the fix?"*
  → Add the `-p` flag for non-interactive mode

- *"When should you use plan mode vs. direct execution?"*
  → Plan mode: architectural decisions, multi-file changes, multiple valid approaches
  → Direct: clear scope, single file, obvious fix

- *"A skill produces verbose output that fills the context window. How do you fix it?"*
  → Set `context: fork` in the skill's YAML frontmatter
