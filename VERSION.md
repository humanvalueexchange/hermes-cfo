# Hermes CFO — Version Manifest
# Single source of truth for all component versions.
# Updated by Claude (CTO) on each component change.
# Grok Build and Vulcan: always test against the versions listed here.

## Live Stack (DGX Spark — 192.168.1.10)

| Component | Version | Updated | Notes |
|---|---|---|---|
| **hermes-agent** | `0.15.2` | 2026-05-30 | v2026.5.29.2 tag — confirmed on 0.15.2 |
| **qwen3.5:27b** | Ollama latest | 2026-05-30 | Conductor / CFO Brain — 262K context |
| **mistral-small:24b** | Ollama latest | 2026-05-29 | Clarifier / Research — 131K context |
| **nemotron-3-nano:30b** | Ollama latest | 2026-05-29 | Executor — 131K context |
| **gemma2:27b** | Ollama latest | — | Open WebUI debug only — 8K context, NOT for Telegram |
| **Open WebUI** | running | 2026-05-29 | Debug console only |
| **HVE MCP Server** | `1.27.1` | — | hve-node at :8765 |

## Update Ownership

| Who | Responsibility |
|---|---|
| **Hermes (CFO AI)** | Daily version check via `scripts/hermes-update.sh` (cron 03:00) |
| **Hermes** | Telegram alert to Hans when update available (< 3 days old = notify, > 7 days = auto-upgrade) |
| **Claude (CTO)** | Approves major version upgrades, reviews security-tagged releases |
| **Grok Build** | Runs `test-tool-enforcement.sh` after every upgrade to confirm no regression |
| **Vulcan** | Builds against version in this file — always check VERSION.md before opening a PR |

## Update Policy

- **Daily**: Hermes checks PyPI at 03:00 UTC, notifies Hans via Telegram if behind
- **< 3 days old**: Notify only — allow team review of release notes
- **3–7 days old**: Notify with auto-upgrade countdown
- **> 7 days old**: Auto-upgrade, restart gateway, notify Hans, Grok Build runs tests
- **Security P0 releases**: CTO fast-tracks — upgrade same day

## Upgrade Log

| Date | From | To | Upgraded By | Notes |
|---|---|---|---|---|
| 2026-05-30 | gemma2:27b → qwen3.5:27b | Conductor swap | Claude (CTO) | gemma2 8K ctx too small; qwen3.5:27b 262K ctx ✅ |
| 2026-05-29 | 0.13.0 | 0.15.2 | Claude (CTO) | Manual — discovered 22-day gap, daily cron now in place |
