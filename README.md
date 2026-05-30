# Hermes — Sovereign AI CFO & Treasury Agent

**Status:** Active — running 24/7 on NVIDIA DGX Spark  
**Version:** v1.0.0  
**Architecture:** 4-model collective (conductor + executor + critic + clarifier)  
**Hardware:** NVIDIA DGX Spark · 128 GB unified memory · ARM64 / aarch64  

---

## What Hermes Is

Hermes is the Chief Financial Officer of Human Value Exchange — a 4-agent AI collective running locally on the DGX Spark. No cloud. No subscriptions. Sovereign treasury intelligence, running 24/7.

Hermes monitors balances, enforces treasury policy, reports to the CEO, and coordinates with Mercury (Bitcoin Lightning node) for real-time payment intelligence.

---

## Model Stack

| Role | Model | Purpose |
|---|---|---|
| Conductor | `mistral-small:24b` | Orchestrates the collective, synthesizes trade proposals |
| Research | `mistral-small:24b` | Market analysis, price action, strategy research |
| Critic | `gemma2:27b` | Risk review, veto authority (`CRITIC:APPROVE` / `CRITIC:VETO`) |
| Execution | `nemotron-3-nano:30b` | Position sizing, fee calculations, code generation |

All models run via **Ollama** on the DGX Spark (native binary, systemd-managed).

**Decision flow (mandatory for all trade decisions):**
```
Research → Conductor → Critic → Execution (only on CRITIC:APPROVE)
```
A `CRITIC:VETO` terminates the flow. No override.

---

## Architecture

```
CEO (Hans) ──Telegram──▶ Hermes Gateway
                              │
                    ┌─────────┴──────────┐
                    │   Conductor        │  mistral-small:24b
                    │   (Orchestrator)   │
                    └─────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
         Research          Critic          Execution
    mistral-small:24b   gemma2:27b    nemotron-3-nano:30b
    (Analysis/Strategy) (Risk/Veto)   (Math/Code/Audit)
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
| **Gateway** | Hermes Gateway service (`~/.hermes/`) |
| **Config** | `~/.hermes/profiles/main/config.yaml` |
| **MCP** | `~/.hermes-mcp.env` (API keys, never committed) |
| **Comms** | Telegram (inbound/outbound), Mattermost (reports) |
| **LAN IP** | `192.168.1.10` (static Ethernet, permanent) |

---

## Repository Structure

```
hermes-cfo/
├── README.md                         ← you are here
├── docs/
│   └── SOUL.md                       ← full Hermes identity, rules, HVE vision
├── config/
│   ├── hermes-config.template.yaml   ← config template (secrets as ${PLACEHOLDERS})
│   └── hermes-env.template           ← .env template — what secrets are needed
├── src/
│   └── hooks/
│       └── inject-market-data.sh     ← pre-LLM hook: live BTC price injection
└── scripts/
    ├── hermes-install.sh             ← bootstrap on fresh DGX Spark
    └── hermes-deploy.sh              ← deploy config changes to live runtime
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
