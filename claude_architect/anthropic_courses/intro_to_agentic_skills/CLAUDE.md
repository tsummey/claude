# Introduction to Agent Skills

Hands-on labs for the Anthropic "Introduction to Agent Skills" course.

## Purpose

Building and understanding agent skills: how Claude uses tools, manages agentic loops, and delegates to subagents. Focus on correct loop termination, tool design, and structured error handling.

## Stack

- Python (venv at repo root: `../../../venv/Scripts/python.exe`)
- `anthropic` SDK, `python-dotenv`
- API key loaded from `.env` as `ANTHROPIC_API_KEY`
- IDE: Visual Studio or Jupyter Notebooks

## Conventions

- Labs are either `.py` scripts (Visual Studio) or `.ipynb` notebooks (Jupyter)
- `stop_reason` is the only correct agentic-loop termination signal — never use text parsing or iteration caps as the primary exit condition
- Subagents have isolated context — pass everything they need explicitly
- Structured tool errors should include `errorCategory`, `isRetryable`, `attemptedAction`
