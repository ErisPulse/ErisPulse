# ライフサイクル管理

ErisPulse は、システムの各コンポーネントの動作状態を監視し、監査、統計、カスタムロジックなどの拡張機能を実装するために、統一されたフック/ライフサイクルシステムを提供します。

システムは以下の 3 つのトリガーメソッドをサポートします：
- `await lifecycle.emit("event", data)` — 簡易版、任意のデータを渡します
- `lifecycle.emit_sync("event", data)` — 同期版（非同期コンテキスト以外で使用）
- `await lifecycle.submit_event("event", ...)` — 旧版との互換性のため、自動的に標準イベント形式を構築します

## イベント処理メカニズム

### ハンドラーの登録

```python
from ErisPulse import sdk

# デコレータモード
@sdk.lifecycle.on("module.load")
async def on_module_load(data):
    print(f"モジュール読み込み: {data}")

# プログラマティック登録
sdk.lifecycle.register("module.load", on_module_load, priority=10)

# 登録解除
sdk.lifecycle.unregister("module.load", on_module_load)

# オーナーごとに一括登録解除（モジュール/アダプターのアンインストール時にフレームワークが自動的に呼び出します）
removed = sdk.lifecycle.unregister_by_owner("MyModule")
print(f"クリーンアップされたライフサイクルフック: {removed} 個")
```

### 優先度

ハンドラーは `priority` パラメータをサポートしており、数値が大きいほど先に実行されます（モジュールローダーと一致）：

```python
@sdk.lifecycle.on("adapter.event.receive", priority=10)  # 最初に実行
async def first_handler(data):
    pass

@sdk.lifecycle.on("adapter.event.receive", priority=0)  # 後に実行
async def second_handler(data):
    pass
```

### ドット構造イベント

具体的なイベントがトリガーされた場合、その親イベントもトリガーされます：
- `module.load` トリガー時は、`module` もトリガーされます
- `adapter.event.receive` トリガー時は、`adapter.event` と `adapter` もトリガーされます

### ワイルドカード

`*` を登録すると、すべてのイベントをキャプチャします：

```python
@sdk.lifecycle.on("*")
async def on_anything(data):
    print(f"イベント受信: {data}")
```

## フック・ブレークポイント一覧

フレームワークには以下のフック・ブレークポイントが組み込まれており、ユーザーは `@sdk.lifecycle.on()` を使用して任意のブレークポイントをリッスンし、カスタムロジックを実装できます。

### コア初期化

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `core.init.start` | SDK 初期化開始 | `{}` |
| `core.init.complete` | SDK 初期化完了 | `{"duration": float, "success": bool, "adapters": {"enabled": [str], "disabled": [str]}, "modules": {"enabled": [str], "disabled": [str]}, "error": str(失敗時のみ)}` |
| `core.uninit.complete` | SDK アン初期化完了 | `{"duration": float, "success": bool, "adapters_closed": int, "modules_unloaded": int, "module_properties_cleared": int, "module_properties_to_clear": [str], "error": str(失敗時のみ)}` |

### 設定変更

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `config.set` | 設定項目が変更された | `{"key": str, "old_value": Any, "new_value": Any}` |

**例：設定監査**

```python
@sdk.lifecycle.on("config.set")
def audit_config(data):
    print(f"[監査] {data['key']}: {data['old_value']} -> {data['new_value']}")
```

### モジュールライフサイクル

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `module.register` | モジュールクラスがマネージャーに登録された | `{"module_name": str, "success": bool}` |
| `module.load` | モジュール読み込み完了（インスタンス化成功） | `{"module_name": str, "success": bool}` |
| `module.init` | モジュール初期化完了（レイジーロード含む） | `{"module_name": str, "success": bool}` |
| `module.unload` | モジュールアンロード | `{"module_name": str, "success": bool}` |

### アダプターライフサイクル

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `adapter.load` | アダプター登録完了 | `{"platform": str, "success": bool}` |
| `adapter.start` | アダプター起動 | `{"platforms": [str]}` |
| `adapter.status.change` | アダプター状態変更 | `{"platform": str, "status": str, "retry_count": int, "error": str(失敗時のみ)}` |
| `adapter.stop` | アダプター停止 | `{"platforms": [str]}` |
| `adapter.stopped` | アダプター停止完了 | `{"platforms": [str]}` |
| `adapter.bot.online` | Bot オンライン | `{"platform": str, "bot_id": str, "info": dict, "status": str}` |
| `adapter.bot.offline` | Bot オフライン | `{"platform": str, "bot_id": str, "status": str}` |

### イベント受信と処理

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `adapter.event.receive` | 外部プラットフォームイベント受信（最も早い段階） | `{"platform": str, "event_type": str, "raw_event_type": str}` |
| `adapter.event.dispatched` | イベント配信完了 | `{"platform": str, "event_type": str, "raw_event_type": str, "onebot_handlers_count": int}` |
| `event.pre_process` | イベントハンドラー実行開始前 | `{"event_type": str, "platform": str, "detail_type": str}` |

**例：イベント統計**

```python
event_counter = {}

@sdk.lifecycle.on("adapter.event.receive")
def count_events(data):
    platform = data["platform"]
    event_counter[platform] = event_counter.get(platform, 0) + 1

@sdk.lifecycle.on("adapter.event.dispatched")
def log_unhandled(data):
    if data["onebot_handlers_count"] == 0:
        print(f"[未処理] {data['platform']}/{data['event_type']}")
```

### メッセージ送信

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `message.sending` | メッセージ送信直前 | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |
| `message.sent` | メッセージ送信完了 | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |

**例：メッセージ送信監査**

```python
@sdk.lifecycle.on("message.sending")
def log_sending(data):
    print(f"[送信] -> {data['platform']}/{data['detail_type']}/{data['target_id']} via {data['method']}")
```

### コマンドシステム

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `command.matched` | コマンドが一致して実行される直前 | `{"command": str, "args": list[str], "platform": str, "user_id": str}` |
| `command.executed` | コマンド実行完了 | `{"command": str, "args": list[str], "platform": str, "user_id": str, "success": bool, "error": str(失敗時のみ)}` |

**例：コマンド統計**

```python
@sdk.lifecycle.on("command.matched")
def count_commands(data):
    print(f"[コマンド] /{data['command']} from {data['user_id']}@{data['platform']}")
```

### HTTP ルーティング

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `server.request` | HTTP リクエスト受信 | `{"method": str, "path": str, "client_ip": str}` |
| `server.response` | HTTP レスポンス送信 | `{"method": str, "path": str, "status_code": int, "client_ip": str}` |

**例：リクエストログ**

```python
@sdk.lifecycle.on("server.response")
def log_http(data):
    print(f"[HTTP] {data['method']} {data['path']} -> {data['status_code']}")
```

### WebSocket

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `server.start` | ルーター・サーバー起動 | `{"base_url": str, "host": str, "port": int}` |
| `server.stop` | ルーター・サーバー停止 | `{}` |
| `server.websocket.connect` | WebSocket 接続確立 | `{"path": str, "module_name": str, "client_ip": str}` |
| `server.websocket.disconnect` | WebSocket 接続切断 | `{"path": str, "module_name": str, "reason": str, "error": str(異常時のみ)}` |

**例：WebSocket 接続監視**

```python
@sdk.lifecycle.on("server.websocket.connect")
def on_ws_connect(data):
    print(f"[WS] 接続: {data['path']} from {data['client_ip']}")

@sdk.lifecycle.on("server.websocket.disconnect")
def on_ws_disconnect(data):
    print(f"[WS] 切断: {data['path']} ({data['reason']})")
```

## 標準イベント定義

```python
STANDARD_EVENTS = {
    "core": ["init.start", "init.complete", "uninit.complete"],
    "module": ["load", "init", "unload", "register"],
    "adapter": [
        "load", "start", "status.change", "stop", "stopped",
        "event.receive", "event.dispatched",
        "bot.online", "bot.offline",
    ],
    "server": [
        "start", "stop",
        "request", "response",
        "websocket.connect", "websocket.disconnect",
    ],
    "event": ["pre_process"],
    "message": ["sending", "sent"],
    "command": ["matched", "executed"],
    "config": ["set"],
}
```

## 完全な API リファレンス

### 登録とキャンセル

| メソッド | 説明 |
|------|------|
| `@lifecycle.on(event, *, priority=0)` | デコレータでハンドラーを登録 |
| `lifecycle.register(event, handler, *, priority=0)` | プログラマティック登録 |
| `lifecycle.unregister(event, handler=None)` | 登録解除（handler=None でそのイベントの全ハンドラーをキャンセル） |

### トリガー

| メソッド | 説明 |
|------|------|
| `await lifecycle.emit(event, data=None)` | 非同期トリガー、ハンドラーが非 None を返すと data が修正される |
| `lifecycle.emit_sync(event, data=None)` | 同期トリガー、非同期ハンドラーは create_task でスケジュールされる |
| `await lifecycle.submit_event(event_type, *, source, msg, data)` | 互換性のため、標準イベント形式を自動的に構築する |

### ユーティリティ

| メソッド | 説明 |
|------|------|
| `lifecycle.start_timer(timer_id)` | タイマー開始 |
| `lifecycle.get_duration(timer_id)` | 経過時間を取得（秒） |
| `lifecycle.stop_timer(timer_id)` | タイマー停止して経過時間を返す |
| `lifecycle.list_hooks()` | 登録済みフックとハンドラー数の一覧表示 |
| `lifecycle.clear()` | 全ハンドラーとタイマーをクリア |

## モジュールでの使用例

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    async def on_load(self, event):
        # シンプルなメッセージ統計の実装
        self.msg_count = 0
        
        @sdk.lifecycle.on("adapter.event.receive")
        async def count(data):
            if data["event_type"] == "message":
                self.msg_count += 1
        
        # すべてのコマンドを監視
        @sdk.lifecycle.on("command.matched")
        async def log_cmd(data):
            sdk.logger.info(f"コマンド実行: /{data['command']} by {data['user_id']}")
        
        # 設定変更監査
        @sdk.lifecycle.on("config.set")
        def audit(data):
            sdk.logger.info(f"設定変更: {data['key']} = {data['new_value']}")
```

## 注意事項

1. **ハンドラーは同期または非同期である可能性がある**：システムが自動的に識別して正しく呼び出します
2. **データの受け渡し**：`emit()` モードでは、ハンドラーが非 None の値を返すと、その値が後続のハンドラーに渡される data に適用されます
3. **イベント命名規則**：親イベントをリッスンしやすくするため、ドット構造でイベント名を付けることを推奨します
4. **エラーの隔離**：単一のハンドラーの例外は、他のハンドラーの実行には影響しません
5. **同期トリガーの制限**：`emit_sync()` 内で非同期ハンドラーは fire-and-forget 方式でスケジュールされ、返り値は受け取れません
6. **ライフサイクルのクリーンアップ**：`sdk.uninit()` を呼び出すと、すべての登録済みハンドラーとタイマーがクリアされます
7. **読み込み優先度**：フレームワークの初期化段階でイベントをリッスンする必要がある場合は、高優先度を設定し、レイジーロードを無効にすることを推奨します

## 関連ドキュメント

- [モジュール開発ガイド](../developer-guide/modules/getting-started.md) - モジュールライフサイクルメソッドを理解する
- [ベストプラクティス](../developer-guide/modules/best-practices.md) - ライフサイクルイベントの使用に関する推奨事項