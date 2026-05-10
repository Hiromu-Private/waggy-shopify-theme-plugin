# Override 戦略

Layer 3 で「Focal を上書きする」具体的な実装パターン 3 種類。

## パターン①: CSS 値上書き（最頻出）

**用途**: 既存 Focal クラスの色・余白・フォント等を Figma 仕様に合わせて変える。

**やり方**: クラス名は変えず、`brand-{パーツ}.css` の中で値を再定義。

### 例: ボタンのフォント・padding を Figma 仕様に

```css
/* assets/brand-button.css */

/* Focal の .button:not(.button--text) はメディアクエリで font-size が分岐するが、
   Brand 層では mobile/desktop ともに固定 12px に揃える */
.button:not(.button--text),
.shopify-challenge__button,
#shopify-product-reviews .spr-summary-actions-newreview,
#shopify-product-reviews .spr-button {
  font-size: 12px;
  font-weight: 400;
  letter-spacing: var(--brand-tracking-button);
}

.button:not(.button--text) {
  padding: 0 32px;  /* 縦は Focal の line-height: var(--button-height) で制御 */
}
```

**ポイント**:
- Focal の重複定義（`.shopify-challenge__button` 等の同等クラス）も含めて上書きする必要がある場合がある（grep で確認）
- 縦 padding は触らない（Focal の責務分離: 縦は line-height、横は padding）
- メディアクエリで分岐していた値を mobile/desktop 共通にする場合、メディアクエリを書かない（CSS の specificity で勝てるなら）

### 例: Sold out バッジを透過枠に

```css
/* assets/brand-label.css */

/* Focal の .label--subdued は背景色 + 白文字の "subdued" デザインだが、
   Brand 仕様は透過背景 + 黒枠 + 黒文字 */
.label--subdued {
  background: transparent;
  color: rgb(0, 0, 0);
  border: 1px solid rgb(0, 0, 0);
  font-weight: 400;
  font-size: 12px;
  line-height: 1;
  letter-spacing: var(--brand-tracking-label, 0.96px);
  padding: 8px 12px;
  border-radius: 0;
}
```

**注意**: 設定 `product_sold_out_accent`（背景色）が無意味化する。管理画面に "効かない設定" が残るリスクは、運用補足（管理者向け説明 or schema 側で `info` を追加）でカバーする。

## パターン②: 新規 modifier の追加

**用途**: 既存クラスを基底として再利用しつつ、新しい見た目バリエーションを足す。

**やり方**: `.{base}--brand-{name}` 形式の新規 modifier を CSS で定義し、Liquid の class 属性に追加する。

### 例: 暗背景上の CTA ボタン

```css
/* assets/brand-button.css */

/* 暗いヒーロー画像の上に置く CTA。透過背景・白枠・白文字 */
.button--brand-outline-white {
  background: transparent !important;
  color: rgb(255, 255, 255);
  border: 1px solid rgb(255, 255, 255);
}

.button--brand-outline-white:hover {
  background: rgba(255, 255, 255, 0.1);
}
```

```liquid
<a href="{{ link }}" class="button button--brand-outline-white">
  View Concept
</a>
```

**ポイント**:
- `!important` は Focal の `.button--primary` などが `--button-background` を強制設定する場合に必要。優先度を確認してから付ける
- セクション schema 側で「ボタンスタイル」を選択肢として持たせるなら、`{%- case block.settings.button_style -%}` で modifier を選ぶ作りにする

### 例: Heading の局所 uppercase

```css
/* assets/brand-heading.css */
.heading--brand-uppercase {
  text-transform: uppercase;
}
```

```liquid
<h2 class="heading h2 heading--brand-uppercase">Original Goods</h2>
```

グローバル設定 `heading_text_transform` を変えると全ヘディングに影響するため、局所適用したい場合に使う。

## パターン③: Icon Brand override（フォールスルー方式）

**用途**: テーマの SVG アイコンの一部を Brand 仕様に差し替えたい。

**最重要原則**: 既存の `render 'icon'` 呼び出し（テーマ内で 200+ 箇所ある）を**一切変更しない**。

**やり方**: `snippets/icon.liquid` の冒頭に「Brand SVG を先に試す」フォールスルー分岐を追加し、Brand SVG は別ファイル `snippets/brand-icons.liquid` に隔離する。

### Step A: snippets/brand-icons.liquid を新規作成

```liquid
{%- comment -%}
  Layer 3: Brand override icons.
  Figma 由来の SVG をここに列挙し、Focal 既定アイコン（snippets/icon.liquid）を上書きする。
  ここに無い `icon` 名は blank を返し、Focal の case 文にフォールスルーする。
{%- endcomment -%}

{%- capture icon_class -%}icon icon--{{ icon }} icon--brand{% if inline %} icon--inline{% endif %}{% if direction_aware %} icon--direction-aware{% endif %}{% if class %} {{ class }}{% endif %}{%- endcapture -%}

{%- case icon -%}
  {%- when 'nav-arrow-right' -%}
    <svg focusable="false" width="{{ width | default: 16 }}" height="{{ height | default: 16 }}" class="{{ icon_class }}" viewBox="0 0 16 16" fill="none">
      <path d="M2 8h12M9 3l5 5-5 5" stroke="currentColor" stroke-width="1" stroke-linecap="square"></path>
    </svg>

  {%- when 'plus' -%}
    <svg focusable="false" width="{{ width | default: 16 }}" height="{{ height | default: 16 }}" class="{{ icon_class }}" viewBox="0 0 16 16">
      <rect x="3" y="7.5" width="10" height="1" fill="currentColor"></rect>
      <rect x="7.5" y="3" width="1" height="10" fill="currentColor"></rect>
    </svg>

  {# 他の Brand override したいアイコン... #}
{%- endcase -%}
```

**ポイント**:
- すべての SVG に `icon--brand` modifier を付ける（DOM 上で Brand override 由来と識別可能に）
- `width | default: 16` パターンで、呼び出し側のサイズ指定があればそれを尊重
- Focal にない名前（例: `external-link`）も自由に追加できる
- `currentColor` で色を継承（Focal と同じパターン）

### Step B: snippets/icon.liquid 冒頭に分岐ロジックを追加

```liquid
{%- comment -%} Layer 3: Brand override が定義されていれば優先（design-system.md §5）{%- endcomment -%}
{%- capture brand_icon_html -%}
  {%- render 'brand-icons',
      icon: icon,
      width: width,
      height: height,
      class: class,
      inline: inline,
      direction_aware: direction_aware
  -%}
{%- endcapture -%}

{%- if brand_icon_html != blank -%}
  {{ brand_icon_html }}
{%- else -%}
{%- comment -%} ここから Focal 既定（既存の case 文） {%- endcomment -%}
{%- capture icon_class -%}icon icon--{{ icon }} {% if inline %}icon--inline{% endif %} {% if direction_aware %}icon--direction-aware{% endif %} {{ class }}{%- endcapture -%}

{%- case icon -%}
  {%- when 'nav-arrow-left' -%}
    {# ... 既存のすべての Focal SVG case ... #}
{%- endcase -%}
{%- endif -%}
```

**ポイント**:
- `{%- capture %}` で `brand-icons` snippet をレンダリングし、空文字でなければ Brand SVG を返す
- 空文字なら Focal 既定の case 文にフォールスルー
- 既存の `render 'icon' with 'nav-arrow-right'` 呼び出しは **一切変更不要**（Liquid 出力 = Brand 化対象 + 非対象、両方とも自動的に正しい SVG が返る）

### このパターンが優れる理由

| 観点 | フォールスルー方式（推奨）| 直接編集 | 別 snippet 方式 |
|---|---|---|---|
| 既存 `render 'icon'` 呼び出し変更 | 不要 | 不要 | 必要（200+ 箇所書き換え）|
| Focal アップデート追従 | ほぼ自動 | 手動マージ | 手動マージ |
| Brand override の見える化 | 強い（別ファイル隔離）| 弱い | 強い |
| Layer 3 原則「Liquid 触らない」| ○ | △ | × |

## 矢印 left / right の扱い（補足）

Figma が `Icon / Arrow` を 1 つしか持たない場合（左向きはミラー）、Brand 側でどう実装するか:

| 案 | 内容 |
|---|---|
| **(A) 別 SVG として独立保持**（推奨）| `nav-arrow-left` と `nav-arrow-right` を別 case として書く。`nav-arrow-right` の path を反転した静的 SVG |
| (B) CSS で反転 | `transform: scaleX(-1)` で反転。SVG 1 個で済むがアクセシビリティ・SSR FOUC 等で副作用 |

推奨は (A)。理由は Tailwind UI / Heroicons / Lucide も同じ判断（`arrow-right.svg` と `arrow-left.svg` を別ファイルで持つ）をしている。

`direction_aware` パラメータは Focal の RTL 言語対応用で、LTR で「左向きを表示」用途には使えない。流用不可。

## どのパターンを選ぶか

| 状況 | 推奨パターン |
|---|---|
| 既存 Focal クラスの色・サイズだけ変えたい | パターン① CSS 値上書き |
| 既存 Focal クラスに新しい見た目バリエーションを足したい | パターン② 新規 modifier |
| テーマの SVG アイコンの一部を Brand SVG に差し替えたい | パターン③ Icon フォールスルー |
| 設定値で表現できる範囲 | Layer 2 の `config/settings_data.json` 編集（Layer 3 ではない）|
| 完全に新しいセクション | Layer 4 の `c-*`（`brand-*` ではない）|
