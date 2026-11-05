# アダプター開発ベストプラクティス

> [!TIP]
> **いつこのドキュメントを読むべきか**：アダプターのスケルトンが動作した後に読むことを推奨します（エンジニアリングのベストプラクティス）。不要であればスキップしても、他の機能の利用には影響しません。


ここでは、アダプター開発におけるエンジニアリング規約をまとめています：Bot ステータスの報告、接続リトライとハートビート、マルチアカウントの解決、標準化されたエラーレスポンス——これらに従うことで、切断に気づかない、マルチアカウントで誤った宛先に送信する、エラーの位置特定が難しいといった、プラットフォーム接続時によくある問題を回避できます。

## Bot ステータス管理と Meta イベント

アダプターは `adapter.emit()` を通じて能動的に meta イベントを送信し、フレームワークが Bot の接続状態、オンライン/オフライン、ハートビート情報を自動的に追跡できるようにする必要があります。

### 1. いつ Meta イベントを送信するか

| イベント | `detail_type` | 発生タイミング | フレームワークの動作 |
|------|--------------|---------|---------|
| 接続 | `"connect"` | Bot がプラットフォームとの接続を確立したとき | Bot を登録し、`adapter.bot.online` ライフサイクルイベントを発火 |
| 切断 | `"disconnect"` | Bot がプラットフォームとの接続を切断したとき | Bot をオフラインとしてマークし、`adapter.bot.offline` ライフサイクルイベントを発火 |
| ハートビート | `"heartbeat"` | 定期送信（30～60 秒を推奨） | Bot のアクティブ時刻とメタ情報を更新 |

### 2. Meta イベントの送信

フレームワークは `emit_meta()` メソッドを提供しており、1 行で meta イベントを送信できます：

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Bot オンライン：1 行で connect イベントを送信
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="私のボット")

        try:
            while True:
                data = await websocket.receive_text()
                event = self.convert(data)
                if event:
                    await self.adapter.emit(event)
        except WebSocketDisconnect:
            pass
        finally:
            # Bot オフライン
            await self.emit_meta("disconnect", bot_id)
```

標準の meta イベントを手動で構築することもできます（旧バージョンの方式も引き続き互換性があります）：

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

アダプターは接続が生存している間、定期的にハートビートイベントを送信し、Bot のアクティブ時刻を更新する必要があります：

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            # フレームワークに meta heartbeat を送信（1 行で完了）
            await self.emit_meta("heartbeat", bot_id)
            await asyncio.sleep(30)
```

### 4. `self` フィールドの自動検出

フレームワークの `adapter.emit()` は、すべてのイベント（meta イベントに限らず）の `self` フィールドを自動的に処理します：

- **通常のイベント**（message/notice/request）の `self` フィールドは自動的に検出され、Bot が登録されます
- **`self` フィールドの拡張情報**：`user_name`、`nickname`、`avatar`、`account_id` のオプションフィールドをサポート

```python
# コンバーターに self フィールドを含めるだけで Bot が自動登録される
onebot_event = {
    "type": "message",
    "detail_type": "private",
    "platform": "myplatform",
    "self": {
        "platform": "myplatform",
        "user_id": "bot123",
        "user_name": "MyBot",
        "nickname": "私のボット",
    },
    # ... その他のフィールド
}
await self.adapter.emit(onebot_event)
# Bot "bot123" が自動登録され、アクティブ時刻が更新されました
```

### 5. Bot ステータスの照会

照会 API（`get_bot_info()` / `list_bots()` / `is_bot_online()` / `get_status_summary()`）と Bot ライフサイクルイベントの一覧表については、[アダプターシステム API - Bot ステータス管理](../../api-reference/adapter-system.md#bot-状态管理) を参照してください。

## 接続管理

### 1. 接続リトライの実装

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
                        f"接続に失敗しました。{wait_time}秒後にリトライします ({retry_count}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("接続に失敗しました。最大リトライ回数に達しました")
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

### 3. ハートビートによるキープアライブと Meta ハートビート

アダプターのハートビートは 2 つのタスクを同時に担う必要があります：プラットフォームにハートビートを送信して接続を維持するとともに、フレームワークに meta heartbeat イベントを送信します。

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = await self._connect_to_platform()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        while self.connection:
            try:
                # 1. プラットフォームにハートビートを送信して接続を維持
                await self.connection.send_json({"type": "ping"})

                # 2. フレームワークに meta heartbeat を送信（emit_meta を使用して 1 行で完了）
                await self.emit_meta("heartbeat", self._bot_id)

                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"ハートビートに失敗しました: {e}")
                break
```

### 4. 接続情報の公開

アダプターが登録するルートはユーザーから参照できるようにし、プラットフォーム側のコールバックアドレスをユーザーが設定しやすくする必要があります。`start()` 内で能動的に接続情報を出力することを推奨します：

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

ユーザーは以下の API でアダプターのすべてのルートと接続アドレスを確認できます：

```python
from ErisPulse import sdk

# アダプターレベルの接続情報（推奨）
info = sdk.adapter.get_connection_info("myplatform")

# ルーティングマネージャーレベルの照会
sdk.router.list_namespaces()              # すべての名前空間を一覧表示
sdk.router.get_module_routes("myplatform")  # 詳細なルート情報
sdk.router.get_module_urls("myplatform")    # 完全な接続 URL
```

> **注意**：ルート登録時の `module_name` は、ErisPulse にアダプターが登録した `platform` 名と完全に一致している必要があります。一致しない場合、`get_connection_info()` がルートを関連付けられなくなります。マルチアカウントアダプターでは、異なる `module_name` を使用するのではなく、アカウントごとにサブパス（`/account1/webhook`、`/account2/webhook` など）を登録してください。

### 5. HTTP ルートのライフサイクル

アダプター/モジュールが `router` を通じて登録した HTTP/WebSocket ルートのライフサイクルは、**帰属原則**に基づいてフレームワークが自動的に管理します：

- 登録時の `module_name`（名前空間）がそのまま帰属識別子となります。**reload / stop / unload の際、フレームワークはその帰属下のすべてのルートと接続リソースを自動的にクリーンアップするため**、手動での登録解除は不要です
- したがって、**`start()`（モジュールの場合は `on_load`）内で無条件にルートを再登録する必要があります**。インスタンスレベルのブールフラグによる「1 回だけ登録する」という最適化は避けてください：設定のホットリロード（アカウントフィールドの変更の即時保存など）は stop/start をトリガーし、**同一インスタンスを再利用**します。フラグが残っていると、ルートがクリーンアップされた後に**永久に失われ**、インターフェースが 404 を返し、プロセスを再起動して初めて復旧するという事象として現れます

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # 起動のたびに無条件で再登録する（reload 後、ルートは前回の stop 時に自動的にクリーンアップ済み）
        router.register_http_route(self.platform, "/qr/start", self._qr_start, methods=["POST"])
        router.register_http_route(self.platform, "/qr/poll", self._qr_poll, methods=["POST"])
```

モジュール側も同様です（`on_load` 内で登録）：

```python
class MyModule(BaseModule):
    async def on_load(self):
        router.register_http_route("MyModule", "/api/panel", self._panel, methods=["GET"])
```

ルートを**事前に手動でアンロード**する必要がある場合（動的にエントリをオフラインにするなど）は、能動的に登録解除できます：

```python
from ErisPulse.Core import router

router.unregister_http_route(self.platform, "/qr/start")
```

- フロントエンド/呼び出し元は、ホットリロードのタイミングによってはルートの 404 を受け取ることがありますが、これは一時的な現象です。ブラウザ向けのインタラクティブページでは、404 に対して有限回の自動リトライを行うことを推奨します

## イベント変換

### 1. OneBot12 標準への厳密な準拠

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """イベントを変換する"""
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
            "myplatform_raw": raw_event,  # 生データを保持（必須）
            "myplatform_raw_type": raw_event.get("type", "")  # 元のタイプ（必須）
        }
        return onebot_event
```

### 2. タイムスタンプの標準化

```python
def _convert_timestamp(self, timestamp):
    """10 桁の秒単位タイムスタンプに変換する"""
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
    """イベント ID を生成する"""
    event_id = raw_event.get("event_id")
    if event_id:
        return str(event_id)
    # プラットフォームが ID を提供していない場合は UUID を生成
    return str(uuid.uuid4())
```

## SendDSL の実装

`At`/`AtAll`/`Reply` 修飾子はフレームワークの SendDSL 基底クラスに組み込まれており、アダプターは `Raw_ob12` と具体的な送信メソッドを実装するだけです。`self._apply_modifiers(message)` と `self.send_context` を使用して開発を簡素化できます。

### 1. Task オブジェクトを必ず返す

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

### 2. チェーン可能な修飾メソッドは self を返す

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self # self を返す
```

### 3. プラットフォーム固有メソッドのサポート

```python
class Send(BaseAdapter.Send):
    def Sticker(self, sticker_id: str):
        """スタンプを送信する"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_sticker",
                message=[{"type": "sticker", "data": {"id": sticker_id}}],
                **self.send_context
            )
        )
    
    def Card(self, card_data: dict):
        """カードメッセージを送信する"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_card",
                message=[{"type": "card", "data": card_data}],
                **self.send_context
            )
        )
```

## API レスポンス

### 1. 標準化されたレスポンス形式

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

### 2. エラーコード規約

OneBot12 標準のエラーコードに従います：

```python
# 1xxxx - アクションリクエストエラー
10001: Bad Request
10002: Unsupported Action
10003: Bad Param

# 2xxxx - アクションハンドラーエラー
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

### 1. 宣言的設定（推奨）

`AccountConfigClass` で設定クラスを宣言すると、フレームワークがマルチアカウントの読み込み、検証、テンプレート生成を自動的に管理します。`BotAccountConfig` 基底クラスは `enabled` と `name` フィールドを提供するため、アダプター側で宣言する必要はありません：

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
            # bot_id はフレームワークがプラットフォームプロトコル/ログインレスポンスから自動的に取得して書き戻します
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # name: アカウント名, account: MyBotConfig インスタンス
```

設定ファイルは自動的に以下のように生成されます：

```toml
[MyAdapter.accounts.default]
token = ""
enabled = true
name = ""
```

### 2. アカウント選択の仕組み

フレームワークには `_resolve_account()` メソッドが組み込まれており、マッチングの優先順位は次のとおりです：

1. **アカウント名** — 設定のキー名と完全一致
2. **`bot_id` フィールド** — 自動取得された bot_id（`event["self"]["user_id"]`）
3. **任意の str フィールド** — 設定内のその他の文字列フィールド
4. **フォールバック** — 最初に有効になっているアカウント

```python
# アカウント名でマッチング
name, account = self._resolve_account("account1")

# bot_id でマッチング（イベント由来の、最も一般的な使い方）
name, account = self._resolve_account("bot_123")

# 最初に有効なアカウントを取得（None を渡す）
name, account = self._resolve_account(None)
```

## エラーハンドリング

### 1. 例外の分類処理

`make_error()` を使って標準化されたエラーレスポンスを構築します。`sdk.client` 経由でリクエストする場合は、ErisPulse の例外をキャッチします：

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
        return self.make_error(retcode=32000, message="リクエストタイムアウト")
    except ClientError as e:
        self.logger.error(f"ネットワークエラー: {e}")
        return self.make_error(retcode=33000, message="ネットワークリクエストに失敗しました")
    except json.JSONDecodeError:
        self.logger.error("JSON の解析に失敗しました")
        return self.make_error(retcode=10006, message="レスポンスの形式が不正です")
    except Exception as e:
        self.logger.error(f"不明なエラー: {e}", exc_info=True)
        return self.make_error(message=str(e))
```

> **後方互換性**：`aiohttp` を直接使用する旧アダプターコードは影響を受けず、引き続き `aiohttp.ClientError` をキャッチできます。例外の変換は、`sdk.client` 経由でリクエストを行った場合にのみ有効です。

### 2. ログ出力

フレームワークはアダプター用の子 logger を自動的に作成するため（`sdk.logger.get_child("MyAdapter")`）、手動で初期化する必要はありません：

```python
class MyAdapter(BaseAdapter):
    # ConfigClass = ...  # 設定クラスを宣言すれば self.logger が自動的に使えるようになる
    
    async def start(self):
        self.logger.info("アダプター起動中...")
        # ...
        self.logger.info("アダプターの起動が完了しました")
    
    async def shutdown(self):
        self.logger.info("アダプター終了中...")
        # ...
        self.logger.info("アダプターの終了が完了しました")
```

## テスト

### 1. ユニットテスト

```python
import pytest
from ErisPulse.Core.Bases import BaseAdapter

class TestMyAdapter:
    def test_converter(self):
        """コンバーターをテストする"""
        converter = MyPlatformConverter()
        raw_event = {"type": "message", "content": "Hello"}
        result = converter.convert(raw_event)
        assert result is not None
        assert result["platform"] == "myplatform"
        assert "myplatform_raw" in result
    
    def test_api_response(self):
        """API レスポンス形式をテストする"""
        adapter = MyAdapter()
        response = adapter.call_api("/test", param="value")
        assert "status" in response
        assert "retcode" in response
```

### 2. 統合テスト

```python
@pytest.mark.asyncio
async def test_adapter_start():
    """アダプターの起動をテストする"""
    adapter = MyAdapter()
    await adapter.start()
    assert adapter._connected is True

@pytest.mark.asyncio
async def test_send_message():
    """メッセージ送信をテストする"""
    adapter = MyAdapter()
    await adapter.start()
    
    result = await adapter.Send.To("user", "123").Text("Hello")
    assert result is not None
```

## 逆変換とメッセージ構築

`Raw_ob12` はアダプターが**必ず実装する必要がある**メソッドであり、逆変換（OneBot12 → プラットフォーム）の統一的なエントリポイントです。標準メソッド（`Text`、`Image` など）は `Raw_ob12` に委譲する必要があり、修飾子の状態（`At`/`Reply`/`AtAll`）は `Raw_ob12` 内でメッセージセグメントにマージする必要があります。

`MessageBuilder` は `Raw_ob12` と併せて使用するメッセージセグメント構築ツールで、チェーン呼び出しとクイック構築をサポートします。

> 完全な実装仕様、コード例、使用方法については、以下を参照してください：
> - [送信メソッド仕様 §6 逆変換仕様](../../standards/send-method-spec.md#6-反向转换规范onebot12--平台)
> - [送信メソッド仕様 §11 メッセージビルダー](../../standards/send-method-spec.md#11-消息构建器-messagebuilder)

## プラットフォームイベントメソッドの拡張

アダプターは Event ラッパークラスにプラットフォーム固有のメソッドを登録でき、モジュール開発者がプラットフォーム固有のデータにより簡単にアクセスできるようになります。

### 1. Mixin クラスを使った一括登録（推奨）

プラットフォームに複数の固有メソッドがある場合は、Mixin クラスの使用を推奨します：

```python
# アダプターの start() またはモジュールレベルで登録する
from ErisPulse.Core.Event import register_event_mixin

class MyPlatformEventMixin:
    def get_chat_name(self):
        """チャット名を取得する"""
        return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

    def is_official_message(self):
        """公式メッセージかどうかを判定する"""
        raw = self.get("myplatform_raw", {})
        return raw.get("sender", {}).get("is_official", False)

    def get_message_type(self):
        """プラットフォームのメッセージタイプを取得する"""
        return self.get("myplatform_raw", {}).get("msg_type", "text")

# 一括登録
register_event_mixin("myplatform", MyPlatformEventMixin)
```

### 2. デコレーターを使った単一メソッドの登録

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

> より詳細な登録・登録解除の説明については、[イベントシステム API - プラットフォーム拡張メソッドの登録](../../api-reference/event-system.md#适配器注册平台扩展方法) を参照してください。

## ドキュメントのメンテナンス

### 1. プラットフォーム特性ドキュメントの維持

`docs/ja/platform-guide/` の下に `{platform}.md` ドキュメントを作成します（他の言語バージョンは自動生成されます）：

```markdown
# プラットフォーム名アダプタードキュメント

## 基本情報
- 対応モジュールバージョン: 1.0.0
- メンテナー: Your Name

## サポートされるメッセージ送信タイプ
...

## 固有のイベントタイプ
...

## 設定オプション
...
```

### 2. バージョン情報の更新

新しいバージョンをリリースする際は、ドキュメント内のバージョン情報を更新します：

```toml
[project]
version = "2.0.0"  # バージョン番号を更新
```

## 関連ドキュメント

### 前置知識のおさらい

- [アダプター開発入門](getting-started.md) - 最初のアダプターを作成する
- [アダプターのコアコンセプト](core-concepts.md) - アダプターのアーキテクチャを理解する
- [SendDSL 詳解](send-dsl.md) - メッセージ送信を学ぶ

### アダプター完成後

- [公開とモジュールストアガイド](../publishing.md) - PyPI とモジュールストアへ公開する