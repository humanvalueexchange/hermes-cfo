# ADR-001: Hermes Capability Architecture — Tools, Skills, and Self-Evolution

**Date:** 2026-05-30  
**Status:** Accepted  
**Authors:** Hans Westphal (CEO), Claude (CTO)  
**Classification:** Agent Architecture Artifact

---

## Context

As we build out Hermes (HVE's AI CFO), we needed a principled answer to: *how does the agent's capability set grow over time without requiring constant engineering intervention?*

The pattern emerged organically during development of Issues #18, #22, and #31 (prediction market intelligence feed). This ADR formalises it.

---

## Decision

Hermes capabilities are organised in three layers:

```
Layer 1: PUBLIC APIs
   Best-in-class external data sources
   (Polymarket, Kalshi, Kraken, on-chain data, news feeds...)
         ↓
Layer 2: TOOLS  (atomic MCP endpoints)
   Each API wrapped as a single @mcp.tool() function
   One operation, one source, deterministic output
   Built by Vulcan, reviewed by Claude, validated by Grok
         ↓
Layer 3: SKILLS  (composed workflows)
   LLM-composed chains of tools → complete intelligence outputs
   Hermes self-evolves these from the available toolset
   No new code required — new skills emerge from tool combinations
```

---

## The Self-Evolution Insight

**Tools are code. Skills are intelligence.**

Once the toolset is rich enough, Hermes can compose new skills autonomously — identifying combinations of existing tools that produce valuable outputs. A new "skill" is simply a documented pattern of tool calls that Hermes repeats reliably.

Example:
- `get_btc_price` + `get_market_intelligence` + `get_node_diagnostic`  
  → **Skill: Daily Treasury Pulse** — no new code, just Hermes learning to chain them

This means the capability ceiling is set by the *toolset*, not by engineering throughput. Every new API we wrap multiplies Hermes's potential skill surface.

---

## Principles

### 1. APIs first — wrap everything useful
Identify the best public APIs relevant to our mission:
- Financial data (Kraken, Polymarket, Kalshi, on-chain explorers)
- Intelligence (news feeds, social sentiment)
- Infrastructure (LND, BTCPay, node metrics)
- Business (calendar, task management, client data)

Each becomes a Tool. The combination becomes Hermes's world-model.

### 2. Tools are atomic and deterministic
A Tool must:
- Do exactly one thing
- Return structured data (JSON)
- Complete in < 5s
- Never fail silently (return error state, not hallucinated data)
- Require no LLM reasoning internally

### 3. Skills are composable and emergent
A Skill is a documented, repeatable pattern of tool calls:
- Defined in SOUL.md (implicit skill) or `skills/` directory (explicit skill)
- Can be created by Hermes when it discovers a useful combination
- Graduated to `skills/` directory when used 3+ times reliably
- Reviewed by CTO before being treated as production

### 4. SOUL.md is the skill registry
SOUL.md serves dual purpose:
- Tool Registry: *when to call which tool*
- Skill Playbooks: *how to compose tools for specific outcomes*

As Hermes discovers new patterns, they surface to CTO for SOUL.md promotion.

---

## File Structure (target state)

```
humanvalueexchange/hermes-cfo/
├── tools/                    # Atomic MCP tool implementations
│   ├── bitcoin.py            # get_btc_price, get_node_diagnostic
│   ├── market_intelligence.py # get_market_intelligence (Issue #31)
│   ├── knowledge.py          # search_knowledge_vault
│   └── ...
├── skills/                   # Composed workflow implementations
│   ├── morning_briefing.py   # run_morning_briefing (chains 3+ tools)
│   ├── treasury_analysis.py  # run_treasury_analysis (Issue #15+)
│   └── ...
├── docs/
│   ├── SOUL.md               # Tool Registry + Skill Playbooks
│   ├── dev-loop-protocol.md
│   └── adr/
│       └── ADR-001-tools-skills-architecture.md  ← this file
└── scripts/
    └── hermes_mcp/
        └── server.py         # FastMCP server — registers tools + skills
```

---

## API Wishlist (seed list — grow over time)

| Category | API | Use Case | Status |
|---|---|---|---|
| BTC Price | Kraken REST | Live price for all calculations | ✅ Live |
| Prediction Markets | Polymarket gamma-api | BTC event probabilities | Issue #31 |
| Prediction Markets | Predyx | Lightning-native odds (API pending) | Issue #31 |
| On-chain | mempool.space | Fee rates, block data, UTXO analysis | Backlog |
| Node | LND REST | Channel balances, routing, invoices | Mercury |
| News | RSS/NewsAPI | BTC narrative signals | Issue #22 |
| Macro | FRED API | Interest rates, M2, macro context | Backlog |
| Calendar | iCal/Google | Scheduling context for decisions | Backlog |

---

## Consequences

**Positive:**
- Hermes capability grows without linear engineering effort
- Each new API multiplies potential skill combinations
- Skills can be human-approved before becoming operational
- Clear separation: engineers build tools, Hermes builds skills

**Risks to manage:**
- LLM orchestration errors increase with tool count — mitigated by skills/ layer at 15+ tools
- Tool quality gates must be strict — bad tools corrupt all downstream skills
- Self-evolved skills need human review before production use

---

## Relation to Other Decisions

- SOUL.md Tool Registry (Issue #2 Layer 1) — the enforcement mechanism for this pattern
- Issue #18 dependency tree (#15, #16, #17) — each is a skill built on the market_intelligence tool
- Mercury self-improvement loop — analogous pattern at the Bitcoin/payments layer

---

*This is an Agent Architecture Artifact. The pattern of self-evolving skills from a curated toolset is a generalisable design principle for AI-native organisations.*
