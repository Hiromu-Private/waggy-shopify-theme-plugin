# Schema設定タイプ リファレンス

Source: https://shopify.dev/docs/storefronts/themes/architecture/settings/input-settings

## 設定タイプ早見表

| タイプ | 用途 | default | 注意 |
|--------|------|---------|------|
| text | 短いテキスト | 任意 | `""` は無効 |
| textarea | 長いテキスト | 任意 | `""` は無効 |
| number | 数値 | 任意 | 文字列NG |
| range | スライダー | **必須** | step整合必須 |
| select | ドロップダウン | 任意 | options必須 |
| radio | ラジオ | 任意 | options必須 |
| checkbox | ON/OFF | 任意 | デフォルトfalse |
| color | カラーピッカー | 任意 | |
| color_background | 背景色 | 任意 | |
| color_scheme | カラースキーム | **必須** | "scheme-1" |
| font_picker | フォント | **必須** | フォント識別子必須 |
| image_picker | 画像 | **非対応** | |
| video | Shopifyホスト動画 | **非対応** | |
| video_url | YouTube/Vimeo | 任意 | accept必須 |
| url | URL | 任意 | `/collections` or `/collections/all` のみ |
| product | 商品 | **非対応** | |
| product_list | 商品リスト | 任意 | limit max 50 |
| collection | コレクション | **非対応** | |
| collection_list | コレクションリスト | 任意 | limit max 50 |
| page | ページ | **非対応** | |
| blog | ブログ | **非対応** | |
| article | 記事 | **非対応** | |
| article_list | 記事リスト | 任意 | limit max 50 |
| link_list | ナビメニュー | 任意 | `main-menu` or `footer` のみ |
| richtext | リッチテキスト | 任意 | `<p>` or `<ul>` でラップ |
| inline_richtext | インラインリッチ | 任意 | 改行なし |
| html | HTML | 任意 | html/head/body 除去 |
| liquid | Liquid | 任意 | Max 50KB |
| metaobject | メタオブジェクト | 任意 | metaobject_type必須 |
| metaobject_list | メタオブジェクトリスト | 任意 | metaobject_type必須 |
| text_alignment | テキスト配置 | 任意 | `left`, `center`, `right` |
| header | 見出し（非入力） | N/A | サイドバー表示のみ |
| paragraph | 説明文（非入力） | N/A | サイドバー表示のみ |

## 設計時の使い分けガイド

| 要件 | 推奨タイプ |
|------|----------|
| 1行テキスト | text |
| 改行なし装飾テキスト | inline_richtext |
| 改行あり装飾テキスト | richtext |
| 2-8択の選択 | select |
| ON/OFF切替 | checkbox |
| 数値スライダー | range |
| コンテンツが増減する | blocks |
| 画像 | image_picker |
| YouTube/Vimeo動画 | video_url（accept指定必須） |
| リンク先URL | url |
| 商品選択 | product |
| コレクション選択 | collection |

## range タイプの制約

- `default` は必須: `min <= default <= max`
- step整合: `(default - min) % step === 0`
- 最大ステップ数: `(max - min) / step <= 101`

例:
```json
{
  "type": "range",
  "id": "padding_top",
  "label": "上余白 (px)",
  "unit": "px",
  "min": 0,
  "max": 100,
  "step": 4,
  "default": 36
}
```

## blocks 設計ルール

- `type` と `name` は必須（@app以外）
- `type` は一意、`name` は一意
- `limit` で各タイプの最大数を制限可能
- `max_blocks` でセクション全体の上限設定（デフォルト50）

例:
```json
{
  "type": "card",
  "name": "カード",
  "limit": 8,
  "settings": [
    { "type": "image_picker", "id": "image", "label": "画像" },
    { "type": "text", "id": "heading", "label": "見出し" },
    { "type": "richtext", "id": "description", "label": "説明文" },
    { "type": "url", "id": "link", "label": "リンク先" }
  ]
}
```

## 日本語ラベル規約

新規カスタムセクション: 直接日本語ラベルを使用（翻訳キー不要）

例:
```json
{ "type": "text", "id": "heading", "label": "見出しテキスト" }
{ "type": "header", "content": "レイアウト設定" }
{ "type": "select", "id": "layout", "label": "レイアウト", "options": [
  { "value": "grid", "label": "グリッド" },
  { "value": "list", "label": "リスト" }
]}
```

## Common Pitfalls

### text/textarea with empty default
```json
// BAD - Shopify rejects this
{ "type": "text", "id": "desc", "label": "Description", "default": "" }

// GOOD - Omit default entirely
{ "type": "text", "id": "desc", "label": "Description" }
```

### range validation
```json
// BAD - default (5) is not a multiple of step (4) from min (0)
{ "type": "range", "id": "x", "label": "X", "min": 0, "max": 100, "step": 4, "default": 5 }

// GOOD
{ "type": "range", "id": "x", "label": "X", "min": 0, "max": 100, "step": 4, "default": 36 }
```

### image_picker with default
```json
// BAD - image_picker does not support default
{ "type": "image_picker", "id": "img", "label": "Image", "default": "something" }

// GOOD
{ "type": "image_picker", "id": "img", "label": "Image" }
```
