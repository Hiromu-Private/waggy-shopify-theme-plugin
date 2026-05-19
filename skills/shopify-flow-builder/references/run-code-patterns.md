# Run Code パターン集

Shopify Flow の Run Code アクションで頻出するロジックパターン。`Input GraphQL` / `JavaScript` / `Output SDL` の3点セットで提示。

## 目次

- §A: 注文金額帯による分岐 + 商品タグ判定（Order paid → MF 更新の代表パターン）
- §B: Discount コード照合（Order created → MFクリアの代表パターン）
- §C: 累積購入額の VIPランク判定
- §D: 配列・オブジェクト操作の頻出スニペット
- §E: 日付生成・タイムゾーン
- §F: 数値比較・型変換

---

## §A. 注文金額帯による分岐 + 商品タグ判定

「Furniture タグを含む注文の支払い完了時に、注文金額帯に応じたクーポン金額を顧客 MF に書き込む」パターン。本スキルでは **Order paid → Customer MF 更新** の典型例。

### Input GraphQL

```graphql
query {
  order {
    id
    customer { id }
    currentSubtotalPriceSet {
      shopMoney { amount }
    }
    lineItems {
      product { tags }
    }
  }
}
```

### JavaScript

```javascript
export default function main(input) {
  const order = input.order;

  // 1. ゲスト注文除外（customer.id が無ければ無条件で false 返却）
  if (!order || !order.customer || !order.customer.id) {
    return { eligible: false, couponAmount: null, grantedAt: null };
  }

  // 2. 商品タグ判定: line_items のうち1つでも "Furniture" タグを含めば true
  const lineItems = order.lineItems || [];
  const hasFurniture = lineItems.some(function (li) {
    if (!li || !li.product || !li.product.tags) return false;
    return li.product.tags.indexOf("Furniture") !== -1;
  });

  if (!hasFurniture) {
    return { eligible: false, couponAmount: null, grantedAt: null };
  }

  // 3. 金額帯判定: Decimal型（文字列）を parseFloat で数値化してから比較
  const subtotalStr = order.currentSubtotalPriceSet && order.currentSubtotalPriceSet.shopMoney
    ? order.currentSubtotalPriceSet.shopMoney.amount
    : "0";
  const subtotal = parseFloat(subtotalStr);

  let couponAmount;
  if (subtotal < 100000) {
    couponAmount = 2000;
  } else if (subtotal < 200000) {
    couponAmount = 3000;
  } else if (subtotal < 300000) {
    couponAmount = 5000;
  } else if (subtotal < 500000) {
    couponAmount = 8000;
  } else {
    couponAmount = 10000;
  }

  // 4. 今日の日付を生成（UTC 基準、Shopify Flow は UTC で動作）
  const now = new Date();
  const yyyy = now.getUTCFullYear();
  const mm = String(now.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(now.getUTCDate()).padStart(2, "0");
  const grantedAt = yyyy + "-" + mm + "-" + dd;

  return { eligible: true, couponAmount: couponAmount, grantedAt: grantedAt };
}
```

### Output SDL

```
"Output of grant evaluation"
type Output {
  "Whether the order is eligible for the grant"
  eligible: Boolean!
  "Coupon amount in JPY, null when not eligible"
  couponAmount: Int
  "Today's date in YYYY-MM-DD"
  grantedAt: String
}
```

### 後段の使い方

- Condition: `runCode.eligible == true`
- Action 1 (Update customer metafield): Value = `{{runCode.couponAmount}}`
- Action 2 (Update customer metafield, date type): Value = `{{runCode.grantedAt}}`

---

## §B. Discount コード照合

「特定の Discount コード（例: `THANKS2000`〜`THANKS10000`）を使った注文が作成された時に、顧客 MF をクリアする」パターン。

### Input GraphQL

```graphql
query {
  order {
    id
    customer { id }
    discountCodes
  }
}
```

### JavaScript

```javascript
export default function main(input) {
  const targetCodes = [
    "THANKS2000",
    "THANKS3000",
    "THANKS5000",
    "THANKS8000",
    "THANKS10000"
  ];

  const order = input.order;

  // ゲスト注文除外
  if (!order || !order.customer || !order.customer.id) {
    return { hasMatch: false };
  }

  // 大文字小文字を正規化して照合（Shopify Discount コードは大小区別なし）
  const codes = order.discountCodes || [];
  const hasMatch = codes.some(function (code) {
    return targetCodes.indexOf(String(code).toUpperCase()) !== -1;
  });

  return { hasMatch: hasMatch };
}
```

### Output SDL

```
"Output of discount code match check"
type Output {
  "Whether the order used any of the target codes"
  hasMatch: Boolean!
}
```

---

## §C. 累積購入額 VIP ランク判定

「累積購入額に応じて Bronze / Silver / Gold / Platinum を顧客タグとして付与する」パターン。

### Input GraphQL

```graphql
query {
  order {
    customer {
      id
      amountSpent { amount }
      tags
    }
  }
}
```

### JavaScript

```javascript
export default function main(input) {
  const customer = input.order.customer;

  if (!customer || !customer.id) {
    return { rank: null, shouldAddTag: false };
  }

  const spent = parseFloat(customer.amountSpent.amount);

  let rank;
  if (spent >= 1000000) {
    rank = "VIP-Platinum";
  } else if (spent >= 500000) {
    rank = "VIP-Gold";
  } else if (spent >= 100000) {
    rank = "VIP-Silver";
  } else if (spent >= 30000) {
    rank = "VIP-Bronze";
  } else {
    return { rank: null, shouldAddTag: false };
  }

  // 既に同じランクのタグが付いていれば再付与不要（冪等性）
  const tags = customer.tags || [];
  const alreadyTagged = tags.indexOf(rank) !== -1;

  return { rank: rank, shouldAddTag: !alreadyTagged };
}
```

### Output SDL

```
"VIP rank evaluation"
type Output {
  "Rank name (VIP-Bronze/Silver/Gold/Platinum) or null"
  rank: String
  "Whether to add the tag (skip if already tagged)"
  shouldAddTag: Boolean!
}
```

---

## §D. 配列・オブジェクト操作の頻出スニペット

### 配列に特定文字列が含まれるか

```javascript
const found = array.indexOf("Furniture") !== -1;
// または .includes（ES2016+、Shopify Flow の Run Code は ES2020+ なので使用可）
const found2 = array.includes("Furniture");
```

### 配列の中に条件を満たす要素が1つでもあるか

```javascript
const hasFurniture = lineItems.some(li =>
  li.product && li.product.tags && li.product.tags.includes("Furniture")
);
```

### 配列の中の数値合計

```javascript
const totalQty = lineItems.reduce((sum, li) => sum + (li.quantity || 0), 0);
```

### オブジェクトが null/undefined でないかの安全アクセス（オプショナルチェーン代替）

Run Code の JS は基本 ES2020+ だが、念のため明示的に書く:

```javascript
const tags = (order.customer && order.customer.tags) || [];
```

または:

```javascript
const tags = order?.customer?.tags || [];
```

### 連想配列のキーチェック

```javascript
const obj = { foo: 1 };
const hasFoo = Object.prototype.hasOwnProperty.call(obj, "foo");
// または:
const hasFoo2 = "foo" in obj;
```

---

## §E. 日付生成・タイムゾーン

Shopify Flow の Run Code は **UTC** で動作する。タイムゾーンを考慮する場合の頻出パターン:

### 今日の日付 (YYYY-MM-DD, UTC)

```javascript
const now = new Date();
const yyyy = now.getUTCFullYear();
const mm = String(now.getUTCMonth() + 1).padStart(2, "0");
const dd = String(now.getUTCDate()).padStart(2, "0");
const today = yyyy + "-" + mm + "-" + dd;
// → "2026-05-13"
```

### 今日の日付 (JST)

```javascript
const now = new Date();
const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
const yyyy = jst.getUTCFullYear();
const mm = String(jst.getUTCMonth() + 1).padStart(2, "0");
const dd = String(jst.getUTCDate()).padStart(2, "0");
const today = yyyy + "-" + mm + "-" + dd;
```

### N日後の日付

```javascript
const now = new Date();
const futureMs = now.getTime() + 30 * 24 * 60 * 60 * 1000;  // +30日
const future = new Date(futureMs);
const yyyy = future.getUTCFullYear();
const mm = String(future.getUTCMonth() + 1).padStart(2, "0");
const dd = String(future.getUTCDate()).padStart(2, "0");
const expiryDate = yyyy + "-" + mm + "-" + dd;
```

### Shopify の order.processedAt をパース

```javascript
const processedAt = new Date(order.processedAt);  // ISO 8601 文字列
const day = processedAt.getUTCDate();
```

---

## §F. 数値比較・型変換

### Decimal型（GraphQL）→ JS Number

```javascript
const amount = parseFloat(order.currentSubtotalPriceSet.shopMoney.amount);
// "199999.0" → 199999
```

JPY は subunit が無いので `parseFloat` の小数点以下は基本 `0`。だが念のため整数化:

```javascript
const amountInt = parseInt(parseFloat(amount), 10);
```

### NaN チェック

```javascript
const value = parseFloat(maybeString);
if (isNaN(value)) {
  return { error: "Invalid number" };
}
```

### 整数のフォーマット（カンマ区切り）

```javascript
const formatted = (199999).toLocaleString("ja-JP");
// → "199,999"
```

ただし、Run Code の Output は変数バインドが目的なので、フォーマットは Action 側で `{{ ... | money }}` などの Liquid フィルタを使う方が良い場合が多い。

---

## Run Code のデバッグ

### `テスト結果` パネルの活用

Run Code エディタ上部の `テスト結果` ボタンを押し、`テストイベントを選択` で過去の実注文を選んで dry-run できる。出力 JSON が表示されるので、想定通りの値が返っているか即確認可能。

### `説明を追加` でロジックの意図を残す

Run Code 単体だと「なぜこのロジックなのか」が分からなくなりやすい。`説明を追加` ボタンで Markdown のメモを残せるので、判定境界の根拠（仕様書へのリンク等）を書いておく。

### console.log は不可

Shopify Flow の Run Code は `console.log` 出力を表示できない。デバッグは Output SDL に一時フィールド（例: `debugInfo: String`）を追加して値を返す方法を取る。

```javascript
return {
  eligible: true,
  couponAmount: 3000,
  debugInfo: JSON.stringify({ subtotal: subtotal, hasFurniture: hasFurniture })
};
```

検証後はこの debugInfo を Output SDL から削除する。
