# Kookプラットフォームの特徴ドキュメント

KookAdapterは、Kook（開黒啦）Bot WebSocketプロトコルに基づいて構築されたアダプターであり、Kookのすべての機能モジュールを統合し、一貫したイベント処理とメッセージ操作のインターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.3.2
- 維持者: ShanFish
- 最終更新日: 2026-11-10

## 基本情報

- プラットフォーム概要: Kook（元開黒啦）は、テキスト、音声、ビデオ通信をサポートするコミュニティプラットフォームであり、完全なBot開発インターフェースを提供します。
- アダプター名: KookAdapter
- 多アカウント対応: 複数のKook Botを同時に設定できます。
- 接続方式: WebSocket長接続（Kookゲートウェイ経由）
- 認証方式: Bot Tokenを用いた認証
- 鏈式修飾対応: `.Reply()`、`.At()`、`.AtAll()`などの修飾メソッドをチェーンで使用できます。
- OneBot12互換: OneBot12形式のメッセージ送信をサポートします。

## 設定説明

KookAdapterは複数アカウントの設定に対応しており、各アカウントは独立したKook Botに対応します。

```toml
# config.toml
# アカウント1
[KookAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"     # Kook Bot Token（必須、形式: Bot xxx/xxx）
bot_id = ""                   # BotのユーザーID（オプション、未記入の場合はtokenから解析）
compress = true               # WebSocket圧縮の有効化（オプション、デフォルトはtrue）
enabled = true                # アカウントの有効化（オプション、デフォルトはtrue）

# アカウント2
[KookAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
bot_id = ""
enabled = true
```

> 旧設定の互換性: 旧の単一アカウントの`[KookAdapter]`設定（tokenを含む）が検出された場合、自動的に`accounts.default`に移行されます。

**各アカウントの設定項目説明:**
- `token`: Kook BotのToken（必須）、[Kook開発者センター](https://developer.kookapp.cn)から取得、形式は`Bot xxx/xxx`
- `bot_id`: BotのユーザーID（オプション）、未記入の場合はtokenから自動解析されます。正確性を確保するため、手動で記入することを推奨します。
- `compress`: WebSocketデータ圧縮の有効化（オプション、デフォルトは`true`）、有効化するとzlibでデータを解凍します。
- `enabled`: アカウントの有効化（オプション、デフォルトはtrue）

**API環境:**
- Kook APIの基本アドレス: `https://www.kookapp.cn/api/v3`
- WebSocketゲートウェイはAPIを介して動的に取得: `POST /gateway/index`

## 標準化対応（4.3.2）

### イベントとアカウント

- **イベント `self.account_id` 注入**: すべてのイベントに発生元のアカウント名が注入され、複数アカウント下では`event.reply()`は自動的に該当アカウントで応答されます。

### Api署名対応

| 動作 | 署名 | 説明 |
|------|------|------|
| get_channel_info | `(guild_id, channel_id)` | 新しい署名guild_idが最初のパラメータに；1つの位置パラメータのみ渡された場合、旧署名（channel_idと見なす）を互換します。 |
| get_channel_member_list | `(guild_id, channel_id)` | 同上互換ルール |
| get_guild_info / get_guild_list | - | dataは`guild_id` / `guild_name`などのフィールドを使用（旧`group_*`フィールドは破壊しないように保持） |

### エラーコード規格

エラーコードはSDKの標準化に従い、Kookプラットフォームの元のエラーコード（401xx/4xxxxなど）は直接retcodeとして使用されません：

| retcode | 説明 |
|---------|------|
| 0 | 成功（成功応答`message`は空文字列） |
| 33001 | ネットワークエラー（リクエスト異常、アカウントAPIインスタンスが初期化されていないなど） |
| 34100 | プラットフォームエラー（Kookが0以外のcodeを返した場合；元の応答は`kook_raw`に保持され、元のcodeは`kook_code`フィールドに別途保存） |
| 10002 | 不支持の動作（`get_guild_member_info` / `get_guild_member_list` / `set_guild_name` / `leave_guild` / `leave_channel`は明示的に返す；未知のAPIエンドポイントは例外を投げず、統一して10002を返す） |

## v5範式更新（4.1.0）

このアダプターはv5範式の対応を完了しました（段階的なアップグレード、API互換性あり）：

- **BaseConverter継承**: 転換器の共通フィールドはフレームワーク`build_base_event`で構築されます。
- **Api DSL**: 標準Apiアクションのマッピング（以下を参照）
- **標準 keyboard 段**: `{"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}}` テキスト+キーボードは自動的にKookカードメッセージ（section + action-group）に組み合わされます；.Keyboard(rows)修飾子は汎用構造を受け入れます。
- **spawn_background 任務の帰属**: 接続タスクはruntime.spawn_backgroundを使用します。
- **フレームワークのソフト依存**: ErisPulse>=2.7.1の実行時検出と警告；起動時にバージョンログを出力します。

### 標準Apiアクション

```python
from ErisPulse import sdk
kook = sdk.adapter.get("kook")

result = await kook.Api.get_self_info()              # GET /users/@me
result = await kook.Api.get_user_info(user_id)       # POST /user/view
result = await kook.Api.get_guild_info(guild_id)     # POST /guild/view（dataにguild_id / guild_nameを使用）
result = await kook.Api.get_guild_list()             # POST /guild/list
result = await kook.Api.get_channel_info(guild_id, channel_id)  # POST /channel/view（新しい署名guild_idが最初のパラメータ）
result = await kook.Api.get_channel_list(guild_id)   # POST /channel/list
await kook.Api.delete_message(msg_id)                # POST /message/delete
result = await kook.Api.Using("main").get_self_info()
```

### ボタン（keyboard）

```python
rows = [[{"label": "選択肢A", "type": "callback", "data": "vote:A"},
         {"label": "公式サイト",  "type": "link",     "data": "https://example.com"}]]
await kook.Send.To("channel", channel_id).Keyboard(rows).Text("選択してください")
# テキストとボタンは自動的にKookカードメッセージ（section + action-group）に組み合わされます。

# ボタンクリックのコールバック（標準フィールド）
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "kook" and event.get("button_data"):
        data = event["button_data"]
```

---

## 支援するメッセージ送信タイプ

すべての送信メソッドはチェーン式構文で実現されます。例えば：
```python
from ErisPulse.Core import adapter
kook = adapter.get("kook")

await kook.Send.To("group", channel_id).Text("Hello World!")
```

支援する送信タイプは以下の通りです：
- `.Text(text: str)`：純粋なテキストメッセージを送信します。
- `.Image(file: bytes | str)`：画像メッセージを送信します。ファイルパス、URL、バイナリデータに対応します。
- `.Video(file: bytes | str)`：ビデオメッセージを送信します。ファイルパス、URL、バイナリデータに対応します。
- `.File(file: bytes | str, filename: str = None)`：ファイルメッセージを送信します。ファイルパス、URL、バイナリデータに対応します。
- `.Voice(file: bytes | str)`：音声メッセージを送信します。ファイルパス、URL、バイナリデータに対応します。
- `.Markdown(text: str)`：KMarkdown形式のメッセージを送信します。
- `.Card(card_data: dict)`：カードメッセージ（CardMessage）を送信します。
- `.MergeForward(nodes, title="合併チャット記録")`：合併転送メッセージを送信します（カードにレンダリング：タイトルheader + 各メッセージごとにsection、KMDエスケープ、≤40ノード）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します。

### 鏈式修飾メソッド（組み合わせ使用可能）

修飾メソッドは`self`を返すため、チェーンで呼び出すことができます。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定したメッセージに返信（引用）します。
- `.At(user_id: str)`：指定したユーザーを@します。複数回呼び出すことで複数のユーザーを@できます。
- `.AtAll()`：全員を@します。

### 鏈式呼び出しの例

```python
# 基本的な送信
await kook.Send.To("group", channel_id).Text("Hello")

# メッセージの返信
await kook.Send.To("group", channel_id).Reply(msg_id).Text("返信メッセージ")

# ユーザーを@する
await kook.Send.To("group", channel_id).At("user_id").Text("こんにちは")

# 複数のユーザーを@する
await kook.Send.To("group", channel_id).At("user1").At("user2").Text("複数のユーザー@")

# 全員を@する
await kook.Send.To("group", channel_id).AtAll().Text("お知らせ")

# 組み合わせ
await kook.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("複合メッセージ")
```

### OneBot12メッセージのサポート

アダプターはOneBot12形式のメッセージ送信をサポートし、プラットフォーム間のメッセージ互換性を確保します：

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)

# 鏈式修飾と組み合わせる
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await kook.Send.To("group", channel_id).Reply(msg_id).Raw_ob12(ob12_msg)

# Raw_ob12でmentionとreplyメッセージセグメントを使用
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
    {"type": "reply", "data": {"message_id": "msg_id"}}
]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

### 追加操作メソッド

メッセージ送信以外にも、Kookアダプターは以下の操作をサポートします：

```python
# メッセージの編集（KMarkdown type=9とCardMessage type=10のみサポート）
await kook.Send.To("group", channel_id).Edit(msg_id, "**更新後の内容**")

# メッセージの撤回
await kook.Send.To("group", channel_id).Recall(msg_id)

# ファイルのアップロード（ファイルURLの取得）
result = await kook.Send.Upload("C:/path/to/file.jpg")
file_url = result["data"]["url"]
```

## 送信メソッドの戻り値

すべての送信メソッドはTaskオブジェクトを返し、直接awaitして送信結果を取得できます。返り値はErisPulseアダプターの標準化された返り値規格に従います：

```python
{
    "status": "ok",           // 実行状態: "ok" または "failed"
    "retcode": 0,             // 返り値コード（0が成功、プラットフォームエラーは34100）
    "data": {...},            // 応答データ
    "message_id": "xxx",      // メッセージID
    "message": "",            // エラー情報（成功応答は空文字列）
    "kook_raw": {...},        // 元の応答データ
    "kook_code": 0            // Kookの元のcode（エラー時は保存）
}
```

### エラーコードの説明

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 33001 | ネットワークエラー（リクエスト異常、アカウントAPIインスタンスが初期化されていないなど） |
| 34100 | プラットフォームエラー（Kookが0以外のcodeを返した場合、元の応答は`kook_raw`に保持され、元のcodeは`kook_code`に保存） |
| 10002 | 不支持の動作（「標準化対応（4.3.2）」のエラーコード規格を参照）

## 特有のイベントタイプ

`platform=="kook"`の検証が必要です。このプラットフォームの特性を使用するには。

### 核心的な違い

1. **チャンネルシステム**: Kookはサーバー（Guild）とチャンネル（Channel）の2層構造を使用し、チャンネルがメッセージの基本的な送信先です。
2. **メッセージタイプ**: Kookはテキスト(1)、画像(2)、ビデオ(3)、ファイル(4)、音声(8)、KMarkdown(9)、カードメッセージ(10)など、多様なメッセージタイプをサポートします。
3. **プライベートメッセージシステム**: Kookはチャンネルメッセージとプライベートメッセージを区別し、異なるAPIエンドポイントを使用します。
4. **メッセージ番号**: KookのWebSocketは`sn`番号を使用してメッセージの順序性を保証し、メッセージの一時保存と乱序の再配置をサポートします。
5. **メッセージの編集と撤回**: KMarkdownとCardMessageの既送信メッセージの編集とメッセージの撤回をサポートします。

### 拡張フィールド

- すべての特有のフィールドは`kook_`前接辞で識別されます。
- 元のデータは`kook_raw`フィールドに保持されます。
- `kook_raw_type`は元のKookメッセージタイプ番号を識別します（例: `1`はテキスト、`255`は通知イベント）。
- イベント`self.account_id`はイベントを発生させたアカウント名です（複数アカウント下では`event.reply()`は該当アカウントで自動的に受理されます）。

### 特殊フィールドの例

```python
# チャンネルテキストメッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ユーザーID",
  "group_id": "チャンネルID",
  "channel_id": "チャンネルID",
  "message_id": "メッセージID",
  "self": {
    "platform": "kook",
    "user_id": "BotID",
    "account_id": "default"
  },
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# 画像付きメッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ユーザーID",
  "group_id": "チャンネルID",
  "channel_id": "チャンネルID",
  "message_id": "メッセージID",
  "kook_raw": {...},
  "kook_raw_type": "2",
  "message": [
    {"type": "image", "data": {"file": "画像URL", "url": "画像URL"}}
  ],
  "alt_message": "画像の内容"
}

# KMarkdownメッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ユーザーID",
  "group_id": "チャンネルID",
  "message_id": "メッセージID",
  "kook_raw": {...},
  "kook_raw_type": "9",
  "message": [
    {"type": "text", "data": {"text": "解析後の純粋なテキスト"}}
  ]
}

# カードメッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ユーザーID",
  "group_id": "チャンネルID",
  "message_id": "メッセージID",
  "kook_raw": {...},
  "kook_raw_type": "10",
  "message": [
    {"type": "json", "data": {"data": "カードのJSON内容"}}
  ]
}

# プライベートメッセージ
{
  "type": "message",
  "detail_type": "private",
  "user_id": "ユーザーID",
  "message_id": "メッセージID",
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "プライベートメッセージの内容"}}
  ]
}
```

### メッセージセグメントタイプ

Kookのメッセージタイプは`type`フィールドに基づいて対応するメッセージセグメントに自動変換されます：

| Kook type | 変換タイプ | 説明 |
|---|---|---|
| 1 | `text` | テキストメッセージ |
| 2 | `image` | 画像メッセージ |
| 3 | `video` | ビデオメッセージ |
| 4 | `file` | ファイルメッセージ |
| 8 | `record` | 音声メッセージ |
| 9 | `text` | KMarkdownメッセージ（純粋なテキスト内容を抽出） |
| 10 | `json` | カードメッセージ（元のJSON） |

メッセージセグメントの構造例：
```json
{
  "type": "image",
  "data": {
    "file": "画像URL",
    "url": "画像URL"
  }
}
```

### Mentionメッセージセグメント

メッセージに@情報が含まれている場合、メッセージセグメントの前に`mention`メッセージセグメントが挿入されます：

```json
{
  "type": "mention",
  "data": {
    "user_id": "@されたユーザーID"
  }
}
```

### mention_allメッセージセグメント

メッセージが全員を@している場合、`mention_all`メッセージセグメントが挿入されます：

```json
{
  "type": "mention_all",
  "data": {}
}
```

## WebSocket接続

### 接続フロー

1. Bot Tokenを使用して`POST /gateway/index`を呼び出し、WebSocketゲートウェイアドレスを取得します。
2. WebSocketゲートウェイに接続します。
3. HELLO（s=1）シグナルを受信し、接続状態を検証します。
4. ハートビートループを開始します（PING、s=2、30秒ごとに1回）、現在のsnを含みます。
5. メッセージイベント（s=0）を受信し、sn番号を使用して順序性を保証します。
6. ハートビート応答PONG（s=3）を受信します。

### シグナルタイプ

| シグナル | s値 | 説明 |
|------|-----|------|
| HELLO | 1 | サーバーの歓迎シグナル、接続成功後に受信します |
| PING | 2 | クライアントのハートビート、30秒ごとに送信し、現在のsnを含みます |
| PONG | 3 | ハートビート応答 |
| RESUME | 4 | 接続の再開シグナル、snを含みセッションを再開します |
| RECONNECT | 5 | サーバーが再接続を要求するシグナル、再びゲートウェイを取得する必要があります |
| RESUME_ACK | 6 | RESUME成功応答 |

### 断線再接続

- 接続が異常断線した場合、アダプターは自動的に再接続を試みます。
- 以前に`sn > 0`があった場合、まずRESUME（s=4）を試みます。
- RESUMEに失敗した場合、snとメッセージキューをリセットし、完全な新接続（HELLOフロー）を行います。
- RECONNECT（s=5）シグナルを受信した場合、状態をクリアして再接続します。

### メッセージ番号メカニズム

Kook WebSocketは`sn`（増加する番号）を使用してメッセージの順序性を保証します：

- 各メッセージイベント（s=0）を受信するたびに、snが増加します。
- 受信したメッセージのsnが連続していない場合、一時保存モードに入ります。
- 一時保存エリアのメッセージはsn順に並べ替えられ、欠落したメッセージが到着した後に順序に従って処理されます。
- 一時保存エリアがクリアされた後は、自動的に一時保存モードを終了します。

## 使用例

### チャンネルメッセージの処理

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

kook = sdk.adapter.get("kook")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await kook.Send.To("group", channel_id).Text("Hello!")
```

### プライベートメッセージの処理

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "private":
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await kook.Send.To("user", user_id).Text(f"あなたが言った: {text}")
```

### 通知イベントの処理（絵文字反応など）

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "added_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"ユーザー {user_id} がメッセージ {msg_id} に絵文字反応を追加しました")

    elif sub_type == "deleted_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"ユーザー {user_id} がメッセージ {msg_id} の絵文字反応を削除しました")
```

### メディアメッセージの送信

```python
# 画像送信（URL）
await kook.Send.To("group", channel_id).Image("https://example.com/image.png")

# 画像送信（バイナリ）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await kook.Send.To("group", channel_id).Image(image_bytes)

# ビデオ送信
await kook.Send.To("group", channel_id).Video("https://example.com/video.mp4")

# ファイル送信
await kook.Send.To("group", channel_id).File("https://example.com/file.pdf", filename="document.pdf")

# 音声送信
await kook.Send.To("group", channel_id).Voice("https://example.com/voice.mp3")
```

### KMarkdownとカードメッセージの送信

```python
# KMarkdown
await kook.Send.To("group", channel_id).Markdown("**太字** *斜体* [リンク](https://example.com)")

# カードメッセージ
card = {
    "type": "card",
    "theme": "primary",
    "size": "lg",
    "modules": [
        {"type": "header", "text": {"type": "plain-text", "content": "タイトル"}},
        {"type": "section", "text": {"type": "kmarkdown", "content": "内容"}}
    ]
}
await kook.Send.To("group", channel_id).Card(card)
```

### メッセージの編集と撤回

```python
# メッセージ送信
result = await kook.Send.To("group", channel_id).Markdown("**元の内容**")
msg_id = result["data"]["msg_id"]

# メッセージの編集（KMarkdownとCardMessageのみサポート）
await kook.Send.To("group", channel_id).Edit(msg_id, "**更新後の内容**")

# メッセージの撤回
await kook.Send.To("group", channel_id).Recall(msg_id)
```

### プライベートメッセージの編集と削除通知の処理

```python
@notice.on_notice()
async def handle_private_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "updated_private_message":
        msg_id = event.get("message_id")
        content = event.get("content")
        print(f"プライベートメッセージが更新されました: {msg_id}, 新しい内容: {content}")

    elif sub_type == "deleted_private_message":
        msg_id = event.get("message_id")
        print(f"プライベートメッセージが削除されました: {msg_id}")
```