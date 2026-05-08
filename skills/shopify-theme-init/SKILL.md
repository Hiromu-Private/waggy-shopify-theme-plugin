---
name: shopify-theme-init
description: "Shopifyテーマプロジェクトの初期化・クリーンアップ。.gitignore / .shopifyignore / docs/構造 / README雛形 を生成し、ルート直下に散らかったスクショや .DS_Store などのゴミを片付ける。新規Shopify CLIテーマにも、既存の散らかったテーマにも適用可能。使用タイミング：「テーマ初期化」「テーマセットアップ」「初期セットアップ」「クリーンアップ」「リポジトリ整理」「ディレクトリ整理」「ゴミ整理」「docs構造作成」「.gitignore作って」「.shopifyignore作って」。shopify-theme-analyzer の前段として実行することを推奨。"
---

# Shopify Theme Init

Shopifyテーマプロジェクトを「Shopify標準ディレクトリ + 周辺の管理ファイル」が揃った状態に整える。新規・既存どちらでも同じ手順で動かせる冪等な初期化スキル。

## 目的

- ルート直下を Shopify 標準8ディレクトリ（`assets/`, `blocks/`, `config/`, `layout/`, `locales/`, `sections/`, `snippets/`, `templates/`）+ `docs/` のみに整理する
- `.gitignore` / `.shopifyignore` / `docs/` 構造 / `README.md` 雛形を生成する
- ルート直下のスクショ（`*.png` / `*.jpg`）や `.DS_Store` などのゴミを `docs/screenshots/` に移動・削除する
- 整理内容ごとに自動分割コミットして git 履歴をクリーンに残す

## 前提

- 対象は Shopify Online Store 2.0 テーマ（CLIで生成されたもの、または同等構造のもの）
- 実行前にユーザーの作業ブランチが clean か作業中かを問わず動作するが、**未コミットの作業がある場合は中断してユーザーに確認する**

## ワークフロー

### Step 1: 現状診断

以下を並列で取得し、現状のスナップショットを作る:

| 確認項目 | コマンド／チェック |
|---|---|
| git 状態 | `git status --short` |
| ルート構成 | `ls -la` |
| 既存 .gitignore | `cat .gitignore` |
| 既存 .shopifyignore | `cat .shopifyignore` |
| Shopify標準ディレクトリ存在確認 | `assets/ blocks/ config/ layout/ locales/ sections/ snippets/ templates/` |
| ルート直下のゴミ候補 | `find . -maxdepth 1 -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name ".DS_Store" \)` |
| docs/ 既存有無 | `ls docs/ 2>/dev/null` |
| Playwright/MCP系成果物 | `.playwright-mcp/`, `.serena/cache/` の有無 |

**ガードレール**: 以下のテーマ実装ディレクトリに未コミットの diff がある場合は中断し、「先にコミットしますか？」とユーザーに確認する。

- `assets/`, `blocks/`, `config/`, `layout/`, `locales/`, `sections/`, `snippets/`, `templates/`

このスキルが整理対象とするファイル（`.gitignore`, `.shopifyignore`, `docs/`, ルート直下PNG, `.DS_Store`, 旧 `document/`）の差分のみであれば続行してよい。

### Step 2: 整理プラン提示

診断結果を踏まえて、以下の形式でプランを提示する:

```
現状:
  - Shopify標準構造: ✓ / ✗ (不足ディレクトリがあれば列挙)
  - .gitignore: なし / あり (差分マージが必要なら明示)
  - .shopifyignore: なし / あり
  - docs/構造: なし / 一部あり / 完備
  - 既存ゴミ: ルート直下PNG 3枚 / .DS_Store 2件 / .playwright-mcp/ 8ファイル / ...

実行プラン (整理内容ごとに分割コミット):
  1. .gitignore 追加 (or 既存に N 行追記)
  2. .shopifyignore 追加
  3. docs/{policies,screenshots} 構造作成 + README雛形
  4. ルート直下PNGを docs/screenshots/ に移動
  5. .DS_Store 削除
  6. 旧 document/ → docs/ リネーム (該当する場合のみ)
```

ユーザーの承認を取ってから Step 3 以降に進む。

**スキップ判断**: 既に整っている項目はプランから除外する（冪等性）。何も整理することがなければ「すでに整っています」と報告して終了。

### Step 3: .gitignore 生成 / マージ

- 既存 `.gitignore` が**ない場合**: [references/gitignore-template.md](references/gitignore-template.md) の内容をそのまま書き込む
- 既存 `.gitignore` が**ある場合**: テンプレートの各行を読み、既存ファイルに含まれていない行のみ末尾に追記する（重複排除）

書き終わったら以下を検証:

```bash
git check-ignore -v .DS_Store .playwright-mcp/ .shopify/metafields.json
```

期待値が ignore されているか確認してから次へ。

**コミット**:
```
chore: .gitignoreを追加してOS/エディタ/CLIゴミの追跡を抑止
```

### Step 4: .shopifyignore 生成

`.shopifyignore` がなければ [references/shopifyignore-template.md](references/shopifyignore-template.md) を書き込む。

これにより `shopify theme push` 時に `docs/`, `README.md`, `.cursor/`, `.serena/` などがアップロード対象から除外される。

**コミット**:
```
chore: .shopifyignoreを追加してCLIアップロード対象を限定
```

### Step 5: docs/ 構造生成 + README雛形

```
docs/
├── README.md            (テーマ説明テンプレ)
├── policies/            (privacy, return, shipping, terms, tokushoho など)
├── screenshots/         (PC/SPの参照画像)
└── .gitkeep             (空ディレクトリ確保用、必要なら)
```

- 既に `document/` が存在し中身がある場合は `docs/` への移動を提案する（中身が同一であれば rename として処理）
- `docs/README.md` には [references/readme-template.md](references/readme-template.md) を使う
- ユーザーに「policies は実ファイル投入する？空のテンプレ置く？」と聞く

**コミット**:
```
chore: docs/ 構造とREADME雛形を作成
```
旧 `document/` リネームが発生した場合は別コミットで:
```
refactor: ドキュメントディレクトリを document/ から docs/ にリネーム
```

### Step 6: 既存ゴミの整理

| ゴミ種別 | アクション |
|---|---|
| ルート直下の `*.png` / `*.jpg` | 追跡済み (`git ls-files` に含まれる) → `git mv`。未追跡 → `mv` してから `git add` |
| `.DS_Store` | ローカル削除（追跡されていれば `git rm --cached`） |
| `.playwright-mcp/` 内ログ | 既に Step 3 でignore済み。実体ファイルは触らない（ログ蓄積価値あり） |
| `.shopify/` 配下 | 既に Step 3 でignore済み。触らない |

**`git mv` vs `mv` の判定**:
```bash
if git ls-files --error-unmatch "$file" >/dev/null 2>&1; then
  git mv "$file" docs/screenshots/
else
  mv "$file" docs/screenshots/
fi
```

**コミット**:
```
chore: ルート直下の参照スクショを docs/screenshots/ に集約
```

### Step 7: 検証

完了報告前に必ず以下を確認:

```bash
# ルート直下が標準構造のみか
ls -1 | grep -v '^\.'

# git ステータスがクリーンか
git status --short

# ignoreが効いているか
git check-ignore .DS_Store .playwright-mcp/ .shopify/

# 直近コミット履歴
git log --oneline -7
```

ルート直下に Shopify 標準8ディレクトリ + `docs/` 以外があれば、その理由を確認するか追加整理する。

## ガードレール

- **削除前確認**: ファイル削除（`.DS_Store` 以外）はユーザー承認なしに実行しない
- **未コミット作業の保護**: スキル開始時点で関係ない未コミット変更がある場合は中断
- **冪等性**: 何度実行しても安全。既に整っている部分はスキップ
- **テーマ動作非破壊**: `assets/` `sections/` `templates/` などの実テーマファイルには一切触れない
- **ライブテーマ非破壊**: `theme push` を伴う動作はしない。ローカルのファイル整理とコミットのみ

## このスキルが触らないもの

- `assets/`, `blocks/`, `config/`, `layout/`, `locales/`, `sections/`, `snippets/`, `templates/` のテーマ実装ファイル
- `.cursor/rules/` などチーム共有のエディタ設定
- `.serena/project.yml` などツールの永続設定（cache だけ ignore）

## 関連スキル

| 順序 | スキル | 役割 |
|---|---|---|
| 1 | **shopify-theme-init** (本スキル) | プロジェクト構造と周辺ファイル整備 |
| 2 | shopify-theme-analyzer | テーマ実装の構造分析（CSS/JS/コンポーネント） |
| 3 | shopify-section-planner | セクション設計 |
| 4 | shopify-dev | セクション実装 |
| 5 | shopify-schema-validator | Schema検証 |

## 命令例

- 「Shopifyテーマを初期化して」
- 「ディレクトリ整理して」
- 「.gitignoreがないから作って」
- 「ルート直下にスクショが散らかってる、整理して」
- 「shopify-theme-init を実行」
