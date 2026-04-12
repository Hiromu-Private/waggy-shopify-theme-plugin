# セクション設計書 出力テンプレート

このテンプレートに従い `document/c-[section-name]-spec.md` を生成する。
各項目は設計内容で埋め、テーマプロファイルの情報を反映すること。

---

```markdown
# [c-セクション名] セクション設計書

## 1. テーマ情報

（theme-profile.md から転記）

| 項目 | 値 |
|------|-----|
| テーマ名 | |
| CSS命名規則 | |
| ブレークポイント | |
| CSS重複防止方式 | |

## 2. 概要

| 項目 | 内容 |
|------|------|
| セクション名 | c-[名前] |
| Schema name | c-[日本語名] |
| ファイル名 | sections/c-[name].liquid |
| 用途 | |
| 配置可能テンプレート | |

## 3. ファイル構成

### 新規作成ファイル

| ファイル | 種別 | 説明 |
|---------|------|------|
| sections/c-[name].liquid | セクション | メインファイル |
| assets/c-[name].css | CSS | セクション固有スタイル（必要な場合） |
| assets/c-[name].js | JS | セクション固有スクリプト（必要な場合） |

### 既存アセットの流用

| アセット | 用途 | 流用方法 |
|---------|------|---------|
| （テーマプロファイルから特定） | | |

## 4. HTML構造（DOMツリー）

テーマ命名規則に準拠したBEMクラス名付きDOMツリーを記載。

```
div.c-section-name (section wrapper)
├── style (inline padding styles)
├── div.color-{{ section.settings.color_scheme }}
│   └── div.section-{{ section.id }}-padding
│       └── div.page-width
│           ├── h2.c-section-name__heading
│           ├── ul.grid.grid--2-col-tablet.grid--4-col-desktop
│           │   └── li.grid__item (for block in blocks)
│           │       └── ...
│           └── ...
```

### 各要素の説明

| 要素 | クラス名 | 説明 | 対応設定 |
|------|---------|------|---------|
| | | | |

## 5. Schema設計

### 5-A. セクション設定 (settings)

| # | type | id | label | default | 備考 |
|---|------|----|-------|---------|------|
| 1 | header | - | レイアウト設定 | - | グループヘッダー |
| 2 | | | | | |

### 5-B. ブロック定義 (blocks)

#### ブロック: [type_name]「[日本語名]」

| 属性 | 値 |
|------|-----|
| type | |
| name | |
| limit | |

ブロック設定:

| # | type | id | label | default | 備考 |
|---|------|----|-------|---------|------|
| 1 | | | | | |

### 5-C. プリセット (presets)

| プリセット名 | デフォルトブロック |
|-------------|-----------------|
| | |

## 6. レスポンシブ動作

| 画面幅 | レイアウト | 備考 |
|--------|----------|------|
| モバイル (～[BP1]px) | | |
| タブレット ([BP1]px～) | | |
| デスクトップ ([BP2]px～) | | |

## 7. CSS設計メモ

### CSS読み込み（重複防止付き）

（テーマプロファイルに基づくパターンを記載）

```liquid
{{ 'c-[name].css' | asset_url | stylesheet_tag }}
```

### 新規CSS（c-[name].css）

| クラス | 役割 | 主なプロパティ |
|--------|------|--------------|
| | | |

### インラインスタイル

（パディング等の動的スタイル）

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
```

## 8. アクセシビリティ

- [ ] 適切なセマンティックHTML
- [ ] 画像: alt, loading="lazy", width/height
- [ ] キーボードナビゲーション対応
- [ ] 見出し階層の適切さ（h1はロゴ/FV専用）

## 9. 実装時の注意事項

### 既存コンポーネント流用

（具体的な使い方を記載）

### 変更禁止ファイル

（テーマプロファイルから転記）

### Liquid安全ルール

- パイプ演算子をif条件内で直接使わない（assignで事前計算）
- 小数リテラル禁止（| divided_by: 100.0 を使用）
- 空値チェック: {% if value != blank %}
```
