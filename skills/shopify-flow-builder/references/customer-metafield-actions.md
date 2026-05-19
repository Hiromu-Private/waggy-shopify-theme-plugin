# Customer Metafield / Tag Action リファレンス

Shopify Flow で顧客に対して状態変更を行うアクションの使い方。本スキルで頻出する4つを掘り下げる。

## 1. Update customer metafield

「顧客メタフィールドに値を書き込む（既存値があれば上書き）」アクション。

### 設定項目

| 項目 | 値 | 備考 |
|---|---|---|
| Customer | `{{order.customer}}` または `{{customer}}` | Trigger に応じて自動推測される |
| Namespace | `custom` 等 | 事前に MF Definition で作成済みのもの |
| Key | `thanks_coupon_amount` 等 | 同上 |
| Type | `number_integer` / `date` / `single_line_text_field` 等 | MF Definition の type と一致させる |
| Value | `{{runCode.couponAmount}}` または `2000` のような固定値 | Run Code 出力を変数バインド可能 |

### 動作仕様

- 既存 MF があっても **上書きする**（明示的なフラグ無し）
- MF Definition が存在しない namespace/key を指定するとエラー
- `Type` が MF Definition と一致しないとエラー
- Value は Liquid 式（`{{ ... }}`）を受け付ける

### よくある落とし穴

- **Date 型に「2026/5/13」のような形式を入れる** → エラー。`YYYY-MM-DD` 厳守
- **Integer 型に文字列「2000」を入れる** → Flow UI が自動変換してくれる場合もあるが、Run Code 出力で `Int` 型として返す方が安全
- **MF Definition の analyticsQueryable が false** → Customer Segment クエリで使えない。事前に有効化する

## 2. Remove customer metafield

「顧客メタフィールドを削除する」アクション。

### 設定項目

| 項目 | 値 | 備考 |
|---|---|---|
| Customer | `{{order.customer}}` | |
| Namespace + Key | ドロップダウンで選択 | MF Definition 一覧から選ぶ形式 |

### Update との違い

- `Remove` は **MF を物理削除**する（次回 query で `null` になる）
- `Update` で空文字や `null` を入れるよりクリーンな状態にできる
- セグメントクエリ `metafield.custom.X = 2000` の判定が確実に false になる

### 利用パターン

- 使用済みクーポンの状態クリア（本スキル §B パターン）
- 一時的な顧客フラグの削除
- MF の値が不正だった場合のリセット

## 3. Add customer tags

「顧客にタグを追加する」アクション。

### 設定項目

| 項目 | 値 |
|---|---|
| Customer | `{{order.customer}}` |
| Tags | カンマ区切りまたは Liquid 式 |

### Value 例

```
VIP-Gold
```

```
{{runCode.rank}}
```

```
VIP-Gold, Repeat-Customer
```

### 動作仕様

- 既存タグに **追加**（既存タグは保持）
- 同じタグが既に付いていても重複しない（Shopify が deduplicate する）
- カンマ区切りで複数タグを一度に追加可能

### Customer Segment との関係

タグベースのセグメント条件は `customer_tags CONTAINS 'VIP-Gold'` のような形で書ける。MF より高速にクエリできる場合がある。

## 4. Remove customer tags

「顧客タグを削除する」アクション。

### 設定項目

| 項目 | 値 |
|---|---|
| Customer | `{{order.customer}}` |
| Tags | カンマ区切り |

### 利用パターン

- VIP ランクのダウングレード（古いランクタグを削除 → 新しいランクタグを Add）
- 期間限定キャンペーン参加者タグの削除
- 顧客誤分類の修正

## MF vs Tags の使い分け

| 観点 | Customer Metafield | Customer Tag |
|---|---|---|
| **値の構造** | typed（Integer / Date / JSON / etc.） | 単純な文字列 |
| **複数値** | 1つの key につき1値（list 型もあるが特殊） | 配列として何個でも |
| **クエリ速度** | analyticsQueryable で対応、やや遅い | 高速 |
| **管理画面 UX** | Definition 画面で型管理可 | Free-form、増えすぎると管理困難 |
| **Storefront 露出** | 制御可（storefront access 設定） | 直接の露出は不可 |
| **Segment 条件** | `metafields.custom.X = N` | `customer_tags CONTAINS 'X'` |
| **本スキル推奨** | 値が typed / 単一値 / Discount 連動 | フラグ的に複数同時に持たせたい時 |

判断基準:

- **クーポン金額（Integer）や付与日（Date）など型が重要** → MF
- **「VIP」「Repeat」「Furniture-Buyer」など複数フラグ同時** → Tag
- **Storefront から読みたい** → MF（storefront access ON）
- **Segment で複雑なクエリしたい** → MF（analyticsQueryable ON）

## アクションのまとめ表

| アクション | trigger に渡す customer | 必須スコープ |
|---|---|---|
| Update customer metafield | `{{order.customer}}` | `write_customers` + metafield 関連 |
| Remove customer metafield | 同上 | 同上 |
| Add customer tags | 同上 | `write_customers` |
| Remove customer tags | 同上 | 同上 |

Flow アプリが内部で API スコープを管理しているため、ユーザーが個別にスコープ付与する必要はない（インストール時に承認済み）。
