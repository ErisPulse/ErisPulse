# 云湖用户平台特性文档

YunhuUserAdapter は、云湖用户账户协议に基づき構築されたアダプタです。ユーザーのメールアドレスアカウントを使用してログインし、WebSocket を介してイベントを受信し、一貫したイベント処理とメッセージ操作のインターフェースを提供します。

---

## 文書情報

- 対応モジュールバージョン: 4.6.1
- 維持者: wsu2059
- 最終更新: 2026-11-10

## 基本情報

- プラットフォーム概要：云湖（Yunhu）は企業向けのリアルタイムコミュニケーションプラットフォームです。本アダプタは**ユーザーアカウント**（ロボットアカウントではなく）を使用して対話します。
- アダプタ名: YunhuUserAdapter
- 複数アカウント対応: アカウント名で識別可能な複数のユーザーアカウントを設定できます。
- チェーン修飾子対応: `.Reply()` などのチェーン修飾子メソッドをサポート。
- OneBot12互換: OneBot12形式のメッセージ送信をサポート。
- 通信方式: メールアドレスでログインし、token を取得し、WebSocket を使用してイベントを受信し、HTTP + Protobuf 協定でメッセージを送信。
- 会話タイプ: プライベートチャット（user）、グループチャット（group）、ロボット会話（chat_type=3、4.6.1から `private` にマッピング）をサポート。

## v5 ファンタム更新（4.2.0）

- **BaseConverter 継承**；**spawn_background タスクの所属**（WS 監視タスク）
- **ユーザーAPI全集**（yhchatAPI full.proto / v1 エンドポイント、protobuf over HTTP を使用）：
  - ユーザー：get_user / edit_nickname / edit_avatar
  - 友人：アドレスブック / 申請リスト / 申請 / 承認 / 無視 / 削除
  - グループ：グループ情報 / メンバー一覧 / 作成 / 解散 / 招待 / 除外 / 禁言 / ロボット一覧
  - 会話：会話一覧；メッセージ：一覧 / 撤回 / ボタン報告
- **フレームワークソフト依存**：ErisPulse>=2.7.1 の実行時検出と警告表示；起動時にバージョンログを出力

## 対応プラットフォーム機能リスト

### イベント受信（WebSocket、protobuf エンコード）

| WS cmd | イベント | 説明 |
|--------|--------|------|
| `push_message` | `message` | プライベートチャット/グループ/Bot 会話メッセージ（テキスト/HTML/Markdown/画像/動画/音声/ファイル/絵文字/フォーム/記事/ステッカー/ボタン/A2UI） |
| `edit_message` | `notice` (`message_edit`) | メッセージ編集通知 |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | スーパーファイル共有 |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | ロボット公告ボード |

### Api DSL メソッド対照表（ YunhuHTTPClient → ユーザーAPI v1 エンドポイント ）

| 分類 | Api メソッド | エンドポイント | 説明 |
|------|-------------|---------------|------|
| アカウント | `get_self_info()` | `/user/info` | ログインユーザー情報（ニックネーム/プロフィール画像/user_id） |
| ユーザー | `get_user(user_id)` | `/user/get-user` | ユーザーの詳細情報 |
| ユーザー | `edit_nickname(nickname)` | `/user/edit-nickname` | 自分のニックネームを変更 |
| ユーザー | `edit_avatar(url)` | `/user/edit-avatar` | 自分のプロフィール画像を変更 |
| 友人 | `get_friend_address_book(md5)` | `/friend/address-book-list` | アドレスブック（カーソル付きページング） |
| 友人 | `get_friend_requests()` | `/friend/request-list` | 友人/グループ参加申請リスト |
| 友人 | `friend_apply(user_id, desc)` | `/friend/apply` | 友人追加申請 |
| 友人 | `friend_agree_apply(user_id)` | `/friend/agree-apply` | 友人申請を承認 |
| 友人 | `friend_ignore_apply(user_id)` | `/friend/ignore-apply` | 友人申請を無視 |
| 友人 | `friend_delete(user_id)` | `/friend/delete-friend` | 友人を削除 |
| グループ | `get_group_info(group_id)` | `/group/info` | グループ情報 |
| グループ | `get_group_member_list(group_id)` | `/group/list-member` | グループメンバー一覧（キーワード検索対応） |
| グループ | `create_group(name, ...)` | `/group/create-group` | グループ作成 |
| グループ | `dismiss_group(group_id)` | `/group/dismiss-group` | グループ解散 |
| グループ | `group_invite(group_id, user_ids)` | `/group/invite` | グループに招待 |
| グループ | `group_remove_member(group_id, user_id)` | `/group/remove-member` | グループメンバーを除外 |
| グループ | `group_gag_member(group_id, user_id, 秒)` | `/group/gag-member` | グループメンバーを一時停止（0=解除） |
| グループ | `get_group_bot_list(group_id)` | `/group/bot-list` | グループ内のロボット一覧 |
| 会話 | `get_conversation_list(md5)` | `/conversation/list` | 会話一覧（カーソル付きページング） |
| メッセージ | `get_message_list(chat_id, chat_type, ...)` | `/msg/list-message` | メッセージ一覧（HTTP クライアントのページング変体参照） |
| メッセージ | `delete_message(msg_id, chat_id, chat_type)` | `/msg/recall-msg` | メッセージ撤回（バッチ撤回は HTTP クライアント参照） |
| メッセージ | `button_report(...)` | `/msg/button-report` | ボタンクリック報告 |
| メタアクション | `get_status` / `get_version` / `get_supported_actions` | - | 実行状態/バージョン/サポートアクション |

### 未対応（エンドポイントは既知、full.proto メッセージは完全、必要に応じて拡張可能）

- ユーザー：認証コードログイン、バッジ、金豆記録、電話番号/メールアドレスの紐付け、通知設定、ユーザーデータの保存と取得
- 友人：ノーノイズ（no-notify）、申請記録の削除
- グループ：コマンドリスト、分類、おすすめ、ライブ配信、グループ情報/グループニックネーム/キーワードの編集、グループ参加の自動承認、グループファイル制限、イベント SSE
- 会話：固定/並べ替え/削除、ノーノイズ
- メッセージ：転送、A2UIの提出、メッセージ一覧の画像取得、ファイルのダウンロード記録
- グループタグ：list / relate / relate-cancel / create / edit / delete / members（エンドポイント `/group-tag/*`）

> 拡張方法：`YunhuHTTPClient` に既存のパターンに従ってメソッドを追加する（`_proto_request` / `_json_request` は共通のラッパー）、`Api` クラスで公開するだけ。エンドポイントとメッセージ定義は `yhchatAPI/src/api/v1/*.md` と `yhchatAPI/src/full.proto` を参照。

### ユーザーAPIの例

```python
from ErisPulse import sdk
yunhu_user = sdk.adapter.get("yunhu_user")

result = await yunhu_user.Api.get_self_info()
result = await yunhu_user.Api.get_friend_requests()          # 友人申請リスト
await yunhu_user.Api.friend_agree_apply(user_id)             # 友人申請を承認
result = await yunhu_user.Api.get_group_member_list(group_id)
result = await yunhu_user.Api.get_conversation_list()        # 会話リスト
await yunhu_user.Api.delete_message(msg_id, chat_id, chat_type)  # 撤回
```

## 友人申請処理（4.6.0 新規追加）

云湖ユーザーのWebSocketは**友人申請イベントをプッシュしません**。アダプタはデフォルトで申請リストをポーリングし、標準リクエストイベントに合成します（[リクエスト操作規範](../standards/request-action-spec.md)に従います）：

- **アカウント設定**：`poll_friend_requests = true`（デフォルトで有効）、`poll_interval = 60`（ポーリング間隔秒、最小5秒）；`false`に設定するとポーリングを無効にできます
- **ポーリングロジック**：`/friend/request-list`を間隔で取得し、**新規申請**を差分で合成し、標準リクエストイベントに変換します：
  - `type="request"`、`detail_type="friend"`
  - `request_id` = **申請者の user_id**
  - `user_nickname` / `comment` は申請資料から取得し、元の項目は `yunhu_user_raw` に保持されます
- **イベントの重複除去**：処理済みの申請は重複してイベントを生成しません

### モジュール側の承認（イベント方式）

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    if event.get("platform") != "yunhu_user":
        return

    applicant = event.get("user_id")
    nickname = event.get("user_nickname", "")
    comment = event.get("comment", "")
    print(f"友人申請: {nickname}({applicant}) 附言: {comment}")

    # 友人申請を承認（accept = 友人追加）
    await event.approve()
    # または申請を無視（reject = 無視）
    # await event.reject()
```

### 直接アダプタを呼び出す（Request DSL）

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# request_id は申請者の user_id
await yunhu_user.Request("申请人user_id").accept()   # accept = 友人追加
await yunhu_user.Request("申请人user_id").reject()   # reject = 無視

# 複数アカウント：アカウントを指定して承認
await yunhu_user.Request("申请人user_id").Using("default").accept()
```

> `accept()` は内部で `/friend/agree-apply` を呼び出し、`reject()` は `/friend/ignore-apply` を呼び出します。両方とも `status` / `retcode` / `message` / `yunhu_user_raw` の標準レスポンスを返します。

## 標準化の一致（4.6.1）

レスポンス構造とエラーコードは[APIレスポンス規格](../standards/api-response.md)に従います。

### 標準レスポンス

Api DSL 20のメソッドはすべて、`status` / `retcode` / `data` / `message_id` / `message` の標準レスポンスを返します。プラットフォームの元のデータは `data` と `yunhu_user_raw` に含まれます。`get_self_info` の元のデータはレスポンスの最上位に移動されます。

### エラーコード規格

| retcode | 含義 | 说明 |
|---------|------|------|
| 0 | 成功 | — |
| 33001 | 網絡エラー | HTTP/WS接続エラー |
| 34100 | プラットフォーム失敗 | 云湖ユーザー端末が失敗した；元のレスポンスは `yunhu_user_raw` に保持されます |
| 10002 | 不支持 | プラットフォームが対応する標準アクションをサポートしていません |
| 10003 | パラメータエラー | request_id、利用可能なアカウントが不足しています |

### イベントフィールド修正

- **`chat_type=3`（ロボット会話）は `private` にマッピング**（元の `"bot"` は非標準受信タイプ；元の chat_type は `yunhu_user_raw` に保持されます）
- **`edit_message` イベントの id に `edit:` プレフィックスを追加**：create イベントと同じ id で下流の重複除去処理に飲み込まれないようにします
- **`message_id` は常に存在します**：存在しない場合は空文字列で補填します
- **イベント `time` はメッセージ自身のタイムスタンプを使用**（秒単位）、アダプタ処理時刻を一律に使用しません

### アカウントと複数アカウント

- `call_api` は `account_id`（標準名）/ `_account_id`（旧名）の両方のアカウントフィールドをサポートし、フレームワーク ApiDSL（`Api.Using(...)`）は自動的に適応します
- `Send` は `send_context`（イベントアカウントのバックアップ）を読み取ります：イベントコンテキストから `Send` を呼び出す場合、デフォルトで元のアカウントにフォールバックします
- イベントの返信は `event.reply()` を直接使用することを推奨し、受理アカウントに自動ルーティングされます

---

## 対応するメッセージ送信タイプ

すべての送信メソッドはチェーン式構文で実現されます。例えば：
```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

対応する送信タイプは以下の通りです：
- `.Text(text: str, buttons: Optional[List] = None)`：テキストメッセージを送信します。
- `.Html(html: str, buttons: Optional[List] = None)`：HTML形式のメッセージを送信します。
- `.Markdown(markdown: str, buttons: Optional[List] = None)`：Markdown形式のメッセージを送信します。
- `.MergeForward(nodes, title="合併チャット記録")`：合併転送メッセージを送信します（`<details>`折りたたみHTMLカードとしてレンダリングされ、msg_type=8 HTMLチャネルで送信されます）。
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)`：画像メッセージを送信します。URL、ローカルパス、またはバイナリデータをサポートします。
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)`：動画メッセージを送信します。URL、ローカルパス、またはバイナリデータをサポートします。
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)`：音声メッセージを送信します。URL、ローカルパス、またはバイナリデータをサポートし、自動的に音声長を検出します。
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)`：`.Audio()`の別名です。
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)`：ファイルメッセージを送信します。URL、ローカルパス、またはバイナリデータをサポートします。
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)`：絵文字/ステッカーメッセージを送信します。ステッカーID、ステッカーURL、またはバイナリ画像データをサポートします。
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)`：A2UIメッセージを送信します（msg_type=14）。A2UI JSONデータはtextフィールドに埋め込まれて送信されます。
- `.Edit(msg_id: str, text: str, content_type: str = "text")`：既存のメッセージを編集します。
- `.Recall(msg_id: str)`：メッセージを撤回します。
- `.Raw_ob12(message: Union[List, Dict])`：OneBot12形式のメッセージを送信します。

### メディアファイル処理

すべてのメディアタイプ（画像、動画、音声、ファイル）は以下の入力方式をサポートします：
- **URL**：`"https://example.com/image.jpg"` — 自動的にダウンロードしてアップロードします
- **ローカルパス**：`"/path/to/file.jpg"` — 自動的に読み取ってアップロードします
- **バイナリデータ**：`open("file.jpg", "rb").read()` — 直接アップロードします

メディアファイルは自動的に七牛云ストレージにアップロードされ、以下の特徴を備えています：
- 自動的に `filetype` ライブラリを使用してファイルタイプとMIMEを検出します
- 自動的にファイルサイズを計算します
- 音声ファイルはMP3、MP4/M4A形式を自動的に検出します

### ボタンパラメータの説明

`buttons` パラメータは、ボタンのレイアウトと機能を示すネストされたリストです。各ボタンオブジェクトには以下のフィールドがあります：

| フィールド         | タイプ   | 必須 | 説明                                                                 |
|--------------------|----------|------|----------------------------------------------------------------------|
| `text`             | string   | はい | ボタンのテキスト                                                     |
| `actionType`       | int      | はい | アクションタイプ：<br>`1`: URLに移動<br>`2`: コピー<br>`3`: クリック報告 |
| `url`              | string   | いいえ | `actionType=1` の場合、移動先のURLを使用します                         |
| `value`            | string   | いいえ | `actionType=2` の場合、この値がクリップボードにコピーされます<br>`actionType=3` の場合、この値がサブスクライバーに送信されます |

例：
```python
buttons = [
    [
        {"text": "コピー", "actionType": 2, "value": "xxxx"},
        {"text": "クリックして移動", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "イベントを報告", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("ボタン付きメッセージ")
```

### チェーン修飾子メソッド（組み合わせて使用可能）

チェーン修飾子メソッドは `self` を返し、チェーン呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定されたメッセージに返信します。
- `.At(user_id: str)`：指定されたユーザーを@します（テキスト形式 @user_id）。
- `.AtAll()`：全員を@します（偽@全員、@all テキストを送信します）。
- `.Buttons(buttons: List)`：ボタンを追加します。

> **注意：** ユーザーアカウントは特別なため、管理者でなくても全員を@できますが、`AtAll()` は@全員のテキストを送信するだけです。

### チェーン呼び出しの例

```python
# 基本的な送信
await yunhu_user.Send.To("user", user_id).Text("Hello")

# メッセージへの返信
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("返信メッセージ")

# 返信 + ボタン
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("返信とボタン付きメッセージ")

# 指定アカウント + 返信 + ボタン
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("完全なチェーン呼び出し")
```

### OneBot12メッセージのサポート

アダプタはOneBot12形式のメッセージを送信することをサポートし、クロスプラットフォームのメッセージ互換性を確保します：

- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します。

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# チェーン修飾子と組み合わせて使用
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

Raw_ob12 は混合メッセージセグメントを自動的にグループ処理します：
- `text`、`mention` タイプは1グループに結合されます
- `image`、`video`、`audio`、`file`、`face`、`markdown`、`html`、`a2ui` などのタイプはそれぞれ独立したグループになります
- `reply` タイプは任意のグループに追加できます

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、await で送信結果を取得できます。返り値は ErisPulse アダプタの標準化された返り値規格に従います：

```python
{
    "status": "ok",           // 実行状態
    "retcode": 0,             // 返り値コード
    "data": {...},            // 返り値データ
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "yunhu_user_raw": {...}   // 元の返り値データ
}
```

## 特有のイベントタイプ

`platform == "yunhu_user"` の検証が必要です。

### 核心的な違い

1. 特有のイベントタイプ：
    - スーパーファイル共有: `yunhu_user_file_send`
    - ロボット公告ボード: `yunhu_user_bot_board`
    - メッセージ編集通知: `message_edit`
    - メッセージ削除通知: `message_delete`（撤回）
2. 特有のメッセージセグメントタイプ：
    - フォームメッセージセグメント: `yunhu_user_form`
    - 記事メッセージセグメント: `yunhu_user_post`
    - ステッカーメッセージセグメント: `yunhu_user_sticker`
    - ボタンメッセージセグメント: `yunhu_user_button`
    - A2UI メッセージセグメント: `a2ui`
3. 拡張フィールド：
    - すべての特有フィールドは `yunhu_user_` プレフィックスで識別されます
    - 元のデータは `yunhu_user_raw` フィールドに保持されます
    - 元のイベントタイプは `yunhu_user_raw_type` フィールドに記録されます
    - プライベートチャットでは `self.user_id` は現在のログインユーザーIDを示します

### 対応する元のイベントタイプ

| 元のイベントタイプ | OneBot12 タイプ | 説明 |
|------------------|----------------|------|
| `push_message`   | `message`      | メッセージのプッシュ（プライベートチャット、グループチャット、Bot 会話） |
| `edit_message`   | `notice` (`message_edit`) | メッセージ編集イベント |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | スーパーファイル共有イベント |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | ロボット公告ボードイベント |

> 他のイベントタイプ（`heartbeat_ack`、`draft_input`、`stream_message` など）は無視されます。

### OneBot12 がサポートする detail_type

| OneBot12 detail_type | 云湖 chat_type | 説明 |
|---------------------|---------------|------|
| `private`           | 1             | プライベートメッセージ |
| `group`             | 2             | グループメッセージ |
| `private`           | 3             | ロボット会話（4.6.1から `private` にマッピング、元の `"bot"` は非標準；元の chat_type は `yunhu_user_raw` に保持されます） |

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
    """云湖用户消息处理"""
    if event.get("platform") != "yunhu_user":
        return
    
    user_id = event.get("user_id", "")
    user_nickname = event.get("user_nickname", "")
    alt_message = event.get("alt_message", "")
    
    print(f"用户 {user_nickname}({user_id}): {alt_message}")
    
    # 检查消息段中的特有类型
    for segment in event.get("message", []):
        seg_type = segment.get("type", "")
        
        if seg_type == "yunhu_user_form":
            form_data = segment["data"]["form"]
            print(f"收到表单消息: {form_data}")
        
        elif seg_type == "yunhu_user_post":
            post_data = segment["data"]
            print(f"收到文章消息: {post_data.get('post_title', '')}")
        
        elif seg_type == "yunhu_user_sticker":
            sticker_url = segment["data"]["file_id"]
            print(f"收到贴纸消息: {sticker_url}")
        
        elif seg_type == "yunhu_user_button":
            buttons = segment["data"]["buttons"]
            print(f"消息包含按钮: {buttons}")
        
        elif seg_type == "a2ui":
            a2ui_data = segment["data"]["a2ui"]
            print(f"收到A2UI消息: {a2ui_data}")
    
    # 使用 event.reply() 自动回复
    await event.reply(f"Echo: {alt_message}")

@notice.on_notice()
async def handle_yunhu_user_notice(event):
    """云湖用户通知事件处理"""
    if event.get("platform") != "yunhu_user":
        return
    
    detail_type = event.get("detail_type", "")
    
    if detail_type == "message_edit":
        message_id = event.get("message_id", "")
        user_nickname = event.get("user_nickname", "")
        edit_time = event.get("edit_time", 0)
        print(f"用户 {user_nickname} 编辑了消息 {message_id}")
    
    elif detail_type == "yunhu_user_file_send":
        file_data = event.get("yunhu_user_file_send", {})
        print(f"收到超级文件分享: {file_data}")
    
    elif detail_type == "yunhu_user_bot_board":
        board_data = event.get("yunhu_user_bot_board", {})
        bot_name = event.get("bot_name", "")
        print(f"机器人 {bot_name} 发布了公告: {board_data.get('content', '')}")
```

## 拡張フィールドの説明

- すべての特有フィールドは `yunhu_user_` プレフィックスで識別し、標準フィールドとの衝突を避ける
- 元のデータは `yunhu_user_raw` フィールドに保持し、云湖プラットフォームの完全な元のデータにアクセスできる
- 元のイベントタイプは `yunhu_user_raw_type` フィールドに記録する（例: `push_message`、`edit_message` など）
- `self.user_id` は現在のログインユーザーIDを示す（ログイン応答から取得）
- スーパーファイル共有は `yunhu_user_file_send` フィールドでファイル共有データを提供
- ロボット公告ボードは `yunhu_user_bot_board` フィールドで公告データを提供

### 特有メッセージセグメントタイプ

#### 表形式メッセージセグメント (yunhu_user_form)

content_type が 5 の場合、メッセージセグメントタイプは `yunhu_user_form` です：

```json
{
    "type": "yunhu_user_form",
    "data": {
        "form": "表单数据"
    }
}
```

#### 記事形式メッセージセグメント (yunhu_user_post)

content_type が 6 の場合、メッセージセグメントタイプは `yunhu_user_post` です：

```json
{
    "type": "yunhu_user_post",
    "data": {
        "post_id": "文章ID",
        "post_title": "文章标题",
        "post_content": "文章内容"
    }
}
```

| フィールド | タイプ | 説明 |
|----------|--------|------|
| `post_id` | string | 文章唯一标识 |
| `post_title` | string | 文章标题 |
| `post_content` | string | 文章内容 |

#### ステッカー形式メッセージセグメント (yunhu_user_sticker)

content_type が 7 の場合、メッセージセグメントタイプは `yunhu_user_sticker` です：

```json
{
    "type": "yunhu_user_sticker",
    "data": {
        "file_id": "贴纸图片URL"
    }
}
```

| フィールド | タイプ | 説明 |
|----------|--------|------|
| `file_id` | string | 贴纸图片URL |

#### ボタン形式メッセージセグメント (yunhu_user_button)

メッセージにボタンが含まれる場合、`yunhu_user_button` メッセージセグメントが追加されます：

```json
{
    "type": "yunhu_user_button",
    "data": {
        "buttons": [[{"text": "按钮文字", "actionType": 3, "value": "值"}]]
    }
}
```

#### A2UI 形式メッセージセグメント (a2ui)

content_type が 14 の場合、メッセージセグメントタイプは `a2ui` です：

```json
{
    "type": "a2ui",
    "data": {
        "a2ui": "A2UI JSON数据"
    }
}
```

---

## 複数アカウントの設定

### 設定の説明

YunhuUserAdapter は複数のユーザーアカウントを同時に設定・実行できます。

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # WebSocket再接続間隔（秒）
ws_timeout = 70             # WebSocketタイムアウト時間（秒）

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # ユーザーのメールアドレス（必須）
password = "password1"       # ユーザーのパスワード（必須）
platform = "windows"         # ログインプラットフォーム（オプション、デフォルトはwindows）
device_id = ""               # デバイスID（オプション、未設定時は自動生成）
poll_friend_requests = true  # 友人申請のポーリング（オプション、デフォルトはtrue）
poll_interval = 60           # 友人申請ポーリング間隔（秒、オプション、デフォルトは60、最小5）
enabled = true               # 有効にするかどうか（オプション、デフォルトはtrue）

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**設定項目の説明：**
- `email`：ユーザーのメールアドレス（必須）、云湖プラットフォームにログインするため
- `password`：ユーザーのパスワード（必須）
- `platform`：ログインプラットフォームの識別子（オプション、デフォルトは `windows`）、選択肢：`windows`、`macos`、`linux`、`ios`、`android`
- `device_id`：デバイドID（オプション、未設定時は自動生成）、セッションの一貫性を保つために固定値を設定することを推奨
- `poll_friend_requests`：友人申請のポーリングを行うかどうか（オプション、デフォルトは `true`；「友人申請処理」参照）
- `poll_interval`：友人申請ポーリング間隔（秒、オプション、デフォルトは60、最小5）
- `enabled`：アカウントを有効にするかどうか（オプション、デフォルトは `true`）

**アダプタレベルの設定：**
- `ws_reconnect_interval`：WebSocketの再接続間隔（秒、デフォルトは30）
- `ws_timeout`：WebSocketのタイムアウト時間（秒、デフォルトは70）

**重要な注意点：**
1. アダプタはメールアドレスでログインし、token を取得し、WebSocket を使用してイベントを受信します
2. WebSocket接続が切断された場合、最大3回まで自動的に再接続します
3. 各アカウントに固定の `device_id` を設定することを推奨します。これによりセッションの一貫性が保たれます
4. デフォルトのアカウント（デフォルトのメールアドレスとパスワード）は自動的にスキップされます

### Using() メソッドでアカウントを指定して Send DSL を使用する

`Using()` メソッドを使用して、どのアカウントを使ってメッセージを送信するかを指定できます。このメソッドは2種類のパラメータを受け付けます：
- **アカウント名**：設定ファイル中のアカウント名（例：`default`、`account2`）
- **user_id**：ログイン後に取得されるユーザーID

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# アカウント名を使ってメッセージを送信
await yunhu_user.Send.Using("default").To("user", "user123").Text("Hello from account1!")

# user_idを使ってメッセージを送信（対応するアカウントを自動的に検索）
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Hello from user!")

# 指定しない場合は最初に有効なアカウントが使用されます
await yunhu_user.Send.To("user", "user123").Text("Hello from default account!")
```

> **注意：** `user_id` を使用する場合、システムは設定ファイルに一致するアカウントを自動的に検索します。これはイベント返信時に特に便利です。`event["self"]["user_id"]` を使用して同じアカウントで返信できます。

### イベント内のアカウント識別子

受信したイベントには自動的に対応するユーザーID情報が含まれます：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # 現在のログインユーザーIDを取得
        my_user_id = event["self"]["user_id"]
        print(f"メッセージはアカウント: {my_user_id} から来ています")
        
        # 同じアカウントで返信メッセージを送信
        yunhu_user = adapter.get("yunhu_user")
        await yunhu_user.Send.Using(my_user_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("返信メッセージ")
```

### ログ情報

アダプタはログに自動的にアカウント情報を含め、デバッグや追跡に便利です：

```
[INFO] 账户 default (user1@example.com) 登录成功，用户ID: 12345678
[INFO] 账户 default WebSocket 监听任务已启动
[INFO] 账户 account2 (user2@example.com) 登录成功，用户ID: 87654321
```

### 管理インターフェース

```python
# すべてのアカウント情報を取得
accounts = yunhu_user.accounts
# 戻り値形式: {"default": {"name": "default", "email": "...", "token": "...", "user_id": "...", ...}, ...}

# アカウントが有効かどうかを確認
for account_name, account_config in yunhu_user._account_configs.items():
    print(f"{account_name}: enabled={account_config.enabled}")

# アカウント名からHTTPクライアントを取得
http_client = yunhu_user._get_http_client("default")

# user_idからアカウントを検索
account_name = yunhu_user._get_account_by_user_id("12345678")
```

## API 呼び出し

アダプタは `call_api` メソッドを提供し、プラットフォームAPIを直接呼び出すことができます：

```python
# メッセージ送信
result = await yunhu_user.call_api("/send", 
    target_type="group", 
    target_id="group_id",
    account_id="default",
    message={"text": "Hello", "msg_type": 1}
)

# メッセージ編集
result = await yunhu_user.call_api("/edit",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id",
    text="新内容",
    content_type="text"
)

# メッセージ撤回
result = await yunhu_user.call_api("/recall",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id"
)

# メッセージ一括撤回
result = await yunhu_user.call_api("/recall_batch",
    target_type="group",
    target_id="group_id",
    msg_id_list=["msg_id_1", "msg_id_2"]
)

# メッセージ一覧取得
result = await yunhu_user.call_api("/list",
    chat_id="group_id",
    chat_type=2,
    msg_count=10,
    msg_id=""
)

# メッセージ編集記録取得
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

**サポートされるAPIエンドポイント：**

| エンドポイント | 説明 |
|----------------|------|
| `/send`        | メッセージ送信 |
| `/edit`        | メッセージ編集 |
| `/recall`      | メッセージ撤回 |
| `/recall_batch`| メッセージ一括撤回 |
| `/list`        | メッセージ一覧取得 |
| `/list_by_seq` | シーケンスによるメッセージ取得 |
| `/list_by_mid_seq` | メッセージIDとシーケンスによるメッセージ取得 |
| `/list_edit_record` | メッセージ編集記録取得 |
| `/button_report` | ボタンイベント報告 |