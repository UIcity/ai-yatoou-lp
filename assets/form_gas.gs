/**
 * AI社員採用設計 — 申込フォーム受信（Google Apps Script）
 * 受信内容をスプレッドシートに記帳し、info@uicity.net へメール通知する。
 *
 * セットアップ手順:
 * 1. スプレッドシートを新規作成（例: 「AI社員採用設計_申込台帳」）し、
 *    拡張機能 → Apps Script でこのコードを貼り付ける。
 * 2. デプロイ → 新しいデプロイ → 種類「ウェブアプリ」
 *    - 次のユーザーとして実行: 自分
 *    - アクセスできるユーザー: 全員
 * 3. 発行された WebアプリURL を index.html 内の FORM_ENDPOINT に貼る。
 *
 * 注意: 申込者への返信・営業連絡は人間が行う（対外送信の人間ゲート=Gv26）。
 */

var NOTIFY_TO = 'info@uicity.net';
var SHEET_NAME = '申込';
var SLACK_WEBHOOK = ''; // 任意: Slack Incoming Webhook URL

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

    var body =
      'AI社員採用設計のLPから新しい申込が届きました。\n\n' +
      '■会社名・屋号: ' + (data.company || '-') + '\n' +
      '■お名前: ' + (data.name || '-') + '\n' +
      '■メール: ' + (data.email || '-') + '\n' +
      '■電話: ' + (data.tel || '-') + '\n' +
      '■業種: ' + (data.industry || '-') + '\n' +
      '■現在困っていること:\n' + (data.issue || '-') + '\n\n' +
      '■送信元ページ: ' + (data.page || '-') + '\n' +
      '■受信日時: ' + new Date().toLocaleString('ja-JP') + '\n\n' +
      '申込台帳（スプレッドシート）にも記帳済みです。返信・ご連絡は人間が行ってください。';

    MailApp.sendEmail({
      to: NOTIFY_TO,
      subject: '【AI社員採用設計】新規申込: ' + (data.company || '会社名未入力'),
      body: body,
      replyTo: (data.email || NOTIFY_TO),
      name: 'AI社員採用設計 申込フォーム'
    });

    if (SLACK_WEBHOOK) {
      UrlFetchApp.fetch(SLACK_WEBHOOK, {
        method: 'post',
        contentType: 'application/json',
        payload: JSON.stringify({ text: '【AI社員採用設計】新規申込\n会社名: ' + (data.company || '-') }),
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
