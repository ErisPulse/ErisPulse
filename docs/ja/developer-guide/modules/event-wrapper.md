# Event 包装クラスの詳細解説

Event モジュールは、イベント処理を簡素化する強力な Event 包装クラスを提供します。

## 核心機能

- **完全な辞書互換性**：Event は dict を継承しています
- **便利なメソッド**：多数の便利なメソッドを提供
- **点アクセス**：ドット記法でイベントフィールドにアクセス可能
- **後方互換性**：すべてのメソッドはオプションです

## 核心フィールドメソッド

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

## メッセージタイプ判定

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"タイプ: {'プライベートチャット' if is_private else 'グループチャット'}")
```

## レプリーメソッド

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    await event.reply("お名前を教えてください:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}！")
```

## コマンド情報取得

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

## メソッド一覧表

### 核心メソッド

#### イベント基本情報
- `get_id()` - イベントIDを取得
- `get_time()` - イベントタイムスタンプ（Unix秒）を取得
- `get_type()` - イベントタイプ（message/notice/request/meta）を取得
- `get_detail_type()` - イベント詳細タイプ（private/group/friend等）を取得
- `get_platform()` - プラットフォーム名を取得

#### ロボット情報
- `get_self_platform()` - ロボットのプラットフォーム名を取得
- `get_self_user_id()` - ロボットのユーザIDを取得
- `get_self_account_id()` - ロボットのアカウントID（多Botモード）を取得
- `get_self_info()` - ロボットの完全な情報辞書を取得

#### 会話識別子
- `get_target_id()` - 統一されたターゲットIDを取得（グループチャットは `group_id`、チャンネルは `channel_id`、プライベートチャットは `user_id`、group → channel → guild → thread → user の順序で最初の非空値を返す）
- `get_session_id()` - 会話のユニークな識別子を取得、形式は `{platform}:{detail_type}:{target_id}`

### メッセージイベントメソッド

#### メッセージ内容
- `get_message()` - メッセージセグメント配列を取得（OneBot12形式）
- `get_alt_message()` - メッセージの代替テキストを取得
- `get_text()` - 純粋なテキスト内容を取得（`get_alt_message()`のエイリアス）
- `get_message_text()` - 純粋なテキスト内容を取得（`get_alt_message()`のエイリアス）

#### 送信者情報
- `get_user_id()` - 送信者のユーザIDを取得
- `get_user_nickname()` - 送信者のニックネームを取得
- `get_sender()` - 送信者の完全な情報辞書を取得

#### グループ/チャンネル情報
- `get_group_id()` - グループIDを取得（グループメッセージ）
- `get_channel_id()` - チャンネルIDを取得（チャンネルメッセージ）
- `get_guild_id()` - サーバIDを取得（サーバメッセージ）
- `get_thread_id()` - トピック/サブチャンネルIDを取得（トピックメッセージ）

#### @メッセージ関連
- `has_mention()` - @ロボットが含まれているか
- `get_mentions()` - すべての@されたユーザIDリストを取得

### メッセージタイプ判定

#### 基本判定
- `is_message()` - メッセージイベントかどうか
- `is_private_message()` - プライベートチャットメッセージかどうか
- `is_group_message()` - グループチャットメッセージかどうか
- `is_at_message()` - @メッセージかどうか（`has_mention()`のエイリアス）

### 通知イベントメソッド

#### 通知操作者
- `get_operator_id()` - 操作者のIDを取得
- `get_operator_nickname()` - 操作者のニックネームを取得

#### 通知タイプ判定
- `is_notice()` - 通知イベントかどうか
- `is_group_member_increase()` - グループメンバー増加イベント
- `is_group_member_decrease()` - グループメンバー減少イベント
- `is_friend_add()` - 友達追加イベント（`detail_type == "friend_increase"`に一致）
- `is_friend_delete()` - 友達削除イベント（`detail_type == "friend_decrease"`に一致）

### 要求イベントメソッド

#### 要求情報
- `get_comment()` - 要求のコメントを取得

#### 要求タイプ判定
- `is_request()` - 要求イベントかどうか
- `is_friend_request()` - 友達要求かどうか
- `is_group_request()` - グループ要求かどうか

### レプリーメソッド

#### 基本レプリー
- `reply(content, method="Text", at_sender=False, reply_to_message=False, at_users=None, reply_to=None, at_all=False, **kwargs)` - 一般的なレプリー方法
  - `content`: 送信内容（テキスト、URL等）
  - `method`: 送信方法、デフォルトは "Text"、"Image"/"Voice"/"Video"/"File" 等が選択可能
  - `at_sender`: 送信者を@するかどうか（user_idを自動抽出）
  - `quote`: 現在のメッセージを引用して返信するかどうか（message_idを自動抽出）
  - `at_users`: @するユーザリスト、例: `["user1", "user2"]`
  - `reply_to`: 手動で指定した返信メッセージID
  - `at_all`: 全員を@するかどうか
  - `**kwargs`: 余分なパラメータ（例: Mentionメソッドのuser_id）

- `reply_ob12(message)` - OneBot12メッセージセグメントを使って返信
  - `message`: OneBot12メッセージセグメントリストまたは辞書、MessageBuilderを使って構築可能

#### プラットフォーム機能確認
- `supports(method)` - 現在のプラットフォームが特定の送信方法（例: `"Image"`、`"Voice"`）をサポートしているか確認、`bool`を返す
- `available_methods()` - 現在のプラットフォームで利用可能なすべての送信方法をリストで返す

#### 転送機能

> **注意**: 転送機能はアダプタの Send DSL を通じて実現する必要があり、Event 包装クラス自体は直接的な転送メソッドを提供していません。

```python
# メッセージをグループに転送
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # または他のグループIDを指定
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### レプリー待ち機能

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text")` - ユーザーの返信を待つ
  - `prompt`: プロンプトメッセージ、提供された場合ユーザに送信
  - `timeout`: 待機タイムアウト時間（秒）、デフォルト60秒
  - `callback`: 返信を受け取ったときに実行されるコールバック関数
  - `validator`: 返信が有効かどうかを検証する関数
  - `method`: プロンプトメッセージを送信する方法、デフォルトは "Text"、"Image"/"Markdown" 等の非テキスト方法もサポート
  - ユーザーの返信されたEventオブジェクトを返す、タイムアウト時はNoneを返す

#### インタラクティブメソッド

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text")` - 確認対話
  - "True"（確認）/ "False"（否定）/ "None"（タイムアウト）を返す
  - 内部的に中英語の確認語を自動認識、カスタム語集を指定可能
  - `method`: 送信方法、デフォルトは "Text"、"Image"/"Markdown" 等の非テキスト方法もサポート

- `choose(prompt, options, timeout=60.0, method="Text")` - 選択メニュー
  - `options`: 選択肢のテキストリスト
  - 選択肢のインデックス（0ベース）を返す、タイムアウト時はNoneを返す
  - `method`: 送信方法、テキスト系メソッド(Text/Markdown/Html)では選択肢をpromptに結合して1つのメッセージとして送信、豊富なメディアメソッドではまず豊富なメディアコンテンツを送信してからText選択肢リストを送信

- `collect(fields, timeout_per_field=60.0)` - フォーム収集
  - `fields`: フィールドリスト、各項目には`key`、`prompt`、オプションの`validator`、オプションの`method`が含まれる
  - `{key: value}`の辞書を返す、1つのフィールドがタイムアウトした場合はNoneを返す
  - 各フィールドは`method`キーで送信方法を指定可能、例: 画像を収集する場合 `{"key": "avatar", "prompt": "プロフィール画像を送ってください", "method": "Image"}`

- `wait_for(event_type="message", condition=None, timeout=60.0)` - 任意のイベントを待つ
  - `condition`: 条件関数、Trueを返した場合に一致
  - 一致するEventオブジェクトを返す、タイムアウト時はNoneを返す

- `conversation(timeout=60.0)` - 複数ラウンド対話コンテキストを作成
  - `Conversation`オブジェクトを返す、`say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`をサポート
  - `is_active`属性は対話がアクティブかどうかを示す

#### インタラクティブメソッドの例

**confirm() - 確認対話:**

```python
@command("delete", help="データを削除")
async def delete_handler(event):
    if await event.confirm("すべてのデータを削除してもよろしいですか？"):
        sdk.storage.delete("all_data")
        await event.reply("データを削除しました")
    else:
        await event.reply("キャンセルしました")
```

**choose() - 選択メニュー:**

```python
@command("color", help="色を選択")
async def color_handler(event):
    choice = await event.choose("色を選んでください：", ["赤", "緑", "青"])
    if choice is not None:
        colors = ["赤", "緑", "青"]
        await event.reply(f"選択した色は：{colors[choice]}")
```

**collect() - フォーム収集:**

```python
@command("register", help="登録")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "お名前を入力してください："},
        {"key": "age", "prompt": "年齢を入力してください：",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"登録完了！{data['name']}、{data['age']}歳")
```

**非テキスト方法のreply:**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("この画像を見てください：").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> 完全なConversation多ラウンド対話の使い方は [Conversation 多ラウンド対話](../../advanced/conversation.md) を参照してください。

### コマンド情報

#### コマンド基本
- `get_command_name()` - コマンド名を取得
- `get_command_args()` - コマンド引数リストを取得
- `get_command_raw()` - コマンドの元のテキストを取得
- `get_command_info()` - 完全なコマンド情報辞書を取得
- `is_command()` - コマンドかどうか

### プラットフォーム拡張メソッド

アダプタはEvent包装クラスにプラットフォーム固有のメソッドを登録できます。メソッドは対応するプラットフォームのEventインスタンスでのみ利用可能で、他のプラットフォームでアクセスすると`AttributeError`が発生します。

プラットフォームメソッドは`Event.__getattribute__`によって、組み込みメソッドよりも優先的に有効になるため、`confirm`、`choose`、`collect`、`wait_reply`などの組み込みインタラクティブメソッドを覆写して、プラットフォーム特有の実装（例: ボタン、カード等）を提供できます。組み込み実装は`_builtin_*`関数としてエクスポートされ、覆写用に利用できます。

```python
# メールイベント - メールメソッドのみ
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ "Hello"を返す
event.get_chat_type()    # ❌ AttributeError

# Telegramイベント - Telegramメソッドのみ
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ "private"を返す
event.get_subject()      # ❌ AttributeError

# 組み込みメソッドは常に利用可能
event.get_text()         # ✅ どのプラットフォームでも
event.reply("hi")        # ✅ どのプラットフォームでも
```

### 登録されたメソッドの確認

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("email")
# ["get_subject", "get_from", ...]
```

### `hasattr` と `dir` のサポート

```python
hasattr(event, "get_subject")   # platform="email" のみTrueを返す
"get_subject" in dir(event)     # 同上
```

### 跨プラットフォーム拡張（ワイルドカード）

`register_event_method` と `register_event_mixin` は `"*"` をプラットフォーム名として渡すことができ、登録されたメソッドは**すべてのプラットフォーム**のEventインスタンスで利用可能になります。AI対話、コンテキスト管理など、跨プラットフォームで再利用可能な機能に適しています。

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self はEventインスタンス、イベントデータと組み込みメソッドにアクセス可能
    await self.reply(f"AI: {prompt}")
```

登録後、どのプラットフォームのイベントハンドラでも `event.ai_chat(...)` を呼び出すことができます。

メソッドの優先順位（高い順）: プラットフォーム固有のメソッド → ワイルドカードメソッド → 組み込みメソッド → 辞書キーのアクセス。

> アダプタ開発者が拡張メソッドを登録する方法については [イベントシステム API - 跨プラットフォーム拡張ワイルドカード](../../api-reference/event-system.md#跨平台扩展通配符) を参照してください。

## 関連ドキュメント

- [モジュール開発入門](getting-started.md) - 最初のモジュールを作成
- [ベストプラクティス](best-practices.md) - 高品質なモジュールの開発