# shopify-blog-publish 初回セットアップガイド

チームメンバーが自分の PC からブログ公開を実行できるようにするための手順。所要 30 分程度。一度セットアップすれば、以後は Claude Code で「ブログを公開して」と言うだけでよい。

## 必要な権限（チーム管理者に依頼するもの）

| 権限 | 用途 |
|---|---|
| Shopify ストアのスタッフ or コラボレーターアカウント（ブログ記事の読み書き + ファイルアップロード） | 記事の作成・公開 |
| ブログ素材 Drive フォルダの閲覧権限（Google アカウントに共有） | 原稿・設定の取得 |
| ブログ素材フォルダの URL | 初回の config 取得先 |

## 1. Claude Code

インストール済みでなければ https://claude.com/claude-code の手順でインストールし、ログインする。

## 2. この plugin のインストール

Claude Code のチャットで:

```
/plugin marketplace add <marketplaceのGitHubリポ>
/plugin install shopify-theme-dev@waggy-shopify-theme-plugin
```

※ すでにインストール済みなら `/plugin marketplace update waggy-shopify-theme-plugin` で最新化。

## 3. Shopify CLI

```bash
npm install -g @shopify/cli@latest
shopify version   # v4系であること
```

認証（対話ログインが Claude Code 内で失敗する場合は /shopify-cli-auth スキルの expect スクリプトを使う）:

```bash
shopify store auth --store <ストアドメイン> --scopes read_content,write_content,write_files
```

## 4. gog CLI（Google Drive アクセス）

```bash
# インストール（未導入の場合）
brew install gog   # または配布元の手順に従う
gog auth add <自分のGoogleアカウント> --services drive
gog auth list --check   # OK であること
```

## 5. Playwright（KV 自動生成に使用）

Playwright MCP か playwright-cli のどちらかが動けばよい。Claude Code に Playwright MCP が設定済みならそのままでよい。

## 6. 動作確認

Claude Code で「ブログ公開の前提チェックをして」と依頼する。スキルが Step 0（config ロード）を実行し、初回はブログ素材フォルダの URL を聞いてくるので、共有された URL を貼る。「前提チェック OK」まで確認できたらセットアップ完了。

## うまくいかないとき

- Shopify の認証エラー → /shopify-cli-auth スキル（アカウント取り違えが最頻出）
- Drive が読めない → 共有権限が自分の Google アカウントに付いているか確認
- どうしても詰まったら、セットアップした管理者に相談
