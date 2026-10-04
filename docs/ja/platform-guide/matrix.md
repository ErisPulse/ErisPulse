# Matrixプラットフォームの機能ドキュメント

MatrixAdapterは、[Matrixプロトコル](https://spec.matrix.org/)に基づいて構築されたアダプターで、Matrixプロトコルのすべてのコア機能モジュールを統合し、統一されたイベント処理とメッセージ操作のインターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.2.0
- メンテナー: ErisPulse

## 基本情報

- プラットフォーム概要: Matrixは、プライベートチャット、グループチャットなど、さまざまなシナリオをサポートするオープンな分散型通信プロトコルです。
- アダプター名: MatrixAdapter
- 複数アカウントのサポート: 複数のMatrixアカウントを同時に設定可能
- 接続方式: Long Polling（Matrix Sync API `/sync`を使用）
- 認証方式: access_tokenまたはuser_id + passwordを使用してトークンを取得
- チェーン修飾のサポート: `.Reply()`、`.At()`、`.AtAll()`などのチェーン修飾メソッドをサポート
- OneBot12の互換性: OneBot12形式のメッセージ送信をサポート

## 設定説明

MatrixAdapterは複数アカウントの設定をサポートし、各アカウントは独自のhomeserverと認証情報を設定します。

```toml
# config.toml
# アカウント1
[Matrix_Adapter.accounts.default]
homeserver = "https://matrix.org"          # Matrixサーバーのアドレス（必須）
access_token = "YOUR_ACCESS_TOKEN"          # アクセストークン（user_id+passwordと二択）
user_id = ""                                # MatrixユーザーID（例: @bot:matrix.org）
password = ""                               # Matrixユーザーのパスワード
auto_accept_invites = true                  # ルーム招待を自動的に受け入れるかどうか（オプション、デフォルトはtrue）
enabled = true                              # 有効化するかどうか（オプション、デフォルトはtrue）

# アカウント2
[Matrix_Adapter.accounts.bot2]
homeserver = "https://matrix.example.com"
access_token = "ANOTHER_TOKEN"
enabled = true
```

> 旧形式の設定との互換性: 旧形式の単一アカウントの`[Matrix_Adapter]`設定（access_tokenを含む）が検出された場合、自動的に`accounts.default`に移行されます。

**各アカウントの設定項目の説明:**
- `homeserver`: Matrixサーバーのアドレス（必須）、デフォルトは`https://matrix.org`
- `access_token`: アクセストークン、Matrixクライアントから取得できます。既にトークンがあれば、そのまま記入します
- `user_id`: MatrixユーザーID（例: `@bot:matrix.org`）、`password`と併せてログインに使用
- `password`: Matrixユーザーのパスワード、自動ログイン時にaccess_tokenを取得するために使用
- `auto_accept_invites`: ルーム招待を自動的に受け入れるかどうか、デフォルトは`true`
- `enabled`: アカウントを有効化するかどうか（オプション、デフォルトはtrue）

**認証方式:**
- 方法1（推奨）: `access_token`を直接提供
- 方法2: `user_id`と`password`を提供し、アダプターが自動的にログインインターフェースを呼び出してトークンを取得

## v5 ファンタム更新（4.2.0）

- **BaseConverterの継承**: コンバーターの共通フィールドはフレームワークのbuild_base_eventによって構築されます
- **Api DSL**: get_self_info/get_user_info/get_group_info/get_group_list/get_group_member_list/leave_group/delete_message(redact) + メタアクション
- **メッセージイベントの追加: message_id**（event_id）; メッセージ登録表はdelete_messageをサポート
- **spawn_background タスクの所属**: 同期/ハートビートタスクはruntime.spawn_backgroundを使用
- **フレームワークのソフト依存**: ErisPulse>=2.7.1の実行時検出と警告を提示; 起動時にバージョンログを出力
- Matrixには元々ボタン機能がないため、標準のkeyboardセグメントはエラーを出さずに優雅に無視されます

## 端末間暗号化（4.3.0）

4.3.0から、アダプターは暗号化ルームの端末間暗号化（matrix-nio[e2e] / vodozemacに基づく）を原生でサポートします：

```toml
[Matrix_Adapter.accounts.default]
user_id = "@bot:matrix.org"
password = "YOUR_PASSWORD"
encryption_enabled = true       # 有効化（デフォルトはfalse、既存の展開には影響しません）
trust_all_devices = true        # 未検証デバイスを自動的に信頼（デフォルト、falseは厳密モード）
```

- 暗号化ルームのメッセージ送受信は自動的に暗号化/復号化され、メディアは`m.file.encrypted`で暗号化されます
- `device_id`は自動的に解析され、永続化されます。セッションは`store_path`（デフォルトは`data/matrix/<アカウント名>`、**削除しないでください**、削除すると履歴メッセージの復号化ができません）
- イベントMixinに`event.is_encrypted()`が追加されました。メディアセグメントには`matrix_encrypted_file`（JWK）が含まれ、`MatrixAdapter.decrypt_media()`で復号化できます
- クロスシグネチャとサーバー側の鍵バックアップはサポートしていません。Python >= 3.10が必要です
- matrix-nioが有効化されていない場合、自動的に平文モードに降格されます

詳細な説明は[アダプターのREADME](https://github.com/ErisPulse/ErisPulse-MatrixAdapter)をご覧ください。

### 標準APIアクションの例

```python
from ErisPulse import sdk
matrix = sdk.adapter.get("matrix")
result = await matrix.Api.get_self_info()            # /account/whoami
result = await matrix.Api.get_group_info(room_id)    # m.room.name
result = await matrix.Api.get_group_list()           # /joined_rooms
await matrix.Api.delete_message(event_id)            # redact（登録表にroom_idを補完）
```

---

### 対応しているプラットフォームの機能

- **イベント**: メッセージ（m.room.message：テキスト/画像/ファイル/音声/ビデオ/返信/編集）、メンバーの追加/削除（m.room.member）、ルーム名の変更などのステータスイベント
- **セッション**: プライベートチャット（DMルームの自動検出）/グループ（ルーム）；送信はText/Image/File/Voice/Video/Markdown/Raw_ob12をサポート
- **API**: whoami/profile/joined_rooms/ルームステータス/メンバー一覧/leave/redact（上記のApi DSLを参照）

---

## 送信可能なメッセージの種類

すべての送信メソッドはチェーン構文で実現されます。例えば：
```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

サポートされる送信タイプは以下の通りです：
- `.Text(text: str)`：テキストメッセージを送信します。
- `.Image(file: bytes | str)`：画像メッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータをサポートします。
- `.Voice(file: bytes | str)`：音声メッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータをサポートします。
- `.Video(file: bytes | str)`：ビデオメッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータをサポートします。
- `.File(file: bytes | str, filename: str = "")`：ファイルメッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータをサポートします。
- `.Notice(text: str)`：通知メッセージ（Matrixのm.noticeタイプ）を送信します。
- `.Html(html: str, fallback: str = "")`：HTML形式のメッセージを送信します。富文本コンテンツをサポートします。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します。

### チェーン修飾メソッド（組み合わせて使用可能）

チェーン修飾メソッドは`self`を返し、チェーン呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定したメッセージに返信します（Matrixの`m.in_reply_to`関係を使用）。
- `.At(user_id: str)`：指定したユーザーに@を付けます（Matrixの`m.mentions`フィールドを使用）。
- `.AtAll()`：ルーム内の全員に@を付けます（Matrixの`@room`メンションを使用）。

### チェーン呼び出しの例

```python
# 基本的な送信
await matrix.Send.To("user", dm_room_id).Text("Hello")

# メッセージへの返信
await matrix.Send.To("group", room_id).Reply("$event_id").Text("返信メッセージ")

# @ユーザー
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("こんにちは")

# @全員
await matrix.Send.To("group", room_id).AtAll().Text("お知らせ")

# 組み合わせ: 返信 + @
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("複合メッセージ")

# HTMLメッセージの送信
await matrix.Send.To("group", room_id).Html("<h1>タイトル</h1><p>内容</p>", fallback="タイトル\n内容")

# 通知メッセージの送信
await matrix.Send.To("group", room_id).Notice("システム通知")
```

### OneBot12メッセージのサポート

アダプターはOneBot12形式のメッセージ送信をサポートし、プラットフォーム間のメッセージ互換性を確保します：

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# チェーン修飾の組み合わせ
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# 複雑なメッセージ
ob12_msg = [
    {"type": "text", "data": {"text": "この画像を見てください："}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "いいでしょ？"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)
```

## 送信メソッドの戻り値

すべての送信メソッドはTaskオブジェクトを返し、awaitで送信結果を取得できます。返り値はErisPulseアダプターの標準化された返り値規格に従います：

```python
{
    "status": "ok",           // 実行ステータス: "ok" または "failed"
    "retcode": 0,             // 返り値コード
    "data": {...},            // 応答データ
    "message_id": "$event_id", // MatrixイベントID
    "message": "",            // エラーメッセージ
    "matrix_raw": {...}       // 元の応答データ
}
```

### エラーコードの説明

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 32000 | リクエストのタイムアウトまたはメディアのアップロードに失敗 |
| 33000 | APIの呼び出しに異常が発生 |
| 34000 | APIが予期しない形式または業務エラーを返した |

## 特有のイベントタイプ

`platform=="matrix"`の検出が必要です。このプラットフォームの特性を使用するには

### 核心的な相違点

1. **分散型アーキテクチャ**: Matrixは分散型の通信プロトコルで、ユーザーIDのフォーマットは`@user:server.domain`、ルームIDのフォーマットは`!room_id:server.domain`です
2. **ルーム概念**: Matrixはプライベートチャットとグループチャットを区別せず、すべての会話は「ルーム」です。アダプターはDM（Direct Message）アカウントデータを自動的に検出してプライベートチャットルームを識別します
3. **Long Polling同期**: `/sync` APIを使用して長時間ポーリングで新規イベントを取得し、WebSocketではなく使用します
4. **MXC URI**: メディアファイルは`mxc://server.domain/media_id`形式で参照されます
5. **HTML富文本**: `formatted_body`を使用してHTML形式のメッセージを送信できます
6. **絵文字の反応**: 伝統的な返信メッセージとは異なり、メッセージレベルの絵文字反応（Reaction）をサポートします
7. **メッセージの編集**: `m.replace`関係を使用して送信済みのメッセージを編集できます
8. **メッセージの撤回**: `m.room.redaction`を使用してメッセージを撤回/削除できます

### 拡張フィールド

- すべての特有のフィールドは`matrix_`接頭辞で識別されます
- 元のデータは`matrix_raw`フィールドに保持されます
- `matrix_raw_type`は元のMatrixイベントタイプを識別します（例: `m.room.message`、`m.room.member`）

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

# プライベートチャットメッセージ
{
  "type": "message",
  "detail_type": "private",
  "user_id": "@user:matrix.org",
  "matrix_room_id": "!dm_room_id:matrix.org"
}

# 絵文字反応
{
  "type": "notice",
  "detail_type": "matrix_reaction",
  "matrix_reaction_event_id": "$reacted_msg_id",
  "matrix_reaction_key": "👍"
}

# メッセージの撤回
{
  "type": "notice",
  "detail_type": "matrix_redaction",
  "matrix_redacted_event_id": "$deleted_msg_id"
}

# メッセージの編集
{
  "type": "message",
  "detail_type": "group",
  "matrix_edit": true,
  "matrix_original_event_id": "$original_event_id"
}

# スレッドメッセージ
{
  "type": "message",
  "detail_type": "group",
  "thread_id": "$thread_root_id"
}
```

### メッセージセグメントの種類

Matrixメッセージは`msgtype`に基づいて対応するメッセージセグメントに自動的に変換されます：

| msgtype | 変換タイプ | 説明 |
|---|---|---|
| m.text | `text` | テキストメッセージ |
| m.notice | `text` | 通知メッセージ |
| m.emote | `text` | 動作メッセージ |
| m.image | `image` | 画像メッセージ |
| m.audio | `voice` | 音声メッセージ |
| m.video | `video` | ビデオメッセージ |
| m.file | `file` | ファイルメッセージ |
| m.location | `location` | 位置メッセージ |

メッセージセグメントの構造例：

```json
// テキストメッセージ（HTML付き）
{
  "type": "text",
  "data": {
    "text": "純粋なテキストの内容",
    "html": "<b>HTMLの内容</b>"
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

### Event Mixinメソッド

MatrixAdapterは以下のイベントミックスインメソッドを登録し、イベント処理で直接呼び出すことができます：

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_room_id()` | `str` | ルームIDを取得します |
| `get_matrix_event_type()` | `str` | 元のMatrixイベントタイプを取得します |
| `get_matrix_sender()` | `str` | 元の送信者のIDを取得します |
| `get_reaction_key()` | `str` | 反応した絵文字を取得します |
| `is_edited()` | `bool` | メッセージが編集されたかどうかを判断します |
| `is_notice()` | `bool` | メッセージがm.noticeタイプかどうかを判断します |

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
```

## Sync API接続

### 同期の流れ

1. access_tokenまたはuser_id + passwordを使用して認証します
2. `/_matrix/client/v3/account/whoami`を呼び出してbot_user_idを取得します
3. connectメタイベントを発行します
4. 初期同期を実行します（`/_matrix/client/v3/sync?timeout=0`）で`next_batch`トークンを取得します
5. DMルームを検出します（`/_matrix/client/v3/user/{user_id}/account_data/m.direct`）
6. Long Polling同期ループを開始します（`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`）
7. 各同期で返された新しいイベントを処理し、変換して発行します

### ハートビートメカニズム

- アダプターは30秒ごとに`heartbeat`メタイベントを発行します
- 接続成功時には`connect`メタイベントを発行します
- 閉じる時には`disconnect`メタイベントを発行します

### ルーム招待

- ルーム招待（`invite`ステータスのルーム）を受け取った場合、`auto_accept_invites`設定が`true`（デフォルト）の場合、アダプターは自動的にルームに参加します
- ルームに参加するには`/_matrix/client/v3/join/{room_id}`インターフェースを呼び出します

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

### 絵文字反応の処理

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
        # 絵文字反応を処理...
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
await matrix.Send.To("group", room_id).File("/path/to/document.pdf", filename="文書.pdf")
```

### メッセージの編集の処理

```python
@message.on_message()
async def handle_edited_message(event):
    if event.get("platform") != "matrix":
        return

    if event.is_edited():
        original_id = event.get("matrix_original_event_id")
        # 編集されたメッセージを処理...
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
        print(f"ユーザー {nickname} ({user_id}) がルームに参加しました")

    elif detail_type == "group_member_decrease":
        user_id = event.get("user_id")
        operator_id = event.get("operator_id")
        print(f"ユーザー {user_id} が削除され、操作者: {operator_id}")
```