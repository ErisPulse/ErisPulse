# アダプターの核心概念

ErisPulse アダプターの核心概念を理解することは、アダプターの開発の基礎となります。

## アダプターのアーキテクチャ

### コンポーネントの関係

```
正の変換（受信方向）                           負の変換（送信方向）
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ プラットフォームネイティブイベント     │                        │ モジュール構築メッセージ     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │ アダプター │   │                  │
│  Converter       │   │ ┌──────────────┐ │   │ Send.Raw_ob12()  │
│  (イベントコンバーター)    │──→│ │              │ │   │ (負の変換の入り口)   │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ プラットフォーム API コール    │
                       │ OneBot12 標準イベント │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ 標準レスポンスフォーマット     │
                       │ イベントシステム         │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ モジュール (イベント処理)  │
                       └──────────────────┘
```

**コアの対称性**：
- **正の変換**（Converter）：プラットフォームネイティブイベント → OneBot12 標準イベント、元のデータは `{platform}_raw` に保持されます
- **負の変換**（Raw_ob12）：OneBot12 メッセージセグメント → プラットフォーム API コール、標準レスポンスフォーマットを返します

## AdapterManager アダプター管理クラス

`AdapterManager` は ErisPulse アダプターシステムのコアコンポーネントであり、すべてのプラットフォームアダプターの登録、起動、停止、イベント配布を管理する責任を持ちます。

### コア機能

- **アダプター登録**：複数のプラットフォームアダプターの登録と管理
- **ライフサイクル管理**：アダプターの起動と停止の制御
- **イベント配布**：OneBot12 標準イベントとプラットフォームネイティブイベントの配布
- **設定管理**：アダプターの有効/無効状態の管理
- **ミドルウェア対応**：OneBot12 イベントミドルウェアの対応

### 基本的な使用方法

```python
from ErisPulse import sdk

# アダプターの登録（通常は Loader が自動的に行います）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# すべてのアダプターの起動
await sdk.adapter.startup()

# 指定されたアダプターの起動
await sdk.adapter.startup(["myplatform"])
# すべてのアダプターの起動
await sdk.adapter.startup()

# アダプターインスタンスの取得
my_adapter = sdk.adapter.get("myplatform")
# または属性経由でアクセス
my_adapter = sdk.adapter.myplatform

# すべてのアダプターの停止
await sdk.adapter.shutdown()
```

### 起動と停止

#### アダプターの起動

```python
# 登録済みのすべてのアダプターを起動
await sdk.adapter.startup()

# 指定されたプラットフォームを起動
await sdk.adapter.startup(["platform1", "platform2"])
```

**起動フロー：**

1. `adapter.start` ライフサイクルイベントを送信
2. `adapter.status.change` イベントを送信（starting）
3. 各アダプターを並列で起動
4. 起動に失敗した場合、自動的に再試行する（指数バックオフ戦略）
5. 起動成功後、`adapter.status.change` イベントを送信（started）

**再試行メカニズム：**

- 初回4回：60秒、10分、30分、60分
- 5回目以降：3時間固定間隔

#### アダプターの停止

```python
# すべてのアダプターを停止
await sdk.adapter.shutdown()
```

**停止フロー：**

1. `adapter.stop` ライフサイクルイベントを送信
2. すべてのアダプターの `shutdown()` メソッドを呼び出し
3. ルーター サーバーを閉じる
4. イベントハンドラーをクリア
5. `adapter.stopped` ライフサイクルイベントを送信

### 設定管理

#### プラットフォームの状態確認

```python
# プラットフォームが登録されているか確認
exists = sdk.adapter.exists("myplatform")

# プラットフォームが有効か確認
enabled = sdk.adapter.is_enabled("myplatform")

# in 演算子を使用
if "myplatform" in sdk.adapter:
    print("プラットフォームが存在し、有効です")
```

#### プラットフォームのリスト表示

```python
# 登録されたすべてのプラットフォームをリスト表示
platforms = sdk.adapter.list_registered()

# すべてのプラットフォームとその状態をリスト表示
status_dict = sdk.adapter.list_items()
# 戻り値: {"platform1": true, "platform2": false, ...}

# 有効なプラットフォームのリストを取得
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### イベントリスニング

#### OneBot12 標準イベント

```python
from ErisPulse import sdk

# すべてのプラットフォームの標準メッセージイベントを監視
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"OneBot12メッセージを受信しました: {data}")

# 特定のプラットフォームの標準メッセージイベントを監視
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"myplatform メッセージを受信しました: {data}")

# すべてのイベントを監視
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"イベントを受信しました: {data.get('type')}")
```

#### プラットフォームネイティブイベント

```python
# 特定のプラットフォームのネイティブイベントを監視
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"ネイティブイベントを受信しました: {data}")

# すべてのプラットフォームのネイティブイベントを監視（ワイルドカード）
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"ネイティブイベントを受信しました: {data}")
```

#### イベント配布メカニズム

`adapter.emit(event_data)` を呼び出すとき：

1. **ミドルウェア処理**：まずすべての OneBot12 ミドルウェアを実行
2. **標準イベント配布**：マッチする OneBot12 イベントハンドラーへ配布
3. **ネイティブイベント配布**：元のデータがある場合、ネイティブイベントハンドラーへ配布

**マッチングルール：**

- 精密マッチ：`@sdk.adapter.on("message")` は `message` イベントのみにマッチ
- ワイルドカード：`@sdk.adapter.on("*")` はすべてのイベントにマッチ
- プラットフォームフィルタリング：`platform="myplatform"` は指定されたプラットフォームのイベントのみを配布

### ミドルウェア

#### ミドルウェアの追加

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """ログ記録ミドルウェア"""
    print(f"イベントを処理中: {data.get('type')}")
    return data  # データを返す必要があります

@sdk.adapter.middleware
async def filter_middleware(data):
    """イベントフィルターミドルウェア"""
    # 不要なイベントをフィルタリング
    if data.get("type") == "notice":
        return None  # None を返す場合、ミドルウェアチェーンはその戻り値を無視し、元のデータをそのまま続けて渡します
    return data  # データを返して継続する必要があります
```

#### ミドルウェア実行順序

ミドルウェアは登録順に実行されます。後で登録されたミドルウェアが先に実行されます。

> **注意**：ミドルウェアが `None` を返した場合（`return data` を忘れたなど）、フレームワークはその戻り値を無視し、元のデータをそのまま続けて渡し、同時に警告レベルのログを出力します。これにより、単一のミドルウェアの失敗によってイベントチェーン全体が中断されることを防ぎます。

```python
# 登録順序
sdk.adapter.middleware(middleware1)  # 最後に実行
sdk.adapter.middleware(middleware2)  # 中間に実行
sdk.adapter.middleware(middleware3)  # 最先に実行

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
# プロパティ名経由でアクセス（大文字小文字を区別しません）
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## BaseAdapter 基底クラス

### 基本的な構造

```python
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.runtime.config_schema import BaseConfig, BotAccountConfig

@dataclass
class MyConfig(BaseConfig):
    """アダプター設定（宣言後、フレームワークが自動的に管理します）"""
    token: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_adapter.token", "default": "Bot Token"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 1},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig  # 設定クラスを宣言
    
    # __init__ をオーバーライドする必要はありません。フレームワークが自動的に処理します：
    # - self.sdk, self.logger
    # - self.cfg（型安全な設定インスタンス、即時読み込み）
    # - self.Send, self.Request
    
    async def start(self):
        """アダプターを起動する（実装が必要です）"""
        cfg = self.cfg  # 自動的にロードされた型安全な設定
        pass
    
    async def shutdown(self):
        """アダプターを停止する（実装が必要です）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォーム API を呼び出す（実装が必要です）"""
        pass
```

### 設定管理

フレームワークは宣言型の設定管理を提供し、dataclass で設定構造を定義することで、フレームワークが自動的にロード、検証、テンプレート生成を処理します。

#### 単一アカウント設定

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BaseConfig

@dataclass
class TelegramConfig(BaseConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "telegram.token", "default": "Bot Token"},
        "required": True,
        "secret": True,
        "ui": {"widget": "password", "group": "basic", "order": 1},
    })
    proxy: str = field(default="", metadata={
        "description": {"i18n": "telegram.proxy", "default": "プロキシアドレス"},
        "ui": {"widget": "text", "group": "advanced", "order": 10},
    })

class TelegramAdapter(BaseAdapter):
    ConfigClass = TelegramConfig
    
    async def start(self):
        cfg = self.cfg  # 型安全、即時読み込み
        if not cfg.token:
            raise ValueError("Token が設定されていません")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### 複数アカウント設定

`BotAccountConfig` 基底クラスは `enabled` と `name` フィールドを提供します。ほとんどのアダプターはプラットフォームプロトコルまたはログインレスポンスから bot_id を自動的に取得し、イベント変換時にアカウント設定に注入できます。：

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BotAccountConfig

# ほとんどのアダプター：bot_id は実行時に自動的に取得されるため、設定は不要です
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Token"},
        "required": True,
    })

# ログイン時に bot_id を取得できない場合、ユーザーが設定で入力できるようにします
@dataclass
class YunhuBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={
        "description": {"i18n": "yunhu.bot_id", "default": "ロボットID"},
        "required": True,
    })
    token: str = field(default="", metadata={
        "description": {"i18n": "yunhu.token", "default": "Token"},
        "required": True,
    })

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            user_id = await self._login(name, account)
            await self.emit_meta("connect", user_id)
```

#### metadata の契約

フィールドの metadata は、TOML のコメント生成と WebUI フォームレンダリングの両方に役立ちます：

```python
metadata = {
    "description": str | dict,  # フィールドの説明（i18n をサポート）
    "required": bool,         # 必須（検証 + WebUI 必須マーカー）
    "secret": bool,           # 敏感（WebUI では *** として表示、ログではマスキング）
    "ui": {                   # WebUI コントロール設定（旧名 "webui" も互換）
        "widget": str,        # コントロールタイプ: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # グループ: "basic" | "advanced" | "connection" など
        "order": int,         # ソート重み（数値が小さいほど優先度が高い）
        "options": list,      # select コントロールのオプション [{label, value}]
        "placeholder": str,   # 入力フィールドのプレースホルダー
    },
    "extra": dict,            # 追加拡張フィールド（schema にそのまま渡されます）
}
```

`description` は2つの形式をサポートします：

- **通常の文字列**（後方互換性のため）：`"Bot Token"`
- **i18n ディクショナリ**（推奨、多言語をサポート）：`{"i18n": "my_adapter.token", "default": "Bot Token"}`

i18n ディクショナリを使用する場合、翻訳キーを i18n システムに事前に登録する必要があります（詳細は [i18n ドキュメント](../../advanced/i18n.md#フィールドの多言語化) を参照してください）。

#### アカウントの解決

複数アカウントアダプターは `_resolve_account()` を使用してターゲットアカウントを自動的に解決できます：

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: アカウント名, account: 設定インスタンス
```

解決戦略：アカウント名一致 → `bot_id` フィールド一致 → その他の str フィールド一致 → 最初に有効なアカウント。

#### 設定のホットアップデート

サブクラスは `on_config_update()` をオーバーライドして設定変更に対応できます：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Token が更新されました。再接続します")
```

### 初期化プロセス

フレームワークは `BaseAdapter.__init__(self, sdk=None)` 内で以下の作業を自動的に実行します：

1. **SDK 参照**：`self.sdk`、`self.logger` を設定
2. **Send/Request ファクトリ**：`self.Send` と `self.Request` を作成
3. **設定テンプレート**：`ConfigClass` を宣言した場合、デフォルト設定テンプレートを自動的に生成（初回のみ）
4. **アカウントテンプレート**：`AccountConfigClass` を宣言した場合、デフォルトアカウントテンプレートを自動的に生成（初回のみ）

設定は `self.cfg` / `self.accounts` 経由で即時読み込みされます（アクセスごとに設定ストアから最新値を取得）。`self.config` は `self.cfg` の互換エイリアスとして引き続き使用できます。

ほとんどのアダプターで `__init__` をオーバーライドする必要はありません。独自の初期化が必要な場合は：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # sdk を渡す
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## Send メッセージ送信 DSL

### 継承関係

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        """Send ネストクラス。BaseAdapter.Send から継承"""
        pass
```

### 使用可能な属性

`Send` クラスは呼び出し時に以下の属性を自動的に設定します：

| プロパティ | 説明 | 設定方法 |
|-----|------|---------|
| `_target_id` | ターゲットID | `To(id)` または `To(type, id)` |
| `_target_type` | ターゲットタイプ | `To(type, id)` |
| `_target_to` | 簡略化されたターゲットID | `To(id)` |
| `_account_id` | 送信アカウントID | `Using(account_id)` |
| `_adapter` | アダプターインスタンス | 自動設定 |
| `_at_user_ids` | @ユーザーリスト | `At(user_id)` |
| `_reply_message_id` | 返信メッセージID | `Reply(message_id)` |
| `_at_all` | 全員に@するか | `AtAll()` |

> **推奨**：`self.send_context` プロパティを使用して一度に `target_type`、`target_id`、`account_id` を取得する方が、インスタンス変数に直接アクセスするよりも明確です。

### フレームワーク補助メソッド

| メソッド/プロパティ | 説明 |
|-----------|------|
| `self._apply_modifiers(message)` | At/AtAll/Reply 修飾子の状態をメッセージセグメントリストにマージします |
| `self.send_context` | `{target_type, target_id, account_id}` ディクショナリを返します |

### 基本的なメソッド

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

### チェーン修飾子メソッド

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

すべての変換後のイベントには、以下が含まれている必要があります：

```python
{
    "id": "イベントの一意な識別子",
    "time": 1234567890,           # 10桁の Unix タイムスタンプ
    "type": "message/notice/request/meta",
    "detail_type": "イベントの詳細タイプ",
    "platform": "プラットフォーム名",
    "self": {
        "platform": "プラットフォーム名",
        "user_id": "ロボットID"     # bot_id と一致している必要があります
    },
    "{platform}_raw": {...},       # 元のデータ（必須）
    "{platform}_raw_type": "..."    # 元のタイプ（必須）
}
```

### コンバーター例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """プラットフォームネイティブイベントを OneBot12 標準フォーマットに変換します"""
        if not isinstance(raw_event, dict):
            return None
        
        # イベントIDを生成
        event_id = raw_event.get("event_id") or str(uuid.uuid4())
        
        # タイムスタンプを変換
        timestamp = raw_event.get("timestamp")
        if timestamp and timestamp > 10**12:
            timestamp = int(timestamp / 1000)
        else:
            timestamp = int(timestamp) if timestamp else int(time.time())
        
        # イベントタイプを変換
        event_type = self._convert_type(raw_event.get("type"))
        detail_type = self._convert_detail_type(raw_event)
        
        # 標準イベントを構築
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
class MyAdapter(BaseAdapter):
    async def start(self):
        """WebSocket ルートを登録"""
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler,
            auth_handler=self._auth_handler
        )
    
    async def _ws_handler(self, websocket):
        """WebSocket 接続ハンドラー"""
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
    
    async def _auth_handler(self, websocket) -> bool:
        """WebSocket 認証"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook 接続

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """WebHook ルートを登録"""
        router.register_http_route(
            module_name="myplatform",
            path="/webhook",
            handler=self._webhook_handler,
            methods=["POST"]
        )
    
    async def _webhook_handler(self, request):
        """WebHook リクエストハンドラー"""
        data = await request.json()
        onebot_event = self.convert(data)
        if onebot_event:
            await self.adapter.emit(onebot_event)
        return {"status": "ok"}
```

> **ルート情報のクエリ**：アダプターが登録したルート（HTTP、WebSocket、SSE）は、`sdk.adapter.get_connection_info(platform)` と `sdk.router.get_module_urls(module_name)` で完全な接続アドレス（`base_url` + パスを含む）を照会できます。詳細は [アダプター開発入門 - 接続情報とルートの検出](getting-started.md#9-接続情報とルートの検出) と [SSE サポート](getting-started.md#10-sse-server-sent-events-サポート) を参照してください。

## API レスポンス標準

フレームワークは `make_response()` と `make_error()` メソッドで標準化されたレスポンスを構築するため、レスポンスディクショナリを手動で構築する必要はありません。

### 成功レスポンス

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        return self.make_response(
            data=raw_response.get("data"),
            message_id=raw_response.get("data", {}).get("message_id", ""),
            raw=raw_response,
        )
    except Exception as e:
        return self.make_error(message=str(e), raw=None)
```

### 手動レスポンス構築（旧方式も互換性維持）

```python
async def call_api(self, endpoint: str, **params):
    return {
        "status": "ok",
        "retcode": 0,
        "data": {...},
        "message_id": "msg_id",
        "message": "",
        "myplatform_raw": raw_response
    }
```

## 複数アカウント対応

### 宣言型設定（推奨）

`AccountConfigClass` を使用して設定クラスを宣言すると、フレームワークは自動的に複数アカウントのロード、検証、テンプレート生成を管理します：

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BotAccountConfig

@dataclass
class MyBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={"description": "Bot ID", "required": True})
    token: str = field(default="", metadata={"description": "Token", "required": True, "secret": True})

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            self.logger.info(f"アカウント {name} を起動中: {account.bot_id}")
            await self._connect(name, account)
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # account.token や account.bot_id などのフィールドを使用
```

### アカウント設定ファイル

```toml
[MyAdapter.accounts.account1]
bot_id = "bot_001"
token = "token1"
enabled = true

[MyAdapter.accounts.account2]
bot_id = "bot_002"
token = "token2"
enabled = true
```

### 指定されたアカウントからの送信

```python
# Using メソッドを使用してアカウントを指定
my_adapter = adapter.get("myplatform")

# イベント内の self.user_id 経由（推奨、最も汎用的）
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# アカウント名経由
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### self.user_id と Using の関係

フレームワークのイベント応答メカニズムは、イベントの `self` フィールドから自動的に `account_id`（優先）または `user_id` を抽出し、`Using` 引数として渡します。アダプター開発者は、Converter 内の `self.user_id` の値が `_resolve_account()` で正しく一致するように確保する必要があります。

**フレームワーク内部動作**（`Event._get_adapter_and_target`）：

```python
# フレームワークが bot_id を抽出するロジック
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# bot_id が空でない場合のみ Using を呼び出す
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **重要なポイント**：アダプターが単一の Bot 設定のみを使用している場合でも、Converter で `self.user_id` が正しく設定されていれば、フレームワークはそれを `Using` 引数として渡します。アダプターは、`self.user_id` が `AccountConfigClass` 内の識別フィールド（例: `bot_id`）と一致していることを確認し、`_resolve_account()` が正しいアカウントに一致できるようにする必要があります。`self.user_id` が空の場合、フレームワークは `Using` を呼び出さず、この場合 `call_api` に渡される `account_id` は `None` となり、`_resolve_account(None)` は最初に有効なアカウントを返します。

## エラーハンドリング

### 接続の再試行

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
                    self.logger.warning(f"接続に失敗しました。{wait_time}秒後に再試行します")
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### API エラーハンドリング

```python
async def call_api(self, endpoint: str, **params):
    try:
        # SDK 内蔵クライアントを使用することを推奨
        from ErisPulse.Core import client
        from ErisPulse.Core.Bases.errors import ClientError, ClientTimeoutError
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            max_retries=2,
        )
        response = await resp.json()
        return self._standardize_response(response)
    except ClientTimeoutError:
        self.logger.error(f"リクエストがタイムアウトしました: {endpoint}")
        return self._error_response("リクエストがタイムアウトしました", 32000)
    except ClientError as e:
        self.logger.error(f"ネットワークエラー: {e}")
        return self._error_response("ネットワークリクエストに失敗しました", 33000)
    except Exception as e:
        self.logger.error(f"未知のエラー: {e}")
        return self._error_response(str(e), 34000)
```

> **後方互換性**：直接 `aiohttp.ClientSession` を使用する旧アダプターコードは影響を受けず、依然として `aiohttp.ClientError` をキャッチできます。2つの方式は共存できます。新しいコードでは `sdk.client` + ErisPulse 異常体系を使用することを推奨します。

## Bot の状態管理

AdapterManager には Bot の状態追跡システムが組み込まれており、登録されているすべての Bot のオンライン状態、アクティビティ時間、メタ情報を自動的に維持します。

### 自動発見メカニズム

アダプターが `adapter.emit()` でイベントを送信すると、フレームワークはイベント内の `self` フィールドを自動的にチェックします：

- **meta イベント**：`detail_type` に基づいて対応する操作を実行します（connect 登録/切断によるオフラインマーカー/heartbeat によるアクティビティ時間更新）
- **通常のイベント**（message/notice/request）：自動的に Bot を発見し、アクティビティ時間を更新します

```python
# self フィールドを含むすべてのイベントが自動発見をトリガーします
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123" は（初出の場合）自動的に登録され、アクティビティ時間が更新されます
```

### Meta イベントタイプ

| `detail_type` | 説明 | フレームワークの動作 |
|---|---|---|
| `connect` | Bot 接続 | Bot を登録し、`adapter.bot.online` ライフサイクルイベントをトリガー |
| `disconnect` | Bot 切断 | Bot をオフラインとしてマークし、`adapter.bot.offline` ライフサイクルイベントをトリガー |
| `heartbeat` | Bot ハートビート | Bot のアクティビティ時間とメタ情報を更新 |

### アダプターからの Meta イベント送信

`emit_meta()` を1行で使用して meta イベントを送信できます：

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # 1行で connect イベントを送信
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="我的机器人")

    async def _on_bot_disconnect(self, bot_id: str):
        await self.emit_meta("disconnect", bot_id)
```

手動で構築することも可能（旧方式も互換性維持）：

```python
await self.adapter.emit({
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": bot_id}
})
```

### `self` フィールドの拡張情報

`self` フィールドには必須の `platform` と `user_id` に加え、以下のオプションフィールドがサポートされます：

| フィールド | 説明 |
|---|---|
| `user_name` | Bot ユーザー名 |
| `nickname` | Bot のニックネーム |
| `avatar` | Bot のアバター URL |
| `account_id` | 複数アカウントの識別子 |

### Bot の状態照会

```python
from ErisPulse import sdk

# 単一の Bot 情報を取得
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# すべての Bot をリスト表示
all_bots = sdk.adapter.list_bots()

# 指定されたプラットフォームの Bot をリスト表示
platform_bots = sdk.adapter.list_bots("myplatform")

# Bot がオンラインかどうかを確認
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# 完全な状態サマリーを取得（WebUI 表示に適しています）
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

### Bot のライフサイクルを監視

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

## 関連ドキュメント

- [アダプター開発入門](getting-started.md) - 最初のアダプターを作成する
- [SendDSL の詳細](send-dsl.md) - メッセージ送信を学ぶ
- [アダプターのベストプラクティス](best-practices.md) - 高品質なアダプターを開発する