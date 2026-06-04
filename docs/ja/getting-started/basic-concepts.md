# 基本概念

本ガイドでは ErisPulse のコアコンセプトを紹介し、フレームワークの設計思想と基本アーキテクチャを理解するのに役立ちます。

## イベント駆動アーキテクチャ

ErisPulse はイベント駆動アーキテクチャを採用しており、すべての対話はイベントを通じて伝達および処理されます。

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
イベントシステムに提出
      │
      ▼
登録されたプロセッサに配信
      │
      ▼
モジュールがイベントを処理
      │
      ▼
アダプター経由で応答を送信
      │
      ▼
ユーザーに表示
```

### OneBot12 標準

ErisPulse は OneBot12 をコアイベント標準として使用しています。OneBot12 は汎用のチャットボットアプリケーションインターフェース標準であり、統一されたイベント形式を定義しています。

すべてのアダプターはプラットフォーム固有のイベントを OneBot12 形式に変換し、コードの一貫性を確保します。

## コアコンポーネント

### 1. SDK オブジェクト

SDK はすべての機能の統一されたエントリーポイントであり、コアコンポーネントへのアクセスを提供します。

```python
from ErisPulse import sdk

# コアモジュールにアクセス
sdk.storage    # ストレージシステム
sdk.config     # 設定システム
sdk.logger     # ログシステム
sdk.adapter    # アダプターシステム
sdk.module     # モジュールシステム
sdk.router     # ルーター（ルーティング）システム
sdk.client     # HTTP クライアント
sdk.lifecycle  # ライフサイクルシステム
```

### 2. Event オブジェクト

Event オブジェクトはイベントデータをカプセル化し、便利なアクセスメソッドを提供します。

```python
@command("info")
async def info_handler(event):
    # イベント情報を取得
    event_id = event.get_id()
    user_id = event.get_user_id()
    platform = event.get_platform()
    text = event.get_text()
    
    # 返信を送信
    await event.reply(f"ユーザー: {user_id}, プラットフォーム: {platform}")
```

### 3. アダプター

アダプターは ErisPulse と外部プラットフォーム間のブリッジです。

**役割：**
- プラットフォームのネイティブイベントを受信
- OneBot12 標準形式に変換
- 標準形式のイベントをプラットフォームに送信

**代表的なアダプター：**
- Yunhu アダプター：クラウド湖（Yunhu）プラットフォームとの通信
- Telegram アダプター：Telegram Bot API との通信
- OneBot11 アダプター：OneBot11 互換のアプリケーションとの通信
- Email アダプター：メールの送受信処理

### 4. モジュール

モジュールは機能拡張の基本単位であり、以下のことができます：
- イベントハンドラーの登録
- ビジネスロジックの実装
- アダプターを呼び出してメッセージを送信
- コアモジュールが提供するサービスの使用

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class MyModule(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0
        )

    async def on_load(self, event):
        """モジュールが読み込まれたときに呼び出されます"""
        # イベントハンドラーを登録
        @command("mycmd", help="私のコマンド")
        async def my_command(event):
            await event.reply("コマンド実行成功")

        self.logger.info("モジュールが読み込まれました")

    async def on_unload(self, event):
        """モジュールがアンロードされるときに呼び出されます"""
        self.logger.info("モジュールがアンロードされました")
```

## イベントタイプ

### メッセージイベント

ユーザーが送信するすべてのメッセージ（プライベートチャットおよびグループチャットを含む）を処理します。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def message_handler(event):
    text = event.get_text()
    await event.reply(f"メッセージを受信しました: {text}")
```

### コマンドイベント

コマンドプレフィックス（例: `/hello`）で始まるメッセージを処理します。

```python
from ErisPulse.Core.Event import command

@command("hello", help="挨拶を送信")
async def hello_handler(event):
    await event.reply("こんにちは！")
```

### 通知イベント

システム通知（例: フレンド追加、グループメンバーの変化）を処理します。

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("フレンド追加を歓迎します！")
```

### リクエストイベント

ユーザーのリクエスト（例: フレンドリクエスト、グループ招待）を処理します。

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    await event.reply("あなたのフレンドリクエストを受け取りました")
```

### メタイベント

システムレベルのイベント（例: 接続、ハートビート）を処理します。

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} に接続しました")
```

## コアモジュールの説明

### Storage（ストレージ）

SQLite ベースのキーバリューストレージシステムであり、データの永続化に使用されます。

```python
# 値の設定
sdk.storage.set("key", "value")

# 値の取得
value = sdk.storage.get("key", "default_value")

# バッチ操作
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
# 設定を取得
config = sdk.config.getConfig("MyModule", {})

# 設定を設定
sdk.config.setConfig("MyModule", {"key": "value"})

# ネストされた設定を読み取る
value = sdk.config.getConfig("MyModule.subkey", "default")
```

### Logger（ログ）

モジュール化されたログシステム。

```python
# ログの記録
sdk.logger.info("これは情報です")
sdk.logger.warning("これは警告です")
sdk.logger.error("これはエラーです")

# 子ロガーを取得
child_logger = sdk.logger.get_child("submodule")
child_logger.info("サブモジュールログ")
```

**プロパティアクセスのシンタックスシュガー**

`get_child()` メソッドを使用する以外に、**プロパティアクセス**を使用して子ロガーを作成することもできます。これはより簡潔な**シンタックスシュガー**（構文糖衣）の記法です。

```python
# プロパティアクセスで子ロガーを作成
sdk.logger.mymodule.info("モジュールメッセージ")

# ネストされたアクセスもサポートされています
sdk.logger.mymodule.database.info("データベースメッセージ")
```

### Router（ルーター）

HTTP および WebSocket のルーティング管理をサポートし、FastAPI のネイティブ型と ErisPulse 抽象型をサポートしています。

> ルーターハンドラーは 2 つの型アノテーションをサポートしています：FastAPI のネイティブ型（`fastapi.Request` / `fastapi.WebSocket`）と ErisPulse 抽象型（`HttpRequest` / `WebSocketConnection`）。より良い移植性を得るために抽象型を使用することをお勧めします。

```python
from ErisPulse import sdk

# 方法1：ErisPulse 抽象型を使用する（推奨）
from ErisPulse.Core import HttpRequest, WebSocketConnection

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}

@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    data = await ws.receive_text()
    await ws.send_text(f"Echo: {data}")

# 方法2：FastAPI のネイティブ型を使用する（既存のコードとの互換性）
from fastapi import Request, WebSocket

@sdk.router.get("MyModule", "/api2")
async def handler2(request: Request):
    return {"status": "ok"}
```

{!--< tips >!--}
> **自動インジェクション**：ルーターシステムはパラメータアノテーションに基づいて、対応する型のオブジェクトを自動的に注入します。手動で作成する必要はありません。
> 
> **よくある問題**：`{"detail":[{"type":"missing","loc":["query","request"],"msg":"Field required"}]}` エラーが表示される場合は、型アノテーションが不足していることを示しています。HTTP ハンドラーのパラメータには `request`、WebSocket ハンドラーのパラメータには `websocket` または `ws` のアノテーションを使用していることを確認してください。

より詳しいルーター機能については [ルーター管理者](../advanced/router.md) を参照してください。

### Client（HTTP クライアント）

HTTP リクエストを送信するための統一された HTTP クライアントです。モジュールとアダプターは、直接 `aiohttp` をインポートする代わりに、グローバルクライアントを優先して使用する必要があります。

```python
from ErisPulse.Core import client

# GET リクエスト
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# POST リクエスト
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice"},
)

# レスポンスのプロパティ
resp.status        # ステータスコード（例: 200）
resp.headers       # レスポンスヘッダー
body = await resp.text()   # テキストレスポンスボディ
data = await resp.json()   # JSON パース
```

{!--< tips >!--}
> グローバルクライアントには、自動再試行、タイムアウト制御、リクエスト統計、およびライフサイクルイベントの統合などの機能があります。詳細は [HTTP クライアント](../advanced/http-client.md) を参照してください。
>
> また、`from ErisPulse import sdk` を使用して `sdk.client` にアクセスすることもでき、効果は同じです。

## SendDSL メッセージ送信

アダプターはチェーンコール方式のメッセージ送信インターフェースを提供します。

### 基本的な送信

```python
# アダプターインスタンスを取得
yunhu = sdk.adapter.get("yunhu")

# メッセージを送信
await yunhu.Send.To("user", "U1001").Text("Hello")

# 送信アカウントを指定
await yunhu.Send.Using("bot1").To("group", "G1001").Text("グループメッセージ")
```

### チェーン修飾子

```python
# ユーザーにメンション
await yunhu.Send.To("group", "G1001").At("U2001").Text("@メッセージ")

# 返信メッセージ
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("返信")

# 全体にメンション
await yunhu.Send.To("group", "G1001").AtAll().Text("告知")
```

### Event 返信メソッド

Event オブジェクトは便利な返信メソッドを提供します。

```python
@command("test")
async def test_handler(event):
    # シンプルなテキスト返信
    await event.reply("返信内容")
    
    # 画像を送信
    await event.reply("http://example.com/image.jpg", method="Image")
    
    # 音声を送信
    await event.reply("http://example.com/voice.mp3", method="Voice")
```

## レイジーロードシステム

ErisPulse はモジュールのレイジーロード（Lazy Load）をサポートしており、モジュールは初めてアクセスされたときにのみ初期化され、起動速度が向上します。

```python
class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,   # レイジーロードを有効にする（デフォルト）
            priority=0       # ロード優先度
        )
```

**即時ロードが必要なシナリオ：**
- ライフサイクルイベントを監視するモジュール
- 定期タスクモジュール
- アプリケーションの起動時に初期化が必要なモジュール

## 次のステップ

- [イベント処理の入門](event-handling.md) - 各種イベントの処理方法を学ぶ
- [一般的なタスクの例](common-tasks.md) - 一般的な機能の実装をマスターする