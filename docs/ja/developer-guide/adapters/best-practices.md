# アダプター開発のベストプラクティス

> [!TIP]
> **このドキュメントを読むタイミング**：アダプターの基本的な構造が動作確認できたら読むことを推奨します（エンジニアリングのベストプラクティスに関する内容）。必要でない場合は飛ばしても、他の機能の使用に影響はありません。

本文書では、ErisPulse アダプター開発におけるベストプラクティスの提案を提供します。

## Bot 状態管理と Meta イベント

アダプタは `adapter.emit()` を使用して Meta イベントを送信し、Bot の接続状態、ログイン/ログアウト、およびハートビート情報をフレームワークが自動的に追跡できるようにする必要があります。

### 1. Meta イベントの送信タイミング

| イベント | `detail_type` | 発生タイミング | フレームワークの動作 |
|------|--------------|---------|---------|
| 接続 | `"connect"` | Bot がプラットフォームとの接続を確立したとき | Bot を登録し、`adapter.bot.online` のライフサイクルイベントをトリガー |
| 切断 | `"disconnect"` | Bot がプラットフォームとの接続を切断したとき | Bot をオフライン状態にマークし、`adapter.bot.offline` のライフサイクルイベントをトリガー |
| ハートビート | `"heartbeat"` | 定期的に送信（推奨 30-60 秒） | Bot の最新アクティブ時間とメタ情報を更新 |

### 2. Meta イベントの送信方法

フレームワークは `emit_meta()` メソッドを提供しており、一行で Meta イベントを送信できます。

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Bot のオンライン：一行で connect イベントを送信
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
            # Bot のオフライン
            await self.emit_meta("disconnect", bot_id)
```

### 3. ハートビートイベント

アダプタは接続が維持されている間、定期的にハートビートイベントを送信し、Bot のアクティブ時間を更新する必要があります。

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            # フレームワークに meta heartbeat を送信（一行で完了）
            await self.emit_meta("heartbeat", bot_id)
            await asyncio.sleep(30)
```

### 4. `self` フィールドの自動発見

フレームワークの `adapter.emit()` は、すべてのイベント（Meta イベントに限らず）中の `self` フィールドを自動的に処理します。

- **通常イベント**（message/notice/request）の `self` フィールドは自動的に Bot を登録します。
- **`self` フィールドの拡張情報**：`user_name`、`nickname`、`avatar`、`account_id` などのオプションフィールドをサポートします。

```python
# 転換器に self フィールドを含めることで Bot の自動登録が可能
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
# Bot "bot123" は自動的に登録され、最新アクティブ時間も更新されます
```

### 5. Bot 状態の照会

フレームワークは以下の照会メソッドを提供します。

```python
from ErisPulse import sdk

# Bot の詳細情報を取得
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# すべての Bot を取得（プラットフォームごとに分類）
all_bots = sdk.adapter.list_bots()

# 指定プラットフォームの Bot を取得
platform_bots = sdk.adapter.list_bots("myplatform")

# Bot がオンラインかどうかを確認
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# 完全な状態サマリーを取得（WebUI に表示するのに適しています）
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

アダプタのハートビートは、2つのタスクを同時に完了する必要があります：プラットフォームにハートビート保活を送信し、フレームワークに meta heartbeat イベントを送信することです。

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

アダプタが登録したルーティングは、ユーザーがプラットフォーム側のコールバックアドレスを設定できるように、ユーザーに見えるようにする必要があります。`start()` で接続情報を明示的に出力することを推奨します：

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

ユーザーは以下の API を使用して、アダプタのすべてのルーティングと接続アドレスを確認できます：

```python
from ErisPulse import sdk

# アダプタレベルの接続情報（推奨）
info = sdk.adapter.get_connection_info("myplatform")

# ルーティングマネージャー レベルのクエリ
sdk.router.list_namespaces()              # すべてのネームスペースをリスト
sdk.router.get_module_routes("myplatform")  # 詳細なルーティング情報
sdk.router.get_module_urls("myplatform")    # 完全な接続 URL
```

> **注意**：ルーティング登録時の `module_name` は、ErisPulse に登録されたアダプタの `platform` 名と完全に一致している必要があります。一致しない場合、`get_connection_info()` はルーティングと関連付けられません。複数アカウントのアダプタは、異なる `module_name` を使用するのではなく、各アカウントごとにサブパスを登録する必要があります（例: `/account1/webhook`、`/account2/webhook`）。

## イベント変換

### 1. OneBot12 標準に厳密に従う

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
            "myplatform_raw": raw_event,  # 保持原始数据（必須）
            "myplatform_raw_type": raw_event.get("type", "")  # 原始类型（必須）
        }
        return onebot_event
```

### 2. 時間スタンプの標準化

```python
def _convert_timestamp(self, timestamp):
    """10 位の秒単位時間スタンプに変換"""
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

`At`/`AtAll`/`Reply` 修飾子はフレームワークの SendDSL 基底クラスに内蔵されており、アダプタは `Raw_ob12` と具体的な送信メソッドを実装するだけでよい。`self._apply_modifiers(message)` と `self.send_context` を使用して開発を簡素化する。

### 1. 必ず Task オブジェクトを返す

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """推奨の実装方法：フレームワークの補助メソッドを使用"""
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

### 3. プラットフォーム固有のメソッドをサポート

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

### 1. 標準化されたレスポンス形式

フレームワークは `make_response()` および `make_error()` メソッドを提供し、標準化されたレスポンスを構築します。

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

### 2. エラーコード規格

OneBot12 標準エラーコードに従います。

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

## 多アカウントサポート

### 1. 宣言的構成（推奨）

`AccountConfigClass` を宣言的に設定することで、フレームワークは多アカウントの自動ロード、検証、およびテンプレート生成を管理します。`BotAccountConfig` 基底クラスは `enabled` および `name` フィールドを提供しており、アダプタはそれらを宣言する必要はありません：

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
            self.logger.info(f"アカウント {name} を起動")
            await self._connect(name, account.token)
            # bot_id はフレームワークによってプラットフォームプロトコル/ログイン応答から自動的に取得され、戻り値として補完されます
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # name: アカウント名, account: MyBotConfig インスタンス
```

構成ファイルは自動的に次のように生成されます：

```toml
[MyAdapter.accounts.default]
token = ""
enabled = true
name = ""
```

### 2. アカウント選択メカニズム

フレームワークには `_resolve_account()` メソッドが内蔵されており、次の優先順位でアカウントを照合します：

1. **アカウント名** — 構成のキー名と正確に一致する
2. **`bot_id` フィールド** — 自動的に取得される bot_id（すなわち `event["self"]["user_id"]`）
3. **任意の str フィールド** — 構成内の他の文字列フィールド
4. **デフォルト** — 最初に有効化されたアカウント

```python
# アカウント名で照合
name, account = self._resolve_account("account1")

# bot_id で照合（イベントからの最も一般的な方法）
name, account = self._resolve_account("bot_123")

# 有効化された最初のアカウントを取得（None を渡す）
name, account = self._resolve_account(None)
```

## エラー処理

### 1. 異常の分類処理

`make_error()` を使用して標準化されたエラー応答を構築します。`sdk.client` を通じてリクエストを行う際、ErisPulse の異常をキャッチします：

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
        return self.make_error(retcode=33000, message="ネットワークリクエストが失敗しました")
    except json.JSONDecodeError:
        self.logger.error("JSON 解析に失敗しました")
        return self.make_error(retcode=10006, message="レスポンス形式が無効です")
    except Exception as e:
        self.logger.error(f"不明なエラー: {e}", exc_info=True)
        return self.make_error(message=str(e))
```

> **後方互換性**：`aiohttp` を直接使用する従来のアダプタコードは影響を受けず、`aiohttp.ClientError` をキャッチし続けることができます。エラー変換は `sdk.client` を通じてリクエストが発行される場合にのみ有効です。

### 2. ログ記録

フレームワークはアダプタごとに自動的にサブロガーを作成します（`sdk.logger.get_child("MyAdapter")`）。手動での初期化は不要です：

```python
class MyAdapter(BaseAdapter):
    # ConfigClass = ...  # 設定クラスを宣言した後、self.logger を自動的に使用可能に
    
    async def start(self):
        self.logger.info("アダプタの起動中...")
        # ...
        self.logger.info("アダプタの起動完了")
    
    async def shutdown(self):
        self.logger.info("アダプタの停止中...")
        # ...
        self.logger.info("アダプタの停止完了")
```

## テスト

### 1. ユニットテスト

```python
import pytest
from ErisPulse.Core.Bases import BaseAdapter

class TestMyAdapter:
    def test_converter(self):
        """変換機能のテスト"""
        converter = MyPlatformConverter()
        raw_event = {"type": "message", "content": "Hello"}
        result = converter.convert(raw_event)
        assert result is not None
        assert result["platform"] == "myplatform"
        assert "myplatform_raw" in result
    
    def test_api_response(self):
        """APIレスポンス形式のテスト"""
        adapter = MyAdapter()
        response = adapter.call_api("/test", param="value")
        assert "status" in response
        assert "retcode" in response
```

### 2. 統合テスト

```python
@pytest.mark.asyncio
async def test_adapter_start():
    """アダプタの起動をテスト"""
    adapter = MyAdapter()
    await adapter.start()
    assert adapter._connected is True

@pytest.mark.asyncio
async def test_send_message():
    """メッセージ送信のテスト"""
    adapter = MyAdapter()
    await adapter.start()
    
    result = await adapter.Send.To("user", "123").Text("Hello")
    assert result is not None
```

## リバース変換とメッセージ構築

`Raw_ob12` はアダプターが**実装しなければならない**メソッドであり、OneBot12 → プラットフォームへのリバース変換の統一エントリポイントです。標準メソッド（`Text`、`Image` など）は `Raw_ob12` に委譲し、修飾子の状態（`At`/`Reply`/`AtAll`）は `Raw_ob12` 内でメッセージセグメントとしてマージする必要があります。

`MessageBuilder` は `Raw_ob12` と併用するためのメッセージセグメント構築ツールであり、チェーン呼び出しと高速な構築をサポートしています。

> 完全な実装規格、コード例、および使用方法については、以下を参照してください：
> - [送信メソッド規格 §6 リバース変換規格 (OneBot12 → プラットフォーム)](../../standards/send-method-spec.md#6-リバース変換規格onebot12--プラットフォーム)
> - [送信メソッド規格 §11 メッセージビルダー](../../standards/send-method-spec.md#11-メッセージビルダー-messagebuilder)

## プラットフォームイベントメソッド拡張

アダプタは、Eventラッパークラスにプラットフォーム固有のメソッドを登録し、モジュール開発者がプラットフォーム特有のデータに簡単にアクセスできるようにすることができます。

### 1. Mixin クラスを使用した一括登録（推奨）

プラットフォームに複数の固有メソッドがある場合、Mixin クラスを使用することを推奨します。

```python
# アダプタの start() またはモジュールレベルで登録
from ErisPulse.Core.Event import register_event_mixin

class MyPlatformEventMixin:
    def get_chat_name(self):
        """チャット名を取得"""
        return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

    def is_official_message(self):
        """公式メッセージかどうかを判定"""
        raw = self.get("myplatform_raw", {})
        return raw.get("sender", {}).get("is_official", False)

    def get_message_type(self):
        """プラットフォームのメッセージタイプを取得"""
        return self.get("myplatform_raw", {}).get("msg_type", "text")

# 一括登録
register_event_mixin("myplatform", MyPlatformEventMixin)
```

### 2. デコレータを使用した単一メソッドの登録

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
        # ... 他のクリーンアップ処理
```

> 詳細な登録および登録解除の説明は、[イベントシステム API - プラットフォーム拡張メソッドの登録](../../api-reference/event-system.md#プラットフォーム拡張メソッドの登録) を参照してください。

## ドキュメントの保守

### 1. プラットフォーム固有のドキュメントの保守

`docs/ja/platform-guide/` ディレクトリに `{platform}.md` ドキュメントを作成します（他の言語バージョンは自動的に生成されます）：

```markdown
# プラットフォーム名アダプタドキュメント

## 基本情報
- 対応モジュールバージョン: 1.0.0
- 保守者: Your Name

## 支援されるメッセージ送信タイプ
...

## 固有のイベントタイプ
...

## 設定オプション
...
```

### 2. バージョン情報の更新

新しいバージョンをリリースする際、ドキュメント内のバージョン情報を更新します：

```toml
[project]
version = "2.0.0"  # バージョン番号を更新
```

## 関連ドキュメント

- [アダプタ開発入門](getting-started.md) - 最初のアダプタを作成する
- [アダプタのコアコンセプト](core-concepts.md) - アダプタアーキテクチャの理解
- [SendDSLの詳細](send-dsl.md) - メッセージ送信の学習