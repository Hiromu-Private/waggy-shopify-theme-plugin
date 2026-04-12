# Shopify Theme Dev Plugin

Shopifyテーマ開発のための Claude Code プラグイン。テーマ分析からセクション設計・実装・自動検証までの全ワークフローを提供する。

公式 [shopify-ai-toolkit](https://github.com/Shopify/shopify-ai-toolkit)（API/ドキュメント検索）と補完関係にあり、「手を動かすテーマ開発」に特化している。

## インストール

Claude Code のチャットで以下を実行:

```
/plugin marketplace add waggy/shopify-theme-plugin
/plugin install shopify-theme-dev@waggy-shopify-theme-plugin
```

### 前提条件

| 依存 | 用途 | 必須 |
|------|------|------|
| Python 3 | Schema バリデーション | ✅ |
| jq | Hook の JSON 解析 | ✅ |
| [shopify-ai-toolkit](https://github.com/Shopify/shopify-ai-toolkit) | Liquid構文バリデーション (validate.mjs) | 推奨 |
| Playwright MCP | ブラウザ検証 | 推奨 |

---

## ワークフロー

```
┌─────────────────────────────┐
│  /shopify-theme-analyzer     │  テーマ構造を自動分析
│  → theme-profile.md          │  → 検証config自動生成
│  → shopify-verify.config.json│
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  /shopify-section-planner    │  セクション設計書を作成
│  → c-*-spec.md               │  （コード生成はしない）
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  /shopify-dev                │  設計書に基づき実装
│  （内部で schema-validator    │  ガードレール付き
│    を自動呼び出し）           │
└──────────────┬──────────────┘
               │ Write/Edit が発火
               ▼
┌─────────────────────────────┐
│  🔄 自動検証（Hook + Agent） │  ターン終了時に自動起動
│  Liquid検証 → Playwright     │  エラー自動修正（最大2回）
│  → 構造化レポート             │
└─────────────────────────────┘
```

### 各スキルの役割

| スキル | トリガー | 入力 | 出力 |
|--------|---------|------|------|
| **shopify-theme-analyzer** | `テーマを分析して` / `theme analyze` | テーマソースコード | `document/theme-profile.md` + `.claude/shopify-verify.config.json` |
| **shopify-section-planner** | `セクションを設計して` / `section plan` | 要件テキスト or Figma URL | `document/c-*-spec.md` |
| **shopify-dev** | `セクションを実装して` / `shopify-dev` | 設計書 or 直接指示 | `.liquid`, `.css`, `.js` ファイル |
| **shopify-schema-validator** | shopify-dev から自動呼び出し | `.liquid` ファイル | コンソールエラーレポート |

### 自動検証の仕組み

3つの Hook と 1つの Agent が連携して、テーマファイル編集後の検証を自動化する:

1. **shopify-verify-record.sh** (PostToolUse) — Write/Edit のたびに、編集がShopifyテーマファイルかを判定し記録
2. **shopify-verify-trigger.sh** (Stop) — ターン終了時に編集記録を確認。あれば停止をブロックし verifier agent の起動を指示
3. **shopify-verifier agent** — Liquid/Schema バリデーション → Playwright でプレビュー検証 → エラー自動修正 → 構造化レポート

**バイパス**: ユーザーが `確認不要` / `--no-verify` / `skip-verify` と入力すれば検証をスキップできる。

---

## プロジェクトセットアップ

新しいShopifyテーマプロジェクトを始めるとき:

```
1. /shopify-theme-analyzer を実行
   → document/theme-profile.md が生成される
   → .claude/shopify-verify.config.json が生成される

2. shopify theme dev でプレビューURLを取得

3. .claude/shopify-verify.config.json の preview_url を設定
```

### shopify-verify.config.json

各プロジェクトの `.claude/` に配置するストア固有の設定ファイル:

```json
{
  "preview_url": "https://xxx.shopifypreview.com",
  "max_verify_cycles": 2,
  "max_urls_per_run": 5,
  "viewports": [
    { "name": "mobile", "width": 375 },
    { "name": "tablet", "width": 768 },
    { "name": "desktop", "width": 1280 }
  ],
  "forbidden_files": ["assets/style.css", "assets/theme.js"],
  "shopify_paths": [
    "sections/*.liquid", "snippets/*.liquid", "blocks/*.liquid",
    "templates/*.json", "layout/*.liquid", "assets/*.css", "assets/*.js"
  ],
  "template_url_mappings": {
    "page.about.json": "/pages/about"
  },
  "noise_baselines": [
    { "pattern": "visumo.jp/MediaManagement", "reason": "3rd party media CMS" }
  ],
  "universal_noise": true
}
```

| フィールド | 説明 |
|-----------|------|
| `preview_url` | `shopify theme dev` のプレビューURL。空なら検証スキップ |
| `forbidden_files` | 絶対に編集してはいけないファイル。analyzer が自動検出 |
| `template_url_mappings` | テンプレート→URL のストア固有マッピング |
| `noise_baselines` | ストア固有の既知ノイズ（3rd-party等）。検証��に除外 |
| `universal_noise` | Shopify共通ノイズ（Web Pixel 404等）も自動除外 |

---

## 設計思想

### なぜ4つのスキルに分離しているか

```
monolith (❌)                  modular (✅)
┌──────────────────┐          ┌─────────┐ ┌─────────┐
│ analyze           │          │ analyzer │ │ planner │
│ plan              │    →     └────┬────┘ └────┬────┘
│ implement         │               │            │
│ validate          │          ┌────┴────┐ ┌────┴─────┐
└──────────────────┘          │   dev   │ │validator │
                              └─────────┘ └──────────┘
```

**単一責任**: 各スキルが1つの明確な仕事を持つ。analyzer はテーマを読むだけ。planner は設計書を書くだけ。dev は実装するだけ。validator は検証するだけ。

**独立実行**: 既存テーマで急ぎの修正が必要なら `/shopify-dev` だけ使える。新規セクションを設計だけしたいなら `/shopify-section-planner` だけ使える。全フロー回す必要がない。

**コンテキスト効率**: 各スキルは必要な情報だけロードする。analyzer の重い分析結果は `theme-profile.md` にシリアライズされ、後続スキルはそれを読むだけ。

### Hook / Agent / Skill の責務分離

| 種類 | いつ動く | 誰が起動する | 例 |
|------|---------|-------------|-----|
| **Skill** | ユーザーが明示的に呼ぶ | ユーザー | `/shopify-dev` |
| **Hook** | ツール実行やイベントで自動 | Claude Code ランタイム | ファイル編集時に記録 |
| **Agent** | Hook がブロックして指示 | Hook → メインエージェント | 検証+自動修正 |

この3層構造により:
- ユーザーは意識せずに検証が走る（Hook が仕掛ける）
- 検証ロジックは独立した Agent に隔離される（メインのコンテキストを汚さない）
- Skill は on-demand で、ユーザーの判断で使う

### config-guard パターン

すべての Hook は起動直後に以下をチェックする:

```bash
CONFIG_FILE="$CLAUDE_PROJECT_DIR/.claude/shopify-verify.config.json"
[[ ! -f "$CONFIG_FILE" ]] && exit 0
```

この1行により:
- **非Shopifyプロジェクトでは一切発火しない** — Next.js や Python プロジェクトで誤爆しない
- **プラグインをグローバルインストールしても安全** — config がある場所だけで動く
- **新規ストアは config 追加だけで有効化** — Hook の登録変更が不要

### "c-" プレフィックス規約

新規作成するファイルにはすべて `c-` プレフィックスを付与する:

```
sections/c-feature-cards.liquid     ← カスタム
sections/featured-collection.liquid ← テーマオリジナル
```

理由:
- **テーマ更新耐性**: テーマをアップデートしても `c-*` ファイルは上書きされない
- **即座に識別**: ファイル一覧を見た瞬間にカスタムファイルが分かる
- **安全な削除**: `c-*` ファイルはすべて削除しても元のテーマに影響しない
- **名前空間分離**: テーマの CSS クラスやセクション type と衝突しない

### テーマ非依存設計

このプラグインは特定のテーマに依存しない。Dawn でも Impulse でも Prestige でも動く:

```
theme-profile.md     = テーマの「設計図」（テーマごとに異なる）
config.json          = ストアの「設定」（ストアごとに異なる）
Skills/Hooks/Agent   = 共通のワークフローロジック（テーマ非依存）
```

`theme-profile.md` と `config.json` がアダプターの役割を果たし、同じスキルが異なるテーマで異なる振る舞いをする。

---

## Tips

### Liquid

#### Schema の default ルール（最重要）

これを間違えると **schema 全体がサイレントに壊れる**。エラーメッセージは出ない。

| Setting type | default |
|---|---|
| `text`, `textarea` | `"default": ""` は **NG**。空にしたいなら default キー自体を省略 |
| `image_picker`, `video`, `product`, `collection`, `page`, `blog`, `article` | default **不可** |
| `font_picker` | default **必須** |
| `range` | `(default - min) % step == 0` を満たすこと |
| `select`, `radio` | options の value のいずれかと一致すること |
| `checkbox` | `true` or `false` |

#### よくある Liquid エラー

```liquid
❌ {{ product.metafields.custom.my_field }}
✅ {{ product.metafields.custom.my_field.value }}

❌ {% if section.settings.image != blank %}
✅ {% if section.settings.image != blank and section.settings.image %}

❌ {{ 'c-section.css' | asset_url | stylesheet_tag }}  {# 存在しないCSS #}
✅ {# CSS ファイルが assets/ に存在することを確認してから読み込む #}
```

### CSS

#### スコーピング

セクション CSS は必ず `#shopify-section-{{ section.id }}` でスコープする:

```css
/* ❌ グローバ��汚染 */
.feature-cards { ... }

/* ✅ セクションスコープ */
#shopify-section-{{ section.id }} .c-feature-cards { ... }
```

#### CSS 重複読み込み防止

テーマによって方式が異なる。`theme-profile.md` の分析結果に従うこと:

```liquid
{%- comment -%} パターンA: Liquid変数チェック（多くのテーマ） {%- endcomment -%}
{%- unless c_feature_cards_css_loaded -%}
  {%- assign c_feature_cards_css_loaded = true -%}
  {{ 'c-feature-cards.css' | asset_url | stylesheet_tag }}
{%- endunless -%}

{%- comment -%} パターンB: stylesheet_tag のみ（Dawn系） {%- endcomment -%}
{{ 'c-feature-cards.css' | asset_url | stylesheet_tag }}
```

#### Forbidden Files

以下のファイルは **絶対に直接編集しない**:
- `assets/style.css`, `assets/base.css`, `assets/theme.css` 等のグローバルCSS
- `assets/theme.js`, `assets/bundle.js` 等のコアJS
- ベンダーライブラリ（Swiper, jQuery 等）

テーマ全体に影響す��スタイル変更が必要な場合は `assets/custom.css`（append-only）を使う。

### Playwright 検証

#### ノイズフィルタリング

Shopify のプレビュー環境では、テーマと無関係のエラーが常に出る:

| ノイズ | 原因 |
|--------|------|
| `web-pixels@*/sandbox/modern/` 404 | Shopify Web Pixel API（dev theme 限定） |
| `shop.app` CSP violation | Shop Pay iframe |
| `/shopify_pay/accelerated_checkout` 404 | Dev theme 限定 |

これらは `config.json` の `universal_noise: true` で自動除外される。ストア固有の 3rd-party ノイズ（Visumo, BTA 等）は `noise_baselines` に追加する。

#### ベースラインの更新

新しい 3rd-party アプリを追加したら `noise_baselines` を更新すること。更新しないと、新アプリのエラーが検証で毎回報告される。

### Schema 設計

#### ブロックの使い分け

```liquid
{%- comment -%} Static Block: セクション内で位置固定。1つだけ配置。 {%- endcomment -%}
{% content_for "block:heading", type: "heading" %}

{%- comment -%} Dynamic Block: マーチャントが自由に追加・並べ替え可能 {%- endcomment -%}
{% content_for "blocks" %}
```

#### 設定のグルーピング

Schema settings は `header` type でグルーピングし、マーチャントの UX を改善する:

```json
{
  "type": "header",
  "content": "レイアウト設定"
},
{
  "type": "select",
  "id": "columns",
  "label": "カラム数",
  "default": "3",
  "options": [
    { "value": "2", "label": "2カラム" },
    { "value": "3", "label": "3カラム" },
    { "value": "4", "label": "4カラム" }
  ]
}
```

---

## プラグイン構成

```
skills/
├── shopify-theme-analyzer/     テーマ構造分析 + config生成
│   ├── SKILL.md
│   └── references/
│       ├── analysis-checklist.md
│       └── theme-profile-template.md
├── shopify-section-planner/    セクション設計書作成
│   ├── SKILL.md
│   └── references/
│       ├── schema-setting-types.md
│       └── output-template.md
├── shopify-dev/                実装オーケストレーター
│   ├── SKILL.md
│   └── references/
│       ├── implementation-guide.md
│       ├── modification-guide.md
│       └── css-js-guide.md
└── shopify-schema-validator/   Schema検証
    ├── SKILL.md
    ├── scripts/validate_schema.py
    └── references/
        ├── setting-types.md
        └── section-schema-rules.md

hooks/
├── hooks.json                  Hook自動登録
├── shopify-theme-context.sh    SessionStart: テーマコンテキスト注入
├── shopify-verify-record.sh    PostToolUse: 編集記録
└── shopify-verify-trigger.sh   Stop: 検証トリガー

agents/
└── shopify-verifier.md         自律検証 + 自動修正エージェント
```

## ライセンス

MIT
