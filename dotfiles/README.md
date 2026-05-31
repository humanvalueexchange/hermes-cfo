# dotfiles/ — Deployment Mapping Reference

This directory contains all configuration artifacts that are deployed to the live DGX Spark.
These files are **templates and live copies** — the authoritative source of truth for the live system.

**Deployment managed by:** `scripts/hermes-deploy.sh`

---

## File → Live Path Mapping

| File in repo | Live path on DGX | Notes |
|---|---|---|
| `SOUL.md` | `~/.hermes/profiles/main/SOUL.md` | Hermes identity. Reloaded on every Telegram message — no restart needed after deploy. |
| `hermes-env.template` | `~/.hermes/.env` *(manual fill)* | Template only — never contains real secrets. Fill in secrets manually after fresh restore. |
| `inject-market-data.sh` | `~/.hermes/agent-hooks/inject-market-data.sh` | Market data hook injected into every Hermes request. |
| `hermes-model-preload.service` | `~/.config/systemd/user/hermes-model-preload.service` | Loads all 3 Platonic stack models on boot. |
| `hermes-gateway.service` | `~/.config/systemd/user/hermes-gateway.service` | Hermes Telegram gateway (main entry point). |
| `hermes-mcp.service` | `~/.config/systemd/user/hermes-mcp.service` | Hermes MCP tool server. |
| `hermes-data-refresh.service` | `~/.config/systemd/user/hermes-data-refresh.service` | Nightly market data refresh. |
| `hermes-data-refresh.timer` | `~/.config/systemd/user/hermes-data-refresh.timer` | Systemd timer for data refresh (triggers service). |
| `hermes-freqtrade.service` | `~/.config/systemd/user/hermes-freqtrade.service` | Freqtrade integration service. |
| `hermes-telegram-log.service` | `~/.config/systemd/user/hermes-telegram-log.service` | Telegram audit log service. |

---

## Deploy Commands

```bash
# Full automated deploy (diffs + restarts only what changed)
cd ~/hermes-cfo && bash scripts/hermes-deploy.sh

# Deploy SOUL.md only (no restart required)
cp dotfiles/SOUL.md ~/.hermes/profiles/main/SOUL.md

# Deploy a specific hook
cp dotfiles/inject-market-data.sh ~/.hermes/agent-hooks/inject-market-data.sh
chmod +x ~/.hermes/agent-hooks/inject-market-data.sh

# Reload a specific systemd service after deploy
systemctl --user daemon-reload
systemctl --user restart hermes-gateway.service
```

---

## Secrets Policy

- **Never commit real secrets** to this repo — use `[PLACEHOLDER]` values in templates
- Live secrets live in `~/.hermes/profiles/main/config.yaml` and `~/.hermes-mcp.env` (both gitignored)
- See `SECURITY.md` for the full placeholder convention and incident response procedure

---

## Config Backup Policy

One backup of the live config is maintained:

```bash
# Before any config change
cp ~/.hermes/profiles/main/config.yaml ~/.hermes/profiles/main/config.yaml.bak
```

Old numbered backups (`.bak.issue26`, `.bak.issue31`, etc.) are cleaned up after each issue
resolution. Timeshift daily snapshots on the DGX NVMe serve as the full system backup.
