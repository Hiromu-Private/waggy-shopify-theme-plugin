# KV サムネイル自動生成手順

`kv-template.html`（config キャッシュ内）にタイトル・サブコピーを差し込み、ブラウザで開いてスクリーンショットを撮ることで、デザイン統一された KV を生成する。

## 1. 差し込み値の決定

| プレースホルダ | 決め方 |
|---|---|
| `{{TITLE_HTML}}` | 記事タイトル。読みやすい位置に `<br>` で改行（1行 12〜14 文字目安、句読点の後で折る）。記事の主張を構成するキーワード 1〜2 語を `<mark>` で囲む |
| `{{TITLE_SIZE}}` | タイトル行数で決める: 2行=100 / 3行=84 / 4行=74 |
| `{{SUBCOPY_TOP}}` | `214 + TITLE_SIZE × 1.5 × 行数 + 62`（整数に丸める） |
| `{{SUBCOPY_HTML}}` | editorial-rules.md セクション6 の原則で作る（対比型・問いかけ型優先、30字前後） |
| `{{EYEBROW}}` | config.kv.eyebrow |
| `{{AUTHOR_NAME}}` / `{{AUTHOR_TITLE}}` | config.kv.authorName / authorTitle |

Python の `str.replace` で置換し、`kv-work/` 作業ディレクトリに `kv.html` として保存。**assets の `logo.png` `author.png` を同じディレクトリにコピーしておく**（テンプレートが相対参照している）。

## 2. スクリーンショット

ブラウザは `file:` プロトコルを拒否することがあるため、ローカル HTTP サーバ経由で開く:

```bash
cd <作業ディレクトリ> && (python3 -m http.server 8377 >/dev/null 2>&1 &)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8377/kv.html   # 200 を確認
```

**Playwright MCP の場合**: `browser_resize(1600, 1100)` → `browser_navigate("http://localhost:8377/kv.html")` → `browser_take_screenshot(type: png, scale: "css")`。`scale: "css"` 必須（device だと Retina で 2〜3 倍サイズになる）。

**playwright-cli の場合**:

```bash
playwright-cli screenshot --viewport-size=1600,1100 http://localhost:8377/kv.html kv-out.png
```

撮影後、HTTP サーバを止める（`kill %1` または `pkill -f "http.server 8377"`）。

## 3. 検証

1. 寸法が config.kv の width×height（例: 1600×1100）ぴったりであること
2. 生成画像を Read で目視確認: 文字切れ・改行位置の不自然さ・マーカー位置・タイトルが右端 110px マージンを侵していないか
3. 問題があれば改行位置・TITLE_SIZE を調整して再生成（1〜2 回のイテレーションは正常）

## 4. 保存

- 生成 PNG を config.kv.filenamePattern（`{slug}` を handle 由来の短縮スラッグに置換）の名前にする
- `gog drive upload <ファイル> --parent <記事フォルダID>` で Drive の記事フォルダへ原本を保存してから、Shopify へのアップロード（graphql-recipes.md）に進む
