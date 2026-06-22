# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This is a personal learning/study workspace for Anthropic's Claude curriculum and the **Claude Certified Architect – Foundations (CCAF)** exam. It is not a single application — it's a collection of independent sub-projects. Scope your work to whichever sub-project the user is asking about; conventions and commands do not carry over between them.

## Layout

- **`claude_architect/`** — CCAF exam prep materials: domain training docs (`domain_training/*.html`), hands-on labs and solutions (`domain_training/labs/`), scenario simulations (`scenario_training/`), and practice questions (`practice_questions/`). `claude_architect/README.md` documents the recommended study order, domain weights, and scoring. Practice-question files (`combined_sample_questions.txt`, `more_questions.txt`, `*.flashcards`, `ccaf_test.html`) are study content — edit them as content, not code.
- **`anthropic_courses/`** — Jupyter notebooks (`*.ipynb`) from Anthropic's training curriculum. **This directory is its own nested git repository** (separate `.git`, ignored by the parent repo's `.gitignore`) — commit changes here separately from the outer repo.
  - **`anthropic_courses/Claude Code In Action/uigen/uigen/`** — the one real software project in this repo: a Next.js/React/TypeScript app ("UIGen") that generates React components via Claude with a live preview. Has its own README, build, lint, and test commands (see below).
- **`code_snippets/`** — standalone Python scripts (`task_1_*.py`) demonstrating agentic-loop and multi-agent orchestration patterns with the `anthropic` SDK. Each script is self-contained and runnable on its own.

## Commands

### UIGen (`anthropic_courses/Claude Code In Action/uigen/uigen/`)

Run all commands from inside that directory.

```bash
npm run setup       # install deps, generate Prisma client, run migrations (first-time setup)
npm run dev          # start dev server (Turbopack) at http://localhost:3000
npm run build        # production build
npm run lint         # next lint
npm test             # vitest (unit tests, e.g. src/lib/__tests__, src/lib/transform/__tests__)
npm run db:reset      # reset the Prisma/SQLite database
```

Run a single test file with `npx vitest run path/to/file.test.ts`.

Without an `ANTHROPIC_API_KEY` in `.env`, the app falls back to a mock provider returning canned components — useful for UI work that doesn't need real generations.

**Do not run `npm audit fix`** — dependency versions are pinned deliberately; `audit fix` can bump past compatible versions and break the app. Security fixes are applied by bumping the specific pinned package instead.

### Python snippets / scenario simulations

These use the `anthropic` SDK and `python-dotenv`, reading `ANTHROPIC_API_KEY` from a local `.env`. A `venv/` exists at the repo root with `anthropic`, `python-dotenv`, and `pydantic` installed.

```bash
./venv/Scripts/python.exe code_snippets/task_1_1_agentic_loop.py
./venv/Scripts/python.exe "claude_architect/scenario_training/scenario 1 - customer support resolution agent/simulation/agent.py"
```

### Notebooks (`anthropic_courses/`)

Open and run with Jupyter; no separate build step.

## Conventions and recurring concepts

The CCAF study materials repeatedly emphasize a set of architectural principles that should inform any agent/tool-design work done in this repo (see `claude_architect/README.md` for the full list):

- **`stop_reason` is the only correct agentic-loop termination signal** — never use text parsing, content-type checks, or iteration caps as the primary exit condition.
- **Subagents have isolated context** — they do not inherit the coordinator's conversation history; pass everything they need explicitly.
- **Programmatic enforcement beats prompt-based enforcement** for anything requiring 100% compliance (e.g. refund thresholds, identity verification) — use hooks/gates, not instructions.
- **Structured tool errors enable recovery** — include `errorCategory`, `isRetryable`, `attemptedAction`, and alternatives rather than generic failure messages; distinguish "empty result" from "access failure".
- **CLAUDE.md hierarchy is user → project → directory** — team-shared standards belong in version-controlled project/directory config, not user-level config.
