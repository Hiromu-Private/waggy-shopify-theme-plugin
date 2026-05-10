# 命名規則

Layer 3（Brand 層）の命名は、**ストア非依存** + **Focal 規約と衝突しない** の 2 つを満たすために `brand-*` 接頭辞で固定する。

## 重要原則

| 原則 | 理由 |
|---|---|
| **ストア名を含めない** | `otc-button.css` のような命名だと、TokyoCrafts や BOVERA に横展開する時にリネームが必要。`brand-button.css` ならそのままコピーすれば動く |
| **`c-` は使わない** | `c-` は Focal セクション規約で「新規セクション・コンポーネント」用に予約されている（`c-feature-cards.liquid` 等）。Layer 3 と衝突する |
| **`theme-` は使わない** | Focal の `theme.css` / `theme.js` と紛らわしい。ファイル一覧で見て区別しにくい |
| **`custom-` は使わない** | Shopify メタフィールド namespace `custom.*` および既存クラス `.label--custom` と語が衝突 |

## ファイル命名

| 役割 | パターン | 例 |
|---|---|---|
| トークン定義（CSS 変数） | `assets/brand-tokens.css` | （単一ファイルで全トークン定義） |
| パーツ別 CSS 上書き | `assets/brand-{パーツ名}.css` | `brand-button.css` / `brand-label.css` / `brand-prev-next-button.css` / `brand-heading.css` |
| 横断的な小修正の集約 | `assets/brand-overrides.css` | （1 ファイルに収まらない時の受け皿） |
| Liquid snippet（Brand 専用）| `snippets/brand-{name}.liquid` | `snippets/brand-icons.liquid` |

**1 ファイル 1 パーツ原則**: `brand-button.css` には Button 関連だけ書く。Label の上書きは `brand-label.css` に分ける。`brand-overrides.css` 1 ファイルに全部詰めると、後で何がどこにあるか分からなくなる。

## CSS 変数命名

| 種別 | 命名 | 例 | 出所 |
|---|---|---|---|
| Focal 標準変数 | `--{name}` | `--text-color`, `--button-background` | `snippets/css-variables.liquid`（Focal 標準）|
| **Brand 固有変数** | `--brand-{name}` | `--brand-gray`, `--brand-tracking-label`, `--brand-tracking-button` | `assets/brand-tokens.css` |

**色の値は RGB カンマ区切り**（Focal の規約踏襲）:

```css
:root {
  --brand-gray: 92, 90, 90;        /* OK: rgb(var(--brand-gray)) で参照可能 */
  --brand-light-gray: 209, 209, 209;
}
```

```css
/* NG: Hex で持つと、Focal の rgba 透過パターンが使えない */
:root {
  --brand-gray: #5C5A5A;
}
```

## クラス命名

3 通りの使い分け:

### ① 既存 Focal クラスの **値だけ上書き**（最頻出・推奨）

**クラス名は変えない**。`brand-*.css` の中で再定義する。

```css
/* brand-label.css */
.label--subdued {
  background: transparent;
  color: rgb(0, 0, 0);
  border: 1px solid rgb(0, 0, 0);
}
```

なぜこれが最強か: Liquid 出力（`<span class="label label--subdued">`）を一切触らないため、Focal が Liquid を更新しても自動的に追従できる。

### ② Focal クラスに **新規 modifier を追加**

`.{base}--brand-{name}` 形式（BEM 修飾子）。

```css
/* brand-button.css */
.button--brand-outline-white {
  background: transparent;
  color: rgb(255, 255, 255);
  border: 1px solid rgb(255, 255, 255);
}
```

```liquid
<a href="{{ link }}" class="button button--brand-outline-white">View Concept</a>
```

「Focal の `.button` 基底（padding / line-height / font-family 等）を再利用しつつ、見た目バリエーションだけ Brand 化する」パターン。

### ③ Focal にない **新規 utility / state**（必要時のみ）

`.brand-{name}` 形式。

```css
/* 必要時のみ */
.brand-uppercase { text-transform: uppercase; }
```

ただし、ほとんどのケースでは ② の modifier 形式が好ましい（既存クラスとの組み合わせで使う前提）。

## 命名の決定ツリー

新しいクラスを定義する時の判断:

```
変更したいのは既存 Focal クラスか？
├─ Yes、値だけ変えたい
│    └─ クラス名は変えず、brand-{パーツ}.css に値を再定義（パターン①）
│
├─ Yes、新しいバリエーションを足したい
│    └─ .{base}--brand-{name} 形式（パターン②）
│       例: .button--brand-outline-white / .label--brand-cart
│
└─ No、Focal にない utility を作りたい
     └─ .brand-{name} 形式（パターン③、必要時のみ）
        例: .brand-uppercase
```

## ストア名を含めるべき場所（例外）

`brand-*` の原則の唯一の例外は `document/design-system.md` の Figma URL や node ID。これはストア固有のデザインソースを指すため:

```markdown
最終更新: 2026-05-10 / Figma node: `2001:68`（OverTheCentral コンポーネントパーツ一覧）
```

ファイル名・クラス名・変数名には絶対にストア名を入れない。

## 既存 Focal クラスを正しく上書きするための事前確認

Brand 層で値上書きする前に、**Focal 側のクラス定義を Read で確認する**:

```bash
grep -n "^\.button\|^\.button:" assets/theme.css | head -10
```

確認すべきポイント:
- メディアクエリで値が分岐しているか（mobile / tabletAndUp 等）
- どの CSS 変数を参照しているか（`var(--button-background)` 等）
- 重複定義（`.button:not(.button--text)` など、特定の限定子が付いているか）

これを怠ると、上書きが部分的にしか効かない / 別のクラスが上書きを打ち消す等の不具合が起きる。
