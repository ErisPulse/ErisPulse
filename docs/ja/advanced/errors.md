# エラー体系とキャッチガイド

ErisPulse で定義されたすべてのカスタムエラーは、`ErisPulseError` を継承しています。aiohttp や aiomysql などのライブラリのエラーは、フレームワーク内でキャッチされ、対応する ErisPulse エラーに変換されます。業務コードでは**下層ライブラリのエラー型に依存する必要はありません**。

{!--< tips >!--}
1. 一般的なエラーを網羅的にキャッチしたい場合：`ErisPulseError` をキャッチ（すべてのフレームワークエラーの基底クラス）
2. 精度を重視したエラー処理をしたい場合：モジュールごとにキャッチ（例：`ModuleCallTimeoutError`、`StorageUnreachableError`）
3. ストレージ操作はデフォルトで例外をスローしません：失敗した場合はログを記録し、`False / None / default` を返します
{!--< /tips >!--}

## エラーの概要

```text
ErisPulseError                      # フレームワークのすべてのエラーの基底クラス
├── ClientError                     # HTTP/WS クライアントリクエストエラーの基底クラス（Core/client）
│   ├── ClientConnectionError       # 接続層エラー：DNS 解析失敗、接続拒否、ネットワーク到達不能
│   ├── ClientTimeoutError          # リクエストタイムアウト
│   └── HTTPStatusError             # HTTP ステータスコードエラー（4xx/5xx で raise_for_status が発生した場合）
├── WebSocketError                  # WebSocket エラーの基底クラス（Core/client の WS 接続）
│   └── WebSocketDisconnect         # WebSocket 接続切断（サーバーサイド/クライアントサイド共通）
├── StorageError                    # ストレージエラーの基底クラス（Core/storage）
│   └── StorageUnreachableError     # ストレージバックエンドが到達不能（プール作成のリトライ回数超過：データベース到達不能/認証情報エラー）
├── InteractionError                # インタラクションセッションエラーの基底クラス（Core/Event/interaction）
├── ModuleError                     # モジュールシステムエラーの基底クラス（Core/module）
│   └── ModuleCallError             # モジュール間呼び出しエラーの基底クラス
│       ├── ModuleNotAvailableError # 対象モジュールが登録されていない/有効化されていない/ロード失敗
│       ├── ServiceNotProvidedError # 対象モジュールがそのサービスを宣言していない（meta.services のホワイトリスト外）
│       └── ModuleCallTimeoutError  # 呼び出しメソッドの実行がタイムアウト（デフォルト 30s）
└── （フレームワーク内部エラー）     # ValueError などパラメータ検証用、以下を参照
```

## 各種例外の説明と発生位置

### Client 系列 — `Core/client.py` / `Core/Bases/client.py`

`sdk.client` / HTTP クライアントと WebSocket クライアントがリクエストを発行する際に送出される例外:

| 例外 | 発生位置 | 代表的なシナリオ |
|------|----------|----------|
| `ClientError` | リクエストラッパー層 | 他のクライアントエラー（aiohttp の内部例外は変換済み） |
| `ClientConnectionError` | 接続確立段階 | 対象サービスに到達できない、DNS 失敗、接続が拒否された |
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
| `WebSocketError` | WS 受信/送信メソッド | 接続が閉じられている、想定外のメッセージタイプを受け取った、WS の内部例外 |
| `WebSocketDisconnect` | WS 受信/送信メソッド | 対向が正常に接続を切断した（フレームワークが自動的に再接続する） |

### Storage 系列 — `Core/storage` / `Core/Bases/sql_base.py`

| 例外 | 発生位置 | 代表的なシナリオ |
|------|----------|----------|
| `StorageError` | ストレージ層 | ストレージ関連の例外の基底クラス |
| `StorageUnreachableError` | プール構築段階 | データベースに到達できない / 認証情報が間違っている / ネットワークの隔離、リトライが尽きる |

> **ストレージ操作の失敗の意味**：KV とクエリ操作は**デフォルトで例外を送出しない**——失敗時には ERROR ログを記録し、`False` / `None` / `default` を返す（接続の問題がフレームワークの実行をブロックしないようにするため）。`StorageUnreachableError` は主にフレームワーク内部の冷却と再接続の判定に使用される。失敗を正確に感知したい場合は、戻り値を確認する。

接続失敗の動作は [ストレージバックエンド → 接続失敗の動作](storage-backends.md#接続失敗の動作) を参照。

### Interaction — `Core/Event/interaction.py`

`wait_reply` / セッションリース / アラートタイマ関連:

| 例外 | 発生位置 | 代表的なシナリオ |
|------|----------|----------|
| `InteractionError` | 交互セッション層 | 交互セッションの例外の基底クラス |

キャンセルされた場合（モジュールのアンロード / プラットフォームのシャットダウン / 同じセッションで新しい待機が上書き）には、`wait_reply` は**例外を送出せず、`None` を返す**。セッションリースが占有されている場合は `hold()` が `SessionOccupiedError`（`InteractionError` に継承）を送出する。

### Module 系列 — `Core/module.py`（`sdk.module.call`）

| 例外 | 発生位置 | 代表的なシナリオ |
|------|----------|----------|
| `ModuleError` | モジュールシステム | モジュールシステムの例外の基底クラス |
| `ModuleCallError` | `module.call()` | モジュール間呼び出しの例外の基底クラス |
| `ModuleNotAvailableError` | `module.call()` | 目標が登録されていない / 有効化されていない / 読み込みに失敗した |
| `ServiceNotProvidedError` | `module.call()` | 目標の `meta.services` ホワイトリストに該当するメソッドが宣言されていない |
| `ModuleCallTimeoutError` | `module.call()` | 呼び出されたコルーチンがタイムアウト時間（デフォルト 30s）を超えた |

```python
from ErisPulse.Core.Bases.errors import ModuleNotAvailableError, ServiceNotProvidedError

try:
    history = await sdk.module.call("Chat", "get_history", session_id, n=20)
except ModuleNotAvailableError:
    ...  # 目標モジュールが存在しない / 有効化されていない
except ServiceNotProvidedError:
    ...  # 目標モジュールが該当サービスを提供していない
```

### フレームワーク内部のパラメータ検証（ValueError）

ストレージクエリビルダーのパラメータ検証（空の列タイプ、`Insert` が dict でない、不安全な列タイプなど）は標準の `ValueError` を送出する——これは**開発時のコードミス**に属し、通常の業務コードではキャッチすべきではなく、呼び出しを修正すべきである。

## 捕獲の提案

```python
from ErisPulse.Core import ErisPulseError  # 基底クラスは Core から統合インポートされています

try:
    ...
except ErisPulseError as e:
    ...  # 統一的なデフォルト処理：フレームワークが定義する全ての独自例外
```

- モジュール開発：必要に応じて正確に例外をキャッチ（上記表参照）、最外層では `ErisPulseError` をデフォルトとして使用可
- 例外はすべて `ErisPulse.Core` から統合インポートされています。また、`ErisPulse.Core.Bases.errors` から個別にインポートすることも可能です。
- 完全な定義は `src/ErisPulse/Core/Bases/errors.py` を参照してください。