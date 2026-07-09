# Shopify Plugin Ecosystem & Theme Workflow

waggy-shopify-theme-plugin の位置づけと、テーマ開発ワークフローを可視化するドキュメント。

---

## 1. Shopify 関連 Plugin の棲み分け

Claude Code 環境でインストールされている 3 つの Shopify 関連 plugin の役割マップ。

```mermaid
graph TB
    User([👤 開発者])

    subgraph Knowledge["📚 知識・コード検証層"]
        AIToolkit["**shopify-ai-toolkit**<br/>by Shopify公式<br/>━━━━━━━━━━━<br/>19 skills<br/>(Liquid / Admin GraphQL /<br/>Hydrogen / Polaris / etc.)<br/>━━━━━━━━━━━<br/>📖 Doc横断検索<br/>✓ theme-check ベース検証"]
    end

    subgraph Workflow["🔨 テーマ開発ワークフロー層"]
        Waggy["**waggy-shopify-theme-plugin**<br/>by waggy (自作)<br/>━━━━━━━━━━━<br/>12 skills + 1 agent + 3 hooks<br/>━━━━━━━━━━━<br/>🔄 analyze → plan → implement → verify<br/>🤖 Playwright 自動検証<br/>⚙️ Hook 自動発火"]
    end

    subgraph Operation["📦 ストア運用層"]
        Admin["**shopify-admin-skills**<br/>by 40rty社<br/>━━━━━━━━━━━<br/>10 categories / 63 skills<br/>(marketing / inventory /<br/>fulfillment / finance / etc.)<br/>━━━━━━━━━━━<br/>🛒 Admin GraphQL 操作<br/>📊 ストア運営ワークフロー"]
    end

    User -->|"テーマ実装したい"| Waggy
    User -->|"Shopify知識・コード検証"| AIToolkit
    User -->|"ストア運用・データ操作"| Admin

    Waggy -.->|"shopify-liquid の<br/>validate.mjs を呼ぶ"| AIToolkit

    classDef knowledgeBox fill:#e8f4fd,stroke:#2563eb,stroke-width:2px,color:#1e3a8a
    classDef workflowBox fill:#fef3e8,stroke:#ea580c,stroke-width:3px,color:#7c2d12
    classDef operationBox fill:#e8fdf4,stroke:#059669,stroke-width:2px,color:#064e3b
    classDef userBox fill:#f3f4f6,stroke:#374151,stroke-width:2px

    class AIToolkit knowledgeBox
    class Waggy workflowBox
    class Admin operationBox
    class User userBox
```

### 役割対比表

| 観点 | shopify-ai-toolkit | **waggy-shopify-theme-plugin** | shopify-admin-skills |
|------|-------------------|-------------------------------|---------------------|
| **メタファー** | 📚 司書 | 🔨 大工の親方 | 📦 ストア店長補佐 |
| **提供元** | Shopify公式 | waggy (自作) | 40rty社 |
| **対象タスク** | API設計・GraphQL・Liquid記法・ドキュメント検索 | テーマ実装ワークフロー丸ごと | ストア運営・在庫・受注・顧客管理 |
| **発火モード** | 受動的（呼ばれた時だけ） | **能動的**（hook で自動起動） | 受動的（呼ばれた時だけ） |
| **構成** | 19 skills | 12 skills + 1 agent + 3 hooks | 63 skills (10 categories) |
| **言語** | 英語 | **日本語** | 英語 |
| **依存** | スタンドアロン | **shopify-ai-toolkit に依存**（validate.mjs を呼ぶ） | スタンドアロン |
| **得意領域** | 知識・公式仕様・lint | テーマ実装 + 検証 + 自動化 | Admin API 経由のストア操作 |
| **不得意領域** | Playwright 検証なし、自動化なし | API設計・Admin GraphQL の知識 | テーマ開発 |

### いつどれを使うか

| やりたいこと | 使う Plugin |
|-------------|------------|
| Liquid タグの正しい使い方を調べる | **shopify-ai-toolkit** (`shopify-liquid`) |
| Admin GraphQL でクエリ書く | **shopify-ai-toolkit** (`shopify-admin`) |
| テーマのセクション新規作成 | **waggy** (`shopify-theme-analyzer` → `shopify-section-planner` → `theme-orchestrator`) |
| Liquid 編集後の自動検証 | **waggy** (Stop hook → `shopify-verifier`) |
| 在庫一括更新・キャンペーン設定 | **shopify-admin-skills** |
| 顧客の cohort 分析・LTV 集計 | **shopify-admin-skills** |

---

## 2. waggy-shopify-theme-plugin 主要ワークフロー（analyze → plan → implement → verify）

開発者が `.liquid` セクションを 1 つ作るときの自動化フロー。図は 13 スキルのうちコアパイプライン（analyzer → planner → orchestrator → schema-validator）と検証系 Hook / Agent の連携を示す。図に含まれない 9 スキル（store-bootstrap / theme-init / ds-component-search / asset-harvest / theme-brand-layer / flow-builder / cv-tracking / delivery-report / cli-auth）は後述の「コンポーネント早見表」を参照。

```mermaid
flowchart TD
    Start([🚀 開発者: テーマ作業開始])

    Start --> SessionStart["**SessionStart hook**<br/>shopify-theme-context.sh<br/>━━━━━━━━━━━<br/>theme-profile.md を Claude に注入"]

    SessionStart --> Q{プロジェクト初回？}
    Q -->|Yes| Analyzer["📊 **shopify-theme-analyzer**<br/>(skill)<br/>━━━━━━━━━━━<br/>CSS命名規則・ブレークポイント・<br/>再利用コンポーネントを抽出<br/>↓<br/>docs/theme-profile.md 生成"]
    Q -->|No| ProfileCheck{theme-profile.md<br/>存在 & 30日以内？}

    Analyzer --> ProfileCheck
    ProfileCheck -->|❌ 古い| Analyzer
    ProfileCheck -->|✅ OK| WorkType{何をする？}

    WorkType -->|新規セクション設計| Planner["📐 **shopify-section-planner**<br/>(skill)<br/>━━━━━━━━━━━<br/>テキスト or Figma 入力 → 要件抽出<br/>既存コンポーネント流用設計<br/>Shopify Dev Docs MCP で仕様検証<br/>↓<br/>docs/c-{name}-spec.md 生成"]
    WorkType -->|既存セクション修正| Orchestrator
    WorkType -->|設計書ベース実装| Orchestrator

    Planner --> Orchestrator["⚙️ **theme-orchestrator**<br/>(skill)<br/>━━━━━━━━━━━<br/>テーマプロファイル準拠で実装<br/>ガードレール (forbidden_files 回避)<br/>↓<br/>.liquid / .css / .js を Write/Edit"]

    Orchestrator -->|"Write/Edit 発火"| PostToolUse["**PostToolUse hook**<br/>shopify-verify-record.sh<br/>━━━━━━━━━━━<br/>編集ファイルをキューに記録"]

    Orchestrator -->|"schema 含む .liquid"| SchemaValidator["✓ **shopify-schema-validator**<br/>(skill / 自動 or 手動)<br/>━━━━━━━━━━━<br/>validate_schema.py で<br/>10 個の critical rule をチェック"]

    PostToolUse --> Continue[他の編集が続く...]
    Continue --> Orchestrator

    Orchestrator -->|"応答完了"| Stop["**Stop hook**<br/>shopify-verify-trigger.sh<br/>━━━━━━━━━━━<br/>キューに編集ファイルがあれば<br/>verifier agent を起動"]

    Stop --> Verifier["🤖 **shopify-verifier**<br/>(agent / Playwright付き)<br/>━━━━━━━━━━━<br/>1. preview URL preflight<br/>2. Liquid 検証<br/>   ↳ ai-toolkit の validate.mjs<br/>3. Schema 検証<br/>   ↳ schema-validator の py<br/>4. 影響ページを Playwright で開く<br/>5. console / network エラー収集"]

    Verifier --> Result{エラー?}
    Result -->|✅ なし| Done([🎉 完成])
    Result -->|❌ あり| AutoFix["🔧 自動修正<br/>(max 2 cycles)"]
    AutoFix --> Verifier

    classDef hookStyle fill:#fff7e6,stroke:#d97706,stroke-width:2px,color:#78350f
    classDef skillStyle fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0c4a6e
    classDef agentStyle fill:#fce7f3,stroke:#be185d,stroke-width:3px,color:#831843
    classDef startEnd fill:#f0fdf4,stroke:#16a34a,stroke-width:2px,color:#14532d

    class SessionStart,PostToolUse,Stop hookStyle
    class Analyzer,Planner,Orchestrator,SchemaValidator skillStyle
    class Verifier,AutoFix agentStyle
    class Start,Done,Continue startEnd
```

### コンポーネント早見表

| 種類 | 名前 | 起動契機 | 役割 |
|------|------|---------|------|
| **Hook** | `shopify-theme-context.sh` | SessionStart | プロジェクトのテーマ情報を Claude に注入 |
| **Hook** | `shopify-verify-record.sh` | PostToolUse (Write/Edit) | 編集ファイルをキューに記録 |
| **Hook** | `shopify-verify-trigger.sh` | Stop | キューに編集があれば verifier 起動 |
| **Skill** | `shopify-theme-init` | 明示呼び出し | プロジェクト構造・ignore 整備、ゴミ整理（analyzer の前段） |
| **Skill** | `shopify-theme-analyzer` | 明示呼び出し | テーマ全体分析 → `theme-profile.md` |
| **Skill** | `shopify-section-planner` | 明示呼び出し | 新規セクション設計書作成 |
| **Skill** | `theme-orchestrator` | 明示呼び出し | 実装オーケストレーション |
| **Skill** | `shopify-ds-component-search` | orchestrator Phase 0 から自動 / 明示 | 既存 `c-*` 資産・Figma Components・中央ライブラリの洗い出し |
| **Skill** | `shopify-asset-harvest` | 実装完了時に orchestrator が提案 / 明示 | 実装資産を汎用化して案件横断ライブラリへ回収（ds-component-search と対） |
| **Skill** | `shopify-schema-validator` | 自動 or 明示 | schema 構文 10 ルール検証 |
| **Skill** | `shopify-theme-brand-layer` | 明示呼び出し | Brand 層（`brand-*`）の設計・実装（横断スキル） |
| **Skill** | `shopify-flow-builder` | 明示呼び出し | Shopify Flow 構築（テーマ開発とは別軸） |
| **Skill** | `shopify-cv-tracking` | 明示呼び出し | CV 計測タグ / カスタムピクセルの実装と検証（別軸） |
| **Skill** | `shopify-delivery-report` | 明示呼び出し / 実装完了時 | クライアント向け報告文生成 + 実績記録（別軸） |
| **Skill** | `shopify-cli-auth` | 明示呼び出し | Shopify CLI v4 のアカウント切替・認証・ストア固定（別軸） |
| **Skill** | `shopify-store-bootstrap` | 明示呼び出し | 新案件立ち上げのフルセットアップ（theme-init / analyzer を内包する上位オーケストレーター） |
| **Agent** | `shopify-verifier` | Stop hook 経由 | Liquid + Playwright 自動検証 |

### 設計原則

1. **単一責任** — 各 skill は 1 つの明確な仕事だけ持つ（analyzer は読むだけ、planner は書くだけ、orchestrator は実装するだけ、validator は検証するだけ）
2. **独立実行** — フローを途中から呼べる。`/theme-orchestrator` だけでも、`/shopify-section-planner` だけでも使える
3. **コンテキスト効率** — 重い分析結果は `theme-profile.md` にシリアライズ、後続スキルは読むだけ
4. **責務分離** — Skill = ユーザー発火 / Hook = ランタイム発火 / Agent = Hook → 隔離プロセス
5. **配布前提** — リポジトリは PUBLIC で第三者が使う。個人情報・マシン固有パス・私物ファイル（`~/.claude/rules/` や個人 memory）への依存をスキルに書かない。既定値は実行者の環境（`git config` / `gh auth status` / 環境変数 / memory の grep 探索）から導出し、個人の慣例は各実行者の memory 側に置く。リリース前チェックは `docs/release-checklist.md` の配布前提チェックで機械的に検出する

---

## 3. データの流れ（補足）

```mermaid
flowchart LR
    SourceCode[📁 テーマソース<br/>sections/ assets/ snippets/]
    Profile[📝 docs/<br/>theme-profile.md]
    Spec[📋 docs/<br/>c-name-spec.md]
    Files[💾 .liquid<br/>.css / .js]
    Queue[🗂️ verify queue]
    Report[📊 検証レポート]

    SourceCode -->|analyzer| Profile
    Profile -->|planner 参照| Spec
    Profile -->|orchestrator 参照| Files
    Spec -->|orchestrator 参照| Files
    Files -->|PostToolUse hook| Queue
    Queue -->|Stop hook → verifier| Report
    Report -.->|エラー時| Files
```

---

## 関連ドキュメント

- [README.md](../README.md) — プラグインの概要・インストール・コマンド一覧
- 各 skill の SKILL.md — `skills/{skill-name}/SKILL.md`
- [shopify-verify.config.json](../README.md#shopify-verifyconfigjson) — プロジェクト固有設定（preview URL、viewport、forbidden_files）
