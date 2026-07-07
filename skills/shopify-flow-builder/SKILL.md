---
name: shopify-flow-builder
description: Shopify Flow のワークフローをゼロから構築するためのベストプラクティス・パターン・構造テンプレート集。.flow ファイルの Export / Import・Git 管理も対象。使用タイミング：Shopify Flow・Flow 自動化・ワークフロー自動化・.flow ファイル、Order paid / Order created / Customer created トリガー、Scheduled time トリガー・定期実行・バッチ処理、顧客メタフィールド自動更新、顧客・商品タグ自動付与、クーポン・割引コード（Discount code）使用検知、販売開始日で自動公開・リリース日のチャネル自動公開（Meta・Google & YouTube）、在庫切れ自動アーカイブ、Run Code / Get list / Publish product アクション、あるいは「注文時に〇〇する Flow」「リリース日が来たら自動公開する Flow」等の具体的依頼。Flow 構築・.flow JSON のバージョン管理のあらゆる場面で発火させる。
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
| **Trigger** | ワークフロー開始イベント | Order paid / Order created / Customer created / Scheduled time など |
| **Run Code + Condition** *(Plus)* または **Get list + For Each + Condition** *(Basic)* | 判定ロジック・対象列挙 | Plus: JS で計算 → Boolean 出力 → Condition で True 分岐<br>Basic: Get list で対象列挙 → For Each 内で Condition 分岐 |
| **Action** | 副作用実行 | Update / Remove customer metafield, Add customer / product tag, Publish / Unpublish product, Update product status, Send email |

**重要:**
- **Order 系トリガー + 1 商品の判定** が必要なケース → Condition ネストを避け Run Code に集約（Shopify Plus）
- **Scheduled time + 複数商品/顧客のバッチ処理** が必要なケース → Get list + For Each + 標準 Condition（Shopify Basic でも動く）

Run Code を持たないプラン（Basic）でも、Scheduled time + 完了マーカータグ方式で大半のバッチ自動化は実現できる。詳細は [references/scheduled-time-trigger.md](references/scheduled-time-trigger.md) 参照。

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

### パターン E: Scheduled time → Get product list → チャネル自動公開（Basic プラン対応）

「販売開始日（メタフィールド）を過ぎた商品を、複数 Sales channel に自動公開する」

- 例: `custom.release_date` を過ぎた商品を Meta / Google / Online Store に自動公開
- Run Code を使わないため **Shopify Basic プランで動作**
- 完了マーカータグ方式により、片側失敗時も次回 cron で自動リトライ
- 構造ドキュメント: [templates/scheduled-channel-auto-publish.md](templates/scheduled-channel-auto-publish.md)
- このパターンの詳細は [references/scheduled-time-trigger.md](references/scheduled-time-trigger.md) および [references/product-channel-publish-actions.md](references/product-channel-publish-actions.md) 参照

### パターン F: Scheduled time → 在庫切れ・期間経過の自動アーカイブ / タグ剥奪

「在庫 0 が N 日続いた商品の自動アーカイブ」「入荷から 30 日経過した商品から `new` タグ自動剥奪」など、定期バッチ系の自動化全般。

- 構造はパターン E と同じ（Get product list → For Each → Condition → Action）
- アクションを `Publish` から `Update product status: ARCHIVED` / `Remove product tags: new` 等に置き換える
- 詳細は [references/scheduled-time-trigger.md](references/scheduled-time-trigger.md) §このトリガーが向いているユースケース 参照

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
│   ├── scheduled-time-trigger.md                  (Scheduled time + Get list バッチパターン)
│   ├── run-code-patterns.md                       (Run Code の JS / GraphQL / SDL パターン集)
│   ├── customer-metafield-actions.md              (Update/Remove MF アクションと Customer Tag アクション)
│   ├── product-channel-publish-actions.md         (Publish/Unpublish product, Add/Remove product tags, Update status)
│   ├── flow-export-versioning.md                  (Export/Import と Git 管理戦略)
│   └── anti-patterns.md                           (避けるべき設計と理由)
└── templates/
    ├── order-paid-to-customer-mf.flow             (Order paid → MF更新の雛形)
    ├── order-created-discount-clear-mf.flow       (Order created → MFクリアの雛形)
    └── scheduled-channel-auto-publish.md          (Scheduled time → チャネル自動公開の構造ドキュメント)
```

## 初動の指針

ユーザーから「〇〇を自動化する Flow を作りたい」と相談されたら、まず以下を順に確認:

1. **トリガーは何か？** — Order paid / Order created / Customer created / **Scheduled time** など。複数候補がある場合は [references/triggers.md](references/triggers.md) と [references/scheduled-time-trigger.md](references/scheduled-time-trigger.md) で発火条件を確認
2. **どんな条件で発火するか？** — line_items タグ、金額、Discount コードの有無、顧客タグ、メタフィールドの値、現在時刻との比較など
3. **何を変更するか？** — 顧客 MF 更新 / 顧客タグ付与 / 商品タグ付与 / 商品の Publish / Unpublish / 商品ステータス更新 / メール送信など
4. **対象は1リソースか複数か？** — 1 リソース（Order トリガーで該当注文 1 件）→ Run Code 中心 / 複数（Scheduled time で条件に合う商品をすべて）→ Get list + For Each
5. **プラン制約は？** — Shopify Basic は Run Code 不可。Scheduled time + 標準アクションで組む
6. **テンプレートに類似があるか？** — Admin > Flow > "テンプレートを見る" で類似 Flow を確認、または本スキルの templates/ を確認

その後、本スキルの「構築の流れ」§ に沿って組み上げる。判断に迷ったら references/ の該当ドキュメントを参照する。
