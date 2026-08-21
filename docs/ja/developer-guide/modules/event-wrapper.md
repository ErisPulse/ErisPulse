# Event 包装クラスの詳細

Event モジュールは、強力な Event 包装クラスを提供し、イベント処理を簡素化します。

各言語の文書へのリンクは、`docs/ja/` を `docs/ja/` に置き換えてください。たとえば、`docs/ja/quick-start.md` は `docs/ja/quick-start.md` に変更します。`README.xx.md` 形式のリンクは、他の言語バージョンを指すため、そのままにしてください。

## コア機能

- **完全な辞書互換性**：Event は dict を継承しています
- **便利なメソッド**：多数の便利なメソッドを提供しています
- **ドットアクセス**：イベントフィールドにドット記法でアクセスできます
- **後方互換性**：すべてのメソッドはオプションです

[**English**](docs/en/core-features.md) | [**日本語**](docs/ja/core-features.md)

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

[**English**](docs/ja/quick-start.md)

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

[**English**](docs/en/quick-start.md) | [**中文**](docs/ja/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## メッセージタイプの判断

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"タイプ: {'プライベートチャット' if is_private else 'グループチャット'}")
```

## 回答機能

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

[**English**](docs/ja/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## コマンド情報の取得

```python
from ErisPulse.Core.Event import command

@command("cmdinfo")
async def cmdinfo_command(event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"コマンド: {cmd_name}, 引数: {cmd_args}")
```

[**English**](docs/en/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## 通知イベントメソッド

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("友達追加ありがとうございます！")
```

[**English**](docs/ja/quick-start.md)

## 方法速查表

### 核心方法

#### 事件基础信息
- `get_id()` - 事件IDを取得
- `get_time()` - イベントのタイムスタンプを取得（Unix秒単位）
- `get_type()` - イベントのタイプを取得（message/notice/request/meta）
- `get_detail_type()` - イベントの詳細タイプを取得（private/group/friend等）
- `get_platform()` - プラットフォーム名を取得

#### ロボット情報
- `get_self_platform()` - ロボットのプラットフォーム名を取得
- `get_self_user_id()` - ロボットのユーザーIDを取得
- `get_self_account_id()` - ロボットのアカウントIDを取得（複数Botモード）
- `get_self_info()` - ロボットの完全な情報辞書を取得

#### 会話識別子
- `get_target_id()` - 統一されたターゲットIDを取得（グループチャットの場合は `group_id`、チャンネルの場合は `channel_id`、プライベートチャットの場合は `user_id`、group → channel → guild → thread → userの順に最初の非空値を取得）
- `get_session_id()` - セッションの一意な識別子を取得、形式は `{platform}:{detail_type}:{target_id}`

### メッセージイベントメソッド

#### メッセージ内容
- `get_message()` - メッセージセグメントの配列を取得（OneBot12形式）
- `get_alt_message()` - メッセージの代替テキストを取得
- `get_text()` - 純粋なテキスト内容を取得（`get_alt_message()`の別名）
- `get_message_text()` - 純粋なテキスト内容を取得（`get_alt_message()`の別名）

#### 送信者情報
- `get_user_id()` - 送信者のユーザーIDを取得
- `get_user_nickname()` - 送信者のニックネームを取得
- `get_sender()` - 送信者の完全な情報辞書を取得

#### グループ/チャンネル情報
- `get_group_id()` - グループIDを取得（グループメッセージ）
- `get_channel_id()` - チャンネルIDを取得（チャンネルメッセージ）
- `get_guild_id()` - サーバーIDを取得（サーバーメッセージ）
- `get_thread_id()` - トピック/サブチャンネルIDを取得（トピックメッセージ）

#### @メッセージ関連
- `has_mention()` - @ロボットを含むかどうか
- `get_mentions()` - すべての@されたユーザーIDのリストを取得

### メッセージタイプ判断

#### 基本判断
- `is_message()` - メッセージイベントかどうか
- `is_private_message()` - プライベートチャットのメッセージかどうか
- `is_group_message()` - グループチャットのメッセージかどうか
- `is_at_message()` - @メッセージかどうか（`has_mention()`の別名）

### 通知イベントメソッド

#### 通知操作者
- `get_operator_id()` - 操作者のIDを取得
- `get_operator_nickname()` - 操作者のニックネームを取得

#### 通知タイプ判断
- `is_notice()` - 通知イベントかどうか
- `is_group_member_increase()` - グループメンバー増加イベント
- `is_group_member_decrease()` - グループメンバー減少イベント
- `is_friend_add()` - 友達追加イベント（`detail_type == "friend_increase"`に一致）
- `is_friend_delete()` - 友達削除イベント（`detail_type == "friend_decrease"`に一致）

### 要求イベントメソッド

#### 要求情報
- `get_comment()` - 要求の付言を取得

#### 要求タイプ判断
- `is_request()` - 要求イベントかどうか
- `is_friend_request()` - 友達要求かどうか
- `is_group_request()` - グループ要求かどうか

### 返信機能

#### 基本返信
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - 一般的な返信メソッド
  - `content`: 送信内容（テキスト、URLなど）
  - `method`: 送信方法、デフォルトは "Text"、"Image"/"Voice"/"Video"/"File" など
  - `at_sender`: 送信者を@するかどうか（自動的に user_id を抽出）
  - `quote`: 現在のメッセージを引用して返信するかどうか（自動的に message_id を抽出）
  - `at_users`: @するユーザーのリスト、例えば `["user1", "user2"]`
  - `reply_to`: 手動で指定された返信メッセージID
  - `at_all`: 全員を@するかどうか
  - `**kwargs`: 余分なパラメータ（例えば Mention 方法の user_id）

- `reply_ob12(message)` - OneBot12メッセージセグメントを使って返信
  - `message`: OneBot12メッセージセグメントのリストまたは辞書、MessageBuilderを使って構築できる

#### プラットフォーム能力の確認
- `supports(method)` - 現在のプラットフォームが特定の送信方法（例えば `"Image"`、`"Voice"`）をサポートしているかどうかを確認し、`bool`を返す
- `available_methods()` - 現在のプラットフォームで利用可能なすべての送信方法をリスト形式で返す

#### 転送機能

> **注意**: 転送機能はアダプタの Send DSL を介して実装する必要があり、Eventラッパークラス自体は直接的な転送メソッドを提供していません。

```python
# メッセージをグループに転送
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # または他のグループIDを指定
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### 返信を待つ機能

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text")` - ユーザーの返信を待つ
  - `prompt`: プロンプトメッセージ、提供された場合、ユーザーに送信される
  - `timeout`: 待機のタイムアウト時間（秒）、デフォルトは60秒
  - `callback`: 返信を受け取ったときに実行されるコールバック関数
  - `validator`: 返信が有効かどうかを検証する関数
  - `method`: プロンプトメッセージの送信方法、デフォルトは "Text"
  - ユーザーの返信のEventオブジェクトを返す、タイムアウトの場合はNoneを返す

#### インタラクティブメソッド

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - 確認対話
  - `True`（確認）/ `False`（否定）/ `None`（タイムアウト）を返す
  - 内部的に中英語の確認語を自動的に認識し、カスタム語集を定義できる
  - `method`: 送信方法、デフォルトは "Text"、"Image"/"Markdown" など非テキスト方式で送信可能
  - `hint`: プロンプトの末尾に自動的に確認語のヒントを追加するかどうか、デフォルトはFalse

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - 選択メニュー
  - `options`: 選択肢のテキストリスト
  - 選択肢のインデックス（0ベース）を返す、タイムアウトの場合はNoneを返す
  - `method`: 送信方法、デフォルトは "Text"、テキスト系メソッド (Text/Markdown/md/Html/h5) はデフォルトで末尾に選択肢を結合
  - `options_format`: 選択肢のフォーマット（デフォルト: "auto"、methodに応じて自動的に組み込みスタイルを選択）
    - `"auto"`: Markdown→箇条書き（`- 1.選択肢`）、Html→順序付きリスト（`<ol>`）、その他→純粋なテキストリスト
    - `"list"`: 各行に1つ、例えば ``1. 選択肢A\n2. 選択肢B``
    - `"inline"`: 1行に表示、例えば ``1.A | 2.B``
    - `"md"`: Markdown 箇条書き
    - `"html"`: Html 順序付きリスト
    - `callable`: 自定義関数、``list[str]``を受け取り``str``を返す
  - `merge_prompt`: 強制的に1つのメッセージに結合して送信するかどうか、デフォルトはFalse
    - `False`（デフォルト）: テキスト系メソッドは自動的に結合；非テキスト系メソッドはまずpromptを送信してからText選択肢を送信
    - `True`: どのようなmethodでも結合して1つのメッセージに送信し、ユーザーが指定したmethodを使って送信する
  - `placeholder`: 選択肢の挿入用のプレースホルダー、デフォルトは`{options}`；promptにこのマークが含まれる場所に選択肢のテキストを置き換える、空文字列に設定すると末尾に常に追加される

- `collect(fields, timeout_per_field=60.0)` - フォーム収集
  - `fields`: フィールドリスト、各項目には`key`、`prompt`、オプションの`validator`、オプションの`method`が含まれる
  - `{key: value}`の辞書を返す、いずれかのフィールドがタイムアウトの場合はNoneを返す
  - 各フィールドは`method`キーで送信方法を指定できる、例えば画像を収集する場合は`{"key": "avatar", "prompt": "プロフィール画像を送ってください", "method": "Image"}`
  - 各フィールドはオプションの`options`キー（リスト）を提供できる、提供された場合、そのフィールドは選択問題になる（自動的にchooseのロジックを呼び出す）
  - 各フィールドはオプションの`options_format`、`merge_prompt`、`placeholder`キーを制御できる、選択肢のフォーマット、メッセージの結合動作、プレースホルダー

- `wait_for(event_type="message", condition=None, timeout=60.0)` - 任意のイベントを待つ
  - `condition`: 条件関数、Trueを返す場合に一致する
  - 一致するEventオブジェクトを返す、タイムアウトの場合はNoneを返す

- `conversation(timeout=60.0)` - マルチラウンド対話コンテキストを作成
  - `Conversation`オブジェクトを返す、`say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`をサポート
  - `is_active`属性は対話がアクティブかどうかを示す

#### インタラクティブメソッドの例

**confirm() - 確認対話：**

```python
@command("delete", help="データを削除")
async def delete_handler(event):
    if await event.confirm("すべてのデータを削除してもよろしいですか？"):
        sdk.storage.delete("all_data")
        await event.reply("データが削除されました")
    else:
        await event.reply("キャンセルされました")
```

**confirm() - ヒント付き：**

```python
# hint=True はプロンプトの末尾に "（はい/いいえ）" を追加する
if await event.confirm("続行してもよろしいですか？", hint=True):
    await event.reply("続行しました")
# ユーザーに表示される内容：続行してもよろしいですか？（はい/いいえ）
```

**choose() - 選択メニュー：**

```python
@command("color", help="色を選択")
async def color_handler(event):
    choice = await event.choose("色を選択してください：", ["赤", "緑", "青"])
    if choice is not None:
        colors = ["赤", "緑", "青"]
        await event.reply(f"選択した色は：{colors[choice]}")
```

**choose() - 選択肢のフォーマットとメッセージの結合：**

```python
# inline形式：選択肢を1行に表示
choice = await event.choose("選択してください：", ["A", "B", "C"], options_format="inline")
# 出力：1.A | 2.B | 3.C

# 自定義フォーマット
choice = await event.choose("選択してください：", ["猫", "犬"],
    options_format=lambda opts: " / ".join(opts))
# 出力：猫 / 犬

# options_format="auto"（デフォルト）：methodに応じて自動的に組み込みスタイルを選択
# Markdown → 箇条書き
choice = await event.choose(
    "## 選択してください", ["猫", "犬"],
    method="Markdown",  # autoは自動的にmdリストと認識
)
# 出力：
# ## 選択してください
# - 1. 猫
# - 2. 犬

# Html → 順序付きリスト
choice = await event.choose(
    "<h2>選択してください</h2>", ["猫", "犬"],
    method="Html", merge_prompt=True,  # autoは自動的にhtmlリストと認識
)
# 出力：
# <h2>選択してください</h2>
# <ol><li>1. 猫</li><li>2. 犬</li></ol>

# 結合モード + プレースホルダー
choice = await event.choose(
    "## 選択してください\n{options}\n番号を返信してください",
    ["猫", "犬"],
    method="Markdown", merge_prompt=True,
)

# 自定義プレースホルダー
choice = await event.choose(
    "選択してください: [choices]",
    ["猫", "犬"],
    placeholder="[choices]",
)
```

**collect() - フォーム収集：**

```python
@command("register", help="登録")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "お名前を入力してください："},
        {"key": "age", "prompt": "年齢を入力してください：",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"登録が完了しました！{data['name']}、{data['age']}歳")
```

**非テキスト方法のreply：**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("この画像を見てください：").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> 完全なConversationマルチラウンド対話の使い方は [Conversationマルチラウンド対話](../../advanced/conversation.md) を参照してください。

### コマンド情報

#### コマンドの基本
- `get_command_name()` - コマンド名を取得
- `get_command_args()` - コマンド引数のリストを取得
- `get_command_raw()` - コマンドの元のテキストを取得
- `get_command_info()` - 完全なコマンド情報の辞書を取得
- `is_command()` - コマンドかどうか

### 元のデータ

- `get_raw()` - プラットフォームの元のイベントデータを取得
- `get_raw_type()` - プラットフォームの元のイベントタイプを取得

### プラットフォーム拡張メソッド

アダプタはEventラッパークラスにプラットフォーム固有のメソッドを登録することができます。メソッドは対応するプラットフォームのEventインスタンスでのみ利用可能で、他のプラットフォームでアクセスすると`AttributeError`が発生します。

プラットフォームメソッドは`Event.__getattribute__`によって、組み込みメソッドよりも優先的に有効になります。そのため、`confirm`、`choose`、`collect`、`wait_reply`などの組み込みインタラクティブメソッドを覆い、プラットフォーム特有の実装（ボタン、カードなど）を提供することができます。組み込みの実装は覆い書き可能な`_builtin_*`関数としてエクスポートされています。

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
event.get_text()         # ✅ すべてのプラットフォームで利用可能
event.reply("hi")        # ✅ すべてのプラットフォームで利用可能
```

### 登録されたメソッドの照会

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("email")
# ["get_subject", "get_from", ...]
```

### `hasattr` と `dir` のサポート

```python
hasattr(event, "get_subject")   # platform="email"の場合のみTrueを返す
"get_subject" in dir(event)     # 同上
```

### 跨プラットフォーム拡張（ワイルドカード）

`register_event_method` と `register_event_mixin` は `"*"` をプラットフォーム名として渡すことができ、登録されたメソッドは**すべてのプラットフォーム**のEventインスタンスで利用可能です。AI対話、コンテキスト管理など、跨プラットフォームで再利用可能な機能に適しています。

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self はEventインスタンス、イベントデータと組み込みメソッドにアクセス可能
    await self.reply(f"AI: {prompt}")
```

登録後、どのプラットフォームのイベントハンドラーでも `event.ai_chat(...)` を呼び出すことができます。

メソッドの優先順位（高い順）：プラットフォーム固有のメソッド → ワイルドカードメソッド → 組み込みメソッド → 辞書キーのアクセス。

> アダプタ開発者が拡張メソッドを登録する方法は [イベントシステムAPI - 跨プラットフォーム拡張（ワイルドカード）](../../api-reference/event-system.md#跨平台扩展通配符) を参照してください。

## 関連ドキュメント

- [モジュール開発入門](getting-started.md) - 最初のモジュールを作成する
- [ベストプラクティス](best-practices.md) - 高品質なモジュールを開発する