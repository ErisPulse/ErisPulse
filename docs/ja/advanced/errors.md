# エラーシステムとキャッチガイド

ErisPulse におけるすべての独自例外は `ErisPulseError` を継承しており、aiohttp や aiomysql などの下層ライブラリの例外は、フレームワーク内でキャッチされ、対応する ErisPulse 例外に変換されます。業務コードでは**下層ライブラリの例外型に依存する必要はありません**。

{!--< tips >!--}
1. 幅広くカバーしたい場合：`ErisPulseError`（すべてのフレームワーク例外の基底クラス）をキャッチ
2. 精度を重視した処理をしたい場合：モジュールごとにキャッチ（例：`ModuleCallTimeoutError`、`StorageUnreachableError`）
3. ストレージ操作はデフォルトで例外をスローしません：失敗時はログを記録し、`False / None / default` を返します。接続状態の変化は `storage.unreachable` / `storage.recovered` イベントをサブスクライブしてください。
{!--< /tips >!--}

## エラーの概要

```text
ErisPulseError                      # すべてのフレームワークエラーの基底クラス
├── ClientError                     # HTTP/WS クライアントリクエストエラーの基底クラス（Core/client）
│   ├── ClientConnectionError       # 接続層エラー：DNS 解析失敗、接続拒否、ネットワーク到達不可
│   ├── ClientTimeoutError          # リクエストタイムアウト
│   └── HTTPStatusError             # HTTP ステータスコードエラー（4xx/5xx および raise_for_status）
├── WebSocketError                  # WebSocket エラーの基底クラス（Core/client の WS 接続）
│   └── WebSocketDisconnect         # WebSocket 接続切断（サーバー/クライアント共通）
├── StorageError                    # ストレージエラーの基底クラス（Core/storage）
│   └── StorageUnreachableError     # ストレージバックエンドに到達不可（プール作成のリトライ回数超過：データベース到達不可/認証情報エラー）
├── InteractionError                # 交互会話エラーの基底クラス（Core/Event/interaction）
│   ├── InteractionCancelled        # 保留中の待機/リースがキャンセルされた（wait_reply 上層で None を返す）
│   └── SessionOccupiedError        # セッションの排他リースが占有されている（hold() で取得失敗）
├── ModuleError                     # モジュールシステムエラーの基底クラス（Core/module）
│   └── ModuleCallError             # モジュール間呼び出しエラーの基底クラス
│       ├── ModuleNotAvailableError # 対象モジュールが登録されていない/有効化されていない/初期化失敗（遅延読み込みアクセス含む）
│       ├── ServiceNotProvidedError # 対象モジュールが該当サービスを宣言していない（meta.services ホワイトリスト外）
│       └── ModuleCallTimeoutError  # 呼び出されたメソッドの実行がタイムアウト（デフォルト 30s）
└── StrictModeError                 # 厳格モードの致命的違反（起動プロセスを中止、loaders/strict）
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

## 各種例外の説明と発生場所

### Client 系列 — `Core/client.py` / `Core/Bases/client.py`

`sdk.client` / HTTP クライアントと WebSocket クライアントがリクエストを発行する際に送出されます：

| 例外 | 発生位置 | 代表的なシナリオ |
|------|----------|----------|
| `ClientError` | リクエストラッパー層 | その他のクライアントエラー（aiohttp の低層エラーは変換済み） |
| `ClientConnectionError` | 接続確立段階 | 対象サービスに到達できない、DNS 失敗、接続拒否 |
| `ClientTimeoutError` | リクエスト実行段階 | リクエストのタイムアウト時間超過 |
| `HTTPStatusError` | `raise_for_status()` | レスポンスステータスコードが 4xx/5xx |

```python
from ErisPulse.Core.Bases.errors import ClientTimeoutError

try:
    resp = await sdk.client.get("https://api.example.com", timeout=5)
except ClientTimeoutError:
    ...
```

### WebSocket 系列 — `Core/client.py`（`send` / `receive`）

| 例外 | 発生位置 | 代表的なシナリオ |
|------|----------|----------|
| `WebSocketError` | WS 受信/送信メソッド | 接続が閉じられている、予期しないメッセージタイプを受け取った、WS の低層エラー |
| `WebSocketDisconnect` | WS 受信/送信メソッド | 対向が正常に接続を切断した（フレームワークが自動的に再接続する） |

### Storage 系列 — `Core/storage` / `Core/Bases/sql_base.py`

| 例外 | 発生位置 | 代表的なシナリオ |
|------|----------|----------|
| `StorageError` | ストレージ層 | ストレージ関連の例外の基底クラス |
| `StorageUnreachableError` | プール構築段階 | データベースに到達できない / 認証情報が間違っている / ネットワーク隔離、リトライが尽きる |

> **ストレージ操作の失敗の意味**：KV とクエリ操作は**デフォルトでは例外を送出しない**——失敗した場合、ERROR ログを記録し、`False` / `None` / `default` を返す（フレームワークの実行を接続の問題で阻害しない）。したがって、業務コードでは通常 `StorageUnreachableError` をキャッチすることは**ない**（主にストレージの低層操作やカスタムバックエンドに使用される）。接続状態を実行時に感知するには、ライフサイクルイベント `storage.unreachable` / `storage.recovered` をサブスクライブする（[ライフサイクルイベント](lifecycle.md#ストレージ接続状態)を参照）。
> 接続失敗の挙動は[ストレージバックエンド → 接続失敗の挙動](storage-backends.md#接続失敗の挙動)を参照。

### Interaction — `Core/Event/interaction.py`

`wait_reply` / セッションのリース / アラートタイマ関連：

| 例外 | 発生位置 | 代表的なシナリオ |
|------|----------|----------|
| `InteractionError` | インタラクションセッション層 | インタラクションセッションの例外の基底クラス |
| `InteractionCancelled` | 待機がキャンセルされたとき | 待機中の future に設定された（待機側がキャッチして `.reason` を取得可能） |
| `SessionOccupiedError` | `hold()` リース取得失敗 | セッションが他のオーナーによって占有されている（`.owner` から占有者を確認可能） |

キャンセルされた待機（モジュールのアンロード / プラットフォームのシャットダウン / 同一セッションで新しい待機が上書き）の際、`wait_reply` は例外を送出せず、**`None` を返す**（`InteractionCancelled` は内部で変換される）。キャンセルの原因を区別する必要がある場合、直接キャッチする。

### Module 系列 — `Core/module.py`（`sdk.module.call`）

| 例外 | 発生位置 | 代表的なシナリオ |
|------|----------|----------|
| `ModuleError` | モジュールシステム | モジュールシステムの例外の基底クラス |
| `ModuleCallError` | `module.call()` | モジュール間呼び出しの例外の基底クラス |
| `ModuleNotAvailableError` | `module.call()` / ラジーロード属性アクセス | 目標が登録されていない / 有効化されていない / 初期化に失敗 |
| `ServiceNotProvidedError` | `module.call()` | 目標の `meta.services` ホワイトリストにそのメソッドが宣言されていない |
| `ModuleCallTimeoutError` | `module.call()` | 被呼び出しのコルーチンがタイムアウト時間（デフォルト 30s）を超えた |

「目標モジュールが利用できない」は、異なるアクセス経路での例外の種類：

| アクセス経路 | 例外 |
|----------|------|
| `await sdk.module.call("X", "method")` | `ModuleNotAvailableError`（型付き） |
| `sdk.module.X.attr`（ラジーロード属性アクセス、初期化失敗後） | `ModuleNotAvailableError` |
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

### フレームワーク内部のパラメータ検証（ValueError）

ストレージクエリビルダーのパラメータ検証（空の列タイプ、`Insert` が dict でない、安全でない列タイプなど）は標準の `ValueError` を送出する——これは**開発時のコードエラー**であり、通常の業務コードではキャッチすべきではなく、呼び出しを修正すべきである。

アダプタの標準動作が失敗しても**例外は送出しない**：`retcode` を持つレスポンス辞書を返す（プロトコルの意味、例えば `retcode=10002` は動作が実装されていないことを示す）——これは client 層の「失敗時に `ClientError` を送出する」のと並行するエラーチャンネルであるため、アダプタの開発時には両方を同時に処理する必要がある。

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