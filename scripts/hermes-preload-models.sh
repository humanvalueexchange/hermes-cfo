#!/usr/bin/env bash
# hermes-preload-models.sh
# Pre-loads all 3 Platonic stack models into Ollama unified memory on boot.
# Runs as a systemd user service. Models stay hot indefinitely (keep_alive: -1).
# Also evicts any non-Platonic models that may be lingering in memory.
# Called by: hermes-model-preload.service

set -euo pipefail

OLLAMA_URL="http://localhost:11434"

# Canonical Platonic 3-model stack — update here when model stack changes
# Format: "name:tag|num_ctx"
MODELS=(
  "qwen3.5:9b|262144"          # Conductor  — 262K ctx, 6.6 GB loaded
  "mistral-small:24b|131072"   # Clarifier  — 131K ctx, 14 GB loaded
  "nemotron-3-nano:30b|131072" # Executor   — 131K ctx, 24 GB loaded
)

# Models to explicitly evict if found loaded (retired from Platonic stack)
EVICT_MODELS=(
  "qwen3.5:27b"
  "qwen2.5:14b"
  "gemma2:27b"
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

evict_model() {
  local model="$1"
  # Only evict if currently loaded
  if curl -s "${OLLAMA_URL}/api/ps" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if any(m['name'].startswith('${model}'.split(':')[0]) for m in d.get('models',[])) else 1)" 2>/dev/null; then
    echo "[preload] Evicting non-Platonic model: ${model}"
    curl -s --max-time 30 "${OLLAMA_URL}/api/generate" \
      -H "Content-Type: application/json" \
      -d "{\"model\":\"${model}\",\"prompt\":\"\",\"keep_alive\":0}" >/dev/null 2>&1
    echo "[preload] Evicted: ${model}"
  fi
}

load_model() {
  local model="$1"
  local num_ctx="$2"
  echo "[preload] Loading: ${model} (ctx: ${num_ctx})"
  local response
  response=$(curl -s --max-time 180 "${OLLAMA_URL}/api/generate" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"${model}\",\"prompt\":\"\",\"keep_alive\":-1,\"options\":{\"num_ctx\":${num_ctx}}}" 2>&1)
  if echo "${response}" | grep -q '"done":true\|"status"'; then
    echo "[preload] ✅ Hot: ${model}"
  else
    echo "[preload] ⚠️  Warning: unexpected response for ${model} — may not be loaded"
    echo "${response}" | head -3
  fi
}

wait_for_ollama

# Step 1: evict non-Platonic models first to free memory
echo "[preload] Evicting non-Platonic models..."
for model in "${EVICT_MODELS[@]}"; do
  evict_model "${model}"
done
sleep 2

# Step 2: load Platonic stack with correct context windows
echo "[preload] Loading Platonic 3-model stack into unified memory..."
for entry in "${MODELS[@]}"; do
  model="${entry%%|*}"
  num_ctx="${entry##*|}"
  load_model "${model}" "${num_ctx}"
done

echo "[preload] All 3 Platonic stack models loaded and hot. Memory:"
curl -s "${OLLAMA_URL}/api/ps" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    for m in d.get('models', []):
        size_gb = m.get('size', 0) / 1e9
        ctx = m.get('context_length', '?')
        print(f'  {m[\"name\"]:<35} {size_gb:>5.1f} GB  ctx:{ctx}')
except Exception as e:
    print(f'  (could not parse ps response: {e})')
"
