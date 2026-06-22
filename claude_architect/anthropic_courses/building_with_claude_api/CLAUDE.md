# Building with the Claude API

Hands-on labs for the Anthropic "Building with the Claude API" course.

## Purpose

Working directly with the Anthropic SDK to understand API fundamentals: messages, streaming, tool use, prompt caching, and token management.

## Stack

- Python (venv at repo root: `../../../venv/Scripts/python.exe`)
- `anthropic` SDK, `python-dotenv`
- API key loaded from `.env` as `ANTHROPIC_API_KEY`
- IDE: Visual Studio or Jupyter Notebooks

## Conventions

- Labs are either `.py` scripts (Visual Studio) or `.ipynb` notebooks (Jupyter)
- Never hardcode API keys — always load from `.env`
- Prefer real API calls over mocks unless explicitly testing error handling
