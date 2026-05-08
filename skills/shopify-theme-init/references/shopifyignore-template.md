# .shopifyignore テンプレート

Shopify CLI (`shopify theme push`, `shopify theme dev`) が**アップロード対象から除外**するファイルを指定する。
`.gitignore` とは別物。git追跡しているがライブテーマには載せたくないドキュメント類を主に除外する。

```
# Documentation (リポジトリでは管理するがテーマには不要)
docs/
README.md
LICENSE
CHANGELOG.md

# Editor / IDE
.vscode/
.idea/
.cursor/

# Tool caches / configs
.serena/
.shopify/

# Local artifacts
.playwright-mcp/
*.log

# OS
.DS_Store
Thumbs.db

# Dependencies
node_modules/

# Env
.env
.env.*
```

## 補足

- Shopify CLI は基本的に `.liquid` / `.json` / `assets/` 配下の画像・JS・CSS のみを認識するため、`docs/` のような *.md は元々アップロードされない。ただし**明示しておくことで意図が伝わる**ため記載している
- `.cursor/rules/` のように **チーム共有したいが** **テーマには載せたくない**ファイルがある場合は `.shopifyignore` に書きつつ git追跡は維持する
- 詳細仕様: https://shopify.dev/docs/themes/tools/cli/configuration#shopifyignore
