# モジュール開発ベストプラクティス

> [!TIP]
> **いつこのドキュメントを読むべきか**：最初のモジュールを書き終えた後に読むことを推奨（エンジニアリングのベストプラクティス）。必要なければスキップしても、他の機能の利用には影響しません。


ここでは、モジュール開発におけるエンジニアリング上の作法をまとめています：非同期操作はイベントループをブロックしない、設定は宣言的に、他のモジュールのリソースを管理する場合はアンロード時に解放する——これに従って書けば、メモリリーク、バックグラウンドタスクの残存、ホットリロードの失効といったモジュール開発で最もよくある落とし穴を回避できます。

## モジュール設計

### 1. 単一責任の原則

各モジュールは1つのコア機能のみを担当すべきです：

```python
# 良い設計：各モジュールは1つの機能のみを担当
class WeatherModule(BaseModule):
    """天気照会モジュール"""
    pass

class NewsModule(BaseModule):
    """ニュース照会モジュール"""
    pass

# 悪い設計：1つのモジュールが複数の無関係な機能を担当
class UtilityModule(BaseModule):
    """天気、ニュース、ジョークなど複数の機能を含む"""
    pass
```

### 2. モジュール命名規則

```toml
[project]
name = "ErisPulse-ModuleName"  # ErisPulse- プレフィックスを使用
```

### 3. 明確な設定管理

宣言的設定（`ConfigClass` + `BaseConfig`）の使用を推奨します。型安全性、自動テンプレート生成、WebUI フォーム対応などの機能が得られます：

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
        "description": {"i18n": "my_module.cache_ttl", "default": "キャッシュ生存時間（秒）"},
    })

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def do_something(self):
        cfg = self.cfg  # 型安全、リアルタイム読み取り
        await self._fetch(cfg.api_url, timeout=cfg.timeout)
```

手動方式で設定ストレージの読み書きを行うことも引き続き可能です（[モジュールのコア概念](core-concepts.md#設定管理)を参照）。

### 宣言的翻訳キー（v2.7.0+）

モジュールは `I18nClass` を通じて翻訳キーを一元的に宣言でき、フレームワークが自動的に i18n システムへ登録するため、手動で `i18n.register()` を呼び出す必要はありません。

```python
from ErisPulse.Core.Bases import BaseI18n, I18nKey

class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        # プレースホルダー付きのビジネス翻訳キー
        welcome: I18nKey = I18nKey(
            default="Welcome, {name}!",
            zh_CN="欢迎你，{name}！",
            zh_TW="歡迎你，{name}！",
            en="Welcome, {name}!",
            ja="ようこそ、{name}！",
            ru="Добро пожаловать, {name}!",
        )
        # 設定フィールド説明の翻訳
        api_url: I18nKey = I18nKey(
            default="API URL",
            zh_CN="API 地址",
            zh_TW="API 位址",
            en="API URL",
            ja="API URL",
            ru="API URL",
        )
```

詳細な使い方は [i18n ドキュメント](../../advanced/i18n.md#推奨される書き方i18nclass-による翻訳キーの宣言v270) を参照してください。

## 非同期プログラミング

### 1. 非同期ライブラリの使用

```python
# SDK 組み込み HTTP クライアントの使用を推奨（非同期、ログと統計を自動取得）
from ErisPulse.Core import client

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await client.get(url)
        return await resp.json()

# sdk.client 経由でも使用可能（効果は同じ）
from ErisPulse import sdk

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await sdk.client.get(url)
        return await resp.json()

# aiohttp を直接インポートしない（フレームワークによる一元管理ができない）
import aiohttp

class MyModule(BaseModule):
    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

# requests は使用しない（同期のためイベントループをブロックする）
import requests

class MyModule(BaseModule):
    def fetch_data(self, url):
        return requests.get(url).json()  # イベントループをブロックする
```

### 2. 正しい非同期操作

```python
from ErisPulse.Core.Event import Event  # event: Event アノテーションで IDE 補完が得られる

async def handle_command(self, event: Event):
    # 結果を待つ必要のある時間のかかる操作：直接 await（ライフサイクルが明確）
    result = await self._long_operation()

async def on_load(self, event: dict):
    # バックグラウンドタスク（ポーリング/タイマー/fire-and-forget）：self.spawn() を使用。
    # モジュールのアンロード時、フレームワークが on_unload の後にフォールバックでキャンセルするため、
    # self を保持することによるリークを回避できる
    self.spawn(self._poll())
```

> [!NOTE]
> バックグラウンドタスクには `self.spawn()` を推奨します（ErisPulse **2.8.0+**）。**2.8.3 以降**は、素の `asyncio.create_task`
> も自動的にモジュールへ暗黙的に帰属します（Task Factory が自動登録し、アンロード時にフォールバックでキャンセル、`self` 参照はリークしなくなります）。
> `self.spawn()` が引き続き推奨の書き方です——非メインループのスレッドからメインループへのスケジューリングや、明示的な `owner=` 指定をサポートします。
> **2.8.3 より前**のバージョンでは、素のタスクは帰属せず `self` 参照を保持し続けるためモジュールインスタンスが回収できなくなり
> （ホットリロード時のリーク）、`self.spawn()` を使う必要があります。詳細は [ライフサイクル管理](../../advanced/lifecycle.md#バックグラウンドタスクの帰属と自動キャンセル) を参照。

### 3. リソース管理

```python
async def on_load(self, event):
    # SDK クライアントは接続プールを自動管理するため、手動で session を作成する必要なし
    pass
    
async def on_unload(self, event):
    # カスタムクライアントが必要な場合は、リソースのクリーンアップを忘れずに
    pass
```

## イベント処理

### 1. Event ラッパークラスの使用

```python
# Event ラッパークラスの便利メソッドを使用
@command("info")
async def info_command(event: Event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"こんにちは、{nickname}！")

# 辞書へ直接アクセスするのではなく
@command("info")
async def info_command(event: Event):
    user_id = event["user_id"]  # わかりにくく、間違いやすい
```

### 2. 遅延ロードの適切な使用

```python
# 低頻度コマンドモジュール：activate_on トリガーを宣言し、最初に一致するコマンドが到着した時点で自動アクティブ化（遅延ロードを維持）
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"command": {"name": "dice", "help": "サイコロを1つ振る", "aliases": ["d"]}},
        ])

# 低頻度リスナーモジュール：イベントトリガーを宣言し、イベント到着時に自動アクティブ化
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"notice": "group_member_increase"},
        ])

# 高頻度トリガー（すべてのメッセージを処理する必要がある）や起動時に即時準備が必要なモジュール：即時ロード
class HotListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# ユーティリティモジュールは遅延ロードが適している
class UtilityModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True)
```

> `activate_on` の完全な構文（イベントの3形式 / コマンド略記と dict 宣言 / help フォールバックチェーン）については
> [遅延ロードモジュールシステム](../../advanced/lazy-loading.md#イベント駆動の遅延アクティベーションactivate_on) を参照してください。

### 3. イベントハンドラーの登録

```python
async def on_load(self, event):
    # on_load 内でイベントハンドラーを登録
    @command("hello")
    async def hello_handler(event: Event):
        await event.reply("こんにちは！")
    
    @message.on_group_message()
    async def group_handler(event: Event):
        self.logger.info("グループメッセージを受信しました")
    
    # 手動で登録解除する必要はなく、フレームワークが自動的に処理する
```

## ユーティリティモジュール：他のモジュールのものを預かる時は「アンロード通知」を受け止める

**いつ必要か**：あなたのモジュールが他のモジュールの代わりにものを管理している場合（タイマーコールバック、サブスクライバー、接続、キャッシュエントリなど）。これらの参照を、相手モジュールのアンロード後も捨てずに保持し続けると、相手のインスタンスは永遠に回収されません——これがユーティリティモジュールで最もよくあるメモリリークの原因です。

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.runtime import off_cleanup, on_cleanup

class MyToolModule(BaseModule):
    def __init__(self):
        self._entries = {}  # {モジュール名: 管理しているもの}

    def register(self, entry):
        owner = on_cleanup(self._drop)   # ① 登録時にクリーンアップチェーンへ登録し、呼び出し元を自動識別
        self._entries.setdefault(owner, []).append(entry)

    def _drop(self, owner: str):
        self._entries.pop(owner, None)   # ② 相手のアンロード時にフレームワークが自動呼び出し：相手のものを破棄

    async def on_unload(self, event):
        off_cleanup(self._drop)          # ③ 自身のアンロード前にフックを解除
```

たったこれだけで、フレームワークが保証します：

- 相手モジュールが**アンロード / 無効化**される（またはアダプターが終了する）とき、`_drop("相手モジュール名")` が必ず呼び出される
- **呼び出し元の識別は全自動**：相手が `on_load` 内で直接 `sdk.MyToolModule.register(...)` を呼び出しても、`sdk.module.call("MyToolModule", "register", ...)` 経由で呼び出しても、誰が呼び出したのかを正しく識別できる
- タイミングを気にする必要なし——フックはフレームワークのクリーンアップチェーン内でトリガーされ、リーク診断より前に実行されるため、誤検出されない

組み込まない場合の結果：相手が `purge` で完全アンロードされるときにインスタンスを回収できず（リーク診断が「回収不可」と報告）、相手自身も `on_unload` 内であなたへの登録解除を行わなければ、リークは恒久的なものになります。

**通常のモジュール（他のモジュールのものを管理しない）はこれを気にする必要ありません**——フレームワークリソース（コマンド / ハンドラー / ルート / バックグラウンドタスクなど）のアンロード時のクリーンアップは全自動です。

> トリガータイミング、呼び出し元識別ルール、タイムアウトとフォールトトレランスなどの詳細は
> [所有権システム · ユーティリティモジュールガイド](../../advanced/ownership.md#ユーティリティモジュールガイド他のモジュールのハンドルを管理する) を参照してください。

## エラー処理

### 1. 例外の分類処理

```python
from ErisPulse.Core.Bases.errors import ClientError

async def handle_event(self, event: Event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # 予期されるビジネスエラー
        self.logger.warning(f"ビジネス警告: {e}")
        await event.reply(f"パラメータエラー: {e}")
    except ClientError as e:
        # ネットワークエラー（sdk.client の基盤となる aiohttp 例外は自動変換済み）
        self.logger.error(f"ネットワークエラー {e.method} {e.url}: {e}")
        await event.reply("ネットワークリクエストに失敗しました。しばらくしてから再試行してください")
    except Exception as e:
        # 予期しないエラー
        self.logger.error(f"不明なエラー: {e}", exc_info=True)
        await event.reply("処理に失敗しました。管理者に連絡してください")
        raise
```

### 2. タイムアウト処理

```python
# SDK 組み込みクライアントの使用を推奨（タイムアウトとリトライを内蔵）
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import ClientTimeoutError

async def fetch_with_timeout(self, url, timeout=30):
    try:
        resp = await client.get(url, timeout=timeout)
        return await resp.json()
    except ClientTimeoutError:
        self.logger.warning(f"リクエストタイムアウト: {url}")
        raise
```

## ストレージシステム

### 1. トランザクションの使用

```python
# トランザクションを使用してデータの一貫性を確保
async def update_user(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])

# ❌ トランザクションを使わないとデータ不整合が起こる可能性
async def update_user(self, user_id, data):
    self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
    # ここでエラーが発生すると、上の設定はロールバックできない
    self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
```

### 2. バッチ操作

```python
# バッチ操作でパフォーマンスを向上
def cache_multiple_items(self, items):
    self.sdk.storage.set_multi({
        f"item:{k}": v for k, v in items.items()
    })

# ❌ 何度も呼び出すと効率が悪い
def cache_multiple_items(self, items):
    for k, v in items.items():
        self.sdk.storage.set(f"item:{k}", v)
```

## ロギング

### 1. ログレベルの適切な使用

```python
# DEBUG: 詳細なデバッグ情報（開発時のみ）
self.logger.debug(f"入力パラメータ: {params}")

# INFO: 正常動作の情報
self.logger.info("モジュールがロードされました")
self.logger.info(f"リクエストを処理中: {request_id}")

# WARNING: 警告情報、主要機能には影響しない
self.logger.warning(f"設定項目 {key} が未設定のため、デフォルト値を使用します")
self.logger.warning("API の応答が遅く、最適化が必要な可能性があります")

# ERROR: エラー情報
self.logger.error(f"API リクエスト失敗: {e}")
self.logger.error(f"イベント処理失敗: {e}", exc_info=True)

# CRITICAL: 致命的エラー、即時対応が必要
self.logger.critical("データベース接続に失敗し、ボットが正常に動作できません")
```

### 2. 構造化ログ

```python
# 構造化ログを使用すると解析しやすい
self.logger.info(f"リクエスト処理: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ 非構造化ログを使用
self.logger.info(f"ユーザー {user_id} からのリクエストを処理しました。所要時間 {duration} ミリ秒")
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
            
            # データをキャッシュ
            self._cache[key] = data
            return data
```

### 2. ブロッキング操作の回避

```python
# 非同期操作を使用
async def process_message(self, event: Event):
    # 非同期処理
    await self._async_process(event)

# ❌ ブロッキング操作
async def process_message(self, event: Event):
    # 同期操作、イベントループをブロックする
    result = self._sync_process(event)
```

## セキュリティ

### 1. 機密データの保護

```python
# 機密データは設定に保存（宣言的 ConfigClass、secret フィールドはログ/エクスポートに入らない）
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
            raise ValueError("config.toml で有効な API キーを設定してください")

# ❌ 機密データのハードコード
class MyModule(BaseModule):
    API_KEY = "sk-1234567890"  # こんなことをしてはいけない！
```

### 2. 入力検証

```python
# ユーザー入力を検証
async def process_command(self, event: Event):
    user_input = event.get_text()
    
    # 入力長を検証
    if len(user_input) > 1000:
        await event.reply("入力が長すぎます。入力し直してください")
        return
    
    # 入力形式を検証
    if not re.match(r'^[a-zA-Z0-9]+$', user_input):
        await event.reply("入力形式が正しくありません")
        return
```

## テスト

### 1. ユニットテスト

```python
import pytest
from ErisPulse.Core.Bases import BaseModule

class TestMyModule:
    def test_config_defaults(self):
        """設定のデフォルト値をテスト"""
        config = MyModule.ConfigClass()
        assert config.timeout == 30
```

### 2. 結合テスト

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

## デプロイ

### 1. バージョン管理

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
```

セマンティックバージョニングに従う：
- MAJOR.MINOR.PATCH
- メジャーバージョン：互換性のない API 変更
- マイナーバージョン：後方互換のある機能追加
- パッチバージョン：後方互換のある問題修正

### 2. README ヘッダー

`epsdk create` が生成する README には ErisPulse ヘッダー識別（ロゴ + バッジ行）が組み込まれています。推奨される2つのパターン：

**パターン A — ErisPulse ロゴのみ（デフォルト）：**

```markdown
<div align="center">

<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" width="180" alt="MyModule" />

# MyModule

**一言説明**

<p>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/pypi/v/ErisPulse-MyModule?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/Powered_by-ErisPulse-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="ErisPulse"></a>
</p>

</div>
```

**パターン B — モジュールアイコン × ErisPulse ロゴ（カスタムアイコンがある場合）：**

```markdown
<div align="center">

<img src=".github/assets/MyModuleIcon.svg" width="120" alt="MyModule" />
<span style="font-size:44px;color:#c8c8c8;margin:0 18px;vertical-align:middle;">×</span>
<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" height="120" alt="ErisPulse" />

# MyModule
（バッジ行は上に同じ）
</div>
```

必要に応じて GitHub Stars、Downloads などのバッジを追加できます。ロゴをプロジェクトのローカル（`.github/assets/ErisPulseLogo.png`）にダウンロードして、相対パス参照に変更することもできます。

## 関連ドキュメント

### 学習パスに戻る

- [モジュール開発入門](getting-started.md) - 最初のモジュールを作成する
- [モジュールのコア概念](core-concepts.md) - モジュールアーキテクチャを理解する

### シナリオ別に詳しく

- [Event ラッパークラス](event-wrapper.md) - イベント処理の詳細
- [公開とモジュールストアガイド](../publishing.md) - モジュールを書いた後に PyPI とモジュールストアへ公開する