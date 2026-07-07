---
name: shopify-cv-tracking
description: "Shopify ストアへの CV 計測タグ・カスタムピクセル実装の実戦ガイド。多通貨（Shopify Markets）の通貨換算、サードパーティアプリ製フォームの会員登録計測、送信値検証の鉄則を収録。使用タイミング：「CV計測」「CVタグ」「コンバージョン計測」「計測タグ」「アドエビス / adebis / AD EBiS」「カスタムピクセル」「Web Pixel」「purchase イベント」「会員登録の計測」「売上が合わない」「計測値がズレる」、Shopify に計測タグを実装・修正・デバッグ・検証するあらゆる場面で使用する。"
---

# Shopify CV Tracking — CV 計測タグ / カスタムピクセル実装

Shopify ストアへの CV（コンバージョン）計測タグ実装を、過去の実事故から抽出したガードレール付きで実行する。**「コードが正しい」と「計測が正しい」は別物。実装 3 割・検証 7 割で臨む**こと。

## 起動時の自動アクション

1. 依頼内容から作業種別を判定: **新規実装**（purchase / 会員登録 / カスタム）か、**既存計測のトラブル調査**（売上が合わない・CV が来ない）か
2. トラブル調査なら「クイック診断」表から当たりを付けて該当 references へ
3. 新規実装なら **Step 1 のチェックリストを完了させてから**コードを書く（ここを飛ばした結果が下記の実事故）

## このスキルが扱う領域

| 計測種別 | 典型イベント | 主な実装先 |
|---------|------------|-----------|
| purchase（購入・売上） | `checkout_completed` | カスタムピクセル（Customer Events API） |
| 会員登録 | register 完了 | テーマ Liquid（+ MutationObserver 方式） |
| カート・回遊系 | `product_added_to_cart` 等 | カスタムピクセル |
| 計測値ズレの調査 | — | 売上乖離の診断法（references 参照） |

計測ツールは adebis（AD EBiS）を主対象とするが、GA4 等の他ツールでも通貨・フォームの罠は共通。

## クイック診断: 「計測値がズレる」と言われたら

既存実装のトラブル調査で呼ばれた場合は、まずここで当たりを付ける:

| 症状 | 最有力の原因 | 参照 |
|------|------------|------|
| 売上が実額より小さく、「実額 / 計測記録」の比率が **1/為替レートに揃っている**（TWD なら約 5 倍） | **通貨ミスマッチ確定**。presentment currency の生値をそのまま送っている | [references/pixel-currency-patterns.md](references/pixel-currency-patterns.md) |
| 売上ズレの比率が**バラついている** | 複数 CV 重複計上・集計仕様の問題など別要因。order_id（adebis なら `ebisOther1`）で逆引き確認 | [references/pixel-currency-patterns.md](references/pixel-currency-patterns.md) |
| 会員登録 CV が異常に少ない / ほぼ 0 件 | フォームがサードパーティアプリ製で Liquid の `{% if customer %}` タグが空振り | [references/third-party-form-cv.md](references/third-party-form-cv.md) |
| 検証中に CV が飛ばない | sessionStorage の発火フラグ残留（新規タブで再試行）、または playwright-cli の Headless 検出で計測ツールがブロック | [references/verification-checklist.md](references/verification-checklist.md) |
| デプロイしたのに挙動が変わらない | push 先テーマ ID の取り違え、または反映遅延（ピクセル URL の `@N` で確認） | [references/verification-checklist.md](references/verification-checklist.md) |

## このスキルが存在する理由（過去の実事故）

| 事故 | 内容 | 原因 |
|------|------|------|
| 売上が 1/為替レート に縮む | 多通貨ストアで adebis の売上記録が実額の約 1/5 になった（CENE 案件 2026-05-25） | Customer Events API は presentment currency（顧客の決済通貨）の生値を返す。TWD の数値をそのまま JP 特化計測タグに送信していた |
| 会員登録 CV が実質 0 件 | 「月 18 件」の計測値は全件が誤計上で、本来の登録は 0 件計上だった（CENE 案件 2026-06-03） | 実フォームがサードパーティアプリ製で、Liquid の `{% if customer %}` タグが構造的に発火しなかった |
| 本番でない場所に push | CV タグを古いテーマ ID の unpublished テーマに push（CENE 案件 2026-06-03） | memory 上の古いテーマ ID を信じ、push 前に Live テーマ ID を確認しなかった |

## Step 1: 実装前チェックリスト（必須）

コードを書く前に以下を確定させる。

### 1-1. 何を計測するか・どこに実装するか

- [ ] 計測種別: purchase / 会員登録 / カスタムイベント
- [ ] 実装先: カスタムピクセル（Customer Events API） / テーマ Liquid
- [ ] カスタムピクセルの場合、sandbox iframe 制約を踏まえる（`allow-same-origin` が無く親 window の `window.Shopify.currency.rate` 等に一切アクセスできない → 詳細は references）

### 1-2. 多通貨ストアか（金額を送るなら必須確認）

- [ ] Shopify Markets で複数通貨を販売しているか確認
- [ ] JPY 以外の通貨が 1 つでもあれば、**通貨換算ヘルパー（toJpy）を必ず通す** → [references/pixel-currency-patterns.md](references/pixel-currency-patterns.md)

### 1-3. サードパーティアプリフォームの有無（会員登録系なら必須確認）

- [ ] `templates/customers/*.json` を読み、メインセクションに **サードパーティアプリブロック（`shopify://apps/...`）** が使われていないか確認
- [ ] 使われていれば、そのアプリの挙動（リダイレクトの有無・完了表示形式）を**実機で 1 回テスト登録して**確認
- [ ] Shopify 標準フロー（register → /account リダイレクト）と違うなら **MutationObserver 方式**に切り替え → [references/third-party-form-cv.md](references/third-party-form-cv.md)
- [ ] 既存タグが空振りしていないか、過去の CV 数が極端に少なくないか計測ツール管理画面（EBiS 等）で確認

## Step 2: 実装パターンへの分岐

| 状況 | 参照 |
|------|------|
| purchase をカスタムピクセルで実装する / 多通貨対応する / 売上乖離を調査する | [references/pixel-currency-patterns.md](references/pixel-currency-patterns.md) |
| 会員登録 CV を実装する / フォームがサードパーティアプリ製 | [references/third-party-form-cv.md](references/third-party-form-cv.md) |
| 実装後の検証・本番反映をする | [references/verification-checklist.md](references/verification-checklist.md) |

### 各 reference の収録内容

**pixel-currency-patterns.md** — カスタムピクセルで金額を扱うなら必読:

- Customer Events API が presentment currency の生値を返す仕様（`MoneyV2` 型でも shop currency に自動換算されない）
- toJpy 換算ヘルパーの完全コード（JPY は ×1 素通し / 未登録通貨は原値返却 / レートは四半期更新）
- Web Pixel sandbox iframe 制約（`allow-same-origin` 無し → 親 window アクセス不可 → レートはハードコード必須）
- ピクセル URL の `@N` バージョン番号によるデプロイ反映確認
- 売上乖離の診断法（比率が 1/為替レートに揃うか否かでの切り分け）

**third-party-form-cv.md** — 会員登録 CV なら必読:

- Bonify / Customer Fields / Helium 等のアプリ製フォームで Liquid の customer 条件タグが空振りする構造
- MutationObserver 方式のコード骨子（完了メッセージ検知 / `input` イベント capture:true でのメールアドレス退避 / sessionStorage 二重発火防止 / `customer.created_at < 600 秒` の保険実装）
- アプリ設定経由の `<script>` 挿入がサニタイズで不可な件

**verification-checklist.md** — 全実装の仕上げに必読:

- 6 パターン検証のチェックボックス
- 多通貨の両側検証（換算が効く + 二重換算しない）
- 本番反映フロー（Live テーマ ID 確認 / `@N` 確認 / テスト顧客削除依頼）

## Step 3: 検証の鉄則（必ず守る）

チェックボックス付きの詳細手順は [references/verification-checklist.md](references/verification-checklist.md)。骨子:

| 鉄則 | 理由 |
|------|------|
| 検証は必ず **Playwright MCP** で行う（playwright-cli 禁止） | playwright-cli は Headless 検出され、adebis 等の商用アドトラッキングがリクエストをブロックする（送信自体が観測できなくなる） |
| ピクセル送信値は**最低 6 パターン**で観察する | 条件によって送信値が変わる。1 パターンの観察では欠陥を見逃す |
| **単発観察での「正常」判定は厳禁** | Shopify Pixel API は条件によって稀に shop currency を返すことがある。1 回だけ JPY 値が来ても「JPY で送信されている」とは判断できない（CENE 案件で実際に誤判断して訂正した経緯あり） |
| 多通貨ストアは **TWD/JPY 両方の環境で検証** | 外貨側で換算が効くこと + JPY 側で誤って為替レートが掛からない（二重換算しない）ことの両方を確認する |
| フォーム CV の検証は**新しいタブ**で行う | sessionStorage の発火フラグが残っていると CV が飛ばず、「実装が壊れている」と誤判定する |

### 最低 6 パターンの内訳

1. クリーン状態（Cookie / storage なし）での初回
2. 同商品の再追加
3. 別商品
4. 数量変更
5. カートクリア後
6. checkout_started まで進める

## Step 4: 本番反映時の注意

| 項目 | 内容 |
|------|------|
| push 先の確認 | **push 前に必ず `shopify theme list --store <store> \| grep live` で最新 Live テーマ ID を確認する**。memory・過去メモのテーマ ID は古い可能性がある（古い ID で unpublished テーマへ push した実事故あり） |
| デプロイ反映確認 | ピクセル URL の `@N` バージョン番号がコード更新時にインクリメントされる。Network タブで @N を見れば反映を確認できる |
| テスト顧客の掃除 | 検証で作成したテスト顧客は本番 DB に残る。Shopify 管理画面 → 顧客管理からの手動削除を必ず依頼する |

## ガードレール（全作業共通）

| ルール | 理由 |
|--------|------|
| 金額系イベントは通貨換算ヘルパーを必ず通す | presentment currency 事故（売上 1/為替レート）の再発防止 |
| 換算レートはハードコード + 四半期更新。値は案件ごとに確認 | sandbox 制約で動的取得は不可能。古いレートの放置も事故のもと |
| 会員登録 CV は実装前に必ずアプリフォーム確認 | Liquid タグ空振り（CV 実質 0 件）事故の再発防止 |
| 単発観察で「正常」と報告しない | Pixel API の揺らぎによる誤判断防止 |
| Live テーマ ID を確認せずに push しない | unpublished テーマへの誤 push 防止 |
| 検証後のテスト顧客削除を依頼する | 本番顧客 DB の汚染防止 |
| ストアドメイン・ID 等の案件識別情報をスキルや汎用ドキュメントに書かない | 機密・顧客情報の流出防止 |

## Reference docs

- **通貨対応・カスタムピクセル実装・売上乖離診断**: [references/pixel-currency-patterns.md](references/pixel-currency-patterns.md)
- **サードパーティアプリフォームの CV 計測**: [references/third-party-form-cv.md](references/third-party-form-cv.md)
- **検証チェックリスト・本番反映フロー**: [references/verification-checklist.md](references/verification-checklist.md)
