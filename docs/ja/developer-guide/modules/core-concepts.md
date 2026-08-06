# モジュールの基本概念

ErisPulse モジュールの基本概念を理解することは、高品質なモジュールを作成するための基盤となります。

## モジュールのライフサイクル

### ロード戦略

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """モジュールのロード戦略を返します"""
        return ModuleLoadStrategy(
            lazy_load=True,   # 延遅ロードか即時ロードか
            priority=0,       # ロード優先度（数値が大きいほど先にロードされます）
            depends=["OtherModule"]  # オプション：依存する他のモジュールを宣言
        )
```

> `depends` で宣言されたモジュールが未登録の場合、現在のモジュールはスキップされ、警告が記録されます。ロード順序はトポロジカルソートによって決定され、同じ階層では `priority` 降順になります。

### on_load メソッド

モジュールのロード時に呼び出され、リソースの初期化やイベントハンドラーの登録に使用されます：

```python
async def on_load(self, event):
    # イベントハンドラーを登録
    @command("hello", help="挨拶コマンド")
    async def hello_handler(event):
        await event.reply("こんにちは！")
    
    # SDKの組み込みHTTPクライアントを使用（接続プールを自動管理するため、手動でセッションを作成する必要はありません）
    # sdk.client からリクエストを送信できます
```

### on_unload メソッド

モジュールのアンロード時に呼び出され、リソースのクリーンアップに使用されます：

```python
async def on_unload(self, event):
    # カスタムリソースのクリーンアップ
    # sdk.client はフレームワークが管理するため、手動で閉じる必要はありません
    
    # イベントハンドラーのキャンセル（フレームワークが自動的に処理します）
    self.logger.info("モジュールがアンロードされました")

## SDK オブジェクト

### コアモジュールへのアクセス

```python
from ErisPulse import sdk

# sdk オブジェクトを通じてすべてのコアモジュールにアクセスする
sdk.logger.info("ログ")
sdk.storage.set("キー", "値")
config = sdk.config.getConfig("MyModule")
```

### モジュール間通信

```python
# 他のモジュールにアクセスする
other_module = sdk.OtherModule
result = await other_module.some_method()

## アダプタ送信方法の照会

新しい標準仕様では、フォールバック送信機構を実装するために `__getattr__` メソッドを上書きすることが求められるため、`hasattr` メソッドを使用してメソッドの存在を確認することができなくなりました。バージョン `2.3.5` 以降、送信方法を照会する機能が追加されました。

### サポートされている送信方法のリスト

```python
# プラットフォームがサポートするすべての送信方法を一覧表示する
methods = sdk.adapter.list_sends("onebot11")
# 返回: ["Text", "Image", "Voice", "Markdown", ...]
```

### メソッドの詳細情報の取得

```python
# 特定のメソッドの詳細情報を取得する
info = sdk.adapter.send_info("onebot11", "Text")
# 返回:
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "テキストメッセージを送信..."
# }

## 設定管理

### 宣言的設定（推奨）

v2.5.2 以降、モジュールは `ConfigClass` を使用して設定クラスを宣言できるようになりました。アダプターと同じ設定 Schema システムを使用します。設定は `self.cfg` でリアルタイムに読み出され、変更後はすぐに有効になります：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_key: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_module.api_key", "default": "API キー"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 1},
        },
    )
    timeout: int = field(
        default=30,
        metadata={
            "description": {"i18n": "my_module.timeout", "default": "タイムアウト（秒）"},
            "ui": {"widget": "number", "group": "advanced", "order": 2},
        },
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def on_load(self, event):
        self.logger.info("モジュールがロードされました")

    async def on_unload(self, event):
        pass

    async def do_something(self):
        cfg = self.cfg  # リアルタイム読み出し、型安全
        api_key = cfg.api_key
        timeout = cfg.timeout
```

`BaseConfig` は汎用的な設定基底クラスで、アダプター、モジュール、外部プロジェクトなどあらゆるシーンに適用できます。設定フィールドは i18n 多言語記述をサポートしています（詳細は [i18n ドキュメント](../../advanced/i18n.md#設定フィールド多言語)をご参照ください）。

### 宣言的翻訳キー（v2.7.0+）

v2.7.0 以降、モジュールは `ConfigClass` を宣言するのと同様に、ネストされた `I18nClass` クラスを使って翻訳キーを一括で宣言することもできます。フレームワークはロード時に宣言されたすべての翻訳キーを**自動的に登録**するため、手動で `i18n.register()` を呼び出す必要はありません。また、設定テンプレートの生成より早いタイミングで登録されるため、設定記述で参照する i18n キーが利用可能であることが保証されます。

```python
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, I18nKey

class MyModule(BaseModule):
    # 設定クラス（任意）
    @dataclass
    class ConfigClass(BaseConfig):
        welcome_msg: str = field(
            default="欢迎",
            metadata={
                "description": {"i18n": "mymodule.welcome_msg", "default": "ウェルカムメッセージ"},
            },
        )

    # 翻訳キーセットクラス（任意）
    class I18nClass(BaseI18n):
        # プロパティ名が自動的に完全なキーパスに連結されます：<モジュール名>.<プロパティ名>
        welcome_msg: I18nKey = I18nKey(
            default="Welcome Message",   # 言語に依存しないフォールバック
            zh_CN="欢迎消息",
            zh_TW="歡迎訊息",
            en="Welcome Message",
            ja="ウェルカムメッセージ",
            ru="Приветственное сообщение",
        )
        hello: I18nKey = I18nKey(
            default="Hello, {name}!",
            zh_CN="你好，{name}！",
            zh_TW="你好，{name}！",
            en="Hello, {name}!",
            ja="こんにちは、{name}！",
            ru="Привет, {name}!",
        )
```

詳細は [i18n 推奨の記述方法](../../advanced/i18n.md#推奨の記述方法I18nClassで翻訳キーを宣言するv270) を参照してください。

### 手動による設定の読み込み（互換方式）

宣言的設定を使用しない場合、直接設定ストレージに対して読み書きすることも可能です。

```python
def _load_config(self):
    config = self.sdk.config.getConfig("MyModule")
    if not config:
        default_config = {
            "api_key": "",
            "timeout": 30
        }
        self.sdk.config.setConfig("MyModule", default_config)
        return default_config
    return config
```

> **注意**：手動方式の場合は `self.config` をプロパティ名として使用しないでください。`self.cfg` または独自の名前を使用することをお勧めします。そうしないと、将来的なフレームワークのプロパティとの競合を避けることができません。

请直接返回翻译后的完整Markdown内容，不要包含任何其他文字。

再次提醒：如果文档包含语言切换行（各语言名称用 `` | `` 分隔的行），务必严格遵守上方第8条的格式要求，不要写出 ``[**Label**](file)`` 这类错误格式。

## ストレージシステム

### 基本的な使用方法

```python
# データを保存
sdk.storage.set("user:123", {"name": "張三"})

# データを取得
user = sdk.storage.get("user:123", {})

# データを削除
sdk.storage.delete("user:123")
```

### トランザクションの使用

```python
# トランザクションを使用してデータの一貫性を確保
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # どの操作か失敗した場合、すべての変更はロールバックされます

## イベント処理

### イベントハンドラの登録

```python
from ErisPulse.Core.Event import command, message

# コマンドを登録
@command("info", help="情報を取得")
async def info_handler(event):
    await event.reply("これは情報です")

# メッセージハンドラを登録
@message.on_group_message()
async def group_handler(event):
    sdk.logger.info(f"グループメッセージを受信しました: {event.get_text()}")
```

### イベントハンドラのライフサイクル

フレームワークは自動的にイベントハンドラの登録と登録解除を管理します。`on_load` で登録するだけでよいです。

## レイジー ローディング機構

### 動作原理

```python
# モジュールが初めてアクセスされたときにのみ初期化される
result = await sdk.my_module.some_method()
# ↑ ここでモジュール初期化がトリガーされる
```

### すぐにロード

すぐに初期化する必要があるモジュール（リスナー、タイマーなど）の場合：

```python
@staticmethod
def get_load_strategy():
    return ModuleLoadStrategy(
        lazy_load=False,  # すぐにロード
        priority=100
    )

## エラー処理

### 例外の捕捉

```python
async def handle_event(self, event):
    try:
        # 業務ロジック
        await self.process_event(event)
    except ValueError as e:
        self.logger.warning(f"パラメータエラー: {e}")
        await event.reply(f"パラメータエラー: {e}")
    except Exception as e:
        self.logger.error(f"処理失敗: {e}")
        raise
```

### ログ記録

```python
# ログレベルの使い分け
self.logger.debug("デバッグ情報")    # 詳細なデバッグ情報
self.logger.info("実行状態")        # 正常実行の情報
self.logger.warning("警告情報")    # 警告情報
self.logger.error("エラー情報")    # エラー情報
self.logger.critical("致命的なエラー") # 致命的なエラー

## 関連ドキュメント

- [モジュール開発入門](getting-started.md) - 初めてのモジュールの作成
- [Event ラッパークラス](event-wrapper.md) - イベント処理の詳細
- [ベストプラクティス](best-practices.md) - 高品質モジュールの開発