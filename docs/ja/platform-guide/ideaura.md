# 花枫咖啡館（RockyChat）プラットフォーム機能ドキュメント

IdeauraAdapter は、花楓コーヒー館（RockyChat）プラットフォームの API を基に構築されたアダプターで、すべてのプラットフォーム機能モジュールを統合し、一貫したイベント処理およびメッセージ操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュール: ErisPulse-Ideaura
- 対応モジュールバージョン: 4.3.2
- 維持者: ErisPulse
- 最終更新日: 2026-11-10

## 基本情報

- プラットフォーム概要: 花楓コーヒー館（RockyChat）は、リアルタイム通信プラットフォームです。
- アダプター名: IdeauraAdapter
- マルチアカウント対応: Bot Token による複数アカウントの設定が可能です。
- チェーン修飾子対応: `.At()`、`.AtAll()`、`.Reply()`、`.Command()` などのチェーン修飾メソッドがサポートされています。
- OneBot12 向け: OneBot12 形式のメッセージ送信が可能です。

## 標準化対応（4.3.2）

### イベントとアカウント

1. **イベント `self.account_id` の注入**: すべてのイベントは、そのイベントが発生したアカウント名を保持しており、マルチアカウント環境では `event.reply()` は自動的に該当アカウントで返信します。
2. **アカウント設定に `bot_id` オプションフィールドを追加**: `IdeauraAccountConfig` は `bot_id` をサポートし、アカウントに対応する Bot ユーザー ID を明示的に指定できます。
3. **友達申請イベントに標準 `request_id` を追加**: `friend_request` / `friend_event` イベントの最上位に `request_id`（`ideaura_request_id` と同じ値）が追加され、`event.approve()` / `event.reject()` で申請を承認・拒否できます。

友達申請処理の例:

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_friend_request(event):
    if event.get("platform") != "ideaura":
        return
    # event["request_id"] は ideaura_request_id と同じ値
    if event.get("detail_type") == "friend":
        await event.approve()    # 友達申請を承認
    # await event.reject()       # 友達申請を拒否
```

インターフェースの規約は SDK の規格に従います: [リクエストと承認アクションの規格](../standards/request-action-spec.md)。

### アクションとエラーコード規格

1. **標準アクション名を HTTP パスに転送しない**: `call_api` に未実装の標準アクション名（例: `get_self_info`）を渡した場合、HTTP パスに転送せず、明示的にエラーコード 10002 を返します。プラットフォームの HTTP パス呼び出しは `/api/` で始まる必要があります。
2. エラーコードが標準化されました（元の HTTP ステータスコード、`-1`、`34000` などの旧値はすべて削除）：

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 33001 | ネットワークエラー（リクエスト異常、タイムアウトなど） |
| 34100 | プラットフォームエラー（元のレスポンスは `ideaura_raw` フィールドに保持） |
| 10002 | 対応していないアクション / メッセージセグメント（未実装の標準アクション、Face エモジセグメントなど） |

### Send 規格

- HTML メソッド名は `HTML`（`Html` は予約別名）
- `Face` セグメントは 10002 エラーコードを返し、警告ログを出力します。純文に降格して送信することはなく、無視されます。
- Raw_ob12 で未知のメッセージセグメントが見つかった場合は警告ログを出力し、すべてのセグメントが処理できない場合は 10002 を返します。

## v5 ファンタジア更新（4.1.0）

- **BaseConverter 継承**: 転換器の共通フィールドはフレームワークの build_base_event で構築されます。
- **spawn_background タスクの所属**: アカウント接続タスクは runtime.spawn_background を使用します。
- **フレームワークのソフト依存**: ErisPulse>=2.7.1 を実行時に検出し、警告を出力します。起動時にバージョンログを出力します。
- Request DSL クエリ式インターフェース（`Request(request_id)`）は延期されます。友達申請の承認はイベント `event.approve()` / `event.reject()` で処理できます（「標準化対応（4.3.2）」を参照）。

### 対応プラットフォーム機能

- **イベント**: メッセージ編集/撤回/転送/既読（ideaura_message_*）、友達申請（friend_request）、友達増減（friend_increase/decrease）、オンラインステータス（friend_online/offline）
- **送信**: Text / Image / Markdown / Raw_ob12（チェーン修飾子 Reply/At/AtAll）
- **友達申請承認**: 4.3.2 以降、イベント `event.approve()` / `event.reject()` で対応
- **未対応**: Api DSL（プラットフォーム REST インターフェースが公開された後に追加）、Request DSL クエリ式インターフェース

---

## 支援されるメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実現されます。例:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

サポートされる送信タイプは以下の通りです:

- `.Text(text: str)`：テキストメッセージを送信します。
- `.Image(file, filename: str = None)`：画像メッセージを送信します。bytes/URL/ローカルパスをサポートします。
- `.Video(file, filename: str = None)`：動画メッセージを送信します。bytes/URL/ローカルパスをサポートします。
- `.File(file, filename: str = None)`：ファイルメッセージを送信します。bytes/URL/ローカルパスをサポートします。
- `.Voice(file, filename: str = None)`：音声メッセージを送信します（ファイルとして）。
- `.Face(face_id: str)`：エモジを送信します（4.3.2 以降**プラットフォームはサポートしていません**。retcode=10002 を返し、無視されます。テキストに降格することもありません）。
- `.Markdown(text: str)`：Markdown 形式のメッセージを送信します。
- `.HTML(html: str)`：HTML 形式のメッセージを送信します（`Html` は予約別名）。
- `.MergeForward(nodes, title="合併チャット記録")`：合併転送メッセージを送信します（`<details>` 折りたたみ HTML カードとしてレンダリングされます）。
- `.Edit(message_id: str, text: str, content_type: str = "text")`：既存のメッセージを編集します。
- `.Recall(message_id: str)`：メッセージを撤回します。

### チェーン修飾メソッド（組み合わせて使用可能）

チェーン修飾メソッドは `self` を返し、チェーンで呼び出すことができます。最終的な送信メソッドの前に呼び出す必要があります:

- `.At(user_id: str, name: str = None)`：指定ユーザーを@します。
- `.AtAll()`：全員を@します。
- `.Reply(message_id: str)`：指定メッセージに返信します。
- `.Command(command_id: str)`：Bot コマンドをトリガーします。送信メソッドと組み合わせて使用します（メッセージを指定されたコマンドとして送信します）。

### チェーン呼び出しの例

```python
# 基本送信
await ideaura.Send.To("user", user_id).Text("Hello")

# Bot コマンドのトリガー
await ideaura.Send.To("group", "chatroom").Command("550e8400-e29b-41d4-a716-446655440000").Text("/weather 北京")

# @ユーザー
await ideaura.Send.To("group", "chatroom").At("456").Text("@李四 你好")

# @複数ユーザー
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@複数ユーザー")

# メッセージの返信
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("返信メッセージ")

# 返信 + @
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("返信して@")

# HTML 形式メッセージ
await ideaura.Send.To("group", "chatroom").HTML("<p>HTML メッセージ</p>")
```

### 異なるターゲットへの送信

```python
# チャットルームに送信
await ideaura.Send.To("group", "chatroom").Text("チャットルームメッセージ")

# トピックに送信
await ideaura.Send.To("group", "topic_id").Text("トピックメッセージ")

# プライベートメッセージ送信
await ideaura.Send.To("user", "user_id").Text("プライベートメッセージ")
```

### OneBot12 メッセージ対応

アダプターは OneBot12 形式のメッセージ送信をサポートし、跨プラットフォームのメッセージ互換性を確保します:

- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12 形式のメッセージを送信します。

```python
# OneBot12 形式メッセージの送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# チェーン修飾子と組み合わせて使用
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

> 未知のメッセージセグメントは警告ログを出力し、無視されます。すべてのメッセージセグメントが処理できない場合は、retcode=10002 を返します。

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、await で送信結果を取得できます。返り値は ErisPulse アダプターの標準化された返り値規格に従います:

```python
{
    "status": "ok",           // 実行状態
    "retcode": 0,             // 返り値コード（0 が成功、エラーコードは「標準化対応（4.3.2）」を参照）
    "data": {...},            // レスポンスデータ
    "self": {...},            // 自身の情報（user_id を含む）
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "ideaura_raw": {...}      // 元のレスポンスデータ
}
```

## 特有のイベントタイプ

`platform=="ideaura"` の検査が必要です。

### 核心的な差異点

1. 特有のイベントタイプ:
    - メッセージ編集: ideaura_message_edit
    - メッセージ撤回: ideaura_message_recall
    - メッセージ転送: ideaura_message_forward
    - メッセージ既読: ideaura_message_read
    - 友達拒否: ideaura_friend_rejected
    - 友達オンライン: ideaura_friend_online
    - 友達オフライン: ideaura_friend_offline
    - ユーザー状態変更: ideaura_user_status_change
    - 転送メッセージセグメント: ideaura_forwarded
    - 編集マークセグメント: ideaura_edited
    - Markdownメッセージセグメント: ideaura_markdown
    - HTMLメッセージセグメント: ideaura_html
    - Bot コマンドメッセージセグメント: ideaura_command
2. 拡張フィールド:
    - すべての特有フィールドは `ideaura_` で始まります
    - 元のデータは `ideaura_raw` フィールドに保持されます
    - イベント `self.user_id` は現在のアカウントのユーザーIDを示し、`self.account_id` はアカウント名です

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
  "ideaura_forward_to": "目的トピックID",
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
  "ideaura_friend_avatar": "アバターURL",
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

4.3.2 以降、最上位に標準 `request_id` フィールドが追加され、`ideaura_request_id` と同じ値です。`event.approve()` / `event.reject()` で承認できます:

```python
{
  "type": "request",
  "detail_type": "friend",
  "platform": "ideaura",
  "user_id": "リクエスト者ID",
  "user_nickname": "リクエスト者のニックネーム",
  "request_id": "リクエストID",
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

| フィールド | タイプ | 説明 |
|------|------|------|
| `forward_source_id` | string | 転送元メッセージID |
| `original_message_id` | string | 元のメッセージID |

### Bot コマンドメッセージセグメント (ideaura_command)

ユーザーが Bot コマンドをトリガーした場合、メッセージセグメントのタイプは `ideaura_command` です:

```json
{
  "type": "ideaura_command",
  "data": {
    "command_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

| フィールド | タイプ | 説明 |
|------|------|------|
| `command_id` | string | コマンド UUID |

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
        print(f"ユーザーのステータスが変更されました: {status}")
```

## Event Mixin 拡張メソッド

アダプターは以下のプラットフォーム固有メソッドを登録しており、`platform == "ideaura"` の場合にのみ使用可能です:

| メソッド | 戻り値型 | 説明 |
|------|----------|------|
| `get_source_type()` | `str` | メッセージの送信元タイプ（`chatroom`/`topic`/`private`） |
| `get_sender_name()` | `str` | 送信者のニックネーム |
| `get_sender_avatar()` | `str` | 送信者のアバター URL |
| `is_sender_bot()` | `bool` | 送信者が Bot かどうか |
| `is_receiver_bot()` | `bool` | 受信者が Bot かどうか |
| `get_command_id()` | `str` | トリガーされた Bot コマンド ID（存在する場合、`ideaura_command_id`） |
| `get_command()` | `str` | `get_command_id()` の別名 |
| `get_topic_name()` | `str` | トピックの名前 |
| `get_message_type()` | `str` | メッセージのタイプ（normal/edited/forwarded/quoted） |
| `get_message_subtype()` | `str` | メッセージのサブタイプ（text/image/video/file/markdown/html） |
| `is_self_message()` | `bool` | 自分が送信したメッセージかどうか |

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() != "ideaura":
        return

    # トリガーされた Bot コマンド ID を取得（存在する場合）
    cmd_id = event.get_command_id()
    if cmd_id:
        print(f"コマンドを受け取りました: {cmd_id}")
```

---

## マルチアカウント設定

### 設定の説明

IdeauraAdapter は複数のアカウントを同時に設定および実行できます。**Bot Token** を使用した認証が必要です。

> [!WARNING]
> 4.0.1 以降**メールアドレス/パスワードによるログインは削除され、Bot Token でのみ対応**します。Bot Token は [MSCPO オープンプラットフォーム](https://open.mscpo.com/rockychat/bots) から取得する必要があります（`bot-token-` で始まります）。

```toml
# config.toml
# アカウント1
[IdeauraAdapter.accounts.default]
token = "bot-token-xxxxxx1"      # ロボット API Token（必須）
bot_id = ""                      # Bot ユーザーID（オプション、アカウントに対応する Bot を明示的に指定）
enabled = true                   # 有効かどうか（オプション、デフォルトはtrue）

# アカウント2
[IdeauraAdapter.accounts.bot2]
token = "bot-token-xxxxxx2"
bot_id = ""
enabled = true

# オプション: 自定義サーバーのアドレス
[IdeauraAdapter]
base_url = "https://api.mscpo.com/api/rockychat"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**設定項目の説明:**
- `token`: ロボット API Token（必須、`bot-token-` で始まる）
- `bot_id`: Bot ユーザーID（オプション、4.3.2 以降対応、アカウントに対応する Bot を明示的に指定）
- `enabled`: アカウントの有効性（オプション、デフォルトはtrue）

**グローバル設定項目:**
- `base_url`: API サーバーのアドレス（オプション、デフォルトは `https://api.mscpo.com/api/rockychat`）
- `ws_url`: WebSocket サーバーのアドレス（オプション、デフォルトは花楓コーヒー館の公式アドレス）
- `heartbeat_interval`: ハートビートの間隔（秒、オプション、デフォルトは30秒）

### Send DSL でアカウントを指定

`Using()` メソッドで送信するアカウントを指定できます:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# アカウント名で送信
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# user_id で送信（自動的に対応するアカウントにマッチ）
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# 指定しない場合は最初に有効なアカウントを使用
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### イベントでのアカウント識別

受信されたイベントには自動的に対応するアカウント情報が含まれます（4.3.2 以降 `self.account_id` はアカウント名です）:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["account_id"]
        print(f"メッセージはアカウント: {account_id} から来ています")
```

---

## 拡張フィールドの説明

- すべての特有フィールドは `ideaura_` で始まり、標準フィールドとの衝突を避ける
- 元のデータは `ideaura_raw` フィールドに保持され、プラットフォームの完全な元のデータにアクセスできる
- `self.user_id` は現在ログインしているアカウントのユーザーIDを示し、`self.account_id` はアカウント名
- `ideaura_source_type`: メッセージの送信元タイプ（`chatroom`/`topic`/`private`）
- `ideaura_sender_name`: 送信者のニックネーム
- `ideaura_sender_avatar`: 送信者のアバターURL
- `ideaura_sender_is_bot`: 送信者がロボットかどうか
- `ideaura_is_self`: 自分が送信したメッセージかどうか（自己メッセージはフィルタリング済み）
- `ideaura_topic_name`: トピックの名前
- `ideaura_message_type`: メッセージのタイプ（normal/edited/forwarded/quoted）
- `ideaura_message_subtype`: メッセージのサブタイプ（text/image/video/file/markdown/html）

### ファイル処理の特性

- ファイルサイズ制限: 10MB（ダウンロードとローカル読み込みの両方に制限があります）
- 自動ファイルタイプ検出: ファイルの魔法のバイトで実際のタイプを検出します
- スマートなファイル名解析: `.bin`/`.dat`/`.tmp` などの意味のない拡張子は自動的に修正されます
- bytes、URL、ローカルパスの3種類のファイル入力方式をサポート
- URL ファイルは自動的にダウンロードされ、サーバーにアップロードされます

### 対応するファイルタイプ

魔法のバイトで自動検出されます:

| タイプ | 拡張子 |
|------|--------|
| 画像 | png, jpg, gif, webp |
| 動画 | mp4, avi, flv |
| 音声 | mp3, wav, ogg |
| ドキュメント | pdf, docx |

---

## 注意事項

1. API サーバーのデフォルトアドレスは `https://api.mscpo.com/api/rockychat`（`base_url` でカスタマイズ可能）です。WebSocket アドレス `wss://api-cofe.allons-y.uk:3009/mqtt` はプラットフォームの固有アドレスであり、アダプター名の変更に伴って変化しません。
2. アダプターは WebSocket 長接続を使用してイベントを受信し、自動再接続（固定5秒の遅延）をサポートします。
3. 自身が送信したメッセージ（`isSelf: true`）は自動的にフィルタリングされ、イベントが発生しません。
4. @全員（`AtAll()`）は管理者権限が必要です。
5. ファイルのアップロードサイズ制限は 10MB です。
6. 音声ファイルは `file` サブタイプとして送信されます（プラットフォームは独立した音声タイプを区別しません）。
7. エモジ（`Face()`）はプラットフォームでサポートされていないため、retcode=10002 を返し、無視されます（テキストに降格することもありません）。
8. プログラム終了時には `shutdown()` を呼び出してリソースを確実に解放してください。