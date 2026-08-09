# イベントシステム API

本ドキュメントでは、ErisPulse のイベントシステムの API について詳しく説明します。

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

@command("admin", permission=is_admin, help="管理者コマンド")
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

# コマンドグループ内のすべてのコマンドを取得
admin_commands = command.get_group_commands("admin")

# 可視化されたすべてのコマンドを取得
visible_commands = command.get_visible_commands()
```

### 返信の待機

```python
# ユーザーからの返信を待機
@command("ask", help="ユーザー情報を尋ねる")
async def ask_command(event):
    reply = await command.wait_reply(
        event,
        prompt="あなたの名前を入力してください:",  # すでに上記で送信済み
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

@command("age", help="ユーザーの年齢を尋ねる")
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
        await event.reply("操作が確定しました！")
    else:
        await event.reply("操作がキャンセルされました。")

@command("confirm", help="操作を確認する")
async def confirm_command(event):
    await command.wait_reply(
        event,
        prompt="'はい'または'いいえ'を入力してください:",
        callback=handle_confirmation
    )

## Message メッセージモジュール

### メッセージイベント

```python
from ErisPulse.Core.Event import message

# すべてのメッセージを監視
@message.on_message()
async def message_handler(event):
    sdk.logger.info(f"受信メッセージ: {event.get_text()}")

# プライベートチャットメッセージを監視
@message.on_private_message()
async def private_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"プライベートチャットから: {user_id}")

# グループチャットメッセージを監視
@message.on_group_message()
async def group_handler(event):
    group_id = event.get_group_id()
    sdk.logger.info(f"グループチャットから: {group_id}")

# @メッセージを監視
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

# ハンドラ内部で条件フィルタを実装
@message.on_message()
async def filtered_handler(event):
    if "キーワード" not in event.get_text():
        return
    # キーワードを含むメッセージを処理
    pass

## 通知モジュール

### 通知イベント

```python
from ErisPulse.Core.Event import notice

# フレンド追加
@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    await event.reply("友達として追加してくれてありがとう！")

# フレンド削除
@notice.on_friend_remove()
async def friend_remove_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"フレンド削除: {user_id}")

# グループメンバー増加
@notice.on_group_increase()
async def member_increase_handler(event):
    user_id = event.get_user_id()
    await event.reply(f"新メンバーようこそ！")

# グループメンバー減少
@notice.on_group_decrease()
async def member_decrease_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"メンバー退会: {user_id}")

## リクエスト モジュール (Request モジュール)

### リクエスト イベント

```python
from ErisPulse.Core.Event import request

# フレンドリクエスト
@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    sdk.logger.info(f"フレンドリクエスト: {user_id}, 注釈: {comment}")

# グループ招待リクエスト
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"グループ招待: {group_id}, から: {user_id}")

## メタ イベント モジュール

### メタ イベント

```python
from ErisPulse.Core.Event import meta

# 接続イベント
@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"プラットフォーム {platform} への接続に成功しました")

# 切断イベント
@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"プラットフォーム {platform} から切断されました")

# ハートビートイベント
@meta.on_heartbeat()
async def heartbeat_handler(event):
    sdk.logger.debug("ハートビートを受信しました")
```

### Bot 状態照会

アダプタがメタイベントを送信した後、フレームワークは自動的に Bot の状態を追跡します。照会 API およびライフサイクルイベントの監視については、[アダプタシステム API - Bot 状態管理](adapter-system.md#bot-状态管理) を参照してください。

## イベント クラス

Event モジュールのイベントハンドラーは、dict を継承したイベントラッパークラスのインスタンスを受け取ります。これには便利なメソッドが提供されています。

### 基本メソッド

```python
# イベント情報の取得
event_id = event.get_id()
event_time = event.get_time()
event_type = event.get_type()
detail_type = event.get_detail_type()
platform = event.get_platform()

# ボット情報の取得
self_platform = event.get_self_platform()
self_user_id = event.get_self_user_id()
self_info = event.get_self_info()
```

### セッション識別子

```python
# 統一されたターゲット ID：グループチャットは group_id、プライベートチャットは user_id など
target_id = event.get_target_id()

# セッション固有の識別子、形式: {platform}:{detail_type}:{target_id}
session_id = event.get_session_id()
# 例: "telegram:private:12345"、"qq:group:67890"
```

`get_target_id()` は以下の順序で最初の非空値を返します：`group_id` → `channel_id` → `guild_id` → `thread_id` → `user_id`。コンテキスト管理や状態保存など、統一された識別子でセッションを管理する必要があるシーンに適しています。

### メッセージ関連メソッド

```python
# メッセージ内容の取得
message_segments = event.get_message()
alt_message = event.get_alt_message()
text = event.get_text()

# 送信者情報の取得
user_id = event.get_user_id()
nickname = event.get_user_nickname()
sender = event.get_sender()

# グループ情報の取得
group_id = event.get_group_id()

# メッセージタイプの判定
is_msg = event.is_message()
is_private = event.is_private_message()
is_group = event.is_group_message()

# メッセージへの @ について
is_at = event.is_at_message()
has_mention = event.has_mention()
mentions = event.get_mentions()
```

### コマンド情報

```python
# コマンド情報の取得
cmd_name = event.get_command_name()
cmd_args = event.get_command_args()
cmd_raw = event.get_command_raw()

# コマンドかどうかの判定
is_cmd = event.is_command()
```

### 返信機能

```python
# 基本的な返信
await event.reply("これはメッセージです")

# 送信方法を指定する
await event.reply("http://example.com/image.jpg", method="Image")

# ユーザーへの @ と返信メッセージ
await event.reply("こんにちは", at_users=["user1"], reply_to="msg_id")

# 全体への @
await event.reply("お知らせ", at_all=True)

# プラットフォーム固有の修飾メソッドを使用（via パラメータ）
await event.reply("看板内容", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])

# 送信チェーンを取得し、自由に修飾メソッドと送信方法を追加（連続する複数の修飾/アクション型メソッドに適しています）
await event.send_chain().Expire(3600).Board("看板内容")
await event.send_chain().DismissBoard()

# OneBot12 メッセージセグメントを使用した返信
from ErisPulse.Core.Event import MessageBuilder
msg = MessageBuilder().text("Hello").image("url").build()
await event.reply_ob12(msg)

# 返信の待機
reply = await event.wait_reply(timeout=30)
```

### プラットフォーム機能の確認

```python
# 現在のプラットフォームが特定の送信方法をサポートしているかを確認
if event.supports("Image"):
    await event.reply(url, method="Image")

# 現在のプラットフォームで利用可能なすべての送信方法を一覧表示
methods = event.available_methods()
# ["Text", "Image", "Voice", ...]
```

### 返信メソッド

`reply()` メソッドは `method` パラメータで送信タイプを指定し、2つの便利なブールパラメータをサポートしています。

```python
# 簡単なテキスト返信
await event.reply("こんにちは")

# 送信者への @付き返信
await event.reply("こんにちは", at_sender=True)

# 現在のメッセージを引用した返信
await event.reply("受信しました", reply_to_message=True)

# 組み合わせ
await event.reply("受信しました", at_sender=True, reply_to_message=True)

# 画像の送信（method パラメータを使用）
if event.supports("Image"):
    await event.reply("http://example.com/img.jpg", method="Image")
else:
    await event.reply("[画像] http://example.com/img.jpg")
```

**パラメータの説明**：

| パラメータ | 型 | 説明 |
|------|------|------|
| `content` | str | 送信内容 |
| `method` | str | 送信方法、デフォルトは "Text"、選択肢は "Image"/"Voice"/"Video"/"File" など |
| `at_sender` | bool | 送信者を @ するか（自動的に user_id を抽出） |
| `quote` | bool | 現在のメッセージを引用して返信するか（自動的に message_id を抽出） |
| `at_users` | list[str] | 指定したユーザーリストを @ |
| `reply_to` | str | 手動で指定したメッセージ ID を返信先とする |
| `at_all` | bool | 全体を @ するか |

### インタラクションメソッド

```python
# confirm — 会話の確定（True/False/None を返す）
if await event.confirm("この操作を実行しますか？"):
    await event.reply("確定しました")

# Text 以外の方式で確認プロンプトを送信
if await event.confirm("http://example.com/image.jpg", method="Image"):
    await event.reply("画像の提示を確認しました")

# choose — 選択メニュー（オプションのインデックスまたは None を返す）
choice = await event.choose("色を選んでください：", ["赤", "緑", "青"])

# options_format="auto"（デフォルト）method に合わせて自動でスタイルを選択します：
# Markdown→順序なしリスト（- 1.オプション）、Html→順序付きリスト（<ol>）、その他→プレーンテキストリスト
# テキスト系メソッド（Markdown/Html 等）はデフォルトで末尾にオプションを統合します
# merge_prompt=True を指定すると任意の method で強制的に統合が可能です。placeholder でプレースホルダーをカスタマイズできます
choice = await event.choose(
    "## 選択してください\n{options}", ["A", "B"],
    method="Markdown", merge_prompt=True,
)

# collect — フォーム収集（{key: value} の辞書または None を返す）
data = await event.collect([
    {"key": "name", "prompt": "お名前を入力してください："},
    {"key": "age", "prompt": "年齢を入力してください：",
     "validator": lambda e: e.get_text().isdigit()},
    {"key": "avatar", "prompt": "アバターを送信してください：", "method": "Image"},
])

# wait_for — 条件を満たす任意のイベントを待機する
evt = await event.wait_for(event_type="notice", condition=lambda e: ..., timeout=120)

# conversation — 多ラウンド会話のコンテキスト
conv = event.conversation(timeout=60)
await conv.say("ようこそ！")
```

> 詳細なインタラクションメソッドのパラメータ説明やその他の例については、[Event クラスの詳細](../developer-guide/modules/event-wrapper.md)と[Conversation 多ラウンド会話](../advanced/conversation.md)を参照してください。

### ユーティリティメソッド

```python
# ディクショナリへ変換（アンダースコアで始まる内部キーはフィルタリングされます）
event_dict = event.to_dict()

# 原始データの取得
raw = event.get_raw()
raw_type = event.get_raw_type()
```

### 処理制御

`event.done(claim=, stop=)` は、「認証」と「ブロック」の2つの直交するセマンティクスを統一して制御します：

- **認証（claim）**：イベントが処理済みであることをマーク（`_processed`）、コマンドディスパッチャーはこれによりスキップします。
- **ブロック（stop）**：低優先度のハンドラーへの伝播を防ぐ（`_propagation_stopped`）。

```python
# 認証 + ブロック（デフォルト）
event.done()

# 認証のみ、ブロックしない（低優先度のオブザーバーでも確認可能）
event.done(stop=False)

# ブロックのみ、認証しない（ファイアウォール / レート制限など）
event.done(claim=False)

# mark_processed はメインメソッドで、done はそのエイリアスです
event.mark_processed()             # event.done() と等価
event.mark_processed(stop=False)   # event.done(stop=False) と等価

# ステータスの確認
event.is_processed()  # 既に認証済みか
event.is_stopped()    # 伝播がブロック済みか
```

### プラットフォーム拡張メソッド

アダプターは Event にプラットフォーム固有のメソッドを登録でき、それらは対応するプラットフォームのインスタンスでのみ使用可能です。

#### ユーザー：プラットフォーム拡張メソッドの使用

アダプターがプラットフォーム固有のメソッドを登録した後は、イベントハンドラー内で直接呼び出せます。各プラットフォームのメソッドは異なりますが、対応する[プラットフォームガイド](../platform-guide/)を参照してください。

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

#### プラットフォームで登録されたメソッドの確認

```python
from ErisPulse.Core.Event import get_platform_event_methods

# 特定のプラットフォームに登録されているメソッドを表示
methods = get_platform_event_methods("email")
# ["get_subject", "get_from", "get_attachments", ...]

# 動的に判定して呼び出す
for method_name in get_platform_event_methods(event.get_platform()):
    method = getattr(event, method_name)
    print(f"{method_name}: {method()}")
```

#### プラットフォームメソッドの分離

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

#### `hasattr` / `dir` サポート

```python
hasattr(event, "get_subject")   # platform="email" の時のみ True を返します
"get_subject" in dir(event)     # 同上
```

### アダプター：プラットフォーム拡張メソッドの登録

アダプターはデコレータを使用して Event にプラットフォーム固有のメソッドを登録できます。メソッドの最初のパラメータは `self`（Event インスタンス）で、自由にイベントデータにアクセスできます。

#### 単一のメソッド登録

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

#### 複数のメソッド登録（Mixin クラス）

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

| 場合 | 返り値 | ユーザー使用方法 |
|------|--------|------------|
| データの返却（テキスト、辞書など） | 直接返り値 | `subject = event.get_subject()` |
| 操作の実行（メッセージ送信など） | `asyncio.Task` を返す | `task = event.do_something()` 可選で `await` |

> **推奨**：データ以外の返り値を持つメソッドは `asyncio.Task` を返すようにします。これにより、ユーザーが自分で `await` するかどうかを選択でき、`await` しなくても操作は実行完了します。

```python
@register_event_method("email")
def forward_email(self, to_address: str):
    """メールを転送 — Task を返すため、ユーザーが await するかどうかを決定できます"""
    import asyncio
    return asyncio.create_task(
        self._do_forward(to_address)
    )

# ユーザーは await して結果を待機できます
await event.forward_email("user@example.com")

# または await せず、バックグラウンドで操作を実行できます
event.forward_email("user@example.com")
```

#### メソッドの登録解除

```python
from ErisPulse.Core.Event import unregister_event_method, unregister_platform_event_methods

# 単一のメソッドを登録解除
unregister_event_method("email", "get_subject")

# 特定のプラットフォームのすべてのメソッドを登録解除（アダプターシャットダウン時に呼び出します）
unregister_platform_event_methods("email")
```

#### 組み込みメソッドのオーバーライド

`register_event_mixin` / `register_event_method` は、Event の組み込みメソッド（`confirm`、`choose`、`collect`、`wait_reply`、`reply` など）のオーバーライドをサポートします。登録されたプラットフォーム固有のメソッドは、Event.__getattribute__ を通じて組み込みメソッドより優先して適用されるため、アダプターはプラットフォーム独自のインタラクション実装を提供できます。

組み込み実装は `_builtin_*` 関数としてエクスポートされており、オーバーライドする側はそれらをフォールバックとして呼び出せます：

```python
from ErisPulse.Core.Event import register_event_mixin, _builtin_choose

class YunhuEventMixin:
    async def choose(self, prompt, options, timeout=60, method="Text"):
        # 雲湖プラットフォームはボタンコンポーネントを使用
        buttons = [[{"text": opt} for opt in options]]
        await self.reply(prompt)
        # ...ボタンのコールバックやテキスト応答を待機...
        # 組み込みロジックにフォールバック
        return await _builtin_choose(self, None, options, timeout, "Text")

register_event_mixin("yunhu", YunhuEventMixin)

## 跨プラットフォーム拡張（ワイルドカード）

`register_event_method` と `register_event_mixin` はプラットフォーム名として `"*"` を渡すことをサポートしており、登録されたメソッドは**すべてのプラットフォーム**の Event インスタンス上で使用可能です。AI対話やコンテキスト管理など、プラットフォームをまたがって再利用する必要がある機能モジュールに適しています。

### 跨プラットフォームメソッドの登録

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    """self は Event インスタンスであり、イベントデータや組み込みメソッドに自由にアクセス可能です"""
    await self.reply(f"AI: {prompt}")
```

登録後、すべてのプラットフォームのイベントハンドラから呼び出すことができます：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handler(event):
    await event.ai_chat(event.get_text())
```

### メソッド解決の優先順位

Event メソッドに属性アクセスする場合、解決順序は以下のようになります：

1. **プラットフォーム固有のメソッド**（現在のプラットフォームでのオーバーライド）
2. **ワイルドカードメソッド**（`"*"` で登録された跨プラットフォームメソッド）
3. **組み込みメソッド**（`reply`、`confirm` など）
4. **辞書キーによるアクセス**

> そのため、ワイルドカードメソッドは組み込みメソッド（`reply` など）をオーバーライドすることは可能ですが、同名のプラットフォーム固有のメソッドによってさらにオーバーライドされます。

## 優先順位システム

イベントハンドラーは優先順位をサポートしており、数値が大きいほど優先度が高くなります：

```python
# 高優先度のハンドラーは先に実行されます
@message.on_message(priority=10)
async def high_priority_handler(event):
    pass

# 低優先度のハンドラーは後に実行されます
@message.on_message(priority=0)
async def low_priority_handler(event):
    pass

## 関連ドキュメント

- [コアモジュール API](core-modules.md) - コアモジュール API
- [アダプタシステム API](adapter-system.md) - アダプタ管理 API
- [モジュール開発ガイド](../developer-guide/modules/) - カスタムモジュールの開発