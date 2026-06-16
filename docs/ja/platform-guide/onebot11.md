# OneBot11プラットフォーム特性ドキュメント

OneBot11Adapter は OneBot V11 プロトコルに基づいて構築されたアダプターです。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.0.0
- メンテナー: ErisPulse

## 基本情報

- プラットフォーム概要：OneBot はチャットボットアプリケーションインターフェース標準です
- アダプター名：OneBotAdapter
- サポートするプロトコル/APIバージョン：OneBot V11
- 複数アカウントサポート：デフォルトで複数アカウントアーキテクチャを採用し、複数のOneBotアカウントの同時設定と実行をサポートします
- 設定キー名：`OneBotAdapter`

## サポートするメッセージ送信タイプ

すべての送信メソッドはメソッドチェーン構文によって実装されています。例：
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# デフォルトアカウントで送信
await onebot.Send.To("group", group_id).Text("Hello World!")

# 特定のアカウントを指定して送信
await onebot.Send.Using("main").To("group", group_id).Text("主アカウントからのメッセージ")

# 链式修饰：@用户 + 回复
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("回复消息")

# @全体成员
await onebot.Send.To("group", group_id).AtAll().Text("公告消息")
```

### 基本送信メソッド

- `.Text(text: str)`：プレーンテキストメッセージを送信します。
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：画像を送信します（URL、Base64、またはbytesをサポート）。
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`：音声メッセージを送信します。
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：動画メッセージを送信します。
- `.Face(id: Union[str, int])`：QQのスタンプ/顔文字を送信します。
- `.File(file: Union[str, bytes], filename: str = "file.dat")`：ファイルを送信します（タイプを自動判定）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します（自動的にOB11に変換）。
- `.Recall(message_id: Union[str, int])`：メッセージを取り消します。

### 群操作メソッド

以下のメソッドは `To("group", group_id)` を使用して対象のグループを指定し、グループコンテキストで実行する必要があります：

- `.Kick(user_id, reject_add_request=False)`：グループメンバーをキックします。
- `.Ban(user_id, duration=1800)`：グループメンバーを禁止します（秒単位、0は解禁）。
- `.WholeBan(enable=True)`：全員禁止を有効/無効にします。
- `.SetAdmin(user_id, enable=True)`：グループ管理者を設定/解除します。
- `.SetCard(user_id, card="")`：グループ名前を設定します。
- `.SetGroupName(name)`：グループ名を変更します。
- `.Leave(is_dismiss=False)`：グループから退会します（グループオーナーは解散も可能です）。
- `.SetTitle(user_id, title="")`：グループタイトルを設定します。
- `.SetPortrait(file)`：グループアイコンを設定します。

### 検索メソッド

- `.GetMsg(message_id)`：メッセージ内容を取得します。
- `.GetForwardMsg(id)`：転送メッセージを取得します。
- `.GetLoginInfo()`：現在のログイン情報（BotのQQ番号）を取得します。
- `.GetFriendList()`：友達リストを取得します。
- `.GetGroupInfo()`：グループ情報を取得します（`To("group", group_id)`が必要）。
- `.GetGroupList()`：グループリストを取得します。
- `.GetGroupMemberInfo(user_id)`：グループメンバー情報を取得します（`To("group", group_id)`が必要）。
- `.GetGroupMemberList()`：グループメンバーのリストを取得します（`To("group", group_id)`が必要）。

### 友達操作メソッド

- `.Like(user_id, times=1)`：友達にいいねを送信します（最大10回）。

### メソッドチェーン修飾メソッド（組み合わせ可能）

メソッドチェーン修飾メソッドは `self` を返し、メソッドチェーン呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります：

- `.At(user_id: Union[str, int], name: str = None)`：指定したユーザーにメンションします（複数回呼び出し可能）。
- `.AtAll()`：全員にメンションします。
- `.Reply(message_id: Union[str, int])`：指定したメッセージに返信します。

### メソッドチェーン呼び出しの例

```python
# 基本送信
await onebot.Send.To("group", 123456).Text("Hello")

# @单个用户
await onebot.Send.To("group", 123456).At(789012).Text("你好")

# @多个用户
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("大家好")

# 发送 OneBot12 格式消息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)

# 点赞
await onebot.Send.Like(123456, times=10)

# 禁言群成员
await onebot.Send.To("group", 123456).Ban(789012, duration=3600)

# 解禁
await onebot.Send.To("group", 123456).Ban(789012, duration=0)

# 踢人
await onebot.Send.To("group", 123456).Kick(789012)

# 设置群管理员
await onebot.Send.To("group", 123456).SetAdmin(789012)

# 修改群名
await onebot.Send.To("group", 123456).SetGroupName("新群名")

# 获取群信息
result = await onebot.Send.To("group", 123456).GetGroupInfo()

# 指定账户操作
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### サポートされていないタイプの処理

未定義の送信メソッドが呼び出された場合、アダプターはテキストプロンプトを返します：
```python
# 存在しないメソッドを呼び出し
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# 実際の送信: "[サポートされていない送信タイプ] メソッド名: SomeUnsupportedMethod, パラメータ: [...]"
```

## 要求操作（Request DSL）

アダプターは要求操作DSLを提供し、友達リクエストとグループリクエスト（グループ追加/招待）の承認/拒否操作に使用できます。

### Event 快捷方法

要求イベントは `event.approve()` と `event.reject()` のショートカットメソッドをサポートし、内部的にRequest DSLを自動的に呼び出します：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

@request.on_group_request()
async def handle_group_request(event):
    group_id = event.get("group_id")
    await event.approve()
```

### 手动调用 Request DSL

```python
# 同意请求
await onebot.Request("flag_string").accept()

# 拒绝请求
await onebot.Request("flag_string").reject()

# 指定账户操作
await onebot.Request("flag_string").Using("main").accept()
```

### 完整示例

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    # 方式一：使用 Event 快捷方法
    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

    # 方式二：使用 Request DSL
    flag = event.get("flag")
    if comment == "passphrase":
        await onebot.Request(flag).accept()
    else:
        await onebot.Request(flag).reject()
```

### 要求操作の戻り値

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "",
    "message": ""
}
```

## イベントタイプのマッピング

### 標準 OB12 マッピング

| OB11 原始タイプ | 変換後の detail_type | 説明 |
|--------------|-------------------|------|
| message_type: private | `private` | プライベートチャットメッセージ |
| message_type: group | `group` | グループチャットメッセージ |
| request_type: friend | `friend` | 友達リクエスト |
| request_type: group | `group` | グループリクエスト |
| meta_event_type: heartbeat | `heartbeat` | ハートビート |
| notice_type: group_upload | `group_file_upload` | グループファイルアップロード |
| notice_type: group_admin | `group_admin_change` | グループ管理者変更 |
| notice_type: group_increase | `group_member_increase` | グループメンバー増加 |
| notice_type: group_decrease | `group_member_decrease` | グループメンバー減少 |
| notice_type: group_ban | `group_ban` | グループ禁止 |
| notice_type: friend_add | `friend_increase` | 友達追加 |
| notice_type: friend_delete | `friend_decrease` | 友達削除 |
| notice_type: group_recall / friend_recall | `message_recall` | メッセージ撤回 |

### 平台特有イベント（onebot11_ 前綴）

| OB11 原始タイプ | 変換後の detail_type | 説明 |
|--------------|-------------------|------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | OneBot 実装のライフサイクル |
| notify + sub_type: honor | `onebot11_honor` | グループの名誉変更 |
| notify + sub_type: poke | `onebot11_poke` | ポケポケ |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | グループのラッキーキング |
| CQ 码未知タイプ | メッセージセグメント `onebot11_{type}` | 未認識の CQ コード |

### イベントの例

```python
// 好友请求
{
  "type": "request",
  "detail_type": "friend",
  "user_id": "789012",
  "comment": "请加好友",
  "request_id": "flag_abc123",
  "flag": "flag_abc123"
}

// 心跳
{
  "type": "meta_event",
  "detail_type": "heartbeat",
  "interval": 5000,
  "status": {...}
}

// 生命周期（プラットフォーム特有）
{
  "type": "meta_event",
  "detail_type": "onebot11_lifecycle",
  "sub_type": "enable"
}

// 戳一戳（プラットフォーム特有）
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// 群红包运气王（プラットフォーム特有）
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// 荣誉变更（プラットフォーム特有）
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "honor_type": "talkative"
}

// CQ 码拡張メッセージセグメント
{
  "type": "message",
  "message": [
    {"type": "onebot11_shake", "data": {}}
  ]
}
```

### 拡張フィールドの説明

- すべての固有フィールドは `onebot11_` プレフィックスで識別されます
- 元のイベントデータは `onebot11_raw` フィールドに保持されます
- 元のイベントタイプは `onebot11_raw_type` フィールドに保持されます
- メッセージ内容のCQコードは対応するメッセージセグメントに変換されます（標準タイプは前綴なし、未知タイプは `onebot11_` 前綴付き）
- 回答メッセージには `reply` タイプのメッセージセグメントが追加されます
- @メッセージには `mention` タイプのメッセージセグメントが追加されます

## イベント拡張メソッド

OneBot11アダプターはイベントオブジェクトに以下のプラットフォーム固有メソッドを登録し、イベントハンドラ内で直接呼び出すことができます：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

### メソッドリスト

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_raw_self_id()` | `str` | BotのQQ番号（原始self_id）を取得します |
| `get_sender_info()` | `dict` | 完全な送信者情報（nickname、role、levelなど）を取得します |
| `get_sender_role()` | `str` | 送信者がグループ内の役割（owner/admin/member）を取得します |
| `get_sender_level()` | `int` | 送信者の等級を取得します |
| `get_sender_title()` | `str` | 送信者のグループタイトルを取得します |
| `is_system_message()` | `bool` | システムメッセージかどうかを判定します（sub_type == "system"） |

### 使用例

```python
from ErisPulse.Core.Event import message, command

@message.on_group_message()
async def handle_group(event):
    role = event.get_sender_role()
    if role == "admin" or role == "owner":
        await event.reply("管理员好！")

    title = event.get_sender_title()
    if title:
        await event.reply(f"你的头衔是: {title}")

@command("whoami")
async def whoami(event):
    info = event.get_sender_info()
    nickname = info.get("nickname", "未知")
    level = event.get_sender_level()
    await event.reply(f"昵称: {nickname}, 等级: {level}")
```

## 設定オプション

OneBot11アダプターは多アカウントアーキテクチャを採用し、各アカウントを個別に設定できます。設定キー名は `OneBotAdapter` です。

### アカウント設定フィールド

| フィールド | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `bot_id` | `str` | はい | `""` | ロボットのQQ番号、アカウントを識別するため |
| `mode` | `str` | いいえ | `"server"` | 実行モード：`"server"`（パッシブリッスン）または `"client"`（アクティブ接続） |
| `url` | `str` | いいえ | `"ws://127.0.0.1:3001"` | ClientモードのWebSocketアドレス |
| `token` | `str` | いいえ | `""` | 認証トークン（Clientモード接続トークン / Serverモード検証トークン） |
| `server_path` | `str` | いいえ | `"/"` | ServerモードのWebSocketパス |
| `enabled` | `bool` | いいえ | `true` | このアカウントを有効にするかどうか |
| `name` | `str` | いいえ | `""` | アカウントの備考名 |

### 内蔵デフォルト値

- 再接続間隔：30秒
- API呼び出しタイムアウト：30秒

### 設定例

```toml
[OneBotAdapter.accounts.main]
bot_id = "123456789"
mode = "server"
server_path = "/onebot-main"
token = "main_token"
enabled = true

[OneBotAdapter.accounts.backup]
bot_id = "987654321"
mode = "client"
url = "ws://127.0.0.1:3002"
token = "backup_token"
enabled = true

[OneBotAdapter.accounts.test]
bot_id = "111222333"
mode = "client"
url = "ws://127.0.0.1:3003"
enabled = false
```

### デフォルト設定

アカウントが設定されていない場合、アダプターは自動的に作成します：
```toml
[OneBotAdapter.accounts.default]
bot_id = ""
mode = "server"
server_path = "/"
enabled = true
```

## 送信メソッドの戻り値

すべての送信メソッドはTaskオブジェクトを返し、直接 `await` して送信結果を取得できます。戻り値はErisPulseアダプターの標準化された戻り値仕様に従います：

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "123456",
    "message": "",
    "onebot11_raw": {...}
}
```

### 多アカウント送信構文

```python
# アカウント選択メソッド
await onebot.Send.Using("main").To("group", 123456).Text("主アカウントメッセージ")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# 通过 bot_id 选择账户
await onebot.Send.Using("123456789").To("group", 123456).Text("通过QQ号选择")

# API呼び出し方法
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

### 账户解析优先级

`call_api` および `Using()` の `account_id` パラメータの解析優先順位は以下の通りです：
1. アカウント名と正確に一致する
2. `bot_id` フィールドと一致する
3. アカウントの任意の `str` 型フィールドと一致する
4. 有効な最初のアカウントに回帰する

## 非同期処理メカニズム

OneBot11アダプターは非同期ノンブロッキング設計を採用し、以下のことを保証します：
1. メッセージ送信がイベント処理ループをブロックしないこと
2. 複数の同時送信操作が並行して行えること
3. APIレスポンスがタイムリーに処理されること
4. WebSocket接続がアクティブな状態を維持すること
5. 複数アカウントの並行処理、各アカウントが独立して実行されること

## エラー処理

アダプターは完全なエラー処理メカニズムを提供します：
1. ネットワーク接続例外の自動再接続（各アカウントの独立した再接続をサポート、間隔は30秒）
2. API呼び出しタイムアウト処理（固定30秒タイムアウト）
3. 送信失敗時のリトライ（最大3回までリトライ）

## イベント処理の強化

多アカウントモードでは、すべてのイベントにアカウント情報が自動的に追加されます：
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "123456789", "platform": "onebot11"},
    "platform": "onebot11",
    // ... その他のイベントフィールド
}
```

アダプターは自動的に `self_id → account_name` のマッピングを維持し、`event.reply()` は手動でアカウントを指定しなくても送信元アカウントに正しくルーティングされます。

## 管理インターフェース

```python
# すべてのアカウント情報を取得
accounts = onebot.accounts

# アカウントの接続状態を確認
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# アカウントを動的に有効化/無効化（アダプターの再起動が必要）
onebot.accounts["test"].enabled = False
```

## self_id 自動マッピング

アダプターはOneBot `self_id`（QQ番号）から `account_name` へのマッピングを自動的に作成し、イベントの返信ルーティングに使用します：

```python
# アダプター内部で自動的に実行
# イベントを受け取ったとき、self.user_idフィールドにbot_idが入力されます
# アダプターは自動的に記録します: self_id("123456789") → account_name("main")

# そのためevent.reply()は正しいアカウントに自動的に送信されます
@message.on_message()
async def handler(event):
    await event.reply("自動的に正しいアカウントにルーティングされます")