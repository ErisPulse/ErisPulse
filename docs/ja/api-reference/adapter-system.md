# アダプターシステム API

> [!TIP]
> **このドキュメントを読むべきケース**：アダプターの管理（インスタンスの取得、起動・停止、Bot のオンライン状態の確認）、Send DSL によるメッセージ送信、ミドルウェアの登録、またはアダプターへの Bot ステータス報告（meta イベント）の実装が必要な場合に本文をご参照ください。該当しない場合はスキップしてください。

このドキュメントでは、ErisPulse アダプターシステムの API について詳しく説明します。

## Adapter マネージャー

### アダプターの取得

```python
from ErisPulse import sdk

# 名前でアダプターを取得
adapter = sdk.adapter.get("platform_name")

# または、属性で直接アクセスすることもできます
adapter = sdk.adapter.platform_name
```

### アダプターイベントリスナーの使用
> 通常は、イベントの監視/処理には`Event`モジュールを使用することをお勧めします。
>
> また、`Event`モジュールは強力なラッパーを提供しており、モジュール開発にさらに便利さをもたらします。

```python
# OneBot12 標準イベントをリッスン
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# 特定プラットフォームの標準イベントをリッスン
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# プラットフォームのネイティブイベントをリッスン
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### アダプターの管理

```python
# すべてのプラットフォームを取得
platforms = sdk.adapter.platforms

# アダプターが存在するかどうかを確認
exists = sdk.adapter.exists("platform_name")

# アダプターの有効化/無効化
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# アダプターの起動/終了
# 以下のメソッドはいずれも引数を渡す場合の例であり、引数なしの場合は登録済みのすべてのアダプターの起動/停止を意味します
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# アダプターが実行中かどうかを確認
is_running = sdk.adapter.is_running("platform_name")

# 実行中のすべてのアダプターを一覧表示
running = sdk.adapter.list_running()

# アダプターのメタ情報を取得（module.get_meta と整合、パネル/ストアなどで利用される）
info = sdk.adapter.get_info("platform_name")   # 登録情報（meta + クラス名、json-safe）
meta = sdk.adapter.get_meta("platform_name")   # 紹介メタ情報（description は i18n 解析に対応）
raw = sdk.adapter.get_meta("platform_name", resolve_i18n=False)  # 生の i18n 辞書をそのまま返す
```

## ミドルウェア

ミドルウェアは、イベントがハンドラーにディスパッチされる前に実行され、イベントデータの変更、フィルタリング、記録などを行うことができます。

### ミドルウェアの登録

```python
@sdk.adapter.middleware
async def my_middleware(event):
    sdk.logger.info(f"ミドルウェア処理: {event}")
    return event
```

### ミドルウェアの実行モデル

- **実行順序**：ミドルウェアは登録順に実行されます（先に登録されたものが先に実行される）
- **データの受け渡し**：各ミドルウェアは、直前のミドルウェアが返した `event` データを受け取ります。いずれかのミドルウェアが `None` を返した場合、その戻り値は無視され、元のデータが保持されたまま引き続き渡されます（同時に `warning` レベルのログが出力されます）
- **データの変更**：ミドルウェアはイベントデータを変更し、変更後の辞書を返すことができます
- **イベントの否決**：ミドルウェアが明示的に `False` を返した場合、イベントは否決されます。イベントは破棄され、どのハンドラーにも渡されず、アウトバウンドの副作用も一切発生しません。否決時には TRACE ログが出力され、`adapter.event.blocked` ライフサイクルフックがトリガーされます（ミドルウェア名と完全なイベントが渡されます）

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
            return False  # 否決：イベントは破棄され、どのハンドラーにも渡されません
    return event
```

> **注意**：イベントを否決するのは、明示的に `False` を返した場合のみです（空の辞書 / `0` / `""` などの falsy 値を返しても否決されません）。
> `None` を返した場合も通過し、ペイロードは変更されません。否決されたイベントは、
> `adapter.event.blocked` フックをリッスンすることで、「イベントがなぜ応答しなかったのか」の監査や調査が可能です。

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

### サポートされる送信メソッドの照会

```python
# プラットフォームがサポートするすべての送信メソッドを一覧表示
methods = sdk.adapter.list_sends("onebot11")
# 戻り値: ["Text", "Image", "Voice", "Markdown", ...]

# 特定のメソッドの詳細情報を取得
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

### チェーン装飾

```python
# @ユーザー
await adapter.Send.To("group", "456").At("789").Text("こんにちは")

# @全員
await adapter.Send.To("group", "456").AtAll().Text("皆さん、こんにちは")

# メッセージに返信
await adapter.Send.To("group", "456").Reply("msg_id").Text("返信内容")

# 組み合わせて使用
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("@したメッセージへの返信")
```

## API 呼び出し

### call_api メソッド

> **注意**：`call_api` はプラットフォームのネイティブ API を直接呼び出す低レベルメソッドです。パラメータや戻り値はプラットフォームによって異なる場合があるため、対応するプラットフォームのアダプタードキュメントをご参照ください。**メッセージの送信には Send DSL の使用をお勧めします**。`call_api` は、Send DSL が対応していないシナリオ（プラットフォーム固有のデータの取得やプラットフォーム管理インターフェースの呼び出しなど）でのみ使用してください。

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

## アダプター基底クラス

### BaseAdapter のメソッド

```python
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
        # アダプターの初期化
        pass
    
    async def start(self):
        """アダプターを起動する（実装必須）"""
        pass
    
    async def shutdown(self):
        """アダプターを終了する（実装必須）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォーム API を呼び出す（実装必須）"""
        pass
```

### Send ネストクラス

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        def Text(self, text: str):
            """テキストメッセージを送信する"""
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

アダプターは、OneBot12 標準の **`meta` イベント**を送信することで、フレームワークに Bot の接続状態を通知します。システムはそこから自動的に Bot 情報を抽出し、ステータスの追跡を行います。

### meta イベントの報告

アダプターは `meta` イベントを通じて Bot のステータスを報告します。`detail_type` は 3 種類あります：`connect`（登録してオンライン）、`heartbeat`（ハートビートによる生存維持）、`disconnect`（オフラインとしてマーク）。`emit_meta()` を使って 1 行で送信することをお勧めします。meta イベントを送信しない場合でも、フレームワークは通常のイベント（message/notice/request）の `self` フィールドから自動的に Bot を検出します。

- **meta イベントの形式と送信方法**（送信タイミング、`emit_meta()` の使い方、手動での形式構築）については、[アダプターのベストプラクティス - Bot ステータス管理と Meta イベント](../developer-guide/adapters/best-practices.md#bot-状态管理与-meta-事件) をご参照ください
- **自動検出メカニズムとフレームワークの動作**については、[アダプターのコアコンセプト - Bot ステータス管理](../developer-guide/adapters/core-concepts.md#bot-状态管理) をご参照ください

### Bot ステータスの照会

```python
# すべてのアダプターと Bot の完全なステータスを取得（WebUI フレンドリー）
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

# すべての Bot を一覧表示
all_bots = sdk.adapter.list_bots()

# 指定したプラットフォームの Bot を一覧表示
tg_bots = sdk.adapter.list_bots("telegram")

# 単一の Bot の詳細を取得
info = sdk.adapter.get_bot_info("telegram", "123456")

# Bot がオンラインかどうかを確認
if sdk.adapter.is_bot_online("telegram", "123456"):
    print("Bot はオンラインです")
```

### Bot ステータスの値

| ステータス | 説明 |
|------|------|
| `online` | オンライン（イベントを継続的に受信、またはアダプターによる明示的なマーク） |
| `offline` | オフライン（アダプターによる明示的なマーク、またはシステム終了時に自動設定） |
| `unknown` | 不明（登録のみでステータス未確認） |

### ライフサイクルイベント

| イベント名 | 発生タイミング | データ |
|--------|---------|------|
| `adapter.bot.online` | 新しい Bot を初めて自動検出した時 | `{platform, bot_id, status}` |
| `adapter.status.change` | アダプターのステータス変化時 | `{platform, status}`。status のすべての値：`starting` / `started` / `start_failed` / `stopping` / `stopped` / `stop_failed` / `skipped-dependency`（依存するアダプターが未準備のため起動をスキップ）/ `disabled`（設定により無効化） |

```python
# Bot オンラインイベントをリッスン
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Bot がオンライン: {event['data']['platform']}/{event['data']['bot_id']}")

# アダプターのステータス変化をリッスン
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"アダプター状態: {event['data']['platform']} -> {event['data']['status']}")
```

> システム終了時（`shutdown`）には、すべての Bot が自動的に `offline` としてマークされます。

## 関連ドキュメント

**API の参照を続ける**：
- [コアモジュール API](core-modules.md) - コアモジュールの API
- [イベントシステム API](event-system.md) - Event モジュールの API

**アダプターを書いてみる**：
- [アダプター開発ガイド](../developer-guide/adapters/) - プラットフォームアダプターの開発
- [アダプター標準化ガイド（総綱）](../standards/standardization-guide.md) - 新しいアダプターを実装する前の標準照合と Checklist