# アダプター開発ベストプラクティス

本文書では、ErisPulse アダプター開発のベストプラクティスを提供します。

## Bot の状態管理と Meta イベント

アダプターは、`adapter.emit()` を通じて積極的に meta イベントを送信し、フレームワークに Bot の接続状態、オンライン/オフライン、ハートビート情報を自動追跡させる必要があります。

### 1. Meta イベントを送信するタイミング

| イベント | `detail_type` | 発生タイミング | フレームワークの動作 |
|------|--------------|---------|---------|
| 接続 | `"connect"` | Bot がプラットフォームとの接続を確立した時 | Bot を登録し、`adapter.bot.online` ライフサイクルイベントをトリガーする |
| 切断 | `"disconnect"` | Bot がプラットフォームから切断された時 | Bot をオフラインとしてマークし、`adapter.bot.offline` ライフサイクルイベントをトリガーする |
| ハートビート | `"heartbeat"` | 定期的に送信（推奨 30〜60 秒） | Bot のアクティブ時間とメタ情報を更新する |

### 2. Meta イベントを送信する

フレームワークは `emit_meta()` メソッドを提供しており、1 行で meta イベントを送信できます。

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Botオンライン：1 行で connect イベントを送信
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="私のBot")

        try:
            while True:
                data = await websocket.receive_text()
                event = self.convert(data)
                if event:
                    await self.adapter.emit(event)
        except WebSocketDisconnect:
            pass
        finally:
            # Botオフライン
            await self.emit_meta("disconnect", bot_id)
```

### 3. ハートビートイベント

アダプターは、接続が生きている間、定期的にハートビートイベントを送信し、Bot のアクティブ時間を更新する必要があります。

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            # フレームワークに meta heartbeat を送信（1 行で完了）
            await self.emit_meta("heartbeat", bot_id)
            await asyncio.sleep(30)
```

### 4. `self` フィールドの自動検出

フレームワークの `adapter.emit()` は、すべてのイベント（meta イベントだけでなく）の `self` フィールドを自動的に処理します。

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

### 5. Bot の状態照会

フレームワークは以下の照会メソッドを提供します。

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
                await self.emit_meta("heartbeat", self._bot_id)

                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"ハートビート失敗: {e}")
                break
```

### 4. 接続情報の公開

アダプターが登録したルートはユーザーに可視すべきであり、ユーザーがプラットフォーム側のコールバックアドレスを設定するのに役立ちます。`start()` で接続情報を主に出力することを推奨します。

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

ユーザーは以下の API を通じてアダプターのすべてのルートと接続アドレスを確認できます。

```python
from ErisPulse import sdk

# アダプターレベルの接続情報（推奨）
info = sdk.adapter.get_connection_info("myplatform")

# ルートマネージャーレベルの照会
sdk.router.list_namespaces()              # すべてのネームスペースを一覧表示
sdk.router.get_module_routes("myplatform")  # 詳細なルート情報
sdk.router.get_module_urls("myplatform")    # 完全な接続 URL
```

> **注意**：ルートを登録する際の `module_name` は、ErisPulse で登録されたアダプターの `platform` 名と完全に一致している必要があります。それ以外の場合、`get_connection_info()` はルートを関連付けられません。マルチアカウントアダプターは、各アカウントに対してサブパス（例: `/account1/webhook`、`/account2/webhook`）を登録する必要があります。`module_name` を使い分けることはできません。

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
            "myplatform_raw": raw_event,  # 原始データを保持（必須）
            "myplatform_raw_type": raw_event.get("type", "")  # 原始タイプ（必須）
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

フレームワークは `make_response()` と `make_error()` メソッドを使用して標準化されたレスポンスを構築します。

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

`make_response()` は、`{platform}_raw` キーを含むレスポンス辞書を自動的に生成します。`make_error()` はデフォルトで `retcode=34000`（Platform Error）を使用します。

### 2. エラーコード規約

OneBot12 標準のエラーコードに従います。

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

### 1. 声明式設定（推奨）

`AccountConfigClass` を使用して設定クラスを宣言すると、フレームワークは自動的にマルチアカウントの読み込み、検証、およびテンプレート生成を管理します。

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BotAccountConfig

@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": "Bot Token",
        "required": True,
        "secret": True,
    })

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            self.logger.info(f"启动账户 {name}")
            await self._connect(name, account.token)
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # name: アカウント名, account: MyBotConfig インスタンス
```

設定ファイルは自動的に次のように生成されます。

```toml
[MyAdapter.accounts.default]
token = ""
enabled = true
name = ""
```

### 2. アカウント選択メカニズム

フレームワークは `_resolve_account()` メソッドを内蔵しており、複数のマッチング戦略をサポートしています。

```python
# アカウント名で一致
name, account = self._resolve_account("account1")

# bot_id フィールドで一致（設定に bot_id フィールドがある場合）
name, account = self._resolve_account("bot_123")

# 最初に有効なアカウントを取得（None を渡す）
name, account = self._resolve_account(None)
```

## エラーハンドリング

### 1. 分類別の例外処理

`make_error()` を使用して標準化されたエラーレスポンスを構築します。`sdk.client` を使用してリクエストする場合、ErisPulse の例外をキャッチします。

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
        self.logger.error(f"请求超时: {endpoint}")
        return self.make_error(retcode=32000, message="请求超时")
    except ClientError as e:
        self.logger.error(f"网络错误: {e}")
        return self.make_error(retcode=33000, message="网络请求失败")
    except json.JSONDecodeError:
        self.logger.error("JSON 解析失败")
        return self.make_error(retcode=10006, message="响应格式错误")
    except Exception as e:
        self.logger.error(f"未知错误: {e}", exc_info=True)
        return self.make_error(message=str(e))
```

> **バック互換性**：直接 `aiohttp` を使用する旧アダプターコードは影響を受けません。引き続き `aiohttp.ClientError` をキャッチできます。例外変換は、`sdk.client` 経由でリクエストを開始した場合にのみ有効になります。

### 2. ログ記録

フレームワークは自動的にアダプターに子ロガー（`sdk.logger.get_child("MyAdapter")`）を作成するため、手動で初期化する必要はありません。

```python
class MyAdapter(BaseAdapter):
    # ConfigClass = ...  # 設定クラスを宣言すると、self.logger が自動的に使用可能になります
    
    async def start(self):
        self.logger.info("アダプターを起動中...")
        # ...
        self.logger.info("アダプターの起動が完了しました")
    
    async def shutdown(self):
        self.logger.info("アダプターをシャットダウン中...")
        # ...
        self.logger.info("アダプターのシャットダウンが完了しました")
```

## テスト

### 1. 単体テスト

```python
import pytest
from ErisPulse.Core.Bases import BaseAdapter

class TestMyAdapter:
    def test_converter(self):
        """テスト変換器"""
        converter = MyPlatformConverter()
        raw_event = {"type": "message", "content": "Hello"}
        result = converter.convert(raw_event)
        assert result is not None
        assert result["platform"] == "myplatform"
        assert "myplatform_raw" in result
    
    def test_api_response(self):
        """テスト API 応答形式"""
        adapter = MyAdapter()
        response = adapter.call_api("/test", param="value")
        assert "status" in response
        assert "retcode" in response
```

### 2. 統合テスト

```python
@pytest.mark.asyncio
async def test_adapter_start():
    """テストアダプター起動"""
    adapter = MyAdapter()
    await adapter.start()
    assert adapter._connected is True

@pytest.mark.asyncio
async def test_send_message():
    """テスト送信メッセージ"""
    adapter = MyAdapter()
    await adapter.start()
    
    result = await adapter.Send.To("user", "123").Text("Hello")
    assert result is not None
```

## 逆変換とメッセージ構築

`Raw_ob12` はアダプターが**実装しなければならない**メソッドで、OneBot12 → プラットフォームへの逆変換の統一エントリーポイントです。標準メソッド（`Text`、`Image` など）は `Raw_ob12` に委譲し、修飾子状態（`At`/`Reply`/`AtAll`）は `Raw_ob12` 内でメッセージセグメントにマージする必要があります。

`MessageBuilder` は `Raw_ob12` と一緒に使用するメッセージセグメント構築ツールで、チェーン呼び出しと高速構築をサポートします。

> 完全な実装規範、コード例、使用方法は以下を参照してください：
> - [送信メソッド規範 §6 逆変換規范](../../standards/send-method-spec.md#6-逆変換規范onebot12--プラットフォーム)
> - [送信メソッド規範 §11 メッセージビルダー](../../standards/send-method-spec.md#11-メッセージビルダー-messagebuilder)

## プラットフォームイベントメソッド拡張

アダプターは Event クラスにプラットフォーム固有メソッドを登録し、モジュール開発者がプラットフォーム特有のデータに簡単にアクセスできるようにすることができます。

### 1. Mixin クラスを使用した一括登録（推奨）

プラットフォームに複数の固有メソッドがある場合、Mixin クラスを使用することを推奨します。

```python
# アダプターの start() またはモジュールレベルで登録
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

### 2. デコレータを使用した単一メソッド登録

```python
from ErisPulse.Core.Event import register_event_method

@register_event_method("myplatform")
def get_chat_name(self):
    return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")
```

### 3. アダプター終了時のクリーンアップ

```python
from ErisPulse.Core.Event import unregister_platform_event_methods

class MyAdapter(BaseAdapter):
    async def shutdown(self):
        # プラットフォームイベントメソッドの登録をクリーンアップ
        unregister_platform_event_methods("myplatform")
        # ... その他のクリーンアップ
```

> 詳細な登録とアンロードの説明は [イベントシステム API - プラットフォーム拡張メソッド登録](../../api-reference/event-system.md#アダプター登録プラットフォーム拡張メソッド) を参照してください。

## ドキュメントの維持

### 1. プラットフォーム特性ドキュメントの維持

`docs/zh-CN/platform-guide/` に `{platform}.md` ドキュメントを作成してください（他の言語バージョンは自動生成されます）。

```markdown
# プラットフォーム名アダプタードキュメント

## 基本情報
- 対応モジュールバージョン: 1.0.0
- 維持者: Your Name

## 支援するメッセージ送信タイプ
...

## 特有イベントタイプ
...

## 設定オプション
...
```

### 2. バージョン情報の更新

新しいバージョンをリリースする際、ドキュメント内のバージョン情報を更新してください。

```toml
[project]
version = "2.0.0"  # バージョン番号を更新
```

## 関連ドキュメント

- [アダプター開発入門](getting-started.md) - 最初のアダプターを作成する
- [アダプターの基本概念](core-concepts.md) - アダプターのアーキテクチャを理解する
- [SendDSL 詳解](send-dsl.md) - メッセージ送信を学ぶ