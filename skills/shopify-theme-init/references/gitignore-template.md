# .gitignore テンプレート

Shopifyテーマプロジェクト用の標準 `.gitignore`。
既存ファイルがある場合は、ここに記載されている行のうち含まれていないものだけ追記する（重複排除マージ）。

```gitignore
# OS
.DS_Store
Thumbs.db

# Editor / IDE
.vscode/
.idea/
*.swp
*.swo

# Shopify CLI (per-developer state)
.shopify/

# Tool caches
.serena/cache/

# MCP / 調査用ローカル成果物
.playwright-mcp/

# Logs
*.log
npm-debug.log*

# Dependencies
node_modules/

# Env
.env
.env.*
!.env.example
```

## 各エントリの根拠

| エントリ | 理由 |
|---|---|
| `.DS_Store` / `Thumbs.db` | macOS / Windows が勝手に作るファイル。リポジトリに混入する価値ゼロ |
| `.vscode/` `.idea/` | エディタ個人設定。チームで揃えたい場合は `.vscode/settings.json` のみ追跡する個別運用に |
| `.shopify/` | Shopify CLI が保持する開発者ごとのストア接続情報・preview state。共有不要 |
| `.serena/cache/` | Serena MCP のシンボル/インデックスキャッシュ。再生成可能 |
| `.playwright-mcp/` | Playwright MCP の console/page スナップショット。ローカル調査ログとして蓄積させたいが追跡は不要 |
| `node_modules/` | npm依存（テーマで使う場合） |
| `.env*` | 秘密情報。`.env.example` のみ追跡 |

## 追加検討

プロジェクト固有で以下を追加する場合がある:

- `*.zip` (テーマZIPエクスポート成果物)
- `release-notes/draft-*` (ドラフト)
- `coverage/` (テストカバレッジ)
