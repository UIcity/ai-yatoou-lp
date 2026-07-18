# AIを、雇おう。｜AI社員採用設計 LP

UIcityグループ BtoB外販の無料オファー「AI社員採用設計」（審査制・無料）のランディングページ。
タグライン「AIを、雇おう。」（06正典 A2-1）・黒×赤ブランド（A2-3/Br5）準拠。

## 構成（静的1ページ・外部依存ほぼゼロ）

| ファイル | 内容 |
|---|---|
| `index.html` | LP本体（CSS/JSすべてインライン・1ファイル完結） |
| `privacy.html` | プライバシーポリシー（※弁護士確認前のたたき台＝Gv37） |
| `assets/favicon.svg` | ファビコン |
| `assets/ogp.png` | OGP画像 1200×630（生成元＝`assets/ogp.html`） |
| `assets/form_gas.gs` | 申込フォーム受信用 Google Apps Script（スプレッドシート記帳＋Slack通知） |
| `robots.txt` / `sitemap.xml` | SEO用 |

## 設計方針

- **表示速度**: 追加リクエストはGoogle FontsのCSS1本のみ（非同期・初回描画はシステムフォント）。画像はすべてインラインSVG。HTML転送 約94KB（gzip後 約20KB想定）。
- **動的表現**: ヒーローのネットワーク粒子Canvas／AI社員例のローテーション／スクロール出現／効果試算のカウントアップとバー。`prefers-reduced-motion` 対応・非表示タブでは描画停止。
- **SEO**: 一意なh1・16のh2・JSON-LD（Organization / Service / FAQPage）・OGP・canonical・sitemap。FAQはdetails要素でHTML内に全文（JS無効でも表示）。

## 公開前の差し替え（`差し替え` でgrep）

1. **ドメイン**: `https://ai.uicity.net/` を確定ドメインへ一括置換（index.html / robots.txt / sitemap.xml）。外販Web入口はUIcityドメイン配下＝Br11③。
2. **フォーム送信先**: `assets/form_gas.gs` をスプレッドシートにデプロイ → WebアプリURLを index.html 内 `FORM_ENDPOINT` に設定。
3. **GA4**: 測定ID発行後、head内のコメントを解除。

## 公開前チェック（人間ゲート）

- LP文言の広告表現チェック: Ma7 AI一次チェック → 原園蒼依 確認（20_無料診断_設計書 §7-4と同運用）
- privacy.html・フォーム同意文言: Gv37 弁護士スポットで確認（法務断定はしない）
- 公開承認: 梶本雅人／運用オーナー: 古田将人（BtoB）
- 申込への返信・営業連絡は人間が実施（対外送信ゲート＝Gv26）
