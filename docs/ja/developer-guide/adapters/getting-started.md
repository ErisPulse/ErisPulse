# アダプタ開発入門

このガイドは、新しいメッセージプラットフォームと接続して ErisPulse アダプタの開発を開始するのを支援します。

```java
// アダプタの開始と初期化
public void startAdapter() {
    // プラットフォーム設定のロード
    String configPath = "configs/platform-config.json";

    // ErisPulse アダプタインスタンスの作成
    ErisPulseAdapter adapter = new ErisPulseAdapter(configPath);

    // サーバー接続の確立
    adapter.connectToServer();

    // メッセージリスナーの登録
    adapter.registerMessageListener(new MessageListener() {
        @Override
        public void onMessageReceived(Message msg) {
            // 受信したメッセージの処理
            System.out.println("受信メッセージ: " + msg.getContent());

            // メッセージの返信
            msg.reply("ありがとうございます。");
        }
    });

    // エラーハンドリング
    adapter.setOnErrorHandler((error) -> {
        System.err.println("エラーが発生しました: " + error.getMessage());
    });
}

## アダプターの概要

### アダプターとは

アダプターは ErisPulse と各メッセージプラットフォームの間の橋渡しとして機能し、主に以下の役割を担当します。

1. **正変換**：プラットフォームからのイベントを受け取り、OneBot12 標準形式に変換する（Converter）
2. **逆変換**：OneBot12 メッセージセグメントをプラットフォーム API コールに変換する（`Raw_ob12`）
3. プラットフォームとの接続管理（WebSocket/WebHook）
4. 統一された SendDSL メッセージ送信インターフェースの提供

### アダプターのアーキテクチャ

```mermaid
flowchart LR
    subgraph receive["正変換（受信）"]
        direction TB
        P1["プラットフォームイベント"] --> C1["Converter.convert()"] --> O1["OneBot12 標準イベント"] --> S1["イベントシステム"] --> M1["モジュール処理"]
    end
    subgraph send["逆変換（送信）"]
        direction TB
        M2["モジュールメッセージ構築"] --> R1["Send.Raw_ob12()"] --> N1["プラットフォームネイティブ API コール"] --> R2["標準応答フォーマット"]
    end

## ディレクトリ構造

標準的なアダプタパッケージ構造:

```
MyAdapter/
├── pyproject.toml          # プロジェクト設定
├── README.md               # プロジェクト説明
├── LICENSE                 # ライセンス
└── MyAdapter/
    ├── __init__.py          # パッケージのエントリポイント
    ├── Core.py               # アダプタのメインクラス
    └── Converter.py          # イベントコンバーター

## クイックスタート

### 1. プロジェクトの作成

```bash
mkdir MyAdapter && cd MyAdapter
```

### 2. pyproject.toml の作成

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "MyAdapterプラットフォームアダプタ"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

dependencies = [
    "ErisPulse>=2.4.0"  # ErisPulse には aiohttp が内蔵されており、通常は個別の依存関係は必要ありません
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points."erispulse.adapter"]
"MyAdapter" = "MyAdapter:MyAdapter"
```

### 3. アダプタのメインクラスの作成

フレームワークは `ConfigClass` / `AccountConfigClass` を使用した宣言的設定管理を提供しており、アダプタは設定クラスを宣言するだけで、自動的に設定を読み込み、検証し、設定テンプレートを生成できます。

```python
# MyAdapter/Core.py
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyAdapterConfig(BaseConfig):
    """MyAdapter 設定"""
    api_endpoint: str = field(
        default="https://api.example.com",
        metadata={
            "description": {"i18n": "my_adapter.api_endpoint", "default": "API アドレス"},
            "required": False,
            "ui": {"widget": "text", "group": "connection", "order": 1},
        },
    )
    token: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_adapter.token", "default": "プラットフォーム Token"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 2},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # 設定クラスを宣言すると、フレームワークが自動的に管理します
    
    # __init__ のオーバーライドは不要です！フレームワークが自動的に処理します：
    # - self.sdk / self.logger が自動的に設定されます
    # - self.cfg は設定をリアルタイムで読み込みます
    # - self.Send / self.Request が自動的に初期化されます
    
    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
```

> ⚠️ **`__init__` について**：新バージョンでは `BaseAdapter.__init__(self, sdk=None)` が SDK参照、ログの初期化、設定の読み込みを自動的に処理します。ほとんどのアダプタでは **`__init__` のオーバーライドは不要** です。詳細は [__init__ 注意事項](#init-注意事項) を参照してください。

> ⚠️ **`super().__init__()` について**：`BaseAdapter.__init__()` は `Send` と `Request` のファクトリインスタンスを作成します。これを呼び忘れると、すべてのメッセージ送信とリクエスト操作で `AttributeError` が発生します。詳細は [__init__ 注意事項](#init-注意事項) を参照してください。

### 4. 必要メソッドの実装

```python
class MyAdapter(BaseAdapter):
    # ... __init__ のコード ...
    
    async def start(self):
        """アダプタを起動します（必須実装）"""
        # WebSocket または WebHook ルートを登録します
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler
        )
        self.logger.info("アダプタが起動しました")
    
    async def shutdown(self):
        """アダプタを閉じます（必須実装）"""
        router.unregister_websocket(
            module_name="myplatform",
            path="/ws"
        )
        # 接続とリソースのクリーンアップ
        self.logger.info("アダプタが閉じられました")
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォーム API を呼び出します（必須実装）"""
        raise NotImplementedError("call_api を実装してください")
```

#### 主導的な Meta イベントの送信

アダプタは、フレームワークが Bot のオンライン状態を追跡できるように、主導的に Meta イベントを送信すべきです。`emit_meta()` を 1 行で実行できます：

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Bot オンライン
        await self.emit_meta("connect", bot_id, user_name="MyBot")

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

> Bot のステータス管理と Meta イベントの詳細については、[アダプタのベストプラクティス - Bot ステータス管理](best-practices.md#bot-状態管理与-meta-事件) を参照してください。

### 5. Send クラスの実装

`At`/`AtAll`/`Reply` デコレータは、フレームワークの SendDSL 基クラスに既に実装されているため、アダプタは `Raw_ob12` と具体的な送信メソッドを実装するだけで済みます。

フレームワークは 2 つの重要なヘルパーメソッドを提供します：
- `self._apply_modifiers(message)` — At/AtAll/Reply デコレータをメッセージセグメントに自動的にマージします
- `self.send_context` — 送信コンテキスト辞書（`target_type`、`target_id`、`account_id`）を取得します

```python
import asyncio

class MyAdapter(BaseAdapter):
    # ... 他のコード ...

    class Send(BaseAdapter.Send):

        def Raw_ob12(self, message, **kwargs):
            """
            OneBot12 形式のメッセージを送信します（必須実装）

            _apply_modifiers を使用してデコレータの状態を自動的にマージし、
            send_context を使用して送信コンテキストを取得します。
            """
            async def _do_send():
                segments = self._apply_modifiers(message)
                return await self._adapter.call_api(
                    endpoint="/send_message",
                    message=segments,
                    **self.send_context,
                    **kwargs
                )
            return asyncio.create_task(_do_send())

        # Text/Image/Voice/Video/File は SendDSL 基クラスから継承されているため、
        # デフォルトでは Raw_ob12 に委譲されます。繰り返し実装する必要はありません。
        # プラットフォーム固有のロジックが必要な場合は、個別のメソッドをオーバーライドできます：
        # def Text(self, text: str):
        #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**メディアクラスの送信メソッド（Image/Video/File）の実装のポイント：**

- 基クラスのデフォルト実装は `file` パラメータを OneBot12 メッセージセグメントにラップして `Raw_ob12` に渡すため、アダプタは `Raw_ob12` 内でダウンロード/アップロードの処理を行う必要があります
- `file` パラメータは `bytes` バイナリデータと `str` URL の両方のタイプをサポートする必要があります
- URL が渡された場合は、ファイルをダウンロードしてからプラットフォームにアップロードする必要があります
- プラットフォームでは通常、まずアップロードインターフェースを呼び出してファイルIDを取得し、次に送信インターフェースを呼び出す必要があります

**`__getattr__` マジックメソッド：**

- メソッド名の大文字と小文字を区別しないように実装（`Text`、`text`、`TEXT` すべてが呼び出せます）
- 定義されていないメソッドは、エラーを返すのではなく、ヒントメッセージを返します

**`Raw_ob12` メソッド：**

- OneBot12 標準メッセージ形式をプラットフォーム形式に変換して送信します
- `self._apply_modifiers(message)` を使用して At/AtAll/Reply デコレータを自動的に処理します
- `**self.send_context` を使用して送信先情報とアカウント情報を渡します

### 6. コンバータの実装

```python
# MyAdapter/Converter.py
import time
import uuid

class MyPlatformConverter:
    def convert(self, raw_event):
        """プラットフォームネイティブイベントを OneBot12 標準形式に変換します"""
        if not isinstance(raw_event, dict):
            return None
        
        onebot_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": int(time.time()),
            "type": self._convert_event_type(raw_event.get("type")),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": raw_event.get("type", "")
        }
        
        return onebot_event
    
    def _convert_event_type(self, event_type):
        """イベントタイプを変換します"""
        type_map = {
            "message": "message",
            "notice": "notice"
        }
        return type_map.get(event_type, "unknown")
    
    def _convert_detail_type(self, raw_event):
        """詳細タイプを変換します"""
        return "private"  # 簡略化されたサンプル
```

### 7. Request クラスの実装（リクエスト操作）

プラットフォームが Bot が意思決定を行う必要があるフレンドリクエストやグループ招待などをサポートしている場合、`Request` 内部クラスを実装できます：

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    # ... Send と他のコード ...

    class Request(RequestDSL):
        """リクエスト操作の実装（フレンドリクエスト、グループ招待など）"""

        def accept(self, **kwargs):
            """リクエストを承認します"""
            async def _do():
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    approve=True,
                    **kwargs,
                )
                return {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            return self._create_task(_do())

        def reject(self, **kwargs):
            """リクエストを拒否します"""
            async def _do():
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    approve=False,
                    **kwargs,
                )
                return {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            return self._create_task(_do())
```

モジュール開発者使用方式：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Event を介した便利なメソッド
    await event.approve()
    # あるいはアダプタを直接操作
    await adapter.myplatform.Request("req_id").accept()
```

> プラットフォームがリクエスト操作をサポートしていない場合は、`Request` 内部クラスを実装する必要はありません。基クラスはデフォルトで `retcode=10002`（サポートされていない操作）を返します。詳細は [リクエスト操作仕様](../../standards/request-action-spec.md) を参照してください。

### 8. パッケージのエントリーポイントの作成

```python
# MyAdapter/__init__.py
from .Core import MyAdapter

## 依存関係の宣言（オプション、2.8.0+）

アダプタは他のアダプタやモジュールへの依存を宣言し、アダプタ間の連携とオプション機能を実現できます：

```python
from typing import ClassVar

class MyAdapter(BaseAdapter):
    # 硬い依存：存在しない場合は起動をスキップ（警告 + status=skipped-dependency イベント）
    depends: ClassVar[dict] = {
        "adapters": ["onebot11"],   # 依存するアダプタ（プラットフォーム名で）
        "modules": ["TranslateEngine"],  # 依存するモジュール（登録名で）
    }
    # ソフトな依存：存在しない場合は起動に影響しない；モジュールのロード/アンロード時にコールバックを受け取る（オプション機能モード）
    optional_modules: ClassVar[list] = ["TranslateEngine"]
```

- **起動順序**：モジュールの硬い依存を宣言したアダプタは**モジュールの初期化完了後に起動される**。
- **ソフトな依存の通知**：`optional_modules`（またはモジュールの硬い依存）に含まれるモジュールがロードされたときに `on_dependency_ready(module_name)` を呼び出す；アンロードされたときに `on_dependency_lost(module_name)` を呼び出す（デフォルトでは空実装、オーバーライド可能）——遅いロードやホットリロードの状況に対応：

```python
async def on_dependency_ready(self, module_name):
    """ソフトな依存モジュールが準備完了：対応するオプション機能を有効化"""
    if module_name == "TranslateEngine":
        self._translate = self.sdk.TranslateEngine

async def on_dependency_lost(self, module_name):
    """ソフトな依存モジュールが失われた：機能をロールバック"""
    if module_name == "TranslateEngine":
        self._translate = None
```

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要です。

## `__init__` 注意事項

アダプター開発において `__init__` のオーバーライドが必要となる層は 3 つあります。各層での正しい実装について以下に記載します。

### 1. BaseAdapter 層（大半の場合オーバーライド不要）

`BaseAdapter.__init__(self, sdk=None)` は `Send` / `Request` ファクトリインスタンスの作成を担当し、以下の自動処理を行います。

- `sdk` パラメータを受け取り、`self.sdk`、`self.logger` を設定
- `ConfigClass` が宣言されている場合、`self.cfg` 経由でグローバル設定をリアルタイムで読み込めるようにする
- `AccountConfigClass` が宣言されている場合、`self.accounts` 経由でマルチアカウント設定をリアルタイムで読み込めるようにする

**大半の場合は `__init__` のオーバーライドは不要**で、`ConfigClass` を宣言するだけで済みます。

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # 宣言するとフレームワークが自動的に設定を管理
    
    async def start(self):
        cfg = self.cfg  # タイプ安全性を保ちつつリアルタイムで読み込み
        ...
```

確かにカスタム初期化が必要な場合は、`super().__init__(sdk)` を呼び出すだけで済みます。

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # sdk を渡す
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

### 2. Send 内部クラス（大半の場合オーバーライド不要）

`SendDSL.__init__` はメソッドチェーン呼び出し時の状態引き継ぎ（ターゲットタイプ、ターゲットID、アカウント等）を担当します。**大半の場合、`__init__` のオーバーライドは不要で、メソッド（`Raw_ob12`、`Text` 等）だけをオーバーライドすれば十分です。**

確かに必要な場合（例: プラットフォーム固有の状態を初期化する場合）、**すべてのパラメータを順伝播する（透過的に渡す）** 必要があります。

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        # 引数：adapter, target_type, target_id, account_id
        def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
            super().__init__(adapter, target_type, target_id, account_id)  # ← すべて透過する必要あり
            self._my_state = None  # プラットフォーム固有の初期化
```

**なぜすべて透過しなければならないのでしょうか？** メソッドチェーンの各ステップは `self.__class__(...)` を使って新しいインスタンスを作成します。

```python
adapter.Send.To("user", "123")               # → Send(adapter, "user", "123", None)
adapter.Send.To("user", "123").Using("bot1")  # → Send(adapter, "user", "123", "bot1")
```

`__init__` のシグネチャが一致しない、または `super()` が呼ばれていない場合、メソッドチェーンは中断します。

### 3. Request 内部クラス（大半の場合オーバーライド不要）

Send と同様です。引数は `adapter`, `request_id`, `account_id` です。

```python
class MyAdapter(BaseAdapter):
    class Request(RequestDSL):
        # 引数：adapter, request_id, account_id
        def __init__(self, adapter, request_id=None, account_id=None):
            super().__init__(adapter, request_id, account_id)  # ← すべて透過する必要あり
            self._my_state = None  # プラットフォーム固有の初期化
```

### まとめ

| 層 | いつオーバーライドするか | 必要な処理 |
|------|------------|-----------|
| **BaseAdapter** | カスタム初期化ロジックが必要な時 | `super().__init__(sdk)` （sdk パラメータを渡す） |
| **Send 内部クラス** | 送信関連の状態を初期化する時 | `super().__init__(adapter, target_type, target_id, account_id)` |
| **Request 内部クラス** | リクエスト関連の状態を初期化する時 | `super().__init__(adapter, request_id, account_id)` |
| 3 層すべて | 大半の場合 | **ConfigClass を宣言すればよく、`__init__` に触れない** |

### 9. 接続情報とルート発見

アダプターがルートを登録すると、フレームワークはすべてのルート情報を記録します。ユーザーは以下の API を通じてアダプターの接続アドレスを確認できます。

```python
from ErisPulse import sdk

# アダプターの完全な接続情報を取得
info = sdk.adapter.get_connection_info("myplatform")
# {
#   "platform": "myplatform",
#   "status": "started",
#   "connection": {
#     "base_url": "http://localhost:8080",
#     "http_routes": [
#       {"path": "/myplatform/webhook", "method": "POST",
#        "url": "http://localhost:8080/myplatform/webhook"}
#     ],
#     "websocket_routes": [
#       {"path": "/myplatform/ws",
#        "url": "ws://localhost:8080/myplatform/ws"}
#     ]
#   }
# }

# すべての名前空間（アダプター/モジュール）のルートを一覧表示
namespaces = sdk.router.list_namespaces()
# {"myplatform": {"http": ["/myplatform/webhook"], "websocket": ["/myplatform/ws"]}}

# 名前空間の完全な接続 URL を取得
urls = sdk.router.get_module_urls("myplatform")
# {"base_url": "http://localhost:8080", "http": [...], "websocket": [...]}

# 名前空間の詳細なルート情報を取得
routes = sdk.router.get_module_routes("myplatform")
# {"http": [{"path": "/myplatform/webhook", "methods": ["POST"]}],
#  "websocket": [{"path": "/myplatform/ws", "auth": false}]}
```

> **ヒント**：`get_connection_info()` が返す情報は、WebUI などにユーザーへ提示するのに適しています。ユーザーがプラットフォーム側のコールバックアドレスや WebSocket 接続アドレスを設定する際に役立ちます。ルート登録時の `module_name` は、アダプターが ErisPulse で登録した `platform` 名前と完全に一致している必要があります。そうしないと、ルート発見が正しく関連付けられません。

### 10. SSE (Server-Sent Events) サポート

ErisPulse はサーバーに依存しない SSE サポートを組み込んでおり、モジュールやアダプターは `@sdk.router.sse()` を使って SSE エンドポイントを登録できます。

#### 基本的な使用法

```python
import asyncio
from ErisPulse import sdk

@sdk.router.sse("MyModule", "/events")
async def event_stream(sse):
    """SSE イベントをプッシュする"""
    count = 0
    while not sse.closed:
        await sse.send({"count": count}, event="update")
        count += 1
        await asyncio.sleep(1)
```

#### リクエストパラメータの使用

ハンドラは `request` パラメータを宣言してクライアントリクエスト情報にアクセスできます。

```python
@sdk.router.sse("MyModule", "/events")
async def event_stream(request, sse):
    token = request.query_params.get("token")
    if not validate_token(token):
        await sse.close()
        return

    while not sse.closed:
        data = await fetch_data(token)
        await sse.send(data)
        await asyncio.sleep(5)
```

#### SseEmitter API

| メソッド | 説明 |
|------|------|
| `sse.send(data, event=None, id=None, retry=None)` | SSE イベントを送信。str 以外の data は自動的に JSON シリアライズされます |
| `sse.close()` | SSE 接続を適切に閉じます（安全に呼び出せ、何度呼んでも問題ありません） |
| `sse.closed` | 接続が既に閉じられているかどうか |
| `sse.request` | 基底のリクエストオブジェクト（query params、headers を読むのに使用可能） |

#### RouteGroup での使用

```python
api = sdk.router.group("MyModule", "/api", version="1")

@api.sse("/events")
async def events(sse):
    await sse.send({"msg": "hello"})
```

#### ルート発見

SSE ルートはルート発見 API に自動的に表示されます。

```python
# list_namespaces は "sse" キーを含みます
sdk.router.list_namespaces()
# {"MyModule": {"http": [...], "websocket": [...], "sse": ["/MyModule/events"]}}

# get_module_routes は streaming: true をマークします
sdk.router.get_module_routes("MyModule")
# {"http": [...], "websocket": [...], "sse": [{"path": "/MyModule/events", "streaming": true}]}

# get_module_urls は完全な URL を生成します
sdk.router.get_module_urls("MyModule")
# {"sse": [{"path": "/MyModule/events", "url": "http://localhost:8080/MyModule/events"}]}
```

> **サーバーに依存しない設計**：`SseEmitter` はコールバックを介して基礎となる HTTP フレームワークと疎結合になっています。フレームワークは `register_sse()` と `@sse` デコレータを統一された登録エントリポイントとして提供しており、アダプターは直接基礎となる HTTP フレームワークに依存せずに SSE エンドポイントを実装できます。

## 次のステップ

- [アダプタの核心概念](core-concepts.md) - アダプタのアーキテクチャについて学ぶ
- [SendDSL の詳細](send-dsl.md) - メッセージ送信について学ぶ
- [コンバータの実装](converter.md) - イベント変換について学ぶ
- [アダプタのベストプラクティス](best-practices.md) - 高品質なアダプタの開発