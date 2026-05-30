#!/usr/bin/env bash
# hermes-deploy.sh — Deploy config/SOUL changes from hermes-cfo to live Hermes runtime
# Safe to run at any time — idempotent. No service restart unless changes detected.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HERMES_PROFILE=~/.hermes/profiles/main
HERMES_HOOKS=~/.hermes/agent-hooks
ENV_FILE=~/.hermes-mcp.env

echo "╔══════════════════════════════════════════════════╗"
echo "║       Hermes CFO — Deploy                        ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── 1. Pull latest from repo ──────────────────────────────────────────────────
echo "→ Pulling latest from hermes-cfo repo..."
cd "$REPO_ROOT"
git pull --rebase origin main
echo ""

# ── 2. Load secrets ───────────────────────────────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: $ENV_FILE not found. Run hermes-install.sh first."
  exit 1
fi
set -a
# shellcheck source=/dev/null
source "$ENV_FILE"
set +a
if [ -z "${HVE_MCP_API_KEY:-}" ]; then
  echo "ERROR: HVE_MCP_API_KEY not set in $ENV_FILE"
  exit 1
fi

# ── 3. Render new config ──────────────────────────────────────────────────────
NEW_CONFIG=$(mktemp)
sed "s/\${HVE_MCP_API_KEY}/$HVE_MCP_API_KEY/g" \
  "$REPO_ROOT/config/hermes-config.template.yaml" \
  > "$NEW_CONFIG"

RESTART_NEEDED=false

# ── 4. Config diff ────────────────────────────────────────────────────────────
if [ -f "$HERMES_PROFILE/config.yaml" ]; then
  if ! diff -q "$NEW_CONFIG" "$HERMES_PROFILE/config.yaml" &>/dev/null; then
    echo "→ Config changed — updating..."
    cp "$NEW_CONFIG" "$HERMES_PROFILE/config.yaml"
    echo "✅ config.yaml updated"
    RESTART_NEEDED=true
  else
    echo "✅ config.yaml — no changes"
  fi
else
  cp "$NEW_CONFIG" "$HERMES_PROFILE/config.yaml"
  echo "✅ config.yaml installed (first time)"
  RESTART_NEEDED=true
fi
rm -f "$NEW_CONFIG"

# ── 5. SOUL.md diff ───────────────────────────────────────────────────────────
if ! diff -q "$REPO_ROOT/dotfiles/SOUL.md" "$HERMES_PROFILE/SOUL.md" &>/dev/null 2>&1; then
  echo "→ SOUL.md changed — updating..."
  cp "$REPO_ROOT/dotfiles/SOUL.md" "$HERMES_PROFILE/SOUL.md"
  echo "✅ SOUL.md updated (no restart required — loaded fresh each message)"
else
  echo "✅ SOUL.md — no changes"
fi

# ── 6. Hooks diff ─────────────────────────────────────────────────────────────
mkdir -p "$HERMES_HOOKS"
if ! diff -q "$REPO_ROOT/dotfiles/inject-market-data.sh" \
            "$HERMES_HOOKS/inject-market-data.sh" &>/dev/null 2>&1; then
  echo "→ inject-market-data.sh changed — updating..."
  cp "$REPO_ROOT/dotfiles/inject-market-data.sh" "$HERMES_HOOKS/inject-market-data.sh"
  chmod +x "$HERMES_HOOKS/inject-market-data.sh"
  echo "✅ inject-market-data.sh updated"
  RESTART_NEEDED=true
else
  echo "✅ inject-market-data.sh — no changes"
fi

# ── 7. Restart if needed ──────────────────────────────────────────────────────
if $RESTART_NEEDED; then
  echo ""
  if systemctl --user is-active --quiet hermes-gateway.service 2>/dev/null; then
    echo "→ Restarting Hermes gateway (config changed)..."
    systemctl --user restart hermes-gateway.service
    sleep 2
    systemctl --user status hermes-gateway.service --no-pager | head -6
    echo "✅ Hermes gateway restarted"
  else
    echo "ℹ️  Gateway not running — changes applied, start with:"
    echo "   systemctl --user start hermes-gateway.service"
  fi
else
  echo ""
  echo "ℹ️  No changes requiring restart."
fi

echo ""
echo "Deploy complete ✅  $(date -u '+%Y-%m-%d %H:%M UTC')"
