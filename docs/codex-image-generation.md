# Claude Code で画像生成する（Codex Image in CC）

Claude Code から ChatGPT（Codex）の画像生成を呼び出すための設定手順です。
ChatGPT のサブスク（Plus / Pro / Business など）があれば、OpenAI の API キーは不要です。

このリポジトリには `.claude/settings.json` に必要なマーケットプレイスとプラグインを登録済みなので、
Claude Code でこのフォルダを開くと自動でインストール確認が出ます。手動でやる場合は下記の 3 ステップ。

## 前提

- Node.js 18.18 以上
- Claude Code（プラグイン対応版）
- ChatGPT アカウント（画像生成はサブスクの利用枠内で動く）

## 3 ステップ

Claude Code のプロンプトで、次を順番に実行します。

```
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/plugin marketplace add KingGyuSuh/codex-image-in-cc
/plugin install codex-image@codex-image-in-cc
/reload-plugins
```

次に Codex CLI を入れて、ChatGPT アカウントでログインします（ブラウザが開きます）。

```
npm install -g @openai/codex
codex login
```

準備ができたか確認します。

```
/codex-image:status
```

`Ready: yes` になれば完了です。あとは日本語で頼むだけです。

```
/codex-image:generate "新入社員向けの給与のしくみ図を作って。A4縦、デスクトップに poster.png として保存して"
/codex-image:edit poster.png "背景を白にして文字を大きく"
```

出力先を指定しないと `./codex-images/<日時>-1.png` に保存されます。

## うまくいかないとき

| 症状 | 対処 |
|---|---|
| `Codex login: Not logged in` | ターミナルで `codex login` を実行して ChatGPT でログイン |
| `imagegen skill: not found` | Codex を一度実行すると `~/.codex/skills/.system/imagegen` に同梱スキルが展開される（例: `codex exec --skip-git-repo-check "hi"`）。それでも無ければ `npm install -g @openai/codex@latest` で更新 |
| クラウド版 Claude Code（claude.ai/code）で動かない | 環境のネットワーク設定で `auth.openai.com` `chatgpt.com` `api.openai.com` を許可するか、ローカルの Claude Code で実行する |
| 1 回の生成に 1〜3 分かかる | 正常です。Codex のエージェント 1 ターン分が走ります |

## 参考

- OpenAI 公式プラグイン: https://github.com/openai/codex-plugin-cc
- 画像生成プラグイン: https://github.com/KingGyuSuh/codex-image-in-cc
