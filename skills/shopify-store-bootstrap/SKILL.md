---
name: shopify-store-bootstrap
description: "新規Shopifyストア案件の立ち上げを一気通貫で行うオーケストレーター。テーマファイル一式を受け取った直後の状態から、git init＋identity設定 → .gitignore/.shopifyignore生成 → first commit → docs構造 → テーマ分析（theme-profile.md）→ shopify.theme.toml store固定 → ストア対応表memory登録 → GitHub privateリポジトリ作成＋push までを正しい順序で漏れなく実行する。使用タイミング：「新しいストア案件を立ち上げて」「新案件のストア準備」「ストアをブートストラップ」「新規ストアのセットアップ」「テーマをダウンロードしたから案件開始」「store bootstrap」、および新規テーマディレクトリで git 未初期化の状態から作業を始めるあらゆる場面。個別作業だけなら shopify-theme-init（構造整理のみ）や shopify-theme-analyzer（分析のみ）を使い、新案件のフルセットアップにはこのスキルを使う。"
---

# Shopify Store Bootstrap

新規ストア案件のプロジェクト立ち上げを1コマンドで完了させるオーケストレーター。
個別スキル（theme-init / theme-analyzer）と周辺作業（git / toml / memory / GitHub）を**正しい順序**で束ねる。

## 目的

新案件のたびに発生していた「やり逃し」を構造的に防ぐ:

- `.gitignore` が無いまま first commit してしまう
- `shopify.theme.toml` の store 固定を忘れる（push-guard hook が機能しない）
- ストア対応表 memory への登録漏れ（次のセッションでアカウント取り違え事故）
- GitHub リモート未作成（バックアップなし）

## 前提

- テーマファイル一式（Shopify 標準8ディレクトリ）がプロジェクトディレクトリに展開済み
- `gh` CLI が認証済み（ストア案件のリポジトリは `Hiromu-Private` アカウント配下が慣例）
- 冪等: 一部完了済みの案件に対しても安全。完了済みステップはスキップして残りだけ実行する

## ワークフロー

### Step 0: 現状診断

以下を並列で確認し、どのステップが完了済みかを判定する:

| 確認項目 | コマンド |
|---|---|
| git 初期化済みか | `git rev-parse --git-dir 2>/dev/null` |
| commit 済みか | `git log --oneline -1 2>/dev/null` |
| .gitignore / .shopifyignore | `ls -a` |
| shopify.theme.toml | `cat shopify.theme.toml 2>/dev/null` |
| docs/ 構造 | `ls docs/ 2>/dev/null` |
| リモート | `git remote -v` |
| ストアハンドル候補 | `grep -o '[a-z0-9-]*\.myshopify\.com' config/settings_data.json templates/*.json 2>/dev/null \| sort -u` |
| Shopify 標準構造 | `assets/ config/ layout/ locales/ sections/ snippets/ templates/` の存在 |

標準構造が無い場合は「テーマファイルが未展開では？」と確認して中断する。

### Step 1: ユーザー確認（1回にまとめる）

不足している情報だけを **AskUserQuestion で一度に** 聞く。ステップごとに小出しにしない:

| 項目 | 内容 | 既定値 |
|---|---|---|
| ストアハンドル | `xxx.myshopify.com` の xxx。Step 0 の grep 候補があれば提示して確認 | なし（必須） |
| CLI アカウント系統 | hiyaku（`h.wagatsuma@hiyaku-inc.com`）/ 2418gmail（`h.wagatsuma.2418@gmail.com`） | なし（必須。「不明」なら memory に未確認と記録） |
| git commit identity | このリポジトリのローカル user.email | `h.wagatsuma.2418@gmail.com` |
| GitHub repo | `Hiromu-Private/<ディレクトリ名>` を private 作成 | 作成する |

### Step 2: git init + identity

```bash
git init && git branch -m main
git config user.name "我妻大夢"
git config user.email "<Step 1 で確認した email>"
git config --get user.email  # 検証
```

グローバル設定は触らない（`--global` 禁止。他案件は別 identity の可能性がある）。

### Step 3: ignore 類の生成（first commit より先）

**順序が重要**: `.DS_Store` などのゴミを初回コミットに混入させないため、ignore 類を先に置く。

- `.gitignore` — [shopify-theme-init/references/gitignore-template.md](../shopify-theme-init/references/gitignore-template.md) を使用
- `.shopifyignore` — [shopify-theme-init/references/shopifyignore-template.md](../shopify-theme-init/references/shopifyignore-template.md) を使用

生成後に検証:

```bash
git check-ignore -v .DS_Store .playwright-mcp/test.log .shopify/metafields.json
find . -name ".DS_Store" -not -path "./.git/*" -delete  # 既存ゴミの物理削除
```

### Step 4: first commit

```bash
git add .
git status --short  # settings_data.json 等、意図しない機密が無いか目視確認
git commit -m "chore: initial commit"
git log -1 --format='%an <%ae>'  # identity 検証
```

コミット後に author が意図した email になっているか必ず確認する。

### Step 5: docs/ 構造 + README

`docs/{policies,screenshots}/.gitkeep` と `docs/README.md` を生成する。
README は [shopify-theme-init/references/readme-template.md](../shopify-theme-init/references/readme-template.md) を使い、テーマ名（`config/settings_schema.json` から）・ストアハンドル・アカウント系統を埋める。

コミット: `chore: docs/ 構造とREADME雛形を作成`

### Step 6: shopify.theme.toml store 固定

```toml
[environments.development]
store = "<handle>.myshopify.com"

[environments.production]
store = "<handle>.myshopify.com"
```

コミット: `chore: shopify.theme.toml で store を <handle> に固定`

これが無いと shopify-push-guard hook が照合できない（`~/.claude/rules/shopify-cli.md` の3原則③）。

### Step 7: テーマ分析

**shopify-theme-analyzer スキルを呼び出す**（Skill tool で `shopify-theme-dev:shopify-theme-analyzer`）。

- `docs/theme-profile.md` と `.claude/shopify-verify.config.json` が生成される
- analyzer 内のユーザー確認（命名規則・CSS戦略の合意）はそのまま通す

コミット: `docs: <テーマ名> のテーマプロファイルと検証Configを追加`

### Step 8: ストア対応表 memory 登録

My_Ops_Hub の memory にある **ストア対応表** に1行追記する:

```
/Users/wh-dev/.claude/projects/-Users-wh-dev-Developer-Waggy-My-Ops-Hub/memory/reference_shopify_cli_accounts.md
```

追記フォーマット（既存行に合わせる）:

```markdown
  - `Store_<ディレクトリ名>` = `<handle>`（<アカウント系統>。本番ドメイン <あれば>・<テーマ名> v<version>・<日付> 立ち上げ）
```

これを忘れると次のセッションで「どのアカウントでログインするか」が分からず、
`don't have access` エラーからのアカウント取り違え調査が再発する。

### Step 9: GitHub private リポジトリ作成 + push

ストア案件の慣例は `Hiromu-Private/<ディレクトリ名>`・**private**・SSH remote:

```bash
gh repo create Hiromu-Private/<ディレクトリ名> --private --description "<ストア名> Shopify theme (<テーマ名> v<version>)"
git remote add origin git@github.com:Hiromu-Private/<ディレクトリ名>.git
git push -u origin main
```

`gh auth status` で active account が `Hiromu-Private` であることを先に確認する。

### Step 10: 完了報告

以下の形式でサマリーを出す:

```
✅ ストア案件立ち上げ完了: <ディレクトリ名>
- git: main ブランチ / identity <email> / N commits
- ignore: .gitignore / .shopifyignore
- 分析: docs/theme-profile.md（<テーマ名> v<version>）
- store 固定: <handle>.myshopify.com
- memory: ストア対応表に登録済み（<アカウント系統>）
- GitHub: https://github.com/Hiromu-Private/<ディレクトリ名>（private）

次のステップ:
- ローカル開発: shopify theme dev（アカウント切替が必要なら /shopify-cli-auth）
- セクション設計: /shopify-section-planner
- クライアント案件の秘書管理: /project-secretary-setup（必要なら）
```

## ガードレール

- **既存リポジトリの破壊禁止**: `git init` 前に `.git` の存在を確認。既にあれば init をスキップし、以降を差分実行
- **`--global` 禁止**: git identity は必ずローカル config
- **push 前の status 確認**: 意図しないファイル（`.env` 等の機密）が含まれていないか `git status` を目視
- **theme push はしない**: このスキルはローカル整備と GitHub push のみ。Shopify ストアには一切書き込まない
- **memory の重複登録防止**: 追記前に該当ストアのエントリが既に無いか grep する

## 関連スキル

| スキル | 関係 |
|---|---|
| shopify-theme-init | Step 3/5 のテンプレート正本（ignore 類・README）。構造整理だけ必要なら単体で使う |
| shopify-theme-analyzer | Step 7 で呼び出す。分析だけ必要なら単体で使う |
| shopify-cli-auth | 立ち上げ後の CLI アカウント切替・認証はこちら |
| shopify-section-planner | 立ち上げ完了後の次工程 |
