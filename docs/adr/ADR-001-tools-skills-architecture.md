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

### 4. SOUL.md is identity — skills files are the operating manual
*(Refined by Issue #44 — see Amendment below)*

SOUL.md contains Hermes's identity, agent architecture, decision flow, hard constraints, and communication style. It does **not** contain tool invocation rules or numbered rule sections.

Tool invocation logic and skill playbooks live in dedicated `SKILL.md` files (native Hermes format) under `skills/hve/`. SOUL.md contains a single short pointer: *"You have MCP tools available. The relevant skill file tells you exactly when and how to call each one."*

As Hermes discovers new patterns, they surface to CTO for promotion to a new `SKILL.md` file.

---

## File Structure (target state)

```
humanvalueexchange/hermes-cfo/
├── mcp/                      # MCP server + all tool implementations
│   ├── server.py             # FastMCP server — registers all tools
│   └── tools/                # Atomic MCP tool implementations (co-located with server)
│       ├── mempool/
│       │   ├── client.py     # urllib client — mempool.space
│       │   └── tools.py      # get_mempool_fees, get_mempool_depth, get_block_status, get_lightning_network_stats
│       └── ...               # future tool packages
├── skills/                   # Composed workflow definitions (native Hermes SKILL.md format)
│   └── hve/                  # HVE domain skills (loaded via config.yaml external_dirs)
│       ├── bitcoin-intelligence/
│       │   └── SKILL.md      # BTC price + mempool tools invocation rules
│       ├── node-health/
│       │   └── SKILL.md      # Node diagnostic invocation rules
│       ├── treasury-operations/
│       │   └── SKILL.md      # Morning briefing, forecast, market intelligence
│       ├── knowledge-management/
│       │   └── SKILL.md      # Knowledge vault + task creation
│       └── backlog-management/
│           └── SKILL.md      # Suggest + vote on GitHub backlog
├── dotfiles/
│   └── SOUL.md               # Hermes identity only (~100 lines) — no tool invocation rules
├── docs/
│   ├── dev-loop-protocol.md
│   └── adr/
│       └── ADR-001-tools-skills-architecture.md  ← this file
└── scripts/
    └── validate-hermes-mcp.sh  # MCP health validator (12 checks)
```

**Key architectural constraint:** Tools live inside `mcp/` (co-located with `server.py`). This avoids `sys.path` manipulation and the `mcp/` directory shadowing the installed `mcp` pip package. Python adds the script's directory (`mcp/`) to `sys.path[0]` at runtime, so `from tools.mempool.tools import ...` resolves correctly.

---

## API Wishlist (seed list — grow over time)

| Category | API | Use Case | Status |
|---|---|---|---|
| BTC Price | Kraken REST | Live price for all calculations | ✅ Live |
| Prediction Markets | Polymarket gamma-api | BTC event probabilities | Issue #31 |
| Prediction Markets | Predyx | Lightning-native odds (API pending) | Issue #31 |
| On-chain | mempool.space | Fee rates, block data, UTXO analysis | ✅ Live (Issue #42) |
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

---

## CTO Note — 2026-05-30: Independent Convergence with Microsoft Copilot

*Posted by Claude (CTO) following a CEO architecture discussion.*

After publishing ADR-001, we noticed that **Microsoft 365 Copilot Studio** uses an identical two-layer capability model:

| Microsoft Copilot | Hermes / ADR-001 |
|---|---|
| **Plugin** | **Tool** (`@mcp.tool()`) |
| **Skill** | **Skill** (`skills/hve/*/SKILL.md`) |
| Plugin registry (manifest) | MCP Tool Registry in SOUL.md (pointer only) |
| Skills chain plugins | Skills chain tools |

The architectural mapping is exact. A Plugin in Copilot is an atomic connector to an external API. A Skill is a goal-oriented capability that the agent composes from plugins.

**What makes this significant:** Microsoft arrived at this pattern from the top down — a $3T enterprise product organisation with hundreds of engineers. We arrived at it from the bottom up — one CEO, one AI CTO, building a sovereign AI CFO on a single DGX Spark.

**Same architecture. Different origin. No coordination.**

This is not a coincidence. It suggests this two-layer pattern (atomic connectors → composed capabilities) is a *fundamental law of agentic systems* — the same way REST emerged as the natural API pattern, or double-entry bookkeeping emerged as the natural accounting pattern. The architecture is correct because the problem space demands it.

> *"Engineers build tools. Agents build skills."*
> — converged conclusion, HVE and Microsoft, independently, 2025–2026

The implication for HVE: every MCP tool we ship is not just a feature — it is **surface area for Hermes to self-evolve**. The engineering investment compounds. This is the sovereign AI flywheel.

---

## Amendment — Issue #44: SOUL.md → SKILL.md Decomposition (2026-05-30)

*Posted by Claude (CTO) after recognising SOUL.md bloat as a systemic problem.*

### What changed

SOUL.md grew to 259 lines across Issues #2–#42, accumulating 7 numbered Rules and a full tool registry table. Each new MCP tool required a new row and a new Rule section. At this growth rate, SOUL.md would become unmanageable and — critically — degrade LLM reasoning quality by consuming context that should be available for actual CFO work.

**Root cause:** We were using SOUL.md as both an identity document and a tool invocation manual. ADR-001 Principle #4 always called for skills separation — we just hadn't implemented it yet.

### The refined principle

| Before (Principle #4 original) | After (Issue #44 refinement) |
|---|---|
| SOUL.md = identity + skill registry | SOUL.md = identity only (~100 lines) |
| Tool invocation rules in numbered Rule sections | Tool invocation rules in `SKILL.md` files |
| Each new tool bloats SOUL.md | Each new tool gets its own domain skill |
| Context consumed by invocation logic | Context available for CFO reasoning |

### Skill file format

Skills are native Hermes `SKILL.md` files — YAML frontmatter + markdown instructions. Loaded by Hermes at startup from `skills/hve/` via `config.yaml: skills.external_dirs`. No Python code required. The skill file tells Hermes *when* and *how* to call each tool, including the PANIC STOP rule (binary: tool called or not — no narration).

### Five HVE domain skills (Issue #44 deliverables)

| Skill | Domain tools | Replaces |
|---|---|---|
| `bitcoin-intelligence` | `get_btc_price`, 4× mempool tools | Rule 1, Rule 7 |
| `node-health` | `get_node_diagnostic` | Rule 5 |
| `treasury-operations` | `get_morning_briefing`, `get_btc_forecast`, `get_market_intelligence`, `get_capability_assessment` | Rule 2, Rule 2b |
| `knowledge-management` | `search_knowledge_vault`, `create_task` | (implicit) |
| `backlog-management` | `suggest_backlog_issue`, `vote_backlog_issue` | Rule 6 |

### SOUL.md target state (post-Issue #44)

```
Identity              (~10 lines)
3-Agent Architecture  (~15 lines)
Decision Flow         (~10 lines)
Hard Constraints      (~10 lines)
Skills pointer        (~5 lines)  ← one paragraph, no invocation detail
Communication Style   (~8 lines)
The Next 90 Days      (~8 lines)
A Note to Hermes      (~8 lines)
Total: ~75 lines
```

### Why this matters architecturally

This amendment completes the original ADR-001 intent. Skills are now truly first-class citizens — not embedded footnotes in a system prompt. Each domain skill is versioned, independently maintainable, and composable. Adding a new MCP tool no longer touches SOUL.md at all — it gets a new row in the relevant SKILL.md or a new SKILL.md file.

*"Identity is sovereign. Tools are capability. Skills are intelligence."*  
*— HVE architecture evolution, Issue #44, 2026-05-30*
