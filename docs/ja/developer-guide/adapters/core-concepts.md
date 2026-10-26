# アダプタのコアコンセプト

> [!TIP]
> **この記事を読むタイミング**：アダプタ開発経路内に必須（BaseAdapter / SendDSL / ライフサイクル等の全メカニズムの詳細説明）。入門だけしたい場合は先に [アダプタ開発入門](getting-started.md) を読んで、"なぜ"の疑問が生じたらここに戻って調べる。

この記事では、アダプタの動作メカニズムを説明します。AdapterManager がどのようにアダプタを登録・イベントを分配するか、`BaseAdapter` が初期化時に何をしてくれたか、設定と複数アカウントの宣言方法など。アダプタを開発する際に「なぜこのように書くのか？」という疑問が生じたときは、ここに来て調べてください。

## アダプタアーキテクチャ

### コンポーネント関係

```
正方向変換（受信方向）                           反方向変換（送信方向）
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ プラットフォーム原生イベント     │                        │ モジュール構築メッセージ     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │  アダプタ (MyAdapter) │   │ Send.Raw_ob12()  │
│  Converter       │   │ ┌──────────────┐ │   │ (反方向変換エントリ)   │
│  (イベント変換器)    │──→│ │              │ │   │                  │
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
- **正方向変換**（Converter）：プラットフォーム原生イベント → OneBot12 標準イベント、元データは `{platform}_raw` に保持
- **反方向変換**（Raw_ob12）：OneBot12 メッセージセグメント → プラットフォーム API 呼び出し、返り値は標準レスポンス形式

## AdapterManager アダプタマネージャー

`AdapterManager` は ErisPulse アダプタシステムのコアコンポーネントで、すべてのプラットフォームアダプタの登録、起動、停止、イベント分配を管理します。

### コア機能

- **アダプタ登録**：複数のプラットフォームアダプタを登録・管理
- **ライフサイクル管理**：アダプタの起動と停止を制御
- **イベント分配**：OneBot12 標準イベントとプラットフォーム原生イベントを分配
- **設定管理**：アダプタの有効/無効状態を管理
- **ミドルウェアサポート**：OneBot12 イベントミドルウェアをサポート

### 基本的な使用法

```python
from ErisPulse import sdk

# アダプタの登録（通常は Loader が自動的に実行）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# すべてのアダプタを起動
await sdk.adapter.startup()

# 指定アダプタを起動
await sdk.adapter.startup(["myplatform"])
# すべてのアダプタを起動
await sdk.adapter.startup()

# アダプタインスタンスを取得
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

# 指定プラットフォームを起動
await sdk.adapter.startup(["platform1", "platform2"])
```

**起動フロー**：

1. `adapter.start` ライフサイクルイベントを送信
2. `adapter.status.change` イベントを送信（starting）
3. 各アダプタを並行起動
4. 起動失敗した場合は自動リトライ（指数バックオフ戦略）
5. 起動成功後 `adapter.status.change` イベントを送信（started）

**リトライメカニズム**：

- 最初の4回のリトライ：60秒、10分、30分、60分
- 5回目以降：3時間固定間隔

#### アダプタの停止

```python
# すべてのアダプタを停止
await sdk.adapter.shutdown()
```

**停止フロー**：

1. `adapter.stop` ライフサイクルイベントを送信
2. すべてのアダプタの `shutdown()` メソッドを呼び出す
3. ルーティングサーバーを閉じる
4. イベントハンドラをクリアする
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
    print(f"OneBot12メッセージを受け取りました: {data}")

# 特定プラットフォームの標準メッセージイベントを監視
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"myplatformメッセージを受け取りました: {data}")

# すべてのイベントを監視
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"イベントを受け取りました: {data.get('type')}")
```

#### プラットフォーム原生イベント

```python
# 特定プラットフォームの原生イベントを監視
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"原生イベントを受け取りました: {data}")

# すべてのプラットフォームの原生イベントを監視（ワイルドカード）
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"原生イベントを受け取りました: {data}")
```

#### イベント分配メカニズム

`adapter.emit(event_data)` を呼び出したとき：

1. **ミドルウェア処理**：まずすべての OneBot12 ミドルウェアを実行
2. **標準イベント分配**：マッチする OneBot12 イベントハンドラに分配
3. **原生イベント分配**：元データがあれば、原生イベントハンドラに分配

**マッチルール**：

- 精確マッチ：`@sdk.adapter.on("message")` は `message` イベントのみマッチ
- ワイルドカード：`@sdk.adapter.on("*")` はすべてのイベントにマッチ
- プラットフォームフィルタ：`platform="myplatform"` は指定プラットフォームのイベントのみ分配

### ミドルウェア

#### ミドルウェアの追加

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """ログ記録ミドルウェア"""
    print(f"イベントを処理しています: {data.get('type')}")
    return data  # 必ずデータを返す

@sdk.adapter.middleware
async def filter_middleware(data):
    """イベントフィルタミドルウェア"""
    # 不要なイベントをフィルタ
    if data.get("type") == "notice":
        return None  # None を返すとミドルウェアチェーンはその返り値を無視し、元のデータをそのまま次に渡す
    return data  # 必ずデータを返して次に渡す
```

#### ミドルウェアの返り値契約

| 返り値 | 行為 |
|--------|------|
| `dict` | イベントペイロードを上書き（後続のハンドラは変更後のイベントを受け取る） |
| `None` | 通過、ペイロードは変更なし（WARNING ログを出力するが、明示的に `return data` を推奨） |
| `False` | **否決**：イベントは破棄され、ハンドラには一切の副作用が発生しない |

否決はファイアウォール、リクエスト制限、ブラックリストなど、"イベントレベルで直接破棄"する場面に適しています（以前は高優先度のイベントハンドラで回避するしかありませんでした）。否決時にフレームワークは TRACE ログを出力し、`adapter.event.blocked` ライフサイクルフックをトリガーします（`middleware` ミドルウェア名、完全な `event`、`platform` / `event_type` / `detail_type` を含む）、これにより"なぜイベントが応答されなかったのか"をトラブルシューティングできます：

```python
@sdk.adapter.middleware
async def rate_limit_middleware(data):
    """リクエスト制限ミドルウェア"""
    if _is_rate_limited(data):
        return False  # 否決：イベントは破棄
    data["rate_marked"] = True
    return data

@sdk.lifecycle.on("adapter.event.blocked")
async def on_event_blocked(data):
    print(f"イベントは {data['middleware']} によって否決されました: {data['event_type']}")
```

#### ミドルウェアの実行順序

ミドルウェアは登録順に実行され、後から登録されたミドルウェアが先に実行されます。

> **注意**：ミドルウェアが `None` を返した場合（`return data` を忘れている場合）、フレームワークはその返り値を無視して元のデータをそのまま次に渡し、warning レベルのログを出力します。これにより、個々のミドルウェアのミスがイベントチェーン全体の中断を引き起こすことはありません。

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
    """アダプタ設定（宣言後、フレームワークが自動的に管理）"""
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
    # - self.cfg（型安全な設定インスタンス、リアルタイムで読み取り）
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
        cfg = self.cfg  # 型安全、リアルタイムで読み取り
        if not cfg.token:
            raise ValueError("Token が設定されていません")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### 複数アカウント設定

`BotAccountConfig` 基底クラスは `enabled` と `name` フィールドを提供します。ほとんどのアダプタはプラットフォームプロトコルやログイン応答から自動的に bot_id を取得でき、イベント変換時にアカウント設定に注入されます。：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

# 大多数のアダプタ：bot_id は実行時に自動取得、設定は不要
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Token"},
        "required": True,
    })

# ログイン時に bot_id を取得できない場合は、ユーザーに設定してもらう
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

フィールド metadata は TOML 注釈生成と WebUI フォームレンダリングの両方に使用されます：

```python
metadata = {
    "description": str | dict,  # フィールド説明（i18n をサポート）
    "required": bool,         # 必須か（検証 + WebUI 必須マーク）
    "secret": bool,           # 敏感か（WebUI では *** に表示、ログでは脱敏）
    "example": bool,          # 落盤しないフラグ：config.toml に書き込まない（デフォルト値/テンプレートは除外）、config.full.example にのみレンダリング；schema に "example": true が付いていれば、CLI 設定ウィザードはデフォルトでスキップ；ユーザーが手動で設定した後は通常の永続化を行う
    "min": number, "max": number,  # 数値範囲検証
    "ui": {                   # WebUI コントロール設定（旧名 "webui" は互換性あり）
        "widget": str,        # コントロールタイプ: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # グループ: "basic" | "advanced" | "connection" など
        "order": int,         # ソートウェイト（小さいほど先に表示）
        "options": list,      # select コントロールの選択肢 [{label, value}]、label は i18n をサポート
        "placeholder": str | dict,  # 入力欄のプレースホルダー（i18n をサポート）
    },
    "extra": dict,            # 余分な拡張フィールド（schema に透かし渡す）
}
```

すべてのユーザーが見えるテキストフィールドは i18n をサポートし、`{"i18n": "key", "default": "text"}` 形式で統一されます。純粋な文字列はそのまま透かし渡されます（後方互換性）。サポートされる i18n フィールド：

| フィールド | 位置 | 説明 |
|------|------|------|
| `description` | field metadata | フィールド説明 |
| `options[].label` | `ui.options` | select コントロールの選択肢ラベル |
| `placeholder` | `ui.placeholder` | 入力欄のプレースホルダー |
| `group_labels` | `_schema_meta` | グループ表示名（Dashboard 分区タイトル） |

i18n を使用する場合は、翻訳キーを i18n システムに事前に登録する必要があります（[i18n ドキュメント](../../advanced/i18n.md#配置フィールド多言語)を参照）。

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

**group_labels** の例（設定クラス定義後に宣言）：

```python
MyConfig._schema_meta = {
    "group_labels": {
        "basic": {"i18n": "my_adapter.group.basic", "default": "基本設定"},
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "高度設定"},
    }
}
```

フレームワークの `resolve_config_schema()` は現在の言語に応じて上記のすべてのフィールドの i18n キーを自動的に解決します。`get_config_schema()` は i18n ディクショナリをそのまま透かし渡し、フロントエンドが独自に解決します。

#### docstring から自動生成されるフィールド説明（v2.8.0+）

metadata で `description` を宣言していないフィールドは、フレームワークが設定クラスの docstring からフィールド説明を自動的に抽出してバックアップとして使用します。2 つの一般的なスタイルをサポートします（混在可能）：

```python
@dataclass
class MyConfig(BaseConfig):
    """
    MyAdapter 設定

    :ivar endpoint: プラットフォーム API アドレス        # reST スタイル
    :ivar timeout: リクエストタイムアウト秒数
    """

    endpoint: str = "https://api.example.com"   # metadata description がない → 注釈/説明は docstring から
    timeout: int = 30

    # Google スタイルもサポート（Attributes: 段）：
    # Attributes:
    #     endpoint: プラットフォーム API アドレス
```

優先順位：**metadata description > docstring フィールド説明 > 空**。i18n ディクショナリ形式の description は影響を受けません（常に優先されます）。

#### 嵌套設定（v2.8.0+）

フィールド型がネストされた dataclass の場合、フレームワークは再帰的に処理します：schema は `"type": "table"` + `"fields"` サブツリーで構成され（WebUI では折りたたみ可能なネストされたグループとしてレンダリング）、TOML テンプレートは `[サブテーブル]` セクションとしてレンダリングされ、デフォルト値、埋め込み、検証、i18n 解析はすべて再帰的に有効になります。

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
    """MyAdapter 設定"""
    endpoint: str = "https://api.example.com"
    retry: RetryConfig = field(default_factory=RetryConfig)   # 嵌套設定セクション
```

生成される TOML テンプレート：

```toml
endpoint = "https://api.example.com"

[retry]
# 最大リトライ回数
max_retries = 3
backoff = 0.5
```

> 嵌套型は直接型注釈を使うことを推奨します；文字列注釈（遅延評価の場面など）は、型が設定クラスのモジュール全体、`__qualname__` 外側のクラス名空間、またはクラス属性から名前で解決できることを保証する必要があります。

#### 落盤しない example フィールド（v2.8.0+）

```python
gc_interval: int = field(default=300, metadata={"example": True})
```

`example: True` が付いたフィールドは：

- config.toml に書き込まれない（アダプタ/モジュール設定テンプレートとデフォルト値は除外、実行時はコードのデフォルト値を使用）
- config.full.example にのみレンダリングされる（ユーザーが参考として手動で config.toml にコピーする）
- schema に `"example": true` が付いている（コンポーネントが表示戦略を独自に決定できる）、CLI 設定ウィザードはデフォルトでスキップ
- ユーザーがこのキーを手動で設定した後は通常の永続化、通常のホットアップデート（ユーザーの明示的な意図が優先）

"冗長でめったに触れない"高度な設定項目に適しており、ユーザーの config.toml を最小限に保ちます。

> ⚠️ `_schema_meta` はクラスレベルのメタデータ（設定フィールドではない）。dataclass のクラス本体で宣言する場合は、`ClassVar` 注釈を付ける必要があります（`_schema_meta: ClassVar[dict] = {...}`）、そうでないと dataclass は普通のフィールドと見なされます。フレームワークはアンダースコアで始まるフィールドを防御的に除外しています（どの schema / テンプレート / デフォルト値 / 検証出力にも含まれません）、それでも規範的な宣言を推奨します。

### 宣言的翻訳キー（v2.7.0+）

アダプタは `ConfigClass` を宣言するのと同じように、`I18nClass` をネストして翻訳キーを一括宣言できます。フレームワークは `__init__` 階段（設定テンプレート生成前）に自動的に宣言されたすべての翻訳キーを登録し、設定説明で参照される i18n キーがテンプレート生成時に利用可能になることを保証します。

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

詳細な使い方（キーのパスルール、明示的な key パラメータなど）は [i18n ドキュメント](../../advanced/i18n.md#推奨書き方-i18nclass-で翻訳キーを宣言する-v270) を参照してください。

### 宣言的イベント拡張メソッド（v2.7.0+）

アダプタは `EventMixin` を使ってプラットフォーム固有のイベント拡張メソッドを一括宣言し、フレームワークが自動的に現在のプラットフォームに登録します。

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

登録後、イベントオブジェクトはこれらのメソッドを直接呼び出せます：

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] 公式メッセージを受け取りました")
```

> アダプタのイベント拡張メソッドは自身のプラットフォーム（``self._platform``）に登録されます。モジュールが跨プラットフォームのイベント拡張を必要とする場合は、従来の ``register_event_mixin()`` API を使用してください。

#### アカウント解決

マルチアカウントアダプタは `_resolve_account()` を使って送信先アカウントを自動的に解決できます：

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: アカウント名, account: 設定インスタンス
```

解決戦略：アカウント名一致 → `bot_id` フィールド一致 → 他の str フィールド一致 → 最初の有効アカウント。

#### 設定のホットアップデート

サブクラスは `on_config_update()` をオーバーライドして設定変更に応答できます：

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
2. **Send/Request ファクトリ**：`self.Send` と `self.Request` を作成
3. **設定テンプレート**：`ConfigClass` を宣言した場合、自動的にデフォルト設定テンプレートを生成（初回）
4. **アカウントテンプレート**：`AccountConfigClass` を宣言した場合、自動的にデフォルトアカウントテンプレートを生成（初回）
5. **EventMixin 登録**：`EventMixin` を宣言した場合、`AdapterManager` がプラットフォーム名を注入した後に自動的に登録

設定は `self.cfg` / `self.accounts` でリアルタイムに読み取ります（各アクセスで設定ストアから最新値を読み取ります）。`self.config` は `self.cfg` の互換性のあるエイリアスとして引き続き使用できます。

ほとんどのアダプタは `__init__` をオーバーライドする必要はありません。カスタム初期化が必要な場合は：

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

| 属性 | 説明 | 設定方法 |
|-----|------|---------|
| `_target_id` | 目標ID | `To(id)` または `To(type, id)` |
| `_target_type` | 目標タイプ | `To(type, id)` |
| `_target_to` | 簡化目標ID | `To(id)` |
| `_account_id` | 送信アカウントID | `Using(account_id)` |
| `_adapter` | アダプタインスタンス | 自動設定 |
| `_at_user_ids` | @ユーザーIDリスト | `At(user_id)` |
| `_reply_message_id` | 返信メッセージID | `Reply(message_id)` |
| `_at_all` | 全員@するか | `AtAll()` |

> **推奨**：`self.send_context` 属性を使って `target_type`、`target_id`、`account_id` を一括で取得する方が、インスタンス変数を直接アクセスするよりも明確です。

### フレームワーク補助メソッド

| メソッド/属性 | 説明 |
|-----------|------|
| `self._apply_modifiers(message)` | At/AtAll/Reply 修飾子の状態をメッセージセグメントリストにマージ |
| `self.send_context` | `{target_type, target_id, account_id}` ディクショナリを返す |

### 基本メソッド

アダプタは `Raw_ob12` を実装するだけで済み、標準メソッド（Text/Image/Voice/Video/File）は `SendDSL` 基底クラスから継承され、既定で `Raw_ob12` に委譲されます：

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

    # Text/Image/Voice/Video/File は基底クラスから継承され、Raw_ob12 に自動的に委譲されるため、再実装は不要
    # プラットフォーム固有のロジックが必要な場合は、個別メソッドをオーバーライドする：
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

### 変換フロー

```
プラットフォーム原生イベント
    ↓
Converter.convert()
    ↓
OneBot12 標準イベント
```

### 必須フィールド

変換後のイベントはすべて以下のフィールドを含む必要があります：

```python
{
    "id": "イベントのユニークな識別子",
    "time": 1234567890,           # 10桁の Unix タイムスタンプ
    "type": "message/notice/request/meta",
    "detail_type": "イベントの詳細なタイプ",
    "platform": "プラットフォーム名",
    "self": {
        "platform": "プラットフォーム名",
        "user_id": "ロボットID"     # bot_id と一致する必要がある
    },
    "{platform}_raw": {...},       # 原始データ（必須）
    "{platform}_raw_type": "..."    # 原始タイプ（必須）
}
```

### 変換器の例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """プラットフォーム原生イベントを OneBot12 標準形式に変換"""
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

### start() の2つの正しい書き方

クライアントモードのアダプタ（WebSocketクライアント、HTTPポーリングなど）は `start()` で常駐接続ループを起動する必要があります。フレームワークは2つの書き方をサポートしていますが、**どちらか一方のみ使用できます**：

**書き方1：spawn-返却式（推奨）**—`spawn_client_loop()` でループをプラットフォームに属するバックグラウンドタスクとしてスケジュールし、`start()` は即座に返ります：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # ループタスクは self._platform に属するため、shutdown でフレームワークが自動的にキャンセル
        self.spawn_client_loop(self._connect_loop())
        # start はここで終了—"起動は成功"、接続失敗はループ内でリトライ

    async def _connect_loop(self):
        while True:
            try:
                await self._connect_and_receive()   # 断線は例外 → 下方の退避
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(5)              # ループ内で自ら退避して再接続
```

**書き方2：常駐式**—`start()` でループを `await` し、決して返りません：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        await self._connect_loop()   # 常駐して返りません；ループが例外を投げると start は失敗
```

2つの書き方の違いと共通点：

| | spawn-返却式 | 常駐式 |
|---|---|---|
| `start()` の返りタイミング | ループを起動した後即座に返る | 接続ループが終了/失敗したとき（フレームワークが退避戦略でリトライ） |
| 接続失敗の処理 | ループ内で自ら例外を捕まえて退避 | 例外を上流に投げ、フレームワークのリトライチェーンに任せる |
| 適用場面 | 複数接続、ルーティング登録後に他のタスクを起動する必要がある場合 | "接続即起動"の単純な実装 |

`spawn_client_loop(coro, *, name="client_loop")` は書き方1のスケジューラーのエントリポイントです：タスクは `self._platform` に属して登録され、アダプタの `shutdown()` 時にフレームワークが自動的にキャンセルします。ループ内で例外が捕まえられていない場合は、自動的にログに記録されます（意図した切断再接続はループ内で自ら捕まえてください）。

> **唯一の誤った書き方は混用**です：spawn した後に同じループを `await` する—これにより `start()` は即座に返る意味を失い、タスクのキャンセル経路も予測不能になります。

### 接続モードの半完成基底クラス

前節の2つの書き方の他に、最も一般的な2つの接続モードに対してフレームワークは「半完成」の基底クラス（`ErisPulse.Core.Bases.adapter_patterns`、ルートパッケージから直接インポート可能）を提供しています：`start` / `shutdown` のライフサイクルの編排はすべて基底クラスが行い、サブクラスは業務のフックだけを実装します。

#### PollingAdapter（HTTPポーリング型）

「クライアントが定期的にイベントを取得する」プラットフォーム（Telegram getUpdates型）に適しています。基底クラスはspawn-返却式で常駐ポーリングループを起動し、失敗した場合に自動的にログを残して指数退避します（基数1秒、上限60秒、成功後はゼロに戻る；定数 `POLLING_ADAPTER_BACKOFF_BASE_SECS` / `POLLING_ADAPTER_BACKOFF_MAX_SECS` は `Core/constants.py` で調整可能）：

```python
from ErisPulse import PollingAdapter

class MyAdapter(PollingAdapter):
    # ポーリング間隔はデフォルト5秒；ConfigClass に poll_interval フィールドを宣言すると設定値が優先され（ホットアップデート有効）
    poll_interval = 5.0

    async def fetch_events(self):
        """プラットフォーム原生イベントを1回取得する（基底クラスが退避を統一して処理するため、try/except は不要）"""
        resp = await self.sdk.client.get(f"{self.cfg.endpoint}/getUpdates")
        data = await resp.json()
        return data.get("result", [])

    def convert_one(self, raw):
        """1つの原生イベントを OneBot12 に変換；None を返すとスキップ"""
        return self.converter.convert(raw)

    async def call_api(self, endpoint: str, **params):
        ...  # 普通のアダプタと同じ
```

最小実装面：`fetch_events` / `convert_one` / `call_api`。`start()` でループを起動して即座に返る；`shutdown()` はサブクラスで処理する必要はない（ポーリングループは owner に属して自動的にキャンセルされる）。

#### WebhookAdapter（HTTPコールバック型）

「プラットフォームがコールバックを送信する」プラットフォームに適しています。基底クラスの `start()` はフレームワーク router に受信ルートを登録します（最終的なパスは `/{プラットフォーム名}/webhook`、POSTメソッド）、登録は `owner_scope` に含まれる—アダプタのアンロード時に owner に従って自動的にクリーンアップされ、手動でアン登録する必要はない：

```python
from ErisPulse import WebhookAdapter

class MyAdapter(WebhookAdapter):
    def verify_request(self, request) -> bool:
        """オプションフック：コールバック検証（デフォルトは通す；False を返すと基底クラスは403で拒絶）"""
        cfg = self.cfg
        if not cfg.token:
            return True
        auth = request.headers.get("authorization", "")
        return auth == f"Bearer {cfg.token}"

    def convert(self, payload):
        """コールバックペイロードを OneBot12 に変換；None を返すとスキップ"""
        return self.converter.convert(payload)

    async def call_api(self, endpoint: str, **params):
        ...  # 普通のアダプタと同じ
```

最小実装面：`convert` / `call_api`（`verify_request` はオプション）。コールバックアドレスは `sdk.adapter.get_connection_info(platform)` で取得してプラットフォームのバックエンドに設定する；検証失敗のリクエストは403、ペイロード解析失敗は400、正常は `{"status": "ok"}` を返す。

#### 3つのモードの選択

| プラットフォームプロトコル | 継承 | フットプリント |
|---|---|---|
| プラットフォームが接続してくる（WebSocket サーバー） | `BaseAdapter` | `epsdk create adapter`（デフォルト ws-server） |
| 自分が接続してくる（HTTP ポーリング） | `PollingAdapter` | `epsdk create adapter --template polling` |
| プラットフォームが送ってくる（HTTP コールバック） | `WebhookAdapter` | `epsdk create adapter --template webhook` |

完全に実行可能な例はリポジトリの `examples/example-adapter/`（ws-server）、`examples/example-adapter-polling/`、`examples/example-adapter-webhook/` にあります。

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

> 純粋なコールバック型のプラットフォームは、上記の登録/検証/クリーンアップの編排を手動で書く必要はありません—`[WebhookAdapter` 半完成基底クラス](#接続モード半完成基底クラス)を継承し、`convert`（オプションで `verify_request` をオーバーライド）を実装するだけで済みます。

> **ルート情報の照会**：アダプタが登録したルート（HTTP、WebSocket、SSE）は `sdk.adapter.get_connection_info(platform)` と `sdk.router.get_module_urls(module_name)` を使って完全な接続アドレス（`base_url` + パス）を照会できます。[アダプタ開発入門 - 接続情報とルート発見](getting-started.md#9-接続情報とルート発見)と [SSE 支援](getting-started.md#10-sse-server-sent-events-サポート)を参照してください。

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

### 手動構築応答（旧版方式は互換性あり）

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

`AccountConfigClass` を宣言して設定クラスを定義した後、フレームワークが自動的に多アカウントのロード、検証、テンプレート生成を管理します：

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
            self.logger.info(f"アカウント {name}: {account.bot_id} を起動します")
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

### 指定アカウントで送信

```python
# Using メソッドでアカウントを指定
my_adapter = adapter.get("myplatform")

# event から self.user_id を使う（推奨、最も汎用的）
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# アカウント名で指定
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### self.user_id と Using の関係

フレームワークのイベント返信メカニズムは、イベントの `self` フィールドから `account_id`（優先）または `user_id` を取り出し、`Using` パラメータとして渡します。アダプタ開発者は、Converter で `self.user_id` の値が `AccountConfigClass` に定義された識別フィールド（例：`bot_id`）と一致するようにし、`_resolve_account()` が正しいアカウントとマッチできるようにする必要があります。

**フレームワーク内部の動作**：

```python
# フレームワークが bot_id を取り出すロジック
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# bot_id が空でない場合にのみ Using を呼び出す
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **重要な点**：アダプタが1つの Bot 設定しか使わなくても、Converter が `self.user_id` を正しく設定している限り、フレームワークはそれを `Using` パラメータとして渡します。アダプタは `self.user_id` が `AccountConfigClass` の識別フィールド（例：`bot_id`）と一致するようにし、`_resolve_account()` が正しいアカウントとマッチできるようにする必要があります。`self.user_id` が空の場合、フレームワークは `Using` を呼び出さず、`call_api` に渡される `account_id` は `None` となり、`_resolve_account(None)` は最初の有効なアカウントを返します。

## エラー処理

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
                    self.logger.warning(f"接続失敗、{wait_time}秒後にリトライします")
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### API エラー処理

```python
async def call_api(self, endpoint: str, **params):
    try:
        # 推奨は SDK 内部クライアントを使う
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

> **後方互換性**：`aiohttp.ClientSession` を直接使う古いアダプタコードは影響を受けず、`aiohttp.ClientError` をキャッチできます。2つの方式は共存可能です。新規コードは `sdk.client` + ErisPulse の例外体系を使うことを推奨します。

## Bot 状態管理

AdapterManager には Bot 状態を追跡するシステムが内蔵されており、登録されたすべての Bot のオンライン状態、アクティブ時間、メタ情報を自動的に管理します。

### 自動発見メカニズム

アダプタが `adapter.emit()` でイベントを送信するとき、フレームワークはイベントの `self` フィールドを自動的にチェックします：

- **meta イベント**：`detail_type` に応じて対応する操作を実行（connect で登録/disconnect でオフラインをマーク/heartbeat でアクティブ時間を更新）
- **通常イベント**（message/notice/request）：Bot を自動的に発見し、アクティブ時間を更新

```python
# self フィールドを含むすべてのイベントは自動発見をトリガー
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123" は自動的に登録（初めて出現した場合）され、アクティブ時間を更新されます
```

### Meta イベントタイプ

| `detail_type` | 説明 | フレームワークの動作 |
|---|---|---|
| `connect` | Bot 接続 | Bot を登録し、`adapter.bot.online` ライフサイクルイベントをトリガー |
| `disconnect` | Bot 切断 | Bot をオフラインにマークし、`adapter.bot.offline` ライフサイクルイベントをトリガー |
| `heartbeat` | Bot ハートビート | Bot のアクティブ時間とメタ情報を更新 |

### アダプタによる Meta イベント送信

送信方法（`emit_meta()` で一行送信、ハートビートイベントと手動構造化フォーマット）は [アダプタのベストプラクティス - Bot 状態管理と Meta イベント](best-practices.md#bot-状態管理と-meta-イベント) を参照してください。

### `self` フィールドの拡張情報

`self` フィールドは必須の `platform` と `user_id` の他に、以下のオプションフィールドをサポートします：

| フィールド | 説明 |
|---|---|
| `user_name` | Bot ユーザー名 |
| `nickname` | Bot ニックネーム |
| `avatar` | Bot アイコン URL |
| `account_id` | 複数アカウント識別 |

### Bot 状態の照会

照会 API（`get_bot_info()` / `list_bots()` / `is_bot_online()` / `get_status_summary()`）は [アダプタシステム API - Bot 状態管理](../../api-reference/adapter-system.md#bot-状態管理) を参照してください。

### Bot ライフサイクルの監視

`adapter.bot.online` / `adapter.bot.offline` ライフサイクルイベントの表と監視の例は [アダプタシステム API - Bot 状態管理](../../api-reference/adapter-system.md#bot-状態管理) を参照してください。

## 関連ドキュメント

### 実装面の詳細

- [SendDSL 詳解](send-dsl.md) - メッセージ送信の学習
- [アダプタのベストプラクティス](best-practices.md) - 高品質なアダプタの開発

### 入門手順の振り返り

- [アダプタ開発入門](getting-started.md) - 最初のアダプタの作成