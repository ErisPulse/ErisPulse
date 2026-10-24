# SnowLumaプラットフォームの特徴ドキュメント

SnowLumaAdapter は、SnowLuma バックエンド（NTQQ hook）に基づいて構築されたアダプターであり、OneBot v11 プロトコルを使用して通信します。

---

## ドキュメント情報

- 対応モジュールバージョン: 0.1.0
- 維持管理者: ErisPulse

## 基本情報

- プラットフォーム紹介：SnowLuma は NTQQ hook をベースとした QQ プロトコル実装で、API はすべて NapCat に準拠しています。OneBot v11 プロトコルを介して外部にサービスを提供します（デフォルトポート：HTTP 3000、WS 3001）
- アダプタ名：SnowLumaAdapter
- 対応プロトコル/APIバージョン：OneBot V11（SnowLuma 拡張アクションを含み、NapCat と完全互換。NapCat バックエンドに直接接続可能）
- 多アカウント対応：デフォルトで多アカウントアーキテクチャを採用しており、複数アカウントを同時に設定・実行できます
- 設定キー名：`SnowLuma_Adapter`

### OneBot11 アダプタとの関係

SnowLuma は OB11 プロトコルを使用し、標準アクションとイベントの変換は OneBot11 アダプタと同構造です（OB12 標準アクション名は自動マッピング）。  
主な違いは以下の通りです：

1. **デフォルトの client モード**：SnowLuma WS（`ws://127.0.0.1:3001`）に自動的に接続し、パブリックネットワークのリッスンは不要です
2. **bot_id の自動認識**：アカウント設定時に QQ 番号を入力する必要がなく、アダプタ起動時に自動的に検出され、`self_id → account_name` のマッピングが維持されます
3. **109 個の拡張アクション**：拍一戳、QQ空間、群ファイル/群相冊、メッセージ履歴、エッセンシャル、既読状態など、SnowLuma/NapCat 互換の拡張機能
4. **メルマガ拡張チェーン**：専用エンドポイント + `upload_forward_msg`（アップロードノードは resid を取得）+ `get_forward_msg`（転送内容の解析）の 3 段階のフォールバック

## 標準Api動作（Api DSL）

アダプターは OneBot12 標準アクション名を自動的に OB11 アクション名にマッピングし、モジュールはプラットフォームをまたいで統一的に呼び出すことができます。

| OB12 標準アクション | OB11 アクション | 説明 |
|--------------|-----------|------|
| get_self_info | get_login_info | フィールドの標準化 user_id/user_name/user_displayname |
| get_user_info | get_stranger_info | フィールドの標準化 |
| delete_message | delete_msg | メッセージの撤回 |
| leave_group | set_group_leave | グループからの退出 |
| upload_file | upload_group_file / upload_private_file | 拡張 group_id/user_id 任意パラメータ |

### 基本的な使い方

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# ロボット情報の取得
result = await snowluma.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# メッセージの撤回
await snowluma.Api.delete_message(message_id=123456)

# 指定アカウント（複数アカウント対応）
result = await snowluma.Api.Using("main").get_self_info()

# 拡張アクションは call() でエスケープハッチを使用（SnowLuma/NapCat 両対応）
result = await snowluma.Api.call("send_poke", group_id=123, user_id=456)
```

---

## 支援されるメッセージ送信タイプ

すべての送信メソッドは、チェーン式の構文で実装されています。たとえば：

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# デフォルトアカウントを使用して送信
await snowluma.Send.To("group", group_id).Text("Hello World!")

# 特定のアカウントを使用して送信
await snowluma.Send.Using("main").To("group", group_id).Text("メインアカウントからのメッセージ")

# チェーン式修飾：ユーザーへのメンション + リプライ
await snowluma.Send.To("group", group_id).At(123456).Reply(msg_id).Text("メッセージへの返信")
```

### 基本的な送信メソッド

- `.Text(text: str)`：純粋なテキストメッセージを送信します。
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：画像を送信します（URL、Base64、または bytes をサポート）。
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`：音声メッセージを送信します。
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：動画メッセージを送信します。
- `.Face(id: Union[str, int])`：QQ絵文字を送信します。
- `.File(file: Union[str, bytes], filename: str = "file.dat")`：ファイルを送信します。
- `.MergeForward(nodes, title="合併チャット記録")`：合併転送メッセージを送信します（下記参照）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します（自動的にOB11に変換されます。純粋なnodeセグメントのリストは自動的に合併転送にルーティングされます）。
- `.Recall(message_id: Union[str, int])`：メッセージを撤回します。

### 合併転送

```python
nodes = [
    {
        "type": "node",
        "data": {
            "user_id": "10000",
            "nickname": "MyBot",
            "content": [{"type": "text", "data": {"text": "【1/3】タイトル\n本文…"}}],
        },
    },
]

# 合併転送を送信します（3段階のフォールバック、SnowLuma / NapCatバックエンドともに適用可能）：
# ① send_group/private_forward_msg 専用エンドポイント（NapCatのネイティブ、SnowLumaの互換）
# ② upload_forward_msg から resid を取得 → send_msg で forward セグメントを送信（SnowLumaの拡張経路）
# ③ send_msg で node セグメントを直接送信
await snowluma.Send.To("group", group_id).MergeForward(nodes)

# 受信した合併転送メッセージを解析します（入力の forward セグメントは onebot11_forward として透過され、data.id は resid になります）
result = await snowluma.Api.get_forward_msg(id="resid_xxx")
```

### グループ操作メソッド

以下メソッドは `To("group", group_id)` を使用して対象グループを指定する必要があります：

- `.Kick(user_id, reject_add_request=False)`：グループメンバーをキックします。
- `.Ban(user_id, duration=1800)`：グループメンバーを一時停止します（秒単位、0は解除を意味します）。
- `.WholeBan(enable=True)`：全員一時停止を有効/無効にします。
- `.SetAdmin(user_id, enable=True)`：グループ管理者を設定/解除します。
- `.SetCard(user_id, card="")`：グループの名寄せを設定します。
- `.SetGroupName(name)`：グループ名を変更します。
- `.Leave(is_dismiss=False)`：グループから退会します（グループ主は解散も可能です）。
- `.SetTitle(user_id, title="")`：グループの肩書きを設定します。
- `.SetPortrait(file)`：グループのプロフィール画像を設定します。

### 一撃 / ソーシャル

- `.GroupPoke(user_id)`：グループ内で一撃します（`To("group", group_id)` が必要です）。
- `.FriendPoke(user_id)`：友達に一撃します。
- `.SendPoke(user_id)`：一撃を送信します（汎用）。
- `.SetMsgEmojiLike(message_id, emoji_id)`：メッセージに絵文字反応を送信します。

### QQスペース

- `.QzoneMsg(content)`：QQスペースの投稿を送信します。
- `.QzoneLike(tid)` / `.QzoneUnlike(tid)`：いいね/いいねを解除します。
- `.QzoneComment(tid, content)`：コメントを送信します。
- `.QzoneDelete(tid)`：投稿を削除します。

### グループファイル / メッセージ履歴 / 読み取り状態

- `.UploadGroupFile(file, name)`：グループにファイルをアップロードします（`To("group", group_id)` が必要です）。
- `.GetGroupFileUrl(file_id)`：グループファイルのダウンロードリンクを取得します。
- `.GetGroupMsgHistory(message_seq=0, count=20)`：グループのメッセージ履歴を取得します。
- `.GetFriendMsgHistory(user_id, count=20)`：友達のメッセージ履歴を取得します。
- `.MarkMsgAsRead()`：現在の会話の読み取り済み状態を設定します。
- `.SetOnlineStatus(status)`：オンラインステータスを設定します。

### チェーン式修飾メソッド（組み合わせて使用可能）

- `.At(user_id: Union[str, int])`：指定ユーザーにメンションします（複数回呼び出すことができます）。
- `.AtAll()`：全員にメンションします。
- `.Reply(message_id: Union[str, int])`：指定メッセージに返信します。

---

## OB11 拡張アクション（Api DSL）

標準アクションに加えて、`OB11ExtensionApi` にミックスインされた 60 以上の型安全な拡張メソッドが提供されており、全 109 の拡張アクションは `Api.call("action_name", ...)` により直接呼び出すことができます（SnowLuma/NapCat 両方で共通）。以下に各グループの概要を示します：

| グループ | 代表的なアクション |
|------|----------|
| 拍一戳 / ソーシャル | send_poke / group_poke / friend_poke / send_like |
| メッセージ返信 / エッセンス | set_msg_emoji_like / get_emoji_likes / set_essence_msg / get_essence_msg_list |
| 既読 / ステータス | mark_msg_as_read / mark_group_msg_as_read / mark_all_as_read / set_online_status / set_input_status |
| メッセージ履歴 | get_group_msg_history / get_friend_msg_history |
| グループ管理拡張 | set_group_reaction / set_group_remark / set_group_sign / set_group_todo / get_group_info_ex / get_group_shut_list / get_group_at_all_remain |
| フレンド / 連絡先 | set_friend_remark / get_unidirectional_friend_list / get_friends_with_category / get_recent_contact |
| グループファイル | get_group_file_url / get_private_file_url / get_group_root_files / get_group_files_by_folder / create_group_file_folder / delete_group_file |
| グループアルバム | get_group_album_list / get_group_album_media_list |
| QQ空間 | send_qzone_msg / get_qzone_msg_list / get_qzone_feeds |
| メッセージの転送 | get_forward_msg / upload_forward_msg |
| メディア / OCR | ocr_image / get_image |

## イベントタイプのマッピング

### 標準 OB12 マッピング

| OB11 原始タイプ | 変換後の detail_type | 説明 |
|--------------|-------------------|------|
| message_type: private | `private` | プライベートチャットメッセージ |
| message_type: group | `group` | グループチャットメッセージ |
| notice_type: group_upload | `group_file_upload` | グループファイルのアップロード |
| notice_type: group_admin | `group_admin_change` | グループ管理者の変更 |
| notice_type: group_increase | `group_member_increase` | グループメンバーの増加 |
| notice_type: group_decrease | `group_member_decrease` | グループメンバーの減少 |
| notice_type: group_ban | `group_ban` | グループの禁止 |
| notice_type: friend_add | `friend_increase` | 友達の追加 |
| notice_type: friend_delete | `friend_decrease` | 友達の削除 |
| notice_type: group_recall / friend_recall | `message_recall` | メッセージの撤回 |

### プラットフォーム固有のイベントと拡張セグメント

- プラットフォーム固有のイベント（poke/honor など）は `snowluma_` というプレフィックスを持つ detail_type を使用します。
- 未認識の CQ コードタイプは `onebot11_{type}` というプレフィックスで透過されます（プロトコルレベルのプレフィックス）。
- 入力側のマージ转发メッセージセグメントは `onebot11_forward` です（`data.id` は resid であり、`Api.get_forward_msg(id=...)` を使用して内容を解析できます）。

### 拡張フィールドの説明

- すべての固有フィールドは `snowluma_` というプレフィックスで識別されます。
- 保存された元のイベントデータは `snowluma_raw` フィールドに格納されます。
- 保存された元のイベントタイプは `snowluma_raw_type` フィールドに格納されます。

## イベント拡張メソッド

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_raw_event()` | `dict` | SnowLuma による完全な元のイベントデータを取得します |
| `get_raw_self_id()` | `str` | 元の self_id（Bot の QQ 号）を取得します |
| `get_sender_info()` | `dict` | 完全な送信者情報（nickname、role、level など）を取得します |
| `get_sender_role()` | `str` | 送信者がグループ内での役割（owner/admin/member）を取得します |
| `get_sender_level()` | `int` | 送信者の等級を取得します |
| `get_sender_title()` | `str` | 送信者のグループヘッダーを取得します |
| `is_system_message()` | `bool` | これがシステムメッセージかどうかを判断します |

---

## 設定オプション

SnowLuma アダプタは、各アカウントごとに独立した設定を持つ多アカウントアーキテクチャを採用しています。設定のキー名は `SnowLuma_Adapter` です。

### アカウント設定フィールド

| フィールド | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `mode` | `str` | いいえ | `"client"` | 実行モード：`"client"`（アクティブ接続、推奨）または `"server"`（パッシブリッスン） |
| `url` | `str` | いいえ | `"ws://127.0.0.1:3001"` | Client モード時の WebSocket アドレス（SnowLuma のデフォルトの WS ポートは 3001） |
| `token` | `str` | いいえ | `""` | アクセストークン（Bearer 認証） |
| `server_path` | `str` | いいえ | `"/"` | Server モード時の WebSocket パス |
| `enabled` | `bool` | いいえ | `true` | そのアカウントを有効にするかどうか |
| `name` | `str` | いいえ | `""` | アカウントの備考名 |

> bot_id（QQ 号）は設定する必要はありません。アダプタが接続した後、自動的に識別され、`self_id → account_name` のマッピングが維持されます。  
> `event.reply()` は自動的に元のアカウントにルーティングされます。

### 設定例

```toml
[SnowLuma_Adapter.accounts.main]
mode = "client"
url = "ws://127.0.0.1:3001"
token = ""
enabled = true

[SnowLuma_Adapter.accounts.second]
mode = "client"
url = "ws://192.168.1.100:3001"
token = "second_token"
enabled = true
```

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、これに直接 await を使用して送信結果を取得できます。返り値は ErisPulse アダプタの標準化された返り値規格に従います：

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "123456",
    "message": "",
    "snowluma_raw": {...}
}
```

### 複数アカウントの送信構文

```python
# アカウント選択方法
await snowluma.Send.Using("main").To("group", 123456).Text("主アカウントメッセージ")

# API呼び出し方法
await snowluma.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

## self_id の自動マッピング

アダプターは、OneBot の `self_id`（QQ番号）と `account_name` のマッピングを自動的に構築し、イベントのルーティングに使用します：

```python
@message.on_message()
async def handler(event):
    # 正しいアカウントに自動ルーティング
    await event.reply("送信元アカウントに自動ルーティング")
```