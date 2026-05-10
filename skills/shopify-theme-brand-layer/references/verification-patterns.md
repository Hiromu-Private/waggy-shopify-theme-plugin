# 検証パターン

Brand 層の変更が正しく動作しているかを効率的に確認する方法。すべて手動で目視確認するのは現実的でないので、**同値クラス分割** + **JS による computed style 確認**で証明する。

## 検証ツール

| ツール | 用途 |
|---|---|
| `shopify theme dev --store {store}.myshopify.com` | ローカルプロキシ起動。CDN キャッシュなしで即時反映 |
| Playwright MCP | ブラウザ操作・computed style 取得・スクリーンショット |
| `grep` / `Read` | 既存 Focal CSS の上書き対象を確認 |

## 同値クラス分割（フォールスルー機構の証明）

すべてのクラス・アイコンを個別検証するのは非現実的。**2 つの同値クラス**に分けて、各 1 サンプルだけ検証すれば全体動作が保証される。

### Icon Brand override の場合

| 同値クラス | 期待動作 | 検証サンプル |
|---|---|---|
| **Brand override 対象**（`brand-icons.liquid` に case あり）| Brand SVG が描画され、`icon--brand` クラスが付く | `nav-arrow-right` |
| **Brand override 対象外**（case なし）| Focal 既定 SVG が描画され、`icon--brand` クラスは付かない | `close` / `header-search` |

両方が期待通りなら、**フォールスルー機構が正しく動作している = 残りのアイコンも実装上保証される**。

### Button 値上書きの場合

| 同値クラス | 期待動作 | 検証サンプル |
|---|---|---|
| **`brand-button.css` で上書き対象** | フォント 12px / weight 400 / letter-spacing 0.48px | `.button.button--primary`（商品ページの「カートに追加」等）|
| **対象外**（`.button--text` 等）| Focal 既定値のまま | `.button.button--text`（テキストリンク風ボタン）|

## Playwright MCP による検証手順

### Step 1: shopify theme dev を起動

```bash
shopify theme dev --store {store}.myshopify.com
```

バックグラウンドで起動し、出力ログから preview URL を取得（毎回ポート番号が変わる）。

### Step 2: Playwright で URL を開く

```javascript
mcp__playwright__browser_navigate({ url: "http://127.0.0.1:{port}" })
```

### Step 3: computed style を JS 経由で取得

```javascript
mcp__playwright__browser_evaluate({ function: `() => {
  // Brand 上書き対象クラスの computed style を取得
  const btn = document.querySelector('.button--primary');
  const cs = getComputedStyle(btn);
  return {
    fontSize: cs.fontSize,
    fontWeight: cs.fontWeight,
    letterSpacing: cs.letterSpacing,
    paddingLeft: cs.paddingLeft,
    paddingRight: cs.paddingRight,
    backgroundColor: cs.backgroundColor,
    color: cs.color,
    // CSS 変数も確認
    buttonBgVar: cs.getPropertyValue('--button-background').trim()
  };
}`})
```

### Step 4: CSS 変数の伝播を確認

```javascript
mcp__playwright__browser_evaluate({ function: `() => {
  const root = getComputedStyle(document.documentElement);
  return {
    'primary-button-background': root.getPropertyValue('--primary-button-background').trim(),
    'brand-tracking-button': root.getPropertyValue('--brand-tracking-button').trim(),
  };
}`})
```

`:root` に Brand トークンが正しく注入されているか確認。

### Step 5: CSS 読み込み順序を確認

```javascript
mcp__playwright__browser_evaluate({ function: `() => {
  return Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(l => l.href.split('/').pop().split('?')[0]);
}`})
```

期待: `theme.css → brand-tokens.css → brand-button.css → ...` の順序。

### Step 6: スクリーンショットで目視確認

```javascript
mcp__playwright__browser_take_screenshot({ filename: "verification.png", fullPage: false })
```

## よくある検証時の落とし穴

### 落とし穴 1: `:root` の値は正しいのに要素レベルで違う

**症状**: `--primary-button-background: 0, 0, 0` が `:root` で確認できるのに、`.button--primary` の `--button-background` が別の値になっている。

**原因**: セクション内の inline `<style>` で個別上書きされている可能性（slideshow 等）。要素から親方向に CSS 変数を辿って確認する:

```javascript
() => {
  const btn = document.querySelector('.button--primary');
  const path = [];
  let el = btn;
  while (el && el !== document.documentElement) {
    path.push({
      classes: el.className.slice(0, 80),
      'button-background': getComputedStyle(el).getPropertyValue('--button-background').trim()
    });
    el = el.parentElement;
  }
  return path;
}
```

詳細は `pitfalls.md` の「セクション individual `<style>`」を参照。

### 落とし穴 2: ブラウザキャッシュ

`shopify theme push` 後の検証では **必ずハードリロード（Cmd+Shift+R）**。`shopify theme dev` のローカルプロキシ経由ならキャッシュ問題は最小だが、念のため。

### 落とし穴 3: shopify theme dev のポートが毎回違う

`shopify theme dev` のローカル URL は **毎回ポートが変わる**（49592, 50237 等）。CI / 自動検証スクリプトで固定 URL を仮定しないこと。

ポート取得方法:
```bash
# 起動ログから取得
shopify theme dev --store ... 2>&1
# →  Preview your theme: http://127.0.0.1:XXXXX
```

## 検証チェックリスト

Brand 層の実装後、以下を順に確認:

- [ ] `shopify theme dev` で起動できる（エラーなし）
- [ ] `brand-tokens.css` / `brand-{パーツ}.css` が `theme.css` の **後**に読み込まれている
- [ ] `:root` に `--brand-*` 変数が正しく注入されている
- [ ] 同値クラス分割: Brand 対象 1 ケース + 対象外 1 ケースで期待通り
- [ ] computed style が Figma 仕様と一致（font-size / weight / letter-spacing / padding 等）
- [ ] スクリーンショットで目視確認（ホーム / 商品ページ / カート / フォーム送信ボタン / モバイル表示）
- [ ] コンソールエラーが Brand 層由来でない（404 等のテーマ標準エラーは無視可）
- [ ] 既存セクションへの副作用なし（特に `.prev-next-button` 等のグローバル上書き時）

## 検証の "卒業" 条件

すべての変更箇所で個別検証する必要はない。**同値クラス分割で 2-3 ケース確認**すれば、残りは実装上の保証で進める。本番反映前に一度ステージング環境（unpublished theme）に push して全体検証する、という運用が現実的。

## DOM 上で Brand override 由来か識別する

すべての Brand SVG / Brand modifier には `icon--brand` のような明示的な modifier クラスを付けると、DOM 検査時に「これは Layer 3 由来」と一目で分かる。デバッグ・検証時の効率が大幅に上がる。

```html
<!-- Brand override の場合 -->
<svg class="icon icon--nav-arrow-right icon--brand">...</svg>

<!-- Focal 既定の場合 -->
<svg class="icon icon--nav-arrow-right">...</svg>
```
