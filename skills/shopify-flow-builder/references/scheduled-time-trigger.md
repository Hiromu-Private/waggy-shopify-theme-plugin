# Scheduled time トリガー リファレンス

`Order paid` や `Customer created` のように外部イベントを起点にする他のトリガーと違い、`Scheduled time` は **時刻そのもの** を起点にする特殊なトリガー。バッチ的に商品・顧客・注文を走査して条件に合うものに対してアクションを実行する場面で使う。Run Code は不要なケースが多く、Shopify Basic プランでも全機能が使える。

## このトリガーが向いているユースケース

| ユースケース | 例 |
|---|---|
| **販売開始日に応じたチャネル自動公開** | `custom.release_date` を過ぎた商品を Meta / Google チャネルに公開 |
| **販売終了日に応じたチャネル自動非公開** | `custom.discontinue_date` を過ぎた商品を Online Store から unpublish |
| **在庫切れ商品の自動アーカイブ** | 在庫 0 が N 日続いた商品を ARCHIVE 状態に |
| **新作タグの自動付け外し** | 入荷から 30 日経過した商品から `new` タグを剥奪 |
| **休眠顧客の自動タグ付け** | 最終注文から 180 日経過した顧客に `dormant` タグ |
| **下書き商品の自動棚卸し** | DRAFT 状態のまま 90 日経過した商品を Slack 通知 |

共通点: **「ある条件を満たすリソースを定期的に列挙して、副作用を実行する」**。Order トリガーとは異なり、対象を1つに絞り込まない（Get list アクションで複数を一括処理する）のが本トリガーの基本骨格。

## トリガー設定

| 項目 | 値 | 注記 |
|---|---|---|
| Type | Scheduled time | |
| Schedule | cron 構文 | 下記表参照 |
| Timezone | ストアの timezone | Admin > Settings > General と同一が既定 |
| `scheduledAt` | 発火時刻（ISO 8601） | Liquid `{{scheduledAt \| date: ...}}` で整形して Get list の query に渡す |

### cron 構文の典型例

| やりたい頻度 | cron | 注意 |
|---|---|---|
| 1時間ごと（毎時0分） | `0 * * * *` | 短すぎると Get list の重複処理リスクが上がる |
| 30分ごと | `*/30 * * * *` | 公式に対応しているが、レート制限と差分処理の設計が必要 |
| 毎日9:00 | `0 9 * * *` | 多くの「日次バッチ」はこれで足りる |
| 毎週月曜10:00 | `0 10 * * MON` | 曜日指定 |
| 毎月1日0:00 | `0 0 1 * *` | 月次バッチ |

**1時間ごとと毎日のどちらを選ぶか:**
- リアルタイム性が必要（販売開始日に近いタイミングで反映したい）→ 1時間ごと
- バックグラウンド処理で十分（在庫アーカイブなど）→ 毎日0時 or 早朝

### `scheduledAt` 変数

トリガーは **発火時刻** を `scheduledAt` という変数で後段に渡す。これは ISO 8601 形式の文字列で、Get list アクションの `query` 引数に Liquid フィルタで整形して渡せる:

```liquid
{{scheduledAt | date: "%Y-%m-%dT%H:%M:%SZ"}}
```

例: `2026-05-19T10:00:00Z`。Shopify の検索クエリは UTC で比較するため `%Z` で `Z` を付ける（タイムゾーン明示）のが安全。

## Scheduled time + Get list アクションの組み合わせ

`Scheduled time` 単体ではアクションを実行できない。**直後に必ず Get list アクション**を置いて対象を列挙する。Get list アクションの一覧:

| アクション | 対象 | 主な query フィルタ |
|---|---|---|
| **Get product list** | Products | `metafields.<ns>.<key>:<=`, `tag:`, `inventory_total:<`, `product_type:`, `status:` |
| **Get customer list** | Customers | `tag:`, `orders_count:<`, `last_order_at:<`, `metafields.<ns>.<key>:` |
| **Get order list** | Orders | `created_at:<`, `financial_status:`, `fulfillment_status:`, `tag:` |

### Get product list の query 構文

[Shopify Search Syntax](https://shopify.dev/docs/api/usage/search-syntax) に準拠。本スキルでよく使うパターン:

| やりたいこと | query 例 |
|---|---|
| メタフィールド `custom.release_date` が現在以前 | `metafields.custom.release_date:<={{scheduledAt \| date: "%Y-%m-%dT%H:%M:%SZ"}}` |
| 特定タグを **含まない** | `NOT tag:"meta公開"` |
| 複数条件の AND | `metafields.custom.release_date:<=NOW AND NOT tag:"meta公開"` |
| 複数条件の OR | `NOT tag:"meta公開" OR NOT tag:"google公開"` |
| status が ACTIVE のもの | `status:active` |
| 在庫 0 のもの | `inventory_total:0` |

### メタフィールド query 構文の表記揺れ

時期によって以下の表記揺れがある。**動かない時は順に試す**:

1. `metafields.custom.release_date:<=VALUE`（推奨・現行ドキュメント準拠）
2. `metafield:custom.release_date:<=VALUE`（フォールバック）

うまく検索にヒットしない時の切り分け:

- **メタフィールド定義の Admin filtering が ON か** を Admin > Settings > Custom data で確認。OFF だと検索クエリが無効化される
- Admin > Products 画面の検索バーに **同じ query 文字列をそのまま貼って** ヒット数を確認。これが正しく動けば Flow からも動く
- メタフィールド定義作成直後は **インデックス反映に数分かかる** ことがある

## Get list の引数

| 引数 | 値の例 | 意味 |
|---|---|---|
| `query` | `metafields.custom.release_date:<=2026-05-19T10:00:00Z AND NOT tag:"meta公開"` | 検索条件 |
| `first` | `50` | 1 回の取得上限（最大 250。50 を推奨） |
| `sortKey` | `UPDATED_AT` / `CREATED_AT` / `TITLE` / `ID` | ソート基準 |
| `reverse` | `true` / `false` | 降順か昇順か |

**first の選び方:**
- 50 はバランス点。多すぎると 1 iteration が長くなりタイムアウトリスク、少なすぎると 1 cron 内で全件処理しきれない
- 「1 cron で処理しきれない場合は次回 cron に持ち越し」が許容できるなら 50 で十分（タグや status の更新が完了マーカーになるため、未処理は次回拾われる）

**sortKey の選び方:**
- `UPDATED_AT desc` → 直近に編集された商品を優先処理（typical）
- `CREATED_AT asc` → 古い商品から処理（販売終了系で使う）

## For Each による反復処理

Get list の出力（`productList.products` など）を **For Each** ノードでループする。For Each 内では当該 iteration の要素が `product` / `customer` / `order` として参照可能。

### For Each 内で使う典型ノード

| ノード | 用途 |
|---|---|
| **Condition** | `product.tags` に特定タグが含まれないか判定（重複処理防止） |
| **Action: Publish product / Unpublish product** | Sales channel への公開・非公開 |
| **Action: Add product tags / Remove product tags** | 完了マーカー付与・削除 |
| **Action: Update product status** | DRAFT / ACTIVE / ARCHIVED 切替 |
| **Action: Add customer tags / Remove customer tags** | 顧客タグ操作 |

Run Code は基本不要。複雑な判定が必要な場合のみ使う（Shopify Plus のみ）。

## 完了マーカー方式とリトライ設計

Scheduled time トリガーはバッチ処理なので、**1度のアクション失敗で全体停止させない設計** が必須。本スキルが推奨するパターン:

### 完了マーカー = タグ

```
For Each product:
  If NOT (product.tags includes "meta公開"):
    Publish product → Meta publication
    Add product tags: "meta公開"
```

- **重複処理防止**: 次回 cron で `meta公開` タグ付き商品は Condition で弾かれる
- **自動リトライ**: Publish 失敗 → タグ未付与 → 次回 cron で再試行
- **部分失敗の許容**: Meta 成功 / Google 失敗の場合、Google だけ次回再試行される（タグを独立管理）

### Publish → Add tag の順序が重要

```
✅ 正しい順序:
1. Publish product
2. Add product tags

❌ 逆順だと:
1. Add product tags  ← ここで完了マーカーが付く
2. Publish product   ← 失敗してもマーカーが付いているので次回拾われない
```

Publish が冪等（成功した商品にもう一度 Publish しても副作用なし）であることを利用した設計。

## アンチパターン

### 1. 完了マーカーなしで「現在以前のメタフィールド条件」だけで絞る

```
query: metafields.custom.release_date:<=NOW
```

このまま For Each で Publish すると、**毎時すべての過去 release_date 商品**が処理対象になる。1 商品が毎時 Publish される（実害は冪等なので無いが、API レート消費・Run history 汚染）。

**対策:** `AND NOT tag:"<完了マーカー>"` を必ず追加し、Publish 後にタグを付与する。

### 2. Timezone の混在

Shopify Flow の `scheduledAt` は **ストア timezone 基準** で発火するが、Get list の query フィルタは **UTC 基準** で評価される。Liquid フィルタで整形する時に `%Z` を付けないと、ストアが Asia/Tokyo 等の場合に 9 時間ずれが発生する。

**対策:** `{{scheduledAt | date: "%Y-%m-%dT%H:%M:%SZ"}}` で `Z` を明示する。または `{{scheduledAt | date: "%FT%TZ"}}` でも同等。

### 3. `first` を大きくしすぎる

`first: 250` にすると 1 回の Flow Run で 250 iterations を回す。各 iteration で Publish + Add tags = 2 アクションなので、合計 500 アクション。Shopify Flow の Run timeout（数分）に引っかかるリスク。

**対策:** `first: 50` を上限とし、残りは次回 cron で処理する設計にする。

### 4. Trigger フィルタ機能で複雑な条件を組む

Scheduled time トリガー自体に細かいフィルタ機能はない。条件は **Get list の query に集約** する。

### 5. cron を `* * * * *`（毎分）にする

レート制限と Run history の肥大化で運用が破綻する。最短でも 5 分間隔（`*/5 * * * *`）に留め、可能なら 1 時間以上を推奨。

## 前提リソースの事前確認

Scheduled time 系 Flow を組む前に、以下を必ず確認:

| 区分 | 確認内容 | 確認方法 |
|---|---|---|
| メタフィールド定義 | `custom.release_date` 等の type と Admin filtering | Admin > Settings > Custom data > Products |
| Admin filtering | **ON になっているか** | 同上、定義の編集画面 |
| 検索クエリ動作 | Admin > Products 検索バーで同じ query を実行してヒット | UI で確認 |
| 完了マーカー用タグ | 既存商品に同名タグがないか | Admin > Products > Filters > Tagged with |
| Publication ID | Meta / Google / Online Store 等の Publication ID | [product-channel-publish-actions.md](product-channel-publish-actions.md) §Publication ID 取得 |

## 関連リファレンス

- 商品系アクション（Publish / Add tags / status 更新）の詳細: [product-channel-publish-actions.md](product-channel-publish-actions.md)
- `.flow` Export / Import: [flow-export-versioning.md](flow-export-versioning.md)
- アンチパターン全般: [anti-patterns.md](anti-patterns.md)
