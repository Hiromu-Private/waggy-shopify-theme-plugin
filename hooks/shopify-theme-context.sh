#!/bin/bash
# SessionStart Hook: Shopifyテーマプロファイルの要約を自動注入
# docs/theme-profile.md (新パス) または document/theme-profile.md (旧パス) が
# 存在するプロジェクトでのみ出力

if [ -f "$PWD/docs/theme-profile.md" ]; then
  PROFILE="$PWD/docs/theme-profile.md"
  PROFILE_REL="docs/theme-profile.md"
elif [ -f "$PWD/document/theme-profile.md" ]; then
  PROFILE="$PWD/document/theme-profile.md"
  PROFILE_REL="document/theme-profile.md"
else
  # 非Shopifyプロジェクトでは無音
  exit 0
fi

# --- 基本情報の抽出 ---
theme_name=$(grep -m1 'テーマ名' "$PROFILE" | sed 's/.*| *\([^|]*\) *|$/\1/' | xargs)
version=$(grep -m1 'バージョン' "$PROFILE" | sed 's/.*| *\([^|]*\) *|$/\1/' | xargs)
analysis_date=$(grep -m1 '分析日' "$PROFILE" | sed 's/.*| *\([^|]*\) *|$/\1/' | xargs)

# --- 鮮度チェック (30日超で警告) ---
freshness_warning=""
if [ -n "$analysis_date" ]; then
  # BSD date (macOS) を先に試し、失敗したら GNU date (Linux) にフォールバック。
  # 両方失敗した場合は analysis_epoch が空になり鮮度チェック自体をスキップする。
  analysis_epoch=$(date -j -f "%Y-%m-%d" "$analysis_date" "+%s" 2>/dev/null \
    || date -d "$analysis_date" "+%s" 2>/dev/null)
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

# --- 新規ファイルプレフィックス (「### "c-" プレフィックス」見出しから抽出) ---
file_prefix=$(grep -m1 -E '^#{2,4} *"[^"]+" *プレフィックス' "$PROFILE" | sed 's/.*"\([^"]*\)".*/\1/')

# --- セクションCSSスコープ規約 (プロファイルに記載がある場合のみ) ---
css_scoping=""
if grep -q '#shopify-section-' "$PROFILE"; then
  css_scoping='#shopify-section-{{ section.id }}'
fi

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
Naming: ${naming}
CSS method: ${css_method}
Custom elements: ${elements}
${file_prefix:+New file prefix: ${file_prefix} (sections/${file_prefix}*.liquid, assets/${file_prefix}*.css, snippets/${file_prefix}*-*.liquid)
}${css_scoping:+CSS scoping: ${css_scoping}
}
Full details: ${PROFILE_REL}
Guided workflow: /theme-orchestrator
EOF
