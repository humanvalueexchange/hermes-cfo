#!/usr/bin/env bash

set -euo pipefail

REPO_DIR="${HOME}/hermes-cfo"
ROOT="/hve-library"
RUNTIME_DIR="${HOME}/.hve-knowledge"
VENV_DIR="${RUNTIME_DIR}/venv"
VAULT_DIR="${ROOT}/vault/hve-knowledge-vault"

echo "== Creating knowledge-layer directories =="
sudo install -d -m 755 -o hans -g hans \
  "${ROOT}" \
  "${ROOT}/intake" \
  "${ROOT}/intake/inbox" \
  "${ROOT}/intake/test-batch" \
  "${ROOT}/raw" \
  "${ROOT}/raw/pdfs" \
  "${ROOT}/processed" \
  "${ROOT}/processed/text" \
  "${ROOT}/processed/chunks" \
  "${ROOT}/index" \
  "${ROOT}/index/lancedb" \
  "${ROOT}/state" \
  "${ROOT}/state/manifests" \
  "${ROOT}/state/logs" \
  "${ROOT}/state/failed" \
  "${ROOT}/state/model-cache" \
  "${ROOT}/vault" \
  "${VAULT_DIR}"
install -d -m 755 "${RUNTIME_DIR}"

echo "== Scaffolding Obsidian vault =="
install -d -m 755 \
  "${VAULT_DIR}/Attachments" \
  "${VAULT_DIR}/Daily" \
  "${VAULT_DIR}/Inbox" \
  "${VAULT_DIR}/Maps" \
  "${VAULT_DIR}/Sources" \
  "${VAULT_DIR}/Templates"

if [[ ! -f "${VAULT_DIR}/Home.md" ]]; then
  cat > "${VAULT_DIR}/Home.md" <<'EOF'
# HVE Knowledge Vault

## Entry points
- [[Inbox/Capture]]
- [[Maps/Knowledge Map]]
- [[Templates/Literature Note Template]]

## Operating model
- PDFs land in `/hve-library/intake/test-batch/`
- Extracted text lands in `/hve-library/processed/text/`
- Chunking and LanceDB index builds run in the overnight window
EOF
fi

if [[ ! -f "${VAULT_DIR}/Inbox/Capture.md" ]]; then
  cat > "${VAULT_DIR}/Inbox/Capture.md" <<'EOF'
# Capture

Drop quick notes here before they are organized into permanent knowledge notes.
EOF
fi

if [[ ! -f "${VAULT_DIR}/Maps/Knowledge Map.md" ]]; then
  cat > "${VAULT_DIR}/Maps/Knowledge Map.md" <<'EOF'
# Knowledge Map

## Current domains
- Bitcoin
- Sovereignty
- Treasury
- Health
- Family
EOF
fi

if [[ ! -f "${VAULT_DIR}/Templates/Literature Note Template.md" ]]; then
  cat > "${VAULT_DIR}/Templates/Literature Note Template.md" <<'EOF'
# Literature Note

## Source
- Title:
- Author:
- Location:

## Key ideas
- 

## Relevance to HVE
- 
EOF
fi

echo "== Installing Phase 1 packages =="
sudo apt-get update -qq
sudo apt-get install -y poppler-utils python3-venv

echo "== Installing knowledge-layer Python runtime =="
if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  uv venv "${VENV_DIR}" --python /usr/bin/python3
fi
uv pip install --python "${VENV_DIR}/bin/python" \
  lancedb pyarrow numpy transformers torch sentencepiece safetensors

echo "== Installing native Obsidian desktop =="
bash "${REPO_DIR}/scripts/bootstrap-obsidian.sh"

echo "== Installing knowledge-layer systemd assets =="
sudo install -m 644 "${REPO_DIR}/dotfiles/hve-knowledge.slice" /etc/systemd/system/hve-knowledge.slice
sudo install -m 644 "${REPO_DIR}/dotfiles/hve-library-manifest.service" /etc/systemd/system/hve-library-manifest.service
sudo install -m 644 "${REPO_DIR}/dotfiles/hve-library-manifest.timer" /etc/systemd/system/hve-library-manifest.timer
sudo install -m 644 "${REPO_DIR}/dotfiles/hve-pdf-extract.service" /etc/systemd/system/hve-pdf-extract.service
sudo install -m 644 "${REPO_DIR}/dotfiles/hve-pdf-extract.timer" /etc/systemd/system/hve-pdf-extract.timer
sudo install -m 644 "${REPO_DIR}/dotfiles/hve-library-chunk.service" /etc/systemd/system/hve-library-chunk.service
sudo install -m 644 "${REPO_DIR}/dotfiles/hve-library-chunk.timer" /etc/systemd/system/hve-library-chunk.timer
sudo install -m 644 "${REPO_DIR}/dotfiles/hve-library-index.service" /etc/systemd/system/hve-library-index.service
sudo install -m 644 "${REPO_DIR}/dotfiles/hve-library-index.timer" /etc/systemd/system/hve-library-index.timer
sudo systemctl daemon-reload
sudo systemctl enable hve-library-manifest.timer hve-pdf-extract.timer hve-library-chunk.timer hve-library-index.timer
sudo systemctl restart hve-library-manifest.timer hve-pdf-extract.timer hve-library-chunk.timer hve-library-index.timer

cat <<'EOF'
Knowledge layer Phase 1 bootstrapped.

Sample PDF drop location:
  /hve-library/intake/test-batch/
Obsidian launcher:
  ~/.local/bin/obsidian-hve
EOF

bash "${REPO_DIR}/scripts/validate-knowledge-layer.sh"
