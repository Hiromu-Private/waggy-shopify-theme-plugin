# テンプレート: Scheduled Channel Auto Publish

「販売開始日（メタフィールド）を過ぎた商品を、複数 Sales channel に自動公開する」Flow の **構造ドキュメント**。`.flow` JSON は SHA256 ハッシュの検証があるため外部生成は不安定。本テンプレートは **Admin UI で構築するためのステップ定義** として提供する。実装後、Admin からエクスポートした `.flow` ファイルをこの隣に保存して Git 管理することを推奨。

## このテンプレートが解く問題

- 販売開始日（`custom.release_date` メタフィールド）を超えた商品を、毎時自動で複数 Sales channel に公開したい
- Meta / Google / Online Store 等、複数チャネルへの公開を **チャネルごと独立** に管理したい
- 失敗時に自動リトライしたい（次回 cron で再処理）
- Shopify Basic プラン（Run Code 不可）でも動く構成にしたい

## 適用範囲

| 項目 | 値 |
|---|---|
| 対応プラン | Shopify Basic 以上（Plus 不要） |
| 利用アクション | 標準アクションのみ（Run Code 不使用） |
| 判定メタフィールド | 任意の date_time 型メタフィールド |
| 公開先チャネル | 1〜N 個（Meta / Google / Online Store / Shop / POS 等） |
| 完了マーカー | チャネルごと独立タグ |

## 全体構造

```
[ Scheduled time trigger ]
   schedule: 0 * * * *           （1時間ごと）
            │
            ▼
[ Get product list ]
   query: metafields.<ns>.<key>:<=NOW
          AND (NOT tag:"<MARKER_1>" OR NOT tag:"<MARKER_2>" ...)
   first: 50, sortKey: UPDATED_AT, reverse: true
            │
            ▼
[ For Each productList.products ]
            │
            ├── [ Branch 1: Meta ]
            │     If NOT (product.tags contains "<MARKER_1>")
            │     → Publish product to Publication 1
            │     → Add product tags "<MARKER_1>"
            │
            ├── [ Branch 2: Google ]
            │     If NOT (product.tags contains "<MARKER_2>")
            │     → Publish product to Publication 2
            │     → Add product tags "<MARKER_2>"
            │
            └── [ Branch N: ... ]
                  （必要なチャネル数だけ複製）
```

## ステップ詳細

### Step 1: Trigger — Scheduled time

| 項目 | 値 |
|---|---|
| Trigger type | Scheduled time |
| Schedule (cron) | `0 * * * *`（毎時 0 分） |
| Timezone | ストアの timezone（既定で問題なし） |

調整指針:
- リアルタイム性重視 → 1 時間以下（最短 5 分 `*/5 * * * *`）
- 軽量処理で十分 → 1 日 1 回（例: `0 6 * * *` = 毎日 6:00）

### Step 2: Get product list

| 引数 | 値 | 備考 |
|---|---|---|
| query | `metafields.<NS>.<KEY>:<={{scheduledAt \| date: "%Y-%m-%dT%H:%M:%SZ"}} AND (NOT tag:"<MARKER_1>" OR NOT tag:"<MARKER_2>")` | フォールバック: `metafield:` 表記。詳細は [../references/scheduled-time-trigger.md](../references/scheduled-time-trigger.md) |
| first | `50` | 上限調整可。最大 250 |
| sortKey | `UPDATED_AT` | |
| reverse | `true` | 直近編集を優先 |

複数チャネル分の `NOT tag:` を OR で繋ぐことで、**いずれか1つでも未公開のものを対象に含める**。

### Step 3: For Each `productList.products`

Flow 標準の For Each ノード。各 iteration 内では `product` が当該商品を指す。

### Step 4〜N: チャネルごとのブランチ

各チャネル分、以下の 3 ノードを並列に配置:

#### Step X-a: Condition

| 項目 | 値 |
|---|---|
| 条件 | `product.tags` does not contain `<MARKER_X>` |

#### Step X-b: Publish product

| 項目 | 値 |
|---|---|
| Product | `{{product}}` |
| Publication | `gid://shopify/Publication/<ID>` |

Publication ID は事前取得（[../references/product-channel-publish-actions.md](../references/product-channel-publish-actions.md) §Publication ID 取得）。

#### Step X-c: Add product tags

| 項目 | 値 |
|---|---|
| Product | `{{product}}` |
| Tags | `<MARKER_X>` |

**順序厳守**: Publish → Add tag。逆順だと失敗時に自動リトライが効かない（アンチパターン）。

## カスタマイズポイント

| 変更したい箇所 | 編集対象 |
|---|---|
| 判定メタフィールド | Step 2 の query の `metafields.<ns>.<key>` |
| 完了マーカータグ名 | Step 2 の query の `NOT tag:"..."` および Step X-a / X-c の値 |
| 公開先チャネル数 | ブランチ（Step X-a/b/c のセット）を複製 |
| Publication ID | Step X-b の値 |
| 実行頻度 | Step 1 の cron |
| 1 回の処理件数 | Step 2 の `first` |

## 設定パラメータの実例（複数チャネル公開シナリオ）

例: Meta + Google の 2 チャネル公開で、メタフィールド `custom.release_date` を判定に使う場合:

| プレースホルダ | 実値 |
|---|---|
| `<NS>` | `custom` |
| `<KEY>` | `release_date` |
| `<MARKER_1>` | `meta公開` |
| `<MARKER_2>` | `google公開` |
| `<Publication_1>` | `gid://shopify/Publication/<META_ID>` |
| `<Publication_2>` | `gid://shopify/Publication/<GOOGLE_ID>` |

Step 2 query の最終形:
```
metafields.custom.release_date:<={{scheduledAt | date: "%Y-%m-%dT%H:%M:%SZ"}} AND (NOT tag:"meta公開" OR NOT tag:"google公開")
```

## 前提リソース（実装前チェックリスト）

- [ ] 判定メタフィールド定義が存在する（type: date_time, **Admin filtering: ON**）
- [ ] 対象 Sales channel アプリがすべてインストール・接続済み
- [ ] 各 Publication ID を取得済み（テキストファイル等に控えてある）
- [ ] Shopify Flow アプリがインストール済み（Admin > Apps）
- [ ] 完了マーカータグ名と既存タグの重複なし（Admin > Products > Filters で確認）
- [ ] テスト商品 2 件を準備（過去 release_date / 未来 release_date）

## テスト計画

### 7.1 事前準備

テスト商品を 2 件作成:
- **商品 A**: `<KEY>` = 現在より 1 時間前 / マーカータグなし / 全 Publication 未公開
- **商品 B**: `<KEY>` = 翌日 09:00 / マーカータグなし / 全 Publication 未公開

### 7.2 検証手順

1. Flow を Draft 状態で保存（**絶対に ON にしない**）
2. Flow 詳細画面の `Run workflow` ボタンで即時実行
3. Run history で全ステップが Success か確認
4. 検証項目:
   - [ ] 商品 A の Sales channels に対象全 Publication がアクティブで表示
   - [ ] 商品 A のタグに全マーカーが付与
   - [ ] 商品 B は変化なし（チャネル未公開・タグなし）
5. 再実行テスト: もう一度 Run workflow → 商品 A に変化なし（重複防止の確認）
6. 片側テスト: 商品 A から `<MARKER_1>` だけ手動削除 → Run workflow → そのチャネルだけ再公開・マーカー復活、他は no-op

### 7.3 本番化判断

- 上記すべて OK + Run history にエラーなし → Flow を ON に切替
- 本番化直後、最初の自動実行（翌時 00 分）の Run history を必ず確認

## 運用ルール

| シナリオ | 対応 |
|---|---|
| 商品の再公開停止 | 該当チャネルから unpublish 後、対応マーカータグを削除する（タグを残すと再公開されない） |
| 販売開始日の延期 | `<KEY>` を未来日時に更新（マーカー未付与なら次回該当時刻に再判定） |
| Flow の一時停止 | Flow 詳細画面で OFF |
| Publication 変更（チャネル ID 変更） | Publication ID を再取得し、Publish product アクションを修正 |
| マーカー命名の変更 | 既存タグの一括 rename が必要。Bulk editor or 別 Flow で対応 |

## エクスポートと Git 管理

実装完了後:

1. Admin > Flow > 該当 Flow > その他のアクション > **エクスポート** で `.flow` ダウンロード
2. ファイルを kebab-case にリネーム（例: `scheduled-channel-auto-publish.flow`）
3. リポにコミット（Store 固有の Publication ID が含まれるため、**ストア専用リポ**へ）
4. このスキルの templates/ に汎用テンプレを保存する場合は、Publication ID をプレースホルダ `<META_ID>` 等に置換してからコミット

詳細は [../references/flow-export-versioning.md](../references/flow-export-versioning.md) 参照。

## 関連リファレンス

- Scheduled time トリガー詳細: [../references/scheduled-time-trigger.md](../references/scheduled-time-trigger.md)
- 商品系アクション詳細: [../references/product-channel-publish-actions.md](../references/product-channel-publish-actions.md)
- アンチパターン: [../references/anti-patterns.md](../references/anti-patterns.md)
- Flow Export / Import: [../references/flow-export-versioning.md](../references/flow-export-versioning.md)
