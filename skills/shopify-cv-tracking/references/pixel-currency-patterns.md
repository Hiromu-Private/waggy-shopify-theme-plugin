# カスタムピクセル通貨対応パターン — Customer Events API の通貨挙動と JPY 換算実装

カスタムピクセル（Web Pixel / Customer Events API）で金額を扱う時の必須知識。ここを飛ばすと売上計測が静かに壊れる。

## 最重要: Customer Events API は presentment currency の生値を返す

- `event.data.checkout.totalPrice.amount` および `cartLine.merchandise.price.amount` は **presentment currency**（顧客の決済通貨）の生値を返す
- **`MoneyV2` 型であっても shop currency（JPY）には自動換算されない**
- Shopify Markets を使った多通貨ストアでは、外貨ロケール（`/zh-tw` 等）の顧客の checkout 情報には外貨（例: TWD）の数値がそのまま入ってくる

### 事故パターン（CENE 案件 2026-05-25 に実際に発生）

この挙動に気づかず adebis / 旧式の JP 特化計測タグへ数値をそのまま送ると、**売上が「実額 ÷ 為替レート」分小さく記録される**。TWD の場合、実額の約 1/5 の売上として記録され続けた。

## 実装パターン: toJpy ヘルパー

金額系イベントは、通貨判定 + JPY 換算ヘルパーを**必ず**通す:

```javascript
// レート値はプレースホルダ。実際の値は案件ごとに記入する（下記注記参照）
const TO_JPY_RATE = { JPY: 1, TWD: /* 現在のレートを記入 */ 0 };  // レートは四半期更新運用
function toJpy(money) {
  if (!money) return 0;
  const rate = TO_JPY_RATE[money.currencyCode || 'JPY'];
  return Math.round(Number(money.amount || 0) * (rate ?? 1));
}
// 使用例: amount: toJpy(event.data.checkout.totalPrice)
```

> ⚠️ **レート値はプロジェクトごとに必ず記入・確認する**（上のコードはプレースホルダ）。値は `window.Shopify.currency.rate` の逆数（Shopify 公式換算レート）を基準にし、四半期ごとに見直す。扱う通貨の種類もストアの Markets 設定に合わせて増減させる。

### 設計意図（変えてはいけないポイント）

| 設計 | 意図 |
|------|------|
| JPY は `× 1` で素通し | 日本サイト側で誤ってレートが掛かる**二重換算事故を防ぐ** |
| 未登録通貨は `?? 1` で原値返却 | 換算表に無い通貨が来ても**計測落ちさせない**（値がゼロや undefined にならない） |
| レートは `window.Shopify.currency.rate` の逆数（Shopify 公式換算レート）準拠 | 恣意的なレートを使わない。四半期ごとに見直して更新する |

## Web Pixel sandbox iframe の制約

- カスタムピクセルは `sandbox="allow-scripts allow-forms"` の iframe 内で実行される
- `allow-same-origin` が**ない**ため、親 window の `window.Shopify.currency.rate` には**直接アクセス不可**
- したがってレート値の動的取得はできない。**コードにハードコードする運用が必須**（上記の四半期更新運用とセット）

## デプロイ反映確認: ピクセル URL の @N バージョン番号

- ピクセルの読み込み URL は `https://{shop}/web-pixels@.../custom/web-pixel-{id}@{version}/sandbox/modern/...` 形式
- **バージョン番号（`@N`）はコード更新時にインクリメント**される
- デプロイが反映されたかどうかの確認指標として使える（DevTools の Network タブで実際に読み込まれている URL の `@N` を見る）

## 売上乖離の診断法

計測ツール側の売上とストア実売上がズレた時の切り分け:

| 症状 | 判定 |
|------|------|
| 「実額 / 計測ツール記録」の比率が **1/為替レートに揃っている**（TWD なら約 5 倍） | **通貨ミスマッチ確定**。presentment currency をそのまま送っている。toJpy ヘルパーを導入する |
| 比率が**バラついている** | 「複数 CV 重複計上」「集計仕様の問題」など別要因が混入している可能性。adebis なら管理画面で order_id（`ebisOther1`）ベースで逆引き確認する |

## 実装後の検証

このパターンを実装したら、必ず [verification-checklist.md](verification-checklist.md) の 6 パターン検証 + 多通貨両側検証を行うこと。単発観察での「正常」判定は禁止（Pixel API は条件によって稀に shop currency を返すことがある）。
