# Flow Export / Import / Git バージョン管理

Shopify Flow は標準で Export / Import に対応している。これを使うと `.flow` JSON をリポにコミットし、Git でバージョン管理・別ストアへの展開・テキスト diff レビューができる。

## Export 手順

1. Admin > Apps > Flow から対象ワークフローを開く
2. 右上の `その他のアクション` ドロップダウンをクリック
3. `エクスポート` を選択
4. ブラウザの「ダウンロード」フォルダに `<ワークフロー名>.flow` が保存される

ファイル名にはワークフロー名がそのまま使われる（スペース・記号含む）。リポにコミットする時は kebab-case にリネーム推奨:

```bash
mv ~/Downloads/'Thanks Coupon — Grant.flow' \
   document/specs/flows/thanks-coupon-grant.flow
```

## Import 手順

1. Admin > Apps > Flow のワークフロー一覧画面で `インポート` ボタンをクリック
2. `.flow` ファイルを選択
3. インポート後、ワークフロー名・トリガー・条件・アクションがすべて復元される
4. **状態は「下書き（OFF）」でインポートされる**。テスト後に手動で ON 切替

別ストアに同じ Flow を展開する時もこの手順で完結する。

## `.flow` ファイルの内部構造

`.flow` は JSON だが、先頭にハッシュ値が付いた特殊フォーマット:

```
<sha256_hash>:{"__metadata":{"version":0.1},"root":{"steps":[...],"links":[...], ...}}
```

`root.steps` 配列の各要素が1ノード（Trigger / Run code / Condition / Action）。`config_field_values` に各ノードの設定値が JSON エンコードされて入る。

### Run Code ステップの例

```json
{
  "step_id": "01KRH1YZMW...",
  "step_position": [0, 180],
  "config_field_values": [
    {
      "config_field_id": "input",
      "value": "query { order { id customer { id } } }"
    },
    {
      "config_field_id": "script",
      "value": "export default function main(input) { ... }"
    },
    {
      "config_field_id": "output_schema",
      "value": "type Output { eligible: Boolean! }"
    }
  ],
  "task_id": "shopify::flow::run_code",
  "task_version": "0.1",
  "task_type": "ACTION"
}
```

### `links` でステップを繋ぐ

```json
"links": [
  {
    "from_step_id": "01KRH1VG...",
    "from_port_id": "output",
    "to_step_id": "01KRH1YZ...",
    "to_port_id": "input"
  }
]
```

Condition ノードの場合は `from_port_id` が `true` または `false` になる。

## Git 運用パターン

リポに `.flow` を保存する時の推奨レイアウト:

```
document/specs/flows/
├── best-practices.md
├── thanks-coupon-grant.flow                   # Export した JSON
├── thanks-coupon-grant.runcode.js             # Run Code の JS 単体ファイル（読みやすさ用）
├── thanks-coupon-grant.md                     # 構造ドキュメント
├── thanks-coupon-clear-on-use.flow
├── thanks-coupon-clear-on-use.runcode.js
└── thanks-coupon-clear-on-use.md
```

### なぜ `.runcode.js` を別に置くか

`.flow` の JSON 内に JS が JSON エンコードされて入るが、改行が `\n` 文字列化されているため**目視レビューや diff が読みにくい**。同じ JS を `.runcode.js` として別ファイルで保存しておくと:

- IDE のシンタックスハイライトが効く
- ESLint / Prettier をかけられる
- `git diff` が綺麗に出る
- レビュー時のコメント付けが容易

**ルール:** Run Code を変更する時は `.runcode.js` を Single Source of Truth として更新 → Admin の Flow Editor に貼り付け → `.flow` を再エクスポート、の順で同期する。

### 別ストア展開

同じ Flow を別の Shopify ストアに展開する時:

1. リポから `.flow` を取得
2. 展開先ストアの Admin > Flow > インポート で読み込み
3. **前提リソースが揃っているか確認**（MF Definition、Discount Code、Customer Segment 等）
4. テストイベントで dry-run
5. OFF 状態のまま検証 → 合格後に ON

前提リソースが揃っていない場合、Flow は保存できるが Action 設定でエラーが出る（例: 存在しない MF を参照）。

## バージョン履歴の管理

Shopify Admin 自体も `バージョン履歴` タブで Flow の編集履歴を保持しているが、これは Shopify 内のもので Git とは別系統。本格的にバージョン管理するなら `.flow` を Git にコミットするのが確実。

コミットメッセージ例:

```
feat(flow): add thanks-coupon-grant flow

Order paid トリガーで Furniture タグ + 金額帯判定 → 顧客 MF 更新。
Run Code に判定ロジックを集約し、Condition は eligible == true の
単純判定のみ。OFF 状態で保存済み。
```

```
fix(flow): adjust amount tier boundary in thanks-coupon-grant

¥100,000 ぎりぎりの注文が 3000 円クーポン帯になるよう調整。
RunCode の `< 100000` を `<= 99999` に変更。.runcode.js を更新後、
Admin に貼り付け → 再エクスポート。
```

## トラブルシューティング

### Import 時に「インポートに失敗しました」エラー

- `.flow` ファイルが壊れている可能性（先頭のハッシュ値が欠けている等）
- Shopify Flow のバージョン互換性（古い `.flow` を新しい Flow にインポート、または逆）
- 対処: Admin で新規ワークフローを作成し、エクスポートして雛形 `.flow` の構造を確認 → 不整合を修正

### Import 後にノードが繋がっていない

- `links` 配列が壊れている、または `step_id` が一意でない
- 対処: Visual Builder で手動で再接続するか、JSON を編集して修復

### Run Code の JS が文法エラー

- `.runcode.js` を IDE で開いて文法チェック
- ES2020+ の機能（`?.`、`??`）は使用可だが、念のため明示的な null チェックを優先
- Run Code の `テスト結果` パネルで実行してエラーログを確認
