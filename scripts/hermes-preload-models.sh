#!/usr/bin/env bash
# hermes-preload-models.sh
# Pre-loads all 3 Platonic stack models into Ollama unified memory on boot.
# Runs as a systemd user service. Models stay hot indefinitely (keep_alive: -1).
# Called by: hermes-model-preload.service

set -euo pipefail

OLLAMA_URL="http://localhost:11434"

# Canonical Platonic 3-model stack — update here when model stack changes
MODELS=(
  "qwen3.5:9b"          # Conductor  — 262K ctx, 6.6 GB
  "mistral-small:24b"   # Clarifier  — 131K ctx, 14 GB
  "nemotron-3-nano:30b" # Executor   — 131K ctx, 24 GB
)

wait_for_ollama() {
  local retries=90
  echo "[preload] Waiting for Ollama API..."
  while ! curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; do
    sleep 2
    retries=$((retries - 1))
    [ "${retries}" -le 0 ] && { echo "[preload] ERROR: Ollama not ready after 180s — aborting"; exit 1; }
  done
  echo "[preload] Ollama ready."
}

load_model() {
  local model="$1"
  echo "[preload] Loading: ${model}"
  local response
  response=$(curl -s --max-time 180 "${OLLAMA_URL}/api/generate" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"${model}\",\"prompt\":\"\",\"keep_alive\":-1}" 2>&1)
  if echo "${response}" | grep -q '"done":true\|"status"'; then
    echo "[preload] ✅ Hot: ${model}"
  else
    echo "[preload] ⚠️  Warning: unexpected response for ${model} — may not be loaded"
    echo "${response}" | head -3
  fi
}

wait_for_ollama

echo "[preload] Loading Platonic 3-model stack into unified memory..."
for model in "${MODELS[@]}"; do
  load_model "${model}"
done

echo "[preload] All 3 Platonic stack models loaded and hot. Memory:"
curl -s "${OLLAMA_URL}/api/ps" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    for m in d.get('models', []):
        size_gb = m.get('size', 0) / 1e9
        print(f'  {m[\"name\"]:<35} {size_gb:.1f} GB')
except Exception as e:
    print(f'  (could not parse ps response: {e})')
"
