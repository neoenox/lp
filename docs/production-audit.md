# Production表示・Lighthouse・アクセシビリティ監査

Production origin `https://neoenox-apps.pages.dev`を、次のworkflowで継続確認します。

- `.github/workflows/audit-production.yml`: 両アプリのブラウザ操作、障害時フォールバック、Lighthouse
- `.github/workflows/audit-production-accessibility.yml`: 両アプリの文書構造、Accessibility Tree、200%文字拡大
- `.github/workflows/validate-production-browser.yml`: PR headから生成したローカル`_site`のブラウザ監査
- `.github/workflows/daily-production-health.yml`: 全公開URL、資産、セキュリティヘッダーの日次死活監視

## PRとProductionの分離

PRでは既存Productionを検査しません。

1. PR headをcheckout
2. `tool/prepare_site.sh`で`_site/`を生成
3. `python3 -m http.server`で`127.0.0.1`へ配信
4. PR成果物をPuppeteerで検査

デプロイ後、手動実行、週次監査ではProduction URLを検査します。これにより、変更前のProductionが正常であることを理由に壊れたPRが通過する問題を防ぎます。

## 対象アプリ

`tool/site_manifest.json`で管理します。

| アプリ | ブラウザ操作 | 実画面画像 | Accessibility |
|---|---|---:|---|
| あしたもつもの | 実画面表示、フォールバック、フォーカス、reduced motion | 4 | 実画面altを含む |
| へぇの種 | サンプルクイズ、回答後フォーカス、noscript | 0 | 文書構造と操作UI |

## あしたもつもの

- JavaScript実行後に実画面4点が表示される
- 先頭画像が`loading="eager"`かつ`fetchpriority="high"`
- 下部画像3点が`loading="lazy"`
- 画像は360×640でaltが空でない
- 390pxでは1列、820pxでは2列、1440pxでは3列
- JavaScript無効時はHTMLモック4点を維持
- `app-screenshots.css`失敗時はHTMLモック4点を維持
- 個別WebP失敗時は該当するHTMLモックだけを維持し、壊れた`img`を残さない
- Tab操作で主要リンクへ到達できる
- `prefers-reduced-motion: reduce`でアニメーションとスムーススクロールを抑止

## へぇの種

- 4つの回答ボタンが表示される
- 回答後に全ボタンを無効化する
- 正解と選択した誤答をそれぞれ1件表示する
- 正答と解説を表示する
- 結果領域へフォーカスを移動する
- JavaScript無効時にnoscriptメッセージを表示する
- 390px、820px、1440pxで横overflowがない

## Accessibility

両アプリで次を確認します。

- `/index.html`直接アクセス
- `html[lang="ja"]`
- 空でないtitle
- `h1`が1件で見出しレベルに飛びがない
- header、main、footerが各1件
- ヘッダーとフッターのnavに一意のラベルがある
- リンクにアクセシブルネームがある
- Chrome Accessibility Treeにbanner、main、contentinfo、navigation、名前付きh1がある
- 実画面を使用するページではaltがAccessibility Treeへ公開される
- 200%文字拡大で横overflowとテキスト欠落がない

PR監査ジョブの権限は`contents: read`のみです。Commit Statusの書き込みは、Production監査後の別ジョブに限定します。

## Lighthouse

両アプリをモバイルとデスクトップで各3回測定し、中央値を記録します。

基準:

- Accessibility: 0.95以上
- Best Practices: 0.90以上
- SEO: 0.90以上
- Performance: 0.80未満を警告

レポートは次の形式で分離します。

```text
production-audit/lighthouse/{app-slug}/mobile/
production-audit/lighthouse/{app-slug}/desktop/
```

## 全公開URL検証

`tool/verify_remote_site.py`は`sitemap.xml`から全公開URLを取得し、次を確認します。

- HTTP成功
- HTML Content-Type
- title
- canonical
- `og:url`
- `og:image`
- `twitter:image`
- ブランド資産
- 実画面スクリーンショット
- 共通CSSとJavaScript

LP本体だけでなくprivacy、terms、contactも検証対象です。

## セキュリティヘッダー検証

`tool/check_production_headers.py`はProductionルートで次を確認します。

- Content Security Policy
- Permissions Policy
- Referrer Policy
- MIME sniffing防止
- frame埋め込み拒否
- Cross-Origin Opener Policy
- Cross-Origin Resource Policy

デプロイ固有URL、Productionスモーク、日次死活監視で同じ検証を実行します。

## 日次死活監視

`.github/workflows/daily-production-health.yml`は毎日06:17 JST相当と手動実行で、ブラウザやLighthouseを起動せず次だけを確認します。

- manifestと公開成果物の整合
- 全sitemap URL
- OGP、favicon、CSS、JavaScript、スクリーンショット
- Productionセキュリティヘッダー

失敗時は`[monitor] Production LP health check failed` Issueを新規作成するか、既存の未解決Issueへログを追記します。回復時は回復runをコメントしてIssueを閉じます。失敗ログはActions artifactへ14日保存します。

## 証跡

Actions artifactへ30日間保存します。

- 各viewportのスクリーンショット
- レスポンシブ配置JSON
- クイズ操作結果
- JavaScript無効時の結果
- CSS／画像障害時の結果
- Accessibility Treeと文書構造
- 200%文字拡大画像とJSON
- Lighthouse HTML／JSONと集計
- 日本語フォントの`fc-match`結果

日次死活監視の失敗ログは14日保存します。外部の一時公開ストレージにはアップロードしません。
