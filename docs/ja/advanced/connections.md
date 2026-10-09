# 接続プールとブロードキャスト

ErisPulse における接続（サーバ側 WebSocket / SSE / クライアント出向 WebSocket）は**フレームワークレベルの一等リソース**です。接続が確立すると自動的に統一登録表に登録され、ブロードキャスト、業務グループサブスクリプション、モジュール間の渡し渡しや再利用が可能になります。モジュールのアンロード時にはフレームワークが自動的に接続を閉じて回収します。これにより、業務側が `_ws_clients` 集合を自前で作成する必要がなく、忘れずにクリーンアップすることでリソースリークを防げます。

> 本文ドキュメントの例はすべて**ルートインポート**の書き方を前提としています（2.10以降推奨）：
> `from ErisPulse import connections, router, client, WebSocketConnection`

## 概要

```python
from ErisPulse import connections, router, WebSocketConnection

# サーバ側：接続は自動登録され、ハンドラ内で業務グループに参加
@router.ws("MyModule", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")            # グループ名は業務側で自由に命名
    async for msg in ws.iter_text():
        ...                             # 接続が切断された際にはフレームワークが自動的に登録を解除し、グループをクリーンアップ

# 任意の位置で：グループにブロードキャスト（成功/失敗の詳細を返す）
result = await connections.broadcast({"type": "notify"}, group="room:1")
if not result.ok:
    ...                                 # result.failed: {接続ID: 例外}

```

3種類の接続はすべて登録表に統合されます：

| kind | 来源 | 归属 owner | 说明 |
|------|------|-----------|------|
| `server` | `@router.ws(...)` / `register_websocket(...)` | ルートを登録したモジュール名 | 接続切断時に自動的に登録を解除 |
| `sse` | `@router.sse(...)` / `register_sse(...)` | ルートを登録したモジュール名 | ブロードキャストは `sse.send()` を使用 |
| `client` | `await client.ws_connect(url)` | 現在のモジュール（または明示的な `owner=`） | 接続の閉じる、リモート切断時に自動的に登録を解除；アダプターが停止した際にはフレームワークが一括して閉じる |

自動登録を不要とする場合：ルートに `track=False` を渡すか、出向接続に `track=False` を渡すことで、従来のコードの挙動は完全に維持されます。

## 接続プールの確認

```python
from ErisPulse import connections

# 特定のモジュールの接続プールを確認（「現在、あるモジュールに何本の接続があるか」）
conns = connections.list(namespace="Dashboard")
for conn in conns:
    print(conn.id, conn.kind, conn.groups, conn.meta)

# その他の条件でフィルタリング（すべての条件がAND条件）
connections.list(owner="MyAdapter", kind="client")
connections.list(group="tenant:acme")

# 全体の統計情報（各条件のカウント）
stats = connections.stats()
# {'total': 5, 'by_kind': {...}, 'by_namespace': {...}, 'by_owner': {...}, 'groups': {...}}

# 所有権監査のカウント（ownership インターフェースでも確認可能）
from ErisPulse import ownership
ownership.counts("Dashboard")   # {'connections': 3, ...}
```

各接続は以下の識別情報を読み取ることができます：`conn.id`（例: `Dashboard:1a2b3c4d`）、`conn.namespace`、`conn.owner`、`conn.kind`、`conn.groups`、`conn.meta`（業務用の自由な辞書）。

## ブロードキャストとサブスクリプション

### グループ（サブスクリプションモデル）

グループは**フラットな文字列**であり、命名は完全に業務側の合意によって行われます（ルーム / テナント / トピックなど）。ネストされた階層は命名規則で表現します（例: `tenant:acme/room:1`）。フレームワークは形式を制限しません。

両方向から操作が可能です：

```python
# 方向1：接続側が参加/退出（ハンドラ内で）
@router.ws("Chat", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")        # 等価: connections.assign(ws.id, "room:1")
    ws.leave_group("room:1")

# 方向2：管理側が割り当て（ルート側 / 他のモジュール）
connections.assign(conn_id, "tenant:acme")
connections.dismiss(conn_id, "tenant:acme")   # グループ名を指定しない場合はすべてのグループから退出
```

接続が切断された際には、すべてのグループから自動的に退出し、業務側によるクリーンアップは不要です。

### ブロードキャスト

```python
result = await connections.broadcast(
    data,                       # WS は send_json を使用；SSE は send を使用（自動的にJSONシリアライズ）
    namespace="Dashboard",      # 名前空間でフィルタリング
    group="room:1",             # グループでフィルタリング
    kind="sse",                 # 接続の種類でフィルタリング
    owner="MyAdapter",          # 所有者でフィルタリング
    ids={conn_id, ...},         # 明示的に候補集を指定（フィルタ条件は依然有効）
    exclude={conn_id},          # 特定の接続を除外
    timeout=10.0,               # 単一接続の送信タイムアウト（トータルの時間ではなく）
    concurrency=64,             # 並列送信の上限
    raise_on_error=False,       # True の場合、失敗した項目があると最初の例外を送出
)
result.total      # 目標接続の総数（除外前に）
result.sent       # 成功した接続IDのリスト
result.failed     # {接続ID: 例外オブジェクト}（タイムアウト/切断済み/送信失敗）
result.excluded   # 除外された接続ID
result.ok         # 全て送信されたか
```

フィルタ条件は **AND** で処理されます。1件の失敗は他の接続への影響はありません。`ids` に存在しない接続は `failed` にカウントされ、業務側が状況を把握できるようにします。

### ライフサイクルイベント

接続の登録/登録解除/グループ変更は標準的なライフサイクルイベントとして発行され、Dashboard などのコンポーネントはサブスクライブしてリアルタイムに表示できます：

```python
from ErisPulse import lifecycle

@lifecycle.on("connection.registered")
async def on_registered(data): ...
@lifecycle.on("connection.unregistered")
async def on_unregistered(data): ...
@lifecycle.on("connection.group.joined")
async def on_joined(data): ...
@lifecycle.on("connection.group.left")
async def on_left(data): ...
```

## モジュール間の渡し渡し / 再利用

接続はフレームワークが登録したリソースであり、どのモジュールでも接続IDを使って取得して**再利用**できます。自前で新たな接続を作成する必要も、誰が接続を作成したかを知る必要もありません：

```python
from ErisPulse import connections

conn = connections.get("Dashboard:1a2b3c4d")   # 存在しない/切断済みの場合は ConnectionNotFoundError を送出
await conn.send_json({"ping": 1})              # どのモジュールからでも送信可能
conn.join_group("someone-elses-room")          # グループ参加も可能
```

**所有権と閉じる権限**：

- 接続の `owner`（作成したモジュール）は、閉じる権限を独占します。非 owner が `close()` を呼び出すと `ConnectionPermissionError`（`from ErisPulse import ConnectionPermissionError`）が送出されます；
- 送信やグループ操作は、どのモジュールからでも許可なく実行可能です；
- owner モジュールのアンロード / アダプターの停止時に、フレームワークは**一括して閉じて登録を解除**します（サーバ側 + 出向接続）。取得した参照で送信を試みても失敗結果が返り、`connection.unregistered` イベントを監視することで感知できます；
- フレームワーク内部のリソース回収には `close(force=True)` を使用して検証を回避します。

> 説明：閉じる権限の検証は、実行時の owner コンテキスト（`owner_scope` / イベント配信 / `spawn_background` など）に依存します。コンテキストが不明な呼び出し（古いコードなど）は許可され、破壊的な影響をゼロに保ちます。新しいコードでは、owner コンテキスト内で呼び出すことで保護されます。

## 出向接続（クライアント側）

```python
from ErisPulse import client

ws = await client.ws_connect("wss://example.com/ws")
ws.id          # 登録済みで、connections で検索/ブロードキャストが可能
ws.owner       # 現在のモジュール（owner コンテキストが利用できない場合は明示的に指定）

# owner コンテキストが利用できない場合（例：ツールスレッドのコールバック）は明示的に指定し、アンロード時に自動回収されます：
ws = await client.ws_connect("wss://example.com/ws", owner="MyAdapter")
```

リモート側が切断した場合、またはローカルで `close()` を呼び出した場合、自動的に登録を解除します。モジュールのアンロード時には、フレームワークがその名下のすべての出向接続を閉じます。これにより、従来のコードで接続を自前で管理し忘れることによるリソースリークはなくなりました。

## スレッド間の投递

子スレッドから接続にアクセスする場合（ブロードキャスト / プッシュ / 閉じる）には、フレームワークの標準的なツールを使ってメインループに投递してください。**`run_coroutine_threadsafe` を手書きで使用しないでください**：

```python
from ErisPulse import run_main_loop, spawn_later, spawn_thread

# 子スレッドでブロックして結果を取得：
run_main_loop(connections.broadcast({"tick": 1}, group="room:1"), timeout=5)

# バックグラウンドスレッド + 遅延タスク（所有権の割り当て、アンロード時に自動キャンセル）：
def push_tick():
    return connections.broadcast({"tick": 1}, group="room:1")
spawn_later(30, push_tick, owner="MyModule")
```

## アンロードとクリーンアップの意味

モジュールのアンロード / アダプターの停止時の所有権回収の流れは次のように進行します：所属するバックグラウンドタスクやタイマーのキャンセル → **所属する接続の閉じて登録を解除** → `on_cleanup` フックの呼び出し → ルート/ハンドラなどの登録済みリソースの登録解除。詳細は [所有権（owner）システム](ownership.md) を参照してください。

> [!WARNING]
> 2.10以降、モジュールのアンロード時に登録された WS/SSE/出向接続が閉じられます。アンロード後に接続が生き続けることを依存している下流コンポーネント（例：旧バージョンの Dashboard プッシュ）は、これはリソースリークを防ぐ意図的な挙動であることを認識する必要があります。

## API 一覧

| API | 说明 |
|-----|------|
| `connections.get(id)` | 接続を取得（モジュール間のエントリーポイント）、存在しない場合は `ConnectionNotFoundError` を送出 |
| `connections.list(namespace=, owner=, group=, kind=)` | 接続のリストをフィルタリングして取得 |
| `connections.stats(namespace=, owner=)` | 各条件のカウント統計 |
| `connections.assign(id, *groups)` / `dismiss(id, *groups)` | 管理側によるグループ参加/退出 |
| `await connections.broadcast(data, ...)` | ブロードキャスト、`BroadcastResult` を返す |
| `await connections.close(id, force=False)` | 閉じて登録を解除（権限チェックあり） |
| `await connections.close_owner(owner)` | 指定 owner 名下のすべての接続を閉じて登録を解除（フレームワークのアンロードチェーンで呼び出される） |
| `conn.join_group(*groups)` / `conn.leave_group(*groups)` | 接続側によるグループ参加/退出 |
| `conn.send_json / send_text / iter_text / ...` | 受信/送信（サーバ側/クライアント側のインターフェースは同一） |
| `conn.meta` | 業務用メタデータ辞書 |
| `conn.close(force=False)` | 閉じる（非 owner は `ConnectionPermissionError` を送出） |