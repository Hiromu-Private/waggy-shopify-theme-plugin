# GraphQL レシピ集（実運用検証済み）

すべて `shopify store execute` で実行する。mutation には `--allow-mutations` が必要。長い値（本文 HTML 等）は `--variable-file` で JSON ファイル渡しにする（シェルエスケープ事故を防ぐ）。

## 既存記事一覧（handle 突き合わせ・重複ガード用）

```bash
shopify store execute --store <store> --query '
query {
  articles(first: 50, sortKey: ID, reverse: true) {
    nodes { id title handle isPublished createdAt templateSuffix tags author { name } }
  }
}'
```

- `sortKey: ID, reverse: true` = 作成が新しい順（下書きも含まれる）
- 注意: `articles(query: "...")` の全文検索は日本語タイトルに対して信頼できない。一覧を取得してローカルで突き合わせる

## 記事の本文取得（逆リンク・バックアップ用）

```bash
shopify store execute --store <store> --query '
query { article(id: "gid://shopify/Article/<ID>") { id title handle body } }'
```

## staged upload（画像アップロードの1段目）

```bash
shopify store execute --store <store> --allow-mutations --query '
mutation {
  stagedUploadsCreate(input: [{
    resource: FILE, filename: "<ファイル名>.png",
    mimeType: "image/png", httpMethod: POST, fileSize: "<バイト数>"
  }]) {
    stagedTargets { url resourceUrl parameters { name value } }
    userErrors { field message }
  }
}'
```

続けて curl で multipart POST（**parameters を全部 -F で先に、file を最後に**）:

```bash
curl -s -w "%{http_code}" -F "<name1>=<value1>" ... -F "file=@<ローカルパス>" "<url>"
# → 201 なら成功
```

## fileCreate → READY ポーリング

```bash
shopify store execute --store <store> --allow-mutations --variable-file vars.json --query '
mutation fileCreate($files: [FileCreateInput!]!) {
  fileCreate(files: $files) {
    files { id fileStatus ... on MediaImage { image { url } } }
    userErrors { field message }
  }
}'
# vars.json: {"files":[{"originalSource":"<resourceUrl>","contentType":"IMAGE","filename":"<名前>.png","alt":"<記事タイトル>"}]}
```

直後は `fileStatus: UPLOADED` で `image: null`。3秒間隔で最大6回ポーリング:

```bash
shopify store execute --store <store> --query '
query { node(id: "<MediaImageのgid>") {
  ... on MediaImage { fileStatus image { url width height } } } }'
```

## articleCreate（公開まで一括）

```bash
shopify store execute --store <store> --allow-mutations --variable-file article.json --query '
mutation articleCreate($article: ArticleCreateInput!) {
  articleCreate(article: $article) {
    article { id title handle isPublished publishedAt templateSuffix tags summary
      image { url altText } blog { id handle }
      metafield(namespace: "global", key: "description_tag") { value } }
    userErrors { field message }
  }
}'
```

article.json の形（値は config と editorial-rules に従って埋める）:

```json
{
  "article": {
    "blogId": "<config.blogId>",
    "title": "<タイトル>",
    "handle": "<スラッグ>",
    "body": "<本文HTML>",
    "summary": "<一覧カード用サマリ>",
    "tags": ["<config.articleTag>"],
    "templateSuffix": "<config.templateSuffix>",
    "isPublished": true,
    "author": {"name": "<config.authorName>"},
    "image": {"url": "<KVのCDN URL>", "altText": "<タイトル>"},
    "metafields": [{
      "namespace": "global", "key": "description_tag",
      "type": "single_line_text_field", "value": "<SEOディスクリプション>"
    }]
  }
}
```

## articleUpdate（逆リンク追加）

```bash
shopify store execute --store <store> --allow-mutations --variable-file backlink.json --query '
mutation articleUpdate($id: ID!, $article: ArticleUpdateInput!) {
  articleUpdate(id: $id, article: $article) {
    article { id handle }
    userErrors { field message }
  }
}'
# backlink.json: {"id":"gid://shopify/Article/<ID>","article":{"body":"<新body全文>"}}
```

body の組み立ては Python 等で: `body.replace('<script type="application/ld+json">', 新段落 + マーカー)`。置換前に必ず assert（マーカーが1個・リンク未存在）。

## 落とし穴

- `article.image` は書き込み時 `{url, altText}` を受け取り、URL から画像をフェッチして CDN に取り込む（`articles/` パスに変わる）
- metafield の type を省略しない（`single_line_text_field`）
- 日本語を含む variables は必ず `json.dumps(..., ensure_ascii=False)` で組み立ててファイル渡し
- zsh では `status` が読み取り専用変数。シェルスクリプト内の変数名に使わない
