# モジュール開発におけるベストプラクティス

このドキュメントでは、ErisPulse モジュール開発に関するベストプラクティスを提供します。

以下のルールに従って変換してください。

1.  Markdown形式を維持する（見出し、リスト、コードブロック、リンク、画像など）
2.  用語を正確に翻訳し、専門性を保つ
3.  コードブロック内のコードロジックは翻訳しないが、コード内の中国語コメント、文字列は日本語に翻訳する
4.  原文の構造とトーンを維持する
5.  用語について、日本語の対応用語が不明な場合は英語の原語を保持する
6.  その他の説明や注釈は追加せず、翻訳後のコンテンツのみを返す
7.  翻訳後のドキュメントに中国語（固有名詞を除く）が残らないようにする。これにはコードブロック内のコメントと文字列も含まれる
8.  翻訳後のMarkdownコンテンツを直接出力する。```markdown```などのコードブロックで囲まない

**重要：パス置換ルール**
-   ドキュメントリンク内の `docs/ja/` を `docs/ja/` に置換する
-   例：`docs/ja/quick-start.md` は `docs/ja/quick-start.md` に変更する
-   現在の言語バージョンではないファイルを指し示すリンク（`README.xx.md` 形式のリンクなど）については、変更せずそのまま保持する
-   これにより、正しい言語バージョンのドキュメントを指すようにする

## モジュール設計

### 1. 単一責任の原則

各モジュールは1つのコア機能のみを担当する必要があります。

```python
# 良い設計：各モジュールは1つの機能のみを担当する
class WeatherModule(BaseModule):
    """天気照会モジュール"""
    pass

class NewsModule(BaseModule):
    """ニュース照会モジュール"""
    pass

# 悪い設計：1つのモジュールが複数の非関連な機能を担当する
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

宣言的設定（`ConfigClass` + `BaseConfig`）を使用することを推奨します。これにより、型安全性、自動テンプレート生成、WebUI フォームサポートなどの機能が得られます。

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
        cfg = self.cfg  # 型安全性があり、即時読み込み
        await self._fetch(cfg.api_url, timeout=cfg.timeout)
```

また、手動での設定ストレージの読み書きを引き続き使用することも可能です（[モジュールの核心的な概念](core-concepts.md#設定管理)を参照）。

### 宣言的翻訳キー（v2.7.0+）

モジュールは `I18nClass` を使用して翻訳キーを集中して宣言できます。フレームワークは i18n システムに自動的に登録されるため、手動で `i18n.register()` を呼び出す必要はありません。

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
        # 設定フィールドの説明の翻訳
        api_url: I18nKey = I18nKey(
            default="API URL",
            zh_CN="API 地址",
            zh_TW="API 位址",
            en="API URL",
            ja="API URL",
            ru="API URL",
        )
```

詳細な使用方法については、[i18n ドキュメント](../../advanced/i18n.md#推奨される書き方 -i18nclass-で翻訳キーを宣言する-v270)を参照してください。

## 非同期プログラミング

### 1. 非同期ライブラリの使用

```python
# SDK内蔵のHTTPクライアント（非同期、自動ログと統計）の使用が推奨
from ErisPulse.Core import client

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await client.get(url)
        return await resp.json()

# sdk.clientを使用することも可能（効果は同じ）
from ErisPulse import sdk

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await sdk.client.get(url)
        return await resp.json()

# aiohttpを直接インポートしないこと（フレームワークによる統一管理が困難）
import aiohttp

class MyModule(BaseModule):
    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

# requestsを使用しないこと（同期的で、イベントループをブロックする）
import requests

class MyModule(BaseModule):
    def fetch_data(self, url):
        return requests.get(url).json()  # イベントループをブロックする
```

### 2. 正しい非同期操作

```python
from ErisPulse.Core.Event import Event  # event: Event注釈でIDEの補完が得られる

async def handle_command(self, event: Event):
    # 結果を待つ必要のある処理：直接await（ライフサイクルが明確）
    result = await self._long_operation()

async def on_load(self, event: dict):
    # バックグラウンドタスク（ポーリング/定時/fire-and-forget）：self.spawn()を使用
    # モジュールのアンロード時にon_unloadの後にフレームワークがキャンセルを保証し、selfの保持によるリークを防ぐ
    self.spawn(self._poll())
```

> [!NOTE]
> バックグラウンドタスクは`self.spawn()`（ErisPulse **2.8.0+**）を使用することを推奨します。`asyncio.create_task`は、裸のタスクを作成し、モジュールに属さないため、アンロード時に自動的にクリーンアップされず、selfの参照を保持してモジュールインスタンスが回収されない（ホットリロードのリーク）可能性があります。詳細は[ライフサイクル管理](../../advanced/lifecycle.md#バックグラウンドタスクの所属と自動キャンセル)をご覧ください。

### 3. リソース管理

```python
async def on_load(self, event):
    # SDKクライアントは接続プールを自動的に管理するため、手動でsessionを作成する必要はない
    pass
    
async def on_unload(self, event):
    # カスタムクライアントが必要な場合は、リソースのクリーンアップを忘れずに
    pass

## イベント処理

### 1. Eventラッパークラスの使用

```python
# Eventラッパークラスの便利な方法を使用
@command("info")
async def info_command(event: Event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"こんにちは、{nickname}！")

# 辞書に直接アクセスするのではなく
@command("info")
async def info_command(event: Event):
    user_id = event["user_id"]  # 明確さに欠け、間違いやすい
```

### 2. 懒惰的ロードの適切な使用

```python
# 使用頻度の低いコマンドモジュール：activate_onトリガーを宣言し、最初の一致するコマンドが到着したときに自動的にアクティブ化（懒惰的ロードを維持）
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"command": {"name": "dice", "help": "サイコロを振る", "aliases": ["d"]}},
        ])

# 使用頻度の低いリスナー・モジュール：イベントトリガーを宣言し、イベントが到着したときに自動的にアクティブ化
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"notice": "group_member_increase"},
        ])

# 高頻度のトリガー（各メッセージを処理する必要がある）または起動時に準備が必要なモジュール：即時ロード
class HotListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# ユーティリティモジュールは懒惰的ロードに適している
class UtilityModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True)
```

> `activate_on`の完全な構文（イベントの三形式 / コマンドの簡略化とdict宣言 / helpのフォールバックチェーン）については、  
> [懒惰的ロードモジュールシステム](../../advanced/lazy-loading.md#イベント駆動の懒惰的アクティベーションactivate_on)を参照してください。

### 3. イベントハンドラの登録

```python
async def on_load(self, event):
    # on_loadでイベントハンドラを登録
    @command("hello")
    async def hello_handler(event: Event):
        await event.reply("こんにちは！")
    
    @message.on_group_message()
    async def group_handler(event: Event):
        self.logger.info("グループメッセージを受信しました")
    
    # 手動での登録解除は不要、フレームワークが自動的に処理します

## エラー処理

### 1. 例外の分類処理

```python
async def handle_event(self, event: Event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # 予期されたビジネスエラー
        self.logger.warning(f"ビジネス警告: {e}")
        await event.reply(f"パラメータエラー: {e}")
    except aiohttp.ClientError as e:
        # ネットワークエラー（推奨: sdk.client + ClientError を使用）
        # 旧コードでは直接 aiohttp を使用しても正常に動作しますが、新規コードでは ErisPulse の例外体系を使用することを推奨します
        self.logger.error(f"ネットワークエラー: {e}")
        await event.reply("ネットワークリクエストに失敗しました。後でもう一度お試しください")
    except Exception as e:
        # 予期しないエラー
        self.logger.error(f"不明なエラー: {e}", exc_info=True)
        await event.reply("処理に失敗しました。管理者に連絡してください")
        raise
```

### 2. タイムアウト処理

```python
# 推奨: SDK 内部のクライアントを使用（タイムアウトと再試行機能が付属）
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import ClientTimeoutError

async def fetch_with_timeout(self, url, timeout=30):
    try:
        resp = await client.get(url, timeout=timeout)
        return await resp.json()
    except ClientTimeoutError:
        self.logger.warning(f"リクエストがタイムアウトしました: {url}")
        raise

## ストレージシステム

### 1. トランザクションを使用する

```python
# トランザクションを使用してデータの一貫性を確保
async def update_user(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])

# ❌ トランザクションを使用しないと、データの一貫性が損なわれる可能性があります
async def update_user(self, user_id, data):
    self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
    # ここでエラーが発生すると、上記の設定はロールバックされません
    self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
```

### 2. バッチ操作

```python
# バッチ操作を使用してパフォーマンスを向上させる
def cache_multiple_items(self, items):
    self.sdk.storage.set_multi({
        f"item:{k}": v for k, v in items.items()
    })

# ❌ 複数回呼び出すと効率が悪い
def cache_multiple_items(self, items):
    for k, v in items.items():
        self.sdk.storage.set(f"item:{k}", v)

## ロギング

### 1. ログレベルを適切に使用する

```python
# DEBUG: 詳細なデバッグ情報（開発時のみ）
self.logger.debug(f"入力パラメータ: {params}")

# INFO: 正常な実行時の情報
self.logger.info("モジュールが読み込まれました")
self.logger.info(f"リクエストを処理中: {request_id}")

# WARNING: 警告メッセージ。主要な機能には影響しない
self.logger.warning(f"設定項目 {key} が設定されていません、デフォルト値を使用します")
self.logger.warning("API レスポンスが遅い、最適化の必要がある可能性があります")

# ERROR: エラーメッセージ
self.logger.error(f"API リクエストに失敗しました: {e}")
self.logger.error(f"イベントの処理に失敗しました: {e}", exc_info=True)

# CRITICAL: 致命的なエラー、即座に対処が必要
self.logger.critical("データベース接続に失敗しました、ボットを正常に実行できません")
```

### 2. 構造化されたロギング

```python
# 構造化されたログを使用すると解析が容易になります
self.logger.info(f"リクエストを処理中: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ 非構造化ログを使用
self.logger.info(f"リクエストを処理しました。ユーザー {user_id} からのもの、所要時間 {duration} ミリ秒")

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
    # 同期操作、イベントループをブロック
    result = self._sync_process(event)

## セキュリティ

### 1. 敏感データ保護

```python
# 敏感データは設定に格納されます（宣言型の ConfigClass、secret フィールドはログ/エクスポートに含まれません）
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

# ❌ 敏感データをハードコードしないでください
class MyModule(BaseModule):
    API_KEY = "sk-1234567890"  # これを行わないでください！
```

### 2. 入力検証

```python
# ユーザー入力を検証
async def process_command(self, event: Event):
    user_input = event.get_text()
    
    # 入力の長さを検証
    if len(user_input) > 1000:
        await event.reply("入力が長すぎます。再入力してください")
        return
    
    # 入力の形式を検証
    if not re.match(r'^[a-zA-Z0-9]+$', user_input):
        await event.reply("入力形式が正しくありません")
        return

## テスト

### 1. ユニットテスト

```python
import pytest
from ErisPulse.Core.Bases import BaseModule

class TestMyModule:
    def test_config_defaults(self):
        """テスト設定のデフォルト値"""
        config = MyModule.ConfigClass()
        assert config.timeout == 30
```

### 2. インテグレーションテスト

```python
@pytest.mark.asyncio
async def test_command_handling():
    """テストコマンドの処理"""
    module = MyModule()
    await module.on_load({})
    
    # コマンドイベントをシミュレート
    event = create_test_command_event("hello")
    await module.handle_command(event)
```

[**English**](docs/en/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## 配置

### 1. バージョン管理

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
```

セマンティックバージョニングに従います：
- MAJOR.MINOR.PATCH
- 主バージョン：互換性のないAPIの変更
- 次バージョン：互換性のある機能の追加
- 修正番号：互換性のある問題の修正

### 2. READMEのヘッダー

`epsdk create` で生成されたREADMEには、ErisPulseのヘッダー識別子（ロゴ + バッジ行）が組み込まれています。2つの推奨モードがあります：

**モード A — ErisPulseロゴのみ（デフォルト）：**

```markdown
<div align="center">

<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" width="180" alt="MyModule" />

# MyModule

**1文で説明**

<p>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/pypi/v/ErisPulse-MyModule?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/Powered_by-ErisPulse-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="ErisPulse"></a>
</p>

</div>
```

**モード B — モジュールアイコン × ErisPulseロゴ（独自アイコンがある場合）：**

```markdown
<div align="center">

<img src=".github/assets/MyModuleIcon.svg" width="120" alt="MyModule" />
<span style="font-size:44px;color:#c8c8c8;margin:0 18px;vertical-align:middle;">×</span>
<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" height="120" alt="ErisPulse" />

# MyModule
（バッジ行は上記と同じ）
</div>
```

GitHub Stars、Downloadsなどのバッジを必要に応じて追加できます。ロゴはプロジェクトのローカルにダウンロードし（`.github/assets/ErisPulseLogo.png`）、相対パスで参照することも可能です。

## 関連ドキュメント

- [モジュール開発入門](getting-started.md) - 初めてのモジュールを作成する
- [モジュールのコア概念](core-concepts.md) - モジュールアーキテクチャを理解する
- [Event ラッパークラス](event-wrapper.md) - イベント処理の詳細