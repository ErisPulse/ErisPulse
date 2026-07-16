# イベントシステム API

このドキュメントでは、ErisPulse イベントシステムの API を詳しく説明します。

## Command コマンドモジュール

### コマンドの登録

```python
from ErisPulse.Core.Event import command

# 基本的なコマンド
@command("hello", help="挨拶を送信します")
async def hello_handler(event):
    await event.reply("こんにちは！")

# エイリアス付きのコマンド
@command(["help", "h"], aliases=["ヘルプ"], help="ヘルプを表示します")
async def help_handler(event):
    pass

# 権限付きのコマンド
def is_admin(event):
    return event.get("user_id") in admin_ids

@command("admin", permission=is_admin, help="管理者コマンド")
async def admin_handler(event):
    pass

# 隠しコマンド
@command("secret", hidden=True, help="秘密のコマンド")
async def secret_handler(event):
    pass

# コマンドグループ
@command("admin.reload", group="admin", help="モジュールを再読み込みします")
async def reload_handler(event):
    pass
```

### コマンド情報

```python
# コマンドヘルプを取得
help_text = command.help()

# 特定のコマンドを取得
cmd_info = command.get_command("admin")

# コマンドグループ内のすべてのコマンドを取得
admin_commands = command.get_group_commands("admin")

# すべての表示コマンドを取得
visible_commands = command.get_visible_commands()
```

### 返信待機

```python
# ユーザーの返信を待機
@command("ask", help="ユーザー情報を尋ねます")
async def ask_command(event):
    reply = await command.wait_reply(
        event,
        prompt="あなたの名前を入力してください:",  # 上記で送信済み
        timeout=30.0
    )
    
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}！")

# 検証付きの返信待機
def validate_age(event_data):
    try:
        age = int(event_data.get_text())
        return 0 <= age <= 150
    except ValueError:
        return False

@command("age", help="ユーザーの年齢を尋ねます")
async def age_command(event):
    await event.reply("あなたの年齢を入力してください:")
    
    reply = await command.wait_reply(
        event,
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"あなたの年齢は {age} 歳です")

# コールバック付きの返信待機
async def handle_confirmation(reply_event):
    text = reply_event.get_text().lower()
    if text in ["はい", "yes", "y"]:
        await event.reply("操作が確認されました！")
    else:
        await event.reply("操作がキャンセルされました。")

@command("confirm", help="操作を確認します")
async def confirm_command(event):
    await command.wait_reply(
        event,
        prompt="'はい'か'いいえ'を入力してください:",
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
    sdk.logger.info(f"メッセージを受信: {event.get_text()}")

# プライベートメッセージを監視
@message.on_private_message()
async def private_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"プライベートチャットからの: {user_id}")

# グループメッセージを監視
@message.on_group_message()
async def group_handler(event):
    group_id = event.get_group_id()
    sdk.logger.info(f"グループチャットからの: {group_id}")

# メンション（@）メッセージを監視
@message.on_at_message()
async def at_handler(event):
    mentions = event.get_mentions()
    sdk.logger.info(f"メンションされたユーザー: {mentions}")
```

### 条件付き監視

```python
# 優先順位で実行順序を制御
@message.on_message(priority=10)  # 数値が大きいほど優先度が高い
async def high_priority_handler(event):
    pass

# ハンドラ内で条件フィルタを実装
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

# 友達追加
@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    await event.reply("友達追加ありがとうございます！")

# 友達削除
@notice.on_friend_remove()
async def friend_remove_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"友達削除: {user_id}")

# グループ参加
@notice.on_group_increase()
async def member_increase_handler(event):
    user_id = event.get_user_id()
    await event.reply(f"新メンバーようこそ！")

# グループ退出
@notice.on_group_decrease()
async def member_decrease_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"グループメンバーが退出しました: {user_id}")
```

## Request リクエストモジュール

### リクエストイベント

```python
from ErisPulse.Core.Event import request

# 友達リクエスト
@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    sdk.logger.info(f"友達リクエスト: {user_id}, メモ: {comment}")

# グループ招待リクエスト
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"グループ招待: {group_id}, 来自: {user_id}")
```

## Meta メタイベントモジュール

### メタイベント

```python
from ErisPulse.Core.Event import meta

# 接続イベント
@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"プラットフォーム {platform} に接続成功しました")

# 切断イベント
@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"プラットフォーム {platform} から切断されました")

# ハートビートイベント
@meta.on_heartbeat()
async def heartbeat_handler(event):
    sdk.logger.debug("ハートビートを受信")
```

### Botステータス照会

アダプターがメタイベントを送信した後、フレームワークは自動的にBotのステータスを追跡します。照会APIとライフサイクルイベント監視については、[アダプターシステム API - Botステータス管理](adapter-system.md#bot-状态管理) を参照してください。

## Event ラッパークラス

Eventモジュールのイベントハンドラーは、dictを継承し、便利なメソッドを提供するEventラッパークラスのインスタンスを受け取ります。

### コアメソッド

```python
# イベント情報を取得
event_id = event.get_id()
event_time = event.get_time()
event_type = event.get_type()
detail_type = event.get_detail_type()
platform = event.get_platform()

# ボット情報を取得
self_platform = event.get_self_platform()
self_user_id = event.get_self_user_id()
self_info = event.get_self_info()
```

### セッション識別子

```python
# 統一されたターゲットID：グループチャットはgroup_id、プライベートチャットはuser_idなど
target_id = event.get_target_id()

# セッション固有の識別子、形式: {platform}:{detail_type}:{target_id}
session_id = event.get_session_id()
# 例: "telegram:private:12345"、"qq:group:67890"
```

`get_target_id()` は、以下の順序で最初の空ではない値を返します：`group_id` → `channel_id` → `guild_id` → `thread_id` → `user_id`。コンテキスト管理、状態保存など、セッションを一意に識別する必要があるシーンに適しています。

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

# コマンドかどうかを判断
is_cmd = event.is_command()
```

### 返信機能

```python
# 基本的な返信
await event.reply("これはメッセージです")

# 送信方法を指定
await event.reply("http://example.com/image.jpg", method="Image")

# @ユーザーと返信メッセージ付き
await event.reply("こんにちは", at_users=["user1"], reply_to="msg_id")

# @全体
await event.reply("お知らせ", at_all=True)

# OneBot12メッセージセグメントを使用した返信
from ErisPulse.Core.Event import MessageBuilder
msg = MessageBuilder().text("Hello").image("url").build()
await event.reply_ob12(msg)

# 返信待機
reply = await event.wait_reply(timeout=30)
```

### プラットフォーム能力照会

```python
# 現在のプラットフォームが特定の送信方法をサポートしているかチェック
if event.supports("Image"):
    await event.reply(url, method="Image")

# 現在のプラットフォームで利用可能なすべての送信方法をリスト
methods = event.available_methods()
# ["Text", "Image", "Voice", ...]
```

### 返信メソッド

`reply()` メソッドは、`method`パラメータを使用して送信タイプを指定し、2つの便利なブールパラメータをサポートしています：

```python
# シンプルなテキスト返信
await event.reply("こんにちは")

# 送信者に@付きで返信
await event.reply("こんにちは", at_sender=True)

# 現在のメッセージを引用して返信
await event.reply("受信しました", reply_to_message=True)

# 組み合わせ使用
await event.reply("受信しました", at_sender=True, reply_to_message=True)

# 画像を送信（methodパラメータを使用）
if event.supports("Image"):
    await event.reply("http://example.com/img.jpg", method="Image")
else:
    await event.reply("[画像] http://example.com/img.jpg")
```

**パラメータ説明**：

| パラメータ | 型 | 説明 |
|------|------|------|
| `content` | str | 送信内容 |
| `method` | str | 送信方法、デフォルト "Text"、選択肢 "Image"/"Voice"/"Video"/"File" など |
| `at_sender` | bool | 送信者に@するか（user_idを自動的に抽出） |
| `quote` | bool | 現在のメッセージを引用して返信するか（message_idを自動的に抽出） |
| `at_users` | list[str] | 指定されたユーザーリストに@ |
| `reply_to` | str | 手動で指定された返信メッセージID |
| `at_all` | bool | 全体に@するか |

### インタラクションメソッド

```python
# confirm — 対話の確認（True/False/Noneを返す）
if await event.confirm("この操作を実行してもよろしいですか？"):
    await event.reply("確認済み")

# Text以外の方法で確認プロンプトを送信
if await event.confirm("http://example.com/image.jpg", method="Image"):
    await event.reply("画像プロンプトを確認しました")

# choose — 選択メニュー（選択肢インデックスまたはNoneを返す）
choice = await event.choose("色を選択してください：", ["赤", "緑", "青"])

# options_format="auto"（デフォルト）methodに基づいてスタイルを自動選択：
# Markdown→順不同リスト（- 1.オプション）、Html→順序付きリスト（<ol>）、その他→プレーンテキストリスト
# テキスト系メソッド（Markdown/Htmlなど）はデフォルトでオプションを末尾に結合
# merge_prompt=True は任意のmethodで強制的に結合を可能にする；placeholderはカスタムプレースホルダーを可能にする
choice = await event.choose(
    "## 選択してください\n{options}", ["A", "B"],
    method="Markdown", merge_prompt=True,
)

# collect — フォーム収集（{key: value}辞書またはNoneを返す）
data = await event.collect([
    {"key": "name", "prompt": "名前を入力してください："},
    {"key": "age", "prompt": "年齢を入力してください：",
     "validator": lambda e: e.get_text().isdigit()},
    {"key": "avatar", "prompt": "アバターを送信してください：", "method": "Image"},
])

# wait_for — 条件を満たす任意のイベントを待機
evt = await event.wait_for(event_type="notice", condition=lambda e: ..., timeout=120)

# conversation — マルチラウンド会話コンテキスト
conv = event.conversation(timeout=60)
await conv.say("ようこそ！")
```

> 完全なインタラクションメソッドのパラメータ説明やさらなる例については、[Event ラッパークラス詳細](../developer-guide/modules/event-wrapper.md) および [Conversation マルチラウンド会話](../advanced/conversation.md) を参照してください。

### ユーティリティメソッド

```python
# 辞書に変換
event_dict = event.to_dict()

# 処理済みかチェック
if not event.is_processed():
    event.mark_processed()

# 原始データを取得
raw = event.get_raw()
raw_type = event.get_raw_type()
```

### プラットフォーム拡張メソッド

アダプターはEventにプラットフォーム固有のメソッドを登録できます。これは、対応するプラットフォームのインスタンスでのみ利用可能です。

#### ユーザー：プラットフォーム拡張メソッドの使用

アダプターがプラットフォーム固有のメソッドを登録した後、イベントハンドラーで直接呼び出すことができます。各プラットフォームのメソッドは異なりますので、対応する[プラットフォームドキュメント](../platform-guide/)を参照してください。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # プラットフォームに応じて固有のメソッドを呼び出し
    if platform == "email":
        subject = event.get_subject()           # メール固有
        attachments = event.get_attachments()   # メール固有
```

#### プラットフォームで登録されたメソッドを照会

```python
from ErisPulse.Core.Event import get_platform_event_methods

# 特定のプラットフォームにどのメソッドが登録されているかを確認
methods = get_platform_event_methods("email")
# ["get_subject", "get_from", "get_attachments", ...]

# 動的に判断して呼び出し
for method_name in get_platform_event_methods(event.get_platform()):
    method = getattr(event, method_name)
    print(f"{method_name}: {method()}")
```

#### プラットフォームメソッドの分離

異なるプラットフォームに登録されたメソッドは干渉しません：

```python
# メールイベント - メール固有のメソッドのみ
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram イベント - Telegram固有のメソッドのみ
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ "private"
event.get_subject()      # ❌ AttributeError
```

#### `hasattr` / `dir` サポート

```python
hasattr(event, "get_subject")   # platform="email"の場合のみTrueを返す
"get_subject" in dir(event)     # 同上
```

### アダプター：プラットフォーム拡張メソッドの登録

アダプターはデコレーターを使用してEventにプラットフォーム固有のメソッドを登録できます。メソッドの最初のパラメータは`self`（Eventインスタンス）で、イベントデータに自由にアクセスできます。

#### 個別のメソッド登録

```python
from ErisPulse.Core.Event import register_event_method

@register_event_method("email")
def get_subject(self):
    """メール件名を取得"""
    return self.get("email_raw", {}).get("subject", "")

@register_event_method("email")
def get_from(self):
    """送信者を取得"""
    return self.get("email_raw", {}).get("from", {})
```

#### 一括登録（Mixinクラス）

メソッドが多い場合は、Mixinクラスを使用して一括登録することをお勧めします：

```python
from ErisPulse.Core.Event import register_event_mixin

class EmailEventMixin:
    def get_subject(self):
        return self.get("email_raw", {}).get("subject", "")

    def get_from(self):
        return self.get("email_raw", {}).get("from", {})

    def get_attachments(self):
        return self.get("email_raw", {}).get("attachments", [])

# すべてのメソッドを一度に登録
register_event_mixin("email", EmailEventMixin)
```

#### 返り値規範

| シーン | 返り値 | ユーザーの使用方法 |
|------|--------|------------|
| データ（テキスト、辞書など）を返す | 直接返り値 | `subject = event.get_subject()` |
| 操作（メッセージ送信など）を実行 | `asyncio.Task`を返す | `task = event.do_something()` 可選 `await` |

> **推奨**：データを返さないメソッドは`asyncio.Task`を返し、ユーザーが`await`するかどうかを自分で決められるようにします。`await`しなくても操作は完了します。

```python
@register_event_method("email")
def forward_email(self, to_address: str):
    """メールを転送 — Taskを返し、ユーザーはawaitするかどうかを自分で決められる"""
    import asyncio
    return asyncio.create_task(
        self._do_forward(to_address)
    )

# ユーザーはawaitして結果を待つことができます
await event.forward_email("user@example.com")

# また、awaitせず、操作はバックグラウンドで実行されます
event.forward_email("user@example.com")
```

#### メソッドの登録解除

```python
from ErisPulse.Core.Event import unregister_event_method, unregister_platform_event_methods

# 個別のメソッドを登録解除
unregister_event_method("email", "get_subject")

# 特定のプラットフォームのすべてのメソッドを登録解除（アダプターシャットダウン時に呼び出される）
unregister_platform_event_methods("email")
```

#### 組み込みメソッドの上書き

`register_event_mixin` / `register_event_method` は、組み込みEventメソッド（`confirm`、`choose`、`collect`、`wait_reply`、`reply`など）の上書きをサポートします。登録されたプラットフォームメソッドは、`Event.__getattribute__`を通じて組み込みメソッドよりも優先して有効になります。そのため、アダプターはプラットフォーム固有のインタラクション実装を提供できます。

組み込み実装は`_builtin_*`関数としてエクスポートされ、上書きする側はそれらをフォールバックとして呼び出すことができます：

```python
from ErisPulse.Core.Event import register_event_mixin, _builtin_choose

class YunhuEventMixin:
    async def choose(self, prompt, options, timeout=60, method="Text"):
        # 雲湖プラットフォームはボタンコンポーネントを使用
        buttons = [[{"text": opt} for opt in options]]
        await self.reply(prompt)
        # ...ボタンコールバックまたはテキスト返信を待機...
        # 組み込みロジックにフォールバック
        return await _builtin_choose(self, None, options, timeout, "Text")

register_event_mixin("yunhu", YunhuEventMixin)
```

## クロスプラットフォーム拡張（ワイルドカード）

`register_event_method`と`register_event_mixin`は、プラットフォーム名として`"*"`を渡すのをサポートします。登録されたメソッドは**すべてのプラットフォーム**のEventインスタンスで利用可能です。AI対話、コンテキスト管理など、クロスプラットフォームで再利用される必要がある機能モジュールに適しています。

### クロスプラットフォームメソッドの登録

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    """selfはEventインスタンスであり、イベントデータと組み込みメソッドに自由にアクセスできます"""
    await self.reply(f"AI: {prompt}")
```

登録後、すべてのプラットフォームのイベントハンドラーが呼び出すことができます：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handler(event):
    await event.ai_chat(event.get_text())
```

### メソッド解決の優先順位

Eventメソッドに属性アクセスする場合、解決順序は以下の通りです：

1. **プラットフォーム固有メソッド**（現在のプラットフォームによる上書き）
2. **ワイルドカードメソッド**（`"*"`で登録されたクロスプラットフォームメソッド）
3. **組み込みメソッド**（`reply`、`confirm`など）
4. **辞書キーアクセス**

> したがって、ワイルドカードメソッドは組み込みメソッド（`reply`など）を上書きできますが、同じ名前のプラットフォーム固有メソッドによってさらに上書きされます。

## 優先順位システム

イベントハンドラーは優先順位をサポートしており、数値が大きいほど優先度が高いです：

```python
# 高優先度ハンドラーが先に実行
@message.on_message(priority=10)
async def high_priority_handler(event):
    pass

# 低優先度ハンドラーが後に実行
@message.on_message(priority=0)
async def low_priority_handler(event):
    pass
```

## 関連ドキュメント

- [コアモジュール API](core-modules.md) - コアモジュールAPI
- [アダプターシステム API](adapter-system.md) - アダプター管理API
- [モジュール開発ガイド](../developer-guide/modules/) - カスタムモジュールの開発