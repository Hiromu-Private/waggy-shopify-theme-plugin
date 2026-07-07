# Schema設定タイプ 設計ガイド

**設定タイプの仕様（タイプ一覧・必須属性・default 可否・バリデーションルール・Common Pitfalls）の正本は [shopify-schema-validator/references/setting-types.md](../../shopify-schema-validator/references/setting-types.md)。** 仕様の確認はそちらを参照すること。本ファイルには planner 固有の「設計時にどのタイプを選ぶか」のガイダンスだけを置く。

Source: https://shopify.dev/docs/storefronts/themes/architecture/settings/input-settings

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

## 設計時の注意（バリデーションに響く選択）

- **range は最低 2 ステップ（3 値以上）が必須**。`(max - min) / step` が 1 しかない（実質 2 値の）設定は Shopify に弾かれるため、**2 択は range でなく select で設計する**。上限は 101 ステップ。`default` は必須で、`min <= default <= max` かつ `(default - min) % step === 0` を満たす値にする
- text / textarea を「初期値なし」にしたい場合は `"default": ""` ではなく default キー自体を省略する設計にする
- image_picker / video / product / collection / page / blog / article は default を持てない。「初期画像を見せたい」等の要件は Liquid 側のプレースホルダ表示で設計する

range の設計例:

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
