# アダプタのコアコンセプト

> [!TIP]
> **この記事を読むべきタイミング**：アダプタ開発経路内では必読（BaseAdapter / SendDSL / ライフサイクル等のコアメカニズムの完全な説明）。開始するだけなら[アダプタ開発入門](getting-started.md)を先に読み、"なぜ"というレベルの疑問が生じたときに本記事を参照してください。

この記事では、アダプタの動作メカニズムを説明します：AdapterManager がどのようにアダプタを登録・イベントを配信するか、`BaseAdapter` が初期化時に何を代行するか、設定と複数アカウントをどのように宣言するか——アダプタを開発する際に「なぜこのように書くのか」という疑問が生じたときは、ここを参照してください。

## アダプタアーキテクチャ

### コンポーネントの関係

```
正方向変換（受信方向）                           逆方向変換（送信方向）
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ プラットフォームの原生イベント     │                        │ モジュールが構築したメッセージ     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │  アダプタ (MyAdapter) │   │                  │
│  Converter       │   │ ┌──────────────┐ │   │ Send.Raw_ob12()  │
│  (イベント変換器)    │──→│ │              │ │   │ (逆方向変換のエントリポイント)   │
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
- **正方向変換**（Converter）：プラットフォームの原生イベント → OneBot12 標準イベント、元データは `{platform}_raw` に保持
- **逆方向変換**（Raw_ob12）：OneBot12 メッセージセグメント → プラットフォーム API 呼び出し、返却は標準レスポンス形式

## AdapterManager アダプタ管理者

`AdapterManager` は ErisPulse アダプタシステムのコアコンポーネントで、すべてのプラットフォームアダプタの登録、起動、停止、イベント配信を管理します。

### 核心機能

- **アダプタの登録**：複数のプラットフォームアダプタを登録・管理
- **ライフサイクル管理**：アダプタの起動と停止を制御
- **イベント配信**：OneBot12 標準イベントとプラットフォーム原生イベントを配信
- **設定管理**：アダプタの有効/無効状態を管理
- **ミドルウェアサポート**：OneBot12 イベントミドルウェアをサポート

### 基本的な使用法

```python
from ErisPulse import sdk

# アダプタの登録（通常Loaderが自動的に実行）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# すべてのアダプタの起動
await sdk.adapter.startup()

# 指定のアダプタを起動
await sdk.adapter.startup(["myplatform"])
# すべてのアダプタを起動
await sdk.adapter.startup()

# アダプタのインスタンスを取得
my_adapter = sdk.adapter.get("myplatform")
# または属性でアクセス
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

**起動プロセス**：

1. `adapter.start` ライフサイクルイベントを送信
2. `adapter.status.change` イベントを送信（starting）
3. 各アダプタを並列に起動
4. 起動に失敗した場合は自動的に再試行（指数バックオフ戦略）
5. 起動成功後、`adapter.status.change` イベントを送信（started）

**再試行メカニズム**：

- 最初の4回の再試行：60秒、10分、30分、60分
- 5回目以降：3時間固定間隔

#### アダプタの停止

```python
# すべてのアダプタを停止
await sdk.adapter.shutdown()
```

**停止プロセス**：

1. `adapter.stop` ライフサイクルイベントを送信
2. すべてのアダプタの `shutdown()` メソッドを呼び出す
3. ルーティングサーバーを停止
4. イベントハンドラをクリア
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
    print("プラットフォームは存在し、有効です")
```

#### プラットフォームの一覧表示

```python
# すべての登録済みプラットフォームをリスト
platforms = sdk.adapter.list_registered()

# すべてのプラットフォームとその状態をリスト
status_dict = sdk.adapter.list_items()
# 戻り値: {"platform1": true, "platform2": false, ...}

# 有効なプラットフォームのリストを取得
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### イベントリスナー

#### OneBot12 標準イベント

```python
from ErisPulse import sdk

# すべてのプラットフォームの標準メッセージイベントをリッスン
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"OneBot12メッセージを受け取りました: {data}")

# 特定のプラットフォームの標準メッセージイベントをリッスン
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"myplatformメッセージを受け取りました: {data}")

# すべてのイベントをリッスン
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"イベントを受け取りました: {data.get('type')}")
```

#### プラットフォーム原生イベント

```python
# 特定のプラットフォームの原生イベントをリッスン
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"原生イベントを受け取りました: {data}")

# すべてのプラットフォームの原生イベントをリッスン（ワイルドカード）
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"原生イベントを受け取りました: {data}")
```

#### イベント配信メカニズム

`adapter.emit(event_data)` を呼び出すと：

1. **ミドルウェア処理**：まずすべての OneBot12 ミドルウェアを実行
2. **標準イベント配信**：マッチする OneBot12 イベントハンドラに配信
3. **原生イベント配信**：元データがあれば、原生イベントハンドラに配信

**マッチングルール**：

- 精確マッチ：`@sdk.adapter.on("message")` は `message` イベントのみマッチ
- ワイルドカード：`@sdk.adapter.on("*")` はすべてのイベントにマッチ
- プラットフォームフィルタ：`platform="myplatform"` は指定プラットフォームのイベントのみ配信

### ミドルウェア

#### ミドルウェアの追加

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """ログ記録ミドルウェア"""
    print(f"イベントを処理します: {data.get('type')}")
    return data  # 必須でデータを返す

@sdk.adapter.middleware
async def filter_middleware(data):
    """イベントフィルタミドルウェア"""
    # 不要なイベントをフィルタ
    if data.get("type") == "notice":
        return None  # 戻り値が None の場合、ミドルウェアチェーンはその返り値を無視し、元のデータをそのまま次に渡す
    return data  # 必須でデータを返して次に渡す
```

#### ミドルウェアの返り値契約

| 返り値 | 挙動 |
|--------|------|
| `dict` | イベントペイロードを上書き（後続のハンドラは変更後のイベントを受け取る） |
| `None` | ファイル：ペイロードを変更せず（出力 WARNING メッセージが推奨される、明示的に `return data` を返す） |
| `False` | **拒否**：イベントは破棄され、どのハンドラにも渡らず、出力副作用も一切ない |

拒否はイベントレベルで直接破棄するシナリオ（以前は高優先度のイベントハンドラで回避する必要があった）に適しています。拒否された場合、フレームワークは TRACE ログを出力し、`adapter.event.blocked` ライフサイクルフックをトリガーします（`middleware` ミドルウェア名、完全な `event`、`platform` / `event_type` / `detail_type` が含まれる）。これにより、"イベントがなぜ応答しないのか"のトラブルシューティングが容易になります：

```python
@sdk.adapter.middleware
async def rate_limit_middleware(data):
    """リクエスト制限ミドルウェア"""
    if _is_rate_limited(data):
        return False  # 拒否：イベントは破棄される
    data["rate_marked"] = True
    return data

@sdk.lifecycle.on("adapter.event.blocked")
async def on_event_blocked(data):
    print(f"イベントは {data['middleware']} によって拒否されました: {data['event_type']}")
```

#### ミドルウェアの実行順序

ミドルウェアは登録順に実行され、後で登録されたミドルウェアが先に実行されます。

> **注意**：ミドルウェアが `None` を返した場合（`return data` を忘れている場合）、フレームワークはその返り値を無視して元のデータをそのまま次に渡し、warning レベルのログを出力します。これにより、個々のミドルウェアのミスがイベントチェーン全体の中断を引き起こすことはありません。

```python
# 登録順
sdk.adapter.middleware(middleware1)  # 最後に実行
sdk.adapter.middleware(middleware2)  # 中間実行
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
# 属性名でアクセス（大文字小文字を区別しない）
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
    
    # __init__ をオーバーライドする必要はない、フレームワークが自動的に処理する：
    # - self.sdk, self.logger
    # - self.cfg（型安全な設定インスタンス、リアルタイム読み取り）
    # - self.Send, self.Request
    
    async def start(self):
        """アダプタの起動（必須実装）"""
        cfg = self.cfg  # 自動的にロードされる型安全な設定
        pass
    
    async def shutdown(self):
        """アダプタの停止（必須実装）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォーム API を呼び出す（必須実装）"""
        pass
```

### 設定管理

フレームワークは宣言的設定管理を提供し、dataclass を使って設定構造を定義し、フレームワークが自動的にロード、検証、テンプレート生成を処理します。

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
        cfg = self.cfg  # 型安全、リアルタイム読み取り
        if not cfg.token:
            raise ValueError("Tokenが設定されていません")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### 複数アカウント設定

`BotAccountConfig` 基底クラスは `enabled` と `name` フィールドを提供します。ほとんどのアダプタは、プラットフォームプロトコルやログイン応答から自動的に bot_id を取得できます。イベント変換時にアカウント設定に注入されます。：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

# 多くのアダプタ：bot_id は実行時に自動的に取得され、設定は不要
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Token"},
        "required": True,
    })

# ログイン時に bot_id を取得できない場合、ユーザーに設定を入力させる
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

フィールドの metadata は TOML コメント生成と WebUI フォームレンダリングの両方に役立ちます：

```python
metadata = {
    "description": str | dict,  # フィールドの説明（i18n をサポート）
    "required": bool,         # 必須かどうか（検証 + WebUI 必須マーク）
    "secret": bool,           # かどうか（WebUI では *** として表示、ログでは脱敏）
    "example": bool,          # ファイルに書き込まないフラグ：config.toml には書き込まない（デフォルト値/テンプレートは除外）、config.full.example にのみレンダリング；schema に "example": true が付いていれば、CLI 設定ウィザードはデフォルトでスキップする；ユーザーが手動で設定した後は通常永続化される
    "min": number, "max": number,  # 数値の範囲検証
    "ui": {                   # WebUI コントロールの設定（旧名 "webui" は互換性あり）
        "widget": str,        # コントロールの種類: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # グループ: "basic" | "advanced" | "connection" など
        "order": int,         # ソートの重み（小さいほど前に表示）
        "options": list,      # select コントロールの選択肢 [{label, value}]、label は i18n をサポート
        "placeholder": str | dict,  # 入力欄のプレースホルダ（i18n をサポート）
    },
    "extra": dict,            # 余分な拡張フィールド（schema に透かし渡す）
}
```

すべてのユーザーが見られるテキストフィールドは i18n をサポートし、一貫して `{"i18n": "key", "default": "text"}` 形式を使用し、純粋な文字列はそのまま透かし渡す（後方互換性）。サポートされる i18n フィールド：

| フィールド | 位置 | 説明 |
|------|------|------|
| `description` | field metadata | フィールドの説明 |
| `options[].label` | `ui.options` | select コントロールの選択肢ラベル |
| `placeholder` | `ui.placeholder` | 入力欄のプレースホルダ |
| `group_labels` | `_schema_meta` | 分グループの表示名（ダッシュボードのセクションタイトル） |

i18n を使用する場合、翻訳キーを i18n システムに事前に登録する必要があります（[i18nドキュメント](../../advanced/i18n.md#設定フィールド多言語)を参照）。

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
                {"label": "純粋な文字列ラベル", "value": "b"},  # 純粋な文字列はそのまま透かし渡す
            ],
        },
    },
)
```

**group_labels** の例（設定クラスの定義後に宣言）：

```python
MyConfig._schema_meta = {
    "group_labels": {
        "basic": {"i18n": "my_adapter.group.basic", "default": "基本設定"},
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "高度設定"},
    }
}
```

フレームワークの `resolve_config_schema()` は現在の言語に応じて上記のすべてのフィールドの i18n キーを自動的に解析します；
`get_config_schema()` は i18n ディクショナリをそのまま透かし渡し、フロントエンドが独自に解析します。

#### docstring からフィールド説明を自動生成（v2.8.0+）

metadata に `description` を宣言していないフィールドの場合、フレームワークは設定クラスの docstring からフィールド説明を自動的に抽出してバックアップとして使用します。2つの一般的なスタイルがサポートされています（混在可能）：

```python
@dataclass
class MyConfig(BaseConfig):
    """
    MyAdapter 配置

    :ivar endpoint: プラットフォーム API アドレス        # reST スタイル
    :ivar timeout: リクエストタイムアウト秒数
    """

    endpoint: str = "https://api.example.com"   # metadata description がない → docstring から説明/説明を取得
    timeout: int = 30

    # Google スタイルもサポート（Attributes: セグメント）：
    # Attributes:
    #     endpoint: プラットフォーム API アドレス
```

優先順位：**metadata description > docstring フィールド説明 > 空**。
i18n ディクショナリ形式の description は影響を受けません（常に優先されます）。

#### 嵌套設定（v2.8.0+）

フィールドの型がネストされた dataclass の場合、フレームワークは再帰的に処理します：schema は `"type": "table"` + `"fields"` のサブツリーを保持します（WebUI では折りたたみ可能なネストされたグループとしてレンダリング）、TOML テンプレートは `[サブテーブル]` セクションとしてレンダリングされ、デフォルト値 / 埋め込み / 検証 / i18n 解析は再帰的に有効になります。

```python
@dataclass
class RetryConfig(BaseConfig):
    """リトライ戦略

    :ivar max_retries: 最大リトライ回数
    """
    max_retries: int = 3
    backoff: float = 0.5

@dataclass
class MyConfig(BaseConfig):
    """MyAdapter 配置"""
    endpoint: str = "https://api.example.com"
    retry: RetryConfig = field(default_factory=RetryConfig)   # 嵌套設定セグメント
```

生成される TOML テンプレート：

```toml
endpoint = "https://api.example.com"

[retry]
# 最大リトライ回数
max_retries = 3
backoff = 0.5
```

> 嵌套型は直接型注釈を使用することを推奨します；文字列注釈（遅延評価の場面など）は、タイプが設定クラスの所在モジュール全体、`__qualname__` 外側のクラス名前空間、またはクラス属性から名前で解決できることを保証する必要があります。

#### ファイルに書き込まない example フィールド（v2.8.0+）

```python
gc_interval: int = field(default=300, metadata={"example": True})
```

`example: True` を持つフィールド：

- `config.toml` に書き込まれない（アダプタ/モジュールの設定テンプレートとデフォルト値は除外）、実行時はコードのデフォルト値を使用
- `config.full.example` にのみレンダリングされる（ユーザーが参考用に `config.toml` に手動でコピーする）
- schema には `"example": true` がマークされる（パネルは独自に表示戦略を決定）、CLI 設定ウィザードはデフォルトでスキップ
- ユーザーがこのキーを手動で設定した後は通常永続化され、通常のホットアップデート（ユーザーの明示的な意図が優先）

`"冗長でほとんど触れない"` 高度な設定項目に適しており、ユーザーの `config.toml` を最小限に保つことができます。

> ⚠️ `_schema_meta` はクラスレベルのメタデータ（設定フィールドではない）。dataclass のクラス本体内で宣言する場合、`ClassVar` 注釈を付ける必要があります（`_schema_meta: ClassVar[dict] = {...}`）、そうでなければ dataclass は普通のフィールドとして扱われます。フレームワークはアンダースコアで始まるフィールドを防御的に除外しています（どの schema / テンプレート / デフォルト値 / 検証出力にも含まれません）、ただし規範的な宣言をお勧めします。

### 宣言式翻訳キー（v2.7.0+）

アダプタは `ConfigClass` を宣言するのと同じように、`I18nClass` というネストされたクラスを使って翻訳キーを一括宣言することができます。フレームワークは `__init__` 階段（設定テンプレート生成の前）に自動的に宣言されたすべての翻訳キーを登録し、設定説明で参照される i18n キーがテンプレート生成時に利用可能になるようにします。

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

> ``I18nKey.default`` は**言語に依存しないバックアップテキスト**であり、どの言語にも登録されません。翻訳を有効にするには、少なくとも1つの言語パラメータを明示的に渡す必要があります。

詳細な使い方（キーのパスルール、明示的な key パラメータなど）は[翻訳ドキュメント](../../advanced/i18n.md#推奨書き方-i18nclass-を使って翻訳キーを宣言する-v270)を参照してください。

### 宣言式イベント拡張メソッド（v2.7.0+）

アダプタは `EventMixin` を使ってプラットフォーム固有のイベント拡張メソッドを一括宣言し、フレームワークが自動的に現在のプラットフォームに登録します。

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    class EventMixin:
        def get_chat_name(self):
            """チャット名を取得"""
            return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

        def is_official_message(self):
            """公式メッセージかどうかを判断"""
            raw = self.get("myplatform_raw", {})
            return raw.get("sender", {}).get("is_official", False)
```

登録後、イベントオブジェクトは直接これらのメソッドを呼び出します：

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] 公式メッセージを受信しました")
```

> アダプタのイベント拡張メソッドは自身のプラットフォーム（``self._platform``）に登録されます。
> モジュールがプラットフォーム間のイベント拡張を使用する場合は、従来の ``register_event_mixin()`` API を使用してください。

#### アカウント解決

アダプタが `call_api` を実装する際、アカウント識別子を具体的なアカウント設定に解決する必要があります。フレームワークはアカウントのバインディング（`Using()` またはイベントチェーンの自動バインディングの結果）を `account_id` として `call_api` に標準フィールドとして渡し、アダプタの実際の消費方法に応じて自動的に適応します——3つの消費形態から1つを選択できます。フレームワークはサインチャーム名と関数本体の定数を検証し、パラメータの位置に関係なく、アダプタの消費に応じて適応します。

```python
# 推奨の形態一：サインチャームに標準名を宣言
async def call_api(self, endpoint: str, account_id: str | None = None, **params):
    name, account = self._resolve_account(account_id)
    # name: アカウント名, account: 設定インスタンス

# 形態二（従来互換）：旧名 _account_id、フレームワークが account_id を旧名に書き換え後、渡す
async def call_api(self, endpoint: str, _account_id: str | None = None, **params):
    name, account = self._resolve_account(_account_id)

# 形態三：関数本体内から params から取得（定数検証で識別される）
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
```

> アダプタがアカウントフィールドを消費しない場合、フレームワークはそのフィールドを削除し（プラットフォームパラメータに漏洩しない）、1回 WARNING を出力します。単一アカウントアダプタは消費しなくてもよい（解析は最初の有効アカウントに回帰）。

解決戦略：アカウント名マッチ → `bot_id` フィールドマッチ → 他の str フィールドマッチ → 最初の有効アカウント。

**実行時識別と永続化**（2.12+）：アダプタが接続確立時 / イベント到着時に `self.update_bot_id(account_name, bot_id)` を呼び出すと、フレームワークは bot_id → アカウント登録表を維持し（解決チェーンの第一優先順位）、値が変化した際に `accounts.<アカウント名>.bot_id` を設定ストアに書き込む：再起動後にアカウントインスタンスが再構築され、bot_id が付与され、第二アカウントなどの解決はログイン後の再起動期間を必要としない（再起動ウィンドウ期間を削除）。

#### 設定のホットアップデート

サブクラスは `on_config_update()` をオーバーライドして設定変更に応答できます：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Tokenが更新されたので、再接続します")
```

### 初期化プロセス

フレームワークは `BaseAdapter.__init__(self, sdk=None)` で自動的に以下の作業を行います：

1. **SDK参照**：`self.sdk`、`self.logger` を設定
2. **Send/Requestファクトリー**：`self.Send` と `self.Request` を作成
3. **設定テンプレート**：`ConfigClass` を宣言した場合、自動的にデフォルト設定テンプレートを生成（初回）
4. **アカウントテンプレート**：`AccountConfigClass` を宣言した場合、自動的にデフォルトアカウントテンプレートを生成（初回）
5. **EventMixin登録**：`EventMixin` を宣言した場合、`AdapterManager` がプラットフォーム名を注入した後に自動的に登録

設定は `self.cfg` / `self.accounts` でリアルタイムに読み取ります（各アクセスで設定ストアから最新値を読み取ります）。`self.config` は `self.cfg` の互換別名として使用できます。

ほとんどのアダプタは `__init__` をオーバーライドする必要はありません。独自の初期化が必要な場合：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # sdkを渡す
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## Send メッセージ送信 DSL

### 継承関係

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        """Sendのネストクラス、BaseAdapter.Sendから継承"""
        pass
```

### 利用可能な属性

`Send` クラスは呼び出し時に自動的に以下の属性を設定します：

| 属性 | 説明 | 設定方法 |
|-----|------|---------|
| `_target_id` | 目標ID | `To(id)` または `To(type, id)` |
| `_target_type` | 目標タイプ | `To(type, id)` |
| `_target_to` | 簡略化した目標ID | `To(id)` |
| `_account_id` | 送信アカウントID | `Using(account_id)` |
| `_adapter` | アダプタインスタンス | 自動設定 |
| `_at_user_ids` | @ユーザー一覧 | `At(user_id)` |
| `_reply_message_id` | 返信するメッセージID | `Reply(message_id)` |
| `_at_all` | @全員かどうか | `AtAll()` |

> **推奨**：`self.send_context` 属性を使って `target_type`、`target_id`、`account_id` を一括して取得するほうが、個々のインスタンス変数を直接アクセスするよりも明確です。

### フレームワーク補助メソッド

| メソッド/属性 | 説明 |
|-----------|------|
| `self._apply_modifiers(message)` | At/AtAll/Reply モディファイアの状態をメッセージセグメントリストにマージする |
| `self.send_context` | `{target_type, target_id, account_id}` ディクショナリを返す；`account_id` が明示的に指定されていない場合、現在のイベント配信チェーンのトリガーアカウントをデフォルトとする |

### 基本メソッド

アダプタは `Raw_ob12` を実装するだけで、標準メソッド（Text/Image/Voice/Video/File）は `SendDSL` 基底クラスから継承され、デフォルトで `Raw_ob12` に委譲されます：

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """OneBot12 メッセージセグメント → プラットフォーム API（必須実装）"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    # Text/Image/Voice/Video/File は基底クラスから継承され、Raw_ob12 にデフォルトで委譲されるため、実装は不要
    # プラットフォーム固有のロジックが必要な場合、個々のメソッドをオーバーライドする：
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### チェーン式修飾メソッド

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

### 変換プロセス

```
プラットフォームの原生イベント
    ↓
Converter.convert()
    ↓
OneBot12 標準イベント
```

### 必須フィールド

変換後のイベントはすべて以下のフィールドを含まなければなりません：

```python
{
    "id": "イベントのユニークな識別子",          # 同一アカウントで同一イベントを再送する場合、同じ id にする必要があります（フレームワークが重複を検出）
    "time": 1234567890,           # 10桁の Unix タイムスタンプ
    "type": "message/notice/request/meta",
    "detail_type": "イベントの詳細タイプ",
    "platform": "プラットフォーム名",
    "message_id": "メッセージID",        # メッセージ系イベントは必須
    "self": {
        "platform": "プラットフォーム名",
        "user_id": "ロボットID"     # bot_id と一致する必要がある
    },
    "{platform}_raw": {...},       # 原始データ（必須）
    "{platform}_raw_type": "..."    # 原始タイプ（必須）
}
```

> イベント id はアカウント次元で指定する必要があります：同一アカウントで同一イベントを再送する場合、id は同じでなければなりません。異なるアカウントが同じグループ/会話で同じ物理メッセージを受け取る場合、id は異なっていなければなりません（例：`f"{self.user_id}:{post_type}:{message_id}"`）。

### 複数アカウント間の重複受理（フレームワークが注入するフィールド）

複数アカウントアダプタの複数アカウントが同じグループ/会話で、同じ物理メッセージが各アカウントに到達する場合、フレームワークは `ErisPulse.framework.cross_account_policy != "off"` の場合、自動的に内容ベースの関連付け（同プラットフォーム + 同会話 + 同送信者 + 同 `alt_message` が短い時間内に）を行い、アダプタは関与する必要はありません：

- `mark`：後続のコピーは `multi_receipt` フィールドを上層に注入して通常通り配信され、モジュールはこのフィールドを読んで独自に裁決
- `drop`：後続のコピーは配信入口で直接破棄
- **@メンション優遇**：`message` セグメントのメンションターゲットが受信アカウント自身のアイデンティティ（`self.user_id` / `self.account_id`）に一致するコピーは無条件で許容（`mark` / `drop` ともに免除）——メンションされたアカウントは必ず自分のイベントを受け取り、`drop` で誤って@駆動の多アカウントモジュールを破棄しない；@メッセージは複数アカウントで1回だけ配信される可能性があるため、@駆動モジュールは `on_at_message` 条件で1回だけ応答する

#### 会話アカウントバインディング（正確な所有権宣言）

内容ベースの関連付けは啓発的な判定（誰が先に到着したか）に依存しています。**正確な会話所有権を宣言する必要がある場合**、`ErisPulse.framework.session_accounts` 配置で会話を特定のアカウントにバインディングします：

```toml
[ErisPulse.framework.session_accounts.snowluma]
"group:643319481" = "1325859446"   # 推奨のプレフィックスキー：会話タイプ:会話ID → 所有アカウント bot_id
"643319481" = "1325859446"         # 裸のキー互換書き方：この会話IDのすべての会話タイプにバインディング
```

> プレフィックスキーは同数値の異種会話（グループ `group:123` とプライベート `user:123`）を互いに影響させないように分離します；裸のキーは互換書き方で、バインディング後はその会話IDのグループチャットとプライベートチャットがすべてバインディングされます。

- バインディングは `cross_account_policy` に依存せず有効になります（配置でバインディングすれば、この会話の重複を無効にします）：所有アカウントのイベントは通常通り配信され、他のアカウントのコピーは配信入口で破棄されます
- **@メンション優遇**は同様に有効です：メンションされた非所有アカウントのコピーは許容されます
- バインディングはリアルタイムに設定を読み込み、ホットアップデートが有効になります；バインディングされていない会話は影響を受けません
- 「1つの会話に複数のアカウントが1つのアカウントに応答させたい」展開では、内容ベースの関連付けよりも正確で、3秒のウィンドウと内容比較の啓発的エラーがありません

`multi_receipt` はフレームワークが注入するオプションフィールドで、アダプタの Converter は生成も消費もしません；ポリシーがデフォルト `off` の場合、イベント構造は既存の契約と完全に一致します。

#### 3段階の重複防止メカニズムの役割

| メカニズム | 配置 | 拦截するもの | 判定依据 |
|------|------|----------|----------|
| イベントの冪等性重複防止 | `ErisPulse.framework.event_dedupe`（デフォルト有効） | 同一イベントの再接続再送信（同じ接続） | イベント `id` |
| 本アカウントのエコー防止 | `ErisPulse.event.message.ignore_self`（デフォルト有効） | 自分のアカウントが送信したメッセージ（送信者 == 受信アカウント） | `self.user_id` vs `user_id` |
| 複数アカウントの重複受理 | `ErisPulse.framework.cross_account_policy`（デフォルト `off`、`drop` 有効） | **同一物理メッセージが他のアカウントのコピー**——複数アカウントが同じグループで bot A が発言し、bot B も同じものを1つ受け取る（メンションが自分アカウントに命中するコピーは豁免） | 内容ベースの関連（同プラットフォーム + 同会話 + 同送信者 + 同内容、短い時間内）、キーには self_id が含まれない |

**典型的なシナリオ——複数アカウントが同じグループで繰り返し発言**：bot A が発言し、同じグループの他のアカウント（bot B）も1つ受け取る。繰り返しモジュールは bot A のメッセージが2回表示されるのを見る。`cross_account_policy = "drop"` を有効にすると、他のアカウントのコピーは配信入口で破棄され、どのモジュールでも1回しか表示されない。**例外：メンション発言**——メンションされたアカウントのコピーは常に許容される（@駆動モジュールは応答に依存し、他のアカウントのコピーは破棄される）。

`ignore_self` との意味は直交し、両方を組み合わせて見える回数を決定します：

| 組み合わせ | 繰り返しモジュールが bot A のメッセージを見る |
|------|--------------------------|
| `drop` + `ignore_self = true`（デフォルト） | 0 または 1 回（先に到着したコピーが A 自身の接続経由なら ignore_self でブロックされる）——**2回は決してない** |
| `drop` + `ignore_self = false` | 恒定して丁度 1 回 |

> `ignore_self` の意味を「自身の全アカウントを除外する」に拡張するのは推奨されません：この判定は受信イベントの `self.user_id` に依存するため（バインディングが確立されていないウィンドウ期間では失敗する）、複数アカウント間の関連は内容ベースの判定であり、`self` 情報に依存しない。また、「各アカウントで受信する」は複数アカウントのログ/同期モジュールの既存の依存であり、範囲を狭めるのは暗黙の破壊です。複数アカウントの重複は `cross_account_policy` に任せるべきです。

### 変換器の例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """プラットフォーム原生イベントを OneBot12 標準形式に変換"""
        if not isinstance(raw_event, dict):
            return None
        
        # イベントIDの生成
        event_id = raw_event.get("event_id") or str(uuid.uuid4())
        
        # 時間スタンプの変換
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

### start() の2つの正しい書き方

クライアントモードのアダプタ（WebSocketクライアント、HTTPポーリングなど）は `start()` で永続的な接続ループを起動する必要があります。フレームワークは2つの書き方をサポートしていますが、**どちらか一方のみ選択してください**：

**書き方1：spawn-返却式（推奨）**——`spawn_client_loop()` でループをプラットフォームに属するバックグラウンドタスクとしてスケジュールし、`start()` は即座に返ります：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # ループタスクは self._platform に属するため、shutdown でフレームワークが自動的にキャンセル
        self.spawn_client_loop(self._connect_loop())
        # start はここで終了——"起動成功"、接続失敗はループ内でリトライ

    async def _connect_loop(self):
        while True:
            try:
                await self._connect_and_receive()   # 断線で例外 → 下方のリトライ
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(5)              # ループ内でリトライ
```

**書き方2：常駐式**——`start()` でループを `await` し、返りません：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        await self._connect_loop()   # 常駐で返りません；ループが例外を投げた場合 = start 失敗
```

2つの書き方の違いと共通点：

| | spawn-返却式 | 常駐式 |
|---|---|---|
| `start()` の返り時間 | ループを起動した後即返り | ループが終了/失敗した時（フレームワークがリトライ戦略で再試行） |
| 接続失敗処理 | ループ内で例外をキャッチしてリトライ | 例外を上昇させ、フレームワークの再試行チェーンに任せる |
| 適用場面 | 複数接続、ルーティング登録後に他のタスクを起動したい場合 | "接続即起動"のシンプルな実装 |

`spawn_client_loop(coro, *, name="client_loop")` は書き方1のスケジューラーの入り口です：タスクは `self._platform` に属する登録を行い、アダプタの `shutdown()` 時にフレームワークが属するタスクを自動的にキャンセルし、自分でタスクハンドルを管理する必要はありません；ループ内で未捕獲の例外は自動的に記録されます（意図的な切断再接続はループ内で自ら捕獲してください）。

> **唯一の誤った書き方は混用すること**：spawn の後に同じループを `await` すると、`start()` が即返り意味を失い、タスクのキャンセル経路が予測不能になります。

### 接続モードの半完成基底クラス

前節の2つの書き方の他に、最も一般的な2つの接続モードに対してフレームワークは「半完成」の基底クラス（`ErisPulse.Core.Bases.adapter_patterns`、ルートパッケージから直接インポート可能）を提供しています：`start` / `shutdown` のライフサイクルの編排はすべて基底クラスが完了し、サブクラスは業務フックのみ実装します。

#### PollingAdapter（HTTPポーリング型）

「クライアントが定期的にイベントを取得する」プラットフォーム（Telegram getUpdates型）に適しています。基底クラスはspawn-返却式で常駐ポーリングループを起動し、取得失敗は自動的に記録され指標バックオフ（基数1秒、上限60秒、成功後は0に戻る；定数 `POLLING_ADAPTER_BACKOFF_BASE_SECS` / `POLLING_ADAPTER_BACKOFF_MAX_SECS` は `Core/constants.py` で調整可能）：

```python
from ErisPulse import PollingAdapter

class MyAdapter(PollingAdapter):
    # ポーリング間隔はデフォルト5秒；ConfigClassでpoll_intervalフィールドを宣言すると設定値が優先される（ホットアップデート有効）
    poll_interval = 5.0

    async def fetch_events(self):
        """1回のプラットフォーム原生イベントを取得（基底クラスが退避を統一して処理するため、try/exceptは不要）"""
        resp = await self.sdk.client.get(f"{self.cfg.endpoint}/getUpdates")
        data = await resp.json()
        return data.get("result", [])

    def convert_one(self, raw):
        """1つの原生イベントをOneBot12に変換；Noneを返すとスキップ"""
        return self.converter.convert(raw)

    async def call_api(self, endpoint: str, **params):
        ...  # 普通のアダプタと同じ
```

最小実装面：`fetch_events` / `convert_one` / `call_api`。`start()` はループを起動した後即返り；`shutdown()` はサブクラスで処理する必要はない（ポーリングループはownerに属するため自動的にキャンセルされる）。

#### WebhookAdapter（HTTPコールバック型）

「プラットフォームがコールバックをプッシュする」プラットフォームに適しています。基底クラスの `start()` はフレームワークのrouterにコールバック受信ルートを登録（最終的なパスは `/{プラットフォーム名}/webhook`、POSTメソード）、登録は `owner_scope` に含まれる——アダプタがアンロードされた時にownerに応じて自動的にクリーンアップされるため、手動でアンロードする必要はない：

```python
from ErisPulse import WebhookAdapter

class MyAdapter(WebhookAdapter):
    def verify_request(self, request) -> bool:
        """オプションのフック：コールバックの検証（デフォルトで許可；Falseを返すと基底クラスが403で拒否）"""
        cfg = self.cfg
        if not cfg.token:
            return True
        auth = request.headers.get("authorization", "")
        return auth == f"Bearer {cfg.token}"

    def convert(self, payload):
        """コールバックのペイロードをOneBot12に変換；Noneを返すとスキップ"""
        return self.converter.convert(payload)

    async def call_api(self, endpoint: str, **params):
        ...  # 普通のアダプタと同じ
```

最小実装面：`convert` / `call_api`（`verify_request` はオプション）。コールバックアドレスは `sdk.adapter.get_connection_info(platform)` で取得してプラットフォームのバックエンドに設定する。検証に失敗したリクエストは403を返し、ペイロードの解析に失敗したリクエストは400を返し、正常なリクエストは `{"status": "ok"}` を返す。

#### 3つのモードの使い分け

| プラットフォームプロトコル | 継承 | フットスターラー |
|---|---|---|
| プラットフォームが接続してくる（WebSocketサーバー） | `BaseAdapter` | `epsdk create adapter`（デフォルト ws-server） |
| 自分が引きに行く（HTTPポーリング） | `PollingAdapter` | `epsdk create adapter --template polling` |
| プラットフォームがプッシュしてくる（HTTPコールバック） | `WebhookAdapter` | `epsdk create adapter --template webhook` |

実行可能な完全な例はリポジトリの `examples/example-adapter/`（ws-server）、`examples/example-adapter-polling/`、`examples/example-adapter-webhook/` を参照してください。

### WebSocket接続

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """WebSocketルートの登録"""
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
        """WebHookルートの登録"""
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

> 純粋なコールバック型のプラットフォームは、上記のルート登録/認証/クリーンアップの編排を手動で書く必要はありません——代わりに [`WebhookAdapter` 半成品基底クラス](#連接モード半成品基底クラス) を継承し、`convert`（`verify_request` はオプション覆写）を実装するだけです。

> **ルート情報の照会**：アダプタが登録したルート（HTTP、WebSocket、SSE）は `sdk.adapter.get_connection_info(platform)` と `sdk.router.get_module_urls(module_name)` を使って完全な接続アドレス（`base_url` + パス）を照会できます。[アダプタ開発入門 - 接続情報とルート発見](getting-started.md#9-接続情報とルート発見) と [SSE 支持](getting-started.md#10-sse-server-sent-events-支持) を参照してください。

## APIレスポンス標準

フレームワークは `make_response()` と `make_error()` メソッドを使って標準化されたレスポンスを作成します。手動でレスポンス辞書を構築する必要はありません。

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

### 手動でレスポンス構築（旧版方式は互換性あり）

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

## 複数アカウントサポート

### 宣言的設定（推奨）

`AccountConfigClass` を宣言して設定クラスを宣言した後、フレームワークは自動的に複数アカウントのロード、検証、テンプレート生成を管理します：

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
            self.logger.info(f"アカウント {name}: {account.bot_id} を起動")
            await self._connect(name, account)
    
    async def call_api(self, endpoint: str, account_id: str | None = None, **params):
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

### アカウント指定による送信

```python
# Usingメソッドでアカウントを指定
my_adapter = adapter.get("myplatform")

# イベントの self.user_id を使用する（推奨、最も汎用的）
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# アカウント名で指定
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### イベントのアカウント識別子と Using の関係

フレームワークのイベント返信メカニズムは、イベントの `self` フィールドからアカウント識別子（`account_id` が優先、`user_id` をデフォルトとして）を抽出し、`Using` に注入します。アダプタ開発者は、Converter が生成するアカウント識別子がアカウント設定（アカウント名や `bot_id` など）と一致することを保証する必要があります。

**フレームワークの注入動作**：

```python
# アカウント識別子を抽出するフレームワークのロジック（account_id が優先、user_id をデフォルトとして）
account = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# アカウント識別子が空でない場合に Using を注入
if account:
    send_chain = send_chain.Using(account)
```

> **重要な点**：アダプタが1つの Bot 設定を使用している場合でも、Converter がアカウント識別子を正しく設定している限り、フレームワークはそれを `Using` に注入します。アダプタは、この識別子が `AccountConfigClass` に定義されたアカウント名や `bot_id` などと一致することを保証する必要があります。識別子が空の場合、フレームワークは `Using` を注入せず、代わりに最初に有効なアカウントにバックアップします。

明示的に指定された `account_id` が解釈できない場合、フレームワークは WARNING を出力し、最初に有効なアカウントにバックアップします。WARNING に含まれる `platform` / `account_id` / `account` は、アカウントに属さないイベントの出所を特定するのに使用できます。

**イベント配信チェーン内の自動バインディング**：イベントの処理チェーン内で送信メソッドを呼び出す場合、**明示的に `Using()` を指定する必要はありません**——フレームワークはイベント配信の入口でトリガーイベントのアカウント識別子を注入し、`Send` / `Api` / `Request` チェーンが明示的にアカウントを指定しない場合、このデフォルトアカウントにバックアップします（明示的な `Using()` は常に優先します；タイマーや起動タスクなどイベントコンテキストのない場面ではデフォルトアカウントの意味を維持します）。イベントチェーン内の自動バインディングは ErisPulse **2.12+** が必要です。

> 事件 `self.user_id` / `self.account_id` 代位の产出契约见[事件转换标准](../../standards/event-conversion.md)；该字段恒定存在是账户解析回退语义的前提——缺失时回退第一个启用账户，多账户下即「从默认账户发出」。

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
                    self.logger.warning(f"接続失敗、{wait_time}秒後に再試行")
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### APIエラーハンドリング

```python
async def call_api(self, endpoint: str, **params):
    try:
        # 推荐使用 SDK 内置客户端
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

> **後方互換性**：`aiohttp.ClientSession` を使用する古いアダプタコードは影響を受けず、`aiohttp.ClientError` をキャッチできます。2つの方法は共存できます。新しいコードは `sdk.client` + ErisPulse の例外体系を使用することを推奨します。

## Bot 状態管理

AdapterManager には Bot 状態の追跡システムが内蔵されており、すべての登録された Bot のオンライン状態、アクティブ時間、およびメタ情報を自動的に維持します。

### 自動発見メカニズム

アダプタが `adapter.emit()` を通じてイベントを送信する場合、フレームワークはイベント内の `self` フィールドを自動的にチェックします：

- **meta イベント**：`detail_type` に応じて対応する操作（接続登録/切断でオフラインをマーク/ハートビートでアクティブ時間を更新）
- **通常イベント**（message/notice/request）：Bot の自動発見とアクティブ時間の更新

```python
# self フィールドを含むすべてのイベントが自動発見をトリガーする
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123" が自動的に登録され、アクティブ時間を更新する（初めて出現した場合）
```

### Meta イベントタイプ

| `detail_type` | 説明 | フレームワークの動作 |
|---|---|---|
| `connect` | Bot が接続 | Bot を登録し、`adapter.bot.online` ライフサイクルイベントをトリガー |
| `disconnect` | Bot が切断 | Bot をオフラインにマークし、`adapter.bot.offline` ライフサイクルイベントをトリガー |
| `heartbeat` | Bot のハートビート | Bot のアクティブ時間とメタ情報を更新 |

### アダプタが Meta イベントを送信する

送信方法（`emit_meta()` で1行送信、ハートビートイベントと手動構造化形式）は[アダプタのベストプラクティス - Bot 状態管理と Meta イベント](best-practices.md#bot-状態管理と-meta-イベント)を参照してください。

### `self` フィールドの拡張情報

`self` フィールドには必須の `platform` と `user_id` の他に、以下のオプションフィールドがサポートされています：

| フィールド | 説明 |
|---|---|
| `user_name` | Bot のユーザー名 |
| `nickname` | Bot のニックネーム |
| `avatar` | Bot のアバターの URL |
| `account_id` | 複数アカウントの識別子 |

### Bot 状態の照会

照会 API（`get_bot_info()` / `list_bots()` / `is_bot_online()` / `get_status_summary()`）は[アダプタシステム API - Bot 状態管理](../../api-reference/adapter-system.md#bot-状態管理)を参照してください。

### Bot ライフサイクルの監視

`adapter.bot.online` / `adapter.bot.offline` ライフサイクルイベントの表と監視の例は[アダプタシステム API - Bot 状態管理](../../api-reference/adapter-system.md#bot-状態管理)を参照してください。

## 関連ドキュメント

### 実装面の詳細

- [SendDSL 詳解](send-dsl.md) - メッセージ送信の学習
- [アダプタのベストプラクティス](best-practices.md) - 高品質なアダプタの開発

### 再びステップを振り返る

- [アダプタ開発入門](getting-started.md) - 最初のアダプタを作成する