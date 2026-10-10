# Onboarding SLA Dashboard Development Guide

## Scope

This is a local-first learning project. Do not add cloud deployment, CI/CD, or
change the Gemini model unless explicitly requested.

## Architecture

- `Agents/ExcelAnalyst/data_cleaner.py`: deterministic cleaning only.
- `Agents/ExcelAnalyst/tools.py`: spreadsheet inspection and metadata extraction.
- `Agents/ExcelAnalyst/schemas.py`: stable Pydantic output contract.
- `Agents/ExcelAnalyst/prompts.py`: LLM instructions only.
- `Agents/ExcelAnalyst/agent.py`: ADK construction and execution entrypoints.

## Rules

- The agent interprets spreadsheet structure; deterministic backend code owns calculations.
- Preserve exact cleaned source headers in all mappings.
- Never treat numeric SLA/duration values as dates based only on their header.
- Require human confirmation for uncertain mappings and ambiguous date formats.
- Partner edits are validated only in `Backend/records/`; the frontend never validates beyond required fields.

## Comprehensive Guide

For full system architecture, annotated file structure, API reference, and calculation rules, see [AI_CONTEXT.md](AI_CONTEXT.md).
