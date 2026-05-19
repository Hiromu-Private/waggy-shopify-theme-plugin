# Flow テンプレート

Shopify Admin の Flow アプリで「インポート」を使うと、これらの `.flow` ファイルから完成形のワークフローを一発復元できる。

## テンプレート一覧

### `order-paid-to-customer-mf.flow`

「注文の支払い完了時に、商品タグ判定 + 金額帯分岐をして顧客 MF を更新する」雛形。

**構造:**
```
Order paid (trigger)
   ↓
Run code  (Furniture タグ判定 + 5段階金額分岐)
   ↓
Condition (runCode.eligible == true)
   ↓ True
Update customer metafield (custom.thanks_coupon_amount = {{runCode.couponAmount}})
   ↓
Update customer metafield (custom.thanks_coupon_granted_at = {{runCode.grantedAt}})
```

**カスタマイズポイント:**

| 変更したい箇所 | 編集対象 |
|---|---|
| 商品タグの名前（Furniture → 別タグ） | Run Code の `indexOf("Furniture")` を変更 |
| 金額帯の境界 | Run Code の `if/else if` チェイン |
| クーポン金額 | Run Code の `couponAmount = 2000` 等 |
| MF の namespace / key | Update customer metafield アクションの設定 |
| トリガー条件（paid → fulfilled 等） | Trigger ノードを変更 |

**インポート後の前提:**
- 顧客 MF Definition `custom.thanks_coupon_amount` (Integer) と `custom.thanks_coupon_granted_at` (Date) が事前作成済みであること
- これらの MF が `analyticsQueryable: true` でないと Customer Segment で参照できない（Segment と組み合わせる場合のみ）

### `order-created-discount-clear-mf.flow`

「特定のDiscount コードを使った注文が作成された時に、関連する顧客 MF を削除する」雛形。

**構造:**
```
Order created (trigger)
   ↓
Run code  (THANKS系コード照合、大文字小文字非依存)
   ↓
Condition (runCode.hasMatch == true)
   ↓ True
Remove customer metafield (custom.thanks_coupon_amount)
   ↓
Remove customer metafield (custom.thanks_coupon_granted_at)
```

**カスタマイズポイント:**

| 変更したい箇所 | 編集対象 |
|---|---|
| 監視する Discount コード | Run Code の `targetCodes` 配列 |
| MF の namespace / key | Remove customer metafield アクションの設定 |
| 部分一致したい（プレフィックス） | Run Code 内で `code.startsWith("THANKS")` 等に変更 |

**インポート後の前提:**
- 顧客 MF Definition が事前作成済み
- 該当する Discount コード（例: `THANKS2000` 等）が Admin > Discounts で作成済み

### `scheduled-channel-auto-publish.md`（構造ドキュメント）

「販売開始日（メタフィールド）を過ぎた商品を、複数 Sales channel（Meta / Google / Online Store 等）に自動公開する」Flow の **構造ドキュメント**。

`.flow` JSON ではなく Markdown で配布する理由:

- `.flow` は内部に SHA256 ハッシュを持ち、外部生成すると Import 失敗のリスクがある
- Publication ID は **ストアごとに異なる固有値** で、テンプレートとして配布する `.flow` には埋め込めない（プレースホルダにすると Import で弾かれる）
- このため Admin UI で構築するための **ステップ定義** として提供する

**構造:**
```
Scheduled time (0 * * * *)
   ↓
Get product list (metafields.<ns>.<key>:<=NOW AND NOT tag:"<marker>" ...)
   ↓
For Each productList.products
   ├─ Branch 1: If NOT tag:"meta公開" → Publish to Meta → Add tag "meta公開"
   ├─ Branch 2: If NOT tag:"google公開" → Publish to Google → Add tag "google公開"
   └─ Branch N: （必要なチャネル数だけ複製）
```

**カスタマイズポイント:**

| 変更したい箇所 | 編集対象 |
|---|---|
| 判定メタフィールド | Get product list の query の `metafields.<ns>.<key>` |
| 完了マーカータグ名 | Condition と Add product tags の値、Get product list の query の `NOT tag:` |
| 公開先チャネル数 | For Each 内のブランチ数 |
| Publication ID | Publish product アクションの値 |
| 実行頻度 | Scheduled time の cron |

**プラン要件:** Shopify Basic 以上で動作（Run Code 不使用）。

**実装後の流れ:** Admin で構築 → Run history で動作確認 → エクスポートしてストア専用リポに `.flow` として保存。本スキルの templates/ に汎用化版を後追いコミットしても良い（Publication ID をプレースホルダ化）。

## 使い方

1. Admin > Apps > Flow > ワークフロー一覧画面の `インポート` ボタンをクリック
2. このリポの `.flow` ファイルを選択（直接 GitHub からダウンロードしても OK）
3. インポート完了後、**下書き（OFF）状態でワークフローが追加される**
4. 必要な箇所をカスタマイズ（Run Code の値、MF 参照先など）
5. テストイベントで動作確認
6. 合格後に `ワークフローをオンにする` で本番有効化

## 注意

- 各テンプレートは「下書き状態」を保ったまま Export されているはず。インポート後も自動で ON にはならない
- 別ストアでの利用には、前提リソース（MF Definition / Discount / Customer Segment 等）の事前作成が必要
- インポート時にエラーが出た場合は、references/flow-export-versioning.md のトラブルシューティング節を参照
