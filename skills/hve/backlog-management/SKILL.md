---
name: backlog-management
description: "Backlog creation and voting workflows for Hermes issue management."
category: hve
version: 1.0
date: 2026-05-30
---

# backlog-management — Backlog Filing & Voting

## When to Invoke
- New backlog idea, repo issue, or implementation proposal
- Voting on a backlog issue
- Requests to post an idea to the Mercury or Hermes backlog

## Required Calls

| Need | Must use | Output rule |
|---|---|---|
| File a backlog issue | `suggest_backlog_issue` | One idea = one tool call |
| Vote on backlog issue | `vote_backlog_issue` | Use the actual vote result |

## Non-Negotiables
- Do not say you will post or delegate a backlog idea without calling the tool immediately.
- Multiple ideas require multiple `suggest_backlog_issue` calls.
- Echo the tool confirmation verbatim before moving on.
