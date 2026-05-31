---
name: knowledge-management
description: "Knowledge, task, client-context, and capability workflows for Hermes."
category: hve
version: 1.0
date: 2026-05-30
---

# knowledge-management — Vault, Tasks & Context

## When to Invoke
- Searching HVE knowledge or prior decisions
- Creating a tracked task
- Looking up client-specific context
- Capability or tool-surface assessment requests

## Required Calls

| Need | Must use | Output rule |
|---|---|---|
| Knowledge lookup | `search_knowledge_vault` | Use tool result, not memory |
| Create tracked task | `create_task` | File the task instead of describing it |
| Client context | `get_client_context` | Use live client context from the tool |
| Capability check | `get_capability_assessment` | Report tool output, not self-description |

## Non-Negotiables
- **Never narrate a call. Make the call.** If you find yourself writing "I will search the knowledge vault" — stop and call the tool.
- Do not claim knowledge-vault content without a tool result.
- Do not promise a task was created unless `create_task` actually succeeded.
- If client context is unavailable, say it is unavailable rather than guessing.
- Echo `create_task` and `search_knowledge_vault` output verbatim before adding commentary.

## Fallbacks
- `search_knowledge_vault` unavailable → say: `Knowledge vault unavailable — MCP tool failed. Cannot retrieve stored context.`
- `create_task` unavailable → say: `Task creation unavailable — MCP tool failed. Task was NOT filed.`
- `get_client_context` unavailable → say: `Client context unavailable — MCP tool failed.`
- `get_capability_assessment` unavailable → say: `Capability assessment unavailable — MCP tool failed.`
