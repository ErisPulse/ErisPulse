# Discordプラットフォーム特徴ドキュメント

DiscordAdapterは、Discord Gateway (WebSocket) およびREST API v10プロトコルに基づいて構築されたアダプタであり、Discord Botのコア機能を統合し、統一されたイベント処理およびメッセージ操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.1.0
- メンテナー: ErisPulse
- Discord API バージョン: v10

## 基本情報

- プラットフォーム概要：Discord は、サーバー、チャンネル、ダイレクトメッセージなど多様な会話形式をサポートする、コミュニティ向けのコミュニケーションプラットフォームです。Bot 開発用のインターフェースも充実しています。
- アダプタ名：DiscordAdapter
- マルチアカウント対応：複数の Discord ロボットを同時に設定可能です。
- 接続方法：Gateway WebSocket（イベント受信）+ REST API（メッセージ送信/インターフェース呼び出し）
- 認証方法：Bot Token（HTTP ヘッダー `Authorization: Bot {token}`、Gateway IDENTIFY ペイロードに token を含む）
- チェーン修飾子対応：`.Reply()`、`.At()`、`.AtAll()` などのチェーン修飾メソッドに対応しています。
- OneBot12 互換性：OneBot12 フォーマットのメッセージ送信に対応しています。

## 設定の説明

DiscordAdapter は、複数のアカウントを設定できるようになっており、各アカウントは個別の Discord Bot に対応します。

```toml
# config.toml

# アカウント1
[DiscordAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"       # Discord Bot Token（必須）
intents = 33281                 # Gateway Intents（オプション、デフォルト値は 33281）
enabled = true                  # 有効にするかどうか（オプション、デフォルト値は true）

# アカウント2
[DiscordAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
intents = 33281
enabled = true
```

**各アカウントの設定項目の説明:**

- `token`：Discord Bot Token（必須）。[Discord Developer Portal](https://discord.com/developers/applications) から取得します。
- `intents`：Gateway Intents のビットマスク（オプション、デフォルト値は `33281`）。Bot がサブスクライブするイベントの種類を決定します。
- `bot_id`：Bot のユーザー ID（オプション、実行時に READY イベントから自動的に取得されるため、手動で入力する必要はありません）。
- `enabled`：このアカウントを有効にするかどうか（オプション、デフォルト値は `true`）。

### Gateway Intents

Intents はビットマスクを使用し、各 Intent の値をビット論理和（`|`）で計算します：

| Intent | ビット | 値 | 説明 | Privileged |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | サーバーの作成/削除/更新、チャンネル、役割の変更 | いいえ |
| GUILD_MEMBERS | `1 << 1` | 2 | メンバーの加入/退去/更新 | はい |
| GUILD_MESSAGES | `1 << 9` | 512 | サーバー内のメッセージの送受信 | いいえ |
| MESSAGE_CONTENT | `1 << 15` | 32768 | メッセージの内容（この Intent がない場合、content は空になります） | はい |

デフォルト値 `33281` は `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)` に等しいです。

> **注意**：Privileged Intents は、Discord Developer Portal → Bot → Privileged Gateway Intents で有効にする必要があります。Bot が 100 以上のサーバーに存在する場合、Discord による審査も必要です。

**API 環境:**
- Discord REST API の基本アドレス：`https://discord.com/api/v10`
- Gateway WebSocket アドレス：`GET /gateway/bot` を使用して動的に取得します。通常は `wss://gateway.discord.gg/?v=10&encoding=json` です。

## 支援されるメッセージ送信タイプ

すべての送信メソッドは、チェーン式の構文で実装されています。たとえば：

```python
from ErisPulse.Core import adapter
discord = adapter.get("discord")

await discord.Send.To("group", channel_id).Text("Hello World!")
```

サポートされている送信タイプは以下の通りです：

- `.Text(text: str)`：純粋なテキストメッセージを送信します。
- `.Embed(embed: dict | list)`：Embed（埋め込み）メッセージを送信します。1つまたは複数のEmbedをサポートしています。
- `.Image(file: bytes | str, filename: str = "image.png")`：画像を送信します。バイナリデータまたはURLをサポートしています。
- `.File(file: bytes | str, filename: str = None)`：ファイルを送信します。バイナリデータまたはURLをサポートしています。
- `.Reply(content: str, message_id: str)`：指定されたメッセージに返信します（便利な終端メソッド）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します。
- `.Raw_json(json_str: str)`：任意のDiscord APIリクエストJSONを送信します。

### チェーン修飾メソッド（組み合わせて使用可能）

チェーン修飾メソッドは `self` を返し、チェーン呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定されたメッセージに返信（引用）します。`message_reference` を設定します。
- `.At(user_id: str)`：指定されたユーザーを@します。`<@user_id>` に変換され、複数回呼び出すことができます。
- `.AtAll()`：全員に@します。`@everyone` に変換されます。

### チェーン呼び出しの例

```python
# 基本的な送信
await discord.Send.To("group", channel_id).Text("Hello")

# メッセージへの返信
await discord.Send.To("group", channel_id).Reply(msg_id).Text("返信メッセージ")

# 便利な返信（一括処理）
await discord.Send.To("group", channel_id).Reply("返信内容", msg_id)

# ユーザーへの@
await discord.Send.To("group", channel_id).At("user_id").Text("こんにちは")

# 複数ユーザーへの@
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("複数ユーザー@")

# 全員への@
await discord.Send.To("group", channel_id).AtAll().Text("お知らせ")

# 組み合わせ
await discord.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("複合メッセージ")

# Embed（埋め込み）メッセージ
embed = {
    "title": "通知",
    "description": "これは埋め込みメッセージです",
    "color": 5814783,
    "fields": [{"name": "フィールド", "value": "値", "inline": True}],
}
await discord.Send.To("group", channel_id).Embed(embed)

# 画像の送信
await discord.Send.To("group", channel_id).Image("https://example.com/image.png")
```

### プライベートメッセージの送信

プライベートメッセージを送信する際、アダプターは自動的にDMチャンネルを作成します：

```python
# プライベートメッセージの送信
await discord.Send.To("user", user_id).Text("プライベートメッセージの内容")
await discord.Send.To("user", user_id).Embed(embed)
```

### メッセージ操作

```python
# メッセージの撤回
await discord.Send.To("group", channel_id).Recall(msg_id)

# OneBot12形式
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
]
await discord.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、直接 await を使用して送信結果を取得できます。返り値は ErisPulse アダプタの標準化された返り値規格に従います：

```python
{
    "status": "ok",           // 実行ステータス: "ok" または "failed"
    "retcode": 0,             // 戻り値コード（0 は成功を意味します）
    "data": {...},            // Discord API の元のレスポンス
    "message_id": "xxx",      // メッセージID（メッセージを送信した場合）
    "message": "",            // エラーメッセージ
    "discord_raw": {...}      // 元のレスポンスデータ
}
```

### エラーコードの説明

| retcode | 说明 |
|---------|------|
| 0 | 成功 |
| 33001 | ネットワークエラー（接続失敗、タイムアウトなど） |
| 34000 | Discord API がエラーを返した（権限不足、パラメータエラーなど） |

## 特有イベントタイプ

このプラットフォームの機能を使用するには、`platform == "discord"` の検証が必要です。

### 核心的な違い

1. **サーバー/チャンネルシステム**：Discord はサーバー（Guild）とチャンネル（Channel）の2層構造を使用しており、チャンネルがメッセージの基本的な送信先となります。
2. **Gateway イベント**：すべてのイベントは WebSocket Gateway を通じて受信され、Opcode + Dispatch メカニズムを使用します。
3. **Intents 訂読**：ビットマスクを使用してイベントタイプを訂読し、`MESSAGE_CONTENT` は Privileged 権限が必要です。
4. **メッセージセグメントタイプ**：テキスト、画像、ファイル、動画、音声、Embed、Sticker などのメッセージセグメントをサポートします。
5. **Mention 形式**：Discord は `<@user_id>` 形式でユーザーをメンションします。

### 拡張フィールド

すべての固有フィールドは `discord_` で始まるプレフィックスで識別されます：
- `discord_raw`：元の Discord イベントデータ
- `discord_raw_type`：元のイベントタイプ名（例：`MESSAGE_CREATE`）
- `discord_guild_id`：サーバー ID
- `discord_channel_id`：チャンネル ID

### detail_type のマッピング

| Discord の状況 | detail_type | 説明 |
|---|---|---|
| チャンネルメッセージ | `channel` | ErisPulse 拡張タイプ |
| プライベートメッセージ（DM） | `private` | OneBot12 標準タイプ |

### イベントタイプのマッピング

| Discord イベント | OneBot12 type | detail_type | 説明 |
|---|---|---|---|
| MESSAGE_CREATE | message | channel/private | メッセージ作成 |
| MESSAGE_UPDATE | message | channel/private | メッセージ編集 |
| MESSAGE_DELETE | notice | group_message_delete / private_message_delete | メッセージ削除 |
| GUILD_MEMBER_ADD | notice | group_member_increase | メンバー加入 |
| GUILD_MEMBER_REMOVE | notice | group_member_decrease | メンバー退去 |
| GUILD_MEMBER_UPDATE | notice | group_member_update | メンバー情報更新 |
| GUILD_ROLE_CREATE | notice | group_role_create | ロール作成 |
| GUILD_ROLE_DELETE | notice | group_role_delete | ロール削除 |
| CHANNEL_CREATE | notice | channel_create | チャンネル作成 |
| CHANNEL_DELETE | notice | channel_delete | チャンネル削除 |
| INTERACTION_CREATE | request | interaction | 交互（ボタン、コマンドなど） |

### 特殊フィールドの例

```python
# チャンネルのテキストメッセージ
{
  "type": "message",
  "detail_type": "channel",
  "user_id": "送信者ID",
  "user_nickname": "ユーザー名",
  "group_id": "チャンネルID",
  "message_id": "メッセージID",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_guild_id": "サーバーID",
  "discord_channel_id": "チャンネルID",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# プライベートメッセージ
{
  "type": "message",
  "detail_type": "private",
  "user_id": "送信者ID",
  "user_nickname": "ユーザー名",
  "message_id": "メッセージID",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_channel_id": "DMチャンネルID",
  "message": [
    {"type": "text", "data": {"text": "プライベートメッセージ"}}
  ],
  "alt_message": "プライベートメッセージ"
}

# Embed を含むメッセージ
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "discord_embed", "data": {"embed": {...}}}
  ],
  "alt_message": "[埋め込みメッセージ]"
}

# 附件を含むメッセージ
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "text", "data": {"text": "この画像を見て"}},
    {"type": "image", "data": {"file": "画像URL", "url": "画像URL", "file_name": "image.png"}}
  ],
  "alt_message": "この画像を見て[画像]"
}
```

### メッセージセグメントタイプ

Discord のメッセージ内容は、`content`、`attachments`、`embeds` フィールドに基づいて対応するメッセージセグメントに自動的に変換されます：

| 入力元 | 変換タイプ | 説明 |
|---|---|---|
| content テキスト | `text` | 純粋なテキスト内容 |
| content `<@id>` | `mention` | ユーザーのメンション |
| content `<@&id>` | `discord_role_mention` | ロールのメンション |
| content `<#id>` | `discord_channel_mention` | チャンネルのメンション |
| attachments (image/*) | `image` | 画像の添付 |
| attachments (video/*) | `video` | 動画の添付 |
| attachments (audio/*) | `audio` | 音声の添付 |
| attachments (その他のタイプ) | `file` | その他のファイルの添付 |
| embeds | `discord_embed` | 埋め込みメッセージ |
| sticker_items | `discord_sticker` | ステッカー |

### discord_embed メッセージセグメント

```json
{
  "type": "discord_embed",
  "data": {
    "embed": {
      "title": "タイトル",
      "description": "説明",
      "color": 12345,
      "fields": [...],
      "image": {"url": "..."},
      "thumbnail": {"url": "..."},
      "footer": {"text": "..."}
    }
  }
}
```

## ゲートウェイ接続

### 接続フロー

1. `GET /gateway/bot` を呼び出して WebSocket ゲートウェイ URL を取得します。
2. `wss://gateway.discord.gg/?v=10&encoding=json` に接続します。
3. opcode 10 HELLO を受信：`heartbeat_interval` を含みます。
4. opcode 2 IDENTIFY を送信：token、intents、properties を含みます。
5. ハートビートループを開始：`heartbeat_interval` に従って opcode 1 Heartbeat を送信します。
6. opcode 0 Dispatch を受信：イベントの配信（`t`=イベント名, `s`=シーケンス番号, `d`=データ）。
7. opcode 11 Heartbeat ACK を受信：ハートビートの確認。

### Opcode 説明

| Opcode | 名称 | 方向 | 説明 |
|--------|------|------|------|
| 0 | Dispatch | 受信 | イベントの配信（`t`、`s`、`d` フィールドを含む） |
| 1 | Heartbeat | 送信/受信 | ハートビート（最後の seq を含む） |
| 2 | Identify | 送信 | 身分認証 |
| 6 | Resume | 送信 | セッションの復元 |
| 7 | Reconnect | 受信 | サーバーからの再接続要求 |
| 9 | Invalid Session | 受信 | 無効なセッション |
| 10 | Hello | 受信 | 接続のハンドシェイク（`heartbeat_interval` を含む） |
| 11 | Heartbeat ACK | 受信 | ハートビートの確認 |

### 断線時の再接続と RESUME

- 接続が切断された後、アダプターは自動的に再接続を試みます。
- 以前に `session_id` が存在する場合、`session_id` を用いて opcode 6 Resume を優先してセッションを復元します。
- Resume は `token`、`session_id`、最後の `seq` を含み、中断したイベントを補います。
- opcode 7 (Reconnect) を受信した場合、セッションの状態を保持して再接続します。
- opcode 9 (Invalid Session) を受信し、`d=false` の場合、セッションをクリアして IDENTIFY を再実行します。

### ハートビートメカニズム

- HELLO を受信した後、`heartbeat_interval * random()` ミリ秒待機して最初のハートビートを送信します。
- その後、`heartbeat_interval` ミリ秒ごとにハートビートを送信します。
- ハートビートは最後の `seq` 値を含みます（opcode 1、`d: seq`）。
- ハートビートを送信した後、`heartbeat_interval` 内に ACK（opcode 11）が受信されない場合、接続に異常が発生したと判断し、再接続を行います。

## 使用例

### チャンネルメッセージの処理

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

discord = sdk.adapter.get("discord")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "discord":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await discord.Send.To("group", channel_id).Text("Hello!")
```

### プライベートメッセージの処理

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "discord":
        return
    if not event.is_dm():
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await discord.Send.To("user", user_id).Text(f"あなたが言った: {text}")
```

### Embedメッセージの送信

```python
embed = {
    "title": "サーバーのお知らせ",
    "description": "ErisPulse Discordアダプターへようこそ",
    "color": 3447003,
    "fields": [
        {"name": "バージョン", "value": "4.0.0", "inline": True},
        {"name": "フレームワーク", "value": "ErisPulse", "inline": True},
    ],
    "footer": {"text": "Powered by ErisPulse"},
    "timestamp": "2025-01-01T00:00:00.000Z",
}
await discord.Send.To("group", channel_id).Embed(embed)
```

### Discord固有メソッドの使用

```python
@message.on_message()
async def handle(event):
    if event.get("platform") != "discord":
        return

    channel_id = event.get_channel_id()
    guild_id = event.get_guild_id()
    is_dm = event.is_dm()
    embeds = event.get_embeds()
    attachments = event.get_attachments()

    if embeds:
        await discord.Send.To("group", channel_id).Text(
            f"Embedが {len(embeds)} 個届きました"
        )
```

### 交互イベントの処理

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_interaction(event):
    if event.get("platform") != "discord":
        return

    interaction = event.get_interaction_data()
    if interaction.get("type") == 3:  # MESSAGE_COMPONENT
        await event.reply("ボタンがクリックされました！")
```