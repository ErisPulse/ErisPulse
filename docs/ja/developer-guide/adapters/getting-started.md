# アダプター開発入門

このガイドは、ErisPulse アダプターの開発を開始し、新しいメッセージ プラットフォームに接続するのに役立ちます。

## アダプターの概要

### アダプターとは何か

アダプターは ErisPulse と各メッセージ プラットフォーム間のブリッジであり、以下の責務を負います：

1. **正方向変換**：プラットフォーム イベントを受け取り、OneBot12 標準形式に変換（Converter）
2. **逆方向変換**：OneBot12 メッセージ セグメントをプラットフォーム API コールに変換（`Raw_ob12`）
3. 管理とプラットフォームの接続（WebSocket/WebHook）
4. 統一された SendDSL メッセージ送信インターフェースを提供

### アダプターのアーキテクチャ

```
正方向変換（受信）                        反向変換（送信）
─────────────                        ─────────────
プラットフォーム イベント                    モジュールが構築するメッセージ
    ↓                                    ↓
Converter.convert()               Send.Raw_ob12()
    ↓                                    ↓
OneBot12 標準イベント                    プラットフォームネイティブ API コール
    ↓                                    ↓
イベントシステム                         標準応答フォーマット
    ↓
モジュールの処理
```

## ディレクトリ構造

標準的なアダプター パッケージ構造：

```
MyAdapter/
├── pyproject.toml          # プロジェクト設定
├── README.md               # プロジェクト説明
├── LICENSE                 # ライセンス
└── MyAdapter/
    ├── __init__.py          # パッケージエントリ
    ├── Core.py               # アダプターのメインクラス
    └── Converter.py          # イベント変換器
```

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
description = "MyAdapterプラットフォームアダプター"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

dependencies = [
    "ErisPulse>=2.4.0"  # ErisPulse には aiohttp が組み込まれているため、通常は個別の依存関係は不要です
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points."erispulse.adapter"]
"MyAdapter" = "MyAdapter:MyAdapter"
```

### 3. アダプターのメインクラスの作成

フレームワークは `ConfigClass` / `AccountConfigClass` の宣言的構成管理を提供しており、アダプターは単に構成クラスを宣言するだけで、自動的に構成の読み込み、検証、および構成テンプレートの生成が行われます。

```python
# MyAdapter/Core.py
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.runtime.config_schema import AdapterConfig

@dataclass
class MyAdapterConfig(AdapterConfig):
    """MyAdapter 配置"""
    api_endpoint: str = field(
        default="https://api.example.com",
        metadata={
            "description": "API アドレス",
            "required": False,
            "webui": {"widget": "text", "group": "connection", "order": 1},
        },
    )
    token: str = field(
        default="",
        metadata={
            "description": "プラットフォーム トークン",
            "required": True,
            "secret": True,
            "webui": {"widget": "password", "group": "basic", "order": 2},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # 構成クラスを宣言し、フレームワークが自動管理

    # __init__ をオーバーライドする必要はありません！フレームワークが自動処理：
    # - self.sdk / self.logger が自動設定される
    # - self.config が自動的に構成をロードされる
    # - self.Send / self.Request が自動的に初期化される

    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
```

> ⚠️ **`__init__` について**：新しいバージョンでは `BaseAdapter.__init__(self, sdk=None)` は SDK リファレンス、ログ初期化、構成のロードを自動的に処理します。ほとんどのアダプターでは **`__init__` をオーバーライドする必要はありません**。詳細は [__init__ の注意点](#init-注意事项) を参照してください。

> ⚠️ **`super().__init__()` について**：`BaseAdapter.__init__()` は `Send` と `Request` のファクトリインスタンスの作成を担当します。これを忘れると、すべてのメッセージ送信とリクエスト操作で `AttributeError` が発生します。詳細は [__init__ の注意点](#init-注意事项) を参照してください。

### 4. 必須メソッドの実装

```python
class MyAdapter(BaseAdapter):
    # ... __init__ のコード ...
    
    async def start(self):
        """アダプターの起動（実装必須）"""
        # WebSocket または WebHook ルートの登録
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler
        )
        self.logger.info("アダプターが起動しました")
    
    async def shutdown(self):
        """アダプターのシャットダウン（実装必須）"""
        router.unregister_websocket(
            module_name="myplatform",
            path="/ws"
        )
        # 接続とリソースのクリーンアップ
        self.logger.info("アダプターがシャットダウンしました")
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォーム API の呼び出し（実装必須）"""
        raise NotImplementedError("call_api の実装が必要です")
```

#### メタイベントの主動送信

アダプターはフレームワークが Bot のオンライン状態を追跡できるように、メタイベントを主動的に送信する必要があります。`emit_meta()` を 1 行で実現できます：

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

> Bot の状態管理とメタイベントの詳細については、[アダプターのベストプラクティス - Bot 状態管理](best-practices.md#bot-状态管理与-meta-事件) を参照してください。

### 5. Send クラスの実装

`At`/`AtAll`/`Reply` デコレータはフレームワークの SendDSL ベースクラスに実装されているため、アダプターは `Raw_ob12` と具体的な送信メソッドを実装するだけで済みます。

フレームワークは2つの重要な補助メソッドを提供します：
- `self._apply_modifiers(message)` — メッセージセグメントに `At`/`AtAll`/`Reply` デコレータを自動的にマージ
- `self.send_context` — 送信コンテキスト辞書（`target_type`、`target_id`、`account_id`）を取得

```python
import asyncio

class MyAdapter(BaseAdapter):
    # ... 他のコード ...
    
    class Send(BaseAdapter.Send):
        
        def Raw_ob12(self, message, **kwargs):
            """
            OneBot12 形式メッセージの送信（実装必須）

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
        
        def Text(self, text: str):
            """テキストメッセージを送信"""
            return self.Raw_ob12([
                {"type": "text", "data": {"text": text}}
            ])
        
        def Image(self, file):
            """画像メッセージを送信"""
            return self.Raw_ob12([
                {"type": "image", "data": {"file": file}}
            ])
```

**メディアクラス送信メソッド（Image/Video/File）の実装のポイント：**

- `file` パラメータは `bytes` バイナリデータと `str` URL の両方をサポートする必要があります
- URL が渡された場合は、まずファイルをダウンロードしてからプラットフォームにアップロードする必要があります
- プラットフォームは通常、送信インターフェースを呼び出す前にアップロードインターフェースを呼び出してファイル識別子を取得する必要があります

**`__getattr__` マジックメソッド：**

- メソッド名の大文字小文字を区別しないように実装（`Text`、`text`、`TEXT` すべて呼び出し可能）
- 未定義のメソッドはエラーを返すのではなく、ヒントメッセージを返すべきです

**`Raw_ob12` メソッド：**

- OneBot12 標準メッセージ形式をプラットフォーム形式に変換して送信
- `self._apply_modifiers(message)` を使用して `At`/`AtAll`/`Reply` デコレータを自動的に処理
- `**self.send_context` を使用して送信先情報とアカウント情報を渡す

### 6. 変換器の実装

```python
# MyAdapter/Converter.py
import time
import uuid

class MyPlatformConverter:
    def convert(self, raw_event):
        """プラットフォームネイティブイベントを OneBot12 標準形式に変換"""
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
        """イベントタイプの変換"""
        type_map = {
            "message": "message",
            "notice": "notice"
        }
        return type_map.get(event_type, "unknown")
    
    def _convert_detail_type(self, raw_event):
        """詳細タイプの変換"""
        return "private"  # 簡略化された例
```

### 7. Request クラスの実装（リクエスト操作）

プラットフォームが Bot が意思決定を行う必要のある要求（フレンドリクエスト、グループ招待など）をサポートしている場合、`Request` 内部クラスを実装できます：

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    # ... Send と他のコード ...

    class Request(RequestDSL):
        """リクエスト操作の実装（フレンドリクエスト、グループ招待など）"""

        def accept(self, **kwargs):
            """リクエストを承認"""
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
            """リクエストを拒否"""
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

モジュール開発者が使用する方法：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Event から便利なメソッド経由
    await event.approve()
    # またはアダプターを直接操作
    await adapter.myplatform.Request("req_id").accept()
```

> プラットフォームがリクエスト操作をサポートしていない場合は、`Request` 内部クラスを実装する必要はありません。ベースクラスはデフォルトで `retcode=10002`（サポートされていない操作）を返します。詳細は [リクエスト操作仕様](../../standards/request-action-spec.md) を参照してください。

### 8. パッケージエントリの作成

```python
# MyAdapter/__init__.py
from .Core import MyAdapter
```

## `__init__` の注意点

アダプター開発には `__init__` のオーバーライドに関与する3つのレイヤーがあります。各レイヤーの正しい方法は以下の通りです。

### 1. BaseAdapter レイヤー（`super().__init__()` の呼び出しが必須）

`BaseAdapter.__init__(self, sdk=None)` は**`Send` と `Request` のファクトリインスタンスの作成**を担当します。アダプターに独自の `__init__` がある場合、必ず親クラスの初期化を呼び出す必要があります：

```python
class MyAdapter(BaseAdapter):
    def __init__(self, sdk=None):
        super().__init__(sdk)  # ← 必須！さもないと Send / Request は初期化されません
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

**呼び出しを忘れた場合の結果**：`adapter.Send.To(...)` と `adapter.Request(...)` の両方が `AttributeError` を返します。

### 2. Send 内部クラス（ほとんどの場合、オーバーライド不要）

`SendDSL.__init__` はチェイン呼び出しの状態の受け渡し（ターゲットタイプ、ターゲットID、アカウントなど）を担当します。**ほとんどの場合、`__init__` をオーバーライドする必要はなく、メソッドだけをオーバーライドする**（`Raw_ob12`、`Text` など）必要があります。

実際に必要な場合（プラットフォーム固有の状態の初期化など）、**すべてのパラメータを透過する**必要があります：

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        # パラメータ：adapter, target_type, target_id, account_id
        def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
            super().__init__(adapter, target_type, target_id, account_id)  # ← パラメータを透過する必要があります
            self._my_state = None  # プラットフォーム固有の初期化
```

**なぜパラメータを透過する必要があるのか**：チェイン呼び出しの各ステップは `self.__class__(...)` を使用して新しいインスタンスを作成します：

```python
adapter.Send.To("user", "123")               # → Send(adapter, "user", "123", None)
adapter.Send.To("user", "123").Using("bot1")  # → Send(adapter, "user", "123", "bot1")
```

もし `__init__` のシグネチャが一致しないか `super()` が呼ばれていなければ、チェイン呼び出しは中断します。

### 3. Request 内部クラス（ほとんどの場合、オーバーライド不要）

Send と同様です。パラメータは `adapter`, `request_id`, `account_id` です：

```python
class MyAdapter(BaseAdapter):
    class Request(RequestDSL):
        # パラメータ：adapter, request_id, account_id
        def __init__(self, adapter, request_id=None, account_id=None):
            super().__init__(adapter, request_id, account_id)  # ← パラメータを透過する必要があります
            self._my_state = None  # プラットフォーム固有の初期化
```

### まとめ

| レイヤー | いつオーバーライドするか | 必須なこと |
|------|------------|-----------|
| **BaseAdapter** | アダプターの状態を初期化する必要がある場合 | `super().__init__(sdk)` （引数あり） |
| **Send 内部クラス** | 送信関連の状態を初期化する必要がある場合 | `super().__init__(adapter, target_type, target_id, account_id)` |
| **Request 内部クラス** | リクエスト関連の状態を初期化する必要がある場合 | `super().__init__(adapter, request_id, account_id)` |
| 3つのレイヤー | ほとんどの場合 | **メソッドだけをオーバーライドし、`__init__` には触れない** |

## 次のステップ

- [アダプターの核心概念](core-concepts.md) - アダプターのアーキテクチャを理解する
- [SendDSL の詳細](send-dsl.md) - メッセージ送信を学ぶ
- [変換器の実装](converter.md) - イベント変換を理解する
- [アダプターのベストプラクティス](best-practices.md) - 高品質なアダプターの開発