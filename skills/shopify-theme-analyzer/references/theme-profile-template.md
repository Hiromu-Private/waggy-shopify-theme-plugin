# テーマプロファイル テンプレート

このテンプレートに従い `document/theme-profile.md` を生成する。
各項目は分析結果で埋め、具体例やコードスニペットを必ず含めること。

---

```markdown
# テーマプロファイル

## 基本情報

| 項目 | 値 |
|------|-----|
| テーマ名 | |
| バージョン | |
| 開発元 | |
| サポートURL | |
| 分析日 | |

## CSS構造

### 変更禁止ファイル
- (一覧: main.css, base.css 等)

### 流用可能コンポーネントCSS
- (一覧: component-slider.css, component-accordion.css 等)

### 命名規則
(BEM / OOCSS / 独自 + 具体例)

例:
- ブロック: `.card`
- エレメント: `.card__heading`
- モディファイア: `.card--standard`

### ブレークポイント

| 名前 | 値 | 用途 |
|------|-----|------|
| | | |

### CSS変数（主要なもの）

カラー:
- `--color-foreground`: (値と使い方)
- `--color-background`: (値と使い方)

フォント:
- (変数一覧)

スペーシング:
- (変数一覧)

## JS構造

### 再利用可能コンポーネント

| コンポーネント | 要素名/クラス | CSS | JS | 用途 |
|--------------|-------------|-----|-----|------|
| | | | | |

### 外部ライブラリ
- (一覧、またはなし)

### イベントシステム
(PubSub / CustomEvent / 独自の説明 + 使い方)

## セクション構造パターン

### CSS読み込み
方式: (stylesheet_tag / link tag / 独自)
重複防止: (パターンA: Liquid変数チェック / パターンB: タグ自体の機能 / なし)

コード例:
```liquid
{{ 'component-example.css' | asset_url | stylesheet_tag }}
```

### HTML構造テンプレート

```liquid
{%- style -%}
  .section-{{ section.id }}-padding {
    padding-top: {{ section.settings.padding_top | times: 0.75 | round: 0 }}px;
    padding-bottom: {{ section.settings.padding_bottom | times: 0.75 | round: 0 }}px;
  }
  @media screen and (min-width: 750px) {
    .section-{{ section.id }}-padding {
      padding-top: {{ section.settings.padding_top }}px;
      padding-bottom: {{ section.settings.padding_bottom }}px;
    }
  }
{%- endstyle -%}

<div class="color-{{ section.settings.color_scheme }} gradient">
  <div class="section-{{ section.id }}-padding">
    <div class="page-width">
      <!-- コンテンツ -->
    </div>
  </div>
</div>
```

### カラースキーム
(適用方法 + コード例)

### パディング
(実装パターン + コード例)

## グリッドシステム

クラス名:
- (例: `.grid`, `.grid__item`, `.grid--2-col-tablet`)

使い方:
```liquid
<ul class="grid grid--2-col-tablet grid--4-col-desktop">
  <li class="grid__item">...</li>
</ul>
```

## 画像パターン

レスポンシブ画像の実装方法:
```liquid
(テーマ固有のコード例)
```

## セクション作成ルール

### "c-" プレフィックス

| 対象 | 例 |
|------|-----|
| セクションファイル名 | `sections/c-[name].liquid` |
| CSSファイル名 | `assets/c-[name].css` |
| JSファイル名 | `assets/c-[name].js` |
| スニペットファイル名 | `snippets/c-[name]-item.liquid` |
| Schema name | `"name": "c-[日本語名]"` |

### CSS重複読み込み防止
(テーマに適したパターンを記載)

### 既存CSS/JS保護ルール
- グローバルCSS（変更禁止ファイル一覧）は編集しない
- 再利用可能コンポーネントは新規に同等機能を作らず流用する
```
