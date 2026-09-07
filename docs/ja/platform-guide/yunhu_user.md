# 雲湖ユーザープラットフォームの機能ドキュメント

YunhuUserAdapter は、雲湖ユーザーアカウントプロトコルに基づいて構築されたアダプタであり、ユーザーメールアドレスアカウントによるログイン、WebSocket を使用したイベント受信、一貫したイベント処理およびメッセージ操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 1.4.0
- メンテナー: wsu2059

## 基本情報

- プラットフォーム概要：雲湖（Yunhu）はエンタープライズ向けのリアルタイムコミュニケーションプラットフォームです。このアダプターは**ユーザーのアカウント**（ロボットアカウントではなく）を使用して対話します。
- アダプター名：YunhuUserAdapter
- 複数アカウント対応：アカウント名で識別し、複数のユーザーアカウントを設定できます
- チェーン修飾子対応：`.Reply()` などのチェーン修飾子メソッドをサポート
- OneBot12互換：OneBot12形式のメッセージ送信をサポート
- 通信方式：メールアドレスでログインし、トークンを取得してWebSocketでイベントを受信し、HTTP + Protobufプロトコルでメッセージを送信
- 会話タイプ：プライベートチャット（user）、グループチャット（group）、ロボット会話（bot）をサポート

## 支援されるメッセージ送信タイプ

すべての送信メソッドは、チェーン式構文で実装されています。たとえば：

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

サポートされている送信タイプは以下の通りです。

- `.Text(text: str, buttons: Optional[List] = None)`：純粋なテキストメッセージを送信します。
- `.Html(html: str, buttons: Optional[List] = None)`：HTML形式のメッセージを送信します。
- `.Markdown(markdown: str, buttons: Optional[List] = None)`：Markdown形式のメッセージを送信します。
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)`：画像メッセージを送信します。URL、ローカルパス、またはバイナリデータをサポートします。
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)`：動画メッセージを送信します。URL、ローカルパス、またはバイナリデータをサポートします。
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)`：音声メッセージを送信します。URL、ローカルパス、またはバイナリデータをサポートし、自動的に音声長を検出します。
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)`：`.Audio()` の別名です。
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)`：ファイルメッセージを送信します。URL、ローカルパス、またはバイナリデータをサポートします。
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)`：絵文字/ステッカーのメッセージを送信します。ステッカーID、ステッカーURL、またはバイナリ画像データをサポートします。
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)`：A2UIメッセージ（メッセージタイプ14）を送信します。A2UI JSONデータはtextフィールドに埋め込まれて送信されます。
- `.Edit(msg_id: str, text: str, content_type: str = "text")`：既存のメッセージを編集します。
- `.Recall(msg_id: str)`：メッセージを撤回します。
- `.Raw_ob12(message: Union[List, Dict])`：OneBot12形式のメッセージを送信します。

### メディアファイル処理

すべてのメディアタイプ（画像、動画、音声、ファイル）は以下の入力方法をサポートします。

- **URL**：`"https://example.com/image.jpg"` — 自動的にダウンロード後にアップロードされます。
- **ローカルパス**：`"/path/to/file.jpg"` — 自動的に読み取り後にアップロードされます。
- **バイナリデータ**：`open("file.jpg", "rb").read()` — 直接アップロードされます。

メディアファイルは自動的に七牛雲ストレージにアップロードされ、以下の機能をサポートします。

- 自動的に `filetype` ライブラリでファイルタイプとMIMEを検出します。
- 自動的にファイルサイズを計算します。
- 音声ファイルは自動的に時長を検出します（MP3、MP4/M4A形式をサポート）。

### ボタンパラメータの説明

`buttons` パラメータは、ボタンのレイアウトと機能を示すネストされたリストです。各ボタンオブジェクトには以下のフィールドが含まれます。

| フィールド         | 型   | 必須 | 説明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | ボタン上の文字                                                         |
| `actionType` | int    | 是       | 動作タイプ：<br>`1`: URLにジャンプ<br>`2`: コピー<br>`3`: クリックして報告            |
| `url`        | string | 否       | `actionType=1` の場合、ジャンプ先のURLを示します                         |
| `value`      | string | 否       | `actionType=2` の場合、この値がクリップボードにコピーされます<br>`actionType=3` の場合、この値がサブスクライバーに送信されます |

例：
```python
buttons = [
    [
        {"text": "コピー", "actionType": 2, "value": "xxxx"},
        {"text": "クリックしてジャンプ", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "イベントを報告", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("ボタン付きのメッセージ")
```

### チェーン式修飾メソッド（組み合わせて使用可能）

チェーン式修飾メソッドは `self` を返し、チェーン式呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります。

- `.Reply(message_id: str)`：指定されたメッセージに返信します。
- `.At(user_id: str)`：@指定ユーザー（テキスト形式 @user_id）。
- `.AtAll()`：@全員（偽@全員、@allテキストを送信します）。
- `.Buttons(buttons: List)`：ボタンを追加します。

> **注意：** ユーザーアカウントは特殊なため、管理者でなくても@全員ができますが、この `AtAll()` は@全員のテキストを送信するだけで、偽@全員です。

### チェーン式呼び出しの例

```python
# 基本的な送信
await yunhu_user.Send.To("user", user_id).Text("Hello")

# メッセージに返信
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("返信メッセージ")

# 返信 + ボタン
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("返信とボタン付きのメッセージ")

# 指定アカウント + 返信 + ボタン
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("完全なチェーン式呼び出し")
```

### OneBot12メッセージのサポート

アダプターはOneBot12形式のメッセージを送信することをサポートし、プラットフォーム間のメッセージ互換性を確保します。

- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します。

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# チェーン式修飾と併用
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

Raw_ob12は、混合メッセージセグメントをグループ化して処理することをサポートします。

- `text`、`mention` タイプは1つのグループとして送信できます。
- `image`、`video`、`audio`、`file`、`face`、`markdown`、`html`、`a2ui` などのタイプはそれぞれ独立したグループになります。
- `reply` タイプは任意のグループに追加できます。

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、これに直接 await を使用して送信結果を取得できます。返り値は ErisPulse アダプタ標準化返り値規格に従います：

```python
{
    "status": "ok",           // 実行ステータス
    "retcode": 0,             // 戻りコード
    "data": {...},            // 応答データ
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "yunhu_user_raw": {...}   // 元の応答データ
}
```

## 特有イベントタイプ

このプラットフォームの機能を使用するには、`platform == "yunhu_user"` の検証が必要です。

### 核心的な差異点

1. 特有イベントタイプ:
    - スーパーファイル共有: `yunhu_user_file_send`
    - ロボット公告ボード: `yunhu_user_bot_board`
    - メッセージ編集通知: `message_edit`
    - メッセージ削除通知: `message_delete`（取り消し）
2. 特有メッセージセグメントタイプ:
    - フォームメッセージセグメント: `yunhu_user_form`
    - 記事メッセージセグメント: `yunhu_user_post`
    - ステッカー・メッセージセグメント: `yunhu_user_sticker`
    - ボタンメッセージセグメント: `yunhu_user_button`
    - A2UIメッセージセグメント: `a2ui`
3. 拡張フィールド:
    - すべての特有フィールドは `yunhu_user_` で始まるプレフィックスで識別されます
    - 元のデータは `yunhu_user_raw` フィールドに保持されます
    - 元のイベントタイプは `yunhu_user_raw_type` フィールドに記録されます
    - プライベートチャットでは `self.user_id` は現在ログインしているユーザーIDを示します

### 対応する元のイベントタイプ

| 元のイベントタイプ | OneBot12 タイプ | 説明 |
|-------------|--------------|------|
| `push_message` | `message` | プッシュメッセージ（プライベートチャット、グループチャット、Bot会話） |
| `edit_message` | `notice` (`message_edit`) | メッセージ編集イベント |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | スーパーファイル共有イベント |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | ロボット公告ボードイベント |

> 他のイベントタイプ（`heartbeat_ack`、`draft_input`、`stream_message` など）は無視されます。

### OneBot12 がサポートする detail_type

| OneBot12 detail_type | 雲湖 chat_type | 説明 |
|---------------------|---------------|------|
| `private` | 1 | プライベートチャットメッセージ |
| `group` | 2 | グループチャットメッセージ |
| `bot` | 3 | ロボット会話 |

### メッセージイベントの例

```python
{
    "id": "event_id",
    "time": 1234567890,
    "type": "message",
    "detail_type": "group",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message": [
        {"type": "text", "data": {"text": "メッセージ内容"}}
    ],
    "alt_message": "メッセージ内容",
    "user_id": "sender_user_id",
    "user_nickname": "送信者ニックネーム",
    "group_id": "group_id",
    "message_id": "msg_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "push_message"
}
```

### メッセージ編集通知の例

```python
{
    "type": "notice",
    "detail_type": "message_edit",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message_id": "msg_id",
    "user_id": "sender_user_id",
    "user_nickname": "送信者ニックネーム",
    "edit_time": 1234567890,
    "group_id": "group_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "edit_message"
}
```

### スーパーファイル共有イベントの例

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_file_send",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "user_id": "send_user_id",
    "user_nickname": "",
    "yunhu_user_file_send": {
        "send_user_id": "送信者ID",
        "user_id": "受信ユーザーID",
        "send_type": "送信タイプ",
        "data": "ファイルデータ"
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "file_send_message"
}
```

### ロボット公告ボードイベントの例

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_bot_board",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "bot_id": "bot_id",
    "bot_name": "ロボット名",
    "yunhu_user_bot_board": {
        "bot_id": "bot_id",
        "chat_id": "chat_id",
        "chat_type": 1,
        "content": "公告内容",
        "content_type": 1,
        "last_update_time": 1234567890
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "bot_board_message"
}
```

### イベント処理の例

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_yunhu_user_message(event):
    """雲湖ユーザーのメッセージを処理"""
    if event.get("platform") != "yunhu_user":
        return
    
    user_id = event.get("user_id", "")
    user_nickname = event.get("user_nickname", "")
    alt_message = event.get("alt_message", "")
    
    print(f"ユーザー {user_nickname}({user_id}): {alt_message}")
    
    # メッセージセグメント内の特有タイプをチェック
    for segment in event.get("message", []):
        seg_type = segment.get("type", "")
        
        if seg_type == "yunhu_user_form":
            form_data = segment["data"]["form"]
            print(f"フォームメッセージを受け取りました: {form_data}")
        
        elif seg_type == "yunhu_user_post":
            post_data = segment["data"]
            print(f"記事メッセージを受け取りました: {post_data.get('post_title', '')}")
        
        elif seg_type == "yunhu_user_sticker":
            sticker_url = segment["data"]["file_id"]
            print(f"ステッカー・メッセージを受け取りました: {sticker_url}")
        
        elif seg_type == "yunhu_user_button":
            buttons = segment["data"]["buttons"]
            print(f"メッセージにボタンが含まれています: {buttons}")
        
        elif seg_type == "a2ui":
            a2ui_data = segment["data"]["a2ui"]
            print(f"A2UIメッセージを受け取りました: {a2ui_data}")
    
    # event.reply() を使用して自動返信
    await event.reply(f"Echo: {alt_message}")

@notice.on_notice()
async def handle_yunhu_user_notice(event):
    """雲湖ユーザーの通知イベントを処理"""
    if event.get("platform") != "yunhu_user":
        return
    
    detail_type = event.get("detail_type", "")
    
    if detail_type == "message_edit":
        message_id = event.get("message_id", "")
        user_nickname = event.get("user_nickname", "")
        edit_time = event.get("edit_time", 0)
        print(f"ユーザー {user_nickname} がメッセージ {message_id} を編集しました")
    
    elif detail_type == "yunhu_user_file_send":
        file_data = event.get("yunhu_user_file_send", {})
        print(f"スーパーファイル共有を受け取りました: {file_data}")
    
    elif detail_type == "yunhu_user_bot_board":
        board_data = event.get("yunhu_user_bot_board", {})
        bot_name = event.get("bot_name", "")
        print(f"ロボット {bot_name} が公告を発表しました: {board_data.get('content', '')}")
```

## 拡張フィールドの説明

- すべての独自フィールドは `yunhu_user_` という接頭辞で識別され、標準フィールドとの衝突を避ける。
- 元のデータは `yunhu_user_raw` フィールドに保存され、クラウド湖プラットフォームの完全な元のデータにアクセスできるようにする。
- 元のイベントタイプは `yunhu_user_raw_type` フィールドに記録される（例: `push_message`、`edit_message` など）。
- `self.user_id` は現在ログインしているユーザーIDを表し、ログインレスポンスから取得する。
- スーパーファイル共有は `yunhu_user_file_send` フィールドを通じてファイル共有データを提供する。
- ロボットの公告ボードは `yunhu_user_bot_board` フィールドを通じて公告データを提供する。

### 独自メッセージセグメントタイプ

#### フォームメッセージセグメント (yunhu_user_form)

content_type が 5 の場合、メッセージセグメントタイプは `yunhu_user_form` となる：

```json
{
    "type": "yunhu_user_form",
    "data": {
        "form": "フォームデータ"
    }
}
```

#### 記事メッセージセグメント (yunhu_user_post)

content_type が 6 の場合、メッセージセグメントタイプは `yunhu_user_post` となる：

```json
{
    "type": "yunhu_user_post",
    "data": {
        "post_id": "記事ID",
        "post_title": "記事タイトル",
        "post_content": "記事内容"
    }
}
```

| フィールド | 型 | 説明 |
|------|------|------|
| `post_id` | string | 記事の一意の識別子 |
| `post_title` | string | 記事タイトル |
| `post_content` | string | 記事内容 |

#### スタンプメッセージセグメント (yunhu_user_sticker)

content_type が 7 の場合、メッセージセグメントタイプは `yunhu_user_sticker` となる：

```json
{
    "type": "yunhu_user_sticker",
    "data": {
        "file_id": "スタンプ画像のURL"
    }
}
```

| フィールド | 型 | 説明 |
|------|------|------|
| `file_id` | string | スタンプ画像のURL |

#### ボタンメッセージセグメント (yunhu_user_button)

メッセージにボタンが含まれる場合、`yunhu_user_button` メッセージセグメントが追加される：

```json
{
    "type": "yunhu_user_button",
    "data": {
        "buttons": [[{"text": "ボタンの文字", "actionType": 3, "value": "値"}]]
    }
}
```

#### A2UI メッセージセグメント (a2ui)

content_type が 14 の場合、メッセージセグメントタイプは `a2ui` となる：

```json
{
    "type": "a2ui",
    "data": {
        "a2ui": "A2UI JSONデータ"
    }
}
```

## 複数アカウントの設定

### 設定の説明

YunhuUserAdapter は、複数のユーザー アカウントを同時に設定および実行することをサポートしています。

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # WebSocket 再接続間隔（秒）
ws_timeout = 70             # WebSocket タイムアウト時間（秒）

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # ユーザーのメールアドレス（必須）
password = "password1"       # ユーザーのパスワード（必須）
platform = "windows"         # ログインプラットフォーム（オプション、デフォルトは windows）
device_id = ""               # デバイスID（オプション、未入力で自動生成）
enabled = true               # アカウントの有効化（オプション、デフォルトは true）

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**設定項目の説明：**
- `email`：ユーザーのメールアドレス（必須）、雲湖プラットフォームへのログインに使用
- `password`：ユーザーのパスワード（必須）
- `platform`：ログインプラットフォーム識別子（オプション、デフォルトは `windows`）、利用可能な値：`windows`、`macos`、`linux`、`ios`、`android`
- `device_id`：デバイスID（オプション、未入力で自動生成）、セッションの一貫性を保つために固定値を設定することを推奨
- `enabled`：アカウントの有効化（オプション、デフォルトは `true`）

**アダプタレベルの設定：**
- `ws_reconnect_interval`：WebSocket 再接続間隔（秒、デフォルトは 30）
- `ws_timeout`：WebSocket タイムアウト時間（秒、デフォルトは 70）

**重要な注意事項：**
1. アダプタはメールアドレスによるログイン方式でトークンを取得し、ログイン後に WebSocket を通じてイベントを受信します。
2. WebSocket 接続が切断された場合、自動的に再接続が行われ、最大3回まで再試行されます。
3. 各アカウントに固定の `device_id` を設定することを推奨します。これにより、セッションの一貫性が保たれます。
4. テンプレートアカウント（デフォルトのメールアドレスとパスワード）は、自動的にスキップされます。

### Send DSL を使用してアカウントを指定

`Using()` メソッドを使用して、どのアカウントを使ってメッセージを送信するかを指定できます。このメソッドは2種類の引数をサポートします：
- **アカウント名**：設定ファイル中のアカウント名（例：`default`、`account2`）
- **user_id**：ログイン後に取得されるユーザーID

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# アカウント名を使ってメッセージを送信
await yunhu_user.Send.Using("default").To("user", "user123").Text("Hello from account1!")

# user_id を使ってメッセージを送信（対応するアカウントを自動的に検索）
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Hello from user!")

# 指定しない場合、最初に有効化されたアカウントが使用されます
await yunhu_user.Send.To("user", "user123").Text("Hello from default account!")
```

> **注意：** `user_id` を使用する場合、システムは設定ファイル内で一致するアカウントを自動的に検索します。イベントの返信処理では、`event["self"]["user_id"]` を使用して同じアカウントに返信するのに特に便利です。

### イベントにおけるアカウント識別

受信したイベントには、対応するユーザーID情報が自動的に含まれます：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # 現在ログインしているユーザーIDを取得
        my_user_id = event["self"]["user_id"]
        print(f"メッセージはアカウント: {my_user_id} から送信されました。")
        
        # 同じアカウントを使って返信
        yunhu_user = adapter.get("yunhu_user")
        await yunhu_user.Send.Using(my_user_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("返信メッセージ")
```

### ログ情報

アダプタは、ログにアカウント情報を自動的に含め、デバッグや追跡に便利です：

```
[INFO] アカウント default (user1@example.com) がログイン成功、ユーザーID: 12345678
[INFO] アカウント default の WebSocket 監視タスクが起動しました
[INFO] アカウント account2 (user2@example.com) がログイン成功、ユーザーID: 87654321
```

### 管理インターフェース

```python
# すべてのアカウント情報を取得
accounts = yunhu_user.accounts
# 戻り値の形式: {"default": {"name": "default", "email": "...", "token": "...", "user_id": "...", ...}, ...}

# アカウントが有効かどうかをチェック
for account_name, account_config in yunhu_user._account_configs.items():
    print(f"{account_name}: enabled={account_config.enabled}")

# アカウント名から HTTP クライアントを取得
http_client = yunhu_user._get_http_client("default")

# user_id からアカウントを検索
account_name = yunhu_user._get_account_by_user_id("12345678")
```

## API 呼び出し

アダプターは `call_api` メソッドを提供し、プラットフォーム API を直接呼び出すことができます。

```python
# メッセージの送信
result = await yunhu_user.call_api("/send", 
    target_type="group", 
    target_id="group_id",
    account_id="default",
    message={"text": "Hello", "msg_type": 1}
)

# メッセージの編集
result = await yunhu_user.call_api("/edit",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id",
    text="新内容",
    content_type="text"
)

# メッセージの撤回
result = await yunhu_user.call_api("/recall",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id"
)

# メッセージの一括撤回
result = await yunhu_user.call_api("/recall_batch",
    target_type="group",
    target_id="group_id",
    msg_id_list=["msg_id_1", "msg_id_2"]
)

# メッセージリストの取得
result = await yunhu_user.call_api("/list",
    chat_id="group_id",
    chat_type=2,
    msg_count=10,
    msg_id=""
)

# メッセージ編集履歴の取得
result = await yunhu_user.call_api("/list_edit_record",
    msg_id="msg_id",
    size=10,
    page=1
)

# ボタンイベントの報告
result = await yunhu_user.call_api("/button_report",
    chat_id="group_id",
    chat_type=2,
    msg_id="msg_id",
    user_id="user_id",
    button_value="button_value"
)
```

**サポートされる API エンドポイント:**

| エンドポイント | 説明 |
|------|------|
| `/send` | メッセージの送信 |
| `/edit` | メッセージの編集 |
| `/recall` | メッセージの撤回 |
| `/recall_batch` | メッセージの一括撤回 |
| `/list` | メッセージリストの取得 |
| `/list_by_seq` | シーケンスによるメッセージの取得 |
| `/list_by_mid_seq` | メッセージIDとシーケンスによるメッセージの取得 |
| `/list_edit_record` | メッセージ編集履歴の取得 |
| `/button_report` | ボタンイベントの報告 |