# 花楓カフェ（RockyChat）プラットフォームの機能ドキュメント

IdeauraAdapter は、花楓カフェ（RockyChat）プラットフォームの API を基に構築されたアダプターであり、すべてのプラットフォーム機能モジュールを統合し、一貫したイベント処理とメッセージ操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュール: ErisPulse-Ideaura
- 対応モジュールバージョン: 4.0.1
- 管理者: ErisPulse

## 基本情報

- プラットフォーム紹介：花楓コーヒーショップ（RockyChat）は、リアルタイム通信プラットフォームです。
- アダプタ名：IdeauraAdapter
- マルチアカウント対応：Bot Token による複数アカウントの設定が可能です。
- チェーン修飾子対応：`.At()`、`.AtAll()`、`.Reply()`、`.Command()` などのチェーン修飾メソッドに対応しています。
- OneBot12互換：OneBot12形式のメッセージ送信が可能です。

## 支援されるメッセージ送信タイプ

すべての送信メソッドは、チェーン式構文で実装されています。たとえば：

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

サポートされている送信タイプは以下の通りです：

- `.Text(text: str)`：純粋なテキストメッセージを送信します。
- `.Image(file, filename: str = None)`：画像メッセージを送信します。bytes/URL/ローカルパスをサポートします。
- `.Video(file, filename: str = None)`：動画メッセージを送信します。bytes/URL/ローカルパスをサポートします。
- `.File(file, filename: str = None)`：ファイルメッセージを送信します。bytes/URL/ローカルパスをサポートします。
- `.Voice(file, filename: str = None)`：音声メッセージを送信します（ファイルとして送信します）。
- `.Face(face_id: str)`：絵文字を送信します（emojiとして純粋なテキスト形式で送信します）。
- `.Markdown(text: str)`：Markdown形式のメッセージを送信します。
- `.Html(html: str)`：HTML形式のメッセージを送信します。
- `.Edit(message_id: str, text: str, content_type: str = "text")`：既存のメッセージを編集します。
- `.Recall(message_id: str)`：メッセージを撤回します。

### チェーン式修飾メソッド（複数使用可能）

チェーン式修飾メソッドは `self` を返し、チェーン式で呼び出すことができます。最終的な送信メソッドの前に呼び出す必要があります：

- `.At(user_id: str, name: str = None)`：指定ユーザーを@します。
- `.AtAll()`：全員を@します。
- `.Reply(message_id: str)`：指定されたメッセージに返信します。
- `.Command(command_id: str)`：Botのコマンドをトリガーします。送信メソッドと併用して使用します（メッセージを指定されたコマンドとして送信します）。

### チェーン式呼び出しの例

```python
# 基本的な送信
await ideaura.Send.To("user", user_id).Text("Hello")

# Botのコマンドをトリガー
await ideaura.Send.To("group", "chatroom").Command("550e8400-e29b-41d4-a716-446655440000").Text("/weather 北京")

# ユーザーを@する
await ideaura.Send.To("group", "chatroom").At("456").Text("@李四 你好")

# 複数ユーザーを@する
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@多人")

# メッセージに返信する
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("返信メッセージ")

# 返信 + @
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("返信して@する")
```

### 異なる送信先への送信

```python
# チャットルームに送信
await ideaura.Send.To("group", "chatroom").Text("チャットルームメッセージ")

# トピックに送信
await ideaura.Send.To("group", "topic_id").Text("トピックメッセージ")

# プライベートチャットメッセージを送信
await ideaura.Send.To("user", "user_id").Text("プライベートチャットメッセージ")
```

### OneBot12メッセージのサポート

アダプターはOneBot12形式のメッセージを送信する機能をサポートしており、これにより異なるプラットフォーム間でのメッセージ互換性が確保されます：

- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します。

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# チェーン式修飾を併用
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、これを直接 await することで送信結果を取得できます。返り値は ErisPulse アダプタの標準化された返り値規格に従います。

```python
{
    "status": "ok",           // 実行状態
    "retcode": 0,             // 戻りコード
    "data": {...},            // 応答データ
    "self": {...},            // 自身の情報（user_id を含む）
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "ideaura_raw": {...}      // 元の応答データ
}
```

## 特有イベントタイプ

このプラットフォームの機能を使用するには、`platform=="ideaura"` の検出が必要です。

### 核心的な差異点

1. 特有のイベントタイプ:
    - メッセージ編集: ideaura_message_edit
    - メッセージ撤回: ideaura_message_recall
    - メッセージ転送: ideaura_message_forward
    - メッセージ既読: ideaura_message_read
    - 友達リクエスト拒否: ideaura_friend_rejected
    - 友達オンライン: ideaura_friend_online
    - 友達オフライン: ideaura_friend_offline
    - ユーザー状態変更: ideaura_user_status_change
    - 転送メッセージセグメント: ideaura_forwarded
    - 編集マークセグメント: ideaura_edited
    - Markdownメッセージセグメント: ideaura_markdown
    - HTMLメッセージセグメント: ideaura_html
    - Botコマンドメッセージセグメント: ideaura_command
2. 拡張フィールド:
    - すべての特有フィールドは `ideaura_` で始まるプレフィックスを付与
    - 元のデータは `ideaura_raw` フィールドに保持
    - `self.user_id` は現在のアカウントのユーザーIDを表す

### メッセージ編集イベント

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_edit",
  "platform": "ideaura",
  "message_id": "メッセージID",
  "user_id": "編集者ID",
  "ideaura_new_content": "編集後の内容",
  "ideaura_updated_message": { ... },
  "ideaura_source_type": "chatroom/topic/private"
}
```

### メッセージ撤回イベント

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_recall",
  "platform": "ideaura",
  "message_id": "撤回されたメッセージID",
  "user_id": "撤回者ID",
  "group_id": "chatroom",
  "ideaura_source_type": "chatroom",
  "ideaura_recall_time": "撤回時間",
  "ideaura_is_self": false
}
```

### メッセージ転送イベント

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_forward",
  "platform": "ideaura",
  "message_id": "元のメッセージID",
  "user_id": "転送者ID",
  "ideaura_forward_to": "目標トピックID",
  "ideaura_original_message_id": "元のメッセージID",
  "ideaura_forwarded_message_id": "転送後の新しいメッセージID"
}
```

### メッセージ既読イベント

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_read",
  "platform": "ideaura",
  "message_id": "メッセージID",
  "ideaura_reader_id": "既読者ID",
  "ideaura_reader_name": "既読者のニックネーム"
}
```

### 友達オンラインイベント

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_online",
  "platform": "ideaura",
  "user_id": "友達ID",
  "user_nickname": "友達のニックネーム",
  "ideaura_friend_avatar": "アイコンURL",
  "ideaura_presence_status": "online"
}
```

### 友達オフラインイベント

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_offline",
  "platform": "ideaura",
  "user_id": "友達ID",
  "ideaura_presence_status": "offline"
}
```

### ユーザー状態変更イベント

```python
{
  "type": "notice",
  "detail_type": "ideaura_user_status_change",
  "platform": "ideaura",
  "user_id": "ユーザーID",
  "ideaura_status": "新しいステータス",
  "ideaura_previous_status": "前のステータス"
}
```

### 友達リクエストイベント

```python
{
  "type": "request",
  "detail_type": "friend",
  "platform": "ideaura",
  "user_id": "リクエスト者ID",
  "user_nickname": "リクエスト者のニックネーム",
  "ideaura_request_id": "リクエストID",
  "ideaura_message": "認証メッセージ"
}
```

### 友達拒否イベント

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_rejected",
  "platform": "ideaura",
  "user_id": "拒否者ID",
  "user_nickname": "拒否者のニックネーム",
  "ideaura_request_id": "リクエストID",
  "ideaura_requester_id": "リクエスト発起者ID",
  "ideaura_requester_name": "リクエスト発起者のニックネーム"
}
```

### 転送メッセージセグメント (ideaura_forwarded)

転送メッセージを受け取った場合、メッセージセグメントのタイプは `ideaura_forwarded` です:

```json
{
  "type": "ideaura_forwarded",
  "data": {
    "forward_source_id": "1001",
    "original_message_id": "1001"
  }
}
```

| フィールド | 型 | 説明 |
|------|------|------|
| `forward_source_id` | string | 転送元メッセージID |
| `original_message_id` | string | 元のメッセージID |

### Botコマンドメッセージセグメント (ideaura_command)

ユーザーがBotコマンドをトリガーした場合、メッセージセグメントのタイプは `ideaura_command` です:

```json
{
  "type": "ideaura_command",
  "data": {
    "command_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

| フィールド | 型 | 説明 |
|------|------|------|
| `command_id` | string | コマンドUUID |

### イベント処理の例

```python
from ErisPulse.Core.Event import notice, message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "ideaura":
        # メッセージイベントを処理
        for segment in event.get("message", []):
            if segment.get("type") == "ideaura_forwarded":
                data = segment["data"]
                print(f"転送メッセージ、元ID: {data['forward_source_id']}")

@notice.on_notice()
async def handle_notice(event):
    if event.get_platform() != "ideaura":
        return

    detail_type = event.get("detail_type")

    if detail_type == "ideaura_message_edit":
        new_content = event.get("ideaura_new_content", "")
        print(f"メッセージが編集されました: {new_content}")

    elif detail_type == "ideaura_message_recall":
        message_id = event.get("message_id")
        print(f"メッセージが撤回されました: {message_id}")

    elif detail_type == "ideaura_friend_online":
        friend_name = event.get_user_nickname()
        print(f"友達がオンラインになりました: {friend_name}")

    elif detail_type == "ideaura_user_status_change":
        status = event.get("ideaura_status")
        print(f"ユーザーの状態が変更されました: {status}")
```

## Event Mixin 拡張メソッド

アダプターは以下のプラットフォーム固有メソッドを登録しており、`platform == "ideaura"` の場合にのみ利用可能です。

| メソッド | 戻り値型 | 説明 |
|------|----------|------|
| `get_source_type()` | `str` | メッセージの送信元タイプ (`chatroom`/`topic`/`private`) |
| `get_sender_name()` | `str` | 送信者のニックネーム |
| `get_sender_avatar()` | `str` | 送信者のアバター URL |
| `is_sender_bot()` | `bool` | 送信者がロボットかどうか |
| `is_receiver_bot()` | `bool` | 受信者がロボットかどうか |
| `get_command_id()` | `str` | Bot 指令 ID (`ideaura_command_id`) が存在する場合、その ID を取得 |
| `get_command()` | `str` | `get_command_id()` の別名 |
| `get_topic_name()` | `str` | トピック名 |
| `get_message_type()` | `str` | メッセージタイプ (normal/edited/forwarded/quoted) |
| `get_message_subtype()` | `str` | メッセージのサブタイプ (text/image/video/file/markdown/html) |
| `is_self_message()` | `bool` | 自分が送信したメッセージかどうか |

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() != "ideaura":
        return

    # Bot 指令 ID を取得（存在する場合）
    cmd_id = event.get_command_id()
    if cmd_id:
        print(f"指令を受信しました: {cmd_id}")
```

## 複数アカウントの設定

### 設定の説明

IdeauraAdapter は、**Bot Token** 認証を使用して、複数のアカウントを同時に設定および実行することをサポートしています。

> [!WARNING]
> 4.0.1 以降、**メールアドレスとパスワードによるログインは削除され、Bot Token でのみ認証が可能です**。Bot Token は [MSCPO 開放プラットフォーム](https://open.mscpo.com/rockychat/bots) から取得する必要があります（`bot-token-` で始まる形式）。

```toml
# config.toml
# アカウント1
[IdeauraAdapter.accounts.default]
token = "bot-token-xxxxxx1"      # ロボット API Token（必須）
enabled = true                   # 有効にするかどうか（オプション、デフォルトはtrue）

# アカウント2
[IdeauraAdapter.accounts.bot2]
token = "bot-token-xxxxxx2"
enabled = true

# オプション：サーバーのカスタムアドレス
[IdeauraAdapter]
base_url = "https://api.mscpo.com/api/rockychat"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**設定項目の説明：**
- `token`：ロボット API Token（必須、`bot-token-` で始まる形式）
- `enabled`：このアカウントを有効にするかどうか（オプション、デフォルトはtrue）

**グローバル設定項目：**
- `base_url`：API サーバーのアドレス（オプション、デフォルトは `https://api.mscpo.com/api/rockychat`）
- `ws_url`：WebSocket サーバーのアドレス（オプション、デフォルトは花楓珈琲館の公式アドレス）
- `heartbeat_interval`：ハートビートの間隔（秒）（オプション、デフォルトは30秒）

### Send DSL でアカウントを指定する

`Using()` メソッドを使用して、どのアカウントを使ってメッセージを送信するかを指定できます：

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# アカウント名を指定してメッセージを送信
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# user_id を指定してメッセージを送信（対応するアカウントに自動マッチング）
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# 指定しない場合は、最初に有効化されたアカウントが使用されます
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### イベントにおけるアカウント識別

受信したイベントには、自動的に対応するアカウント情報が含まれます：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["user_id"]
        print(f"メッセージはアカウント: {account_id} から送信されました")
```

## 拡張フィールドの説明

- すべての独自フィールドは `ideaura_` という接頭辞で識別され、標準フィールドとの衝突を回避します。
- 元のデータは `ideaura_raw` フィールドに保持され、プラットフォームの完全な元のデータにアクセスできるようにします。
- `self.user_id` は、現在ログインしているアカウントのユーザーIDを示します。
- `ideaura_source_type`：メッセージの送信元の種類（`chatroom`/`topic`/`private`）
- `ideaura_sender_name`：送信者のニックネーム
- `ideaura_sender_avatar`：送信者のアバターURL
- `ideaura_sender_is_bot`：送信者がロボットかどうか
- `ideaura_is_self`：送信したメッセージが自分自身のものかどうか（自分自身のメッセージはフィルタリング済み）
- `ideaura_topic_name`：トピック名
- `ideaura_message_type`：メッセージの種類（normal/edited/forwarded/quoted）
- `ideaura_message_subtype`：メッセージのサブタイプ（text/image/video/file/markdown/html）

### ファイル処理の特性

- ファイルサイズ制限：10MB（ダウンロードとローカル読み取りの両方に制限があります）
- 自動的なファイルタイプ検出：ファイルヘッダの魔法のバイトを使って実際のタイプを検出します。
- スマートなファイル名解析：`.bin`/`.dat`/`.tmp` などの意味のない拡張子に対して自動的に修正を行います。
- bytes、URL、ローカルパスの3種類のファイル入力方法をサポートします。
- URLから取得したファイルは自動的にダウンロードされ、サーバにアップロードされます。

### 対応するファイルタイプ

魔法のバイトを使って自動的に検出されます：

| タイプ | 拡張子 |
|------|--------|
| 画像 | png, jpg, gif, webp |
| 動画 | mp4, avi, flv |
| 音声 | mp3, wav, ogg |
| ドキュメント | pdf, docx |

## 注意事項

1. API サーバーのデフォルトアドレスは `https://api.mscpo.com/api/rockychat` です（`base_url` でカスタマイズ可能です）。WebSocket アドレス `wss://api-cofe.allons-y.uk:3009/mqtt` はプラットフォーム固有のアドレスであり、アダプター名の変更にかかわらず変化しません。
2. アダプターは WebSocket 長接続を使用してイベントを受け取り、自動再接続（固定5秒の遅延）をサポートします。
3. 自身が送信したメッセージ（`isSelf: true`）は自動的にフィルタリングされ、イベントが発生しません。
4. @全員（`AtAll()`）は管理者権限が必要です。
5. ファイルのアップロードサイズ制限は 10MB です。
6. 音声ファイルは `file` のサブタイプとして送信されます（プラットフォームは独立した音声形式を区別しません）。
7. エモジ（`Face()`）は純粋なテキスト形式で emoji を送信します。
8. プログラムを終了する際は、リソース解放を確実にするために `shutdown()` を呼び出してください。