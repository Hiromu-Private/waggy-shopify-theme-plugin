# サードパーティアプリ製フォームの CV 計測

会員登録などのフォーム CV を計測する時、**実フォームがサードパーティアプリで構築されていると Shopify 標準前提の計測タグは空振りする**。この文書はその見抜き方と正解パターン。

## 問題: Liquid の customer 条件タグが発火しない

Shopify テーマの `sections/main-customers-register.liquid` 等に `{% if customer %}` で囲んだ CV 計測タグを置いても、**実フォームがサードパーティアプリで構築されている場合は発火しないことが多い**。

該当アプリ例: Bonify Customer Account Fields / Customer Fields / Helium Customer Fields 等。

### 発火しない理由

これらのアプリは**登録完了後に `/account` への自動リダイレクトを行わず、同一ページ内に完了メッセージを表示する**カスタム挙動を取る。Shopify 標準の「register → /account リダイレクト」フローが成立しないため、リダイレクト後のログイン済み状態で発火する前提のタグは永遠に空振りする。

### 実事故（CENE 案件 2026-06-03 に発覚）

「会員登録 CV 月 18 件」と計測されていたが、その 18 件は**ログイン済みユーザーが偶然 `/account/register` に直アクセスした誤計上のみ**。本来の登録は **0 件** がカウントされていた。**数字が出ているからといって正しく計測できているとは限らない**。

## 事前確認チェックリスト（実装前に必ず）

新しい CV タグを Shopify テーマに追加する前に必ず確認する:

- [ ] 1. `templates/customers/*.json` を読み、**サードパーティアプリブロック（`shopify://apps/...`）がメインセクションに使われていないか**確認
- [ ] 2. 使われていれば、そのアプリの挙動（リダイレクトの有無・完了表示形式）を**実機で 1 回テスト登録して**確認
- [ ] 3. Shopify 標準フローと違うなら、下記「MutationObserver 方式」へ切り替え
- [ ] 4. 既存タグが空振りしていないか、過去の CV 数が極端に少なくないか計測ツール管理画面（EBiS 等）で確認

## 正解パターン: MutationObserver 方式

### 構成要素

| 要素 | 実装 | 理由 |
|------|------|------|
| CV 発火トリガー | 完了メッセージのテキスト（例: 「会員登録が完了」）の出現を **MutationObserver で検知**し、その時点で `ebis.push({page_id: 'member', ...})` を発火 | リダイレクトが起きないため、DOM 変化が唯一の完了シグナル |
| メールアドレス取得 | **`input` イベントを `capture: true` で常時監視**して sessionStorage に退避 | **submit イベントは AJAX 送信時に発火しない**ので使えない |
| 二重発火防止 | sessionStorage の発火フラグ | タブごとに分離される用途に合う（検証時に新規タブが必須になる理由でもある） |
| 保険 | `sections/main-customers-account.liquid` に `customer.created_at < 600 秒` の発火条件も置く | 「登録 → ログイン → /account」パターンも拾う |

### コード骨子（register ページ側）

```html
<script>
(function () {
  var FIRED_KEY = 'ebis_register_cv_fired';
  var SUCCESS_TEXT = '会員登録が完了';  // アプリの完了メッセージ文言に合わせる（実機テスト登録で確認）

  // メールアドレス退避: input イベントを capture:true で常時監視
  // submit イベントは AJAX 送信では発火しないため使わない
  document.addEventListener('input', function (e) {
    var el = e.target;
    if (el && el.type === 'email' && el.value) {
      sessionStorage.setItem('register_email', el.value);
    }
  }, true);

  // 完了メッセージの出現を MutationObserver で検知して CV 発火
  var observer = new MutationObserver(function () {
    if (sessionStorage.getItem(FIRED_KEY)) return;  // 二重発火防止
    if (document.body.textContent.indexOf(SUCCESS_TEXT) === -1) return;
    sessionStorage.setItem(FIRED_KEY, '1');
    // ここで計測タグを発火（adebis の例。退避したメールアドレスはここで利用）
    // ebis.push({ page_id: 'member', ... });
  });
  observer.observe(document.body, { childList: true, subtree: true, characterData: true });
})();
</script>
```

### コード骨子（保険: /account ページ側）

`sections/main-customers-account.liquid` に、作成から 600 秒以内の顧客のみ発火する条件を置く:

```liquid
{% if customer %}
  {% assign now_ts = 'now' | date: '%s' | plus: 0 %}
  {% assign created_ts = customer.created_at | date: '%s' | plus: 0 %}
  {% assign age_seconds = now_ts | minus: created_ts %}
  {% if age_seconds < 600 %}
    <!-- 作成 10 分以内の顧客のみ CV 発火。
         register 側と同じ sessionStorage フラグを見て二重発火を防ぐ -->
  {% endif %}
{% endif %}
```

## アプリ設定経由の script 挿入は基本不可

アプリの「Register Success Message」等の設定欄に HTML は入っても、**`<script>` タグはサーバ側でサニタイズされて消えることが多い**（Bonify で確認済み）。アプリ設定経由の JS 挿入は基本不可と考え、テーマ Liquid 側に上記 MutationObserver 方式で実装する。

## 実装後の検証

必ず [verification-checklist.md](verification-checklist.md) に従う。特にフォーム CV は**新しいタブでの検証が必須**（sessionStorage の発火フラグが残っていると CV が飛ばない）。検証後のテスト顧客削除依頼も忘れないこと。
