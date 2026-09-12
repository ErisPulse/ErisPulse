# OneBot11プラットフォーム特徴ドキュメント

OneBot11Adapter は、OneBot V11 プロトコルに基づいて構築されたアダプタです。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.3.0
- メンテナー: ErisPulse

## 基本情報

- プラットフォーム概要：OneBot はチャットボットアプリケーションのインターフェース標準です。
- アダプター名：OneBotAdapter
- 対応プロトコル/APIバージョン：OneBot V11
- マルチアカウント対応：デフォルトでマルチアカウントアーキテクチャを採用しており、複数の OneBot アカウントを同時に設定および実行できます。
- 設定キー名：`OneBotAdapter`

## v5 フレームワークの更新 (4.3.0)

このアダプタは v5 フレームワークに準拠しました（段階的なアップグレード、API 互換性を維持）：

- **BaseConverter 継承**：コンバーターの共通フィールド（id/time/platform/self/raw）は、フレームワークの build_base_event によって構築され、OB11 のフィールド名（echo/time/self_id）に従って上書きされます。
- **spawn_background によるタスクの所有**：Client モードでの接続タスクは、asyncio.spawn_background を使用して実行されます（所有者としての所有、シャットダウン時に自動回収）。
- **フレームワークのソフト依存**：アダプタのインストール時に ErisPulse のハード依存を宣言しなくなり、pip による解析時にフレームワークのバージョンが変更されるのを回避します。実行時に ErisPulse >= 2.7.1 を検出し、バージョンが低すぎる場合はログで警告を出します。
- **起動時のバージョンログ**：初期化時に OneBotAdapter v4.3.0 がロードされたことを出力します。

既存の機能（4.2.0 以降でサポート）：多アカウント、Api DSL 標準アクションのマッピング（get_self_info → get_login_info など）、Request DSL（友人/グループリクエストの承認：event.approve() / event.reject()）、EventMixin、i18n。

---

## 標準Api動作（Api DSL）

アダプタは OneBot12 標準アクション名を自動的に OB11 アクション名にマッピングし、モジュールはプラットフォームをまたいで統一して呼び出すことができます。

| OB12 標準アクション | OB11 アクション | 説明 |
|-------------------|----------------|------|
| get_self_info     | get_login_info | フィールドの標準化 user_id/user_name/user_displayname |
| get_user_info     | get_stranger_info | フィールドの標準化 |
| delete_message    | delete_msg     | メッセージの撤回 |
| leave_group       | set_group_leave | グループから退出 |
| get_friend_list   | get_friend_list | アクション名が一致し、デフォルトで透過 |
| get_group_info    | get_group_info | アクション名が一致し、デフォルトで透過 |
| upload_file       | upload_group_file / upload_private_file | 拡張 group_id/user_id 任意パラメータ、filetype は自動検出でタイプルーティング |

### 基本的な使い方

```python
from ErisPulse import sdk
onebot = sdk.adapter.get("onebot11")

# ロボット情報の取得
result = await onebot.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# メッセージの撤回
await onebot.Api.delete_message(message_id=123456)

# グループファイルのアップロード（filetype は自動検出で upload_group_file にルーティング）
result = await onebot.Api.upload_file(group_id=123456, file="/path/to/file.zip")

# 指定アカウント（複数アカウント）
result = await onebot.Api.Using("main").get_self_info()

# マッピングされていない OB11 アクションは call() でエスケープ（NapCat/Lagrange などの拡張も通用）
result = await onebot.Api.call("send_poke", group_id=123, user_id=456)
```

---

## 支持するメッセージ送信タイプ

すべての送信メソッドは、チェーン式構文で実現されています。たとえば：

```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# デフォルトアカウントを使用して送信
await onebot.Send.To("group", group_id).Text("Hello World!")

# 特定のアカウントを使用して送信
await onebot.Send.Using("main").To("group", group_id).Text("メインアカウントからのメッセージ")

# チェーン式修飾：@ユーザー + 返信
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("返信メッセージ")

# @全員
await onebot.Send.To("group", group_id).AtAll().Text("お知らせメッセージ")
```

### 基本送信メソッド

- `.Text(text: str)`：テキストメッセージを送信します。
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：画像を送信します（URL、Base64、または bytes に対応）。
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`：音声メッセージを送信します。
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：動画メッセージを送信します。
- `.Face(id: Union[str, int])`：QQ エモートを送信します。
- `.File(file: Union[str, bytes], filename: str = "file.dat")`：ファイルを送信します（自動でタイプを判定）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12 形式のメッセージを送信します（自動で OB11 に変換）。
- `.Recall(message_id: Union[str, int])`：メッセージを撤回します。

### グループ操作メソッド

以下のメソッドは、`To("group", group_id)` を使って対象グループを指定し、グループコンテキストで操作を実行します：

- `.Kick(user_id, reject_add_request=False)`：グループメンバーをキックします。
- `.Ban(user_id, duration=1800)`：グループメンバーを一時禁止します（秒単位、0 は解除）。
- `.WholeBan(enable=True)`：全員禁止を有効/無効にします。
- `.SetAdmin(user_id, enable=True)`：グループ管理者を設定/解除します。
- `.SetCard(user_id, card="")`：グループ内のニックネームを設定します。
- `.SetGroupName(name)`：グループ名を変更します。
- `.Leave(is_dismiss=False)`：グループから退会します（グループ主は解散も可能）。
- `.SetTitle(user_id, title="")`：グループ内の役職を設定します。
- `.SetPortrait(file)`：グループのアイコンを設定します。

### 検索メソッド

- `.GetMsg(message_id)`：メッセージの内容を取得します。
- `.GetForwardMsg(id)`：転送メッセージを取得します。
- `.GetLoginInfo()`：現在のログインアカウント情報を取得します。
- `.GetFriendList()`：友達リストを取得します。
- `.GetGroupInfo()`：グループ情報を取得します（`To("group", group_id)` が必要）。
- `.GetGroupList()`：グループリストを取得します。
- `.GetGroupMemberInfo(user_id)`：グループメンバー情報を取得します（`To("group", group_id)` が必要）。
- `.GetGroupMemberList()`：グループメンバーのリストを取得します（`To("group", group_id)` が必要）。

### 友達操作メソッド

- `.Like(user_id, times=1)`：友達にいいねを送信します（最大 10 回）。

### チェーン式修飾メソッド（組み合わせ可能）

チェーン式修飾メソッドは `self` を返すため、連続して呼び出すことができます。最終的な送信メソッドの前に呼び出す必要があります：

- `.At(user_id: Union[str, int], name: str = None)`：指定ユーザーを@します（複数回呼び出せます）。
- `.AtAll()`：全員を@します。
- `.Reply(message_id: Union[str, int])`：指定メッセージに返信します。

### チェーン式呼び出しの例

```python
# 基本送信
await onebot.Send.To("group", 123456).Text("Hello")

# @1人
await onebot.Send.To("group", 123456).At(789012).Text("你好")

# @複数人
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("大家好")

# OneBot12 形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)

# いいね
await onebot.Send.Like(123456, times=10)

# グループメンバーを禁止
await onebot.Send.To("group", 123456).Ban(789012, duration=3600)

# 解禁
await onebot.Send.To("group", 123456).Ban(789012, duration=0)

# キック
await onebot.Send.To("group", 123456).Kick(789012)

# グループ管理者を設定
await onebot.Send.To("group", 123456).SetAdmin(789012)

# グループ名を変更
await onebot.Send.To("group", 123456).SetGroupName("新グループ名")

# グループ情報を取得
result = await onebot.Send.To("group", 123456).GetGroupInfo()

# 特定アカウントで操作
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### 未サポートのタイプの処理

定義されていない送信メソッドを呼び出した場合、アダプタはテキストの提示を返します：

```python
# 未定義のメソッドを呼び出す
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# 実際に送信される: "[未サポートの送信タイプ] メソッド名: SomeUnsupportedMethod, パラメータ: [...]"
```

## リクエスト操作（Request DSL）

アダプターは、フレンドリクエストおよびグループリクエスト（グループ参加/招待）の承認/拒否操作を処理するためのリクエスト操作 DSL を提供します。

### Event ショートカットメソッド

リクエストイベントは `event.approve()` および `event.reject()` ショートカットメソッドをサポートし、内部的に Request DSL を自動的に呼び出します：

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

### 手動で Request DSL を呼び出す

```python
# リクエストを承認
await onebot.Request("flag_string").accept()

# リクエストを拒否
await onebot.Request("flag_string").reject()

# 特定のアカウントで操作
await onebot.Request("flag_string").Using("main").accept()
```

### 完全な例

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    # 方法1：Event ショートカットメソッドを使用
    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

    # 方法2：Request DSL を使用
    flag = event.get("flag")
    if comment == "passphrase":
        await onebot.Request(flag).accept()
    else:
        await onebot.Request(flag).reject()
```

### リクエスト操作の返り値

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
| request_type: friend | `friend` | フレンドリクエスト |
| request_type: group | `group` | グループリクエスト |
| meta_event_type: heartbeat | `heartbeat` | ハートビート |
| notice_type: group_upload | `group_file_upload` | グループファイルアップロード |
| notice_type: group_admin | `group_admin_change` | グループ管理者変更 |
| notice_type: group_increase | `group_member_increase` | グループメンバー増加 |
| notice_type: group_decrease | `group_member_decrease` | グループメンバー減少 |
| notice_type: group_ban | `group_ban` | グループ禁止 |
| notice_type: friend_add | `friend_increase` | フレンド追加 |
| notice_type: friend_delete | `friend_decrease` | フレンド削除 |
| notice_type: group_recall / friend_recall | `message_recall` | メッセージ撤回 |

### プラットフォーム固有イベント（onebot11_ 前綴）

| OB11 原始タイプ | 変換後の detail_type | 説明 |
|--------------|-------------------|------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | OneBot 実装のライフサイクル |
| notify + sub_type: honor | `onebot11_honor` | グループの栄誉変更 |
| notify + sub_type: poke | `onebot11_poke` | ポケポケ |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | グループの赤包運気王 |
| CQ コードの未知タイプ | メッセージセグメント `onebot11_{type}` | 未認識の CQ コード |

### イベント例

```python
// フレンドリクエスト
{
  "type": "request",
  "detail_type": "friend",
  "user_id": "789012",
  "comment": "フレンドを追加してください",
  "request_id": "flag_abc123",
  "flag": "flag_abc123"
}

// ハートビート
{
  "type": "meta_event",
  "detail_type": "heartbeat",
  "interval": 5000,
  "status": {...}
}

// ライフサイクル（プラットフォーム固有）
{
  "type": "meta_event",
  "detail_type": "onebot11_lifecycle",
  "sub_type": "enable"
}

// ポケポケ（プラットフォーム固有）
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// グループの赤包運気王（プラットフォーム固有）
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// 栄誉変更（プラットフォーム固有）
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "honor_type": "talkative"
}

// CQ コード拡張メッセージセグメント
{
  "type": "message",
  "message": [
    {"type": "onebot11_shake", "data": {}}
  ]
}
```

### 拡張フィールドの説明

- すべての固有フィールドは `onebot11_` 前綴で識別されます
- 元のイベントデータは `onebot11_raw` フィールドに保持されます
- 元のイベントタイプは `onebot11_raw_type` フィールドに保持されます
- メッセージ内容中の CQ コードは対応するメッセージセグメントに変換されます（標準タイプは前綴なし、未知タイプは `onebot11_` 前綴を追加）
- レプリーフメッセージには `reply` タイプのメッセージセグメントが追加されます
- @メッセージには `mention` タイプのメッセージセグメントが追加されます

## 事件拡張メソッド

OneBot11 アダプタは、イベントオブジェクトに以下のようなプラットフォーム固有のメソッドを登録しており、イベントハンドラで直接呼び出すことができます。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

### メソッド一覧

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_raw_event()` | `dict` | OneBot11 の完全な元のイベントデータを取得します |
| `get_raw_self_id()` | `str` | 元の self_id（Bot の QQ 番号）を取得します |
| `get_sender_info()` | `dict` | 送信者の完全な情報（nickname、role、level など）を取得します |
| `get_sender_role()` | `str` | 送信者がグループ内での役割（owner/admin/member）を取得します |
| `get_sender_level()` | `int` | 送信者の等級を取得します |
| `get_sender_title()` | `str` | 送信者のグループヘッダーを取得します |
| `is_system_message()` | `bool` | システムメッセージかどうかを判断します（sub_type == "system"） |

### 使用例

```python
from ErisPulse.Core.Event import message, command

@message.on_group_message()
async def handle_group(event):
    role = event.get_sender_role()
    if role == "admin" or role == "owner":
        await event.reply("管理者さん、こんにちは！")

    title = event.get_sender_title()
    if title:
        await event.reply(f"あなたのヘッダーは: {title}")

@command("whoami")
async def whoami(event):
    info = event.get_sender_info()
    nickname = info.get("nickname", "不明")
    level = event.get_sender_level()
    await event.reply(f"ニックネーム: {nickname}, 等級: {level}")
```

## 設定オプション

OneBot11 アダプターは、各アカウントごとに独立した構成を持つ多アカウントアーキテクチャを採用しています。設定キー名は `OneBotAdapter` です。

### アカウント設定フィールド

| フィールド | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `bot_id` | `str` | はい | `""` | ロボットの QQ 番号。アカウントを識別するための識別子 |
| `mode` | `str` | いいえ | `"server"` | 実行モード：`"server"`（パッシブリッスン）または `"client"`（アクティブ接続） |
| `url` | `str` | いいえ | `"ws://127.0.0.1:3001"` | Client モード時の WebSocket アドレス |
| `token` | `str` | いいえ | `""` | 認証トークン（Client モード接続トークン / Server モード検証トークン） |
| `server_path` | `str` | いいえ | `"/"` | Server モード時の WebSocket パス |
| `enabled` | `bool` | いいえ | `true` | そのアカウントを有効にするかどうか |
| `name` | `str` | いいえ | `""` | アカウントの備考名 |

### 内部デフォルト値

- 再接続間隔：30秒
- API 呼び出しのタイムアウト：30秒

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

アカウントの設定が一切行われていない場合、アダプターは自動的に以下のようなデフォルトアカウントを作成します。

```toml
[OneBotAdapter.accounts.default]
bot_id = ""
mode = "server"
server_path = "/"
enabled = true
```

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、直接 await を使用して送信結果を取得できます。返り値は ErisPulse アダプタの標準化された返り値規格に従います：

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

### 複数アカウントでの送信構文

```python
# アカウント選択方法
await onebot.Send.Using("main").To("group", 123456).Text("主アカウントのメッセージ")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# bot_id によるアカウント選択
await onebot.Send.Using("123456789").To("group", 123456).Text("QQ番号で選択")

# API呼び出し方式
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

### アカウントの解決優先度

`call_api` および `Using()` の `account_id` パラメータの解決優先度は以下の通りです：
1. アカウント名の正確な一致
2. `bot_id` フィールドの一致
3. アカウントの任意の `str` 型フィールドの一致
4. 最初の有効なアカウントに回帰

## 非同期処理メカニズム

OneBot11 アダプターは非同期非ブロッキング設計を採用しており、以下の点を保証します：

1. メッセージ送信がイベント処理ループをブロックしないこと  
2. 複数の並行送信操作を同時に実行できること  
3. APIレスポンスをタイムリーに処理できること  
4. WebSocket接続をアクティブな状態に保つこと  
5. 複数アカウントの並行処理が可能で、各アカウントは独立して実行されること

## エラー処理

アダプターは包括的なエラー処理メカニズムを提供します：

1. ネットワーク接続異常時の自動再接続（各アカウントごとに独立して再接続が可能、30秒間隔）
2. API呼び出しのタイムアウト処理（固定30秒のタイムアウト）
3. 接続失敗時の自動再試行（間隔をあけて再試行）

## イベント処理の強化

複数アカウントモードでは、すべてのイベントに自動的にアカウント情報が追加されます：
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "123456789", "platform": "onebot11"},
    "platform": "onebot11",
    // ... その他のイベントフィールド
}
```

アダプターは `self_id → account_name` のマッピングを自動的に管理します。`event.reply()` では、元のアカウントに正しくルーティングするためにアカウントを手動で指定する必要がありません。

## 管理インターフェース

```python
# すべてのアカウント情報を取得
accounts = onebot.accounts

# アカウントの接続状態を確認
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# アカウントの動的有効化/無効化（アダプタの再起動が必要）
onebot.accounts["test"].enabled = False
```

## self_id 自自動マッピング

アダプターは、OneBot `self_id`（QQ番号）から `account_name` への自動マッピングを確立し、イベントのルーティングに使用します：

```python
# アダプター内部で自動的に実行されます
# イベントを受け取った際に、self.user_id フィールドに bot_id が設定されます
# アダプターは自動的に記録します: self_id("123456789") → account_name("main")

# したがって、event.reply() は正しいアカウントにメッセージを送信するために自動的にルーティングされます
@message.on_message()
async def handler(event):
    await event.reply("正しいアカウントに自動ルーティングされます")
```