# 雲湖ユーザープラットフォーム特徴ドキュメント

YunhuUserAdapter は、雲湖ユーザーアカウントプロトコルに基づいて構築されたアダプターです。ユーザーアカウント（ロボットアカウントではなく）を使用してメールアドレスでログインし、WebSocket を使用してイベントを受信し、統一されたイベント処理とメッセージ操作のインターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.2.0
- 維持管理者: wsu2059

## 基本情報

- プラットフォーム概要: 雲湖（Yunhu）はエンタープライズ向けのリアルタイムコミュニケーションプラットフォームであり、このアダプターは**ユーザーアカウント**（ロボットアカウントではなく）を通じて対応します。
- アダプター名: YunhuUserAdapter
- マルチアカウント対応: アカウント名で識別し、複数のユーザーアカウントを設定できます。
- チェーン修飾対応: `.Reply()` などのチェーン修飾メソッドをサポートします。
- OneBot12互換: OneBot12形式のメッセージ送信をサポートします。
- 通信方式: メールアドレスでログインし、token を取得し、WebSocket を使用してイベントを受信し、HTTP + Protobuf プロトコルを使用してメッセージを送信します。
- 会話タイプ: プライベートチャット（user）、グループチャット（group）、ロボット会話（bot）をサポートします。

## v5 ファンタジー更新（4.2.0）

- **BaseConverter 継承**；**spawn_background タスクの所属**（WS 監視タスク）
- **ユーザーアプリケーションプログラミングインターフェース（API）全集**（yhchatAPI full.proto / v1 エンドポイント、Protobuf over HTTP をベース）：
  - ユーザー：get_user / edit_nickname / edit_avatar
  - フレンド：アドレスブック / 申請リスト / 申請 / 承認 / 無視 / 削除
  - グループ：グループ情報 / メンバー一覧 / 作成 / 解散 / 招待 / 除外 / 禁言 / ロボット一覧
  - 会話：会話一覧；メッセージ：一覧 / 撤回 / ボタン報告
- **フレームワークソフト依存**：ErisPulse>=2.7.1 を実行時に検出し、警告を表示します；起動時にバージョンログを出力します

## 対応プラットフォーム機能リスト

### イベント受信（WebSocket、protobuf エンコード）

| WS cmd | イベント | 説明 |
|--------|------|------|
| `push_message` | `message` | プライベートチャット/グループチャット/Bot 会話メッセージ（テキスト/HTML/Markdown/画像/動画/音声/ファイル/絵文字/フォーム/記事/ステッカー/ボタン/A2UI） |
| `edit_message` | `notice` (`message_edit`) | メッセージ編集通知 |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | スーパーファイル共有 |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | ロボット公告ボード |

### Api DSL メソッド対照表（ YunhuHTTPClient → ユーザーアプリケーションプログラミングインターフェース v1 エンドポイント ）

| 分類 | Api メソッド | エンドポイント | 説明 |
|------|---------|------|------|
| アカウント | `get_self_info()` | `/user/info` | ログインユーザー情報（ニックネーム/プロフィール画像/user_id） |
| ユーザー | `get_user(user_id)` | `/user/get-user` | ユーザー詳細情報 |
| ユーザー | `edit_nickname(nickname)` | `/user/edit-nickname` | 自分のニックネームを変更します |
| ユーザー | `edit_avatar(url)` | `/user/edit-avatar` | 自分のプロフィール画像を変更します |
| フレンド | `get_friend_address_book(md5)` | `/friend/address-book-list` | アドレスブック（カーソル付きページング） |
| フレンド | `get_friend_requests()` | `/friend/request-list` | フレンド/グループ参加申請リスト |
| フレンド | `friend_apply(user_id, desc)` | `/friend/apply` | フレンド申請を送信します |
| フレンド | `friend_agree_apply(user_id)` | `/friend/agree-apply` | フレンド申請を承認します |
| フレンド | `friend_ignore_apply(user_id)` | `/friend/ignore-apply` | フレンド申請を無視します |
| フレンド | `friend_delete(user_id)` | `/friend/delete-friend` | フレンドを削除します |
| グループ | `get_group_info(group_id)` | `/group/info` | グループ情報 |
| グループ | `get_group_member_list(group_id)` | `/group/list-member` | グループメンバー一覧（キーワード検索対応） |
| グループ | `create_group(name, ...)` | `/group/create-group` | グループを作成します |
| グループ | `dismiss_group(group_id)` | `/group/dismiss-group` | グループを解散します |
| グループ | `group_invite(group_id, user_ids)` | `/group/invite` | メンバーを招待します |
| グループ | `group_remove_member(group_id, user_id)` | `/group/remove-member` | メンバーをグループから除外します |
| グループ | `group_gag_member(group_id, user_id, 秒)` | `/group/gag-member` | グループメンバーを一時的に禁止します（0=解除） |
| グループ | `get_group_bot_list(group_id)` | `/group/bot-list` | グループ内のロボット一覧 |
| 会話 | `get_conversation_list(md5)` | `/conversation/list` | 会話一覧（カーソル付きページング） |
| メッセージ | `get_message_list(chat_id, chat_type, ...)` | `/msg/list-message` | メッセージ一覧（複数のページング変種あり HTTP クライアントを参照） |
| メッセージ | `delete_message(msg_id, chat_id, chat_type)` | `/msg/recall-msg` | メッセージを撤回します（一括撤回は HTTP クライアントを参照） |
| メッセージ | `button_report(...)` | `/msg/button-report` | ボタンクリック報告 |
| 元アクション | `get_status` / `get_version` / `get_supported_actions` | - | 実行状態/バージョン/サポートアクション |

### 未対応（エンドポイントは既知、full.proto メッセージは完全、必要に応じて拡張可能）

- ユーザー：認証コードログイン、バッジ、金豆記録、電話番号/メールアドレスのバインド、通知設定、ユーザーのデータ保存と取得
- フレンド：通知を無視（no-notify）、申請記録の削除
- グループ：コマンドリスト、カテゴリ、おすすめ、ライブ配信、グループ情報を編集/グループニックネーム/キーワード、グループ参加の自動承認、グループファイル制限、イベント SSE
- 会話：固定/並べ替え/削除、通知を無視
- メッセージ：転送、A2UI提出、メッセージ一覧の画像取得、ファイルのダウンロード記録
- グループタグ：list / relate / relate-cancel / create / edit / delete / members（エンドポイント `/group-tag/*`）

> 拡張方法：`YunhuHTTPClient` に既存のパターンに従ってメソッドを追加します（`_proto_request` / `_json_request` 一般的なラッパー）、そして `Api` クラスで公開します。エンドポイントとメッセージ定義は `yhchatAPI/src/api/v1/*.md` と `yhchatAPI/src/full.proto` を参照してください。

### ユーザーアプリケーションプログラミングインターフェースの例

```python
from ErisPulse import sdk
yunhu_user = sdk.adapter.get("yunhu_user")

result = await yunhu_user.Api.get_self_info()
result = await yunhu_user.Api.get_friend_requests()          # フレンド申請リスト
await yunhu_user.Api.friend_agree_apply(user_id)             # フレンド申請を承認
result = await yunhu_user.Api.get_group_member_list(group_id)
result = await yunhu_user.Api.get_conversation_list()        # 会話リスト
await yunhu_user.Api.delete_message(msg_id, chat_id, chat_type)  # メッセージを撤回
```

---

## 支援されるメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実装されています。例：
```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

サポートされる送信タイプは以下の通りです：
- `.Text(text: str, buttons: Optional[List] = None)`：テキストメッセージを送信します。
- `.Html(html: str, buttons: Optional[List] = None)`：HTML形式のメッセージを送信します。
- `.Markdown(markdown: str, buttons: Optional[List] = None)`：Markdown形式のメッセージを送信します。
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)`：画像メッセージを送信します。URL、ローカルパスまたはバイナリデータをサポートします。
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)`：動画メッセージを送信します。URL、ローカルパスまたはバイナリデータをサポートします。
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)`：音声メッセージを送信します。URL、ローカルパスまたはバイナリデータをサポートし、音声の長さを自動検出します。
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)`：`.Audio()` の別名です。
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)`：ファイルメッセージを送信します。URL、ローカルパスまたはバイナリデータをサポートします。
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)`：絵文字/ステッカーメッセージを送信します。ステッカーID、ステッカーURLまたはバイナリ画像データをサポートします。
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)`：A2UIメッセージ（メッセージタイプ14）を送信します。A2UI JSONデータはtextフィールドに埋め込まれて送信されます。
- `.Edit(msg_id: str, text: str, content_type: str = "text")`：既存のメッセージを編集します。
- `.Recall(msg_id: str)`：メッセージを撤回します。
- `.Raw_ob12(message: Union[List, Dict])`：OneBot12形式のメッセージを送信します。

### メディアファイル処理

すべてのメディアタイプ（画像、動画、音声、ファイル）は以下の入力方法をサポートしています：
- **URL**：`"https://example.com/image.jpg"` — 自動的にダウンロードしてアップロード
- **ローカルパス**：`"/path/to/file.jpg"` — 自動的に読み込んでアップロード
- **バイナリデータ**：`open("file.jpg", "rb").read()` — 直接アップロード

メディアファイルは自動的に七牛雲ストレージにアップロードされ、以下の特徴をサポートします：
- 自動的に `filetype` ライブラリを使ってファイルタイプとMIMEを検出します
- 自動的にファイルサイズを計算します
- 音声ファイルはMP3、MP4/M4A形式を自動的に検出します

### ボタンパラメータの説明

`buttons` パラメータは、ボタンのレイアウトと機能を示すネストされたリストです。各ボタンオブジェクトには以下のフィールドが含まれます：

| フィールド         | タイプ   | 必須 | 説明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | ボタン上の文字                                                         |
| `actionType` | int    | 是       | アクションタイプ：<br>`1`: URLにジャンプ<br>`2`: コピー<br>`3`: クリック報告            |
| `url`        | string | 否       | `actionType=1` の場合、ジャンプ先のURLとして使用されます                         |
| `value`      | string | 否       | `actionType=2` の場合、この値がクリップボードにコピーされます<br>`actionType=3` の場合、この値がサブスクライバに送信されます |

例：
```python
buttons = [
    [
        {"text": "コピー", "actionType": 2, "value": "xxxx"},
        {"text": "クリックしてジャンプ", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "イベントを報告", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("ボタン付きメッセージ")
```

### チェーン修飾メソッド（組み合わせて使用可能）

チェーン修飾メソッドは `self` を返すため、チェーンで呼び出すことができます。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定されたメッセージに返信します。
- `.At(user_id: str)`：指定されたユーザーを@します（テキスト形式の@user_id）。
- `.AtAll()`：全員を@します（偽@全員、@allテキストを送信）。
- `.Buttons(buttons: List)`：ボタンを追加します。

> **注意：** ユーザーアカウントは特殊であるため、管理者でなくても全員を@できますが、この `AtAll()` は単に全員を@するテキストを送信するだけです。これは偽@全員です。

### チェーン呼び出しの例

```python
# 基本的な送信
await yunhu_user.Send.To("user", user_id).Text("Hello")

# メッセージに返信
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("返信メッセージ")

# 返信 + ボタン
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("返信とボタン付きメッセージ")

# 指定アカウント + 返信 + ボタン
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("完全なチェーン呼び出し")
```

### OneBot12メッセージのサポート

アダプターはOneBot12形式のメッセージを送信することができ、クロスプラットフォームのメッセージ互換性を確保します：

- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します。

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# チェーン修飾と組み合わせて使用
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

Raw_ob12は、混合メッセージセグメントを自動的に処理します：
- `text`、`mention` などのタイプはグループにまとめられます
- `image`、`video`、`audio`、`file`、`face`、`markdown`、`html`、`a2ui` などのタイプはそれぞれ独立したグループになります
- `reply` などのタイプは、どのグループにも追加できます

## 送信メソッドの戻り値

すべての送信メソッドはTaskオブジェクトを返し、awaitで送信結果を取得できます。返り値はErisPulseアダプターの標準化された返り値規格に従います：

```python
{
    "status": "ok",           // 実行ステータス
    "retcode": 0,             // 返り値コード
    "data": {...},            // 応答データ
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "yunhu_user_raw": {...}   // 元の応答データ
}
```

## 特有のイベントタイプ

`platform == "yunhu_user"` で検証してから、このプラットフォームの特有の機能を使用する必要があります。

### 核心的な差異点

1. 特有のイベントタイプ：
    - スーパーファイル共有: `yunhu_user_file_send`
    - ロボット公告ボード: `yunhu_user_bot_board`
    - メッセージ編集通知: `message_edit`
    - メッセージ削除通知: `message_delete`（撤回）
2. 特有のメッセージセグメントタイプ:
    - フォームメッセージセグメント: `yunhu_user_form`
    - 記事メッセージセグメント: `yunhu_user_post`
    - ステッカー・メッセージセグメント: `yunhu_user_sticker`
    - ボタン・メッセージセグメント: `yunhu_user_button`
    - A2UI・メッセージセグメント: `a2ui`
3. 拡張フィールド:
    - すべての特有のフィールドは `yunhu_user_` で始まります
    - 元のデータは `yunhu_user_raw` フィールドに保存されます
    - 元のイベントタイプは `yunhu_user_raw_type` フィールドに記録されます
    - プライベートチャットでは `self.user_id` は現在のログインユーザーIDを示します

### 支援される元のイベントタイプ

| 元のイベントタイプ | OneBot12 タイプ | 説明 |
|-------------|--------------|------|
| `push_message` | `message` | メッセージ送信（プライベートチャット、グループチャット、Bot 会話） |
| `edit_message` | `notice` (`message_edit`) | メッセージ編集イベント |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | スーパーファイル共有イベント |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | ロボット公告ボードイベント |

> 他のイベントタイプ（`heartbeat_ack`、`draft_input`、`stream_message` など）は無視されます。

### OneBot12 でサポートされる detail_type

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
    """雲湖ユーザーのメッセージを処理する"""
    if event.get("platform") != "yunhu_user":
        return
    
    user_id = event.get("user_id", "")
    user_nickname = event.get("user_nickname", "")
    alt_message = event.get("alt_message", "")
    
    print(f"ユーザー {user_nickname}({user_id}): {alt_message}")
    
    # メッセージセグメント内の特有のタイプをチェック
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
            print(f"ボタンを含むメッセージ: {buttons}")
        
        elif seg_type == "a2ui":
            a2ui_data = segment["data"]["a2ui"]
            print(f"A2UIメッセージを受け取りました: {a2ui_data}")
    
    # event.reply() を使用して自動返信
    await event.reply(f"Echo: {alt_message}")

@notice.on_notice()
async def handle_yunhu_user_notice(event):
    """雲湖ユーザーの通知イベントを処理する"""
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
        print(f"ロボット {bot_name} が公告を投稿しました: {board_data.get('content', '')}")
```

## 拡張フィールドの説明

- すべての特有のフィールドは `yunhu_user_` で始まり、標準のフィールドとの衝突を避ける
- 元のデータは `yunhu_user_raw` フィールドに保存され、雲湖プラットフォームの完全な元のデータにアクセスできる
- 元のイベントタイプは `yunhu_user_raw_type` フィールドに記録される（例: `push_message`、`edit_message` など）
- `self.user_id` は現在のログインユーザーIDを示す（ログイン応答から取得）
- スーパーファイル共有は `yunhu_user_file_send` フィールドを通じてファイル共有データを提供する
- ロボット公告ボードは `yunhu_user_bot_board` フィールドを通じて公告データを提供する

### 特有のメッセージセグメントタイプ

#### フォームメッセージセグメント (yunhu_user_form)

content_type が 5 の場合、メッセージセグメントタイプは `yunhu_user_form` です：

```json
{
    "type": "yunhu_user_form",
    "data": {
        "form": "フォームデータ"
    }
}
```

#### 記事メッセージセグメント (yunhu_user_post)

content_type が 6 の場合、メッセージセグメントタイプは `yunhu_user_post` です：

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

| フィールド | タイプ | 説明 |
|------|------|------|
| `post_id` | string | 記事のユニークな識別子 |
| `post_title` | string | 記事のタイトル |
| `post_content` | string | 記事の内容 |

#### ステッカー・メッセージセグメント (yunhu_user_sticker)

content_type が 7 の場合、メッセージセグメントタイプは `yunhu_user_sticker` です：

```json
{
    "type": "yunhu_user_sticker",
    "data": {
        "file_id": "ステッカー画像のURL"
    }
}
```

| フィールド | タイプ | 説明 |
|------|------|------|
| `file_id` | string | ステッカー画像のURL |

#### ボタン・メッセージセグメント (yunhu_user_button)

メッセージにボタンが含まれる場合、`yunhu_user_button` メッセージセグメントが追加されます：

```json
{
    "type": "yunhu_user_button",
    "data": {
        "buttons": [[{"text": "ボタンの文字", "actionType": 3, "value": "値"}]]
    }
}
```

#### A2UI メッセージセグメント (a2ui)

content_type が 14 の場合、メッセージセグメントタイプは `a2ui` です：

```json
{
    "type": "a2ui",
    "data": {
        "a2ui": "A2UI JSONデータ"
    }
}
```

---

## マルチアカウントの設定

### 設定の説明

YunhuUserAdapter は複数のユーザーアカウントを同時に設定および実行することをサポートしています。

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # WebSocket再接続間隔（秒）
ws_timeout = 70             # WebSocketタイムアウト時間（秒）

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # ユーザーのメールアドレス（必須）
password = "password1"       # ユーザーのパスワード（必須）
platform = "windows"         # ログインプラットフォーム（オプション、デフォルトはwindows）
device_id = ""               # デバイスID（オプション、未設定の場合は自動生成）
enabled = true               # アカウントを有効にするかどうか（オプション、デフォルトはtrue）

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**設定項目の説明：**
- `email`：ユーザーのメールアドレス（必須）、雲湖プラットフォームにログインするために使用
- `password`：ユーザーのパスワード（必須）
- `platform`：ログインプラットフォームの識別子（オプション、デフォルトは `windows`）、有効値は `windows`、`macos`、`linux`、`ios`、`android`
- `device_id`：デバイスID（オプション、未設定の場合は自動生成）、固定値を設定してセッションの一貫性を保つことを推奨
- `enabled`：アカウントを有効にするかどうか（オプション、デフォルトは `true`）

**アダプターのレベルの設定：**
- `ws_reconnect_interval`：WebSocket再接続間隔（秒、デフォルトは30）
- `ws_timeout`：WebSocketタイムアウト時間（秒、デフォルトは70）

**重要な注意事項：**
1. アダプターはメールアドレスを使用してログインし、tokenを取得し、WebSocketを介してイベントを受信します
2. WebSocket接続が切断された場合、自動的に再接続され、最大3回まで再試行されます
3. 各アカウントに固定の `device_id` を設定することを推奨します。これにより、セッションの一貫性が保たれます
4. 未変更のテンプレートアカウント（デフォルトのメールアドレスとパスワード）は自動的にスキップされます

### Send DSL を使用してアカウントを指定する

`Using()` メソッドを使用して、どのアカウントを使ってメッセージを送信するかを指定することができます。このメソッドは2つのパラメータをサポートします：
- **アカウント名**：設定ファイルのアカウント名（例：`default`、`account2`）
- **user_id**：ログイン後に取得されるユーザーID

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# アカウント名を使ってメッセージを送信する
await yunhu_user.Send.Using("default").To("user", "user123").Text("Hello from account1!")

# user_idを使ってメッセージを送信する（自動的に対応するアカウントを検索）
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Hello from user!")

# 指定しない場合は、最初に有効なアカウントが使用されます
await yunhu_user.Send.To("user", "user123").Text("Hello from default account!")
```

> **ヒント：** `user_id` を使用する場合、システムは設定ファイルに一致するアカウントを自動的に検索します。これはイベントの返信を処理するときに特に便利です。`event["self"]["user_id"]` を使用して、同じアカウントで返信することができます。

### イベントにおけるアカウント識別

受信したイベントには自動的に対応するユーザーID情報が含まれています：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # 現在のログインユーザーIDを取得
        my_user_id = event["self"]["user_id"]
        print(f"メッセージはアカウント: {my_user_id} から来ています")
        
        # 同じアカウントを使ってメッセージを返信する
        yunhu_user = adapter.get("yunhu_user")
        await yunhu_user.Send.Using(my_user_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("返信メッセージ")
```

### ログ情報

アダプターはログに自動的にアカウント情報を含め、デバッグや追跡に役立ちます：

```
[INFO] アカウント default (user1@example.com) にログイン成功、ユーザーID: 12345678
[INFO] アカウント default のWebSocket監視タスクが起動しました
[INFO] アカウント account2 (user2@example.com) にログイン成功、ユーザーID: 87654321
```

### 管理インターフェース

```python
# すべてのアカウント情報を取得する
accounts = yunhu_user.accounts
# 戻り値形式: {"default": {"name": "default", "email": "...", "token": "...", "user_id": "...", ...}, ...}

# アカウントが有効かどうかをチェックする
for account_name, account_config in yunhu_user._account_configs.items():
    print(f"{account_name}: enabled={account_config.enabled}")

# アカウント名からHTTPクライアントを取得する
http_client = yunhu_user._get_http_client("default")

# user_idからアカウントを検索する
account_name = yunhu_user._get_account_by_user_id("12345678")
```

## APIの呼び出し

アダプターは `call_api` メソッドを提供し、プラットフォームのAPIを直接呼び出すことができます：

```python
# メッセージを送信する
result = await yunhu_user.call_api("/send", 
    target_type="group", 
    target_id="group_id",
    account_id="default",
    message={"text": "Hello", "msg_type": 1}
)

# メッセージを編集する
result = await yunhu_user.call_api("/edit",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id",
    text="新しい内容",
    content_type="text"
)

# メッセージを撤回する
result = await yunhu_user.call_api("/recall",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id"
)

# メッセージを一括撤回する
result = await yunhu_user.call_api("/recall_batch",
    target_type="group",
    target_id="group_id",
    msg_id_list=["msg_id_1", "msg_id_2"]
)

# メッセージ一覧を取得する
result = await yunhu_user.call_api("/list",
    chat_id="group_id",
    chat_type=2,
    msg_count=10,
    msg_id=""
)

# メッセージ編集履歴を取得する
result = await yunhu_user.call_api("/list_edit_record",
    msg_id="msg_id",
    size=10,
    page=1
)

# ボタンイベント報告
result = await yunhu_user.call_api("/button_report",
    chat_id="group_id",
    chat_type=2,
    msg_id="msg_id",
    user_id="user_id",
    button_value="button_value"
)
```

**サポートされているAPIエンドポイント：**

| エンドポイント | 説明 |
|------|------|
| `/send` | メッセージを送信する |
| `/edit` | メッセージを編集する |
| `/recall` | メッセージを撤回する |
| `/recall_batch` | メッセージを一括撤回する |
| `/list` | メッセージ一覧を取得する |
| `/list_by_seq` | シーケンスでメッセージを取得する |
| `/list_by_mid_seq` | メッセージIDとシーケンスでメッセージを取得する |
| `/list_edit_record` | メッセージ編集履歴を取得する |
| `/button_report` | ボタンイベント報告を送信する |