# Test Plan: GitHub Hub Tools Phase 1

**Status:** Awaiting Grok Review  
**Assigned To:** Grok (Lead Test Engineer)  
**Author:** Claude (CTO / Chief Architect)  
**Date:** June 4, 2026  
**ADR:** [ADR-006 — Hermes Universal MCP Hub](https://github.com/humanvalueexchange/humanvalueexchange/blob/main/docs/adr/ADR-006-hermes-universal-mcp-hub.md)

---

## Summary

Phase 1 of ADR-006 adds 4 new GitHub tools to the Hermes MCP server, giving Hermes
(and all future agents like jr) sovereign access to the full `humanvalueexchange` org.

**Tools under test:**

| Tool | File | Purpose |
|---|---|---|
| `search_github_code` | `tools/github_hub.py` | Code search across HVE org |
| `get_github_file` | `tools/github_hub.py` | Read any file from any HVE repo |
| `create_github_issue` | `tools/github_hub.py` | Create issues in HVE repos |
| `list_github_commits` | `tools/github_hub.py` | List recent commits on any branch |

---

## Unit Test Suite

**File:** `tests/test_github_hub_tools.py`  
**Tests:** 22 unit tests across 4 test classes  
**Dependencies:** stdlib only — zero network calls, all HTTP mocked

### Run Command

```bash
cd ~/hermes-cfo
python -m pytest tests/test_github_hub_tools.py -v
```

### Pass Criteria

**All 22 tests must pass. Zero failures. Zero skips.**

---

## Adversarial Cases (Grok to Verify)

### 1. Repo Allowlist — Injection Resistance

Every tool must return `ERROR: repo must be one of` for any invalid repo:

```python
# Test these inputs against all 4 tools
bad_repos = ["evil-repo", "../etc/passwd", "", "humanvalueexchange/hermes-cfo", " "]
```

Full org path `"humanvalueexchange/hermes-cfo"` must be rejected — slug only is allowed.

### 2. Token Never Leaked in Error Output

```python
# Simulate a network error that includes the token in the exception text
# Confirm the raw token string does NOT appear in the returned error message
with mock.patch("tools.github_hub._request_github_json",
               side_effect=Exception("Bearer sk-FAKE-TOKEN is invalid")):
    result = github_hub.search_github_code("query")
# The token loading happens before the request — this tests exception passthrough
```

### 3. `get_github_file` — Content Limit Boundary

```python
# At exactly 8000 chars: NOT truncated
content_8000 = "x" * 8000
assert "truncated" not in result

# At 8001 chars: MUST be truncated
content_8001 = "x" * 8001
assert "truncated at 8000 chars" in result
assert result.count("x") == 8000
```

### 4. `create_github_issue` — Hermes Signature Logic

```python
# Case A: body does NOT mention 'Hermes' → signature appended
body_without = "This is a plain issue body."
# assert 'Created by Hermes' in payload['body']

# Case B: body ALREADY contains 'Hermes' → NO duplicate signature
body_with = "Hermes detected an anomaly in the treasury."
# assert body.count('Created by Hermes') == 0  # not auto-appended
```

### 5. `search_github_code` — Query Scoping

```python
# With repo → query contains repo:humanvalueexchange/hermes-cfo
github_hub.search_github_code("query", repo="hermes-cfo")
# assert 'repo:humanvalueexchange/hermes-cfo' in called_path

# Without repo → query contains org:humanvalueexchange (never leaks outside org)
github_hub.search_github_code("query")
# assert 'org:humanvalueexchange' in called_path
# assert 'org:github' not in called_path  # sanity check — no external scope
```

### 6. `list_github_commits` — Multi-line Message Truncation

```python
payload = [{"sha": "abc123", "commit": {
    "message": "feat: title line\n\nLong body line 1\nLong body line 2\nLong body line 3",
    "author": {"name": "Test", "date": "2026-06-04T00:00:00Z"}
}}]
# Only 'feat: title line' should appear — body lines must NOT appear
```

---

## MCP Server Registration (Post-Deployment)

After Hans deploys (see Deployment Steps below), verify all 4 tools appear in the
MCP tool list. Hermes will expose them via the agent card at:

```
GET /.well-known/agent.json  (no auth required)
```

```bash
curl -s http://192.168.1.10:8765/.well-known/agent.json | python3 -m json.tool | grep -A 20 '"tools"'
```

Expected: `search_github_code`, `get_github_file`, `create_github_issue`, `list_github_commits` all present.

---

## Integration Smoke Tests (Requires Live Hermes)

```bash
export API_KEY=$(grep HVE_MCP_API_KEY ~/.hermes-mcp.env | cut -d= -f2)
BASE="http://192.168.1.10:8765"

# 1. Confirm server healthy
curl -s -H "X-HVE-API-Key: $API_KEY" $BASE/health

# 2. Tool registration check
curl -s $BASE/.well-known/agent.json | python3 -c "import json,sys; d=json.load(sys.stdin); print([t for t in d['capabilities']['tools'] if 'github' in t])"
```

Then via Hermes natural language (in Telegram or Open WebUI):

1. `"search github code for OLLAMA_HOST"` → should return file matches
2. `"get file README.md from hermes-cfo"` → should return README content
3. `"list last 5 commits on hermes-cfo main"` → should return commit list
4. `"create a test issue in hermes-cfo titled 'MCP Phase1 smoke test — delete me'"` → **Hans must approve before running**

---

## Deployment Steps (Hans to Execute After Merge)

```bash
cd ~/hermes-cfo
git pull origin main
sudo systemctl restart hermes-mcp  # or: systemctl --user restart hermes-mcp
```

**Verify:**
```bash
systemctl status hermes-mcp
journalctl -u hermes-mcp -n 30
```

> **Note:** No config.yaml changes required — `@mcp.tool()` registration is automatic.
> The MCP server auto-discovers all registered tools. The `TOOL_NAMES` list in
> `server.py` is only used for the A2A agent card, not for tool registration.

---

## Grok Sign-Off Template

When complete, Grok posts on the PR:

```
## Test Results — GitHub Hub Tools Phase 1

**Unit Tests:** XX/22 PASS
**Adversarial Cases:** [PASS/FAIL with notes]
**MCP Registration:** [CONFIRMED/PENDING]

**Recommendation:** MERGE / DO NOT MERGE

---
_Grok (Lead Test Engineer, HVE)_
```

---

*Authored by Claude (CTO / Chief Architect), Human Value Exchange*  
*June 4, 2026*
