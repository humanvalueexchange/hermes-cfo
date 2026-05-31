#!/usr/bin/env bash
# validate-hermes-mcp.sh
# Validates the HVE Hermes MCP Server is correctly installed and responding.

set -euo pipefail

PORT="${HVE_MCP_PORT:-8765}"
ENV_FILE="${HOME}/.hermes-mcp.env"
PASS=0
FAIL=0

check() {
    local label="$1"
    local result="$2"
    if [ "${result}" = "ok" ]; then
        echo "PASS ${label}"
        ((PASS++)) || true
    else
        echo "FAIL ${label} — ${result}"
        ((FAIL++)) || true
    fi
}

# systemd service
state=$(systemctl --user is-active hermes-mcp 2>/dev/null || echo "inactive")
check "hermes-mcp service active" "$([ "$state" = "active" ] && echo ok || echo "$state")"

# env file + API key
check "env file exists" "$([ -f "${ENV_FILE}" ] && echo ok || echo "missing ${ENV_FILE}")"
check "API key set" "$(grep -q 'HVE_MCP_API_KEY=.' "${ENV_FILE}" 2>/dev/null && echo ok || echo "HVE_MCP_API_KEY empty or missing")"

# agent card
card=$(curl -sf "http://127.0.0.1:${PORT}/.well-known/agent.json" 2>/dev/null || echo "")
check "agent card reachable" "$([ -n "${card}" ] && echo ok || echo "http://127.0.0.1:${PORT}/.well-known/agent.json unreachable")"
check "agent card has name" "$(echo "${card}" | grep -q 'HVE Hermes' && echo ok || echo "name field missing")"

# MCP endpoint — streamable-http requires session init before tools/list
API_KEY=$(grep HVE_MCP_API_KEY "${ENV_FILE}" 2>/dev/null | cut -d= -f2- || echo "")

# Step 1: initialize — get session ID from response header
init_headers=$(curl -si -X POST "http://127.0.0.1:${PORT}/mcp" \
    -H "Content-Type: application/json" \
    -H "X-HVE-API-Key: ${API_KEY}" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"validate","version":"1.0"}}}' \
    2>/dev/null || echo "")
SESSION_ID=$(echo "${init_headers}" | grep -i "mcp-session-id:" | head -1 | awk '{print $2}' | tr -d '\r')
check "MCP endpoint responding" "$([ -n "${SESSION_ID}" ] && echo ok || echo "POST /mcp returned nothing")"

# Step 2: tools/list with session ID
mcp_resp=$(curl -sf -X POST "http://127.0.0.1:${PORT}/mcp" \
    -H "Content-Type: application/json" \
    -H "X-HVE-API-Key: ${API_KEY}" \
    -H "Accept: application/json, text/event-stream" \
    -H "mcp-session-id: ${SESSION_ID}" \
    -d '{"jsonrpc":"2.0","method":"tools/list","id":2}' 2>/dev/null || echo "")
check "MCP tools list returned" "$(echo "${mcp_resp}" | grep -q 'get_btc_forecast' && echo ok || echo "tools not found in response")"

# tasks file
TASKS_FILE="${HOME}/hermes-cfo/logs/tasks/tasks.json"
check "tasks file exists" "$([ -f "${TASKS_FILE}" ] && echo ok || echo "missing ${TASKS_FILE}")"

echo ""
if [ "${FAIL}" -eq 0 ]; then
    echo "PASS all ${PASS} checks passed — Hermes MCP Server is healthy."
else
    echo "RESULT ${PASS} passed, ${FAIL} failed."
    exit 1
fi
