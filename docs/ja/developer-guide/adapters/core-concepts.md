# アダプタのコア概念

> [!TIP]
> **この記事を読むべきタイミング**：アダプタ開発経路の必須読物（BaseAdapter / SendDSL / ライフサイクル等のコアメカニズムの完全な説明）。立ち上げだけなら [アダプタ開発入門](getting-started.md) を先に読むと良い。"なぜ"という疑問が生じたときは、この記事を参照。

この記事では、アダプタの動作メカニズムを説明します：AdapterManager がどのようにアダプタを登録・イベントを配信するか、`BaseAdapter` が初期化時に何をしてくれたか、設定と複数アカウントの宣言方法など。アダプタを開発する際に"なぜこのように書くのか"という疑問が生じたときは、ここを参照してください。

## アダプタアーキテクチャ

### コンポーネント関係

```
正方向変換（受信方向）                           逆方向変換（送信方向）
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ プラットフォーム独自イベント     │                        │ モジュール構築メッセージ     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │  アダプタ (MyAdapter) │   │ Send.Raw_ob12()  │
│  Converter       │   │ ┌──────────────┐ │   │ (逆方向変換エントリポイント)   │
│  (イベント変換器)    │──→│ │              │ │   │                  │
│                  │   │ │              │ │   │                  │
└────────┬─────────┘   │ └──────────────┘ │   └────────┬─────────┘
         │                   └──────────────────┘            │
         ↓                                           ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ プラットフォーム API 呼び出し    │
                       │ OneBot12 標準イベント │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓              ┌──────────────────┐
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
- **正方向変換**（Converter）：プラットフォーム独自イベント → OneBot12 標準イベント、元データは `{platform}_raw` に保持
- **逆方向変換**（Raw_ob12）：OneBot12 メッセージセグメント → プラットフォーム API 呼び出し、返却は標準レスポンス形式

## AdapterManager アダプタマネージャー

`AdapterManager` は ErisPulse アダプタシステムのコアコンポーネントで、すべてのプラットフォームアダプタの登録、起動、停止、イベント配信を担当します。

### コア機能

- **アダプタ登録**：複数のプラットフォームアダプタの登録と管理
- **ライフサイクル管理**：アダプタの起動と停止を制御
- **イベント配信**：OneBot12 標準イベントとプラットフォーム独自イベントの配信
- **設定管理**：アダプタの有効/無効ステータスの管理
- **ミドルウェアサポート**：OneBot12 イベントミドルウェアのサポート

### 基本的な使用方法

```python
from ErisPulse import sdk

# アダプタの登録（通常 Loader が自動的に実行）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# すべてのアダプタを起動
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

**起動の流れ**：

1. `adapter.start` ライフサイクルイベントを送信
2. `adapter.status.change` イベントを送信（starting）
3. 各アダプタを並列に起動
4. 起動に失敗した場合は自動的に再試行（指数バックオフ戦略）
5. 起動成功後 `adapter.status.change` イベントを送信（started）

**再試行メカニズム**：

- 最初の4回の再試行：60秒、10分、30分、60分
- 5回目以降：3時間固定間隔

#### アダプタの停止

```python
# すべてのアダプタを停止
await sdk.adapter.shutdown()
```

**停止の流れ**：

1. `adapter.stop` ライフサイクルイベントを送信
2. すべてのアダプタの `shutdown()` メソッドを呼び出す
3. ルーティングサーバーを停止
4. イベントハンドラをクリア
5. `adapter.stopped` ライフサイクルイベントを送信

### 設定管理

#### プラットフォームのステータス確認

```python
# プラットフォームが登録されているか確認
exists = sdk.adapter.exists("myplatform")

# プラットフォームが有効かどうか確認
enabled = sdk.adapter.is_enabled("myplatform")

# in 演算子を使用
if "myplatform" in sdk.adapter:
    print("プラットフォームが存在し、有効です")
```

#### プラットフォームのリスト

```python
# すべての登録済みプラットフォームをリスト
platforms = sdk.adapter.list_registered()

# すべてのプラットフォームとそのステータスをリスト
status_dict = sdk.adapter.list_items()
# 戻り値: {"platform1": true, "platform2": false, ...}

# 有効なプラットフォームのリストを取得
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### イベントのリスニング

#### OneBot12 標準イベント

```python
from ErisPulse import sdk

# すべてのプラットフォームの標準メッセージイベントをリッスン
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"OneBot12 メッセージを受け取りました: {data}")

# 特定のプラットフォームの標準メッセージイベントをリッスン
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"myplatform メッセージを受け取りました: {data}")

# すべてのイベントをリッスン
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"イベントを受け取りました: {data.get('type')}")
```

#### プラットフォーム独自イベント

```python
# 特定のプラットフォームの独自イベントをリッスン
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"独自イベントを受け取りました: {data}")

# すべてのプラットフォームの独自イベントをリッスン（ワイルドカード）
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"独自イベントを受け取りました: {data}")
```

#### イベント配信メカニズム

`adapter.emit(event_data)` を呼び出すと：

1. **ミドルウェア処理**：すべての OneBot12 ミドルウェアを実行
2. **標準イベント配信**：マッチする OneBot12 イベントハンドラに配信
3. **独自イベント配信**：元データがあれば、独自イベントハンドラに配信

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
    print(f"イベントを処理中: {data.get('type')}")
    return data  # 必須でデータを返す

@sdk.adapter.middleware
async def filter_middleware(data):
    """イベントフィルタリングミドルウェア"""
    # 不要なイベントをフィルタリング
    if data.get("type") == "notice":
        return None  # None を返すとミドルウェアチェーンは該当値を無視し、元のデータを次の処理に渡す
    return data  # 必須でデータを返して次の処理に渡す
```

#### ミドルウェアの戻り値契約

| 戻り値 | 行動 |
|--------|------|
| `dict` | イベントペイロードを上書き（次の処理は改写後のイベントを受け取る） |
| `None` | 通過、ペイロードは変更なし（WARNING ログ出力されるため、明示的に `return data` を推奨） |
| `False` | **拒否**：イベントは破棄され、どの処理にも渡らず、出力副作用も一切ない |

拒否は、ファイアウォール、リクエスト制限、ブラックリストなど、"イベントレベルで直接破棄"するシナリオに適しています（以前は高優先度のイベントハンドラで回避するしかありませんでした）。拒否時は、TRACE ログが出力され、`adapter.event.blocked` ライフサイクルフックがトリガーされ、`middleware` ミドルウェア名、完全な `event`、`platform` / `event_type` / `detail_type` が渡され、"なぜイベントが応答しなかったのか"を調査するのに便利です：

```python
@sdk.adapter.middleware
async def rate_limit_middleware(data):
    """リクエスト制限ミドルウェア"""
    if _is_rate_limited(data):
        return False  # 拒否：イベントは破棄
    data["rate_marked"] = True
    return data

@sdk.lifecycle.on("adapter.event.blocked")
async def on_event_blocked(data):
    print(f"イベントは {data['middleware']} によって拒否されました: {data['event_type']}")
```

#### ミドルウェアの実行順序

ミドルウェアは登録順に実行され、後から登録されたミドルウェアが先に実行されます。

> **注意**：ミドルウェアが `None` を返した場合（`return data` を忘れている場合）、フレームワークはその返り値を無視して元のデータを次の処理に渡し、警告レベルのログを出力します。これにより、1つのミドルウェアのミスがイベントチェーン全体を中断することはありません。

```python
# 登録順
sdk.adapter.middleware(middleware1)  # 最後に実行
sdk.adapter.middleware(middleware2)  # 中間に実行
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
    
    # __init__ をオーバーライドする必要はない。フレームワークが自動的に処理する：
    # - self.sdk, self.logger
    # - self.cfg（型安全な設定インスタンス、リアルタイム読み取り）
    # - self.Send, self.Request
    
    async def start(self):
        """アダプタを起動する（必須実装）"""
        cfg = self.cfg  # 自動的にロードされる型安全な設定
        pass
    
    async def shutdown(self):
        """アダプタを停止する（必須実装）"""
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
        cfg = self.cfg  # 型安全でリアルタイムに読み取り
        if not cfg.token:
            raise ValueError("Token が設定されていません")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### 複数アカウント設定

`BotAccountConfig` 基底クラスは `enabled` と `name` フィールドを提供します。ほとんどのアダプタは、プラットフォームプロトコルやログイン応答から自動的に bot_id を取得できます。イベント変換時にアカウント設定に注入されます。：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

# ほとんどのアダプタ：bot_id は実行時に自動的に取得され、設定は不要
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Token"},
        "required": True,
    })

# ログイン時に bot_id を取得できない場合、ユーザーに設定してもらう
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

フィールドの metadata は TOML 注釈生成と WebUI フォームレンダリングの両方に使用されます：

```python
metadata = {
    "description": str | dict,  # フィールドの説明（i18n をサポート）
    "required": bool,         # 必須フィールドか（検証 + WebUI 必須マーク）
    "secret": bool,           # 敏感フィールドか（WebUI で *** に表示、ログで脱敏）
    "example": bool,          # ファイルに書き込まないフラグ：config.toml に書き込まない（デフォルト値/テンプレートは除外）、config.full.example にのみレンダリング；schema に "example": true が付いていると、CLI 設定ガイドはデフォルトでスキップ；ユーザーが手動で設定すると通常永続化
    "min": number, "max": number,  # 数値範囲検証
    "ui": {                   # WebUI コントロール設定（旧名 "webui" は互換性あり）
        "widget": str,        # コントロールタイプ: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # グループ: "basic" | "advanced" | "connection" 等
        "order": int,         # ソートウェイト（小さいほど前に表示）
        "options": list,      # select コントロールの選択肢 [{label, value}]、label は i18n をサポート
        "placeholder": str | dict,  # 入力欄のプレースホルダー（i18n をサポート）
    },
    "extra": dict,            # 余分な拡張フィールド（schema に透かし渡す）
}
```

すべてのユーザーが見られるテキストフィールドは i18n をサポートし、統一的に `{"i18n": "key", "default": "テキスト"}` 形式を使用し、純粋な文字列はそのまま透かし渡します（後方互換性）。サポートされる i18n フィールド：

| フィールド | 位置 | 说明 |
|------|------|------|
| `description` | field metadata | フィールドの説明 |
| `options[].label` | `ui.options` | select コントロールの選択肢のラベル |
| `placeholder` | `ui.placeholder` | 入力欄のプレースホルダー |
| `group_labels` | `_schema_meta` | グループの表示名（ダッシュボードのセクションタイトル） |

i18n を使用する場合、翻訳キーを i18n システムに事前に登録する必要があります（[i18n ドキュメント](../../advanced/i18n.md#配置字段多语言) を参照）。

**description / placeholder / options label** の例：

```python
token: str = field(
    default="",
    metadata={
        "description": {"i18n": "my_adapter.token", "default": "Bot Token"},
        "ui": {
            "widget": "text",
            "placeholder": {"i18n": "my_adapter.token.ph", "default": "Token を入力してください"},
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
                {"label": "純粋な文字列のラベル", "value": "b"},  # 純粋な文字列はそのまま透かし渡す
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

フレームワークの `resolve_config_schema()` は現在の言語に応じて上記のすべてのフィールドの i18n キーを自動的に解決します；`get_config_schema()` は i18n 辞書をそのまま透かし渡し、フロントエンドが独自に解決します。

#### docstring から自動生成されるフィールド説明（v2.8.0+）

metadata に `description` を宣言していないフィールドは、フレームワークが設定クラスの docstring からフィールド説明を自動的に抽出してバックアップとして使用します。2つの一般的なスタイルをサポートします（混在可）：

```python
@dataclass
class MyConfig(BaseConfig):
    """
    MyAdapter 配置

    :ivar endpoint: プラットフォーム API アドレス        # reST スタイル
    :ivar timeout: リクエストタイムアウト秒数
    """

    endpoint: str = "https://api.example.com"   # metadata description がない → コメント/説明を docstring から取得
    timeout: int = 30

    # Google スタイルもサポート（Attributes: セグメント）：
    # Attributes:
    #     endpoint: プラットフォーム API アドレス
```

優先順位：**metadata description > docstring フィールド説明 > 空**。i18n 辞書形式の description は影響を受けません（常に優先されます）。

#### 嵌套設定（v2.8.0+）

フィールドの型がネストされた dataclass の場合、フレームワークは再帰的に処理します：schema は `"type": "table"` + `"fields"` サブツリーで保持され（WebUI は可展開のネストされたグループとしてレンダリング）、TOML テンプレートは `[サブテーブル]` セクションとしてレンダリングされ、デフォルト値、埋め込み、検証、i18n 解析はすべて再帰的に有効になります。

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

> 嵌套型は直接型注釈を使用することを推奨します；文字列注釈（遅延評価の場面）は、タイプが配置クラスのモジュール全体、`__qualname__` 外側のクラス名前空間、またはクラス属性から名前で解決できることを保証する必要があります。

#### 保存しない example フィールド（v2.8.0+）

```python
gc_interval: int = field(default=300, metadata={"example": True})
```

`example: True` を持つフィールド：

- `config.toml` に書き込まれない（アダプタ/モジュールの設定テンプレートとデフォルト値は除外、実行時はコードのデフォルト値を使用）
- `config.full.example` にのみレンダリングされる（ユーザーが参考として手動で `config.toml` にコピーする）
- schema には `"example": true` マークが付く（ポータルは表示戦略を独自に決定）、CLI 設定ガイドはデフォルトでスキップ
- ユーザーがこのキーを手動で設定すると、通常永続化され、通常のホットアップデート（ユーザーの明示的な意図が優先）

"冗長でほとんど触れない"高度な設定項目に適しており、ユーザーの `config.toml` を最小限に保ちます。

> ⚠️ `_schema_meta` はクラスレベルのメタデータ（設定フィールドではない）。dataclass のクラス本体内で宣言する場合は、`ClassVar` 注釈を付ける必要があります（`_schema_meta: ClassVar[dict] = {...}`）、そうでないと dataclass は普通のフィールドと見なされます。フレームワークは下線付きのフィールドを防御的に除外しています（設定テンプレート、デフォルト値、検証の出力には一切含まれません）、しかし、規範的な宣言を推奨します。

### 宣言的翻訳キー（v2.7.0+）

アダプタは `ConfigClass` を宣言するのと同じように、`I18nClass` というネストされたクラスを使って翻訳キーを一括で宣言できます。フレームワークは `__init__` 階段（設定テンプレート生成の前）で、宣言されたすべての翻訳キーを自動的に登録し、設定説明で参照される i18n キーがテンプレート生成時に利用可能になるようにします。

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

> ``I18nKey.default`` は**言語に依存しないバックアップテキスト**で、どの言語にも登録されません。翻訳を有効にするには、少なくとも1つの言語パラメータを明示的に渡す必要があります。

詳細な使い方（キーのパスルール、明示的な key パラメータなど）は [i18n ドキュメント](../../advanced/i18n.md#推荐写法通过-i18nclass-声明翻译键-v270) を参照してください。

### 宣言的イベント拡張メソッド（v2.7.0+）

アダプタは `EventMixin` を使ってプラットフォーム固有のイベント拡張メソッドを一括で宣言し、フレームワークが自動的に現在のプラットフォームに登録します。

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

登録後、イベントオブジェクトはこれらのメソッドを直接呼び出せます：

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] 公式メッセージを受信しました")
```

> アダプタのイベント拡張メソッドは自身のプラットフォーム（``self._platform``）に登録されます。モジュールで跨プラットフォームのイベント拡張が必要な場合は、従来の ``register_event_mixin()`` API を使用してください。

#### アカウント解決

アダプタが `call_api` を実装する際、アカウント識別子を具体的なアカウント設定に解決する必要があります。`Send` / `Api` チェーンに渡される `account_id`（`Using()` またはイベントチェーンのバインド結果）が解決の対象です：

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: アカウント名, account: 設定インスタンス
```

解決戦略：アカウント名マッチ → `bot_id` フィールドマッチ → 他の str フィールドマッチ → 最初の有効アカウント。

### 設定のホットアップデート

サブクラスは `on_config_update()` をオーバーライドして設定変更に反応できます：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Token が更新されました、再接続します")
```

### 初期化プロセス

フレームワークは `BaseAdapter.__init__(self, sdk=None)` で自動的に以下の作業を行います：

1. **SDK リファレンス**：`self.sdk`、`self.logger` を設定
2. **Send/Request ファクトリー**：`self.Send` と `self.Request` を作成
3. **設定テンプレート**：`ConfigClass` を宣言した場合、初めて自動的にデフォルト設定テンプレートを生成
4. **アカウントテンプレート**：`AccountConfigClass` を宣言した場合、初めて自動的にデフォルトアカウントテンプレートを生成
5. **EventMixin 登録**：`EventMixin` を宣言した場合、`AdapterManager` がプラットフォーム名を注入した後に自動的に登録

設定は `self.cfg` / `self.accounts` でリアルタイムに読み取り（毎回設定ストアから最新値を読み取り）。`self.config` は `self.cfg` の互換エイリアスとして使用できます。

ほとんどのアダプタは `__init__` をオーバーライドする必要はありません。初期化をカスタマイズする必要がある場合：

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
        """Send 嵌套クラス、BaseAdapter.Send から継承"""
        pass
```

### 利用可能な属性

`Send` クラスは呼び出し時に自動的に以下の属性を設定します：

| 属性 | 说明 | 設定方法 |
|-----|------|---------|
| `_target_id` | 目標ID | `To(id)` または `To(type, id)` |
| `_target_type` | 目標タイプ | `To(type, id)` |
| `_target_to` | 簡易目標ID | `To(id)` |
| `_account_id` | 送信アカウントID | `Using(account_id)` |
| `_adapter` | アダプタインスタンス | 自動設定 |
| `_at_user_ids` | @ユーザーIDリスト | `At(user_id)` |
| `_reply_message_id` | 返信メッセージID | `Reply(message_id)` |
| `_at_all` | 全員@するか | `AtAll()` |

> **推奨**：`self.send_context` 属性を使って `target_type`、`target_id`、`account_id` を一括で取得する方が、個々のインスタンス変数を直接アクセスするよりも明確です。

### フレームワーク補助メソッド

| メソッド/属性 | 说明 |
|-----------|------|
| `self._apply_modifiers(message)` | At/AtAll/Reply 修飾子の状態をメッセージセグメントリストにマージする |
| `self.send_context` | `{target_type, target_id, account_id}` の辞書を返す；`account_id` が明示的に指定されていない場合は、現在のイベント配信チェーンのトリガーアカウントをデフォルトとして返す |

### 基本メソッド

アダプタは `Raw_ob12` を実装するだけで、標準メソッド（Text/Image/Voice/Video/File）は `SendDSL` 基底クラスから継承され、デフォルトで `Raw_ob12` に委任されます：

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

    # Text/Image/Voice/Video/File は基底クラスから継承され、Raw_ob12 にデフォルトで委任されるため、再実装は不要
    # プラットフォーム固有のロジックが必要な場合は、個々のメソッドをオーバーライドできる：
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

### 変換プロセス

```
プラットフォーム独自イベント
    ↓
Converter.convert()
    ↓
OneBot12 標準イベント
```

### 必須フィールド

変換後のイベントはすべて以下のフィールドを含む必要があります：

```python
{
    "id": "イベントの一意識別子",          # 同一アカウントで再送信された同じイベントは同一である必要がある（フレームワークが重複を防止）
    "time": 1234567890,           # 10桁 Unix タイムスタンプ
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

> イベント `id` はアカウント次元で指定する必要があります：同一アカウントで再送信された同じイベントは同一の `id` を持つ必要があり、異なるアカウントが同じグループ/会話でメッセージを受け取る場合、`id` は異なる必要があります（たとえば `f"{self.user_id}:{post_type}:{message_id}"`）。

### 跨アカウント重複受理（フレームワークが注入するフィールド）

多アカウントアダプタの複数のアカウントが同じグループ/会話で、同一の物理メッセージをそれぞれ受け取る場合、フレームワークは `ErisPulse.framework.cross_account_policy != "off"` のときに自動的に内容ベースの関連付け（同プラットフォーム + 同会話 + 同送信者 + 同 `alt_message` が短い時間内にある）を行い、アダプタは関与する必要はありません：

- `mark`：その後のコピーは `multi_receipt`: {"event_id": 最初に受理されたイベントのID, "self_id": 最初に受理されたアカウント} というトップレベルのフィールドを注入して通常通り配信され、モジュールはこのフィールドを読み取って裁決する
- `drop`：その後のコピーは配信の入口で直接破棄される

`multi_receipt` はフレームワークが注入するオプションのフィールドであり、アダプタの Converter は生成せず、消費しない。ポリシーがデフォルトの `off` の場合、イベント構造は既存の契約と完全に一致する。

#### 3層の重複防止メカニズムの役割分担

| メカニズム | 配置 | 拦截するもの | 判定依据 |
|------|------|----------|----------|
| イベントの冪等性重複防止 | `ErisPulse.framework.event_dedupe`（デフォルトで有効） | 同一イベント id の再接続再送信（同一接続） | イベント `id` |
| 本号エコー防止 | `ErisPulse.event.message.ignore_self`（デフォルトで有効） | 受信アカウント自身のメッセージ（送信者 == 受信アカウント） | `self.user_id` vs `user_id` |
| 跨アカウント重複受理 | `ErisPulse.framework.cross_account_policy`（デフォルト `off`、`drop` で有効） | **同一物理メッセージが他のアカウントのコピー**——多アカウントで同じグループにいる bot A が発言し、bot B も同じメッセージを受け取る —— 短い時間内に、プラットフォーム + 会話 + 送信者 + 内容が一致する内容ベースの関連付け、キーには self_id が含まれない |
| 本号エコー防止 | `ErisPulse.event.message.ignore_self`（デフォルトで有効） | 受信アカウント自身のメッセージ（送信者 == 受信アカウント） | `self.user_id` vs `user_id` |
| 跨アカウント重複受理 | `ErisPulse.framework.cross_account_policy`（デフォルト `off`、`drop` で有効） | **同一物理メッセージが他のアカウントのコピー**——多アカウントで同じグループにいる bot A が発言し、bot B も同じメッセージを受け取る —— 短い時間内に、プラットフォーム + 会話 + 送信者 + 内容が一致する内容ベースの関連付け、キーには self_id が含まれない |

**典型的なシナリオ——多アカウントで同じグループで繰り返し**：bot A が発言し、同じグループにいる他のアカウント（bot B）も同じメッセージのコピーを受け取る。`cross_account_policy = "drop"` を有効にすると、後続のアカウントのコピーは配信の入口で破棄され、どのモジュールでも1回だけ表示される。

`ignore_self` の意味と正交であり、2つの組み合わせで表示回数が決まる：

| 組み合わせ | リピーターモジュールが bot A のメッセージを見る |
|------|--------------------------|
| `drop` + `ignore_self = true`（デフォルト） | 0 または 1 回（先に来るコピーが bot A 自身の接続からブロックされた場合）——**2回になることはない** |
| `drop` + `ignore_self = false` | 恒定で1回だけ |

> `ignore_self` の意味を「自身のすべてのアカウントを除外する」に拡張しないでください：この判定は受信イベントの `self.user_id`（バインドが確立されていない窓期には失敗する）に依存し、跨アカウントの関連は内容ベースの判定であり、`self` 情報に依存しない。また、「各アカウントで受信する」は既存の跨アカウントのログ/同期系モジュールの依存であり、意味を狭めるのは暗黙の破壊です。跨アカウントの重複は `cross_account_policy` に任せるべきです。

### 変換器の例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """プラットフォーム独自イベントを OneBot12 標準形式に変換"""
        if not isinstance(raw_event, dict):
            return None
        
        # イベント ID を生成
        event_id = raw_event.get("event_id") or str(uuid.uuid4())
        
        # 時間を変換
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

### start() の2つの正しい書き方

クライアントモードのアダプタ（WebSocketクライアント、HTTPポーリングなど）は `start()` で常駐の接続ループを起動する必要があります。フレームワークは2つの書き方をサポートしていますが、**どちらか一方を選ぶ必要があります**：

**書き方1：spawn-返却式（推奨）**——`spawn_client_loop()` でループをプラットフォームに属するバックグラウンドタスクとしてスケジュールし、`start()` は即座に返ります：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # ループタスクは self._platform に属するため、shutdown でフレームワークが自動的にキャンセル
        self.spawn_client_loop(self._connect_loop())
        # start はここで終了——"起動は成功"、接続失敗はループ内で再試行

    async def _connect_loop(self):
        while True:
            try:
                await self._connect_and_receive()   # 切断は例外を投げる → 下方の退避
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(5)              # ループ内で再試行
```

**書き方2：常駐式**——`start()` で接続ループを `await` し、返り値はなくなります：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        await self._connect_loop()   # 常駐で返り値はなく、ループが例外を投げる = start 失敗
```

2つの書き方の違いと共通点：

| | spawn-返却式 | 常駐式 |
|---|---|---|
| `start()` の返り値タイミング | ループを起動した後即返り | 接続ループが終了/失敗した時（フレームワークが退避戦略で再試行） |
| 接続失敗の処理 | ループ内で例外をキャッチして退避 | 例外を上に投げ、フレームワークの再試行チェーンに任せる |
| 適用場面 | 複数接続、ルーティング登録後に他のタスクを起動する必要がある場合 | "接続即起動"のシンプルな実装 |

`spawn_client_loop(coro, *, name="client_loop")` は書き方1のスケジューラー：タスクは `self._platform` に属して登録され、`shutdown()` 時にフレームワークが自動的にキャンセルされ、タスクハンドルを自分で管理する必要がない。ループ内で未捕獲の例外は自動的にログに残る（意図した切断再接続はループ内でキャッチすること）。

> **唯一の誤った書き方は混用すること**：spawn した後に同じループを `await` すると、`start()` が即返りの意味が失われ、タスクのキャンセル経路も予測不能になる。

### 接続モードの半完成基底クラス

上記の2つの書き方の他に、最も一般的な2つの接続モードに対してフレームワークは「半完成」の基底クラスを提供しています（`ErisPulse.Core.Bases.adapter_patterns`、ルートパッケージから直接インポート可能）：`start` / `shutdown` のライフサイクルの編集はすべて基底クラスが行い、サブクラスは業務フックを実装するだけです。

#### PollingAdapter（HTTPポーリング型）

「クライアントが定期的にイベントを取得する」プラットフォーム（Telegram getUpdates型）に適しています。基底クラスはspawn-返却式で常駐ポーリングループを起動し、失敗した場合は自動的にログを記録して指数退避（基数 1 秒、上限 60 秒、成功後はゼロに戻る；定数 `POLLING_ADAPTER_BACKOFF_BASE_SECS` / `POLLING_ADAPTER_BACKOFF_MAX_SECS` は `Core/constants.py` で調整可能）：

```python
from ErisPulse import PollingAdapter

class MyAdapter(PollingAdapter):
    # ポーリング間隔はデフォルト 5 秒；ConfigClass で poll_interval フィールドを宣言すると設定値が使用され（ホットアップデート有効）
    poll_interval = 5.0

    async def fetch_events(self):
        """プラットフォーム独自イベントを一括取得（例外は基底クラスが退避、try/except は不要）"""
        resp = await self.sdk.client.get(f"{self.cfg.endpoint}/getUpdates")
        data = await resp.json()
        return data.get("result", [])

    def convert_one(self, raw):
        """1件のプラットフォーム独自イベントを OneBot12 に変換；None を返すとスキップ"""
        return self.converter.convert(raw)

    async def call_api(self, endpoint: str, **params):
        ...  # 一般のアダプタと同じ
```

最小実装面：`fetch_events` / `convert_one` / `call_api`。`start()` はループを起動した後即返り；`shutdown()` はサブクラスで処理する必要はない（ポーリングループは owner に属して自動的にキャンセルされる）。

#### WebhookAdapter（HTTPコールバック型）

「プラットフォームがコールバックをプッシュする」プラットフォームに適しています。基底クラスの `start()` はフレームワークのルーターにコールバック受信ルートを登録（最終的なパスは `/{プラットフォーム名}/webhook`、POST メソッド）、登録は `owner_scope` に含まれる——アダプタがアンロードされたときに自動的にクリーンアップされ、手動でアン登録する必要はない：

```python
from ErisPulse import WebhookAdapter

class MyAdapter(WebhookAdapter):
    def verify_request(self, request) -> bool:
        """オプションのフック：コールバックの検証（デフォルトでは通過；False を返すと基底クラスが 403 で拒絶）"""
        cfg = self.cfg
        if not cfg.token:
            return True
        auth = request.headers.get("authorization", "")
        return auth == f"Bearer {cfg.token}"

    def convert(self, payload):
        """コールバックのペイロードを OneBot12 に変換；None を返すとスキップ"""
        return self.converter.convert(payload)

    async def call_api(self, endpoint: str, **params):
        ...  # 一般のアダプタと同じ
```

最小実装面：`convert` / `call_api`（`verify_request` はオプション）。コールバックアドレスは `sdk.adapter.get_connection_info(platform)` で取得してプラットフォームのバックエンドに記入する。検証に失敗したリクエストは 403、ペイロードの解析に失敗したリクエストは 400、正常は `{"status": "ok"}` を返す。

#### 3つのモードの選択方法

| プラットフォームプロトコル | 継承 | フットスターター |
|---|---|---|
| プラットフォームが接続してくる（WebSocket サーバー） | `BaseAdapter` | `epsdk create adapter`（デフォルト ws-server） |
| 私たちが取得する（HTTP ポーリング） | `PollingAdapter` | `epsdk create adapter --template polling` |
| プラットフォームがプッシュしてくる（HTTP コールバック） | `WebhookAdapter` | `epsdk create adapter --template webhook` |

完全に実行可能な例はリポジトリの `examples/example-adapter/`（ws-server）、`examples/example-adapter-polling/`、`examples/example-adapter-webhook/` を参照してください。

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

> コールバック型のプラットフォームは、上記のルート登録/検証/クリーンアップの編集を手動で書く必要はありません——`[WebhookAdapter` 半完成基底クラス](#连接模式半成品基类) を継承し、`convert`（`verify_request` をオーバーライドする場合も可）を実装するだけです。

> **ルート情報の照会**：アダプタが登録したルート（HTTP、WebSocket、SSE）は `sdk.adapter.get_connection_info(platform)` と `sdk.router.get_module_urls(module_name)` で完全な接続アドレス（`base_url` + パス）を照会できます。[アダプタ開発入門 - 接続情報とルート発見](getting-started.md#9-连接信息与路由发现) と [SSE 支持](getting-started.md#10-sse-server-sent-events-支持) を参照してください。

## API 応答標準

フレームワークは `make_response()` と `make_error()` メソッドを使って標準化された応答を構築し、手動で応答辞書を構築する必要はありません。

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

### 手動で応答構築（旧方式、互換性あり）

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

### アカウント指定での送信

```python
# Using メソッドでアカウントを指定
my_adapter = adapter.get("myplatform")

# イベントの self.user_id を推奨（最も汎用的）
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# アカウント名で指定
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### イベントのアカウント識別子と Using の関係

フレームワークの返信メカニズムは、イベントの `self` フィールドからアカウント識別子（`account_id` が優先、`user_id` がバックアップ）を抽出し、`Using` に注入します。アダプタ開発者は、Converter が生成するアカウント識別子がアカウント設定と一致することを保証する必要があります（アカウント名または `bot_id` などのフィールド）。

**フレームワークの注入動作**：

```python
# フレームワークがアカウント識別子を抽出するロジック（account_id が優先、user_id がバックアップ）
account = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# 空でない場合に Using を注入
if account:
    send_chain = send_chain.Using(account)
```

> **重要な点**：アダプタが1つの Bot 設定のみを使用する場合でも、Converter がアカウント識別子を正しく設定している限り、フレームワークはそれを `Using` に注入します。アダプタは、この識別子が `AccountConfigClass` のアカウント名または `bot_id` などのフィールドと一致することを保証し、正しいアカウントに解析できるようにする必要があります。識別子が空の場合、フレームワークは `Using` を注入せず、この場合、送信は未指定アカウントとして処理され、最初の有効なアカウントにフォールバックします。明示的に指定された `account_id` が解析できない場合、フレームワークは WARNING を記録し、最初の有効なアカウントにフォールバックします。WARNING に含まれる `platform` / `account_id` / `account` は、アカウントに属さないイベントのソースを特定するのに使用できます。

**イベント配信チェーン内の自動バインディング**：イベントのチェーン内で送信メソッドを呼び出す際には、**明示的に `Using()` を指定する必要はありません**——フレームワークはイベント配信のエントリポイントでトリガーされたイベントのアカウント識別子を注入し、`Send` / `Api` / `Request` チェーンで明示的にアカウントが指定されていない場合、このコンテキストに基づいてデフォルトのアカウントをバインディングします（明示的な `Using()` は常に優先されます；タイマーや起動タスクなどのイベントコンテキストがない場面では、デフォルトのアカウントの意味が維持されます）。

> イベント `self.user_id` / `self.account_id` 代位の生成契約は[イベント変換標準](../../standards/event-conversion.md)を参照してください。このフィールドが恒常的に存在することがアカウント解析のバックアップ意味の前提です——存在しない場合は最初の有効なアカウントにフォールバックし、複数アカウントの場合は「デフォルトアカウントから発信」になります。

## エラー処理

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
                    self.logger.warning(f"接続に失敗しました、{wait_time}秒後に再試行します")
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### API エラー処理

```python
async def call_api(self, endpoint: str, **params):
    try:
        # 推奨する SDK 内部クライアントを使用
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

> **後方互換性**：`aiohttp.ClientSession` を使用する古いアダプタのコードは影響を受けず、`aiohttp.ClientError` をキャッチできます。2つの方法は共存できます。新しいコードでは `sdk.client` + ErisPulse の例外体系を使用することを推奨します。

## Bot 状態管理

AdapterManager には Bot の状態を追跡するシステムが内蔵されており、登録されたすべての Bot のオンライン状態、アクティブ時間、メタ情報を自動的に管理します。

### 自動発見メカニズム

アダプタが `adapter.emit()` でイベントを送信するとき、フレームワークはイベントの `self` フィールドを自動的にチェックします：

- **meta イベント**：`detail_type` に応じて対応する操作を実行（connect 登録/ disconnect でオフラインをマーク/ heartbeat でアクティブ時間を更新）
- **通常のイベント**（message/notice/request）：Bot の自動発見を行い、アクティブ時間を更新

```python
# self フィールドを含むすべてのイベントは自動発見をトリガー
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123" は自動的に登録され（初めての場合は）、アクティブ時間を更新
```

### Meta イベントタイプ

| `detail_type` | 说明 | フレームワークの動作 |
|---|---|---|
| `connect` | Bot が接続 | Bot を登録し、`adapter.bot.online` ライフサイクルイベントをトリガー |
| `disconnect` | Bot が切断 | Bot をオフラインにマークし、`adapter.bot.offline` ライフサイクルイベントをトリガー |
| `heartbeat` | Bot のハートビート | Bot のアクティブ時間とメタ情報を更新 |

### アダプタが Meta イベントを送信

送信方法（`emit_meta()` で1行送信、ハートビートイベントと手動構造化形式）は [アダプタのベストプラクティス - Bot 状態管理と Meta イベント](best-practices.md#bot-状态管理与-meta-事件) を参照してください。

### `self` フィールドの拡張情報

`self` フィールドには、必須の `platform` と `user_id` の他、以下のオプションフィールドをサポートしています：

| フィールド | 说明 |
|---|---|
| `user_name` | Bot のユーザー名 |
| `nickname` | Bot のニックネーム |
| `avatar` | Bot のアバター URL |
| `account_id` | 複数アカウントの識別子 |

### Bot 状態の照会

照会 API（`get_bot_info()` / `list_bots()` / `is_bot_online()` / `get_status_summary()`）は [アダプタシステム API - Bot 状態管理](../../api-reference/adapter-system.md#bot-状态管理) を参照してください。

### Bot のライフサイクルを監視

`adapter.bot.online` / `adapter.bot.offline` ライフサイクルイベントの表と監視の例は [アダプタシステム API - Bot 状態管理](../../api-reference/adapter-system.md#bot-状态管理) を参照してください。

## 関連ドキュメント

### 実装の詳細

- [SendDSL 詳解](send-dsl.md) - メッセージ送信の学習
- [アダプタのベストプラクティス](best-practices.md) - 高品質なアダプタの開発

### 起動手順を振り返る

- [アダプタ開発入門](getting-started.md) - 最初のアダプタの作成