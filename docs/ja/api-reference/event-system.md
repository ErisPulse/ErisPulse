# イベントシステム API

このドキュメントでは、ErisPulse イベントシステムの API を詳しく紹介します。

## Command コマンドモジュール

### コマンドの登録

```python
from ErisPulse.Core.Event import command

# 基本的なコマンド
@command("hello", help="挨拶を送信")
async def hello_handler(event):
    await event.reply("こんにちは！")

# エイリアス付きのコマンド
@command(["help", "h"], aliases=["ヘルプ"], help="ヘルプを表示")
async def help_handler(event):
    pass

# 権限付きのコマンド
def is_admin(event):
    return event.get("user_id") in admin_ids

@command("admin", permission=is_admin, help="管理者用コマンド")
async def admin_handler(event):
    pass

# 非表示コマンド
@command("secret", hidden=True, help="秘密のコマンド")
async def secret_handler(event):
    pass

# コマンドグループ
@command("admin.reload", group="admin", help="モジュールを再読み込み")
async def reload_handler(event):
    pass
```

### コマンド情報

```python
# コマンドのヘルプを取得
help_text = command.help()

# 特定のコマンドを取得
cmd_info = command.get_command("admin")

# コマンドグループ内のコマンドをすべて取得
admin_commands = command.get_group_commands("admin")

# すべての可視コマンドを取得
visible_commands = command.get_visible_commands()
```

### 返信の待機

```python
# ユーザーからの返信を待機
@command("ask", help="ユーザー情報を尋ねる")
async def ask_command(event):
    reply = await command.wait_reply(
        event,
        prompt="名前を入力してください:",  # 上記で送信済み
        timeout=30.0
    )
    
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}！")

# バリデーション付きの返信待機
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
        await event.reply(f"あなたの年齢は {age} 歳です")

# コールバック付きの返信待機
async def handle_confirmation(reply_event):
    text = reply_event.get_text().lower()
    if text in ["はい", "yes", "y"]:
        await event.reply("操作が確認されました！")
    else:
        await event.reply("操作がキャンセルされました。")

@command("confirm", help="操作を確認する")
async def confirm_command(event):
    await command.wait_reply(
        event,
        prompt="'はい'または'いいえ'を入力してください:",
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

# プライベートチャットメッセージを監視
@message.on_private_message()
async def private_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"プライベートチャットの送信元: {user_id}")

# グループメッセージを監視
@message.on_group_message()
async def group_handler(event):
    group_id = event.get_group_id()
    sdk.logger.info(f"グループメッセージの送信元: {group_id}")

# メンションメッセージを監視
@message.on_at_message()
async def at_handler(event):
    mentions = event.get_mentions()
    sdk.logger.info(f"メンションされたユーザー: {mentions}")
```

### 条件付き監視

```python
# 優先度を使用して実行順序を制御
@message.on_message(priority=10)  # 数値が大きいほど優先度が高い
async def high_priority_handler(event):
    pass

# ハンドラー内で条件フィルタを実装
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

# フレンドの追加
@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    await event.reply("フレンド追加への歓迎！")

# フレンドの削除
@notice.on_friend_remove()
async def friend_remove_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"フレンド削除: {user_id}")

# グループメンバーの増加
@notice.on_group_increase()
async def member_increase_handler(event):
    user_id = event.get_user_id()
    await event.reply(f"新しいメンバーへようこそ！")

# グループメンバーの減少
@notice.on_group_decrease()
async def member_decrease_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"グループメンバーの退出: {user_id}")
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

# 切断イベント
@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"プラットフォーム {platform} から切断")

# ハートビートイベント
@meta.on_heartbeat()
async def heartbeat_handler(event):
    sdk.logger.debug("ハートビートを受信")
```

### Bot ステータスの確認

アダプタがメタイベントを送信すると、フレームワークは自動的に Bot のステータスを追跡します。クエリ API とライフサイクルイベントのリスニングについては、[アダプタシステム API - Bot ステータス管理](adapter-system.md#bot-状態管理) を参照してください。

## Event ラップクラス

Event モジュールのイベントハンドラーは、`dict` を継承し便利なメソッドを提供する Event ラップクラスのインスタンスを受け取ります。

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
# 統一されたターゲットID：グループチャットの場合は group_id、プライベートチャットの場合は user_id、など
target_id = event.get_target_id()

# セッションの唯一識別子、形式: {platform}:{detail_type}:{target_id}
session_id = event.get_session_id()
# 例: "telegram:private:12345"、"qq:group:67890"
```

`get_target_id()` は、`group_id` → `channel_id` → `guild_id` → `thread_id` → `user_id` の順で、最初に取得できる非空の値を返します。コンテキスト管理、ステータス保存など、統一されたセッション識別子が必要なシナリオに適しています。

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

# メッセージタイプを判定
is_msg = event.is_message()
is_private = event.is_private_message()
is_group = event.is_group_message()

# メンション関連
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

# コマンドかどうかを判定
is_cmd = event.is_command()
```

### 返信機能

```python
# 基本的な返信
await event.reply("これはメッセージです")

# 送信方法を指定
await event.reply("http://example.com/image.jpg", method="Image")

# ユーザーへのメンションと返信メッセージを含む
await event.reply("こんにちは", at_users=["user1"], reply_to="msg_id")

# 全体メンション
await event.reply("お知らせ", at_all=True)

# プラットフォーム固有の修飾メソッドを使用（via パラメータ）
await event.reply("看板の内容", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])

# 送信チェーンを取得し、自由に修飾メソッドと送信方法を追加（複数の修飾/アクションメソッドを連続で使用する場合に適しています）
await event.send_chain().Expire(3600).Board("看板の内容")
await event.send_chain().DismissBoard()

# OneBot12 メッセージセグメントを使用して返信
from ErisPulse.Core.Event import MessageBuilder
msg = MessageBuilder().text("Hello").image("url").build()
await event.reply_ob12(msg)

# 返信を待機
reply = await event.wait_reply(timeout=30)
```

### プラットフォーム機能の照会

```python
# 現在のプラットフォームが特定の送信方法をサポートしているか確認
if event.supports("Image"):
    await event.reply(url, method="Image")

# 現在のプラットフォームで使用可能なすべての送信方法を一覧表示
methods = event.available_methods()
# ["Text", "Image", "Voice", ...]
```

### 返信メソッド

`reply()` メソッドは、`method` パラメータを使用して送信タイプを指定し、2つの便利なブール引数をサポートします：

```python
# シンプルなテキスト返信
await event.reply("こんにちは")

# 送信者へのメンション付きで返信
await event.reply("こんにちは", at_sender=True)

# 現在のメッセージを引用して返信
await event.reply("受信しました", reply_to_message=True)

# 組み合わせて使用
await event.reply("受信しました", at_sender=True, reply_to_message=True)

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
| `method` | str | 送信方法、デフォルトは "Text"、選択肢: "Image"/"Voice"/"Video"/"File" など |
| `at_sender` | bool | 送信者にメンションするか（自動的に user_id を抽出） |
| `quote` | bool | 現在のメッセージを引用して返信するか（自動的に message_id を抽出） |
| `at_users` | list[str] | 指定されたユーザーへのメンションリスト |
| `reply_to` | str | 手動で返信メッセージの ID を指定 |
| `at_all` | bool | 全体メンションするか |

### インタラクションメソッド

```python
# confirm — 会話の確認（True/False/None を返す）
if await event.confirm("この操作を実行してもよろしいですか？"):
    await event.reply("確認済み")

# テキスト以外の方法で確認プロンプトを送信
if await event.confirm("http://example.com/image.jpg", method="Image"):
    await event.reply("画像プロンプトが確認されました")

# choose — 選択メニュー（オプションのインデックスまたは None を返す）
choice = await event.choose("色を選択してください：", ["赤", "緑", "青"])

# options_format="auto"（デフォルト）は method に応じて自動的にスタイルを選択します：
# Markdown→箇条書きリスト（- 1.オプション）、Html→番号付きリスト（<ol>）、その他→プレーンテキストリスト
# テキスト系メソッド（Markdown/Html 等）はデフォルトでオプションを末尾にマージします
# merge_prompt=True を使用すると、任意の method でのマージを強制できます。プレースホルダーはカスタマイズ可能です。
choice = await event.choose(
    "## 選択してください\n{options}", ["A", "B"],
    method="Markdown", merge_prompt=True,
)

# collect — フォーム収集（{key: value} の辞書または None を返す）
data = await event.collect([
    {"key": "name", "prompt": "名前を入力してください："},
    {"key": "age", "prompt": "年齢を入力してください：",
     "validator": lambda e: e.get_text().isdigit()},
    {"key": "avatar", "prompt": "アバターを送信してください：", "method": "Image"},
])

# wait_for — 条件を満たす任意のイベントを待機
evt = await event.wait_for(event_type="notice", condition=lambda e: ..., timeout=120)

# conversation — マルチターン会話コンテキスト
conv = event.conversation(timeout=60)
await conv.say("歓迎！")
```

> 完全なインタラクションメソッドのパラメータ説明とさらに多くの例については、[Event ラップクラスの詳細](../developer-guide/modules/event-wrapper.md) と [Conversation マルチターン会話](../advanced/conversation.md) を参照してください。

### ユーティリティメソッド

```python
# ディクショナリに変換
event_dict = event.to_dict()

# 処理済みかを確認
if not event.is_processed():
    event.mark_processed()

# 生のデータを取得
raw = event.get_raw()
raw_type = event.get_raw_type()
```

### プラットフォーム拡張メソッド

アダプタは Event にプラットフォーム固有のメソッドを登録でき、対応するプラットフォームのインスタンスでのみ使用可能です。

#### ユーザー：プラットフォーム拡張メソッドの使用

アダプタがプラットフォーム固有のメソッドを登録すると、イベントハンドラーで直接呼び出すことができます。各プラットフォームのメソッドは異なりますが、対応する [プラットフォームガイド](../platform-guide/) を参照してください。

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

#### プラットフォームで登録されたメソッドの照会

```python
from ErisPulse.Core.Event import get_platform_event_methods

# 特定のプラットフォームに登録されているメソッドを表示
methods = get_platform_event_methods("email")
# ["get_subject", "get_from", "get_attachments", ...]

# 動的に判断して呼び出す
for method_name in get_platform_event_methods(event.get_platform()):
    method = getattr(event, method_name)
    print(f"{method_name}: {method()}")
```

#### プラットフォームメソッドの隔離

異なるプラットフォームで登録されたメソッドは干渉しません：

```python
# メールイベント - メール専用のメソッドのみ
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram イベント - Telegram 専用のメソッドのみ
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ "private"
event.get_subject()      # ❌ AttributeError
```

#### `hasattr` / `dir` のサポート

```python
hasattr(event, "get_subject")   # platform="email" の場合のみ True を返します
"get_subject" in dir(event)     # 同上
```

### アダプタ：プラットフォーム拡張メソッドの登録

アダプタはデコレータを使用して Event にプラットフォーム固有のメソッドを登録でき、メソッドの最初のパラメータは `self`（Event インスタンス）であり、イベントデータに自由にアクセスできます。

#### 単一メソッドの登録

```python
from ErisPulse.Core.Event import register_event_method

@register_event_method("email")
def get_subject(self):
    """メールの件名を取得"""
    return self.get("email_raw", {}).get("subject", "")

@register_event_method("email")
def get_from(self):
    """送信者を取得"""
    return self.get("email_raw", {}).get("from", {})
```

#### バッチ登録（Mixin クラス）

メソッドが多い場合は、Mixin クラスを使用して一括登録することを推奨します：

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

#### 返り値の仕様

| シナリオ | 返り値 | ユーザーが使用する方法 |
|------|--------|------------|
| データを返す（テキスト、辞書など） | 直接返り値 | `subject = event.get_subject()` |
| 操作を実行する（メッセージの送信など） | `asyncio.Task` を返す | `task = event.do_something()`（オプションで await） |

> **推奨**：データ以外を返すメソッドは `asyncio.Task` を返します。これにより、ユーザーは `await` するかどうかを自分で決定でき、`await` しなくても操作は完了します。

```python
@register_event_method("email")
def forward_email(self, to_address: str):
    """メールを転送 — Task を返すため、ユーザーが await するかどうかを決定できます"""
    import asyncio
    return asyncio.create_task(
        self._do_forward(to_address)
    )

# ユーザーは結果を待機するために await できます
await event.forward_email("user@example.com")

# あるいは await せず、バックグラウンドで操作を実行することもできます
event.forward_email("user@example.com")
```

#### メソッドの登録解除

```python
from ErisPulse.Core.Event import unregister_event_method, unregister_platform_event_methods

# 単一メソッドの登録解除
unregister_event_method("email", "get_subject")

# 特定のプラットフォームのすべてのメソッドの登録解除（アダプタのシャットダウン時に呼び出す）
unregister_platform_event_methods("email")
```

#### 組み込みメソッドの上書き

`register_event_mixin` / `register_event_method` は、`confirm`、`choose`、`collect`、`wait_reply`、`reply` などの Event 組み込みメソッドを上書きできます。登録されたプラットフォームメソッドは、Event 内部の `_builtin_*` 関数を介して優先的に組み込みメソッドに作用するため、アダプタはプラットフォーム固有のインタラクション実装を提供できます。

組み込み実装は `_builtin_*` 関数としてエクスポートされており、上書きする側はそれらをフォールバックとして呼び出すことができます：

```python
from ErisPulse.Core.Event import register_event_mixin, _builtin_choose

class YunhuEventMixin:
    async def choose(self, prompt, options, timeout=60, method="Text"):
        # 雲湖プラットフォームはボタンコンポーネントを使用します
        buttons = [[{"text": opt} for opt in options]]
        await self.reply(prompt)
        # ...ボタンのコールバックかテキストの返信を待機...
        # 組み込みロジックにフォールバック
        return await _builtin_choose(self, None, options, timeout, "Text")

register_event_mixin("yunhu", YunhuEventMixin)
```

## クロスプラットフォーム拡張（ワイルドカード）

`register_event_method` と `register_event_mixin` は、プラットフォーム名として `"*"` を受け入れ、登録されたメソッドは**すべてのプラットフォーム**の Event インスタンスで使用可能になります。AI 会話、コンテキスト管理など、複数のプラットフォームで再利用される必要がある機能モジュールに適しています。

### クロスプラットフォームメソッドの登録

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    """self は Event インスタンスであり、イベントデータと組み込みメソッドに自由にアクセスできます"""
    await self.reply(f"AI: {prompt}")
```

登録後、すべてのプラットフォームのイベントハンドラーが呼び出すことができます：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handler(event):
    await event.ai_chat(event.get_text())
```

### メソッドの解決優先度

Event メソッドに属性アクセスした場合、解決の順序は以下の通りです：

1. **プラットフォーム固有メソッド**（現在のプラットフォームによる上書き）
2. **ワイルドカードメソッド**（`"*"` によって登録されたクロスプラットフォームメソッド）
3. **組み込みメソッド**（`reply`、`confirm` など）
4. **辞書キーアクセス**

> したがって、ワイルドカードメソッドは組み込みメソッド（`reply` など）を上書きできますが、同名のプラットフォーム固有メソッドによってさらに上書きされる可能性があります。

## 優先度システム

イベントハンドラーは優先度をサポートしており、数値が大きいほど優先度が高くなります：

```python
# 高優先度のハンドラーが先に実行
@message.on_message(priority=10)
async def high_priority_handler(event):
    pass

# 低優先度のハンドラーが後で実行
@message.on_message(priority=0)
async def low_priority_handler(event):
    pass
```

## 関連ドキュメント

- [コアモジュール API](core-modules.md) - コアモジュール API
- [アダプタシステム API](adapter-system.md) - Adapter 管理 API
- [モジュール開発ガイド](../developer-guide/modules/) - カスタムモジュールの開発