# アダプターシステム API

本文書では、ErisPulse アダプターシステムの API について詳しく説明します。

## アダプターマネージャー

### アダプターの取得

```python
from ErisPulse import sdk

# 名称でアダプターを取得
adapter = sdk.adapter.get("platform_name")

# または、属性で直接アクセスすることもできます
adapter = sdk.adapter.platform_name
```

### アダプターイベントの監視
> 通常、`Event` モジュールを使ってイベントの監視/処理を行うことを推奨します。
>
> また、`Event` モジュールは強力なラッパーを提供しており、モジュール開発に多くの利便性をもたらします。

```python
# OneBot12 標準イベントを監視
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# 特定のプラットフォームの標準イベントを監視
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# プラットフォームのネイティブイベントを監視
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### アダプターマネージメント

```python
# すべてのプラットフォームを取得
platforms = sdk.adapter.platforms

# アダプターが存在するか確認
exists = sdk.adapter.exists("platform_name")

# アダプターの有効化/無効化
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# アダプターの起動/停止
# 以下のメソッドは、引数を渡す場合の例を示しています。引数なしの場合は、すべての登録されたアダプターを起動/停止します。
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# アダプターの実行状態を確認
is_running = sdk.adapter.is_running("platform_name")

# 実行中のすべてのアダプターをリストアップ
running = sdk.adapter.list_running()

# アダプターのメタ情報を取得（module.get_meta と対応、パネル / ストア等の消費用）
info = sdk.adapter.get_info("platform_name")   # 登録情報（meta + クラス名、json-safe）
meta = sdk.adapter.get_meta("platform_name")   # 説明メタ情報（description は i18n 解析をサポート）
raw = sdk.adapter.get_meta("platform_name", resolve_i18n=False)  # 透かし i18n ディクショナリをそのまま返す
```

## ミドルウェア

ミドルウェアは、イベントがハンドラに配信される前に実行され、イベントデータを変更、フィルタ、または記録することができます。

### ミドルウェアの登録

```python
@sdk.adapter.middleware
async def my_middleware(event):
    sdk.logger.info(f"ミドルウェア処理: {event}")
    return event
```

### ミドルウェア実行モデル

- **実行順序**：ミドルウェアは登録順に実行されます（先に登録されたものから実行）
- **データの伝達**：各ミドルウェアは、前のミドルウェアが返した `event` データを受け取ります。もし、あるミドルウェアが `None` を返した場合、その返り値は無視され、元のデータが引き続き伝達されます（同時に `warning` レベルのログが出力されます）
- **データの変更**：ミドルウェアはイベントデータを変更して、変更後の辞書を返すことができます
- **イベントの否認**：ミドルウェアが明示的に `False` を返した場合、イベントは否認されます—イベントはすべてのハンドラに渡らず、出力副作用も一切ありません。否認された場合、`TRACE` ログが出力され、`adapter.event.blocked` ライフサイクルフックがトリガーされ、ミドルウェア名と完全なイベントが渡されます

```python
@sdk.adapter.middleware
async def add_timestamp(event):
    event["processed_at"] = time.time()
    return event

@sdk.adapter.middleware
async def filter_spam(event):
    if event.get("detail_type") == "private":
        text = event.get("alt_message", "")
        if "スパム広告" in text:
            return False  # 否認：イベントはハンドラに渡らず、すべての出力副作用も無視
    return event
```

> **注意**：イベントを否認するのは、明示的に `False` を返した場合のみです（空の辞書 / `0` / `""` などの falsy 値を返しても否認されません）；
> `None` を返しても、イベントは許可され、負荷は変化しません。否認されたイベントは、`adapter.event.blocked` フックを監視することで、イベントがなぜ応答しなかったのかを監査・調査することができます。

## Send メッセージ送信

### 基本的な送信

```python
# アダプターを取得
adapter = sdk.adapter.get("platform")

# テキストメッセージを送信
await adapter.Send.To("user", "123").Text("Hello")

# 画像メッセージを送信
await adapter.Send.To("group", "456").Image("https://example.com/image.jpg")
```

### 送信アカウントの指定

```python
# アカウント名を使用
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# アカウント ID を使用
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### 送信メソッドの照会

```python
# プラットフォームがサポートするすべての送信メソッドをリストアップ
methods = sdk.adapter.list_sends("onebot11")
# 戻り値: ["Text", "Image", "Voice", "Markdown", ...]

# あるメソッドの詳細情報を取得
info = sdk.adapter.send_info("onebot11", "Text")
# 戻り値:
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "テキストメッセージを送信..."
# }
```

### チェーン修飾

```python
# @ユーザー
await adapter.Send.To("group", "456").At("789").Text("こんにちは")

# @全員
await adapter.Send.To("group", "456").AtAll().Text("みなさんこんにちは")

# メッセージへの返信
await adapter.Send.To("group", "456").Reply("msg_id").Text("返信内容")

# 組み合わせ
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("返信@メッセージ")
```

## API 呼び出し

### call_api メソッド

> **注意**：`call_api` は、プラットフォームのネイティブ API を直接呼び出す低レベルメソッドです。各プラットフォームのパラメータと戻り値は異なる可能性があるため、対応するプラットフォームアダプターのドキュメントを参照してください。**Send DSL を使用することを推奨します**。Send DSL がサポートしていない場面（プラットフォーム固有のデータの取得、プラットフォーム管理インターフェースの呼び出し等）でのみ `call_api` を使用してください。

```python
# プラットフォーム API を呼び出す
result = await adapter.call_api(
    endpoint="/send",
    content="Hello",
    recvId="123",
    recvType="user"
)

# 標準化されたレスポンス
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "msg_id",
    "message": "",
    "{platform}_raw": raw_response
}
```

## アダプターベースクラス

### BaseAdapter メソッド

```python
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
        # アダプターを初期化
        pass
    
    async def start(self):
        """アダプターを起動する（必須実装）"""
        pass
    
    async def shutdown(self):
        """アダプターを停止する（必須実装）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォーム API を呼び出す（必須実装）"""
        pass
```

### Send 嵌套クラス

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        def Text(self, text: str):
            """テキストメッセージを送信"""
            import asyncio
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )
```

## Bot 状態管理

アダプターは、OneBot12 標準の **`meta` イベント**を送信することで、フレームワークに Bot の接続状態を通知します。システムは、このイベントから Bot 情報を自動的に抽出して、状態を追跡します。

### meta イベントタイプ

アダプターは、以下の 3 種類の `meta` イベントを送信する必要があります：

| `type` | `detail_type` | 説明 | 発生タイミング |
|--------|--------------|------|---------|
| `meta` | `connect` | Bot が接続・オンライン | アダプターがプラットフォームとの接続を確立した後 |
| `meta` | `heartbeat` | Bot のハートビート | 定期的に送信（推奨 30-60 秒） |
| `meta` | `disconnect` | Bot が接続を切断 | 接続が切断されたと検知したとき |

### self フィールド拡張

ErisPulse は、OneBot12 標準の `self` フィールドに以下のオプションフィールドを拡張しています：

| フィールド | タイプ | 説明 |
|------|------|------|
| `self.platform` | string | プラットフォーム名（OB12 標準） |
| `self.user_id` | string | Bot ユーザー ID（OB12 標準） |
| `self.user_name` | string | Bot ニックネーム（ErisPulse 拡張） |
| `self.avatar` | string | Bot アバター URL（ErisPulse 拡張） |
| `self.account_id` | string | 多アカウント識別子（ErisPulse 拡張） |

### meta イベント形式

#### connect — 接続・オンライン

```python
await adapter.emit({
    "id": "unique_id",
    "time": 1712345678,
    "type": "meta",
    "detail_type": "connect",
    "platform": "telegram",
    "self": {
        "platform": "telegram",
        "user_id": "123456",
        "user_name": "MyBot",
        "avatar": "https://example.com/avatar.jpg"
    },
    "telegram_raw": {...},
    "telegram_raw_type": "bot_connected"
})
```

システム処理：Bot を登録し、`online` にマークし、`adapter.bot.online` ライフサイクルイベントをトリガーします。

#### heartbeat — ハートビート

```python
await adapter.emit({
    "id": "unique_id",
    "time": 1712345708,
    "type": "meta",
    "detail_type": "heartbeat",
    "platform": "telegram",
    "self": {
        "platform": "telegram",
        "user_id": "123456"
    }
})
```

システム処理：`last_active` 時間を更新（ハートビートではメタ情報の更新もサポート）。

#### disconnect — 接続切断

```python
await adapter.emit({
    "id": "unique_id",
    "time": 1712345738,
    "type": "meta",
    "detail_type": "disconnect",
    "platform": "telegram",
    "self": {
        "platform": "telegram",
        "user_id": "123456"
    }
})
```

システム処理：Bot を `offline` にマークし、`adapter.bot.offline` ライフサイクルイベントをトリガーします。

### 通常イベントの自動発見

`meta` イベント以外にも、通常イベント（`message`/`notice`/`request`）の `self` フィールドは、自動的に Bot を発見して登録し、アクティブ時間を更新します。つまり、アダプターが `connect` イベントを送信しなくても、フレームワークは最初の通常イベントから Bot を発見することができます。

### アダプター接続例

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # プラットフォームとの接続を確立...
        connection = await self._connect()
        
        # 接続成功、connect イベントを送信
        await adapter.emit({
            "id": str(uuid4()),
            "time": int(time.time()),
            "type": "meta",
            "detail_type": "connect",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": self.bot_id,
                "user_name": self.bot_name,
                "avatar": self.bot_avatar
            },
            "myplatform_raw": raw_data,
            "myplatform_raw_type": "connected"
        })
    
    async def on_disconnect(self):
        # 接続切断、disconnect イベントを送信
        await adapter.emit({
            "id": str(uuid4()),
            "time": int(time.time()),
            "type": "meta",
            "detail_type": "disconnect",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": self.bot_id
            }
        })
```

### Bot 状態の照会

```python
# すべてのアダプターと Bot の完全な状態を取得（WebUI 友好）
summary = sdk.adapter.get_status_summary()
# {
#     "adapters": {
#         "telegram": {
#             "status": "started",
#             "bots": {
#                 "123456": {
#                     "status": "online",
#                     "last_active": 1712345678.0,
#                     "info": {"nickname": "MyBot"}
#                 }
#             }
#         }
#     }
# }

# すべての Bot をリストアップ
all_bots = sdk.adapter.list_bots()

# 指定プラットフォームの Bot をリストアップ
tg_bots = sdk.adapter.list_bots("telegram")

# 単一 Bot の詳細を取得
info = sdk.adapter.get_bot_info("telegram", "123456")

# Bot がオンラインか確認
if sdk.adapter.is_bot_online("telegram", "123456"):
    print("Bot はオンラインです")
```

### Bot 状態値

| 状態 | 説明 |
|------|------|
| `online` | オンライン（継続的にイベントを受け取るか、アダプターが明示的にマーク） |
| `offline` | オフライン（アダプターが明示的にマーク、またはシステムのシャットダウン時に自動設定） |
| `unknown` | 未知（登録のみ、状態が確認されていない） |

### ライフサイクルイベント

| イベント名 | 発生タイミング | データ |
|--------|---------|------|
| `adapter.bot.online` | 新しい Bot が自動的に発見されたとき | `{platform, bot_id, status}` |
| `adapter.status.change` | アダプターの状態が変化したとき | `{platform, status}`、status の完全な値：`starting` / `started` / `start_failed` / `stopping` / `stopped` / `stop_failed` / `skipped-dependency`（依存するアダプターが準備できていないために起動をスキップ） / `disabled`（設定で無効化） |

```python
# Bot オンラインイベントを監視
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Bot オンライン: {event['data']['platform']}/{event['data']['bot_id']}")

# アダプター状態変化を監視
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"アダプター状態: {event['data']['platform']} -> {event['data']['status']}")
```

> システムのシャットダウン時（`shutdown`）、すべての Bot は自動的に `offline` にマークされます。

## 関連ドキュメント

- [コアモジュール API](core-modules.md) - コアモジュール API
- [イベントシステム API](event-system.md) - Event モジュール API
- [アダプター開発ガイド](../developer-guide/adapters/) - プラットフォームアダプターの開発