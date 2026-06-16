# Discord プラットフォーム仕様ドキュメント

DiscordAdapter は Discord Gateway (WebSocket) および REST API v10 プロトコルに基づいて構築されたアダプタであり、Discord Bot のコア機能を統合し、統一されたイベント処理とメッセージ操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.0.0
- メンテナー: ErisPulse
- Discord API バージョン: v10

## 基本情報

- プラットフォームの概要：Discord は広く人気のあるコミュニティ通話プラットフォームであり、サーバー、チャンネル、DM（DM: Direct Message）など、多様な会話形式をサポートし、完全な Bot 開発インターフェースを提供します
- アダプタ名：DiscordAdapter
- マルチアカウントサポート：複数の Discord Bot を同時に設定可能
- 接続方式：Gateway WebSocket（イベント受信）+ REST API（メッセージ送信/インターフェース呼び出し）
- 認証方式：Bot Token（HTTP ヘッダー `Authorization: Bot {token}`、Gateway IDENTIFY payload に token を含める）
- チェーン修飾サポート：`.Reply()`、`.At()`、`.AtAll()` などのチェーン修飾メソッドをサポート
- OneBot12 互換性：OneBot12 形式メッセージの送信をサポート

## 設定説明

DiscordAdapter はマルチアカウント設定をサポートしており、各アカウントは独立した Discord Bot に対応します。

```toml
# config.toml

# アカウント1
[DiscordAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"       # Discord Bot Token（必須）
intents = 33281                 # Gateway Intents（オプション、デフォルト 33281）
enabled = true                  # 有効にするかどうか（オプション、デフォルト true）

# アカウント2
[DiscordAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
intents = 33281
enabled = true
```

**設定項目説明（各アカウントについて）：**

- `token`：Discord Bot Token（必須）。[Discord Developer Portal](https://discord.com/developers/applications) から取得
- `intents`：Gateway Intents ビットマスク（オプション、デフォルト `33281`）。Bot が訂閲するイベントタイプを決定します
- `bot_id`：Bot のユーザー ID（オプション、実行時 READY イベントから自動的に取得されるため手動で入力する必要はありません）
- `enabled`：このアカウントを有効にするかどうか（オプション、デフォルト `true`）

### Gateway Intents

Intents はビットマスクを使用し、各 Intent 値のビット OR（`|`）演算で計算されます：

| Intent | ビット | 値 | 説明 | Privileged |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | サーバー作成/削除/更新、チャンネル、ロールの変更 | 否 |
| GUILD_MEMBERS | `1 << 1` | 2 | メンバーの追加/削除/更新 | 是 |
| GUILD_MESSAGES | `1 << 9` | 512 | サーバーメッセージの送受信 | 否 |
| MESSAGE_CONTENT | `1 << 15` | 32768 | メッセージコンテンツ（この Intentsがない場合 content は空） | 是 |

デフォルト値 `33281` = `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)`。

> **注意**：Privileged Intents は Discord Developer Portal → Bot → Privileged Gateway Intents で有効にする必要があります。Bot が100個以上のサーバーにある場合は、Discord の承認を通過する必要があります。

**API 環境：**
- Discord REST API ベース URL：`https://discord.com/api/v10`
- Gateway WebSocket URL：`GET /gateway/bot` で動的に取得します。通常は `wss://gateway.discord.gg/?v=10&encoding=json`

## サポートされるメッセージ送信タイプ

すべての送信メソッドはチェーン構文を実装しており、例えば以下のようになります：
```python
from ErisPulse.Core import adapter
discord = adapter.get("discord")

await discord.Send.To("group", channel_id).Text("Hello World!")
```

サポートされる送信タイプは以下の通りです：
- `.Text(text: str)`：純テキストメッセージを送信します。
- `.Embed(embed: dict | list)`：Embed 埋め込みメッセージを送信します。単一または複数の Embed をサポートします。
- `.Image(file: bytes | str, filename: str = "image.png")`：画像を送信します。バイナリデータまたは URL をサポートします。
- `.File(file: bytes | str, filename: str = None)`：ファイルを送信します。バイナリデータまたは URL をサポートします。
- `.Reply(content: str, message_id: str)`：指定されたメッセージに返信します（便利なショートカットメソッド）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12 形式のメッセージを送信します。
- `.Raw_json(json_str: str)`：任意の Discord API リクエスト JSON を送信します。

### チェーン修飾メソッド（組み合わせ可能）

チェーン修飾メソッドは `self` を返し、チェーン呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：メッセージを返信（参照）し、`message_reference` を設定します。
- `.At(user_id: str)`：指定したユーザーに@を付与します。`<@user_id>` に変換され、複数回呼び出すことができます。
- `.AtAll()`：全員に@を付与します。`@everyone` に変換されます。

### チェーン呼び出しの例

```python
# 基本的な送信
await discord.Send.To("group", channel_id).Text("Hello")

# メッセージに返信
await discord.Send.To("group", channel_id).Reply(msg_id).Text("返信メッセージ")

# 便利な返信（ワンステップ）
await discord.Send.To("group", channel_id).Reply("返信内容", msg_id)

# ユーザーに@を付ける
await discord.Send.To("group", channel_id).At("user_id").Text("こんにちは")

# 複数のユーザーに@を付ける
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("複数ユーザー@")

# 全員に@を付ける
await discord.Send.To("group", channel_id).AtAll().Text("お知らせ")

# 組み合わせて使用
await discord.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("複合メッセージ")

# Embed 埋め込みメッセージ
embed = {
    "title": "通知",
    "description": "これは埋め込みメッセージです",
    "color": 5814783,
    "fields": [{"name": "フィールド", "value": "値", "inline": True}],
}
await discord.Send.To("group", channel_id).Embed(embed)

# 画像を送信
await discord.Send.To("group", channel_id).Image("https://example.com/image.png")
```

### DM（Direct Message）送信

DM を送信する際、アダプタは自動的に DM チャンネルを作成します：

```python
# DM を送信
await discord.Send.To("user", user_id).Text("DMコンテンツ")
await discord.Send.To("user", user_id).Embed(embed)
```

### メッセージ操作

```python
# メッセージを取り消す（撤回）
await discord.Send.To("group", channel_id).Recall(msg_id)

# OneBot12 形式
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
]
await discord.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、直接 await して送信結果を取得できます。戻り値は ErisPulse アダプタの標準化された戻り値仕様に従います：

```python
{
    "status": "ok",           // 実行状態: "ok" または "failed"
    "retcode": 0,             // 戻りコード（0 は成功）
    "data": {...},            // Discord API の元のレスポンス
    "message_id": "xxx",      // メッセージID（メッセージを送信する場合）
    "message": "",            // エラーメッセージ
    "discord_raw": {...}      // 元のレスポンスデータ
}
```

### エラーコードの説明

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 33001 | ネットワークエラー（接続失敗、タイムアウトなど） |
| 34000 | Discord API エラー（権限不足、パラメータエラーなど） |

## 固有のイベントタイプ

プラットフォーム固有の機能を使用するには、`platform == "discord"` の検査が必要です。

### コアの違い点

1. **サーバー/チャンネルシステム**：Discord はサーバー（Guild）とチャンネル（Channel）の2層構造を使用しており、チャンネルがメッセージの基本的な送信ターゲットです
2. **Gateway イベント**：すべてのイベントは WebSocket Gateway 経由で受信され、Opcode + Dispatch メカニズムを使用します
3. **Intents 訂閲**：ビットマスクを使用してイベントタイプを訂閲し、`MESSAGE_CONTENT` には Privileged 権限が必要です
4. **メッセージセグメントタイプ**：テキスト、画像、ファイル、動画、音声、Embed、Sticker などのメッセージセグメントをサポート
5. **Mention 形式**：Discord はユーザー参照に `<@user_id>` 形式を使用します

### 拡張フィールド

すべての固有フィールドは `discord_` プレフィックスで識別されます：
- `discord_raw`：元の Discord イベントデータ
- `discord_raw_type`：元のイベントタイプ名（例：`MESSAGE_CREATE`）
- `discord_guild_id`：サーバー ID
- `discord_channel_id`：チャンネル ID

### detail_type マッピング

| Discord のシナリオ | detail_type | 説明 |
|---|---|---|
| チャンネルメッセージ | `channel` | ErisPulse 拡張タイプ |
| DM（プライベートメッセージ） | `private` | OneBot12 標準タイプ |

### イベントタイプマッピング

| Discord イベント | OneBot12 type | detail_type | 説明 |
|---|---|---|---|
| MESSAGE_CREATE | message | channel/private | メッセージ作成 |
| MESSAGE_UPDATE | message | channel/private | メッセージ編集 |
| MESSAGE_DELETE | notice | group_message_delete / private_message_delete | メッセージ削除 |
| GUILD_MEMBER_ADD | notice | group_member_increase | メンバー追加 |
| GUILD_MEMBER_REMOVE | notice | group_member_decrease | メンバー削除 |
| GUILD_MEMBER_UPDATE | notice | group_member_update | メンバー情報更新 |
| GUILD_ROLE_CREATE | notice | group_role_create | ロール作成 |
| GUILD_ROLE_DELETE | notice | group_role_delete | ロール削除 |
| CHANNEL_CREATE | notice | channel_create | チャンネル作成 |
| CHANNEL_DELETE | notice | channel_delete | チャンネル削除 |
| INTERACTION_CREATE | request | interaction | インタラクション（ボタン、コマンドなど） |

### 特殊フィールドの例

```python
# チャンネルテキストメッセージ
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

# DMメッセージ
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
    {"type": "text", "data": {"text": "DMコンテンツ"}}
  ],
  "alt_message": "DMコンテンツ"
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

# 添付ファイルを含むメッセージ
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

Discord のメッセージコンテンツは、`content`、`attachments`、`embeds` フィールドに基づいて対応するメッセージセグメントに自動的に変換されます：

| 出典 | 変換タイプ | 説明 |
|---|---|---|
| content テキスト | `text` | 純テキストコンテンツ |
| content `<@id>` | `mention` | ユーザー参照 |
| content `<@&id>` | `discord_role_mention` | ロール参照 |
| content `<#id>` | `discord_channel_mention` | チャンネル参照 |
| attachments (image/*) | `image` | 画像添付ファイル |
| attachments (video/*) | `video` | 動画添付ファイル |
| attachments (audio/*) | `audio` | 音声添付ファイル |
| attachments (その他) | `file` | ファイル添付ファイル |
| embeds | `discord_embed` | 埋め込みメッセージ |
| sticker_items | `discord_sticker` | スタンプ |

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

## Gateway 接続

### 接続フロー

1. `GET /gateway/bot` を呼び出して WebSocket Gateway URL を取得
2. `wss://gateway.discord.gg/?v=10&encoding=json` に接続
3. opcode 10 HELLO を受信：`heartbeat_interval` を含みます
4. opcode 2 IDENTIFY を送信：token、intents、properties を含みます
5. ハートビートループ開始：`heartbeat_interval` ごとに opcode 1 Heartbeat を送信
6. opcode 0 Dispatch を受信：イベント配信（`t`=イベント名、`s`=シーケンス番号、`d`=データ）
7. opcode 11 Heartbeat ACK を受信：ハートビート確認

### Opcode の説明

| Opcode | 名前 | 方向 | 説明 |
|--------|------|------|------|
| 0 | Dispatch | 受信 | イベント配信（`t`、`s`、`d` フィールドを含む） |
| 1 | Heartbeat | 送信/受信 | ハートビート（最後の seq を含む） |
| 2 | Identify | 送信 | 認証 |
| 6 | Resume | 送信 | セッション復旧 |
| 7 | Reconnect | 受信 | サーバーによる再接続要求 |
| 9 | Invalid Session | 受信 | 無効なセッション |
| 10 | Hello | 受信 | 接続ハンドシェイク（`heartbeat_interval` を含む） |
| 11 | Heartbeat ACK | 受信 | ハートビート確認 |

### 切断再接続と RESUME

- 接続が切断された後、アダプタは自動的に再接続を試みます
- 前回の `session_id` がある場合は、RESUME（opcode 6）を優先してセッションを復旧します
- RESUME は `token`、`session_id`、最後の `seq` を含みます。復旧後、漏れているイベントを送信し足します
- opcode 7（Reconnect）を受信した場合は、セッション状態を維持したまま再接続します
- opcode 9（Invalid Session）を受信して `d=false` の場合は、セッションをクリアして再び IDENTIFY を行います

### ハートビートメカニズム

- HELLO を受信した後、`heartbeat_interval * random()` ミリ秒待って最初のハートビートを送信します
- その後は、`heartbeat_interval` ミリ秒ごとにハートビートを送信します
- ハートビートは最後の `seq` 値を含みます（opcode 1、`d: seq`）
- ハートビートを送信してから `heartbeat_interval` 内に ACK（opcode 11）を受信しなかった場合は、接続異常とみなして再接続します

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

### DMの処理

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "discord":
        return
    if not event.is_dm():
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await discord.Send.To("user", user_id).Text(f"あなたは言いました: {text}")
```

### Embed メッセージの送信

```python
embed = {
    "title": "サーバーのお知らせ",
    "description": "ErisPulse Discord アダプターへようこそ",
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

### Discord 固有メソッドの使用

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
            f"{len(embeds)} 個の Embed を受け取りました"
        )
```

### インタラクションイベントの処理

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_interaction(event):
    if event.get("platform") != "discord":
        return

    interaction = event.get_interaction_data()
    if interaction.get("type") == 3:  # MESSAGE_COMPONENT
        await event.reply("ボタンがクリックされました！")