# エラー体系とキャッチガイド

> [!NOTE]
> **L1 必読**——「読むべき順」の5つのコアドキュメントの1つ、モジュール開発に必須。

ErisPulse におけるすべてのカスタムエラーは `ErisPulseError` を継承しており、aiohttp、aiomysql などのライブラリのエラーは、フレームワーク内部で ErisPulse エラーに変換されます。業務コードは**下層ライブラリのエラー型に依存する必要はありません**。

{!--< tips >!--}
1. 広範囲にキャッチしたい場合：`ErisPulseError` をキャッチ（すべてのフレームワークエラーの基底クラス）
2. 精度よく処理したい場合：モジュールごとにキャッチ（例：`ModuleCallTimeoutError`、`StorageUnreachableError`）
3. ストレージ操作はデフォルトでエラーを送出しない：失敗時はログを記録し、`False / None / default` を返す。接続状態の変化は `storage.unreachable` / `storage.recovered` イベントをサブスクライブ
{!--< /tips >!--}

## エラー一覧

```text
ErisPulseError                      # すべてのフレームワークエラーの基底クラス
├── ClientError                     # HTTP/WS クライアントリクエストエラーの基底クラス（Core/client）
│   ├── ClientConnectionError       # 接続層エラー：DNS 解析失敗、接続拒否、ネットワーク不可達
│   ├── ClientTimeoutError          # リクエストタイムアウト
│   └── HTTPStatusError             # HTTP ステータスコードエラー（4xx/5xx で raise_for_status が発動）
├── WebSocketError                  # WebSocket エラーの基底クラス（Core/client の WS 接続）
│   └── WebSocketDisconnect         # WebSocket 接続切断（サーバー/クライアント共通）
├── ConnectionRegistryError         # 接続レジストリエラーの基底クラス（Core/connections、2.10+）
│   ├── ConnectionNotFoundError     # 接続が存在しない/既に切断・登録解除（connections.get/close）
│   └── ConnectionPermissionError   # 所有者以外が他人の接続を閉じる（閉じる権限は作成者に帰属）
├── StorageError                    # ストレージエラーの基底クラス（Core/storage）
│   └── StorageUnreachableError     # ストレージバックエンドが不可達（プール作成時のリトライが尽きた：データベース不可達/認証情報エラー）
├── InteractionError                # 交互会話エラーの基底クラス（Core/Event/interaction）
│   ├── InteractionCancelled        # 保留中の待機/リースがキャンセルされた（wait_reply が上層で None に変換）
│   └── SessionOccupiedError        # 会話の排他リースが占有された（hold() で取得失敗）
├── ModuleError                     # モジュールシステムエラーの基底クラス（Core/module）
│   └── ModuleCallError             # モジュール間呼び出しエラーの基底クラス
│       ├── ModuleNotAvailableError # 目標モジュールが登録されていない/有効化されていない/初期化失敗（遅延ロードアクセス含む）
│       ├── ServiceNotProvidedError # 目標モジュールが該当サービスを宣言していない（meta.services ホワイトリスト外）
│       └── ModuleCallTimeoutError  # 被呼び出しメソッドがタイムアウト（デフォルト 30s）
├── ShadowError                     # シャドウモジュールエラーの基底クラス（Core/shadow）
│   ├── ShadowStateError            # 状態が満たされない：目標がロードされていない/既にアクティブなシャドウがある/シャドウがバインドされていない（start/dismiss）
│   ├── ShadowSourceError           # シャドウソースが利用できない：パスが存在しない/ローダーが欠落/ロード失敗（start）
│   └── ShadowPromoteError          # 転正失敗：シャドウが登録されていない/ロードされていない/ローダーにスナップショットがない/再ロード失敗（promote）
└── StrictModeError                 # 厳格モードの致命的違反（起動プロセスを中止、loaders/strict）
```

## 構造化属性

エラーをキャッチした後、構造化された属性を読み取ることができます（エラーメッセージの解析は不要）。

| エラー | 属性 |
|------|------|
| `ClientError`（含むサブクラス） | `.url` リクエスト URL、`.method` リクエストメソッド、`.attempts` 既に試行した回数（リトライが尽きた場合） |
| `HTTPStatusError` | `.status` ステータスコード、`.message` レスポンスメッセージ |
| `WebSocketDisconnect` | `.code` 閉じコード、`.reason` 閉じ理由 |
| `ConnectionNotFoundError` | `.connection_id` 検索した接続 ID |
| `ConnectionPermissionError` | `.connection_id` 目標接続 ID、`.owner` 接続の所有者 |
| `StorageUnreachableError` | `.backend` バックエンド名（sqlite/mysql/postgres）、`.cooldown` コoldown 秒数 |
| `ModuleCallError`（含むサブクラス） | `.module` 目標モジュール名、`.method` 目標メソッド名 |
| `ModuleCallTimeoutError` | `.module/.method` を継承、さらに `.timeout` タイムアウト制限（秒） |
| `InteractionCancelled` | `.reason` キャンセル理由、`.wait_key` 会話キー |
| `SessionOccupiedError` | `.wait_key` 会話キー、`.owner` 占用者 |
| `StrictModeError` | `.violations` 違反記録リスト |

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await sdk.client.post(url, json=payload)
except ClientError as e:
    print(f"リクエスト失敗 {e.method} {e.url}、合計 {e.attempts} 回試行: {e}")
```

## 各エラーの説明と発生場所

### Client シリーズ — `Core/client.py` / `Core/Bases/client.py`

`sdk.client` / HTTP クライアントと WebSocket クライアントがリクエストを発行する際に発生：

| エラー | 発生場所 | 代表的なシナリオ |
|------|----------|----------|
| `ClientError` | リクエストのラッパー層 | 他のクライアントエラー（aiohttp のエラーは変換済み） |
| `ClientConnectionError` | 接続確立段階 | 目標サービスが不可達、DNS 失敗、接続拒否 |
| `ClientTimeoutError` | リクエスト実行段階 | リクエストタイムアウト時間を超過 |
| `HTTPStatusError` | `raise_for_status()` | レスポンスステータスコードが 4xx/5xx |

```python
from ErisPulse.Core.Bases.errors import ClientTimeoutError

try:
    resp = await sdk.client.get("https://api.example.com", timeout=5)
except ClientTimeoutError:
    ...
```

### WebSocket シリーズ — `Core/client.py`（`send` / `receive`）

| エラー | 発生場所 | 代表的なシナリオ |
|------|----------|----------|
| `WebSocketError` | WS 送受信メソッド | 接続が閉じられている、想定外のメッセージタイプを受け取った、下層の WS エラー |
| `WebSocketDisconnect` | WS 送受信メソッド | 対向が正常に接続を切断した（フレームワークが自動的に再接続） |

### 接続レジストリシリーズ — `Core/connections.py`（2.10+）

| エラー | 発生場所 | 代表的なシナリオ |
|------|----------|----------|
| `ConnectionNotFoundError` | `connections.get` / `assign` / `dismiss` / `close` | 接続 ID が存在しない、または既に切断・登録解除されている |
| `ConnectionPermissionError` | 非所有者が `conn.close()` を呼び出す | 跨モジュールで他人の接続を閉じる（送信とグループ分けは制限されない） |

### Storage シリーズ — `Core/storage` / `Core/Bases/sql_base.py`

| エラー | 発生場所 | 代表的なシナリオ |
|------|----------|----------|
| `StorageError` | ストレージ層 | ストレージ関連のエラーの基底クラス |
| `StorageUnreachableError` | プール作成段階 | データベースが不可達 / 認証情報エラー / ネットワーク隔離、リトライが尽きた |

> **ストレージ操作の失敗の意味**：KV およびクエリ操作は**デフォルトでエラーを送出しない**——失敗時は ERROR ログを記録し、`False` / `None` / `default` を返す（接続問題がフレームワークの実行をブロックしないように）。したがって、通常の業務コードでは `StorageUnreachableError` をキャッチすることは**ない**（ストレージの低レベル操作やカスタムバックエンドに使用される）。実行時の接続状態の感知は、ライフサイクルイベント `storage.unreachable` / `storage.recovered` をサブスクライブすること（[ライフサイクルイベント](lifecycle.md#ストレージ接続状態)を参照）。

接続失敗の挙動は[ストレージバックエンド → 接続失敗の挙動](storage-backends.md#接続失敗の挙動)を参照。

### Interaction — `Core/Event/interaction.py`

`wait_reply` / 会話リース / アラームタイマー関連：

| エラー | 発生場所 | 代表的なシナリオ |
|------|----------|----------|
| `InteractionError` | 交互会話層 | 交互会話エラーの基底クラス |
| `InteractionCancelled` | 保留中の待機がキャンセルされた時 | キャンセルされた待機 future に設定される（待機側がキャッチして `.reason` を取得できる） |
| `SessionOccupiedError` | `hold()` リース取得失敗 | 会話が他の所有者に占有されている（`.owner` で占有者を確認可能） |

キャンセルされた場合（モジュールのアンロード / プラットフォームの停止 / 同会話の新しい待機が上書き）は、`wait_reply` はエラーを送出せず、`None` を返す（`InteractionCancelled` は内部で変換される）。キャンセルの理由を区別したい場合は、直接キャッチする。

### Module シリーズ — `Core/module.py`（`sdk.module.call`）

| エラー | 発生場所 | 代表的なシナリオ |
|------|----------|----------|
| `ModuleError` | モジュールシステム | モジュールシステムのエラーの基底クラス |
| `ModuleCallError` | `module.call()` | モジュール間呼び出しのエラーの基底クラス |
| `ModuleNotAvailableError` | `module.call()` / 遅延ロード属性アクセス | 目標が登録されていない / 有効化されていない / 初期化失敗 |
| `ServiceNotProvidedError` | `module.call()` | 目標の `meta.services` ホワイトリストに該当メソッドが宣言されていない |
| `ModuleCallTimeoutError` | `module.call()` | 被呼び出しコルーチンがタイムアウト時間（デフォルト 30s）を超えた |

「目標モジュールが利用できない」の異なるアクセス経路でのエラーの種類：

| アクセス経路 | エラー |
|----------|------|
| `await sdk.module.call("X", "method")` | `ModuleNotAvailableError`（型付き） |
| `sdk.module.X.attr`（初期化失敗後の遅延ロード属性アクセス） | `ModuleNotAvailableError` |
| `sdk.module.X`（モジュールが有効化されていないときの属性アクセス） | `AttributeError`（Python の属性の慣習、`hasattr` はこの意味に依存） |

```python
from ErisPulse.Core.Bases.errors import ModuleNotAvailableError, ServiceNotProvidedError

try:
    history = await sdk.module.call("Chat", "get_history", session_id, n=20)
except ModuleNotAvailableError:
    ...  # 目標モジュールが存在しない / 有効化されていない
except ServiceNotProvidedError:
    ...  # 目標モジュールが該当サービスを提供していない
```

### Shadow シリーズ — `Core/shadow.py`（シャドウモジュール）

| エラー | 発生場所 | 代表的なシナリオ |
|------|----------|----------|
| `ShadowError` | シャドウモジュールメカニズム | シャドウエラーの基底クラス（すべてのシャドウエラーを一括キャッチ） |
| `ShadowStateError` | `shadow_start()` / `dismiss_shadow()` | 目標がロードされていない / 既にアクティブなシャドウがある / シャドウがバインドされていない |
| `ShadowSourceError` | `shadow_start()` | ソースパスが存在しない / プラグインローダーが欠落 / ソースからロード可能なクラスがない / 装載失敗 |
| `ShadowPromoteError` | `promote_shadow()` | シャドウが登録されていない / 未ロード / 加工ローダーがスナップショットをサポートしていない / 転正後の再ロード失敗 |

### フレームワーク内部のパラメータ検証（ValueError）

ストレージクエリビルダーのパラメータ検証（空の列タイプ、`Insert` が dict でない、不安全な列タイプなど）は標準の `ValueError` を送出する——これは**開発期のコードエラー**であり、通常の業務コードではキャッチすべきではなく、呼び出しを修正すべきである。

アダプタの標準アクションが失敗してもエラーを送出しない：`retcode` を持つレスポンス辞書を返す（プロトコルの意味、例：`retcode=10002` はアクションが実装されていないことを意味する）——これは client 層の「失敗時に `ClientError` を送出する」と並行するエラーのチャネルであり、アダプタの開発時には両方を処理する必要がある。

## キャッチの推奨

```python
from ErisPulse.Core import ErisPulseError  # 基底クラスは Core から集約インポート

try:
    ...
except ErisPulseError as e:
    ...  # 一括キャッチ：すべてのフレームワーク独自エラー
```

- モジュール開発：必要に応じて精緻にキャッチ（上表参照）、最外層では `ErisPulseError` で一括キャッチ
- エラーはすべて `ErisPulse.Core` から集約インポートされている（`SessionOccupiedError` / `InteractionCancelled` / `StrictModeError` も含む）、`ErisPulse.Core.Bases.errors` からインポートすることも可能
- 完全な定義は `src/ErisPulse/Core/Bases/errors.py` を参照

## シャットダウン時のノイズの折りたたみ

長期稼働のプロセスがシャットダウン（またはバックグラウンドループがキャンセル）された際、イベントループは `Task was destroyed but it is pending!` などの解釈器のノイズを多数出力することがある。フレームワークでは**同様のノイズの折りたたみ**を内蔵している：2秒の時間枠内に同種のメッセージは TRACE に降格され、合計数が表示され、1回だけ出力され、末尾に「（他に N 件の同種のメッセージが折りたたまれました）」と付加される。これは意図的なノイズ低減処理であり、折りたたみの付加がフレームワークが本物のエラーを無視したことを意味するものではない。業務エラー（上記の各エラー）は通常通り完全に出力される。