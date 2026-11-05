# 例外体系と捕捉ガイド

> [!NOTE]
> **L1 コア必読**——トップページの「リーディングパス」に含まれる5つのコアドキュメントの1つ。モジュール開発に必須です。


ErisPulse のすべてのカスタム例外は `ErisPulseError` を継承しており、低レベルライブラリの例外（aiohttp、aiomysql など）はフレームワーク内部で捕捉され、対応する ErisPulse 例外に変換されます。ビジネスコードは**いかなる低レベルライブラリの例外型にも依存する必要はありません**。

{!--< tips >!--}
1. 広くフォールバックしたい場合：`ErisPulseError` を捕捉する（すべてのフレームワーク例外の基底クラス）
2. 厳密に処理したい場合：モジュールごとに捕捉する（例：`ModuleCallTimeoutError`、`StorageUnreachableError`）
3. ストレージ操作はデフォルトで例外をスローしない：失敗時はログを記録し `False / None / default` を返す。接続状態の変化は `storage.unreachable` / `storage.recovered` イベントを購読
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
│   ├── ConnectionNotFoundError     # 接続が存在しない／切断・登録解除済み（connections.get/close）
│   └── ConnectionPermissionError   # owner 以外が他者の接続をクローズ（クローズ権は作成者に帰属）
├── StorageError                    # ストレージ例外の基底クラス（Core/storage）
│   └── StorageUnreachableError     # ストレージバックエンド到達不能（プール作成のリトライ使い果たし：DB 到達不能／認証情報エラー）
├── InteractionError                # インタラクション例外の基底クラス（Core/Event/interaction）
│   ├── InteractionCancelled        # 保留中の待機/リースがキャンセルされた（wait_reply では上位層で None 返却に変換）
│   └── SessionOccupiedError        # セッションの排他リースが占有済み（hold() の取得失敗）
├── ModuleError                     # モジュールシステム例外の基底クラス（Core/module）
│   └── ModuleCallError             # モジュール間呼び出し例外の基底クラス
│       ├── ModuleNotAvailableError # 対象モジュールが未登録／無効／初期化失敗（遅延読み込みアクセスを含む）
│       ├── ServiceNotProvidedError # 対象モジュールが当該サービスを宣言していない（meta.services ホワイトリスト外）
│       └── ModuleCallTimeoutError  # 呼び出されたメソッドの実行タイムアウト（デフォルト 30 秒）
├── ShadowError                     # シャドウモジュール例外の基底クラス（Core/shadow）
│   ├── ShadowStateError            # 状態不充足：対象未ロード／アクティブなシャドウが既に存在／シャドウ未バインド（start/dismiss）
│   ├── ShadowSourceError           # シャドウソース利用不可：パス不存在／ローダー欠如／ロード失敗（start）
│   └── ShadowPromoteError          # 正式化失敗：シャドウ未登録／未ロード／ローダーにスナップショットなし／リロード失敗（promote）
└── StrictModeError                 # 厳格モードにおける致命的な違反（起動フローを中止、loaders/strict）
```

## 構造化属性

例外を捕捉した後、構造化属性を読み取れます（メッセージテキストを解析する必要はありません）：

| 例外 | 属性 |
|------|------|
| `ClientError`（サブクラスを含む） | `.url` リクエスト URL、`.method` リクエストメソッド、`.attempts` 試行回数（リトライ使い果たし時） |
| `HTTPStatusError` | `.status` ステータスコード、`.message` レスポンスメッセージ |
| `WebSocketDisconnect` | `.code` クローズコード、`.reason` クローズ理由 |
| `ConnectionNotFoundError` | `.connection_id` 検索対象の接続 id |
| `ConnectionPermissionError` | `.connection_id` 対象接続 id、`.owner` 接続の所有者 owner |
| `StorageUnreachableError` | `.backend` バックエンド名（sqlite/mysql/postgres）、`.cooldown` クールダウン秒数 |
| `ModuleCallError`（サブクラスを含む） | `.module` 対象モジュール名、`.method` 対象メソッド名 |
| `ModuleCallTimeoutError` | `.module/.method` を継承、加えて `.timeout` タイムアウト上限（秒） |
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

### Client 系列 — `Core/client.py` / `Core/Bases/client.py`

`sdk.client` / HTTP クライアントおよび WebSocket クライアントがリクエストを発行する際にスローされます：

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

### WebSocket 系列 — `Core/client.py`（`send` / `receive`）

| 例外 | 発生箇所 | 典型的なシナリオ |
|------|----------|----------|
| `WebSocketError` | WS 送受信メソッド | 接続が既に閉じている、予期しないメッセージ型を受信、低レベル WS 例外 |
| `WebSocketDisconnect` | WS 送受信メソッド | ピアによる正常な切断（フレームワークが自動再接続） |

### 接続レジストリ系列 — `Core/connections.py`（2.10+）

| 例外 | 発生箇所 | 典型的なシナリオ |
|------|----------|----------|
| `ConnectionNotFoundError` | `connections.get` / `assign` / `dismiss` / `close` | 接続 id が存在しない、または切断・登録解除済み |
| `ConnectionPermissionError` | owner 以外が `conn.close()` を呼び出し | モジュールをまたいで他者の接続をクローズ（送信とグループ化は制限されない） |

### Storage 系列 — `Core/storage` / `Core/Bases/sql_base.py`

| 例外 | 発生箇所 | 典型的なシナリオ |
|------|----------|----------|
| `StorageError` | ストレージ層 | ストレージ関連例外の基底クラス |
| `StorageUnreachableError` | プール作成フェーズ | DB 到達不能／認証情報エラー／ネットワーク分離、リトライ使い果たし |

> **ストレージ操作の失敗セマンティクス**：KV およびクエリ操作は**デフォルトで例外をスローしません**——失敗時には ERROR ログを記録し、
> `False` / `None` / `default` を返します（接続問題がフレームワークの実行をブロックするのを避けるため）。そのため、ビジネスコードが通常
> `StorageUnreachableError` を捕捉することは**ありません**（主にストレージの低レベルを直接操作する場合やカスタムバックエンド向けのものです）。
> 実行時に接続状態を感知するには、ライフサイクルイベント `storage.unreachable` / `storage.recovered` を購読してください
> （詳細は[ライフサイクルイベント](lifecycle.md#ストレージ接続状態)を参照）。

接続失敗時の動作の詳細は[ストレージバックエンド → 接続失敗時の動作](storage-backends.md#接続失敗時の動作)を参照してください。

### Interaction — `Core/Event/interaction.py`

`wait_reply` / セッションリース / リマインダータイマー関連：

| 例外 | 発生箇所 | 典型的なシナリオ |
|------|----------|----------|
| `InteractionError` | インタラクション層 | インタラクション例外の基底クラス |
| `InteractionCancelled` | 保留中の待機がキャンセルされた際 | 待機用 future に設定される（待機側は捕捉して `.reason` を取得可能） |
| `SessionOccupiedError` | `hold()` のリース取得失敗 | セッションが既に他の owner に占有されている（`.owner` で占有者を確認可能） |

待機がキャンセルされた場合（モジュールのアンインストール／プラットフォームのシャットダウン／同一セッションの新しい待機への置き換え）、`wait_reply` は例外をスローせずに **`None` を返します**（`InteractionCancelled` は内部で変換されます）。キャンセル理由を区別する必要がある場合にのみ、直接捕捉してください。

### Module 系列 — `Core/module.py`（`sdk.module.call`）

| 例外 | 発生箇所 | 典型的なシナリオ |
|------|----------|----------|
| `ModuleError` | モジュールシステム | モジュールシステム例外の基底クラス |
| `ModuleCallError` | `module.call()` | モジュール間呼び出し例外の基底クラス |
| `ModuleNotAvailableError` | `module.call()` / 遅延読み込み属性アクセス | 対象が未登録／無効／初期化失敗 |
| `ServiceNotProvidedError` | `module.call()` | 対象の `meta.services` ホワイトリストにそのメソッドが宣言されていない |
| `ModuleCallTimeoutError` | `module.call()` | 呼び出されたコルーチンがタイムアウト時間を超過（デフォルト 30 秒） |

「対象モジュールが利用不可」の場合の、アクセスパスごとの例外タイプ：

| アクセスパス | 例外 |
|----------|------|
| `await sdk.module.call("X", "method")` | `ModuleNotAvailableError`（型付き） |
| `sdk.module.X.attr`（遅延読み込み属性アクセス、初期化失敗後） | `ModuleNotAvailableError` |
| `sdk.module.X`（モジュールが無効な場合の属性アクセス） | `AttributeError`（Python の属性の慣習、`hasattr` はこのセマンティクスに依存） |

```python
from ErisPulse.Core.Bases.errors import ModuleNotAvailableError, ServiceNotProvidedError

try:
    history = await sdk.module.call("Chat", "get_history", session_id, n=20)
except ModuleNotAvailableError:
    ...  # 対象モジュールが存在しない／無効
except ServiceNotProvidedError:
    ...  # 対象モジュールがそのサービスを提供していない
```

### Shadow 系列 — `Core/shadow.py`（シャドウモジュール）

| 例外 | 発生箇所 | 典型的なシナリオ |
|------|----------|----------|
| `ShadowError` | シャドウモジュール機構 | シャドウ例外の基底クラス（すべてのシャドウエラーを一括捕捉） |
| `ShadowStateError` | `shadow_start()` / `dismiss_shadow()` | 対象未ロード／アクティブなシャドウが既に存在／シャドウ未バインド |
| `ShadowSourceError` | `shadow_start()` | ソースパス不存在／プラグインローダー欠如／ソースにロード可能なクラスなし／ロード失敗 |
| `ShadowPromoteError` | `promote_shadow()` | シャドウ未登録／未ロード／ローダーがスナップショット非対応／正式化リロード失敗 |

### フレームワーク内部のパラメータ検証（ValueError）

ストレージクエリビルダーのパラメータ検証（空の列タイプ、`Insert` が dict でない、安全でない列タイプなど）は標準の
`ValueError` をスローします——これは**開発時のコーディングエラー**に属し、正常なビジネスコードで捕捉すべきものではなく、
呼び出し側を修正すべきものです。

アダプターの標準アクション失敗は**例外をスローしません**：`retcode` を含むレスポンス辞書を返します（プロトコルセマンティクス、例：
`retcode=10002` はアクションが実装されていないことを示す）——client 層の「失敗時に `ClientError` をスローする」とは並行する
2つのエラーチャネルであり、アダプター開発時には両方を処理する必要があります。

## 捕捉の推奨事項

```python
from ErisPulse.Core import ErisPulseError  # 基底クラスは Core から集約エクスポート済み

try:
    ...
except ErisPulseError as e:
    ...  # 統一フォールバック：すべてのフレームワークカスタム例外
```

- モジュール開発：必要に応じて厳密に捕捉し（上の表を参照）、最外層は `ErisPulseError` でフォールバック可能
- 例外はすべて `ErisPulse.Core` から集約エクスポートされており（`SessionOccupiedError` / `InteractionCancelled` / `StrictModeError` を含む）、`ErisPulse.Core.Bases.errors` からもインポート可能
- 完全な定義は `src/ErisPulse/Core/Bases/errors.py` を参照

## シャットダウンノイズの折りたたみ

長期駐留プロセスがシャットダウンする際（またはバックグラウンドループがキャンセルされた際）、イベントループはしばしば処置の価値のない
`Task was destroyed but it is pending!` などのインタープリターノイズを大量に吐き出します。フレームワークには**同種ノイズの折りたたみ**が組み込まれています：
2 秒ウィンドウ内の同種メッセージは TRACE にダウングレードされてカウントが統合され、1 回だけ出力され、末尾に
「（他に N 件の同種メッセージが折りたたまれました）」というサフィックスが付きます。これは意図的なノイズ低減動作です——折りたたみサフィックスが表示されても、
フレームワークが実際の例外を握りつぶしたことを意味しません。ビジネス例外（上表の各種）は従来どおり完全に出力されます。折りたたみはインタープリター終了時のノイズのみを対象とし、
ビジネス例外には影響しません。どのレベルの例外を記録すべきで、どれをダウングレード／折りたたみできるかについては、
[エンジニアリング堅牢性ルール · 例外記録のレベル分け](../styleguide/engineering.md#1-例外記録のレベル分け) に従ってください。

## 関連ドキュメント

トラブルシューティングの目的に応じて選択してください：

- **ストレージ操作が `False` / `None` を返し、接続状態を把握したい** → [ストレージバックエンド · 接続失敗時の動作](storage-backends.md#接続失敗時の動作)、または [storage.unreachable / storage.recovered イベント](lifecycle.md#ストレージ接続状態) を購読
- **`wait_reply` が `None` を返し、何によってキャンセルされたかを知りたい** → [インタラクションシステム](interaction.md)（キャンセル理由対応表）
- **`module.call` がモジュール呼び出し例外をスロー** → [モジュール間通信](module-communication.md)
- **接続 / WebSocket のエラー** → [ネットワーククライアント](client.md)（ClientError 体系）と[接続プールとブロードキャスト](connections.md)（接続レジストリ例外）