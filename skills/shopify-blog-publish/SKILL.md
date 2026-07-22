---
name: shopify-blog-publish
description: Google Drive に置かれたブログ原稿を、Shopify ストアのブログ記事として変換・サムネイル生成・公開まで一気通貫で行う。原稿ダウンロード → 編集ルールに沿った本文HTML変換（要点ボックス・FAQ構造化データ・メタデータ）→ KVサムネイル（Driveにあれば使用、なければテンプレートから自動生成）→ Shopify Files 登録 → 記事公開 → 相互内部リンク → ストアフロント検証まで自動実行する。即時公開だけでなく予約公開（スケジュール投稿）にも対応し、config に chatShare がある場合は社内チャット共有文の生成と予約投稿シートへの登録まで行う。ストア固有の設定は Drive の `_publish-config/` フォルダから取得するため、スキル自体は汎用。使用タイミング：「ブログを公開して」「ブログをアップして」「新しい記事が上がった」「blog publish」「記事を公開して」「コラムを公開」「◯日に公開できるように登録して」「予約投稿して」、または Drive 上のブログ原稿を Shopify に反映するあらゆる場面。
---

# Shopify Blog Publish

Drive の原稿フォルダから Shopify ブログ記事の公開までをワンショットで行う。実行者は原稿がアップされた後にこのスキルを発動するだけでよい。

## 前提

| 要件 | 確認方法 |
|---|---|
| Shopify CLI（v4）+ 対象ストアへの認証 | `shopify store auth --scopes read_content,write_content,write_files` 済み。未認証なら /shopify-cli-auth |
| gog CLI + Google アカウント認証 | `gog auth list --check`。対象 Drive フォルダへのアクセス権が必要 |
| Playwright（KV 自動生成時のみ） | Playwright MCP または playwright-cli のどちらか |
| 初回のみ: ブログ素材フォルダの URL | チーム管理者から共有される（配下に `_publish-config/` があるフォルダ） |

初回セットアップの詳細は [references/setup-guide.md](references/setup-guide.md)。

## Step 0: 前提チェック & config ロード

1. ローカルキャッシュ `~/.config/shopify-blog-publish/` を確認。`<store>/config.json` があれば読み込む
2. **キャッシュがない場合（初回）**: 実行者に「ブログ素材フォルダの URL」を聞く → URL からフォルダ ID を取り出し、`gog drive ls --parent <folderId>` で `_publish-config/` を探す → その中のファイルをすべてダウンロードし（`config.json` / `editorial-rules.md` / `kv-template.html` / `assets/*` のほか、config が参照する追加ファイルも含む）、`~/.config/shopify-blog-publish/<store>/` へ保存（素材フォルダ ID も `source-folder.txt` として保存）
3. `shopify store auth --store <config.store>` の認証状態とスコープを確認（`read_content, write_content, write_files` が必要）。GraphQL 実行が通るかは Step 1 のクエリ自体で確認する
4. `editorial-rules.md` を**必ず全文読む**。以降の変換・編集判断はすべてこのルールに従う

> config の値と Drive 正本が乖離している可能性に注意。公開結果がおかしい場合はキャッシュを削除して再取得する。

## Step 1: 対象記事の特定

1. `gog drive ls --parent <素材フォルダID>` で記事フォルダを列挙（`_publish-config` は除外）
2. ブログの既存記事（handle・タイトル）を取得:
   ```bash
   shopify store execute --store <store> --query '
   query { articles(first: 50, sortKey: ID, reverse: true) {
     nodes { id title handle isPublished createdAt templateSuffix tags } } }'
   ```
3. フォルダ名と既存記事タイトルを突き合わせ、**未公開の記事フォルダ**を特定する。ユーザーが記事名を指定していればそれを優先
4. 対象フォルダの中身を `gog drive ls` し、原稿ドキュメントと画像素材（KV・図版）の有無を把握する

## Step 2: 重複ガード（唯一の停止点）

直近作成の記事（下書き含む）に、対象原稿とタイトルが類似するものがないか確認する。**類似の下書きが見つかったら、そこで停止してユーザーに報告する**（別の担当者が並行して同じ記事を作成している可能性がある。その下書きに統合するか、破棄するかは人間の判断）。

## Step 3: 本文変換

1. 原稿を `gog drive download <fileId> --format txt` でダウンロードして全文読む
2. `editorial-rules.md` の全ルールに従って本文 HTML を組み立てる。要点: h1/style 禁止・h2 から・章番号は書かない・要点ボックス1〜3個・文中列挙は素の ul/ol・図版は高解像度版・FAQPage JSON-LD を末尾に・strong は核心フレーズのみ
3. メタデータを作成: title（プレフィックス除去）/ handle（英語スラッグ）/ summary / description_tag / tags / templateSuffix（書式は editorial-rules.md セクション5）
4. FAQ JSON-LD は投入前に必ず JSON パースして妥当性を検証する

## Step 4: 内部リンク選定

Step 1 で取得した公開記事一覧から、内容が本当に関連する2本を選び、本文末尾（JSON-LD の直前）に「関連コラム」段落を追加する（形式は editorial-rules.md セクション4）。逆リンクは Step 7 で張る。

## Step 5: KV サムネイル

- **記事フォルダに規格サイズの PNG（config.kv の width×height）があればそれを使用**。ダウンロードして寸法を検証する
- **なければテンプレートから自動生成**: 手順は [references/kv-generation.md](references/kv-generation.md)。生成した PNG は `gog drive upload --parent <記事フォルダID>` で **Drive の記事フォルダへ原本として保存**する（ファイル名は config.kv.filenamePattern の {slug} を handle 由来の短縮スラッグで置換）

## Step 6: 公開

1. **staged upload**: `stagedUploadsCreate`（resource: FILE, mimeType: image/png, httpMethod: POST）→ curl で multipart POST（201 を確認）
2. **fileCreate** で Files 登録 → `fileStatus` が READY になるまでポーリングして CDN URL を取得
3. **articleCreate** で本文・メタデータ・KV（image.url + altText=タイトル）・`isPublished: true` を一括投入。`userErrors` が空であることを必ず確認
4. 具体的な GraphQL は [references/graphql-recipes.md](references/graphql-recipes.md) を使う（実運用で検証済みの形）

### 予約公開（スケジュール投稿）にする場合

ユーザーが「◯日に公開」「予約投稿」を指定した場合は、手順 3 を次のように変える:

- **`isPublished: true` と未来の `publishDate` は同時指定不可**（userErrors になる）。予約は **`isPublished: false` ＋ 未来の `publishDate`（UTC）** で articleCreate する
- 作成後 `article { isPublished publishedAt }` を取得し、`isPublished: false` かつ `publishedAt` が指定の未来日時で返ればスケジュール済み（時刻到達で自動公開される）
- ストアフロントは公開時刻まで 404 が正常。**Step 7 の逆リンクと Step 8 のストアフロント検証は公開後に実施する**（公開前に逆リンクを張ると 404 リンクになる）。公開後の残タスクとして実行者側のタスク管理に必ず記録すること

## Step 6b: 社内チャット共有の予約（config.chatShare がある場合のみ）

config.json に `chatShare` セクションがあるストアでは、記事の公開（予約公開を含む）と同じ作業の中で、社内チャットへの共有文の予約投稿まで行う。`chatShare` が無ければこの Step はスキップ。

1. `_publish-config/` の `chatShare.formatFile` を読み、そのテンプレートと生成ルールに従って共有文を作る
2. 共有文を formatFile の指示する保存先へ Markdown で保存する（送信前に人間がレビュー・手動送信できる状態を保つ）
3. 予約投稿シート（`chatShare.sheetId` の `chatShare.sheetTab` タブ）へ行を追加する:
   - **A列データ最終行の次の行**に `gog sheets update` で書き込む（**append は使わない** — ルームID解決列の数式が下の行まで敷かれており、append だと位置がズレる）
   - A=公開日＋`chatShare.sendTime`、B=`chatShare.roomName`、C=共有文。**送信時刻は必ず記事の公開時刻より後にする**（公開前に送ると共有URLが404になる）
   - シートへのアクセスに専用アカウントが要る場合は `chatShare.sheetAccount` を使う
4. 書き込み後、ルームID解決列（VLOOKUP）が数値のIDになっていることを確認する。`#N/A` の場合は roomName が `chatShare.mappingTab` に未登録 → 対応表へ追加してから再確認

## Step 7: 逆リンク

Step 4 で選んだ2記事それぞれについて:
1. 現在の body を取得し、**バックアップ JSON として Drive の新記事フォルダへアップロード**（`article_<id>_<日付>_prelink.json`）
2. 本文末尾（既存の関連コラム段落の後・JSON-LD の直前）に新記事へのリンク段落を挿入して articleUpdate
3. 挿入前に「リンクがまだ存在しないこと」「JSON-LD マーカーが1つだけであること」をコードで assert する

## Step 8: ストアフロント検証

公開ドメイン（config.publicDomain）で以下を curl 検証し、すべて OK であることを確認する:

- 記事 URL（`https://<publicDomain>/blogs/<blogHandle>/<handle>`）が HTTP 200
- タイトル・要点ボックス・FAQPage JSON-LD・description_tag が HTML に含まれる
- og:image が新 KV を指している
- ブログ一覧ページに新記事が表示されている
- 逆リンク2記事に新記事への言及がある

## Step 9: 完了報告

```
✓ 公開しました: https://<publicDomain>/blogs/<blogHandle>/<handle>
- 記事ID / handle / タイトル
- KV: 使用した画像（既存 or 自動生成）と Drive 保存先
- 内部リンク: 新記事→2本 / 逆リンク2本→新記事
- 検証結果: Step 8 のチェックリスト
- バックアップ: Drive 記事フォルダ内の prelink JSON
```

予約公開の場合は「公開しました」の代わりに公開予定日時（とスケジュール済みであることの確認結果）を報告し、公開後に残る作業（逆リンク・検証）をタスクとして明記する。chatShare を実行した場合は予約行の内容（送信日時・ルーム名）も報告に含める。

## ガードレール

| ルール | 理由 |
|---|---|
| `articleDelete` をこのスキルから実行しない | 削除は必ず人間の明示指示で |
| 既存記事の変更は「逆リンク段落の追加」のみ。他の本文改変は禁止 | 公開済みコンテンツの保護 |
| 逆リンク追加前に必ずバックアップを Drive へアップ | ロールバック可能性の確保 |
| `userErrors` が返ったら即中断してユーザーに報告 | 中途半端な状態で続行しない |
| Step 2 の重複検出時は停止 | 並行作業者の下書きを潰さない |
| live テーマのファイルには一切触れない（記事データのみ操作） | テーマ事故防止 |
| チャット共有の予約時刻は記事の公開時刻より後にする | 公開前に送ると共有URLが404になる |
| 予約公開の記事に逆リンクを張るのは公開後 | 公開前に張ると404リンクになる |

## トラブルシューティング

| 症状 | 対処 |
|---|---|
| GraphQL で ACCESS_DENIED | スコープ不足。`shopify store auth --store <store> --scopes read_content,write_content,write_files` で再認証 |
| gog がフォルダを読めない | 実行者の Google アカウントに素材フォルダの閲覧権限がない。管理者に共有を依頼 |
| fileCreate 後 image が null | 処理中。fileStatus が READY になるまで 3 秒間隔でポーリング |
| KV 生成でフォントが崩れる | ネットワーク遮断で Google Fonts が読めていない。オンラインで再実行 |
| config の値が古い | `rm -rf ~/.config/shopify-blog-publish/<store>` して再取得 |

## ファイル構成

```
shopify-blog-publish/
├── SKILL.md                      # このファイル（フロー全体）
└── references/
    ├── setup-guide.md            # 実行者の初回セットアップガイド
    ├── graphql-recipes.md        # 検証済み GraphQL operation 集
    └── kv-generation.md          # KV サムネイル自動生成の詳細手順
```
