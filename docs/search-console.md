# Google Search Console運用手順

Production originは`https://neoenox-apps.pages.dev`です。現時点ではカスタムドメインを使用しないため、Search ConsoleではURLプレフィックスプロパティとしてこのoriginを登録します。

## リポジトリ側の準備

Search Consoleが発行したHTMLタグの`content`値だけを、GitHub ActionsのRepository variableとして登録します。

- Variable name: `SEARCH_CONSOLE_VERIFICATION`
- Variable value: `<meta name="google-site-verification" content="...">`の`content`値

`tool/prepare_site.sh`は値が設定されている場合だけ、公開成果物のルート`index.html`へ検証メタタグを1件追加します。値が空の場合、メタタグは出力しません。

設定場所:

1. GitHubリポジトリのSettingsを開く
2. Secrets and variables → Actions → Variablesを開く
3. `SEARCH_CONSOLE_VERIFICATION`を追加する
4. `Deploy to Cloudflare Pages`を再実行する

確認コマンド:

```bash
curl -fsSL https://neoenox-apps.pages.dev/ | grep 'google-site-verification'
```

## Search Console側の操作

1. URLプレフィックスプロパティ`https://neoenox-apps.pages.dev/`を追加する
2. HTMLタグ方式を選択する
3. 発行された`content`値をRepository variableへ登録する
4. Productionデプロイの成功を確認する
5. Search Consoleで所有権確認を実行する
6. `https://neoenox-apps.pages.dev/sitemap.xml`を送信する
7. 次のURLをURL検査する
   - `https://neoenox-apps.pages.dev/`
   - `https://neoenox-apps.pages.dev/apps/ashita-motsumono/`
   - `https://neoenox-apps.pages.dev/apps/ehenotane/`
8. canonical、robots、sitemap、クロールの警告を確認する

## 完了記録

完了時はIssueへ次を記録します。

- プロパティ登録日
- 所有権確認の成功
- sitemap送信結果
- 主要3 URLの取得可否
- 残っている警告と対応方針

## 注意

Search Consoleのプロパティ作成と確認値の発行はGoogleアカウント上の外部操作です。リポジトリだけでは完了できません。確認値をソースへ直接ハードコードする必要はなく、Repository variableからデプロイ成果物へ注入します。
