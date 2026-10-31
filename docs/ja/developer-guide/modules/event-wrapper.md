# Event 包装类详解

> [!NOTE]
> **L1 核心必読**——「読むべき道筋」の5つの核心ドキュメントの1つ、モジュール開発に必須。

プロセッサの `event` パラメータが直接 `.get_text()` / `.reply()` / `.wait_reply()` を呼べるのは、Event 包装クラスのおかげです。本記事では、Event 包装クラスの全メソッド一覧を紹介します。イベントハンドラを書く際には、このリストを参照してください。メソッドの署名と動作は、ここを基準とします。

## event パラメータに型注釈を追加する

イベントハンドラの `event` パラメータは **Event 包装クラス**（dict のサブクラス）です。型注釈を付けることを強く推奨します：

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE が便利なメソッドを自動補完
    await event.reply(text)   # 拼写ミスは静的チェック時に発見可能
```

型注釈を付けないと、IDE は Event 上のメソッド（`get_text()` / `reply()` / `wait_reply()` / プラットフォーム拡張メソッド）を認識できず、すべて手動で記述する必要があります。

> **注意**：イベントハンドラのコールバックの `event` は **Event 包装クラス**（注釈は `Event`）です。一方、モジュールのライフサイクルメソッド `on_load` / `on_unload` の `event` は普通の **dict**（注釈は `dict`）です。これらを混同しないでください。

## 核心特性

- **完全に dict に互換性がある**：Event は dict を継承
- **便利なメソッド**：多数の便利なメソッドを提供
- **点アクセス**：ドット演算子でイベントフィールドにアクセス可能
- **後方互換性**：すべてのメソッドはオプション

## 核心フィールドメソッド

```python
from ErisPulse.Core.Event import command

@command("info")
async def info_command(event: Event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, プラットフォーム: {platform}, 時間: {time}")
```

## メッセージイベントメソッド

```python
from ErisPulse.Core.Event import message

@message.on_private_message()
async def private_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"こんにちは、{nickname}！")
```

## メッセージタイプの判断

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event: Event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"タイプ: {'プライベートチャット' if is_private else 'グループチャット'}")
```

## 回答機能

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event: Event):
    await event.reply("名前を入力してください:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}！")

@command("price")
async def price_command(event: Event):
    await event.reply("金額を入力してください（例：5元）:")
    # 回答は正規表現に一致する必要があります。一致しない場合は、タイムアウトまで待機します。
    reply = await event.wait_reply(timeout=30, regex=r"\d+\s*元")
    if reply:
        await event.reply(f"受信金額: {reply.get_text()}")
```

## 会話の高度な機能

> [!NOTE]
> 本節の機能は ErisPulse **2.8.0+** が必要です。

```python
# 会話のリマインダー：5分間返信がなければリマインダーを送信し、ユーザーが返信すると自動的にキャンセル
reminder = event.remind(300, "まだですか？話したくない場合は「退出」を送信してください")
reminder.cancel()  # 手動でキャンセルすることも可能です

# タイムアウトの昇格：時間内に必ず到達（返信でキャンセルされない）、長時間処理がなければ管理者に通知
event.escalate(1800, lambda e: notify_master("工事件がタイムアウトしました"))

# 複数ルートの待機：「同意」および「拒否」を同時に待機し、先着順
which, reply = await event.select(
    event.expect(pattern="同意*", user="10001"),
    event.expect(pattern="拒否*", user="10002"),
    timeout=60,
)
if which is None:
    await event.reply("承認が受け取られませんでした")

# 会話レベルの待機：同じグループ内の誰からの返信でも対象になります（グループ協力）
reply = await event.wait_reply(session=True, prompt="誰かが回答してくれませんか？")

# 会話の受信箱：現在の会話の最近20件のメッセージ（ロボット含む、AIコンテキスト/再送防止のベース）
messages = await event.history(20)

# メッセージトランザクション：例外が発生した場合、トランザクション内で送信されたメッセージは自動的に撤回されます
async with event.message_tx():
    await event.reply("処理中、少々お待ちください...")
    result = await do_something()
    await event.reply(f"完了: {result}")
```

## コマンド情報の取得

```python
from ErisPulse.Core.Event import command

@command("cmdinfo")
async def cmdinfo_command(event: Event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"コマンド: {cmd_name}, 引数: {cmd_args}")
```

## 通知イベントメソッド

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event: Event):
    await event.reply("友達追加ありがとうございます！")
```

## メソッドの速見表

### 核心メソッド

#### イベントの基本情報
- `get_id()` - イベントIDを取得
- `get_time()` - イベントのタイムスタンプ（Unix秒）
- `get_type()` - イベントのタイプ（message/notice/request/meta）
- `get_detail_type()` - イベントの詳細タイプ（private/group/friend等）
- `get_platform()` - プラットフォーム名を取得

#### ロボット情報
- `get_self_platform()` - ロボットのプラットフォーム名を取得
- `get_self_user_id()` - ロボットのユーザーIDを取得
- `get_self_account_id()` - ロボットのアカウントID（複数ロボットモード）
- `get_self_info()` - ロボットの完全な情報の辞書を取得

#### 会話識別子
- `get_target_id()` - 統一されたターゲットIDを取得（グループチャットは `group_id`、チャンネルは `channel_id`、プライベートチャットは `user_id`、グループ → チャンネル → グuild → スレッド → ユーザーの順で最初の非空値）
- `get_session_id()` - 会話の唯一の識別子を取得、形式は `{platform}:{detail_type}:{target_id}`

### メッセージイベントメソッド

#### メッセージ内容
- `get_message()` - メッセージセグメントの配列を取得（OneBot12形式）
- `get_alt_message()` - メッセージの代替テキストを取得
- `get_text()` - 純粋なテキスト内容を取得（`get_alt_message()`の別名）
- `get_message_text()` - 純粋なテキスト内容を取得（`get_alt_message()`の別名）

#### 送信者情報
- `get_user_id()` - 送信者のユーザーIDを取得
- `get_user_nickname()` - 送信者のニックネームを取得
- `get_sender()` - 送信者の完全な情報の辞書を取得

#### グループ/チャンネル情報
- `get_group_id()` - グループIDを取得（グループメッセージ）
- `get_channel_id()` - チャンネルIDを取得（チャンネルメッセージ）
- `get_guild_id()` - サーバーIDを取得（サーバーメッセージ）
- `get_thread_id()` - トピック/サブチャンネルIDを取得（トピックメッセージ）

#### @メッセージ関連
- `has_mention()` - @ロボットを含むか
- `get_mentions()` - すべての@されたユーザーIDのリストを取得

### メッセージタイプの判断

#### 基本判断
- `is_message()` - メッセージイベントか
- `is_private_message()` - プライベートチャットメッセージか
- `is_group_message()` - グループチャットメッセージか
- `is_at_message()` - @メッセージか（`has_mention()`の別名）

### 通知イベントメソッド

#### 通知操作者
- `get_operator_id()` - 操作者のIDを取得
- `get_operator_nickname()` - 操作者のニックネームを取得

#### 通知タイプの判断
- `is_notice()` - 通知イベントか
- `is_group_member_increase()` - グループメンバー増加イベントか
- `is_group_member_decrease()` - グループメンバー減少イベントか
- `is_friend_add()` - 友達追加イベントか（`detail_type == "friend_increase"`に一致）
- `is_friend_delete()` - 友達削除イベントか（`detail_type == "friend_decrease"`に一致）

### リクエストイベントメソッド

#### リクエスト情報
- `get_comment()` - リクエストのコメントを取得

#### リクエストタイプの判断
- `is_request()` - リクエストイベントか
- `is_friend_request()` - 友達リクエストか
- `is_group_request()` - グループリクエストか

### 回答機能

#### 基本回答
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - 一般的な回答メソッド
  - `content`: 送信内容（テキスト、URLなど）
  - `method`: 送信方法、デフォルトは "Text"、"Image"/"Voice"/"Video"/"File" など
  - `at_sender`: 送信者を@するか（user_idを自動抽出）
  - `quote`: 現在のメッセージを引用して返信するか（message_idを自動抽出）
  - `at_users`: @するユーザーIDのリスト、例: `["user1", "user2"]`
  - `reply_to`: 手動で指定する返信メッセージID
  - `at_all`: 全員を@するか
  - `**kwargs`: 余分なパラメータ（例: Mentionメソッドのuser_id）

- `reply_ob12(message)` - OneBot12メッセージセグメントを使って回答
  - `message`: OneBot12メッセージセグメントのリストまたは辞書、MessageBuilderを使って構築

#### プラットフォーム機能の確認
- `supports(method)` - 現在のプラットフォームが特定の送信方法（例: `"Image"`、`"Voice"`）をサポートするか、`bool`を返す
- `available_methods()` - 現在のプラットフォームで利用可能な送信方法のリストを返す

#### 転送機能

> **注意**：転送機能はアダプタの Send DSL によって実現されるため、Event 包装クラス自体には直接の転送メソッドは提供されていません。

```python
# メッセージをグループに転送
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # または他のグループIDを指定
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### 返信を待つ機能

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - ユーザーの返信を待つ
  - `prompt`: プロンプトメッセージ、提供された場合はユーザーに送信
  - `timeout`: 待機のタイムアウト時間（秒）、デフォルトは60秒
  - `callback`: 回答を受け取ったときに実行するコールバック関数
  - `validator`: 回答が有効かどうかを検証する関数
  - `method`: プロンプトメッセージの送信方法、デフォルトは "Text"、"Image"/"Markdown" など
  - `pattern`: glob 通配符（`*` / `?` / `[seq]`）、返信テキストが一致する必要がある、一致しない場合は待機を続ける
  - `regex`: 正規表現、返信テキストが一致する必要がある（`pattern` と `regex` はどちらか一方）
  - 返信された Event オブジェクトを返す、タイムアウト時は None を返す

#### 会話機能

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - 確認会話
  - 返り値は `True`（確認）/ `False`（否定）/ `None`（タイムアウト）
  - 内部的に中英確認語が自動認識され、カスタム語集も指定可能
  - `method`: 送信方法、デフォルトは "Text"、"Image"/"Markdown" など非テキスト方法もサポート
  - `hint`: プロンプト末尾に確認語のヒントを自動追加するか、デフォルトは False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - 選択メニュー
  - `options`: 選択肢のテキストリスト
  - 返り値は選択肢のインデックス（0-based）、タイムアウト時は None を返す
  - `method`: 送信方法、デフォルトは "Text"、テキスト系メソッド (Text/Markdown/md/Html/h5) はデフォルトで選択肢を末尾にマージ
  - `options_format`: 選択肢のフォーマット（デフォルト: "auto"、method に応じて自動選択）
    - `"auto"`: Markdown→無序リスト（`- 1.選択肢`）、Html→有序リスト（`<ol>`）、その他の場合は純粋なテキストリスト
    - `"list"`: 各行に1つ、例: ``1. 選択肢A\n2. 選択肢B``
    - `"inline"`: 単行で表示、例: ``1.A | 2.B``
    - `"md"`: Markdown 無序リスト
    - `"html"`: Html 有序リスト
    - `callable`: 自定義関数、``list[str]`` を受け取り ``str`` を返す
  - `merge_prompt`: 強制的に1つのメッセージとして送信するか、デフォルトは False
    - `False`（デフォルト）: テキスト系メソッドは自動的にマージ、非テキストメソッドはまず prompt を送信してから Text 選択肢を送信
    - `True`: どんな method でも1つのメッセージにマージし、指定された method で送信
  - `placeholder`: 選択肢の置換文字、デフォルトは `{options}`、prompt にこの文字が含まれる場所に選択肢テキストを置換、空文字にすると常に末尾に追加

- `collect(fields, timeout_per_field=60.0)` - フォーム収集
  - `fields`: フィールドリスト、各項目には `key`、`prompt`、オプションの `validator`、オプションの `method` が含まれる
  - 返り値は `{key: value}` の辞書、任意のフィールドがタイムアウトした場合は None を返す
  - 各フィールドは `method` キーで送信方法を指定できる、例: 画像を収集する際には `{"key": "avatar", "prompt": "プロフィール画像を送ってください", "method": "Image"}`
  - 各フィールドは `options` キー（リスト）を提供できる、提供された場合は選択問題になる（`choose` のロジックを自動的に呼び出す）
  - 各フィールドは `options_format`、`merge_prompt`、`placeholder` キーを指定できる、オプションのフォーマット、メッセージのマージ動作、および置換文字を制御する

- `wait_for(event_type="message", condition=None, timeout=60.0)` - 任意のイベントを待つ
  - `condition`: 条件関数、True を返す場合に一致
  - 返り値は一致する Event オブジェクト、タイムアウト時は None を返す

- `conversation(timeout=60.0)` - 複数ラウンドの会話コンテキストを作成
  - 返り値は `Conversation` オブジェクト、`say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()` がサポートされる
  - `is_active` 属性は会話がアクティブかどうかを示す

#### 会話機能の例

**confirm() - 確認会話：**

```python
@command("delete", help="データを削除")
async def delete_handler(event: Event):
    if await event.confirm("すべてのデータを削除しますか？"):
        sdk.storage.delete("all_data")
        await event.reply("データを削除しました")
    else:
        await event.reply("キャンセルしました")
```

**confirm() - ヒント付き：**

```python
# hint=True はプロンプト末尾に "（はい/いいえ）" を追加します
if await event.confirm("続行しますか？", hint=True):
    await event.reply("続行しました")
# ユーザーが見るのは：続行しますか？（はい/いいえ）
```

**choose() - 選択メニュー：**

```python
@command("color", help="色を選択")
async def color_handler(event: Event):
    choice = await event.choose("色を選択してください：", ["赤", "緑", "青"])
    if choice is not None:
        colors = ["赤", "緑", "青"]
        await event.reply(f"選択した色は：{colors[choice]}")
```

**choose() - 選択肢のフォーマットとメッセージのマージ：**

```python
# inline 形式：選択肢を1行に表示
choice = await event.choose("選択してください：", ["A", "B", "C"], options_format="inline")
# 出力：1.A | 2.B | 3.C

# 自定義フォーマット
choice = await event.choose("選択してください：", ["猫", "犬"],
    options_format=lambda opts: " / ".join(opts))
# 出力：猫 / 犬

# options_format="auto"（デフォルト）：method に応じて自動的に組み込みスタイルを選択
# Markdown → 無序リスト
choice = await event.choose(
    "## 選択してください", ["猫", "犬"],
    method="Markdown",  # auto は md 列表を自動認識
)
# 出力：
# ## 選択してください
# - 1. 猫
# - 2. 犬

# Html → 有序リスト
choice = await event.choose(
    "<h2>選択してください</h2>", ["猫", "犬"],
    method="Html", merge_prompt=True,  # auto は html 列表を自動認識
)
# 出力：
# <h2>選択してください</h2>
# <ol><li>1. 猫</li><li>2. 犬</li></ol>

# マージモード + 置換文字
choice = await event.choose(
    "## 選択してください\n{options}\n番号を返信してください",
    ["猫", "犬"],
    method="Markdown", merge_prompt=True,
)

# 自定義置換文字
choice = await event.choose(
    "選択してください: [choices]",
    ["猫", "犬"],
    placeholder="[choices]",
)
```

**collect() - フォーム収集：**

```python
@command("register", help="登録")
async def register_handler(event: Event):
    data = await event.collect([
        {"key": "name", "prompt": "名前を入力してください："},
        {"key": "age", "prompt": "年齢を入力してください：",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"登録完了！{data['name']}、{data['age']}歳")
```

**非 Text メソッドの reply：**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("画像を見てください：").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> 完全な Conversation 多ラウンド会話の使い方は [Conversation 多ラウンド会話](../../advanced/conversation.md) を参照してください。

### コマンド情報

#### コマンドの基本
- `get_command_name()` - コマンド名を取得
- `get_command_args()` - コマンド引数のリストを取得
- `get_command_raw()` - コマンドの元のテキストを取得
- `get_command_info()` - 完全なコマンド情報の辞書を取得
- `is_command()` - コマンドか

### 元のデータ

- `get_raw()` - プラットフォームの元のイベントデータを取得
- `get_raw_type()` - プラットフォームの元のイベントタイプを取得

### プラットフォーム拡張メソッド

アダプタは Event 包装クラスにプラットフォーム固有のメソッドを登録できます。メソッドは対応するプラットフォームの Event インスタンスでのみ利用可能で、他のプラットフォームでアクセスすると `AttributeError` が発生します。

プラットフォームメソッドは `Event.__getattribute__` によって、組み込みメソッドよりも優先的に有効になるため、`confirm`、`choose`、`collect`、`wait_reply` などの組み込みインタラクティブメソッドを覆い、プラットフォーム固有の実装（例: ボタン、カードなど）を提供できます。組み込み実装は覆い書きする側に `_builtin_*` 関数として導出されます。

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
hasattr(event, "get_subject")   # platform="email" のみで True を返す
"get_subject" in dir(event)     # 同上
```

### 跨プラットフォーム拡張（ワイルドカード）

`register_event_method` と `register_event_mixin` は `"*"` をプラットフォーム名として渡すことができ、登録されたメソッドは**すべてのプラットフォーム**の Event インスタンスで利用可能になります。AI会話、コンテキスト管理など、跨プラットフォームで再利用可能な機能に適しています。

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self は Event インスタンス、イベントデータと組み込みメソッドにアクセス可能
    await self.reply(f"AI: {prompt}")
```

登録後、どのプラットフォームのイベントハンドラでも `event.ai_chat(...)` を呼び出すことができます。

メソッドの優先順位（高い順）：プラットフォーム固有メソッド → ワイルドカードメソッド → 組み込みメソッド → dict キーのアクセス。

> アダプタ開発者が拡張メソッドを登録する方法については [イベントシステム API - 跨プラットフォーム拡張ワイルドカード](../../api-reference/event-system.md#跨プラットフォーム拡張ワイルドカード) を参照してください。

## 関連ドキュメント

### モジュール開発の継続

- [モジュール開発入門](getting-started.md) - 最初のモジュールを作成
- [モジュール開発ベストプラクティス](best-practices.md) - 高品質なモジュールの開発

### インタラクティブ機能の深掘り

- [Conversation 多ラウンド会話](../../advanced/conversation.md) - `wait_reply` 以上の完全な会話エンジン（収集、検証、分岐ジャンプ）