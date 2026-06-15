---
name: shopify-ds-component-search
description: "Shopify テーマで brand 系 c-* セクション・スニペット・CSS を実装する前に、既存資産（流用可能な c-* snippet・BEM ブロック・Figma Components）を必ず列挙する事前確認スキル。Figma + DS を持つテーマ（ALLUP-SHOP 等）で重複実装を防ぐ。自動発火タイミング: 「c-* セクション作成」「{% render 'c-...' %} を書く」「assets/c-*.css を新規作成」「design_version=brand のセクション編集」「pill ボタン/eyebrow/カード/ヘッダー等の brand UI 追加」「Figma Components 由来のコンポーネント実装」「ALLUP DS / ブランドデザイン / brand mode 実装」を検知したら、コードを書く前に必ず実行。明示的呼出: /shopify-ds-component-search"
---

# Shopify DS Component Search — 既存資産事前確認スキル

Figma 正本 + デザインシステムを持つ Shopify テーマ（ALLUP-SHOP 等）で、brand 系 UI 実装前に**既存資産を必ず洗い出す**ためのスキル。

## このスキルが解決する問題

過去の実際の事故（2026-06-15, ALLUP-SHOP）:
- `collection-list.liquid` に "view-all" pill ボタンを実装する際、既に `c-news` / `c-special` / `c-featured-collection` の3つで**完全同一の pill ボタン**が実装されていたが、それを確認せずに4つ目の独自 BEM (`.collection-list__view-all-btn`) を raw value (`#fff` / `14px` / `6px`) で新規実装した。
- 結果: 4箇所で同じデザインシステム概念が4つの異なる実装に分裂、DS トークン未使用、後から大規模リファクタが必要になった。

このスキルはこの種の事故を**コードを書く前**に防ぐ。

## 起動時のアクション

ユーザーが「brand UI を実装したい」と意図したタイミング（明示呼出 or 自動発火）で、以下を**順番に**実行する:

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

ユーザープロジェクトに該当する Figma fileKey が memory / reference にあれば取得する。
ALLUP-SHOP の場合: `mcp__figma__get_metadata` で fileKey `aeeoz4ciQYve6jW8ByGYy0` / nodeId `2021:2` を読み、各コンポーネント名と node-id を一覧化。

### 4. 早見表として出力

以下フォーマットでユーザーに提示:

```markdown
## 流用可能な c-* 資産（プロジェクト: ALLUP-SHOP）

| カテゴリ | snippet | CSS class | Figma node | 用途 |
|---|---|---|---|---|
| ボタン | `c-view-all` | `.c-view-all` | (c-button 2021:10) | 全 brand section の「すべて見る」pill |
| カード | `c-collection-card` | `.c-collection-card` | 2056:29 | コレクション一覧の各カード |
| カード | `c-product-card` | `.c-product-card` | 2051:68 | 商品カード |
| ニュース | `c-news-item` | `.c-news-item` | 2057:37 | ニュース行 |
| ... | ... | ... | ... | ... |

## DS トークン（assets では `var(--*)` で参照）

主要トークンは `snippets/c-css-tokens.liquid` で定義。
- 色: `--color-brand-primary`, `--color-text-onbrand`, `--color-surface-1`, ...
- スペース: `--space-1`〜`--space-7`（4px刻み）
- 半径: `--radius-sm` / `--radius-md` / `--radius-lg` / `--radius-pill`
- タイポ: `--text-body` / `--text-small` / `--text-caption` / `--text-h2` / `--text-h3`
- モーション: `--duration-fast` / `--easing-standard`
```

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

- `/shopify-theme-analyzer` — テーマ全体の分析（より重い）
- `/theme-orchestrator` — 実装本体のワークフロー
- `/shopify-section-planner` — 新規セクション設計
