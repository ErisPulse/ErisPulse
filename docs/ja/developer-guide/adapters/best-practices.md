# アダプタ開発のベストプラクティス

このドキュメントは、ErisPulse アダプタ開発におけるベストプラクティスを提供します。

## Bot 状態管理と Meta イベント

アダプタは、`adapter.emit()` を通じて Meta イベントを送信し、フレームワークが Bot の接続状態、ログイン/ログアウト、およびハートビート情報を自動的に追跡できるようにする必要があります。

### 1. 何时发送 Meta 事件

| イベント | `detail_type` | 発生タイミング | フレームワークの動作 |
|------|--------------|---------|---------|
| 接続 | `"connect"` | Bot がプラットフォームと接続したとき | Bot を登録し、`adapter.bot.online` のライフサイクルイベントをトリガー |
| 切断 | `"disconnect"` | Bot がプラットフォームと切断したとき | Bot をオフラインにマークし、`adapter.bot.offline` のライフサイクルイベントをトリガー |
| ハートビート | `"heartbeat"` | 定期的に送信（30-60秒が推奨） | Bot のアクティブタイムとメタ情報を更新 |

### 2. 发送 Meta 事件

フレームワークは `emit_meta()` メソッドを提供しており、一行で Meta イベントを送信できます：

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Bot 上線：一行で connect イベントを送信
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="私のロボット")

        try:
            while True:
                data = await websocket.receive_text()
                event = self.convert(data)
                if event:
                    await self.adapter.emit(event)
        except WebSocketDisconnect:
            pass
        finally:
            # Bot 下線
            await self.emit_meta("disconnect", bot_id)
```

### 3. 心跳イベント

アダプタは接続が維持されている間、定期的にハートビートイベントを送信し、Bot のアクティブタイムを更新する必要があります：

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            # フレームワークに meta heartbeat を送信（一行で完了）
            await self.emit_meta("heartbeat", bot_id)
            await asyncio.sleep(30)
```

### 4. `self` フィールドの自動発見

フレームワークの `adapter.emit()` は、すべてのイベント（Meta イベントに限らず）の `self` フィールドを自動的に処理します：

- **通常のイベント**（message/notice/request）の `self` フィールドは自動的に Bot を登録します
- **`self` フィールドの拡張情報**：`user_name`、`nickname`、`avatar`、`account_id` などのオプションフィールドがサポートされます

```python
# 転換器に self フィールドを含めれば、Bot は自動的に登録され、アクティブタイムが更新されます
onebot_event = {
    "type": "message",
    "detail_type": "private",
    "platform": "myplatform",
    "self": {
        "platform": "myplatform",
        "user_id": "bot123",
        "user_name": "MyBot",
        "nickname": "私のロボット",
    },
    # ... その他のフィールド
}
await self.adapter.emit(onebot_event)
# Bot "bot123" は自動的に登録され、アクティブタイムが更新されます
```

### 5. Bot 状態の照会

フレームワークは以下の照会メソッドを提供しています：

```python
from ErisPulse import sdk

# Bot の詳細情報を取得
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# すべての Bot をリストアップ（プラットフォーム別にグループ化）
all_bots = sdk.adapter.list_bots()

# 指定のプラットフォームの Bot をリストアップ
platform_bots = sdk.adapter.list_bots("myplatform")

# Bot がオンラインかどうかを確認
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# 完全なステータスサマリーを取得（WebUI に表示するのに適しています）
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

## 接続管理

### 1. 接続の再試行実装

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
                        f"接続失敗、{wait_time}秒後に再試行 ({retry_count}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("接続失敗、最大再試行回数に達しました")
                    raise
```

### 2. 接続状態管理

```python
class MyAdapter(BaseAdapter):
    async def start(self):
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

### 3. ハートビート保活と Meta ハートビート

アダプタのハートビートは、プラットフォームへのハートビート保活と、フレームワークへの meta heartbeat イベント送信の両方を完了する必要があります。

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = await self._connect_to_platform()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        while self.connection:
            try:
                # 1. プラットフォームにハートビート保活を送信
                await self.connection.send_json({"type": "ping"})

                # 2. フレームワークに meta heartbeat を送信（emit_meta で一行で完了）
                await self.emit_meta("heartbeat", self._bot_id)

                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"ハートビート失敗: {e}")
                break
```

### 4. 接続情報の公開

アダプタが登録するルートは、ユーザーがプラットフォーム側のコールバックアドレスを設定できるように、ユーザーに見えるようにする必要があります。`start()` で接続情報を明示的に出力することを推奨します：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        router.register_websocket(
            module_name=self.platform,
            path="/ws",
            handler=self._ws_handler
        )

        if self.sdk:
            info = self.sdk.adapter.get_connection_info(self.platform)
            if info:
                self.logger.info(f"WebSocket アドレス: "
                    f"{info.get('connection', {}).get('base_url', '')}"
                    f"{info.get('connection', {}).get('websocket_routes', [])}")
```

ユーザーは以下の API を使って、アダプタのすべてのルートと接続アドレスを照会できます：

```python
from ErisPulse import sdk

# アダプタレベルの接続情報（推奨）
info = sdk.adapter.get_connection_info("myplatform")

# ルートマネージャレベルの照会
sdk.router.list_namespaces()              # すべての名前空間をリストアップ
sdk.router.get_module_routes("myplatform")  # 詳細なルート情報
sdk.router.get_module_urls("myplatform")    # 完全な接続 URL
```

> **注意**: ルート登録時の `module_name` は、ErisPulse で登録するアダプタの `platform` 名と完全に一致している必要があります。そうでない場合、`get_connection_info()` はルートと関連付けられません。複数アカウントアダプタは、異なる `module_name` を使用するのではなく、サブパス（例: `/account1/webhook`、`/account2/webhook`）を各アカウントに登録する必要があります。

## イベント変換

### 1. OneBot12 標準の厳密遵守

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
            "myplatform_raw": raw_event,  # 保持原始数据（必须）
            "myplatform_raw_type": raw_event.get("type", "")  # 原始类型（必须）
        }
        return onebot_event
```

### 2. 時間スタンプの標準化

```python
def _convert_timestamp(self, timestamp):
    """10桁の秒単位時間スタンプに変換"""
    if not timestamp:
        return int(time.time())
    
    # ミリ秒単位の時間スタンプの場合
    if timestamp > 10**12:
        return int(timestamp / 1000)
    
    # 秒単位の時間スタンプの場合
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

## SendDSL 実装

`At`/`AtAll`/`Reply` 修飾子はフレームワークの SendDSL 基底クラスに既に実装されています。アダプタは `Raw_ob12` と具体的な送信メソッドを実装するだけで、`self._apply_modifiers(message)` と `self.send_context` を使用して開発を簡素化できます。

### 1. Task オブジェクトを返す必要がある

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """推奨実装：フレームワークの補助メソッドを使用"""
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

### 2. 鏈式修飾メソッドは self を返す

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self # self を返す
```

### 3. プラットフォーム固有のメソッドをサポート

```python
class Send(BaseAdapter.Send):
    def Sticker(self, sticker_id: str):
        """ステッカーを送信"""
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
                message=[{"type": "card", "data": {"card_data": card_data}}],
                **self.send_context
            )
        )
```

## API レスポンス

### 1. レスポンスの標準化

フレームワークは `make_response()` と `make_error()` メソッドを提供し、標準化されたレスポンスを構築できます：

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        if raw_response.get("success"):
            return self.make_response(
                data=raw_response.get("data"),
                message_id=raw_response.get("data", {}).get("message_id", ""),
                raw=raw_response,
            )
        else:
            return self.make_error(
                retcode=raw_response.get("code", 10001),
                message=raw_response.get("message", ""),
                raw=raw_response,
            )
    except Exception as e:
        return self.make_error(message=str(e))
```

`make_response()` は `{platform}_raw` キーを含むレスポンス辞書を自動的に生成します。`make_error()` はデフォルトで `retcode=34000`（Platform Error）を使用します。

### 2. エラーコード規格

OneBot12 標準エラーコードに従います：

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

## 多アカウントサポート

### 1. 宣言的構成（推奨）

`AccountConfigClass` を宣言して構成クラスを定義した後、フレームワークが多アカウントの読み込み、検証、テンプレート生成を自動的に管理します。`BotAccountConfig` 基底クラスは `enabled` と `name` フィールドを提供しており、アダプタは宣言する必要はありません：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Bot Token"},
        "required": True,
        "secret": True,
    })

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            self.logger.info(f"アカウント {name} を起動中")
            await self._connect(name, account.token)
            # bot_id はフレームワークがプラットフォームプロトコル/ログイン応答から自動的に取得して戻し埋めします
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # name: アカウント名, account: MyBotConfig インスタンス
```

構成ファイルは自動的に生成されます：

```toml
[MyAdapter.accounts.default]
token = ""
enabled = true
name = ""
```

### 2. アカウント選択メカニズム

フレームワークは `_resolve_account()` メソッドを内蔵しており、以下の優先順位でマッチします：

1. **アカウント名** — 構成のキー名と正確に一致
2. **`bot_id` フィールド** — 自動的に取得された bot_id（イベントの `event["self"]["user_id"]` から）
3. **任意の str フィールド** — 構成の他の文字列フィールド
4. **デフォルト** — 最初に有効なアカウント

```python
# アカウント名でマッチ
name, account = self._resolve_account("account1")

# bot_id でマッチ（イベントからの最も一般的な方法）
name, account = self._resolve_account("bot_123")

# 最初に有効なアカウントを取得（None を渡す）
name, account = self._resolve_account(None)
```

## エラーハンドリング

### 1. エラータイプの分類

`make_error()` を使用して標準化されたエラーレスポンスを構築します。`sdk.client` でリクエストする際は ErisPulse のエラーをキャッチします：

```python
from ErisPulse.Core.Bases.errors import ClientError, ClientTimeoutError

async def call_api(self, endpoint: str, **params):
    try:
        from ErisPulse.Core import client
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            max_retries=2,
        )
        response = await resp.json()
        return self.make_response(data=response, raw=response)
    except ClientTimeoutError:
        self.logger.error(f"リクエストタイムアウト: {endpoint}")
        return self.make_error(retcode=32000, message="リクエストタイムアウト")
    except ClientError as e:
        self.logger.error(f"ネットワークエラー: {e}")
        return self.make_error(retcode=33000, message="ネットワークリクエスト失敗")
    except json.JSONDecodeError:
        self.logger.error("JSON 解析失敗")
        return self.make_error(retcode=10006, message="レスポンス形式エラー")
    except Exception as e:
        self.logger.error(f"未知のエラー: {e}", exc_info=True)
        return self.make_error(message=str(e))
```

> **後方互換性**: `aiohttp` を直接使用する古いアダプタコードは影響を受けません。`sdk.client` を通じてリクエストする場合にのみ、エラーの変換が有効になります。

### 2. ログ記録

フレームワークはアダプタにサブロガー（`sdk.logger.get_child("MyAdapter")`）を自動的に作成します。手動の初期化は不要です：

```python
class MyAdapter(BaseAdapter):
    # ConfigClass = ...  # 構成クラスを宣言した後、self.logger が自動的に利用可能になります
    
    async def start(self):
        self.logger.info("アダプタ起動中...")
        # ...
        self.logger.info("アダプタ起動完了")
    
    async def shutdown(self):
        self.logger.info("アダプタ終了中...")
        # ...
        self.logger.info("アダプタ終了完了")
```

## テスト

### 1. 単体テスト

```python
import pytest
from ErisPulse.Core.Bases import BaseAdapter

class TestMyAdapter:
    def test_converter(self):
        """テスト転換器"""
        converter = MyPlatformConverter()
        raw_event = {"type": "message", "content": "Hello"}
        result = converter.convert(raw_event)
        assert result is not None
        assert result["platform"] == "myplatform"
        assert "myplatform_raw" in result
    
    def test_api_response(self):
        """テスト API レスポンス形式"""
        adapter = MyAdapter()
        response = adapter.call_api("/test", param="value")
        assert "status" in response
        assert "retcode" in response
```

### 2. 統合テスト

```python
@pytest.mark.asyncio
async def test_adapter_start():
    """テストアダプタ起動"""
    adapter = MyAdapter()
    await adapter.start()
    assert adapter._connected is True

@pytest.mark.asyncio
async def test_send_message():
    """テストメッセージ送信"""
    adapter = MyAdapter()
    await adapter.start()
    
    result = await adapter.Send.To("user", "123").Text("Hello")
    assert result is not None
```

## リバースコンバージョンとメッセージ構築

`Raw_ob12` はアダプタが**実装しなければならない**メソッドで、OneBot12 → プラットフォームのリバースコンバージョンの統一エントリーポイントです。標準メソッド（`Text`、`Image` など）は `Raw_ob12` に委譲し、修飾子の状態（`At`/`Reply`/`AtAll`）は `Raw_ob12` 内でメッセージセグメントにマージされる必要があります。

`MessageBuilder` は `Raw_ob12` と一緒に使用するメッセージセグメント構築ツールで、チェーン呼び出しと迅速な構築をサポートします。

> 完全な実装規格、コード例、使用方法については、以下のドキュメントを参照してください：
> - [送信メソッド規格 §6 リバースコンバージョン規格](../../standards/send-method-spec.md#6-リバースコンバージョン規格onebot12--プラットフォーム)
> - [送信メソッド規格 §11 メッセージビルダー](../../standards/send-method-spec.md#11-メッセージビルダー-messagebuilder)

## プラットフォームイベントメソッド拡張

アダプタは Event 包装クラスにプラットフォーム固有のメソッドを登録し、モジュール開発者がプラットフォーム特有のデータに簡単にアクセスできるようにすることができます。

### 1. Mixin クラスを使用した一括登録（推奨）

プラットフォームに複数の固有メソッドがある場合、Mixin クラスの使用が推奨されます：

```python
# アダプタの start() またはモジュールレベルで登録
from ErisPulse.Core.Event import register_event_mixin

class MyPlatformEventMixin:
    def get_chat_name(self):
        """チャット名を取得"""
        return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

    def is_official_message(self):
        """公式メッセージかどうかを判断"""
        raw = self.get("myplatform_raw", {})
        return raw.get("sender", {}).get("is_official", False)

    def get_message_type(self):
        """プラットフォームのメッセージタイプを取得"""
        return self.get("myplatform_raw", {}).get("msg_type", "text")

# 一括登録
register_event_mixin("myplatform", MyPlatformEventMixin)
```

### 2. デコレーターを使用した個別メソッド登録

```python
from ErisPulse.Core.Event import register_event_method

@register_event_method("myplatform")
def get_chat_name(self):
    return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")
```

### 3. アダプタ終了時のクリーンアップ

```python
from ErisPulse.Core.Event import unregister_platform_event_methods

class MyAdapter(BaseAdapter):
    async def shutdown(self):
        # プラットフォームイベントメソッドの登録をクリーンアップ
        unregister_platform_event_methods("myplatform")
        # ... その他のクリーンアップ
```

> 詳細な登録とアンロードの説明は、[イベントシステム API - プラットフォーム拡張メソッドの登録](../../api-reference/event-system.md#アダプタ登録プラットフォーム拡張メソッド)を参照してください。

## ドキュメントの維持

### 1. プラットフォーム機能ドキュメントの維持

`docs/ja/platform-guide/` に `{platform}.md` ドキュメントを作成します（他の言語バージョンは自動生成されます）：

```markdown
# プラットフォーム名アダプタドキュメント

## 基本情報
- 対応モジュールバージョン: 1.0.0
- 維持者: あなたの名前

## 支援されるメッセージ送信タイプ
...

## 特有のイベントタイプ
...

## 構成オプション
...
```

### 2. バージョン情報の更新

新バージョンをリリースする際、ドキュメント内のバージョン情報を更新します：

```toml
[project]
version = "2.0.0"  # バージョン番号を更新
```

## 関連ドキュメント

- [アダプタ開発入門](getting-started.md) - 最初のアダプタを作成する
- [アダプタのコアコンセプト](core-concepts.md) - アダプタアーキテクチャを理解する
- [SendDSL 詳解](send-dsl.md) - メッセージ送信を学ぶ