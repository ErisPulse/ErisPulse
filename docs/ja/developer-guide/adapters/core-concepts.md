# アダプタのコアコンセプト

ErisPulse アダプタのコアコンセプトを理解することは、アダプタを開発するための基礎です。

## アダプタアーキテクチャ

### コンポーネントの関係

```
正方向変換（受信方向）                           逆方向変換（送信方向）
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ───────────────────┐
│ プラットフォーム固有イベント     │                        │ モジュールが構築するメッセージ     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │ アダプタ (MyAdapter) │   │                  │
│  Converter       │   │ ┌──────────────┐ │   │ Send.Raw_ob12()  │
│  (イベント変換器)    │──→│ │              │ │   │ (逆方向変換エントリ)   │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ プラットフォーム API 呼び出し    │
                       │ OneBot12 標準イベント │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ 標準レスポンス形式     │
                       │ イベントシステム         │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ モジュール (イベント処理)  │
                       └──────────────────┘
```

**コアの対称性**：
- **正方向変換**（Converter）：プラットフォーム固有イベント → OneBot12 標準イベント、元データは `{platform}_raw` に保持される
- **逆方向変換**（Raw_ob12）：OneBot12 メッセージセグメント → プラットフォーム API 呼び出し、標準レスポンス形式で返される

## AdapterManager 适配器管理器

`AdapterManager` は、ErisPulse におけるアダプタシステムの中心となるコンポーネントであり、すべてのプラットフォームアダプタの登録、起動、停止、イベント配信を管理します。

### 核心機能

- **アダプタの登録**：複数のプラットフォームアダプタの登録と管理
- **ライフサイクル管理**：アダプタの起動と停止の制御
- **イベント配信**：OneBot12 標準イベントとプラットフォーム固有イベントの配信
- **設定管理**：アダプタの有効/無効状態の管理
- **ミドルウェアのサポート**：OneBot12 イベントミドルウェアのサポート

### 基本的な使用法

```python
from ErisPulse import sdk

# アダプタの登録（通常は Loader が自動的に行います）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# すべてのアダプタを起動
await sdk.adapter.startup()

# 指定のアダプタを起動
await sdk.adapter.startup(["myplatform"])
# 全てのアダプタを起動
await sdk.adapter.startup()

# アダプタのインスタンスを取得
my_adapter = sdk.adapter.get("myplatform")
# または属性アクセスで取得
my_adapter = sdk.adapter.myplatform

# すべてのアダプタを停止
await sdk.adapter.shutdown()
```

### 起動と停止

#### アダプタの起動

```python
# すべての登録済みアダプタを起動
await sdk.adapter.startup()

# 指定のプラットフォームを起動
await sdk.adapter.startup(["platform1", "platform2"])
```

**起動の流れ：**

1. `adapter.start` ライフサイクルイベントを送信
2. `adapter.status.change` イベントを送信（starting）
3. 各アダプタを並列で起動
4. 起動に失敗した場合、指数バックオフ戦略による自動リトライ
5. 起動に成功した場合、`adapter.status.change` イベントを送信（started）

**リトライメカニズム：**

- 最初の4回のリトライ：60秒、10分、30分、60分
- 5回目以降：3時間固定間隔

#### アダプタの停止

```python
# すべてのアダプタを停止
await sdk.adapter.shutdown()
```

**停止の流れ：**

1. `adapter.stop` ライフサイクルイベントを送信
2. すべてのアダプタの `shutdown()` メソッドを呼び出す
3. ルーティングサーバーを停止
4. イベントハンドラをクリア
5. `adapter.stopped` ライフサイクルイベントを送信

### 設定管理

#### プラットフォームの状態を確認

```python
# プラットフォームが登録されているか確認
exists = sdk.adapter.exists("myplatform")

# プラットフォームが有効か確認
enabled = sdk.adapter.is_enabled("myplatform")

# in 演算子を使用
if "myplatform" in sdk.adapter:
    print("プラットフォームは存在し、有効です")
```

#### プラットフォームの一覧表示

```python
# すべての登録済みプラットフォームを取得
platforms = sdk.adapter.list_registered()

# すべてのプラットフォームとその状態を取得
status_dict = sdk.adapter.list_items()
# 戻り値: {"platform1": true, "platform2": false, ...}

# 有効なプラットフォームのリストを取得
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### イベントの監視

#### OneBot12 標準イベント

```python
from ErisPulse import sdk

# すべてのプラットフォームの標準メッセージイベントを監視
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"OneBot12 メッセージを受信: {data}")

# 特定のプラットフォームの標準メッセージイベントを監視
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"myplatform からのメッセージを受信: {data}")

# すべてのイベントを監視
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"イベントを受信: {data.get('type')}")
```

#### プラットフォーム固有イベント

```python
# 特定のプラットフォームの固有イベントを監視
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"固有イベントを受信: {data}")

# すべてのプラットフォームの固有イベントを監視（ワイルドカード）
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"固有イベントを受信: {data}")
```

#### イベント配信メカニズム

`adapter.emit(event_data)` を呼び出したとき：

1. **ミドルウェア処理**：まずすべての OneBot12 ミドルウェアを実行
2. **標準イベント配信**：一致する OneBot12 イベントハンドラに配信
3. **固有イベント配信**：元のデータが存在する場合、固有イベントハンドラに配信

**一致ルール：**

- 精確一致：`@sdk.adapter.on("message")` は `message` イベントのみに一致
- ワイルドカード：`@sdk.adapter.on("*")` はすべてのイベントに一致
- プラットフォームフィルタ：`platform="myplatform"` は指定のプラットフォームのイベントのみに配信

### ミドルウェア

#### ミドルウェアの追加

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """ログ記録ミドルウェア"""
    print(f"イベントを処理: {data.get('type')}")
    return data  # 必須で、データを返す

@sdk.adapter.middleware
async def filter_middleware(data):
    """イベントフィルタリングミドルウェア"""
    # 不要なイベントをフィルタリング
    if data.get("type") == "notice":
        return None  # None を返した場合、ミドルウェアチェーンはその返り値を無視し、元のデータを保持して次に渡す
    return data  # 必須で、データを返して次に渡す
```

#### ミドルウェアの実行順序

ミドルウェアは登録順に実行され、後から登録されたミドルウェアが先に実行されます。

> **注意**：ミドルウェアが `None` を返した場合（たとえば `return data` を忘れている場合）、フレームワークはその返り値を無視して元のデータを保持して次に渡し、warning レベルのログを出力します。これにより、1つのミドルウェアのミスがイベントチェーン全体を中断することはありません。

```python
# 登録順
sdk.adapter.middleware(middleware1)  # 最後に実行
sdk.adapter.middleware(middleware2)  # 中間で実行
sdk.adapter.middleware(middleware3)  # 最初に実行

# 実行順序：middleware3 -> middleware2 -> middleware1
```

### アダプタインスタンスの取得

#### get() メソッド

```python
adapter = sdk.adapter.get("myplatform")
if adapter:
    await adapter.Send.To("user", "123").Text("Hello")
```

#### 属性アクセス

```python
# 属性名でアクセス（大文字小文字を区別しません）
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## BaseAdapter 基底クラス

### 基本構造

```python
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig, BotAccountConfig

@dataclass
class MyConfig(BaseConfig):
    """アダプタの設定（宣言後、フレームワークが自動的に管理）"""
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
    
    # __init__ はオーバーライド不要、フレームワークが自動処理：
    # - self.sdk, self.logger
    # - self.cfg（型安全な設定インスタンス、リアルタイム読み込み）
    # - self.Send, self.Request
    
    async def start(self):
        """アダプタの起動（必須実装）"""
        cfg = self.cfg  # 自動読み込みされた型安全な設定
        pass
    
    async def shutdown(self):
        """アダプタの終了（必須実装）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォームAPIの呼び出し（必須実装）"""
        pass
```

### 設定管理

フレームワークは宣言的設定管理を提供し、dataclassを使って設定構造を定義すると、フレームワークが自動的にロード、検証、テンプレート生成を処理します。

#### 単一アカウント設定

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

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
        cfg = self.cfg  # 型安全、リアルタイム読み込み
        if not cfg.token:
            raise ValueError("Tokenが設定されていません")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### 複数アカウント設定

`BotAccountConfig` 基底クラスは `enabled` と `name` フィールドを提供します。ほとんどのアダプタは、プラットフォームプロトコルまたはログイン応答から実行時に `bot_id` を自動的に取得でき、イベント変換時にアカウント設定に注入されます。

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

# 多くのアダプタでは、bot_idは実行時に自動取得され、設定は不要です
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Token"},
        "required": True,
    })

# ログイン時に bot_id を取得できない場合は、ユーザーに設定で入力させることもできます
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

#### metadata 約定

フィールドの metadata は、TOMLコメント生成とWebUIフォームレンダリングの両方に使用されます：

```python
metadata = {
    "description": str | dict,  # フィールドの説明（i18n対応）
    "required": bool,         # 必須か（検証 + WebUIの必須マーク）
    "secret": bool,           # 敏感情報か（WebUIでは***表示、ログでは脱敏）
    "ui": {                   # WebUIコントロール設定（旧名 "webui" は互換性あり）
        "widget": str,        # コントロールタイプ: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # グループ: "basic" | "advanced" | "connection" など
        "order": int,         # ソート優先度（小さいほど前に表示）
        "options": list,      # selectコントロールの選択肢 [{label, value}]、label は i18n に対応
        "placeholder": str | dict,  # 入力欄のプレースホルダー（i18n に対応）
    },
    "extra": dict,            # 余分な拡張フィールド（schemaに透過）
}
```

すべてのユーザーが見られるテキストフィールドは i18n をサポートし、`{"i18n": "key", "default": "テキスト"}` 形式で統一されます。  
純粋な文字列はそのまま透過されます（後方互換）。サポートされる i18n フィールドは以下の通りです：

| フィールド | 位置 | 説明 |
|------|------|------|
| `description` | field metadata | フィールドの説明 |
| `options[].label` | `ui.options` | select コントロールの選択肢ラベル |
| `placeholder` | `ui.placeholder` | 入力欄のプレースホルダー |
| `group_labels` | `_schema_meta` | グループ表示名（ダッシュボードのセクションタイトル） |

i18n を使用する場合は、翻訳キーを i18n システムに事前に登録する必要があります（[i18n ドキュメント](../../advanced/i18n.md#設定フィールド多言語)を参照）。

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
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "高度設定"},
    }
}
```

フレームワークの `resolve_config_schema()` は、現在の言語に応じて上記のすべての i18n キーを自動的に解決します。  
`get_config_schema()` は i18n ディクショナリをそのまま透過し、フロントエンドが独自に解析します。

### 宣言的翻訳キー（v2.7.0+）

アダプタは `ConfigClass` を宣言するのと同じように、`I18nClass` 内部クラスを使って翻訳キーを一括で宣言できます。  
フレームワークは `__init__` 段階（設定テンプレート生成前）で自動的に宣言されたすべての翻訳キーを登録し、  
設定の説明で参照される i18n キーがテンプレート生成時に利用可能になるようにします。

```python
from ErisPulse.Core.Bases import BaseAdapter, BaseI18n, I18nKey

class MyAdapter(BaseAdapter):
    class I18nClass(BaseI18n):
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="API 地址",
            zh_TW="API 位址",
            en="API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
        )
        token: I18nKey = I18nKey(
            default="Platform Token",
            zh_CN="平台 Token",
            zh_TW="平台權杖",
            en="Platform Token",
            ja="プラットフォームトークン",
            ru="Токен платформы",
        )
```

> ``I18nKey.default`` は**言語に依存しないバックアップテキスト**で、どの言語にも登録されません。  
> 翻訳を有効にするには、少なくとも1つの言語パラメータを明示的に渡す必要があります。

詳細な使い方（キーのパスルール、明示的な key パラメータなど）は [i18n ドキュメント](../../advanced/i18n.md#推奨書き方-through-i18nclass-宣言翻訳キー-v270) を参照してください。

### 宣言的イベント拡張メソッド（v2.7.0+）

アダプタは `EventMixin` を使ってプラットフォーム固有のイベント拡張メソッドを一括で宣言でき、フレームワークが自動的に現在のプラットフォームに登録します。

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    class EventMixin:
        def get_chat_name(self):
            """チャット名を取得"""
            return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

        def is_official_message(self):
            """公式メッセージか判定"""
            raw = self.get("myplatform_raw", {})
            return raw.get("sender", {}).get("is_official", False)
```

登録後、イベントオブジェクトはこれらのメソッドを直接呼び出すことができます：

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] 公式メッセージが届きました")
```

> アダプタのイベント拡張メソッドは自身のプラットフォーム（``self._platform``）に登録されます。  
> モジュールがプラットフォーム間のイベント拡張を必要とする場合は、従来の ``register_event_mixin()`` API を使用してください。

#### アカウント解決

複数アカウントアダプタは `_resolve_account()` を使って目的のアカウントを自動的に解決できます：

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: アカウント名, account: 設定インスタンス
```

解決戦略：アカウント名一致 → `bot_id` フィールド一致 → 他の str フィールド一致 → 最初の有効アカウント。

#### 設定のホット更新

サブクラスは `on_config_update()` をオーバーライドして設定変更に反応できます：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Tokenが更新されたため、再接続します")
```

### 初期化プロセス

フレームワークは `BaseAdapter.__init__(self, sdk=None)` で自動的に以下の処理を行います：

1. **SDK参照**：`self.sdk`、`self.logger` を設定
2. **Send/Request工場**：`self.Send` と `self.Request` を作成
3. **設定テンプレート**：`ConfigClass` を宣言した場合、初めての起動時にデフォルト設定テンプレートを自動生成
4. **アカウントテンプレート**：`AccountConfigClass` を宣言した場合、初めての起動時にデフォルトアカウントテンプレートを自動生成
5. **EventMixin登録**：`EventMixin` を宣言した場合、`AdapterManager` がプラットフォーム名を注入した後に自動的に登録

設定は `self.cfg` / `self.accounts` でリアルタイムに読み取ります（アクセスするたびに設定ストアから最新値を読み込みます）。`self.config` は `self.cfg` の互換エイリアスとして引き続き使用できます。

ほとんどのアダプタは `__init__` をオーバーライドする必要はありません。カスタム初期化が必要な場合は：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # sdkを渡す
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## Send 消息送信 DSL

### 継承関係

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        """Send 嵌套クラス。BaseAdapter.Send から継承"""
        pass
```

### 利用可能な属性

`Send` クラスを呼び出すと、以下の属性が自動的に設定されます：

| 属性 | 説明 | 設定方法 |
|-----|------|---------|
| `_target_id` | 目標ID | `To(id)` または `To(type, id)` |
| `_target_type` | 目標タイプ | `To(type, id)` |
| `_target_to` | 簡略化された目標ID | `To(id)` |
| `_account_id` | 送信アカウントID | `Using(account_id)` |
| `_adapter` | 适配器インスタンス | 自動設定 |
| `_at_user_ids` | @ユーザー一覧 | `At(user_id)` |
| `_reply_message_id` | 回答するメッセージID | `Reply(message_id)` |
| `_at_all` | 全員に@するか | `AtAll()` |

> **推奨**：`self.send_context` 属性を使って `target_type`、`target_id`、`account_id` を一括で取得する。インスタンス変数に直接アクセスするよりも明確です。

### フレームワーク補助メソッド

| メソッド/属性 | 説明 |
|-----------|------|
| `self._apply_modifiers(message)` | At/AtAll/Reply 修飾子の状態をメッセージセグメントリストにマージする |
| `self.send_context` | `{target_type, target_id, account_id}` ディクショナリを返す |

### 基本メソッド

アダプタは `Raw_ob12` を実装するだけで、標準メソッド（Text/Image/Voice/Video/File）は `SendDSL` 基クラスから継承され、デフォルトで `Raw_ob12` に委譲されます：

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """OneBot12 メッセージセグメント → プラットフォーム API に実装する必要がある"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    # Text/Image/Voice/Video/File は基クラスから継承され、Raw_ob12 に自動的に委譲される。再実装する必要はない
    # プラットフォーム固有のロジックが必要な場合は、個別のメソッドをオーバーライドする：
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
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

### コンバートフロー

```
プラットフォームの元のイベント
    ↓
Converter.convert()
    ↓
OneBot12 標準イベント
```

### 必須フィールド

コンバート後のイベントはすべて以下のフィールドを含む必要があります：

```python
{
    "id": "イベントの唯一識別子",
    "time": 1234567890,           # 10桁 Unix タイムスタンプ
    "type": "message/notice/request/meta",
    "detail_type": "イベントの詳細タイプ",
    "platform": "プラットフォーム名",
    "self": {
        "platform": "プラットフォーム名",
        "user_id": "ロボットID"     # bot_id と一致する必要がある
    },
    "{platform}_raw": {...},       # 元のデータ（必須）
    "{platform}_raw_type": "..."    # 元のタイプ（必須）
}
```

### コンバーターの例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """プラットフォームの元のイベントを OneBot12 標準形式に変換する"""
        if not isinstance(raw_event, dict):
            return None
        
        # イベントIDの生成
        event_id = raw_event.get("event_id") or str(uuid.uuid4())
        
        # タイムスタンプの変換
        timestamp = raw_event.get("timestamp")
        if timestamp and timestamp > 10**12:
            timestamp = int(timestamp / 1000)
        else:
            timestamp = int(timestamp) if timestamp else int(time.time())
        
        # イベントタイプの変換
        event_type = self._convert_type(raw_event.get("type"))
        detail_type = self._convert_detail_type(raw_event)
        
        # 標準イベントの構築
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
        """WebSocket ルートの登録"""
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler,
            auth_handler=self._auth_handler
        )
    
    async def _ws_handler(self, websocket):
        """WebSocket 接続ハンドラ"""
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
        """WebHook ルートの登録"""
        router.register_http_route(
            module_name="myplatform",
            path="/webhook",
            handler=self._webhook_handler,
            methods=["POST"]
        )
    
    async def _webhook_handler(self, request):
        """WebHook リクエストハンドラ"""
        data = await request.json()
        onebot_event = self.convert(data)
        if onebot_event:
            await self.adapter.emit(onebot_event)
        return {"status": "ok"}
```

> **ルート情報の照会**：アダプタが登録したルート（HTTP、WebSocket、SSE）は、`sdk.adapter.get_connection_info(platform)` および `sdk.router.get_module_urls(module_name)` を使用して完全な接続アドレス（`base_url` + パス）を照会できます。詳細は [アダプタ開発入門 - 接続情報とルート発見](docs/ja/getting-started.md#9-接続情報とルート発見) および [SSE 支持](docs/ja/getting-started.md#10-sse-server-sent-events-サポート) を参照してください。

## API レスポンス標準

フレームワークは、`make_response()` と `make_error()` メソッドを提供し、手動でレスポンス辞書を構築することなく、標準化されたレスポンスを構築できます。

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

### 手動でレスポンスを構築する（旧バージョンの方法も互換性があります）

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

### 宣言的構成（推奨）

`AccountConfigClass` を宣言的に定義すると、フレームワークはアカウントの自動読み込み、検証、テンプレート生成を管理します。

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

@dataclass
class MyBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={"description": "Bot ID", "required": True})
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

### アカウント構成ファイル

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

### 特定アカウントによる送信

```python
# Using メソッドを使用してアカウントを指定
my_adapter = adapter.get("myplatform")

# イベント内の self.user_id を使用（推奨、最も汎用的）
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# アカウント名を使用
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### self.user_id と Using の関係

フレームワークのイベント返信メカニズムは、イベントの `self` フィールドから `account_id`（優先）または `user_id` を抽出し、`Using` パラメータとして渡します。アダプター開発者は、Converter で `self.user_id` の値が `_resolve_account()` と正しく一致することを保証する必要があります。

**フレームワーク内部の動作**：

```python
# フレームワークが bot_id を抽出するロジック
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# bot_id が空でない場合に Using を呼び出す
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **重要なポイント**：アダプターが 1 つの Bot 構成のみを使用する場合でも、Converter が正しく `self.user_id` を設定している限り、フレームワークはそれを `Using` パラメータとして渡します。アダプターは、`self.user_id` が `AccountConfigClass` の識別フィールド（例：`bot_id`）と一致していることを保証し、`_resolve_account()` が正しいアカウントにマッチできるようにする必要があります。`self.user_id` が空の場合、フレームワークは `Using` を呼び出さず、`call_api` に渡される `account_id` は `None` になります。この場合、`_resolve_account(None)` は最初の有効なアカウントを返します。

## エラー処理

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
                    self.logger.warning(f"接続に失敗しました。{wait_time}秒後に再試行します。")
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### API エラー処理

```python
async def call_api(self, endpoint: str, **params):
    try:
        # 推奨される SDK 内部のクライアントを使用します
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
        return self._error_response("ネットワークリクエストが失敗しました", 33000)
    except Exception as e:
        self.logger.error(f"未知のエラー: {e}")
        return self._error_response(str(e), 34000)
```

> **後方互換性**：`aiohttp.ClientSession` を直接使用する古いアダプタコードは影響を受けません。引き続き `aiohttp.ClientError` をキャッチできます。両方の方法を同時に使用できます。新規開発は `sdk.client` と ErisPulse の例外体系を使用することを推奨します。

## Bot 状態管理

AdapterManager には、登録済みのすべての Bot のオンライン状態、アクティブ時間、メタ情報などを自動的に維持する Bot 状態追跡システムが内蔵されています。

### 自動検出メカニズム

アダプタが `adapter.emit()` を使ってイベントを送信する際、フレームワークは自動的にイベント内の `self` フィールドをチェックします。

- **meta イベント**：`detail_type` に基づいて対応する操作を実行します（connect で Bot を登録 / disconnect でオフラインをマーク / heartbeat でアクティブ時間を更新）
- **通常イベント**（message/notice/request）：Bot を自動検出し、アクティブ時間を更新します

```python
# self フィールドを含むすべてのイベントが自動検出をトリガーします
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123" は自動的に登録され、アクティブ時間が更新されます（初回登録の場合）
```

### Meta イベントの種類

| `detail_type` | 説明 | フレームワークの動作 |
|---|---|---|
| `connect` | Bot が接続 | Bot を登録し、`adapter.bot.online` ライフサイクルイベントを発火します |
| `disconnect` | Bot が切断 | Bot をオフラインにマークし、`adapter.bot.offline` ライフサイクルイベントを発火します |
| `heartbeat` | Bot のハートビート | Bot のアクティブ時間とメタ情報を更新します |

### アダプタによる Meta イベント送信

`emit_meta()` を使って、一行で Meta イベントを送信できます：

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # 一行で connect イベントを送信
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="私のロボット")

    async def _on_bot_disconnect(self, bot_id: str):
        await self.emit_meta("disconnect", bot_id)
```

手動で構築することもサポートされており、従来の方法も互換性があります：

```python
await self.adapter.emit({
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": bot_id}
})
```

### `self` フィールドの拡張情報

`self` フィールドには、必須の `platform` と `user_id` の他に、以下のオプションフィールドがサポートされています：

| フィールド | 説明 |
|---|---|
| `user_name` | Bot のユーザー名 |
| `nickname` | Bot のニックネーム |
| `avatar` | Bot のアバターの URL |
| `account_id` | 複数アカウントの識別子 |

### Bot 状態の照会

```python
from ErisPulse import sdk

# 単一の Bot 情報を取得
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# すべての Bot をリスト表示
all_bots = sdk.adapter.list_bots()

# 指定プラットフォームの Bot をリスト表示
platform_bots = sdk.adapter.list_bots("myplatform")

# Bot がオンラインかどうかをチェック
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# 完全な状態サマリーを取得（WebUI に表示するのに適しています）
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
    sdk.logger.info(f"Bot 上線: {platform}/{bot_id}")

@sdk.lifecycle.on("adapter.bot.offline")
async def on_bot_offline(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Bot 下線: {platform}/{bot_id}")
```

## 関連ドキュメント

- [アダプタの開発入門](docs/ja/getting-started.md) - 最初のアダプタを作成する
- [SendDSL 詳解](docs/ja/send-dsl.md) - メッセージ送信の学習
- [アダプタのベストプラクティス](docs/ja/best-practices.md) - 高品質なアダプタの開発