# アダプター開発のベストプラクティス

本ドキュメントでは、ErisPulse アダプター開発のベストプラクティスを提供します。

## Botの状態管理とMetaイベント

アダプターは、`adapter.emit()` を通じて積極的に meta イベントを送信し、フレームワークに Bot の接続状態、オンライン/オフライン、ハートビート情報を自動追跡させる必要があります。

### 1. Metaイベントを送信するタイミング

| イベント | `detail_type` | 発生タイミング | フレームワークの動作 |
|------|--------------|---------|---------|
| 接続 | `"connect"` | Bot がプラットフォームとの接続を確立した時 | Bot を登録し、`adapter.bot.online` ライフサイクルイベントをトリガーする |
| 切断 | `"disconnect"` | Bot がプラットフォームから切断された時 | Bot をオフラインとしてマークし、`adapter.bot.offline` ライフサイクルイベントをトリガーする |
| ハートビート | `"heartbeat"` | 定期的に送信（30〜60秒を推奨） | Bot のアクティブ時間とメタ情報を更新する |

### 2. Metaイベントの送信

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Botオンライン：connect イベントを送信
        await self.adapter.emit({
            "type": "meta",
            "detail_type": "connect",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": bot_id,
                "user_name": "MyBot",
                "nickname": "私のBot",
                "avatar": "https://example.com/avatar.png",
            }
        })

        try:
            while True:
                data = await websocket.receive_text()
                event = self.convert(data)
                if event:
                    await self.adapter.emit(event)
        except WebSocketDisconnect:
            pass
        finally:
            # Botオフライン：disconnect イベントを送信
            await self.adapter.emit({
                "type": "meta",
                "detail_type": "disconnect",
                "platform": "myplatform",
                "self": {
                    "platform": "myplatform",
                    "user_id": bot_id,
                }
            })
```

### 3. ハートビートイベント

アダプターは、接続が生きている間、定期的にハートビートイベントを送信し、Bot のアクティブ時間を更新する必要があります：

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            await self.adapter.emit({
                "type": "meta",
                "detail_type": "heartbeat",
                "platform": "myplatform",
                "self": {
                    "platform": "myplatform",
                    "user_id": bot_id,
                }
            })
            await asyncio.sleep(30)
```

### 4. `self` フィールドの自動検出

フレームワークの `adapter.emit()` は、すべてのイベント（meta イベントだけでなく）の `self` フィールドを自動的に処理します：

- **通常のイベント**（message/notice/request）の `self` フィールドは、Bot を自動的に検出して登録します
- **`self` フィールドの拡張情報**：`user_name`、`nickname`、`avatar`、`account_id` オプションフィールドをサポートします

```python
# コンバーターに self フィールドを含めるだけで Bot が自動登録されます
onebot_event = {
    "type": "message",
    "detail_type": "private",
    "platform": "myplatform",
    "self": {
        "platform": "myplatform",
        "user_id": "bot123",
        "user_name": "MyBot",
        "nickname": "私のBot",
    },
    # ... その他のフィールド
}
await self.adapter.emit(onebot_event)
# Bot "bot123" が自動登録され、アクティブ時間が更新されました
```

### 5. Botの状態照会

フレームワークは以下の照会メソッドを提供します：

```python
from ErisPulse import sdk

# Bot の詳細情報を取得
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# すべての Bot をリストアップ（プラットフォーム別）
all_bots = sdk.adapter.list_bots()

# 指定したプラットフォームの Bot をリストアップ
platform_bots = sdk.adapter.list_bots("myplatform")

# Bot がオンラインかどうかを確認
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# 完全なステータスサマリーを取得（WebUIでの表示に適しています）
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

## 接続管理

### 1. 再接続の実装

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                await self._connect_to_platform()
                self.logger.info("接続成功")
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    # 指数バックオフ戦略
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(
                        f"接続失敗、{wait_time}秒後に再試行します ({retry_count}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("接続失敗、最大再試行回数に達しました")
                    raise
```

### 2. 接続状態管理

```python
class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.connection = None
        self._connected = False
    
    async def _ws_handler(self, websocket: WebSocket):
        self.connection = websocket
        self._connected = True
        self.logger.info("接続が確立されました")
        
        try:
            while True:
                data = await websocket.receive_text()
                await self._process_event(data)
        except WebSocketDisconnect:
            self.logger.info("接続が切断されました")
        finally:
            self.connection = None
            self._connected = False
```

### 3. ハートビートキープアライブと Meta ハートビート

アダプターのハートビートは、プラットフォームへのキープアライブ送信と、フレームワークへの meta heartbeat イベント送信の2つのタスクを同時に実行する必要があります。

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = await self._connect_to_platform()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        while self.connection:
            try:
                # 1. プラットフォームにハートビートを送信してキープアライブ
                await self.connection.send_json({"type": "ping"})

                # 2. フレームワークに meta heartbeat イベントを送信（Bot のアクティブ時間を更新）
                await self.adapter.emit({
                    "type": "meta",
                    "detail_type": "heartbeat",
                    "platform": "myplatform",
                    "self": {
                        "platform": "myplatform",
                        "user_id": self._bot_id,
                    }
                })

                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"ハートビート失敗: {e}")
                break
```

## イベント変換

### 1. OneBot12 標準の厳格な遵守

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """イベントを変換"""
        onebot_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": int(time.time()),
            "type": self._convert_type(raw_event.get("type")),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,  # 元のデータを保持（必須）
            "myplatform_raw_type": raw_event.get("type", "")  # 元のタイプ（必須）
        }
        return onebot_event
```

### 2. タイムスタンプの標準化

```python
def _convert_timestamp(self, timestamp):
    """10桁の秒単位タイムスタンプに変換"""
    if not timestamp:
        return int(time.time())
    
    # ミリ秒単位のタイムスタンプの場合
    if timestamp > 10**12:
        return int(timestamp / 1000)
    
    # 秒単位のタイムスタンプの場合
    return int(timestamp)
```

### 3. イベント ID の生成

```python
import uuid

def _generate_event_id(self, raw_event):
    """イベント ID を生成"""
    event_id = raw_event.get("event_id")
    if event_id:
        return str(event_id)
    # プラットフォームが ID を提供していない場合、UUID を生成
    return str(uuid.uuid4())
```

## SendDSL の実装

`At`/`AtAll`/`Reply` 修飾子はフレームワークの SendDSL 基底クラスに組み込まれているため、アダプターは `Raw_ob12` と具体的な送信メソッドを実装するだけで済みます。`self._apply_modifiers(message)` と `self.send_context` を使用して開発を簡素化します。

### 1. Task オブジェクトを返さなければならない

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """推奨される実装：フレームワークのヘルパーメソッドを使用"""
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
        return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### 2. チェーン修飾メソッドは self を返す

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self # self を返す
```

### 3. プラットフォーム固有のメソッドのサポート

```python
class Send(BaseAdapter.Send):
    def Sticker(self, sticker_id: str):
        """スタンプを送信"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_sticker",
                message=[{"type": "sticker", "data": {"id": sticker_id}}],
                **self.send_context
            )
        )
    
    def Card(self, card_data: dict):
        """カードメッセージを送信"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_card",
                message=[{"type": "card", "data": card_data}],
                **self.send_context
            )
        )
```

## API レスポンス

### 1. レスポンス形式の標準化

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        return {
            "status": "ok" if raw_response.get("success") else "failed",
            "retcode": 0 if raw_response.get("success") else raw_response.get("code", 10001),
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

### 2. エラーコード規約

OneBot12 標準のエラーコードに従います：

```python
# 1xxxx - アクションリクエストエラー
10001: Bad Request
10002: Unsupported Action
10003: Bad Param

# 2xxxx - アクションハンドラエラー
20001: Bad Handler
20002: Internal Handler Error

# 3xxxx - アクション実行エラー
31000: Database Error
32000: Filesystem Error
33000: Network Error
34000: Platform Error
35000: Logic Error
```

## マルチアカウントサポート

### 1. アカウント設定の検証

```python
def _get_config(self):
    """設定を検証"""
    config = self.config_manager.getConfig("MyAdapter", {})
    accounts = config.get("accounts", {})
    
    if not accounts:
        # デフォルトアカウントを作成
        default_account = {
            "token": "",
            "enabled": False
        }
        config["accounts"] = {"default": default_account}
        self.config_manager.setConfig("MyAdapter", config)
    
    return config
```

### 2. アカウント選択メカニズム

```python
async def _get_account_for_message(self, event):
    """イベントに基づいて送信アカウントを選択"""
    bot_id = event.get("self", {}).get("user_id")
    
    # 一致するアカウントを検索
    for account_name, account_config in self.accounts.items():
        if account_config.get("bot_id") == bot_id:
            return account_name
    
    # 見つからない場合、最初に有効なアカウントを使用
    for account_name, account_config in self.accounts.items():
        if account_config.get("enabled", True):
            return account_name
    
    return None
```

## エラーハンドリング

### 1. 分類別の例外処理

```python
async def call_api(self, endpoint: str, **params):
    try:
        # API リクエストを送信するために SDK 組み込みのクライアントを使用することを推奨します
        from ErisPulse.Core import client
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            max_retries=2,
        )
        response = await resp.json()
        return self._standardize_response(response)
    except aiohttp.ClientError as e:
        # ネットワークエラー（client 使用時、組み込みの再試行メカニズムが先に処理します）
        self.logger.error(f"ネットワークエラー: {e}")
        return self._error_response("ネットワークリクエスト失敗", 33000)
    except asyncio.TimeoutError:
        # タイムアウトエラー
        self.logger.error(f"リクエストタイムアウト: {endpoint}")
        return self._error_response("リクエストタイムアウト", 32000)
    except json.JSONDecodeError:
        # JSON 解析エラー
        self.logger.error("JSON 解析失敗")
        return self._error_response("レスポンス形式エラー", 10006)
    except Exception as e:
        # 不明なエラー
        self.logger.error(f"不明なエラー: {e}", exc_info=True)
        return self._error_response(str(e), 34000)
```

### 2. ログ記録

```python
class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.logger = logger.get_child("MyAdapter")
    
    async def start(self):
        self.logger.info("アダプターを起動中...")
        # ...
        self.logger.info("アダプターの起動が完了しました")
    
    async def shutdown(self):
        self.logger.info("アダ