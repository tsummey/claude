# Claude Code in Action

Hands-on labs for the Anthropic "Claude Code in Action" course.

## Purpose

Learning to build and extend applications using Claude Code as an AI-powered development tool. Covers agentic coding workflows, Claude Code SDK usage, and real project delivery.

## Stack

- Next.js / React / TypeScript (UIGen app lives in `uigen/uigen/`)
- Node.js, npm
- Python (venv at repo root: `../../../venv/Scripts/python.exe`), `anthropic` SDK, `python-dotenv`
- API key loaded from `.env` as `ANTHROPIC_API_KEY`
- IDE: Visual Studio or Jupyter Notebooks (Python labs)

## Commands (UIGen)

Run from `uigen/uigen/`:

```bash
npm run setup    # first-time: install deps, Prisma client, migrations
npm run dev      # dev server at http://localhost:3000
npm run build    # production build
npm run lint     # next lint
npm test         # vitest unit tests
npm run db:reset # reset SQLite database
```

## Conventions

- Without `ANTHROPIC_API_KEY`, UIGen falls back to a mock provider
- Do not run `npm audit fix` — dependency versions are pinned deliberately
