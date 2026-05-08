# docs/README.md テンプレート

`docs/` 配下に置くドキュメントの目次として使う README 雛形。
スキルが `docs/README.md` を生成するときに参照する。

```markdown
# {{THEME_NAME}} — Theme Documentation

このディレクトリには {{THEME_NAME}} ストア（Shopify テーマ）の参考ドキュメント・素材を置く。
`docs/` 配下のファイルは Shopify CLI の `theme push` 対象外（`.shopifyignore` で除外）。

## ディレクトリ

| パス | 内容 |
|---|---|
| `policies/` | プライバシーポリシー、返品ポリシー、特定商取引法表示などのポリシー文書（Shopify 管理画面 Pages に投入する原稿） |
| `screenshots/` | 開発・レビュー用の参照スクショ（PC/SP、ページ別） |

## 開発フロー（参考）

1. `shopify-theme-init` ─ プロジェクト構造とignore周りを整える（このファイルが生成された時点）
2. `shopify-theme-analyzer` ─ テーマのCSS/JS/コンポーネント構造を分析
3. `shopify-section-planner` ─ 新規セクションを設計
4. `shopify-dev` ─ セクション実装
5. `shopify-schema-validator` ─ Schema検証

## ローカル開発

\`\`\`bash
shopify theme dev
\`\`\`

## ライブテーマへの反映

\`\`\`bash
shopify theme push --theme {{THEME_ID}}
\`\`\`

## 関連リンク

- Shopify 管理画面: https://admin.shopify.com/store/{{STORE_HANDLE}}
- ライブテーマプレビュー: （適宜）
```

## 置換変数

スキル実行時に以下を `config/settings_schema.json` などから抽出して埋める:

- `{{THEME_NAME}}` — `config/settings_schema.json[0].theme_name`
- `{{STORE_HANDLE}}` — Shopify ストアハンドル（プロジェクトルートに `shopify.theme.toml` があればそこから、なければユーザーに確認）
- `{{THEME_ID}}` — `shopify.theme.toml` の `[environments.*]` から取得、または未置換のまま残してユーザー手動入力に委ねる

`.shopify/` は `.gitignore` 対象（per-developer state）なので、再現可能な情報源としては使わない。

抽出失敗時はテンプレを未置換のまま書き込み、ユーザーに「あとで埋めてください」と伝える。
