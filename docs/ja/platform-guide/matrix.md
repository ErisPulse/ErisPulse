# Matrixプラットフォームの特徴ドキュメント

MatrixAdapter は [Matrixプロトコル](https://spec.matrix.org/) に基づいて構築されたアダプターであり、Matrixプロトコルのすべてのコア機能モジュールを統合し、一貫したイベント処理およびメッセージ操作インターフェースを提供します。

---

[**English**](docs/en/quick-start.md) | [**日本語**](docs/ja/quick-start.md) | [**简体中文**](docs/ja/quick-start.md)

## ドキュメント情報

- 対応モジュールバージョン: 4.1.0
- 維持者: ErisPulse

[クイックスタートガイド](docs/ja/quick-start.md) | [詳細なインストール手順](docs/ja/installation.md) | [APIリファレンス](docs/ja/api-reference.md) | [FAQ](docs/ja/faq.md)

## 基本情報

- プラットフォーム紹介：Matrixは、プライベートチャット、グループチャットなど多様なシナリオをサポートするオープンな分散型通信プロトコルです
- アダプタ名：MatrixAdapter
- 複数アカウント対応：複数の Matrix アカウントを同時に設定できます
- 接続方法：Long Polling（Matrix Sync API `/sync` を使用）
- 認証方法：access_token または user_id + password を使用してトークンを取得
- チェーン修飾子対応：`.Reply()`、`.At()`、`.AtAll()` などのチェーン修飾子メソッドをサポート
- OneBot12互換：OneBot12形式のメッセージ送信をサポート

[**English**](docs/ja/quick-start.md)

## 設定の説明

MatrixAdapter は、各アカウントごとに homeserver と認証情報を個別に設定できる多アカウント設定をサポートしています。

```toml
# config.toml
# アカウント1
[Matrix_Adapter.accounts.default]
homeserver = "https://matrix.org"          # Matrixサーバーのアドレス（必須）
access_token = "YOUR_ACCESS_TOKEN"          # アクセストークン（user_id + password のどちらか一方）
user_id = ""                                # MatrixのユーザーID（例: @bot:matrix.org）
password = ""                               # Matrixのユーザーのパスワード
auto_accept_invites = true                  # ルーム招待を自動的に受け入れるかどうか（オプション、デフォルトはtrue）
enabled = true                              # アカウントを有効にするかどうか（オプション、デフォルトはtrue）

# アカウント2
[Matrix_Adapter.accounts.bot2]
homeserver = "https://matrix.example.com"
access_token = "ANOTHER_TOKEN"
enabled = true
```

> 旧設定の互換性：`access_token` を含む旧形式の単一アカウントの `[Matrix_Adapter]` 設定が検出された場合、自動的に `accounts.default` に移行されます。

**各アカウントの設定項目の説明：**
- `homeserver`：Matrixサーバーのアドレス（必須）、デフォルトは `https://matrix.org`
- `access_token`：Matrixクライアントから取得できるアクセストークン。既にトークンがある場合は、そのまま記入してください
- `user_id`：MatrixのユーザーID（例: `@bot:matrix.org`）、`password` と併用してログインします
- `password`：Matrixのユーザーのパスワード、自動ログイン時に access_token を取得するために使用します
- `auto_accept_invites`：ルーム招待を自動的に受け入れるかどうか、デフォルトは `true`
- `enabled`：このアカウントを有効にするかどうか（オプション、デフォルトはtrue）

**認証方法：**
- 方法1（推奨）：`access_token` を直接提供する
- 方法2：`user_id` と `password` を提供し、アダプタが自動的にログインAPIを呼び出してトークンを取得する

[**English**](docs/ja/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## 支持的消息送信タイプ

すべての送信メソッドは、チェーン式構文で実装されています。例：

```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

サポートされている送信タイプは以下の通りです：

- `.Text(text: str)`：純粋なテキストメッセージを送信します。
- `.Image(file: bytes | str)`：画像メッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータをサポートします。
- `.Voice(file: bytes | str)`：音声メッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータをサポートします。
- `.Video(file: bytes | str)`：ビデオメッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータをサポートします。
- `.File(file: bytes | str, filename: str = "")`：ファイルメッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータをサポートします。
- `.Notice(text: str)`：通知メッセージを送信します（Matrixのm.noticeタイプ）。
- `.Html(html: str, fallback: str = "")`：HTML形式のメッセージを送信します。富文本コンテンツをサポートします。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します。

### チェーン式修飾メソッド（組み合わせて使用可能）

チェーン式修飾メソッドは`self`を返し、チェーン式呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定されたメッセージに返信します（Matrixの`m.in_reply_to`関係を使用）。
- `.At(user_id: str)`：指定されたユーザーを@します（Matrixの`m.mentions`フィールドで実現）。
- `.AtAll()`：部屋内の全員に@します（Matrixの`@room`メンションで実現）。

### チェーン式呼び出しの例

```python
# 基本的な送信
await matrix.Send.To("user", dm_room_id).Text("Hello")

# メッセージに返信
await matrix.Send.To("group", room_id).Reply("$event_id").Text("返信メッセージ")

# ユーザーを@する
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("こんにちは")

# 全員に@する
await matrix.Send.To("group", room_id).AtAll().Text("公告通知")

# 組み合わせ：返信 + @
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("複合メッセージ")

# HTMLメッセージの送信
await matrix.Send.To("group", room_id).Html("<h1>タイトル</h1><p>内容</p>", fallback="タイトル\n内容")

# 通知メッセージの送信
await matrix.Send.To("group", room_id).Notice("システム通知")
```

### OneBot12メッセージのサポート

アダプタはOneBot12形式のメッセージを送信する機能をサポートしており、プラットフォーム間のメッセージ互換性を確保します：

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# チェーン式修飾と併用
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# 複雑なメッセージ
ob12_msg = [
    {"type": "text", "data": {"text": "この画像を見て："}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "いいでしょ？"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、これに直接 await を使用して送信結果を取得できます。返り値は ErisPulse アダプタの標準化された返り値規格に従います：

```python
{
    "status": "ok",           // 実行ステータス: "ok" または "failed"
    "retcode": 0,             // 戻りコード
    "data": {...},            // 応答データ
    "message_id": "$event_id", // Matrix イベントID
    "message": "",            // エラーメッセージ
    "matrix_raw": {...}       // 元の応答データ
}
```

### 戻りコードの説明

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 32000 | リクエストがタイムアウトまたはメディアのアップロードに失敗した |
| 33000 | APIの呼び出しに異常が発生した |
| 34000 | APIが予期しない形式または業務エラーを返した |

## 特有イベントタイプ

このプラットフォームの機能を使用するには、`platform=="matrix"` の検証が必要です。

### 核心的な違い

1. **分散型アーキテクチャ**：Matrix は分散型の通信プロトコルであり、ユーザーIDの形式は `@user:server.domain`、ルームIDの形式は `!room_id:server.domain` です。
2. **ルーム概念**：Matrix はグループチャットとプライベートチャットを区別せず、すべての会話は「ルーム」として扱われます。アダプターはDM（Direct Message）アカウントデータを用いて自動的にプライベートチャットルームを識別します。
3. **Long Polling 同期**：WebSocket ではなく、`/sync` API を用いた長時間ポーリングで新規イベントを取得します。
4. **MXC URI**：メディアファイルは `mxc://server.domain/media_id` 形式で参照されます。
5. **HTML フォーマット**：`formatted_body` を用いて HTML 形式のメッセージを送信できます。
6. **絵文字応答**：従来の返信メッセージとは異なり、メッセージレベルでの絵文字応答（Reaction）がサポートされています。
7. **メッセージ編集**：`m.replace` 関係を用いて送信済みメッセージの編集が可能です。
8. **メッセージ撤回**：`m.room.redaction` を用いてメッセージの撤回/削除が可能です。

### 拡張フィールド

- すべての独自フィールドは `matrix_` という接頭辞で識別されます。
- 元のデータは `matrix_raw` フィールドに保持されます。
- `matrix_raw_type` は元のMatrixイベントタイプ（例：`m.room.message`、`m.room.member`）を識別します。

### 特殊フィールドの例

```python
# グループメッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "@user:matrix.org",
  "group_id": "!room_id:matrix.org",
  "matrix_room_id": "!room_id:matrix.org"
}

# プライベートメッセージ
{
  "type": "message",
  "detail_type": "private",
  "user_id": "@user:matrix.org",
  "matrix_room_id": "!dm_room_id:matrix.org"
}

# 絵文字応答
{
  "type": "notice",
  "detail_type": "matrix_reaction",
  "matrix_reaction_event_id": "$reacted_msg_id",
  "matrix_reaction_key": "👍"
}

# メッセージ撤回
{
  "type": "notice",
  "detail_type": "matrix_redaction",
  "matrix_redacted_event_id": "$deleted_msg_id"
}

# メッセージ編集
{
  "type": "message",
  "detail_type": "group",
  "matrix_edit": True,
  "matrix_original_event_id": "$original_event_id"
}

# スレッドメッセージ
{
  "type": "message",
  "detail_type": "group",
  "thread_id": "$thread_root_id"
}
```

### メッセージセグメントタイプ

Matrixメッセージは `msgtype` に基づいて対応するメッセージセグメントに自動的に変換されます：

| msgtype | 変換タイプ | 説明 |
|---|---|---|
| m.text | `text` | テキストメッセージ |
| m.notice | `text` | 通知メッセージ |
| m.emote | `text` | 動作メッセージ |
| m.image | `image` | 画像メッセージ |
| m.audio | `voice` | 音声メッセージ |
| m.video | `video` | 動画メッセージ |
| m.file | `file` | ファイルメッセージ |
| m.location | `location` | 位置メッセージ |

メッセージセグメントの構造例：

```json
// テキストメッセージ（HTML付き）
{
  "type": "text",
  "data": {
    "text": "純粋なテキスト内容",
    "html": "<b>HTMLコンテンツ</b>"
  }
}

// 画像メッセージ
{
  "type": "image",
  "data": {
    "url": "mxc://matrix.org/abc123",
    "filename": "photo.png",
    "matrix_mxc": "mxc://matrix.org/abc123",
    "info": {
      "mimetype": "image/png",
      "w": 800,
      "h": 600,
      "size": 123456
    }
  }
}

// 位置メッセージ
{
  "type": "location",
  "data": {
    "latitude": 0.0,
    "longitude": 0.0,
    "matrix_geo_uri": "geo:39.9,116.4",
    "text": "北京市"
  }
}
```

### Event Mixin メソッド

MatrixAdapter は以下のイベントミキシンメソッドを登録しており、イベント処理中で直接呼び出すことができます：

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_room_id()` | `str` | ルームIDを取得します |
| `get_matrix_event_type()` | `str` | 元のMatrixイベントタイプを取得します |
| `get_matrix_sender()` | `str` | 元の送信者IDを取得します |
| `get_reaction_key()` | `str` | 応答用の絵文字を取得します |
| `is_edited()` | `bool` | メッセージが編集されたものかどうかを判定します |
| `is_notice()` | `bool` | メッセージが m.notice タイプかどうかを判定します |

```python
@message.on_message()
async def handle_message(event):
    if event.get("platform") != "matrix":
        return

    room_id = event.get_room_id()
    event_type = event.get_matrix_event_type()
    sender = event.get_matrix_sender()
    is_edited = event.is_edited()
    is_notice = event.is_notice()

## Sync API 接続

### 同期フロー

1. access_token または user_id + password を使用して認証を行う
2. `/_matrix/client/v3/account/whoami` を呼び出し、bot_user_id を取得する
3. connect 元イベントを発行する
4. 初期同期を実行する（`/_matrix/client/v3/sync?timeout=0`）`next_batch` token を取得する
5. DM ルームを検出する（`/_matrix/client/v3/user/{user_id}/account_data/m.direct`）
6. Long Polling 同期ループを開始する（`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`）
7. 各同期で返された新しいイベントを処理し、発行する

### ハートビートメカニズム

- アダプターは 30 秒ごとに `heartbeat` 元イベントを発行する
- 接続が成功した場合に `connect` 元イベントを発行する
- 閉じる際に `disconnect` 元イベントを発行する

### ルーム招待

- ルーム招待（`invite` 状態のルーム）を受け取った場合、`auto_accept_invites` 設定が `true`（デフォルト）の場合、アダプターは自動的にルームに参加する
- ルームに参加する際には `/_matrix/client/v3/join/{room_id}` エンドポイントを呼び出す

[**English**](docs/ja/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## 使用例

### グループメッセージの処理

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

matrix = sdk.adapter.get("matrix")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "matrix":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    room_id = event.get("group_id")

    if text == "hello":
        await matrix.Send.To("group", room_id).Reply(
            event.get("message_id")
        ).Text("Hello!")
```

### 表情応酬の処理

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_reaction(event):
    if event.get("platform") != "matrix":
        return

    if event.get("detail_type") == "matrix_reaction":
        reaction_key = event.get("matrix_reaction_key")
        reacted_event_id = event.get("matrix_reaction_event_id")
        room_id = event.get_room_id()
        # 表情応酬の処理...
```

### メディアメッセージの送信

```python
# 画像の送信（URL）
await matrix.Send.To("group", room_id).Image("https://example.com/image.png")

# 画像の送信（MXC URI）
await matrix.Send.To("group", room_id).Image("mxc://matrix.org/abc123")

# 画像の送信（バイナリデータ）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await matrix.Send.To("group", room_id).Image(image_bytes)

# 画像の送信（ローカルファイルパス）
await matrix.Send.To("group", room_id).Image("/path/to/image.png")

# ファイルの送信（ファイル名付き）
await matrix.Send.To("group", room_id).File("/path/to/document.pdf", filename="ドキュメント.pdf")
```

### メッセージ編集の処理

```python
@message.on_message()
async def handle_edited_message(event):
    if event.get("platform") != "matrix":
        return

    if event.is_edited():
        original_id = event.get("matrix_original_event_id")
        # 編集されたメッセージの処理...
```

### メンバー変更の監視

```python
@notice.on_notice()
async def handle_member_change(event):
    if event.get("platform") != "matrix":
        return

    detail_type = event.get("detail_type")

    if detail_type == "group_member_increase":
        user_id = event.get("user_id")
        nickname = event.get("user_nickname")
        print(f"ユーザー {nickname} ({user_id}) が部屋に参加しました")

    elif detail_type == "group_member_decrease":
        user_id = event.get("user_id")
        operator_id = event.get("operator_id")
        print(f"ユーザー {user_id} が削除されました。操作者: {operator_id}")