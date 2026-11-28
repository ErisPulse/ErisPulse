# Terminal プラットフォーム機能ドキュメント

TerminalAdapter はコマンドライン端末アダプターです。端末そのものがチャットセッションとなり、モジュールロジックをローカルで素早くデバッグするために使用されます。

---

## ドキュメント情報

- 対応モジュールバージョン: 1.2.2
- メンテナー: ErisPulse
- 最終更新: 2026-11-10

## 基本情報

- プラットフォーム概要：ローカルのコマンドラインをチャットセッションとして扱い、stdin の入力をメッセージとし、モジュールの応答をターミナルに直接出力する
- アダプター名：TerminalAdapter
- プラットフォーム識別子：`terminal`
- シングルアカウント設計（ローカルデバッグ向け）
- フレームワーク要件：ソフト依存 `ErisPulse>=2.7.1`（実行時に検出して通知するのみ、強制ではない）

## 設定の説明

```toml
[Terminal]
bot_id = "terminal_bot"    # Bot のユーザー ID
bot_name = "TerminalBot"   # Bot のニックネーム
user_id = "terminal_user"  # シミュレートされたユーザーの ID（Bot と会話するエンドユーザー）
user_name = "User"         # シミュレートされたユーザーのニックネーム
prompt = "> "              # 入力プロンプト
reply_prefix = "[Bot] "    # Bot の返信の行プレフィックス（空の場合はプレフィックスを付けない）
echo_input = false         # ユーザー入力をエコー表示するかどうか（パイプ入力の場合に有効化）
```

## v5 パラダイム更新（1.1.0）

- **spawn_background タスクの帰属**：stdin 読み取りループを `runtime.spawn_background` を使用するように変更
- **フレームワークのソフト依存**：実行時に `ErisPulse>=2.7.1` を検出して通知し、起動時にバージョンログを出力

## 標準化対応（1.2.2）

レスポンス構造とエラーコードは [API レスポンス仕様](../standards/api-response.md) に従います。

### メッセージイベントへの message_id 補完

stdin メッセージイベントにトップレベルの標準 `message_id` フィールド（uuid により生成）が補完され、モジュールはターミナルメッセージを安定して参照して返信・重複排除を行えるようになりました。

### Send の BaseAdapter.Send 継承

`Send` はフレームワークの `BaseAdapter.Send` を継承し、**標準修飾子チェーン（`At` / `AtAll` / `Reply` など）が有効になります**。修飾セグメントとテキストセグメントがまとめてレンダリングされて出力されます。`node`（統合転送）セグメントはプレーンテキストの原文出力に縮退されます（内容は失われません）。

### メタアクションの補完

標準メタアクションが補完され、標準レスポンスを返します：

| アクション | data の内容 |
|------|----------|
| `get_status` | `enabled`（実行状態）/ `boot_time`（起動タイムスタンプ） |
| `get_version` | `impl`（TerminalAdapter）/ `version` / `onebot_version` |
| `get_supported_actions` | サポートされているアクション名のリスト |

```python
from ErisPulse import sdk
terminal = sdk.adapter.get("terminal")

result = await terminal.Api.get_status()
result = await terminal.Api.get_version()
result = await terminal.Api.get_supported_actions()
result = await terminal.Api.get_self_info()    # user_id/user_name
result = await terminal.Api.get_user_info("terminal_user")
result = await terminal.Api.get_friend_list()
```

### delete_message の機能縮退セマンティクス修正

ターミナルにはメッセージ撤回機能がないため、`delete_message` は「成功を返す」から**機能縮退の標準セマンティクス**に修正されました——`retcode=10002`（サポートされていない操作）を返し、モジュールはこれに基づいて縮退を判定できます。

### エラーコード仕様

| retcode | 意味 | 説明 |
|---------|------|------|
| 0 | 成功 | — |
| 10002 | サポートなし | グループ操作、メッセージ撤回、未実装の標準アクション |

## 使用方法

```python
# モジュールは通常どおりメッセージを監視するだけで構いません
from ErisPulse.Core.Event import message

@message.on_message()
async def handle(event):
    if event.get("platform") == "terminal":
        await event.reply("受信：" + event.get_text())
```

- ターミナルに入力されたテキストがそのままユーザーメッセージとなり、複数行（空行で終了）に対応しています
- イベント構造の例（stdin メッセージ）：

```json
{
  "id": "<uuid>",
  "time": 1700000000,
  "message_id": "<uuid>",
  "type": "message",
  "detail_type": "private",
  "platform": "terminal",
  "self": {"platform": "terminal", "user_id": "terminal_bot", "user_name": "TerminalBot"},
  "user_id": "terminal_user",
  "message": [{"type": "text", "data": {"text": "入力内容"}}],
  "alt_message": "入力内容",
  "terminal_raw": {"text": "入力内容"},
  "terminal_raw_type": "stdin_line"
}
```

- 送信例（修飾子チェーンが使用可能）：

```python
terminal = sdk.adapter.get("terminal")

await terminal.Send.To("private", "terminal_user").Text("Hello")
await terminal.Send.To("private", "terminal_user").At("terminal_user").Text("修飾子付きメッセージ")
await terminal.Send.To("private", "terminal_user").Raw_ob12([
    {"type": "text", "data": {"text": "OneBot12 セグメント"}}
])
```

- 開発時にモジュールのロジックを素早く検証するのに適しており、実際のプラットフォームへの接続は不要です