---
name: theme-orchestrator
description: "Shopifyテーマ開発の統合ワークフロー。セクション新規作成・実装、既存セクション修正、CSS/JS追加をテーマプロファイルに基づいて一貫して管理。ガードレール付き。使用タイミング：「セクションを作って」「セクションを実装して」「CSSを追加して」「テーマ実装」「theme-orchestrator」「liquidを書いて」「セクション修正」。shopify-section-implementerの後継。前提：shopify-theme-analyzerでテーマ分析済みであること。"
---

# Theme Orchestrator - Shopifyテーマ開発オーケストレーター

テーマプロファイルに基づき、Shopifyテーマのセクション作成・修正・CSS/JS追加を一貫したワークフローで実行する。

## 起動時の自動アクション

1. テーマプロファイルの存在をチェック（`docs/theme-profile.md` 優先、旧 `document/theme-profile.md` フォールバック）
   - **存在する**: 全文を読み込み、テーマ情報を把握
   - **存在しない**: 「先に `/shopify-theme-analyzer` を実行してください」と案内して終了

2. `分析日` フィールドを確認
   - 30日以上経過している場合: 「テーマプロファイルが古くなっています（X日前）。`/shopify-theme-analyzer` の再実行を推奨します」と警告
   - ただし警告のみで、作業は続行可能

3. テーマプロファイルから以下を記憶:
   - 変更禁止ファイル一覧
   - CSS命名規則・ブレークポイント
   - 再利用可能カスタム要素一覧
   - CSS読み込み方式（インライン / 外部ファイル）
   - セクション構造パターン（HTML, カラースキーム, パディング）

## ガードレール（全ワークフロー共通）

以下のルールは **すべての作業で必ず遵守** すること:

| ルール | 詳細 |
|--------|------|
| 禁止ファイル | テーマプロファイルの`変更禁止ファイル`に記載されたファイルは**絶対に編集しない** |
| 命名 | テーマの命名規則に従う。新規ファイルは `c-` プレフィックス |
| コンポーネント再利用 | 新規JS/CSS作成前に **Phase 0 (`/shopify-ds-component-search`)** で既存資産を確認。既存で実現可能なら**必ず流用**（snippet化 / 共通CSS流用） |
| DS トークン | brand系 c-* CSS に raw value (px / hex / rgb) を書かない。`var(--space-*)` `var(--text-*)` `var(--color-*)` `var(--radius-*)` を使う |
| CSS手法 | テーマプロファイルのCSS読み込みパターンに従う |
| CSSスコーピング | インラインスタイルは `#shopify-section-{{ section.id }}` でスコープ限定 |
| Schema検証 | `.liquid`ファイル作成・編集後に `/shopify-schema-validator` を実行 |
| custom.css | `custom.css` は**追記のみ**可。既存行の修正・削除は禁止 |

## Phase 0: 既存資産確認（全ワークフロー共通・必須）

⚠️ **コードを書く前に必ず実行する。スキップすると重複実装事故が起きる**（実例: ALLUP-SHOP 2026-06-15 view-all pill ボタンが4セクションで重複実装される事故が発生し、後から snippet 化リファクタが必要になった）。

### 実行内容

`/shopify-ds-component-search` を呼び出して以下を取得:

1. **流用可能なスニペット一覧** (`snippets/c-*.liquid`)
2. **既存BEMブロック一覧** (`assets/c-*.css`)
3. **Figma 📦 Components の対応関係**（プロジェクトに Figma fileKey reference があれば）
4. **使うべき DS トークン**（raw value を書かないため）

### 判定フロー

```
[既存資産あり] → 流用 (`{% render 'c-...' %}` を使う)
   ↓
[一部マッチ]   → 既存 snippet を拡張するか議論
   ↓
[マッチ無し]   → 新規作成。ただし BEM 命名・DS トークン・Figma 対応を明示してから書く
```

### 出力をユーザーへ提示

調査結果を「実装提案の冒頭」に必ず含める:

```markdown
## Phase 0 調査結果

### 流用可能な既存資産
- `c-view-all` snippet (assets/c-view-all.css) — 全 brand pill button が使う正本
- ...

### 該当する Figma Component
- c-button (node 2021:10) — Variant=primary/secondary/ghost
- ...

### 推奨アクション
既存の `c-view-all` snippet を流用する。新 BEM の追加は不要。
```

### スキップが許容される例

以下の場合のみ Phase 0 を省略してよい:
- 完全に純粋な「文言修正」「typo 修正」のみ（HTML/CSS 構造に手を入れない）
- legacy（design_version=legacy）セクションへの修正のみで、brand 系には一切触れない

それ以外（brand 系・design_version=brand・新規 c-* 作成・CSS追加）は**必ず実行**。

---

## ワークフロー分岐

ユーザーのリクエストに応じて、以下のいずれかのワークフローを実行する（**いずれも Phase 0 を完了してから入る**）。

---

### A. 新規セクション作成

#### Phase 1: 設計

- 設計書（`docs/c-*-spec.md`、または旧 `document/c-*-spec.md`）が既に存在する場合: そのまま使用
- 存在しない場合:
  - **シンプルなセクション**: このスキル内でインライン設計（ユーザーと確認後に実装）
  - **複雑なセクション**: `/shopify-section-planner` にルーティングして設計書を作成

設計時の確認事項:
- セクションの目的・用途
- 含まれるコンテンツ要素
- blocks として繰り返す要素の有無
- 既存カスタム要素で実現可能な機能（カルーセル、アコーディオン、タブ等）
- レスポンシブ要件

#### Phase 2: 実装

[references/implementation-guide.md](references/implementation-guide.md) に従って実装。

**ファイル作成**:

| 対象 | パス | 条件 |
|------|------|------|
| セクション | `sections/c-[name].liquid` | 必須 |
| CSS（外部） | `assets/c-[name].css` | CSSが多い場合 |
| JS | `assets/c-[name].js` | カスタムJS必要時 |
| スニペット | `snippets/c-[name]-*.liquid` | 再利用可能なパーツ |

**実装順序**:
1. セクションファイルの骨格（HTML構造 + テーマパターン準拠）
2. Schema定義（共通設定 + セクション固有設定 + blocks）
3. CSS（テーマの方式に従う）
4. JS（必要な場合のみ、既存カスタム要素を優先）

#### Phase 3: 検証

- `/shopify-schema-validator` でSchema検証
- 変更禁止ファイルに触れていないことを確認
- `c-` プレフィックスが正しく使われているか確認
- 作成ファイル一覧をユーザーに提示

---

### B. 既存セクション修正

#### Phase 1: 読み込み・判定

- 対象セクションファイルを読み込む
- **テーマオリジナル**（`c-` なし）か **カスタムセクション**（`c-` あり）を判定

| タイプ | 方針 |
|--------|------|
| テーマオリジナル | 直接編集は避ける。代替案を提案: (1) `c-` オーバーライドセクション作成、(2) `custom.css` への追記、(3) 最小限の修正 |
| カスタムセクション | テーマ規約に従って自由に編集可能 |

#### Phase 2: 編集

- テーマオリジナルの修正は**最小限**に留める
- 変更理由をコメントで記述（将来のテーマアップデートで確認しやすくする）
- CSS追加は [references/modification-guide.md](references/modification-guide.md) を参照

#### Phase 3: 検証

- 新規セクションと同じ検証を実施

---

### C. CSS/JS追加

[references/css-js-guide.md](references/css-js-guide.md) に従って追加。

- テーマのブレークポイントを使用（テーマプロファイル参照）
- テーマの命名規則に従う
- `custom.css` への追記: テーマ全体に影響するスタイルの場合のみ
- セクション固有のスタイル: セクションファイル内のインラインスタイル or `c-*.css`
- **既存カスタム要素で実現可能な機能は新規JSを作らない**

---

## "c-" プレフィックスルール

| 対象 | 例 |
|------|-----|
| セクションファイル名 | `sections/c-feature-cards.liquid` |
| CSSファイル名 | `assets/c-feature-cards.css` |
| JSファイル名 | `assets/c-feature-cards.js` |
| スニペットファイル名 | `snippets/c-feature-card-item.liquid` |
| Schema name | `"name": "c-特集カード"` |
| Schema class | `"class": "shopify-section--c-feature-cards"` |

## 関連スキル

| スキル | 用途 | いつ使う |
|--------|------|---------|
| `/shopify-ds-component-search` | 既存 c-* 資産・Figma Componentsの洗い出し | **Phase 0 — 全 brand 系作業の前に必須** |
| `/shopify-theme-analyzer` | テーマ分析・プロファイル生成 | 初回 or テーマ更新時 |
| `/shopify-section-planner` | 複雑なセクションの設計書作成 | 複雑な新規セクション時 |
| `/shopify-schema-validator` | Schema JSON検証 | セクション作成・編集後 |

## Reference docs

- **セクション実装ガイド**: [references/implementation-guide.md](references/implementation-guide.md)
- **既存セクション修正ガイド**: [references/modification-guide.md](references/modification-guide.md)
- **CSS/JS追加ガイド**: [references/css-js-guide.md](references/css-js-guide.md)
