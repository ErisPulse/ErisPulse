# アダプタ開発のベストプラクティス

> [!TIP]
> **この記事を読むタイミング**：アダプタの基本構造が動くようになったら読むことを推奨します（工程化のベストプラクティス）。必要なければ飛ばしても、他の機能の使用に影響はありません。

ここでは、アダプタ開発における工程上の約束事項をまとめます。Botの状態報告、接続の再試行とハートビート、複数アカウントの解析、標準化されたエラー応答など、この通りに実装することで、接続切断の無感知、複数アカウントでの送信先ミス、エラーの原因特定困難といったプラットフォーム接続時の一般的な問題を回避できます。

## Botの状態管理とMetaイベント

アダプタは、`adapter.emit()` を使ってMetaイベントを送信し、フレームワークがBotの接続状態、オンライン・オフライン、ハートビート情報を自動的に追跡できるようにする必要があります。

### 1. Metaイベントを送信するタイミング

| イベント | `detail_type` | 発生タイミング | フレームワークの動作 |
|------|--------------|---------|---------|
| 接続 | `"connect"` | Botがプラットフォームと接続したとき | Botを登録し、`adapter.bot.online`のライフサイクルイベントをトリガー |
| 切断 | `"disconnect"` | Botがプラットフォームと切断したとき | Botをオフラインにマークし、`adapter.bot.offline`のライフサイクルイベントをトリガー |
| ハートビート | `"heartbeat"` | 定期的に送信（推奨は30〜60秒） | Botのアクティブタイムとメタ情報を更新 |

### 2. Metaイベントの送信

フレームワークは`emit_meta()`メソッドを提供しており、1行でMetaイベントを送信できます。

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Botがオンラインになったとき：1行でconnectイベントを送信
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
            # Botがオフラインになったとき
            await self.emit_meta("disconnect", bot_id)
```

`emit_meta()` 以外にも、手動で標準的なMetaイベントを構築することもできます（旧バージョンの方法も互換性があります）：

```python
await self.adapter.emit({
    "id": str(uuid4()),
    "time": int(time.time()),
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {
        "platform": "myplatform",
        "user_id": bot_id,
        "user_name": "MyBot",
        "avatar": "https://example.com/avatar.jpg",
    },
    "myplatform_raw": raw_data,
    "myplatform_raw_type": "connected",
})
```

### 3. ハートビートイベント

アダプタは、接続が維持されている間、定期的にハートビートイベントを送信し、Botのアクティブタイムを更新する必要があります。

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            # フレームワークにmeta heartbeatを送信（1行で完了）
            await self.emit_meta("heartbeat", bot_id)
            await asyncio.sleep(30)
```

### 4. `self`フィールドの自動発見

フレームワークの`adapter.emit()`は、`self`フィールドを含むすべてのイベント（Metaイベントに限らず）を自動的に処理します：

- **通常のイベント**（message/notice/request）の`self`フィールドは自動的にBotとして登録されます
- **`self`フィールドの拡張情報**：`user_name`、`nickname`、`avatar`、`account_id`などのオプションフィールドがサポートされています

```python
# 転換器にselfフィールドを含めることで、Botが自動的に登録されます
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
    # ... 他のフィールド
}
await self.adapter.emit(onebot_event)
# Bot "bot123" は自動的に登録され、アクティブタイムが更新されます
```

### 5. Botの状態の照会

照会API（`get_bot_info()` / `list_bots()` / `is_bot_online()` / `get_status_summary()`）とBotのライフサイクルイベントの表は、[アダプタシステムAPI - Botの状態管理](../../api-reference/adapter-system.md#bot-状態管理)をご覧ください。

## 接続管理

### 1. 接続の再試行の実装

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                await self._connect_to_platform()
                self.logger.info("接続に成功しました")
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    # 指数バックオフ戦略
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(
                        f"接続に失敗しました。{wait_time}秒後に再試行します ({retry_count}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("接続に失敗しました。最大再試行回数に達しました")
                    raise
```

### 2. 接続状態の管理

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

### 3. ハートビート保活とMetaハートビート

アダプタのハートビートは、2つのタスクを同時に行う必要があります：プラットフォームへのハートビート保活送信と、フレームワークへのmeta heartbeatイベント送信。

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

                # 2. フレームワークにmeta heartbeatを送信（emit_metaで1行で完了）
                await self.emit_meta("heartbeat", self._bot_id)

                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"ハートビートに失敗しました: {e}")
                break
```

### 4. 接続情報の公開

アダプタが登録したルートは、ユーザーがプラットフォーム側のコールバックアドレスを設定できるように、表示されるべきです。`start()`で接続情報を明示的に出力することを推奨します：

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
                self.logger.info(f"WebSocketアドレス: "
                    f"{info.get('connection', {}).get('base_url', '')}"
                    f"{info.get('connection', {}).get('websocket_routes', [])}")
```

ユーザーは以下のAPIを使って、アダプタのすべてのルートと接続アドレスを照会できます：

```python
from ErisPulse import sdk

# アダプタレベルの接続情報（推奨）
info = sdk.adapter.get_connection_info("myplatform")

# ルートマネージャーのレベルでの照会
sdk.router.list_namespaces()              # すべての名前空間をリストアップ
sdk.router.get_module_routes("myplatform")  # 詳細なルート情報
sdk.router.get_module_urls("myplatform")    # 完全な接続URL
```

> **注意**：ルート登録時の`module_name`は、ErisPulseに登録されたアダプタの`platform`名と完全に一致する必要があります。一致しないと`get_connection_info()`はルートを関連付けられません。複数アカウントのアダプタは、異なる`module_name`ではなく、各アカウントにサブパス（例：`/account1/webhook`、`/account2/webhook`）を登録する必要があります。

### 5. HTTPルートのライフサイクル

アダプタ/モジュールが`router`を使って登録したHTTP/WebSocketルートは、フレームワークによって**帰属原則**に従ってライフサイクル管理されます：

- 登録時の`module_name`（名前空間）が帰属識別子です。**reload / stop / unloadの際にフレームワークは、該当する帰属内のすべてのルートと接続リソースを自動的にクリーンアップ**します。手動でアン登録する必要はありません。
- したがって、**`start()`（モジュールでは`on_load`）では、必ずルートを再登録する必要があります**。インスタンスレベルのブール値フラグを使って「一度だけ登録」の最適化をしないでください。設定のホットリロード（アカウントフィールドの変更が即座に保存される）は、`stop/start`をトリガーし、**同一インスタンスが再利用される**ため、フラグが残るとルートがクリーンアップ後に**永久に失われ**、エンドポイントが404となり、プロセスの再起動でしか復旧しません

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # 毎回起動時に無条件に再登録（reload後のルートは、前のstopで自動的にクリーンアップされている）
        router.register_http_route(self.platform, "/qr/start", self._qr_start, methods=["POST"])
        router.register_http_route(self.platform, "/qr/poll", self._qr_poll, methods=["POST"])
```

モジュール側も同様です（`on_load`で登録）：

```python
class MyModule(BaseModule):
    async def on_load(self):
        router.register_http_route("MyModule", "/api/panel", self._panel, methods=["GET"])
```

ルートを**事前に手動でアン登録**（例：動的にエントリをオフラインにする）する必要がある場合は、明示的に登録解除できます：

```python
from ErisPulse.Core import router

router.unregister_http_route(self.platform, "/qr/start")
```

- ホットリロードのウィンドウ中、クライアントは一時的にルートが404になる可能性があります。これは一時的な現象です。ブラウザ向けのインタラクティブページは、404に対して有限回の自動リトライを実装することを推奨します

## イベントの変換

### 1. OneBot12標準に厳密に従う

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
            "myplatform_raw": raw_event,  # 保持したまま（必須）
            "myplatform_raw_type": raw_event.get("type", "")  # 元のタイプ（必須）
        }
        return onebot_event
```

### 2. 時間スタンプの標準化

```python
def _convert_timestamp(self, timestamp):
    """10桁の秒単位の時間スタンプに変換"""
    if not timestamp:
        return int(time.time())
    
    # ミリ秒単位の時間スタンプの場合
    if timestamp > 10**12:
        return int(timestamp / 1000)
    
    # 秒単位の時間スタンプの場合
    return int(timestamp)
```

### 3. イベントIDの生成

```python
import uuid

def _generate_event_id(self, raw_event):
    """イベントIDを生成"""
    event_id = raw_event.get("event_id")
    if event_id:
        return str(event_id)
    # プラットフォームがIDを提供していない場合、UUIDを生成
    return str(uuid.uuid4())
```

## SendDSLの実装

`At`/`AtAll`/`Reply`修飾子は、フレームワークのSendDSL基底クラスに既に実装済みです。アダプタは`Raw_ob12`と具体的な送信メソッドを実装するだけで済みます。`self._apply_modifiers(message)`と`self.send_context`を使用して開発を簡素化します。

### 1. Taskオブジェクトを必ず返す

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

### 2. 鏈式修飾メソッドはselfを返す

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self # selfを返す
```

### 3. プラットフォーム固有のメソッドをサポート

```python
class Send(BaseAdapter.Send):
    def Sticker(self, sticker_id: str):
        """スタンプ送信"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_sticker",
                message=[{"type": "sticker", "data": {"id": sticker_id}}],
                **self.send_context
            )
        )
    
    def Card(self, card_data: dict):
        """カードメッセージ送信"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_card",
                message=[{"type": "card", "data": {"id": card_data}}],
                **self.send_context
            )
        )
```

## API応答

### 1. 標準化された応答形式

フレームワークは`make_response()`と`make_error()`メソッドを提供し、標準化された応答を構築できます：

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

`make_response()`は、`{platform}_raw`キーを含む応答辞書を自動的に生成します。`make_error()`はデフォルトで`retcode=34000`（Platform Error）を使用します。

### 2. エラーコードの規範

OneBot12標準のエラーコードに従います：

```python
# 1xxxx - 動作リクエストエラー
10001: Bad Request
10002: Unsupported Action
10003: Bad Param

# 2xxxx - 動作ハンドラエラー
20001: Bad Handler
20002: Internal Handler Error

# 3xxxx - 動作実行エラー
31000: Database Error
32000: Filesystem Error
33000: Network Error
34000: Platform Error
35000: Logic Error
```

## 複数アカウントのサポート

### 1. 宣言的構成（推奨）

`AccountConfigClass`を使って構成クラスを宣言した後、フレームワークが複数アカウントのロード、検証、テンプレート生成を自動的に管理します。`BotAccountConfig`基底クラスは`enabled`と`name`フィールドを提供しており、アダプタは宣言する必要はありません：

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
            self.logger.info(f"アカウント {name} を起動します")
            await self._connect(name, account.token)
            # bot_idはフレームワークがプラットフォームプロトコル/ログイン応答から自動的に取得し、戻し埋めされます
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # name: アカウント名, account: MyBotConfigインスタンス
```

構成ファイルは自動的に生成されます：

```toml
[MyAdapter.accounts.default]
token = ""
enabled = true
name = ""
```

### 2. アカウント選択メカニズム

送信時に指定されたアカウント識別子（`Using()` / イベントチェーンバインド）は、フレームワークが自動的に解析し、以下の優先順位で一致します：

1. **アカウント名** — 構成のキー名と正確に一致
2. **`bot_id`フィールド** — アカウント構成の`bot_id`（実行時に自動的に戻し埋めされます、通常は`event["self"]["user_id"]`）
3. **任意のstrフィールド** — 構成の他の文字列フィールド
4. **デフォルト** — 最初に有効化されたアカウント

アダプタは`call_api`を実装する際、フレームワークが提供するアカウント解析を使って「識別子 → アカウント構成」のマッピングを完了します：

```python
# アカウント名で一致
name, account = self._resolve_account("account1")

# bot_idで一致（最も一般的な方法、イベントから取得）
name, account = self._resolve_account("bot_123")

# 有効化された最初のアカウントを取得（Noneを渡す）
name, account = self._resolve_account(None)
```

## エラーハンドリング

### 1. エラーの分類と処理

`make_error()`を使って標準化されたエラー応答を構築します。`sdk.client`を使ってリクエストする際は、ErisPulseの例外をキャッチします：

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
        self.logger.error(f"リクエストがタイムアウトしました: {endpoint}")
        return self.make_error(retcode=32000, message="リクエストがタイムアウトしました")
    except ClientError as e:
        self.logger.error(f"ネットワークエラー: {e}")
        return self.make_error(retcode=33000, message="ネットワークリクエストに失敗しました")
    except json.JSONDecodeError:
        self.logger.error("JSONの解析に失敗しました")
        return self.make_error(retcode=10006, message="レスポンス形式が無効です")
    except Exception as e:
        self.logger.error(f"未知のエラー: {e}", exc_info=True)
        return self.make_error(message=str(e))
```

> **後方互換性**：`aiohttp`を使用する旧アダプタのコードは影響を受けません。`sdk.client`を使ってリクエストする場合のみ、例外の変換が有効になります。

### 2. ログ記録

フレームワークは、アダプタごとにサブロガーを自動的に作成します（`sdk.logger.get_child("MyAdapter")`）。手動で初期化する必要はありません：

```python
class MyAdapter(BaseAdapter):
    # ConfigClass = ...  # 構成クラスを宣言するとself.loggerが自動的に利用可能になります
    
    async def start(self):
        self.logger.info("アダプタの起動中...")
        # ...
        self.logger.info("アダプタの起動完了")
    
    async def shutdown(self):
        self.logger.info("アダプタの終了中...")
        # ...
        self.logger.info("アダプタの終了完了")
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
        """テストAPI応答形式"""
        adapter = MyAdapter()
        response = adapter.call_api("/test", param="value")
        assert "status" in response
        assert "retcode" in response
```

### 2. 集成テスト

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

`Raw_ob12`はアダプタが**必ず実装**すべきメソッドであり、OneBot12からプラットフォームへのリバースコンバージョンの統一エントリーポイントです。標準メソッド（`Text`、`Image`など）は`Raw_ob12`に委譲し、修飾子の状態（`At`/`Reply`/`AtAll`）は`Raw_ob12`内でメッセージセグメントにマージする必要があります。

`MessageBuilder`は`Raw_ob12`と併用するメッセージセグメント構築ツールで、チェーン呼び出しと迅速な構築が可能です。

> 完全な実装規範、コード例、使用方法は、以下のドキュメントをご覧ください：
> - [送信メソッド規範 §6 リバースコンバージョン規範](../../standards/send-method-spec.md#6-リバースコンバージョン規範onebot12--プラットフォーム)
> - [送信メソッド規範 §11 メッセージビルダー](../../standards/send-method-spec.md#11-メッセージビルダー-messagebuilder)

## プラットフォームイベントメソッドの拡張

アダプタは、Eventラッパークラスにプラットフォーム固有のメソッドを登録することで、モジュール開発者がプラットフォーム固有のデータに簡単にアクセスできるようにすることができます。

### 1. Mixinクラスを使って一括登録（推奨）

プラットフォームに複数の固有メソッドがある場合、Mixinクラスを使って一括登録することを推奨します：

```python
# アダプタのstart()またはモジュールレベルで登録
from ErisPulse.Core.Event import register_event_mixin

class MyPlatformEventMixin:
    def get_chat_name(self):
        """チャット名を取得"""
        return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

    def is_official_message(self):
        """公式メッセージか判定"""
        raw = self.get("myplatform_raw", {})
        return raw.get("sender", {}).get("is_official", False)

    def get_message_type(self):
        """プラットフォームのメッセージタイプを取得"""
        return self.get("myplatform_raw", {}).get("msg_type", "text")

# 一括登録
register_event_mixin("myplatform", MyPlatformEventMixin)
```

### 2. デコレータを使って個別メソッドを登録

```python
from ErisPulse.Core.Event import register_event_method

@register_event_method("myplatform")
def get_chat_name(self):
    return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")
```

### 3. アダプタの終了時にクリーンアップ

```python
from ErisPulse.Core.Event import unregister_platform_event_methods

class MyAdapter(BaseAdapter):
    async def shutdown(self):
        # プラットフォームイベントメソッドの登録をクリーンアップ
        unregister_platform_event_methods("myplatform")
        # ... その他のクリーンアップ
```

> 詳細な登録とアン登録の説明は、[イベントシステムAPI - プラットフォーム拡張メソッドの登録](../../api-reference/event-system.md#アダプタ登録プラットフォーム拡張メソッド)をご覧ください。

## ドキュメントの維持

### 1. プラットフォーム特性のドキュメントを維持

`docs/ja/platform-guide/`に`{platform}.md`ドキュメントを作成します（他の言語バージョンは自動生成されます）：

```markdown
# プラットフォーム名アダプタドキュメント

## 基本情報
- 対応モジュールバージョン: 1.0.0
- 維持者: あなたの名前

## 支援されるメッセージ送信タイプ
...

## 特有のイベントタイプ
...

## 設定オプション
...
```

### 2. バージョン情報を更新

新しいバージョンをリリースする際、ドキュメントのバージョン情報を更新します：

```toml
[project]
version = "2.0.0"  # バージョン番号を更新
```

## 関連ドキュメント

### 前提知識の振り返り

- [アダプタ開発入門](getting-started.md) - 最初のアダプタの作成
- [アダプタのコアコンセプト](core-concepts.md) - アダプタアーキテクチャの理解
- [SendDSLの詳細](send-dsl.md) - メッセージ送信の学習

### アダプタの完成後

- [公開とモジュールストアのガイド](../publishing.md) - PyPIやモジュールストアへの公開