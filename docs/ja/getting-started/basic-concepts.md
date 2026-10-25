# 基本概念

> [!NOTE]
> **L1 コア必読**——ドキュメントトップページの「L1 コア5編」のうちの第2編（モジュール開発入門 → **基本概念** → Event ラッパークラス → 設定ファイルの説明 → 例外キャッチ）。

ユーザーがメッセージを送ってからボットが返信するまでの間に、どのようなコンポーネントを経由するのでしょうか？アダプターとモジュールはそれぞれ何を担当しているのでしょうか？この記事を読み終えれば、ハンドラーを書く際に直面する設計上の問題を自力で答えられるようになり、例をただ写すだけではなくなります。

## イベント駆動アーキテクチャ

ErisPulse はイベント駆動アーキテクチャを採用しており、すべての対話はイベントを通じて伝達・処理されます。

### イベントフロー

```
ユーザーがメッセージを送信
      │
      ▼
プラットフォームが受信
      │
      ▼
アダプターがプラットフォームのネイティブイベントを受信
      │
      ▼
OneBot12 標準イベントに変換
      │
      ▼
イベントシステムへ送出
      │
      ▼
登録済みのハンドラーに配信
      │
      ▼
モジュールがイベントを処理
      │
      ▼
アダプターを通じてレスポンスを送信
      │
      ▼
プラットフォームがユーザーに表示
```

### OneBot12 標準

ErisPulse は OneBot12 をコアイベント標準として使用しています。OneBot12 は汎用のチャットボットアプリケーションインターフェース標準であり、統一されたイベント形式を定義しています。

すべてのアダプターはプラットフォーム固有のイベントを OneBot12 形式に変換し、コードの一貫性を保証します。

## コアコンポーネント

### 1. SDK オブジェクト

SDK はすべての機能の統一されたエントリーポイントであり、コアコンポーネントへのアクセスを提供します。

```python
from ErisPulse import sdk

# コアモジュールへのアクセス
sdk.storage    # ストレージシステム
sdk.config     # 設定システム
sdk.logger     # ログシステム
sdk.adapter    # アダプターシステム
sdk.module     # モジュールシステム
sdk.router     # ルーティングシステム
sdk.client     # HTTPクライアント
sdk.lifecycle  # ライフサイクルシステム
```

> [!WARNING]
> **ルートから一括インポート**：`from ErisPulse.Core import adapter` / `import ErisPulse.Core.adapter`
> これらの書き方は**マネージャーインスタンス**（`AdapterManager` シングルトン）にバインドされます。`ErisPulse.Core`
> パッケージの再エクスポートは同名のサブモジュールを覆い隠します。テスト、パッチ、またはモジュールオブジェクト自体が必要な場合は、
> 一律 `from ErisPulse import sdk` ルートインポート（`sdk.adapter` はマネージャーインスタンス）を使用してください。

### 2. Event オブジェクト

Event オブジェクトはイベントデータをラップし、便利なアクセスメソッドを提供します。

```python
@command("info")
async def info_handler(event):
    # イベント情報を取得
    event_id = event.get_id()
    user_id = event.get_user_id()
    platform = event.get_platform()
    text = event.get_text()
    
    # レスポンスを送信
    await event.reply(f"ユーザー: {user_id}, プラットフォーム: {platform}")
```

### 3. アダプター

アダプターは ErisPulse と外部プラットフォームの間のブリッジです。

**役割：**
- プラットフォームのネイティブイベントを受け取る
- OneBot12 標準形式に変換する
- 標準形式のイベントをプラットフォームに送信する

**例のアダプター：**
- Yunhu アダプター：雲湖プラットフォームとの通信
- Telegram アダプター：Telegram Bot API との通信
- OneBot11 アダプター：OneBot11 兼容アプリとの通信
- Email アダプター：メールの送受信処理

### 4. モジュール

モジュールは機能拡張の基本単位であり、以下を実現できます：
- イベントハンドラの登録
- ビジネスロジックの実装
- アダプターを呼び出してメッセージを送信
- コアモジュールが提供するサービスの利用

#### モジュール発見メカニズム

ErisPulse は Python の `importlib.metadata.entry_points` を使用して、インストール済みのモジュールを発見します。モジュールは `pyproject.toml` でエントリーポイントを宣言します：

```toml
[project.entry-points."erispulse.module"]
MyModule = "my_package:Main"
```

SDK の初期化時に、`erispulse.module` グループのすべてのエントリーポイントをスキャンし、モジュールクラスを `ModuleManager` に登録し、依存関係に基づいてトポロジカルソートした後、順次初期化します。

#### 最小限のモジュール

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")

    async def on_load(self, event):
        self.logger.info("モジュールがロードされました")

    async def on_unload(self, event):
        self.logger.info("モジュールがアンロードされました")
```

#### モジュールのライフサイクル

- **登録**：SDK がモジュールクラスを発見し、マネージャーに登録
- **ロード**：モジュールインスタンスを作成し、`on_load(event)` を呼び出す（`event = {"module_name": "MyModule"}`）
- **アンロード**：`on_unload(event)` を呼び出し、リソースをクリーンアップ

#### ロード戦略

`get_load_strategy()` を使用して、モジュールのロード動作を宣言します：

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # ラグジュアリーなロードかどうか（デフォルトは True）
            priority=0        # ロード優先度、数値が大きいほど初期化が早くなる
        )
```

- **`lazy_load=True`（デフォルト）**：`sdk.MyModule` に初めてアクセスしたときにモジュールを初期化し、起動時間を短縮
- **`lazy_load=False`**：SDK の起動時に即座に初期化し、ライフサイクルイベントを監視するか、定時タスクを実行するモジュールに適しています
- **`priority`**：同じ優先度のモジュールは登録順にロードされ、数値が大きいほど初期化が早くなります

> 詳細なラグジュアリーなロードの仕組みについては、[ラグジュアリーなロードシステム](../advanced/lazy-loading.md)を参照してください。

## イベントタイプ

ErisPulse は 5 種類のイベントをサポートしています：

| イベントタイプ | デコレーター | 説明 |
|---------|--------|------|
| メッセージイベント | `@message.on_message()` | ユーザーが送信したすべてのメッセージ（個人チャット、グループチャット） |
| コマンドイベント | `@command("name")` | コマンドプレフィックスで始まるメッセージ（例：`/hello`） |
| 通知イベント | `@notice.on_friend_add()` など | システム通知（フレンド追加、グループメンバーの変更など） |
| リクエストイベント | `@request.on_friend_request()` など | ユーザーリクエスト（フレンドリクエスト、グループ招待） |
| メタイベント | `@meta.on_connect()` など | システムレベルのイベント（接続、切断、ハートビート） |

> 各イベントタイプの詳細な使い方とコード例については、[イベント処理入門](event-handling.md) を参照してください。

## コアモジュールの説明

### Storage（ストレージ）

SQLite ベースのキーバリューストレージシステムで、データの永続化に使用します。

```python
# 値の設定
sdk.storage.set("key", "value")

# 値の取得
value = sdk.storage.get("key", "default_value")

# 一括操作
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2"
})

# トランザクション
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Config（設定）

TOML 形式の設定ファイル管理。

```python
# 設定の取得
config = sdk.config.getConfig("MyModule", {})

# 設定の保存
sdk.config.setConfig("MyModule", {"key": "value"})

# ネストされた設定の読み取り
value = sdk.config.getConfig("MyModule.subkey", "default")
```

### Logger（ログ）

モジュール化されたログシステム。

```python
# ログの記録
sdk.logger.info("これは情報メッセージです")
sdk.logger.warning("これは警告メッセージです")
sdk.logger.error("これはエラーメッセージです")

# 子ロガーの取得
child_logger = sdk.logger.get_child("submodule")
child_logger.info("サブモジュールのログ")
```

**属性アクセスのシンタックスシュガー**

`get_child()` メソッドを使用する以外に、**属性アクセス**の方法で子ロガーを作成することもできます。これはより簡潔な**シンタックスシュガー**の書き方です：

```python
# 属性アクセスで子ロガーを作成
sdk.logger.mymodule.info("モジュールメッセージ")

# ネストされたアクセスもサポート
sdk.logger.mymodule.database.info("データベースメッセージ")
```

### Router（ルーティング）

FastAPI + Uvicorn ベースの HTTP および WebSocket ルーティング管理。デコレータールーティング、ミドルウェア、グループ化、レート制限、CORS をサポートします。

```python
from ErisPulse.Core import HttpRequest

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}
```

> ルーティング API の完全な情報（WebSocket、ミドルウェア、レート制限、CORS など）については、[ルートマネージャー](../advanced/router.md) を参照してください。

### Client（ネットワーククライアント）

統合されたネットワーククライアントで、HTTP リクエスト、WebSocket 接続、コネクションプール管理、自動リトライ、タイムアウト制御、リクエスト統計、ライフサイクルイベント統合を集約しています。

```python
from ErisPulse.Core import client

# HTTP リクエスト
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# リトライとタイムアウト付き
resp = await client.get(url, timeout=30, max_retries=3)

# WebSocket 接続
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

> ネットワーククライアント API の完全な情報については、[ネットワーククライアント](../advanced/http-client.md) を参照してください。

## SendDSL メッセージ送信

アダプターはチェーン呼び出しのメッセージ送信インターフェースを提供します。

### 基本的な送信

```python
# アダプターインスタンスの取得
yunhu = sdk.adapter.get("yunhu")

# メッセージの送信
await yunhu.Send.To("user", "U1001").Text("Hello")

# 送信アカウントの指定
await yunhu.Send.Using("bot1").To("group", "G1001").Text("グループメッセージ")
```

### チェーン修飾

```python
# @ユーザー
await yunhu.Send.To("group", "G1001").At("U2001").Text("@メッセージ")

# メッセージへの返信
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("返信")

# @全員
await yunhu.Send.To("group", "G1001").AtAll().Text("お知らせ")
```

### Event 返信メソッド

Event オブジェクトは便利な返信メソッドを提供しています：

```python
@command("test")
async def test_handler(event):
    # シンプルなテキスト返信
    await event.reply("返信内容")
    
    # 画像の送信
    await event.reply("http://example.com/image.jpg", method="Image")
    
    # 音声の送信
    await event.reply("http://example.com/voice.mp3", method="Voice")
```

## 遅延読み込みシステム

ErisPulse はデフォルトでモジュールの遅延読み込みを有効にしており、モジュールは初めてアクセスされた時（例：`sdk.MyModule`）にのみ初期化されるため、起動速度が大幅に向上します。

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # 遅延読み込みを有効化（デフォルト）
            priority=0        # ロード優先度、数値が大きいほど先に初期化されます
        )
```

**遅延読み込みを無効にする必要があるシナリオ（`lazy_load=False`）：**
- ライフサイクルイベントをリッスンするモジュール（例：`core.init.complete`）
- 定期タスクやバックグラウンドサービスを起動するモジュール
- 他のモジュールがロードされる前に初期化を完了する必要があるモジュール

> 遅延読み込みメカニズムの詳細と注意事項については、[遅延読み込みシステム](../advanced/lazy-loading.md) を参照してください。

## 次のステップ

- **L1 パスに沿って続行**：次は [Event ラッパークラス](../developer-guide/modules/event-wrapper.md) で、イベントオブジェクトのすべての読み書きメソッドを習得します
- **書きながら学びたい**：[イベント処理入門](event-handling.md) ではイベントタイプ別にコピーしてすぐ使えるハンドラーの書き方を紹介しています。[よくあるタスクの例](common-tasks.md) では永続化、定期タスク、権限制御などのよく使う機能を網羅しています