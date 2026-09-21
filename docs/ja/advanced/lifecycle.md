# ライフサイクル管理

ErisPulse は、システム各コンポーネントの実行状態を監視し、監査、統計、カスタムロジックなどの拡張機能を実現するための統一されたフック/ライフサイクルシステムを提供しています。

システムは以下の3種類のトリガ方法をサポートしています：
- `await lifecycle.emit("event", data)` — 精簡版、任意のデータを渡す（`to="Owner"` の場合、特定の宛先に投送）
- `lifecycle.emit_sync("event", data)` — 同期版（非非同期コンテキスト用）
- `await lifecycle.submit_event("event", ...)` — 旧版との互換性、標準イベント形式を自動構築

## イベント処理メカニズム

### ハンドラの登録

```python
from ErisPulse import sdk

# デコレータ形式
@sdk.lifecycle.on("module.load")
async def on_module_load(data):
    print(f"モジュールのロード: {data}")

# プログラム的登録
sdk.lifecycle.register("module.load", on_module_load, priority=10)

# 登録解除
sdk.lifecycle.unregister("module.load", on_module_load)

# 所有者ごとの一括登録解除（モジュール/アダプタのアンロード時にフレームワークが自動的に呼び出す）
removed = sdk.lifecycle.unregister_by_owner("MyModule")
print(f"クリーンアップされたライフサイクルフック数: {removed}")
```

### 優先度

ハンドラは `priority` パラメータをサポートし、数値が大きいほど先に実行されます（モジュールローダーと同様）：

```python
@sdk.lifecycle.on("adapter.event.receive", priority=10)  # 最初に実行
async def first_handler(data):
    pass

@sdk.lifecycle.on("adapter.event.receive", priority=0)  # 後に実行
async def second_handler(data):
    pass
```

### 点構造イベント

特定のイベントをトリガすると、その親イベントもトリガされます：
- `module.load` をトリガすると、`module` もトリガされます。
- `adapter.event.receive` をトリガすると、`adapter.event` と `adapter` もトリガされます。

### ワイルドカード

`*` を登録すると、すべてのイベントをキャッチできます：

```python
@sdk.lifecycle.on("*")
async def on_anything(data):
    print(f"イベント受信: {data}")
```

### 定向配信（emit to=）

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要です。

`emit()` で `to` パラメータを指定すると、定向配信モードになります：イベントは、その所有者（owner）として登録されたハンドラにのみ配信されます（モジュールは `on_load` 内で登録されたフックは自動的に自身の所有者として登録されます）。他のモジュールやワイルドカード `*` ハンドラはイベントを感知しません。

```python
# 投递側：イベントは Chat モジュールが登録したハンドラにのみ投递
await sdk.lifecycle.emit("message_received", {"text": "hi"}, to="Chat")

# 訂正側（Chat モジュール内）：同名のハンドラを登録し、owner は登録時に自動的に記録されます
@sdk.lifecycle.on("message_received")
async def on_message_received(data): ...

@sdk.lifecycle.on("message")   # 点構造の親プレフィックスも同様に効きます（owner でフィルタリング）
async def on_any(data): ...
```

- 目標の owner に登録されたハンドラがない場合 → イベントは**静かに破棄**されます（`has_handlers()` で事前に検出可能です）。
- `data` が dict の場合、自動的に `_trace_id` を付与します（既存値を上書きしません）。
- `emit_sync` / `submit_event` も `to=` パラメータをサポートしています。
- モジュール間通信の3層モデル（RPC / 定向 / ブロードキャスト）については、[モジュール間通信](module-communication.md)を参照してください。

### 一回限りの登録（once）

2.7.0 から、`lifecycle.once()` で登録されたハンドラは**一度トリガされた後、自動的に登録解除**されます。これは「最初の準備完了」のような一回限りのフックに適しています。

```python
@sdk.lifecycle.once("core.init.complete")
async def on_first_ready(data):
    print("最初の準備完了、以降はトリガされません")
```

- `on()` と同じ優先度パラメータの意味（`priority` 数値が大きいほど先に実行されます）。
- 自動的に登録解除され、手動での `unregister` は不要です。
- 同期/非同期のハンドラが両方サポートされています。

### 監視者検索（has_handlers）

ホットパスの短絡処理では、`has_handlers()` を使って監視者が存在するか事前に判断し、不要なイベントのループやタスクのスケジューリングを避けることができます。

```python
if sdk.lifecycle.has_handlers("message.sending"):
    await sdk.lifecycle.emit("message.sending", send_ctx)
```

- **正確なイベント名、ワイルドカード `*`、親イベント**の3つのマッチングをカバーしています。
- 監視者がいない場合、`False` を返し、`emit` を安全にスキップできます。

## フックブレークポイント一覧

プラットフォームからフレームワークにメッセージが届き、処理が完了する典型的なライフサイクルイベントの順序：

```mermaid
sequenceDiagram
    participant P as プラットフォーム
    participant A as アダプタ
    participant F as フレームワークコア
    participant M as モジュールハンドラ

    P->>A: ネイティブイベント到着
    A->>F: adapter.event.receive（初期段階）
    F->>F: event.pre_process（ハンドラ実行前）
    F->>M: ハンドラに配分（コマンド/メッセージ/通知など）
    M->>M: command.matched / command.executed
    M->>F: event.reply()
    F->>F: message.sending（送信前）
    F->>A: SendDSL で送信
    A->>P: プラットフォームに送信
    A->>F: message.sent（送信完了）
    F->>F: adapter.event.dispatched（配分完了）
```

フレームワークは以下のフックブレークポイントを内蔵しており、ユーザーは `@sdk.lifecycle.on()` で任意のブレークポイントを監視してカスタムロジックを実装できます。

### コア初期化

| フック名 | トリガタイミング | データ |
|---------|---------|------|
| `core.init.start` | SDK 初期化開始 | `{}` |
| `core.init.stage` | 初期化各段階開始（バックグラウンドで発行） | `{"stage": str}`、値は `discovery` / `adapter_register` / `adapter_start` / `module_register` / `module_init` / `adapter_start_deferred` / `router_start` |
| `core.init.complete` | SDK 初期化完了 | `{"duration": float, "success": bool, "stages": {stage: float}, "adapters": {"enabled": [str], "disabled": [str]}, "modules": {"enabled": [str], "disabled": [str]}, "error": str(失敗時のみ)}` |
| `core.uninit.complete` | SDK 反初期化完了 | `{"duration": float, "success": bool, "adapters_closed": int, "modules_unloaded": int, "module_properties_cleared": int, "module_properties_to_clear": [str], "error": str(失敗時のみ)}` |

**例：起動進捗表示**

```python
@sdk.lifecycle.on("core.init.stage")
def show_stage(data):
    print(f"[起動] 階段に進入: {data['stage']}")
```

### 設定変更

| フック名 | トリガタイミング | データ |
|---------|---------|------|
| `config.set` | 設定項目が変更された | `{"key": str, "old_value": Any, "new_value": Any}` |
| `config.updated` | 外部で config.toml を編集した後に木全体の変更を検出 | `{"old_config": dict, "new_config": dict, "config_file": str}` |

**例：設定監査**

```python
@sdk.lifecycle.on("config.set")
def audit_config(data):
    print(f"[監査] {data['key']}: {data['old_value']} -> {data['new_value']}")
```

### モジュールライフサイクル

| フック名 | トリガタイミング | データ |
|---------|---------|------|
| `module.register` | モジュールクラスがマネージャーに登録された | `{"module_name": str, "success": bool}` |
| `module.load` | モジュールのロードが完了した（インスタンス化成功） | `{"module_name": str, "success": bool}` |
| `module.init` | モジュールの初期化が完了した（遅延ロード含む） | `{"module_name": str, "success": bool}` |
| `module.unload` | モジュールのアンロード | `{"module_name": str, "success": bool}` |
| `module.reload` | モジュールのホットリロードが完了した（依存モジュールの再ロード含む） | `{"module_name": str, "success": bool}` |

### アダプタライフサイクル

| フック名 | トリガタイミング | データ |
|---------|---------|------|
| `adapter.load` | アダプタの登録が完了した | `{"platform": str, "success": bool}` |
| `adapter.start` | アダプタの起動 | `{"platforms": [str]}` |
| `adapter.status.change` | アダプタのステータスが変化した | `{"platform": str, "status": str, "retry_count": int, "error": str(失敗時のみ)}` |
| `adapter.stop` | アダプタの停止 | `{"platforms": [str]}` |
| `adapter.stopped` | アダプタの停止が完了した | `{"platforms": [str]}` |
| `adapter.bot.online` | Bot のオンライン | `{"platform": str, "bot_id": str, "info": dict, "status": str}` |
| `adapter.bot.offline` | Bot のオフライン | `{"platform": str, "bot_id": str, "status": str}` |

### イベント受信と処理

| フック名 | トリガタイミング | データ |
|---------|---------|------|
| `adapter.event.receive` | 外部プラットフォームイベントを受信した（初期段階） | `{"platform": str, "event_type": str, "raw_event_type": str}` |
| `adapter.event.blocked` | ミドルウェアがイベントを拒否した（`False` を返した場合、イベントは処理されず破棄される） | `{"middleware": str, "platform": str, "event_type": str, "detail_type": str, "event": dict, "_trace_id": str}` |
| `adapter.event.dispatched` | イベントの配分が完了した | `{"platform": str, "event_type": str, "raw_event_type": str, "onebot_handlers_count": int}` |
| `event.pre_process` | イベントハンドラが実行される前に | `{"event_type": str, "platform": str, "detail_type": str}` |

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

| フック名 | トリガタイミング | データ |
|---------|---------|------|
| `message.sending` | メッセージが送信される直前 | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |
| `message.sent` | メッセージの送信が完了した | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |

**例：メッセージ送信監査**

```python
@sdk.lifecycle.on("message.sending")
def log_sending(data):
    print(f"[送信] -> {data['platform']}/{data['detail_type']}/{data['target_id']} via {data['method']}")
```

### コマンドシステム

| フック名 | トリガタイミング | データ |
|---------|---------|------|
| `command.matched` | コマンドがマッチし、実行される直前 | `{"command": str, "args": list[str], "platform": str, "user_id": str}` |
| `command.executed` | コマンドの実行が完了した | `{"command": str, "args": list[str], "platform": str, "user_id": str, "success": bool, "error": str(失敗時のみ)}` |

**例：コマンド統計**

```python
@sdk.lifecycle.on("command.matched")
def count_commands(data):
    print(f"[コマンド] /{data['command']} from {data['user_id']}@{data['platform']}")
```

### HTTP ルーティング

| フック名 | トリガタイミング | データ |
|---------|---------|------|
| `server.request` | HTTP リクエストを受け取った | `{"method": str, "path": str, "client_ip": str}` |
| `server.response` | HTTP レスポンスを送信した | `{"method": str, "path": str, "status_code": int, "client_ip": str}` |

**例：リクエストログ**

```python
@sdk.lifecycle.on("server.response")
def log_http(data):
    print(f"[HTTP] {data['method']} {data['path']} -> {data['status_code']}")
```

### WebSocket

| フック名 | トリガタイミング | データ |
|---------|---------|------|
| `server.start` | ルーティングサーバーの起動 | `{"base_url": str, "host": str, "port": int, "success": bool, "error": str(失敗時のみ)}` |
| `server.stop` | ルーティングサーバーの停止 | `{}` |
| `server.websocket.connect` | WebSocket 接続が確立した | `{"path": str, "module_name": str, "client_ip": str}` |
| `server.websocket.disconnect` | WebSocket 接続が切断した | `{"path": str, "module_name": str, "reason": str, "error": str(異常時のみ)}` |

**例：WebSocket 接続監視**

```python
@sdk.lifecycle.on("server.websocket.connect")
def on_ws_connect(data):
    print(f"[WS] 接続: {data['path']} from {data['client_ip']}")

@sdk.lifecycle.on("server.websocket.disconnect")
def on_ws_disconnect(data):
    print(f"[WS] 切断: {data['path']} ({data['reason']})")
```

### ストレージ接続状態

ストレージバックエンドの接続プールの確立、障害、および回復（すべてバックグラウンドで発行され、ストレージ操作をブロックしません）：

| フック名 | トリガタイミング | データ |
|---------|---------|------|
| `storage.ready` | ストレージバックエンドの接続プールが準備完了（各イベントループで最初にプールが成功した場合） | `{"backend": str}` |
| `storage.unreachable` | 接続リトライが尽きてクールダウン期間に入る（この間、操作は即時失敗する） | `{"backend": str, "error": str, "cooldown": float}` |
| `storage.recovered` | クールダウンが終了し、再接続に成功し、ストレージが再利用可能になった | `{"backend": str}` |

**例：ストレージ障害アラート**

```python
@sdk.lifecycle.on("storage.unreachable")
def alert_storage_down(data):
    print(f"[アラート] ストレージバックエンド {data['backend']} が利用不可: {data['error']}、{data['cooldown']}s 後に自動再接続")

@sdk.lifecycle.on("storage.recovered")
def notify_storage_back(data):
    print(f"[回復] ストレージバックエンド {data['backend']} が再利用可能になりました")
```

### HTTP クライアント

`sdk.client` のリクエストと接続イベント（すべてバックグラウンドで発行）：

| フック名 | トリガタイミング | データ |
|---------|---------|------|
| `client.request.success` | HTTP リクエストが成功した | `{"method": str, "url": str, "status": int, "elapsed": float}` |
| `client.request.failed` | HTTP リクエストがリトライを尽して最終的に失敗した | `{"method": str, "url": str, "error": str, "attempts": int, "elapsed": float}` |
| `client.ws.connect` | WebSocket 接続が確立した | `{"url": str}` |

### 国際化

| フック名 | トリガタイミング | データ |
|---------|---------|------|
| `i18n.language.changed` | フレームワークの言語が切り替わった（`i18n.set_language`） | `{"language": str, "previous": str}` |

## 標準イベント定義

```python
STANDARD_EVENTS = {
    "core": ["init.start", "init.stage", "init.complete", "uninit.complete"],
    "module": ["load", "init", "unload", "register", "reload"],
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
    "config": ["set", "updated"],
    "storage": ["ready", "unreachable", "recovered"],
    "client": ["request.success", "request.failed", "ws.connect"],
    "i18n": ["language.changed"],
}
```

## 完全な API リファレンス

### 登録と解除

| メソッド | 説明 |
|------|------|
| `@lifecycle.on(event, *, priority=0)` | デコレータでハンドラを登録します |
| `lifecycle.register(event, handler, *, priority=0)` | プログラム的に登録します |
| `lifecycle.unregister(event, handler=None)` | ハンドラの登録を解除します（handler=None の場合、該当イベントのすべてのハンドラを解除します） |

### トリガ

| メソッド | 説明 |
|------|------|
| `await lifecycle.emit(event, data=None, *, to=None)` | 非同期でトリガします。ハンドラは**並列実行**されます（互いにブロックせず、返却時にすべて完了）。返り値が None でない場合は、優先度順に data が置き換えられます。`to` で owner を指定すると、宛先に投げられます。 |
| `lifecycle.fire(event, data=None, *, to=None)` | **バックグラウンドで発行（投げた後は即座に終了）**：ハンドラはバックグラウンドタスクで並列実行され、待機せず、返り値もありません。ハンドラがいない場合、オーバーヘッドはゼロです。高頻度のホットパスや純粋な観測イベントに適しています。シャットダウンシーケンスや順序に敏感な消費（例：`config.set`）は `emit` を使用してください。 |
| `lifecycle.emit_sync(event, data=None, *, to=None)` | 同期でトリガします。非同期ハンドラは create_task でスケジュールされます。 |
| `await lifecycle.submit_event(event_type, *, source, msg, data, to=None, background=False)` | 旧版との互換性のために、標準イベント形式を自動的に構築します。`background=True` の場合、`fire` でバックグラウンドで発行されます。 |

### ユーティリティ

| メソッド | 説明 |
|------|------|
| `lifecycle.start_timer(timer_id)` | タイマーを開始します。 |
| `lifecycle.get_duration(timer_id)` | 経過時間を取得します（秒）。 |
| `lifecycle.stop_timer(timer_id)` | タイマーを停止し、経過時間を返します。 |
| `lifecycle.list_hooks()` | すべての登録されたフックとハンドラ数をリストアップします。 |
| `lifecycle.clear()` | すべてのハンドラとタイマーをクリアします。 |

## モジュールでの使用例

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    async def on_load(self, event):
        # 簡単なメッセージ統計を実装
        self.msg_count = 0
        
        @sdk.lifecycle.on("adapter.event.receive")
        async def count(data):
            if data["event_type"] == "message":
                self.msg_count += 1
        
        # すべてのコマンドを監視
        @sdk.lifecycle.on("command.matched")
        async def log_cmd(data):
            sdk.logger.info(f"コマンド実行: /{data['command']} by {data['user_id']}")
        
        # 設定変更の監査
        @sdk.lifecycle.on("config.set")
        def audit(data):
            sdk.logger.info(f"設定変更: {data['key']} = {data['new_value']}")
```

## バックグラウンドタスクの所有者と自動キャンセル

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要です。

モジュールが作成した asyncio バックグラウンドタスクが `on_unload` でキャンセルされない場合、`self` の参照が保持され、モジュールインスタンスが回収されず（ホットリロード後に古いインスタンスが残る）。フレームワークは以下のバックアップメカニズムを提供しています：

- **`self.spawn(coro)`**（モジュール内推奨）：タスクはモジュール名に自動的に所有者として登録され、モジュールのアンロード時にフレームワークが `on_unload` **後に**未終了のタスクをバックアップでキャンセルし、警告を記録します。
- **`spawn_background(coro)`**（`ErisPulse.runtime`）：自動的に現在の `owner_scope` コンテキストをキャプチャします。`cancel_owner_tasks(owner)` で所有者ごとにキャンセルし、`cancel_all_background_tasks()` は `sdk.uninit()` のバックアップで使用します。
- **アダプタ**：プラットフォーム名の下のバックグラウンドタスクも同様にバックアップでキャンセルされます。

```python
async def on_load(self, event):
    # 推奨：バックグラウンドタスクは self.spawn() を使用し、アンロード時にフレームワークがバックアップでキャンセルします
    self.spawn(self._poll())

async def on_unload(self, event):
    # 精密制御の場合は、明示的にキャンセルして終了を待つ必要があります
    if self._poll_task:
        self._poll_task.cancel()
        await asyncio.gather(self._poll_task, return_exceptions=True)

async def _poll(self):
    while True:
        await asyncio.sleep(60)
        ...
```

> [!IMPORTANT]
> フレームワークのバックアップは**強制キャンセル**（`cancel_owner_tasks`）です。これは `on_unload` の返り値の後に実行されます。そのため、優雅な終了が必要なタスク（バッファのフラッシュ、状態の永続化、接続の閉じる）は、`on_unload` で明示的に `cancel()` + `await` する必要があります——バックアップが終了ロジックを保持することを期待しないでください。フレームワークは「`self` を保持するタスクが残らない」ことを保証しますが、「優雅」を保証するわけではありません。`await` の結果が必要なタスクは直接 `await` し、バックグラウンドタスクに投げないでください。

## 注意事項

1. **ハンドラは同期または非同期**：システムは自動的に正しく呼び出します。
2. **データの渡し方**：`emit()` モードでは、ハンドラが None 以外の値を返すと、後続のハンドラに渡される data が変更されます。
3. **イベント名の命名規則**：点構造の命名を推奨し、親イベントの監視がしやすくなります。
4. **エラーの隔離**：個々のハンドラの例外は他のハンドラの実行に影響しません。
5. **同期トリガの制限**：`emit_sync()` では、非同期ハンドラは fire-and-forget でスケジュールされ、返り値は戻されません。
6. **ライフサイクルのクリーンアップ**：`sdk.uninit()` を呼び出すと、すべての登録されたハンドラとタイマーがクリーンアップされます。
7. **ロード優先性**：フレームワークの初期化段階でイベントを監視したい場合は、高優先度を設定し、遅延ロードを無効にすることを推奨します。

## 関連ドキュメント

- [モジュール開発ガイド](../developer-guide/modules/getting-started.md) - モジュールのライフサイクルメソッドについて学ぶ
- [ベストプラクティス](../developer-guide/modules/best-practices.md) - ライフサイクルイベントの使用に関する推奨事項