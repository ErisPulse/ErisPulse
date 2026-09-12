# QQBotプラットフォームの特徴ドキュメント

QQBotAdapter は、QQ公式のロボット（QQ OpenAPI）プロトコルに基づいて構築されたアダプターです。グループチャット、プライベートチャット、チャンネルなど、全シーンの機能を統合し、OneBot12 標準イベント、標準APIアクション、およびリクエスト操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 5.0.0
- メンテナー: ErisPulse

## 基本情報

- プラットフォーム概要：QQ公式ロボット開発インターフェース。グループチャット、プライベートチャット、チャンネルなど、さまざまなシナリオに対応。
- アダプタ名：QQBotAdapter
- 接続方法：**WebSocket 長接続**（デフォルト）または **Webhook HTTPコールバック**（アカウント設定に応じて、Ed25519検証付き）
- 認証方式：appId + clientSecret から access_token を取得（7200秒、45秒前に自動更新）
- APIルートアドレス：`https://api.bot.qq.com`（v5以降、公式統一ドメイン。sandboxは廃止）
- OneBot12互換性：メッセージ送受信、イベント、**標準APIアクション**、**リクエスト操作**を完全カバー。
- 複数アカウント：サポート。`accounts` で任意のアカウントを並列実行可能（WebSocket/Webhookモードを混在させることも可能）。

## 設定の説明

```toml
# config.toml
[QQBot_Adapter]
intents = "[0, 9, 12, 25, 26, 27]"   # グローバル：サブスクライブするイベント intents（JSON配列、イベント名をサポート）

[QQBot_Adapter.accounts.default]
appid = "YOUR_APPID"                 # QQボットアプリID（必須）
secret = "YOUR_CLIENT_SECRET"        # QQボットクライアントシークレット（必須）
mode = "websocket"                   # イベント受信方式：websocket / webhook
bot_id = ""                          # ボットID（空欄の場合は自動取得；Using()で指定する場合に手動で記入可能）
gateway_url = ""                     # WebSocketゲートウェイアドレス（空欄の場合は /gateway/bot から動的に取得）
api_base_url = "https://api.bot.qq.com"  # APIルートアドレス（プロキシに使用する場合にカスタマイズ可能）
webhook_path = "/webhook"            # Webhookコールバックパス（mode=webhook の場合に有効）
enabled = true
```

**v5の破壊的変更：**
- 公式では `api.bot.qq.com` を統一使用し、`sandbox` 設定は廃止されました（旧設定は自動的に移行され無視されます）
- 旧バージョンのフラットな設定（`[QQBot_Adapter]` の下に直接 appid/secret を記述）は `accounts.default` に自動的に移行されます
- フレームワークは**ソフト依存**です：アダプタをインストールしてもフレームワークのバージョンは引きずりません；実行時に `ErisPulse>=2.7.1` を検出し、警告を表示します

**intentsの説明（ビット番号またはイベント名をサポート）：**

| ビット | イベント名 | 説明 |
|----|--------|------|
| 0 | GUILDS | チャンネルの変更 |
| 1 | GUILD_MEMBERS | チャンネルメンバーの変更 |
| 9 | GUILD_MESSAGES | チャンネルメッセージ（プライベートドメイン） |
| 12 | DIRECT_MESSAGE | チャンネルのダイレクトメッセージ |
| 24 | GROUP_MEMBER | グループメンバーの変更（v5で追加） |
| 25 | GROUP_AND_C2C_EVENT | グループメンションメッセージとプライベートチャットメッセージ |
| 26 | INTERACTION | インタラクションイベント（ボタンなど） |
| 27 | MESSAGE_AUDIT | メッセージ審査イベント |
| 30 | PUBLIC_GUILD_MESSAGES | チャンネルメッセージ（パブリックドメイン） |

## メッセージ送信

### 基本送信

```python
from ErisPulse import sdk
qqbot = sdk.adapter.get("qqbot")

await qqbot.Send.To("user", user_openid).Text("Hello World!")

# グループメンション（自動的に <qqbot-at-user id="x" /> 形式を使用）
await qqbot.Send.To("group", group_openid).At("member_openid").Text("@あなた")

# チャンネルメッセージ（自動的に <@user_id> 形式を使用）
await qqbot.Send.To("channel", channel_id).Text("チャンネルメッセージ")

# パッシブリプライ（自動的に msg_id を付与、手動での Reply は不要）
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("返信内容")

# フルメディア（URL / 本地パス / 二進制；5MBを超える場合は自動的に分割アップロード）
await qqbot.Send.To("group", gid).Image("https://example.com/img.png")

# Markdown（ネイティブ / テンプレート）
await qqbot.Send.To("group", gid).Markdown("# タイトル\n- リスト")
await qqbot.Send.To("user", uid).Markdown(template_id=1, kv=[{"key": "title", "value": "通知"}])

# キーボード（自動的に markdown タイプに設定し、bot_appid を付与）
await qqbot.Send.To("group", gid).Keyboard(keyboard).Text("選択してください")

# ストリームメッセージ（1:1チャット）
await qqbot.Send.To("user", openid).Stream("回答内容")

# 複数アカウント
await qqbot.Send.Using("account2").To("group", gid).Text("2番目のボットからのメッセージ")
```

## OneBot12 標準APIアクション

```python
result = await qqbot.Api.get_self_info()                     # ロボット情報
result = await qqbot.Api.get_group_info(group_openid)        # グループ情報
result = await qqbot.Api.get_group_member_list(group_openid) # グループメンバー一覧（自動ページング）
result = await qqbot.Api.get_guild_list()                    # チャンネル一覧
result = await qqbot.Api.get_channel_list(guild_id)          # サブチャンネル一覧
await qqbot.Api.delete_message(message_id)                   # メッセージの削除（自動でメッセージの送信元に応じたエンドポイントをルーティング）
result = await qqbot.Api.get_status()                        # 複数アカウントの実行状態
result = await qqbot.Api.Using("account2").get_self_info()   # 指定アカウント
```

サポートされる標準アクション: `get_self_info` / `get_group_info` / `get_group_member_info` / `get_group_member_list` / `get_guild_info` / `get_guild_list` / `get_guild_member_info` / `get_guild_member_list` / `get_channel_info` / `get_channel_list` / `set_channel_name` / `leave_channel` / `delete_message` / `get_status` / `get_version` / `get_supported_actions`。サポートされていないアクションは `retcode=10002` を返します。

## 要求操作（グループ参加申請の承認）

`GROUP_JOIN_REQUEST` イベントは OneBot12 の `request` イベントに変換され、標準化された承認がサポートされています。

```python
from ErisPulse.Core.Event import request as request_event

@request_event.on_request()
async def handle_join(event):
    if event.get("platform") == "qqbot":
        await event.approve()                  # 承認
        # await event.reject(comment="理由")   # 拒否
```

`request_id` は公式の `join_request_id` に対応し、アダプターは申請のコンテキストを自動的にキャッシュし、`POST /v2/groups/{group_openid}/approval_join_request/{member_openid}` にルーティングします。

## @ロボット検出メカニズム（重要）

QQ公式の「@された」事実はイベント名によって保持され、グループメッセージの@マークは `<@{群空間openid}>`（READYが返すbot_idとは**同一のID体系ではない**）です。アダプターは自動的に以下を処理します：

1. **マーク解析**：`<@openid>` と `<qqbot-at-user>` の2種類のスタイルがmentionセグメントとして解析され、テキスト中に残りません。
2. **名前の正規化**：`/users/@me`が返すロボット名とmentions配列のニックネームが一致する場合、@ロボットと認識し、mentionセグメントをbot_idに正規化します（元のopenidは`data.qqbot_openid`に保持されます）。
3. **openidの学習**：ロボットが各グループにおけるopenidを自動的に学習し、「すべてのグループメッセージを受信」モードでの@識別に使用します。
4. **注入保証**：`GROUP_AT_MESSAGE_CREATE` / `AT_MESSAGE_CREATE`はロボットのmentionセグメントが存在することを保証します。

したがって、qqbotプラットフォームでは`on_at_message()` / `event.is_at_message()`を直接使用できます。"すべてのグループメッセージを受信"権限を有効にした後、@メッセージは`GROUP_MESSAGE_CREATE`として送信されます（`GROUP_AT_MESSAGE_CREATE`はもはや到達しません）。アダプターは同様に認識します。

## プラットフォームネイティブAPIメソッド族

アダプタは、QQ公式APIの完全なセットを公開しています（詳細はアダプタリポジトリの platform-features.md を参照）：

- **ロボット**: `get_me()`、`reply_interaction()`
- **チャンネル**: `get_guilds/get_guild/mute_guild_all/roles管理/api_permission`
- **サブチャンネル**: `get_channels/get_channel/create_channel/update_channel/delete_channel/pins`
- **チャンネルメンバー**: `get_guild_members/get_guild_member/mute/roles/kick`
- **権限/リアクション/スケジュール/投稿/音声**: 全てのメソッド
- **グループ管理**（一部のインターフェースはホワイトリストロボット限定）: `get_group_members/get_group_bot_state/ブラックリスト/入群承認/ミュート/承認ポリシー`
- **メニュー/パネル**: `get_custom_menu/update_custom_menu/コマンドパネルCRUD`
- **豊富なメディア**: `_upload_media`（URL/パス/バイナリ、5MBを超える場合は自動的に分割）、`stream_message`（ストリームメッセージ）

## WebSocket / Webhook 接続

### WebSocket フロー

1. appId + clientSecret を使用して access_token を取得（事前に45秒前に自動的に更新、失敗した場合は3回リトライ）
2. `GET /gateway/bot` を使用して動的にゲートウェイアドレスを取得（`gateway_url` を設定する場合は直接使用）
3. OP_HELLO → Identify/Resume → READY（session_id と bot_id を取得）→ ハートビートループ
4. 接続切断後の再接続：最大50回、指数バックオフ `min(5 * 2^n, 300)` 秒を使用；OP_RECONNECT はセッションを保持

### Webhook モード

アカウントの `mode = "webhook"` が設定された後、ErisPulse router を使用して HTTP ルーティングを登録：

- Ed25519 による検証（シード = secret を32バイトに循環的に埋め込む）、`X-Signature-Ed25519` と `X-Signature-Timestamp + body` の検証
- 自動的に op=13 の署名検証ハンドシェイクと op=0 のイベント配信を処理
- `cryptography` ライブラリに依存（アダプタのインストール時に付属）

## エラーコードの説明

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 10001 | パラメータが不足しています |
| 10002 | 対応していないアクションです |
| 10003 | 目標/アカウントを特定できません |
| 32000 | リクエストタイムアウト |
| 33000 | ネットワーク/API呼び出し異常 |
| 34001 | リクエストが存在しないか、期限切れです（Request DSL） |
| 34100 | メディアのアップロードに失敗しました |
| 34000+ | プラットフォームのビジネスエラー（公式の code をそのまま転送） |

## 使用例

### 群メッセージの処理（@検出）

```python
from ErisPulse.Core.Event import message

@message.on_at_message()
async def handle_at(event):
    if event.get("platform") != "qqbot":
        return
    text = event.get_text()
    if text == "签到":
        await event.reply("已签到")
```

### 交互イベントの処理

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "qqbot":
        return
    if event.get("detail_type") == "qqbot_interaction":
        await qqbot.reply_interaction(event.get("qqbot_interaction_id"), code=0)
        button_id = event.get("qqbot_button_id", "")
        # ボタンの処理...
```

### 複数アカウントの起動

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

2つのアカウントを並行して起動：bot_a は WebSocket を使用し、bot_b は Webhook を使用し、互いに影響を受けません。