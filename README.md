# アプノキ — LPサイト

生活、学び、遊び、仕事など、複数ジャンルの個人開発アプリを掲載する静的ポータルです。

- ルート: アプリ一覧
- `/apps/{app-slug}/`: アプリ専用LP
- `/apps/{app-slug}/privacy`: プライバシーポリシー
- `/apps/{app-slug}/terms`: 利用規約
- `/apps/{app-slug}/contact`: お問い合わせ

> [!IMPORTANT]
> 「あしたもつもの」の正式名称、問い合わせ先、Production originは`docs/public-identity.md`で管理します。公開表示は「あしたもつもの」、問い合わせ先は`kaenozu@gmail.com`、Production originは`https://lp-5t7.pages.dev`です。

## 公開環境

- Production URL: `https://lp-5t7.pages.dev`
- Cloudflare Pagesプロジェクト: `lp`
- 配信方式: Direct Upload
- Productionブランチ: `master`
- 自動デプロイ: GitHub Actionsの`Deploy to Cloudflare Pages`

HTML、CSS、JavaScriptだけで構成し、フロントエンドフレームワークは使用していません。

## 公開物

`tool/prepare_site.sh`が公開専用ディレクトリ`_site/`を生成します。

```text
index.html
robots.txt
sitemap.xml
_headers
assets/
apps/
```

`.github/`、`docs/`、`tool/`、`README.md`は配信しません。

`_headers`ではCSP、Permissions Policy、Referrer Policy、MIME sniffing防止、frame制限、Cross-Origin Policyを設定します。

## アプリmanifest

`tool/site_manifest.json`を公開アプリの単一の定義元として使用します。

管理項目:

- URLスラッグ
- 表示名
- 公開状態
- Google Play URL
- App Store URL
- アプリごとのOGP画像
- 実画面スクリーンショット
- JavaScript実行後に期待する実画面画像数

アプリ一覧にまだ掲載しない法務ページなどの単独ページは、同じmanifestの`standalone_pages`にパスとOGP画像を登録します。登録ページはsitemap、HTML集合、canonical、OGPの検証対象になります。

公開状態:

- `preparing`: 準備中。ストアリンクを表示しない
- `published`: 公開中。Google PlayまたはApp Storeの正式URLが必須
- `suspended`: 公開停止中。主要ストア導線を表示しない

ルートのアプリカードは`data-app-slug`、`data-release-status`、`data-release-status-label`でmanifestと対応させます。

`tool/validate_site.py`は、manifest、ポータルカード、アプリLP、ストアURLの整合を検証します。`published`なのに正式ストアURLがない場合や、準備中のLPがストアリンクを公開している場合はCIを失敗させます。

詳細は`docs/store-release.md`を参照してください。

## Search Console

Search ConsoleのHTMLタグ確認値は、Repository variable `SEARCH_CONSOLE_VERIFICATION`からデプロイ成果物へ注入します。

```text
<meta name="google-site-verification" content="Repository variableの値">
```

値が未設定の場合、検証タグは出力しません。Googleアカウント上でURLプレフィックスプロパティを作成し、確認値を発行してから設定します。

手順は`docs/search-console.md`を参照してください。

## デプロイ

`master`へのpushで次を実行します。

1. `_site/`を生成
2. Search Console確認値が設定済みならルートへ注入
3. 全JavaScriptの構文を確認
4. HTML、公開状態、ストアURL、画像、canonical、OGP、sitemap、内部リンクを検証
5. Cloudflare Pagesへデプロイ
6. デプロイ固有URLの全公開ページ、資産、セキュリティヘッダーを検証
7. Productionの全公開ページ、資産、セキュリティヘッダーを検証
8. commit statusを記録

記録するStatus:

- `cloudflare-pages-production`
- `cloudflare-pages-brand-verification`
- `production-browser-verification`
- `lighthouse-production`
- `production-accessibility-semantics`

Production検証は`sitemap.xml`に掲載された全ページを対象とします。LPだけでなくprivacy、terms、contactも検査します。

## PR検証

PRではProduction URLではなく、PR headから生成した`_site/`を`127.0.0.1`で配信して検査します。

### 静的検証

`.github/workflows/validate.yml`

- 公開物の許可リスト
- manifestとHTML集合の一致
- 公開状態、ストアURL、ポータルカード、LP導線の一致
- 全ページのcanonical、`og:url`、OGP、Twitter Card
- `.html`付き内部リンクの禁止
- PNG／WebPの形式と寸法
- sitemapの完全一致
- 全JavaScriptの構文
- Search Console注入処理の単体テスト
- Production監査コードの契約テスト

### ブラウザ検証

`.github/workflows/validate-production-browser.yml`

「あしたもつもの」:

- 実画面4点の表示
- eager／lazy／fetchpriority
- 390px、820px、1440pxの配置
- 横overflow
- キーボードフォーカス
- reduced motion
- JavaScript無効時のHTMLモック
- スクリーンショットCSS失敗時のHTMLモック
- WebP画像失敗時のHTMLモック

「へぇの種」:

- 4択クイズの回答処理
- 正解／不正解表示
- 回答後のフォーカス移動
- 全選択肢の無効化
- noscript表示
- 390px、820px、1440pxの横overflow

### アクセシビリティ検証

`.github/workflows/audit-production-accessibility.yml`

両アプリについて次を確認します。

- `/index.html`直接アクセス
- `html[lang]`
- 見出し階層
- header、main、footer、nav
- リンクのアクセシブルネーム
- Chrome Accessibility Tree
- 画像代替テキスト
- 200%文字拡大
- テキスト欠落と横overflow

PRジョブは`contents: read`のみです。Status書き込みはデプロイ後または手動Production監査の別ジョブに限定します。

## Production監査

### 週次・デプロイ後の詳細監査

`.github/workflows/audit-production.yml`はデプロイ成功後、手動実行、毎週月曜日に実行します。

- 両アプリのブラウザ操作
- フォールバック
- Lighthouse mobile／desktop
- 各モード3回測定
- Accessibility 0.95以上
- Best Practices 0.90以上
- SEO 0.90以上
- Performance 0.80未満は警告

レポートとスクリーンショットはGitHub Actions artifactに30日保存し、外部の一時公開ストレージへアップロードしません。

### 日次の軽量死活監視

`.github/workflows/daily-production-health.yml`は毎日06:17 JST相当と手動実行で、次を確認します。

- 全sitemap URL
- OGP、favicon、CSS、JavaScript、スクリーンショット
- Productionセキュリティヘッダー

失敗時は`[monitor] Production LP health check failed` Issueを作成または更新します。回復時は回復runを記録してIssueを閉じます。失敗ログは14日保存します。

詳細は`docs/production-audit.md`を参照してください。

## リリース前の法務整合

ストア提出前に、提出ビルドの実装、LPのプライバシーポリシー／利用規約、ストア申告を照合します。

確認対象:

- 分析、クラッシュ、広告、課金
- 外部AI／APIへの送信
- 端末内・クラウド保存
- 画像、通知、各権限
- データ削除方法
- 対象年齢
- Google Playデータセーフティ
- App Store App Privacyを使用する場合の回答

チェックシートは`docs/release-legal-checklist.md`です。

## ローカル確認

```bash
bash tool/prepare_site.sh
python3 tool/validate_site.py _site
python3 -m unittest tool/test_production_audit.py
python3 -m unittest tool/test_production_accessibility_audit.py
python3 -m unittest tool/test_release_operations.py
python3 -m http.server 8123 --directory _site
```

ブラウザで`http://127.0.0.1:8123`へアクセスします。HTMLファイルを直接開くとルート絶対パスのCSSやJavaScriptを正しく確認できません。

Search Console確認タグを含めてローカル生成する場合:

```bash
SEARCH_CONSOLE_VERIFICATION=verification_token bash tool/prepare_site.sh
SEARCH_CONSOLE_VERIFICATION=verification_token python3 tool/validate_site.py _site
```

全JavaScriptの構文確認:

```bash
while IFS= read -r -d '' file; do
  node --check "$file"
done < <(find _site tool -type f \( -name '*.js' -o -name '*.cjs' \) -print0 | sort -z)
```

Productionのヘッダー確認:

```bash
python3 tool/check_production_headers.py https://lp-5t7.pages.dev/
```

## 主な構成

```text
/
├── .github/workflows/
│   ├── deploy.yml
│   ├── validate.yml
│   ├── validate-production-audit.yml
│   ├── validate-production-browser.yml
│   ├── audit-production.yml
│   ├── audit-production-accessibility.yml
│   └── daily-production-health.yml
├── _headers
├── index.html
├── robots.txt
├── sitemap.xml
├── lighthouserc.mobile.cjs
├── lighthouserc.desktop.cjs
├── assets/
├── apps/
│   ├── ashita-motsumono/
│   └── ehenotane/
├── tool/
│   ├── site_manifest.json
│   ├── prepare_site.sh
│   ├── inject_search_console_verification.py
│   ├── validate_site.py
│   ├── verify_remote_site.py
│   ├── check_production_headers.py
│   └── test_*.py
└── docs/
    ├── app-lp-template.md
    ├── new-app-checklist.md
    ├── production-audit.md
    ├── public-identity.md
    ├── release-legal-checklist.md
    ├── search-console.md
    └── store-release.md
```

## URLルール

公開URLはextensionless形式へ統一します。

```text
/apps/{slug}/privacy
/apps/{slug}/terms
/apps/{slug}/contact
```

実ファイル名は`privacy.html`、`terms.html`、`contact.html`です。内部リンク、canonical、`og:url`、sitemapに`.html`を含めません。

## 新アプリの追加

`docs/app-lp-template.md`と`docs/new-app-checklist.md`を使用してください。

最低限更新する項目:

- `apps/{slug}/`の4ページ
- `tool/site_manifest.json`
- ルートカードと公開状態data属性
- `sitemap.xml`
- `assets/brand/og-{slug}.png`
- 操作可能なUIがある場合はPuppeteer監査

## 外部操作として残る項目

- Search ConsoleでURLプレフィックスプロパティを作成し、発行された確認値をRepository variableへ登録する
- Search Consoleへ`sitemap.xml`を送信し、主要URLのインデックス状況を確認する
- 各アプリの公開直前に`docs/release-legal-checklist.md`を完了する
- Google Play／App Store公開後に`docs/store-release.md`に従って正式ストアURLを反映する
- 実機スマートフォン、タブレット、キーボード操作をリリースごとに確認する
