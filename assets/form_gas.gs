/**
 * AI社員採用設計 — 申込フォーム受信（Google Apps Script）
 *
 * セットアップ手順:
 * 1. スプレッドシートを新規作成（例: 「AI社員採用設計_申込台帳」）し、
 *    拡張機能 → Apps Script でこのコードを貼り付ける。
 * 2. SLACK_WEBHOOK を設定（省略可。空なら通知なし）。
 * 3. デプロイ → 新しいデプロイ → 種類「ウェブアプリ」
 *    - 次のユーザーとして実行: 自分
 *    - アクセスできるユーザー: 全員
 * 4. 発行された WebアプリURL を index.html 内の FORM_ENDPOINT に貼る。
 *
 * 注意: 申込への返信・営業連絡は人間が行う（対外送信の人間ゲート=Gv26）。
 */

var SHEET_NAME = '申込';
var SLACK_WEBHOOK = ''; // 任意: Slack Incoming Webhook URL（#外販通知など）

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(SHEET_NAME);
    if (!sheet) {
      sheet = ss.insertSheet(SHEET_NAME);
      sheet.appendRow(['受信日時', '会社名', 'お名前', 'メール', '電話', '業種', '困っていること', '送信元ページ', '対応状況']);
    }
    sheet.appendRow([
      new Date(),
      data.company || '',
      data.name || '',
      data.email || '',
      data.tel || '',
      data.industry || '',
      data.issue || '',
      data.page || '',
      '未対応'
    ]);

    if (SLACK_WEBHOOK) {
      UrlFetchApp.fetch(SLACK_WEBHOOK, {
        method: 'post',
        contentType: 'application/json',
        payload: JSON.stringify({
          text: '【AI社員採用設計】新規申込\n会社名: ' + (data.company || '-') +
                '\nお名前: ' + (data.name || '-') +
                '\n業種: ' + (data.industry || '-') +
                '\n困っていること: ' + ((data.issue || '').slice(0, 200))
        }),
        muteHttpExceptions: true
      });
    }

    return ContentService.createTextOutput(JSON.stringify({ ok: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ ok: false, error: String(err) }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
