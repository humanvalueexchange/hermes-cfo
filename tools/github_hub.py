"""
HVE GitHub Hub Tools — Universal MCP Server Phase 1

Extends Hermes MCP tool coverage to the full humanvalueexchange org.
Provides code search, file reading, issue creation, and commit listing
across all HVE repos.

All tools follow the same stdlib-only, token-from-env pattern as
tools/github_issues.py. No additional dependencies required.

Token source: HVE_GITHUB_TOKEN in ~/.hermes/.env
"""
from __future__ import annotations

import base64
import json
import os
import urllib.parse
import urllib.request

HVE_ORG = "humanvalueexchange"
VALID_REPOS = ("hermes-cfo", "mercury", "humanvalueexchange")


def _load_github_token() -> str | None:
    env_file = os.path.expanduser("~/.hermes/.env")
    if not os.path.exists(env_file):
        return None
    for line in open(env_file).read().splitlines():
        if line.startswith("HVE_GITHUB_TOKEN="):
            return line.split("=", 1)[1].strip()
    return None


def _request_github_json(
    path: str,
    token: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
) -> dict | list:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method=method,
    )
    with urllib.request.urlopen(req, timeout=15) as response:  # noqa: S310
        return json.loads(response.read())


def search_github_code(query: str, repo: str = "", limit: int = 10) -> str:
    """Search code across HVE org repos. Optionally scope to a specific repo."""
    if not query.strip():
        return "ERROR: query cannot be empty"
    limit = max(1, min(int(limit), 30))
    token = _load_github_token()
    if not token:
        return "ERROR: HVE_GITHUB_TOKEN not found in ~/.hermes/.env"

    q = query.strip()
    if repo.strip():
        if repo.strip() not in VALID_REPOS:
            return f"ERROR: repo must be one of {VALID_REPOS}"
        q = f"{q} repo:{HVE_ORG}/{repo.strip()}"
    else:
        q = f"{q} org:{HVE_ORG}"

    params = urllib.parse.urlencode({"q": q, "per_page": str(limit)})
    try:
        data = _request_github_json(f"/search/code?{params}", token)
    except Exception as exc:
        return f"ERROR searching code: {exc}"

    items = data.get("items", [])
    total = data.get("total_count", 0)
    if not items:
        return f"No code results for '{query}' in HVE org."

    lines = [f"## Code Search: '{query}' — {total} total, {len(items)} shown\n"]
    for item in items:
        repo_full = item["repository"]["full_name"]
        file_path = item["path"]
        html_url = item["html_url"]
        lines.append(f"- [{repo_full}/{file_path}]({html_url})")

    return "\n".join(lines)


def get_github_file(repo: str, path: str, ref: str = "main") -> str:
    """Read the contents of any file from an HVE org repo."""
    if repo not in VALID_REPOS:
        return f"ERROR: repo must be one of {VALID_REPOS}"
    if not path.strip():
        return "ERROR: path cannot be empty"

    token = _load_github_token()
    if not token:
        return "ERROR: HVE_GITHUB_TOKEN not found in ~/.hermes/.env"

    encoded_path = urllib.parse.quote(path.strip(), safe="/")
    params = urllib.parse.urlencode({"ref": ref})

    try:
        data = _request_github_json(
            f"/repos/{HVE_ORG}/{repo}/contents/{encoded_path}?{params}",
            token,
        )
    except Exception as exc:
        return f"ERROR reading file: {exc}"

    if isinstance(data, list):
        names = [item["name"] for item in data]
        return f"## {repo}/{path}/ (directory)\n" + "\n".join(f"- {n}" for n in names)

    content_b64 = data.get("content", "")
    if not content_b64:
        return f"ERROR: no content returned for {repo}/{path}"

    try:
        content = base64.b64decode(content_b64).decode("utf-8", errors="replace")
    except Exception as exc:
        return f"ERROR decoding file content: {exc}"

    size = data.get("size", 0)
    sha = data.get("sha", "")[:7]

    truncated = ""
    if len(content) > 8000:
        content = content[:8000]
        truncated = "\n\n... [truncated at 8000 chars — use a narrower path or ref to read more]"

    return f"## {repo}/{path} (sha:{sha}, {size} bytes)\n\n```\n{content}\n```{truncated}"


def create_github_issue(repo: str, title: str, body: str = "", labels: str = "") -> str:
    """Create a new GitHub issue in an HVE org repo."""
    if repo not in VALID_REPOS:
        return f"ERROR: repo must be one of {VALID_REPOS}"
    if not title.strip():
        return "ERROR: title cannot be empty"

    token = _load_github_token()
    if not token:
        return "ERROR: HVE_GITHUB_TOKEN not found in ~/.hermes/.env"

    issue_body = body.strip()
    if issue_body and "Hermes" not in issue_body:
        issue_body += "\n\n---\n*Created by Hermes (CFO AI agent, Human Value Exchange)*"

    payload: dict = {"title": title.strip()}
    if issue_body:
        payload["body"] = issue_body
    if labels.strip():
        payload["labels"] = [label.strip() for label in labels.split(",") if label.strip()]

    try:
        data = _request_github_json(
            f"/repos/{HVE_ORG}/{repo}/issues",
            token,
            method="POST",
            payload=payload,
        )
        return f"✅ Issue created: {repo}#{data['number']} — {data['title']}\n{data['html_url']}"
    except Exception as exc:
        return f"ERROR creating issue: {exc}"


def list_github_commits(repo: str = "hermes-cfo", branch: str = "main", limit: int = 10) -> str:
    """List recent commits on a branch of an HVE org repo."""
    if repo not in VALID_REPOS:
        return f"ERROR: repo must be one of {VALID_REPOS}"
    limit = max(1, min(int(limit), 30))
    token = _load_github_token()
    if not token:
        return "ERROR: HVE_GITHUB_TOKEN not found in ~/.hermes/.env"

    params = urllib.parse.urlencode({"sha": branch, "per_page": str(limit)})

    try:
        commits = _request_github_json(
            f"/repos/{HVE_ORG}/{repo}/commits?{params}",
            token,
        )
    except Exception as exc:
        return f"ERROR listing commits: {exc}"

    if not commits:
        return f"No commits found on {repo}/{branch}."

    lines = [f"## {repo}/{branch} — Last {len(commits)} commits\n"]
    for commit in commits:
        sha = commit["sha"][:7]
        msg = commit["commit"]["message"].splitlines()[0]
        author = commit["commit"]["author"]["name"]
        date = commit["commit"]["author"]["date"][:10]
        lines.append(f"- `{sha}` {date} **{author}**: {msg}")

    return "\n".join(lines)
