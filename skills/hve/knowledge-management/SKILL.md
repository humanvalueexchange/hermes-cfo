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
- Do not claim knowledge-vault content without a tool result.
- Do not promise a task was created unless `create_task` actually succeeded.
- If client context is unavailable, say it is unavailable rather than guessing.
