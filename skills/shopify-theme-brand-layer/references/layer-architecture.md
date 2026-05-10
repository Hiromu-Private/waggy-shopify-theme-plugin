# 4 レイヤーアーキテクチャ

Shopify テーマ（Focal v13.0.0 等の有料上位テーマ）でブランド固有の見た目を実装する時、すべての判断は「**4 つの層のうちどこに書くか**」を決めることから始まる。層を間違えるとテーマアップデートで壊れるか、別ストアへの横展開時に大量のリネーム作業が発生する。

## 4 レイヤー構造

| 層 | 名前 | 触り方 | 具体物 | 命名 |
|---|---|---|---|---|
| **Layer 1** | Focal 標準コード | **編集禁止** | `assets/theme.css` / `theme.js` / `snippets/css-variables.liquid` 等 — テーマ提供元が `git pull` で更新する対象 | Focal 既定（`.button`, `.label`, `.heading` 等） |
| **Layer 2** | Focal 標準設定値 | 管理画面 or `config/settings_data.json` 編集 | 既存スキーマ項目（`primary_button_background` 等） | スキーマ定義済みキー名 |
| **Layer 3** | **Brand 層**（このスキルの主戦場）| `brand-*.css` / `brand-*.liquid` を新規追加 | `assets/brand-*.css` / `--brand-*` 変数 / `.{base}--brand-{name}` modifier | **`brand-` 接頭辞**（ストア非依存） |
| **Layer 4** | 新規セクション / コンポーネント | `c-*` で新規作成 | `sections/c-*.liquid` / `assets/c-*.css` / `<c-*>` カスタム要素 | **`c-` 接頭辞**（Focal セクション規約）|

## 判断フロー

新しいデザイン要件が来たら、上から順に試す:

```
[1] Layer 2 の設定値で表現できるか？
    Yes → config/settings_data.json の値変更だけで完結（最小コスト）
    No  ↓

[2] 既存 Focal クラスの値（色・サイズ・余白）だけ変えれば足りるか？
    Yes → Layer 3。brand-{パーツ名}.css の中で
          .label--subdued { background: transparent; ... } のように
          クラス名を変えずに値だけ再定義
    No  ↓

[3] 既存 Focal クラスに新しい見た目バリエーションを足したいか？
    Yes → Layer 3。新規 modifier .{base}--brand-{name} を追加
          例: .button--brand-outline-white（暗背景上 CTA）
    No  ↓

[4] Focal にない完全新規セクション・コンポーネントか？
    Yes → Layer 4。c-{name}.liquid / .css を新規作成
          （Focal セクション規約に従う、theme-profile.md 参照）
```

## Layer 3 と Layer 4 の使い分け（最頻出の混乱点）

| 状況 | Layer | 例 |
|---|---|---|
| 既存 `.button` の **色だけ**変えたい | Layer 3 (brand-button.css で値上書き) | Figma 仕様の黒背景白文字に |
| 既存 `.button` に **新しいバリエーション**を足したい | Layer 3 (`.button--brand-outline-white`) | 暗背景上の CTA |
| 既存 `.label--subdued` の見た目を全面変更 | Layer 3 (brand-label.css で値上書き) | Sold out バッジを透過枠に |
| 商品カードのカルーセルセクション**自体**を新規追加 | Layer 4 (`c-feature-cards`) | テーマにない新しいセクション |
| `.button--brand-outline-white` という新規 modifier | **Layer 3**（`c-` ではない）| Focal `.button` を基底に再利用するため |

**よくある間違い**: `.c-button--outline-white` のような名前を付けてしまう。これは `c-` の意味（新規セクション）と衝突する。Focal `.button` を基底に再利用しているのだから、`brand-` 接頭辞で `.button--brand-outline-white` が正しい。

## Layer 3 の核心原則: Liquid を一切触らない

Layer 3 で **既存 Focal クラスの値を上書きする時、Liquid の出力 HTML は絶対に変更しない**。

理由:
- Focal が Liquid を更新しても、Brand 層の CSS は無関係に動き続ける
- `<span class="label label--subdued">SOLD OUT</span>` というマークアップを変えずに、CSS だけで見た目を変える
- これによりテーマアップデートに対する追従コストが最小化される

例:

```css
/* OK: Layer 3 で .label--subdued の値を再定義（クラス名は変えない） */
.label--subdued {
  background: transparent;
  color: rgb(0, 0, 0);
  border: 1px solid rgb(0, 0, 0);
}
```

```liquid
<!-- NG: Layer 3 で Liquid 側のクラス名を書き換える -->
<!-- これをやると Focal のスニペット更新時にコンフリクト -->
<span class="label label--brand-sold-out">SOLD OUT</span>
```

## 読み込み順序（layout/theme.liquid）

```liquid
{# 1. Focal 標準（変更禁止）#}
<link rel="stylesheet" href="{{ 'theme.css' | asset_url }}">

{# 2. Brand トークン定義 — 標準より後、上書きより前 #}
<link rel="stylesheet" href="{{ 'brand-tokens.css' | asset_url }}">

{# 3. Brand 上書き — 一番最後 = 最強の優先度 #}
<link rel="stylesheet" href="{{ 'brand-button.css' | asset_url }}">
<link rel="stylesheet" href="{{ 'brand-label.css' | asset_url }}">
<link rel="stylesheet" href="{{ 'brand-prev-next-button.css' | asset_url }}">

{# 4. 各セクションの c-*.css は section 側で個別読み込み（変更なし）#}
```

順序が逆だと CSS の優先度で Focal 標準が勝ってしまい、Brand 上書きが効かない。

## Layer of Truth（情報の出所）

| 真実 | 場所 | 意味 |
|---|---|---|
| **デザイン真実** | Figma | 色・余白・タイポの最終決定権 |
| **設定真実 / 値** | `config/settings_data.json` + 管理画面 | Layer 2 の現在値 |
| **Focal 実装** | `assets/theme.css`（Layer 1） | 変更禁止。クラス定義の出発点 |
| **Brand 実装** | `assets/brand-*.css`（Layer 3） | Focal 上書き + ストア固有トークン定義 |
| **新規コンポーネント** | `assets/c-*.css` / `sections/c-*.liquid`（Layer 4） | 単発で追加するパーツ |
| **対応表** | `document/design-system.md` | Figma → Layer 1〜4 のマッピング |

## なぜ "Brand 層" という独立名前空間が必要か

業界比較:
- Salesforce Lightning Design System: "Aura → Brand → Component" の 3 段カスケード
- Adobe Spectrum: "Global → Alias → Component" のトークン階層
- IBM Carbon: "Core → Theme → Component" の階層

**Layer 3 = Brand 層** は、これら主要デザインシステムが採用する「**フレームワーク基底は触らず、自分の名前空間でだけ拡張する**」パターンの Shopify 版。

ストア固有名（`otc-` 等）を避けて `brand-` で固定する理由は、**1 つのデザインシステム設計を複数ストアに横展開できる**ようにするため。`brand-button.css` を別ストアにコピーする時、リネーム作業ゼロで動く。

## チェックリスト: 新規変更時の Layer 確認

- [ ] この変更は Layer 2 の設定値で表現可能か？（最初に試す）
- [ ] Layer 3 で実装する場合、既存 Focal クラスの **値だけ**変えるパターンか、**新規 modifier** を足すパターンか
- [ ] 新規 modifier の名前は `.{base}--brand-{name}` 形式か（`.c-{name}` でない）
- [ ] Liquid 出力 HTML は変更していないか
- [ ] `brand-*.css` のファイル名にストア名（`otc-` 等）を含めていないか
- [ ] `layout/theme.liquid` で `theme.css` の **後**に読み込んでいるか
- [ ] `document/design-system.md` の §7 / §8 にチェックリスト項目を追加したか
