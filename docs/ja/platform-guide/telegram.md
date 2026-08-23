# Telegramプラットフォームの特徴ドキュメント

TelegramAdapterは、Telegram Bot APIに基づいて構築されたアダプターであり、さまざまなメッセージタイプとイベント処理をサポートしています。

---

[**English**](docs/en/quick-start.md) | [**中文**](docs/ja/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## ドキュメント情報

- 対応モジュールバージョン: 4.1.1
- メンテナー: ErisPulse

[**English**](docs/ja/quick-start.md)

## 基本情報

- プラットフォームの概要: Telegram はクロスプラットフォームのリアルタイムメッセージングソフトウェアです。
- アダプタ名: TelegramAdapter
- 対応するプロトコル/APIバージョン: Telegram Bot API
- セッションタイプのマッピング: `private` → 送信時に `user` を使用、`group`/`supergroup` → `group`、`channel` → `channel`

[**基本情報**](docs/ja/quick-start.md) | [**プラグイン開発**](docs/ja/plugin-development.md) | [**アダプタ開発**](docs/ja/adapter-development.md) | [**FAQ**](docs/ja/faq.md) | [**貢献**](docs/ja/contributing.md) | [**ライセンス**](docs/ja/license.md)

## 支援されるメッセージ送信タイプ

すべての送信メソッドは、チェーン式の構文で実装されています。たとえば：

```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### 基本的な送信メソッド

| メソッド | 説明 | パラメータ |
|------|------|------|
| `.Text(text)` | 純粋なテキストメッセージを送信 | `text: str` |
| `.Face(emoji)` | エモジーダイスを送信 | `emoji: str`（例: 🎲 🎯 🏀） |
| `.Markdown(text, content_type)` | Markdown形式のメッセージを送信 | `content_type` はデフォルトで `"MarkdownV2"` |
| `.HTML(text)` | HTML形式のメッセージを送信 | `text: str` |
| `.Sticker(file)` | ステッカーを送信 | `file: str (file_id/URL) \| bytes` |
| `.Location(lat, lng)` | 位置情報を送信 | `latitude: float, longitude: float` |
| `.Venue(lat, lng, title, addr)` | 地点情報を送信 | タイトルと住所を含む |
| `.Contact(phone, first, last)` | 連絡先を送信 | 電話番号と名前を含む |

### メディア送信メソッド

すべてのメディアメソッドは、`bytes`（アップロード）と `str`（file_id / URL）の2種類の入力形式をサポートしています：

| メソッド | 説明 |
|------|------|
| `.Image(file, caption, content_type)` | 画像を送信 |
| `.Video(file, caption, content_type)` | ビデオを送信 |
| `.Voice(file, caption)` | 音声を送信 |
| `.Audio(file, caption, content_type)` | 音声を送信 |
| `.File(file, caption)` | ファイルを送信 |
| `.Document(file, caption, content_type)` | `File` のエイリアス |

### メッセージ管理メソッド

| メソッド | 説明 |
|------|------|
| `.Edit(message_id, text, content_type)` | 既存のメッセージを編集 |
| `.Recall(message_id)` | 指定されたメッセージを削除 |
| `.Forward(from_chat_id, message_id)` | メッセージを転送（元の送信元を保持） |
| `.CopyMessage(from_chat_id, message_id)` | メッセージをコピー（元の送信元を保持しない） |
| `.AnswerCallback(callback_query_id, text, show_alert)` | コールバッククエリに応答 |

### 原始メッセージ送信

- `.Raw_ob12(message: List[Dict])`：OneBot12標準形式のメッセージを送信
- `.Raw_json(json_str: str)`：原始JSON形式のメッセージを送信

### チェーン式修飾メソッド

| メソッド | 説明 |
|------|------|
| `.At(user_id)` | 指定ユーザーを@する（Telegramのentitiesで実現、複数回呼び出せる） |
| `.AtAll()` | 全員を@する（`@All`テキストを送信） |
| `.Reply(message_id)` | 指定されたメッセージに返信 |
| `.Keyboard(inline_keyboard)` | インラインキーボードを設定（`list[list[dict]]`形式） |
| `.ProtectContent(protect)` | 内容を保護（転送や保存を防止） |
| `.Silent(silent)` | 静かに送信（ユーザーに通知しない） |

### 送信例

```python
# 基本的なテキスト送信
await telegram.Send.To("user", user_id).Text("Hello World!")

# インラインキーボード付きメッセージ
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")
keyboard = [
    [{"text": "ボタン1", "callback_data": "btn1"}, {"text": "ボタン2", "callback_data": "btn2"}],
    [{"text": "公式サイトにアクセス", "url": "https://example.com"}],
]
await telegram.Send.To("group", group_id).Keyboard(keyboard).Text("選択してください：")

# メディア送信（URL方式）
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="画像")

# ユーザーを@する
await telegram.Send.To("group", group_id).At("6117725680").Text("こんにちは！")

# 返信 + 内容保護
await telegram.Send.To("group", group_id).Reply("12345").ProtectContent().Text("機密メッセージ")

# 静かに送信
await telegram.Send.To("group", group_id).Silent().Text("通知なし")

# コールバッククエリに応答
await telegram.Send.AnswerCallback(callback_query_id, text="処理済み", show_alert=False)

# OneBot12の複合メッセージ
ob12_message = [
    {"type": "text", "data": {"text": "複雑なメッセージ："}},
    {"type": "mention", "data": {"user_id": "6117725680", "user_name": "ユーザー名"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)

# ステッカーを送信
await telegram.Send.To("user", user_id).Sticker("CAACAgIAAxkBAA...")  # file_id

# 位置情報を送信
await telegram.Send.To("user", user_id).Location(39.9042, 116.4074)

## 特有イベントタイプ

Telegram イベントの変換は OneBot12 標準に従い、`telegram_` プレフィックスによるプラットフォーム拡張を提供します。

### メッセージイベント detail_type マッピング

| Telegram chat.type | OneBot12 detail_type | 送信先の種類 |
|---|---|---|
| `private` | `private` | `user` |
| `group` | `group` | `group` |
| `supergroup` | `group` | `group` |
| `channel` | `channel` | `channel` |

### 特有イベントタイプ

| detail_type | 説明 |
|---|---|
| `telegram_callback_query` | コールバッククエリ（インラインキーボードボタンのクリック） |
| `telegram_inline_query` | インラインクエリ |
| `telegram_chosen_inline_result` | 選択されたインライン結果 |
| `telegram_poll` | 投票イベント |
| `telegram_poll_answer` | 投票回答 |
| `telegram_my_chat_member` | Bot 自身のメンバー状態の変更 |
| `telegram_chat_member` | チャットメンバーの変更 |
| `telegram_chat_join_request` | チャットへの参加リクエスト |
| `telegram_shipping_query` | 配送に関するクエリ |
| `telegram_pre_checkout_query` | 事前決済クエリ |

### 標準メッセージセグメントタイプ

変換後のメッセージセグメントは OneBot12 標準形式を使用します：

| メッセージセグメントタイプ | 説明 | data フィールド |
|---|---|---|
| `text` | 純粋なテキスト（@ユーザー名を含まない） | `text` |
| `mention` | @ユーザー（標準 OB12） | `user_id`, `user_name` |
| `reply` | メッセージへの返信引用 | `message_id`, `user_id` |
| `image` | 画像 | `file_id`, `url` |
| `video` | 動画 | `file_id`, `url`, `duration`, `width`, `height` |
| `voice` | 音声 | `file_id`, `url`, `duration` |
| `audio` | 音楽 | `file_id`, `url`, `duration`, `title`, `performer` |
| `file` | ファイル | `file_id`, `url`, `file_name`, `file_size`, `mime_type` |
| `location` | 位置情報 | `latitude`, `longitude`, オプションで `title`, `address` |

### プラットフォーム拡張メッセージセグメント

`telegram_` プレフィックスで識別される拡張メッセージセグメント：

| メッセージセグメントタイプ | 説明 | data フィールド |
|---|---|---|
| `telegram_sticker` | ステッカー | `file_id`, `emoji`, `sticker_type`, `url` |
| `telegram_animation` | GIF 動画 | `file_id`, `url`, `duration`, `caption` |
| `telegram_contact` | 連絡先 | `phone_number`, `first_name`, `last_name`, `user_id` |
| `telegram_inline_keyboard` | インラインキーボード | `inline_keyboard` |

### イベントの例

#### グループチャットメッセージ（@ユーザーのメンション付き）
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
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
    "username": "erispulse",
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

#### インラインキーボード付きメッセージ
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

## Event Mixin 拡張メソッド

アダプタは以下のプラットフォーム固有メソッドを登録しており、`platform == "telegram"` の場合にのみ利用可能です：

### メッセージ関連

| メソッド | 戻り値型 | 説明 |
|------|----------|------|
| `is_bot_message()` | `bool` | メッセージがロボットからのものかどうかを判定します |
| `is_edited_message()` | `bool` | 編集されたメッセージかどうかを判定します |
| `is_topic_message()` | `bool` | トピック/Topic メッセージかどうかを判定します |
| `get_update_id()` | `int` | Telegram update ID を取得します |
| `get_chat_title()` | `str` | チャットのタイトルを取得します |
| `get_chat_username()` | `str` | チャットのユーザーネームを取得します |
| `get_forward_from()` | `dict` | 転送元情報を取得します |
| `get_topic_id()` | `str` | トピック ID を取得します |

### コールバッククエリ関連

| メソッド | 戻り値型 | 説明 |
|------|----------|------|
| `get_callback_data()` | `str` | コールバッククエリの callback_data を取得します |
| `get_callback_id()` | `str` | コールバッククエリ ID（応答用）を取得します |

### メッセージセグメントデータ抽出

| メソッド | 戻り値型 | 説明 |
|------|----------|------|
| `get_inline_keyboard()` | `list` | メッセージ内のインラインキーボードを取得します |
| `get_sticker_info()` | `dict` | ステッカー情報（sticker）を取得します |
| `get_contact_info()` | `dict` | 連絡先情報（contact）を取得します |
| `get_location()` | `dict` | 位置情報（location）を取得します |

### 使用例

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_message(event):
    if event.get("platform") != "telegram":
        return

    # メッセージ属性
    if event.is_bot_message():
        return  # ロボットからのメッセージを無視

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
        await telegram.Send.AnswerCallback(callback_id, text="クリックしました")

        # メッセージへの返信
        await event.reply(f"あなたがクリックした内容：{callback_data}")

## 拡張フィールドの説明

- すべての固有フィールドは `telegram_` という接頭辞で識別されます
- 元のデータは `telegram_raw` フィールドに保持されます
- 元のイベントタイプは `telegram_raw_type` フィールドに保持されます
- チャンネルメッセージは `detail_type="channel"` を使用します
- プライベートチャットメッセージは `detail_type="private"` を使用します（送信時には `user` に変換する必要があります）
- トピックメッセージには `thread_id` フィールドが含まれます
- `@` でのメンションは標準の `mention` メッセージセグメントタイプを使用します（`type: "mention"`、テキスト内には @ユーザー名が含まれません）

[**English**](docs/en/telegram.md) | [**日本語**](docs/ja/telegram.md)

## 設定オプション

Telegram アダプタは複数アカウントの設定をサポートしています。

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

Telegram アダプタは **Polling（ポーリング）** モードのみをサポートし、Webhook モードは削除されました。

### 代理設定

Telegram API にプロキシ経由で接続する必要がある場合は、システムレベルのプロキシ（環境変数 `ALL_PROXY` / `HTTPS_PROXY`）を使用してください。

### 旧版設定の移行

旧版の単一トークン設定は自動的に互換性を持ちます：
```toml
# 旧版形式（引き続き使用可能ですが、移行することを推奨します）
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
```

新しい形式への移行を推奨します：
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true
```

docs/ja/quick-start.md