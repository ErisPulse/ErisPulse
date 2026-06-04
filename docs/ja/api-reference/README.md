# API リファレンス

このディレクトリには、ErisPulse フレームワークの API リファレンスドキュメントが含まれています。

## ドキュメント一覧

- [コアモジュール API](core-modules.md) - ストレージ、設定、ログなどのコアモジュール API
- [イベントシステム API](event-system.md) - Event モジュール API リファレンス
- [アダプターシステム API](adapter-system.md) - Adapter マネージャー API リファレンス
- [ErisPulse 自動生成 API](auto_api/README.md) - 自動生成 API リファレンス

## API の概要

### コアモジュール

ErisPulse SDK は以下のコアモジュールを提供します：

| モジュール | パス | 説明 |
|------|------|------|
| `sdk.storage` | `sdk.storage` | ストレージシステム |
| `sdk.config` | `sdk.config` | 設定管理 |
| `sdk.logger` | `sdk.logger` | ログシステム |
| `sdk.adapter` | `sdk.adapter` | アダプター管理 |
| `sdk.module` | `sdk.module` | モジュール管理 |
| `sdk.lifecycle` | `sdk.lifecycle` | ライフサイクル管理 |
| `sdk.router` | `sdk.router` | ルーティング管理 |

### イベントシステム

Event モジュールは以下のサブモジュールを提供します：

| モジュール | パス | 説明 |
|------|------|------|
| `command` | `ErisPulse.Core.Event.command` | コマンド処理 |
| `message` | `ErisPulse.Core.Event.message` | メッセージイベント |
| `notice` | `ErisPulse.Core.Event.notice` | 通知イベント |
| `request` | `ErisPulse.Core.Event.request` | リクエストイベント |
| `meta` | `ErisPulse.Core.Event.meta` | メタイベント |

### 基底クラス

ErisPulse は以下の基底クラスを提供します：

| 基底クラス | パス | 説明 |
|------|------|------|
| `BaseModule` | `ErisPulse.Core.Bases.BaseModule` | モジュール基底クラス |
| `BaseAdapter` | `ErisPulse.Core.Bases.BaseAdapter` | アダプター基底クラス |

## 使用例

### コアモジュールへのアクセス

```python
from ErisPulse import sdk

# ストレージシステム
sdk.storage.set("key", "value")
value = sdk.storage.get("key")

# 設定管理
config = sdk.config.getConfig("MyModule")

# ログシステム
sdk.logger.info("ログ情報")

# アダプター管理
adapter = sdk.adapter.get("platform")
await adapter.Send.To("user", "123").Text("Hello")

# モジュール管理
module = sdk.module.get("ModuleName")

# ライフサイクル管理
await sdk.lifecycle.submit_event("custom.event", msg="カスタムイベント")

# ルーティング管理
sdk.router.register_http_route("MyModule", "/api", handler, ["GET"])
```

### イベントシステムの使用

```python
from ErisPulse.Core.Event import command, message, notice, request, meta

# コマンド処理
@command("hello", help="挨拶コマンド")
async def hello_handler(event):
    await event.reply("こんにちは！")

# メッセージ処理
@message.on_group_message()
async def group_handler(event):
    sdk.logger.info(f"グループメッセージを受信: {event.get_text()}")

# 通知処理
@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("友だち追加ありがとうございます！")

# リクエスト処理
@request.on_friend_request()
async def friend_request_handler(event):
    pass

# メタイベント処理
@meta.on_connect()
async def connect_handler(event):
    sdk.logger.info("プラットフォーム接続成功")
```

### 基底クラスの継承

```python
from ErisPulse.Core.Bases import BaseModule

class MyModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
    
    async def on_load(self, event):
        """モジュールのロード"""
        pass
    
    async def on_unload(self, event):
        """モジュールのアンロード"""
        pass
```

## 関連ドキュメント

- [コアコンセプト](../getting-started/basic-concepts.md) - フレームワークのコアコンセプトを理解する
- [モジュール開発ガイド](../developer-guide/modules/) - カスタムモジュールの開発
- [アダプター開発ガイド](../developer-guide/adapters/) - プラットフォームアダプターの開発