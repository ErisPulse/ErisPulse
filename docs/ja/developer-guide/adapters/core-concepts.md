# アダプタのコア概念

> [!TIP]
> **この記事を読むべきタイミング**：アダプタ開発経路内では必読（BaseAdapter / SendDSL / ライフサイクルなど、コアメカニズムの完全な説明）。開発の立ち上げだけなら [アダプタ開発入門](getting-started.md) を先に読むと良い。"なぜこう書くのか"という疑問が生じた際は、この記事に戻って確認する。

この記事では、アダプタの実行メカニズムを説明します。AdapterManager がどのようにアダプタを登録・イベントを配信するか、`BaseAdapter` が初期化時に何をしてくれたか、設定と複数アカウントの宣言方法など——アダプタを開発する際に「なぜこう書くのか」という疑問が生じた場合、ここに確認してください。

## アダプタアーキテクチャ

### コンポーネント関係

```
正方向変換（受信方向）                           逆方向変換（送信方向）
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ プラットフォーム固有イベント     │                        │ モジュールが構築するメッセージ     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │  アダプタ (MyAdapter) │   │                  │
│  Converter       │   │ ┌──────────────┐ │   │ Send.Raw_ob12()  │
│  (イベント変換器)    │──→│ │              │ │   │ (逆方向変換エントリポイント)   │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ プラットフォーム API 調用    │
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
- **正方向変換**（Converter）：プラットフォーム固有イベント → OneBot12 標準イベント、元データは `{platform}_raw` に保持
- **逆方向変換**（Raw_ob12）：OneBot12 メッセージセグメント → プラットフォーム API 調用、返却は標準レスポンス形式

## AdapterManager アダプタマネージャー

`AdapterManager` は ErisPulse アダプタシステムのコアコンポーネントであり、すべてのプラットフォームアダプタの登録、起動、停止、イベント配信を管理します。

### コア機能

- **アダプタ登録**：複数のプラットフォームアダプタを登録・管理
- **ライフサイクル管理**：アダプタの起動と停止を制御
- **イベント配信**：OneBot12 標準イベントとプラットフォーム固有イベントを配信
- **設定管理**：アダプタの有効/無効状態を管理
- **ミドルウェアサポート**：OneBot12 イベントミドルウェアをサポート

### 基本的な使用方法

```python
from ErisPulse import sdk

# アダプタの登録（通常 Loader が自動で行う）
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

**起動フロー**：

1. `adapter.start` ライフサイクルイベントを送信
2. `adapter.status.change` イベントを送信（starting）
3. 各アダプタを並行起動
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

**停止フロー**：

1. `adapter.stop` ライフサイクルイベントを送信
2. 各アダプタの `shutdown()` メソッドを呼び出す
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
# すべての登録済みプラットフォームを取得
platforms = sdk.adapter.list_registered()

# すべてのプラットフォームとその状態を取得
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

#### プラットフォーム固有イベント

```python
# 特定のプラットフォームの固有イベントをリッスン
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"固有イベントを受け取りました: {data}")

# すべてのプラットフォームの固有イベントをリッスン（ワイルドカード）
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"固有イベントを受け取りました: {data}")
```

#### イベント配信メカニズム

`adapter.emit(event_data)` を呼び出すとき：

1. **ミドルウェア処理**：まずすべての OneBot12 ミドルウェアを実行
2. **標準イベント配信**：マッチする OneBot12 イベントハンドラに配信
3. **固有イベント配信**：元データがあれば、固有イベントハンドラに配信

**マッチルール**：

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
        return None  # 戻り値が None の場合、ミドルウェアチェーンはその値を無視し、元のデータをそのまま伝播
    return data  # 必須でデータを返して伝播を続ける
```

#### ミドルウェアの戻り値の契約

| 戻り値 | 行動 |
|--------|------|
| `dict` | イベントペイロードを上書き（後続のハンドラは変更後のイベントを受け取る） |
| `None` | 通過、ペイロードは変更なし（WARNINGを出力するが、明示的に`return data`を推奨） |
| `False` | **拒否**：イベントは破棄され、ハンドラには一切の副作用が発生しない |

拒否はファイアウォール、リクエスト制限、ブラックリストなど「イベントレベルで直接破棄」する場面に適しています（以前は高優先度のイベントハンドラで回避するしかありませんでした）。拒否された場合、フレームワークはTRACEログを出力し、`adapter.event.blocked` ライフサイクルフックをトリガーします（`middleware`ミドルウェア名、完全な`event`、`platform` / `event_type` / `detail_type`を含む）、イベントがなぜ反応しなかったのかを調査するのに便利です：

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

> **注意**：ミドルウェアが `None` を返した場合（`return data` を忘れている場合）、フレームワークはその返り値を無視して元のデータをそのまま伝播し、warningレベルのログを出力します。これにより、個々のミドルウェアのミスがイベントチェーン全体の中断を引き起こすことはありません。

```python
# 登録順
sdk.adapter.middleware(middleware1)  # 最後に実行
sdk.adapter.middleware(middleware2)  # 中間実行
sdk.adapter.middleware(middleware3)  # 最初に実行

# 実行順：middleware3 -> middleware2 -> middleware1
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
    """アダプター設定（宣言後はフレームワークが自動管理）"""
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
    
    # __init__ のオーバーライドは不要。フレームワークが自動的に処理：
    # - self.sdk, self.logger
    # - self.cfg（型安全な設定インスタンス、リアルタイム読み取り）
    # - self.Send, self.Request
    
    async def start(self):
        """アダプターを起動する（実装必須）"""
        cfg = self.cfg  # 自動的に読み込まれた型安全な設定
        pass
    
    async def shutdown(self):
        """アダプターをシャットダウンする（実装必須）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォーム API を呼び出す（実装必須）"""
        pass
```

### 設定管理

フレームワークは宣言的な設定管理を提供しています。dataclass で設定構造を定義すると、読み込み、検証、テンプレート生成が自動的に処理されます。

#### 単一アカウントの設定

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
            raise ValueError("Token が設定されていません")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### 複数アカウントの設定

`BotAccountConfig` 基底クラスは `enabled` と `name` フィールドを提供します。ほとんどのアダプターはプラットフォームのプロトコルやログインレスポンスから bot_id を自動取得でき、イベント変換時にアカウント設定へ注入します。

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

# ほとんどのアダプター：bot_id は実行時に自動取得されるため設定は不要
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Token"},
        "required": True,
    })

# ログイン時に bot_id を取得できない場合は、設定でユーザーに入力してもらうことができます
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

#### metadata の規約

フィールドの metadata は、TOML コメント生成と WebUI フォームレンダリングの両方に使用されます：

```python
metadata = {
    "description": str | dict,  # フィールドの説明（i18n 対応）
    "required": bool,         # 必須かどうか（検証 + WebUI の必須マーク）
    "secret": bool,           # 機密情報かどうか（WebUI では *** と表示、ログではマスキング）
    "example": bool,          # 永続化しないフラグ：config.toml に書き込まない（デフォルト値/テンプレートとも除外）、
                              # config.full.example にのみレンダリング；schema には "example": true のマークが付き、
                              # CLI 設定ウィザードではデフォルトでスキップ；ユーザーが手動設定した後は通常どおり永続化
    "min": number, "max": number,  # 数値範囲の検証
    "ui": {                   # WebUI コントロール設定（旧名 "webui" も互換）
        "widget": str,        # コントロールタイプ: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # グループ: "basic" | "advanced" | "connection" など
        "order": int,         # ソートの重み（小さいほど先に表示）
        "options": list,      # select コントロールの選択肢 [{label, value}]、label は i18n 対応
        "placeholder": str | dict,  # 入力フィールドのプレースホルダー（i18n 対応）
    },
    "extra": dict,            # 追加の拡張フィールド（schema へそのまま透過）
}
```

ユーザーに表示されるすべてのテキストフィールドは i18n に対応しており、統一して `{"i18n": "key", "default": "テキスト"}` 形式を使用します。純粋な文字列はそのまま透過されます（後方互換）。対応している i18n フィールド：

| フィールド | 場所 | 説明 |
|------|------|------|
| `description` | field metadata | フィールドの説明 |
| `options[].label` | `ui.options` | select コントロールの選択肢ラベル |
| `placeholder` | `ui.placeholder` | 入力フィールドのプレースホルダー |
| `group_labels` | `_schema_meta` | グループの表示名（Dashboard のセクションタイトル） |

i18n を使用する場合は、事前に翻訳キーを i18n システムへ登録しておく必要があります（詳細は [i18n ドキュメント](../../advanced/i18n.md#設定フィールドの多言語化) を参照）。

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
                {"label": "純粋な文字列ラベル", "value": "b"},  # 純粋な文字列はそのまま透過
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
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "高度な設定"},
    }
}
```

フレームワークの `resolve_config_schema()` は、現在の言語に応じて上記すべてのフィールドの i18n キーを自動解決します。`get_config_schema()` は i18n 辞書をそのまま透過し、フロントエンド側で解決します。

#### docstring によるフィールド説明の自動生成（v2.8.0+）

metadata で `description` が宣言されていないフィールドについては、フレームワークが設定クラスの docstring からフィールドの説明を自動抽出し、フォールバックとして使用します。一般的な 2 つのスタイルに対応しています（混用可）：

```python
@dataclass
class MyConfig(BaseConfig):
    """
    MyAdapter の設定

    :ivar endpoint: プラットフォーム API のアドレス        # reST スタイル
    :ivar timeout: リクエストのタイムアウト秒数
    """

    endpoint: str = "https://api.example.com"   # metadata description なし → コメント/説明は docstring から取得
    timeout: int = 30

    # Google スタイルも同様にサポート（Attributes: セクション）：
    # Attributes:
    #     endpoint: プラットフォーム API のアドレス
```

優先順位：**metadata description > docstring のフィールド説明 > 空**。
i18n 辞書形式の description は影響を受けません（常に優先されます）。

#### ネストした設定（v2.8.0+）

フィールドの型がネストした dataclass の場合、フレームワークは再帰的に処理します：schema は `"type": "table"` + `"fields"` のサブツリーとして表現され（WebUI では折りたたみ可能なネストグループとしてレンダリング）、TOML テンプレートでは `[サブテーブル]` セクションとしてレンダリングされます。デフォルト値 / 補完 / 検証 / i18n 解決はいずれも再帰的に適用されます。

```python
@dataclass
class RetryConfig(BaseConfig):
    """リトライポリシー

    :ivar max_retries: 最大リトライ回数
    """
    max_retries: int = 3
    backoff: float = 0.5

@dataclass
class MyConfig(BaseConfig):
    """MyAdapter の設定"""
    endpoint: str = "https://api.example.com"
    retry: RetryConfig = field(default_factory=RetryConfig)   # ネストした設定セクション
```

生成される TOML テンプレート：

```toml
endpoint = "https://api.example.com"

[retry]
# 最大リトライ回数
max_retries = 3
backoff = 0.5
```

> ネストした型には直接の型アノテーションを推奨します。文字列アノテーション（遅延評価のシナリオなど）の場合は、型が設定クラスの所在モジュールのグローバル名前空間、`__qualname__` の外側クラスの名前空間、またはクラス属性から名前で解決できることを保証する必要があります。

#### 永続化されない example フィールド（v2.8.0+）

```python
gc_interval: int = field(default=300, metadata={"example": True})
```

`example: True` を持つフィールドは以下のとおりです：

- config.toml には書き込まれない（アダプター/モジュールの設定テンプレートとデフォルト値のいずれからも除外され、実行時はコード上のデフォルト値が使用される）
- プロジェクト内の `config.full.example` にのみレンダリングされる（ユーザーの参考用。必要に応じて config.toml へ手動でコピー）
- schema には `"example": true` のマークが付く（パネル側で表示ポリシーを自由に決定可能）。CLI 設定ウィザードではデフォルトでスキップ
- ユーザーが手動でこのキーを設定した後は、通常どおり永続化・ホットアップデートされる（ユーザーの明示的な意図が優先）

「冗長でほとんど触れることのない」高度な設定項目に適しており、ユーザーの config.toml を最小限に保てます。

> ⚠️ `_schema_meta` はクラスレベルのメタデータです（設定フィールドではありません）。dataclass のクラス本体内で宣言する場合は、必ず `ClassVar` アノテーションを付ける必要があります（`_schema_meta: ClassVar[dict] = {...}`）。そうしないと、dataclass に通常のフィールドと見なされます。フレームワークはアンダースコア接頭辞のフィールドに対して防御的な除外を行っています（schema / テンプレート / デフォルト値 / 検証出力のいずれにも含まれません）が、それでも規約に従った宣言を推奨します。

### 宣言的な翻訳キー（v2.7.0+）

アダプターは `ConfigClass` を宣言するのと同じように、ネストクラス `I18nClass` によって翻訳キーを一元的に宣言できます。フレームワークは `__init__` の段階（設定テンプレート生成の前）で、宣言されたすべての翻訳キーを自動登録するため、設定の説明で参照される i18n キーがテンプレート生成時に利用可能であることが保証されます。

```python
from ErisPulse.Core.Bases import BaseAdapter, BaseI18n, I18nKey

class MyAdapter(BaseAdapter):
    class I18nClass(BaseI18n):
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="API アドレス",
            zh_TW="API アドレス",
            en="API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
        )
        token: I18nKey = I18nKey(
            default="Platform Token",
            zh_CN="プラットフォーム Token",
            zh_TW="プラットフォーム Token",
            en="Platform Token",
            ja="プラットフォームトークン",
            ru="Токен платформы",
        )
```

> ``I18nKey.default`` は**言語に依存しないフォールバックテキスト**であり、どの言語にも登録されません。
> 翻訳を有効にするには、少なくとも 1 つの言語パラメータを明示的に渡す必要があります。

詳細な使い方（キーのパス規則、明示的な key パラメータなど）については、[i18n ドキュメント](../../advanced/i18n.md#推奨される書き方i18nclassによる翻訳キーの宣言v270) を参照してください。

### 宣言的なイベント拡張メソッド（v2.7.0+）

アダプターは `EventMixin` を通じて、プラットフォーム固有のイベント拡張メソッドを一元的に宣言できます。フレームワークが現在のプラットフォームへ自動登録します。

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    class EventMixin:
        def get_chat_name(self):
            """チャット名を取得する"""
            return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

        def is_official_message(self):
            """公式メッセージかどうかを判定する"""
            raw = self.get("myplatform_raw", {})
            return raw.get("sender", {}).get("is_official", False)
```

登録後は、イベントオブジェクトからこれらのメソッドを直接呼び出せます：

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] 公式メッセージを受信しました")
```

> アダプターのイベント拡張メソッドは、自身のプラットフォーム（``self._platform``）に登録されます。
> モジュールでクロスプラットフォームのイベント拡張が必要な場合は、既存の ``register_event_mixin()`` API を使用してください。

#### アカウントの解決

アダプターが `call_api` を実装する際は、アカウント識別子を具体的なアカウント設定へ解決する必要があります。フレームワークはアカウントのバインディング（`Using()` またはイベントチェーンによる自動バインディングの結果）を標準フィールド `account_id` として `call_api` に渡し、アダプターの実際の消費方法に応じて自動的に適応させます。3 つの消費形態のいずれかを選択でき、フレームワークはシグネチャのパラメータ名と関数本体内の定数によって検出するため、パラメータの位置は問いません：

```python
# 形態 1（推奨）：シグネチャで標準名を宣言
async def call_api(self, endpoint: str, account_id: str | None = None, **params):
    name, account = self._resolve_account(account_id)
    # name: アカウント名, account: 設定インスタンス

# 形態 2（既存互換）：旧名 _account_id。フレームワークが account_id を自動的に旧名へ書き換えて渡す
async def call_api(self, endpoint: str, _account_id: str | None = None, **params):
    name, account = self._resolve_account(_account_id)

# 形態 3：関数本体内で params から取得（定数検出により識別される）
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
```

> アダプターがアカウントフィールドを消費しない場合、フレームワークはそのフィールドを除去し（プラットフォームパラメータへの混入を防止）、WARNING を一度出力します。単一アカウントのアダプターでは消費しなくても構いません（解決は最初に有効化されているアカウントへフォールバックします）。

解決ポリシー：アカウント名の一致 → `bot_id` フィールドの一致 → その他の str フィールドの一致 → 最初に有効化されているアカウント。

**実行時の識別と永続化**（2.12+）：アダプターは接続の確立時 / イベントの到着時に `self.update_bot_id(account_name, bot_id)` を呼び出します。フレームワークは bot_id → アカウントのレジストリを維持し（解決チェーンの第一優先度）、値が変化した際に `accounts.<アカウント名>.bot_id` を設定ストレージへ書き込みます：再起動後はアカウントインスタンスの再構築時に bot_id が付与された状態になるため、第 2 アカウントなどのシナリオにおける解決がアカウントアクティビティによるバックフィルに依存しなくなります（再起動時のウィンドウ期間を解消）。

#### 設定のホットアップデート

サブクラスは `on_config_update()` をオーバーライドして設定変更に応答できます：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Token が更新されました。再接続します")
```

### 初期化プロセス

フレームワークは `BaseAdapter.__init__(self, sdk=None)` 内で以下の処理を自動的に行います：

1. **SDK 参照**：`self.sdk`、`self.logger` を設定
2. **Send/Request ファクトリ**：`self.Send` と `self.Request` を作成
3. **設定テンプレート**：`ConfigClass` が宣言されている場合、デフォルトの設定テンプレートを自動生成（初回のみ）
4. **アカウントテンプレート**：`AccountConfigClass` が宣言されている場合、デフォルトのアカウントテンプレートを自動生成（初回のみ）
5. **EventMixin の登録**：`EventMixin` が宣言されている場合、`AdapterManager` によるプラットフォーム名の注入後に自動登録

設定は `self.cfg` / `self.accounts` からリアルタイムに読み込まれます（アクセスのたびに設定ストレージから最新値が読み取られます）。`self.config` は `self.cfg` の互換エイリアスとして引き続き使用できます。

ほとんどのアダプターでは `__init__` のオーバーライドは不要です。カスタム初期化が必要な場合：

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
| `_target_to` | 簡略化された目標ID | `To(id)` |
| `_account_id` | 送信アカウントID | `Using(account_id)` |
| `_adapter` | アダプタインスタンス | 自動設定 |
| `_at_user_ids` | @ユーザーIDリスト | `At(user_id)` |
| `_reply_message_id` | レスポンスするメッセージID | `Reply(message_id)` |
| `_at_all` | @全員か | `AtAll()` |

> **推奨**：`self.send_context` 属性を使って `target_type`、`target_id`、`account_id` を一括で取得するようにしてください。個々のインスタンス変数にアクセスするよりも明確です。

### フレームワーク補助メソッド

| メソッド/属性 | 説明 |
|-----------|------|
| `self._apply_modifiers(message)` | At/AtAll/Reply 修飾子の状態をメッセージセグメントリストにマージする |
| `self.send_context` | `target_type`、`target_id`、`account_id` の辞書を返す；`account_id` が明示的に指定されていない場合は、イベント配信チェーンのトリガーアカウントをデフォルトにする |

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

    # Text/Image/Voice/Video/File は基底クラスから継承され、Raw_ob12 にデフォルトで委譲されるため、再実装は不要
    # プラットフォーム固有のロジックが必要な場合は、単一メソッドをオーバーライドすることができる：
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
プラットフォーム固有イベント
    ↓
Converter.convert()
    ↓
OneBot12 標準イベント
```

### 必須フィールド

変換後のイベントはすべて以下のフィールドを含む必要があります：

```python
{
    "id": "イベントの唯一識別子",          # 同一アカウントで同じイベントを再送信する際は同じ値にする必要がある（フレームワークが重複を防ぐ）
    "time": 1234567890,           # 10桁の Unix タイムスタンプ
    "type": "message/notice/request/meta",
    "detail_type": "イベントの詳細タイプ",
    "platform": "プラットフォーム名",
    "message_id": "メッセージID",        # メッセージ系イベントは必須
    "self": {
        "platform": "プラットフォーム名",
        "user_id": "ロボットID"     # bot_id と一致する必要がある
    },
    "{platform}_raw": {...},       # 元データ（必須）
    "{platform}_raw_type": "..."    # 元のタイプ（必須）
}
```

> イベント `id` にはアカウントの次元が必要です：同一アカウントで同じイベントを再送信する際は `id` を同じにする必要があります。異なるアカウントが同じグループ/会話で同じ物理メッセージを受け取る場合、`id` は異なる必要があります（たとえば `f"{self.user_id}:{post_type}:{message_id}"` のように）。

### 複数アカウントの重複受信（フレームワークが注入するフィールド）

複数アカウントアダプタの複数のアカウントが同じグループ/会話で、同一の物理メッセージが各アカウントに順次到達する場合、フレームワークは `ErisPulse.framework.cross_account_policy != "off"` の場合、内容ベースの関連付け（同じプラットフォーム + 同じ会話 + 同じ送信者 + 同じ `alt_message` が短い時間内に）を自動的に行い、アダプタは関与する必要はありません：

- `mark`：後続のコピーは `multi_receipt` というトップレベルのフィールド `{"event_id": 初回受理イベントのID, "self_id": 初回受理アカウント}` を注入して通常通り配信され、モジュールはこのフィールドを読んで裁決する
- `drop`：後続のコピーは配信の入口で直接破棄される

`multi_receipt` はフレームワークが注入するオプションのフィールドであり、アダプタの変換器は生成も消費もしません。ポリシーはデフォルトで `off` で、イベントの構造は既存の契約と完全に一致します。

#### 3層の重複防止メカニズムの役割分担

| メカニズム | 設定 | 拦截するもの | 判定依据 |
|------|------|----------|----------|
| イベントの冪等性重複防止 | `ErisPulse.framework.event_dedupe`（デフォルト有効） | 同一イベント id の再接続再送信（同一接続） | イベント `id` |
| 本アカウントの自己発言フィルタ | `ErisPulse.event.message.ignore_self`（デフォルト有効） | 受信アカウント自身のメッセージ（送信者 == 受信アカウント） | `self.user_id` vs `user_id` |
| 複数アカウントの重複受信 | `ErisPulse.framework.cross_account_policy`（デフォルト `off`、`drop` 有効） | **同一物理メッセージが他のアカウントのコピー**——複数アカウントが同じグループで bot A が発言し、bot B も同様のメッセージを1つ受け取る | 内容ベースの関連付け（同プラットフォーム + 同会話 + 同送信者 + 同内容、短い時間内）、キーには self_id は含まれない |

**典型的なシナリオ——複数アカウントが同じグループで発言**：bot A が発言し、同じグループ内の他のアカウント（bot B）も同様のメッセージを1つ受け取る。`cross_account_policy = "drop"` を有効にすると、後続のアカウントのコピーは配信の入口で破棄され、どのモジュールも1回だけ表示されます。

`ignore_self` と `cross_account_policy` の意味は直交しており、2つの組み合わせで表示回数が決まります：

| 組み合わせ | フォローミュールが bot A のメッセージを見る回数 |
|------|--------------------------|
| `drop` + `ignore_self = true`（デフォルト） | 0 または 1 回（先に到着したコピーが A 自身の接続から `ignore_self` でブロックされた場合）——**2回になることはない** |
| `drop` + `ignore_self = false` | 恒定で1回（先に到着したコピーが A 自身の接続からブロックされない限り） |

> `ignore_self` の意味を「自身の全アカウントを排除する」に拡張しないでください：この判定は受信イベントの `self.user_id`（バインドが確立していない期間に失敗する可能性がある、上記の実行時境界を参照）に依存しており、複数アカウントの関連付けは内容ベースの判定であり、`self` 情報に依存しません。また、「各アカウントの受信」は複数アカウントのログや同期系モジュールの既存の依存関係であり、その意味を狭めるのは暗黙の破壊です。複数アカウントの重複は `cross_account_policy` に任せてください。

### 変換器の例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """プラットフォーム固有イベントを OneBot12 標準形式に変換"""
        if not isinstance(raw_event, dict):
            return None
        
        # イベント ID を生成
        event_id = raw_event.get("event_id") or str(uuid.uuid4())
        
        # 時間スタンプを変換
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

クライアントモードのアダプタ（WebSocketクライアント、HTTPポーリングなど）は `start()` で常駐接続ループを起動する必要があります。フレームワークは2つの書き方をサポートしていますが、**どちらか一方のみ使用できます**。

**書き方1：spawn-返却式（推奨）**——`spawn_client_loop()` でループをプラットフォームに属するバックグラウンドタスクとしてスケジュールし、`start()` は即座に返ります：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # ループタスクは self._platform に属するため、shutdown でフレームワークが自動的にキャンセル
        self.spawn_client_loop(self._connect_loop())
        # start はここで終了——"起動成功"と即座に返す。接続失敗はループ内で再試行

    async def _connect_loop(self):
        while True:
            try:
                await self._connect_and_receive()   # 切断は例外 → 下方の退避
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(5)              # ループ内で再試行
```

**書き方2：常駐式**——`start()` で接続ループを `await` し、決して返りません：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        await self._connect_loop()   # 常駐で返らない；ループが例外を投げた場合、フレームワークの再試行チェーンに渡される
```

2つの書き方の違いと共通点：

| | spawn-返却式 | 常駐式 |
|---|---|---|
| `start()` の返り時点 | ループ起動後即座に返る | 接続ループが終了/失敗した時（フレームワークは退避戦略で再試行） |
| 接続失敗の処理 | ループ内で例外を捕まえて退避 | 例外を上昇させ、フレームワークの再試行チェーンに渡す |
| 適用場面 | 複数接続、ルーティング登録後に他のタスクを起動する必要がある場合 | "接続即起動"の意味を持つ単純な実装 |

`spawn_client_loop(coro, *, name="client_loop")` は書き方1のスケジューラーの入り口です：タスクは `self._platform` に属して登録され、アダプタの `shutdown()` 時にフレームワークが自動的にキャンセルされます。ループ内で未捕獲の例外は自動的に記録されます（意図的な切断再接続はループ内で捕まえてください）。

> **唯一の誤った書き方は混用すること**：spawn の後に `await` で同じループを実行すると、`start()` は即座に返る意味を失い、タスクのキャンセル経路が予測不可能になります。

### 接続モードの半完成基底クラス

上記の2つの書き方のほか、最も一般的な2つの接続モードに対してフレームワークは「半完成」の基底クラスを提供しています（`ErisPulse.Core.Bases.adapter_patterns`、ルートパッケージから直接インポート可能）：`start` / `shutdown` のライフサイクルの編集はすべて基底クラスが行い、サブクラスは業務フックを実装するだけです。

#### PollingAdapter（HTTPポーリング型）

「クライアントが定期的にイベントを取得する」プラットフォーム（Telegram getUpdates型）に適しています。基底クラスはspawn-返却式で常駐ポーリングループを起動し、取得失敗は自動的に記録され指数退避されます（基数1秒、上限60秒、成功後はゼロに戻る；定数 `POLLING_ADAPTER_BACKOFF_BASE_SECS` / `POLLING_ADAPTER_BACKOFF_MAX_SECS` は `Core/constants.py` で調整可能）：

```python
from ErisPulse import PollingAdapter

class MyAdapter(PollingAdapter):
    # ポーリング間隔はデフォルト5秒；ConfigClass で poll_interval フィールドを宣言した場合は設定値が優先される（ホットアップデート有効）
    poll_interval = 5.0

    async def fetch_events(self):
        """プラットフォーム固有イベントを一括取得（例外は基底クラスが退避し、try/exceptは不要）"""
        resp = await self.sdk.client.get(f"{self.cfg.endpoint}/getUpdates")
        data = await resp.json()
        return data.get("result", [])

    def convert_one(self, raw):
        """1件の固有イベントをOneBot12に変換；Noneを返すとスキップ"""
        return self.converter.convert(raw)

    async def call_api(self, endpoint: str, **params):
        ...  # 普通のアダプタと同じ
```

最小実装面：`fetch_events` / `convert_one` / `call_api`。`start()` でループを起動して即座に返る；`shutdown()` はサブクラスで処理する必要がない（ポーリングループはownerに属して自動的にキャンセルされる）。

#### WebhookAdapter（HTTPコールバック型）

「プラットフォームがコールバックを送信する」プラットフォームに適しています。基底クラスの `start()` はフレームワークの router にコールバック受信ルートを登録します（最終パスは `/{プラットフォーム名}/webhook`、POSTメソッド）、登録は `owner_scope` で行われる——アダプタのアンロード時にownerに従って自動的にクリーンアップされるため、手動で登録解除する必要はない：

```python
from ErisPulse import WebhookAdapter

class MyAdapter(WebhookAdapter):
    def verify_request(self, request) -> bool:
        """オプションフック：コールバック検証（デフォルトで許可；Falseを返すと基底クラスが403で拒絶）"""
        cfg = self.cfg
        if not cfg.token:
            return True
        auth = request.headers.get("authorization", "")
        return auth == f"Bearer {cfg.token}"

    def convert(self, payload):
        """コールバックペイロードをOneBot12に変換；Noneを返すとスキップ"""
        return self.converter.convert(payload)

    async def call_api(self, endpoint: str, **params):
        ...  # 普通のアダプタと同じ
```

最小実装面：`convert` / `call_api`（`verify_request` はオプション）。コールバックアドレスは `sdk.adapter.get_connection_info(platform)` で取得してプラットフォームのバックエンドに設定する。検証に失敗したリクエストは403、ペイロード解析に失敗したリクエストは400、正常なリクエストは `{"status": "ok"}` を返す。

#### 3つのモードの使い分け

| プラットフォームプロトコル | 継承 | フレームワーク |
|---|---|---|
| プラットフォームが接続してくる（WebSocketサーバー） | `BaseAdapter` | `epsdk create adapter`（デフォルト ws-server） |
| 自分がポーリングする（HTTPポーリング） | `PollingAdapter` | `epsdk create adapter --template polling` |
| プラットフォームがコールバックしてくる（HTTPコールバック） | `WebhookAdapter` | `epsdk create adapter --template webhook` |

実行可能な完全な例はリポジトリの `examples/example-adapter/`（ws-server）、`examples/example-adapter-polling/`、`examples/example-adapter-webhook/` を参照してください。

### WebSocket 接続

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

### WebHook 接続

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

> コールバック型のプラットフォームでは、上記の登録/検証/クリーンアップの編集を手動で書く必要はありません——`[WebhookAdapter` 半完成基底クラス](#接続モード半完成基底クラス)を継承し、`convert`（`verify_request` をオーバーライドする場合も可）を実装するだけです。

> **ルート情報の取得**：アダプタが登録したルート（HTTP、WebSocket、SSE）は、`sdk.adapter.get_connection_info(platform)` と `sdk.router.get_module_urls(module_name)` を使って完全な接続アドレス（`base_url` + パス）を取得できます。[アダプタ開発入門 - 接続情報とルート発見](getting-started.md#9-接続情報とルート発見)と [SSE 支持](getting-started.md#10-sse-server-sent-events-サポート)を参照してください。

## API レスポンス標準

フレームワークは `make_response()` と `make_error()` メソッドを使って標準化されたレスポンスを構築し、手動でのレスポンス辞書の構築は不要です。

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

`AccountConfigClass` を宣言して設定クラスを定義した後、フレームワークは自動的に複数アカウントのロード、検証、テンプレート生成を管理します：

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

### アカウント指定での送信

```python
# Using メソッドでアカウントを指定
my_adapter = adapter.get("myplatform")

# イベントの self.user_id を使用する（推奨、最も汎用的）
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# アカウント名を指定
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### イベントのアカウント識別子と Using の関係

フレームワークのイベント返信メカニズムは、イベントの `self` フィールドからアカウント識別子（`account_id` が優先され、`user_id` がバックアップ）を抽出し、`Using` に注入します。アダプタの開発者は、Converter が生成するアカウント識別子がアカウント設定（アカウント名や `bot_id` など）と一致することを保証する必要があります。

**フレームワークが注入する動作**：

```python
# フレームワークがアカウント識別子を抽出するロジック（account_id が優先され、user_id がバックアップ）
account = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# アカウント識別子が空でない場合に Using を注入
if account:
    send_chain = send_chain.Using(account)
```

> **重要な点**：アダプタが1つの Bot 設定しか使用しない場合でも、Converter がアカウント識別子を正しく設定している限り、フレームワークはそれを `Using` に注入します。アダプタは、この識別子が `AccountConfigClass` のアカウント名や `bot_id` などのフィールドと一致していることを保証する必要があります。識別子が空の場合、フレームワークは `Using` を注入せず、その場合、送信は未指定アカウントで処理されます——最初の有効なアカウントにフォールバックします。

明示的に渡された `account_id` が解析できない場合、フレームワークは WARNING を記録し、最初の有効なアカウントにフォールバックします；WARNING に含まれる `platform` / `account_id` / `account` は、アカウントに属さないイベントの原因を特定するのに使用できます。

**イベント処理チェーン内の自動バインディング**：イベント処理チェーン内で送信メソッドを呼び出す際は**明示的に `Using()` を指定する必要はありません**——フレームワークはイベント処理の入口でトリガーイベントのアカウント識別子を注入し、`Send` / `Api` / `Request` チェーンが明示的に `Using()` を指定していない場合、その上下文に基づいてデフォルトでバインディングされます（明示的な `Using()` は常に優先されます；タイマー / スタートタスクなどのイベント上下文がない場面ではデフォルトアカウントの意味が維持されます）。イベントチェーンの自動バインディングは ErisPulse **2.12+** が必要です。

> イベント `self.user_id` / `self.account_id` の代位の生成契約は[イベント変換標準](../../standards/event-conversion.md)を参照してください；このフィールドが恒常的に存在することがアカウント解析のフォールバック意味の前提です——存在しない場合、最初の有効なアカウントにフォールバックし、複数アカウントの場合は「デフォルトアカウントから送信される」ことになります。

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
        # 推奨は SDK 内部のクライアントを使用
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
        self.logger.error(f"不明なエラー: {e}")
        return self._error_response(str(e), 34000)
```

> **互換性**：`aiohttp.ClientSession` を使用する古いアダプタコードは影響を受けません。`aiohttp.ClientError` を捕まえることができます。2つの方法は共存できます。新しいコードは `sdk.client` + ErisPulse の例外体系を使用することを推奨します。

## Bot 状態管理

AdapterManager には Bot 状態の追跡システムが内蔵されており、すべての登録された Bot のオンライン状態、アクティブ時間、およびメタ情報を自動的に管理します。

### 自動発見メカニズム

アダプタが `adapter.emit()` を使ってイベントを送信するとき、フレームワークはイベントの `self` フィールドを自動的にチェックします：

- **meta イベント**：`detail_type` に応じて対応する操作を実行（connect で登録/ disconnect でオフラインをマーク/ heartbeat でアクティブ時間を更新）
- **普通のイベント**（message/notice/request）：Bot の自動発見とアクティブ時間の更新

```python
# self フィールドを含むすべてのイベントは自動発見をトリガーします
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123" は自動的に登録され（最初に出現した場合）、アクティブ時間を更新されます
```

### Meta イベントタイプ

| `detail_type` | 説明 | フレームワークの動作 |
|---|---|---|
| `connect` | Bot が接続 | Bot を登録し、`adapter.bot.online` ライフサイクルイベントをトリガー |
| `disconnect` | Bot が切断 | Bot のオフラインをマークし、`adapter.bot.offline` ライフサイクルイベントをトリガー |
| `heartbeat` | Bot のハートビート | Bot のアクティブ時間とメタ情報を更新 |

### アダプタが Meta イベントを送信

送信方法（`emit_meta()` で1行送信、ハートビートイベントと手動構成形式）は [アダプタのベストプラクティス - Bot 状態管理と Meta イベント](best-practices.md#bot-状態管理と-meta-イベント) を参照してください。

### `self` フィールドの拡張情報

`self` フィールドは必須の `platform` と `user_id` の他に、以下のオプションフィールドをサポートします：

| フィールド | 説明 |
|---|---|
| `user_name` | Bot のユーザー名 |
| `nickname` | Bot のニックネーム |
| `avatar` | Bot のアイコン URL |
| `account_id` | 複数アカウントの識別子 |

### Bot 状態の照会

照会 API（`get_bot_info()` / `list_bots()` / `is_bot_online()` / `get_status_summary()`）は [アダプタシステム API - Bot 状態管理](../../api-reference/adapter-system.md#bot-状態管理) を参照してください。

### Bot ライフサイクルの監視

`adapter.bot.online` / `adapter.bot.offline` ライフサイクルイベントの表と監視例は [アダプタシステム API - Bot 状態管理](../../api-reference/adapter-system.md#bot-状態管理) を参照してください。

## 関連ドキュメント

### 実装面の詳細

- [SendDSL 詳解](send-dsl.md) - メッセージ送信の学習
- [アダプタのベストプラクティス](best-practices.md) - 高品質なアダプタの開発

### 再びステップを振り返る

- [アダプタ開発入門](getting-started.md) - 最初のアダプタを作成する