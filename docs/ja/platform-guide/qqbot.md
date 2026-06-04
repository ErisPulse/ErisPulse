# QQBotプラットフォーム特性

QQBotAdapterはQQBot（QQロボットのドキュメント）プロトコルに基づいて構築されたアダプタで、QQBotのすべての機能モジュールを統合し、統一されたイベント処理とメッセージ操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 1.0.0
- メンテナ: ErisPulse

## 基本情報

- プラットフォーム概要：QQBotはQQ公式が提供するロボットの開発インターフェースであり、グループチャット、プライベートチャット、チャンネルなどの多彩なシナリオをサポートしています。
- アダプター名：QQBotAdapter
- 接続方式：WebSocket ロング接続（QQBotゲートウェイを経由）
- 認証方式：appId + clientSecret に基づいて access_token を取得
- チェーン修飾子のサポート：`.Reply()`、`.At()`、`.AtAll()`、`.Keyboard()` などのチェーン修飾メソッドをサポート
- OneBot12互換性：OneBot12フォーマットメッセージの送信をサポート

## 設定説明

```toml
# config.toml
[QQBot_Adapter]
appid = "YOUR_APPID"          # QQロボットアプリID（必須）
secret = "YOUR_CLIENT_SECRET"  # QQロボットクライアントシークレット（必須）
sandbox = false                 # サンドボックス環境を使用するか（任意、デフォルトはfalse）
intents = [1, 30, 25]          # イベントのインテントビットを購読（任意）
gateway_url = "wss://api.sgroup.qq.com/websocket/"  # カスタムゲートウェイアドレス（任意）
```

**設定項目の説明：**
- `appid`：QQロボットのアプリID（必須）、QQオープンプラットフォームから取得
- `secret`：QQロボットのクライアントシークレット（必須）、QQオープンプラットフォームから取得
- `sandbox`：サンドボックス環境を使用するかどうか。サンドボックス環境APIアドレスは `https://sandbox.api.sgroup.qq.com`
- `intents`：イベント購読インテントリスト。各値は左シフト演算子（<<）を行い、ビットOR演算（|）されます
  - `1`：チャンネル関連イベント
  - `25`：チャンネルメッセージイベント
  - `30`：グループ@メッセージイベント
- `gateway_url`：WebSocketゲートウェイアドレス。デフォルトは `wss://api.sgroup.qq.com/websocket/`

**API環境：**
- 本番環境：`https://api.sgroup.qq.com`
- サンドボックス環境：`https://sandbox.api.sgroup.qq.com`

## サポートされているメッセージ送信タイプ

すべての送信メソッドはチェーン構文を介して実装されています。例：

```python
from ErisPulse.Core import adapter
qqbot = adapter.get("qqbot")

await qqbot.Send.To("user", user_openid).Text("Hello World!")
```

サポートされている送信タイプは以下の通りです：

- `.Text(text: str)`：プレーンテキストメッセージを送信。
- `.Image(file: bytes | str)`：画像メッセージを送信。ファイルパス、URL、バイナリデータをサポート。
- `.Markdown(content: str)`：Markdown形式のメッセージを送信。
- `.Ark(template_id: int, kv: list)`：Arkテンプレートメッセージを送信。
- `.Embed(embed_data: dict)`：Embedメッセージを送信。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信。

### チェーン修飾子メソッド（組み合わせ可能）

チェーン修飾子メソッドは `self` を返し、チェーン呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定されたメッセージに返信。
- `.At(user_id: str)`：指定されたユーザーに@する（`<@user_id>` 形式で内容を挿入）。
- `.AtAll()`：全員に@する（`@所有人` テキストを挿入）。
- `.Keyboard(keyboard: dict)`：キーボードボタンを追加。

### チェーン呼び出しの例

```python
# 基本的な送信
await qqbot.Send.To("user", user_openid).Text("Hello")

# メッセージに返信
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("返信メッセージ")

# 返信 + ボタン
await qqbot.Send.To("group", group_openid).Reply(msg_id).Keyboard(keyboard).Text("返信とボタン付きのメッセージ")

# ユーザーに@する
await qqbot.Send.To("group", group_openid).At("member_openid").Text("こんにちは")

# 組み合わせて使用
await qqbot.Send.To("group", group_openid).Reply(msg_id).At("member_openid").Keyboard(keyboard).Text("複合メッセージ")
```

### OneBot12メッセージサポート

アダプターはOneBot12形式のメッセージ送信をサポートしており、クロスプラットフォームメッセージの互換性を容易にします：

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await qqbot.Send.To("user", user_openid).Raw_ob12(ob12_msg)

# チェーン修飾子と組み合わせる
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await qqbot.Send.To("group", group_openid).Reply(msg_id).Raw_ob12(ob12_msg)
```

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、直接 await を行って送信結果を取得できます。戻り値は ErisPulse アダプターの標準化された戻り値規格に従います：

```python
{
    "status": "ok",           // 実行ステータス: "ok" または "failed"
    "retcode": 0,             // 返りコード
    "data": {...},            // レスポンスデータ
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "qqbot_raw": {...}        // 元のレスポンスデータ
}
```

### エラーコードの説明

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 10003 | 送信先を特定できない |
| 32000 | リクエストがタイムアウトした |
| 33000 | API呼び出しの異常 |
| 34000 | APIが予期しない形式を返した、またはビジネスエラー |

## 特有のイベントタイプ

本プラットフォームの機能を使用するには、`platform=="qqbot"` の検出が必要です

### 主な差異点

1.  **openid体系**：QQBotはQQ番号ではなくopenidを使用します。ユーザーとグループの識別子はすべてopenid文字列です。
2.  **グループメッセージは必ず@する**：グループ内のメッセージは、ユーザーがロボットに@した場合のみ受信されます（`GROUP_AT_MESSAGE_CREATE`）。
3.  **チャンネルシステム**：QQBotはチャンネル（Guild）とサブチャンネル（Channel）のメッセージとイベントをサポートします。
4.  **メッセージ審査**：送信されたメッセージには審査が必要な場合があり、`qqbot_audit_pass`/`qqbot_audit_reject` イベントで結果が通知されます。
5.  **受動的な返信**：グループメッセージとプライベートチャットメッセージは受動的な返信メカニズムをサポートしており、送信時に `msg_id` を携带する必要があります。

### 拡張フィールド

- すべての特有のフィールドは `qqbot_` プレフィックスで識別されます。
- 元のデータは `qqbot_raw` フィールドに保持されます。
- `qqbot_raw_type` は元のQQBotイベントタイプを識別します（例: `C2C_MESSAGE_CREATE`）。
- 添付ファイルデータは `qqbot_attachment` フィールドを介して元の添付ファイル情報を保存します。

### 特殊フィールドの例

```python
# グループ@メッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "MEMBER_OPENID",
  "group_id": "GROUP_OPENID",
  "qqbot_group_openid": "GROUP_OPENID",
  "qqbot_member_openid": "MEMBER_OPENID",
  "qqbot_event_id": "メッセージイベントID",
  "qqbot_reply_token": "返信トークン"
}

# プライベートチャットメッセージ
{
  "type": "message",
  "detail_type": "private",
  "user_id": "USER_OPENID",
  "qqbot_openid": "USER_OPENID",
  "qqbot_event_id": "メッセージイベントID",
  "qqbot_reply_token": "返信トークン"
}

# インタラクションイベント
{
  "type": "notice",
  "detail_type": "qqbot_interaction",
  "qqbot_interaction_id": "インタラクションID",
  "qqbot_interaction_type": "インタラクションタイプ",
  "qqbot_interaction_data": {
    "...": "インタラクションデータ"
  }
}

# メッセージ審査
{
  "type": "notice",
  "detail_type": "qqbot_audit_pass",
  "qqbot_audit_id": "審査ID",
  "qqbot_message_id": "メッセージID"
}

# メッセージ削除
{
  "type": "notice",
  "detail_type": "qqbot_message_delete",
  "message_id": "削除されたメッセージID",
  "operator_id": "操作者ID"
}

# 絵文字の反応
{
  "type": "notice",
  "detail_type": "qqbot_reaction_add",
  "qqbot_raw": {
    "...": "元のデータ"
  }
}
```

### チャンネルメッセージセグメント

チャンネルメッセージは `mentions` フィールドをサポートし、変換後は `mention` メッセージセグメントとして表現されます：

```json
{
  "type": "mention",
  "data": {
    "user_id": "被@ユーザーID",
    "user_name": "被@ユーザーのニックネーム"
  }
}
```

### 添付ファイルメッセージセグメント

QQBotの添付ファイルは `content_type` に基づいて対応するメッセージセグメントに自動的に変換されます：

| content_type プレフィックス | 変換タイプ | 説明 |
|---|---|---|
| `image` | `image` | 画像メッセージ |
| `video` | `video` | 動画メッセージ |
| `audio` | `voice` | 音声メッセージ |
| その他 | `file` | ファイルメッセージ |

添付ファイルメッセージセグメントの構造：

```json
{
  "type": "image",
  "data": {
    "url": "添付ファイルURL",
    "qqbot_attachment": {
      "content_type": "image/png",
      "url": "元の添付ファイルURL"
    }
  }
}
```

## WebSocket接続

### 接続手順

1.  appId + clientSecret を使用して access_token を取得
2.  WebSocketゲートウェイに接続
3.  OP_HELLO（op=10）メッセージを受信し、ハートビート間隔を取得
4.  OP_IDENTIFY（op=2）を送信して認証
5.  READY イベントを受信し、session_id と bot_id を取得
6.  ハートビートループを開始（OP_HEARTBEAT、op=1）
7.  イベントの配信を受信（OP_DISPATCH、op=0）

### 再接続（切断時の再接続）

- 自動再接続をサポート。最大再接続回数は50回です。
- 再接続待ち時間には指数バックオフアルゴリズムを使用：`min(5 * 2^min(count, 6), 300)` 秒
- セッションの復帰（OP_RESUME、op=6）をサポート。session_id + seq を使用して復元します。
- OP_RECONNECT（op=7）または OP_INVALID_SESSION（op=9）を受信したら自動的に再接続がトリガーされます。

### Token更新

- access_token の有効期限は通常7200秒です。
- アダプターは毎回7080秒（7200-120）でtokenを自動更新します。
- 更新インターフェース：`POST https://bots.qq.com/app/getAppAccessToken`

## イベント購読

intents値はビット演算で組み合わせます：

```python
intents = [1, 30, 25]
value = 0
for intent in intents:
    value |= (1 << intent)
```

一般的なintentビット：

| intent値 | 説明 |
|----------|------|
| 1 | チャンネル関連イベント（GUILD_CREATEなど） |
| 25 | チャンネルメッセージイベント（AT_MESSAGE_CREATEなど） |
| 30 | グループ@メッセージイベント（GROUP_AT_MESSAGE_CREATEなど） |

## 使用例

### グループメッセージの処理

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

qqbot = sdk.adapter.get("qqbot")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "qqbot":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    group_id = event.get("group_id")

    if text == "hello":
        await qqbot.Send.To("group", group_id).Reply(
            event.get("message_id")
        ).Text("Hello!")
```

### インタラクションイベントの処理

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "qqbot":
        return

    if event.get("detail_type") == "qqbot_interaction":
        interaction_id = event.get("qqbot_interaction_id", "")
        interaction_data = event.get("qqbot_interaction_data", {})
        # インタラクションを処理...
```

### メディアメッセージの送信

```python
# 画像を送信（URL）
await qqbot.Send.To("group", group_openid).Image("https://example.com/image.png")

# 画像を送信（バイナリ）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await qqbot.Send.To("user", user_openid).Image(image_bytes)
```

### メッセージ審査結果の監視

```python
@notice.on_notice()
async def handle_audit(event):
    if event.get("platform") != "qqbot":
        return

    detail_type = event.get("detail_type")

    if detail_type == "qqbot_audit_pass":
        msg_id = event.get("qqbot_message_id")
        print(f"メッセージ審査通過: {msg_id}")

    elif detail_type == "qqbot_audit_reject":
        reason = event.get("qqbot_audit_reject_reason", "")
        print(f"メッセージ審査拒否: {reason}")