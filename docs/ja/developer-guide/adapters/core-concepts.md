# アダプターの核心概念

ErisPulse アダプターの核心概念を理解することは、アダプター開発の基礎となります。

## アダプターのアーキテクチャ

### コンポーネントの関係

```
正方向変換（受信方向）                           逆方向変換（送信方向）
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ プラットフォーム  │                        │ モジュールによる   │
│ ネイティブイベント│                        │ メッセージ構築     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │ 适配器 (MyAdapter) │   │                  │
│  Converter       │   │ ┌──────────────┐ │   │ Send.Raw_ob12()  │
│  (事件转换器)    │──→│ │              │ │   │ (反向转换入口)   │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ プラットフォーム  │
                       │ OneBot12         │    │ API 呼び出し     │
                       │ 標準イベント     │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ 標準レスポンス   │
                       │ イベントシステム │    │     形式         │
                       └────────┬─────────┘    └──────────────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ モジュール        │
                       │ (イベント処理)   │
                       └──────────────────┘
```

**コアの対称性**：
- **正方向変換**（Converter）：プラットフォームネイティブイベント → OneBot12 標準イベント、元のデータは `{platform}_raw` に保持されます
- **逆方向変換**（Raw_ob12）：OneBot12 消息段 → プラットフォーム API 呼び出し、標準のレスポンス形式を返します

## AdapterManager アダプター管理マネージャー

`AdapterManager` は、ErisPulse アダプターシステムのコアコンポーネントであり、すべてのプラットフォームアダプターの登録、起動、終了、およびイベントのディスパッチを管理します。

### コア機能

- **アダプター登録**：複数のプラットフォームアダプターを登録および管理します
- **ライフサイクル管理**：アダプターの起動と終了を制御します
- **イベントディスパッチ**：OneBot12 標準イベントとプラットフォームネイティブイベントをディスパッチします
- **設定管理**：アダプターの有効/無効状態を管理します
- **ミドルウェアサポート**：OneBot12 イベントミドルウェアをサポートします

### 基本的な使用

```python
from ErisPulse import sdk

# アダプターの登録（通常はLoaderにより自動的に完了します）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# すべてのアダプターを起動
await sdk.adapter.startup()

# 指定したアダプターを起動
await sdk.adapter.startup(["myplatform"])
# すべてのアダプターを起動
await sdk.adapter.startup()

# アダプターインスタンスの取得
my_adapter = sdk.adapter.get("myplatform")
# またはプロパティ経由でアクセス
my_adapter = sdk.adapter.myplatform

# すべてのアダプターを終了
await sdk.adapter.shutdown()
```

### 起動と終了

#### アダプターの起動

```python
# 登録済みのすべてのアダプターを起動
await sdk.adapter.startup()

# 指定したプラットフォームを起動
await sdk.adapter.startup(["platform1", "platform2"])
```

**起動フロー：**

1. `adapter.start` ライフサイクルイベントを送信します
2. `adapter.status.change` イベントを送信します（starting）
3. 各アダプターを並行して起動します
4. 起動失敗時、自動リトライ（指数バックオフ戦略）
5. 起動成功後、`adapter.status.change` イベントを送信します（started）

**リトライメカニズム：**

- 最初の4回のリトライ：60秒、10分、30分、60分
- 5回目以降：3時間の固定間隔

#### アダプターの終了

```python
# すべてのアダプターを終了
await sdk.adapter.shutdown()
```

**終了フロー：**

1. `adapter.stop` ライフサイクルイベントを送信します
2. すべてのアダプターの `shutdown()` メソッドを呼び出します
3. ルーティングサーバーを閉じます
4. イベントプロセッサをクリアします
5. `adapter.stopped` ライフサイクルイベントを送信します

### 設定管理

#### プラットフォーム状態の確認

```python
# プラットフォームが登録されているか確認
exists = sdk.adapter.exists("myplatform")

# プラットフォームが有効か確認
enabled = sdk.adapter.is_enabled("myplatform")

# in 演算子を使用
if "myplatform" in sdk.adapter:
    print("プラットフォームは存在し、有効です")
```

#### プラットフォームの一覧

```python
# 登録済みのすべてのプラットフォームを一覧表示
platforms = sdk.adapter.list_registered()

# すべてのプラットフォームとその状態を一覧表示
status_dict = sdk.adapter.list_items()
# 返り値: {"platform1": true, "platform2": false, ...}

# 有効なプラットフォームのリストを取得
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### イベントリスニング

#### OneBot12 標準イベント

```python
from ErisPulse import sdk

# すべてのプラットフォームの標準メッセージイベントをリッスン
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"OneBot12メッセージを受信: {data}")

# 特定のプラットフォームの標準メッセージイベントをリッスン
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"myplatform メッセージを受信: {data}")

# すべてのイベントをリッスン
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"イベントを受信: {data.get('type')}")
```

#### プラットフォームネイティブイベント

```python
# 特定のプラットフォームのネイティブイベントをリッスン
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"ネイティブイベントを受信: {data}")

# すべてのプラットフォームのネイティブイベントをリッスン（ワイルドカード）
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"ネイティブイベントを受信: {data}")
```

#### イベントディスパッチメカニズム

`adapter.emit(event_data)` を呼び出すと：

1. **ミドルウェア処理**：すべての OneBot12 ミドルウェアを実行します
2. **標準イベントディスパッチ**：一致する OneBot12 イベントハンドラにディスパッチします
3. **ネイティブイベントディスパッチ**：元のデータが存在する場合、ネイティブイベントハンドラにディスパッチします

**一致ルール：**

- 精密一致：`@sdk.adapter.on("message")` は `message` イベントのみに一致します
- ワイルドカード：`@sdk.adapter.on("*")` はすべてのイベントに一致します
- プラットフォームフィルタ：`platform="myplatform"` は指定されたプラットフォームのイベントのみにディスパッチします

### ミドルウェア

#### ミドルウェアの追加

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """ログ記録ミドルウェア"""
    print(f"イベントを処理: {data.get('type')}")
    return data  # 必須でデータを返す

@sdk.adapter.middleware
async def filter_middleware(data):
    """イベントフィルタミドルウェア"""
    # 不要なイベントをフィルタリング
    if data.get("type") == "notice":
        return None  # None を返す場合、ミドルウェアチェーンはその返り値を無視し、元のデータを保持して次の処理に渡します
    return data  # 必須でデータを返して次の処理に渡します
```

#### ミドルウェアの実行順序

ミドルウェアは登録順に実行され、後から登録されたミドルウェアが先に実行されます。

> **注意**：ミドルウェアが `None` を返した場合（例：`return data` を忘れている場合）、フレームワークはその返り値を無視して元のデータを保持し、次の処理に渡します。また、warning レベルのログを出力します。これにより、1つのミドルウェアのミスがイベントチェーン全体を中断することはありません。

```python
# 登録順
sdk.adapter.middleware(middleware1)  # 最後に実行
sdk.adapter.middleware(middleware2)  # 中間に実行
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
# プロパティ名を用いたアクセス（大文字小文字を区別しない）
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## BaseAdapter 基底クラス

### 基本構造

```python
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.runtime.config_schema import AdapterConfig, BotAccountConfig

@dataclass
class MyConfig(AdapterConfig):
    """适配器配置（声明后框架自动管理）"""
    token: str = field(
        default="",
        metadata={
            "description": "Bot Token",
            "required": True,
            "secret": True,
            "webui": {"widget": "password", "group": "basic", "order": 1},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig  # 声明配置类
    
    # 无需覆写 __init__，框架自动处理：
    # - self.sdk, self.logger
    # - self.config（类型安全的配置实例）
    # - self.Send, self.Request
    
    async def start(self):
        """启动适配器（必须实现）"""
        cfg = self.config  # 自动加载的类型安全配置
        pass
    
    async def shutdown(self):
        """关闭适配器（必须实现）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """调用平台 API（必须实现）"""
        pass
```

### 配置管理

フレームワークは宣言的設定管理を提供し、dataclass で設定構造を定義して、フレームワークが自動的にロード、検証、テンプレート生成を処理します。

#### 単一アカウント設定

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import AdapterConfig

@dataclass
class TelegramConfig(AdapterConfig):
    token: str = field(default="", metadata={
        "description": "Bot Token",
        "required": True,
        "secret": True,
        "webui": {"widget": "password", "group": "basic", "order": 1},
    })
    proxy: str = field(default="", metadata={
        "description": "代理地址",
        "webui": {"widget": "text", "group": "advanced", "order": 10},
    })

class TelegramAdapter(BaseAdapter):
    ConfigClass = TelegramConfig
    
    async def start(self):
        cfg = self.config  # 类型安全，自动加载
        if not cfg.token:
            raise ValueError("未配置 Token")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### 多アカウント設定

```python
from ErisPulse.runtime.config_schema import BotAccountConfig

@dataclass
class YunhuBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={
        "description": "机器人ID",
        "required": True,
        "webui": {"widget": "text", "group": "basic", "order": 1},
    })
    token: str = field(default="", metadata={
        "description": "机器人Token",
        "required": True,
        "secret": True,
        "webui": {"widget": "password", "group": "basic", "order": 2},
    })

class YunhuAdapter(BaseAdapter):
    AccountConfigClass = YunhuBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            await self._connect(name, account)
            await self.emit_meta("connect", account.bot_id, user_name=account.name)
```

#### metadata 約定

フィールドの metadata は、TOML コメント生成と WebUI フォームレンダリングの両方に使用されます：

```python
metadata = {
    "description": str,       # 字段描述（TOML注释 + WebUI label）
    "required": bool,         # 是否必填（校验 + WebUI 必填标记）
    "secret": bool,           # 是否敏感（WebUI 显示为 ***，日志中脱敏）
    "webui": {
        "widget": str,        # 控件类型: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # 分组: "basic" | "advanced" | "connection" 等
        "order": int,         # 排序权重（越小越靠前）
        "options": list,      # select 控件的可选项 [{label, value}]
        "placeholder": str,   # 输入框占位符
    }
}
```

#### 账户解析

多账户适配器可使用 `_resolve_account()` 自动解析目标账户：

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: 账户名, account: 配置实例
```

解析策略：账户名匹配 → `bot_id` 字段匹配 → 其他 str 字段匹配 → 第一个启用账户。

#### 配置热更新

子类可覆写 `on_config_update()` 响应配置变更：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Token 已更新，将重新连接")
```

### 初期化プロセス

フレームワークは `BaseAdapter.__init__(self, sdk=None)` で自動的に以下の処理を行います：

1. **SDK参照**：`self.sdk`、`self.logger` を設定します
2. **Send/Requestファクトリ**：`self.Send` と `self.Request` を作成します
3. **設定のロード**：`ConfigClass` が宣言されている場合、`self.config` に自動的にロードします
4. **アカウントのロード**：`AccountConfigClass` が宣言されている場合、`self.accounts` に自動的にロードします

大多数のアダプターでは `__init__` をオーバーライドする必要はありません。カスタム初期化が必要な場合は：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # sdk を渡す
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## Send 消息送信 DSL

### 継承関係

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        """Send 嵌套类，继承自 BaseAdapter.Send"""
        pass
```

### 利用可能な属性

`Send` クラスは呼び出し時に自動的に以下の属性を設定します：

| 属性 | 説明 | 設定方法 |
|-----|------|---------|
| `_target_id` | 目标ID | `To(id)` または `To(type, id)` |
| `_target_type` | 目标类型 | `To(type, id)` |
| `_target_to` | 簡略化されたターゲットID | `To(id)` |
| `_account_id` | 送信アカウントID | `Using(account_id)` |
| `_adapter` | アダプターインスタンス | 自動設定 |
| `_at_user_ids` | @ユーザーIDリスト | `At(user_id)` |
| `_reply_message_id` | 返信するメッセージID | `Reply(message_id)` |
| `_at_all` | 全員に@するか | `AtAll()` |

> **推奨**：`self.send_context` 属性を使って `target_type`、`target_id`、`account_id` を一度に取得する方が、直接インスタンス変数にアクセスするよりも明確です。

### フレームワーク補助メソッド

| メソッド/属性 | 説明 |
|-----------|------|
| `self._apply_modifiers(message)` | At/AtAll/Reply 修飾子の状態をメッセージセグメントリストにマージします |
| `self.send_context` | `{target_type, target_id, account_id}` ディクショナリを返します |

### 基本メソッド

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """推荐实现方式"""
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

### チェーン修飾メソッド

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

変換後のイベントは以下のフィールドを含む必要があります：

```python
{
    "id": "事件唯一标识",
    "time": 1234567890,           # 10位 Unix 时间戳
    "type": "message/notice/request/meta",
    "detail_type": "事件详细类型",
    "platform": "平台名称",
    "self": {
        "platform": "平台名称",
        "user_id": "机器人ID"
    },
    "{platform}_raw": {...},       # 原始数据（必须）
    "{platform}_raw_type": "..."    # 原始类型（必须）
}
```

### コンバーターの例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """将平台原生事件转换为 OneBot12 标准格式"""
        if not isinstance(raw_event, dict):
            return None
        
        # 生成事件 ID
        event_id = raw_event.get("event_id") or str(uuid.uuid4())
        
        # 转换时间戳
        timestamp = raw_event.get("timestamp")
        if timestamp and timestamp > 10**12:
            timestamp = int(timestamp / 1000)
        else:
            timestamp = int(timestamp) if timestamp else int(time.time())
        
        # 转换事件类型
        event_type = self._convert_type(raw_event.get("type"))
        detail_type = self._convert_detail_type(raw_event)
        
        # 构建标准事件
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
        """注册 WebSocket 路由"""
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler,
            auth_handler=self._auth_handler
        )
    
    async def _ws_handler(self, websocket):
        """WebSocket 连接处理器"""
        self.connection = websocket
        
        try:
            while True:
                data = await websocket.receive_text()
                onebot_event = self.convert(data)
                if onebot_event:
                    await self.adapter.emit(onebot_event)
        except WebSocketDisconnect:
            self.logger.info("连接已断开")
        finally:
            self.connection = None
    
    async def _auth_handler(self, websocket) -> bool:
        """WebSocket 认证"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook 接続

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """注册 WebHook 路由"""
        router.register_http_route(
            module_name="myplatform",
            path="/webhook",
            handler=self._webhook_handler,
            methods=["POST"]
        )
    
    async def _webhook_handler(self, request):
        """WebHook 请求处理器"""
        data = await request.json()
        onebot_event = self.convert(data)
        if onebot_event:
            await self.adapter.emit(onebot_event)
        return {"status": "ok"}
```

> **路由信息查询**：适配器注册的路由（HTTP、WebSocket、SSE）可以通过 `sdk.adapter.get_connection_info(platform)` 和 `sdk.router.get_module_urls(module_name)` 查询完整连接地址（包含 `base_url` + 路径）。详见 [适配器开发入门 - 连接信息与路由发现](getting-started.md#9-连接信息与路由发现) 和 [SSE 支持](getting-started.md#10-sse-server-sent-events-支持)。

## API 応答標準

フレームワークは `make_response()` と `make_error()` メソッドを使用して、標準化されたレスポンスを構築し、手動でレスポンス辞書を構築する必要はありません。

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

### 手動構築のレスポンス（旧版方式でも互換性あり）

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

## 多アカウントサポート

### 声明式設定（推奨）

`AccountConfigClass` を使用して設定クラスを宣言すると、フレームワークは多アカウントのロード、検証、テンプレート生成を自動的に管理します：

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
            self.logger.info(f"启动账户 {name}: {account.bot_id}")
            await self._connect(name, account)
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # 使用 account.token, account.bot_id 等字段
```

### 账户配置文件

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

### 指定アカウントでの送信

```python
# Using メソッドでアカウントを指定
my_adapter = adapter.get("myplatform")

# アカウント名で
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")

# アカウント ID で
await my_adapter.Send.Using("account_id").To("user", "123").Text("Hello")
```

## エラーハンドリング

### 接続リトライ

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
                    self.logger.warning(f"连接失败，{wait_time}秒后重试")
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### API エラーハンドリング

```python
async def call_api(self, endpoint: str, **params):
    try:
        # SDK 内部クライアントの推奨
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
        self.logger.error(f"请求超时: {endpoint}")
        return self._error_response("请求超时", 32000)
    except ClientError as e:
        self.logger.error(f"网络错误: {e}")
        return self._error_response("网络请求失败", 33000)
    except Exception as e:
        self.logger.error(f"未知错误: {e}")
        return self._error_response(str(e), 34000)
```

> **互換性の維持**：`aiohttp.ClientSession` を直接使用する旧版アダプターコードは影響を受けず、`aiohttp.ClientError` を捕捉することもできます。両方の方式は共存できます。新しいコードでは `sdk.client` + ErisPulse 例外体系の使用を推奨します。

## Bot 状態管理

AdapterManager 内置了 Bot 状态追踪系统，自动维护所有已注册 Bot 的在线状态、活跃时间和元信息。

### 自動発見メカニズム

アダプターが `adapter.emit()` を呼び出すと、フレームワークはイベント内の `self` フィールドを自動的にチェックします：

- **meta イベント**：根据 `detail_type` 执行对应操作（connect 注册/断开标记离线/heartbeat 更新活跃时间）
- **普通イベント**（message/notice/request）：自动发现 Bot 并更新活跃时间

```python
# 所有包含 self 字段的事件都会触发自动发现
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123" 已自动注册（如果首次出现）并更新活跃时间
```

### Meta イベントタイプ

| `detail_type` | 説明 | フレームワークの動作 |
|---|---|---|
| `connect` | Bot 接続 | Bot を登録し、`adapter.bot.online` ライフサイクルイベントを発行します |
| `disconnect` | Bot 断开 | Bot をオフラインにマークし、`adapter.bot.offline` ライフサイクルイベントを発行します |
| `heartbeat` | Bot ハートビート | Bot のアクティブ時間とメタ情報を更新します |

### 适配器发送 Meta 事件

使用 `emit_meta()` 一行即可发送 meta 事件：

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # 一行发送 connect 事件
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="我的机器人")

    async def _on_bot_disconnect(self, bot_id: str):
        await self.emit_meta("disconnect", bot_id)
```

也支持手动构造（旧版方式仍然兼容）：

```python
await self.adapter.emit({
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": bot_id}
})
```

### `self` 字段扩展信息

`self` 字段除必需的 `platform` 和 `user_id` 外，还支持以下可选字段：

| 字段 | 説明 |
|---|---|
| `user_name` | Bot 用户名 |
| `nickname` | Bot 昵称 |
| `avatar` | Bot 头像 URL |
| `account_id` | 多账户标识 |

### Bot 状態の照会

```python
from ErisPulse import sdk

# 获取单个 Bot 信息
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# 列出所有 Bot
all_bots = sdk.adapter.list_bots()

# 列出指定平台的 Bot
platform_bots = sdk.adapter.list_bots("myplatform")

# 检查 Bot 是否在线
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# 获取完整状态摘要（适合 WebUI 展示）
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

### Bot ライフサイクルの監視

```python
from ErisPulse import sdk

@sdk.lifecycle.on("adapter.bot.online")
async def on_bot_online(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Bot 上线: {platform}/{bot_id}")

@sdk.lifecycle.on("adapter.bot.offline")
async def on_bot_offline(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Bot 下线: {platform}/{bot_id}")
```

## 関連文書

- [アダプター開発入門](getting-started.md) - 最初のアダプターを作成する
- [SendDSL 詳解](send-dsl.md) - メッセージ送信を学ぶ
- [アダプター開発ベストプラクティス](best-practices.md) - 高品質なアダプターを開発する

翻訳は以上です。