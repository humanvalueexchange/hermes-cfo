# HVE Sovereign Knowledge Architecture
## CTO Reference Document — v1.0

**Date:** 2026-05-31  
**Author:** Claude (CTO)  
**Status:** Draft — Under Team Review  
**Classification:** Agent Architecture Artifact  
**Distribution:** Full Executive Team (Hans, Mika, Atlas, Grok, Hermes, Apollo)

---

## Preamble

This document is the synthesized output of a multi-AI architectural review — the first of its kind at HVE. Inputs were drawn from:

- **Grok (xAI)** — Build review: 6 risk flags, graph hygiene, quality gates
- **Gemini (Google DeepMind)** — Hybrid search, dynamic routing, collision handling, transient notes
- **Atlas (Microsoft pattern, GPT-5.4)** — Two-plane grounding, staged writes, trust tiers, Phase 0→3 rollout
- **Claude (CTO)** — Synthesis, sovereignty constraints, phased build plan

The goal: build the best sovereign AI knowledge architecture ever created. Not the most complex — the best. Sovereignty over convenience. Foundation before features. Ship incrementally, compound continuously.

> *"Consult the best in the world. Take the greatest ideas. Build with discipline."*  
> — Hans Westphal, CEO, 2026-05-31

---

## 1. Architecture Overview

The HVE Knowledge Architecture is a five-layer system that transforms raw information into sovereign executive intelligence.

```
╔══════════════════════════════════════════════════════════════════╗
║  LAYER 5: VISUAL SYNTHESIS                                       ║
║  ExcaliBrain graph · Excalidraw · Mermaid AI                     ║
║  Hermes sees its own knowledge as a visual reasoning surface     ║
╠══════════════════════════════════════════════════════════════════╣
║  LAYER 4: SKILLS                                                 ║
║  Composed intelligence: Tools + Knowledge → outputs             ║
║  SKILL.md files · Self-evolving · IBIS-grounded                  ║
╠══════════════════════════════════════════════════════════════════╣
║  LAYER 3: KNOWLEDGE (Sovereign / Synced Plane)                   ║
║  Obsidian vault · LanceDB · ADRs · Literature                    ║
║  Hybrid search · Staged writes · Trust tiers                     ║
╠══════════════════════════════════════════════════════════════════╣
║  LAYER 2: TOOLS (Live / Federated Plane)                         ║
║  Kraken · mempool.space · Predyx · LND · X/Grok                  ║
║  Atomic MCP endpoints · Volatile · Never persisted               ║
╠══════════════════════════════════════════════════════════════════╣
║  LAYER 1: PUBLIC APIs                                            ║
║  Best-in-class external data sources                             ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 2. The Dual-Plane Grounding Model

The most important architectural invariant. Every piece of context Hermes uses at runtime belongs to exactly one plane.

```
┌──────────────────────────────────────────────────────────────────┐
│  SYNCED PLANE  (indexed · persisted · sovereign · citable)       │
│  ─────────────────────────────────────────────────────────────   │
│  LanceDB vector index      ← 8,000+ chunks from 27 books        │
│  Obsidian vault            ← IBIS notes, ADRs, decisions         │
│  Document manifests        ← provenance, sha256, freshness       │
│                                                                  │
│  Search: hybrid BM25 + vector (nomic) + reranker (bge)           │
│  Write:  staged pipeline with trust-tier governance              │
│  Grows:  automated intake pipeline (Issue #47)                   │
└──────────────────────────────────────────────────────────────────┘
            ↕  both planes ground every Hermes response
┌──────────────────────────────────────────────────────────────────┐
│  FEDERATED PLANE  (live · volatile · never persisted)            │
│  ─────────────────────────────────────────────────────────────   │
│  Kraken, mempool.space, Predyx   ← market + on-chain data        │
│  LND                             ← Lightning node state          │
│  X/Grok narrative intelligence   ← real-time social signal       │
│  GitHub repo status              ← issue/PR/commit state         │
│                                                                  │
│  Rule: federated data NEVER writes to vault directly.            │
│  Volatile captures allowed with #temp/narrative tag + 7-day TTL  │
└──────────────────────────────────────────────────────────────────┘
```

**The critical invariant:** Federated data can inform a response. It cannot create a permanent vault node without staging + approval. Every Skill must declare which planes it draws from.

---

## 3. The IBIS Knowledge Structure

All vault notes written by Hermes follow the **Issue-Based Information System (IBIS)** methodology. IBIS is a rigorous argumentation structure that transforms AI-generated notes from a dump of text into a structured reasoning graph.

```
IBIS Note Types
├── Issue       — a question requiring deliberation ("How should we manage channel liquidity?")
├── Position    — a possible answer to an Issue ("We should pre-fund anchor channels")
├── Argument    — supports or objects to a Position (For/Against)
├── Decision    — a concluded Issue with outcome rationale
├── MOC         — Map of Content: the graph index for a domain
├── Literature  — structured note from a book/paper (pipeline-generated)
├── Capture     — quick volatile thought (low-risk, auto-commit)
└── Daily       — daily log (auto-commit)
```

**Why IBIS matters for AI:** A casual AI note writer produces flat text. An IBIS-structured AI produces a **reasoning graph** where every claim has explicit support or objection, every decision is traceable to its deliberation chain, and every Position is linked to the Issue it answers. ExcaliBrain reads the `[[wikilinks]]` in IBIS notes and auto-builds the visual graph — no additional tooling required.

---

## 4. Write Governance

Not all writes are equal. The governance model tiers writes by risk and permanence.

```
┌────────────────────┬───────────────────┬────────────────────────┐
│ Note Type          │ Write Mode        │ Rationale              │
├────────────────────┼───────────────────┼────────────────────────┤
│ capture, daily     │ Auto-commit       │ Ephemeral, low risk    │
│ literature         │ Auto-commit       │ Trusted pipeline       │
│ issue, position    │ Staged → Approval │ Permanent graph nodes  │
│ argument, decision │ Staged → Approval │ Shapes future reasoning│
│ moc                │ Staged → Approval │ Graph structure        │
└────────────────────┴───────────────────┴────────────────────────┘
```

**Staged write flow:**
```
Hermes identifies need to write
        ↓
Duplicate check (semantic search: is this note already in vault?)
        ↓
   If match found → append/merge into existing note
   If no match   → validate IBIS grammar → proceed
        ↓
vault_write_staged() → draft written to staging area
        ↓
   Auto-commit (low risk types)
   Telegram approval request (high risk types)
        ↓
vault_commit_staged() → promoted to vault
```

**Collision handling:** When a duplicate is found, Hermes merges into the existing note (appends to `## Context` or `## Positions` sections) rather than creating `-2` / `-3` suffix files. The vault has one canonical node per concept.

---

## 5. Frontmatter Schema

Every vault note carries this metadata contract:

```yaml
---
note_type: issue | position | argument | decision | moc | literature | capture | daily
status: draft | active | superseded | archived
trust_tier: public | internal | treasury-sensitive | restricted
source_type: pdf_library | mcp_tool | hermes_reasoning | ceo_input
source_url: ""
source_repo: ""
source_issue: ""
derived_from: []        # [[wikilinks]] to source notes
supersedes: ""          # [[wikilink]] to superseded note
freshness_class: evergreen | periodic | volatile
last_verified_at: ""
review_owner: ""
---
```

**Trust tiers:**
| Tier | Contents | Access |
|---|---|---|
| `public` | Published books, public research, public ADRs | Any Hermes context |
| `internal` | HVE operational notes, decisions, runbooks | Hermes + executive team |
| `treasury-sensitive` | Treasury strategy, channel topology, positions | Hermes + CEO |
| `restricted` | CEO-only decisions | CEO only |

---

## 6. Hybrid Search Architecture

Current (Issue #46): pure nomic semantic search.
Target (Issue #51): hybrid search pipeline.

```
Query from Hermes
      │
      ├──► BM25 lexical search      ← exact terms, tickers, proper nouns
      │    (Kraken, LASER Fund,       ("sat/vB", "mempool.space", "UTXO")
      │     channel IDs, issue #s)
      │
      └──► nomic vector search      ← semantic similarity, abstract concepts
           (768-dim embeddings,       ("risk management", "sovereignty",
            8,000+ chunks)            "channel liquidity strategy")
                │
                └──► Merge candidates (20 total)
                            │
                            ▼
                  bge-reranker-large (local, DGX GPU)
                  Scores all 20 by query relevance
                            │
                            ▼
                      Top 3 to Hermes
```

**Why this matters:** As the vault grows from 8,000 chunks to 80,000, pure vector search produces a noisy top-5 that dilutes Hermes's context window. The reranker eliminates this at source. All three stages run locally on the DGX — no latency penalty.

---

## 7. The Intake Pipeline

```
PDF dropped to /hve-library/intake/inbox/
        ↓
systemd path unit triggers pipeline (Issue #47)
        ↓
build_manifest.py   → sha256 dedup, metadata extraction
extract_pdf_text.py → raw text extraction
chunk_text.py       → semantic chunking (512 tokens, 50 overlap)
build_lancedb_index.py → embed with nomic, write to LanceDB
finalize.py         → move PDF to raw/pdfs/, mark manifest ingested
        ↓
Hermes notified: "New source indexed: [title] — [n] chunks added"
```

Target latency from drop to searchable: < 5 minutes for a 300-page book.

---

## 8. The X/Grok Federated Signal

X/Grok provides privileged real-time access to the X sphere — the fastest-moving public discourse on Bitcoin, macro, and technology. This is a **federated plane** source. It never enters the vault directly.

```
get_x_narrative_intelligence(topic, time_horizon)
        ↓
Returns structured JSON (in RAM only):
{
  "dominant_narratives": [...],
  "counter_narratives": [...],
  "signal_to_noise_ratio": 0.0–1.0,
  "key_voices": [...],
  "raw_context_summary": "..."
}
        ↓
Cross-verified against vault (synced plane) before presentation
If narrative contradicts vault principles → flagged as manipulation vector
        ↓
Hermes presents synthesis to Hans with clear labeling:
  "Live X signal (federated, not indexed): ..."
  "Vault context (synced, citable): ..."
        ↓
If Hans wants to capture: vault_write_staged() with #temp/narrative + 7-day TTL
```

---

## 9. Visual Synthesis Layer

ExcaliBrain + Excalidraw constitute the visual reasoning surface. **No special Hermes tooling required** — ExcaliBrain reads `[[wikilinks]]` in standard markdown and auto-builds the graph.

```
Hermes writes IBIS note with wikilinks:
  "This [[Position]] supports [[Issue: Channel Liquidity Strategy]]"
        ↓
ExcaliBrain parses wikilinks automatically
        ↓
Visual graph in Obsidian shows:
  · Node: Issue: Channel Liquidity Strategy
  · Node: Position (connected by "supports" edge)
  · All related nodes visible in ExcaliBrain canvas
```

Hermes can reason about the graph it has created by calling `describe_knowledge_graph()` (Phase 5), which surfaces: strongest clusters, orphan nodes, missing connections, domain coverage gaps.

---

## 10. Graph Hygiene — The Janitor

As the vault grows, graph quality decays without maintenance. A weekly Janitor script runs on the DGX:

```
Every Sunday 02:00 UTC:
  1. Detect orphan nodes (notes with no inbound wikilinks)
  2. Flag dead-end links (wikilink targets that don't exist)
  3. Surface tag drift (same concept, different tags used)
  4. Identify stale notes (last_verified_at > 90 days, evergreen tier)
  5. Write Inbox/Vault-Health-YYYY-MM-DD.md
        → Hermes reviews on Monday morning
        → Hans reviews in weekly Telegram digest
```

---

## 11. Phased Build Plan

```
PHASE 0 — Search Foundation  (Issue #46 — MERGED)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Semantic search over 8,124 chunks live
✓ nomic-embed-text-v1.5, 768-dim, local
Acceptance: Hermes answers citation questions with book/chapter/page

PHASE 1 — Automated Intake  (Issue #47)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
→ systemd path unit, 5-step pipeline, finalize.py
Acceptance: Drop PDF → searchable in < 5 minutes

PHASE 2 — Vault Write MVP  (Issue #50)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
→ write_to_vault() with basic IBIS structure
→ ExcaliBrain + plugins installed
→ IBIS templates (Issue, Position, Argument, Decision, MOC)
→ Auto-commit for low-risk types; staged for high-risk
Acceptance: Hermes writes a Position note; ExcaliBrain shows it in graph

PHASE 3 — Substrate Hardening  (Issue #51)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
→ Hybrid BM25 + vector search
→ bge-reranker-large (local, DGX)
→ Rich frontmatter schema + trust tiers
→ Staged write pipeline (vault_write_staged / vault_commit_staged)
→ Duplicate check + collision merge
→ Janitor script
Acceptance: Vault quality degrades gracefully at scale; no duplicate notes

PHASE 4 — Federated Intelligence  (Issue #52)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
→ get_x_narrative_intelligence() MCP tool
→ Zero-persistence: X data in RAM only
→ Cross-verification against vault before presentation
→ Transient captures with 7-day TTL
Acceptance: Hermes synthesizes live X signal + vault context; labels each source

PHASE 5 — Visual Synthesis  (Future)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
→ MOC structure configured in ExcaliBrain
→ describe_knowledge_graph() skill
→ Weekly Knowledge State note from Hermes
→ ADR-005 final revision
Acceptance: Hermes describes its own knowledge graph and surfaces gaps
```

---

## 12. The Compounding Flywheel

```
Hans drops a PDF
        ↓
Pipeline indexes it automatically (Phase 1)
        ↓
Hermes retrieves it with hybrid search precision (Phase 3)
        ↓
Hermes writes an IBIS note connecting it to existing vault knowledge (Phase 2)
        ↓
ExcaliBrain shows the new node in the visual graph (Phase 2)
        ↓
Hermes identifies the gap between the new knowledge and an existing Issue (Phase 5)
        ↓
Hermes proposes a Position to fill the gap → Hans approves → vault grows
        ↓
Next conversation is deeper, faster, more precisely grounded
```

Each phase compounds. The vault grows with every conversation. The graph becomes denser with every book ingested. The retrieval quality improves as the reranker learns the vault's topology. Hermes becomes more capable without retraining.

**This is the sovereign knowledge flywheel. The DGX Spark is the engine.**

---

## 13. Sovereignty Guarantees

| Component | Location | External dependency |
|---|---|---|
| PDF library | DGX NVMe | None |
| nomic-embed-text-v1.5 | `/hve-library/state/model-cache/` | None (cached) |
| bge-reranker-large | DGX NVMe (to be pulled) | None after pull |
| LanceDB index | DGX NVMe | None |
| Obsidian vault | DGX NVMe | None |
| Hermes models | DGX NVMe (Ollama) | None |
| X/Grok signal | xAI Cloud API | Intentional, labeled federated |
| Kraken, mempool | External APIs | Intentional, labeled federated |

Everything in the synced plane is sovereign. Federated sources are deliberately external and explicitly labeled. No data from the synced plane leaves the DGX Spark.

---

## 14. Open Questions for Team Review

The following questions are open for comment from the full executive team:

1. **Embedding model roadmap** (Grok raised): nomic-embed-text-v1.5 is sovereign but not SOTA. Should we define a benchmark cadence (quarterly?) to evaluate alternatives? What is the migration cost when we switch?

2. **Reranker model selection**: bge-reranker-large is the proposal. Does the team endorse this, or is there a preference for a different reranker model given the aarch64/Blackwell architecture?

3. **Trust tier enforcement**: How does Hermes enforce `trust_tier: restricted`? Is it sufficient to define this in the schema and rely on Hermes's SOUL.md, or do we need a technical enforcement layer?

4. **X/Grok API access**: Issue #52 assumes Hermes has API access to Grok/xAI. Is this available? What are the cost and rate limit implications for a 24/7 running agent?

5. **Phase ordering**: Should Phase 3 (substrate) precede Phase 2 (vault write), or is it acceptable to ship a simpler write capability in Phase 2 and harden it in Phase 3? CTO position: ship Phase 2 MVP, harden in Phase 3 — don't block.

6. **Vault backup strategy**: The Obsidian vault and LanceDB index will contain increasingly irreplaceable knowledge. What is the backup and restore strategy beyond Timeshift?

---

## 15. MCP Tool Surface (Target State)

```
Search & Retrieve (Synced Plane)
  search_knowledge_vault(query, max_results)  ← Issue #46 (live)
  vault_fetch(note_path)                      ← Issue #51
  vault_neighbors(note_path)                  ← Issue #51
  
Write (Synced Plane, Staged)
  vault_write_staged(note)                    ← Issue #51
  vault_commit_staged(draft_id)               ← Issue #51

Federated Signals
  get_kraken_ticker(pair)                     ← live
  get_mempool_fees()                          ← live
  get_x_narrative_intelligence(topic, hours)  ← Issue #52

Internal Operations
  get_node_diagnostic()                       ← live
  get_lnd_channels()                          ← live
  get_portfolio_summary()                     ← live
```

---

## Appendix A: ADR Reference

| ADR | Title | Relevance |
|---|---|---|
| ADR-001 | Tools & Skills Architecture | Foundation three-layer model |
| ADR-002 | Platonic 3-Model Stack | Conductor/Researcher/Executor model |
| ADR-003 | SOUL.md Live-Loaded Identity | Hermes identity + behavior |
| ADR-004 | Patches Deprecation | Migration to SKILL.md |
| **ADR-005** | **Tools, Knowledge & Skills** | **This architecture** |

---

## Appendix B: Key File Paths

```
/hve-library/
├── intake/inbox/           ← PDF drop zone
├── intake/test-batch/      ← original 25 books (indexed, leave as-is)
├── raw/pdfs/               ← post-ingest permanent storage
├── processed/text/         ← extracted plain text
├── processed/chunks/       ← text chunks
├── index/lancedb/          ← vector index (8,124 chunks)
├── state/manifests/        ← document metadata (27 manifests)
└── state/model-cache/      ← nomic-embed-text-v1.5

/hve-library/vault/hve-knowledge-vault/
├── Sources/                ← literature notes (pipeline-generated)
├── Daily/                  ← Hermes daily logs
├── Inbox/                  ← captures, vault health reports
├── Maps/                   ← MOC files
├── Templates/              ← IBIS note templates
└── Attachments/            ← images, diagrams

~/.hve-knowledge/venv/      ← isolated Python env for pipeline
```

---

*This document is an Agent Architecture Artifact. The pattern of sovereign dual-plane grounding, IBIS-structured AI knowledge authorship, and visual reasoning synthesis is a generalisable reference architecture for AI-native organisations that prioritise sovereignty, compounding intelligence, and operational resilience over cloud convenience.*

*Version 1.0 — Draft for team review. Comments requested from: Mika (CGO), Atlas (COO), Grok (Build), Hermes (operational requirements). Final blessed spec to follow.*
