# Discord プラットフォーム特性ドキュメント

DiscordAdapter は、Discord Gateway (WebSocket) および REST API v10 プロトコルに基づいて構築されたアダプターであり、Discord Bot のコア機能を統合し、一貫したイベント処理およびメッセージ操作のインターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.4.3
- メンテナ: ErisPulse
- Discord API バージョン: v10
- 最終更新日: 2026-11-10

## 基本情報

- プラットフォーム概要: Discord は、サーバー、チャンネル、プライベートメッセージなど多様な会話形式をサポートする、人気のあるコミュニティコミュニケーションプラットフォームであり、Bot 開発のための包括的な API を提供します。
- アダプター名: DiscordAdapter
- 多アカウント対応: 複数の Discord Bot を同時に設定できます。
- 接続方法: Gateway WebSocket（イベント受信）+ REST API（メッセージ送信/インターフェース呼び出し）
- 認証方法: Bot Token（HTTP ヘッダー `Authorization: Bot {token}`、Gateway IDENTIFY ペイロードに token 搭載）
- チェーン修飾子対応: `.Reply()`、`.At()`、`.AtAll()` などのチェーン修飾メソッドに対応
- OneBot12 兼容: OneBot12 形式のメッセージ送信に対応

## 設定説明

DiscordAdapter は複数アカウントの設定をサポートし、各アカウントは個別の Discord Bot に対応します。

```toml
# config.toml

# アカウント1
[DiscordAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"       # Discord Bot Token（必須）
intents = 33281                 # Gateway Intents（オプション、デフォルト 33281）
enabled = true                  # 有効化するかどうか（オプション、デフォルト true）

# アカウント2
[DiscordAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
intents = 33281
enabled = true
```

**各アカウントの設定項目説明:**

- `token`: Discord Bot Token（必須）、[Discord Developer Portal](https://discord.com/developers/applications) から取得
- `intents`: Gateway Intents ビットマスク（オプション、デフォルト `33281`）、Bot がサブスクライブするイベントの種類を決定
- `bot_id`: Bot のユーザー ID（オプション、実行時に READY イベントから自動取得、手動入力不要）
- `enabled`: そのアカウントを有効化するかどうか（オプション、デフォルト `true`）

### Gateway Intents

Intents はビットマスクを使用し、各 Intent 値をビット演算 OR (`|`) で計算します：

| Intent | ビット | 値 | 説明 | Privileged |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | サーバーの作成/削除/更新、チャンネル、ロールの変更 | 否 |
| GUILD_MEMBERS | `1 << 1` | 2 | メンバーの加入/離脱/更新 | 是 |
| GUILD_MESSAGES | `1 << 9` | 512 | サーバーのメッセージ送受信 | 否 |
| MESSAGE_CONTENT | `1 << 15` | 32768 | メッセージ内容（この Intent がない場合 content は空） | 是 |

デフォルト値 `33281` = `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)`。

> **注意**: Privileged Intents は Discord Developer Portal → Bot → Privileged Gateway Intents で有効化する必要があります。Bot が 100 以上のサーバーに存在する場合は、Discord 審査も必要です。

**API 環境:**
- Discord REST API 基本アドレス: `https://discord.com/api/v10`
- Gateway WebSocket アドレス: `GET /gateway/bot` で動的に取得、通常は `wss://gateway.discord.gg/?v=10&encoding=json`

## 標準化対応（4.4.3）

### イベント変更

1. **イベント id の一意性**: MESSAGE_UPDATE / MESSAGE_DELETE、REACTION_ADD / REMOVE（REMOVE_ALL / REMOVE_EMOJI 含む）などの派生イベントの `id` は `"イベント名:元のid"`（例: `MESSAGE_UPDATE:123456`）に変更され、CREATE イベントと id が衝突してフレームワークで重複排除されるのを防ぎます。
2. **イベント `self.account_id` の注入**: すべてのイベントに、イベントを生成したアカウント名が含まれ、多アカウント下では `event.reply()` は該当アカウントで自動的に受理・送信されます。
3. **INTERACTION_CREATE イベントの修正**: 元々誤って `type="request"`（detail_type `interaction`）と表示されていましたが、現在は `type="notice"`、`detail_type="discord_interaction"` に変更され、対話データは `discord_interaction` フィールドに保持されます。

### Api 署名対応

| 動作 | 署名 | 説明 |
|------|------|------|
| get_channel_info | `(guild_id, channel_id)` | 新しい署名 guild_id が先頭に、1 つの位置引数のみ渡した場合は旧署名を互換する（channel_id と見なす） |
| get_channel_list | `(guild_id, joined_only=False)` | 新たに joined_only キーワード引数を追加 |
| get_guild_info / get_guild_list | - | data は `guild_id` / `guild_name`（旧 `group_id` / `group_name` フィールドは保持、既存の呼び出し元への破壊を避ける） |

### エラーコード規格化

エラーコードは SDK の標準化に従っており（元の `34000` は使用されない）:

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 33001 | ネットワークエラー（接続失敗、タイムアウトなど） |
| 34100 | プラットフォーム拒否（元の応答は `discord_raw` フィールドに保持） |
| 10002 | 不支持の動作（`get_guild_member_list` / `set_guild_name` / `get_channel_member_info` / `get_channel_member_list` / `leave_channel` は明示的に返す、Discord REST には対応する意味がない） |
| 10003 | パラメータエラー（例: メッセージ登録表に該当するコンテキストがないため撤回できない） |

## v5 ファンタジー更新（4.2.0）

このアダプターは v5 ファンタジーに完全に整合しています（増分アップグレード、API 兼容）：

- **BaseConverter 継承**: 転換器の共通フィールドはフレームワーク `build_base_event` で構築されます。
- **Api DSL**: 標準 Api 動作のマッピング（以下を参照）
- **標準 keyboard 段**: Discord components（action row + buttons）に変換；.Keyboard(rows) 修飾子は汎用構造を受け入れる
- **対話コールバックの標準フィールド**: INTERACTION_CREATE イベントには interaction_id / button_data が含まれる
- **spawn_background タスクの所属**: 接続タスクは runtime.spawn_background を使用
- **フレームワークのソフト依存**: ErisPulse>=2.7.1 を実行時に検出して警告を表示；起動時にバージョンログを出力

### 標準 Api 動作

```python
from ErisPulse import sdk
discord = sdk.adapter.get("discord")

result = await discord.Api.get_self_info()                # GET /users/@me
result = await discord.Api.get_user_info(user_id)         # GET /users/{id}
result = await discord.Api.get_guild_info(guild_id)       # GET /guilds/{id}（data は guild_id / guild_name を使用）
result = await discord.Api.get_guild_list()               # GET /users/@me/guilds
result = await discord.Api.get_channel_info(guild_id, channel_id)  # GET /channels/{id}（新しい署名 guild_id が先頭）
result = await discord.Api.get_channel_list(guild_id)     # GET /guilds/{id}/channels
result = await discord.Api.get_guild_member_info(gid, uid)
await discord.Api.delete_message(message_id)              # 登録表は自動的に channel_id を補完
await discord.Api.leave_guild(guild_id)
result = await discord.Api.Using("main").get_self_info()
```

### ボタン（keyboard / components）

```python
rows = [[{"label": "クリック", "type": "callback", "data": "btn:1"},
         {"label": "公式サイト",  "type": "link",     "data": "https://example.com"}]]
await discord.Send.To("channel", channel_id).Keyboard(rows).Text("選択してください")
# 自動的に components に変換：callback → custom_id / link → url
```

---

## 支援されるメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実行されます。例：

```python
from ErisPulse.Core import adapter
discord = adapter.get("discord")

await discord.Send.To("group", channel_id).Text("Hello World!")
```

サポートされる送信タイプは以下の通りです：

- `.Text(text: str)`：テキストメッセージを送信。
- `.Embed(embed: dict | list)`：埋め込みメッセージを送信、1 つまたは複数の Embed をサポート。
- `.MergeForward(nodes, title="合併チャット記録")`：埋め込みメッセージを送信（タイトル + 各メッセージが 1 つの field、25 fields まで、value は 1024 文字まで）。
- `.Image(file: bytes | str, filename: str = "image.png")`：画像を送信、バイトデータまたは URL をサポート。
- `.File(file: bytes | str, filename: str = None)`：ファイルを送信、バイトデータまたは URL をサポート。
- `.Reply(content: str, message_id: str)`：指定メッセージに返信（便利な終端メソッド）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12 形式メッセージを送信。
- `.Raw_json(json_str: str)`：任意の Discord API リクエスト JSON を送信。

### チェーン修飾メソッド（複数使用可能）

チェーン修飾メソッドは `self` を返し、チェーンで呼び出すことができます。最終送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定メッセージに返信（引用）、`message_reference` を設定。
- `.At(user_id: str)`：指定ユーザーを @、`<@user_id>` に変換、複数回呼び出せる。
- `.AtAll()`：全員を @、`@everyone` に変換。

### チェーン呼び出しの例

```python
# 基本送信
await discord.Send.To("group", channel_id).Text("Hello")

# メッセージに返信
await discord.Send.To("group", channel_id).Reply(msg_id).Text("返信メッセージ")

# 便利な返信（1ステップ）
await discord.Send.To("group", channel_id).Reply("返信内容", msg_id)

# ユーザーを @
await discord.Send.To("group", channel_id).At("user_id").Text("こんにちは")

# 複数ユーザーを @
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("複数ユーザー@")

# 全員を @
await discord.Send.To("group", channel_id).AtAll().Text("お知らせ")

# 組み合わせ
await discord.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("複合メッセージ")

# 埋め込みメッセージ
embed = {
    "title": "通知",
    "description": "これは埋め込みメッセージです",
    "color": 5814783,
    "fields": [{"name": "フィールド", "value": "値", "inline": True}],
}
await discord.Send.To("group", channel_id).Embed(embed)

# 画像送信
await discord.Send.To("group", channel_id).Image("https://example.com/image.png")
```

### プライベートメッセージ送信

プライベートメッセージ送信時、アダプターは自動的に DM チャンネルを作成します：

```python
# プライベートメッセージ送信
await discord.Send.To("user", user_id).Text("プライベートメッセージ内容")
await discord.Send.To("user", user_id).Embed(embed)
```

### メッセージ操作

```python
# メッセージ撤回
await discord.Send.To("group", channel_id).Recall(msg_id)

# OneBot12 形式
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
]
await discord.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、await で送信結果を取得できます。返り値は ErisPulse アダプターの標準化された返り値規格に従います：

```python
{
    "status": "ok",           // 実行状態: "ok" または "failed"
    "retcode": 0,             // 返り値コード（0 が成功）
    "data": {...},            // Discord API 原始応答
    "message_id": "xxx",      // メッセージID（送信メッセージの場合）
    "message": "",            // エラーメッセージ
    "discord_raw": {...}      // 原始応答データ
}
```

### エラーコードの説明

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 33001 | ネットワークエラー（接続失敗、タイムアウトなど） |
| 34100 | プラットフォーム拒否（権限不足、パラメータエラーなど、元の応答は `discord_raw` フィールドに保持） |
| 10002 | 不支持の動作（「標準化対応（4.4.3）」のエラーコード規格を参照） |
| 10003 | パラメータエラー（例: 撤回時に該当するメッセージコンテキストがない） |

## 特有のイベントタイプ

`platform == "discord"` を検証してから本プラットフォームの特性を使用する必要があります。

### 核心的な違い

1. **サーバー/チャンネル構造**: Discord はサーバー（Guild）とチャンネル（Channel）の2層構造を使用し、チャンネルがメッセージの基本的な送信ターゲットです。
2. **Gateway イベント**: すべてのイベントは WebSocket Gateway を通じて受信され、Opcode + Dispatch 仕組みを使用します。
3. **Intents 訂正**: 位マスクを使用してイベントタイプを訂正し、`MESSAGE_CONTENT` は Privileged 権限が必要です。
4. **メッセージセグメントタイプ**: テキスト、画像、ファイル、ビデオ、音声、Embed、Sticker などのメッセージセグメントをサポートします。
5. **Mention 形式**: Discord は `<@user_id>` 形式を使用してユーザーのメンションを表します。

### 拡張フィールド

すべての特有のフィールドは `discord_` で始まります：
- `discord_raw`: 原始 Discord イベントデータ
- `discord_raw_type`: 原始イベントのタイプ名（例: `MESSAGE_CREATE`）
- `discord_guild_id`: サーバー ID
- `discord_channel_id`: チャンネル ID
- `discord_interaction`: 対話イベントデータ（INTERACTION_CREATE）

### detail_type マッピング

| Discord の状況 | detail_type | 説明 |
|---|---|---|
| チャンネルメッセージ | `channel` | ErisPulse 拡張タイプ |
| プライベートメッセージ（DM） | `private` | OneBot12 標準タイプ |

### イベントタイプマッピング

| Discord イベント | OneBot12 type | detail_type | 説明 |
|---|---|---|---|
| MESSAGE_CREATE | message | channel/private | メッセージ作成 |
| MESSAGE_UPDATE | message | channel/private | メッセージ編集（id は `MESSAGE_UPDATE:元のid`） |
| MESSAGE_DELETE | notice | group_message_delete / private_message_delete | メッセージ削除（id は `MESSAGE_DELETE:元のid`） |
| MESSAGE_REACTION_ADD | notice | group_message_reaction_add | リアクション追加（id は `MESSAGE_REACTION_ADD:元のid`） |
| MESSAGE_REACTION_REMOVE | notice | group_message_reaction_remove | リアクション削除（id は `MESSAGE_REACTION_REMOVE:元のid`） |
| GUILD_MEMBER_ADD | notice | group_member_increase | メンバー加入 |
| GUILD_MEMBER_REMOVE | notice | group_member_decrease | メンバー離脱 |
| GUILD_MEMBER_UPDATE | notice | group_member_update | メンバー情報更新 |
| GUILD_ROLE_CREATE | notice | group_role_create | ロール作成 |
| GUILD_ROLE_DELETE | notice | group_role_delete | ロール削除 |
| CHANNEL_CREATE | notice | channel_create | チャンネル作成 |
| CHANNEL_DELETE | notice | channel_delete | チャンネル削除 |
| INTERACTION_CREATE | notice | discord_interaction | 対話（ボタン、コマンドなど） |

> 4.4.3 以降、MESSAGE_UPDATE / MESSAGE_DELETE、REACTION_ADD / REMOVE などの非作成イベントの
> `id` はすべて `"イベント名:元のid"` に変更され、MESSAGE_CREATE イベントの id と衝突してフレームワークで重複排除されるのを防ぎます。

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
  "self": {
    "platform": "discord",
    "user_id": "BotID",
    "account_id": "default"
  },
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
    {"type": "text", "data": {"text": "プライベートメッセージ内容"}}
  ],
  "alt_message": "プライベートメッセージ内容"
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
    {"type": "text", "data": {"text": "この画像を見てください"}},
    {"type": "image", "data": {"file": "画像URL", "url": "画像URL", "file_name": "image.png"}}
  ],
  "alt_message": "この画像を見てください[画像]"
}
```

### メッセージセグメントタイプ

Discord メッセージの内容は `content`、`attachments`、`embeds` フィールドに基づいて対応するメッセージセグメントに自動変換されます：

| 源 | 変換タイプ | 説明 |
|---|---|---|
| content テキスト | `text` | テキスト内容 |
| content `<@id>` | `mention` | ユーザーのメンション |
| content `<@&id>` | `discord_role_mention` | ロールのメンション |
| content `<#id>` | `discord_channel_mention` | チャンネルのメンション |
| attachments (image/*) | `image` | 画像の添付 |
| attachments (video/*) | `video` | ビデオの添付 |
| attachments (audio/*) | `audio` | 音声の添付 |
| attachments (その他の) | `file` | ファイルの添付 |
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

## Gateway 接続

### 接続フロー

1. `GET /gateway/bot` を呼び出して WebSocket ゲートウェイ URL を取得する
2. `wss://gateway.discord.gg/?v=10&encoding=json` に接続する
3. opcode 10 HELLO を受信: `heartbeat_interval` を含む
4. opcode 2 IDENTIFY を送信: token、intents、properties を含む
5. ハートビートループを開始: `heartbeat_interval` で定期的に opcode 1 Heartbeat を送信
6. opcode 0 Dispatch を受信: イベント配信（`t`=イベント名, `s`=シーケンス番号, `d`=データ）
7. opcode 11 Heartbeat ACK を受信: ハートビート確認

### Opcode 説明

| Opcode | 名称 | 方向 | 説明 |
|--------|------|------|------|
| 0 | Dispatch | 受信 | イベント配信（`t`、`s`、`d` フィールドを含む） |
| 1 | Heartbeat | 送信/受信 | ハートビート（最後の seq を含む） |
| 2 | Identify | 送信 | 身分認証 |
| 6 | Resume | 送信 | セッションの再開 |
| 7 | Reconnect | 受信 | サーバーからの再接続要求 |
| 9 | Invalid Session | 受信 | 無効なセッション |
| 10 | Hello | 受信 | 接続ハンドシェイク（`heartbeat_interval` を含む） |
| 11 | Heartbeat ACK | 受信 | ハートビート確認 |

### 切断再接続と RESUME

- 接続が切断された後、アダプターは自動的に再接続を試みます
- 以前に `session_id` があれば、優先的に RESUME（opcode 6）でセッションを再開します
- RESUME は `token`、`session_id`、最後の `seq` を含み、切断後に漏れたイベントを再送します
- opcode 7（Reconnect）を受信した場合、セッションの状態を保持して再接続します
- opcode 9（Invalid Session）を受信し、`d=false` の場合、セッションをクリアして再 IDENTIFY を行います

### ハートビートメカニズム

- HELLO を受信した後、`heartbeat_interval * random()` ミリ秒待って最初のハートビートを送信します
- その後、`heartbeat_interval` ミリ秒ごとにハートビートを送信します
- ハートビートは最後の `seq` 値を含みます（opcode 1、`d: seq`）
- ハートビートを送信した後、`heartbeat_interval` 内に ACK（opcode 11）が受信されない場合、接続異常と見なし、再接続します

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

### Embed メッセージの送信

```python
embed = {
    "title": "サーバーのお知らせ",
    "description": "ErisPulse Discord アダプターをご利用いただきありがとうございます",
    "color": 3447003,
    "fields": [
        {"name": "バージョン", "value": "4.4.3", "inline": True},
        {"name": "フレームワーク", "value": "ErisPulse", "inline": True},
    ],
    "footer": {"text": "Powered by ErisPulse"},
    "timestamp": "2025-01-01T00:00:00.000Z",
}
await discord.Send.To("group", channel_id).Embed(embed)
```

### Discord 特有のメソッドの使用

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
            f"埋め込みメッセージ {len(embeds)} 個を受け取りました"
        )
```

### 対話イベントの処理

4.4.3 以降、INTERACTION_CREATE は `notice` / `discord_interaction` として配信されます：

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "discord":
        return
    if event.get("detail_type") != "discord_interaction":
        return

    interaction = event.get_interaction_data()  # event["discord_interaction"] と同等
    if interaction.get("type") == 3:  # MESSAGE_COMPONENT
        await event.reply("ボタンがクリックされました！")
```