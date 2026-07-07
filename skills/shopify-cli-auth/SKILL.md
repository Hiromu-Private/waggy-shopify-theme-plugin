---
name: shopify-cli-auth
description: "Shopify CLI（v4）のアカウント切替・認証トラブル対応・新規ストアの shopify.theme.toml 初期設定を行う実戦ガイド。使用タイミング：「アカウント切り替えて」「auth login」「別のストアに繋ぎたい」「don't have access エラー」「新しいストアをセットアップ」「ストアを固定して」「shopify コマンドが見つからない（command not found）」「Claude Code から shopify にログイン」。CLI v4 は認証をグローバル単一アカウントに集約する（OAuth ログインのみ・App / Admin API トークンは使えない）ため、複数ストアは順番に切り替えて使う。Claude Code 内蔵 Bash は pty を持たず対話ログインが弾かれるので、同梱の expect スクリプトで TTY をエミュレートして突破する。"
---

# Shopify CLI Auth — アカウント切替・認証・ストア固定

Shopify CLI v4 のアカウント運用と認証トラブル対応を、事故（ストア取り違え push・認証アカウント不一致）を避けるガードレール付きで実行する。

## 最重要の前提: CLI v4 はグローバル単一アカウント

**CLI v4 は認証を macOS Keychain の単一エントリに集約する**。プロジェクトごとに別アカウントを「同時に」有効化することはできず、**最後に `shopify auth login` したアカウントが全プロジェクト共通で有効**になる。

- したがって複数ストア（別アカウント配下）は **順番に切り替えて使う**。同時起動はできない
- `XDG_CONFIG_HOME` を切り替えてもアクティブアカウントは分離されない（v4 では無効。かつ gh / brew 等 XDG 準拠ツールの設定パスまで巻き込む副作用があるため、この方式は採用しない）
- どうしても 2 アカウントを同時に動かす必要がある場合、唯一の手段は **macOS ユーザーアカウントを分ける**（各ユーザーが独立 Keychain を持つ）。運用コストが高いので原則は切替運用

## 認証は OAuth ログインのみ（App / トークン方式が使えない環境向け）

ストアへのアプリ導入（App Store の「Theme Access」app・管理画面のカスタムアプリ / Admin API トークン発行）ができない環境では、`SHOPIFY_CLI_THEME_TOKEN`（`--password`）方式は使えない。

- 認証手段は `shopify auth login`（OAuth）**のみ**
- アカウント切替はクリーン再ログインで行う:

  ```bash
  shopify auth logout && shopify auth login
  # → 目的アカウントを選択
  ```

## 最大リスク: ストア取り違え push → `shopify.theme.toml` で store 固定

アカウントがグローバル単一なので、別アカウント作業中に**誤ったストアへ push する事故**が起きやすい。これを防ぐ安全装置が、各プロジェクト直下に置く `shopify.theme.toml` での store 明示固定（トークン不要、ドメイン or ストアプレフィックスを書くだけ）:

```toml
[environments.development]
store = "<your-store>.myshopify.com"

[environments.production]
store = "<your-store>.myshopify.com"
```

- 固定後はストア未指定のコマンドでも正しいストアに固定される
- 起動時に `--store <prefix>` か `--environment development` を明示すればさらに確実
- **`theme` 系コマンドを叩く前に必ず `shopify.theme.toml` の `store` を確認する**。空文字（`store = ""`）や toml 自体が無いプロジェクトは未固定 = 取り違えリスクが残っている

## 新規ストアプロジェクトの追加手順（toml 固定だけ）

```bash
PROJECT_DIR=/path/to/Store_XXX

# 1. 対象ストアを固定（これだけで「未指定 push で別ストアに飛ぶ」を塞げる）
cat > "$PROJECT_DIR/shopify.theme.toml" <<EOF
[environments.development]
store = "<your-store>.myshopify.com"

[environments.production]
store = "<your-store>.myshopify.com"
EOF

# 2. 必要なアカウントへ切替（既にそのアカウントなら不要）
shopify auth login

# 3. 確認: ストア未指定の theme list が当該ストアを引けば固定成功
shopify theme list
```

## トラブルシューティング

| 症状 | 原因と対処 |
|------|-----------|
| `Looks like you don't have access to this dev store` | ほぼ確実に**アカウント取り違え**（今アクティブな OAuth アカウントが対象ストアの権限を持っていない）。`shopify auth logout && shopify auth login` で、そのストアのオーナー / Staff アカウントへ切り替える。`theme list` も同じエラーなら認証アカウント不一致で確定 |
| 今どのアカウントに繋がっているか分からない | `shopify auth whoami` は v4 で**廃止**。`shopify theme list` の出力に出るストア固有テーマ名で「今どのアカウント = どのストア」を判定する |
| `shopify` が **command not found** | npm 版 `@shopify/cli` の中途半端なグローバルインストールが Homebrew 版の `/opt/homebrew/bin/shopify` シンボリックリンクを壊すと発生。`@shopify/cli` を npm から除去 → `brew upgrade shopify-cli && brew link --overwrite shopify-cli` で復旧。**Homebrew 一本に統一**（npm と二重管理しない）。`shopify/shopify` tap は新しい brew で `brew trust shopify/shopify` が必要 |

## Claude Code 内からのログイン自動化（expect スクリプト）

Claude Code 内蔵 Bash ツールは pty を持たないため、`shopify auth login` の対話プロンプト（"Which account would you like to use?"）が `isTTY()` 判定で弾かれる。`!` プレフィックスや `bash` 直叩きでも同様に失敗する。**同梱の expect スクリプトで TTY をエミュレートして突破する**。

```bash
# スキルはプラグインインストール先（任意 cwd）から動くので、スクリプトのパスを動的解決する
EXP=$(find "$HOME/.claude/plugins" -path '*shopify-cli-auth/scripts/shopify-login.exp' 2>/dev/null | head -1)
[ -z "$EXP" ] && EXP="${CLAUDE_PLUGIN_ROOT}/skills/shopify-cli-auth/scripts/shopify-login.exp"

# 配布物は read-only の場所に置かれ得るので cp してから実行する
cp "$EXP" /tmp/shopify-login.exp
chmod +x /tmp/shopify-login.exp
/tmp/shopify-login.exp
rm /tmp/shopify-login.exp   # 使い終わったら消す
```

- スクリプトは既定で**先頭アカウント（デフォルトハイライト）を確定**する
- 目的アカウントが先頭でない場合は、スクリプト内の `send -- "\r"` の直前に `send -- "\x1b\[B"`（下矢印キー）を必要な回数だけ追加してから実行する
- 完了確認は `shopify theme list` のテーマ名で行う。v4 は Keychain 連携でブラウザ OAuth 不要なケースが多く、アカウント選択の完了 = 認証完了になりがち
- スクリプト本体: [scripts/shopify-login.exp](scripts/shopify-login.exp)

## ガードレール（全作業共通）

| ルール | 理由 |
|--------|------|
| `theme` 系コマンドの前に `shopify.theme.toml` の `store` を必ず確認する | ストア取り違え push の再発防止（グローバル単一アカウントの最大リスク） |
| 権限エラーが出たら、まずアカウント切替を疑う | v4 では「アクセス不可」の大半が認証アカウント不一致 |
| Homebrew 一本で管理し npm 版と混在させない | `shopify` の command not found（シンボリックリンク破壊）防止 |
| ストアドメイン・プレフィックス・アカウントのメールアドレス等の案件識別情報をスキルや汎用ドキュメントに書かない | 機密・顧客情報の流出防止（案件固有の対応表は各案件の memory / 管理側に置く） |

## ファイル構成

```
shopify-cli-auth/
├── SKILL.md                    (本ファイル: v4 のアカウント運用・認証・ストア固定)
└── scripts/
    └── shopify-login.exp       (Claude Code 内から OAuth ログインを突破する expect スクリプト)
```
