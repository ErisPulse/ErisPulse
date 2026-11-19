# QQBotプラットフォーム機能ドキュメント

QQBotAdapter は、QQ公式ボット（QQ OpenAPI）プロトコルに基づいて構築されたアダプターです。グループチャット、プライベートチャット、チャンネルなど全シナリオの機能を統合し、OneBot12 標準イベント、標準Apiアクション、リクエスト操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 5.3.3
- メンテナー: ErisPulse
- 最終更新: 2026-11-10

## 基本情報

- プラットフォーム概要：QQ公式ボット開発API、グループチャット、プライベートチャット、チャンネルなど多様なシナリオをサポート
- アダプター名：QQBotAdapter
- 接続方式：**WebSocket 常時接続**（デフォルト）または **Webhook HTTP コールバック**（アカウントごとの設定、Ed25519 署名検証）
- 認証方式：appId + clientSecret で access_token を取得（7200秒、45秒前に自動リフレッシュ）
- APIルートアドレス：`https://api.bot.qq.com`（v5 から公式統一ドメイン、sandbox は廃止）
- OneBot12互換：メッセージ送受信、イベント、**標準Apiアクション**、**リクエスト操作**を完全カバー
- マルチアカウント：対応、`accounts` 下の任意のアカウントを並列実行（websocket/webhook モードの混在可能）

## 設定説明

```toml
# config.toml
[QQBot_Adapter]
intents = "[0, 9, 12, 25, 26, 27]"   # グローバル：購読するイベントの intents（JSON配列、イベント名対応）

[QQBot_Adapter.accounts.default]
appid = "YOUR_APPID"                 # QQボットアプリケーションID（必須）
secret = "YOUR_CLIENT_SECRET"        # QQボットクライアントシークレット（必須）
mode = "websocket"                   # イベント受信方式：websocket / webhook
bot_id = ""                          # ボットID（空欄で自動取得；Using() での特定用に手動入力可）
gateway_url = ""                     # WebSocketゲートウェイアドレス（空欄の場合 /gateway/bot から動的取得）
api_base_url = "https://api.bot.qq.com"  # APIルートアドレス（プロキシ用にカスタマイズ可）
access_token_url = ""                # カスタムトークンAPI（空欄の場合は公式APIを使用）
webhook_path = "/webhook"            # Webhookコールバックパス（mode=webhook 時に有効）
enabled = true
```

**v5 破壊的変更：**
- `sandbox` フィールドは廃止されました：公式は `api.bot.qq.com` に統一されており、旧設定の sandbox は自動的に移行されて無視されます（警告を出力）
- 旧版のフラット設定（`[QQBot_Adapter]` の下に直接 appid/secret を記述）は自動的に `accounts.default` へ移行されます
- フレームワークは**ソフト依存**です：アダプターのインストールでフレームワークバージョンは引き上げられません；実行時に `ErisPulse>=2.7.1` を検出して通知します

**intents の説明（ビット番号またはイベント名をサポート）：**

| ビット | イベント名 | 説明 |
|----|--------|------|
| 0 | GUILDS | チャンネル変更 |
| 1 | GUILD_MEMBERS | チャンネルメンバー変更 |
| 9 | GUILD_MESSAGES | チャンネルメッセージ（プライベートドメインは審査必要） |
| 10 | GUILD_MESSAGE_REACTIONS | チャンネルメッセージリアクション |
| 12 | DIRECT_MESSAGE | チャンネルDM |
| 24 | GROUP_MEMBER | グループメンバー変更（**v5新規**） |
| 25 | GROUP_AND_C2C_EVENT | グループ@メッセージとプライベートチャットメッセージ |
| 26 | INTERACTION | インタラクションイベント（ボタンなど） |
| 27 | MESSAGE_AUDIT | メッセージ審査イベント |
| 28 | FORUMS_EVENT | フォーラムイベント（プライベートドメインのみ） |
| 29 | AUDIO_ACTION | オーディオ操作 |
| 30 | PUBLIC_GUILD_MESSAGES | チャンネルメッセージ（パブリックドメイン） |

```toml
# 2つの書き方は等価
intents = "[0, 9, 12, 25, 26, 27]"
intents = '["GUILDS", "GUILD_MESSAGES", "DIRECT_MESSAGE", "GROUP_AND_C2C_EVENT", "INTERACTION", "MESSAGE_AUDIT"]'
```

## 標準化アラインメント

本セクションでは、アダプターと ErisPulse 標準化仕様に準拠した動作について説明します。仕様の詳細は、SDK ドキュメントの『リクエスト操作仕様』（`docs/ja/standards/request-action-spec.md`）および『API レスポンス仕様』（`docs/ja/standards/api-response.md`）を参照してください。

### エラーコードの標準化（5.3.x）

- **プラットフォームエラーは統一して 34100**：QQ公式 API がエラーを返した場合は `retcode=34100` を返し、元のレスポンス（公式の `code`/`message` を含む）は `qqbot_raw` フィールドに保持されます（メディアアップロード失敗も同様に 34100 を使用）
- **タイムアウトは 33001**：API 呼び出しのタイムアウトは `retcode=33001` を返します（旧 32000 は使用されません）
- **撤回コンテキスト欠落は 10003**：`delete_message` でメッセージの帰属コンテキストが見つからない場合は `retcode=10003` を返します（パラメータエラー）
- **リクエスト系は 34001/34003 を維持**：リクエストが存在しないまたは期限切れの場合は `34001` を返します；リクエストコンテキストにルーティングパラメータが欠落している場合は `34003` を返します

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 10001 | パラメータ欠落/エンドポイントが空 |
| 10002 | サポートされていないアクション |
| 10003 | 送信先/アカウントを特定できない、撤回コンテキスト欠落などのパラメータエラー |
| 33000 | ネットワーク/API呼び出し異常 |
| 33001 | リクエストタイムアウト |
| 34001 | リクエストが存在しないまたは期限切れ（Request DSL） |
| 34003 | リクエストコンテキストにルーティングパラメータが欠落（Request DSL） |
| 34100 | プラットフォームビジネスエラー（元のレスポンスと公式 code は `qqbot_raw` に保持） |

### 通知イベントの命名（5.3.x）

フレンド追加・削除の通知イベントは標準命名に統一されました：

| 公式イベント | 変換後の detail_type | 説明 |
|----------|-------------------|------|
| FRIEND_ADD | `friend_increase` | フレンド追加（旧 `friend_add` は廃止） |
| FRIEND_DEL | `friend_decrease` | フレンド削除（旧 `friend_del` は廃止） |

### リクエストコンテキストの保持（5.3.2 以降）

グループ参加申請イベントのエントリは、`request_id` を申請コンテキスト（グループ/申請者 openid）にマッピングしてキャッシュします（TTL 3600 秒、上限 512 件、リクエスト処理成功後にクリア）。承認実行時は `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}` にルーティングされます。

### 拡張アクションのルーティング（5.3.x）

チャンネルメンバー権限の照会は、プラットフォームプレフィックス付きの拡張アクションを通じて提供されます：

```python
result = await qqbot.Api.call("qqbot.get_channel_member_permissions", channel_id="...", member_id="...")
```

### Stream 送信の send_context 読み取り

ストリーミングメッセージ（`.Stream()`）は `send_context` を読み取ります：イベントチェーン内では現在のイベント発生源アカウントを自動的に使用し、明示的に `Using()` で指定されたアカウントが優先されます。

## メッセージ送信

### 基本送信

```python
from ErisPulse import sdk
qqbot = sdk.adapter.get("qqbot")

# テキストを送信
await qqbot.Send.To("user", user_openid).Text("Hello World!")

# グループチャット@メッセージ（自動的に <qqbot-at-user id="x" /> 形式を使用）
await qqbot.Send.To("group", group_openid).At("member_openid").Text("@あなた")
await qqbot.Send.To("group", group_openid).AtAll().Text("お知らせ")

# チャンネルメッセージ（@ は自動的に <@user_id> 形式を使用）
await qqbot.Send.To("channel", channel_id).Text("チャンネルメッセージ")

# チャンネルDM（先にセッションを作成）
dms = await qqbot.create_dms(user_id, source_guild_id)
await qqbot.Send.To("dms", dms["data"]["guild_id"]).Text("DM")

# メッセージへの返信（パッシブ返信、自動的に msg_id を付与）
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("返信内容")

# マルチアカウント（Using/Account でアカウント名または bot_id を指定）
await qqbot.Send.Using("account2").To("group", group_openid).Text("2つ目のボットからの送信")
```

### リッチメディア

```python
# URL / ローカルパス / バイナリの3方式をサポート；5MB超過時は自動分割アップロード
await qqbot.Send.To("group", gid).Image("https://example.com/img.png")
await qqbot.Send.To("user", uid).Image("/path/to/local.png")
await qqbot.Send.To("user", uid).Voice(open("audio.mp3", "rb").read())
await qqbot.Send.To("user", uid).Video("https://example.com/v.mp4")
await qqbot.Send.To("user", uid).File(b"...", filename="doc.pdf")

# チャンネル画像は multipart ダイレクトアップロード（file_image）
await qqbot.Send.To("channel", cid).Image(open("img.png", "rb").read())
```

`file_type` のマッピング：画像=1、動画=2、音声=3、ファイル=4（メッセージセグメントタイプから自動判定、`file` セグメントは拡張子から推測）。

### Markdown / Ark / Embed / Keyboard

```python
# ネイティブ Markdown
await qqbot.Send.To("group", gid).Markdown("# タイトル\n- リスト項目")

# テンプレート Markdown
await qqbot.Send.To("user", uid).Markdown(template_id=1, kv=[{"key": "title", "value": "通知"}])
await qqbot.Send.To("user", uid).Markdown(custom_template_id="23456", kv=[...])

# Ark テンプレート
await qqbot.Send.To("user", uid).Ark(23, [{"key": "a", "value": "b"}])

# Embed（チャンネル/チャンネルDMのみ）
await qqbot.Send.To("channel", cid).Embed({"title": "タイトル", "content": "内容"})

# キーボード（自動的に markdown タイプに設定され bot_appid を付与）
keyboard = {"content": {"rows": [[{"label": "確認", "type": 2, "data": "ok"}]]}}
await qqbot.Send.To("group", gid).Keyboard(keyboard).Text("選択してください")

# 一括転送（公式 md には折りたたみ構文がないため引用リストとしてレンダリング；ネイティブ Markdown 権限が必要、失敗時は自動的にプレーンテキストへフォールバック）
await qqbot.Send.To("group", gid).MergeForward(nodes)
```

### ストリーミングメッセージ（v5 新規、1対1チャット）

```python
# 単発のストリーミング送信（input_state=10 で直接完了）
await qqbot.Send.To("user", openid).Stream("回答内容")

# 複数回追記のストリーミング
r = await qqbot.stream_message(openid, "1つ目の部分", input_state=1, msg_id=パッシブmsg_id)
stream_id = r["data"]["id"]
r = await qqbot.stream_message(openid, "2つ目の部分", stream_msg_id=stream_id, index=1, input_state=1)
r = await qqbot.stream_message(openid, "最後の部分", stream_msg_id=stream_id, index=2, input_state=10)
```

### メッセージの撤回

```python
# 標準 Api アクション：メッセージの発生源（グループ/プライベートチャット/チャンネル/DM）に応じて自動的に対応する撤回エンドポイントへルーティング
await qqbot.Api.delete_message(message_id)
```

アダプターは送受信メッセージの帰属先を自動的に登録するため、group_id/channel_id を手動で渡す必要はありません；コンテキストが欠落している場合は `retcode=10003` を返します。

## OneBot12 標準Apiアクション（v5 新規）

```python
# ボット情報
result = await qqbot.Api.get_self_info()

# グループ管理
result = await qqbot.Api.get_group_info(group_openid)          # {group_id, group_name}
result = await qqbot.Api.get_group_member_list(group_openid)   # 自動ページング集約
result = await qqbot.Api.get_group_member_info(group_openid, member_openid)

# チャンネル
result = await qqbot.Api.get_guild_list()
result = await qqbot.Api.get_guild_info(guild_id)
result = await qqbot.Api.get_guild_member_list(guild_id)
result = await qqbot.Api.get_channel_list(guild_id)
result = await qqbot.Api.get_channel_info(guild_id, channel_id)
await qqbot.Api.set_channel_name(guild_id, channel_id, "新しい名前")
await qqbot.Api.leave_channel(guild_id, channel_id)            # サブチャンネルを削除

# メタアクション
result = await qqbot.Api.get_status()   # {"good": bool, "bots": [...]}
result = await qqbot.Api.get_version()  # {"impl": "ErisPulse-QQBotAdapter", "onebot_version": "12"}

# マルチアカウント
result = await qqbot.Api.Using("account2").get_self_info()
```

サポートされている標準アクション：`get_self_info` / `get_group_info` / `get_group_member_info` / `get_group_member_list` / `get_guild_info` / `get_guild_list` / `get_guild_member_info` / `get_guild_member_list` / `get_channel_info` / `get_channel_list` / `set_channel_name` / `leave_channel` / `delete_message` / `get_status` / `get_version` / `get_supported_actions`。サポートされていないアクションは `retcode=10002` を返します（例：`get_friend_list`。QQ公式に対応するAPIがないため）。

## リクエスト操作（Request DSL、v5 新規）

`GROUP_JOIN_REQUEST`（グループ参加申請）イベントは、1対1インタラクションの `request` イベントに変換され、標準化された承認をサポートします：

```python
from ErisPulse.Core.Event import request as request_event

@request_event.on_request()
async def handle_join_request(event):
    if event.get("platform") != "qqbot":
        return
    # 自動承認
    result = await event.approve()
    # または拒否：await event.reject(comment="条件を満たしていません")
    # またはアカウント指定：await qqbot.Request(event["request_id"]).Using("account2").accept()
```

- `request_id` = 公式 `join_request_id`
- アダプターは申請コンテキスト（グループ/申請者 openid）を自動的にキャッシュし、実行時は `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}` にルーティングします
- 拒否には `reject_reason` を付与できます；コンテキストが期限切れの場合は `retcode=34001` を返します

プラットフォームメソッドを直接呼び出すこともできます：

```python
await qqbot.approve_group_join(group_openid, member_openid, join_request_id, approve=True)
await qqbot.approve_group_join(group_openid, member_openid, approve=False, reject_reason="理由")
```

## プラットフォームネイティブAPIメソッド群

アダプターは完全な QQ 公式 API を公開しています（第1引数は多くの場合ターゲットID、`account_id` でアカウントを任意指定可能）：

### ボット / インタラクション
`get_me()`、`reply_interaction(interaction_id, code=0)`

### チャンネル（Guild）
`get_guilds()`、`get_guild(guild_id)`、`mute_guild_all(guild_id, mute_seconds)`、
`get_guild_roles` / `create_guild_role` / `update_guild_role` / `delete_guild_role`、
`get_guild_api_permission`、`demand_guild_api_permission(guild_id, channel_id, path, method, desc)`

### サブチャンネル（Channel）
`get_channels`、`get_channel`、`create_channel(guild_id, name, type=0, ...)`、`update_channel(channel_id, name=..., ...)`、`delete_channel`、
`get_channel_pins`、`pin_message`、`unpin_message`

### チャンネルメンバー
`get_guild_members`、`get_guild_member`、`mute_guild_members`（一括/全チャンネル）、`mute_guild_member`、
`add_guild_member_role` / `remove_guild_member_role`、`kick_guild_member`

### 権限 / お知らせ / リアクション
`get_channel_role_permissions`、`update_channel_role_permissions`、`get_channel_member_permissions`（拡張アクション `qqbot.get_channel_member_permissions`）、`update_channel_member_permissions`、`create_announce`、
`add_reaction`、`delete_reaction`、`get_reaction_users`

### スケジュール / スレッド / オーディオ
`get_schedules`、`get_schedule`、`create_schedule`、`update_schedule`、`delete_schedule`、
`get_threads`、`get_thread`、`publish_thread(channel_id, title, content, format=3)`、`delete_thread`、
`control_audio(channel_id, audio_url, text, status)`、`mic_online`、`mic_offline`

### グループ管理（v2、**一部のAPIはホワイトリストボットのみ開放**）
```python
await qqbot.get_group_info_raw(group_openid)          # グループ情報
await qqbot.get_group_bot_state(group_openid)         # グループ内のボット状態
await qqbot.get_group_members(group_openid)           # メンバーリスト（next_cursor を含む）
await qqbot.get_group_member(group_openid, member_openid)
await qqbot.batch_remove_group_members(group_openid, [member_openid], add_to_blacklist=False)
await qqbot.get_group_member_blacklist(group_openid)
await qqbot.update_group_member_blacklist(group_openid, "add", [member_openid])
await qqbot.get_group_join_requests(group_openid)     # 参加申請リスト
await qqbot.approve_group_join(...)                   # 参加申請の承認
await qqbot.get_group_restrict_setting(group_openid)  # ミュート設定
await qqbot.set_group_restrict(group_openid, [{"op": "add", "member_openid": "...", "mute_expire_at": 123}])
# 参加承認ポリシー
await qqbot.get_join_approval_strategies()
await qqbot.create_join_approval_strategy(strategy_dict)
await qqbot.update_join_approval_strategy(strategy_id, **fields)
await qqbot.delete_join_approval_strategy(strategy_id)
await qqbot.execute_join_approval_strategy(strategy_id)
await qqbot.update_join_approval_strategy_whitelist(strategy_id, "add", [user_ids])
```

### カスタムメニュー / コマンドパネル（v5 新規）
```python
# グローバルカスタムメニュー（C2C のみ有効；サブメニューは最大5項目、ネスト不可）
menu_items = [
    {"type": "send_message", "content": {"label": "ヘルプ", "content": "/help"}},
    {"type": "link", "content": {"label": "公式サイト", "content": "https://example.com"}},
]
await qqbot.update_custom_menu(menu_items)
result = await qqbot.get_custom_menu()

# コマンドパネル（scope: c2c/group/channel/dm；ボットごとに最大20個）
await qqbot.create_command_panel("c2c", [
    {"type": "command", "content": {"label": "天気照会", "content": "/weather"}},
    {"type": "link", "content": {"label": "もっと見る", "content": "https://example.com"}},
], remark="パネルの備考", target_type="all")
await qqbot.get_command_panels("c2c")
await qqbot.get_command_panel(panel_id)
await qqbot.update_command_panel(panel_id, items)
await qqbot.delete_command_panel(panel_id)
await qqbot.update_command_panel_targets(panel_id, "add", user_openids=[...])
```

## WebSocket 接続

### 接続フロー

1. appId + clientSecret で access_token を取得（`POST https://bots.qq.com/app/getAppAccessToken`）
2. `GET /gateway/bot` によりゲートウェイアドレスを動的取得（`gateway_url` 設定時はそれを直接使用）
3. OP_HELLO（op=10）を受信し、ハートビート間隔を取得
4. OP_IDENTIFY（op=2）を送信して認証（intents はビット演算による組み合わせをサポート）
5. READY を受信して session_id と bot_id を取得し、connect meta イベントを送信
6. ハートビートループ（op=1）とイベントディスパッチ（op=0）

### 切断時の再接続

- 最大再接続 50 回、指数バックオフ `min(5 * 2^n, 300)` 秒
- OP_RECONNECT（op=7）受信時はセッションを保持（Resume）；OP_INVALID_SESSION（op=9）の場合は再 Identify
- 送受信が正常な場合は再接続カウントを自動的にリセット

### Token 管理

- access_token の有効期限は 7200 秒、**45秒前に自動リフレッシュ**（リクエスト時の遅延チェック）
- リフレッシュ失敗時は自動的に 3 回リトライ（遅延を増加させながら）
- リクエストヘッダー：`Authorization: QQBot {token}` + **`X-Union-Appid: {appid}`**（v5 新規）

## Webhook 接入（v5 新規）

アカウントの `mode` を `webhook` に設定するだけで、HTTP コールバックでイベントを受信するように変更できます：

```toml
[QQBot_Adapter.accounts.mybot]
appid = "..."
secret = "..."
mode = "webhook"
webhook_path = "/webhook"    # 複数の webhook アカウントがある場合は競合回避のため自動的にアカウント名を追加
```

- アダプターは ErisPulse router を通じて HTTP ルートを登録し、起動ログに完全なコールバック URL が出力されます
- **Ed25519 署名検証**：シード = secret を 32 バイトまで循環埋め込み；`X-Signature-Ed25519` による `X-Signature-Timestamp + body` の署名を検証
- op=13 署名検証ハンドシェイク（コールバックアドレス設定の検証）と op=0 イベントディスパッチを自動処理
- `cryptography` ライブラリに依存（アダプターと共にインストール済み）

## イベント購読と openid 体系

1. QQBot は QQ番号ではなく openid 体系を使用し、ユーザー/グループの識別子はすべて openid 文字列です
2. グループメッセージはデフォルトで、ユーザーがボットを@した場合にのみ受信します（`GROUP_AT_MESSAGE_CREATE`）
3. **すべてのグループメッセージを受信**：[QQオープンプラットフォーム](https://q.qq.com/) のボット管理画面で該当する権限を有効にする必要があります（API では設定できません）；有効化後、非@グループメッセージは `GROUP_MESSAGE_CREATE` でプッシュされ、アダプターは変換を完全にサポートしています（`qqbot_is_at_message=false` とマーク；メッセージ内にボットへの@マークが含まれる場合は自動的に@メッセージとして認識されます）
4. **@検出**：QQ の「被@」はイベント名によって表現され、グループメッセージの @ マークは `<@{グループスペースopenid}>`（READY bot_id とは異なる id 体系）です。アダプターは両方のマークスタイルを自動解析し、ボットの mention セグメントを注入/正規化することで `on_at_message()`/`is_at_message()` を利用可能にします；同時に、各グループにおけるボットの openid を自動学習し、「すべてのグループメッセージを受信」モードの `GROUP_MESSAGE_CREATE` 内の@メッセージも認識できるようにします（元の openid は mention セグメントの `data.qqbot_openid` に保持されます）
5. パッシブ返信：グループ/プライベートチャットメッセージには `msg_id` または `event_id` が必要で、アダプターが自動的にキャッシュして付与します
6. `event_id` はリッチメディアと混在して送信できません（公式制限）。アダプターは自動的にダウングレード処理します
7. 送信は審査をトリガーする場合があり、結果は `qqbot_audit_pass` / `qqbot_audit_reject` イベントで通知されます
8. プログラム終了時は `shutdown()` を呼び出してリソースを解放します

## 使用例

### グループメッセージの処理（@検出）

```python
from ErisPulse.Core.Event import message

@message.on_at_message()
async def handle_at(event):
    if event.get("platform") != "qqbot":
        return
    text = event.get_text()
    if text == "チェックイン":
        await event.reply("チェックインしました")
```

### ボタンインタラクションの処理

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("detail_type") != "qqbot_interaction":
        return
    button_id = event.get("qqbot_button_id")
    await qqbot.reply_interaction(event.get("qqbot_interaction_id"), code=0)
    if button_id == "confirm":
        await qqbot.Send.To("group", event.get("group_id")).Text("確認しました")
```

### マルチアカウント起動

```toml
[QQBot_Adapter.accounts.bot_a]
appid = "A_APPID"
secret = "..."
enabled = true

[QQBot_Adapter.accounts.bot_b]
appid = "B_APPID"
secret = "..."
mode = "webhook"
enabled = true
```

2つのアカウントが並列に起動します：bot_a は WebSocket 経由、bot_b は Webhook 経由で、互いに影響しません。