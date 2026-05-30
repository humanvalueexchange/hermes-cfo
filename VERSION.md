# Hermes CFO — Version Manifest
# Single source of truth for all component versions.
# Updated by Claude (CTO) on each component change.
# Grok Build and Vulcan: always test against the versions listed here.

## Live Stack (DGX Spark — 192.168.1.10)

| Component | Version | Updated | Notes |
|---|---|---|---|
| **hermes-agent** | `0.15.2` | 2026-05-29 | v2026.5.29.2 tag |
| **gemma2:27b** | Ollama latest | 2026-05-29 | Conductor / CFO Brain |
| **mistral-small:24b** | Ollama latest | 2026-05-29 | Clarifier / Research |
| **nemotron-3-nano:30b** | Ollama latest | 2026-05-29 | Executor |
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
| 2026-05-29 | 0.13.0 | 0.15.2 | Claude (CTO) | Manual — discovered 22-day gap, daily cron now in place |
