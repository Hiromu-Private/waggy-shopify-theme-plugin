#!/bin/bash
# PostToolUse Hook: Record Shopify file edits to a per-session scratch file.
# stdin: { tool_name, tool_input: {file_path, ...}, tool_response, session_id, ... }
#
# User-level hook. Only activates when $CLAUDE_PROJECT_DIR contains
# .claude/shopify-verify.config.json (Shopify theme project).

set -euo pipefail

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Skip if no file_path
[[ -z "$FILE_PATH" ]] && exit 0

# Resolve to absolute path if relative
[[ "$FILE_PATH" != /* ]] && FILE_PATH="$(pwd)/$FILE_PATH"

# ─── Config guard ─────────────────────────────────────────
# Only activate for Shopify theme projects with a verify config.
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
CONFIG_FILE="$PROJECT_DIR/.claude/shopify-verify.config.json"
[[ ! -f "$CONFIG_FILE" ]] && exit 0

# Guard: file must be inside this project (multi-project safety)
[[ "$FILE_PATH" != "$PROJECT_DIR"/* ]] && exit 0

# Strip project prefix to get relative path
REL_PATH="${FILE_PATH#$PROJECT_DIR/}"

# ─── Dynamic path matching from config ────────────────────
# Read shopify_paths from config and match against relative path.
MATCH=0
while IFS= read -r pattern; do
  [[ -z "$pattern" ]] && continue
  # shellcheck disable=SC2053
  [[ "$REL_PATH" == $pattern ]] && MATCH=1 && break
done < <(jq -r '.shopify_paths[]' "$CONFIG_FILE" 2>/dev/null)

[[ "$MATCH" -eq 0 ]] && exit 0

# ─── Record the edit ──────────────────────────────────────
SCRATCH="/tmp/shopify-verify-${SESSION_ID}.txt"
touch "$SCRATCH"
# Deduplicate: only append if not already present
grep -qxF "$REL_PATH" "$SCRATCH" || echo "$REL_PATH" >> "$SCRATCH"

exit 0
