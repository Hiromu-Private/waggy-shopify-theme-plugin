#!/bin/bash
# Stop Hook: Trigger shopify-verifier sub-agent based on configured verify_mode.
# stdin: { session_id, transcript_path, stop_hook_active, last_assistant_message, ... }
#
# User-level hook. Only activates when $CLAUDE_PROJECT_DIR contains
# .claude/shopify-verify.config.json (Shopify theme project).
#
# verify_mode (config):
#   - "manual" : never auto-trigger. Only fires when user includes force keyword.
#   - "smart"  : (default) trigger only on "big" changes — new .liquid file
#                creation or diff > 50 lines across recorded theme files.
#   - "auto"   : legacy behavior. Trigger on any recorded theme edit.
#
# Bypass keywords (in last user message):
#   skip:  skip-verify | --no-verify | 確認不要 | 検証スキップ
#   force: verify-please | verify-now | 検証して
#
# Decision order (first hit wins): no config / stop_hook_active / no recorded
# edits → allow; skip keyword → allow; force keyword → flag only; empty
# preview_url → allow (verifier can't run without a URL, even forced);
# manual Playwright tool_use on the preview host this turn → allow;
# then mode gating (manual/smart/auto) → block with reason.

set -euo pipefail

# jq is required for all parsing below; without it, degrade to a silent pass.
command -v jq >/dev/null 2>&1 || exit 0

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
# No scratch file or empty → no shopify edits recorded.
[[ ! -s "$SCRATCH" ]] && exit 0

# ─── Read config values + last user message ───────────────
VERIFY_MODE=$(jq -r '.verify_mode // "smart"' "$CONFIG_FILE" 2>/dev/null)
SMART_DIFF_THRESHOLD=$(jq -r '.smart_diff_threshold // 50' "$CONFIG_FILE" 2>/dev/null)
MAX_VERIFY_CYCLES=$(jq -r '.max_verify_cycles // 2' "$CONFIG_FILE" 2>/dev/null)
MAX_VERIFY_CYCLES=${MAX_VERIFY_CYCLES:-2}
PREVIEW_URL=$(jq -r '.preview_url // empty' "$CONFIG_FILE" 2>/dev/null)

LAST_USER_MSG=""
if [[ -n "$TRANSCRIPT_PATH" && -f "$TRANSCRIPT_PATH" ]]; then
  # Transcript rows with type=="user" also include tool_result turns, meta rows
  # and sub-agent (sidechain) prompts. Keep only real user input: flatten
  # text-part arrays (tool_result parts drop out), discard empty results, and
  # collapse newlines so one message = one line for tail -1.
  LAST_USER_MSG=$(jq -r '
    select(.type == "user")
    | select(.isMeta != true and .isSidechain != true)
    | .message.content
    | if type == "string" then .
      elif type == "array" then ([.[] | select(.type? == "text") | .text] | join(" "))
      else empty end
    | select(. != "")
    | gsub("[\n\r]"; " ")
  ' "$TRANSCRIPT_PATH" 2>/dev/null | tail -1 || true)
fi

# ─── Case 3a: Negative bypass (skip keyword) ──────────────
if printf '%s\n' "$LAST_USER_MSG" | grep -qiE '(skip-verify|--no-verify|確認不要|検証スキップ)'; then
  rm -f "$SCRATCH"
  exit 0
fi

# ─── Case 3b: Positive bypass (force keyword) ─────────────
FORCE_VERIFY=0
if printf '%s\n' "$LAST_USER_MSG" | grep -qiE '(verify-please|verify-now|検証して)'; then
  FORCE_VERIFY=1
fi

# ─── Case 3c: No preview URL configured ───────────────────
# The verifier cannot run without a URL, even when forced → allow stop.
# Checked before the smart heuristics so projects without a preview_url
# never pay the git status/diff cost on every turn.
if [[ -z "$PREVIEW_URL" ]]; then
  rm -f "$SCRATCH"
  exit 0
fi

# ─── Case 4: Manual Playwright already used ───────────────
# Main agent already ran Playwright manually this turn → don't double-verify.
# Strict match: require the tool_use JSON structure (not a mere text mention)
# plus the preview host in the same window, so Playwright usage unrelated to
# the theme does not suppress verification.
if [[ "$FORCE_VERIFY" -eq 0 && -n "$TRANSCRIPT_PATH" && -f "$TRANSCRIPT_PATH" ]]; then
  RECENT_WINDOW=$(tail -300 "$TRANSCRIPT_PATH" 2>/dev/null || true)
  NAV_TOOL_USE_RE='"name"[[:space:]]*:[[:space:]]*"mcp__playwright__browser_navigate"'
  if [[ "$RECENT_WINDOW" =~ $NAV_TOOL_USE_RE ]]; then
    # Host part of preview_url (scheme, then port/path/query stripped).
    PREVIEW_HOST="${PREVIEW_URL#*://}"
    PREVIEW_HOST="${PREVIEW_HOST%%[/:?]*}"
    # Empty host (malformed URL) → structure-only detection, as before.
    if [[ -z "$PREVIEW_HOST" || "$RECENT_WINDOW" == *"$PREVIEW_HOST"* ]]; then
      rm -f "$SCRATCH"
      exit 0
    fi
  fi
fi

# ─── Mode-based gating (skipped if force keyword present) ─
if [[ "$FORCE_VERIFY" -eq 0 ]]; then
  case "$VERIFY_MODE" in
    manual)
      # Never trigger automatically. Drop scratch and allow stop.
      rm -f "$SCRATCH"
      exit 0
      ;;

    smart)
      # Trigger only on "big" changes.
      # Big = new .liquid file created (untracked or A status), OR total diff > threshold.
      BIG_CHANGE=0
      REASONS=()

      # Heuristic 1: new .liquid file creation
      # Check each recorded file: if it's untracked or git-status shows "A" or "??", it's a new file.
      while IFS= read -r rel; do
        [[ -z "$rel" ]] && continue
        # Only check .liquid files
        case "$rel" in *.liquid)
          status=$(cd "$PROJECT_DIR" && git status --porcelain -- "$rel" 2>/dev/null | head -c 2 || true)
          if [[ "$status" == "??" || "$status" == "A " || "$status" == "AM" ]]; then
            BIG_CHANGE=1
            REASONS+=("new file: $rel")
          fi
          ;;
        esac
      done < "$SCRATCH"

      # Heuristic 2: total diff lines (added + deleted) across recorded files > threshold
      if [[ "$BIG_CHANGE" -eq 0 ]]; then
        TOTAL_LINES=0
        while IFS= read -r rel; do
          [[ -z "$rel" ]] && continue
          # numstat: added<TAB>deleted<TAB>file. Skip binary (-).
          numstat=$(cd "$PROJECT_DIR" && git diff HEAD --numstat -- "$rel" 2>/dev/null || true)
          added=$(echo "$numstat" | awk '{print $1}')
          deleted=$(echo "$numstat" | awk '{print $2}')
          [[ "$added" == "-" || -z "$added" ]] && added=0
          [[ "$deleted" == "-" || -z "$deleted" ]] && deleted=0
          TOTAL_LINES=$((TOTAL_LINES + added + deleted))

          # Also include untracked files (not in HEAD): count line count as added.
          if (cd "$PROJECT_DIR" && git ls-files --error-unmatch -- "$rel" >/dev/null 2>&1); then
            :  # tracked, already counted via diff
          else
            if [[ -f "$PROJECT_DIR/$rel" ]]; then
              ucount=$(wc -l < "$PROJECT_DIR/$rel" 2>/dev/null || echo 0)
              TOTAL_LINES=$((TOTAL_LINES + ucount))
            fi
          fi
        done < "$SCRATCH"

        if [[ "$TOTAL_LINES" -gt "$SMART_DIFF_THRESHOLD" ]]; then
          BIG_CHANGE=1
          REASONS+=("diff size: ${TOTAL_LINES} lines (threshold: ${SMART_DIFF_THRESHOLD})")
        fi
      fi

      if [[ "$BIG_CHANGE" -eq 0 ]]; then
        # Small change in smart mode → skip silently.
        rm -f "$SCRATCH"
        exit 0
      fi
      # Safe array expansion for bash 3.2 + set -u.
      if [[ "${#REASONS[@]}" -gt 0 ]]; then
        SMART_REASONS=$(printf '  - %s\n' "${REASONS[@]}")
      else
        SMART_REASONS="  - (heuristic matched but no reason recorded)"
      fi
      ;;

    auto)
      # Always trigger when scratch has entries.
      SMART_REASONS=""
      ;;

    *)
      # Unknown mode → fall back to auto for safety.
      SMART_REASONS=""
      ;;
  esac
fi

# ─── Block stop and request verification ──────────────────
# Build a markdown file list for the reason message.
FILES_LIST=$(awk '{printf "  - %s\n", $0}' "$SCRATCH")

# Build trigger context line.
if [[ "$FORCE_VERIFY" -eq 1 ]]; then
  TRIGGER_NOTE="Trigger: force keyword in user message (mode bypassed)."
elif [[ "$VERIFY_MODE" == "smart" ]]; then
  TRIGGER_NOTE="Trigger: smart mode detected significant change:
${SMART_REASONS}"
else
  TRIGGER_NOTE="Trigger: verify_mode = ${VERIFY_MODE}."
fi

REASON=$(cat <<EOF
Shopify theme files were edited in this turn. You MUST run the shopify-theme-dev:shopify-verifier sub-agent before completing.

${TRIGGER_NOTE}

Edited files:
$FILES_LIST

Preview URL: $PREVIEW_URL

Call: Agent(subagent_type=shopify-theme-dev:shopify-verifier) with a prompt that includes:
1. The file list above
2. The preview URL above
3. Instructions: "Verify these edits via Playwright Chromium. Auto-fix any errors detected (max ${MAX_VERIFY_CYCLES} cycles). Return a structured report."

After the verifier completes its work, try to stop again — the hook will allow it (stop_hook_active will be true).

To opt out of automatic verification in the future, set "verify_mode": "manual" in .claude/shopify-verify.config.json. To skip just this turn, include "skip-verify" / "確認不要" in your next message.
EOF
)

# Output JSON to block the stop and inject the reason as context.
jq -n --arg reason "$REASON" '{
  decision: "block",
  reason: $reason
}'

exit 0
