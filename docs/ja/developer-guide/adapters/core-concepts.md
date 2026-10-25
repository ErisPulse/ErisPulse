# アダプタのコア概念

> [!TIP]
> **この記事を読むタイミング**：アダプタ開発経路の場合必読（BaseAdapter / SendDSL / ライフサイクル等の完全な説明）。開発の入り口だけ知りたい場合は [アダプタ開発入門](getting-started.md) を先に読み、"なぜこう書くのか"の疑問が生じたときにこの記事に戻る。

この記事ではアダプタの動作メカニズムを説明します：AdapterManagerがイベントをどのように登録・配信するか、`BaseAdapter`が初期化時にどのような処理を行うか、設定と複数アカウントの宣言方法など。アダプタ開発時に"なぜこのように書くのか"という疑問が生じたときは、ここに来て調べてください。

## アダプタアーキテクチャ

### コンポーネントの関係

```
正方向変換（受信方向）                           反方向変換（送信方向）
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ 平台の原生イベント │                        │ モジュールが構築したメッセージ │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │  アダプタ (MyAdapter) │   │ Send.Raw_ob12()  │
│  Converter       │   │ ┌──────────────┐ │   │ (反方向変換のエントリポイント)   │
│  (イベント変換器)    │──→│ │              │ │   │                  │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ 平台 API の呼び出し    │
                       │ OneBot12 標準イベント │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ 標準のレスポンス形式     │
                       │ イベントシステム         │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ モジュール (イベントを処理)  │
                       └──────────────────┘
```

**コアの対称性**：
- **正方向変換**（Converter）：プラットフォームの原生イベント → OneBot12 標準イベント、元データは`{platform}_raw`に保持
- **反方向変換**（Raw_ob12）：OneBot12 メッセージセグメント → プラットフォーム API 呼び出し、返却は標準のレスポンス形式

## AdapterManager アダプタ管理器

`AdapterManager`はErisPulseアダプタシステムのコアコンポーネントで、すべてのプラットフォームアダプタの登録、起動、停止、イベント配信を管理します。

### コア機能

- **アダプタの登録**：複数のプラットフォームアダプタを登録・管理
- **ライフサイクル管理**：アダプタの起動と停止を制御
- **イベント配信**：OneBot12 標準イベントとプラットフォーム原生イベントを配信
- **設定管理**：アダプタの有効/無効状態を管理
- **ミドルウェアサポート**：OneBot12 イベントミドルウェアをサポート

### 基本的な使用法

```python
from ErisPulse import sdk

# アダプタの登録（通常はLoaderが自動的に実行）
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
4. 起動失敗した場合は指数バックオフ戦略で自動的に再試行
5. 起動成功後は `adapter.status.change` イベントを送信（started）

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
# すべての登録済みプラットフォームをリストアップ
platforms = sdk.adapter.list_registered()

# すべてのプラットフォームとその状態をリストアップ
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

`adapter.emit(event_data)` を呼び出すとき：

1. **ミドルウェア処理**：すべての OneBot12 ミドルウェアを実行
2. **標準イベント配信**：マッチする OneBot12 イベントハンドラに配信
3. **原生イベント配信**：元データがあれば、原生イベントハンドラに配信

**マッチルール**：

- 精密マッチ：`@sdk.adapter.on("message")` は `message` イベントのみマッチ
- ワイルドカード：`@sdk.adapter.on("*")` はすべてのイベントにマッチ
- プラットフォームフィルター：`platform="myplatform"` は指定プラットフォームのイベントのみ配信

### ミドルウェア

#### ミドルウェアの追加

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """ログ記録ミドルウェア"""
    print(f"イベントを処理しています: {data.get('type')}")
    return data  # 必須でデータを返す

@sdk.adapter.middleware
async def filter_middleware(data):
    """イベントフィルターミドルウェア"""
    # 不要なイベントをフィルタリング
    if data.get("type") == "notice":
        return None  # Noneを返すとミドルウェアチェーンはその返り値を無視し、元のデータをそのまま次の処理に渡す
    return data  # 必須でデータを返して次の処理に渡す
```

#### ミドルウェアの返り値の契約

| 返り値 | 行動 |
|--------|------|
| `dict` | イベントのペイロードを上書き（その後のハンドラは変更後のイベントを受け取る） |
| `None` | 通す、ペイロードは変更なし（WARNINGレベルのログが出力される予定—明示的に `return data` を返すことを推奨） |
| `False` | **拒否**：イベントは破棄され、どのハンドラにも渡らず、出力副作用も一切発生しない |

拒否はイベントレベルで直接破棄する場面（以前は高優先度のイベントハンドラで回避するしかなかった）に適しています。拒否した場合、フレームワークはTRACEレベルのログを出力し、`adapter.event.blocked` ライフサイクルフック（`middleware`ミドルウェア名、完全な`event`、`platform` / `event_type` / `detail_type`）をトリガーし、"イベントがなぜ反応しなかったのか"の調査に役立ちます：

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

ミドルウェアは登録順に実行され、後から登録されたミドルウェアが先に実行されます。

> **注意**：ミドルウェアが `None` を返した場合（`return data` を忘れている場合）、フレームワークはその返り値を無視して元のデータをそのまま次の処理に渡し、WARNINGレベルのログを出力します。これにより、1つのミドルウェアのミスがイベントチェーン全体の中断を引き起こすことはありません。

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
    
    # __init__ をオーバーライドする必要はない、フレームワークが自動的に処理する：
    # - self.sdk, self.logger
    # - self.cfg（型安全な設定インスタンス、実時読み取り）
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

フレームワークは宣言的設定管理を提供し、dataclassを使って設定構造を定義し、フレームワークが自動的にロード、検証、テンプレート生成を処理します。

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
        cfg = self.cfg  # 型安全、実時読み取り
        if not cfg.token:
            raise ValueError("Tokenが設定されていません")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### 複数アカウント設定

`BotAccountConfig`基底クラスは`enabled`と`name`フィールドを提供します。ほとんどのアダプタはプラットフォームプロトコルやログイン応答から`bot_id`を自動的に取得できます。イベント変換時にアカウント設定に注入されます。：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

# 多くのアダプタ：bot_idは実行時に自動的に取得され、設定は不要
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Token"},
        "required": True,
    })

# ログイン時にbot_idを取得できない場合、ユーザーに設定してもらう
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

フィールドのmetadataはTOMLのコメント生成とWebUIのフォームレンダリングの両方に役立ちます：

```python
metadata = {
    "description": str | dict,  # フィールドの説明（i18nをサポート）
    "required": bool,         # 必須か（検証 + WebUIの必須マーク）
    "secret": bool,           # 敏感か（WebUIでは***に表示、ログでは脱敏）
    "example": bool,          # 記録しないフラグ：config.tomlには書き込まない（デフォルト値/テンプレートは除外）、config.full.exampleにのみレンダリング；schemaに"example": trueを付けると、CLIの設定ガイドはデフォルトでスキップ；ユーザーが手動で設定した後は通常の永続化
    "min": number, "max": number,  # 数値の範囲検証
    "ui": {                   # WebUIコントロールの設定（旧名"webui"も互換）
        "widget": str,        # コントロールの種類: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # グループ: "basic" | "advanced" | "connection" 等
        "order": int,         # ソートの重み（小さいほど前に表示）
        "options": list,      # selectコントロールの選択肢 [{label, value}]、labelはi18nをサポート
        "placeholder": str | dict,  # 入力欄のプレースホルダー（i18nをサポート）
    },
    "extra": dict,            # 余分な拡張フィールド（schemaに透かし渡す）
}
```

すべてのユーザーが見られるテキストフィールドはi18nをサポートし、統一された`{"i18n": "key", "default": "text"}`形式を使用します。純粋な文字列はそのまま透かし渡されます（後方互換性）。サポートされるi18nフィールド：

| フィールド | 位置 | 説明 |
|------|------|------|
| `description` | field metadata | フィールドの説明 |
| `options[].label` | `ui.options` | selectコントロールのオプションラベル |
| `placeholder` | `ui.placeholder` | 入力欄のプレースホルダー |
| `group_labels` | `_schema_meta` | グループの表示名（ダッシュボードのセクションタイトル） |

i18nを使用する際は、翻訳キーをi18nシステムに事前に登録する必要があります（[i18nドキュメント](../../advanced/i18n.md#設定フィールド多言語)を参照）。

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
                {"label": "純粋な文字列のラベル", "value": "b"},  # 純粋な文字列はそのまま透かし渡す
            ],
        },
    },
)
```

**group_labels**の例（設定クラスの定義後に宣言）：

```python
MyConfig._schema_meta = {
    "group_labels": {
        "basic": {"i18n": "my_adapter.group.basic", "default": "基本設定"},
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "高度設定"},
    }
}
```

フレームワークの`resolve_config_schema()`は現在の言語に応じて上記のすべてのフィールドのi18nキーを自動的に解決します。`get_config_schema()`はi18n辞書をそのまま透かし渡し、フロントエンドが独自に解決します。

#### docstringから自動生成されるフィールド説明（v2.8.0+）

metadataに`description`を宣言していないフィールドは、フレームワークが設定クラスのdocstringからフィールド説明を抽出してバックアップとして使用します。2つの一般的なスタイル（混用可）がサポートされています：

```python
@dataclass
class MyConfig(BaseConfig):
    """
    MyAdapterの設定

    :ivar endpoint: プラットフォームAPIアドレス        # reSTスタイル
    :ivar timeout: 要求のタイムアウト秒数
    """

    endpoint: str = "https://api.example.com"   # metadata descriptionがない→docstringの説明/説明を参照
    timeout: int = 30

    # Googleスタイルもサポート（Attributes:セクション）：
    # Attributes:
    #     endpoint: プラットフォームAPIアドレス
```

優先順位: **metadata description > docstringフィールド説明 > 空**。i18n辞書形式のdescriptionは影響を受けません（常に優先されます）。

#### 嵌套設定（v2.8.0+）

フィールド型がネストされたdataclassの場合、フレームワークは再帰的に処理します：schemaは`"type": "table"` + `"fields"`サブツリーを保持し（WebUIでは折りたたみ可能なネストされたグループとしてレンダリング）、TOMLテンプレートは`[サブテーブル]`セクションとしてレンダリングされ、デフォルト値/埋め込み/検証/i18nの解釈は再帰的に有効になります。

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
    """MyAdapterの設定"""
    endpoint: str = "https://api.example.com"
    retry: RetryConfig = field(default_factory=RetryConfig)   # 嵌套設定セクション
```

生成されるTOMLテンプレート：

```toml
endpoint = "https://api.example.com"

[retry]
# 最大リトライ回数
max_retries = 3
backoff = 0.5
```

> 嵌套型は直接型注釈を使うことを推奨します；文字列注釈（遅延評価の場面など）は、タイプが設定クラスの所属モジュールからグローバルに、`__qualname__`外側のクラス名前空間、またはクラス属性から名前で解決可能であることを保証する必要があります。

#### 保存されないexampleフィールド（v2.8.0+）

```python
gc_interval: int = field(default=300, metadata={"example": True})
```

`example: True`を持つフィールド：

- config.tomlに書き込まれない（アダプタ/モジュールの設定テンプレートとデフォルト値は除外、実行時はコードのデフォルト値を使用）
- config.full.exampleにのみレンダリングされる（ユーザーが参考としてconfig.tomlに手動でコピーする）
- schemaに`"example": true`のマークが付く（パネルは表示戦略を独自に決定可能）、CLIの設定ガイドはデフォルトでスキップ
- ユーザーがこのキーを手動で設定した後は通常の永続化、通常のホットアップデート（ユーザーの明示的な意図が優先）

"冗長でほとんど触れない"高度な設定項目に適しており、ユーザーのconfig.tomlを最小化します。

> ⚠️ `_schema_meta`はクラスレベルのメタデータ（設定フィールドではない）。dataclassクラス本体で宣言する場合は、`ClassVar`注釈を付ける必要があります（`_schema_meta: ClassVar[dict] = {...}`）、そうでないとdataclassは普通のフィールドとして扱われます。フレームワークはアンダースコアで始まるフィールドを防衛的に除外しています（すべてのschema / テンプレート / デフォルト値 / 検証出力から除外）。ただし、規則的な宣言を推奨します。

### 宣言的翻訳キー（v2.7.0+）

アダプタは`ConfigClass`を宣言するのと同じように、`I18nClass`をネストして翻訳キーを一括宣言できます。フレームワークは`__init__`段階（設定テンプレート生成前）で自動的に宣言されたすべての翻訳キーを登録し、設定説明で参照されるi18nキーがテンプレート生成時に利用可能になることを保証します。

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

> ``I18nKey.default``は**言語に依存しないバックアップテキスト**で、どの言語にも登録されません。翻訳を有効にするには、少なくとも1つの言語パラメータを明示的に渡す必要があります。

詳細な使い方（キーのパスルール、明示的なkeyパラメータなど）は[翻訳ドキュメント](../../advanced/i18n.md#推奨書き方-i18nclass-を宣言して翻訳キーを宣言する-v270)を参照してください。

### 宣言的イベント拡張メソッド（v2.7.0+）

アダプタは`EventMixin`をネストしてプラットフォーム固有のイベント拡張メソッドを一括宣言し、フレームワークが自動的に現在のプラットフォームに登録します。

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    class EventMixin:
        def get_chat_name(self):
            """チャット名を取得"""
            return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

        def is_official_message(self):
            """公式メッセージか判断"""
            raw = self.get("myplatform_raw", {})
            return raw.get("sender", {}).get("is_official", False)
```

登録後、イベントオブジェクトは直接これらのメソッドを呼び出せます：

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] 公式メッセージを受け取りました")
```

> アダプタのイベント拡張メソッドは自身のプラットフォーム（``self._platform``）に登録されます。モジュールがプラットフォーム間のイベント拡張を必要とする場合は、従来の``register_event_mixin()`` APIを使用してください。

#### アカウント解決

複数アカウントアダプタは`_resolve_account()`を使用して送信先アカウントを自動的に解決できます：

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: アカウント名, account: 設定インスタンス
```

解決戦略：アカウント名一致 → `bot_id`フィールド一致 → 他のstrフィールド一致 → 最初の有効アカウント。

#### 設定のホットアップデート

サブクラスは`on_config_update()`をオーバーライドして設定変更に反応できます：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Tokenが更新されたため、再接続します")
```

### 初期化プロセス

フレームワークは`BaseAdapter.__init__(self, sdk=None)`で以下の作業を自動的に行います：

1. **SDK参照**：`self.sdk`、`self.logger`を設定
2. **Send/Request工場**：`self.Send`と`self.Request`を作成
3. **設定テンプレート**：`ConfigClass`を宣言した場合、自動的にデフォルト設定テンプレートを生成（初回）
4. **アカウントテンプレート**：`AccountConfigClass`を宣言した場合、自動的にデフォルトアカウントテンプレートを生成（初回）
5. **EventMixin登録**：`EventMixin`を宣言した場合、`AdapterManager`がプラットフォーム名を注入した後に自動的に登録

設定は`self.cfg` / `self.accounts`でリアルタイムに読み取ります（設定ストアから最新値を毎回読み取り）。`self.config`は`self.cfg`の互換エイリアスとして引き続き使用できます。

ほとんどのアダプタは`__init__`をオーバーライドする必要はありません。独自の初期化が必要な場合：

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
        """Sendのネストクラス、BaseAdapter.Sendから継承"""
        pass
```

### 利用可能な属性

`Send`クラスは呼び出し時に以下の属性を自動的に設定します：

| 属性 | 説明 | 設定方法 |
|-----|------|---------|
| `_target_id` | 目標ID | `To(id)` または `To(type, id)` |
| `_target_type` | 目標タイプ | `To(type, id)` |
| `_target_to` | 簡易目標ID | `To(id)` |
| `_account_id` | 送信アカウントID | `Using(account_id)` |
| `_adapter` | アダプタインスタンス | 自動設定 |
| `_at_user_ids` | @ユーザーIDリスト | `At(user_id)` |
| `_reply_message_id` | 返信するメッセージID | `Reply(message_id)` |
| `_at_all` | @全員か | `AtAll()` |

> **推奨**：`self.send_context`属性を使って`target_type`、`target_id`、`account_id`を一度に取得し、インスタンス変数を直接アクセスするよりも明確にします。

### フレームワーク補助メソッド

| メソッド/属性 | 説明 |
|-----------|------|
| `self._apply_modifiers(message)` | At/AtAll/Reply修飾子の状態をメッセージセグメントリストにマージする |
| `self.send_context` | `{target_type, target_id, account_id}`の辞書を返す |

### 基本メソッド

アダプタは`Raw_ob12`を実装するだけで、標準メソッド（Text/Image/Voice/Video/File）は`SendDSL`基底クラスから継承され、デフォルトで`Raw_ob12`に委譲されます：

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

    # Text/Image/Voice/Video/Fileは基底クラスから継承され、Raw_ob12に自動的に委譲される
    # プラットフォーム固有のロジックが必要な場合は、個別のメソッドをオーバーライドできる：
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
プラットフォームの原生イベント
    ↓
Converter.convert()
    ↓
OneBot12標準イベント
```

### 必須フィールド

変換後のイベントはすべて以下のフィールドを含む必要があります：

```python
{
    "id": "イベントの一意識別子",
    "time": 1234567890,           # 10桁Unixタイムスタンプ
    "type": "message/notice/request/meta",
    "detail_type": "イベントの詳細タイプ",
    "platform": "プラットフォーム名",
    "self": {
        "platform": "プラットフォーム名",
        "user_id": "ロボットID"     # bot_idと一致する必要がある
    },
    "{platform}_raw": {...},       # 原始データ（必須）
    "{platform}_raw_type": "..."    # 原始タイプ（必須）
}
```

### 変換器の例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """プラットフォームの原生イベントをOneBot12標準形式に変換"""
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

### start()の2つの正しい書き方

クライアントモードのアダプタ（WebSocketクライアント、HTTPポーリングなど）は`start()`内で常駐接続ループを起動する必要があります。フレームワークは2つの書き方をサポートしており、**どちらか一方のみ選択可能**です：

**書き方1：spawn-返却式（推奨）** — `spawn_client_loop()`でループをプラットフォームに属するバックグラウンドタスクとしてスケジュールし、`start()`は即座に返却：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # ループタスクはself._platformに属するため、shutdown時にフレームワークが自動的にキャンセル
        self.spawn_client_loop(self._connect_loop())
        # startはここで終了 — 「起動即成功」、接続失敗はループ内で再試行

    async def _connect_loop(self):
        while True:
            try:
                await self._connect_and_receive()   # 断線は例外を投げる → 下の退避
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(5)              # ループ内で自ら退避再接続
```

**書き方2：常駐式** — `start()`で接続ループを`await`し、返却しない：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        await self._connect_loop()   # 常駐で返却しない；ループが例外を投げる = start失敗
```

2つの書き方の違いと共通点：

| | spawn-返却式 | 常駐式 |
|---|---|---|
| `start()`の返却タイミング | ループを起動した後即座に返却 | 接続ループが終了/失敗した時（フレームワークが退避戦略で再試行） |
| 接続失敗処理 | ループ内で自ら例外を捕獲退避 | 例外を上流に投げ、フレームワークの再試行チェーンに任せる |
| 適用場面 | 複数接続、ルーティング登録後に他のタスクを起動する必要がある場合 | 「接続即起動」のシンプルな実装 |

`spawn_client_loop(coro, *, name="client_loop")`は書き方1のスケジューラエントリポイントです：タスクは`self._platform`に属して登録され、アダプタの`shutdown()`でフレームワークが自動的にキャンセル、自分でタスクハンドルを管理する必要はありません；ループ内で捕獲されない例外は自動的にログに残ります（予期される切断再接続はループ内で自ら捕獲してください）。

> **唯一の誤った書き方**は混用することです：spawnした後に同じループを`await`する — これにより`start()`の即時返却の意味が失われ、タスクのキャンセル経路も予測不能になります。

### 接続モードの半完成基底クラス

前節の2つの書き方の他に、最も一般的な2つの接続モードに対してフレームワークは「半完成」の基底クラス（`ErisPulse.Core.Bases.adapter_patterns`、ルートパッケージから直接インポート可能）を提供しています：`start` / `shutdown`のライフサイクルの編排はすべて基底クラスが行い、サブクラスは業務フックだけを実装します。

#### PollingAdapter（HTTPポーリング型）

「クライアントが定期的にイベントを取得する」プラットフォーム（TelegramのgetUpdates型）に適しています。基底クラスはspawn-返却式で常駐ポーリングループを起動し、取得失敗は自動的にログに残り指数退避されます（基数1秒、上限60秒、成功後はゼロに戻る；定数`POLLING_ADAPTER_BACKOFF_BASE_SECS` / `POLLING_ADAPTER_BACKOFF_MAX_SECS`は`Core/constants.py`で調整可能）：

```python
from ErisPulse import PollingAdapter

class MyAdapter(PollingAdapter):
    # ポーリング間隔はデフォルト5秒；ConfigClassにpoll_intervalフィールドを宣言した場合は設定値で上書き（ホットアップデート有効）
    poll_interval = 5.0

    async def fetch_events(self):
        """プラットフォームの原生イベントを1回取得（例外は基底クラスが退避、try/exceptは不要）"""
        resp = await self.sdk.client.get(f"{self.cfg.endpoint}/getUpdates")
        data = await resp.json()
        return data.get("result", [])

    def convert_one(self, raw):
        """1件の原生イベントをOneBot12に変換；Noneを返すとスキップ"""
        return self.converter.convert(raw)

    async def call_api(self, endpoint: str, **params):
        ...  # 普通のアダプタと同じ
```

最小実装面：`fetch_events` / `convert_one` / `call_api`。`start()`はループを起動して即座に返却；`shutdown()`はサブクラスで処理する必要なし（ポーリングループはownerに属して自動的にキャンセル）。

#### WebhookAdapter（HTTPコールバック型）

「プラットフォームがコールバックをプッシュする」プラットフォームに適しています。基底クラスの`start()`はフレームワークのrouterにコールバックルートを登録（最終パスは`/{プラットフォーム名}/webhook`、POSTメソッド）、登録は`owner_scope`の中に含まれる — アダプタのアンロード時にownerに従って自動的にクリーンアップされ、手動でアン登録する必要はない：

```python
from ErisPulse import WebhookAdapter

class MyAdapter(WebhookAdapter):
    def verify_request(self, request) -> bool:
        """オプションフック：コールバックの検証（デフォルトでは通す；Falseを返すと基底クラスが403で拒絶）"""
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

最小実装面：`convert` / `call_api`（`verify_request`はオプション）。コールバックアドレスは`sdk.adapter.get_connection_info(platform)`で取得してプラットフォームのバックエンドに設定；検証失敗のリクエストは403、ペイロード解析失敗は400、正常は`{"status": "ok"}`を返す。

#### 3つのモードの選択

| プラットフォームプロトコル | 継承 | フットプリント |
|---|---|---|
| プラットフォームが接続してくる（WebSocketサーバー） | `BaseAdapter` | `epsdk create adapter`（デフォルトはws-server） |
| 我々が取得しに行く（HTTPポーリング） | `PollingAdapter` | `epsdk create adapter --template polling` |
| プラットフォームがプッシュしてくる（HTTPコールバック） | `WebhookAdapter` | `epsdk create adapter --template webhook` |

実行可能な完全な例はリポジトリの`examples/example-adapter/`（ws-server）、`examples/example-adapter-polling/`、`examples/example-adapter-webhook/`を参照してください。

### WebSocket接続

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """WebSocketルートを登録"""
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
        """WebHookルートを登録"""
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

> コールバック型のプラットフォームは、上記の登録/検証/クリーンアップの編集を手動で書く必要はありません — `WebhookAdapter`半完成基底クラスを継承し、`convert`（`verify_request`はオプション）を実装するだけです。

> **ルート情報の取得**：アダプタが登録したルート（HTTP、WebSocket、SSE）は`sdk.adapter.get_connection_info(platform)`と`sdk.router.get_module_urls(module_name)`で完全な接続アドレス（`base_url` + パス）を取得できます。[アダプタ開発入門 - 接続情報とルート発見](getting-started.md#9-接続情報とルート発見)と[SSEサポート](getting-started.md#10-sse-server-sent-events-サポート)を参照してください。

## APIレスポンス標準

フレームワークは`make_response()`と`make_error()`メソッドを提供し、標準化されたレスポンスを構築するために手動でレスポンス辞書を構築する必要がありません。

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

### 手動でレスポンス構築（旧方式は互換性あり）

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

`AccountConfigClass`を宣言した後、フレームワークが自動的に多アカウントのロード、検証、テンプレート生成を管理します：

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
# Usingメソッドでアカウントを指定
my_adapter = adapter.get("myplatform")

# イベントのself.user_idを使用する（推奨、最も汎用的）
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# アカウント名を使用する
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### self.user_id と Using の関係

フレームワークのイベント返信メカニズムは、イベントの`self`フィールドから`account_id`（優先）または`user_id`を抽出し、`Using`パラメータとして渡します。アダプタ開発者は、Converterが`self.user_id`の値を正しく注入していることを保証する必要があります。

**フレームワーク内部の動作**：

```python
# フレームワークがbot_idを抽出するロジック
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# bot_idが空でない場合にUsingを呼び出す
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **重要な点**：アダプタが1つのBot設定しか使用しない場合でも、Converterが`self.user_id`を正しく設定していれば、フレームワークはそれを`Using`パラメータとして渡します。アダプタは、`self.user_id`が`AccountConfigClass`の識別子フィールド（例：`bot_id`）と一致することを保証し、`_resolve_account()`が正しいアカウントをマッチできるようにする必要があります。`self.user_id`が空の場合、フレームワークは`Using`を呼び出さず、`call_api`に受け取る`account_id`は`None`となり、`_resolve_account(None)`は最初の有効なアカウントを返します。

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
                    self.logger.warning(f"接続失敗、{wait_time}秒後に再試行します")
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### APIエラー処理

```python
async def call_api(self, endpoint: str, **params):
    try:
        # 推奨はSDKの組み込みクライアントを使用
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
        self.logger.error(f"要求タイムアウト: {endpoint}")
        return self._error_response("要求タイムアウト", 32000)
    except ClientError as e:
        self.logger.error(f"ネットワークエラー: {e}")
        return self._error_response("ネットワーク要求失敗", 33000)
    except Exception as e:
        self.logger.error(f"未知のエラー: {e}")
        return self._error_response(str(e), 34000)
```

> **互換性**：`aiohttp.ClientSession`を使用する古いアダプタコードは影響を受けず、`aiohttp.ClientError`をキャッチできます。2つの方法は共存できます。新規コードは`sdk.client` + ErisPulseの例外体系を使用することを推奨します。

## Botステータス管理

AdapterManagerにはBotステータスの追跡システムが内蔵されており、登録されたすべてのBotのオンラインステータス、アクティブ時間、メタ情報を自動的に管理します。

### 自動発見メカニズム

アダプタが`adapter.emit()`でイベントを送信するとき、フレームワークはイベントの`self`フィールドを自動的にチェックします：

- **metaイベント**：`detail_type`に応じて対応する操作を実行（connectで登録/断開でオフラインをマーク/heartbeatでアクティブ時間を更新）
- **普通のイベント**（message/notice/request）：Botを自動的に発見し、アクティブ時間を更新

```python
# selfフィールドを含むすべてのイベントが自動発見をトリガー
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123" は自動的に登録（初めて出現した場合）され、アクティブ時間を更新されます
```

### Metaイベントタイプ

| `detail_type` | 説明 | フレームワークの動作 |
|---|---|---|
| `connect` | Botが接続 | Botを登録し、`adapter.bot.online`ライフサイクルイベントをトリガー |
| `disconnect` | Botが切断 | Botをオフラインにマークし、`adapter.bot.offline`ライフサイクルイベントをトリガー |
| `heartbeat` | Botのハートビート | Botのアクティブ時間とメタ情報を更新 |

### アダプタによるMetaイベント送信

送信方法（`emit_meta()`で一行送信、ハートビートイベントと手動構成の形式）は[アダプタのベストプラクティス - Botステータス管理とMetaイベント](best-practices.md#bot-ステータス管理と-meta-イベント)を参照してください。

### `self`フィールドの拡張情報

`self`フィールドは必須の`platform`と`user_id`の他に、以下のオプションフィールドをサポートします：

| フィールド | 説明 |
|---|---|
| `user_name` | Botのユーザー名 |
| `nickname` | Botのニックネーム |
| `avatar` | BotのアバターURL |
| `account_id` | 多アカウント識別子 |

### Botステータスの照会

照会API（`get_bot_info()` / `list_bots()` / `is_bot_online()` / `get_status_summary()`）は[アダプタシステムAPI - Botステータス管理](../../api-reference/adapter-system.md#bot-ステータス管理)を参照してください。

### Botライフサイクルの監視

`adapter.bot.online` / `adapter.bot.offline`ライフサイクルイベントの表と監視例は[アダプタシステムAPI - Botステータス管理](../../api-reference/adapter-system.md#bot-ステータス管理)を参照してください。

## 関連ドキュメント

### 実装面の詳細

- [SendDSLの詳細](send-dsl.md) - メッセージ送信の学習
- [アダプタのベストプラクティス](best-practices.md) - 高品質なアダプタの開発

### 再び入門ステップを振り返る

- [アダプタ開発入門](getting-started.md) - 最初のアダプタを作成する