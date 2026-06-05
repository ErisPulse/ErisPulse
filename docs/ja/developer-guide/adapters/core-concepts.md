# アダプターのコア概念

ErisPulse アダプターのコア概念を理解することは、アダプター開発の基礎となります。

## アダプターのアーキテクチャ

### コンポーネントの関係

```
正方向変換（受信方向）                           逆方向変換（送信方向）
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ プラットフォーム  │                        │ モジュールによる   │
│ ネイティブイベント│                        │ メッセージ構築     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │ アダプター        │   │                  │
│  Converter       │   │ (MyAdapter)      │   │ Send.Raw_ob12()  │
│  (イベント       │──→│ ┌──────────────┐ │   │ (逆方向変換      │
│   コンバーター)  │   │ │              │ │   │  エントリ)       │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ プラットフォーム  │
                       │ OneBot12         │    │ API 呼び出し     │
                       │ 標準イベント     │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ 標準レスポンス   │
                       │ イベントシステム │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ モジュール        │
                       │ (イベント処理)   │
                       └──────────────────┘
```

**コアの対称性**：
- **正方向変換**（Converter）：プラットフォームネイティブイベント → OneBot12 標準イベント、元のデータは `{platform}_raw` に保持されます
- **逆方向変換**（Raw_ob12）：OneBot12 メッセージセグメント → プラットフォーム API 呼び出し、標準のレスポンス形式を返します

## AdapterManager アダプター管理マネージャー

`AdapterManager` は、ErisPulse アダプターシステムのコアコンポーネントであり、すべてのプラットフォームアダプターの登録、起動、終了、およびイベントのディスパッチを管理します。

### コア機能

- **アダプター登録**：複数のプラットフォームアダプターを登録および管理します
- **ライフサイクル管理**：アダプターの起動と終了を制御します
- **イベントディスパッチ**：OneBot12 標準イベントとプラットフォームネイティブイベントをディスパッチします
- **設定管理**：アダプターの有効/無効状態を管理します
- **ミドルウェアサポート**：OneBot12 イベントミドルウェアをサポートします

### 基本的な使用方法

```python
from ErisPulse import sdk

# アダプターの登録（通常はLoaderにより自動的に完了します）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# すべてのアダプターを起動
await sdk.adapter.startup()

# 指定したアダプターを起動
await sdk.adapter.startup(["myplatform"])
# すべてのアダプターを起動
await sdk.adapter.startup()

# アダプターインスタンスの取得
my_adapter = sdk.adapter.get("myplatform")
# またはプロパティ経由でアクセス
my_adapter = sdk.adapter.myplatform

# すべてのアダプターを終了
await sdk.adapter.shutdown()
```

### 起動と終了

#### アダプターの起動

```python
# 登録済みのすべてのアダプターを起動
await sdk.adapter.startup()

# 指定したプラットフォームを起動
await sdk.adapter.startup(["platform1", "platform2"])
```

**起動フロー：**

1. `adapter.start` ライフサイクルイベントを送信します
2. `adapter.status.change` イベントを送信します（starting）
3. 各アダプターを並行して起動します
4. 起動失敗時、自動リトライ（指数バックオフ戦略）
5. 起動成功後、`adapter.status.change` イベントを送信します（started）

**リトライメカニズム：**

- 最初の4回のリトライ：60秒、10分、30分、60分
- 5回目以降：3時間の固定間隔

#### アダプターの終了

```python
# すべてのアダプターを終了
await sdk.adapter.shutdown()
```

**終了フロー：**

1. `adapter.stop` ライフサイクルイベントを送信します
2. すべてのアダプターの `shutdown()` メソッドを呼び出します
3. ルーティングサーバーを閉じます
4. イベントプロセッサをクリアします
5. `adapter.stopped` ライフサイクルイベントを送信します

### 設定管理

#### プラットフォーム状態の確認

```python
# プラットフォームが登録されているか確認
exists = sdk.adapter.exists("myplatform")

# プラットフォームが有効か確認
enabled = sdk.adapter.is_enabled("myplatform")

# in 演算子を使用
if "myplatform" in sdk.adapter:
    print("プラットフォームは存在し、有効です")
```

#### プラットフォームの一覧

```python
# 登録済みのすべてのプラットフォームを一覧表示
platforms = sdk.adapter.list_registered()

# すべてのプラットフォームとその状態を一覧表示
status_dict = sdk.adapter.list_items()
# 返り値: {"platform1": true, "platform2": false, ...}

# 有効なプラットフォームのリストを取得
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### イベントリスニング

#### OneBot12 標準イベント

```python
from ErisPulse import sdk

# すべてのプラットフォームの標準メッセージイベントをリッスン
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"OneBot12メッセージを受信: {data}")

# 特定のプラットフォームの標準メッセージイベントをリッスン
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"myplatform メッセージを受信: {data}")

# すべてのイベントをリッスン
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"イベントを受信: {data.get('type')}")
```

#### プラットフォームネイティブイベント

```python
# 特定のプラットフォームのネイティブイベントをリッスン
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"ネイティブイベントを受信: {data}")

# すべてのプラットフォームのネイティブイベントをリッスン（ワイルドカード）
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"ネイティブイベントを受信: {data}")
```

#### イベントディスパッチメカニズム

`adapter.emit(event_data)` を呼び出すと：

1. **ミドルウェア処理**：すべての OneBot12 ミドルウェアを実行します
2. **標準イベントディスパッチ**：一致する OneBot12 イベントハンドラにディスパッチします
3. **ネイティブイベントディスパッチ**：元のデータが存在する場合、ネイティブイベントハンドラにディスパッチします

**一致ルール：**

- 精密一致：`@sdk.adapter.on("message")` は `message` イベントのみに一致します
- ワイルドカード：`@sdk.adapter.on("*")` はすべてのイベントに一致します
- プラットフォームフィルタ：`platform="myplatform"` は指定されたプラットフォームのイベントのみにディスパッチします

### ミドルウェア

#### ミドルウェアの追加

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """ログ記録ミドルウェア"""
    print(f"イベントを処理: {data.get('type')}")
    return data  # 必須でデータを返す

@sdk.adapter.middleware
async def filter_middleware(data):
    """イベントフィルタミドルウェア"""
    # 不要なイベントをフィルタリング
    if data.get("type") == "notice":
        return None  # None を返す場合、ミドルウェアチェーンはその返り値を無視し、元のデータを保持して次の処理に渡します
    return data  # 必須でデータを返して次の処理に渡します
```

#### ミドルウェアの実行順序

ミドルウェアは登録順に実行され、後から登録されたミドルウェアが先に実行されます。

> **注意**：ミドルウェアが `None` を返した場合（例：`return data` を忘れている場合）、フレームワークはその返り値を無視して元のデータを保持し、次の処理に渡します。また、warning レベルのログを出力します。これにより、1つのミドルウェアのミスがイベントチェーン全体を中断することはありません。

```python
# 登録順
sdk.adapter.middleware(middleware1)  # 最後に実行
sdk.adapter.middleware(middleware2)  # 中間に実行
sdk.adapter.middleware(middleware3)  # 最初に実行

# 実行順序：middleware3 -> middleware2 -> middleware1
```

### アダプターインスタンスの取得

#### get() メソッド

```python
adapter = sdk.adapter.get("myplatform")
if adapter:
    await adapter.Send.To("user", "123").Text("Hello")
```

#### プロパティアクセス

```python
# プロパティ名を用いたアクセス（大文字小文字を区別しない）
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## BaseAdapter 基底クラス

### 基本構造

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        # アダプターの初期化
        pass
    
    async def start(self):
        """アダプターの起動（必須実装）"""
        pass
    
    async def shutdown(self):
        """アダプターの終了（必須実装）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォーム API の呼び出し（必須実装）"""
        pass
```

### 初期化プロセス

```python
class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        # SDK の参照を取得
        self.sdk = sdk
        
        # コアモジュールの取得
        self.logger = logger.get_child("MyAdapter")
        self.config_manager = config_manager
        self.adapter = adapter
        
        # 設定のロード
        self.config = self._get_config()
        
        # コンバーターの設定
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## Send 消息送信 DSL

### 継承関係

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        """Send 嵌套类，继承自 BaseAdapter.Send"""
        pass
```

### 利用可能な属性

`Send` クラスは呼び出し時に自動的に以下の属性を設定します：

| 属性 | 説明 | 設定方法 |
|-----|------|---------|
| `_target_id` | 目標ID | `To(id)` または `To(type, id)` |
| `_target_type` | 目標タイプ | `To(type, id)` |
| `_target_to` | 簡略化された目標ID | `To(id)` |
| `_account_id` | 送信アカウントID | `Using(account_id)` |
| `_adapter` | アダプターインスタンス | 自動設定 |
| `_at_user_ids` | @ユーザーIDリスト | `At(user_id)` |
| `_reply_message_id` | 回答するメッセージID | `Reply(message_id)` |
| `_at_all` | 全員に@するか | `AtAll()` |

> **推奨**：`self.send_context` 属性を使って `target_type`、`target_id`、`account_id` を一度に取得する方が、直接インスタンス変数にアクセスするよりも明確です。

### フレームワーク補助メソッド

| メソッド/属性 | 説明 |
|-----------|------|
| `self._apply_modifiers(message)` | At/AtAll/Reply 修飾子の状態をメッセージセグメントリストにマージします |
| `self.send_context` | `{target_type, target_id, account_id}` ディクショナリを返します |

### 基本メソッド

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """推奨される実装方法"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    def Text(self, text: str):
        """テキストメッセージを送信"""
        return self.Raw_ob12([
            {"type": "text", "data": {"text": text}}
        ])
```

### チェーン修飾メソッド

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self
```

## イベントコンバーター

### 変換フロー

```
プラットフォームの元のイベント
    ↓
Converter.convert()
    ↓
OneBot12 標準イベント
```

### 必須フィールド

変換後のイベントは以下のフィールドを含む必要があります：

```python
{
    "id": "イベントの唯一識別子",
    "time": 1234567890,           # 10桁 Unix タイムスタンプ
    "type": "message/notice/request/meta",
    "detail_type": "イベントの詳細タイプ",
    "platform": "プラットフォーム名",
    "self": {
        "platform": "プラットフォーム名",
        "user_id": "ロボットID"
    },
    "{platform}_raw": {...},       # 元のデータ（必須）
    "{platform}_raw_type": "..."    # 元のタイプ（必須）
}
```

### コンバーターの例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """プラットフォームの元のイベントを OneBot12 標準形式に変換"""
        if not isinstance(raw_event, dict):
            return None
        
        # イベントIDの生成
        event_id = raw_event.get("event_id") or str(uuid.uuid4())
        
        # タイムスタンプの変換
        timestamp = raw_event.get("timestamp")
        if timestamp and timestamp > 10**12:
            timestamp = int(timestamp / 1000)
        else:
            timestamp = int(timestamp) if timestamp else int(time.time())
        
        # イベントタイプの変換
        event_type = self._convert_type(raw_event.get("type"))
        detail_type = self._convert_detail_type(raw_event)
        
        # 標準イベントの構築
        onebot_event = {
            "id": str(event_id),
            "time": timestamp,
            "type": event_type,
            "detail_type": detail_type,
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": raw_event.get("type", "")
        }
        
        return onebot_event
```

## 接続管理

### WebSocket 接続

```python
from fastapi import WebSocket

class MyAdapter(BaseAdapter):
    async def start(self):
        """WebSocket ルートの登録"""
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler,
            auth_handler=self._auth_handler
        )
    
    async def _ws_handler(self, websocket: WebSocket):
        """WebSocket 接続ハンドラ"""
        self.connection = websocket
        
        try:
            while True:
                data = await websocket.receive_text()
                onebot_event = self.convert(data)
                if onebot_event:
                    await self.adapter.emit(onebot_event)
        except WebSocketDisconnect:
            self.logger.info("接続が切断されました")
        finally:
            self.connection = None
    
    async def _auth_handler(self, websocket: WebSocket) -> bool:
        """WebSocket 認証"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook 接続

```python
from fastapi import Request

class MyAdapter(BaseAdapter):
    async def start(self):
        """WebHook ルートの登録"""
        router.register_http_route(
            module_name="myplatform",
            path="/webhook",
            handler=self._webhook_handler,
            methods=["POST"]
        )
    
    async def _webhook_handler(self, request: Request):
        """WebHook リクエストハンドラ"""
        data = await request.json()
        onebot_event = self.convert(data)
        if onebot_event:
            await self.adapter.emit(onebot_event)
        return {"status": "ok"}
```

## API 応答標準

### 成功応答

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        return {
            "status": "ok",
            "retcode": 0,
            "data": raw_response.get("data"),
            "message_id": raw_response.get("data", {}).get("message_id", ""),
            "message": "",
            "myplatform_raw": raw_response
        }
    except Exception as e:
        return {
            "status": "failed",
            "retcode": 34000,
            "data": None,
            "message_id": "",
            "message": str(e),
            "myplatform_raw": None
        }
```

### 失敗応答

```python
async def call_api(self, endpoint: str, **params):
    # ...
    return {
        "status": "failed",
        "retcode": 10003,  # エラーコード
        "data": None,
        "message_id": "",
        "message": "必要なパラメータが不足しています",
        "myplatform_raw": None
    }
```

## 多アカウントサポート

### アカウント設定

```toml
[MyAdapter.accounts.account1]
token = "token1"
enabled = true

[MyAdapter.accounts.account2]
token = "token2"
enabled = true
```

### アカウント指定による送信

```python
# Using メソッドでアカウントを指定
my_adapter = adapter.get("myplatform")

# アカウント名で
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")

# アカウントIDで
await my_adapter.Send.Using("account_id").To("user", "123").Text("Hello")
```

## エラーハンドリング

### 接続リトライ

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                await self._connect_to_platform()
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(f"接続失敗、{wait_time}秒後に再試行します")
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### API エラーハンドリング

```python
async def call_api(self, endpoint: str, **params):
    try:
        # SDK 内部クライアントの推奨
        from ErisPulse.Core import client
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            max_retries=2,
        )
        response = await resp.json()
        return self._standardize_response(response)
    except aiohttp.ClientError as e:
        self.logger.error(f"ネットワークエラー: {e}")
        return self._error_response("ネットワークリクエストに失敗しました", 33000)
    except asyncio.TimeoutError:
        self.logger.error(f"リクエストタイムアウト: {endpoint}")
        return self._error_response("リクエストがタイムアウトしました", 32000)
    except Exception as e:
        self.logger.error(f"不明なエラー: {e}")
        return self._error_response(str(e), 34000)
```

## Bot 状態管理

AdapterManager には、すべての登録済み Bot のオンライン状態、アクティブ時間、メタ情報を自動的に維持する Bot 状態追跡システムが内蔵されています。

### 自動発見メカニズム

アダプターが `adapter.emit()` を呼び出すと、フレームワークはイベント内の `self` フィールドを自動的にチェックします：

- **meta イベント**：`detail_type` に応じて対応する操作（connect で Bot を登録/disconnect でオフラインをマーク/heartbeat でアクティブ時間を更新）
- **通常イベント**（message/notice/request）：Bot を自動的に発見し、アクティブ時間を更新

```python
# self フィールドを含むすべてのイベントが自動発見をトリガーします
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123" が自動的に登録されます（初めて出現する場合）し、アクティブ時間を更新します
```

### Meta イベントタイプ

| `detail_type` | 説明 | フレームワークの動作 |
|---|---|---|
| `connect` | Bot が接続 | Bot を登録し、`adapter.bot.online` ライフサイクルイベントを発行します |
| `disconnect` | Bot が切断 | Bot をオフラインにマークし、`adapter.bot.offline` ライフサイクルイベントを発行します |
| `heartbeat` | Bot のハートビート | Bot のアクティブ時間とメタ情報を更新します |

### アダプターによる Meta イベント送信

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        await self.adapter.emit({
            "type": "meta",
            "detail_type": "connect",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": bot_id,
                "user_name": "MyBot",
                "nickname": "私のロボット",
            }
        })

    async def _on_bot_disconnect(self, bot_id: str):
        await self.adapter.emit({
            "type": "meta",
            "detail_type": "disconnect",
            "platform": "myplatform",
            "self": {"platform": "myplatform", "user_id": bot_id}
        })
```

### `self` フィールドの拡張情報

`self` フィールドには、必須の `platform` と `user_id` の他に、以下のオプションフィールドをサポートします：

| フィールド | 説明 |
|---|---|
| `user_name` | Bot のユーザー名 |
| `nickname` | Bot のニックネーム |
| `avatar` | Bot のアバター URL |
| `account_id` | 多アカウント識別子 |

### Bot 状態の照会

```python
from ErisPulse import sdk

# 単一の Bot 情報を取得
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# すべての Bot を取得
all_bots = sdk.adapter.list_bots()

# 指定プラットフォームの Bot を取得
platform_bots = sdk.adapter.list_bots("myplatform")

# Bot がオンラインかを確認
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# 完全なステータスサマリーを取得（WebUI に表示するのに適しています）
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

### Bot ライフサイクルの監視

```python
from ErisPulse import sdk

@sdk.lifecycle.on("adapter.bot.online")
async def on_bot_online(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Bot がオンラインになりました: {platform}/{bot_id}")

@sdk.lifecycle.on("adapter.bot.offline")
async def on_bot_offline(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Bot がオフラインになりました: {platform}/{bot_id}")
```

## 関連文書

- [アダプター開発入門](getting-started.md) - 最初のアダプターを作成する
- [SendDSL 詳解](send-dsl.md) - メッセージ送信を学ぶ
- [アダプター開発ベストプラクティス](best-practices.md) - 高品質なアダプターを開発する

翻訳は以上です。