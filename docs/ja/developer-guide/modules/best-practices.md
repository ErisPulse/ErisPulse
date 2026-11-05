# モジュール開発ベストプラクティス

> [!TIP]
> **このドキュメントを読むべきタイミング**：最初のモジュールを書き終えた後に読むことを推奨します（エンジニアリングのベストプラクティス）。必要なければスキップしても、他の機能の利用には影響しません。


ここでは、モジュール開発における実装規約をまとめています：非同期操作でイベントループをブロックしない、設定は宣言的に行う、他のモジュールのリソースを預かる場合はアンロード時に解放する——これに従って書けば、メモリリーク、バックグラウンドタスクの残留、ホットリロードの失効といったモジュール開発で最もよくある落とし穴を避けられます。

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

### 2. モジュールの命名規則

```toml
[project]
name = "ErisPulse-ModuleName"  # ErisPulse- プレフィックスを使用
```

### 3. 明確な設定管理

宣言的設定（`ConfigClass` + `BaseConfig`）の使用を推奨します。型安全性、テンプレート自動生成、WebUI フォームサポートなどの機能が得られます：

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
        "description": {"i18n": "my_module.cache_ttl", "default": "キャッシュ有効期間（秒）"},
    })

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def do_something(self):
        cfg = self.cfg  # 型安全、リアルタイム読み取り
        await self._fetch(cfg.api_url, timeout=cfg.timeout)
```

従来どおり手動方式で設定ストレージを読み書きすることも可能です（[モジュールのコア概念](core-concepts.md#設定管理)を参照）。

### 宣言的な翻訳キー（v2.7.0+）

モジュールは `I18nClass` を通じて翻訳キーを一元宣言でき、フレームワークが自動的に i18n システムへ登録するため、手動で `i18n.register()` を呼び出す必要はありません。

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

詳細な使い方は [i18n ドキュメント](../../advanced/i18n.md#推奨される書き方i18nclass-で翻訳キーを宣言するv270)を参照してください。

## 非同期プログラミング

### 1. 非同期ライブラリを使用する

```python
# SDK 組み込み HTTP クライアントの使用を推奨（非同期、ログと統計が自動）
from ErisPulse.Core import client

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await client.get(url)
        return await resp.json()

# sdk.client 経由でも使用可能（同じ効果）
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

# requests を使用しない（同期処理のためイベントループをブロックする）
import requests

class MyModule(BaseModule):
    def fetch_data(self, url):
        return requests.get(url).json()  # イベントループをブロックする
```

### 2. 正しい非同期処理

```python
from ErisPulse.Core.Event import Event  # event: Event のアノテーションで IDE 補完が効く

async def handle_command(self, event: Event):
    # 結果を待つ必要がある時間のかかる操作：直接 await（ライフサイクルが明確）
    result = await self._long_operation()

async def on_load(self, event: dict):
    # バックグラウンドタスク（ポーリング/タイマー/fire-and-forget）：self.spawn() を使用。
    # モジュールのアンロード時、フレームワークが on_unload の後に最終的にキャンセルするため、
    # self を保持し続けることによるリークを防げる
    self.spawn(self._poll())
```

> [!NOTE]
> バックグラウンドタスクには `self.spawn()` を推奨します（ErisPulse **2.8.0+**）。**2.8.3 以降**は裸の `asyncio.create_task`
> も自動的にモジュールへ暗黙帰属します（Task Factory が自動登録し、アンロード時に最終的にキャンセルするため、`self` 参照はリークしません）。
> `self.spawn()` が依然として推奨される書き方です——メインループ以外のスレッドからメインループへのスケジューリングや、明示的な `owner=` 指定をサポートします。
> **2.8.3 未満**のバージョンでは、裸のタスクは帰属せず `self` 参照を保持し続けるため、モジュールインスタンスが回収されなくなります
> （ホットリロード時のリーク）。必ず `self.spawn()` を使用してください。詳細は[ライフサイクル管理](../../advanced/lifecycle.md#バックグラウンドタスクの帰属と自動キャンセル)を参照してください。

### 3. リソース管理

```python
async def on_load(self, event):
    # SDK クライアントは接続プールを自動管理するため、session を手動で作成する必要はない
    pass
    
async def on_unload(self, event):
    # カスタムクライアントを使用する場合は、リソースのクリーンアップを忘れずに
    pass
```

## イベント処理

### 1. Event ラッパークラスを使用する

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
    user_id = event["user_id"]  # わかりにくく、ミスしやすい
```

### 2. 遅延ロードの適切な活用

```python
# 低頻度コマンドモジュール：activate_on トリガーを宣言し、最初に一致するコマンドが到着した時点で自動アクティベート（遅延ロードを維持）
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"command": {"name": "dice", "help": "サイコロを1つ振る", "aliases": ["d"]}},
        ])

# 低頻度リスナーモジュール：イベントトリガーを宣言し、イベント到着時に自動アクティベート
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"notice": "group_member_increase"},
        ])

# 高頻度トリガー（すべてのメッセージの処理が必要）や起動時に即時準備が必要なモジュール：即時ロード
class HotListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# ユーティリティモジュールは遅延ロードに適している
class UtilityModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True)
```

> `activate_on` の完全な構文（イベントの3形式 / コマンド省略記法と dict 宣言 / help フォールバックチェーン）については、
> [遅延ロードモジュールシステム](../../advanced/lazy-loading.md#イベント駆動の遅延アクティベーションactivate_on)を参照してください。

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

## ユーティリティモジュール：他モジュールのものを預かるときは「アンロード通知」を受け止める

**いつ必要か**：あなたのモジュールが他のモジュールの代わりに何かを保持している場合（タイマーコールバック、サブスクライバー、接続、キャッシュエントリなど）。これらの参照は、相手のモジュールがアンロードされた後も破棄しないままだと、相手のインスタンスは永遠に回収されません——これがユーティリティモジュールで最もよくあるメモリリークの発生源です。

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.runtime import off_cleanup, on_cleanup

class MyToolModule(BaseModule):
    def __init__(self):
        self._entries = {}  # {モジュール名: 預かっているもの}

    def register(self, entry):
        owner = on_cleanup(self._drop)   # ① 登録時にクリーンアップチェーンへ登録し、呼び出し元を自動識別
        self._entries.setdefault(owner, []).append(entry)

    def _drop(self, owner: str):
        self._entries.pop(owner, None)   # ② 相手のアンロード時にフレームワークが自動呼び出し：その持ち物を破棄

    async def on_unload(self, event):
        off_cleanup(self._drop)          # ③ 自身のアンロード前にフックを解除
```

以上だけです。フレームワークは次を保証します：

- 相手モジュールが**アンロード / 無効化**されたとき（またはアダプターがシャットダウンされたとき）に、`_drop("相手モジュール名")` が必ず呼び出される
- **呼び出し元の識別は完全自動**：相手が `on_load` 内で直接 `sdk.MyToolModule.register(...)` を呼び出しても、`sdk.module.call("MyToolModule", "register", ...)` 経由で呼び出しても、誰による呼び出しかを正しく識別できる
- タイミングを気にする必要はない——フックはフレームワークのクリーンアップチェーン内でトリガーされ、リーク診断より先に実行されるため、誤検出はない

対応しなかった場合の結果：相手が `purge` で完全アンロードされるときにインスタンスを回収できなくなります（リーク診断が「回収不可」と報告）。さらに相手自身も `on_unload` 内であなたへの登録解除を行わない場合、リークは永続的になります。

**通常のモジュール（他のモジュールのものを預からない）はこれを気にする必要がありません**——フレームワークリソース（コマンド / ハンドラー / ルート / バックグラウンドタスクなど）のアンロード時のクリーンアップは完全自動です。

> トリガータイミング、呼び出し元識別ルール、タイムアウトとフォールトトレランスなどの詳細は、
> [所有権システム · ユーティリティモジュールガイド](../../advanced/ownership.md#ユーティリティモジュールガイド他のモジュールのハンドル)を参照してください。

## エラー処理

### 1. 例外の分類処理

```python
from ErisPulse.Core.Bases.errors import ClientError

async def handle_event(self, event: Event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # 予期されたビジネスエラー
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
        self.logger.warning(f"リクエストがタイムアウトしました: {url}")
        raise
```

## ストレージシステム

### 1. トランザクションを使用する

```python
# トランザクションを使用してデータの一貫性を確保
async def update_user(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])

# ❌ トランザクションを使用しないとデータの不整合が発生する可能性がある
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

# ❌ 複数回の呼び出しは効率が低い
def cache_multiple_items(self, items):
    for k, v in items.items():
        self.sdk.storage.set(f"item:{k}", v)
```

## ロギング

### 1. ログレベルの適切な使用

```python
# DEBUG: 詳細なデバッグ情報（開発時のみ）
self.logger.debug(f"入力パラメータ: {params}")

# INFO: 通常の実行情報
self.logger.info("モジュールがロードされました")
self.logger.info(f"リクエストを処理: {request_id}")

# WARNING: 警告情報、主要機能には影響しない
self.logger.warning(f"設定項目 {key} が設定されていないため、デフォルト値を使用します")
self.logger.warning("API の応答が遅く、最適化が必要な可能性があります")

# ERROR: エラー情報
self.logger.error(f"API リクエストに失敗: {e}")
self.logger.error(f"イベントの処理に失敗: {e}", exc_info=True)

# CRITICAL: 致命的なエラー、即時の対応が必要
self.logger.critical("データベース接続に失敗し、ボットが正常に動作できません")
```

### 2. 構造化ログ

```python
# 構造化ログを使用すると解析しやすい
self.logger.info(f"リクエストを処理: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ 非構造化ログの使用
self.logger.info(f"リクエストを処理しました。ユーザー {user_id} から、所要時間 {duration} ミリ秒")
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

### 2. ブロッキング操作を避ける

```python
# 非同期操作を使用
async def process_message(self, event: Event):
    # 非同期処理
    await self._async_process(event)

# ❌ ブロッキング操作
async def process_message(self, event: Event):
    # 同期操作のためイベントループをブロックする
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
    API_KEY = "sk-1234567890"  # このようにしないでください！
```

### 2. 入力バリデーション

```python
# ユーザー入力の検証
async def process_command(self, event: Event):
    user_input = event.get_text()
    
    # 入力長の検証
    if len(user_input) > 1000:
        await event.reply("入力が長すぎます。再度入力してください")
        return
    
    # 入力形式の検証
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

## HTTP ルートのライフサイクル

モジュールが `router` 経由で登録した HTTP/WebSocket ルートのライフサイクルは、フレームワークが**帰属原則**に基づいて自動管理します：

- 登録時の名前空間がそのまま帰属識別子になります。**reload / unload 時にフレームワークがその帰属下のすべてのルートと接続リソースを自動クリーンアップする**ため、手動での登録解除は不要です
- したがって、**`on_load` 内では無条件にルートを再登録しなければなりません**。インスタンスレベルのブールフラグによる「1 回だけ登録する」最適化はしないでください：設定のホットリロードは stop/start をトリガーして**同一インスタンスを再利用**するため、フラグが残留すると、ルートがクリーンアップされた後に**永久に失われ**、エンドポイントが 404 を返し、プロセスを再起動するまで回復しなくなります

```python
class MyModule(BaseModule):
    async def on_load(self):
        # ロードのたびに無条件で再登録
        router.register_http_route("MyModule", "/api/panel", self._panel, methods=["GET"])
```

ルートを事前に手動でアンロードする必要がある場合（特定のエントリを動的にオフラインにするなど）は、能動的に登録解除できます：

```python
from ErisPulse.Core import router

router.unregister_http_route("MyModule", "/api/panel")
```

- フロントエンド/呼び出し側は、ホットリロードのウィンドウ期間中にルートの 404 を受信する可能性がありますが、これは一時的な現象です。ブラウザ向けのインタラクティブページでは、404 に対して有限回の自動リトライを行うことを推奨します

## デプロイ

### 1. バージョン管理

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
```

セマンティックバージョニングに従います：
- MAJOR.MINOR.PATCH
- メジャーバージョン：互換性のない API 変更
- マイナーバージョン：後方互換性のある機能追加
- パッチバージョン：後方互換性のある問題修正

### 2. README ヘッダー

`epsdk create` で生成される README には、ErisPulse のヘッダー識別（ロゴ + バッジ行）が組み込まれています。推奨される2つのパターン：

**パターン A — ErisPulse ロゴのみ（デフォルト）：**

```markdown
<div align="center">

<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" width="180" alt="MyModule" />

# MyModule

**一言説明**

<p>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/pypi/v/ErisPulse-MyModule?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/ライセンス-MIT-blue?style=for-the-badge" alt="License"></a>
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
（バッジ行は上記と同じ）
</div>
```

必要に応じて GitHub Stars、Downloads などのバッジを追加できます。ロゴはプロジェクトのローカルにダウンロードし（`.github/assets/ErisPulseLogo.png`）、相対パスで参照するように変更することもできます。

## 関連ドキュメント

### 学習パスに戻る

- [モジュール開発入門](getting-started.md) - 最初のモジュールを作成する
- [モジュールのコア概念](core-concepts.md) - モジュールアーキテクチャを理解する

### シナリオ別に深掘り

- [Event ラッパークラス](event-wrapper.md) - イベント処理の詳細
- [公開とモジュールストアガイド](../publishing.md) - モジュールを書き終えたら PyPI とモジュールストアへ公開する