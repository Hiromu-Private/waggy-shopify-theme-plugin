---
name: shopify-ds-component-search
description: "Shopify テーマで brand 系 c-* セクション・スニペット・CSS を実装する前に、既存資産（案件横断アセットライブラリ・流用可能な c-* snippet・BEM ブロック・Figma Components）を必ず列挙する事前確認スキル。重複実装を防ぐ。自動発火タイミング: 「c-* セクション作成」「{% render 'c-...' %} を書く」「assets/c-*.css を新規作成」「design_version=brand のセクション編集」「pill ボタン/eyebrow/カード/ヘッダー等の brand UI 追加」「Figma Components 由来のコンポーネント実装」「ブランドデザイン / brand mode 実装」「既存資産確認」を検知したら、コードを書く前に必ず実行。明示的呼出: /shopify-ds-component-search"
---

# Shopify DS Component Search — 既存資産事前確認スキル

brand 系 UI 実装前に**既存資産を必ず洗い出す**ためのスキル。検索は 2 層:

1. **中央アセットライブラリ**（案件横断。過去案件から回収済みの資産）
2. **現在のプロジェクト**（c-* snippet / BEM / Figma Components）

## このスキルが解決する問題

過去の実際の事故（2026-06-15, ALLUP-SHOP）:
- `collection-list.liquid` に "view-all" pill ボタンを実装する際、既に `c-news` / `c-special` / `c-featured-collection` の3つで**完全同一の pill ボタン**が実装されていたが、それを確認せずに4つ目の独自 BEM (`.collection-list__view-all-btn`) を raw value (`#fff` / `14px` / `6px`) で新規実装した。
- 結果: 4箇所で同じデザインシステム概念が4つの異なる実装に分裂、DS トークン未使用、後から大規模リファクタが必要になった。

このスキルはこの種の事故を**コードを書く前**に防ぐ。

## 起動時のアクション

ユーザーが「brand UI を実装したい」と意図したタイミング（明示呼出 or 自動発火）で、以下を**順番に**実行する:

### 0. 中央アセットライブラリの検索（案件横断）

```bash
ASSETS_DIR="${SHOPIFY_ASSETS_DIR:-$HOME/Developer/Waggy/shopify-assets}"
[ -f "$ASSETS_DIR/INDEX.md" ] && grep -i "<実装したいUIのキーワード>" "$ASSETS_DIR/INDEX.md"
```

- キーワードは複数試す（例: pill ボタンなら `pill` / `button` / `view-all` / `cta`）
- ヒットしたら `$ASSETS_DIR/cards/{カード名}.md` を読み、「使い方」「汎用化メモ」を確認。実コードは `files:` に列挙された `$ASSETS_DIR/snippets/` 内
- ライブラリ未設置（INDEX.md 不在）なら静かにスキップして Step 1 へ（エラーにしない）

### 1. `snippets/c-*.liquid` の列挙

```bash
ls /path/to/project/snippets/c-*.liquid
```

各 snippet について、ヘッダーコメント（`{%- comment -%}` 内）から:
- 用途（1行サマリ）
- 受け付ける引数（必須/任意）
- 使用例
を抽出する。

### 2. `assets/c-*.css` の BEM ブロック列挙

```bash
grep -hE "^\.c-[a-z][a-z0-9-]*" /path/to/project/assets/c-*.css | sort -u
```

主要な class 名を一覧化。重複している BEM パターンの有無も確認。

### 3. Figma 📦 Components ページの取得

Figma fileKey は次の優先順で解決する（ハードコード禁止）:

1. `docs/theme-profile.md` に Figma ファイルの記載があればそれを使う
2. ユーザーがこの会話で Figma URL を共有していればそこから抽出
3. どちらも無ければ**この Step はスキップ**し、出力にその旨を明記（ユーザーに URL を求めてもよい）

fileKey が解決できたら `mcp__figma__get_metadata` で Components ページ（📦 等の命名）を読み、各コンポーネント名と node-id を一覧化。

### 4. 早見表として出力

以下フォーマットでユーザーに提示:

```markdown
## 流用可能な資産（プロジェクト: {プロジェクト名}）

| 出所 | カテゴリ | snippet / カード | CSS class | Figma node | 用途 |
|---|---|---|---|---|---|
| 📦 中央ライブラリ | ボタン | `pill-view-all-button`（カード） | — | — | pill 型「すべて見る」ボタン。汎用化済み |
| 案件内 | ボタン | `c-view-all` | `.c-view-all` | (c-button {node-id}) | 全 brand section の「すべて見る」pill |
| 案件内 | カード | `c-product-card` | `.c-product-card` | {node-id} | 商品カード |
| ... | ... | ... | ... | ... | ... |

## DS トークン（assets では `var(--*)` で参照）

主要トークンの定義場所（例: `snippets/c-css-tokens.liquid`）と、実際に定義されている
トークン名（色 / スペース / 半径 / タイポ / モーション）を**そのプロジェクトの実物から**列挙する。
```

（表の内容は実在の検索結果のみ。プレースホルダのまま出力しない。中央ライブラリのヒットは `📦 中央ライブラリ` 行として区別し、カード名とカードパスを示す）

### 5. 流用可能性の判定

ユーザーが実装しようとしている UI を聞き出し、上記一覧と照合:

| ケース | 推奨アクション |
|---|---|
| 完全マッチ | `{% render 'c-{snippet}' %}` を直接使う |
| 一部マッチ | 既存 snippet を拡張（引数追加）するか、新 BEM 作成かを判断材料込みで提示 |
| マッチ無し | 新規作成。ただし**BEMブロック命名・DSトークン使用・Figma Component との対応**を明示してから書く |

## 出力の必須項目

このスキルは必ず以下を含めて返す:

1. **流用可能なスニペット**（あれば snippet 名と引数）
2. **使うべき DS トークン**（raw value 禁止の明確化）
3. **Figma の対応コンポーネント**（あれば node-id）
4. **新規作成すべきか流用すべきかの推奨**

## このスキルを必須化するワークフロー

`/theme-orchestrator` は内部でこのスキルを Phase 0（実装前必須）として呼び出す。
単発で `c-*` を編集する場合も、Edit/Write の前に明示的に呼ぶこと。

## 関連

- `/shopify-asset-harvest` — 書き込み側。実装完了時に資産を中央ライブラリへ回収する（このスキルの Step 0 が読むデータはそこで蓄積される）
- `/shopify-theme-analyzer` — テーマ全体の分析（より重い）
- `/theme-orchestrator` — 実装本体のワークフロー
- `/shopify-section-planner` — 新規セクション設計
