#!/bin/bash
# SessionStart Hook: Shopifyテーマプロファイルの要約を自動注入
# document/theme-profile.md が存在するプロジェクトでのみ出力

PROFILE="$PWD/document/theme-profile.md"

# 非Shopifyプロジェクトでは無音
if [ ! -f "$PROFILE" ]; then
  exit 0
fi

# --- 基本情報の抽出 ---
theme_name=$(grep -m1 'テーマ名' "$PROFILE" | sed 's/.*| *\([^|]*\) *|$/\1/' | xargs)
version=$(grep -m1 'バージョン' "$PROFILE" | sed 's/.*| *\([^|]*\) *|$/\1/' | xargs)
analysis_date=$(grep -m1 '分析日' "$PROFILE" | sed 's/.*| *\([^|]*\) *|$/\1/' | xargs)

# --- 鮮度チェック (30日超で警告) ---
freshness_warning=""
if [ -n "$analysis_date" ]; then
  analysis_epoch=$(date -j -f "%Y-%m-%d" "$analysis_date" "+%s" 2>/dev/null)
  current_epoch=$(date "+%s")
  if [ -n "$analysis_epoch" ]; then
    days_old=$(( (current_epoch - analysis_epoch) / 86400 ))
    if [ "$days_old" -gt 30 ]; then
      freshness_warning="WARNING: Profile is ${days_old} days old. Consider re-running /shopify-theme-analyzer"
    fi
  fi
fi

# --- 変更禁止ファイル ---
forbidden=$(awk '/^### 変更禁止ファイル/{found=1; next} /^###/{if(found) exit} found && /^- /' "$PROFILE" \
  | sed 's/^- `\([^`]*\)`.*/\1/' | tr '\n' ',' | sed 's/,$//;s/,/, /g')

# --- ブレークポイント ---
breakpoints=$(awk '/^### ブレークポイント/{found=1; next} found && /^\| *[a-z]/{
  gsub(/^ *\| */, ""); gsub(/ *\| *$/, "");
  split($0, cols, / *\| */);
  printf "%s(%s)", cols[1], cols[2];
  sep=1
} found && sep && /^$/{exit} found && sep{sep_print=1}' "$PROFILE" \
  | sed 's/)\([a-z]\)/) \/ \1/g')

# --- 命名規則 ---
naming=$(awk '/^### 命名規則/{found=1; next} found && /[^ ]/{print; exit}' "$PROFILE" | xargs)

# --- CSSプレフィックス ---
css_prefix=$(grep 'CSSプレフィックス' "$PROFILE" | head -1 | sed 's/CSSプレフィックス: *//')

# --- CSS読み込み方式 ---
css_method=$(grep '^方式:' "$PROFILE" | head -1 | sed 's/方式: *//')

# --- 主要カスタム要素 (要素名のみ抽出) ---
elements=$(awk '/^### 再利用可能コンポーネント/{found=1; next} /^###/{if(found) exit} found' "$PROFILE" \
  | grep '|.*`' | grep -v 'コンポーネント\|---' \
  | sed -n 's/.*`\([a-z][a-z0-9_-]*\)`.*/\1/p' | head -15 | tr '\n' ',' | sed 's/,$//;s/,/, /g')

# --- 出力 ---
cat <<EOF
[Shopify Theme Context] ${theme_name} v${version} (analyzed: ${analysis_date})
${freshness_warning:+${freshness_warning}
}
Forbidden files: ${forbidden}
Breakpoints: ${breakpoints}
CSS prefix: ${css_prefix}
Naming: ${naming}
CSS method: ${css_method}
Custom elements: ${elements}
New file prefix: c- (sections/c-*.liquid, assets/c-*.css, snippets/c-*-*.liquid)
CSS scoping: #shopify-section-{{ section.id }}

Full details: document/theme-profile.md
Guided workflow: /shopify-dev
EOF
