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
3. [ ] **配布前提チェック**（リポジトリは PUBLIC。前例: v0.6.1 で個人情報3件を後追い除去）:
   - [ ] 個人情報の grep がゼロ件:
     `grep -rn "我妻\|wagatsuma\|hiyaku\|2418\|wh-dev" skills/ hooks/ agents/ docs/ README.md`
     （`Hiromu-Private` は marketplace add の1箇所のみ許容）
   - [ ] マシン固有の絶対パス（`/Users/` 等）・私物ファイル参照（`~/.claude/rules/` や個人 memory のパス）が無い
   - [ ] 既定値は実行者環境から導出しているか（`git config` / `gh auth status` / 環境変数 / memory の grep 探索）。個人の慣例はスキルでなく実行者側の memory に置く
4. [ ] `scripts/bump-version.sh X.Y.Z` で 3 ファイルのバージョンを一括更新
5. [ ] `scripts/bump-version.sh --check` が ✅ を返す
6. [ ] `git push origin main`
7. [ ] Claude Code で `/plugin marketplace update waggy-shopify-theme-plugin`
8. [ ] 新しいセッションでスキルが認識されることを確認（追加スキルの明示呼出が通るか）

## バージョンを持つ 3 ファイル

| ファイル | 誰が読むか |
|---|---|
| `.claude-plugin/plugin.json` | Claude Code プラグインシステム（**正本**） |
| `.claude-plugin/marketplace.json` | marketplace 更新機構 |
| `package.json` | 参考情報のみ（npm 配布なし・private） |

3 つの同期は手作業でやらない。必ず `scripts/bump-version.sh` を使う。
