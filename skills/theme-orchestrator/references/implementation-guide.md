# セクション実装ガイド

テーマプロファイルのパターンに従い、新規セクションを実装する際のリファレンス。

> **前提**: 本ガイドのコード例には**テーマ系統依存の部分**（クラス名・翻訳キー・カスタム要素・CSS変数）が含まれ、多くは Focal/Prestige 系テーマのパターン。実装時は必ず `docs/theme-profile.md` の規約を優先し、例をコピーする前に対象テーマに同じ仕組みが存在するか確認すること。

## セクションファイル骨格

```liquid
{%- comment -%}
  Section: c-[section-name]
  Purpose: [セクションの目的]
{%- endcomment -%}

{%- comment -%} CSS読み込み（外部CSSの場合のみ） {%- endcomment -%}
{%- comment -%} テーマのCSS読み込み方式に従うこと。テーマプロファイル参照 {%- endcomment -%}

<style>
  #shopify-section-{{ section.id }} {
    /* セクション固有のCSS変数 */
  }

  @media screen and (min-width: 700px) {
    #shopify-section-{{ section.id }} {
      /* タブレット以上のオーバーライド */
    }
  }
</style>

{%- comment -%} Focal/Prestige 系の例: 背景ハッシュクラス方式。Dawn 系は color-{{ section.settings.color_scheme.id }} クラスを付けるだけ {%- endcomment -%}
{%- assign color_scheme_hash = section.settings.color_scheme.settings.background_gradient | default: section.settings.color_scheme.settings.background | md5 -%}

<div class="section-spacing color-scheme color-scheme--{{ section.settings.color_scheme.id }} color-scheme--bg-{{ color_scheme_hash }} {% if section.settings.separate_section_with_border %}bordered-section{% endif %}">
  <div class="container">
    <div class="section-stack">
      {%- render 'section-header', subheading: section.settings.subheading, heading: section.settings.title, content: section.settings.content, text_alignment: 'center' -%}

      <!-- メインコンテンツ -->
    </div>
  </div>
</div>

{% schema %}
{
  "name": "c-[セクション名]",
  "class": "shopify-section--c-[section-name]",
  "tag": "section",
  "settings": [],
  "blocks": [],
  "presets": [
    {
      "name": "c-[セクション名]"
    }
  ]
}
{% endschema %}
```

**重要**: 上記は骨格の一例で、`color_scheme_hash` / `section-spacing` / `container` / `section-stack` / `bordered-section` / `section-header` スニペットは Focal/Prestige 系テーマ固有。Dawn / Horizon 等には存在しないため、実際のHTML構造、クラス名、CSS変数は必ずテーマプロファイルのパターンに合わせること（Dawn 系のカラースキームは `color-{{ section.settings.color_scheme.id }}` クラス方式）。

## Schema共通設定

テーマの他セクションが持つ共通設定（カラースキーム等）は、テーマプロファイルが該当する場合に新規セクションにも含める。以下は Focal/Prestige 系の例:

```json
{
  "type": "color_scheme",
  "id": "color_scheme",
  "label": "t:global.colors.scheme",
  "default": "scheme-1"
},
{
  "type": "checkbox",
  "id": "separate_section_with_border",
  "label": "t:global.section.separate_section_with_border",
  "default": true
},
{
  "type": "checkbox",
  "id": "remove_vertical_spacing",
  "label": "t:global.spacing.remove_vertical_spacing",
  "default": false
}
```

**注意（テーマ系統依存）**: 本ガイドの Schema 例に登場する `t:global.*` 翻訳キーは Focal 系固有。翻訳キーはテーマの `locales/*.schema.json` に存在するもののみ使い、無ければ直接テキスト（例: `"label": "カラースキーム"`）を書く。`separate_section_with_border` / `remove_vertical_spacing` はそれを解釈する CSS を持つ Focal 系でのみ有効（`type: color_scheme` 自体は Shopify 標準の設定タイプで全テーマ可）。

## セクションヘッダーパターン

テーマに共通の見出しスニペットがあれば流用する。以下は Focal 系の `section-header` スニペットの例（Dawn / Horizon 系には同等スニペットが無いことが多く、その場合は見出しマークアップをセクション内に直接書く）:

```liquid
{%- render 'section-header',
  subheading: section.settings.subheading,
  heading: section.settings.title,
  content: section.settings.content,
  text_alignment: 'center'
-%}
```

対応するSchema設定:
```json
{
  "type": "text",
  "id": "subheading",
  "label": "t:global.text.subheading"
},
{
  "type": "text",
  "id": "title",
  "label": "t:global.text.heading"
},
{
  "type": "richtext",
  "id": "content",
  "label": "t:global.text.content"
}
```

## Blocksパターン

### 基本的なblock定義

```json
{
  "blocks": [
    {
      "type": "item",
      "name": "アイテム",
      "settings": [
        {
          "type": "image_picker",
          "id": "image",
          "label": "t:global.image.image"
        },
        {
          "type": "text",
          "id": "title",
          "label": "t:global.text.heading"
        },
        {
          "type": "richtext",
          "id": "content",
          "label": "t:global.text.content"
        }
      ]
    }
  ]
}
```

### blockのループ

```liquid
{%- for block in section.blocks -%}
  <div class="c-[name]__item" {{ block.shopify_attributes }}>
    {%- if block.settings.image != blank -%}
      {{- block.settings.image | image_url: width: block.settings.image.width | image_tag: sizes: '(max-width: 699px) 100vw, 33vw', widths: '200,400,600,800,1000' -}}
    {%- endif -%}

    {%- if block.settings.title != blank -%}
      <h3>{{ block.settings.title }}</h3>
    {%- endif -%}

    {%- if block.settings.content != blank -%}
      <div class="prose">{{ block.settings.content }}</div>
    {%- endif -%}
  </div>
{%- endfor -%}
```

**重要**: `{{ block.shopify_attributes }}` を各blockのルート要素に必ず含めること（テーマエディタでの選択に必要）。

## カルーセル実装（既存カスタム要素の流用）

カルーセルはテーマ既存のカスタム要素を theme-profile.md で確認して流用する。以下は Focal/Prestige 系の `scroll-carousel` / `carousel-navigation` の例（Dawn 系では `slider-component` が相当。既存要素が無いテーマでは新規 JS を検討）:

```liquid
<scroll-carousel class="scroll-area snap-x bleed md:unbleed" id="carousel-{{ section.id }}">
  {%- for block in section.blocks -%}
    <div class="snap-center" {{ block.shopify_attributes }}>
      <!-- block content -->
    </div>
  {%- endfor -%}
</scroll-carousel>

<carousel-navigation aria-controls="carousel-{{ section.id }}">
  <carousel-prev-button class="circle-button ring-inset">
    {%- render 'icon' with 'arrow-left' -%}
  </carousel-prev-button>
  <carousel-next-button class="circle-button ring-inset">
    {%- render 'icon' with 'arrow-right' -%}
  </carousel-next-button>
</carousel-navigation>
```

## レスポンシブ画像

```liquid
{%- assign sizes = '(max-width: 699px) 100vw, 50vw' -%}

<picture>
  {%- if block.settings.mobile_image != blank -%}
    <source
      media="(max-width: 699px)"
      srcset="{{ block.settings.mobile_image | image_url: width: 400 }} 400w, {{ block.settings.mobile_image | image_url: width: 600 }} 600w, {{ block.settings.mobile_image | image_url: width: 800 }} 800w"
      width="{{ block.settings.mobile_image.width }}"
      height="{{ block.settings.mobile_image.height }}"
    >
  {%- endif -%}

  {{- block.settings.image | image_url: width: block.settings.image.width | image_tag:
    sizes: sizes,
    widths: '200,400,600,800,1000,1200,1400,1600',
    loading: 'lazy'
  -}}
</picture>
```

## 遅延読み込み制御

ファーストビューの画像は lazy を外す:

```liquid
{%- if forloop.first -%}
  {%- assign loading_strategy = nil -%}
  {%- assign fetch_priority = 'high' -%}
{%- else -%}
  {%- assign loading_strategy = 'lazy' -%}
  {%- assign fetch_priority = 'low' -%}
{%- endif -%}
```

## CSS外部ファイルパターン（コード量が多い場合）

```liquid
{{ 'c-[section-name].css' | asset_url | stylesheet_tag }}
```

CSS重複防止が必要な場合（同一セクションが複数回配置される可能性がある場合）:

```liquid
{%- unless c_section_name_css_loaded -%}
  {%- assign c_section_name_css_loaded = true -%}
  {{ 'c-[section-name].css' | asset_url | stylesheet_tag }}
{%- endunless -%}
```

## チェックリスト

実装完了時に確認:

- [ ] `c-` プレフィックスが全ファイルに適用されている
- [ ] テーマプロファイルが該当する場合、Schema共通設定（color_scheme 等）が含まれている
- [ ] `{{ block.shopify_attributes }}` が各blockに含まれている
- [ ] 画像にレスポンシブ対応（sizes, widths）が設定されている
- [ ] テーマの命名規則に従っている
- [ ] 既存カスタム要素を流用している（新規JSの作成を最小限に）
- [ ] 変更禁止ファイルに触れていない
- [ ] `/shopify-schema-validator` で検証済み
