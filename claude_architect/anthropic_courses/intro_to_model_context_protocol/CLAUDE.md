# Introduction to Model Context Protocol

Hands-on labs for the Anthropic "Introduction to Model Context Protocol" course.

## Purpose

Understanding and implementing MCP servers and clients. Covers the MCP transport layer, tool/resource/prompt primitives, and connecting MCP servers to Claude.

## Stack

- Python or Node.js depending on lab (check individual lab READMEs)
- `anthropic` SDK, `mcp` SDK
- API key loaded from `.env` as `ANTHROPIC_API_KEY`
- IDE: Visual Studio or Jupyter Notebooks (Python labs)

## Conventions

- Python labs are either `.py` scripts (Visual Studio) or `.ipynb` notebooks (Jupyter)
- MCP servers expose tools, resources, and prompts — keep each primitive focused on one responsibility
- Test MCP servers standalone before wiring to Claude
- Each lab is self-contained; check for its own `requirements.txt` or `package.json`
