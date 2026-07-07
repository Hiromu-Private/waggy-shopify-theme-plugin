---
name: shopify-asset-harvest
description: "実装済みの Shopify テーマ資産（snippet / CSS / セクション / 計測タグ / schema パターン）を汎用化して案件横断アセットライブラリに登録する回収スキル。使用タイミング：「資産化して」「asset harvest」「ライブラリに登録して」「この実装を再利用できるようにして」「資産を回収」、セクション実装の完了時・案件の納品時。登録先は ~/Developer/Waggy/shopify-assets（環境変数 SHOPIFY_ASSETS_DIR で上書き可）。"
---

# Shopify Asset Harvest — 資産回収スキル

案件で作った実装を「次の案件で流用できる形」に汎用化して中央ライブラリへ蓄積する。
**このスキルが回らないと `/shopify-ds-component-search` の中央ライブラリ検索は永遠に空振りする**。実装完了・納品のタイミングで能動的に回すこと。

## ライブラリの場所解決

```bash
ASSETS_DIR="${SHOPIFY_ASSETS_DIR:-$HOME/Developer/Waggy/shopify-assets}"
```

`$ASSETS_DIR/INDEX.md` が存在しなければ、ライブラリ未設置。ユーザーに確認のうえ `git clone` または初期構造（INDEX.md / cards/ / snippets/、書式は本スキルの references 参照）を作成する。

## 手順

### Step 1: 対象の特定

harvest 対象を確定する。指定が無ければ「このセッションで実装・修正したテーマファイル」から再利用価値の高いものを候補提示して選んでもらう。

再利用価値の判断基準:
- 複数案件で出現しうる UI/機能か（pill ボタン・カード・スライダー・お知らせバー・計測タグ等）
- テーマ非依存に汎用化できるか（Focal 専用構造そのままなら themes に明記して登録は可）
- 一過性のクライアント固有要件でないか（固有すぎるものは登録しない）

### Step 2: 重複チェック

```bash
grep -i "<関連キーワード>" "$ASSETS_DIR/INDEX.md"
```

類似カードが既にあれば**新規カードを作らず既存カードの更新**（コード改善の反映・`## 使用実績` への追記）を提案する。同一概念の資産カード分裂はこのライブラリの敵。

### Step 3: 機密スクラブ + 汎用化

`references/generalization-checklist.md` のチェックリストを**全項目**通す。要点:

- ストアドメイン・URL・ID・トークン類を除去
- テーマ固有依存（翻訳キー `t:`、color_scheme 構造、カスタム要素）を除去または「汎用化メモ」に明記
- raw value（色・サイズ）は CSS 変数 + フォールバックに置換
- 権利面で丸ごと複製が不適切な場合は「パターン・構造」レベルに抽象化

### Step 4: カード + 実コードの配置

- カード: `$ASSETS_DIR/cards/{name}.md` — 書式は `$ASSETS_DIR/cards/_TEMPLATE.md` に完全準拠（frontmatter: name / type / themes / origin / harvested / tags / files / deps）
- 実コード: `$ASSETS_DIR/snippets/{name}.liquid` 等。カードの `files:` に列挙
- harvested 日付は今日。tags は「次の自分が検索しそうな語」を先頭に

### Step 5: INDEX 追記 + コミット

1. `$ASSETS_DIR/INDEX.md` のテーブルに 1 行追記: `| {name} | {type} | {tags} | {origin} | {一言概要} |`
2. ライブラリリポ内でコミット:

```bash
cd "$ASSETS_DIR" && git add -A && git commit -m "harvest: {name}（{origin} から回収）"
```

（このリポにリモートがあれば push、無ければコミットのみで終了）

### Step 6: 完了報告

登録したカード名・パス・INDEX の行・次回の引き方（`/shopify-ds-component-search` が自動で拾う旨）を報告する。

## ガードレール

| ルール | 理由 |
|---|---|
| 機密チェックリストを通す前に書き込まない | 認証情報・顧客情報の流出防止 |
| 元案件のファイルは一切変更しない（読むだけ） | harvest は読み取り専用の回収作業 |
| INDEX.md に無いカードを作らない（必ず両方更新） | 索引に無い資産は検索不能＝死蔵 |
| 権利がグレーな資産は登録前にユーザーへ確認 | 受託契約上の権利帰属への配慮 |

## 関連

- `/shopify-ds-component-search` — 読み出し側。Step 0 でこのライブラリを検索する
- `/theme-orchestrator` — 実装完了時にこのスキルの実行を提案してくる
