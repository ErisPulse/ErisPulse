# アダプタのコアコンセプト

ErisPulse アダプタのコアコンセプトを理解することは、アダプタを開発するための基礎です。

## アダプタアーキテクチャ

### コンポーネント関係

```
正方向変換（受信方向）                           逆方向変換（送信方向）
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ プラットフォーム固有イベント     │                        │ モジュール構築メッセージ     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │  アダプタ (MyAdapter) │   │ Send.Raw_ob12()  │
│  Converter       │   │ ┌──────────────┐ │   │ (逆方向変換エントリ)   │
│  (イベント変換器)    │──→│ │              │ │   │                  │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ プラットフォームAPI呼び出し    │
                       │ OneBot12標準イベント │    └────────┬─────────┘
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

**コア対称性**:
- **正方向変換**（Converter）：プラットフォーム固有イベント → OneBot12標準イベント、元データは`{platform}_raw`に保持
- **逆方向変換**（Raw_ob12）：OneBot12メッセージセグメント → プラットフォームAPI呼び出し、返却は標準レスポンス形式

## AdapterManager アダプタ管理器

`AdapterManager`はErisPulseアダプタシステムのコアコンポーネントであり、すべてのプラットフォームアダプタの登録、起動、停止、イベント配信を管理します。

### コア機能

- **アダプタ登録**：複数のプラットフォームアダプタの登録と管理
- **ライフサイクル管理**：アダプタの起動と停止を制御
- **イベント配信**：OneBot12標準イベントとプラットフォーム固有イベントの配信
- **設定管理**：アダプタの有効/無効状態を管理
- **ミドルウェアサポート**：OneBot12イベントミドルウェアをサポート

### 基本的な使用

```python
from ErisPulse import sdk

# アダプタの登録（通常Loaderが自動的に実行）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# すべてのアダプタを起動
await sdk.adapter.startup()

# 指定されたプラットフォームを起動
await sdk.adapter.startup(["platform1", "platform2"])
# すべてのアダプタを起動
await sdk.adapter.startup()

# アダプタのインスタンスを取得
my_adapter = sdk.adapter.get("myplatform")
# 属性アクセスでも取得可能
my_adapter = sdk.adapter.myplatform

# すべてのアダプタを停止
await sdk.adapter.shutdown()
```

### 起動と停止

#### アダプタの起動

```python
# すべての登録済みアダプタを起動
await sdk.adapter.startup()

# 指定されたプラットフォームを起動
await sdk.adapter.startup(["platform1", "platform2"])
```

**起動プロセス**:

1. `adapter.start`ライフサイクルイベントを送信
2. `adapter.status.change`イベントを送信（starting）
3. 各アダプタを並列に起動
4. 起動に失敗した場合は、指数関数的バックオフ戦略で自動的に再試行
5. 起動成功後、`adapter.status.change`イベントを送信（started）

**再試行メカニズム**:

- 最初の4回の再試行：60秒、10分、30分、60分
- 5回目以降：3時間固定間隔

#### アダプタの停止

```python
# すべてのアダプタを停止
await sdk.adapter.shutdown()
```

**停止プロセス**:

1. `adapter.stop`ライフサイクルイベントを送信
2. すべてのアダプタの`shutdown()`メソッドを呼び出す
3. ルーティングサーバーを閉じる
4. イベントハンドラをクリア
5. `adapter.stopped`ライフサイクルイベントを送信

### 設定管理

#### プラットフォームのステータス確認

```python
# プラットフォームが登録されているか確認
exists = sdk.adapter.exists("myplatform")

# プラットフォームが有効かどうか確認
enabled = sdk.adapter.is_enabled("myplatform")

# in演算子を使用
if "myplatform" in sdk.adapter:
    print("プラットフォームが存在し、有効です")
```

#### プラットフォームのリスト表示

```python
# すべての登録済みプラットフォームをリスト表示
platforms = sdk.adapter.list_registered()

# すべてのプラットフォームとそのステータスをリスト表示
status_dict = sdk.adapter.list_items()
# 返却値: {"platform1": true, "platform2": false, ...}

# 有効なプラットフォームのリストを取得
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### イベントの監視

#### OneBot12標準イベント

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

`adapter.emit(event_data)`を呼び出すと：

1. **ミドルウェア処理**：まずすべてのOneBot12ミドルウェアを実行
2. **標準イベント配信**：一致するOneBot12イベントハンドラに配信
3. **固有イベント配信**：元データがあれば、固有イベントハンドラに配信

**一致ルール**:

- 精確一致：`@sdk.adapter.on("message")`は`message`イベントのみを一致
- ワイルドカード：`@sdk.adapter.on("*")`はすべてのイベントに一致
- プラットフォームフィルタリング：`platform="myplatform"`は指定されたプラットフォームのイベントのみ配信

### ミドルウェア

#### ミドルウェアの追加

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """ログ記録ミドルウェア"""
    print(f"イベントを処理: {data.get('type')}")
    return data  # 必ずデータを返す

@sdk.adapter.middleware
async def filter_middleware(data):
    """イベントフィルタリングミドルウェア"""
    # 不要なイベントをフィルタリング
    if data.get("type") == "notice":
        return None  # Noneを返すとミドルウェアチェーンはその返り値を無視し、元のデータを保持して継続
    return data  # 伝播を続けるために必ずデータを返す
```

#### ミドルウェアの実行順序

ミドルウェアは登録順に実行され、後から登録されたミドルウェアが先に実行されます。

> **注意**：ミドルウェアが`None`を返した場合（`return data`を忘れているなど）、フレームワークはその返り値を無視して元のデータを保持して継続し、警告レベルのログを出力します。これにより、1つのミドルウェアのミスがイベントチェーン全体を中断することはありません。

```python
# 登録順
sdk.adapter.middleware(middleware1)  # 最後に実行
sdk.adapter.middleware(middleware2)  # 中間に実行
sdk.adapter.middleware(middleware3)  # 最初に実行

# 実行順序：middleware3 -> middleware2 -> middleware1
```

### アダプタインスタンスの取得

#### get()メソッド

```python
adapter = sdk.adapter.get("myplatform")
if adapter:
    await adapter.Send.To("user", "123").Text("Hello")
```

#### 属性アクセス

```python
# 属性名でアクセス（大文字小文字を区別しない）
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## BaseAdapter 基底クラス

### 基本構造

```python
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.runtime.config_schema import BaseConfig, BotAccountConfig

@dataclass
class MyConfig(BaseConfig):
    """アダプタの設定（宣言後、フレームワークが自動管理）"""
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
    
    # __init__をオーバーライドする必要はない、フレームワークが自動処理：
    # - self.sdk, self.logger
    # - self.cfg（型安全な設定インスタンス、リアルタイム読み取り）
    # - self.Send, self.Request
    
    async def start(self):
        """アダプタを起動する（必須実装）"""
        cfg = self.cfg  # 自動読み込みの型安全な設定
        pass
    
    async def shutdown(self):
        """アダプタを停止する（必須実装）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォームAPIを呼び出す（必須実装）"""
        pass
```

### 設定管理

フレームワークは宣言的設定管理を提供し、dataclassで設定構造を定義することで、フレームワークが自動的に読み込み、検証、テンプレート生成を処理します。

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
        cfg = self.cfg  # 型安全、リアルタイム読み取り
        if not cfg.token:
            raise ValueError("Tokenが設定されていません")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### 複数アカウント設定

`BotAccountConfig`基底クラスは`enabled`と`name`フィールドを提供します。ほとんどのアダプタはプラットフォームプロトコルやログイン応答から実行時に`bot_id`を自動的に取得でき、イベント変換時にアカウント設定に注入されます。

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BotAccountConfig

# ほとんどのアダプタ：実行時にbot_idを自動取得、設定は不要
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Token"},
        "required": True,
    })

# ログイン時にbot_idを取得できない場合、ユーザーに設定で入力させる
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

#### metadataの約束

フィールドのmetadataはTOMLコメント生成とWebUIフォームレンダリングの両方に役立ちます：

```python
metadata = {
    "description": str | dict,  # フィールドの説明（i18nをサポート）
    "required": bool,         # 必須かどうか（検証 + WebUIの必須マーク）
    "secret": bool,           # 敏感な情報かどうか（WebUIでは***に表示、ログでは脱敏）
    "ui": {                   # WebUIコントロールの設定（旧名"webui"も互換）
        "widget": str,        # コントロールの種類: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # グループ: "basic" | "advanced" | "connection" 等
        "order": int,         # ソートの重み（小さいほど先に表示）
        "options": list,      # selectコントロールの選択肢 [{label, value}]、labelはi18nをサポート
        "placeholder": str | dict,  # 入力欄のプレースホルダー（i18nをサポート）
    },
    "extra": dict,            # 余分な拡張フィールド（schemaに透かし渡す）
}
```

すべてのユーザーが見えるテキストフィールドはi18nをサポートし、統一された`{"i18n": "key", "default": "text"}`形式を使用します。純粋な文字列はそのまま透かし渡されます（後方互換性）。サポートされるi18nフィールド：

| フィールド | 位置 | 説明 |
|------|------|------|
| `description` | field metadata | フィールドの説明 |
| `options[].label` | `ui.options` | selectコントロールの選択肢ラベル |
| `placeholder` | `ui.placeholder` | 入力欄のプレースホルダー |
| `group_labels` | `_schema_meta` | グループの表示名（ダッシュボードのセクションタイトル） |

i18nを使用する場合、事前に翻訳キーをi18nシステムに登録する必要があります（[i18nドキュメント](../../advanced/i18n.md#設定フィールド多言語)を参照）。

**description / placeholder / options label**の例：

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
                {"label": "純粋な文字列ラベル", "value": "b"},  # 純粋な文字列はそのまま透かし渡す
            ],
        },
    },
)
```

**group_labels**の例（設定クラス定義後に宣言）：

```python
MyConfig._schema_meta = {
    "group_labels": {
        "basic": {"i18n": "my_adapter.group.basic", "default": "基本設定"},
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "高度設定"},
    }
}
```

フレームワークの`resolve_config_schema()`は現在の言語に応じて上記のすべてのi18nキーを自動的に解釈します。`get_config_schema()`はi18n辞書をそのまま透かし渡し、フロントエンドが独自に解釈します。

### 宣言的翻訳キー (v2.7.0+)

アダプタは`ConfigClass`を宣言するのと同じように、`I18nClass`というネストされたクラスを使って翻訳キーを一括宣言することができます。フレームワークは`__init__`段階で（設定テンプレート生成の前に）宣言されたすべての翻訳キーを自動的に登録し、設定説明で参照されるi18nキーがテンプレート生成時に利用可能になることを保証します。

```python
from ErisPulse.Core.Bases import BaseAdapter, BaseI18n, I18nKey

class MyAdapter(BaseAdapter):
    class I18nClass(BaseI18n):
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="API アドレス",
            zh_TW="API 位址",
            en="API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
        )
        token: I18nKey = I18nKey(
            default="Platform Token",
            zh_CN="プラットフォーム Token",
            zh_TW="平台權杖",
            en="Platform Token",
            ja="プラットフォームトークン",
            ru="Токен платформы",
        )
```

> `I18nKey.default`は**言語に依存しないバックアップテキスト**であり、どの言語にも登録されません。翻訳を有効にするには、少なくとも1つの言語パラメータを明示的に渡す必要があります。

詳細な使い方（キーのパスルール、明示的なkeyパラメータなど）は[i18nドキュメント](../../advanced/i18n.md#推奨書き方-through-i18nclass-宣言翻訳キー-v270)を参照してください。

#### アカウントの解決

複数アカウントアダプタは`_resolve_account()`を使って目的のアカウントを自動的に解決できます：

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: アカウント名, account: 設定インスタンス
```

解決戦略：アカウント名一致 → `bot_id`フィールド一致 → 他のstrフィールド一致 → 最初の有効なアカウント。

#### 設定のホットアップデート

サブクラスは`on_config_update()`をオーバーライドして設定変更に応答できます：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Tokenが更新されたので、再接続します")
```

### 初期化プロセス

フレームワークは`BaseAdapter.__init__(self, sdk=None)`で自動的に以下の作業を行います：

1. **SDK参照**：`self.sdk`、`self.logger`を設定
2. **Send/Request工場**：`self.Send`と`self.Request`を作成
3. **設定テンプレート**：`ConfigClass`を宣言した場合、初めての設定テンプレートを自動生成
4. **アカウントテンプレート**：`AccountConfigClass`を宣言した場合、初めてのアカウントテンプレートを自動生成

設定は`self.cfg` / `self.accounts`でリアルタイムに読み取り（毎回アクセス時に最新値を設定ストアから読み取ります）されます。`self.config`は`self.cfg`の互換別名として引き続き使用できます。

ほとんどのアダプタは`__init__`をオーバーライドする必要はありません。独自の初期化が必要な場合は：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # sdkを渡す
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## Send メッセージ送信DSL

### 継承関係

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        """Sendネストクラス、BaseAdapter.Sendから継承"""
        pass
```

### 利用可能な属性

`Send`クラスは呼び出し時に自動的に以下の属性を設定します：

| 属性 | 説明 | 設定方法 |
|-----|------|---------|
| `_target_id` | 目標ID | `To(id)` または `To(type, id)` |
| `_target_type` | 目標タイプ | `To(type, id)` |
| `_target_to` | 簡略化された目標ID | `To(id)` |
| `_account_id` | 送信アカウントID | `Using(account_id)` |
| `_adapter` | アダプタインスタンス | 自動設定 |
| `_at_user_ids` | @ユーザー一覧 | `At(user_id)` |
| `_reply_message_id` | 返信メッセージID | `Reply(message_id)` |
| `_at_all` | @全員かどうか | `AtAll()` |

> **推奨**：`self.send_context`属性を使って`target_type`、`target_id`、`account_id`を一度に取得する方が、インスタンス変数に直接アクセスするよりも明確です。

### フレームワーク補助メソッド

| メソッド/属性 | 説明 |
|-----------|------|
| `self._apply_modifiers(message)` | At/AtAll/Reply修飾子の状態をメッセージセグメントリストにマージ |
| `self.send_context` | `{target_type, target_id, account_id}`辞書を返す |

### 基本メソッド

アダプタは`Raw_ob12`を実装するだけで十分で、標準メソッド（Text/Image/Voice/Video/File）は`SendDSL`基底クラスから継承され、デフォルトで`Raw_ob12`に委譲されます：

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """必須実装：OneBot12メッセージセグメント → プラットフォームAPI"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    # Text/Image/Voice/Video/Fileは基底クラスから継承され、Raw_ob12に自動的に委譲されるため、再実装は不要
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

## イベント変換器

### 変換フロー

```
プラットフォームの元イベント
    ↓
Converter.convert()
    ↓
OneBot12標準イベント
```

### 必須フィールド

変換後のイベントはすべて以下の必須フィールドを含む必要があります：

```python
{
    "id": "イベントのユニークな識別子",
    "time": 1234567890,           # 10桁のUnixタイムスタンプ
    "type": "message/notice/request/meta",
    "detail_type": "イベントの詳細タイプ",
    "platform": "プラットフォーム名",
    "self": {
        "platform": "プラットフォーム名",
        "user_id": "ロボットID"     # bot_idと一致する必要がある
    },
    "{platform}_raw": {...},       # 元データ（必須）
    "{platform}_raw_type": "..."    # 元のタイプ（必須）
}
```

### 変換器の例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """プラットフォームの元イベントをOneBot12標準形式に変換"""
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

### WebSocket接続

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """WebSocketルーティングの登録"""
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler,
            auth_handler=self._auth_handler
        )
    
    async def _ws_handler(self, websocket):
        """WebSocket接続ハンドラ"""
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
        """WebSocket認証"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook接続

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """WebHookルーティングの登録"""
        router.register_http_route(
            module_name="myplatform",
            path="/webhook",
            handler=self._webhook_handler,
            methods=["POST"]
        )
    
    async def _webhook_handler(self, request):
        """WebHookリクエストハンドラ"""
        data = await request.json()
        onebot_event = self.convert(data)
        if onebot_event:
            await self.adapter.emit(onebot_event)
        return {"status": "ok"}
```

> **ルーティング情報の照会**：アダプタが登録したルーティング（HTTP、WebSocket、SSE）は、`sdk.adapter.get_connection_info(platform)`と`sdk.router.get_module_urls(module_name)`で完全な接続アドレス（`base_url` + パス）を照会できます。詳しくは[アダプタ開発入門 - 接続情報とルーティング発見](getting-started.md#9-接続情報とルーティング発見)と[SSEサポート](getting-started.md#10-sse-server-sent-events-サポート)を参照してください。

## APIレスポンス標準

フレームワークは`make_response()`と`make_error()`メソッドを提供し、標準化されたレスポンスを構築できます。手動でレスポンス辞書を構築する必要はありません。

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

### 手動でレスポンス構築（旧方式も互換性あり）

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

### 宣言的設定（推奨）

`AccountConfigClass`を宣言した後、フレームワークは自動的に多アカウントの読み込み、検証、テンプレート生成を管理します：

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
            self.logger.info(f"アカウント {name}: {account.bot_id} を起動")
            await self._connect(name, account)
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # account.token, account.bot_idなどのフィールドを使用
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

### 指定アカウントでの送信

```python
# Usingメソッドでアカウントを指定
my_adapter = adapter.get("myplatform")

# イベント内のself.user_idを使用する（推奨、最も汎用的）
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# アカウント名で指定
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### self.user_idとUsingの関係

フレームワークのイベント返信メカニズムは、イベントのselfフィールドから`account_id`（優先）または`user_id`を抽出し、`Using`パラメータとして渡します。アダプタ開発者は、Converterで`self.user_id`の値が`_resolve_account()`で正しく一致することを保証する必要があります。

**フレームワーク内部の動作**（`Event._get_adapter_and_target`）：

```python
# フレームワークがbot_idを抽出するロジック
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# bot_idが空でない場合にUsingを呼び出す
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **重要な点**：アダプタが1つのBot設定のみを使用している場合でも、Converterで`self.user_id`を正しく設定すれば、フレームワークはそれを`Using`パラメータとして渡します。アダプタは`self.user_id`が`AccountConfigClass`中の識別フィールド（例：`bot_id`）と一致していることを保証し、`_resolve_account()`が正しいアカウントにマッチすることを確保する必要があります。`self.user_id`が空の場合、フレームワークは`Using`を呼び出さず、`call_api`に受け取る`account_id`は`None`となり、`_resolve_account(None)`は最初の有効なアカウントを返します。

## エラーハンドリング

### 接続再試行

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

### APIエラーハンドリング

```python
async def call_api(self, endpoint: str, **params):
    try:
        # 推奨はSDKのビルトインクライアントを使用
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
        self.logger.error(f"未知のエラー: {e}")
        return self._error_response(str(e), 34000)
```

> **後方互換性**：`aiohttp.ClientSession`を使用する古いアダプタコードは影響を受けません。`aiohttp.ClientError`をキャッチすることができます。両方の方法を共存させることができます。新規コードは`sdk.client` + ErisPulseの例外体系を使用することを推奨します。

## Botステータス管理

AdapterManagerにはBotのステータス追跡システムが内蔵されており、登録されたすべてのBotのオンラインステータス、アクティブ時間、メタ情報を自動的に管理します。

### 自動発見メカニズム

アダプタが`adapter.emit()`でイベントを送信するとき、フレームワークは自動的にイベント内の`self`フィールドをチェックします：

- **metaイベント**：`detail_type`に応じて対応する操作を実行（connectでBotを登録、disconnectでオフラインをマーク、heartbeatでアクティブ時間を更新）
- **通常イベント**（message/notice/request）：Botを自動的に発見し、アクティブ時間を更新

```python
# selfフィールドを含むすべてのイベントが自動発見をトリガー
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123"は自動的に登録（初めて出現した場合）され、アクティブ時間を更新
```

### Metaイベントタイプ

| `detail_type` | 説明 | フレームワークの動作 |
|---|---|---|
| `connect` | Bot接続 | Botを登録し、`adapter.bot.online`ライフサイクルイベントをトリガー |
| `disconnect` | Bot切断 | Botをオフラインとマークし、`adapter.bot.offline`ライフサイクルイベントをトリガー |
| `heartbeat` | Botハートビート | Botのアクティブ時間とメタ情報を更新 |

### アダプタによるMetaイベント送信

`emit_meta()`を使用すれば一行でMetaイベントを送信できます：

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # 一行でconnectイベントを送信
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="私のロボット")

    async def _on_bot_disconnect(self, bot_id: str):
        await self.emit_meta("disconnect", bot_id)
```

手動で構築する方法（旧方式も互換性あり）もサポートしています：

```python
await self.adapter.emit({
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": bot_id}
})
```

### `self`フィールドの拡張情報

`self`フィールドには必須の`platform`と`user_id`の他に、以下のオプションフィールドもサポートされています：

| フィールド | 説明 |
|---|---|
| `user_name` | Botのユーザー名 |
| `nickname` | Botのニックネーム |
| `avatar` | BotのアバターURL |
| `account_id` | 多アカウント識別子 |

### Botステータスの照会

```python
from ErisPulse import sdk

# 単一のBot情報を取得
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# すべてのBotをリスト表示
all_bots = sdk.adapter.list_bots()

# 指定プラットフォームのBotをリスト表示
platform_bots = sdk.adapter.list_bots("myplatform")

# Botがオンラインかどうかをチェック
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# 完全なステータスサマリーを取得（WebUI表示に適した）
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

### Botライフサイクルの監視

```python
from ErisPulse import sdk

@sdk.lifecycle.on("adapter.bot.online")
async def on_bot_online(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Botがオンライン: {platform}/{bot_id}")

@sdk.lifecycle.on("adapter.bot.offline")
async def on_bot_offline(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Botがオフライン: {platform}/{bot_id}")
```

## 関連ドキュメント

- [アダプタ開発入門](getting-started.md) - 最初のアダプタを作成する
- [SendDSL 詳解](send-dsl.md) - メッセージ送信を学ぶ
- [アダプタのベストプラクティス](best-practices.md) - 高品質なアダプタを開発する