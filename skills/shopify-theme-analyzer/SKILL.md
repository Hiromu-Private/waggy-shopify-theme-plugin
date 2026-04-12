---
name: shopify-theme-analyzer
description: "Shopifyテーマの構造を自動分析し、テーマプロファイル（document/theme-profile.md）を生成する。CSS命名規則、ブレークポイント、再利用可能なコンポーネント（カルーセル、スライダー等）、変更禁止ファイル一覧を抽出。使用タイミング：新しいShopifyプロジェクト開始時、「テーマを分析して」「theme analyze」。セクション設計（shopify-section-planner）の前提として実行。"
---

# Shopify Theme Analyzer

Shopifyテーマの構造を自動分析し、セクション開発に必要なテーマプロファイルを生成する。

## 目的

- テーマ固有のCSS命名規則、ブレークポイント、コンポーネント構造を把握
- 再利用可能なJS/CSSコンポーネントを特定
- 変更禁止ファイルを明確化
- 結果を `document/theme-profile.md` に保存し、`shopify-section-planner` から参照可能にする

## ワークフロー

### Step 1: テーマ識別

`config/settings_schema.json` を読み、以下を抽出:

- テーマ名
- バージョン
- 開発元
- サポートURL

### Step 2: 既存アセットスキャン

| 対象 | 分析内容 |
|------|---------|
| CSS ファイル | `assets/` のCSS一覧をスキャンし、グローバルCSS（変更禁止）とコンポーネントCSS（流用可能）を分類 |
| JS ファイル | `customElements.define` 検索でカスタム要素一覧を取得 |
| 外部ライブラリ | Swiper, Flickity, Alpine.js 等の検出 |
| イベントシステム | PubSub, CustomEvent 等のパターンを検出 |

### Step 3: テーマパターン抽出

代表セクション 2-3 個を読み、以下を把握:

| 分析項目 | 抽出内容 |
|---------|---------|
| CSS読み込み方法 | `stylesheet_tag` / `<link>` / 独自方式 |
| CSS重複防止方式 | Liquid変数チェック / タグ自体の機能 / なし |
| HTML構造規約 | ラッパークラス、カラースキーム適用方法 |
| CSS命名規則 | BEM / OOCSS / 独自（具体例付き） |
| レスポンシブ | ブレークポイント数値と使い方 |
| グリッドシステム | クラス名、カラム数指定方法 |
| パディング/余白 | インラインスタイル + Schema設定のパターン |
| 画像パターン | レスポンシブ画像の実装方法 |
| Schema傾向 | 設定のグルーピング方法、翻訳キーの使い方 |

分析項目の完全チェックリストは [references/analysis-checklist.md](references/analysis-checklist.md) を参照。

### Step 4: ユーザー確認

分析結果サマリーを以下の形式で提示し、補足・修正を受ける:

```
テーマ: [テーマ名] v[バージョン]
CSS命名規則: [BEM等]
ブレークポイント: [750px, 990px等]
再利用可能コンポーネント:
  - カルーセル: slider-component (component-slider.js/css)
  - アコーディオン: accordion (component-accordion.js/css)
  - ...
変更禁止CSS: main.css, base.css, ...
CSS読み込み方式: [stylesheet_tag / link tag / ...]
CSS重複防止方式: [パターンA / パターンB]
```

ユーザーから補足・修正を受けてから Step 5 へ進む。

### Step 5: テーマプロファイル保存

[references/theme-profile-template.md](references/theme-profile-template.md) に従い `document/theme-profile.md` を生成・保存する。

### Step 6: 検証Config自動生成

テーマ分析結果をもとに `.claude/shopify-verify.config.json` を生成する。このファイルはShopify検証Hook（ユーザーレベル）が参照する設定ファイル。

**生成ルール:**

| フィールド | 値の決定方法 |
|-----------|------------|
| `preview_url` | 空文字列（`shopify theme dev` 実行時にユーザーが手動設定） |
| `max_verify_cycles` | `2`（固定） |
| `max_urls_per_run` | `5`（固定） |
| `viewports` | `[{mobile: 375}, {tablet: 768}, {desktop: 1280}]`（固定） |
| `forbidden_files` | Step 2で特定した「変更禁止ファイル」一覧（グローバルCSS + ベンダーJS等） |
| `shopify_paths` | 固定パターン（`sections/*.liquid`, `snippets/*.liquid` 等） |
| `template_url_mappings` | `templates/` ディレクトリのJSONファイルからジェネリックルールで自動生成 |
| `noise_baselines` | 空配列（ストア固有ノイズは実行時に判明するため初期値なし） |
| `universal_noise` | `true` |

**template_url_mappings 自動生成ルール:**

`templates/` 内の `.json` ファイルを走査し、以下のルールで変換:

| テンプレートファイル | URL |
|---|---|
| `index.json` | `/` |
| `page.X.json` | `/pages/X` |
| `product.json` | （マッピングしない。ジェネリックルールで処理） |
| `collection.json` | （マッピングしない。ジェネリックルールで処理） |
| `cart.json` | `/cart` |
| `search.json` | `/search?q=test` |

**既存configがある場合:**

`.claude/shopify-verify.config.json` が既に存在する場合は**上書きしない**。ユーザーに差分を提示し、マージするか聞く。

## セクション作成ルール（全テーマ共通）

以下のルールはテーマプロファイルに含めること:

### 既存CSS/JSの保護

- `main.css`, `base.css`, `theme.css` 等の**既存グローバルCSSは変更しない**
- 新規スタイルは新規ファイル（`c-section-name.css`）に記述
- 既存のカルーセル、スライダー、アコーディオン等の**JS/CSSコンポーネントは必ず流用**し、新規に同等機能を作らない

### "c-" プレフィックス

新規作成するセクションには "c-" を付与し、テーマ元のセクションと区別する。

| 対象 | 例 |
|------|-----|
| セクションファイル名 | `sections/c-feature-cards.liquid` |
| CSSファイル名 | `assets/c-feature-cards.css` |
| JSファイル名 | `assets/c-feature-cards.js` |
| スニペットファイル名 | `snippets/c-feature-card-item.liquid` |
| Schema name | `"name": "c-特集カード"` |
| CSSクラス名 | テーマの命名規則に従い、状況に応じて判断 |

### CSS重複読み込み防止

テーマプロファイルの分析結果に基づき、以下のいずれかを採用:

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

## 有名テーマ簡易ヒント

| テーマ | 特徴 |
|--------|------|
| Dawn | BEM, stylesheet_tag, CSS custom properties, カスタム要素 |
| Prestige | OOCSS寄り, Flickity, CSS Grid |
| Impulse | BEM変形, Alpine.js, Swiper |

これらはあくまで初期参考。実際は自動分析結果を優先すること。

## Reference docs

- **分析チェックリスト**: [references/analysis-checklist.md](references/analysis-checklist.md)
- **テーマプロファイルテンプレート**: [references/theme-profile-template.md](references/theme-profile-template.md)
