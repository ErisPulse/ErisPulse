# Telegramプラットフォーム特性ドキュメント

TelegramAdapter は Telegram Bot API をベースに構築されたアダプターで、複数のメッセージタイプとイベント処理をサポートしています。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.3.3
- メンテナー: ErisPulse
- 最終更新: 2026-11-10

## 基本情報

- プラットフォーム概要：Telegram はクロスプラットフォームのインスタントメッセージングソフトウェアです
- アダプター名：TelegramAdapter
- サポートするプロトコル/APIバージョン：Telegram Bot API
- 会話タイプのマッピング：`private` → 送信時は `user`、`group`/`supergroup` → `group`、`channel` → `channel`

## 標準化対応（4.3.3）

本章では、4.3.3 バージョンで完了した標準化対応の内容を説明します：イベントの変更、マルチアカウントの規約、エラーコード規範と Send 規範。

### イベントの変更

1. **グループ参加申請イベントの標準化**：
   - `detail_type` が `telegram_chat_join_request` から標準の `"group"` に変更され、`sub_type="join"` となります
   - `@request.on_group_request()` がこのイベントを直接キャッチできるようになりました
   - `request_id` の合成ルールは変更なし：`tjr_{chat_id}_{user_id}_{date}`
   - イベントは `event.approve()` / `event.reject()` で承認可能です（`approveChatJoinRequest` / `declineChatJoinRequest` に対応）
2. **イベントへの `self.account_id` 注入**：すべてのイベントはそれを生成したアカウント名を保持し、マルチアカウント環境下では `event.reply()` が自動的にそのアカウントで送信を処理します
3. **unknown イベント**：`self.user_id` には bot_id が設定されます（メッセージイベントの動作と一致）

リクエストイベントインターフェースの規約は SDK 標準に従います：[リクエストと承認アクション規範](../standards/request-action-spec.md)。

### アカウントとマルチアカウント

`call_api` は双方向互換のアカウントフィールドをサポートします：標準フィールド `account_id`（ApiDSL.Using ではこの名前を使用）/ 旧エイリアス `_account_id`；フレームワークの ApiDSL は新旧アダプターを自動的に適応させます。

```python
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")

await telegram.Api.Using("main").get_self_info()        # 標準的な方法でアカウントを指定
await telegram.Api.get_self_info(account_id="main")     # 標準フィールド account_id を明示的に渡す
```

### エラーコード規範

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 33001 | ネットワークエラー（接続失敗、タイムアウトなど） |
| 34100 | プラットフォーム拒否（元のレスポンスは `telegram_raw` フィールドに保持） |
| 10002 | サポートされていないアクション（`get_friend_list` / `get_group_list` など、Telegram Bot API に対応するインターフェースが存在しない） |

### Send 規範

- HTML メソッド名は `HTML` で、`Html` は予約済みエイリアスです
- `Location` のシグネチャに `title` / `content` のオプションパラメータを補完
- `AnswerCallback` / `Raw_json` は send_context アカウントを使用：イベント処理チェーン内で送信 DSL を呼び出す際、自動的に現在のイベントが属するアカウントで送信します

## 標準Apiアクション（Api DSL）

アダプターは OB12 標準アクションを Telegram Bot API にマッピングし、data フィールドを標準化します：

| OB12 標準アクション | Telegram API | data フィールド |
|--------------|--------------|----------|
| get_self_info | getMe | user_id / user_name / user_displayname |
| get_user_info(user_id) | getChat | user_id / user_name / user_displayname |
| get_group_info(group_id) | getChat | group_id / group_name |
| get_group_member_info(group_id, user_id) | getChatMember | user_id / user_name / telegram_role |
| delete_message(message_id) | deleteMessage | メッセージ登録テーブルに基づいて chat_id を自動補完 |
| leave_group(group_id) | leaveChat | - |

拡張アクション：get_group_admin_list(group_id)（管理者リスト）、get_chat_member_count(chat_id)（メンバー数）。

```python
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")

result = await telegram.Api.get_self_info()
result = await telegram.Api.get_group_info(group_id=-100123)
result = await telegram.Api.get_group_admin_list(-100123)
await telegram.Api.delete_message(message_id=55)   # chat_id を自動補完
result = await telegram.Api.Using("main").get_self_info()
```

> Telegram Bot API にはフレンドリスト/グループリストを取得するインターフェースが存在せず、get_friend_list/get_group_list は明示的に
> retcode=10002（サポートされていないアクション）を返します。

---

## リクエスト操作（Request DSL）

グループ参加申請の処理は、approveChatJoinRequest / declineChatJoinRequest に基づきます。4.3.3 以降、`chat_join_request` は標準の `group` リクエストイベント（`sub_type="join"`）にマッピングされ、`@request.on_group_request()` が直接キャッチできるようになりました：

```python
from ErisPulse.Core.Event import request

@request.on_group_request()
async def handle_join_request(event):
    if event.get("platform") != "telegram":
        return
    # event["request_id"] は合成識別子（tjr_{chat_id}_{user_id}_{date}、ルールは変更なし）
    if event.get("sub_type") == "join":
        await event.approve()          # 承認（approveChatJoinRequest）
    # await event.reject()             # 拒否（declineChatJoinRequest）

# 手動呼び出し（対応するリクエストイベントを先に受信してコンテキストを登録しておく必要あり）
await telegram.Request(event["request_id"]).accept()
await telegram.Request(event["request_id"]).reject()
await telegram.Request(event["request_id"]).Using("main").accept()
```

---

## サポートされるメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実装されています。例：

```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### 基本送信メソッド

| メソッド | 説明 | パラメータ |
|------|------|------|
| `.Text(text)` | プレーンテキストメッセージを送信 | `text: str` |
| `.Face(emoji)` | 絵文字ダイスを送信 | `emoji: str`（例：🎲 🎯 🏀） |
| `.Markdown(text, content_type)` | Markdown 形式のメッセージを送信 | `content_type` のデフォルトは `"MarkdownV2"` |
| `.HTML(text)` | HTML 形式のメッセージを送信（`Html` は予約済みエイリアス） | `text: str` |
| `.MergeForward(nodes, title)` | 結合転送メッセージを送信（タイトル + 各 blockquote 引用ブロック、4096 で切り詰め） | `nodes: List[Dict]`, `title: str` |
| `.Sticker(file)` | ステッカーを送信 | `file: str (file_id/URL) \| bytes` |
| `.Location(lat, lng, title="", content="")` | 位置情報を送信（タイトルと内容はオプション） | `latitude: float, longitude: float, title: str, content: str` |
| `.Venue(lat, lng, title, addr)` | 場所（会場）情報を送信 | タイトルと住所を含む |
| `.Contact(phone, first, last)` | 連絡先を送信 | 電話番号と氏名を含む |

### メディア送信メソッド

すべてのメディアメソッドは `bytes`（アップロード）と `str`（file_id / URL）の2種類の入力をサポートします：

| メソッド | 説明 |
|------|------|
| `.Image(file, caption, content_type)` | 画像を送信 |
| `.Video(file, caption, content_type)` | 動画を送信 |
| `.Voice(file, caption)` | ボイスメッセージを送信 |
| `.Audio(file, caption, content_type)` | 音声を送信 |
| `.File(file, caption)` | ファイルを送信 |
| `.Document(file, caption, content_type)` | File のエイリアス |

### メッセージ管理メソッド

| メソッド | 説明 |
|------|------|
| `.Edit(message_id, text, content_type)` | 既存のメッセージを編集 |
| `.Recall(message_id)` | 指定したメッセージを削除 |
| `.Forward(from_chat_id, message_id)` | メッセージを転送（転送元を保持） |
| `.CopyMessage(from_chat_id, message_id)` | メッセージをコピー（転送元なし） |
| `.AnswerCallback(callback_query_id, text, show_alert)` | コールバッククエリに応答（send_context アカウントを使用） |

### 生メッセージ送信

- `.Raw_ob12(message: List[Dict])`：OneBot12 標準形式のメッセージを送信
- `.Raw_json(json_str: str)`：生の JSON 形式メッセージを送信（send_context アカウントを使用）

### チェーン修飾メソッド

| メソッド | 説明 |
|------|------|
| `.At(user_id)` | 指定ユーザーを@（Telegram entities で実装、複数回呼び出し可能） |
| `.AtAll()` | 全メンバーに@（`@All` テキストを送信） |
| `.Reply(message_id)` | 指定メッセージに返信 |
| `.Keyboard(inline_keyboard)` | インラインキーボードを設定（`list[list[dict]]`） |
| `.ProtectContent(protect)` | コンテンツを保護（転送と保存を防止） |
| `.Silent(silent)` | サイレント送信（ユーザーに通知しない） |

### 送信例

```python
# 基本的なテキスト送信
await telegram.Send.To("user", user_id).Text("Hello World!")

# インラインキーボード付きのメッセージ
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")
keyboard = [
    [{"text": "ボタン1", "callback_data": "btn1"}, {"text": "ボタン2", "callback_data": "btn2"}],
    [{"text": "公式サイトへ", "url": "https://example.com"}],
]
await telegram.Send.To("group", group_id).Keyboard(keyboard).Text("選択してください：")

# メディア送信（URL 方式）
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="画像")

# @ユーザー
await telegram.Send.To("group", group_id).At("6117725680").Text("こんにちは！")

# 返信 + コンテンツ保護
await telegram.Send.To("group", group_id).Reply("12345").ProtectContent().Text("機密メッセージ")

# サイレント送信
await telegram.Send.To("group", group_id).Silent().Text("サイレント通知")

# HTML 形式メッセージ（Html は旧名のエイリアス）
await telegram.Send.To("user", user_id).HTML("<b>太字</b> <i>斜体</i>")

# 位置情報の送信（タイトル付き）
await telegram.Send.To("user", user_id).Location(39.9042, 116.4074, title="天安門", content="北京中心部")

# コールバッククエリへの応答
await telegram.Send.AnswerCallback(callback_query_id, text="処理済み", show_alert=False)

# OneBot12 組み合わせメッセージ
ob12_message = [
    {"type": "text", "data": {"text": "複雑なメッセージ："}},
    {"type": "mention", "data": {"user_id": "6117725680", "user_name": "ユーザー名"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)

# ステッカーの送信
await telegram.Send.To("user", user_id).Sticker("CAACAgIAAxkBAA...")  # file_id
```

## 固有イベントタイプ

Telegram イベントの変換は OneBot12 標準に従い、同時に `telegram_` プレフィックスでプラットフォーム拡張を提供します。

### メッセージイベントの detail_type マッピング

| Telegram chat.type | OneBot12 detail_type | 送信ターゲットタイプ |
|---|---|---|
| `private` | `private` | `user` |
| `group` | `group` | `group` |
| `supergroup` | `group` | `group` |
| `channel` | `channel` | `channel` |

### 固有イベントタイプ

| detail_type | 説明 |
|---|---|
| `telegram_callback_query` | コールバッククエリ（インラインキーボードボタンのクリック） |
| `telegram_inline_query` | インラインクエリ |
| `telegram_chosen_inline_result` | 選択されたインライン結果 |
| `telegram_poll` | 投票イベント |
| `telegram_poll_answer` | 投票回答 |
| `telegram_my_chat_member` | Bot 自身のメンバーステータス変更 |
| `telegram_chat_member` | チャットメンバー変更 |
| `telegram_shipping_query` | 配送先クエリ |
| `telegram_pre_checkout_query` | 決済前クエリ |

> チャット参加リクエスト（chat_join_request）は標準の `group` リクエストイベント（`sub_type="join"`）に標準化され、
> detail_type として `telegram_chat_join_request` は使用されなくなりました；関連するプラットフォームフィールド
> （`telegram_chat_join_request_id`、`telegram_chat` など）は引き続き保持されます。

### 標準メッセージセグメントタイプ

変換後のメッセージセグメントは OneBot12 標準形式を使用します：

| メッセージセグメントタイプ | 説明 | data フィールド |
|---|---|---|
| `text` | プレーンテキスト（@ユーザー名を含まない） | `text` |
| `mention` | @ユーザー（標準 OB12） | `user_id`, `user_name` |
| `reply` | 返信引用 | `message_id`, `user_id` |
| `image` | 画像 | `file_id`, `url` |
| `video` | 動画 | `file_id`, `url`, `duration`, `width`, `height` |
| `voice` | ボイス | `file_id`, `url`, `duration` |
| `audio` | 音声 | `file_id`, `url`, `duration`, `title`, `performer` |
| `file` | ファイル | `file_id`, `url`, `file_name`, `file_size`, `mime_type` |
| `location` | 位置情報 | `latitude`, `longitude`, オプションの `title`, `address` |

### プラットフォーム拡張メッセージセグメント

`telegram_` プレフィックスで識別される拡張メッセージセグメント：

| メッセージセグメントタイプ | 説明 | data フィールド |
|---|---|---|
| `telegram_sticker` | ステッカー | `file_id`, `emoji`, `sticker_type`, `url` |
| `telegram_animation` | GIF アニメーション | `file_id`, `url`, `duration`, `caption` |
| `telegram_contact` | 連絡先 | `phone_number`, `first_name`, `last_name`, `user_id` |
| `telegram_inline_keyboard` | インラインキーボード | `inline_keyboard` |

### イベント例

#### グループチャットメッセージ（@メンションを含む）
```python
{
  "type": "message",
  "detail_type": "group",
  "platform": "telegram",
  "user_id": "6117725680",
  "user_nickname": "WSu2059",
  "group_id": "-1002850921906",
  "message_id": "172",
  "message": [
    {"type": "text", "data": {"text": "/it.echo "}},
    {"type": "mention", "data": {"user_id": "", "user_name": "@nm123_91178"}}
  ],
  "alt_message": "/it.echo @nm123_91178",
  "self": {
    "platform": "telegram",
    "user_id": "6117725680",
    "account_id": "default"
  },
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
    "username": "erispulse",
    "type": "supergroup"
  }
}
```

#### グループ参加申請イベント（標準化後）
```python
{
  "type": "request",
  "detail_type": "group",
  "sub_type": "join",
  "platform": "telegram",
  "user_id": "6117725680",
  "user_nickname": "申請者のニックネーム",
  "request_id": "tjr_-1002850921906_6117725680_1731212345",
  "group_id": "-1002850921906",
  "comment": "招待リンクの名前",
  "self": {
    "platform": "telegram",
    "user_id": "6117725680",
    "account_id": "default"
  },
  "telegram_chat_join_request_id": "",
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
    "type": "supergroup"
  }
}
```

#### コールバッククエリイベント
```python
{
  "type": "notice",
  "detail_type": "telegram_callback_query",
  "user_id": "123456",
  "user_nickname": "YingXinche",
  "telegram_callback_id": "cb_123",
  "telegram_callback_data": "callback_data",
  "message_id": "msg_456"
}
```

#### インラインクエリイベント
```python
{
  "type": "request",
  "detail_type": "telegram_inline_query",
  "user_id": "789012",
  "user_nickname": "YingXinche",
  "telegram_query_id": "iq_789",
  "telegram_query_text": "search_text",
  "telegram_query_offset": "0"
}
```

#### インラインキーボード付きのメッセージ
```python
{
  "type": "message",
  "detail_type": "group",
  "message": [
    {"type": "text", "data": {"text": "選択してください："}},
    {
      "type": "telegram_inline_keyboard",
      "data": {
        "inline_keyboard": [
          [{"text": "ボタン1", "callback_data": "btn1"}],
          [{"text": "アクセス", "url": "https://example.com"}]
        ]
      }
    }
  ]
}
```

## Event Mixin 拡張メソッド

アダプターは以下のプラットフォーム専用メソッドを登録しており、`platform == "telegram"` の場合にのみ使用できます：

### メッセージ関連

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `is_bot_message()` | `bool` | メッセージがボットからのものかどうかを判定 |
| `is_edited_message()` | `bool` | 編集されたメッセージかどうかを判定 |
| `is_topic_message()` | `bool` | トピック（Topic）メッセージかどうかを判定 |
| `get_update_id()` | `int` | Telegram update ID を取得 |
| `get_chat_title()` | `str` | チャットタイトルを取得 |
| `get_chat_username()` | `str` | チャットのユーザー名を取得 |
| `get_forward_from()` | `dict` | 転送元情報を取得 |
| `get_topic_id()` | `str` | トピック ID を取得 |

### コールバッククエリ関連

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_callback_data()` | `str` | コールバッククエリの callback_data を取得 |
| `get_callback_id()` | `str` | コールバッククエリ ID を取得（応答に使用） |

### メッセージセグメントデータの抽出

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_inline_keyboard()` | `list` | メッセージ内のインラインキーボードを取得 |
| `get_sticker_info()` | `dict` | ステッカー情報を取得 |
| `get_contact_info()` | `dict` | 連絡先情報を取得 |
| `get_location()` | `dict` | 位置情報を取得 |

### 使用例

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_message(event):
    if event.get("platform") != "telegram":
        return

    # メッセージの属性
    if event.is_bot_message():
        return  # ボットのメッセージを無視

    if event.is_edited_message():
        print("これは編集されたメッセージです")

    # チャット情報
    title = event.get_chat_title()
    username = event.get_chat_username()

    # 転送元
    forward = event.get_forward_from()

    # メッセージセグメントデータ
    sticker = event.get_sticker_info()
    contact = event.get_contact_info()
    location = event.get_location()
    keyboard = event.get_inline_keyboard()

    # トピック
    if event.is_topic_message():
        topic_id = event.get_topic_id()

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "telegram":
        return

    if event.get("detail_type") == "telegram_callback_query":
        callback_data = event.get_callback_data()
        callback_id = event.get_callback_id()

        # コールバッククエリへの応答
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.AnswerCallback(callback_id, text="クリックされました")

        # メッセージへの返信（マルチアカウント環境下では自動的にイベントが属するアカウントで処理）
        await event.reply(f"あなたがクリックした内容：{callback_data}")
```

## 拡張フィールドの説明

- すべての固有フィールドは `telegram_` プレフィックスで識別されます
- 元のデータは `telegram_raw` フィールドに保持されます
- 元のイベントタイプは `telegram_raw_type` フィールドに保持されます
- イベントの `self.account_id` はイベントを生成したアカウント名です（マルチアカウント環境下では `event.reply()` が自動的にそのアカウントで処理します）
- チャンネルメッセージは `detail_type="channel"` を使用します
- 個人チャットメッセージは `detail_type="private"` を使用します（送信時は `user` に変換する必要があります）
- トピックメッセージには `thread_id` フィールドが含まれます
- `@` メンションは標準の `mention` メッセージセグメントタイプ（`type: "mention"`）を使用し、テキストには @ユーザー名が含まれません

## 設定オプション

Telegram アダプターはマルチアカウント設定をサポートします：

### 設定例
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true

[Telegram_Adapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
enabled = true
```

### 実行モード

Telegram アダプターは **Polling（ポーリング）** モードのみをサポートし、Webhook モードは削除されました。

### プロキシ設定

プロキシ経由で Telegram API に接続する必要がある場合は、システムレベルのプロキシ（環境変数 `ALL_PROXY` / `HTTPS_PROXY`）を使用してください。

### 旧バージョン設定の移行

旧バージョンの単一 token 設定は自動的に互換性を保ちます：
```toml
# 旧形式（引き続き使用可能ですが、移行を推奨）
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
```

新しい形式への移行を推奨します：
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true
```