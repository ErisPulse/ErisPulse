# アダプターシステム API

このドキュメントでは、ErisPulse アダプターシステムの API を詳細に紹介します。

## Adapter 管理器

### アダプタの取得

```python
from ErisPulse import sdk

# 名前でアダプタを取得
adapter = sdk.adapter.get("platform_name")

# または属性アクセスで直接取得
adapter = sdk.adapter.platform_name
```

### アダプタイベントの監視
> 通常は、`Event`モジュールを使用してイベントの監視/処理を行うことを推奨します。
> 同時に、`Event`モジュールは強力なラッパーを提供し、モジュール開発の利便性を高めます。

```python
# OneBot12 標準イベントを監視
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# 特定プラットフォームの標準イベントを監視
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# プラットフォームのネイティブイベントを監視
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### アダプタ管理

```python
# 全プラットフォームを取得
platforms = sdk.adapter.platforms

# アダプタが存在するか確認
exists = sdk.adapter.exists("platform_name")

# アダプタの有効化/無効化
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# アダプタの起動/停止
# 以下のメソッドはすべて引数を渡す例を示しています。引数がない場合は、登録済みのすべてのアダプタの起動/停止を意味します
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# アダプタが実行中か確認
is_running = sdk.adapter.is_running("platform_name")

# 実行中のアダプタを一覧表示
running = sdk.adapter.list_running()
```

## ミドルウェア

### ミドルウェアの登録

```python
# ミドルウェアを追加
@sdk.adapter.middleware
async def my_middleware(event):
    # イベントを処理
    sdk.logger.info(f"ミドルウェア処理: {event}")
    return event
```

### ミドルウェアの実行順序

ミドルウェアは登録順に実行され、イベントがハンドラにルーティングされる前に実行されます。

## Send メッセージ送信

### 基本的な送信

```python
# アダプタを取得
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

### サポートされている送信メソッドのクエリ

```python
# プラットフォームがサポートするすべての送信メソッドを一覧表示
methods = sdk.adapter.list_sends("onebot11")
# 返回: ["Text", "Image", "Voice", "Markdown", ...]

# 特定のメソッドの詳細を取得
info = sdk.adapter.send_info("onebot11", "Text")
# 返回:
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "テキストメッセージを送信..."
# }
```

### チェーン構造修飾

```python
# @ユーザー
await adapter.Send.To("group", "456").At("789").Text("こんにちは")

# @全体メンバー
await adapter.Send.To("group", "456").AtAll().Text("皆さんこんにちは")

# メッセージへの返信
await adapter.Send.To("group", "456").Reply("msg_id").Text("返信内容")

# 組み合わせて使用
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("@への返信")
```

## API 呼び出し

### call_api メソッド
> 注意：各プラットフォームの API 呼び出し方法は異なる場合があります。各プラットフォーム固有のアダプタドキュメントを参照してください。
> call_api メソッドを直接使用することは推奨されません。メッセージ送信には Send クラスを使用することを推奨します。

```python
# プラットフォーム API を呼び出す
result = await adapter.call_api(
    endpoint="/send",
    content="Hello",
    recvId="123",
    recvType="user"
)

# 標準化された応答
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "msg_id",
    "message": "",
    "{platform}_raw": raw_response
}
```

## アダプタの基本クラス

### BaseAdapter メソッド

```python
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
        # アダプタを初期化
        pass
    
    async def start(self):
        """アダプタを起動（必須実装）"""
        pass
    
    async def shutdown(self):
        """アダプタを停止（必須実装）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォーム API を呼び出す（必須実装）"""
        pass
```

### Send ネストクラス

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

## Bot ステータス管理

アダプタは、OneBot12 標準の **`meta` イベント**を送信することで、フレームワークに対して Bot の接続状態を通知します。システムは自動的に Bot 情報を抽出し、ステータス追跡を行います。

### meta イベントの種類

アダプタは以下の 3 種類の `meta` イベントを送信すべきです：

| `type` | `detail_type` | 説明 | 実行タイミング |
|--------|--------------|------|---------|
| `meta` | `connect` | Bot 接続開始 | アダプタとプラットフォームの接続に成功した後 |
| `meta` | `heartbeat` | Bot ハートビート | 定期的に送信（推奨 30-60 秒） |
| `meta` | `disconnect` | Bot 接続切断 | 接続切断を検知した時 |

### self フィールドの拡張

ErisPulse は OneBot12 標準の `self` フィールドに以下の拡張フィールドを追加しています：

| フィールド | タイプ | 説明 |
|------|------|------|
| `self.platform` | string | プラットフォーム名（OB12 標準） |
| `self.user_id` | string | Bot ユーザー ID（OB12 標準） |
| `self.user_name` | string | Bot の表示名（ErisPulse 拡張） |
| `self.avatar` | string | Bot のアバター URL（ErisPulse 拡張） |
| `self.account_id` | string | マルチアカウント識別子（ErisPulse 拡張） |

### meta イベントのフォーマット

#### connect — 接続開始

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

システム処理：Bot を登録し、`online` としてマーク、`adapter.bot.online` ライフサイクルイベントをトリガーします。

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

システム処理：`last_active` 時間を更新します（ハートビートでもメタ情報の更新がサポートされています）。

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

システム処理：Bot を `offline` としてマークし、`adapter.bot.offline` ライフサイクルイベントをトリガーします。

### 通常イベントの自動検出

`meta` イベントに加え、通常のイベント（`message`/`notice`/`request`）の `self` フィールドも自動的に検出され、Bot を登録してアクティビティ時間を更新します。これは、アダプタが `connect` イベントを送信しなくても、フレームワークが最初の通常イベントから Bot を検出できることを意味します。

### アダプタ実装例

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # プラットフォームと接続を確立...
        connection = await self._connect()
        
        # 接続に成功し、connect イベントを送信
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
        # 接続切断し、disconnect イベントを送信
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

### Bot ステータスの照会

```python
# 全アダプタと Bot の完全なステータスを取得（WebUI 友好）
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

# 全 Bot を一覧表示
all_bots = sdk.adapter.list_bots()

# 指定プラットフォームの Bot を一覧表示
tg_bots = sdk.adapter.list_bots("telegram")

# 単一の Bot の詳細を取得
info = sdk.adapter.get_bot_info("telegram", "123456")

# Bot がオンラインか確認
if sdk.adapter.is_bot_online("telegram", "123456"):
    print("Bot オンライン")
```

### Bot ステータス値

| ステータス | 説明 |
|------|------|
| `online` | オンライン（継続的にイベントを受信、またはアダプタが主动でマークした場合） |
| `offline` | オフライン（アダプタが主动でマーク、またはシステムシャットダウン時に自動設定） |
| `unknown` | 不明（登録のみでステータス未確認） |

### ライフサイクルイベント

| イベント名 | 実行タイミング | データ |
|--------|---------|------|
| `adapter.bot.online` | 新しい Bot が自動的に検出された時 | `{platform, bot_id, status}` |
| `adapter.status.change` | アダプタのステータスが変更された時（starting/started/stopping/stopped/stop_failed） | `{platform, status}` |

```python
# Bot オンラインイベントを監視
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Bot オンライン: {event['data']['platform']}/{event['data']['bot_id']}")

# アダプタのステータス変化を監視
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"アダプタのステータス: {event['data']['platform']} -> {event['data']['status']}")
```

> システムシャットダウン時（`shutdown`）、すべての Bot は自動的に `offline` としてマークされます。

## 関連ドキュメント

- [コアモジュール API](core-modules.md) - コアモジュール API
- [イベントシステム API](event-system.md) - Event モジュール API
- [アダプタ開発ガイド](../developer-guide/adapters/) - プラットフォームアダプタの開発