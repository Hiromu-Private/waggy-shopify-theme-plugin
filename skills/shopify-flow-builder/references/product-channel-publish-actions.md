# 商品・チャネル・タグ系アクション リファレンス

Shopify Flow の標準アクションのうち、**商品系（Product）** と **Sales channel への Publish / Unpublish** に関するアクション集。Customer 系アクションは [customer-metafield-actions.md](customer-metafield-actions.md) を参照。

## アクション一覧（このリファレンスでカバーする範囲）

| アクション ID | 名称（日本語 / 英語） | 主な用途 |
|---|---|---|
| `shopify::admin::product_publish` | 商品を公開する / Publish product | 特定 Publication（Online Store / Meta / Google など）への公開 |
| `shopify::admin::product_unpublish` | 商品を非公開にする / Unpublish product | 同 Publication からの非公開化 |
| `shopify::admin::product_add_tags` | 商品にタグを追加 / Add product tags | 完了マーカー付与、セグメント分類 |
| `shopify::admin::product_remove_tags` | 商品からタグを削除 / Remove product tags | マーカー解除、再処理対象に戻す |
| `shopify::admin::product_update_status` | 商品ステータスを更新 / Update product status | DRAFT / ACTIVE / ARCHIVED 切替 |

これらはすべて **標準アクション**（Shopify Basic プランから使用可能）。Run Code は不要。

## Publish product アクション

### 設定項目

| フィールド | 値の例 | 説明 |
|---|---|---|
| Product | `{{product}}` | For Each 内なら iteration の `product` を参照、または明示的に `productList.products[0]` 等 |
| Publication | `gid://shopify/Publication/<ID>` | 公開先 Sales channel の Publication ID |

### Publication ID の取得

実装着手前に必ず取得する。GraphQL Admin API で実行:

```graphql
query GetPublications {
  publications(first: 25) {
    nodes {
      id
      name
      app {
        title
      }
    }
  }
}
```

期待される名前と対応 Sales channel:

| `name` フィールド | 対応 Sales channel | 用途 |
|---|---|---|
| `Online Store` | Online Store | テーマ経由の公開 |
| `Point of Sale` | Shopify POS | 店舗販売 |
| `Facebook & Instagram` | Meta（Facebook / Instagram） | Meta 系チャネル公開 |
| `Google & YouTube` または `Google` | Google Shopping / YouTube | Google 系チャネル公開 |
| `Shop` | Shop アプリ | Shop モバイルアプリ |

**取得方法の選択肢:**

1. **Shopify CLI 経由**（推奨・自動化向け）
   ```bash
   shopify store auth
   shopify store execute --query 'query { publications(first: 25) { nodes { id name } } }'
   ```
   `shopify-admin-execution` skill が利用可能ならこちらが速い

2. **Admin GraphiQL App 経由**（手動・最も確実）
   - Admin > Apps > Shopify GraphiQL App を開く（未インストールならインストール）
   - 上記クエリを貼り付けて Execute
   - 結果から ID（`gid://shopify/Publication/<数値>`）をコピー

3. **`shopify-cli` を使わない場合の curl**
   ```bash
   curl -X POST "https://<shop>.myshopify.com/admin/api/2026-01/graphql.json" \
     -H "X-Shopify-Access-Token: <ADMIN_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"query":"query { publications(first: 25) { nodes { id name } } }"}'
   ```

### Publication が一覧に存在しない場合

該当 Sales channel のアプリがストアにインストールされていないか、接続が完了していない。

| 不足 | 対処 |
|---|---|
| Facebook & Instagram channel 未インストール | Admin > Apps and sales channels > Add sales channel から追加し、Meta Business アカウントと接続 |
| Google & YouTube channel 未インストール | 同上で Google アカウントと接続 |
| インストール済みだが Publication 一覧に出ない | 接続が未完了。Sales channel 設定画面で再認証・再接続 |

### Publish の冪等性

**重要:** Publish product は **既に公開済みの商品に対しても安全に実行できる**（副作用なし、エラーにもならない）。これが Scheduled time + 完了マーカー方式の自動リトライ設計を成立させる前提。

### よくあるエラー

| エラー | 原因 | 対処 |
|---|---|---|
| `Publication does not exist` | Publication ID が間違っている / チャネル削除済み | §Publication ID 取得 で再取得 |
| `Product is not eligible for this publication` | 商品が当該チャネルの要件を満たしていない（例: Google Shopping は画像必須、価格・在庫必須） | 商品データを補完 |
| アクション成功だが Sales channel に表示されない | チャネル側の同期遅延 | 数分待つ、または Sales channel 設定画面で同期再実行 |

## Unpublish product アクション

設定項目は Publish と同じ。Publication ID で対象チャネルを指定する。

### 典型ユースケース

- 販売終了日（`custom.discontinue_date`）を過ぎた商品を全 Publication から自動非公開
- 在庫切れ + 再入荷予定なしの商品を Meta / Google から自動撤退
- 季節商品（特定タグ付き）をシーズン終了で一括非公開

## Add product tags / Remove product tags

### 設定項目

| フィールド | 値の例 | 説明 |
|---|---|---|
| Product | `{{product}}` | 対象商品 |
| Tags | `meta公開` または `tag1, tag2` | カンマ区切りで複数指定可 |

### タグの命名規則

| パターン | 例 | 用途 |
|---|---|---|
| **完了マーカー**（日本語可） | `meta公開` / `google公開` / `online_store公開` | チャネル公開済みの印 |
| **段階マーカー** | `release_scheduled` / `released` | 状態遷移を表現 |
| **エラーマーカー** | `publish_failed_meta` | 失敗を記録（手動調査用） |
| **セグメントタグ** | `new_arrival` / `summer_2026` | Online Store のフィルタ等 |

**注意:**

- タグの最大文字数は 255、商品ごとの最大タグ数は 250
- 日本語タグは利用可能だが、テーマの Liquid フィルタや検索クエリで使う場合は **クォート必須**: `tag:"meta公開"`
- 既存タグと重複する Add は no-op（エラーにならない）
- 存在しないタグを Remove するのも no-op

### 完了マーカー方式の典型構造

```
For Each product:
  If product.tags does NOT contain "meta公開":
    Publish product → Meta publication
    Add product tags: "meta公開"
```

- Publish が成功 → Add tag → 次回 cron で Condition により弾かれる
- Publish が失敗 → タグ未付与 → 次回 cron で再試行

## Update product status

### 設定項目

| フィールド | 値 | 説明 |
|---|---|---|
| Product | `{{product}}` | 対象商品 |
| Status | `DRAFT` / `ACTIVE` / `ARCHIVED` | 商品のステータス |

### 典型ユースケース

| シナリオ | 遷移 |
|---|---|
| 在庫切れ + 再入荷なしを自動アーカイブ | `ACTIVE` → `ARCHIVED` |
| 季節商品の冬眠 | `ACTIVE` → `DRAFT` |
| 販売開始日到来で公開 | `DRAFT` → `ACTIVE` |

**注意:** `ARCHIVED` にすると Online Store からも非表示になる（Sales channel との関係は別）。明示的に **Publish を控える** + **Archive する** のような組み合わせをする時は、両方のアクションを設定する。

## Sales channel への一括公開パターン

「販売開始日に複数 Sales channel に同時公開」をする場合、各チャネルごとに Publish + Add tag をブランチで並列実行する:

```
For Each product:
  Branch A: If NOT tag:"meta公開"
    → Publish to Meta
    → Add tag "meta公開"

  Branch B: If NOT tag:"google公開"
    → Publish to Google
    → Add tag "google公開"

  Branch C: If NOT tag:"online_store公開"
    → Publish to Online Store
    → Add tag "online_store公開"
```

各ブランチが独立しているため:
- Meta だけ失敗 / Google 成功 のような部分失敗を許容
- ブランチごとに次回 cron で個別リトライ
- 新規チャネル追加時は新ブランチを追加するだけ

## 関連リファレンス

- Scheduled time トリガーの設定: [scheduled-time-trigger.md](scheduled-time-trigger.md)
- 顧客系アクション（Customer tag / MF）: [customer-metafield-actions.md](customer-metafield-actions.md)
- `.flow` Export / Import: [flow-export-versioning.md](flow-export-versioning.md)
- アンチパターン: [anti-patterns.md](anti-patterns.md)
