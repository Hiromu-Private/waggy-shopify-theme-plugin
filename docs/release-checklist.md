# リリースチェックリスト

プラグインの変更を実環境（配布先の Claude Code セッション）へ届けるための手順。
**このリストを飛ばすと「直したのに実環境が古いまま」が再発する**。
（前例: 2026-06-15 の 0.2.0 バンプは package.json しか更新せず、プラグインシステムが読む
plugin.json / marketplace.json が 0.1.0 のまま。6 月に追加したスキルが配布版で有効化されていなかった）

## 手順

1. [ ] 変更をコミットした（Conventional Commits）
2. [ ] スキルを追加/削除/リネームした場合:
   - [ ] README.md の「各スキルの役割」テーブルを更新（`ls skills/` と突合）
   - [ ] README.md のプラグイン構成ツリーを更新
   - [ ] docs/architecture.md のスキル数・早見表を更新
   - [ ] 旧スキル名の残存を全域 grep（`grep -rn "旧名" skills/ README.md docs/`）
3. [ ] `scripts/bump-version.sh X.Y.Z` で 3 ファイルのバージョンを一括更新
4. [ ] `scripts/bump-version.sh --check` が ✅ を返す
5. [ ] `git push origin main`
6. [ ] Claude Code で `/plugin marketplace update waggy-shopify-theme-plugin`
7. [ ] 新しいセッションでスキルが認識されることを確認（追加スキルの明示呼出が通るか）

## バージョンを持つ 3 ファイル

| ファイル | 誰が読むか |
|---|---|
| `.claude-plugin/plugin.json` | Claude Code プラグインシステム（**正本**） |
| `.claude-plugin/marketplace.json` | marketplace 更新機構 |
| `package.json` | 参考情報のみ（npm 配布なし・private） |

3 つの同期は手作業でやらない。必ず `scripts/bump-version.sh` を使う。
