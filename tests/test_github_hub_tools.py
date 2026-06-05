"""Tests for tools/github_hub.py — GitHub Universal Hub Tools.

Follows the same mock.patch pattern as test_github_issue_tools.py.
All HTTP calls are mocked — no real network requests.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import github_hub


class SearchGithubCodeTests(unittest.TestCase):
    def test_returns_formatted_results(self) -> None:
        payload = {
            "total_count": 42,
            "items": [
                {
                    "repository": {"full_name": "humanvalueexchange/hermes-cfo"},
                    "path": "mcp/server.py",
                    "html_url": "https://github.com/humanvalueexchange/hermes-cfo/blob/main/mcp/server.py",
                },
                {
                    "repository": {"full_name": "humanvalueexchange/mercury"},
                    "path": "src/main.py",
                    "html_url": "https://github.com/humanvalueexchange/mercury/blob/main/src/main.py",
                },
            ],
        }
        with mock.patch("tools.github_hub._load_github_token", return_value="token"), \
             mock.patch("tools.github_hub._request_github_json", return_value=payload):
            result = github_hub.search_github_code("OLLAMA_HOST")

        self.assertIn("## Code Search: 'OLLAMA_HOST'", result)
        self.assertIn("42 total, 2 shown", result)
        self.assertIn("hermes-cfo/mcp/server.py", result)
        self.assertIn("mercury/src/main.py", result)

    def test_scoped_to_repo_builds_correct_query(self) -> None:
        payload = {"total_count": 1, "items": [{
            "repository": {"full_name": "humanvalueexchange/hermes-cfo"},
            "path": "tools/github_hub.py",
            "html_url": "https://github.com/humanvalueexchange/hermes-cfo/blob/main/tools/github_hub.py",
        }]}
        with mock.patch("tools.github_hub._load_github_token", return_value="token"), \
             mock.patch("tools.github_hub._request_github_json", return_value=payload) as req:
            github_hub.search_github_code("def search", repo="hermes-cfo")

        called_path = req.call_args[0][0]
        self.assertIn("repo:humanvalueexchange/hermes-cfo", called_path)

    def test_org_scope_when_no_repo(self) -> None:
        payload = {"total_count": 0, "items": []}
        with mock.patch("tools.github_hub._load_github_token", return_value="token"), \
             mock.patch("tools.github_hub._request_github_json", return_value=payload) as req:
            github_hub.search_github_code("anything")

        called_path = req.call_args[0][0]
        self.assertIn("org:humanvalueexchange", called_path)

    def test_empty_results(self) -> None:
        payload = {"total_count": 0, "items": []}
        with mock.patch("tools.github_hub._load_github_token", return_value="token"), \
             mock.patch("tools.github_hub._request_github_json", return_value=payload):
            result = github_hub.search_github_code("nonexistent_xyzzy")

        self.assertIn("No code results", result)

    def test_empty_query_returns_error(self) -> None:
        result = github_hub.search_github_code("  ")
        self.assertEqual(result, "ERROR: query cannot be empty")

    def test_invalid_repo_returns_error(self) -> None:
        result = github_hub.search_github_code("hello", repo="bad-repo")
        self.assertIn("ERROR: repo must be one of", result)

    def test_missing_token_returns_error(self) -> None:
        with mock.patch("tools.github_hub._load_github_token", return_value=None):
            result = github_hub.search_github_code("anything")
        self.assertIn("ERROR: HVE_GITHUB_TOKEN", result)

    def test_limit_capped_at_30(self) -> None:
        payload = {"total_count": 0, "items": []}
        with mock.patch("tools.github_hub._load_github_token", return_value="token"), \
             mock.patch("tools.github_hub._request_github_json", return_value=payload) as req:
            github_hub.search_github_code("query", limit=999)

        called_path = req.call_args[0][0]
        self.assertIn("per_page=30", called_path)


class GetGithubFileTests(unittest.TestCase):
    def test_reads_file_and_returns_content(self) -> None:
        payload = {
            "content": "aGVsbG8gd29ybGQ=",  # base64("hello world")
            "size": 11,
            "sha": "abc1234567890",
        }
        with mock.patch("tools.github_hub._load_github_token", return_value="token"), \
             mock.patch("tools.github_hub._request_github_json", return_value=payload):
            result = github_hub.get_github_file("hermes-cfo", "README.md")

        self.assertIn("## hermes-cfo/README.md", result)
        self.assertIn("hello world", result)
        self.assertIn("11 bytes", result)
        self.assertIn("sha:abc1234", result)

    def test_directory_listing(self) -> None:
        payload = [
            {"name": "server.py"},
            {"name": "market_intelligence.py"},
        ]
        with mock.patch("tools.github_hub._load_github_token", return_value="token"), \
             mock.patch("tools.github_hub._request_github_json", return_value=payload):
            result = github_hub.get_github_file("hermes-cfo", "mcp")

        self.assertIn("(directory)", result)
        self.assertIn("server.py", result)
        self.assertIn("market_intelligence.py", result)

    def test_large_file_truncated(self) -> None:
        import base64 as b64
        long_content = "x" * 9000
        payload = {
            "content": b64.b64encode(long_content.encode()).decode(),
            "size": 9000,
            "sha": "abc1234567890",
        }
        with mock.patch("tools.github_hub._load_github_token", return_value="token"), \
             mock.patch("tools.github_hub._request_github_json", return_value=payload):
            result = github_hub.get_github_file("hermes-cfo", "large.py")

        self.assertIn("truncated at 8000 chars", result)
        self.assertEqual(result.count("x"), 8000)

    def test_file_within_limit_not_truncated(self) -> None:
        import base64 as b64
        content = "y" * 100
        payload = {
            "content": b64.b64encode(content.encode()).decode(),
            "size": 100,
            "sha": "abc1234567890",
        }
        with mock.patch("tools.github_hub._load_github_token", return_value="token"), \
             mock.patch("tools.github_hub._request_github_json", return_value=payload):
            result = github_hub.get_github_file("hermes-cfo", "small.py")

        self.assertNotIn("truncated", result)

    def test_invalid_repo_returns_error(self) -> None:
        result = github_hub.get_github_file("bad-repo", "README.md")
        self.assertIn("ERROR: repo must be one of", result)

    def test_empty_path_returns_error(self) -> None:
        result = github_hub.get_github_file("hermes-cfo", "  ")
        self.assertEqual(result, "ERROR: path cannot be empty")

    def test_missing_token_returns_error(self) -> None:
        with mock.patch("tools.github_hub._load_github_token", return_value=None):
            result = github_hub.get_github_file("hermes-cfo", "README.md")
        self.assertIn("ERROR: HVE_GITHUB_TOKEN", result)


class CreateGithubIssueTests(unittest.TestCase):
    def test_creates_issue_and_returns_url(self) -> None:
        payload = {
            "number": 99,
            "title": "Test Issue",
            "html_url": "https://github.com/humanvalueexchange/hermes-cfo/issues/99",
        }
        with mock.patch("tools.github_hub._load_github_token", return_value="token"), \
             mock.patch("tools.github_hub._request_github_json", return_value=payload) as req:
            result = github_hub.create_github_issue("hermes-cfo", "Test Issue", "body text")

        self.assertIn("\u2705 Issue created: hermes-cfo#99", result)
        self.assertIn("https://github.com", result)
        self.assertEqual(req.call_args.kwargs["method"], "POST")

    def test_hermes_signature_appended_when_missing(self) -> None:
        payload = {"number": 100, "title": "T", "html_url": "http://x"}
        with mock.patch("tools.github_hub._load_github_token", return_value="token"), \
             mock.patch("tools.github_hub._request_github_json", return_value=payload) as req:
            github_hub.create_github_issue("hermes-cfo", "T", "plain body without agent mention")

        body_sent = req.call_args.kwargs["payload"]["body"]
        self.assertIn("Hermes", body_sent)

    def test_hermes_signature_not_duplicated(self) -> None:
        payload = {"number": 101, "title": "T", "html_url": "http://x"}
        with mock.patch("tools.github_hub._load_github_token", return_value="token"), \
             mock.patch("tools.github_hub._request_github_json", return_value=payload) as req:
            github_hub.create_github_issue("hermes-cfo", "T", "Body mentioning Hermes directly")

        body_sent = req.call_args.kwargs["payload"]["body"]
        self.assertEqual(body_sent.count("Created by Hermes"), 0)  # not auto-appended

    def test_labels_are_parsed_and_sent(self) -> None:
        payload = {"number": 102, "title": "T", "html_url": "http://x"}
        with mock.patch("tools.github_hub._load_github_token", return_value="token"), \
             mock.patch("tools.github_hub._request_github_json", return_value=payload) as req:
            github_hub.create_github_issue("hermes-cfo", "T", labels="bug,priority-high")

        labels_sent = req.call_args.kwargs["payload"]["labels"]
        self.assertIn("bug", labels_sent)
        self.assertIn("priority-high", labels_sent)

    def test_empty_title_returns_error(self) -> None:
        result = github_hub.create_github_issue("hermes-cfo", "  ")
        self.assertEqual(result, "ERROR: title cannot be empty")

    def test_invalid_repo_returns_error(self) -> None:
        result = github_hub.create_github_issue("bad-repo", "Title")
        self.assertIn("ERROR: repo must be one of", result)

    def test_missing_token_returns_error(self) -> None:
        with mock.patch("tools.github_hub._load_github_token", return_value=None):
            result = github_hub.create_github_issue("hermes-cfo", "Title")
        self.assertIn("ERROR: HVE_GITHUB_TOKEN", result)


class ListGithubCommitsTests(unittest.TestCase):
    def test_formats_commit_list(self) -> None:
        payload = [
            {
                "sha": "abc1234567890",
                "commit": {
                    "message": "feat: add github hub tools\n\nExtended details.",
                    "author": {"name": "Claude", "date": "2026-06-04T22:00:00Z"},
                },
            },
            {
                "sha": "def5678901234",
                "commit": {
                    "message": "fix: expand VALID_REPOS",
                    "author": {"name": "HansHWestphal", "date": "2026-06-04T21:00:00Z"},
                },
            },
        ]
        with mock.patch("tools.github_hub._load_github_token", return_value="token"), \
             mock.patch("tools.github_hub._request_github_json", return_value=payload):
            result = github_hub.list_github_commits("hermes-cfo")

        self.assertIn("## hermes-cfo/main", result)
        self.assertIn("`abc1234`", result)
        self.assertIn("feat: add github hub tools", result)
        self.assertNotIn("Extended details", result)  # only first line of commit message
        self.assertIn("**Claude**", result)
        self.assertIn("2026-06-04", result)

    def test_empty_commits(self) -> None:
        with mock.patch("tools.github_hub._load_github_token", return_value="token"), \
             mock.patch("tools.github_hub._request_github_json", return_value=[]):
            result = github_hub.list_github_commits()

        self.assertIn("No commits found", result)

    def test_invalid_repo_returns_error(self) -> None:
        result = github_hub.list_github_commits(repo="bad-repo")
        self.assertIn("ERROR: repo must be one of", result)

    def test_missing_token_returns_error(self) -> None:
        with mock.patch("tools.github_hub._load_github_token", return_value=None):
            result = github_hub.list_github_commits()
        self.assertIn("ERROR: HVE_GITHUB_TOKEN", result)

    def test_limit_capped_at_30(self) -> None:
        with mock.patch("tools.github_hub._load_github_token", return_value="token"), \
             mock.patch("tools.github_hub._request_github_json", return_value=[]) as req:
            github_hub.list_github_commits(limit=999)

        called_path = req.call_args[0][0]
        self.assertIn("per_page=30", called_path)


if __name__ == "__main__":
    unittest.main()
