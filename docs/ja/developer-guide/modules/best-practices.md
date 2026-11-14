# モジュール開発のベストプラクティス

> [!TIP]
> **この記事を読むタイミング**：最初のモジュールを書いた後に読むことを推奨します（エンジニアリングのベストプラクティス）。必要なければ飛ばしても、他の機能の使用に影響はありません。


ここでは、モジュール開発における工程的な書き方の約束事項をまとめます：非同期処理はイベントループをブロックしないこと、設定は宣言型にすること、他人のリソースを管理する場合はアンロード時に解放すること——これらを守れば、メモリリーク、バックグラウンドタスクの残留、ホットリロードの失敗といった、モジュール開発で最もよくある問題を回避できます。

## モジュール設計

### 1. 単一責任の原則

各モジュールは1つのコア機能だけを担当するべきです：

```python
# 良い設計：各モジュールは1つの機能だけを担当
class WeatherModule(BaseModule):
    """天気情報取得モジュール"""
    pass

class NewsModule(BaseModule):
    """ニュース情報取得モジュール"""
    pass

# 悪い設計：1つのモジュールが複数の無関係な機能を担当
class UtilityModule(BaseModule):
    """天気、ニュース、ジョークなど複数の機能を含む"""
    pass
```

### 2. モジュール命名規則

```toml
[project]
name = "ErisPulse-ModuleName"  # ErisPulse- で始まる名前
```

### 3. 明確な設定管理

宣言型の設定（`ConfigClass` + `BaseConfig`）を使用することを推奨します。これにより、型安全性、自動テンプレート生成、WebUIフォームサポートなどの機能が得られます：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_url: str = field(default="https://api.example.com", metadata={
        "description": {"i18n": "my_module.api_url", "default": "API アドレス"},
    })
    timeout: int = field(default=30, metadata={
        "description": {"i18n": "my_module.timeout", "default": "タイムアウト時間（秒）"},
    })
    cache_ttl: int = field(default=3600, metadata={
        "description": {"i18n": "my_module.cache_ttl", "default": "キャッシュの有効時間（秒）"},
    })

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def do_something(self):
        cfg = self.cfg  # 型安全、リアルタイム読み取り
        await self._fetch(cfg.api_url, timeout=cfg.timeout)
```

また、手動で設定ストレージを読み書きする方法も引き続き使用できます（[モジュールのコアコンセプト](core-concepts.md#設定管理)を参照）。

### 宣言型の翻訳キー（v2.7.0+）

モジュールは `I18nClass` を使って翻訳キーを一括で宣言し、フレームワークが自動的に i18n システムに登録します。`i18n.register()` を手動で呼び出す必要はありません。

```python
from ErisPulse.Core.Bases import BaseI18n, I18nKey

class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        # プレースホルダー付きの業務翻訳キー
        welcome: I18nKey = I18nKey(
            default="Welcome, {name}!",
            zh_CN="ようこそ、{name}！",
            zh_TW="ようこそ、{name}！",
            en="Welcome, {name}!",
            ja="ようこそ、{name}！",
            ru="Добро пожаловать, {name}!",
        )
        # 設定項目の説明の翻訳
        api_url: I18nKey = I18nKey(
            default="API URL",
            zh_CN="API アドレス",
            zh_TW="API 位址",
            en="API URL",
            ja="API URL",
            ru="API URL",
        )
```

詳細な使い方は [i18n ドキュメント](../../advanced/i18n.md#推奨書き方-i18nclass-を使って翻訳キーを宣言する-v270) を参照してください。

## 非同期プログラミング

### 1. 非同期ライブラリの使用

```python
# 推奨：SDK 内部の HTTP クライアント（非同期、自動ログと統計）
from ErisPulse.Core import client

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await client.get(url)
        return await resp.json()

# sdk.client でも同じ効果
from ErisPulse import sdk

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await sdk.client.get(url)
        return await resp.json()

# aiohttp を直接インポートしないこと（フレームワークの統一管理が難しくなる）
import aiohttp

class MyModule(BaseModule):
    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

# requests を使用しないこと（同期的で、イベントループをブロックする）
import requests

class MyModule(BaseModule):
    def fetch_data(self, url):
        return requests.get(url).json()  # イベントループをブロックする
```

### 2. 正しい非同期操作

```python
from ErisPulse.Core.Event import Event  # event: Event 注釈は強く推奨；カスタムメソッドの補完は epsdk types を参照

async def handle_command(self, event: Event):
    # 結果を待つ必要がある長時間処理：直接 await（ライフサイクルが明確）
    result = await self._long_operation()

async def on_load(self, event: dict):
    # バックグラウンドタスク（ポーリング/タイマー/fire-and-forget）：self.spawn() を使用
    # モジュールのアンロード時にフレームワークが on_unload 後にバックグラウンドタスクをキャンセルし、self への参照を保持しない
    self.spawn(self._poll())
```

> [!NOTE]
> バックグラウンドタスクは `self.spawn()` を推奨します（ErisPulse **2.8.0+**）。**2.8.3 以降**では、裸の `asyncio.create_task` も自動的にモジュールに所属します（Task Factory が自動的に登録され、アンロード時にバックグラウンドタスクをキャンセルし、`self` の参照を保持しません）；`self.spawn()` は非メインループスレッドからメインループにスケジュールするサポートや、明示的な `owner=` 指定が可能なため、引き続き推奨されます。**2.8.3 以前**では、裸のタスクは所属せず、`self` の参照を保持してモジュールインスタンスが回収されず（ホットリロードでリーク）、`self.spawn()` を使用する必要があります。詳細は [ライフサイクル管理](../../advanced/lifecycle.md#バックグラウンドタスクの所属と自動キャンセル) を参照してください。

### 3. リソース管理

```python
async def on_load(self, event):
    # SDK クライアントは接続プールを自動管理するため、session の手動作成は不要
    pass
    
async def on_unload(self, event):
    # 自前でクライアントを作成する場合は、リソースの解放を忘れずに
    pass
```

## イベント処理

### 1. Event パッケージクラスの使用

```python
from ErisPulse.Core.Event import Event
# Event パッケージクラスの便利なメソッドを使用
@command("info")
async def info_command(event: Event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"こんにちは、{nickname}！")

# ダイレクトに辞書をアクセスしないこと
@command("info")
async def info_command(event: Event):
    user_id = event["user_id"]  # 明確さに欠け、間違いやすい
```

### 2. 懒惰なロード（Lazy Load）の適切な使用

```python
# 低頻度コマンドモジュール：activate_on トリガーを宣言し、最初の一致するコマンドが到着した時点で自動的にアクティブ化（ロードを遅らせる）
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"command": {"name": "dice", "help": "サイコロを振る", "aliases": ["d"]}},
        ])

# 低頻度リスナー・モジュール：イベントトリガーを宣言し、イベントが到着した時点で自動的にアクティブ化
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"notice": "group_member_increase"},
        ])

# 高頻度（メッセージごとに処理する）または起動時に即座に準備が必要なモジュール：即時ロード
class HotListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# ユーティリティ・モジュールは lazy load が適しています
class UtilityModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True)
```

> `activate_on` の完全な構文（イベントの3形式 / コマンドの簡略化と dict 声明 / help のフォールバックチェーン）は [Lazy Load モジュールシステム](../../advanced/lazy-loading.md#イベント駆動のlazy-activateactivate_on) を参照してください。

### 3. イベントハンドラの登録

```python
from ErisPulse.Core.Event import Event
async def on_load(self, event):
    # on_load でイベントハンドラを登録
    @command("hello")
    async def hello_handler(event: Event):
        await event.reply("こんにちは！")
    
    @message.on_group_message()
    async def group_handler(event: Event):
        self.logger.info("グループメッセージを受信しました")
    
    # 手動で登録解除は不要、フレームワークが自動的に処理します
```

## ユーティリティ・モジュール：他人のリソースを管理するときはアンロード通知を受け止める

**いつ必要になるか**：あなたのモジュールが他のモジュールのリソース（タイマー、サブスクライバー、接続、キャッシュエントリなど）を管理している場合。これらのリファレンスが、相手のモジュールがアンロードされた後も削除されない場合、相手のインスタンスは永遠に回収されません——これはユーティリティ・モジュールで最もよくあるメモリリークの原因です。

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.runtime import off_cleanup, on_cleanup

class MyToolModule(BaseModule):
    def __init__(self):
        self._entries = {}  # {モジュール名: 管理するもの}

    def register(self, entry):
        owner = on_cleanup(self._drop)   # ① 登録時にクリーンアップチェーンに登録し、呼び出し元を自動的に識別
        self._entries.setdefault(owner, []).append(entry)

    def _drop(self, owner: str):
        self._entries.pop(owner, None)   # ② 相手がアンロードされたときにフレームワークが自動的に呼び出す：そのリソースを破棄

    async def on_unload(self, event):
        off_cleanup(self._drop)          # ③ 自分がアンロードされる前にハンドラを解除
```

これで、フレームワークが保証します：

- 相手のモジュールが**アンロード / 禁用**（またはアダプターが閉じる）されたときに、`_drop("相手のモジュール名")` は必ず呼び出されます
- **呼び出し元の識別は自動的**：相手が `on_load` で `sdk.MyToolModule.register(...)` を直接呼び出すか、`sdk.module.call("MyToolModule", "register", ...)` を経由して呼び出すかに関わらず、正しく識別されます
- 時間の管理は不要——ハンドラはフレームワークのクリーンアップチェーン内で呼び出され、リーク診断よりも早く、誤報が発生しません

接続しない場合の結果：相手が `purge` で完全にアンロードされたときにインスタンスが回収されない（リーク診断で「回収不可」と表示される）；もし相手自身が `on_unload` で自分に登録を解除しない場合、リークは永久的になります。

**他人のリソースを管理しない通常のモジュールは、この点を気にする必要はありません**——フレームワークが管理するリソース（コマンド / ハンドラ / ルーティング / バックグラウンドタスクなど）のアンロード時のクリーンアップは自動的です。

> 触発タイミング、呼び出し元識別ルール、タイムアウトとフォールトトレランスなどの詳細は [所有権システム・ユーティリティ・モジュールガイド](../../advanced/ownership.md#ユーティリティ・モジュールガイド他人のモジュールのハンドルを管理する) を参照してください。

## エラー処理

### 1. エラーの分類処理

```python
from ErisPulse.Core.Event import Event
from ErisPulse.Core.Bases.errors import ClientError

async def handle_event(self, event: Event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # 予期された業務エラー
        self.logger.warning(f"業務警告: {e}")
        await event.reply(f"パラメータエラー: {e}")
    except ClientError as e:
        # ネットワークエラー（sdk.client の下層 aiohttp エラーは自動的に変換）
        self.logger.error(f"ネットワークエラー {e.method} {e.url}: {e}")
        await event.reply("ネットワークリクエストに失敗しました。後で再度お試しください。")
    except Exception as e:
        # 予期しないエラー
        self.logger.error(f"不明なエラー: {e}", exc_info=True)
        await event.reply("処理に失敗しました。管理者にお問い合わせください。")
        raise
```

### 2. タイムアウト処理

```python
# 推奨：SDK 内部のクライアントを使用（タイムアウトとリトライが自動で付与）
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import ClientTimeoutError

async def fetch_with_timeout(self, url, timeout=30):
    try:
        resp = await client.get(url, timeout=timeout)
        return await resp.json()
    except ClientTimeoutError:
        self.logger.warning(f"リクエストがタイムアウトしました: {url}")
        raise
```

## ストレージ・システム

### 1. トランザクションの使用

```python
# トランザクションを使用してデータの一貫性を確保
async def update_user(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])

# ❌ トランザクションを使わないとデータの一貫性が保てない
async def update_user(self, user_id, data):
    self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
    # ここでエラーが発生すると、上記の設定はロールバックできない
    self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
```

### 2. バッチ操作

```python
# バッチ操作を使用してパフォーマンスを向上
def cache_multiple_items(self, items):
    self.sdk.storage.set_multi({
        f"item:{k}": v for k, v in items.items()
    })

# ❌ 複数回の呼び出しは効率が悪い
def cache_multiple_items(self, items):
    for k, v in items.items():
        self.sdk.storage.set(f"item:{k}", v)
```

## ログ記録

### 1. ログレベルの適切な使用

```python
# DEBUG: 詳細なデバッグ情報（開発時のみ）
self.logger.debug(f"入力パラメータ: {params}")

# INFO: 正常な実行情報
self.logger.info("モジュールがロードされました")
self.logger.info(f"リクエストを処理しました: {request_id}")

# WARNING: 警告情報、主な機能に影響しない
self.logger.warning(f"設定項目 {key} が設定されていません。デフォルト値を使用します。")
self.logger.warning("APIの応答が遅いです。最適化が必要かもしれません。")

# ERROR: エラー情報
self.logger.error(f"APIリクエストに失敗しました: {e}")
self.logger.error(f"イベント処理に失敗しました: {e}", exc_info=True)

# CRITICAL: 致命的なエラー、即時対応が必要
self.logger.critical("データベース接続に失敗しました。ロボットは正常に動作できません。")
```

### 2. 構造化ログ

```python
# 構造化ログを使用して、解析しやすくする
self.logger.info(f"リクエストを処理しました: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ 非構造化ログの使用
self.logger.info(f"リクエストを処理しました。ユーザー {user_id} から、{duration} ミリ秒かかりました。")
```

## パフォーマンス最適化

### 1. キャッシュの使用

```python
class MyModule(BaseModule):
    def __init__(self):
        self._cache = {}
        self._cache_lock = asyncio.Lock()
    
    async def get_data(self, key):
        async with self._cache_lock:
            if key in self._cache:
                return self._cache[key]
            
            # データベースから取得
            data = await self._fetch_from_db(key)
            
            # キャッシュ
            self._cache[key] = data
            return data
```

### 2. ブロッキング操作の回避

```python
from ErisPulse.Core.Event import Event
# 非同期操作を使用
async def process_message(self, event: Event):
    # 非同期で処理
    await self._async_process(event)

# ❌ ブロッキング操作
async def process_message(self, event: Event):
    # 同期操作でイベントループをブロック
    result = self._sync_process(event)
```

## セキュリティ

### 1. 敏感データの保護

```python
# 敏感データは設定に保存（宣言型 ConfigClass、secret フィールドはログやエクスポートに含まれない）
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseModule, BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_key: str = field(
        default="",
        metadata={"description": "API キー", "secret": True},
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    def check_api_key(self):
        if not self.cfg.api_key or self.cfg.api_key == "YOUR_API_KEY_HERE":
            raise ValueError("config.toml に有効な API キーを設定してください")

# ❌ 敏感データのハードコード
class MyModule(BaseModule):
    API_KEY = "sk-1234567890"  # これを行わないでください！
```

### 2. 入力の検証

```python
from ErisPulse.Core.Event import Event
# ユーザー入力の検証
async def process_command(self, event: Event):
    user_input = event.get_text()
    
    # 入力長の検証
    if len(user_input) > 1000:
        await event.reply("入力が長すぎます。再度入力してください。")
        return
    
    # 入力形式の検証
    if not re.match(r'^[a-zA-Z0-9]+$', user_input):
        await event.reply("入力形式が正しくありません。")
        return
```

## テスト

### 1. 単体テスト

```python
import pytest
from ErisPulse.Core.Bases import BaseModule

class TestMyModule:
    def test_config_defaults(self):
        """設定のデフォルト値をテスト"""
        config = MyModule.ConfigClass()
        assert config.timeout == 30
```

### 2. 統合テスト

```python
@pytest.mark.asyncio
async def test_command_handling():
    """コマンド処理をテスト"""
    module = MyModule()
    await module.on_load({})
    
    # コマンドイベントをシミュレート
    event = create_test_command_event("hello")
    await module.handle_command(event)
```

## HTTP ルーティングのライフサイクル

モジュールが `router` で登録した HTTP/WebSocket ルーティングは、フレームワークによって**所有権の原則**に基づいてライフサイクルが自動管理されます：

- 登録時のネームスペースが所有権の識別子です。**リロード / アンロード時にフレームワークは自動的にその所有権以下のすべてのルーティングと接続リソースをクリーンアップ**し、手動での登録解除は不要です。
- したがって、**`on_load` では必ずルーティングを再登録する必要があります**。インスタンスレベルのブール値フラグを使って「一度だけ登録する」ような最適化は行わないでください：設定のホットリロードは stop/start をトリガーし、**同一インスタンスを再利用するため、フラグが保持されるとルーティングがクリーンアップ後に** **永久的に失われ、エンドポイントが 404 になり、プロセスを再起動しないと復帰しません**

```python
class MyModule(BaseModule):
    async def on_load(self):
        # 毎回ロード時に必ず再登録
        router.register_http_route("MyModule", "/api/panel", self._panel, methods=["GET"])
```

ルーティングを事前に手動でアンロードしたい場合（動的にエントリをオフラインにするなど）は、明示的に登録解除できます：

```python
from ErisPulse.Core import router

router.unregister_http_route("MyModule", "/api/panel")
```

- ホットリロードの間、クライアント側は一時的にルーティングが 404 になる可能性がありますが、これは一時的な現象です。ブラウザ向けのインタラクティブページでは、404 に対して有限回の自動リトライを実装することを推奨します。

## 部署

### 1. バージョン管理

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
```

セマンティックバージョニングに従います：
- MAJOR.MINOR.PATCH
- 主バージョン：互換性のない API 変更
- 次バージョン：互換性のある機能追加
- リビジョン番号：互換性のあるバグ修正

### 2. README ヘッダー

`epsdk create` で生成された README には、ErisPulse のヘッダー（ロゴ + バッジ行）が既に含まれています。2 つの推奨モードがあります：

**モード A — ErisPulse ロゴのみ（デフォルト）：**

```markdown
<div align="center">

<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" width="180" alt="MyModule" />

# MyModule

**1行で説明**

<p>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/pypi/v/ErisPulse-MyModule?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/Powered_by-ErisPulse-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="ErisPulse"></a>
</p>

</div>
```

**モード B — モジュールアイコン × ErisPulse ロゴ（独自アイコンがある場合）：**

```markdown
<div align="center">

<img src=".github/assets/MyModuleIcon.svg" width="120" alt="MyModule" />
<span style="font-size:44px;color:#c8c8c8;margin:0 18px;vertical-align:middle;">×</span>
<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" height="120" alt="ErisPulse" />

# MyModule
（バッジ行は上と同じ）
</div>
```

必要に応じて、GitHub スター数やダウンロード数などのバッジを追加できます。ロゴはプロジェクトにダウンロードして、相対パスで参照することもできます（`.github/assets/ErisPulseLogo.png`）。

## 関連ドキュメント

### 学習パスに戻る

- [モジュール開発入門](getting-started.md) - 最初のモジュールを作成する
- [モジュールのコアコンセプト](core-concepts.md) - モジュールのアーキテクチャを理解する

### シナリオ別に深く学ぶ

- [Event パッケージクラス](event-wrapper.md) - イベント処理の詳細
- [公開とモジュールストアガイド](../publishing.md) - モジュールを PyPI とモジュールストアに公開する方法