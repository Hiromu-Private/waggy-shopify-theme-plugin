#!/bin/bash
# Stop Hook: Trigger shopify-verifier sub-agent if recent edits exist.
# stdin: { session_id, transcript_path, stop_hook_active, last_assistant_message, ... }
#
# User-level hook. Only activates when $CLAUDE_PROJECT_DIR contains
# .claude/shopify-verify.config.json (Shopify theme project).

set -euo pipefail

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty')

# ─── Config guard ─────────────────────────────────────────
# Only activate for Shopify theme projects with a verify config.
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
CONFIG_FILE="$PROJECT_DIR/.claude/shopify-verify.config.json"
[[ ! -f "$CONFIG_FILE" ]] && exit 0

SCRATCH="/tmp/shopify-verify-${SESSION_ID}.txt"

# ─── Case 1 ───────────────────────────────────────────────
# Already blocked once this turn → cleanup and allow stop.
if [[ "$STOP_ACTIVE" == "true" ]]; then
  rm -f "$SCRATCH"
  exit 0
fi

# ─── Case 2 ───────────────────────────────────────────────
# No scratch file or empty → no shopify edits to verify.
[[ ! -s "$SCRATCH" ]] && exit 0

# ─── Case 3 ───────────────────────────────────────────────
# Bypass signal in last user message (skip-verify, --no-verify, 確認不要, etc.)
if [[ -n "$TRANSCRIPT_PATH" && -f "$TRANSCRIPT_PATH" ]]; then
  LAST_USER_MSG=$(jq -r 'select(.type=="user") | .message.content // empty' "$TRANSCRIPT_PATH" 2>/dev/null | tail -1)
  if echo "$LAST_USER_MSG" | grep -qiE '(skip-verify|--no-verify|確認不要|検証スキップ)'; then
    rm -f "$SCRATCH"
    exit 0
  fi
fi

# ─── Case 4 ───────────────────────────────────────────────
# Main agent already ran Playwright manually this turn → don't double-verify.
if [[ -n "$TRANSCRIPT_PATH" && -f "$TRANSCRIPT_PATH" ]]; then
  RECENT_PLAYWRIGHT=$(tail -40 "$TRANSCRIPT_PATH" 2>/dev/null | grep -c "mcp__playwright__browser_navigate" 2>/dev/null || true)
  RECENT_PLAYWRIGHT=${RECENT_PLAYWRIGHT:-0}
  if [[ "$RECENT_PLAYWRIGHT" -gt 0 ]]; then
    rm -f "$SCRATCH"
    exit 0
  fi
fi

# ─── Case 5 ───────────────────────────────────────────────
# Block stop and request verification via shopify-verifier sub-agent.
PREVIEW_URL=$(jq -r '.preview_url // empty' "$CONFIG_FILE" 2>/dev/null)
if [[ -z "$PREVIEW_URL" ]]; then
  # No preview URL configured → skip verification silently
  rm -f "$SCRATCH"
  exit 0
fi

# Build a markdown file list for the reason message
FILES_LIST=$(awk '{printf "  - %s\n", $0}' "$SCRATCH")

REASON=$(cat <<EOF
Shopify theme files were edited in this turn. You MUST run the shopify-verifier sub-agent before completing.

Edited files:
$FILES_LIST

Preview URL: $PREVIEW_URL

Call: Agent(subagent_type=shopify-verifier) with a prompt that includes:
1. The file list above
2. The preview URL above
3. Instructions: "Verify these edits via Playwright Chromium. Auto-fix any errors detected (max 2 cycles). Return a structured report."

After the verifier completes its work, try to stop again — the hook will allow it (stop_hook_active will be true).
EOF
)

# Output JSON to block the stop and inject the reason as context
jq -n --arg reason "$REASON" '{
  decision: "block",
  reason: $reason
}'

exit 0
