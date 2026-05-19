# Shopify Theme Dev Plugin

Shopifyテーマ開発のための Claude Code プラグイン。テーマ分析からセクション設計・実装・自動検証までの全ワークフローを提供する。

公式 [shopify-ai-toolkit](https://github.com/Shopify/shopify-ai-toolkit)（API/ドキュメント検索）と補完関係にあり、「手を動かすテーマ開発」に特化している。

## インストール

Claude Code のチャットで以下を実行:

```
/plugin marketplace add Hiromu-Private/waggy-shopify-theme-plugin
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
│  /theme-orchestrator         │  設計書に基づき実装
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
| **shopify-theme-init** | `テーマ初期化` / `クリーンアップ` / `.gitignore作って` | 既存テーマ or 新規CLI生成テーマ | `.gitignore` + `.shopifyignore` + `docs/` 構造 |
| **shopify-theme-analyzer** | `テーマを分析して` / `theme analyze` | テーマソースコード | `docs/theme-profile.md` + `.claude/shopify-verify.config.json` |
| **shopify-section-planner** | `セクションを設計して` / `section plan` | 要件テキスト or Figma URL | `docs/c-*-spec.md` |
| **theme-orchestrator** | `セクションを実装して` / `theme-orchestrator` | 設計書 or 直接指示 | `.liquid`, `.css`, `.js` ファイル |
| **shopify-schema-validator** | theme-orchestrator から自動呼び出し | `.liquid` ファイル | コンソールエラーレポート |
| **shopify-theme-brand-layer** | `Brand 層を作りたい` / `brand-*.css 作って` / `Figma デザインをテーマに反映` / `テーマアップデートに耐える上書き方法` | Figma URL + 既存テーマ | `assets/brand-*.css` + `snippets/brand-icons.liquid` + `document/design-system.md` |
| **shopify-flow-builder** | `Shopify Flow 作って` / `Order paid トリガー` / `Scheduled time Flow` / `販売開始日で自動公開` / `顧客MF自動更新` / `クーポン使用検知` / `.flow ファイル` | トリガー要件 + Run Code ロジック or Get list バッチ要件 | `.flow` JSON テンプレート + 構造ドキュメント + Visual Builder 構築手順 |

**shopify-theme-brand-layer** は他 4 スキルと並列に位置する**横断スキル**。analyze 後にブランド固有の見た目を Layer 3（`brand-*` 名前空間）として実装する設計プロセスを提供する。テーマアップデートに耐える 4 レイヤー構造（Focal 標準 / 設定値 / Brand 層 / 新規セクション）と命名規則を含む。

**shopify-flow-builder** はテーマ開発ワークフローとは別軸の**Shopify Flow 自動化スキル**。2 系統のパターンを内包する:

- **Order 系（Plus 推奨）**: Order paid / Order created などのトリガーから、Run Code を中心軸とした判定ロジック・顧客メタフィールド更新・タグ付与・割引コード検知などを `.flow` JSON テンプレートで構築
- **Scheduled time 系（Basic 対応）**: 定期実行で Get list → For Each → 標準アクションのバッチ処理。販売開始日でのチャネル自動公開・在庫切れ自動アーカイブ・期間経過タグ自動剥奪などを Run Code 不使用で構築（構造ドキュメント方式）

### 自動検証の仕組み

3つの Hook と 1つの Agent が連携して、テーマファイル編集後の検証を自動化する:

1. **shopify-verify-record.sh** (PostToolUse) — Write/Edit のたびに、編集がShopifyテーマファイルかを判定し記録
2. **shopify-verify-trigger.sh** (Stop) — ターン終了時に編集記録を確認。**`verify_mode` 設定**に従って起動可否を判定し、起動が必要なら停止をブロックして verifier agent の起動を指示
3. **shopify-verifier agent** — Liquid/Schema バリデーション → Playwright でプレビュー検証 → エラー自動修正 → 構造化レポート

#### verify_mode の3モード

| モード | 挙動 |
|---|---|
| `manual` | 自動発火しない。強制実行キーワードでだけ起動 |
| `smart` (デフォルト) | 大きな変更（新規 `.liquid` 作成 or diff > `smart_diff_threshold` 行）のときだけ自動起動 |
| `auto` | 記録された Shopify 編集が1件でもあれば起動（旧挙動） |

3モードとも以下のキーワードで挙動を上書きできる:

- **強制スキップ**: `skip-verify` / `--no-verify` / `確認不要` / `検証スキップ`
- **強制実行**: `verify-please` / `verify-now` / `検証して`

設定例:

```json
{
  "verify_mode": "smart",
  "smart_diff_threshold": 50
}
```

---

## プロジェクトセットアップ

新しいShopifyテーマプロジェクトを始めるとき:

```
1. /shopify-theme-init を実行（既存ゴミ整理、.gitignore / docs/ 構造を整える）

2. /shopify-theme-analyzer を実行
   → docs/theme-profile.md が生成される
   → .claude/shopify-verify.config.json が生成される

3. shopify theme dev でプレビューURLを取得

4. .claude/shopify-verify.config.json の preview_url を設定
```

### shopify-verify.config.json

各プロジェクトの `.claude/` に配置するストア固有の設定ファイル:

```json
{
  "preview_url": "https://xxx.shopifypreview.com",
  "verify_mode": "smart",
  "smart_diff_threshold": 50,
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
| `verify_mode` | 自動検証の発火モード。`manual` / `smart` (default) / `auto` |
| `smart_diff_threshold` | `smart` モードで「大きな変更」と判定する diff 行数（add+delete 合計）。デフォルト `50` |
| `forbidden_files` | 絶対に編集してはいけないファイル。analyzer が自動検出 |
| `template_url_mappings` | テンプレート→URL のストア固有マッピング |
| `noise_baselines` | ストア固有の既知ノイズ（3rd-party等）。検証時に除外 |
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

**独立実行**: 既存テーマで急ぎの修正が必要なら `/theme-orchestrator` だけ使える。新規セクションを設計だけしたいなら `/shopify-section-planner` だけ使える。全フロー回す必要がない。

**コンテキスト効率**: 各スキルは必要な情報だけロードする。analyzer の重い分析結果は `theme-profile.md` にシリアライズされ、後続スキルはそれを読むだけ。

### Hook / Agent / Skill の責務分離

| 種類 | いつ動く | 誰が起動する | 例 |
|------|---------|-------------|-----|
| **Skill** | ユーザーが明示的に呼ぶ | ユーザー | `/theme-orchestrator` |
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
├── theme-orchestrator/         実装オーケストレーター
│   ├── SKILL.md
│   └── references/
│       ├── implementation-guide.md
│       ├── modification-guide.md
│       └── css-js-guide.md
├── shopify-schema-validator/   Schema検証
│   ├── SKILL.md
│   ├── scripts/validate_schema.py
│   └── references/
│       ├── setting-types.md
│       └── section-schema-rules.md
├── shopify-theme-brand-layer/  Brand 層（Layer 3）設計・実装プロセス
│   ├── SKILL.md
│   ├── references/
│   │   ├── layer-architecture.md      4 レイヤー構造と判断フロー
│   │   ├── naming-conventions.md      brand-* 命名規則
│   │   ├── override-strategies.md     値上書き / modifier / icon 分岐の 3 パターン
│   │   ├── verification-patterns.md   同値クラス分割 + Playwright 検証
│   │   └── pitfalls.md                6 つの実証済み落とし穴
│   └── templates/
│       ├── design-system-skeleton.md  §0〜§12 章建てテンプレート
│       └── brand-icons-template.liquid 5 アイコン case 雛形
└── shopify-flow-builder/       Shopify Flow（.flow JSON）ゼロ構築スキル
    ├── SKILL.md
    ├── references/
    │   ├── triggers.md                       主要トリガー一覧と context
    │   ├── scheduled-time-trigger.md         Scheduled time + Get list バッチパターン (Basic 対応)
    │   ├── run-code-patterns.md              Run Code 中心の判定ロジック雛形 (Plus)
    │   ├── customer-metafield-actions.md     顧客MF更新アクションのパターン
    │   ├── product-channel-publish-actions.md 商品 Publish/Tag/status アクション (Basic 対応)
    │   ├── flow-export-versioning.md         .flow JSON の Git 管理運用
    │   └── anti-patterns.md                  Condition 階層化など典型ハマり所
    ├── templates/
    │   ├── order-paid-to-customer-mf.flow         Order paid → 顧客MF
    │   ├── order-created-discount-clear-mf.flow   Order created → Discount検知
    │   └── scheduled-channel-auto-publish.md      Scheduled time → チャネル自動公開 (構造ドキュメント)
    └── evals/
        └── evals.json                       発火・出力テストケース

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
