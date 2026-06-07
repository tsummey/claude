# Lab D3-01: CLAUDE.md Hierarchy, Slash Commands & Path Rules
### Domain 3 | Task Statements 3.1, 3.2, 3.3 | Estimated Time: 50 minutes

---

## Objective

Build a complete Claude Code configuration for a realistic multi-package project.
You will create CLAUDE.md files at multiple hierarchy levels, implement custom
slash commands and skills, and configure path-specific rules. Then you will
diagnose common configuration failures.

This lab is done in Claude Code itself — not a Python script. You are configuring
the tool you're using.

---

## Prerequisites

- Claude Code installed and running
- A working project directory (we'll use `claude_architect/labs/sample_project/`)

---

## Setup: Create Sample Project Structure

In Claude Code terminal or VS Code terminal, run:

```bash
# Create the sample project
mkdir -p C:\Users\tsummey\projects\claude\claude_architect\labs\sample_project\src\api
mkdir -p C:\Users\tsummey\projects\claude\claude_architect\labs\sample_project\src\payments
mkdir -p C:\Users\tsummey\projects\claude\claude_architect\labs\sample_project\src\frontend
mkdir -p C:\Users\tsummey\projects\claude\claude_architect\labs\sample_project\.claude\commands
mkdir -p C:\Users\tsummey\projects\claude\claude_architect\labs\sample_project\.claude\skills
mkdir -p C:\Users\tsummey\projects\claude\claude_architect\labs\sample_project\.claude\rules
```

---

## Part 1: CLAUDE.md Hierarchy (15 minutes)

### Step 1: Create the project-level CLAUDE.md

Create: `sample_project/.claude/CLAUDE.md`

```markdown
# PaymentService Project

## Overview
REST API handling payment processing, customer management, and order fulfillment.
Built with FastAPI + PostgreSQL + Redis.

## Universal Standards (apply everywhere in this project)

### Code Quality
- Type hints required on all function signatures
- All functions must have docstrings
- Maximum function length: 50 lines (refactor if longer)
- No magic numbers — use named constants

### Security
- Never log PII: customer names, emails, payment details, SSNs
- Never commit secrets — use environment variables
- All user inputs must be validated before database queries
- Monetary values stored as integers (cents), never floats

### Testing
- New code requires tests before merging
- Test file naming: `{module_name}_test.py` adjacent to source
- Use pytest fixtures, not global variables

### Git
- Branch naming: feature/{ticket-id}-{brief-description}
- Commits must reference ticket number: "PROJ-123: Add refund validation"

## Project Commands
- Run tests: `pytest src/ -v --cov=src`
- Start dev server: `uvicorn app.main:app --reload --port 8000`
- Format: `black src/ && isort src/`
- Type check: `mypy src/`

@import ./docs/api-standards.md
```

### Step 2: Create directory-level CLAUDE.md for payments package

Create: `sample_project/src/payments/CLAUDE.md`

```markdown
# Payments Package — Additional Standards

## PCI Compliance (required for all payment code)
- Never store full card numbers — store only last 4 digits
- All payment operations must be idempotent (safe to retry)
- Every payment action must generate an audit log entry
- Refunds require approval_token from get_approval() before processing

## Error Handling
- All payment operations: wrap in try/except with specific exception types
- On failure: log error_code + correlation_id (never the full card details)
- Always rollback database transactions on payment failures

## Integration Notes
- Use Stripe client from `payments.stripe_client` — never import stripe directly
- Test payments: use test card 4242424242424242
- Webhook signatures must be verified before processing
```

### Step 3: Verify hierarchy behavior

Open Claude Code in the sample project directory and run:
```
/memory
```

**Observe:** Which CLAUDE.md files are loaded? Are both the project-level and
payments-level files shown?

Now open Claude Code from within `src/payments/` and run `/memory` again.
**Observe:** Do you see the payments-specific rules?

```python
"""
OBSERVATION:
When running from project root, loaded files: [list them]
When running from src/payments/, loaded files: [list them]
Key insight: [what did you learn about CLAUDE.md inheritance?]
"""
```

---

## Part 2: Custom Slash Commands (10 minutes)

### Create a team-wide /review command

Create: `sample_project/.claude/commands/review.md`

```markdown
Review the current changes against our team standards:

## Security Check
- [ ] No PII being logged anywhere in the diff
- [ ] No credentials or secrets in the code
- [ ] User inputs validated before database operations
- [ ] SQL queries use parameterized statements (not string concatenation)

## Code Quality Check  
- [ ] Type hints on all new function signatures
- [ ] Docstrings on all new functions
- [ ] No magic numbers — named constants used
- [ ] Functions under 50 lines

## Testing Check
- [ ] Tests exist for new code paths
- [ ] Test file adjacent to source file
- [ ] Edge cases covered (null values, empty lists, boundary conditions)

## Payments-Specific (if in payments package)
- [ ] Payment operations are idempotent
- [ ] No full card numbers stored or logged
- [ ] Audit log entries created for all payment actions

Format findings as: [PASS/FAIL/N-A] Category — specific observation
Report only FAIL items as actionable findings with file:line references.
```

### Create a /investigate skill

Create: `sample_project/.claude/skills/investigate.md`

```markdown
---
context: fork
allowed-tools: Read, Grep, Glob, Bash
argument-hint: "component name or file path to investigate"
---

# Investigate Component

Investigate the component or file: $ARGUMENTS

Perform a thorough investigation:

1. Use Glob to find all related files (source + tests + config)
2. Use Read to examine the main component file
3. Use Grep to find all callers, importers, and consumers of this component
4. Use Grep to find all tests that cover this component
5. Use Bash to check git log for recent changes: `git log --oneline -10 -- $ARGUMENTS`

Return a structured investigation report:
- **What it does**: Brief description
- **Dependencies**: What it imports/uses
- **Consumers**: What uses this component
- **Test coverage**: Which tests cover it
- **Recent changes**: Last 10 commits touching it
- **Concerns**: Anything that looks problematic

Keep the report concise — this is a summary for the main session, not raw output.
```

### Test your commands

In Claude Code (from the sample_project directory):
1. Type `/review` — does it run the review checklist?
2. Type `/investigate src/payments/refund.py` — does it run in isolation?

---

## Part 3: Path-Specific Rules (15 minutes)

### Create rules for test files

Create: `sample_project/.claude/rules/testing-conventions.md`

```markdown
---
paths:
  - "**/*_test.py"
  - "**/test_*.py"
  - "**/conftest.py"
---

# Test File Conventions

When working on test files:

## Test Structure
- One test class per module being tested
- Method naming: `test_{method_name}_{scenario}` (e.g., `test_process_refund_success`)
- Use Arrange-Act-Assert pattern with blank lines separating sections

## Fixtures
- Define fixtures in conftest.py, not in test files
- Always use the `db_session` fixture for database tests (handles cleanup)
- Mock external services: never make real HTTP calls in tests

## Assertions  
- Use specific assertions: `assert result == expected` not `assert result`
- For exceptions: `with pytest.raises(ValueError, match="specific message")`
- Test one behavior per test method — not multiple assertions on different behaviors

## What to Test
- Happy path: normal successful operation
- Error paths: every `except` clause should have a corresponding test
- Edge cases: None/null inputs, empty collections, boundary values
- Do NOT test: implementation details, private methods, third-party library behavior
```

### Create rules for API handler files

Create: `sample_project/.claude/rules/api-conventions.md`

```markdown
---
paths:
  - "src/api/**/*.py"
  - "src/*/routes.py"
  - "src/*/endpoints.py"
---

# API Handler Conventions

When working on API endpoint files:

## Request Handling
- All endpoints must have Pydantic request models — no raw dict parsing
- Use FastAPI dependency injection for auth: `current_user: User = Depends(get_current_user)`
- Validate content type for POST/PUT requests

## Response Format
All API responses must follow this structure:
```json
{
  "success": true|false,
  "data": {...} | null,
  "error": null | {"code": "ERROR_CODE", "message": "human readable"}
}
```

## Status Codes
- 200: Success with data
- 201: Created (POST that creates a resource)
- 400: Bad request (validation error)
- 401: Unauthorized (not authenticated)
- 403: Forbidden (authenticated but not authorized)
- 404: Not found
- 422: Unprocessable entity (business logic error)
- 500: Unexpected server error (log these)

## Error Handling
- Catch specific exceptions, not broad `except Exception`
- Always include correlation_id in error responses
- Never expose stack traces in API responses
```

### Verify path-scoped loading

Open Claude Code and try editing a test file vs. an API file:
```
# Edit a test file and run /memory
# Edit an API file and run /memory
# Observe: which rules load in each case?
```

```python
"""
OBSERVATION:
When editing a test file, additional rules loaded: [list them]
When editing an API file, additional rules loaded: [list them]
Key insight: Path-specific rules vs CLAUDE.md — difference: [your answer]
"""
```

---

## Part 4: Diagnose Configuration Failures (10 minutes)

For each scenario, identify the root cause and the fix:

```python
"""
SCENARIO DIAGNOSIS:

Scenario A:
New developer Sarah joined the team and cloned the repo.
Claude Code doesn't enforce the "no PII in logs" rule for her,
even though it works for everyone else on the team.
Root cause:
Fix:

Scenario B:
The /review command works for you but your teammate says they don't see it
when they type /review.
Root cause:
Fix:

Scenario C:
You have test conventions in src/auth/CLAUDE.md but they don't apply to
test files in src/payments/ even though the conventions should be universal.
Root cause (why directory CLAUDE.md isn't working here):
Better approach:

Scenario D:
Your /investigate skill produces 3000 tokens of output that fills up your
main conversation context, making subsequent questions slow and expensive.
Root cause:
Fix (which frontmatter setting?):

Scenario E:
A teammate creates a personal variant of the /review skill that's much stricter.
They want it to apply only to their sessions, not to push it to the team.
Where should they create this file?
Answer:
"""
```

---

## Completion Criteria

✅ Project-level and directory-level CLAUDE.md files created with appropriate content
✅ /review command created and tested in Claude Code
✅ /investigate skill created with `context: fork` and `allowed-tools` restriction
✅ Path-specific rules created for test files and API files
✅ All 5 scenario diagnoses completed correctly

---

*Next Lab: D3-02 — CI/CD Integration with Claude Code*
