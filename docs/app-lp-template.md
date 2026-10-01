# アプリLPテンプレート

新しいアプリLPを追加するときは、現在のextensionless URL、ブランド資産配置、manifest駆動の検証に合わせます。

## 1. アプリディレクトリ

スラッグを`my-app`とした場合、次の4ファイルを作成します。

```text
apps/my-app/
├── index.html
├── privacy.html
├── terms.html
└── contact.html
```

リポジトリ内のファイル名には`.html`を使用しますが、公開リンクには`.html`を含めません。

```text
/apps/my-app/
/apps/my-app/privacy
/apps/my-app/terms
/apps/my-app/contact
```

## 2. 公開manifest

`tool/site_manifest.json`の`apps`へアプリを追加します。

```json
{
  "slug": "my-app",
  "og_image": "og-my-app.png",
  "screenshots": [],
  "expected_real_screens": 0
}
```

- `screenshots`: `assets/apps/{slug}/screenshots/`に置く実画面画像名
- `expected_real_screens`: JavaScript実行後に表示される実画面画像数
- 実画面を使用しないLPは空配列と`0`を指定

HTML数、OGP対応、sitemap、ブラウザ監査対象をコードへ個別にハードコードしないでください。

## 3. OGP画像

```text
assets/brand/og-my-app.png
```

要件:

- PNG
- 1200×630
- 1MB未満
- HTMLの`og:image`と`twitter:image`を同じURLへ統一

## 4. 共通資産

全ページでドメインルート基準の絶対パスを使用します。

```html
<link rel="icon" href="/assets/brand/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/styles.css">
<script src="/assets/app.js"></script>
```

アプリ固有JavaScriptがある場合は、共通JavaScriptの後に読み込みます。

## 5. URLとmetaタグ

各ページに次を1件ずつ設定します。

- `title`
- `meta[name="description"]`
- `link[rel="canonical"]`
- `meta[property="og:title"]`
- `meta[property="og:description"]`
- `meta[property="og:url"]`
- `meta[property="og:image"]`
- `meta[name="twitter:card"]`
- `meta[name="twitter:image"]`

例:

```html
<link rel="canonical" href="https://neoenox-apps.pages.dev/apps/my-app/privacy">
<meta property="og:url" content="https://neoenox-apps.pages.dev/apps/my-app/privacy">
<meta property="og:image" content="https://neoenox-apps.pages.dev/assets/brand/og-my-app.png">
<meta name="twitter:image" content="https://neoenox-apps.pages.dev/assets/brand/og-my-app.png">
```

## 6. 内部リンク

```html
<a href="/apps/my-app/">アプリLP</a>
<a href="/apps/my-app/privacy">プライバシーポリシー</a>
<a href="/apps/my-app/terms">利用規約</a>
<a href="/apps/my-app/contact">お問い合わせ</a>
```

`privacy.html`のような公開リンクは禁止です。CIが検出します。

## 7. 法務ページ

公開前に、実際のアプリ実装と一致するように次を確定します。

- 取得・保存する情報
- 外部送信の有無
- SDKと外部サービス
- 広告、課金、分析、クラッシュレポート
- データ削除方法
- 問い合わせ先
- 免責条項と適用法令上の制限

公開用ページにTODO注記を残さないでください。

## 8. 追加時に更新するファイル

- `tool/site_manifest.json`
- ルート`index.html`のカード
- `sitemap.xml`
- `assets/brand/og-{slug}.png`
- 必要に応じてアプリ固有CSS／JavaScript／スクリーンショット
- ブラウザ操作がある場合は専用Puppeteer監査

`tool/prepare_site.sh`と`tool/validate_site.py`はmanifestから検証するため、通常はアプリ名ごとの分岐を追加しません。
