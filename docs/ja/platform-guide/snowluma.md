# SnowLuma プラットフォーム機能ドキュメント

SnowLumaAdapter は SnowLuma バックエンド（NTQQ hook）を基盤に構築されたアダプターで、OneBot v11 プロトコルを使用して通信します。

---

## ドキュメント情報

- 対応モジュールバージョン: 0.3.0
- メンテナー: ErisPulse

## 基本情報

- プラットフォーム概要：SnowLuma は NTQQ hook ベースの QQ プロトコル実装で、API は全面的に NapCat に準拠しており、OneBot v11 プロトコルで外部サービスを提供します（デフォルトポート：HTTP 3000、WS 3001）
- アダプター名：SnowLumaAdapter
- サポートプロトコル/APIバージョン：OneBot V11（公式アクションカタログは合計 200 アクションで、アダプターが全量カバー。NapCat と完全互換で、NapCat バックエンドに直接接続可能）
- マルチアカウント対応：デフォルトでマルチアカウントアーキテクチャを採用し、複数アカウントの同時設定・実行に対応
- 設定キー名：`SnowLuma_Adapter`

### OneBot11 アダプターとの関係

SnowLuma は OB11 プロトコルを使用しており、標準アクションとイベント変換は OneBot11 アダプターと同構造です（OB12 標準アクション名を自動マッピング）。
主な相違点：

1. **デフォルトは client モード**：SnowLuma WS（`ws://127.0.0.1:3001`）へ能動的に接続し、公開リッスンは不要。別途 server（リバース WS）/ http（API+ポーリング）/ webhook（API+レポート）を含む計 4 モードに対応
2. **bot_id の自動認識**：アカウント設定に QQ 番号を記入する必要はなく、アダプター起動後に自動検出し、`self_id → account_name` マッピングを維持します
3. **200 アクションの完全ラップ**：型付きメソッドは 169 個（127 個の汎用拡張 + 42 個の SnowLuma 固有）、残りは Core 直接呼び出し / ApiDSL パススルー / サーバーサイド別名で、完全な対応はアダプターリポジトリの [docs/api-coverage.md](https://github.com/ErisPulse/ErisPulse-SnowLumaAdapter/blob/main/docs/api-coverage.md) を参照
4. **マージ転送拡張リンク**：専用エンドポイント + `upload_forward_msg`（ノードをアップロードして resid を取得）+ `get_forward_msg`（転送内容を解析）の 3 段階フォールバック

---

## 標準 API アクション（Api DSL）

アダプターは OneBot12 標準アクション名を OB11 アクション名へ自動マッピングし、モジュールからプラットフォーム間で統一的に呼び出せます：

| OB12 標準アクション | OB11 アクション | 説明 |
|--------------|-----------|------|
| get_self_info | get_login_info | フィールド標準化：user_id/user_name/user_displayname |
| get_user_info | get_stranger_info | フィールド標準化 |
| delete_message | delete_msg | メッセージの取り消し |
| leave_group | set_group_leave | グループ退出 |
| upload_file | upload_group_file / upload_private_file | group_id/user_id のオプションパラメータを拡張 |

### 基本的な使い方

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# ボット情報を取得
result = await snowluma.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# メッセージを取り消す
await snowluma.Api.delete_message(message_id=123456)

# アカウント指定（マルチアカウント）
result = await snowluma.Api.Using("main").get_self_info()

# サーバーサイド別名など一部のアクションは call() エスケープハッチで呼び出します（SnowLuma/NapCat 共通）
result = await snowluma.Api.call("upload_foward_msg", messages=[...])  # upload_forward_msg の別名
```

---

## サポートされるメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実装されています。例：

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# デフォルトアカウントで送信
await snowluma.Send.To("group", group_id).Text("Hello World!")

# 特定のアカウントを指定して送信
await snowluma.Send.Using("main").To("group", group_id).Text("メインアカウントからのメッセージ")

# チェーン修飾：@ユーザー + 返信
await snowluma.Send.To("group", group_id).At(123456).Reply(msg_id).Text("返信メッセージ")
```

### 基本送信メソッド

- `.Text(text: str)`：プレーンテキストメッセージを送信します。
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：画像を送信します（URL、Base64、bytes に対応）。
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`：音声メッセージを送信します。
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：動画メッセージを送信します。
- `.Face(id: Union[str, int])`：QQ 絵文字（Face）を送信します。
- `.File(file: Union[str, bytes], filename: str = "file.dat")`：ファイルを送信します。
- `.MergeForward(nodes, title="チャット履歴の結合")`：マージ転送メッセージを送信します（次節参照）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12 形式メッセージを送信します（自動的に OB11 へ変換。純粋な node セグメントリストは自動的にマージ転送へルーティング）。
- `.Recall(message_id: Union[str, int])`：メッセージを取り消します。

### マージ転送

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

# マージ転送を送信（3 段階フォールバック、SnowLuma / NapCat バックエンドの両方に対応）：
# ① send_group/private_forward_msg 専用エンドポイント（NapCat ネイティブ、SnowLuma 互換）
# ② upload_forward_msg で resid を取得 → send_msg で forward セグメントを送信（SnowLuma 拡張リンク）
# ③ send_msg で node セグメントを直接送信
await snowluma.Send.To("group", group_id).MergeForward(nodes)

# 受信済みのマージ転送メッセージを解析（受信 forward セグメントは onebot11_forward でパススルー、data.id が resid）
result = await snowluma.Api.get_forward_msg(id="resid_xxx")
```

### グループ操作メソッド

以下のメソッドは `To("group", group_id)` で対象グループを指定する必要があります：

- `.Kick(user_id, reject_add_request=False)`：グループメンバーをキックします。
- `.Ban(user_id, duration=1800)`：グループメンバーをミュートします（秒）。0 は解除を意味します。
- `.WholeBan(enable=True)`：全員ミュートのオン/オフを切り替えます。
- `.SetAdmin(user_id, enable=True)`：グループ管理者を設定/解除します。
- `.SetCard(user_id, card="")`：グループ内ニックネーム（カード）を設定します。
- `.SetGroupName(name)`：グループ名を変更します。
- `.Leave(is_dismiss=False)`：グループから退席します（グループオーナーは解散可能）。
- `.SetTitle(user_id, title="")`：グループ称号を設定します。
- `.SetPortrait(file)`：グループアイコンを設定します。

### つつき / ソーシャル

- `.GroupPoke(user_id)`：グループ内でつつきます（`To("group", group_id)` が必要）。
- `.FriendPoke(user_id)`：友だちをつつきます。
- `.SendPoke(user_id)`：つつきを送信します（汎用）。
- `.SetMsgEmojiLike(message_id, emoji_id)`：メッセージへの絵文字リアクション。

### QQ空間

- `.QzoneMsg(content)`：QQ空間につぶやきを投稿します。
- `.QzoneLike(tid)` / `.QzoneUnlike(tid)`：いいね/いいね解除。
- `.QzoneComment(tid, content)`：コメントします。
- `.QzoneDelete(tid)`：削除します。

### グループファイル / メッセージ履歴 / 既読状態

- `.UploadGroupFile(file, name)`：グループファイルをアップロードします（`To("group", group_id)` が必要）。
- `.GetGroupFileUrl(file_id)`：グループファイルのダウンロードリンクを取得します。
- `.GetGroupMsgHistory(message_id=0, count=20)`：グループメッセージ履歴を取得します（message_id=0 は最新から開始）。
- `.GetFriendMsgHistory(user_id, count=20)`：友だちメッセージ履歴を取得します。
- `.MarkMsgAsRead(message_id)`：メッセージ ID ごとに既読をマークします。
- `.SetOnlineStatus(status)`：オンラインステータスを設定します。

### 会話への送信（SnowLuma 拡張、グループチャット/個人チャット自動ルーティング）

- `.AIRecord(character, text, chat_type=1)`：AI 音声をグループへ送信します（`To("group", group_id)` が必要。キャラクターは `Api.get_ai_characters` から取得）。
- `.CustomFace(emoji_id, reply_to=None)`：アカウントのお気に入り絵文字を送信します（絵文字の表示スタイルを保持）。
- `.FlashMsg(fileset_id)`：フラッシュ転送メッセージを送信します（相手側は受信後にダウンロード可能）。
- `.ForwardSingle(message_id)`：単一メッセージを現在の会話へ転送します。
- `.TuwenArk(title, desc, jump_url, summary="[共有]", preview_url=...)`：画像+テキストの Ark カードを送信します。

### チェーン修飾メソッド（組み合わせ可能）

- `.At(user_id: Union[str, int])`：指定ユーザーをメンションします（複数回呼び出し可能）。
- `.AtAll()`：全メンバーへメンションします。
- `.Reply(message_id: Union[str, int])`：指定メッセージに返信します。

---

## OB11 拡張アクション（Api DSL）

公式アクションカタログは合計 **200 アクション**あり、アダプターは 169 個を型付きでラップしています（`OB11ExtensionApi` の 127 個の汎用 + `SnowLumaExtensionApi` の 42 個の SnowLuma 固有）。残りは Core 直接呼び出し / ApiDSL パススルー / サーバーサイド別名で、1 件ごとの状態は[カバレッジ対照表](https://github.com/ErisPulse/ErisPulse-SnowLumaAdapter/blob/main/docs/api-coverage.md)を参照してください。
すべてのアクションは `Api.call("action_name", ...)` で直接呼び出せます（SnowLuma/NapCat 共通部分はバックエンドをまたいで移植可能）。グループ別概要：

| 分類 | 代表アクション |
|------|----------|
| つつき / ソーシャル | send_poke / group_poke / friend_poke / send_like |
| メッセージリアクション / 精華 | set_msg_emoji_like / get_msg_emoji_likes / fetch_emoji_like / set_essence_msg / get_essence_msg_list |
| 既読 / ステータス | mark_msg_as_read / mark_all_as_read / set_online_status / set_diy_online_status / set_input_status / nc_get_user_status |
| メッセージ履歴 | get_group_msg_history / get_friend_msg_history |
| グループ管理拡張 | set_group_reaction / set_group_remark / set_group_sign / set_group_todo（cancel/complete/list を含む）/ get_group_info_ex / get_group_shut_list / get_group_at_all_remain / set_group_kick_members / set_group_member_invite_policy / set_group_search / set_group_robot_add_option |
| グループタグ / 管理設定 | add_group_tag / delete_group_tag / get_group_tags / get_group_admin_settings / set_group_add_option / set_group_member_permissions / set_group_new_member_history_visibility |
| 友だち / コンタクト | set_friend_remark / delete_friend / set_friends_category / get_unidirectional_friend_list / get_friends_with_category / get_doubt_friends_add_request（処理を含む） |
| グループファイル | get_group_file_url / get_private_file_url / get_group_root_files / get_group_files_by_folder / create_group_file_folder / delete_group_file（フォルダの削除/名前変更を含む）/ move_group_file / trans_group_file / get_group_file_system_info |
| グループ情報 | get_group_honor_info / get_group_share_link / get_group_system_msg / get_group_ignore_add_request / get_group_ignored_notifies |
| グループアルバム（リスト） | get_group_album_list / get_group_album_media_list |
| QQ空間 | send_qzone_msg / get_qzone_msg_list / get_qzone_feeds / like_qzone / unlike_qzone / comment_qzone / delete_qzone_msg |
| マージ転送 / 単一転送 | get_forward_msg / upload_forward_msg / send_forward_msg / forward_group_single_msg / forward_friend_single_msg |
| Ark カード / ミニプログラム | send_ark_share / send_group_ark_share / share_peer / share_group_ex / send_tuwen_ark / get_mini_app_ark / get_share_link |
| AI 音声 | get_ai_characters / get_ai_record / send_group_ai_record |
| グループアナウンス / 機種 / 装扮 | get_group_notice / send_group_notice / delete_group_notice / get_model_show / set_model_show / get_friend_dress |
| メディア / OCR | ocr_image / get_image / get_record / fetch_ptt_text |
| 認証情報 / 機能 | get_cookies / get_csrf_token / get_credentials / get_clientkey / can_send_image / can_send_record / get_version_info |
| ツール / その他 | check_url_safely / clean_cache / get_file / get_rkey / get_rkey_server / translate_en2zh / get_online_clients / get_profile_like / click_inline_keyboard_button |

### 使用例

```python
snowluma = sdk.adapter.get("snowluma")

# 既読（メッセージ ID で指定）
await snowluma.Api.mark_msg_as_read(message_id=123)

# 音声をテキストに変換（メッセージ ID で指定）
result = await snowluma.Api.fetch_ptt_text(message_id=123)

# 絵文字リアクションの詳細
result = await snowluma.Api.get_msg_emoji_likes(message_id=123)

# グループアナウンス
await snowluma.Api.send_group_notice(group_id=123456, content="お知らせ", pinned=1)

# AI 音声
await snowluma.Api.send_group_ai_record(group_id=123456, character="1002", text="こんにちは")
```

## SnowLuma 固有アクション（SnowLumaExtensionApi）

以下のアクションは SnowLuma サーバー固有のもの（NapCat/Lagrange 汎用ではない）で、同様に型付きメソッドとして提供されます：

### QQ空間拡張

```python
# つぶやきの詳細と 1 ページ分のコメント（アクセス権限が必要）
result = await snowluma.Api.get_qzone_msg_detail(tid="tid_xxx", num=20)
# 投稿済みつぶやきの閲覧権限を変更：1=全員、4=友だち、16=一部の友だち、64=自分のみ、128=一部の友だちには非表示
await snowluma.Api.set_qzone_msg_right(tid="tid_xxx", ugc_right=64)
# 特定ユーザーのブラックリスト登録/解除（ボット自身の空間ブラックリスト）
await snowluma.Api.set_qzone_ban(user_id=789, enable=True)
```

### グループアルバム

```python
result = await snowluma.Api.get_qun_album_list(group_id=123456)
await snowluma.Api.upload_image_to_qun_album(group_id=123456, album_id="a1", album_name="アルバム", file="https://a.jpg")
await snowluma.Api.upload_video_to_qun_album(group_id=123456, album_id="a1", album_name="アルバム", file="./v.mp4")
await snowluma.Api.do_group_album_comment(group_id=123456, album_id="a1", lloc="xxx", content="いい写真ですね")
await snowluma.Api.del_group_album_media(group_id=123456, album_id="a1", lloc="xxx")
```

### システム絵文字

```python
result = await snowluma.Api.fetch_sys_faces()            # 完全なカタログ（グループ別）
result = await snowluma.Api.search_sys_faces(query="笑顔")  # 名前/別名/番号で検索
result = await snowluma.Api.fetch_face_entity(face_id=1)   # 番号で照会
result = await snowluma.Api.fetch_super_face_id(face_id=1) # スーパー絵文字形式かどうか
```

### ストリーミングインターフェース

```python
# ファイルをチャンク分割でボットローカルへアップロード（新規ストリーム → チャンクごと → is_complete で結合、送信可能なローカルパスを返す）
await snowluma.Api.upload_file_stream(stream_id="uuid", total_chunks=2, file_size=1024, filename="a.txt")
# ストリーミングダウンロード（file_info → file_chunk* → file_complete のフレーム分割で返す）
await snowluma.Api.download_file_stream(file_id="cached-id", chunk_size=65536)
await snowluma.Api.download_file_image_stream(file="https://a.jpg")
await snowluma.Api.download_file_record_stream(file_id="cached-record")
await snowluma.Api.clean_stream_temp_file()
```

### フラッシュ転送 / お気に入り絵文字 / 低レベルチャネル

```python
# QQ フラッシュ転送：共有コード → fileset_id → 送信/リスト/直リンク
fileset = await snowluma.Api.get_fileset_id(share_code="abcd1234")
await snowluma.Api.send_flash_msg(fileset_id="fs_xxx", group_id=123456)
result = await snowluma.Api.get_flash_file_list(fileset_id="fs_xxx")
result = await snowluma.Api.download_fileset(fileset_id="fs_xxx")

# お気に入り絵文字
await snowluma.Api.add_custom_face(file="https://a.gif")
result = await snowluma.Api.fetch_custom_face(count=10, return_type="url")
await snowluma.Api.send_custom_face(emoji_id="emoji_id_or_md5", group_id=123456)

# 低レベルチャネル（高度な使い方）
await snowluma.Api.send_packet(cmd="Oidb.0xxxx", data="hex...")
await snowluma.Api.request_decrypt_key(db_path="./db")
await snowluma.Api.bot_exit()
```

---

## イベントタイプマッピング

### 標準 OB12 マッピング

| OB11 元のタイプ | 変換後 detail_type | 説明 |
|--------------|-------------------|------|
| message_type: private | `private` | 個人チャットメッセージ |
| message_type: group | `group` | グループチャットメッセージ |
| notice_type: group_upload | `group_file_upload` | グループファイルアップロード |
| notice_type: group_admin | `group_admin_change` | グループ管理者の変更 |
| notice_type: group_increase | `group_member_increase` | グループメンバーの追加 |
| notice_type: group_decrease | `group_member_decrease` | グループメンバーの減少 |
| notice_type: group_ban | `group_ban` | グループミュート |
| notice_type: friend_add | `friend_increase` | 友だち追加 |
| notice_type: friend_delete | `friend_decrease` | 友だち削除 |
| notice_type: group_recall / friend_recall | `message_recall` | メッセージ取り消し |

### プラットフォーム固有イベントと拡張セグメント

- プラットフォーム固有イベント（poke/honor など）は `snowluma_` プレフィックスの detail_type を使用します
- 未認識の CQ コードタイプは `onebot11_{type}` プレフィックスでパススルーされます（プロトコルレベルのプレフィックス）
- 受信マージ転送メッセージセグメントは `onebot11_forward` です（`data.id` が resid で、`Api.get_forward_msg(id=...)` で内容を解析できます）

### 拡張フィールドの説明

- すべての固有フィールドは `snowluma_` プレフィックスで識別されます
- 元のイベントデータは `snowluma_raw` フィールドに保持されます
- 元のイベントタイプは `snowluma_raw_type` フィールドに保持されます

---

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
| `get_raw_event()` | `dict` | SnowLuma の完全な元イベントデータを取得 |
| `get_raw_self_id()` | `str` | 元の self_id（ボットの QQ 番号）を取得 |
| `get_sender_info()` | `dict` | 送信者の完全な情報を取得（nickname、role、level などを含む） |
| `get_sender_role()` | `str` | 送信者のグループ内での役割を取得（owner/admin/member） |
| `get_sender_level()` | `int` | 送信者のレベルを取得 |
| `get_sender_title()` | `str` | 送信者のグループ称号を取得 |
| `is_system_message()` | `bool` | システムメッセージかどうかを判定 |

---

## 設定オプション

SnowLuma アダプターはマルチアカウントアーキテクチャを採用し、各アカウントは独立して設定されます。設定キー名は `SnowLuma_Adapter` です。

### アカウント設定フィールド

| フィールド | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `mode` | `str` | いいえ | `"client"` | `client`（WS に能動接続）/ `server`（リバース WS）/ `http`（HTTP API+ポーリング）/ `webhook`（HTTP API+レポート） |
| `url` | `str` | いいえ | `"ws://127.0.0.1:3001"` | Client モードの WebSocket アドレス（SnowLuma のデフォルト WS ポートは 3001） |
| `token` | `str` | いいえ | `""` | アクセストークン（Bearer 認証） |
| `server_path` | `str` | いいえ | `"/"` | Server モードの WebSocket パス |
| `http_url` | `str` | いいえ | `"http://127.0.0.1:3000"` | http/webhook モードの API アドレス |
| `poll_interval` | `float` | いいえ | `1.0` | http モードのイベントポーリング間隔（秒） |
| `webhook_path` | `str` | いいえ | `"/snowluma_{account}"` | webhook モードのレポートルーティングプレフィックス |
| `enabled` | `bool` | いいえ | `true` | このアカウントを有効にするかどうか |
| `name` | `str` | いいえ | `""` | アカウントの備考名 |

> bot_id（QQ 番号）は設定不要です：アダプターは接続後に自動認識し、`self_id → account_name` マッピングを維持します。
> `event.reply()` は送信元アカウントへ自動ルーティングします。

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

---

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、await で直接送信結果を取得できます。戻り値は ErisPulse アダプター標準化戻り値仕様に従います：

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

### マルチアカウント送信構文

```python
# アカウント選択メソッド
await snowluma.Send.Using("main").To("group", 123456).Text("メインアカウントのメッセージ")

# API 呼び出し方式
await snowluma.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

## self_id 自動マッピング

アダプターは OneBot の `self_id`（QQ 番号）から `account_name` へのマッピングを自動的に構築し、イベントの返却ルーティングに使用します：

```python
@message.on_message()
async def handler(event):
    # 正しいアカウントへ自動ルーティング
    await event.reply("送信元アカウントへ自動ルーティング")
```