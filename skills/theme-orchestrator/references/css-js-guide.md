# CSS/JS追加ガイド

テーマプロファイルの規約に従い、CSS/JSを追加するためのリファレンス。

> **前提**: 本ガイドのブレークポイント値・CSS変数名・ユーティリティクラス・カスタム要素名は**テーマ系統依存**（例の多くは Focal/Prestige 系）。実装時は必ず `docs/theme-profile.md` の規約を優先し、例をコピーする前に対象テーマに同じ仕組みが存在するか確認すること。

## CSS追加の判定

| 追加先 | いつ使う |
|--------|---------|
| セクション内 `<style>` | セクション固有・少量のCSS |
| `assets/c-[name].css` | セクション固有・大量のCSS |
| `custom.css`（追記） | テーマ全体に影響する変更、テーマオリジナルの上書き |

**注意**: テーマのコアCSS（Focal 系: `theme.css`、Dawn 系: `base.css` 等）への直接編集は禁止。`custom.css` がテーマに無い場合は assets に新規作成し `layout/theme.liquid` で読み込む。

## インラインスタイルのパターン

```liquid
<style>
  #shopify-section-{{ section.id }} {
    --columns-per-row: {{ section.settings.columns | default: 3 }};
    --gap: {{ section.settings.gap | default: '1.5rem' }};
  }

  @media screen and (max-width: 699px) {
    #shopify-section-{{ section.id }} {
      --columns-per-row: {{ section.settings.columns_mobile | default: 1 }};
    }
  }

  @media screen and (min-width: 1000px) {
    #shopify-section-{{ section.id }} {
      --columns-per-row: {{ section.settings.columns_desktop | default: section.settings.columns | default: 3 }};
    }
  }
</style>
```

## ブレークポイント

テーマプロファイルのブレークポイントに従う。以下は Focal 系の値の例（Dawn 系は 749px / 989px 等、テーマにより異なる）:

```css
/* モバイル: デフォルト（max-width: 699px） */
.element { /* モバイルスタイル */ }

/* タブレット以上 */
@media screen and (min-width: 700px) {
  .element { /* タブレットスタイル */ }
}

/* デスクトップ以上 */
@media screen and (min-width: 1000px) {
  .element { /* デスクトップスタイル */ }
}

/* ワイド */
@media screen and (min-width: 1150px) {
  .element { /* ワイドスタイル */ }
}
```

**CSSプレフィックスクラス**（Focal/Prestige 系の例。Dawn / Horizon 系には無い。theme-profile.md で提供有無を確認してから使う）:
- `sm:` = 700px以上（例: `sm:text-start`）
- `md:` = 1000px以上（例: `md:unbleed`）

## CSS変数の活用

テーマが提供するCSS変数を**新規定義より優先**して使う。変数名はテーマ固有（以下は Focal 系の例。Dawn 系は `--color-foreground` / `--font-body-family` / `--page-width` 等）:

```css
/* Good: テーマ変数を使用 */
.c-element {
  max-width: var(--container-sm-max-width);
  padding-inline: var(--container-gutter);
  font-family: var(--text-font-family);
  color: rgb(var(--text-color));
  border-color: rgb(var(--border-color));
  border-radius: var(--button-border-radius);
}

/* Bad: ハードコード値 */
.c-element {
  max-width: 980px;
  padding-inline: 1.25rem;
  font-family: Arial, sans-serif;
}
```

## テーマユーティリティクラスの活用

新規CSSを書く前に、テーマの既存ユーティリティクラスで実現できないか確認する。下表は Focal/Prestige 系の例（クラス名はテーマごとに異なる。Dawn 系: `.page-width` 等。theme-profile.md のクラス一覧を参照）:

| 用途 | 既存クラス |
|------|----------|
| コンテナ | `.container`, `.container--sm`, `.container--lg` |
| セクション間余白 | `.section-spacing` |
| 上ボーダー | `.bordered-section` |
| 縦方向スタック | `.section-stack`, `.v-stack` |
| 横方向スタック | `.h-stack` |
| テキスト整列 | `.text-center`, `.text-start`, `.text-end` |
| メディア上コンテンツ | `.content-over-media` |
| カラースキーム | `.color-scheme` |
| スクロール領域 | `.scroll-area`, `.snap-x`, `.bleed` |
| テキストスタイル | `.prose` |

## JS追加の判定

### 既存カスタム要素で実現可能か確認

下表は Focal/Prestige 系の例。カスタム要素名はテーマごとに全く異なる（Dawn 系: `slider-component` / `details-disclosure` / `modal-dialog` 等）ため、theme-profile.md か assets/ の JS で実在を確認してから使う:

| やりたいこと | 既存要素 | 新規JS不要 |
|------------|---------|----------|
| スクロールカルーセル | `scroll-carousel` | YES |
| フェードカルーセル | `effect-carousel` | YES |
| アコーディオン | `accordion-disclosure` | YES |
| タブ切り替え | `x-tabs` | YES |
| モーダル | `x-modal` | YES |
| ドロワー | `x-drawer` | YES |
| ビフォーアフター | `before-after` | YES |
| カウントダウン | `countdown-timer` | YES |
| 上記にない機能 | - | 新規JS作成を検討 |

### 新規JS作成時のパターン

```javascript
// assets/c-[section-name].js

class CSectionName extends HTMLElement {
  connectedCallback() {
    // 初期化処理
  }

  disconnectedCallback() {
    // クリーンアップ
  }
}

if (!customElements.get('c-section-name')) {
  customElements.define('c-section-name', CSectionName);
}
```

JS読み込み:
```liquid
<script src="{{ 'c-[section-name].js' | asset_url }}" defer="defer"></script>
```

## チェックリスト

- [ ] テーマのブレークポイントに従っている
- [ ] テーマのCSS変数を活用している（ハードコード値の最小化）
- [ ] テーマの命名規則に従っている
- [ ] 既存ユーティリティクラスを確認し、不要なCSS記述を避けている
- [ ] 既存カスタム要素で実現可能な機能を新規JSで作っていない
- [ ] `custom.css` への追記にはヘッダーコメントが付いている
- [ ] 変更禁止ファイルに触れていない
