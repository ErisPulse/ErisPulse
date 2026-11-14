# OneBot11プラットフォームの機能ドキュメント

OneBot11Adapterは、OneBot V11プロトコルに基づいて構築されたアダプターです。

---

## ドキュメント情報

- 対応するモジュールのバージョン: 4.6.2
- メンテナー: ErisPulse
- 最終更新日: 2026-11-10

## 基本情報

- プラットフォームの概要: OneBotはチャットボットアプリケーションのインターフェース標準です
- アダプター名: OneBotAdapter
- 対応するプロトコル/APIバージョン: OneBot V11
- 多アカウントのサポート: デフォルトでマルチアカウントアーキテクチャ、複数のOneBotアカウントを同時に設定および実行できます
- 設定のキー名: `OneBotAdapter`

## v5范式更新（4.3.0から）

このアダプターはv5范式への対応を完了しました（段階的なアップグレード、APIの互換性を保持）：

- **BaseConverterの継承**: コンバーターの共通フィールド（id/time/platform/self/raw）は、フレームワークのbuild_base_eventによって構築され、OB11のフィールド名（echo/time/self_id）に上書きされます
- **spawn_backgroundタスクの所有**: Clientモードの接続タスクはRuntime.spawn_backgroundを使用するよう変更されました（所有者に属し、シャットダウン時に自動的に回収されます）
- **フレームワークのソフト依存**: アダプターのインストール時にErisPulseのハード依存を宣言しなくなり、pipの解析時にフレームワークのバージョンを調整する必要がありません。実行時にErisPulse>=2.7.1を検出し、バージョンが低すぎる場合はログに警告を出します
- **起動時のバージョンログ**: 初期化時にOneBotAdapter vX.Y.Zがロードされたことを出力します

既存の機能（4.2.0から対応）：マルチアカウント、Api DSL標準アクションマッピング（get_self_info→get_login_infoなど）、Request DSL（友達/グループリクエスト承認：event.approve() / event.reject()）、EventMixin、i18n。

4.3.1からリクエストイベントの処理は規格に従って実装され、以下の[標準化対応](#標準化対応)の章を参照してください。

---

## 標準Apiアクション（Api DSL）

アダプターはOneBot12標準アクション名を自動的にOB11アクション名にマッピングし、モジュールはプラットフォームを跨いで統一して呼び出すことができます：

| OB12標準アクション | OB11アクション | 説明 |
|--------------|-----------|------|
| get_self_info | get_login_info | フィールドの標準化 user_id/user_name/user_displayname |
| get_user_info | get_stranger_info | フィールドの標準化 |
| delete_message | delete_msg | メッセージの撤回 |
| leave_group | set_group_leave | グループから退出 |
| get_friend_list | get_friend_list | アクション名が一致し、デフォルトで透過 |
| get_group_info | get_group_info | アクション名が一致し、デフォルトで透過 |
| upload_file | upload_group_file / upload_private_file | 拡張 group_id/user_idのオプションパラメータ、filetypeは自動的に検出してルーティング |

### 基本的な使い方

```python
from ErisPulse import sdk
onebot = sdk.adapter.get("onebot11")

# ロボット情報を取得
result = await onebot.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# メッセージを撤回
await onebot.Api.delete_message(message_id=123456)

# グループファイルをアップロード（filetypeは自動的に検出してupload_group_fileにルーティング）
result = await onebot.Api.upload_file(group_id=123456, file="/path/to/file.zip")

# 指定したアカウントを使用（マルチアカウント）
result = await onebot.Api.Using("main").get_self_info()

# マッピングされていないOB11アクションはcall()を使って実行（NapCat/Lagrangeなどの拡張に共通）
result = await onebot.Api.call("send_poke", group_id=123, user_id=456)
```

### OB11プロトコルの拡張（NapCat/go-cqhttp/SnowLuma に共通）

頻繁に使用される拡張アクションは型付きメソッドとして封印され（`OB11ExtensionApi` mixin）、IDEの補完がサポートされています：

```python
await onebot.Api.send_poke(user_id=789, group_id=123456)
await onebot.Api.set_msg_emoji_like(message_id=123, emoji_id="76")
await onebot.Api.mark_msg_as_read(group_id=123456)
result = await onebot.Api.get_group_msg_history(group_id=123456, count=20)
await onebot.Api.set_essence_msg(message_id=123)
result = await onebot.Api.ocr_image(image="https://example.com/img.png")
```

> 拡張アクションは直接OB11アクション名を使用し、プラットフォームのプレフィックスは付けません。少数の未封印のアクションは`Api.call("action_name", ...)`を使って呼び出します。

### Sendのクエリメソッド（廃止済み）

以下のSendメソッドはまだ使用可能ですが、廃止済みとしてマークされています。Api DSLの使用を推奨します：

| Sendメソッド（廃止） | Api DSLの代替 |
|------------------|-------------|
| `Send.GetLoginInfo()` | `Api.get_self_info()` |
| `Send.GetFriendList()` | `Api.get_friend_list()` |
| `Send.GetGroupInfo()` | `Api.get_group_info(group_id)` |
| `Send.GetGroupList()` | `Api.get_group_list()` |
| `Send.GetGroupMemberInfo(uid)` | `Api.get_group_member_info(gid, uid)` |
| `Send.GetGroupMemberList()` | `Api.get_group_member_list(gid)` |
| `Send.GetMsg(mid)` | `Api.call("get_msg", message_id=mid)` |
| `Send.GetForwardMsg(id)` | `Api.call("get_forward_msg", id=id)` |

## 標準化対応

このセクションは、アダプターがErisPulseの標準化規格に準拠している動作を説明します。規格の詳細はSDKドキュメントの《リクエスト操作規格》（`docs/ja/standards/request-action-spec.md`）と《APIレスポンス規格》（`docs/ja/standards/api-response.md`）を参照してください。

### リクエストイベントの処理（4.3.1から）

アダプターはリクエスト操作規格に従ってリクエストイベントの受信と応答を実装します：

- **コンテキストの保持**: イベントのエントリポイントは`request_id`を`{request_type, sub_type, group_id, account, ts}`にマッピングし、キャッシュします（TTL 3600秒、上限512件、リクエスト処理が成功した後にクリアされます）、後続の`accept()`/`reject()`ルーティングに使用されます
- **エンドポイントの優先度**: `accept()`/`reject()`のkwargsによる明示的なパラメータ（`request_type`/`sub_type`/`group_id`は予約名）> イベントの保持されたコンテキスト > フレンドエンドポイント（`set_friend_add_request`）に回帰し、WARNINGを出力します
- **グループ招待/グループ参加リクエスト**: `request_type == "group"`の場合は、`set_group_add_request`に正しくルーティングされます（グループ参加`sub_type="add"`、招待`sub_type="invite"`）
- **廃止の説明**: 4.3.1以前は、リクエストタイプを指定するために非公開パラメータ`_request_type`を使用していましたが、廃止され、渡されても無視されます

### call_apiのエラーハンドリング

- アカウントが接続されていない、または接続が閉じられている場合、`call_api`は`ConnectionError`をスローせず、標準の失敗レスポンス（`status="failed"`、`retcode=33001`）を返します
- API呼び出しがタイムアウトした場合も、標準の失敗レスポンス（`retcode=33001`）を返します

### アカウントフィールドの両方の互換性

- `call_api`は標準フィールド`account_id`と旧フィールド名`_account_id`（標準名が優先）の両方を受け入れます；フレームワークApiDSLは自動的に適応し、モジュールコードでは`account_id`を使用することを推奨します
- Send DSLの全メソッドは`send_context`を読み取ります：イベントチェーン内では自動的に現在のイベントのソースアカウントを使用し、明示的に`Using()`で指定されたアカウントが優先されます

### エラーコード規格

| retcode | 含意 | 発生場面 |
|---------|------|----------|
| 0 | 成功 | アクションが正常に実行された |
| 33001 | ネットワークエラー | アカウントが接続されていない、接続が閉じられている、API呼び出しがタイムアウトした |
| 10002 | 対応していないアクション | 実装されていないアクションを呼び出した |
| 10003 | パラメータエラー | 必要なパラメータが不足している |

> プラットフォームの元のレスポンスデータは`onebot11_raw`フィールドに保持されます。

---

## 対応するメッセージ送信タイプ

すべての送信メソッドはチェーン式の構文で実現されます。例えば：
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# デフォルトアカウントを使用して送信
await onebot.Send.To("group", group_id).Text("Hello World!")

# 特定のアカウントを使用して送信
await onebot.Send.Using("main").To("group", group_id).Text("メインアカウントからのメッセージ")

# チェーン式修飾：@ユーザー + レプリー
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("返信メッセージ")

# @全員
await onebot.Send.To("group", group_id).AtAll().Text("お知らせメッセージ")
```

### 基礎的な送信メソッド

- `.Text(text: str)`：純粋なテキストメッセージを送信します。
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：画像を送信します（URL、Base64、またはbytesをサポート）。
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`：音声メッセージを送信します。
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：動画メッセージを送信します。
- `.Face(id: Union[str, int])`：QQ絵文字を送信します。
- `.File(file: Union[str, bytes], filename: str = "file.dat")`：ファイルを送信します（自動的にタイプを判断します）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します（自動的にOB11に変換します）。
- `.Recall(message_id: Union[str, int])`：メッセージを撤回します。

### グループ操作メソッド

以下のメソッドは`To("group", group_id)`で指定されたグループを対象とし、グループコンテキストを使用して操作を実行します：

- `.Kick(user_id, reject_add_request=False)`：グループメンバーを蹴ります。
- `.Ban(user_id, duration=1800)`：グループメンバーを禁止します（秒単位）、0は解禁を意味します。
- `.WholeBan(enable=True)`：全員禁止をオン/オフします。
- `.SetAdmin(user_id, enable=True)`：グループ管理者を設定/解除します。
- `.SetCard(user_id, card="")`：グループ名前を設定します。
- `.SetGroupName(name)`：グループ名を変更します。
- `.Leave(is_dismiss=False)`：グループを退きます（グループ主は解散できます）。
- `.SetTitle(user_id, title="")`：グループタイトルを設定します。
- `.SetPortrait(file)`：グループアイコンを設定します。

### クエリメソッド

- `.GetMsg(message_id)`：メッセージの内容を取得します。
- `.GetForwardMsg(id)`：転送メッセージを取得します。
- `.GetLoginInfo()`：現在のログイン情報（アカウント）を取得します。
- `.GetFriendList()`：友達リストを取得します。
- `.GetGroupInfo()`：グループ情報（`To("group", group_id)`が必要）を取得します。
- `.GetGroupList()`：グループリストを取得します。
- `.GetGroupMemberInfo(user_id)`：グループメンバー情報（`To("group", group_id)`が必要）を取得します。
- `.GetGroupMemberList()`：グループメンバーリスト（`To("group", group_id)`が必要）を取得します。

### 友達操作メソッド

- `.Like(user_id, times=1)`：友達にいいねを送ります（最大10回）。

### チェーン式修飾メソッド（組み合わせて使用可能）

チェーン式修飾メソッドは`self`を返し、チェーン式で呼び出すことができます。最終的な送信メソッドの前に呼び出す必要があります：

- `.At(user_id: Union[str, int], name: str = None)`：指定したユーザーを@します（複数回呼び出すことができます）。
- `.AtAll()`：全員を@します。
- `.Reply(message_id: Union[str, int])`：指定したメッセージに返信します。

### チェーン式呼び出しの例

```python
# 基礎的な送信
await onebot.Send.To("group", 123456).Text("Hello")

# @1人のユーザー
await onebot.Send.To("group", 123456).At(789012).Text("こんにちは")

# @複数のユーザー
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("皆さんこんにちは")

# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)

# いいねを送る
await onebot.Send.Like(123456, times=10)

# グループメンバーを禁止
await onebot.Send.To("group", 123456).Ban(789012, duration=3600)

# 解禁
await onebot.Send.To("group", 123456).Ban(789012, duration=0)

# メンバーを蹴る
await onebot.Send.To("group", 123456).Kick(789012)

# グループ管理者を設定
await onebot.Send.To("group", 123456).SetAdmin(789012)

# グループ名を変更
await onebot.Send.To("group", 123456).SetGroupName("新しいグループ名")

# グループ情報を取得
result = await onebot.Send.To("group", 123456).GetGroupInfo()

# 指定されたアカウントで操作
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### 対応していないタイプの処理

未定義の送信メソッドを呼び出した場合、アダプターはテキストの提示を返します：
```python
# 存在しないメソッドを呼び出す
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# 実際の送信: "[対応していない送信タイプ] メソッド名: SomeUnsupportedMethod, パラメータ: [...]"
```

## リクエスト操作（Request DSL）

アダプターはリクエスト操作DSLを提供し、友達リクエストとグループリクエスト（グループ参加/招待）の承認/拒否操作に使用できます。

### Eventの高速メソッド

リクエストイベントは`event.approve()`と`event.reject()`の高速メソッドをサポートし、内部でRequest DSLを自動的に呼び出します：

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

### 手動でRequest DSLを呼び出す

```python
# リクエストを承認
await onebot.Request("flag_string").accept()

# リクエストを拒否
await onebot.Request("flag_string").reject()

# 指定されたアカウントで操作
await onebot.Request("flag_string").Using("main").accept()
```

### 完全な例

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    # 方法1: Eventの高速メソッドを使用
    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

    # 方法2: Request DSLを使用
    flag = event.get("flag")
    if comment == "passphrase":
        await onebot.Request(flag).accept()
    else:
        await onebot.Request(flag).reject()
```

### リクエスト操作の戻り値

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

### 標準OB12マッピング

| OB11の元のタイプ | 変換後のdetail_type | 説明 |
|--------------|-------------------|------|
| message_type: private | `private` | プライベートメッセージ |
| message_type: group | `group` | グループメッセージ |
| request_type: friend | `friend` | 友達リクエスト |
| request_type: group | `group` | グループリクエスト |
| meta_event_type: heartbeat | `heartbeat` | ハートビート |
| notice_type: group_upload | `group_file_upload` | グループファイルアップロード |
| notice_type: group_admin | `group_admin_change` | グループ管理者の変更 |
| notice_type: group_increase | `group_member_increase` | グループメンバーの増加 |
| notice_type: group_decrease | `group_member_decrease` | グループメンバーの減少 |
| notice_type: group_ban | `group_ban` | グループ禁止 |
| notice_type: friend_add | `friend_increase` | 友達の追加 |
| notice_type: friend_delete | `friend_decrease` | 友達の削除 |
| notice_type: group_recall / friend_recall | `message_recall` | メッセージの撤回 |

### プラットフォーム固有のイベント（onebot11_プレフィックス）

| OB11の元のタイプ | 変換後のdetail_type | 説明 |
|--------------|-------------------|------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | OneBot実装のライフサイクル |
| notify + sub_type: honor | `onebot11_honor` | グループの名誉変更 |
| notify + sub_type: poke | `onebot11_poke` | ぽちり |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | グループのラッキー王 |
| CQコードの未知のタイプ | メッセージセグメント `onebot11_{type}` | 未認識のCQコード |

### イベントの例

```json
// 友達リクエスト
{
  "type": "request",
  "detail_type": "friend",
  "user_id": "789012",
  "comment": "友達を追加してください",
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

// ぽちり（プラットフォーム固有）
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// グループのラッキー王（プラットフォーム固有）
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// 名誉変更（プラットフォーム固有）
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "honor_type": "talkative"
}

// CQコード拡張メッセージセグメント
{
  "type": "message",
  "message": [
    {"type": "onebot11_shake", "data": {}}
  ]
}
```

### 拡張フィールドの説明

- すべての固有フィールドは`onebot11_`プレフィックスで識別されます
- 元のイベントデータは`onebot11_raw`フィールドに保持されます
- 元のイベントタイプは`onebot11_raw_type`フィールドに保持されます
- メッセージ内容のCQコードは対応するメッセージセグメントに変換されます（標準タイプはプレフィックスなし、未知タイプは`onebot11_`プレフィックスを付ける）
- レプリーメッセージには`reply`タイプのメッセージセグメントが追加されます
- @メッセージには`mention`タイプのメッセージセグメントが追加されます

## イベント拡張メソッド

OneBot11アダプターはイベントオブジェクトに以下のプラットフォーム固有のメソッドを登録し、イベントハンドラで直接呼び出すことができます：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_event = event.get_raw_event()
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

### メソッドリスト

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_raw_event()` | `dict` | OneBot11の完全な元のイベントデータを取得します |
| `get_raw_self_id()` | `str` | 元のself_id（BotのQQ番号）を取得します |
| `get_sender_info()` | `dict` | 完全な送信者情報を取得します（nickname、role、levelなどの含まれる） |
| `get_sender_role()` | `str` | 送信者がグループ内の役割を取得します（owner/admin/member） |
| `get_sender_level()` | `int` | 送信者のレベルを取得します |
| `get_sender_title()` | `str` | 送信者のグループタイトルを取得します |
| `is_system_message()` | `bool` | 送信者がシステムメッセージかどうかを判断します（sub_type == "system"） |

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
        await event.reply(f"あなたのタイトルは: {title}")

@command("whoami")
async def whoami(event):
    info = event.get_sender_info()
    nickname = info.get("nickname", "不明")
    level = event.get_sender_level()
    await event.reply(f"ニックネーム: {nickname}, レベル: {level}")
```

## 設定オプション

OneBot11アダプターはマルチアカウントアーキテクチャを採用しており、各アカウントは独立に設定されます。設定のキー名は`OneBotAdapter`です。

### アカウント設定フィールド

| フィールド | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `bot_id` | `str` | はい | `""` | ロボットのQQ番号、アカウントを識別するために使用されます |
| `mode` | `str` | いいえ | `"server"` | 実行モード：`"server"`（パッシブリッスン）または `"client"`（アクティブ接続） |
| `url` | `str` | いいえ | `"ws://127.0.0.1:3001"` | ClientモードのWebSocketアドレス |
| `token` | `str` | いいえ | `""` | 認証トークン（Clientモードの接続トークン / Serverモードの検証トークン） |
| `server_path` | `str` | いいえ | `"/"` | ServerモードのWebSocketパス |
| `enabled` | `bool` | いいえ | `true` | そのアカウントを有効にするかどうか |
| `name` | `str` | いいえ | `""` | アカウントの備考名 |

### 内部デフォルト値

- 再接続間隔：30秒
- API呼び出しのタイムアウト：30秒

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

アカウントが設定されていない場合、アダプターは自動的に以下のように作成されます：
```toml
[OneBotAdapter.accounts.default]
bot_id = ""
mode = "server"
server_path = "/"
enabled = true
```

## 送信メソッドの戻り値

すべての送信メソッドはTaskオブジェクトを返し、awaitで送信結果を取得できます。返り値はErisPulseアダプターの標準化された返り値規格に従います：

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

### 多アカウント送信の構文

```python
# アカウント選択メソッド
await onebot.Send.Using("main").To("group", 123456).Text("メインアカウントのメッセージ")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# bot_idでアカウントを選択
await onebot.Send.Using("123456789").To("group", 123456).Text("QQ番号で選択")

# API呼び出し方式
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

### アカウント解析の優先順位

`call_api`と`Using()`で`account_id`パラメータの解析の優先順位は以下の通りです：
1. アカウント名と正確に一致する
2. `bot_id`フィールドと一致する
3. アカウントの任意の`str`型フィールドと一致する
4. 最初に有効なアカウントに回帰する

## 非同期処理メカニズム

OneBot11アダプターは非同期非ブロッキング設計を採用しており、以下のことを保証します：
1. メッセージ送信はイベント処理ループをブロックしません
2. 複数の並行送信操作を同時に実行できます
3. APIの応答を適切に処理できます
4. WebSocket接続をアクティブな状態に保ちます
5. 各アカウントが独立して実行されるマルチアカウントの並行処理

## エラーハンドリング

アダプターは包括的なエラーハンドリングメカニズムを提供しています：
1. ネットワーク接続の異常は自動的に再接続されます（各アカウントごとに独立した再接続が可能、間隔は30秒）
2. API呼び出しのタイムアウト処理（固定30秒のタイムアウト、タイムアウト時は`retcode=33001`の標準失敗レスポンスを返します）
3. アカウントが接続されていない、または接続が閉じている場合、`call_api`は`retcode=33001`の標準失敗レスポンスを返し、`ConnectionError`はスローされません
4. 接続失敗時は間隔に従って自動的に再試行します

## イベント処理の強化

マルチアカウントモードでは、すべてのイベントに自動的にアカウント情報が追加されます：
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "123456789", "platform": "onebot11"},
    "platform": "onebot11",
    // ... その他のイベントフィールド
}
```

アダプターは自動的に`self_id → account_name`のマッピングを維持し、`event.reply()`は手動でアカウントを指定しなくても、正しく送信元アカウントにルーティングされます。

## 管理インターフェース

```python
# すべてのアカウント情報を取得
accounts = onebot.accounts

# アカウントの接続状態をチェック
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# アカウントの有効/無効を動的に変更（アダプターの再起動が必要）
onebot.accounts["test"].enabled = False
```

## self_idの自動マッピング

アダプターはOneBotの`self_id`（QQ番号）から`account_name`へのマッピングを自動的に確立し、イベントの返信ルーティングに使用します：

```python
# アダプター内部で自動的に完了
# イベントを受け取ったとき、self.user_idフィールドはbot_idに設定されます
# アダプターは自動的に記録します: self_id("123456789") → account_name("main")

# そのためevent.reply()は正しくアカウントにルーティングされます
@message.on_message()
async def handler(event):
    await event.reply("正しくルーティングされたアカウントに自動送信")
```