---
name: backlog-management
description: "Backlog creation and voting workflows for Hermes issue management."
category: hve
version: 1.0
date: 2026-05-30
---

# backlog-management — Backlog Filing, Review & Voting

## When to Invoke
- New backlog idea, repo issue, or implementation proposal
- Reading or reviewing an existing GitHub issue or RFC
- Posting follow-up feedback on an existing issue thread
- Voting on a backlog issue
- Requests to post an idea to the Mercury or Hermes backlog

## Required Calls

| Need | Must use | Output rule |
|---|---|---|
| File a backlog issue | `suggest_backlog_issue` | One idea = one tool call |
| Vote on backlog issue | `vote_backlog_issue` | Use the actual vote result |
| Read an existing issue | `read_github_issue` | Quote the returned thread, not memory |
| Comment on an existing issue | `comment_github_issue` | Use the returned comment URL |
| Scan matching issues | `list_github_issues` | Report the actual list returned |

## Non-Negotiables
- Do not say you will post or delegate a backlog idea without calling the tool immediately.
- Multiple ideas require multiple `suggest_backlog_issue` calls.
- Echo the tool confirmation verbatim before moving on.
- Do not claim you reviewed an issue thread without `read_github_issue`.
- Do not claim you posted a review comment without `comment_github_issue`.
