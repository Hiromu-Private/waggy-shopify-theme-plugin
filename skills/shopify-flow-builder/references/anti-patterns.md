# アンチパターン集

Shopify Flow を組む時に避けるべき設計と、その理由・代替案。

## 1. Condition ノードを5階層以上ネストする

### 問題

```
Trigger
   ↓
Condition (subtotal < 100000)
   ├─ True → Action (set 2000)
   └─ False → Condition (subtotal < 200000)
                ├─ True → Action (set 3000)
                └─ False → Condition (subtotal < 300000)
                             ├─ True → Action (set 5000)
                             └─ False → ...（さらに2段ネスト）
```

- Visual Builder で視認性が壊滅的
- ノード位置の自動配置で重なり合う
- 編集時に間違ったノードをクリックしやすい
- メンテナンス時にロジックを追えなくなる

### 代替案: Run Code に集約

```javascript
let couponAmount;
if (subtotal < 100000) couponAmount = 2000;
else if (subtotal < 200000) couponAmount = 3000;
else if (subtotal < 300000) couponAmount = 5000;
// ...
return { couponAmount };
```

Condition は `runCode.couponAmount != null` または `runCode.eligible == true` の1段だけ。

## 2. `currentSubtotalPriceSet.shopMoney.amount` をそのまま比較

### 問題

`amount` は GraphQL の Decimal 型で **文字列**（例: `"199999.0"`）として渡る。Flow UI で直接 `< 100000` のような比較をしても期待通り動かない。

### 症状

- 「金額帯分岐が常に同じ枝に行く」
- 「99999 と 100000 で動作が変わらない」
- 「巨大金額（1000000）と小額（1000）で同じ結果」

### 代替案: Run Code 内で parseFloat

```javascript
const subtotal = parseFloat(order.currentSubtotalPriceSet.shopMoney.amount);
if (subtotal < 100000) { ... }
```

## 3. Update metafield の Value 欄に JS を書こうとする

### 問題

```
Value: {{ if subtotal < 100000 then 2000 else 3000 }}
```

このような書き方はサポートされない。Value 欄は **Liquid 式評価のみ**で、JS の条件式は使えない。

### 代替案: Run Code で計算 → 変数バインド

Run Code で `couponAmount` を出力 → Update metafield の Value 欄に `{{runCode.couponAmount}}` をバインドする。

## 4. ゲスト注文（customer.id null）対策を省略

### 問題

`Order created` / `Order paid` はゲストチェックアウトの注文でも発火する。`order.customer` が `null` のまま Update customer metafield アクションに渡ると、アクションが失敗するか、意図しない customer に書き込まれる可能性がある。

### 症状

- Flow Run history で「アクション失敗」が頻発
- 一部の注文だけ MF 更新されない

### 代替案: Run Code 先頭でガード

```javascript
if (!order || !order.customer || !order.customer.id) {
  return { eligible: false };
}
```

Condition で `eligible == true` 判定すれば、ゲスト注文は自動的に False 分岐に流れて Action 実行されない。

## 5. テスト未済で `ワークフローをオンにする` を押す

### 問題

ON にした瞬間から実注文に対して発火する。テスト未済の Flow が誤動作すると:

- 全顧客 MF が想定外の値で上書きされる
- 大量のメール送信や Slack 通知でスパム化
- ロールバックは Flow を OFF にしても **既に書き込まれた MF は戻らない**

### 代替案: 必ず OFF（下書き）で保存

1. Visual Builder で構築 → 保存ボタンを押さず自動保存させる
2. ワークフロー名を設定
3. 「ワークフローをオンにする」は **絶対に押さない**
4. `テストイベントを選択` で過去の実注文に対して dry-run
5. テスト合格後に手動で ON

### 段階的 ON 戦略

複数の Flow を組む時:

- クリア系（MF を消す）Flow → 先に ON
- 付与系（MF を書く）Flow → 後に ON

逆順にすると、付与された MF が即座にクリアされず、意図しないセグメント所属が発生する。

## 6. 大文字小文字を区別したまま Discount コード照合

### 問題

Shopify Discount コードは **大文字小文字を区別しない**入力を受け付けるが、`order.discountCodes` 配列にどのケースで格納されるかは保証されていない（通常は登録時の表記）。

### 症状

- 顧客が `thanks3000` と入力 → コードは適用される
- Flow の Run Code で `codes.includes("THANKS3000")` 判定 → false（小文字で渡るため）
- Flow が発火せず、MF クリアが漏れる

### 代替案: `.toUpperCase()` で正規化

```javascript
const hasMatch = codes.some(code =>
  targetCodes.includes(String(code).toUpperCase())
);
```

`targetCodes` 側は最初から大文字で定義。`String()` で囲んで型安全に。

## 7. `analyticsQueryable` 未設定の MF を Segment クエリで使う

### 問題

Segment Query Language で `metafields.custom.thanks_coupon_amount = 2000` のような条件を書いても、MF Definition の `analyticsQueryable` capability が無効だとフィルタとして認識されない。

### 症状

- セグメント保存時に「filter cannot be found」エラー
- Discount に紐付けたセグメントのメンバー数が常に 0

### 代替案: 事前に MF Definition で有効化

```graphql
mutation {
  metafieldDefinitionUpdate(definition: {
    namespace: "custom"
    key: "thanks_coupon_amount"
    ownerType: CUSTOMER
    capabilities: {
      analyticsQueryable: { enabled: true }
    }
  }) {
    updatedDefinition { id }
    userErrors { field message }
  }
}
```

2026-04 API バージョン以降で CUSTOMER ownerType に対応。

## 8. 日付の絶対値ハードコード

### 問題

```javascript
return { expiryDate: "2027-05-13" };
```

このように特定日付を Run Code 内にハードコードすると、年が変わるたびに修正が必要。

### 代替案: 動的計算

```javascript
const now = new Date();
const expiry = new Date(now.getTime() + 365 * 24 * 60 * 60 * 1000);
const expiryDate = expiry.toISOString().split("T")[0];
return { expiryDate };
```

## 9. Trigger で「フィルタ条件」をすべて済ませようとする

### 問題

Trigger ノードに条件フィルタ機能がある場合、そこで「Furniture タグ含む注文のみ」のように絞ろうとする。

### 代替案

Trigger フィルタは**簡単な条件**（例: Order paid のみ）に留め、複雑な判定は Run Code で集約する。理由:

- Trigger フィルタの記法は限定的（複数条件の AND/OR が組みにくい）
- ロジックを Run Code に集約すれば、Trigger を変更しても判定は再利用できる
- 変更時の影響範囲を1ノードに限定できる

## 10. Run Code の Output SDL を不完全に定義

### 問題

```
type Output {
  message: String
}
```

`!` を付けない（nullable）と、後段の Action で「変数が null かもしれない」扱いになり、Value バインドで警告が出ることがある。

### 代替案

確実に値を返すフィールドは `!`（non-null）を付ける:

```
type Output {
  eligible: Boolean!
  couponAmount: Int
  grantedAt: String
}
```

`eligible` は必ず boolean を返すので `!`。`couponAmount` は eligible: false の時に null を返すので `!` を付けない。

## まとめ

これらアンチパターンの根底にある原則:

- **ロジックは Run Code に集約する**（Visual Builder の Condition ネストを避ける）
- **型変換は明示的に**（Decimal 文字列 → Number、大文字小文字正規化）
- **null/undefined をガードする**（特に customer.id）
- **OFF で保存・テスト・ON 切替の順序を厳守**
- **動的な値は動的に計算する**（日付・タイムゾーン）
- **前提リソース（MF Definition の capability 等）を事前確認する**
