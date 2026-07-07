# アダプターの核となる概念

ErisPulse アダプターの核となる概念を理解することは、アダプターを開発する基礎となります。

## アダプターのアーキテクチャ

### コンポーネントの関係

```
正方向の変換（受信方向）                           反方向の変換（送信方向）
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ プラットフォームネイティブイベント     │                        │ モジュール構築メッセージ     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │  アダプター (MyAdapter) │   │                  │
│  Converter       │   │ ┌──────────────┐ │   │ Send.Raw_ob12()  │
│  (イベントコンバーター)    │──→│ │              │ │   │ (反方向変換のエントリポイント) │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ プラットフォームAPI呼び出し    │
                       │ OneBot12 標準イベント │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ 標準応答フォーマット     │
                       │  イベントシステム         │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ モジュール (イベント処理)  │
                       └──────────────────┘
```

**コアの対称性**：
- **正方向の変換**（Converter）：プラットフォームネイティブイベント → OneBot12 標準イベント、元のデータは `{platform}_raw` に保持されます
- **反方向の変換**（Raw_ob12）：OneBot12 メッセージセグメント → プラットフォームAPI呼び出し、標準応答フォーマットを返します

## AdapterManager アダプター管理者

`AdapterManager` は ErisPulse アダプターシステムのコアコンポーネントであり、すべてのプラットフォームアダプターの登録、起動、停止、イベント配信を管理します。

### 核心機能

- **アダプター登録**：複数のプラットフォームアダプターを登録および管理します
- **ライフサイクル管理**：アダプターの起動と停止を制御します
- **イベント配信**：OneBot12 標準イベントとプラットフォームネイティブイベントを配信します
- **設定管理**：アダプターの有効化/無効化状態を管理します
- **ミドルウェアサポート**：OneBot12 イベントミドルウェアをサポートします

### 基本的な使用

```python
from ErisPulse import sdk

# アダプターの登録（通常は Loader によって自動的に行われます）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# すべてのアダプターを起動
await sdk.adapter.startup()

# 指定されたアダプターを起動
await sdk.adapter.startup(["myplatform"])
# すべてのアダプターを起動
await sdk.adapter.startup()

# アダプターのインスタンスを取得
my_adapter = sdk.adapter.get("myplatform")
# またはプロパティ経由でアクセス
my_adapter = sdk.adapter.myplatform

# すべてのアダプターを停止
await sdk.adapter.shutdown()
```

### 起動と停止

#### アダプターの起動

```python
# 登録されたすべてのアダプターを起動
await sdk.adapter.startup()

# 指定されたプラットフォームを起動
await sdk.adapter.startup(["platform1", "platform2"])
```

**起動プロセス：**

1. `adapter.start` ライフサイクルイベントを送出
2. `adapter.status.change` イベントを送出（starting）
3. 各アダプターを並列に起動
4. 起動に失敗した場合、自動的に再試行（指数バックオフ戦略）
5. 起動成功後、`adapter.status.change` イベントを送出（started）

**再試行メカニズム：**

- 最初の4回の再試行：60秒、10分、30分、60分
- 5回目以降：3時間の固定間隔

#### アダプターの停止

```python
# すべてのアダプターを停止
await sdk.adapter.shutdown()
```

**停止プロセス：**

1. `adapter.stop` ライフサイクルイベントを送出
2. すべてのアダプターの `shutdown()` メソッドを呼び出し
3. ルーター（ルーティング）サーバーを停止
4. イベントハンドラーをクリア
5. `adapter.stopped` ライフサイクルイベントを送出

### 設定管理

#### プラットフォームの状態を確認

```python
# プラットフォームが登録されているか確認
exists = sdk.adapter.exists("myplatform")

# プラットフォームが有効か確認
enabled = sdk.adapter.is_enabled("myplatform")

# in 演算子を使用
if "myplatform" in sdk.adapter:
    print("プラットフォームが存在し、有効です")
```

#### プラットフォームのリスト

```python
# 登録されているすべてのプラットフォームをリスト
platforms = sdk.adapter.list_registered()

# すべてのプラットフォームとその状態をリスト
status_dict = sdk.adapter.list_items()
# 返り値: {"platform1": true, "platform2": false, ...}

# 有効なプラットフォームのリストを取得
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### イベント監視

#### OneBot12 標準イベント

```python
from ErisPulse import sdk

# すべてのプラットフォームの標準メッセージイベントを監視
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"OneBot12メッセージを受信: {data}")

# 特定のプラットフォームの標準メッセージイベントを監視
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"myplatformメッセージを受信: {data}")

# すべてのイベントを監視
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"イベントを受信: {data.get('type')}")
```

#### プラットフォームネイティブイベント

```python
# 特定のプラットフォームのネイティブイベントを監視
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"ネイティブイベントを受信: {data}")

# すべてのプラットフォームのネイティブイベントを監視（ワイルドカード）
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"ネイティブイベントを受信: {data}")
```

#### イベント配信メカニズム

`adapter.emit(event_data)` を呼び出したとき：

1. **ミドルウェア処理**：まずすべての OneBot12 ミドルウェアを実行
2. **標準イベント配信**：一致する OneBot12 イベントハンドラーに配信
3. **ネイティブイベント配信**：元のデータが存在する場合、ネイティブイベントハンドラーに配信

**マッチングルール：**

- 正確一致：`@sdk.adapter.on("message")` は `message` イベントにのみ一致
- ワイルドカード：`@sdk.adapter.on("*")` はすべてのイベントに一致
- プラットフォームフィルタ：`platform="myplatform"` は指定されたプラットフォームのイベントのみ配信

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
    """イベントフィルタミドルウェア"""
    # 処理不要なイベントをフィルタリング
    if data.get("type") == "notice":
        return None  # Noneを返した場合、ミドルウェアチェーンはその値を無視し、元のデータを渡し続けます
    return data  # データを返して続行する必要があります
```

#### ミドルウェアの実行順序

ミドルウェアは登録順に実行されます。後で登録されたミドルウェアが先に実行されます。

> **注意**：ミドルウェアが `None` を返した場合（`return data` を忘れた場合など）、フレームワークはその戻り値を無視し、元のデータをそのまま渡し続けます。同時に warning レベルのログを出力します。これにより、単一のミドルウェアのエラーでイベントチェーン全体が中断するのを防ぎます。

```python
# 登録順序
sdk.adapter.middleware(middleware1)  # 最後に実行
sdk.adapter.middleware(middleware2)  # 中間で実行
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
# プロパティ名でアクセス（大文字小文字を区別しません）
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
    """アダプター設定（宣言後にフレームワークが自動的に管理します）"""
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
    # - self.cfg（型安全な設定インスタンス、リアルタイムで読み取り）
    # - self.Send, self.Request
    
    async def start(self):
        """アダプターを起動する（実装が必要）"""
        cfg = self.cfg  # 自動読み込みの型安全設定
        pass
    
    async def shutdown(self):
        """アダプターを停止する（実装が必要）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォームAPIを呼び出す（実装が必要）"""
        pass
```

### 設定管理

フレームワークは宣言型の設定管理を提供し、dataclass で設定構造を定義し、フレームワークが自動的にロード、検証、テンプレート生成を処理します。

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
        cfg = self.cfg  # 型安全、リアルタイムで読み取り
        if not cfg.token:
            raise ValueError("Tokenが設定されていません")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### マルチアカウント設定

`BotAccountConfig` 基底クラスは `enabled` および `name` フィールドを提供します。大部分のアダプターはプラットフォームプロトコルまたはログイン応答から自動的に bot_id を取得でき、イベント変換時にアカウント設定に注入します。：

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BotAccountConfig

# 大部分のアダプター：bot_id は実行時に自動取得、設定不要
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Token"},
        "required": True,
    })

# ログイン時に bot_id を取得できない場合、ユーザーが設定で入力できるようにする
@dataclass
class YunhuBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={
        "description": {"i18n": "yunhu.bot_id", "default": "ボットID"},
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

#### metadata 仕様

フィールドの metadata は、TOML コメント生成と WebUI フォームレンダリングの両方をサポートします：

```python
metadata = {
    "description": str | dict,  # フィールドの説明（i18n対応）
    "required": bool,         # 必須（検証 + WebUI 必須マーク）
    "secret": bool,           # 敏感（WebUI では *** として表示、ログではマスキング）
    "ui": {                   # WebUI コントロール設定（古い名前 "webui" でも互換）
        "widget": str,        # コントロールタイプ: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # グループ: "basic" | "advanced" | "connection" など
        "order": int,         # ソート順（数値が小さいほど上位）
        "options": list,      # select コントロールのオプション [{label, value}]、label は i18n 対応
        "placeholder": str | dict,  # 入力プレースホルダー（i18n対応）
    },
    "extra": dict,            # 追加拡張フィールド（schema にそのまま透過）
}
```

すべてのユーザーに見えるテキストフィールドは i18n をサポートし、統一的な `{"i18n": "key", "default": "テキスト"}` 形式を使用します。純粋な文字列はそのまま透過されます（後方互換性）。対応する i18n フィールド：

| フィールド | 場所 | 説明 |
|------|------|------|
| `description` | field metadata | フィールドの説明 |
| `options[].label` | `ui.options` | select コントロールのオプションラベル |
| `placeholder` | `ui.placeholder` | 入力プレースホルダー |
| `group_labels` | `_schema_meta` | グループ表示名（Dashboard セクションタイトル） |

i18n を使用する場合、翻訳キーを i18n システムに事前に登録する必要があります（詳細は [i18n ドキュメント](../../advanced/i18n.md#フィールドの多言語化)）。

**description / placeholder / options label** の例：

```python
token: str = field(
    default="",
    metadata={
        "description": {"i18n": "my_adapter.token", "default": "Bot Token"},
        "ui": {
            "widget": "text",
            "placeholder": {"i18n": "my_adapter.token.ph", "default": "Tokenを入力してください"},
        },
    },
)
mode: str = field(
    default="a",
    metadata={
        "description": {"i18n": "my_adapter.mode", "default": "モード"},
        "ui": {
            "widget": "select",
            "options": [
                {"label": {"i18n": "my_adapter.mode.a", "default": "オプションA"}, "value": "a"},
                {"label": "純粋な文字列ラベル", "value": "b"},  # 純粋な文字列はそのまま透過
            ],
        },
    },
)
```

**group_labels** の例（設定クラス定義後に宣言）：

```python
MyConfig._schema_meta = {
    "group_labels": {
        "basic": {"i18n": "my_adapter.group.basic", "default": "基本設定"},
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "高度な設定"},
    }
}
```

フレームワークの `resolve_config_schema()` は現在の言語に基づいて上記すべてのフィールドの i18n キーを自動的に解決します。`get_config_schema()` は i18n 辞書をそのまま透過し、フロントエンド側で解決します。

#### アカウントの解決

マルチアカウントアダプターは `_resolve_account()` を使用してターゲットアカウントを自動的に解決できます：

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: アカウント名, account: 設定インスタンス
```

解決戦略：アカウント名の一致 → `bot_id` フィールドの一致 → その他の str フィールドの一致 → 最初の有効なアカウント。

#### 設定のホット更新

サブクラスは `on_config_update()` をオーバーライドして設定変更に応答できます：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Tokenが更新されました。再接続します")
```

### 初期化プロセス

フレームワークは `BaseAdapter.__init__(self, sdk=None)` で以下の処理を自動的に行います：

1. **SDK参照**：`self.sdk`、`self.logger` を設定
2. **Send/Request ファクトリ**：`self.Send` と `self.Request` を作成
3. **設定テンプレート**：`ConfigClass` を宣言している場合、デフォルトの設定テンプレートを自動生成（初回）
4. **アカウントテンプレート**：`AccountConfigClass` を宣言している場合、デフォルトのアカウントテンプレートを自動生成（初回）

設定は `self.cfg` / `self.accounts` を介してリアルタイムで読み取り（毎回アクセスするたびに設定ストアから最新値を取得）。`self.config` は `self.cfg` の互換エイリアスとして引き続き使用できます。

大部分のアダプターは `__init__` をオーバーライドする必要はありません。カスタム初期化が必要な場合は：

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
        """Send ネストクラス、BaseAdapter.Send を継承"""
        pass
```

### 使用可能なプロパティ

`Send` クラスは呼び出し時に以下のプロパティが自動的に設定されます：

| プロパティ | 説明 | 設定方法 |
|-----|------|---------|
| `_target_id` | ターゲットID | `To(id)` または `To(type, id)` |
| `_target_type` | ターゲットタイプ | `To(type, id)` |
| `_target_to` | 簡易ターゲットID | `To(id)` |
| `_account_id` | 送信アカウントID | `Using(account_id)` |
| `_adapter` | アダプターインスタンス | 自動設定 |
| `_at_user_ids` | @ユーザーリスト | `At(user_id)` |
| `_reply_message_id` | 返信メッセージID | `Reply(message_id)` |
| `_at_all` | 全体@するか | `AtAll()` |

> **推奨**：`self.send_context` プロパティを一度に `target_type`、`target_id`、`account_id` を取得する方が、インスタンス変数に直接アクセスするよりも明確です。

### フレームワーク補助メソッド

| メソッド/プロパティ | 説明 |
|-----------|------|
| `self._apply_modifiers(message)` | At/AtAll/Reply 修飾子の状態をメッセージセグメントリストにマージ |
| `self.send_context` | `{target_type, target_id, account_id}` 辞書を返す |

### 基本的なメソッド

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """推奨実装方法"""
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

### 変換プロセス

```
プラットフォーム元のイベント
    ↓
Converter.convert()
    ↓
OneBot12 標準イベント
```

### 必須フィールド

すべての変換後のイベントには以下が含まれている必要があります：

```python
{
    "id": "イベントの一意な識別子",
    "time": 1234567890,           # 10桁の Unix タイムスタンプ
    "type": "message/notice/request/meta",
    "detail_type": "イベントの詳細タイプ",
    "platform": "プラットフォーム名",
    "self": {
        "platform": "プラットフォーム名",
        "user_id": "ボットID"     # bot_id と一致している必要があります
    },
    "{platform}_raw": {...},       # 元のデータ（必須）
    "{platform}_raw_type": "..."    # 元のタイプ（必須）
}
```

### コンバーターの例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """プラットフォームネイティブイベントを OneBot12 標準フォーマットに変換"""
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

> **ルート情報の照会**：アダプターが登録したルート（HTTP、WebSocket、SSE）は、`sdk.adapter.get_connection_info(platform)` と `sdk.router.get_module_urls(module_name)` を使用して完全な接続アドレス（`base_url` + パスを含む）を照会できます。詳細は [アダプター開発入門 - 接続情報とルートの検出](getting-started.md#9-接続情報とルートの検出) および [SSE サポート](getting-started.md#10-sse-server-sent-events-サポート) を参照してください。

## API 応答の標準

フレームワークは `make_response()` と `make_error()` メソッドを使用して標準化された応答を構築し、応答辞書を手動で構築する必要はありません。

### 成功応答

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

### 手動で応答を構築する（旧方式も互換性維持）

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

## マルチアカウントサポート

### 宣言型設定（推奨）

`AccountConfigClass` を使用して設定クラスを宣言すると、フレームワークはマルチアカウントの読み込み、検証、テンプレート生成を自動的に管理します：

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BotAccountConfig

@dataclass
class MyBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={"description": "ボットID", "required": True})
    token: str = field(default="", metadata={"description": "Token", "required": True, "secret": True})

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            self.logger.info(f"アカウント {name} を起動: {account.bot_id}")
            await self._connect(name, account)
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # account.token, account.bot_id などのフィールドを使用
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

### 特定のアカウントから送信

```python
# Using メソッドを使用してアカウントを指定
my_adapter = adapter.get("myplatform")

# イベント内の self.user_id（推奨、最も汎用的）
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# アカウント名経由
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### self.user_id と Using の関係

フレームワークのイベント応答メカニズムは、イベントの `self` フィールドから `account_id`（優先順位：高い順）または `user_id` を自動的に抽出し、`Using` パラメータとして渡します。アダプターデベッパーは、Converter 内の `self.user_id` の値が `_resolve_account()` で正しく一致するようにする必要があります。

**フレームワーク内部の動作**（`Event._get_adapter_and_target`）：

```python
# フレームワークによる bot_id の抽出ロジック
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# bot_id が空でない場合のみ Using を呼び出す
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **重要なポイント**：アダプターが単一の Bot 設定のみを使用していても、Converter が `self.user_id` を正しく設定していれば、フレームワークはそれを `Using` パラメータとして渡します。アダプターは、`self.user_id` が `AccountConfigClass` 内の識別フィールド（例：`bot_id`）と一致していることを確認し、`_resolve_account()` が正しいアカウントに一致させます。`self.user_id` が空の場合、フレームワークは `Using` を呼び出さず、その場合 `call_api` に渡される `account_id` は `None` となり、`_resolve_account(None)` は最初の有効なアカウントを返します。

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
                    self.logger.warning(f"接続失敗、{wait_time}秒後に再試行")
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### API エラーハンドリング

```python
async def call_api(self, endpoint: str, **params):
    try:
        # SDK 内蔵クライアントの使用を推奨
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
        self.logger.error(f"リクエストタイムアウト: {endpoint}")
        return self._error_response("リクエストタイムアウト", 32000)
    except ClientError as e:
        self.logger.error(f"ネットワークエラー: {e}")
        return self._error_response("ネットワークリクエスト失敗", 33000)
    except Exception as e:
        self.logger.error(f"不明なエラー: {e}")
        return self._error_response(str(e), 34000)
```

> **後方互換性**：直接 `aiohttp.ClientSession` を使用する旧アダプターのコードは影響を受けません。依然として `aiohttp.ClientError` をキャッチできます。両方の方法は共存可能です。新規コードでは `sdk.client` + ErisPulse 例外体系を使用することを推奨します。

## Bot ステータス管理

AdapterManager には Bot ステータス追跡システムが組み込まれており、すべての登録済み Bot のオンラインステータス、アクティブ時間、メタ情報を自動的に維持します。

### 自動発見メカニズム

アダプターが `adapter.emit()` を使用してイベントを送信すると、フレームワークはイベント内の `self` フィールドを自動的にチェックします：

- **meta イベント**：`detail_type` に基づいて対応する操作を実行（connect 登録/オフラインマーキング/heartbeat アクティビティ更新）
- **通常のイベント**（message/notice/request）：自動的に Bot を発見し、アクティビティ時間を更新します

```python
# self フィールドを含むすべてのイベントが自動発見をトリガーします
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123" は自動的に登録されます（初出の場合）かつアクティビティ時間が更新されます
```

### Meta イベントタイプ

| `detail_type` | 説明 | フレームワークの動作 |
|---|---|---|
| `connect` | Bot 接続 | Bot を登録し、`adapter.bot.online` ライフサイクルイベントをトリガー |
| `disconnect` | Bot 切断 | Bot をオフラインとしてマークし、`adapter.bot.offline` ライフサイクルイベントをトリガー |
| `heartbeat` | Bot ハートビート | Bot のアクティビティ時間とメタ情報を更新 |

### アダプターによる Meta イベントの送信

`emit_meta()` を1行で使用して meta イベントを送信できます：

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # connect イベントを1行で送信
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="私のロボット")

    async def _on_bot_disconnect(self, bot_id: str):
        await self.emit_meta("disconnect", bot_id)
```

手動で構築することもサポートされています（旧方式も互換性維持）：

```python
await self.adapter.emit({
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": bot_id}
})
```

### `self` フィールドの拡張情報

`self` フィールドは必須の `platform` と `user_id` に加え、以下のオプショナルフィールドをサポートします：

| フィールド | 説明 |
|---|---|
| `user_name` | Bot ユーザー名 |
| `nickname` | Bot ニックネーム |
| `avatar` | Bot アバター URL |
| `account_id` | マルチアカウント識別子 |

### Bot ステータス照会

```python
from ErisPulse import sdk

# 単一の Bot 情報を取得
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# すべての Bot をリスト
all_bots = sdk.adapter.list_bots()

# 指定されたプラットフォームの Bot をリスト
platform_bots = sdk.adapter.list_bots("myplatform")

# Bot がオンラインかチェック
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# 完全なステータスサマリーを取得（WebUI 表示に適しています）
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

### Bot ライフサイクルを監視

```python
from ErisPulse import sdk

@sdk.lifecycle.on("adapter.bot.online")
async def on_bot_online(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Bot オンライン: {platform}/{bot_id}")

@sdk.lifecycle.on("adapter.bot.offline")
async def on_bot_offline(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Bot オフライン: {platform}/{bot_id}")
```

## 関連ドキュメント

- [アダプター開発入門](getting-started.md) - 最初のアダプターを作成
- [SendDSL の詳細](send-dsl.md) - メッセージ送信を学習
- [アダプターのベストプラクティス](best-practices.md) - 高品質なアダプターの開発