# Shopify Flow Triggers リファレンス

Shopify Flow で利用可能なトリガー（イベント）の選び方と、各トリガーが提供する GraphQL スキーマの抜粋。Run Code の Input GraphQL を書く時の参照に使う。

## トリガー選択の指針

| やりたいこと | 推奨トリガー | 理由 |
|---|---|---|
| 注文金額・タグに応じて顧客MF更新 | **Order paid** | 売上確定後に発火、未払いキャンセル除外 |
| Discount コード使用検知 | **Order created** | 注文作成と同時に発火、即時性確保 |
| 高リスク注文への対応 | **Order risk analyzed** | リスク判定後に発火 |
| 新規顧客への welcome 処理 | **Customer created** | アカウント作成時に発火 |
| 返金時のロイヤルティ調整 | **Refund created** | 返金完了時に発火 |
| 在庫数の変動通知 | **Inventory level updated** | 在庫変動で発火 |

`Order paid` と `Order created` は似ているが、本スキルでは:
- **付与系（給付・特典）→ Order paid**（実売上のみ対象）
- **クリア系・使用検知 → Order created**（注文作成と同時に即反応）

## 主要トリガーの GraphQL スキーマ

Run Code の Input GraphQL で取得できるフィールドの一例。完全なスキーマは Admin > Apps > Flow の Run Code エディタで右上の GRAPHQL バッジ近くにある「変数を追加」ボタンを押すと自動補完される。

### Order paid / Order created

```graphql
query {
  order {
    id
    name                          # 注文番号 (#1001)
    note
    customer {
      id
      email
      firstName
      lastName
      tags
      ordersCount
      amountSpent { amount currencyCode }
    }
    currentSubtotalPriceSet {
      shopMoney { amount currencyCode }     # 商品計（税込・送料抜き・割引後）
    }
    currentTotalPriceSet {
      shopMoney { amount currencyCode }     # 総額
    }
    currentTotalTaxSet {
      shopMoney { amount currencyCode }
    }
    discountCodes                  # ["THANKS3000", "SUMMER10"] 等
    tags                           # Order tags
    lineItems {
      title
      quantity
      product {
        id
        title
        tags                       # 商品タグ ["Furniture", "Sale"] 等
        productType
      }
      variant {
        id
        title
        price
        sku
      }
    }
    shippingAddress {
      countryCode
      province
      city
    }
  }
}
```

**Decimal 型に注意:** `amount` フィールドは **文字列** で渡る（例: `"199999.0"`）。Run Code 内で必ず `parseFloat(amount)` してから数値比較する。

**lineItems の構造:** Shopify Flow の Run Code GraphQL では `lineItems` は connection ではなく **シンプルな配列**として渡る（Flow 側が抽象化している）。`order.lineItems.forEach(li => ...)` で直接ループ可能。

### Customer created

```graphql
query {
  customer {
    id
    email
    firstName
    lastName
    tags
    createdAt
    acceptsMarketing
    addressesCount
  }
}
```

### Refund created

```graphql
query {
  refund {
    id
    note
    totalRefundedSet {
      shopMoney { amount currencyCode }
    }
    order {
      id
      customer { id }
    }
    refundLineItems {
      lineItem {
        product { id title tags }
      }
      quantity
    }
  }
}
```

### Inventory level updated

```graphql
query {
  inventoryLevel {
    available
    location { id name }
    item {
      sku
      variant {
        id
        product { id title }
      }
    }
  }
}
```

## トリガーごとの典型的なユースケース

### Order paid

- 累積購入額でのVIPランク更新
- 特定タグ商品購入者へのクーポン金額書き込み
- 注文回数による顧客タグ自動付与
- 最終購入日の MF 記録

### Order created

- Discount コード使用検知 → MF クリア
- 注文タグ自動付与（金額・地域・配送方法ベース）
- リスクスコアに応じた Slack 通知
- B2B 注文の自動承認フロー起点

### Customer created

- welcome メール送信
- 初期 MF 値書き込み
- 新規顧客のデフォルトタグ付与
- マーケティング購読リスト追加

### Refund created

- ロイヤルティポイント減算
- VIPランクの再計算
- 返金理由の集計用タグ付与

## 「テンプレートを見る」での先行調査

新規 Flow を組む前に、必ず Admin > Flow > "テンプレートを見る" で類似テンプレートを確認する。各カテゴリの主な内容:

| カテゴリ | 主なテンプレート例 |
|---|---|
| `customers` | 顧客タグ付与・MF初期化・welcomeメール |
| `loyalty` | 累積購入額タグ、リピート顧客タグ、誕生日特典 |
| `orders` | 注文タグ付与、商品タグベースの注文タグ |
| `promotions` | Discount code 使用検知、クーポン関連 |
| `custom_data` | MF 初期化、MF 更新パターン |
| `risk` | 高リスク注文への対応、リスク判定後アクション |
| `inventory_and_merch` | 在庫切れ通知、再入荷タグ |
| `fulfillment` | フルフィルメント通知、配送状態更新 |

類似テンプレートが見つかったら、「インストール」して中身を確認→必要な箇所だけ編集する方が、ゼロから組むより圧倒的に速い。

## トリガー選択時の注意事項

- **`Order created` は注文作成時に1回のみ発火。** 注文の更新では発火しない
- **`Order paid` は支払い完了時。** カード決済なら即時、銀行振込なら入金確認後
- **`Customer created` は手動作成・ゲスト→アカウント化でも発火。** 注文時にゲストからアカウント作成された場合も含む
- **Trigger フィルタ機能はバージョン依存。** Trigger 自体に WHERE 条件を入れられる場合があるが、Run Code で集約する方が見通しが良い
