#!/bin/bash
# プラグインのバージョンを3ファイル一括で更新/検査する
#
# 用法:
#   scripts/bump-version.sh 0.3.0    # 3ファイルを 0.3.0 に更新
#   scripts/bump-version.sh --check  # 3ファイルの版が一致するか検査（リリース前確認）
#
# 背景: 2026-06-15 の 0.2.0 バンプが package.json しか更新せず、
# プラグインシステムが読む plugin.json / marketplace.json が 0.1.0 のまま
# 配布され続けた事故の再発防止。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FILES=(
  "$ROOT/.claude-plugin/plugin.json"
  "$ROOT/.claude-plugin/marketplace.json"
  "$ROOT/package.json"
)

current_versions() {
  local f v
  for f in "${FILES[@]}"; do
    v=$(grep -o '"version": *"[^"]*"' "$f" | head -1 | sed 's/.*"version": *"\([^"]*\)".*/\1/')
    printf '%s\t%s\n' "${v:-MISSING}" "${f#"$ROOT"/}"
  done
}

if [ "${1:-}" = "--check" ]; then
  echo "== version check =="
  current_versions
  n=$(current_versions | cut -f1 | sort -u | wc -l | tr -d ' ')
  if [ "$n" != "1" ]; then
    echo "❌ バージョン不一致。scripts/bump-version.sh X.Y.Z で揃えてください"
    exit 1
  fi
  echo "✅ 3ファイル一致"
  exit 0
fi

NEW="${1:-}"
if ! printf '%s' "$NEW" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "用法: scripts/bump-version.sh <X.Y.Z> | --check" >&2
  exit 1
fi

echo "== before =="
current_versions

for f in "${FILES[@]}"; do
  count=$(grep -c '"version": *"' "$f" || true)
  if [ "$count" != "1" ]; then
    echo "❌ ${f#"$ROOT"/} に version キーが ${count} 個あります。想定は 1 個。手動確認してください" >&2
    exit 1
  fi
  if sed --version >/dev/null 2>&1; then
    sed -i -E "s/\"version\": *\"[^\"]*\"/\"version\": \"$NEW\"/" "$f"   # GNU sed
  else
    sed -i '' -E "s/\"version\": *\"[^\"]*\"/\"version\": \"$NEW\"/" "$f" # BSD/macOS sed
  fi
done

# JSON としての妥当性を最終確認
python3 - "${FILES[@]}" <<'PY'
import json, sys
for path in sys.argv[1:]:
    json.load(open(path))
print("JSON validity: OK")
PY

echo "== after =="
current_versions
echo "✅ 完了。次: git commit → push → /plugin marketplace update（docs/release-checklist.md 参照）"
