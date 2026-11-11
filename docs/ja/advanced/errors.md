# 例外体系と捕捉ガイド

> [!NOTE]
> **L1 コア必読**——トップページの「リーディングパス」にある 5 つのコアドキュメントの 1 つ。モジュール開発に必須。


ErisPulse のすべてのカスタム例外は `ErisPulseError` を継承しています。低レベルライブラリの例外（aiohttp、aiomysql など）
はフレームワーク内部で捕捉され、対応する ErisPulse 例外へ変換されます——ビジネスコードは**いかなる低レベルライブラリの例外型にも依存する必要がありません**。

{!--< tips >!--}
1. 広くフォールバックしたい場合：`ErisPulseError` を捕捉（すべてのフレームワーク例外の基底クラス）
2. 厳密に処理したい場合：モジュールごとに捕捉（例：`ModuleCallTimeoutError`、`StorageOperationError`、`StorageUnreachableError`）
3. ストレージ書き込み操作の失敗は**デフォルトで `StorageOperationError` を送出**（2.12 以降）。接続レベルの到達不能時のクールダウン期間中のフェイルファストは引き続き `False / None / default` を返します。接続状態の変化は `storage.unreachable` / `storage.recovered` イベントを購読してください
{!--< /tips >!--}

## 例外一覧

```text
ErisPulseError                      # すべてのフレームワーク例外の基底クラス
├── ClientError                     # HTTP/WS クライアントリクエスト例外の基底クラス（Core/client）
│   ├── ClientConnectionError       # 接続層エラー：DNS 解決失敗、接続拒否、ネットワーク到達不能
│   ├── ClientTimeoutError          # リクエストタイムアウト
│   └── HTTPStatusError             # HTTP ステータスコードエラー（例：4xx/5xx かつ raise_for_status）
├── WebSocketError                  # WebSocket 例外の基底クラス（Core/client の WS 接続）
│   └── WebSocketDisconnect         # WebSocket 切断（サーバー/クライアント共通）
├── ConnectionRegistryError         # 接続レジストリ例外の基底クラス（Core/connections、2.10+）
│   ├── ConnectionNotFoundError     # 接続が存在しない/切断済みで登録解除（connections.get/close）
│   └── ConnectionPermissionError   # owner 以外による他者接続のクローズ（クローズ権は作成者に帰属）
├── StorageError                    # ストレージ例外の基底クラス（Core/storage）
│   ├── StorageOperationError       # ストレージ操作の実行失敗（2.12 以降は書き込みパスでデフォルト送出）
│   └── StorageUnreachableError     # ストレージバックエンド到達不能（プール構築リトライ使い果たし：データベース到達不能/認証情報エラー）
├── InteractionError                # インタラクションセッション例外の基底クラス（Core/Event/interaction）
│   ├── InteractionCancelled        # 保留中の待機/リースがキャンセル（wait_reply では上位層で None 返却に変換）
│   └── SessionOccupiedError        # セッション排他リースが占有済み（hold() による取得失敗）
├── ModuleError                     # モジュールシステム例外の基底クラス（Core/module）
│   └── ModuleCallError             # モジュール間呼び出し例外の基底クラス
│       ├── ModuleNotAvailableError # 対象モジュールが未登録/未有効化/初期化失敗（遅延ロードアクセスを含む）
│       ├── ServiceNotProvidedError # 対象モジュールが当該サービスを未宣言（meta.services ホワイトリスト外）
│       └── ModuleCallTimeoutError  # 呼び出されたメソッドの実行タイムアウト（デフォルト 30s）
├── ShadowError                     # シャドウモジュール例外の基底クラス（Core/shadow）
│   ├── ShadowStateError            # 状態不充足：対象が未ロード/アクティブなシャドウが既存/シャドウ未バインド（start/dismiss）
│   ├── ShadowSourceError           # シャドウソース利用不可：パス不存在/ローダー欠落/ロード失敗（start）
│   └── ShadowPromoteError          # 昇格失敗：シャドウ未登録/未ロード/ローダーにスナップショットなし/リロード失敗（promote）
└── StrictModeError                 # 厳格モードの致命的違反（起動フローを中止、loaders/strict）
```

## 構造化属性

例外を捕捉した後、構造化された属性を読み取れます（メッセージテキストを解析する必要はありません）：

| 例外 | 属性 |
|------|------|
| `ClientError`（サブクラスを含む） | `.url` リクエスト URL、`.method` リクエストメソッド、`.attempts` 試行回数（リトライを使い果たした場合） |
| `HTTPStatusError` | `.status` ステータスコード、`.message` レスポンスメッセージ |
| `WebSocketDisconnect` | `.code` クローズコード、`.reason` クローズ理由 |
| `ConnectionNotFoundError` | `.connection_id` 検索した接続 id |
| `ConnectionPermissionError` | `.connection_id` 対象接続 id、`.owner` 接続の所有者 owner |
| `StorageUnreachableError` | `.backend` バックエンド名（sqlite/mysql/postgres）、`.cooldown` クールダウン秒数 |
| `StorageOperationError` | `.operation` 操作名（set/delete/clear/set_multi/transaction_begin）、`.key` 操作キー |
| `ModuleCallError`（サブクラスを含む） | `.module` 対象モジュール名、`.method` 対象メソッド名 |
| `ModuleCallTimeoutError` | `.module/.method` を継承、さらに `.timeout` タイムアウト制限（秒） |
| `InteractionCancelled` | `.reason` キャンセル理由、`.wait_key` セッションキー |
| `SessionOccupiedError` | `.wait_key` セッションキー、`.owner` 占有者 |
| `StrictModeError` | `.violations` 違反記録のリスト |

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await sdk.client.post(url, json=payload)
except ClientError as e:
    print(f"リクエスト失敗 {e.method} {e.url}、合計 {e.attempts} 回試行: {e}")
```

## 各例外の説明と発生箇所

### Client 系 — `Core/client.py` / `Core/Bases/client.py`

`sdk.client` / HTTP クライアントと WebSocket クライアントがリクエストを発行する際に送出されます：

| 例外 | 発生箇所 | 典型的なシナリオ |
|------|----------|----------|
| `ClientError` | リクエストラッパー層 | その他のクライアントエラー（低レベル aiohttp 例外は変換済み） |
| `ClientConnectionError` | 接続確立フェーズ | 対象サービス到達不能、DNS 失敗、接続拒否 |
| `ClientTimeoutError` | リクエスト実行フェーズ | リクエストタイムアウト時間を超過 |
| `HTTPStatusError` | `raise_for_status()` | レスポンスステータスコードが 4xx/5xx |

```python
from ErisPulse.Core.Bases.errors import ClientTimeoutError

try:
    resp = await sdk.client.get("https://api.example.com", timeout=5)
except ClientTimeoutError:
    ...
```

### WebSocket 系 — `Core/client.py`（`send` / `receive`）

| 例外 | 発生箇所 | 典型的なシナリオ |
|------|----------|----------|
| `WebSocketError` | WS 送受信メソッド | 接続が既にクローズ済み、予期しないメッセージタイプの受信、低レベル WS 例外 |
| `WebSocketDisconnect` | WS 送受信メソッド | ピアによる正常な切断（フレームワークが自動再接続） |

### 接続レジストリ系 — `Core/connections.py`（2.10+）

| 例外 | 発生箇所 | 典型的なシナリオ |
|------|----------|----------|
| `ConnectionNotFoundError` | `connections.get` / `assign` / `dismiss` / `close` | 接続 id が存在しない、または切断・登録解除済み |
| `ConnectionPermissionError` | owner 以外が `conn.close()` を呼び出し | モジュールを跨いだ他者接続のクローズ（送信とグループ化は制限されない） |

### Storage 系 — `Core/storage` / `Core/Bases/sql_base.py`

| 例外 | 発生箇所 | 典型的なシナリオ |
|------|----------|----------|
| `StorageError` | ストレージ層 | ストレージ関連例外の基底クラス |
| `StorageOperationError` | KV 書き込みパス / トランザクション開始（2.12 以降） | 書き込みロック競合タイムアウト / SQL エラー / 制約違反 / トランザクション開始タイムアウト——**デフォルトで送出** |
| `StorageUnreachableError` | プール構築フェーズ | データベース到達不能 / 認証情報エラー / ネットワーク分離、リトライを使い果たし |

> **ストレージ操作の失敗セマンティクス（2.12 以降の階層化）**：
> - **書き込みパスの実行失敗はデフォルトで送出** `StorageOperationError`（`aset` / `adelete` / `aclear` / `set_multi`
>   および同期ブリッジの同一パス）——ライブラリには到達可能なのに書き込みが失敗したということはデータが書き込まれていないことを意味し、サイレントに返すと呼び出し側はデータ損失に気づけません。
>   重要な書き込みは try/except で捕捉し、補償処理を行ってください
> - **接続レベルの到達不能**（クールダウン期間中のフェイルファスト）は引き続き `False` / `None` / `default` を返します（フレームワークのレジリエンスセマンティクス）。
>   通常、ビジネスコードで `StorageUnreachableError` を捕捉することはありません。実行時に接続状態を感知するにはライフサイクルイベント
>   `storage.unreachable` / `storage.recovered` を購読してください（詳細は[ライフサイクルイベント](lifecycle.md#存储连接状态)）
> - **トランザクション開始が 30s を超過**すると `StorageOperationError` を送出（`STORAGE_TXN_BEGIN_TIMEOUT_SECS`）——
>   並発する長時間トランザクションを無限に待ち続けるのはフレームワークの欠陥であり、必ず観測可能でなければなりません

接続失敗時の動作の詳細は[ストレージバックエンド → 接続失敗時の動作](storage-backends.md#连接失败行为)を参照してください。

### Interaction — `Core/Event/interaction.py`

`wait_reply` / セッションリース / リマインダータイマー関連：

| 例外 | 発生箇所 | 典型的なシナリオ |
|------|----------|----------|
| `InteractionError` | インタラクションセッション層 | インタラクションセッション例外の基底クラス |
| `InteractionCancelled` | 保留中の待機がキャンセルされたとき | 待機用 future にセットされる（待機側は捕捉して `.reason` を取得可能） |
| `SessionOccupiedError` | `hold()` によるリース取得失敗 | セッションが既に他の owner に占有されている（`.owner` で占有者を確認可能） |

待機がキャンセルされた場合（モジュールのアンロード / プラットフォームのシャットダウン / 同一セッションで新しい待機が取って代わった場合）、`wait_reply` は**`None` を返し**
例外を送出しません（`InteractionCancelled` は内部で変換されます）。キャンセル理由を区別する必要がある場合にのみ、直接捕捉してください。

### Module 系 — `Core/module.py`（`sdk.module.call`）

| 例外 | 発生箇所 | 典型的なシナリオ |
|------|----------|----------|
| `ModuleError` | モジュールシステム | モジュールシステム例外の基底クラス |
| `ModuleCallError` | `module.call()` | モジュール間呼び出し例外の基底クラス |
| `ModuleNotAvailableError` | `module.call()` / 遅延ロード属性アクセス | 対象が未登録 / 未有効化 / 初期化失敗 |
| `ServiceNotProvidedError` | `module.call()` | 対象の `meta.services` ホワイトリストで当該メソッドが未宣言 |
| `ModuleCallTimeoutError` | `module.call()` | 呼び出されたコルーチンがタイムアウト時間を超過（デフォルト 30s） |

「対象モジュールが利用不可」となる場合の、アクセスパスごとの例外タイプ：

| アクセスパス | 例外 |
|----------|------|
| `await sdk.module.call("X", "method")` | `ModuleNotAvailableError`（型付き） |
| `sdk.module.X.attr`（遅延ロード属性アクセス、初期化失敗後） | `ModuleNotAvailableError` |
| `sdk.module.X`（モジュールが未有効化のときの属性アクセス） | `AttributeError`（Python の属性アクセスの慣例。`hasattr` はこの挙動に依存） |

```python
from ErisPulse.Core.Bases.errors import ModuleNotAvailableError, ServiceNotProvidedError

try:
    history = await sdk.module.call("Chat", "get_history", session_id, n=20)
except ModuleNotAvailableError:
    ...  # 対象モジュールが存在しない / 未有効化
except ServiceNotProvidedError:
    ...  # 対象モジュールが当該サービスを提供していない
```

### Shadow 系 — `Core/shadow.py`（シャドウモジュール）

| 例外 | 発生箇所 | 典型的なシナリオ |
|------|----------|----------|
| `ShadowError` | シャドウモジュール機構 | シャドウ例外の基底クラス（すべてのシャドウエラーを統一的に捕捉） |
| `ShadowStateError` | `shadow_start()` / `dismiss_shadow()` | 対象が未ロード / アクティブなシャドウが既に存在 / シャドウ未バインド |
| `ShadowSourceError` | `shadow_start()` | ソースパスが存在しない / プラグインローダーが欠落 / ソースにロード可能なクラスがない / ロード失敗 |
| `ShadowPromoteError` | `promote_shadow()` | シャドウが未登録 / 未ロード / ローダーがスナップショット非対応 / 昇格時のリロード失敗 |

### フレームワーク内部のパラメータ検証（ValueError）

ストレージクエリビルダーによるパラメータ検証（空のカラム型、`Insert` に dict 以外を渡す、安全でないカラム型など）は標準の
`ValueError` を送出します——これらは**開発段階のコーディングミス**に属するため、正常なビジネスコードで捕捉すべきものではなく、呼び出し側を修正すべきものです。

アダプタの標準アクションの失敗は**例外を送出しません**：`retcode` を含むレスポンス辞書を返します（プロトコルセマンティクス。例：
`retcode=10002` はアクションが未実装であることを示す）——これは client 層の「失敗時に `ClientError` を送出」とは並行する
2 つのエラーチャネルであり、アダプタ開発時には両方を処理する必要があります。

## 捕捉の推奨事項

```python
from ErisPulse.Core import ErisPulseError  # 基底クラスは Core から集約エクスポート済み

try:
    ...
except ErisPulseError as e:
    ...  # 統一フォールバック：すべてのフレームワークカスタム例外
```

- モジュール開発：必要に応じて個別に捕捉（上記の表）。最外層は `ErisPulseError` でフォールバック可能
- 例外はすべて `ErisPulse.Core` から集約エクスポートされています（`SessionOccupiedError` / `InteractionCancelled` / `StrictModeError` を含む）。`ErisPulse.Core.Bases.errors` からもインポート可能
- 完全な定義は `src/ErisPulse/Core/Bases/errors.py` を参照

## シャットダウン時のノイズ折りたたみ

長期間常駐するプロセスは、シャットダウン時（またはバックグラウンドループのキャンセル時）に、イベントループが処置の価値のない
`Task was destroyed but it is pending!` 系のインタプリタノイズを大量に吐き出すことがよくあります。フレームワークには**同種ノイズの折りたたみ**が組み込まれています：
2 秒のウィンドウ内の同種メッセージは TRACE にダウングレードされ、カウントを統合して 1 回だけ出力され、末尾に
「（同種のメッセージがさらに N 件折りたたまれました）」という接尾辞が付きます。これは意図的なノイズ低減の動作であり——折りたたみ接尾辞が見えても、
フレームワークが実際の例外を握りつぶしたことを意味しません。ビジネス例外（上記の表の各種）は従来どおり完全に出力されます。折りたたみはインタプリタ終了時のノイズのみを対象とし、
ビジネス例外には影響しません。どのレベルの例外が記録に値し、どれをダウングレード/折りたたみできるかについては、
[エンジニアリング堅牢性ルール · 例外記録のレベル分け](../styleguide/engineering.md#1-异常留痕分级)に従ってください。

## 関連ドキュメント

トラブルシューティングの目的に応じて選択してください：

- **ストレージ操作が `False` / `None` を返し、接続状態を把握したい** → [ストレージバックエンド · 接続失敗時の動作](storage-backends.md#连接失败行为)、または [storage.unreachable / storage.recovered イベント](lifecycle.md#存储连接状态)の購読
- **`wait_reply` が `None` を返し、何によってキャンセルされたかを知りたい** → [インタラクションセッションシステム](interaction.md)（キャンセル理由の対応表）
- **`module.call` がモジュール呼び出し例外を送出する** → [モジュール間通信](module-communication.md)
- **接続 / WebSocket のエラー** → [ネットワーククライアント](client.md)（ClientError 体系）と[接続プールとブロードキャスト](connections.md)（接続レジストリ例外）