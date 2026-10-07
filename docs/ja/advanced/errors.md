# エラーシステムとキャッチガイド

ErisPulse におけるすべての独自例外は `ErisPulseError` を継承しており、aiohttp や aiomysql などの下層ライブラリの例外は、フレームワーク内でキャッチされ、対応する ErisPulse 例外に変換されます。業務コードでは**下層ライブラリの例外型に依存する必要はありません**。

{!--< tips >!--}
1. 幅広くカバーしたい場合：`ErisPulseError`（すべてのフレームワーク例外の基底クラス）をキャッチ
2. 精度を重視した処理をしたい場合：モジュールごとにキャッチ（例：`ModuleCallTimeoutError`、`StorageUnreachableError`）
3. ストレージ操作はデフォルトで例外をスローしません：失敗時はログを記録し、`False / None / default` を返します。接続状態の変化は `storage.unreachable` / `storage.recovered` イベントをサブスクライブしてください。
{!--< /tips >!--}

## エラーの概要

```text
ErisPulseError                      # フレームワークのすべての例外の基底クラス
├── ClientError                     # HTTP/WS クライアントリクエスト例外の基底クラス（Core/client）
│   ├── ClientConnectionError       # 接続層のエラー：DNS 解析失敗、接続拒否、ネットワーク unreachable
│   ├── ClientTimeoutError          # リクエストのタイムアウト
│   └── HTTPStatusError             # HTTP ステータスコードエラー（4xx/5xx で raise_for_status が発生）
├── WebSocketError                  # WebSocket 例外の基底クラス（Core/client の WS 接続）
│   └── WebSocketDisconnect         # WebSocket の切断（サーバー/クライアント共通）
├── StorageError                    # ストレージ例外の基底クラス（Core/storage）
│   └── StorageUnreachableError     # ストレージのバックエンド unreachable（プール構築の再試行が尽きる：データベース unreachable/資格情報エラー）
├── InteractionError                # 交互会話例外の基底クラス（Core/Event/interaction）
│   ├── InteractionCancelled        # 待機中の待ち/リースがキャンセルされた（wait_reply 上層が None を返す）
│   └── SessionOccupiedError        # 会話の排他リースが占有されている（hold() で取得失敗）
├── ModuleError                     # モジュールシステム例外の基底クラス（Core/module）
│   └── ModuleCallError             # モジュール間呼び出し例外の基底クラス
│       ├── ModuleNotAvailableError # 目標モジュールが登録されていない/有効化されていない/初期化失敗（遅延読み込みアクセス含む）
│       ├── ServiceNotProvidedError # 目標モジュールが該当サービスを宣言していない（meta.services ホワイトリスト外）
│       └── ModuleCallTimeoutError  # 呼び出されたメソッドの実行がタイムアウト（デフォルト 30s）
├── ShadowError                     # シャドウモジュール例外の基底クラス（Core/shadow）
│   ├── ShadowStateError            # 状態が満たされない：目標がロードされていない/既にアクティブなシャドウがある/シャドウがバインドされていない（start/dismiss）
│   ├── ShadowSourceError           # シャドウソースが利用できない：パスが存在しない/ローダーが欠落/ロード失敗（start）
│   └── ShadowPromoteError          # 転正失敗：シャドウが登録されていない/ロードされていない/ローダーにスナップショットがない/再ロード失敗（promote）
└── StrictModeError                 # 严格モードの致命的な違反（起動プロセスを中止、loaders/strict）
```

## 構造化属性

例外がキャプチャされた後、メッセージテキストを解析せずに構造化された属性にアクセスできます：

| 例外 | 属性 |
|------|------|
| `ClientError`（およびそのサブクラス） | `.url` 要求のURL、`.method` 要求メソッド、`.attempts` 試行回数（リトライが失敗した場合） |
| `HTTPStatusError` | `.status` ステータスコード、`.message` 応答メッセージ |
| `WebSocketDisconnect` | `.code` 閉じるコード、`.reason` 閉じる理由 |
| `StorageUnreachableError` | `.backend` バックエンド名（sqlite/mysql/postgres）、`.cooldown` クールダウン秒数 |
| `ModuleCallError`（およびそのサブクラス） | `.module` 目標モジュール名、`.method` 目標メソッド名 |
| `ModuleCallTimeoutError` | `.module/.method` を継承、さらに `.timeout` タイムアウト期限（秒） |
| `InteractionCancelled` | `.reason` 取消理由、`.wait_key` セッションキー |
| `SessionOccupiedError` | `.wait_key` セッションキー、`.owner` 占有者 |
| `StrictModeError` | `.violations` 違反記録のリスト |

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await sdk.client.post(url, json=payload)
except ClientError as e:
    print(f"要求失敗 {e.method} {e.url}、合計 {e.attempts} 回試行: {e}")
```

## 各種エラーの説明と発生位置

### Client 系列 — `Core/client.py` / `Core/Bases/client.py`

`sdk.client` / HTTP クライアントおよび WebSocket クライアントがリクエストを発行する際に発生するエラー：

| エラー | 発生位置 | 代表的なシナリオ |
|------|----------|----------|
| `ClientError` | リクエストラッパー層 | その他のクライアントエラー（aiohttp の下層エラーは変換済み） |
| `ClientConnectionError` | 接続確立段階 | 目標サービスに到達できない、DNS 失敗、接続が拒否された |
| `ClientTimeoutError` | リクエスト実行段階 | リクエストのタイムアウト時間が超過した |
| `HTTPStatusError` | `raise_for_status()` | 応答ステータスコードが 4xx/5xx |

```python
from ErisPulse.Core.Bases.errors import ClientTimeoutError

try:
    resp = await sdk.client.get("https://api.example.com", timeout=5)
except ClientTimeoutError:
    ...
```

### WebSocket 系列 — `Core/client.py`（`send` / `receive`）

| エラー | 発生位置 | 代表的なシナリオ |
|------|----------|----------|
| `WebSocketError` | WS 受信/送信メソッド | 接続が閉じられている、予期しないメッセージタイプを受け取った、下層 WS エラー |
| `WebSocketDisconnect` | WS 受信/送信メソッド | 対向が正常に接続を切断した（フレームワークが自動的に再接続する） |

### Storage 系列 — `Core/storage` / `Core/Bases/sql_base.py`

| エラー | 発生位置 | 代表的なシナリオ |
|------|----------|----------|
| `StorageError` | ストレージ層 | ストレージ関連エラーの基底クラス |
| `StorageUnreachableError` | プールの構築段階 | データベースに到達できない / 認証情報が誤っている / ネットワーク隔離、リトライが尽きる |

> **ストレージ操作の失敗の意味**：KV およびクエリ操作は**デフォルトでは例外を送出しない**——失敗した場合は ERROR ログを記録し、`False` / `None` / `default` を返す（フレームワークの実行を接続の問題でブロックしないようにするため）。したがって、通常の業務コードでは、`StorageUnreachableError` をキャッチすることはない（これはストレージの下層を直接操作するか、カスタムバックエンドを使用する場合に主に使用される）。接続状態を実行時に検知するには、ライフサイクルイベント `storage.unreachable` / `storage.recovered` をサブスクライブする（[ライフサイクルイベント](lifecycle.md#ストレージ接続状態)を参照）。
> 接続失敗の挙動は[ストレージバックエンド → 接続失敗の挙動](storage-backends.md#接続失敗の挙動)を参照。

### Interaction — `Core/Event/interaction.py`

`wait_reply` / セッションのリース / アラームタイマー関連：

| エラー | 発生位置 | 代表的なシナリオ |
|------|----------|----------|
| `InteractionError` | 交互セッション層 | 交互セッションのエラーの基底クラス |
| `InteractionCancelled` | 待機がキャンセルされたとき | 待機の future に設定される（待機側がキャッチして `.reason` を取得できる） |
| `SessionOccupiedError` | `hold()` リース取得失敗 | セッションが他のオーナーによって占有されている（`.owner` で占有者を確認可能） |

キャンセルされた待機（モジュールのアンロード / プラットフォームのシャットダウン / 同一セッションで新しい待機が上書き）の際、`wait_reply` は例外を送出せず、代わりに `None` を返す（`InteractionCancelled` は内部で変換される）。キャンセルの原因を区別したい場合は、直接キャッチする。

### Module 系列 — `Core/module.py`（`sdk.module.call`）

| エラー | 発生位置 | 代表的なシナリオ |
|------|----------|----------|
| `ModuleError` | モジュールシステム | モジュールシステムのエラーの基底クラス |
| `ModuleCallError` | `module.call()` | モジュール間呼び出しのエラーの基底クラス |
| `ModuleNotAvailableError` | `module.call()` / ラグジュアリー属性アクセス | 目標が登録されていない / 有効化されていない / 初期化に失敗した |
| `ServiceNotProvidedError` | `module.call()` | 目標の `meta.services` ホワイトリストにそのメソッドが宣言されていない |
| `ModuleCallTimeoutError` | `module.call()` | 被呼び出しのコルーチンがタイムアウト時間（デフォルト 30s）を超えた |

「目標モジュールが利用できない」が、異なるアクセス経路で発生する場合のエラーの種類：

| アクセス経路 | エラー |
|----------|------|
| `await sdk.module.call("X", "method")` | `ModuleNotAvailableError`（型付き） |
| `sdk.module.X.attr`（初期化に失敗した後のラグジュアリー属性アクセス） | `ModuleNotAvailableError` |
| `sdk.module.X`（モジュールが有効化されていないときの属性アクセス） | `AttributeError`（Python の属性の慣例、`hasattr` はこの意味に依存） |

```python
from ErisPulse.Core.Bases.errors import ModuleNotAvailableError, ServiceNotProvidedError

try:
    history = await sdk.module.call("Chat", "get_history", session_id, n=20)
except ModuleNotAvailableError:
    ...  # 目標モジュールが存在しない / 有効化されていない
except ServiceNotProvidedError:
    ...  # 目標モジュールがそのサービスを提供していない
```

### Shadow 系列 — `Core/shadow.py`（影モジュール）

| エラー | 発生位置 | 代表的なシナリオ |
|------|----------|----------|
| `ShadowError` | 影モジュールメカニズム | 影エラーの基底クラス（すべての影エラーを一括でキャッチする） |
| `ShadowStateError` | `shadow_start()` / `dismiss_shadow()` | 目標がロードされていない / 既にアクティブな影がある / 影がバインドされていない |
| `ShadowSourceError` | `shadow_start()` | ソースパスが存在しない / プラグインローダーが欠落している / ソースにロード可能なクラスがない / 装載に失敗した |
| `ShadowPromoteError` | `promote_shadow()` | 影が登録されていない / ロードされていない / ローダーがスナップショットをサポートしていない / 転正リロードに失敗した |

### フレームワーク内部のパラメータ検証（ValueError）

ストレージクエリビルダーのパラメータ検証（空の列タイプ、`Insert` が dict でない、不安全な列タイプなど）は標準の `ValueError` を送出する——これは**開発期のコードエラー**であり、通常の業務コードはキャッチせず、呼び出しを修正する必要がある。

アダプターの標準アクションが失敗しても**例外は送出しない**：`retcode` を持つ応答辞書を返す（プロトコルの意味、例えば `retcode=10002` はアクションが実装されていないことを示す）——これは client 層の「失敗時に `ClientError` を送出する」とは並行する二つのエラー経路であり、アダプターの開発時には両方を処理する必要がある。

## エラーのキャプチャに関する提案

```python
from ErisPulse.Core import ErisPulseError  # 基底クラスは Core から集約的にエクスポートされています

try:
    ...
except ErisPulseError as e:
    ...  # 一括処理：フレームワークが定義したすべての独自例外
```

- モジュール開発：必要に応じて正確にキャッチ（上記表参照）。最外層では `ErisPulseError` を使用して一括処理が可能です。
- すべての例外は `ErisPulse.Core` から集約的にエクスポートされています（`SessionOccupiedError` / `InteractionCancelled` / `StrictModeError` 含む）。また、`ErisPulse.Core.Bases.errors` から個別にインポートすることも可能です。
- 完全な定義は `src/ErisPulse/Core/Bases/errors.py` を参照してください。

## 騒音の抑制

長期間実行されるプロセスが終了（またはバックグラウンドのループがキャンセル）される際、イベントループは多くの処理されない `Task was destroyed but it is pending!` などの解釈器のノイズを出力することがよくあります。フレームワークには**同種のノイズの折りたたみ**が組み込まれています。2秒の時間枠内に同種のメッセージはTRACEに昇格され、統合カウントされ、1度だけ出力され、末尾には「（さらに N 件の同種のメッセージが折りたたまれました）」というサフィックスが付きます。これは意図的なノイズ抑制です。このサフィックスが表示されたからといって、フレームワークが実際の例外を無視しているわけではありません。業務上の例外（上記の各々の種類）はそのまま完全に出力されます。