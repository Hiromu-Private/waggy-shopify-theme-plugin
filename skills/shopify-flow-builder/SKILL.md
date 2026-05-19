---
name: shopify-flow-builder
description: Shopify Flow（Order paid / Order created / Customer created などのトリガーを起点とした、顧客メタフィールド更新・顧客タグ付与・Discount コード検知などのワークフロー）をゼロから構築するためのベストプラクティス・パターン集・.flow JSON テンプレート集。Use this skill whenever a user mentions Shopify Flow 作成, ワークフロー自動化, Order paid トリガー, Order created トリガー, customer metafield 自動更新, 顧客タグ自動付与, クーポン配布自動化, Thanks Coupon, ロイヤルティポイント付与, Discount code 使用検知, Run Code action, Shopify Flow テンプレート, .flow ファイル, Flow エクスポート, あるいは具体的に「注文時に〇〇を更新する Flow」「特定タグの注文に〇〇する Flow」「金額帯に応じて顧客 MF に値を書き込む Flow」「クーポン使用時に〇〇をクリアする Flow」「リピート購入で自動的にタグを付ける Flow」などの依頼が出た時。Shopify Flow を Visual Builder でゼロから構築するあらゆる場面で発火させる。.flow JSON のインポート・エクスポート・バージョン管理の話題でも必ず発火させる。
---

# Shopify Flow Builder

Shopify Flow を Visual Builder でゼロから構築するための実践ガイド。トリガー選択、Run Code を中心軸とした判定ロジック、アクション連携、`.flow` JSON エクスポートによる Git 管理までを一貫したパターンで提供する。

## このスキルが解く問題

Shopify Flow Visual Builder で実際にワークフローを組む時、初心者がぶつかる典型的な詰まり所:

1. **5階層の if-else が UI 上で煩雑** — Condition ノードを5階層ネストすると視認性が壊滅。Run Code に集約すべきだが、その判断基準と移行方法が分からない
2. **`order.currentSubtotalPriceSet.shopMoney.amount` が文字列で比較できない** — GraphQL Decimal 型が文字列で渡されるため、Flow UI の数値比較が動かない。`parseFloat()` を入れる場所が分からない
3. **`order.lineItems` の中に特定タグの商品が含まれるか** — 配列の中身を判定する標準的な書き方が UI に無い
4. **既存テンプレートからの派生方法** — Browse templates の使い方とコピー後の編集ポイントが不明
5. **`.flow` ファイルを Git で管理する方法** — Export 機能の存在に気付かず、毎回手動再構築

このスキルは **Run Code アクションを中心軸とした構築パターン** と **`.flow` JSON テンプレート** を提供し、上記すべてを解決する。

## 3 レイヤー構造（Flow の核心）

| 層 | 役割 | 例 |
|---|---|---|
| **Trigger** | ワークフロー開始イベント | Order paid / Order created / Customer created など |
| **Run Code + Condition** | 判定ロジック（Furniture 判定、金額帯、コード照合 等） | JS で計算 → Boolean 出力 → Condition で True 分岐 |
| **Action** | 副作用実行 | Update / Remove customer metafield, Add customer tag, Send email |

**重要:** Condition だけで複雑な判定を組むのではなく、Run Code に集約してから単純な Condition で True/False 分岐するのが本スキルの基本指針。

## Run Code の3要素（必ずセット）

Run Code アクションは3つのエディタを持つ:

1. **Input GraphQL** (`前のステップから入力を選択`): Trigger オブジェクトから必要なフィールドを取得
2. **JavaScript Code** (`コードを記述`): 入力を加工・判定し、Output を返す
3. **Output SDL** (`出力を定義`): 後段ノードが参照する変数の型定義

これらは依存関係があり、`Input` で取得しないフィールドは JS から見えない。`Output SDL` で宣言しないフィールドは後段の Condition / Action から参照できない。3つを必ずセットで設計する。

## 構築の流れ（標準フロー）

新規 Flow を作る時の手順は常にこの順序を守る。各ステップの詳細は references/ 内のドキュメントを参照:

1. **テンプレートライブラリを先に見る** — Admin > Flow > "テンプレートを見る" で類似ユースケース（カテゴリ: customers / loyalty / orders / promotions / custom_data）を確認。9割のケースで類似テンプレが存在し、コピー → 編集の方が速い
2. **トリガー選択** — どのイベントで発火させるか決める。詳細は [references/triggers.md](references/triggers.md)
3. **Run Code を直後に配置** — 判定ロジック・データ整形を1つの JS にまとめる。書き方のパターンは [references/run-code-patterns.md](references/run-code-patterns.md)
4. **Condition で Run Code の出力を判定** — 通常は `runCode.eligible == true` のような単純な Boolean 比較
5. **Action 追加** — Update / Remove customer metafield、Add customer tag など。詳細は [references/customer-metafield-actions.md](references/customer-metafield-actions.md)
6. **ワークフロー名を設定** — `その他のアクション` > `名前を変更`。命名規則は「機能名 — 動詞」（例: `Thanks Coupon — Grant`）
7. **OFF（下書き）状態で保存** — 絶対に「ワークフローをオンにする」は押さない。テスト合格まで OFF を厳守
8. **`.flow` Export してリポに保存** — Single Source of Truth として Git 管理。詳細は [references/flow-export-versioning.md](references/flow-export-versioning.md)
9. **テスト（テストイベントを選択 → 過去注文で dry-run）→ 本番 ON 切替**

## 推奨ワークフローパターン

本スキルがカバーする代表的なパターンと、それに対応するテンプレート:

### パターン A: Order paid → 顧客 MF 更新

「注文の支払い完了時に、注文内容を判定して顧客メタフィールドに値を書き込む」

- 例: 累積購入額に応じた VIP ランク、Furniture 購入特典クーポン金額、最終購入日記録
- テンプレート: [templates/order-paid-to-customer-mf.flow](templates/order-paid-to-customer-mf.flow)
- このパターンの詳細は [references/run-code-patterns.md](references/run-code-patterns.md) §A 参照

### パターン B: Order created → Discount code 検知 → 顧客 MF クリア

「特定のクーポンコードを使った注文が作成された時、関連する顧客メタフィールドをクリアして再利用を防ぐ」

- 例: Thanks Coupon の使用済み判定、ワンタイムコードのトラッキング
- テンプレート: [templates/order-created-discount-clear-mf.flow](templates/order-created-discount-clear-mf.flow)
- 詳細は [references/run-code-patterns.md](references/run-code-patterns.md) §B 参照

### パターン C: Order paid → 顧客タグ付与

「注文条件を満たす顧客に、自動的にタグを付与する」

- 例: 「3回以上購入」「特定カテゴリ購入者」などのセグメント自動分類
- 実装: パターン A の Update customer metafield を Add customer tag アクションに置き換える
- 詳細は [references/customer-metafield-actions.md](references/customer-metafield-actions.md) §タグアクション 参照

### パターン D: Customer created → 初期値書き込み

「新規顧客作成時に、顧客メタフィールドの初期値や welcome メール送信」

- Trigger を `Customer created` に変更すれば、パターン A と同じ構造で書ける

## ベストプラクティスの核

| 観点 | 推奨 | 避けるべき |
|---|---|---|
| **判定ロジック集約** | Run Code に1つの JS で書く | Condition を5階層ネスト |
| **Decimal 型比較** | Run Code 内で `parseFloat()` してから比較 | Flow UI で文字列のまま `<` 比較 |
| **配列の中身判定** | Run Code で `array.some()` | UI の "For each" ループのみで集約 |
| **大文字小文字** | Run Code 内で `.toUpperCase()` 正規化 | 元の値で `==` 比較 |
| **ゲスト注文除外** | Run Code 先頭で `customer.id` 存在チェック → eligible: false 返却 | Action 側でエラー任せ |
| **保存状態** | 必ず OFF（下書き）で保存 | テスト未済で ON にする |
| **バージョン管理** | `.flow` Export → リポに commit | Admin UI のみで管理 |
| **デプロイ順序** | クリア系 Flow を先に ON → 付与系を後に ON | 付与系を先に ON すると即時クリア無しで MF が貯まる |

詳細は [references/anti-patterns.md](references/anti-patterns.md) を参照。

## `.flow` Export / Import によるバージョン管理

Shopify Flow は **Export / Import に標準対応** している。これを使うと:

- リポに `.flow` JSON をコミットしてバージョン管理できる
- 別ストアに同じ Flow を一発で展開できる
- Run Code の JS が JSON 内に含まれるため、テキスト diff が取れる

`.flow` ファイルは `その他のアクション > エクスポート` でダウンロード。中身は `<hash>:{"__metadata":..., "root":{"steps":[...], "links":[...]}}` の形式。詳細は [references/flow-export-versioning.md](references/flow-export-versioning.md)。

**運用パターン:** リポに `docs/flows/<flow-name>.flow` と `<flow-name>.runcode.js`（読みやすさ用の JS 単体ファイル）を並べて保存。Run Code を変更する時は JS 単体ファイルを正として更新 → Admin に貼り付け → 再エクスポート、の流れ。

## ファイル構成

このスキルは以下の構成:

```
shopify-flow-builder/
├── SKILL.md                                       (本ファイル: 構築の流れと全体方針)
├── references/
│   ├── triggers.md                                (Trigger 一覧と GraphQL スキーマ)
│   ├── run-code-patterns.md                       (Run Code の JS / GraphQL / SDL パターン集)
│   ├── customer-metafield-actions.md              (Update/Remove MF アクションと Customer Tag アクション)
│   ├── flow-export-versioning.md                  (Export/Import と Git 管理戦略)
│   └── anti-patterns.md                           (避けるべき設計と理由)
└── templates/
    ├── order-paid-to-customer-mf.flow             (Order paid → MF更新の雛形)
    └── order-created-discount-clear-mf.flow       (Order created → MFクリアの雛形)
```

## 初動の指針

ユーザーから「〇〇を自動化する Flow を作りたい」と相談されたら、まず以下を順に確認:

1. **トリガーは何か？** — Order paid / Order created / Customer created など。複数候補がある場合は references/triggers.md で発火条件を確認
2. **どんな条件で発火するか？** — line_items タグ、金額、Discount コードの有無、顧客タグなど
3. **何を変更するか？** — 顧客 MF 更新 / 顧客タグ付与 / メール送信 / 商品タグ更新など
4. **テンプレートに類似があるか？** — Admin > Flow > "テンプレートを見る" で `loyalty` / `customers` / `orders` カテゴリを覗いて類似 Flow を確認

その後、本スキルの「構築の流れ」§ に沿って組み上げる。判断に迷ったら references/ の該当ドキュメントを参照する。
