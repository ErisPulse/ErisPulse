# 設定ファイルの説明
> このドキュメントでは、フレームワークの設定ファイルについて説明します。サードパーティのモジュールに設定が必要な場合は、モジュールのドキュメントを参照してください。

ErisPulse は、`config/config.toml` という TOML 形式の設定ファイルを使用してプロジェクトの設定を管理します。

[**English**](docs/ja/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## 設定ファイルの位置

設定ファイルはプロジェクトのルートディレクトリの `config/` フォルダにあります：

```
project/
├── config/
│   └── config.toml
├── main.py
```

[**English**](docs/ja/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## 設定の読み込みエラー処理

フレームワークは `config.toml` を読み込む際に、3 種類のエラー状態を区別し、**操作可能な診断情報を提供**します。デフォルト設定に静かに回復するのではなく、明確なエラー情報を通知します。

| エラー状態 | 発生条件 | フレームワークの動作 |
|---------|---------|---------|
| ファイルが存在しない | `config.toml` が存在しない | 初回起動時は正常に空の設定を静かに使用（警告を出さない） |
| TOML 構文エラー | ファイルは存在するが、形式が不正（例：クォートが欠けている、括弧が閉じられていない） | **行番号/列番号と原因**を出力し、デフォルト設定に回復したことを通知 |
| 権限/その他のエラー | 読み取り権限がない、IO エラーなど | **明確な原因**を出力し、デフォルト設定に回復したことを通知 |

たとえば、誤って設定を `port = 8000`（クォートのない文字列）と記述した場合、ログには次のような内容が表示されます：

```
[ERROR] [Config] 設定ファイル config/config.toml の構文エラー（第 3 行 第 1 列）: ...
[WARNING] [Config] 設定ファイルの読み込みに失敗しました。前回の有効な設定を使用して続行します。今回のファイル変更は有効ではありません。修正後、再読み込みまたは再起動してください。
```

これにより、**INFO レベルのログ**で問題を即座に特定でき、「なぜ設定の変更が有効にならないのか」を混乱することなく把握できます。

> **実行中に設定ファイルを破損させた場合**？ ロボットが実行中、手動で `config.toml` を編集して構文エラーを導入した場合、フレームワークは次回の書き込み（設定のマージ）時に「設定ファイルが破損しました（構文エラー、第 X 行）、マージ書き込みできません。設定ファイルを修正した後に再起動してください」と出力します。混乱を招く「書き込みに失敗しました」ではなく、明確なメッセージを提供します。書き込み保留中の設定項目は保持され、失われることはありません。

## 環境変数による上書き

フレームワークは、環境変数を用いて `ErisPulse.*` の設定項目を**上書き**することをサポートしています（Docker / コンテナ化 / CI 部署に適しており、`config.toml` を変更する必要はありません）。

命名規則：ドット区切りのパス `ErisPulse.<section>.<key>` をすべて大文字にし、`.` を `_` に置き換え、`ERISPULSE_` をプレフィックスに追加します：

| 設定項目 | 環境変数 | 例値 |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `false` |

動作の説明：
- **優先度が最も高い**：環境変数は「設定ファイル」と「デフォルト値」を上書きし、元の値の型に応じて自動的に変換します（`bool` / `int` / `float` / カンマ区切りの `list` / 文字列）
- **永続化しない**：上書きは実行中にのみ有効であり、`config.toml` には書き戻されません
- **ホット更新をサポート**：実行中に環境変数を変更し、設定監視のリロードを組み合わせることで有効になります

```bash
# Docker 部署の例：config.toml を変更せず、直接ポートを上書き
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> 注：`ErisPulse.server.port` のようなフレームワークの設定は、`get_server_config()` などの API で読み取られ、すべて環境変数の上書きの影響を受けます。

## 設定のホットアップデート

2.7.0 以降、フレームワークは**システム化された**設定ホットアップデートをサポートするようになりました。`config.toml` を外部から変更した後（バックグラウンドの watcher が 5 秒ごとに検出します）、またはコードで `setConfig()` を呼び出した後、各コンポーネントは自動的に応答します：

| コンポーネント | ホットアップデートがサポートされる設定 | 挙動 |
|------|----------------|------|
| **ログ Logger** | `logger.level` / `log_files` / `memory_limit` / `format` | 自動的に再適用（変更検出付き） |
| **コマンドシステム CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | 次のメッセージで即座に有効化 |
| **アダプタの並行処理** | `framework.handler_max_concurrency` | 有効なキャッシュされた信号量を無効化し、新しい値で再構築 |
| **プロアクティブ GC** | `framework.proactive_gc_interval` | 各ラウンドで再読み込みし、実行時の調整/無効化が可能 |
| **マスターシステム Master** | `master.users` | `is_master()` 検査ごとにリアルタイムで読み込み、再起動不要 |
| **モジュール/アダプタの設定** | 各々の設定項目 | `on_config_update(old, new)` コールバックをトリガー |

**再起動が必要な設定**（安全にホット切り替えできないため、変更時に「プロセスを再起動後に有効になります」という警告が表示されます）：

| 設定 | 理由 |
|------|------|
| `router.cors.*` / `router.security.*` | ミドルウェアはサービス起動時に FastAPI に書き込まれており、実行時に安全にホット切り替えできない |
| `storage.use_global_db` | SQLite ファイルハンドルは実行時に既に開かれているため、パスを切り替えるのは安全ではない |

> **途中で編集保存に失敗した場合？** `config.toml` を編集する際に一時的な構文エラーが発生した場合、フレームワークは**前回の有効な設定を保持**し、診断ログを出力します。各コンポーネントに空の設定をブロードキャストすることはありません（`on_config_update` が空値を受け取り、誤ってデフォルト値に戻らないようにするため）。

[**English**](docs/ja/quick-start.md)

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

[**English**](docs/ja/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## ログ設定

```toml
[ErisPulse.logger]
level = "INFO"
log_files = ["app.log", "debug.log"]
memory_limit = 1000
```

| 設定項目 | タイプ | デフォルト値 | 説明 |
|---------|------|---------|------|
| level | string | INFO | ログレベル：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACE は最低レベルで、フレームワーク内部の詳細なデバッグ情報を出力） |
| format | string | rich | ログ出力形式：`rich`（カラー表示、デフォルト）、`plain`（カラーなしの純粋なテキスト、ログ収集/パイプリダイレクトに適している）、`json`（JSON形式、ELK などに適している） |
| log_files | array | 空 | ログ出力ファイルのリスト |
| memory_limit | integer | 1000 | メモリに保持するログの件数 |

[**English**](docs/ja/quick-start.md)

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
| uninit_timeout | integer | 30 | エレガントなシャットダウンの総タイムアウト時間（秒）、超過後は強制終了。0 はタイムアウトを設定しないことを意味する |
| strict_mode | integer | 0 | 厳格モードのレベル、下記「厳格モード」の説明を参照 |

### 厳格モード

厳格モードは、モジュール/アダプターがロード段階で不正または失敗した場合の処理戦略を制御します。現代のモジュール/アダプターはすべて対応する基底クラス（`BaseModule`/`BaseAdapter`）を継承する必要があります。基底クラスを継承していないコンポーネントは、フレームワークのコンテキストシステムとバックアップクリーンアップに影響を与え、リソースリークを引き起こす可能性があります。

> **2.5.2 変更**：デフォルトのレベルは `1`（スキップ）から `0`（緩和）に調整され、新規ユーザーが初期使用時に遭遇するロード問題を減らしました。基底クラスを継承していないコンポーネントは WARNING で提示され、ロードを試みるようになります。以前の動作を復元するには、`strict_mode = 1` を明示的に設定してください。

| レベル | 名称 | 行動 |
|------|------|------|
| 0 | 緩和（デフォルト） | 不正は警告のみ、基底クラスを継承していないコンポーネントもロードを試みる（旧コンポーネントとの互換性） |
| 1 | 厳格-スキップ | 基底クラスを継承していないコンポーネントを拒否しスキップし、他のコンポーネントは正常に起動する |
| 2 | 厳格-致命 | すべての不正を収集し、統一的に報告して起動を中止する |

各レベルにおいて、「ロード/登録/初期化段階でのエラー」はコンポーネント自身のクラッシュとして常にスキップされます。違いは以下の通りです：

- **0 → 1**：唯一の動作変更は「基底クラスを継承していない」が「ロードを続ける」から「スキップ」に変わる点です。
- **1 → 2**：すべての不正（基底クラスを継承していない、ロード失敗、登録失敗、初期化失敗など）が致命的となり、起動チェックポイントで収集された後に一括で不正リストを出力して起動を中止します。

#### 豁免リスト

一部のコンポーネントが一時的に移行できない場合（例えば依存する旧モジュールなど）、そのコンポーネントを豁免リストに追加することができます。リストに含まれるコンポーネントは、不正であっても緩和モードとして扱われ、ロードを継続します：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> 厳格モードによってコンポーネントが拒否された場合、ログには明確にロードを回復する方法（豁免リストに追加するか、レベルを下げること）が提示されます。

## ストレージ設定

```toml
[ErisPulse.storage]
use_global_db = false
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| use_global_db | boolean | false | プロジェクトデータベースではなく、ErisPulseパッケージ内に含まれるグローバルデータベースを使用するかどうか。`true` の場合、すべてのプロジェクトが ErisPulse パッケージ内の SQLite データベースを共有する。`false`（デフォルト）の場合は、各プロジェクトが `config/` ディレクトリ下に独立したデータベースを使用する。 |

[**English**](docs/en/quick-start.md) | [**日本語**](docs/ja/quick-start.md) | [**简体中文**](docs/ja/quick-start.md)

## イベントの設定

### コマンドの設定

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| prefix | string | / | コマンドのプレフィックス |
| case_sensitive | boolean | true | 大文字小文字を区別するかどうか（`/Help` と `/help` が異なるコマンドとして扱われるかどうか） |
| allow_space_prefix | boolean | false | 空白をプレフィックスとして許可するかどうか |
| must_at_bot | boolean | false | コマンドをトリガーするには必ず@botが必要かどうか（プライベートチャットは制限されない） |

### メッセージの設定

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| ignore_self | boolean | true | ロボット自身のメッセージを無視するかどうか |

[**English**](docs/ja/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## 国際化設定

```toml
[ErisPulse.i18n]
language = "auto"
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| language | string | auto | フレームワークの内部テキストの表示言語。`auto` に設定するとシステム言語を自動検出し、具体的な言語コード `zh-CN`、`zh-TW`、`en`、`ja`、`ru` を指定することも可能です。 |

[docs/ja/quick-start.md]

## モジュール設定

各モジュールは設定ファイルで独自の設定を定義できます：

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

モジュール内で設定を読み取り、書き込みます：

```python
from ErisPulse import sdk

# 設定の読み込み
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# 実行時での設定の書き込み（遅延保存）
sdk.config.setConfig("MyModule.timeout", 60)

# ファイルへの即時保存
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` はデフォルトで遅延書き込み（約5秒ごとに一括保存）が行われます。`immediate=True` を設定すると即時永続化されます。設定の変更は `config.set` ライフサイクルイベントをトリガーします。

[**English**](docs/en/quick-start.md) | [**中文**](docs/ja/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## 次に進む

- [CLI コマンドリファレンス](cli-reference.md) - すべてのコマンドラインコマンドの詳細を確認
- [開発者ガイド](../developer-guide/) - カスタムモジュールの開発方法を学ぶ

リンクの言語バージョンを正しく設定するため、`docs/ja/` は `docs/ja/` に置き換えてください。