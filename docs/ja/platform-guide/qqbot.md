# QQBotプラットフォームの特徴ドキュメント

QQBotAdapter は、QQBot（QQロボットのドキュメント）プロトコルに基づいて構築されたアダプターであり、QQBotのすべての機能モジュールを統合し、一貫したイベント処理とメッセージ操作のインターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 1.0.0
- メンテナー: ErisPulse

## 基本情報

- プラットフォーム概要：QQBotはQQ公式が提供するBot開発用のAPIで、グループチャット、プライベートチャット、チャンネルなど多様な場面に対応しています。
- アダプタ名：QQBotAdapter
- 接続方法：WebSocket長時間接続（QQBotゲートウェイを使用）
- 認証方法：appId + clientSecretを用いてaccess_tokenを取得
- チェーン修飾サポート：`.Reply()`、`.At()`、`.AtAll()`、`.Keyboard()` などのチェーン修飾メソッドに対応
- OneBot12互換：OneBot12形式のメッセージ送信に対応

## 設定の説明

```toml
# config.toml
[QQBot_Adapter]
appid = "YOUR_APPID"          # QQ ロボットアプリのID（必須）
secret = "YOUR_CLIENT_SECRET"  # QQ ロボットクライアントのシークレット（必須）
sandbox = false                 # サンドボックス環境を使用するかどうか（オプション、デフォルトはfalse）
intents = [1, 30, 25]          # 訂読するイベント intents ビット（オプション）
gateway_url = "wss://api.sgroup.qq.com/websocket/"  # カスタムのゲートウェイアドレス（オプション）
```

**設定項目の説明：**
- `appid`：QQ ロボットのアプリID（必須）、QQオープンプラットフォームから取得
- `secret`：QQ ロボットのクライアントシークレット（必須）、QQオープンプラットフォームから取得
- `sandbox`：サンドボックス環境を使用するかどうか、サンドボックス環境のAPIアドレスは `https://sandbox.api.sgroup.qq.com`
- `intents`：イベントのサブスクリプション intents リスト、各値は左シフト後にビット演算 OR で結合される
  - `1`：チャンネル関連イベント
  - `25`：チャンネルメッセージイベント
  - `30`：グループのメンションメッセージイベント
- `gateway_url`：WebSocket ゲートウェイアドレス、デフォルトは `wss://api.sgroup.qq.com/websocket/`

**API環境：**
- 本番環境：`https://api.sgroup.qq.com`
- サンドボックス環境：`https://sandbox.api.sgroup.qq.com`

## 支持するメッセージ送信タイプ

すべての送信メソッドは、チェーン式の構文で実装されています。たとえば：

```python
from ErisPulse.Core import adapter
qqbot = adapter.get("qqbot")

await qqbot.Send.To("user", user_openid).Text("Hello World!")
```

サポートされている送信タイプは以下の通りです：

- `.Text(text: str)`：純粋なテキストメッセージを送信します。
- `.Image(file: bytes | str)`：画像メッセージを送信します。ファイルパス、URL、バイナリデータをサポートします。
- `.Markdown(content: str)`：Markdown形式のメッセージを送信します。
- `.Ark(template_id: int, kv: list)`：Arkテンプレートメッセージを送信します。
- `.Embed(embed_data: dict)`：Embedメッセージを送信します。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します。

### チェーン式修飾メソッド（複数組み合わせて使用可能）

チェーン式修飾メソッドは `self` を返し、チェーン式で呼び出すことができます。最終的な送信メソッドの前に必ず呼び出す必要があります：

- `.Reply(message_id: str)`：指定されたメッセージに返信します。
- `.At(user_id: str)`：指定されたユーザーを@します（`<@user_id>`形式で内容に挿入します）。
- `.AtAll()`：全員を@します（`@所有人`というテキストを挿入します）。
- `.Keyboard(keyboard: dict)`：キーボードボタンを追加します。

### チェーン式呼び出しの例

```python
# 基本的な送信
await qqbot.Send.To("user", user_openid).Text("Hello")

# メッセージの返信
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("返信メッセージ")

# 返信 + ボタン
await qqbot.Send.To("group", group_openid).Reply(msg_id).Keyboard(keyboard).Text("返信とキーボード付きのメッセージ")

# ユーザーを@する
await qqbot.Send.To("group", group_openid).At("member_openid").Text("こんにちは")

# 組み合わせて使用
await qqbot.Send.To("group", group_openid).Reply(msg_id).At("member_openid").Keyboard(keyboard).Text("複合メッセージ")
```

### OneBot12メッセージのサポート

アダプタはOneBot12形式のメッセージ送信をサポートしており、プラットフォーム間のメッセージ互換性に役立ちます：

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await qqbot.Send.To("user", user_openid).Raw_ob12(ob12_msg)

# チェーン式修飾との組み合わせ
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await qqbot.Send.To("group", group_openid).Reply(msg_id).Raw_ob12(ob12_msg)
```

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返します。これに await を直接適用して送信結果を取得できます。返り値は ErisPulse アダプターの標準化された返り値規格に準拠しています：

```python
{
    "status": "ok",           // 実行ステータス: "ok" または "failed"
    "retcode": 0,             // 戻りコード
    "data": {...},            // 応答データ
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "qqbot_raw": {...}        // 元の応答データ
}
```

### エラーコードの説明

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 10003 | 送信先が特定できません |
| 32000 | 要求のタイムアウト |
| 33000 | APIの呼び出しに異常が発生しました |
| 34000 | APIが予期しない形式または業務上のエラーを返しました |

## 特有イベントタイプ

このプラットフォームの機能を使用するには、`platform=="qqbot"` の検出が必要です。

### 核心的な違い

1. **openid体系**：QQBotは QQ番号ではなく openid を使用しており、ユーザーとグループの識別子はすべて openid 文字列です。
2. **グループメッセージは必ず@**：グループ内でのメッセージは、ユーザーがロボットを@した場合にのみ受け取れます（`GROUP_AT_MESSAGE_CREATE`）。
3. **チャンネルシステム**：QQBotはチャンネル（Guild）とサブチャンネル（Channel）のメッセージとイベントをサポートしています。
4. **メッセージ審査**：送信されたメッセージは審査を通過する必要があり、`qqbot_audit_pass`/`qqbot_audit_reject` イベントで結果が通知されます。
5. **受動的返信**：グループメッセージとプライベートチャットメッセージは受動的返信メカニズムをサポートしており、返信時に `msg_id` を含める必要があります。

### 拡張フィールド

- すべての特有フィールドは `qqbot_` で始まるプレフィックスで識別されます。
- 保持された元のデータは `qqbot_raw` フィールドに格納されます。
- `qqbot_raw_type` は元のQQBotイベントタイプを識別します（例：`C2C_MESSAGE_CREATE`）。
- 附件データは `qqbot_attachment` フィールドに格納されます。

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

# メッセージ反応
{
  "type": "notice",
  "detail_type": "qqbot_reaction_add",
  "qqbot_raw": {
    "...": "元のデータ"
  }
}
```

### チャンネルメッセージセグメント

チャンネルメッセージは `mentions` フィールドをサポートし、変換後は `mention` メッセージセグメントとして表示されます：

```json
{
  "type": "mention",
  "data": {
    "user_id": "@されたユーザーID",
    "user_name": "@されたユーザーのニックネーム"
  }
}
```

### 附件メッセージセグメント

QQBotの附件は `content_type` に基づいて自動的に対応するメッセージセグメントに変換されます：

| content_type 前綴 | 変換タイプ | 説明 |
|---|---|---|
| `image` | `image` | 画像メッセージ |
| `video` | `video` | 動画メッセージ |
| `audio` | `voice` | 音声メッセージ |
| その他 | `file` | ファイルメッセージ |

附件メッセージセグメントの構造は以下の通りです：
```json
{
  "type": "image",
  "data": {
    "url": "附件URL",
    "qqbot_attachment": {
      "content_type": "image/png",
      "url": "元の附件URL"
    }
  }
}
```

## WebSocket接続

### 接続フロー

1. appId + clientSecret を使用して access_token を取得する
2. WebSocket ゲートウェイに接続する
3. OP_HELLO（op=10）メッセージを受信し、ハートビートの間隔を取得する
4. 認証のために OP_IDENTIFY（op=2）を送信する
5. READY イベントを受信し、session_id と bot_id を取得する
6. ハートビートループを開始する（OP_HEARTBEAT、op=1）
7. イベントの配信を受信する（OP_DISPATCH、op=0）

### 接続切断後の再接続

- 自動再接続をサポートし、最大再接続回数は50回
- 再接続待機時間は指数バックオフアルゴリズムを使用：`min(5 * 2^min(count, 6), 300)` 秒
- session_id + seq を使用してセッションの復元をサポート（OP_RESUME、op=6）
- OP_RECONNECT（op=7）または OP_INVALID_SESSION（op=9）を受信した際に自動的に再接続をトリガーする

### Tokenの更新

- access_token の有効期限は通常7200秒
- アダプターは自動的に7080秒（7200-120）ごとにトークンを更新する
- 更新インターフェース：`POST https://bots.qq.com/app/getAppAccessToken`

## イベントのサブスクライブ（Intents）

Intents 値はビット演算によって組み合わせられます：

```python
intents = [1, 30, 25]
value = 0
for intent in intents:
    value |= (1 << intent)
```

一般的に使用される Intent ビット：
| Intent値 | 説明 |
|----------|------|
| 1 | チャンネル関連イベント（GUILD_CREATEなど） |
| 25 | チャンネルメッセージイベント（AT_MESSAGE_CREATEなど） |
| 30 | グループメンションメッセージイベント（GROUP_AT_MESSAGE_CREATEなど） |

## 使用例

### 群メッセージの処理

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

### 交互イベントの処理

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "qqbot":
        return

    if event.get("detail_type") == "qqbot_interaction":
        interaction_id = event.get("qqbot_interaction_id", "")
        interaction_data = event.get("qqbot_interaction_data", {})
        # 交互イベントの処理...
```

### メディアメッセージの送信

```python
# 画像の送信（URL）
await qqbot.Send.To("group", group_openid).Image("https://example.com/image.png")

# 画像の送信（バイナリ）
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
```