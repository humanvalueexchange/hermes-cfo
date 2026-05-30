# ADR-004: Deprecation of the patches/ Convention

**Date:** 2026-05-30  
**Status:** Accepted  
**Authors:** Hans Westphal (CEO), Claude (CTO)  

---

## Context

An early workflow convention in this repo used a `patches/` directory to record diffs of every change deployed to the live DGX as an audit trail ("what actually landed on the machine"). Several PRs and issues referenced this pattern.

In practice, the workflow broke down:

1. **Duplication** — the patch was a diff of a file that was already committed in full to the repo. The repo *is* the audit trail.
2. **Staleness** — patches were generated from intermediate states and quickly diverged from both the deployed version and the repo version, making them actively misleading.
3. **Maintenance burden** — generating, storing, and naming patches correctly required manual discipline that was not followed consistently.

---

## Decision

The `patches/` directory is **permanently removed**. All changes to deployed configurations must be committed to the main branch of this repo as the authoritative record.

### Audit trail going forward

| What changed | How it's recorded |
|---|---|
| Agent config (`config.yaml`) | Template in `config/hermes-config.template.yaml` — diff the template |
| SOUL.md | `dotfiles/SOUL.md` — diff in git history |
| Scripts | Committed directly — full git history |
| Model swaps | `VERSION.md` upgrade log + ADR-002 |
| Security changes | Commit message + `SECURITY.md` |

### Deploy verification

`scripts/hermes-deploy.sh` diffs live files against repo dotfiles and only writes changes — this provides an implicit record of what was out-of-sync at deploy time (visible in the terminal output and `logs/`).

---

## Consequences

- **Positive:** Eliminates stale, misleading diff files
- **Positive:** Reduces repo noise; single source of truth
- **Trade-off:** Less granular "what was deployed on date X" history — mitigated by git commit timestamps and `VERSION.md` log
- **Note for Vulcan/contributors:** Do not recreate `patches/`. If you need to record a specific deployment state, use a git tag on the deployed commit.

---

## Related

- Issue #35 (Grok review — patches/ gap flagged)  
- `scripts/hermes-deploy.sh` — current deploy/diff mechanism  
- `VERSION.md` — model swap and upgrade log
