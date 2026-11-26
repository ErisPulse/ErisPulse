# 設定ファイルの説明

> [!NOTE]
> **L1コア必読**——ホーム画面の「読む経路」にある5つのコアドキュメントの1つで、モジュール開発に必須です。

> このドキュメントでは、フレームワーク自身の設定ファイル `config/config.toml` について説明します：各設定セクションが何を管理するのか、どの設定がホットアップデートをサポートするのか、環境変数でどのように上書きするのか。サードパーティのモジュールの設定項目は、モジュール固有のドキュメントを参照してください。

ErisPulseは、TOML形式の設定ファイル `config/config.toml` を使用してプロジェクトの設定を管理します。

## 設定ファイルの位置

設定ファイルはプロジェクトルートの `config/` フォルダ内にあります：

```
project/
├── config/
│   └── config.toml
├── main.py
```

### 複数インスタンスの注意点とロックファイル

フレームワークが起動する際、プロジェクトルートの実行ステータスディレクトリ **`.erispulse/`** 内に `config.lock` ロックファイルを作成し、プロセス終了まで保持します（複数インスタンスが設定ディレクトリを共有していることを検出するため；2.10以前は `config/` ディレクトリの `.erispulse_config.lock` が、アップグレード後に最初の起動時に自動的に削除されます）。ログに「設定ファイルが他のErisPulseインスタンスによって同時に使用されている可能性がある」という警告が表示された場合、**2つ以上のErisPulseプロセスが同じ設定ファイルを書き込んでいる**（典型的なシナリオ：複数のコンテナが同じホストの `config/` ディレクトリをマウントしている）ことを意味します。並行書き込みはお互いに上書きするため、各インスタンスに独立した設定ディレクトリを使用してください。

### 敏感な設定はバージョン管理に含めない

設定ファイルにはトークン（token/API key）などの機密情報が含まれます：フレームワークの初期化と `epsdk init` は自動的に `config/` ディレクトリに `.gitignore` を生成します（内容は一行のみ `*`——**ディレクトリ内のすべてのファイルをバージョン管理から除外し、除外ファイル自身も除外対象になります**）；既存の `.gitignore` は上書きされません。`.erispulse/` 実行ステータスディレクトリ（インスタンスロック、CLI実行ステータスファイル）はローカルマシンのステータスに属し、プロジェクトテンプレートの `.gitignore` は既定で除外されています。

## 設定の読み込みエラー処理

フレームワークは `config.toml` を読み込む際に3つのエラー状態を区別し、**操作可能な診断情報を提供**します。デフォルト設定に静かに回帰するのではなく、警告を出力します。

| エラー状態 | 発生条件 | フレームワークの動作 |
|---------|---------|---------|
| ファイルが存在しない | `config.toml` が存在しない | 正常な初回起動で、空の設定を使用する（警告を出さない） |
| TOML構文エラー | ファイルは存在するが形式が不正（例：クォートが足りない、括弧が閉じていない） | **行番号/列番号と原因**を出力し、**前回の有効な設定を保持して実行を継続**（今回のファイルの変更は有効にならない） |
| 権限/その他のエラー | 読み取り権限がない、IOエラーなど | **明確な原因**を出力し、**前回の有効な設定を保持して実行を継続** |

> **「前回の有効な設定」＝デフォルト設定ではない**：ファイルが破損した場合、フレームワークは**今回の起動前の最後に解析成功した設定**（実行中にホットアップデートでファイルを壊した場合は古い値を使用）を使用します。故障処置の際、「設定がリセットされた」と仮定しないでください。

たとえば、`config.toml` を `port = 8000`（クォートのない文字列）として誤って書いた場合、ログには次のような出力がされます：

```
[ERROR] [Config] 設定ファイル config/config.toml の構文エラー（第 3 行 第 1 列）: ...
[WARNING] [Config] 設定ファイルの読み取りに失敗しました。前回の有効な設定を使用して実行を継続します。今回のファイルの変更は有効になりません。修正後、再読み込みまたは再起動してください。
```

このように、**デフォルトのINFOレベル**で問題をすぐに特定でき、「なぜ設定を変更しても効果がないのか」を混乱させません。

> **実行中に設定ファイルを壊してしまった？** ロボットが実行中に `config.toml` を手動で編集して構文エラーを導入した場合、フレームワークは次回の書き込み（設定のマージ）時に「設定ファイルが壊れています（構文エラー、第 X 行）、マージ書き込みができないため、設定ファイルを修正してから再起動してください」と出力します。これは「書き込みに失敗しました」という混乱を招くものではありません。書き込まれる設定項目は保持され、失われることはありません。

## コメントの保持と最小限の書き込み

config.toml 内の**コメントとキーの順序は、フレームワークが書き込んだ後も完全に保持されます**：コード `setConfig()`、CLI設定ウィザードの保存、またはアダプタ/モジュールの初期設定テンプレートの生成など、フレームワークは関連するキーだけを変更し、ユーザーが書いたコメントや整理された順序は削除や再配置されません（tomlclass による無損失TOMLエンジンを使用し、未触れた内容はバイト単位で保証され、ファイルの元のCRLF/LF改行スタイルも変更されません）。

フレームワークは書き込み内容を最小限に抑えています：

- **フレームワークのデフォルト設定は自動的に書き込まれません**：`gc`、`scope`、`transcript` などの組み込みデフォルト値はメモリ内に駐留し、config.toml には明示的に設定されたキーのみが含まれ、最小限になります。完全な設定項目はプロジェクト内の `config/config.full.example` を参照し、必要に応じて config.toml にコピーして変更してください（未設定の項目は一律組み込みデフォルト値を使用し、動作は変わりません）。
- **`config.full.example` の自動維持**：`epsdk init` を実行したかどうかに関わらず、フレームワークを起動するたび（`epsdk run` / `main.py`）に、`config/config.full.example` が欠落している場合は自動的に生成されます。ファイルの先頭行はフレームワークが自動的に維持するマークであり、生成器の内容が更新された場合（新しい設定項目、新しいコンポーネントの追加など）は、起動時に1回更新されます。先頭行を削除/変更すると手動で管理するようになり、フレームワークは上書きしません。
- **アダプタ/モジュールの設定テンプレート**：初期化時にコメント付きのテンプレートとしてファイルに書き込まれます（フィールドの説明がコメントになります）。`example` というマークが付いているフィールドは書き込まれず、`config.full.example` に記録され、参考としてのみ使用されます。
- **宣言的なコメントの再読**：設定ファイル内のコメントはドキュメントそのものになります。`ep doctor` と設定検証の失敗通知は、該当フィールドのファイル内のコメントを原文として引用します（手動でコメントを変更しても、通知はファイルの現状に従います）。エラー時に設定項目の意味を再びドキュメントを調べる必要はありません。

## 環境変数による上書き

フレームワークは環境変数を**用いて `ErisPulse.*` 設定項目を上書き**することをサポートしています（Docker / コンテナ化 / CI 部署に適しています。`config.toml` を変更する必要はありません）。

命名規則：点分パス `ErisPulse.<section>.<key>` をすべて大文字にし、`.` を `_` に置き換え、`ERISPULSE_` を接頭辞として付けます：

| 設定項目 | 環境変数 | 例値 |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `2` |

動作の説明：

- **優先度が最も高い**：環境変数は「設定ファイル」および「デフォルト値」を上書きし、元の値の型に応じて自動変換されます（`bool` / `int` / `float` / カンマ区切りの `list` / 文字列）
- **永続化されない**：上書きは実行中にのみ有効であり、`config.toml` には書き込まれません
- **ホットアップデートをサポート**：実行中に環境変数を変更した後、設定監視のリロードを組み合わせることで有効になります

```bash
# Dockerデプロイの例：config.tomlを変更せず、直接ポートを上書き
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> 注：`ErisPulse.server.port` などのフレームワーク設定は `get_server_config()` などのAPIで読み取られ、環境変数の上書きの影響を受けます。

### モジュール設定の環境変数バインディング（2.9.0+）

モジュール自身の宣言的設定（`ConfigClass`）は、フィールドレベルの環境変数バインディングをサポートしています——`field(metadata=...)` で `env` を宣言します：

```python
@dataclass
class MyConfig(BaseConfig):
    api_key: str = field(default="", metadata={
        "description": "APIキー",
        "env": "MYMODULE_API_KEY",   # 環境変数バインディング
    })
    retries: int = field(default=3, metadata={"env": "MYMODULE_RETRIES"})
```

動作の説明：

- **優先度**：環境変数 > `config.toml` > 宣言時のデフォルト値（設定ファイルのホットアップデート後もこの優先度を維持）
- **型変換**：環境変数の値はフィールドの注釈に応じて自動変換されます——`str` はそのまま、`int` / `float` / `bool`（`true` / `1` / `yes` / `on`）は自動変換、`list` / `dict` はJSON解析を経ます；変換に失敗した場合はその上書きを無視し（デフォルト値に戻り）、警告を出力します
- **宣言1つ、どこでも有効**：設定の読み取り、ホットアップデート、検証で同じパイプラインを使用します；設定パネルのSchemaは `env` 名をマークし、`config.toml` テンプレートのコメントは利用可能な環境変数を示します（テンプレートは環境変数の実際の値を書き込まないため、漏洩を回避）
- **完全な互換性**：`env` を宣言していないフィールドの動作は変わりません；フレームワークの設定パイプラインを経ないConfigClassの直接インスタンス化は環境変数の影響を受けません

```bash
# Dockerデプロイの例：config.tomlを変更せず、モジュールのAPIキーを注入
MYMODULE_API_KEY=sk-xxx docker compose up -d
```

> **設定クラス vs モデルフィールド どちらを使うか？** 設定クラスは「モジュールがどのように動作するか」（動作パラメータ、ホットアップデート）を管理し、ORMの `Field()` は「ユーザーがどのようなデータを生成したか」（データベーステーブル、クエリ）を管理します。両者は同一の制約語彙と検証エンジンを使用します；対照表は [データモデル層 · どちらの宣言を使うか](../developer-guide/orm.md#どちらの宣言を使うか) を参照してください。

## 設定のホットリロード

2.7.0 から、フレームワークは設定ホットリロードを**体系的にサポート**しています。外部で `config.toml` が変更された後（バックグラウンド watcher が 5 秒ごとに検出）、またはコードから `setConfig()` が呼び出された後、各コンポーネントが自動的に応答します：

| コンポーネント | ホットリロード対応の設定 | 動作 |
|------|----------------|------|
| **ロガー Logger** | `logger.level` / `log_files` / `log_dir`（分割系パラメータを含む）/ `memory_limit` / `total_memory_limit` / `format` / `exclude_levels` | 自動的に再適用（変更検出あり） |
| **コマンドシステム CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | 次のメッセージから有効 |
| **アダプターの並行処理** | `framework.handler_max_concurrency` | キャッシュ済みセマフォを無効化し、新しい値で再構築 |
| **プロアクティブ GC** | `framework.proactive_gc_*` | 設定変更で即座に GC タスクを再起動、実行時の調整/無効化/再有効化に対応 |
| **イベント重複排除/クロスアカウント** | `framework.event_dedupe` / `cross_account_policy` | 遅延キャッシュ無効化、次のイベントで新しい値を再読み込み |
| **セッションアカウントバインディング** | `framework.session_accounts` | イベントごとにリアルタイム読み取り、変更は即座に有効 |
| **メモリトレーシング** | `framework.memory_tracing` | 次のプロアクティブ GC ラウンドで有効（tracemalloc はフレーム数を安全にホットリセットできないため） |
| **マスターシステム Master** | `master.users` | `is_master()` のチェックのたびにリアルタイム読み取り、再起動不要 |
| **モジュール/アダプター設定** | それぞれの設定項目 | `on_config_update(old, new)` コールバックをトリガー |

**再起動が必要な設定**（安全にホットスイッチできないため、変更時には「プロセス再起動後に有効化」という警告を出力します）：

| 設定 | 理由 |
|------|------|
| `router.cors.*` / `router.security.*` | ミドルウェアはサービス起動時に FastAPI へ登録されるため、実行時に安全にホットスイッチできない |
| `storage.use_global_db` | SQLite のファイルハンドルが実行時に既に開かれているため、パスの切り替えは安全でない |
| `storage.sqlite.busy_timeout` | busy_timeout は PRAGMA により接続確立時に適用されるため、既に開いている接続は設定に応じて更新されない |

> **編集中の保存でエラーが出る？** `config.toml` の編集中に一時的な構文エラーが発生した場合、フレームワークは**前回の有効な設定を保持**し、診断ログを出力します。空の設定を各コンポーネントへブロードキャストすることはありません（`on_config_update` が空の値を受け取って誤ってデフォルトへ戻るのを防ぐため）。

### ホットリロードパイプラインの内部解説

「設定を変更したのに、各コンポーネントはどうやって知るのか？」——その背後には、検出 → リロード → ブロードキャストという一連のパイプラインがあります：

```mermaid
flowchart TD
    A["外部で config.toml を編集"] --> B{"誰が先に検知する？"}
    B -->|"バックグラウンド watcher スレッド<br/>5 秒ごとに mtime をポーリング"| C["_check_file_change が変更を判定"]
    B -->|"コードが設定を読む際<br/>キャッシュが 60 秒超過"| C
    C --> D["_load_config が TOML を再パース"]
    D --> E{"パース成功？"}
    E -->|"いいえ（構文エラー）"| F["前回の有効な設定を保持<br/>ブロードキャストせず、診断ログを出力"]
    E -->|"はい"| G["lifecycle.emit config.updated<br/>old_config / new_config を伴う"]
    G --> H["各コンポーネントのリスナーが応答<br/>（logger / scope / コマンド / GC ...）"]
```

**2 つの検出パス**（どちらか一方で十分であり、双方ともセーフティネットとして機能します）：

| パス | 仕組み | 発火タイミング |
|------|------|---------|
| バックグラウンド watcher | デーモンスレッド `config-watcher` が **5 秒**ごとに `wait` でファイルの `mtime` をポーリング | 外部でファイル変更後、最大 5 秒以内 |
| 遅延検出 | `getConfig()` の読み取り時に、キャッシュが **60 秒**を超えていれば先にファイルを確認 | 次に設定を読み込むとき |

> **フレームワークは自分自身の書き込みを誤検知しない**：`setConfig()` がディスクへ書き込む際に「自身が書き込んだ mtime」を記録し、watcher は比較時にそれを除外するため、**外部編集**のみを変更として扱います。

**2 種類の設定変更イベント：**

| イベント | トリガー元 | データ | 典型的なシナリオ |
|------|--------|------|---------|
| `config.set` | コード / Dashboard が `setConfig()` を呼び出し | `{key, old_value, new_value}` | 単一キーの書き込み（テンプレート生成、状態記録、実行時の設定変更） |
| `config.updated` | 外部編集を watcher/遅延検出が捕捉 | `{old_config, new_config, config_file}` | 手動での `config.toml` 編集 |

> `setConfig()` はデフォルトで**ディスクへの書き込みを 5 秒遅延**させ（複数回の書き込みを統合）、`immediate=True` で即時書き込みします。watcher は外部変更を検出するとメモリキャッシュのみを更新し、外部の変更をファイルへ書き戻すことは**ありません**。

**自動応答コンポーネント一覧**（通常は両方のイベントを購読し、応答内容は同一です）：

| コンポーネント | 購読イベント | 応答 |
|------|------|------|
| Logger | `config.set` + `config.updated` | レベル/ファイル/ディレクトリ分割/メモリ上限/フォーマット/除外レベルを再適用（変更検出あり、変化がなければ何もしない） |
| Scope | `config.updated` | スコープバインディングキャッシュの再構築 |
| コマンドシステム | `config.updated` | プレフィックス/大文字小文字区別/スペースプレフィックス/must_at_bot のパースパラメータを更新、次のメッセージから有効 |
| アダプターの並行処理 | `config.set` + `config.updated` | `handler_max_concurrency` のセマフォを無効化して再構築 |
| プロアクティブ GC | `config.set` + `config.updated` | `proactive_gc_*` により GC バックグラウンドタスクを即時再起動 |
| アダプター | `on_config_update` へルーティング | 各アダプターの `on_config_update(old, new)` コールバック |
| モジュール | `on_config_update` へルーティング | 各モジュールの `on_config_update(old, new)` コールバック |
| ストレージ | `config.updated` | `use_global_db` の変更は**警告のみ**（再起動が必要） |
| ルーティング | `config.updated` | `cors.*` / `security.*` の変更は**警告のみ**（再起動が必要） |

## 設定の読み取りと削除API

### getAllConfig：全量設定スナップショット

プライベート `_cache` を直接読み取るのを代替します（外部でプライベート属性を読み取るのはバージョン互換性の保護を受けません）：

```python
config = sdk.config.getAllConfig()     # 深いコピーのスナップショット、直接編集してもフレームワークの状態に影響しない
config["ErisPulse"]["server"]["port"]
```

ビューの口径は `getConfig` と同じ：`setConfig` / `delete` による遅延書き込みも反映され、ファイルの内容と厳密に一致します。

### delConfig：設定キーの削除

`setConfig(key, None)` は値を空に設定するだけで、キーはファイルに残ります。`delConfig` はキーをファイルから**削除**します：

```python
sdk.config.delConfig("ErisPulse.modules.status.OldModule")            # 遅延で書き込み
sdk.config.delConfig("OneBot.deprecated_key", immediate=True)         # 即時でファイルに書き込み
```

- 点分パスをサポート；キーが存在しない場合は `False` を返す
- 書き込みはコメント保持の経路を使用し、ファイルの他の内容や順序は影響を受けない
- `config.set` イベントのブロードキャストを再利用（`new_value=None`）：アダプタ/モジュールの `on_config_update` などの既存のリスナーは変更なしで削除を感知できる

## 完全な設定例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.master]
# users は2つの書き方に対応しています（いずれか一方を選択）：
#   グローバルマスター（すべてのプラットフォームに有効）：users = ["123456", "789012"]
#   プラットフォームごとにマスターを指定：users = { yunhu = ["123456"], telegram = ["789012"] }
users = {}

[ErisPulse.logger]
level = "INFO"
format = "rich"
log_files = []
log_dir = "logs"
log_rotation = "size"
log_max_size_mb = 10
log_backup_count = 5
log_rotation_when = "midnight"
memory_limit = 1000
exclude_levels = []

[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []

[ErisPulse.storage]
backend = "sqlite"
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
auto_start = true
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
# コンテナ / ファイルマウントがない環境では、内側にPEMの内容を埋め込むことができます（ssl_certfile/ssl_keyfileのパスより優先されます）
# ssl_cert = """-----BEGIN CERTIFICATE-----
# ...
# -----END CERTIFICATE-----"""
# ssl_key = """-----BEGIN PRIVATE KEY-----
# ...
# -----END PRIVATE KEY-----"""
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 監視するアドレス、0.0.0.0はすべてのインターフェースを意味します |
| port | integer | 8000 | 監視するポート番号 |
| auto_start | boolean | true | `sdk.init()` 時にルーティングサーバーを自動的に起動するかどうか。`false`に設定するとルーティングサーバーの起動をスキップします（純イベント/無WebUIのシーン） |
| ssl_certfile | string | 空 | SSL証明書ファイルのパス |
| ssl_keyfile | string | 空 | SSL秘密鍵ファイルのパス |
| ssl_cert | string | 空 | **内側にPEM証明書の内容を埋め込む**（パスではなく）。`ssl_key`とペアで使用する場合、`ssl_certfile`/`ssl_keyfile`のパスよりも優先されます；フレームワークはSSLコンテキストを構築するために一時的にファイルを書き込んでからすぐに削除します |
| ssl_key | string | 空 | **内側にPEM秘密鍵の内容を埋め込む**（パスではなく）、上記と同じ意味 |

> **ポートの占有は致命的なエラーではない**：起動時に `port` が既に占有されていることが検出された場合、フレームワークはルーティングサーバーの起動をスキップして警告を出力し、**アダプタとモジュールは通常通り動作します**（HTTP/WS/SSEルーティングとWebUIは利用できません）。ロボットは動くがWebUIが開かないという問題を解決する際には、まずポートを確認してください。

## マスターシステムの設定

マスターシステムはフレームワークのマスター（Bot管理者）アカウントを識別するために使用されます。`master.users` は3種類の書き方をサポートしています：

```toml
[ErisPulse.master]
# 書き方1：グローバルマスター（すべてのプラットフォームに適用、後で追加されるプラットフォームも含む）
users = ["123456", "789012"]

# 書き方2：プラットフォームごとにマスターを指定（dict）
# users = { yunhu = ["123456"], telegram = ["789012"] }

# 書き方3：グローバルマスターとプラットフォーム専用マスターを共存させる——dict中の global キーがグローバルマスターバケツ
# users = { global = ["123456"], yunhu = ["789012"] }
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| users | array / object | 空 | マスターアカウントのリスト。`list` 形式はグローバルマスター（すべてのプラットフォームに適用）；`dict` 形式はプラットフォームごとに指定（キーがプラットフォーム名、`global` キーがグローバルマスターバケツ）、値はそのプラットフォームのマスターアカウントのリスト |

> **新しいプラットフォームについて**：`list` 形式と `dict` 中の `global` バケツはどちらも「1度定義すればすべてのプラットフォームに適用される」ため、後で新しいプラットフォームを接続する際にも設定を変更する必要はありません。プラットフォーム専用の項目は、同名（またはワイルドカード寛容一致）のプラットフォームにのみ適用されます。`master.add(None, uid)` は永続化時に `global` バケツに書き込まれ、既存のプラットフォームの項目は影響を受けません。

コードでは `master.is_master(event)` または `master.is_master(platform, user_id)` を使って確認し、毎回呼び出すたびにリアルタイムで設定を読み取ります（ホットアップデートに対応し、再起動は不要）：

```python
from ErisPulse.Core import master

if master.is_master(event):
    await event.reply("マスター、こんにちは")
```

### 判定チェーンと実行時追加

マスター判定チェーンは **設定マスター → 実行時記録 → providerチェーン** です：

```python
from ErisPulse.Core import master

master.is_master(event)                      # イベントから判定
master.is_master("yunhu", "123")             # 明示的に判定
master.add("yunhu", "123")                   # 実行時に追加（デフォルトで永続化；persist=Falseはメモリ内のみ）
master.remove("yunhu", "123")                # 削除（デフォルトで永続化）
master.list()                                # マージ：{"global": [...], "<platform>": [...]}
```

### 自作アイデンティティソース（provider）

設定の他に、独自のアイデンティティソースを登録できます：`fn(platform, user_id) -> bool`。組み込みのアイデンティティソース（設定 + 実行時記録）がヒットしなかった場合、順次試行され、いずれかが許可された場合、マスターと判定されます。適切なアダプターの管理者インターフェース、データベースのロールなど、外部のアイデンティティ体系に接続するのに適しています。

登録エントリ `master.provider` はデコレータ / 関数式の2種類の書き方ができ、登録された関数の上にある `fn.unregister()` で登録解除ができます：

```python
from ErisPulse.Core import master

# 書き方1：デコレータ（常駐アイデンティティソース、推奨）
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # 自作の判定ロジック

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # 不要になったら登録解除

# 書き方2：関数式（モジュールロード期に登録 / アンロード期に登録解除）
fn = master.provider(admin_provider)
fn.unregister()
```

> providerの例外はキャッチされ、スキップされ、アイデンティティ判定チェーンをブロックしません。インスタンスメソッドをバインドした関数は `unregister` が付与されないため、登録/登録解除のペアが必要な場面では**モジュールレベルの関数**を使用してください。

### ユーザー優先：マスターチェーンの有効範囲はユーザーが最終決定

コマンドの `master=True` は**開発者のデフォルト**です：ユーザーは
`ErisPulse.event.overrides.command.<module>.<cmd>.master = true/false`
で、厳格化または緩和を上書きできます（[統一イベントオーバーライド設定](#統一イベントオーバーライド設定eventoverrides)を参照、ユーザーの明示的な設定が有効）。

## ログ設定

```toml
[ErisPulse.logger]
level = "INFO"
log_files = []                # 明示的なログファイルリスト（log_dir と排他、優先度高）
log_dir = "logs"                  # ログディレクトリ（設定後は自動で分割ローテーション）
log_rotation = "size"         # 分割方式: "size" / "date" / "none"
log_max_size_mb = 10          # size モードの単一ファイル上限（MB）
log_backup_count = 5          # 保持する過去ログファイル数
log_rotation_when = "midnight"  # date モードのローテーション周期: S/M/H/D/midnight
memory_limit = 1000             # 単一モジュールのメモリログ件数上限（0 = メモリログコピー無効）
total_memory_limit = 5000       # 全モジュールのメモリログ合計件数上限（0 = 無制限）
exclude_levels = ["EVENT"]
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| level | string | INFO | ログレベル：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACE が最低レベルで、フレームワーク内部の詳細なデバッグ情報を出力） |
| format | string | rich | ログ出力フォーマット：`rich`（カラー、デフォルト）、`plain`（色なしのプレーンテキスト、ログ収集/パイプのリダイレクトに適する）、`json`（JSON 構造化、ELK などに適する） |
| log_files | array | 空 | ログ出力ファイルのリスト（明示的なパス、分割なし） |
| log_dir | string | "logs" | ログ出力ディレクトリ（自動作成）。設定するとディレクトリ内の `erispulse.log` に書き込み、`log_rotation` に従って自動分割；`log_files` と排他で、`log_files` が優先 |
| log_rotation | string | size | 分割方式：`size`（サイズ別）/ `date`（時間別）/ `none`（分割なし） |
| log_max_size_mb | float | 10 | size モードの単一ファイルサイズ上限（MB）。超過すると `.1`/`.2` のバックアップにローテーション |
| log_backup_count | integer | 5 | 保持する過去ログファイル数。超えた分の最も古いバックアップは自動削除 |
| log_rotation_when | string | midnight | date モードのローテーション周期：`S`/`M`/`H`/`D`/`midnight`（デフォルトは毎日 0 時） |
| memory_limit | integer | 1000 | 単一モジュールのメモリに保存されるログ件数；`0` はメモリログコピーを無効化（メモリへの書き込みを停止、既存の記録は保持） |
| total_memory_limit | integer | 5000 | 全モジュールのメモリログ合計件数上限；`0` は無制限。上限超過時はローテーション戦略に従って最も古い記録を破棄（件数が最も多いモジュールのキューを優先的に削減）。単一モジュールの `memory_limit` とは独立して機能 |
| exclude_levels | array | 空 | 指定したログレベルをブロック。ブロックされたレベルのログは**完全に破棄**されます（メモリに書き込まず、Dashboard などのサブスクライバーにプッシュせず、コンソールに出力せず、ファイルに書き込まない）。ホットアップデート対応 |

コードで動的に切り替えることも可能です：

```python
from ErisPulse.Core import logger

# サイズ別分割：単一ファイル 10MB、5 世代保持
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# 時間別分割：毎日 0 時にローテーション、7 世代保持
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]
> `log_dir` および分割関連の設定には ErisPulse **2.8.0+** が必要です。

> **プライバシー保護**：メッセージの送受信内容は **EVENT レベル**（数値 21）で記録されます。`exclude_levels = ["EVENT"]` を設定するだけで、バックエンド（Dashboard のログパネルなど）から各グループ/個人チャットのメッセージ内容が見えなくなり、他のレベルのログには影響しません。

設定ファイル（ホットアップデート対応）の他に、実行時にコードで同等の機能に切り替えることも可能です――`/privacy on|off` のような管理コマンドを実装する際には、設定ファイルを書く必要がありません：

```python
from ErisPulse import logger

logger.exclude_level("EVENT")        # 実行時に特定レベルをブロック（exclude_levels 設定と同じセマンティクス）
logger.allow_level("EVENT")          # そのレベルを復元
logger.list_excluded_levels()        # 現在ブロックされているレベルを確認
logger.set_format("json")            # 出力を JSON 行プロトコルに切り替え（format 設定キーと同じ効果）
```

> [!NOTE]
> `exclude_levels` のこの機能には ErisPulse **2.8.0+** が必要です。

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
| uninit_timeout | integer | 30 | グレースフルシャットダウンの合計タイムアウト時間（秒）、超過すると強制終了。0 はタイムアウトなしを意味する |
| strict_mode | integer | 0 | 厳格モードのレベル、下記「厳格モード」の説明を参照 |
| handler_max_concurrency | integer | 64 | イベントハンドラーの最大同時実行 Task 数、大きくするとスループットが向上するがメモリ使用量が増加する |
| handler_queue_max_pending | integer | 4096 | イベント急増時のキューイングバックプレッシャー：プラットフォームごとの未処理 handler Task 数の上限、超過時は新規イベントのハンドラー Task を直接破棄し WARNING を記録（破棄数は troubleshoot での調査時に確認可能）；`0` は無制限を意味する |
| offline_bot_expiry | integer | 3600 | オフライン Bot 記録の自動失効時間（秒）、0 は失効しないことを意味する |
| plugins_dir | string / list | "plugins" | ローカルプラグインフォルダー（プロジェクトルート相対）；プラグインファイルの追加/削除/変更はホットリロード watcher が自動検出する |
| watch_ignore_dirs | list | 内蔵リスト | ホットリロードのファイル監視で無視するディレクトリ名（`.venv`/`.git`/`__pycache__` など）；空でないリストを指定すると内蔵リストを**全体置き換え**し、`[]` はどのディレクトリも無視しないことを意味する |
| watch_include_plugin_dirs | boolean | true | `epsdk run --reload` がプラグインディレクトリをプラグイン用ホットリロード watcher の精密処理（単一モジュールのリロード）に委ね、全体監視から除外するかどうか |
| event_dedupe | boolean | true | イベントの冪等重複排除：同一イベント id の重複配信（接続層の再プッシュ / ゲートウェイの再送）は一度のみ配信される |
| cross_account_policy | string | "off" | クロスアカウント重複受付ポリシー：同一物理メッセージが複数アカウント経由で順次到着した場合の処理——`off` は関連付けなし（イベントは通常どおり個別に配信、デフォルト）；`mark` はコピーにトップレベルの `multi_receipt` フィールド（最初に受付したイベントを指す）を注入したうえで通常どおり配信し、モジュールがそのフィールドを読み取って自ら判断；`drop` はコピーを配信の入り口で直接破棄（フレームワーク層での重複排除、モジュールは無感知）。mention 先が受信アカウント自身（`user_id` / `account_id`）に該当するコピーは関連付けの対象外（at 指名優遇）；ポリシーはホットアップデート対応、変更は即時反映される |
| session_accounts | table | {} | セッションアカウントバインディング：`{"プラットフォーム名": {"セッションID": "アカウントbot_id"}}`、セッションを一意の所属アカウントに正確にバインドする——バインドされたセッションは所属アカウントにのみ配信され、他のアカウントのコピーは破棄される（`cross_account_policy` とは独立して有効、設定すれば有効化；at 指名優遇は維持）。セッション ID は `"group:123"` のプレフィックス形式を推奨（同数値のプライベートセッションと分離）、プレフィックスなしの `"123"` という互換表記はすべてのセッションタイプにマッチ；設定はリアルタイムで読み込まれ、ホットアップデートが反映される |
| memory_tracing | boolean | false | メモリトレーシング（tracemalloc）：有効にすると `/metrics` とメモリスナップショットで traced メモリと上位アロケーションポイントを出力でき、増加閾値が RSS を誤用しなくなる；割り当てパスに約 2 倍の CPU オーバーヘッド——トラブルシューティング時に有効化し、通常時は無効にすること；ホットアップデート対応、次回のプロアクティブ GC ラウンドから有効 |

セッションアカウントバインディングの例（プレフィックスキー形式を推奨）：

```toml
[ErisPulse.framework.session_accounts.snowluma]
"group:643319481" = "1325859446"
```

### プロアクティブ GC 設定

SDK の初期化完了後にプロアクティブ GC のバックグラウンドタスクが起動され、周期的に Python GC と内部リソースの回収（オフライン Bot のクリーンアップなど）を実行します。すべてのパラメータはホットアップデートに対応しており、変更時にはタスクが即時再起動されます。

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | 回収間隔（秒）、小数をサポート。0 はプロアクティブ GC を無効化 |
| proactive_gc_generation | integer | 0 | 通常ラウンドで回収するジェネレーション（0/1/2、0..2 にクランプ）。注意：`gc.collect(2)` はフルコレクションと同等のため、デフォルトの 0 は軽量さを維持；フルコレクションは `proactive_gc_full_every` により周期的にトリガーされる |
| proactive_gc_full_every | integer | 20 | N ラウンドごとに 1 回フルコレクションを実行、0 は周期的なフルコレクションを無効化。フルコレクションは `proactive_gc_memory_growth_mb` の閾値制約を受ける |
| proactive_gc_memory_growth_mb | integer | 32 | フルコレクション実行のメモリ増加閾値（MB）：前回のフルコレクション後のメモリベースライン（tracemalloc を優先、次点で RSS）と比較し、増加がこの値に達した場合にのみフルコレクションを実行。0 は閾値なし |
| proactive_gc_idle_only | boolean | false | 有効にすると、イベント急増時（未完了の pending handler が存在する場合）はそのラウンドの Python GC をスキップし、停止がメッセージ処理と競合するのを回避；内部リソースの回収には影響しない |
| proactive_gc_gen0_min | integer | 500 | 通常ラウンドで回収をトリガーする gen0 ゴミ量の下限：`gc.get_count()[0]` がこの値を下回る場合はスキップ（空回転ラウンドはほぼゼロオーバーヘッド）。0 は常に回収 |

> **2.7.1 での変更**：デフォルトの `proactive_gc_generation` を `2` から `0` に、デフォルトの `proactive_gc_full_every` を `0` から `20` に変更しました。従来の `generation=2` は、毎ラウンド最も重いフルコレクションを実行することを意味します；新しいデフォルトは回収カバレッジを維持しつつ、空回転のオーバーヘッドを大幅に低減します。明示的に設定された旧値は、引き続き文字どおりのセマンティクスで有効です。

### 厳格モード

厳格モードは、モジュール/アダプターがロード段階で不適合または失敗した際の処理ポリシーを制御します。現代的なモジュール/アダプターは対応する基底クラス（`BaseModule`/`BaseAdapter`）を継承すべきであり、基底クラスを継承していないコンポーネントはフレームワークのコンテキストシステムとフォールバッククリーンアップに影響を与え、リソースリークを引き起こす可能性があります。

> **2.5.2 での変更**：新規ユーザーが初回利用時に遭遇するロード問題を減らすため、デフォルトレベルを `1`（スキップ）から `0`（寛容）に変更しました。基底クラスを継承していないコンポーネントは直接拒否するのではなく、WARNING で通知したうえでロードを試みます。旧動作に戻したい場合は、明示的に `strict_mode = 1` を設定してください。

| レベル | 名称 | 動作 |
|------|------|------|
| 0 | 寛容（デフォルト） | 違反は警告のみ、基底クラスを継承していないコンポーネントも引き続きロードを試みる（旧コンポーネントと互換） |
| 1 | 厳格-スキップ | 基底クラスを継承していないコンポーネントを拒否してスキップ、その他は正常に起動 |
| 2 | 厳格-致命的 | すべての違反を収集したのち一括報告し、起動全体を中止 |

いずれのレベルでも、「ロード/登録/初期化段階でのエラー」のようなコンポーネント自身のクラッシュは常にスキップされます；違いは次のとおりです：

- **0 → 1**：唯一の動作の変化は、「基底クラス未継承」の扱いが「引き続きロード」から「スキップ」に変わる点です。
- **1 → 2**：すべての違反（基底クラス未継承、ロード失敗、登録失敗、初期化失敗など）が致命的に昇格し、起動チェックポイントで収集したのち、違反リストを一度に出力して中止します。

#### 免除リスト

一部のコンポーネントがどうしても当面は移行できない場合（依存している旧モジュールなど）は、免除リストに追加できます。リストに挙げられたコンポーネントは、不適合であっても寛容モードとして扱われ、引き続きロードされます：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> コンポーネントが厳格モードで拒否された場合、ログにはロードを復旧する方法（免除リストへの追加、またはレベルの引き下げ）が明確に表示されます。

#### CLI との連携

`epsdk run` の起動前セルフチェック（設定ファイルのパース可能性、コンポーネントの必須設定の完全性）は、デフォルトでこの設定に従います：0 以外の場合はチェック失敗時に起動を拒否し、0 の場合は警告のみで続行します。設定を変更せずに一時的に切り替えることも可能です：`epsdk run --strict` は今回の実行でセルフチェックと厳格レベルを同時に有効化し（レベルは上げる方向のみ、`ERISPULSE_FRAMEWORK_STRICT_MODE` 環境変数を介して実行プロセスに伝達されます）、`--no-strict` は今回に限り一時的に寛容へ下げて警告のみとします。

## ストレージ設定

2.8.0以降、ストレージエンジンは3種類の非同期バックエンドをサポートし、**APIは完全に一致し、設定で1度の切り替えが可能**です：

| バックエンド | ドライバー | インストール | 特徴 |
|------|------|------|------|
| SQLite（デフォルト） | aiosqlite | 開梱即用 | 零設定、単一ファイル、WAL並列処理 |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | 既存のMySQLインフラストラクチャ、多インスタンス共有 |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | トランザクション能力が高く、高並列処理 |

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite"（デフォルト）/ "mysql" / "postgres"
use_global_db = false     # 仅 SQLite：使用包内全局数据库 data/config.db

[ErisPulse.storage.sqlite]     # 仅 backend = "sqlite" 时生效
busy_timeout = 5000       # 写锁等待上限（毫秒，PRAGMA busy_timeout）

[ErisPulse.storage.mysql]      # backend = "mysql" 时生效
host = "127.0.0.1"
port = 3306
user = "erispulse"
password = ""
database = "erispulse"
# charset = "utf8mb4"
# pool_min = 1
# pool_max = 10

[ErisPulse.storage.postgres]   # backend = "postgres" 时生效
host = "127.0.0.1"
port = 5432
user = "erispulse"
password = ""
database = "erispulse"
# pool_min = 1
# pool_max = 10
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| backend | string | sqlite | ストレージバックエンド: `sqlite` / `mysql` / `postgres`、切り替えでコード変更なし |
| use_global_db | boolean | false | 仅 SQLite: パッケージ内グローバルデータベース data/config.db を使用するか、プロジェクト固有のデータベースを使用するか |
| storage.sqlite.busy_timeout | int | 5000 | 仅 SQLite: 写ロック待機上限（ミリ秒、PRAGMA busy_timeout）；値を大きくするとロック待ちの忍耐を長くする、変更は再起動で有効 |
| storage.mysql.* | table | 上記参照 | MySQL接続パラメータ（host / port / user / password / database / charset / pool） |
| storage.postgres.* | table | 上記参照 | PostgreSQL接続パラメータ（host / port / user / password / database / pool） |

環境変数による上書きもサポート（Docker / 12-factor）: `ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`。

> [!TIP]
> - 接続パラメータを変更した後はフレームワークを再起動して有効にする必要がある；接続プールの作成が瞬間的に失敗しても、指数関数的に再試行する
> - 切り替える前に検証スクリプトで自検できる：`python tests/devs/test_storage_backend_verify.py --backend mysql`
> - トランザクション / 方言の違い / 自作バックエンドなど詳細な説明は[ストレージバックエンド](../advanced/storage-backends.md)を参照

## Webサービスとルーティング設定

Webサーバーとルーティング（`[ErisPulse.server]` / `[ErisPulse.router]`）の完全な設定項目――host / port / auto_start / ssl、CORS とセキュリティヘッダー（`router.cors.*` / `router.security.*`、変更には再起動が必要）、APIレート制限（`router.rate_limit.*`、`rate_limit_trust_proxy` はレート制限のキーとしてプロキシヘッダーとピアアドレスのどちらを使用するかを決定します、リバースプロキシ環境でのデプロイ時には必ず確認してください）――については、[ルーティングシステム](../advanced/router.md)と[デプロイガイド](deployment.md)を参照してください。

## インタラクションセッション設定

インタラクション待機 / セッション排他リースのパラメータ（`[ErisPulse.interaction]`、`checkpoint_ttl` の会話チェックポイント有効期限を含む）については、[Conversation マルチターン対話](../advanced/conversation.md)および[インタラクションセッションシステム](../advanced/interaction.md)を参照してください。

## イベント設定

### コマンド設定

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| prefix | string | / | コマンドのプレフィックス |
| case_sensitive | boolean | true | 大文字小文字を区別するかどうか（`/Help` と `/help` が異なるコマンドかどうか） |
| allow_space_prefix | boolean | false | プレフィックスにスペースを許可するかどうか |
| must_at_bot | boolean | false | コマンドをトリガーするには@ボットが必要かどうか（プライベートチャットは制限されない） |

### メッセージ設定

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| ignore_self | boolean | true | 自分自身のメッセージを無視するかどうか |

> イベントの重複除去は3層で、それぞれの重複を処理します：`event_dedupe`（framework、同じイベントIDの重複投下）→ `ignore_self`（本節、ロボット自身のメッセージ）→ `cross_account_policy`（framework、複数アカウントの同じ群の内容の副本来源）。各層の役割は[アダプターのコアコンセプト](../developer-guide/adapters/core-concepts.md)を参照してください。

## セッショントランク設定（transcript）

```toml
[ErisPulse.transcript]
enabled = true
max_per_session = 50
ttl_hours = 168.0
self_echo = "bot"
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| enabled | boolean | true | 入力/出力メッセージを自動的に記録するかどうか（無効にすると書き込みは停止し、履歴は照会可能） |
| max_per_session | int | 50 | 1セッションに保持する条数（0 = このセッションの裁断を無効化） |
| ttl_hours | float | 168.0 | 全体の保持期間（時間、0 = 永久に削除しない） |
| self_echo | string | bot | 入力されたbotのエコー（`self.user_id == user_id`、OneBot `report-self-message`）の処理：`bot` = botとして記録し、`meta.self_echo`をマークする；`skip` = 記録しない；`user` = userとして記録する（旧動作） |

> 保持戦略のリスクと監査は [セッショントランク](../advanced/transcript.md) を参照してください。帰属フィールド（`sender` / `meta`）と出力の所属（`meta.module`）は同ドキュメントを参照してください。

## 国際化設定

```toml
[ErisPulse.i18n]
language = "auto"
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| language | string | auto | フレームワーク内蔵テキストの表示言語。`auto`に設定するとシステム言語を自動検出、具体的なコード（`zh-CN`、`zh-TW`、`en`、`ja`、`ru`）を設定することもできる |

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

# 設定の読み取り
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# 実行時に設定を書き込む（遅延保存）
sdk.config.setConfig("MyModule.timeout", 60)

# ファイルに即時保存
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` はデフォルトで遅延書き込み（約5秒毎に一括保存）を使用し、`immediate=True` で即時永続化されます。設定変更は `config.set` ライフサイクルイベントをトリガーします。

## スコープ設定（scope）

> [!NOTE]
> 本機能は ErisPulse **2.8.0+** が必要です。

スコープは「**どの範囲で有効か**」を宣言します——特定のプラットフォーム / Bot / セッションでどのモジュールが有効か（① モジュール次元）、特定のユーザー / グループ / Bot / アダプターのイベントを受信するかしないか（② アイデンティティ次元）、モジュールがどの出力呼び出しを行うか（③ 出力次元）：

```toml
[ErisPulse.scope]
default_allow = true        # グローバルデフォルト（false = 明示的拒否の厳密モード；出力次元には影響しない）
cache_size = 1024           # LRUキャッシュサイズ

# ① モジュール次元（優先度：セッション > Bot > プラットフォーム；条目は正確 / glob / re: 正規表現に対応）
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]
blocked = ["re:^Danger"]

# 子級バインディングは merge = true の場合、低優先度の条目と逐条目結合（デフォルトは全体上書き）
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true

# ② アイデンティティ次元（優先度：ユーザー > セッション > Bot > アダプター；各レベルは allow か deny のどちらかを書く）
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                 # 該プラットフォームのすべてのイベントをエントランスで破棄
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]         # ユーザーキーは glob / re: 正規表現に対応
deny = ["u_bad", "spam_*"]

# ③ 出力次元（デフォルトはすべて許可；ルールは内側に表、条目は正確 / glob / re: 正規表現に対応）
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                    # 送信を完全に禁止
api = { allow = ["get_*"] }               # クエリ系の標準APIのみ許可
request = { deny = true }                 # リクエスト処理を禁止
```

| 設定項目 | 型 | 説明 |
|---------|------|------|
| `scope.default_allow` | boolean | グローバルデフォルト：モジュール/アイデンティティがルールに合致しなかった場合の許可/拒否（`true`） |
| `scope.cache_size` | integer | LRUキャッシュサイズ（デフォルト 1024） |
| `scope.platforms / bots / sessions` | table | ① モジュール3段階バインディング：`{modules=[...], blocked=[...], merge=bool?}` |
| `scope.identity.adapters / bots / sessions / users` | table | ② アイデンティティ4段階バインディング：`{allow=true}` / `{deny=true}` |
| `scope.actions.<module>.<action>` | table | ③ 出力ルール：`{allow=[...], deny=true|[...]}`（アクションは send / api / request） |

> 詳細と実行時API（次元化 `sdk.scope.set_module()` / `set_identity()` / `set_action()`、判定 `is_allowed()` / `is_identity_allowed()` / `is_action_allowed()`、および辞書式のデフォルト `get()` / `set()` / `delete()`）は[スコープ（scope）](../advanced/scope.md)を参照してください。

## 統一イベントオーバーライド設定（event.overrides）

統一オーバーライドシステム：**イベントタイプごとに**任意のモジュールハンドラの動作をオーバーライドし、モジュールコードを変更せずに動作をカスタマイズします。OneBot12標準タイプ（meta / message / notice / request）と拡張タイプ（command）それぞれに独自のオーバーライド可能なパラメータがあります：

```toml
[ErisPulse.event.overrides]

# message：テキストのトリガー条件（コード内の条件とAND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice / request / meta：detail_typeのホワイトリスト（条目は正確 / glob / re: 正規表現に対応）
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command（拡張タイプ）：実装パラメータのオーバーライド（ユーザーの優先；無効化はacl deny）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true               # 仅框架マスターに変更（falseで開発者のマスター制限を解除）
hidden = true               # ヘルプリストに非表示
aliases = ["rs"]            # 生效のエイリアス

# acl（command専用）：コマンドのユーザーホワイト/ブラックリスト（コマンド名はglob / re: 正規表現に対応、正確なキーが優先）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]  # ユーザー識別子 "platform:user_id"
deny = ["onebot11:u_bad"]

# ACLのデフォルト：acl設定のないコマンドを許可（true）/ 严格拒否（false）
acl_default_allow = true
```

| 設定項目 | 型 | 説明 |
|---------|------|------|
| `event.overrides.message.<module>` | table | テキスト条件：`{pattern="...", regex="..."}` |
| `event.overrides.notice / request.<module>` | table | `{detail_types=[...], pattern, regex}` |
| `event.overrides.meta.<module>` | table | `{detail_types=[...]}` |
| `event.overrides.command.<module>` | table | モジュールレベルのパラメータオーバーライド（`hidden = true` などのスカラー値） |
| `event.overrides.command.<module>.<command>` | table | コマンドレベルのオーバーライド（コマンドレベルが優先） |
| `event.overrides.acl.<command名>` | table | ユーザーホワイト/ブラックリスト：`{allow=[...], deny=[...]}` |
| `event.overrides.acl_default_allow` | boolean | ACLのデフォルト：acl設定のないコマンドを許可（`true`）/ 严格拒否（`false`） |

> 実行時API（`from ErisPulse.Core.Event import overrides` 後、タイプごとのサブネームスペースで `overrides.message.set()` / `overrides.command.set()` / `overrides.acl.set()` など呼び出す、または `sdk.Event.overrides` でアクセス）は [イベント処理入門 · イベントオーバーライド](../getting-started/event-handling.md#イベントオーバーライドモジュールコードを変更せずに任意のイベントタイプの動作をオーバーライド) を参照してください。

## 次に

- **L1経路に従って**：次のドキュメント [例外の捕捉](../advanced/errors.md) で、フレームワークをクラッシュさせないエラーハンドリングの書き方を学びます
- **TOMLを手動で書きたくない**：`epsdk config` で宣言式の設定項目をインタラクティブに入力する向導を使用し、[CLIコマンドリファレンス · config](cli-reference.md#config) を参照してください
- **設定ファイルを変更したくない**：環境変数で設定項目を上書きし、[デプロイガイド](deployment.md)のDockerの使い方を参照してください