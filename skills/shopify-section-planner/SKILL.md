---
name: shopify-section-planner
description: "Shopifyテーマの新規セクション設計・プランニング。テーマプロファイル（document/theme-profile.md）を参照し、既存CSS/JS/コンポーネントを流用した設計書を作成する。全テーマ対応。コード生成は行わない。使用タイミング：「〇〇なセクションを設計して」「セクションをプランニングして」「セクション設計書」「section plan」。Figmaデザインからの変換にも対応。前提：shopify-theme-analyzerでテーマ分析済みであること。"
---

# Shopify Section Planner

テーマプロファイルに基づき、新規セクションの設計書を作成する。コード生成は行わない。

## 前提条件

- `document/theme-profile.md` が存在すること（`shopify-theme-analyzer` で生成）
- 存在しない場合: 「先に `shopify-theme-analyzer` を実行してください（`/shopify-theme-analyzer`）」と案内して終了

## ワークフロー

### Phase 1: 前提確認 + 要件収集

1. `document/theme-profile.md` の存在をチェック
   - **存在する**: 読み込んでテーマ情報を把握
   - **存在しない**: 「先に shopify-theme-analyzer を実行してください」と案内して終了

2. テキスト入力 / Figma入力から要件を収集:
   - セクションの目的・用途
   - 含まれるコンテンツ要素（テキスト、画像、ボタン等）
   - 繰り返し要素の有無（blocks候補）
   - レスポンシブ要件
   - インタラクション要件（スライダー、アコーディオン等）

3. **既存コンポーネントで実現可能な機能を特定**（テーマプロファイル参照）

4. 不明点は最大2往復で質問

**Figma入力の場合:**
- Figma Dev Mode MCP からデザインデータを取得
- レイアウト構造、余白、タイポグラフィ、カラーを分析
- localhost ソースが返された場合はそのまま設計書に記載（プレースホルダー禁止）

### Phase 2: Shopify Dev Docs 検証

| ケース | アクション |
|--------|----------|
| 基本的な設定タイプ（text, range, select等） | [references/schema-setting-types.md](references/schema-setting-types.md) で十分。MCP不要 |
| `video_url`, `metaobject`, nested blocks 等 | Shopify Dev MCP `search_docs_chunks` で仕様を検証 |
| 詳細な仕様が必要な場合 | Shopify Dev MCP `fetch_full_docs` で完全なドキュメントを取得 |

### Phase 3: 設計書作成

[references/output-template.md](references/output-template.md) に従い設計書を作成。

テーマプロファイルの情報を反映:
- 既存コンポーネント流用箇所を明記
- テーマの命名規則に準拠したクラス名
- テーマのCSS読み込み方式に合わせた記述
- 重複読み込み防止パターンの選択
- "c-" プレフィックスルールの適用

### Phase 4: レビュー確認

- 設計書を提示し、修正点がないか確認
- **既存コンポーネント流用箇所**が正しいか重点確認
- OK なら `document/c-[section-name]-spec.md` に保存

## "c-" プレフィックスルール

新規作成するセクションには "c-" を付与し、テーマ元のセクションと区別する。

| 対象 | 例 |
|------|-----|
| セクションファイル名 | `sections/c-feature-cards.liquid` |
| CSSファイル名 | `assets/c-feature-cards.css` |
| JSファイル名 | `assets/c-feature-cards.js` |
| スニペットファイル名 | `snippets/c-feature-card-item.liquid` |
| Schema name | `"name": "c-特集カード"` |
| CSSクラス名 | テーマの命名規則に従い、状況に応じて判断 |

## 既存CSS/JSの保護

- グローバルCSSは変更しない
- 既存コンポーネント（カルーセル、スライダー等）は新規に同等機能を作らず必ず流用

## CSS重複読み込み防止

テーマプロファイルの分析結果に基づき適切なパターンを採用:

**パターンA: Liquid変数チェック（汎用）**

```liquid
{%- unless c_feature_cards_css_loaded -%}
  {%- assign c_feature_cards_css_loaded = true -%}
  {{ 'c-feature-cards.css' | asset_url | stylesheet_tag }}
{%- endunless -%}
```

**パターンB: テーマ既存方式に従う（Dawn等）**

```liquid
{{ 'c-feature-cards.css' | asset_url | stylesheet_tag }}
```

## Reference docs

- **Schema設定タイプ**: [references/schema-setting-types.md](references/schema-setting-types.md)
- **出力テンプレート**: [references/output-template.md](references/output-template.md)
