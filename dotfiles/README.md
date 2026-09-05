# dotfiles/ — Deployment Mapping Reference

This directory contains all configuration artifacts that are deployed to the live DGX Spark.
These files are **templates and live copies** — the authoritative source of truth for the live system.

**Deployment managed by:** `scripts/hermes-deploy.sh`

---

## File → Live Path Mapping

| File in repo | Live path on DGX | Notes |
|---|---|---|
| `SOUL.md` | active Hermes profile `SOUL.md` | Hermes identity. Reloaded on every message — no restart needed after deploy. |
| `hermes-env.template` | `~/.hermes/.env` *(manual fill)* | Template only — never contains real secrets. Fill in secrets manually after fresh restore. |
| `hermes-model-preload.service` | `~/.config/systemd/user/hermes-model-preload.service` | Loads all 3 Platonic stack models on boot. |
| `hermes-gateway.service` | `~/.config/systemd/user/hermes-gateway-hanshermesagent.service` | Hermes WhatsApp gateway (main entry point). |

---

## Native Skills

Hermes native skills are loaded directly from the repository via `skills.external_dirs` in `config.yaml`:

```yaml
skills:
  external_dirs:
    - /home/hans/hanshermesagent/skills/hve
```

Changes to `skills/hve/**/SKILL.md` require a Hermes gateway restart after deploy.

---

## Deploy Commands

```bash
# Full automated deploy (diffs + restarts only what changed)
cd ~/hanshermesagent && bash scripts/hermes-deploy.sh

# Deploy SOUL.md only (no restart required)
cp dotfiles/SOUL.md ~/.hermes/profiles/<active-profile>/SOUL.md

# Reload user services after deploy
systemctl --user daemon-reload
systemctl --user restart hermes-gateway-hanshermesagent.service
```

---

## Secrets Policy

- **Never commit real secrets** to this repo — use `[PLACEHOLDER]` values in templates
- Live secrets live in the active Hermes profile `config.yaml` and `~/.hermes-mcp.env` (both gitignored)
- See `SECURITY.md` for the full placeholder convention and incident response procedure

---

## Config Backup Policy

One backup of the live config is maintained:

```bash
# Before any config change
cp ~/.hermes/profiles/<active-profile>/config.yaml ~/.hermes/profiles/<active-profile>/config.yaml.bak
```

Old numbered backups (`.bak.issue26`, `.bak.issue31`, etc.) are cleaned up after each issue
resolution. Timeshift daily snapshots on the DGX NVMe serve as the full system backup.
