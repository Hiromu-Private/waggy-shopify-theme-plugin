---
name: shopify-theme-brand-layer
description: Shopify テーマ（Focal v13.0.0 等の上位有料テーマ）にブランド固有の見た目を「Layer 3 = brand-*.css / brand-icons.liquid」として実装する設計プロセスとテンプレート群。テーマアップデートに耐える上書き戦略・命名規則（`brand-*` 接頭辞）・4 レイヤー構造の判断フロー・実装時の落とし穴を含む。Use this skill whenever a user mentions Shopify テーマのブランド化, Figma デザインのテーマ反映, brand-*.css 作成, theme-profile.md / design-system.md の整備, Focal テーマの上書き, c- と brand- の使い分け, テーマアップデートに耐える CSS 設計, あるいは具体的に「商品カードのバッジを変えたい」「ボタンの色を Figma 仕様に」「アイコンをブランド SVG に置き換えたい」「テーマの設定値だけでは表現できない見た目を実装したい」といった依頼が出た時。Shopify ストア固有の Brand 層を切り出すあらゆる場面で発火させる。
---

# Shopify Theme Brand Layer

Shopify テーマ（特に Focal v13.0.0 のような有料の上位テーマ）に対して、ブランド固有の見た目を **テーマアップデートで壊れない形で**実装するための設計プロセス。複数のストアで横展開できるよう、ストア名に依存しないジェネリックな名前空間 `brand-*` を採用する。

## このスキルが解く問題

Shopify テーマで「ブランドのデザイン仕様」を実装する時、初心者がやりがちな 3 つの失敗:

1. **`assets/theme.css` を直接編集する** → テーマアップデート（`git pull` / theme push）でコンフリクト or 上書き消失
2. **`c-*-overrides.css` のような名前で「上書き」を書く** → `c-` は新規セクション/コンポーネント用の予約接頭辞（[Focal セクション規約](references/naming-conventions.md)）と衝突
3. **`otc-button.css` のようにストア名を含む接頭辞を使う** → 別ストアに横展開する時に名前衝突 or 全リネーム作業発生

このスキルは **Layer 3 = "Brand 層"** という独立した名前空間を導入し、上記すべてを回避する。

## 4 レイヤー構造（核心概念）

このスキルが扱うすべての判断は、まず「どの層に書くか」を決めることから始まる。

| 層 | 名前 | 触り方 | 具体物 |
|---|---|---|---|
| **Layer 1** | Focal 標準コード（変更禁止） | 編集しない | `assets/theme.css` / `theme.js` 等 |
| **Layer 2** | Focal 標準設定値 | 管理画面 or `config/settings_data.json` | 既存スキーマ項目 |
| **Layer 3** | **Brand 層**（このスキルの主戦場） | `brand-*.css` / `brand-*.liquid` を追加 | `--brand-*` 変数 / `.{base}--brand-{name}` modifier |
| **Layer 4** | 新規セクション / コンポーネント | `c-*` で新規作成 | `sections/c-*.liquid` 等 |

詳細は [references/layer-architecture.md](references/layer-architecture.md) を参照。

## ワークフロー

ユーザーから「Shopify テーマでブランドの見た目にしたい」「Figma 仕様をテーマに反映したい」等の依頼が来たら、以下の順で進める。

### Step 1: 現状把握（テーマと Figma の両方を読む）

1. **テーマ側**: 該当パーツのクラス・CSS 変数・設定キーを特定する
   - 例: ボタンなら `.button` 基底 + `.button--primary` / `.button--secondary` + `--primary-button-background` 等
   - `grep` で `assets/theme.css` 内の定義位置を確認
   - `config/settings_schema.json` / `config/settings_data.json` の関連キーを確認

2. **Figma 側**: Figma MCP `get_design_context` で対象ノードを取得し、デザイントークン（色 / 余白 / フォント / letter-spacing）を抽出
   - Figma 名と node ID を後で `design-system.md` に記録するため必ずメモ

3. **既存ドキュメント確認**: プロジェクトに `document/design-system.md` / `document/theme-profile.md` があれば最初に読む。なければこのスキルの [templates/design-system-skeleton.md](templates/design-system-skeleton.md) から開始

### Step 2: Layer 判断（どこに書くか決める）

[references/layer-architecture.md](references/layer-architecture.md) の判断フローに従って:

1. **Layer 2 の設定値で表現できるか？** → できるなら `config/settings_data.json` の値変更だけで完結（最小コスト）
2. **既存 Focal クラスの値だけ変えれば足りるか？** → Layer 3 で **クラス名を変えずに値だけ上書き**
3. **既存 Focal クラスに新しい見た目バリエーションを足したいか？** → Layer 3 で `.{base}--brand-{name}` modifier を追加
4. **Focal にない完全新規セクションか？** → Layer 4 で `c-*` を新規作成

判断を間違えると、テーマアップデートで壊れるか、別ストア横展開時にリネーム作業が発生する。

### Step 3: 実装

Layer 3 で実装する場合の具体的なパターンは [references/override-strategies.md](references/override-strategies.md) を参照。3 つの主要パターン:

- **CSS 値上書き**: `.label--subdued` のような既存クラスの背景色だけ変える
- **新規 modifier**: `.button--brand-outline-white` のような新しい見た目バリエーション
- **Icon Brand override**: `snippets/icon.liquid` 冒頭にフォールスルー分岐を追加し、`snippets/brand-icons.liquid` に Brand SVG を隔離

命名規則の詳細は [references/naming-conventions.md](references/naming-conventions.md)。

ファイル雛形:
- アイコン case 文の雛形: [templates/brand-icons-template.liquid](templates/brand-icons-template.liquid)

### Step 4: 検証（同値クラス分割で効率化）

すべてのアイコン / ボタン / ラベルを個別に検証するのは非現実的。**同値クラス分割**で 2 ケースだけ実証すれば全体動作が保証される。詳細は [references/verification-patterns.md](references/verification-patterns.md)。

検証ツール:
- `shopify theme dev --store {store}.myshopify.com` でローカルプレビュー（CDN キャッシュなし、即時反映）
- Playwright MCP で computed style と DOM 構造を JS 経由で確認
- 結果のスクリーンショットを保存

### Step 5: ドキュメント反映

実装した内容を `document/design-system.md` に記録する。ドキュメント構造は [templates/design-system-skeleton.md](templates/design-system-skeleton.md) のテンプレートに従う。

特に重要なのは:
- §7（書き換え一覧）と §8（新規ファイル一覧）のチェックボックスを「✅ 適用済み YYYY-MM-DD」に更新
- 実装中に見つけた「設計図には書かれていなかった落とし穴」は §12 の実装ログに記録（Skill 化の素材になる）

## 実装時の落とし穴

過去のストア（OverTheCentral 等）で実証された 3 つの落とし穴。実装中に必ず確認すること:

1. **セクション individual `<style>` がストア設定を上書きする** — slideshow 等のセクションは block 単位で `--primary-button-background` を inline `<style>` で再定義する。`config/settings_data.json` の値変更だけでは反映されない箇所があることを前提に設計する
2. **`settings_data.json` に未定義キーがある** — 既存値の変更だけでなく、Brand 化に必要なキーが `current` ブロックに無い場合は新規追加が必要
3. **Focal の責務分離を尊重する** — 「縦は line-height、横は padding」「色は CSS 変数、サイズは固定値」のような設計を超えて上書きしない

詳細と実例は [references/pitfalls.md](references/pitfalls.md) を参照。

## このスキルの守備範囲

| カバーする | カバーしない |
|---|---|
| Focal v13.0.0 等の上位有料 Shopify テーマ | Dawn / Sense 等の Shopify 公式テーマ（命名規則・構造が異なる） |
| Brand 層（Layer 3）の設計と実装 | 新規セクション開発（Layer 4 = `c-*`、別途 Focal セクション規約に従う） |
| ボタン / ラベル / アイコン / 見出し等のアトミックパーツ | 商品カード全体・カートフロー全体のような大きな構造変更 |
| Figma → テーマへの変換 | Figma デザイン自体の作成 |

## 参照ファイルの優先順位

依頼内容に応じて、以下の順で `references/` を読む:

| 依頼の性質 | 最初に読む |
|---|---|
| 「どこに書くか」を判断したい | [layer-architecture.md](references/layer-architecture.md) |
| 「`brand-*` の命名がよくわからない」 | [naming-conventions.md](references/naming-conventions.md) |
| 「上書きする CSS のパターンを知りたい」 | [override-strategies.md](references/override-strategies.md) |
| 「実装が動いているか確かめたい」 | [verification-patterns.md](references/verification-patterns.md) |
| 「設定変えたけど反映されない」 | [pitfalls.md](references/pitfalls.md) |
