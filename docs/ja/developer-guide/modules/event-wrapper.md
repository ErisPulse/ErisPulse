# Event ラッパークラス詳細解説

Event モジュールは、イベント処理を簡素化する強力な Event ラッパークラスを提供します。

## 主な特徴

- **辞書との完全な互換性**：Event は dict を継承しています
- **便利なメソッド**：多数の便利なメソッドを提供します
- **ドットアクセス**：ドット表記によるイベントフィールドへのアクセスをサポートしています
- **後方互換性**：すべてのメソッドはオプションです

## コアフィールドメソッド

```python
from ErisPulse.Core.Event import command

@command("info")
async def info_command(event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, プラットフォーム: {platform}, 時間: {time}")
```

## メッセージイベントメソッド

```python
from ErisPulse.Core.Event import message

@message.on_private_message()
async def private_handler(event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"こんにちは、{nickname}！")
```

## メッセージタイプの判定

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"タイプ: {'プライベート' if is_private else 'グループ'}")
```

## 返信機能

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    await event.reply("あなたの名前を入力してください:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}！")
```

## コマンド情報の取得

```python
from ErisPulse.Core.Event import command

@command("cmdinfo")
async def cmdinfo_command(event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"コマンド: {cmd_name}, 引数: {cmd_args}")
```

## 通知イベントメソッド

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("友達追加ありがとうございます！")
```

## メソッド早見表

### コアメソッド

#### イベント基本情報
- `get_id()` - イベントIDを取得
- `get_time()` - イベントのタイムスタンプ（Unix秒）を取得
- `get_type()` - イベントタイプ（message/notice/request/meta）を取得
- `get_detail_type()` - イベントの詳細タイプ（private/group/friendなど）を取得
- `get_platform()` - プラットフォーム名を取得

#### ボット情報
- `get_self_platform()` - ボットのプラットフォーム名を取得
- `get_self_user_id()` - ボットのユーザーIDを取得
- `get_self_account_id()` - ボットのアカウントIDを取得（マルチBotモード）
- `get_self_info()` - ボットの完全な情報辞書を取得

### メッセージイベントメソッド

#### メッセージ内容
- `get_message()` - メッセージセグメントの配列（OneBot12形式）を取得
- `get_alt_message()` - メッセージの代替テキストを取得
- `get_text()` - プレーンテキスト内容を取得（`get_alt_message()` のエイリアス）
- `get_message_text()` - プレーンテキスト内容を取得（`get_alt_message()` のエイリアス）

#### 送信者情報
- `get_user_id()` - 送信者のユーザーIDを取得
- `get_user_nickname()` - 送信者のニックネームを取得
- `get_sender()` - 送信者の完全な情報辞書を取得

#### グループ/チャンネル情報
- `get_group_id()` - グループIDを取得（グループメッセージ）
- `get_channel_id()` - チャンネルIDを取得（チャンネルメッセージ）
- `get_guild_id()` - サーバーIDを取得（サーバーメッセージ）
- `get_thread_id()` - トピック/サブチャンネルIDを取得（トピックメッセージ）

#### メンション関連
- `has_mention()` - ボットへのメンションが含まれているか
- `get_mentions()` - メンションされたすべてのユーザーIDのリストを取得

### メッセージタイプの判定

#### 基本判定
- `is_message()` - メッセージイベントかどうか
- `is_private_message()` - プライベートメッセージかどうか
- `is_group_message()` - グループメッセージかどうか
- `is_at_message()` - メンションメッセージかどうか（`has_mention()` のエイリアス）

### 通知イベントメソッド

#### 通知操作者
- `get_operator_id()` - 操作者のIDを取得
- `get_operator_nickname()` - 操作者のニックネームを取得

#### 通知タイプの判定
- `is_notice()` - 通知イベントかどうか
- `is_group_member_increase()` - グループメンバー増加イベント
- `is_group_member_decrease()` - グループメンバー減少イベント
- `is_friend_add()` - 友達追加イベント（`detail_type == "friend_increase"` に一致）
- `is_friend_delete()` - 友達削除イベント（`detail_type == "friend_decrease"` に一致）

### リクエストイベントメソッド

#### リクエスト情報
- `get_comment()` - リクエストの付言を取得

#### リクエストタイプの判定
- `is_request()` - リクエストイベントかどうか
- `is_friend_request()` - 友達リクエストかどうか
- `is_group_request()` - グループリクエストかどうか

### 返信機能

#### 基本返信
- `reply(content, method="Text", at_users=None, reply_to=None, at_all=False, **kwargs)` - 汎用返信メソッド
  - `content`: 送信内容（テキスト、URLなど）
  - `method`: 送信方法、デフォルトは "Text"
  - `at_users`: メンションするユーザーのリスト、例: `["user1", "user2"]`
  - `reply_to`: 返信先のメッセージID
  - `at_all`: 全員にメンションするかどうか
  - "Text", "Image", "Voice", "Video", "File", "Mention" などをサポート
  - `**kwargs`: 追加パラメータ（Mention メソッドの user_id など）

- `reply_ob12(message)` - OneBot12 メッセージセグメントを使用して返信
  - `message`: OneBot12 メッセージセグメントのリストまたは辞書、MessageBuilder を併用可能

#### 転送機能

> **注意**：転送機能はアダプターの Send DSL を通じて実装する必要があります。Event ラッパークラス自体は直接的な転送メソッドを提供しません。

```python
# グループへメッセージを転送
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # または他のグループIDを指定
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### 返信待機機能

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None)` - ユーザーからの返信を待機
  - `prompt`: プロンプトメッセージ、指定した場合ユーザーに送信されます
  - `timeout`: 待機タイムアウト時間（秒）、デフォルトは60秒
  - `callback`: コールバック関数、返信を受信した際に実行
  - `validator`: 検証関数、返信が有効かどうかを検証するために使用
  - ユーザーが返信した Event オブジェクトを返します。タイムアウトした場合は None を返します

#### 対話メソッド

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None)` - 確認ダイアログ
  - `True`（確認）/ `False`（否定）/ `None`（タイムアウト）を返します
  - 中国語・英語の肯定/否定語の自動認識を内蔵、語彙セットのカスタマイズも可能

- `choose(prompt, options, timeout=60.0)` - 選択メニュー
  - `options`: オプションのテキストリスト
  - 選択されたインデックス（0-based）を返します。タイムアウトした場合は `None` を返します

- `collect(fields, timeout_per_field=60.0)` - フォーム収集
  - `fields`: フィールドのリスト。各項目には `key`、`prompt`、任意で `validator` が含まれます
  - `{key: value}` の辞書を返します。いずれかのフィールドがタイムアウトした場合は `None` を返します

- `wait_for(event_type="message", condition=None, timeout=60.0)` - 任意のイベントを待機
  - `condition`: フィルター関数。`True` を返した場合に一致とみなされます
  - 一致した Event オブジェクトを返します。タイムアウトした場合は `None` を返します

- `conversation(timeout=60.0)` - 複数回の対話コンテキストを作成
  - `Conversation` オブジェクトを返します。`say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()` をサポート
  - `is_active` 属性は対話がアクティブかどうかを示します

### コマンド情報

#### コマンド基本
- `get_command_name()` - コマンド名を取得
- `get_command_args()` - コマンドの引数リストを取得
- `get_command_raw()` - コマンドの生テキストを取得
- `get_command_info()` - 完全なコマンド情報辞書を取得
- `is_command()` - コマンドかどうか

### 生データ

- `get_raw()` - プラットフォームの生イベントデータを取得
- `get_raw_type()` - プラットフォームの生イベントタイプを取得

### プラットフォーム拡張メソッド

アダプターは各プラットフォーム専用のメソッドを登録します。以下は一般的な例です（具体的なメソッドについては各 [プラットフォームガイド](../../platform-guide/) を参照してください）：

- `get_platform_event_methods(platform)` - 指定したプラットフォームに登録されている拡張メソッドのリストを照会
- プラットフォーム拡張メソッドは、対応するプラットフォームの Event インスタンスでのみ利用可能です
- `hasattr(event, "method_name")` を使用してメソッドが存在するかどうかを安全に判定できます

### ユーティリティメソッド

- `to_dict()` - 通常の辞書に変換
- `is_processed()` - すでに処理済みかどうか
- `mark_processed()` - 処理済みとしてマーク

### ドットアクセス

Event は dict を継承しているため、すべての辞書キーへのドットアクセスをサポートしています：

```python
platform = event.platform          # event["platform"] と同等
user_id = event.user_id          # event["user_id"] と同等
message = event.message          # event["message"] と同等
```

## プラットフォーム拡張メソッド

アダプターは Event ラッパークラスに対してプラットフォーム専用のメソッドを登録できます。メソッドは対応するプラットフォームの Event インスタンスでのみ利用可能であり、他のプラットフォームからアクセスすると `AttributeError` がスローされます。

```python
# メールイベント - メールメソッドのみ
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ "Hello" を返す
event.get_chat_type()    # ❌ AttributeError

# Telegram イベント - Telegram メソッドのみ
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ "private" を返す
event.get_subject()      # ❌ AttributeError

# 組み込みメソッドは常に利用可能
event.get_text()         # ✅ すべてのプラットフォーム
event.reply("hi")        # ✅ すべてのプラットフォーム
```

### 登録済みメソッドの照会

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("email")
# ["get_subject", "get_from", ...]
```

### `hasattr` と `dir` のサポート

```python
hasattr(event, "get_subject")   # platform="email" の場合のみ True を返す
"get_subject" in dir(event)     # 同上
```

> アダプター開発者向けの拡張メソッドの登録方法については、[イベントシステム API - アダプター：プラットフォーム拡張メソッドの登録](../../api-reference/event-system.md#适配器注册平台扩展方法) を参照してください。

## 関連ドキュメント

- [モジュール開発入門](getting-started.md) - 最初のモジュールを作成
- [ベストプラクティス](best-practices.md) - 高品質なモジュールを開発