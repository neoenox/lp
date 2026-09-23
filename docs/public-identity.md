# 公開ID決定記録

最終更新日: 2026年7月13日

「あしたもつもの」の公開媒体で使用する名称、問い合わせ先、Production URLを次のとおり統一します。

## 決定事項

| 項目 | 正式値 |
|---|---|
| サービス名 | あしたもつもの |
| Google Playアプリ名 | あしたもつもの |
| 問い合わせ先 | kaenozu@gmail.com |
| Production origin | https://neoenox-apps.pages.dev |
| アプリLP | https://neoenox-apps.pages.dev/apps/ashita-motsumono/ |
| プライバシーポリシー | https://neoenox-apps.pages.dev/apps/ashita-motsumono/privacy |
| 利用規約 | https://neoenox-apps.pages.dev/apps/ashita-motsumono/terms |
| お問い合わせ | https://neoenox-apps.pages.dev/apps/ashita-motsumono/contact |

## 表記ルール

- 公開表示では、漢字を含む「あした持つもの」を使用せず、ひらがなの「あしたもつもの」に統一します。
- リポジトリ名、パッケージ名、URL slugは既存の`ashita-motsumono` / `ashita_motsumono`を維持します。
- canonical、OGP、Twitter Card、sitemap、robots、Production監査は`https://neoenox-apps.pages.dev`を基準にします。
- カスタムドメインは現時点では導入せず、取得・DNS・更新運用を決定した時点で別途移行します。
- Google Play公開後は、主要CTAを正式なストアURLへ更新します。

## 反映対象

- LP本文、ヘッダー、フッター、法務ページ
- title、description、canonical、OGP、Twitter Card
- Android表示名とFlutterアプリタイトル
- Play Consoleのアプリ名、連絡先、プライバシーポリシーURL
- ストア掲載文と提出チェックリスト
- sitemap、robots、Production検証URL
