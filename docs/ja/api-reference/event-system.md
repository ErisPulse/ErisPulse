# イベントシステム API

本文档详细介绍了 ErisPulse 事件系统的 API。

イベントシステムは、プラットフォームイベントを 5 つのタイプのハンドラに分類して配信します。

```mermaid
flowchart LR
    A["プラットフォームイベント<br/>（OneBot12 標準）"] --> B{"イベントタイプ"}
    B --> C["command<br/>コマンドハンドラ"]
    B --> D["message<br/>メッセージハンドラ"]
    B --> E["notice<br/>通知ハンドラ"]
    B --> F["request<br/>リクエストハンドラ"]
    B --> G["meta<br/>メタイベントハンドラ"]
    C & D & E & F & G --> H["Eventラッパークラス<br/>reply / get_text / done 等"]
```

## Command コマンドモジュール

### コマンドの登録

```python
from ErisPulse.Core.Event import command

# 基本コマンド
@command("hello", help="挨拶を送信")
async def hello_handler(event):
    await event.reply("こんにちは！")

# 別名付きコマンド
@command(["help", "h"], aliases=["help", "h"], help="ヘルプを表示")
async def help_handler(event):
    pass

# 権限付きコマンド
def is_admin(event):
    return event.get("user_id") in admin_ids

@command("admin", permission=is_admin, help="管理者コマンド")
async def admin_handler(event):
    pass

# 非表示コマンド
@command("secret", hidden=True, help="秘密コマンド")
async def secret_handler(event):
    pass

# コマンドグループ
@command("admin.reload", group="admin", help="モジュールを再ロード")
async def reload_handler(event):
    pass

# サブコマンド（スペースで区切られた複数のトークンを持つコマンド名）
# 最長前接辞マッチングを使用：/admin add x は admin add（args が ["x"]）に優先的にマッチ；
# 子コマンドに permission が宣言されていない場合、親コマンドの最近の ancestor コマンドの permission を継承
@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    pass
```

### コマンド情報

すべてのコマンドクエリAPIは、オプションの**セッションコンテキスト**をサポートします：`event=`（Event または dict）または明示的な `platform=` / `bot_id=` / `session_id=`（event と重複する場合は明示的な引数が優先）を渡すことで、現在のセッションで利用できないモジュールのコマンドをスコープの次元でフィルタリングします（advanced/scope.mdを参照）；
すべてがオプションのキーワード引数であり、渡さない場合は既定の全量の動作を維持します。

```python
# コマンドヘルプを取得
help_text = command.help()

# セッション感知ヘルプ：現在のセッションで利用可能なコマンドのみを表示
help_text = command.help(event=event)

# 特定のコマンドを取得（マージされた有効なパラメータを返す；セッションで利用できない場合は None を返す）
cmd_info = command.get_command("admin")
cmd_info = command.get_command("admin", event=event)

# すべてのコマンドを取得（セッション感知時、利用できないモジュールのコマンドをフィルタリング）
all_commands = command.get_commands()
all_commands = command.get_commands(event=event)

# コマンドグループ内のすべてのコマンドを取得（セッション感知フィルタリングをサポート）
admin_commands = command.get_group_commands("admin")
admin_commands = command.get_group_commands("admin", event=event)

# すべての表示可能なコマンドを取得
visible_commands = command.get_visible_commands()

# セッション感知の表示可能なコマンド（event または明示的なキーワード引数のいずれかで可能）
visible_commands = command.get_visible_commands(event=event)
visible_commands = command.get_visible_commands(
    platform=event.get("platform"),
    bot_id=event.get_self_account_id(),
    session_id=event.get_session_id(),
)
```

### レプリィ待ち

```python
# ユーザーの返信を待つ
@command("ask", help="ユーザー情報を尋ねる")
async def ask_command(event):
    reply = await command.wait_reply(
        event,
        prompt="名前を入力してください:",  # すでに送信済み
        timeout=30.0
    )
    
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}！")

# 検証付きのレプリィ待ち
def validate_age(event_data):
    try:
        age = int(event_data.get_text())
        return 0 <= age <= 150
    except ValueError:
        return False

@command("age", help="ユーザーの年齢を尋ねる")
async def age_command(event):
    await event.reply("年齢を入力してください:")
    
    reply = await command.wait_reply(
        event,
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"年齢は {age} 歳です")

# コールバック付きのレプリィ待ち
async def handle_confirmation(reply_event):
    text = reply_event.get_text().lower()
    if text in ["はい", "yes", "y"]:
        await event.reply("操作が確認されました！")
    else:
        await event.reply("操作がキャンセルされました。")

@command("confirm", help="操作を確認")
async def confirm_command(event):
    await command.wait_reply(
        event,
        prompt="はいまたはいいえを入力してください:",
        callback=handle_confirmation
    )
```

## Message メッセージモジュール

### メッセージイベント

```python
from ErisPulse.Core.Event import message

# すべてのメッセージを監視
@message.on_message()
async def message_handler(event):
    sdk.logger.info(f"メッセージを受け取りました: {event.get_text()}")

# プライベートメッセージを監視
@message.on_private_message()
async def private_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"プライベートメッセージの送信元: {user_id}")

# グループメッセージを監視
@message.on_group_message()
async def group_handler(event):
    group_id = event.get_group_id()
    sdk.logger.info(f"グループメッセージの送信元: {group_id}")

# @メッセージを監視
@message.on_at_message()
async def at_handler(event):
    mentions = event.get_mentions()
    sdk.logger.info(f"メンションされたユーザー: {mentions}")
```

### 条件付き監視

```python
# 優先度を使って実行順序を制御
@message.on_message(priority=10)  # 数値が大きいほど優先度が高い
async def high_priority_handler(event):
    pass

# ハンドラ内部で条件フィルタリングを実装
@message.on_message()
async def filtered_handler(event):
    if "キーワード" not in event.get_text():
        return
    # キーワードを含むメッセージを処理
    pass
```

## Notice 通知モジュール

### 通知イベント

```python
from ErisPulse.Core.Event import notice

# フレンド追加
@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    await event.reply("フレンド追加ありがとうございます！")

# フレンド削除
@notice.on_friend_remove()
async def friend_remove_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"フレンド削除: {user_id}")

# グループメンバー追加
@notice.on_group_increase()
async def member_increase_handler(event):
    user_id = event.get_user_id()
    await event.reply(f"新メンバーを歓迎します！")

# グループメンバー削除
@notice.on_group_decrease()
async def member_decrease_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"グループメンバーの退会: {user_id}")
```

## Request リクエストモジュール

### リクエストイベント

```python
from ErisPulse.Core.Event import request

# フレンドリクエスト
@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    sdk.logger.info(f"フレンドリクエスト: {user_id}, コメント: {comment}")

# グループ招待リクエスト
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"グループ招待: {group_id}, 送信元: {user_id}")
```

## Meta メタイベントモジュール

### メタイベント

```python
from ErisPulse.Core.Event import meta

# 接続イベント
@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"プラットフォーム {platform} に接続成功")

# 接続切断イベント
@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"プラットフォーム {platform} が切断されました")

# ハートビートイベント
@meta.on_heartbeat()
async def heartbeat_handler(event):
    sdk.logger.debug("ハートビートを受信しました")
```

### Bot 状態照会

アダプタが meta イベントを送信すると、フレームワークは自動的に Bot 状態を追跡します。照会 API とライフサイクルイベントの監視は [アダプタシステム API - Bot 状態管理](adapter-system.md#bot-状態管理) を参照してください。

## Event ラッパークラス

Event モジュールのイベントハンドラは、dict を継承した Event ラッパークラスのインスタンスを受け取り、便利なメソッドを提供します。

### 核心メソッド

```python
# イベント情報を取得
event_id = event.get_id()
event_time = event.get_time()
event_type = event.get_type()
detail_type = event.get_detail_type()
platform = event.get_platform()

# ロボット情報を取得
self_platform = event.get_self_platform()
self_user_id = event.get_self_user_id()
self_info = event.get_self_info()
```

### セッション識別子

```python
# 統一されたターゲット ID：グループチャットは group_id を返し、プライベートチャットは user_id を返す、以此类推
target_id = event.get_target_id()

# セッションの唯一の識別子、形式: {platform}:{detail_type}:{target_id}
session_id = event.get_session_id()
# 例: "telegram:private:12345"、"qq:group:67890"
```

`get_target_id()` は、`group_id` → `channel_id` → `guild_id` → `thread_id` → `user_id` の順に最初の非空値を返します。これは、コンテキスト管理、状態の保存など、セッションを統一的に識別する必要がある場面に適しています。

### メッセージメソッド

```python
# メッセージ内容を取得
message_segments = event.get_message()
alt_message = event.get_alt_message()
text = event.get_text()

# 送信者情報を取得
user_id = event.get_user_id()
nickname = event.get_user_nickname()
sender = event.get_sender()

# グループ情報を取得
group_id = event.get_group_id()

# メッセージタイプを判断
is_msg = event.is_message()
is_private = event.is_private_message()
is_group = event.is_group_message()

# @メッセージ関連
is_at = event.is_at_message()
has_mention = event.has_mention()
mentions = event.get_mentions()
```

### コマンド情報

```python
# コマンド情報を取得
cmd_name = event.get_command_name()
cmd_args = event.get_command_args()
cmd_raw = event.get_command_raw()

# それがコマンドかどうかを判断
is_cmd = event.is_command()
```

### レプリィ機能

```python
# 基本的なレプリィ
await event.reply("これはメッセージです")

# 送信方法を指定
await event.reply("http://example.com/image.jpg", method="Image")

# @ユーザーと返信メッセージを含む
await event.reply("こんにちは", at_users=["user1"], reply_to="msg_id")

# @全員
await event.reply("お知らせ", at_all=True)

# プラットフォーム固有の修飾方法を使用（via パラメータ）
await event.reply("ボードの内容", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])

# 送信チェーンを取得し、修飾方法と送信方法を自由に追加（複数の修飾/アクション型メソッドに適しています）
await event.send_chain().Expire(3600).Board("ボードの内容")
await event.send_chain().DismissBoard()

# OneBot12 メッセージセグメントを使って返信
from ErisPulse.Core.Event import MessageBuilder
msg = MessageBuilder().text("Hello").image("url").build()
await event.reply_ob12(msg)

# レプリィを待つ
reply = await event.wait_reply(timeout=30)
```

### プラットフォーム能力照会

```python
# 現在のプラットフォームが特定の送信方法をサポートしているかをチェック
if event.supports("Image"):
    await event.reply(url, method="Image")

# 現在のプラットフォームで利用可能なすべての送信方法をリストアップ
methods = event.available_methods()
# ["Text", "Image", "Voice", ...]
```

### レプリィメソッド

`reply()` メソッドは、`method` パラメータを使って送信タイプを指定し、2つの便利なブール値パラメータもサポートします：

```python
# 簡単なテキスト返信
await event.reply("こんにちは")

# 送信者に@を付けて返信
await event.reply("こんにちは", at_sender=True)

# 現在のメッセージを引用して返信
await event.reply("受信しました", quote=True)

# 組み合わせて使用
await event.reply("受信しました", at_sender=True, quote=True)

# 画像を送信（method パラメータを使用）
if event.supports("Image"):
    await event.reply("http://example.com/img.jpg", method="Image")
else:
    await event.reply("[画像] http://example.com/img.jpg")
```

**パラメータの説明**：

| パラメータ | 型 | 説明 |
|------|------|------|
| `content` | str | 送信内容 |
| `method` | str | 送信方法、デフォルトは "Text"、"Image"/"Voice"/"Video"/"File" など |
| `at_sender` | bool | 送信者に@を付けるかどうか（user_id を自動的に抽出） |
| `quote` | bool | 現在のメッセージを引用して返信するかどうか（message_id を自動的に抽出） |
| `at_users` | list[str] | @するユーザーのリスト |
| `reply_to` | str | 手動で指定する返信メッセージの ID |
| `at_all` | bool | 全員に@するかどうか |

### 交互メソッド

```python
# confirm — 確認対話（True/False/None を返す）
if await event.confirm("この操作を実行してもよろしいですか？"):
    await event.reply("確認されました")

# Text 以外の方法で確認の提示を送信
if await event.confirm("http://example.com/image.jpg", method="Image"):
    await event.reply("画像の確認が完了しました")

# choose — 選択メニュー（選択肢のインデックスまたは None を返す）
choice = await event.choose("色を選択してください：", ["赤", "緑", "青"])

# options_format="auto"（デフォルト）method に応じてスタイルを自動選択：
# Markdown→箇条書き（- 1.選択肢）、Html→順序付きリスト（<ol>）、その他→純粋なテキストリスト
# テキスト系の方法（Markdown/Html など）はデフォルトで選択肢を末尾に結合
# merge_prompt=True で任意の method に強制的に結合；placeholder で占位符をカスタマイズ
choice = await event.choose(
    "## 選択してください\n{options}", ["A", "B"],
    method="Markdown", merge_prompt=True,
)

# collect — フォーム収集（{key: value} 辞書または None を返す）
data = await event.collect([
    {"key": "name", "prompt": "名前を入力してください："},
    {"key": "age", "prompt": "年齢を入力してください：",
     "validator": lambda e: e.get_text().isdigit()},
    {"key": "avatar", "prompt": "プロフィール画像を送信してください：", "method": "Image"},
])

# wait_for — 条件を満たす任意のイベントを待つ
evt = await event.wait_for(event_type="notice", condition=lambda e: ..., timeout=120)

# conversation — 複数ラウンド対話コンテキスト
conv = event.conversation(timeout=60)
await conv.say("ようこそ！")
```

> 完全な交互メソッドのパラメータ説明とより多くの例は [Event ラッパークラスの詳細](../developer-guide/modules/event-wrapper.md) と [Conversation 複数ラウンド対話](../advanced/conversation.md) を参照してください。

### ユーティリティメソッド

```python
# _ で始まる内部キーをフィルタリングして辞書に変換
event_dict = event.to_dict()

# 元のデータを取得
raw = event.get_raw()
raw_type = event.get_raw_type()
```

### リンク制御

`event.done(claim=, stop=)` は「認領」および「ブロック」の2つの正交的な意味を統一的に制御します：

- **認領（claim）**：イベントが処理されたことをマーク（`_processed`）、コマンドディスパッチャーはこれに基づいて重複処理をスキップ
- **ブロック（stop）**：低優先度のハンドラへのイベント伝播を阻止（`_propagation_stopped`）

```python
# 認領 + ブロック（デフォルト）
event.done()

# 認領のみ、ブロックしない（低優先度の観測者はまだイベントを見ることができます）
event.done(stop=False)

# ブロックのみ、認領しない（例：ファイアウォール / 限流）
event.done(claim=False)

# mark_processed が主メソッドで、done はその別名
event.mark_processed()             # 等価 event.done()
event.mark_processed(stop=False)   # 等価 event.done(stop=False)

# 状態を照会
event.is_processed()  # 既に認領されているか
event.is_stopped()    # 伝播がブロックされているか
```

### プラットフォーム拡張メソッド

アダプタは Event にプラットフォーム固有のメソッドを登録でき、対応するプラットフォームのインスタンスでのみ利用可能です。

#### ユーザー：プラットフォーム拡張メソッドの使用

アダプタがプラットフォーム固有のメソッドを登録した後、イベントハンドラ内で直接呼び出すことができます。各プラットフォームのメソッドは異なりますので、対応する [プラットフォームドキュメント](../platform-guide/) を参照してください。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # プラットフォームに応じて固有メソッドを呼び出す
    if platform == "email":
        subject = event.get_subject()           # メール固有
        attachments = event.get_attachments()   # メール固有
```

#### プラットフォーム登録メソッドの照会

```python
from ErisPulse.Core.Event import get_platform_event_methods

# 特定のプラットフォームで登録されたメソッドを照会
methods = get_platform_event_methods("email")
# ["get_subject", "get_from", "get_attachments", ...]

# 動的に判定して呼び出す
for method_name in get_platform_event_methods(event.get_platform()):
    method = getattr(event, method_name)
    print(f"{method_name}: {method()}")
```

#### プラットフォームメソッドの隔離

異なるプラットフォームで登録されたメソッドは互いに干渉しません：

```python
# メールイベント - メール固有のメソッドのみ
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram イベント - Telegram 固有のメソッドのみ
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ "private"
event.get_subject()      # ❌ AttributeError
```

#### `hasattr` / `dir` のサポート

```python
hasattr(event, "get_subject")   # platform="email" のみで True を返す
"get_subject" in dir(event)     # 同上
```

#### アダプタ：プラットフォーム拡張メソッドの登録

アダプタはデコレータを使って Event にプラットフォーム固有のメソッドを登録でき、メソッドの最初の引数は `self`（Event インスタンス）で、イベントデータに自由にアクセスできます。

#### 単一メソッドの登録

```python
from ErisPulse.Core.Event import register_event_method

@register_event_method("email")
def get_subject(self):
    """メールの件名を取得"""
    return self.get("email_raw", {}).get("subject", "")

@register_event_method("email")
def get_from(self):
    """送信元を取得"""
    return self.get("email_raw", {}).get("from", {})
```

#### バッチ登録（Mixin クラス）

メソッドが多い場合は、Mixin クラスを使ってバッチ登録することを推奨します：

```python
from ErisPulse.Core.Event import register_event_mixin

class EmailEventMixin:
    def get_subject(self):
        return self.get("email_raw", {}).get("subject", "")

    def get_from(self):
        return self.get("email_raw", {}).get("from", {})

    def get_attachments(self):
        return self.get("email_raw", {}).get("attachments", [])

# 一度にすべてのメソッドを登録
register_event_mixin("email", EmailEventMixin)
```

#### 戻り値の規則

| 情景 | 戻り値 | ユーザーの使用方法 |
|------|--------|------------|
| データを返す（テキスト、辞書など） | 直接戻り値を返す | `subject = event.get_subject()` |
| 操作を実行する（メッセージ送信など） | `asyncio.Task` を返す | `task = event.do_something()` は `await` が選択可能 |

> **推奨**：データを返さないメソッドは `asyncio.Task` を返すようにし、ユーザーが `await` を選択できるようにします。`await` しなくても操作は完了します。

```python
@register_event_method("email")
def forward_email(self, to_address: str):
    """メール転送 — Task を返す、ユーザーは `await` を選択可能"""
    import asyncio
    return asyncio.create_task(
        self._do_forward(to_address)
    )

# ユーザーは `await` して結果を待つこともできます
await event.forward_email("user@example.com")

# または `await` しないで、バックグラウンドで実行することもできます
event.forward_email("user@example.com")
```

#### メソッドの解除登録

```python
from ErisPulse.Core.Event import unregister_event_method, unregister_platform_event_methods

# 単一メソッドの解除登録
unregister_event_method("email", "get_subject")

# 特定のプラットフォームのすべてのメソッドを解除登録（アダプタのシャットダウン時に呼び出す）
unregister_platform_event_methods("email")
```

#### 内部メソッドの上書き

`register_event_mixin` / `register_event_method` は Event 内部メソッド（`confirm`、`choose`、`collect`、`wait_reply`、`reply` など）を上書きすることをサポートします。登録されたプラットフォームメソッドは `Event.__getattribute__` によって内部メソッドよりも優先して有効になるため、アダプタはプラットフォーム特有のインタラクティブ実装を提供できます。

内部実装は `_builtin_*` 関数としてエクスポートされ、上書きする側はそれらをバックアップとして呼び出すことができます。

```python
from ErisPulse.Core.Event import register_event_mixin, _builtin_choose

class YunhuEventMixin:
    async def choose(self, prompt, options, timeout=60, method="Text"):
        # 雲湖プラットフォームはボタンコンポーネントを使用
        buttons = [[{"text": opt} for opt in options]]
        await self.reply(prompt)
        # ...ボタンのコールバックまたはテキストの返信を待つ...
        # 内部ロジックに回帰
        return await _builtin_choose(self, None, options, timeout, "Text")

register_event_mixin("yunhu", YunhuEventMixin)
```

## 跨プラットフォーム拡張（ワイルドカード）

`register_event_method` と `register_event_mixin` は `"*"` をプラットフォーム名として渡すことができ、登録されたメソッドは**すべてのプラットフォーム**の Event インスタンスで利用可能です。AI チャット、コンテキスト管理など、プラットフォーム間で再利用可能な機能モジュールに適しています。

### 跨プラットフォームメソッドの登録

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    """self は Event インスタンスで、イベントデータと内部メソッドに自由にアクセス可能"""
    await self.reply(f"AI: {prompt}")
```

登録後、すべてのプラットフォームのイベントハンドラで呼び出すことができます：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handler(event):
    await event.ai_chat(event.get_text())
```

### メソッドの優先順位

Event メソッドを属性アクセスで取得する際の優先順位は以下の通りです：

1. **プラットフォーム固有のメソッド**（現在のプラットフォームの上書き）
2. **ワイルドカードメソッド**（`"*"` で登録された跨プラットフォームメソッド）
3. **内部メソッド**（`reply`、`confirm` など）
4. **辞書キーのアクセス**

> したがって、ワイルドカードメソッドは内部メソッド（`reply` など）を上書きできますが、同名のプラットフォーム固有のメソッドによってさらに上書きされます。

## 優先度システム

イベントハンドラは優先度をサポートし、数値が大きいほど優先度が高くなります：

```python
# 高優先度のハンドラが先に実行されます
@message.on_message(priority=10)
async def high_priority_handler(event):
    pass

# 低優先度のハンドラが後に実行されます
@message.on_message(priority=0)
async def low_priority_handler(event):
    pass
```

## 関連ドキュメント

- [コアモジュール API](core-modules.md) - コアモジュール API
- [アダプタシステム API](adapter-system.md) - Adapter 管理 API
- [モジュール開発ガイド](../developer-guide/modules/) - 自作モジュールの開発ガイド