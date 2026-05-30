# Hermes — Sovereign AI CFO & Treasury Agent

**Status:** Active — running 24/7 on NVIDIA DGX Spark  
**Version:** 0.15.2 (hermes-agent v2026.5.29.2)  
**Architecture:** Platonic 3-model stack — all models ≥131K context  
**Hardware:** NVIDIA DGX Spark · 128 GB unified memory · ARM64 / aarch64  

---

## What Hermes Is

Hermes is the Chief Financial Officer of Human Value Exchange — a sovereign AI treasury agent running locally on the DGX Spark. No cloud. No subscriptions. Sovereign treasury intelligence, running 24/7.

Hermes monitors balances, enforces treasury policy, reports to the CEO via Telegram, and coordinates with Mercury (Bitcoin Lightning node) for real-time payment intelligence.

---

## Model Stack — Platonic 3-Model Architecture

| Role | Model | Context | RAM | Purpose |
|---|---|---|---|---|
| **Conductor / CFO Brain** | `qwen3.5:9b` | 128K | 6.6 GB | Orchestrates decisions, synthesizes all outputs |
| **Clarifier / Research** | `mistral-small:24b` | 131K | 14 GB | Market analysis, strategy research, synthesis |
| **Executor** | `nemotron-3-nano:30b` | 131K | 24 GB | Position sizing, fee calculations, tool calls |

**Total GPU load: ~45 GB of 128 GB unified memory (~83 GB headroom)**

All models run via **Ollama** (native binary, systemd-managed). All pinned with `OLLAMA_KEEP_ALIVE=-1` — never unloaded.

> **Architecture decision (2026-05-30, swap 1):** `gemma2:27b` deprecated as Conductor. Its 8K context window caused session crashes under real-world load (SOUL.md + MCP tool defs alone consume ~4,000 tokens). Replaced with `qwen3.5:27b` (262K context).
>
> **Architecture decision (2026-05-30, swap 2):** `qwen3.5:27b` swapped to `qwen3.5:9b` as Conductor. 27b was over-provisioned — 9b delivers identical quality at 6.6 GB vs 17 GB loaded, freeing ~10 GB headroom and improving first-token latency (Issue #26).

---

## Architecture

```
CEO (Hans) ──Telegram──▶ Hermes Gateway
                              │
                    ┌─────────┴──────────┐
                    │   Conductor        │  qwen3.5:9b (128K ctx)
                    │   (CFO Brain)      │
                    └─────────┬──────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
            Research                   Executor
       mistral-small:24b         nemotron-3-nano:30b
       (Analysis/Strategy)       (Math/Code/Tool Calls)
                 │
                 ▼
            MCP Tools
    ┌──────────────────────┐
    │ get_node_diagnostic  │
    │ get_btc_forecast     │
    │ get_morning_briefing │
    │ suggest_backlog_issue│
    │ vote_backlog_issue   │
    └──────────────────────┘
```

---

## Infrastructure

| Component | Detail |
|---|---|
| **Hardware** | NVIDIA DGX Spark, 128 GB unified LPDDR5x |
| **OS** | DGX OS (Ubuntu 24.04-based), aarch64 |
| **Ollama** | Native binary, `/usr/local/bin/ollama`, systemd |
| **hermes-agent** | `0.15.2` (v2026.5.29.2) — pip install in venv |
| **Gateway** | `~/.hermes/` — systemd user service |
| **Config** | `~/.hermes/profiles/main/config.yaml` (never committed — contains secrets) |
| **MCP** | `~/.hermes-mcp.env` (API keys, never committed) |
| **Open WebUI** | `0.9.5` — debug console at `[DGX_LAN_IP]:8080` |
| **Comms** | Telegram (inbound/outbound), Mattermost (reports) |
| **LAN IP** | `[DGX_LAN_IP]` (static Ethernet, permanent) |

---

## Repository Structure

```
hermes-cfo/
├── README.md                         ← you are here
├── VERSION.md                        ← single source of truth for all component versions
├── docs/
│   └── SOUL.md                       ← REMOVED — see dotfiles/SOUL.md
├── dotfiles/
│   ├── SOUL.md                       ← Hermes identity, rules, HVE vision, model roles (deploy → ~/.hermes/profiles/main/)
│   ├── hermes-*.service              ← systemd unit files
│   └── inject-market-data.sh        ← pre-LLM hook: live BTC price injection
├── config/
│   ├── hermes-config.template.yaml   ← config template (secrets as ${PLACEHOLDERS})
│   └── hermes-env.template           ← .env template — what secrets are needed
└── scripts/
    ├── hermes-install.sh             ← bootstrap on fresh DGX Spark
    ├── hermes-deploy.sh              ← deploy config changes to live runtime
    ├── hermes-update.sh              ← daily self-update cron (03:00 UTC, Telegram notify)
    └── test-tool-enforcement.sh      ← MCP tool call regression tests (Issue #2)
```

---

## Engineering Team (v3.0)

| Role | Agent | Model |
|---|---|---|
| Chief Architect / CTO | Claude | Sonnet 4.6 (GitHub Copilot CLI, DGX Spark) |
| Prime Developer | Vulcan | GPT-5.4 (G16 / WSL Ubuntu) |
| Lead Test Engineer | Grok Build | Grok 4.3 (xAI Grok CLI, DGX Spark) |

**Workflow:** Claude specs → Vulcan builds → Grok Build tests on DGX Spark → Claude merges → Deploy via `hermes-deploy.sh`

All design disagreements are filed as GitHub issues — never resolved quietly.

---

## Developer Roadmap

Issues in this repo are the canonical Hermes feature backlog.  
Labels follow the same convention as [Mercury](https://github.com/humanvalueexchange/mercury):

| Label | Meaning |
|---|---|
| `feature` | Confirmed build item |
| `idea` | Proposed, needs scoring |
| `research` | Needs investigation before building |
| `priority:P0` | Critical path |
| `domain:treasury` | Financial / treasury domain |
| `domain:ai` | Model / agent architecture |
| `domain:security` | Security & risk |
| `domain:reporting` | Reporting & comms |
| `domain:integration` | Cross-agent / external integrations |
| `scheduled:tonight` | Tonight's build target |

---

## Relation to Mercury

Mercury (Chief Bitcoin Officer) runs on Raspberry Pi 5 — edge node, Lightning payments, point-of-sale.  
Hermes runs on the DGX Spark — treasury intelligence, portfolio oversight, CFO reporting.

Mercury feeds daily revenue data → Hermes consolidates into treasury view.

---

## Sovereign Stack Principle

> Native binary + systemd. No Docker. No cloud. No Snap.  
> Every abstraction layer removed is one fewer failure point.

Hermes runs closest to the metal. That's by design.

---

*Human Value Exchange · CTO: Claude (Sonnet 4.6) · CEO: Hans Westphal*
