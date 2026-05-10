# 実装時の落とし穴

過去のストア（OverTheCentral 等）で実証された 3 つの主要な落とし穴。実装中・検証中に必ずこれらをチェックする。

## 落とし穴 ①: セクション individual `<style>` がストア設定を上書きする

### 症状

`config/settings_data.json` で `primary_button_background: "#000000"` (黒) を設定し、`:root` の `--primary-button-background: 0, 0, 0` も確認できているのに、ホームのヒーロースライドの primary ボタンが **白背景・黒文字** で表示される。

### 原因

Focal の slideshow / hero 等のセクションは、各 block の中に inline `<style>` タグを生成し、ブロック単位で CSS 変数を再定義する設計（"scoped section styles"）:

```html
<style>
  #block-template--XXX__slideshow-slide-2 {
    --heading-color: 255, 255, 255;
    --text-color: 255, 255, 255;
    --primary-button-background: 255, 255, 255;  /* ← スライド側で白に上書き */
    --primary-button-text-color: 0, 0, 0;
  }
</style>
```

これは Focal の意図的な設計（管理者が「このスライドだけボタン色を変えたい」を実現するため）で、削除はできない。

### 影響範囲

- `settings_data.json` の `primary_button_*` を変えても、**スライド単位 / セクション単位で個別オーバーライドされる箇所には反映されない**
- 主に slideshow / hero 系セクションが該当

### 対処法

1. **正常な挙動として受け入れる**: スライドごとに個別の見た目を許容する設計と理解する
2. **schema 側で Brand modifier を選べるようにする**: 「ボタンスタイル: Primary / Outline White」のような選択肢を block schema に追加し、`{%- case block.settings.button_style -%}` で `.button--brand-outline-white` 等の modifier を適用
3. **Figma で個別仕様として扱う**: ヒーローの白枠ボタンは `Btn / Outline / White`（= `.button--brand-outline-white`）として独立カタログ化

### 検証方法

要素から親方向に CSS 変数を辿って、どこで上書きされているか特定:

```javascript
() => {
  const btn = document.querySelector('.button--primary');
  const path = [];
  let el = btn;
  while (el && el !== document.documentElement) {
    path.push({
      tag: el.tagName,
      classes: el.className.slice(0, 80),
      'button-background': getComputedStyle(el).getPropertyValue('--button-background').trim(),
      hasInlineStyleTag: el.querySelector('style')?.textContent?.includes('--primary-button-background')
    });
    el = el.parentElement;
  }
  return path;
}
```

### 学び

別ストアでも slideshow 系セクションのボタン色は **`config/settings_data.json` の値変更だけでは反映されない**。schema や block 設定で個別に Brand modifier を指定する必要がある。

---

## 落とし穴 ②: settings_data.json に「未定義キー」がある

### 症状

`config/settings_data.json` の `current` ブロックに `primary_button_background` はあるのに、`primary_button_text_color` が **存在しない**。値を変えようとして grep しても引っかからない。

### 原因

Focal の `settings_schema.json` は多数のキーを定義しているが、preset の `current` 値として明示されていないキーは、Focal の schema default が暗黙的に使われる。設定値がデフォルト = JSON に書く必要がない、という Shopify の仕様。

### 対処法

値変更時は **「既存キーの値を変える」だけでなく「未定義キーを新規追加する」必要がある**:

```diff
   "primary_button_background": "#000000",
+  "primary_button_text_color": "#ffffff",
   "secondary_button_background": "#ffffff",
   "secondary_button_text_color": "#000000",
```

### 確認手順

1. 該当キーが `current` ブロックに存在するか確認（grep）
2. 存在すれば値を書き換え
3. 存在しなければ **新規追加**（隣接する論理的に近いキーの直下に挿入）

```bash
grep -n "primary_button" config/settings_data.json
```

`current` ブロック以外（`presets` 配下）にも同名キーがあるが、それは **別の preset 定義**で、現在のストアの見た目には影響しない。`current` ブロック（通常 L11 あたり開始）の中だけが対象。

### 学び

settings.json は「明示的に書かれていない = Focal default」という前提を理解する。Brand 化の際は schema を Read してデフォルト値を確認し、必要に応じて current に明示追加する。

---

## 落とし穴 ③: Focal の責務分離を破ると見た目が壊れる

### 症状

`.button` の高さを変えたくて Brand 層で `padding: 16px 32px` を当てたら、line-height との整合が崩れて文字が縦中央でなくなった。

### 原因

Focal `.button` は **責務分離設計**:

```css
/* Focal 標準 */
.button {
  line-height: var(--button-height);  /* 高さは line-height で制御 */
  padding: 0 30px;                     /* 横は padding で制御 */
}
```

縦は `line-height: var(--button-height)`（設定 `button_height` で 48px / 56px 等）、横は `padding: 0 30px` という分業。

Brand 層で `padding: 16px 32px` のように縦にも値を入れると、line-height との二重指定になり、ボタン全体の高さが想定外になる。

### 対処法

Brand 層では **横 padding のみ上書き**:

```css
/* OK */
.button:not(.button--text) {
  padding: 0 32px;  /* 縦は触らない */
}
```

```css
/* NG */
.button:not(.button--text) {
  padding: 16px 32px;  /* 縦に値を入れると line-height と衝突 */
}
```

ボタン高さを変えたい場合は `config/settings_data.json` の `button_height` を変える（Layer 2）。

### Focal の他の責務分離パターン

| プロパティ | 責務 |
|---|---|
| 縦サイズ | `line-height: var(--{...}-height)` で制御 |
| 横サイズ | `padding` で制御 |
| 色 | `--{...}-background` / `--{...}-text-color` 等の CSS 変数 |
| サイズ系（border-radius / border-width 等）| 直接の固定値 |

Brand 層で上書きする時、これらの責務を **混ぜない** こと。

### 学び

既存テーマの設計思想（責務分離）を尊重する。Brand 層で「全部書き換え」するのではなく、**「Focal の意図を読み取り、必要な部分だけ拡張する」**。これが Layer 3 が長期的に機能する条件。

---

## 落とし穴 ④（補足）: shopify CLI のポートが毎回変わる

### 症状

`shopify theme dev` のローカル URL を `http://127.0.0.1:9292` と決め打ちしたら、別のポートで起動して接続失敗。

### 原因

`shopify theme dev` は空きポートを動的に割り当てる（49592 / 50237 等、毎回異なる）。

### 対処法

`shopify theme dev` 起動時の出力ログから preview URL を取得する:

```bash
# Background で起動
shopify theme dev --store {store}.myshopify.com 2>&1
# 出力例:
#   Preview your theme: http://127.0.0.1:50237
```

ログを TaskOutput / BashOutput で読み取り、URL 部分を抽出する。

---

## 落とし穴 ⑤（補足）: icon.liquid の末尾形式

### 症状

`snippets/icon.liquid` の末尾に `{%- endif -%}` を追加しようと Edit で末尾を指定したら、改行 / 空白の関係で old_string がマッチしない。

### 原因

Focal の `icon.liquid` の末尾は **改行なしで `{%- endcase -%}` が直接 EOF に接している**ことがある:

```
    </svg>
{%- endcase -%}
```
(↑ ファイルの最終バイトが `-%}` で改行なし)

### 対処法

`tail -3 snippets/icon.liquid` で末尾形式を確認してから Edit する。**Liquid ファイルの末尾改行有無はファイルごとに異なる**ので、必ず Read で確認。

---

## 落とし穴 ⑥（補足）: 既存 Focal クラスの重複定義に注意

### 症状

`brand-button.css` で `.button:not(.button--text) { font-size: 12px; }` を書いたが、一部のボタンは依然として元のサイズで表示される。

### 原因

Focal `theme.css` は `.button` を `.shopify-challenge__button` / `#shopify-product-reviews .spr-button` 等の **別セレクタと一緒に定義**している場合がある:

```css
/* Focal 標準 */
.button:not(.button--text),
.shopify-challenge__button,
#shopify-product-reviews .spr-summary-actions-newreview,
#shopify-product-reviews .spr-button {
  font-size: calc(var(--base-font-size) - 3px);
  ...
}
```

`brand-button.css` でも同じ並列セレクタを書かないと、`.shopify-challenge__button` 等は Focal 既定のままになる。

### 対処法

Focal 側の定義を grep で確認し、並列セレクタも上書き対象に含める:

```css
/* Brand 層 */
.button:not(.button--text),
.shopify-challenge__button,
#shopify-product-reviews .spr-summary-actions-newreview,
#shopify-product-reviews .spr-button {
  font-size: 12px;
  font-weight: 400;
  letter-spacing: var(--brand-tracking-button);
}
```

---

## 落とし穴チェックリスト

Brand 層実装の各段階で:

- [ ] セクション individual `<style>` で個別上書きされる箇所はないか確認したか（特に slideshow / hero）
- [ ] `settings_data.json` の `current` ブロックに該当キーがあるか / 無ければ新規追加したか
- [ ] Focal の責務分離（縦は line-height、横は padding）を守っているか
- [ ] Focal `theme.css` の並列セレクタも上書き対象に含めたか
- [ ] `shopify theme dev` のポート番号は固定値で決め打ちしていないか
- [ ] icon.liquid 等を Edit する時、ファイル末尾の改行有無を確認したか
