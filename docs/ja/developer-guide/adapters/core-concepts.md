# アダプタのコアコンセプト

ErisPulseアダプタのコアコンセプトを理解することは、アダプタ開発の基礎です。

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

**コア対称性**：
- **正方向変換**（Converter）：プラットフォーム独自イベント → OneBot12標準イベント、元データは`{platform}_raw`に保持
- **逆方向変換**（Raw_ob12）：OneBot12メッセージセグメント → プラットフォームAPI呼び出し、返却は標準レスポンス形式

## AdapterManager アダプタマネージャー

`AdapterManager`はErisPulseアダプタシステムのコアコンポーネントで、すべてのプラットフォームアダプタの登録、起動、停止、イベント配信を管理します。

### コア機能

- **アダプタ登録**：複数のプラットフォームアダプタを登録・管理
- **ライフサイクル管理**：アダプタの起動と停止を制御
- **イベント配信**：OneBot12標準イベントとプラットフォーム独自イベントを配信
- **設定管理**：アダプタの有効/無効状態を管理
- **ミドルウェアサポート**：OneBot12イベントミドルウェアをサポート

### 基本使用

```python
from ErisPulse import sdk

# アダプタの登録（通常Loaderが自動的に実行）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# すべてのアダプタを起動
await sdk.adapter.startup()

# 指定プラットフォームを起動
await sdk.adapter.startup(["myplatform"])
# すべてのアダプタを起動
await sdk.adapter.startup()

# アダプタインスタンスの取得
my_adapter = sdk.adapter.get("myplatform")
# または属性アクセス
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

**起動プロセス**：

1. `adapter.start`ライフサイクルイベントを送信
2. `adapter.status.change`イベントを送信（starting）
3. 各アダプタを並行起動
4. 起動失敗時は指数バックオフ戦略で自動リトライ
5. 起動成功後`adapter.status.change`イベントを送信（started）

**リトライメカニズム**：

- 最初の4回：60秒、10分、30分、60分
- 5回目以降：3時間固定間隔

#### アダプタの停止

```python
# すべてのアダプタを停止
await sdk.adapter.shutdown()
```

**停止プロセス**：

1. `adapter.stop`ライフサイクルイベントを送信
2. すべてのアダプタの`shutdown()`メソッドを呼び出す
3. ルーティングサーバーを停止
4. イベントハンドラをクリア
5. `adapter.stopped`ライフサイクルイベントを送信

### 設定管理

#### プラットフォームのステータス確認

```python
# プラットフォームが登録されているか確認
exists = sdk.adapter.exists("myplatform")

# プラットフォームが有効か確認
enabled = sdk.adapter.is_enabled("myplatform")

# in演算子を使用
if "myplatform" in sdk.adapter:
    print("プラットフォームが存在し、有効です")
```

#### プラットフォームの一覧表示

```python
# すべての登録済みプラットフォームをリスト
platforms = sdk.adapter.list_registered()

# すべてのプラットフォームとそのステータスをリスト
status_dict = sdk.adapter.list_items()
# 戻り値: {"platform1": true, "platform2": false, ...}

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

# 特定プラットフォームの標準メッセージイベントを監視
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"myplatformメッセージを受信: {data}")

# すべてのイベントを監視
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"イベントを受信: {data.get('type')}")
```

#### プラットフォーム独自イベント

```python
# 特定プラットフォームの独自イベントを監視
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"独自イベントを受信: {data}")

# すべてのプラットフォームの独自イベントを監視（ワイルドカード）
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"独自イベントを受信: {data}")
```

#### イベント配信メカニズム

`adapter.emit(event_data)`を呼び出したとき：

1. **ミドルウェア処理**：まずすべてのOneBot12ミドルウェアを実行
2. **標準イベント配信**：マッチするOneBot12イベントハンドラに配信
3. **独自イベント配信**：元データがあれば独自イベントハンドラに配信

**マッチルール**：

- 精確マッチ：`@sdk.adapter.on("message")`は`message`イベントのみマッチ
- ワイルドカード：`@sdk.adapter.on("*")`はすべてのイベントにマッチ
- プラットフォームフィルタ：`platform="myplatform"`は指定プラットフォームのイベントのみ配信

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
    # 不要なイベントをフィルタ
    if data.get("type") == "notice":
        return None  # Noneを返すとミドルウェアチェーンはその返り値を無視し、元のデータを引き続き伝播
    return data  # 必須でデータを返すことで伝播を続ける
```

#### ミドルウェアの実行順序

ミドルウェアは登録順に実行され、後から登録されたミドルウェアが先に実行されます。

> **注意**：ミドルウェアが`None`を返した場合（`return data`を忘れているなど）、フレームワークはその返り値を無視し元のデータを引き続き伝播し、warningレベルのログを出力します。これにより、1つのミドルウェアのミスがイベントチェーン全体を中断することはありません。

```python
# 登録順
sdk.adapter.middleware(middleware1)  # 最後に実行
sdk.adapter.middleware(middleware2)  # 中間実行
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
from ErisPulse.Core.Bases import BaseConfig, BotAccountConfig

@dataclass
class MyConfig(BaseConfig):
    """アダプタの設定（宣言後フレームワークが自動管理）"""
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
    
    # __init__をオーバーライドする必要はない、フレームワークが自動処理する：
    # - self.sdk, self.logger
    # - self.cfg（型安全な設定インスタンス、リアルタイム読み取り）
    # - self.Send, self.Request
    
    async def start(self):
        """アダプタを起動する（必須実装）"""
        cfg = self.cfg  # 自動読み込みされた型安全な設定
        pass
    
    async def shutdown(self):
        """アダプタを停止する（必須実装）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォームAPIを呼び出す（必須実装）"""
        pass
```

### 設定管理

フレームワークは宣言的設定管理を提供し、dataclassを使って設定構造を定義し、フレームワークが自動的に読み込み、検証、テンプレート生成を処理します。

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
        cfg = self.cfg  # 型安全でリアルタイム読み取り
        if not cfg.token:
            raise ValueError("Tokenが設定されていません")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### 複数アカウント設定

`BotAccountConfig`基底クラスは`enabled`と`name`フィールドを提供します。ほとんどのアダプタはプラットフォームプロトコルやログイン応答から`bot_id`を自動的に取得でき、イベント変換時にアカウント設定に注入されます。

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

# 多くのアダプタでは、bot_idは実行時に自動取得され、設定は不要
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Token"},
        "required": True,
    })

# ログイン時にbot_idを取得できない場合は、ユーザーに設定してもらう
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

#### metadataの約束事

フィールドのmetadataはTOMLのコメント生成とWebUIフォームのレンダリングに使用されます：

```python
metadata = {
    "description": str | dict,  # フィールドの説明（i18nをサポート）
    "required": bool,         # 必須かどうか（検証 + WebUIの必須マーク）
    "secret": bool,           # 敏感情報かどうか（WebUIでは***表示、ログでは脱敏）
    "example": bool,          # 永続化しないフラグ：config.tomlに書き込まない（デフォルト値/テンプレートから除外）、config.full.exampleにのみレンダリングされる；schemaに"example": trueが付いている場合、CLI設定ガイドはデフォルトでスキップされる；ユーザーが手動で設定した後は通常永続化される
    "min": number, "max": number,  # 数値範囲検証
    "ui": {                   # WebUIコントロール設定（旧名"webui"も互換性あり）
        "widget": str,        # コントロールタイプ: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # グループ: "basic" | "advanced" | "connection" 等
        "order": int,         # ソートの重み（小さいほど前に表示）
        "options": list,      # selectコントロールの選択肢 [{label, value}]、labelはi18nをサポート
        "placeholder": str | dict,  # 入力欄のプレースホルダー（i18nをサポート）
    },
    "extra": dict,            # 余分な拡張フィールド（schemaに透かし送信）
}
```

すべてのユーザーが見えるテキストフィールドはi18nをサポートし、統一的に`{"i18n": "key", "default": "テキスト"}`形式を使用し、純粋な文字列はそのまま透かし送信（後方互換）。サポートされるi18nフィールド：

| フィールド | 位置 | 説明 |
|------|------|------|
| `description` | field metadata | フィールドの説明 |
| `options[].label` | `ui.options` | selectコントロールの選択肢ラベル |
| `placeholder` | `ui.placeholder` | 入力欄のプレースホルダー |
| `group_labels` | `_schema_meta` | グループ表示名（Dashboardのセクションタイトル） |

i18nを使用する場合、翻訳キーをi18nシステムに事前に登録する必要があります（[i18nドキュメント](../../advanced/i18n.md#配置フィールド多言語)を参照）。

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
                {"label": "純粋な文字列のラベル", "value": "b"},  # 純粋な文字列はそのまま透かし送信
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

フレームワークの`resolve_config_schema()`は現在の言語に応じて上記の全てのフィールドのi18nキーを自動的に解決します；`get_config_schema()`はi18n辞書をそのまま透かし送信し、フロントエンドが独自に解決します。

#### docstringから自動生成されるフィールド説明（v2.8.0+）

metadataに`description`を宣言していないフィールドは、フレームワークが設定クラスのdocstringからフィールドの説明を抽出してバックアップとして使用します。2種類の一般的なスタイルをサポートし、混用も可能です：

```python
@dataclass
class MyConfig(BaseConfig):
    """
    MyAdapterの設定

    :ivar endpoint: プラットフォームAPIアドレス        # reSTスタイル
    :ivar timeout: リクエストのタイムアウト秒数
    """

    endpoint: str = "https://api.example.com"   # metadata descriptionがない → docstringの説明/コメントを取得
    timeout: int = 30

    # Googleスタイルもサポート（Attributes:セクション）：
    # Attributes:
    #     endpoint: プラットフォームAPIアドレス
```

優先度：**metadata description > docstringフィールド説明 > 空**。i18n形式のdescriptionは影響を受けません（常に優先）。

#### 嵌套設定（v2.8.0+）

フィールドの型がネストされたdataclassの場合、フレームワークは再帰的に処理します：schemaは`"type": "table"` + `"fields"`サブツリーで構成され（WebUIでは折りたたみ可能なネストされたグループとしてレンダリング）、TOMLテンプレートは`[サブテーブル]`セクションとしてレンダリングされ、デフォルト値/埋め込み/検証/i18nの解決は再帰的に有効になります。

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

> 嵌套型は直接型注釈を使用することを推奨します；文字列注釈（遅延評価の場面など）は、型が設定クラスの所属モジュール全体、`__qualname__`の外側クラス名前空間、またはクラス属性から名前で解決できることを保証する必要があります。

#### 永続化しないexampleフィールド（v2.8.0+）

```python
gc_interval: int = field(default=300, metadata={"example": True})
```

`example: True`のフィールド：

- `config.toml`に書き込まれない（アダプタ/モジュールの設定テンプレートとデフォルト値は除外され、実行時のコードデフォルト値が使われる）
- `config.full.example`にのみレンダリングされる（ユーザーが参考として`config.toml`に手動でコピーする）
- schemaには`"example": true`のマークが付く（パネルは独自の表示戦略を決定できる）、CLI設定ガイドはデフォルトでスキップされる
- ユーザーがこのキーを手動で設定した後は通常永続化され、通常のホットアップデートが行われる（ユーザーの明示的な意図が優先）

「冗長でほとんど触れない」高度な設定項目に適しており、`config.toml`を最小限に保つことができます。

> ⚠️ `_schema_meta`はクラスレベルのメタデータ（設定フィールドではない）。`dataclass`クラス本体内部で宣言する場合は、`ClassVar`注釈を付ける必要があります（`_schema_meta: ClassVar[dict] = {...}`）、そうでなければ`dataclass`は普通のフィールドとして扱われます。フレームワークはアンダースコアで始まるフィールドを防御的に除外しています（すべてのschema/テンプレート/デフォルト値/検証出力から除外）、しかし規範的な宣言を推奨します。

### 宣言的翻訳キー（v2.7.0+）

アダプタは`ConfigClass`を宣言するように、`I18nClass`をネストして翻訳キーを一括宣言できます。フレームワークは`__init__`段階（設定テンプレート生成の前）で自動的に宣言されたすべての翻訳キーを登録し、設定説明で参照されるi18nキーがテンプレート生成時に利用可能になることを保証します。

```python
from ErisPulse.Core.Bases import BaseAdapter, BaseI18n, I18nKey

class MyAdapter(BaseAdapter):
    class I18nClass(BaseI18n):
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="APIアドレス",
            zh_TW="API位址",
            en="API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
        )
        token: I18nKey = I18nKey(
            default="Platform Token",
            zh_CN="プラットフォームToken",
            zh_TW="平台權杖",
            en="Platform Token",
            ja="プラットフォームトークン",
            ru="Токен платформы",
        )
```

> `I18nKey.default`は**言語に依存しないバックアップテキスト**で、どの言語にも登録されません。翻訳を有効にするには、少なくとも1つの言語パラメータを明示的に渡す必要があります。

詳細な使い方（キーのパスルール、明示的なkeyパラメータなど）は[翻訳ドキュメント](../../advanced/i18n.md#推奨書き方-i18nclass-を使用した翻訳キーの宣言-v270)を参照してください。

### 宣言的イベント拡張メソッド（v2.7.0+）

アダプタは`EventMixin`を使ってプラットフォーム特有のイベント拡張メソッドを一括宣言し、フレームワークは自動的に現在のプラットフォームに登録します。

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

登録後、イベントオブジェクトはこれらのメソッドを直接呼び出せます：

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] 公式メッセージを受信しました")
```

> アダプタのイベント拡張メソッドは自身のプラットフォーム（`self._platform`）に登録されます。モジュールがプラットフォーム間のイベント拡張を使用する場合は、従来の`register_event_mixin()` APIを使用してください。

#### アカウントの解決

多アカウントアダプタは`_resolve_account()`を使って送信先アカウントを自動的に解決できます：

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: アカウント名, account: 設定インスタンス
```

解決戦略：アカウント名一致 → `bot_id`フィールド一致 → 他のstrフィールド一致 → 最初の有効アカウント。

#### 設定のホットアップデート

サブクラスは`on_config_update()`をオーバーライドして設定変更に応答できます：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Tokenが更新されました、再接続します")
```

### 初期化プロセス

フレームワークは`BaseAdapter.__init__(self, sdk=None)`で自動的に以下の作業を行います：

1. **SDK参照**：`self.sdk`、`self.logger`を設定
2. **Send/Requestファクトリ**：`self.Send`と`self.Request`を作成
3. **設定テンプレート**：`ConfigClass`を宣言した場合、初期に自動的にデフォルト設定テンプレートを生成
4. **アカウントテンプレート**：`AccountConfigClass`を宣言した場合、初期に自動的にデフォルトアカウントテンプレートを生成
5. **EventMixin登録**：`EventMixin`を宣言した場合、`AdapterManager`にプラットフォーム名を注入した後に自動的に登録

設定は`self.cfg` / `self.accounts`でリアルタイムに読み取ります（各アクセス時に設定ストアから最新値を読み取ります）。`self.config`は`self.cfg`の互換別名として引き続き使用できます。

ほとんどのアダプタは`__init__`をオーバーライドする必要はありません。カスタム初期化が必要な場合：

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
| `_at_user_ids` | @ユーザーIDリスト | `At(user_id)` |
| `_reply_message_id` | 返信メッセージID | `Reply(message_id)` |
| `_at_all` | @全員 | `AtAll()` |

> **推奨**：`self.send_context`属性を使って`target_type`、`target_id`、`account_id`を一度に取得する方が、個々のインスタンス変数に直接アクセスするよりも明確です。

### フレームワーク補助メソッド

| メソッド/属性 | 説明 |
|-----------|------|
| `self._apply_modifiers(message)` | At/AtAll/Reply修飾子ステータスをメッセージセグメントリストにマージ |
| `self.send_context` | `{target_type, target_id, account_id}`辞書を返す |

### 基本メソッド

アダプタは`Raw_ob12`を実装するだけで済み、標準メソッド（Text/Image/Voice/Video/File）は`SendDSL`基底クラスから継承され、デフォルトで`Raw_ob12`に委譲されます：

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

    # Text/Image/Voice/Video/Fileは基底クラスから継承され、Raw_ob12に自動的に委譲されるため、再実装する必要はない
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
プラットフォーム独自イベント
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
    "{platform}_raw": {...},       # 元データ（必須）
    "{platform}_raw_type": "..."    # 元のタイプ（必須）
}
```

### 変換器の例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """プラットフォーム独自イベントをOneBot12標準形式に変換"""
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

> **ルート情報の照会**：アダプタが登録したルート（HTTP、WebSocket、SSE）は`sdk.adapter.get_connection_info(platform)`と`sdk.router.get_module_urls(module_name)`で完全な接続アドレス（`base_url` + パス）を照会できます。詳細は[アダプタ開発入門 - 接続情報とルート発見](getting-started.md#9-接続情報とルート発見)と[SSEサポート](getting-started.md#10-sse-server-sent-events-サポート)を参照してください。

## APIレスポンス標準

フレームワークは`make_response()`と`make_error()`メソッドを提供し、標準化されたレスポンスを構築します。レスポンス辞書を手動で構築する必要はありません。

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

`AccountConfigClass`を宣言して設定クラスを指定した後、フレームワークは自動的に多アカウントのロード、検証、テンプレート生成を管理します：

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

### アカウントを指定して送信

```python
# Usingメソッドでアカウントを指定
my_adapter = adapter.get("myplatform")

# イベントのself.user_idを使用（推奨、最も汎用的）
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# アカウント名を使用
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### self.user_id と Using の関係

フレームワークのイベント返信メカニズムは、イベントの`self`フィールドから`account_id`（優先）または`user_id`を抽出し、`Using`パラメータとして渡します。アダプタ開発者は、Converterで`self.user_id`の値が`_resolve_account()`で正しく一致することを保証する必要があります。

**フレームワーク内部の動作**：

```python
# フレームワークがbot_idを抽出するロジック
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# bot_idが空でない場合にUsingを呼び出す
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **重要な点**：アダプタが1つのBot設定しか使用しない場合でも、Converterで`self.user_id`を正しく設定している限り、フレームワークはそれを`Using`パラメータとして渡します。アダプタは`self.user_id`が`AccountConfigClass`の識別フィールド（例：`bot_id`）と一致することを保証し、`_resolve_account()`が正しいアカウントを一致させられるようにする必要があります。`self.user_id`が空の場合、フレームワークは`Using`を呼び出さず、`call_api`に受け取る`account_id`は`None`となり、`_resolve_account(None)`は最初の有効なアカウントを返します。

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
        # 推奨はSDKの内蔵クライアントを使用
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

> **互換性**：`aiohttp.ClientSession`を使用する旧アダプタコードは影響を受けず、`aiohttp.ClientError`をキャッチできます。2つの方法は共存できます。新規コードは`sdk.client` + ErisPulseの例外体系を使用することを推奨します。

## Botステータス管理

AdapterManagerにはBotのステータス追跡システムが内蔵されており、登録済みBotのオンラインステータス、アクティブ時間、メタ情報を自動的に管理します。

### 自動発見メカニズム

アダプタが`adapter.emit()`でイベントを送信するとき、フレームワークはイベントの`self`フィールドを自動的にチェックします：

- **metaイベント**：`detail_type`に応じて対応する操作を実行（connectでBotを登録/切断でオフラインをマーク/heartbeatでアクティブ時間を更新）
- **通常イベント**（message/notice/request）：Botを自動的に発見し、アクティブ時間を更新

```python
# selfフィールドを持つすべてのイベントは自動発見をトリガーする
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123" が自動的に登録（初めて出現した場合）され、アクティブ時間を更新される
```

### Metaイベントタイプ

| `detail_type` | 説明 | フレームワークの動作 |
|---|---|---|
| `connect` | Bot接続 | Botを登録し、`adapter.bot.online`ライフサイクルイベントをトリガー |
| `disconnect` | Bot切断 | Botをオフラインにマークし、`adapter.bot.offline`ライフサイクルイベントをトリガー |
| `heartbeat` | Botハートビート | Botのアクティブ時間とメタ情報を更新 |

### アダプタがMetaイベントを送信

`emit_meta()`で一行でMetaイベントを送信できます：

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # 一行でconnectイベントを送信
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="私のロボット")

    async def _on_bot_disconnect(self, bot_id: str):
        await self.emit_meta("disconnect", bot_id)
```

また、手動で構築することもできます（旧方式は互換性あり）：

```python
await self.adapter.emit({
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": bot_id}
})
```

### `self`フィールドの拡張情報

`self`フィールドには必須の`platform`と`user_id`に加えて、以下のオプションフィールドもサポートされます：

| フィールド | 説明 |
|---|---|
| `user_name` | Botのユーザー名 |
| `nickname` | Botのニックネーム |
| `avatar` | BotのアイコンURL |
| `account_id` | 多アカウント識別子 |

### Botステータスの照会

```python
from ErisPulse import sdk

# 単一Botの情報を取得
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# すべてのBotをリスト
all_bots = sdk.adapter.list_bots()

# 指定プラットフォームのBotをリスト
platform_bots = sdk.adapter.list_bots("myplatform")

# Botがオンラインか確認
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# 完全なステータスサマリーを取得（WebUI表示に適している）
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
- [SendDSL詳解](send-dsl.md) - メッセージ送信を学ぶ
- [アダプタベストプラクティス](best-practices.md) - 高品質なアダプタを開発する