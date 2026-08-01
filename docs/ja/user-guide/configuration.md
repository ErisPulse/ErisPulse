# 設定ファイルの説明
> このドキュメントでは、フレームワークの設定ファイルについて説明します。サードパーティのモジュールに設定が必要な場合は、モジュールのドキュメントを参照してください。

ErisPulse は、プロジェクトの設定を管理するために TOML 形式の設定ファイル `config/config.toml` を使用します。

## 設定ファイルの位置

設定ファイルはプロジェクトのルートディレクトリの `config/` フォルダ内にあります：

```
project/
├── config/
│   └── config.toml
├── main.py
```

## 設定ファイルの読み込みエラー処理

フレームワークは `config.toml` を読み込む際に、3つのエラー状態を区別し、**操作可能な診断情報**を出力します。これは、デフォルト設定に静かに回復するのではなく、明確なエラーメッセージを提供します。

| エラー状態 | 発生条件 | フレームワークの動作 |
|---------|---------|---------|
| ファイルが存在しない | `config.toml` が存在しない | 初回起動時は正常に動作し、空の設定（警告なし）で静かに使用 |
| TOML構文エラー | ファイルは存在するが形式が無効（例：引用符が足りない、括弧が閉じられていない） | **行番号/列番号と原因**を出力し、デフォルト設定に回復したことを通知 |
| 権限/その他のエラー | 読み取り権限がない、IOエラーなど | **明確な原因**を出力し、デフォルト設定に回復したことを通知 |

たとえば、設定を `port = 8000`（引用符が足りない文字列）と誤って記述した場合、ログには次のようなエラーが表示されます：

```
[ERROR] [Config] 設定ファイル config/config.toml の構文エラー（第 3 行 第 1 列）: ...
[WARNING] [Config] デフォルト設定に回復しました。カスタム設定は有効化されませんでした。修正後、再起動してください。
```

これにより、**INFOレベルのログ**でも問題を即座に特定でき、「なぜ設定を変更しても効果がないのか」を混乱させることはありません。

> **実行中に設定ファイルを誤って編集した場合**？ ロボットが実行中の間に `config.toml` を手動で編集して構文エラーを導入した場合、フレームワークは次回の書き込み（設定のマージ）時に「設定ファイルが破損しました（構文エラー、第 X 行）、マージ書き込みが不可能です。設定ファイルを修正してから再起動してください」と出力します。これは、混乱を招く「書き込み失敗」ではなく、明確なエラーメッセージです。書き込まれる設定項目は保持され、失われることはありません。

## 環境変数による上書き

フレームワークは、環境変数を使って `ErisPulse.*` 設定項目を**上書き**することをサポートしています（Docker / コンテナ化 / CI 部署に適しています。`config.toml` を変更する必要はありません）。

命名規則：`ErisPulse.<セクション>.<キー>` のドット区切りパスを、大文字にし、`.` を `_` に置換し、`ERISPULSE_` プレフィックスを追加します：

| 設定項目 | 環境変数 | 例値 |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `false` |

動作の説明：
- **優先度が最も高い**：環境変数は「設定ファイル」と「デフォルト値」を上書きし、元の値の型に応じて自動的に変換（`bool` / `int` / `float` / カンマ区切りの `list` / 文字列）
- **永続化されない**：上書きは実行中にのみ有効で、`config.toml` には書き戻されない
- **ホットアップデートをサポート**：実行中に環境変数を変更した後、設定監視のリロードを組み合わせれば即座に有効になります

```bash
# Docker 部署の例：config.toml を変更せずに、直接ポートを上書き
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> 注：`ErisPulse.server.port` のようなフレームワーク設定は、`get_server_config()` などの API で読み取られ、すべて環境変数の上書きの影響を受けます。

## 設定のホットアップデート

2.7.0 以降、フレームワークは**システム化された**設定のホットアップデートをサポートしています。外部で `config.toml` を変更した後（バックグラウンドの watcher が 5 秒ごとにチェック）、またはコードで `setConfig()` を呼び出した後、各コンポーネントは自動的に対応します：

| コンポーネント | ホットアップデートがサポートされる設定 | 動作 |
|------|----------------|------|
| **ログ Logger** | `logger.level` / `log_files` / `memory_limit` / `format` | 変更検出付きで自動的に再適用 |
| **コマンドシステム CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | 次のメッセージで即座に有効 |
| **アダプターの並行処理** | `framework.handler_max_concurrency` | 失効したキャッシュシグナルを破棄し、新しい値で再構築 |
| **プロアクティブ GC** | `framework.proactive_gc_interval` | 各ラウンドで再読み込みし、実行時の調整/無効化をサポート |
| **モジュール/アダプターの設定** | 各々の設定項目 | `on_config_update(old, new)` コールバックをトリガー |

**再起動が必要な設定**（安全にホット切り替えできないため、変更時に「プロセスを再起動後に有効になります」と警告が出力されます）：

| 設定 | 原因 |
|------|------|
| `router.cors.*` / `router.security.*` | ミドルウェアはサービス起動時に FastAPI に書き込まれており、実行中に安全にホット切り替えできない |
| `storage.use_global_db` | SQLite ファイルハンドルは実行時に既に開かれているため、パスの切り替えは安全ではない |

> **途中で編集保存に失敗した場合**？ `config.toml` を編集中に一時的な構文エラーが発生した場合、フレームワークは**前回の有効な設定を保持**し、診断ログを出力します。各コンポーネントに空の設定をブロードキャストすることはありません（`on_config_update` が空値を受信して誤ってデフォルトに戻るのを防ぐため）。

## 完全な設定例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.logger]
level = "INFO"
format = "rich"
log_files = []
memory_limit = 1000

[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []

[ErisPulse.storage]
use_global_db = false

[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false
must_at_bot = false

[ErisPulse.event.message]
ignore_self = true

[ErisPulse.i18n]
language = "auto"
```

## サーバー設定

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 監聴アドレス。0.0.0.0 はすべてのインターフェースを意味します |
| port | integer | 8000 | 監聴ポート番号 |
| ssl_certfile | string | 空 | SSL 証明書ファイルのパス |
| ssl_keyfile | string | 空 | SSL 秘密鍵ファイルのパス |

## ログ設定

```toml
[ErisPulse.logger]
level = "INFO"
log_files = ["app.log", "debug.log"]
memory_limit = 1000
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| level | string | INFO | ログレベル：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACE は最低レベルで、フレームワーク内部の詳細なデバッグ情報を出力します） |
| format | string | rich | ログ出力形式。デフォルトでは rich のカラーログを使用します |
| log_files | array | 空 | ログ出力ファイルのリスト |
| memory_limit | integer | 1000 | メモリ内に保持するログの件数 |

## フレームワーク設定

```toml
[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | モジュールの遅延ロードを有効にするかどうか |
| uninit_timeout | integer | 30 | エレガントなシャットダウンの合計タイムアウト時間（秒）。超過すると強制終了します。0 はタイムアウトを設定しないことを意味します |
| strict_mode | integer | 0 | 厳格モードのレベル。下記の「厳格モード」の説明を参照してください |

### 厳格モード

厳格モードは、モジュール/アダプターがロード段階で不正な状態や失敗した場合の処理戦略を制御します。モダンなモジュール/アダプターは、それぞれの基底クラス（`BaseModule`/`BaseAdapter`）を継承する必要があります。基底クラスを継承していないコンポーネントは、フレームワークのコンテキストシステムとバックアップクリーンアップに影響を与え、リソースリークを引き起こす可能性があります。

> **2.5.2 変更**：デフォルトレベルは `1`（スキップ）から `0`（緩和）に変更され、新規ユーザーが初めて使用する際に発生するロード問題を減らしました。基底クラスを継承していないコンポーネントは、WARNING として警告を表示し、ロードを試みます。以前の動作を復元するには、`strict_mode = 1` を明示的に設定してください。

| レベル | 名称 | 動作 |
|------|------|------|
| 0 | 緩和（デフォルト） | 不正は警告のみ。基底クラスを継承していないコンポーネントもロードを試みます（旧コンポーネントとの互換性） |
| 1 | 厳格-スキップ | 基底クラスを継承していないコンポーネントを拒否してスキップし、他のコンポーネントは正常に起動します |
| 2 | 厳格-致命 | すべての不正を収集して一括で報告し、起動全体を中止します |

各レベルで、「ロード/登録/初期化段階でエラーが発生した」コンポーネントの自身のクラッシュは常にスキップされます。違いは以下の通りです：

- **0 → 1**：唯一の動作変更は、「基底クラスを継承していない」コンポーネントが「ロードする」から「スキップする」に変わる点です。
- **1 → 2**：すべての不正（基底クラスを継承していない、ロード失敗、登録失敗、初期化失敗など）が致命的になり、起動チェックポイントで一括で不正リストを出力して中止します。

#### 豁免リスト

一部のコンポーネントが一時的に移行できない場合（依存する旧モジュールなど）、豁免リストに追加することで、不正なコンポーネントでも緩和モードとして扱われ、ロードを続けます：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> あるコンポーネントが厳格モードで拒否された場合、ログにはロードを回復する方法（豁免リストに追加するか、レベルを下げること）が明確に示されます。

## ストレージ設定

```toml
[ErisPulse.storage]
use_global_db = false
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| use_global_db | boolean | false | プロジェクトデータベースではなく、ErisPulse パッケージ内のグローバルデータベースを使用するかどうか。`true` の場合、すべてのプロジェクトは ErisPulse パッケージ内の SQLite データベースを共有します。`false`（デフォルト）の場合は、各プロジェクトは `config/` ディレクトリ内に独立したデータベースを使用します |

## イベント設定

### コマンド設定

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| prefix | string | / | コマンドのプレフィックス |
| case_sensitive | boolean | true | 大文字小文字を区別するかどうか（`/Help` と `/help` が異なるコマンドになるかどうか） |
| allow_space_prefix | boolean | false | プレフィックスにスペースを許可するかどうか |
| must_at_bot | boolean | false | コマンドをトリガーするには必ず@機械である必要があるかどうか（プライベートチャットは制限されません） |

### メッセージ設定

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| ignore_self | boolean | true | ロボット自身のメッセージを無視するかどうか |

## 国際化設定

```toml
[ErisPulse.i18n]
language = "auto"
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| language | string | auto | フレームワークの内部テキストの表示言語。`auto` に設定するとシステム言語を自動検出します。具体的な言語コード（`zh-CN`、`zh-TW`、`en`、`ja`、`ru`）を指定することもできます |

## モジュール設定

各モジュールは、設定ファイルで独自の設定を定義できます：

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

モジュール内で設定を読み取り、書き込みます：

```python
from ErisPulse import sdk

# 設定の読み取り
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# 実行時に設定を書き込み（遅延保存）
sdk.config.setConfig("MyModule.timeout", 60)

# ファイルに即時保存
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` はデフォルトで遅延書き込み（約 5 秒ごとに一括保存）され、`immediate=True` を設定すると即時永続化されます。設定の変更は `config.set` のライフサイクルイベントをトリガーします。

## 次に進む

- [CLI コマンドリファレンス](cli-reference.md) - すべてのコマンドラインコマンドを確認
- [開発者ガイド](../developer-guide/) - 自作モジュールの開発方法を学ぶ