# 設定ファイルの説明

> [!NOTE]
> **L1コア必読**— ホームページ「読むべき経路」の5つのコアドキュメントの1つで、モジュール開発に不可欠です。

> このドキュメントは、フレームワーク自身の設定ファイル `config/config.toml` について説明します：各設定セクションが何を管理しているか、どの設定がホットアップデートをサポートしているか、環境変数でどのように上書きできるか。サードパーティのモジュールの設定項目は、それぞれのモジュールのドキュメントを参照してください。

ErisPulseは、TOML形式の設定ファイル `config/config.toml` を使用して、プロジェクトの設定を管理します。

## 設定ファイルの位置

設定ファイルは、プロジェクトのルートディレクトリの `config/` フォルダ内にあります：

```
project/
├── config/
│   └── config.toml
├── main.py
```

### 複数インスタンスの注意点とロックファイル

フレームワークが起動する際、プロジェクトのルートディレクトリの実行状態ディレクトリ **`.erispulse/`** に `config.lock` ロックファイルを作成し、プロセス終了まで保持します（複数のインスタンスが同じ設定ディレクトリを共有しているかを検出するため；2.10以前は `config/` ディレクトリの `.erispulse_config.lock` が、アップグレード後に最初の起動時に自動的に削除されます）。ログに「設定ファイルが他のErisPulseインスタンスによって同時に使用されている可能性がある」という警告が表示された場合、**2つ以上のErisPulseプロセスが同じ設定ファイルを書き込んでいる**ことを意味します（典型的なシナリオ：複数のコンテナが同じホストマシンの `config/` ディレクトリをマウントしている）— 並行的な書き込みは互いに上書きするため、各インスタンスに独立した設定ディレクトリを使用してください。

### 敏感な設定はバージョン管理に含めない

設定ファイルにはトークン（token / API key）などの機密情報が含まれます：フレームワークの初期化と `epsdk init` は、自動的に `config/` ディレクトリに `.gitignore` を生成します（内容は一行のみ `*` — **ディレクトリ内のすべてのファイルをバージョン管理から除外し、除外ファイル自身も除外対象になります**）。既存の `.gitignore` は上書きされません。`.erispulse/` 実行状態ディレクトリ（インスタンスロック、CLI実行状態ファイル）は、ローカルマシンの状態に属するため、プロジェクトテンプレートの `.gitignore` には既定で除外されています。

## 設定の読み込みエラー処理

フレームワークは `config.toml` を読み込む際に、3つのエラー状態を区別し、**操作可能な診断情報を提供**します。デフォルト設定に静かに戻るのではなく、エラーを出力します。

| エラー状態 | トリガー条件 | フレームワークの動作 |
|---------|---------|---------|
| ファイルが存在しない | `config.toml` が存在しない | 正常な初期起動では、空の設定を静かに使用します（警告は出力しません） |
| TOML構文エラー | ファイルは存在するが、形式が無効（例：引用符が足りない、括弧が閉じていない） | **エラー行番号/列番号と原因**を出力し、**前回の有効な設定を保持して実行を継続**します（今回のファイルの変更は有効になりません） |
| 権限/その他のエラー | 読み取り権限がない、IOエラーなど | **明確な原因**を出力し、**前回の有効な設定を保持して実行を継続**します |

> **「前回の有効な設定」＝デフォルト設定ではありません**：ファイルが破損した場合、フレームワークは**今回の起動前の最後に解析された設定**（実行中にホットアップデートでファイルを破損させた場合は、旧値を使用）を保持します。故障の対処では、「設定がリセットされた」と仮定しないでください。

たとえば、`port = 8000`（引用符のない文字列）と誤って記述した場合、ログには次のような出力がされます：

```
[ERROR] [Config] 設定ファイル config/config.toml が構文エラー（第 3 行 第 1 列）: ...
[WARNING] [Config] 設定ファイルの読み取りに失敗しました。前回の有効な設定を使用して実行を継続し、今回のファイルの変更は有効になりません——修正後、再読み込みまたは再起動してください
```

これにより、**デフォルトのINFOレベル**で問題をすぐに特定でき、「なぜ設定の変更が有効にならないのか」を混乱させません。

> **実行中に設定ファイルを破損させた場合？** ロボットが実行中に `config.toml` を手動編集して構文エラーを導入した場合、フレームワークは次回の書き込み（設定のマージ）時に「設定ファイルが破損（構文エラー、第 X 行）、マージ書き込みができない——まず設定ファイルを修正して再起動してください」と出力します。混乱する「書き込み失敗」ではなく、待機中の設定項目は保持され、失われることはありません。

## コメントの保持と最小限の書き込み

config.toml 内の**コメントとキーの順序は、フレームワークが書き込んだ後も完全に保持されます**：コード `setConfig()`、CLI 設定アシスタントの保存、またはアダプタ/モジュールの初期設定テンプレートの生成など、フレームワークは関連するキーのみを変更し、あなたが書いたコメントや整理された順序は削除や再配置されません（tomlclass による無損失TOMLエンジンを使用し、未触れた内容はバイト単位で保持され、ファイルのCRLF/LF行末スタイルも変更されません）。

フレームワークは、書き込み内容を最小限に抑えています：

- **フレームワークのデフォルト設定は自動的に書き込まれません**：`gc`、`scope`、`transcript` などの組み込みのデフォルト値はメモリ内に保持され、config.toml には明示的に設定されたキーのみが含まれ、最小限に保たれます。完全な設定項目は、プロジェクト内の `config/config.full.example` を参照してください。必要に応じて config.toml にコピーして変更してください（設定されていない項目はすべて組み込みのデフォルト値を使用し、動作は変わりません）。
- **`config.full.example` の自動維持**：`epsdk init` を実行したかどうかに関わらず、フレームワークを起動するたびに（`epsdk run` / `main.py`）、`config/config.full.example` が欠落している場合に自動生成されます。ファイルの先頭行はフレームワークが維持するマークであり、生成器の内容が更新された場合（新しい設定項目、新しいコンポーネントの追加など）に起動時に更新されます。先頭行を削除または変更すると、手動で管理し、フレームワークは上書きしません。
- **アダプタ/モジュールの設定テンプレート**：初期化時にコメント付きのテンプレートを書き込みます（フィールドの説明がコメントになります）。`example` とマークされたフィールドは書き込みされず、`config.full.example` に記録され、参照用です。
- **宣言的なコメントの再読**：設定ファイル内のコメントはドキュメントそのものです——`ep doctor` と設定検証の失敗メッセージは、該当フィールドのファイル内のコメントをそのまま引用します（手動でコメントを変更した場合でも、メッセージはファイルの現状に従います）。エラーの際には、ドキュメントを再度参照してフィールドの意味を確認する必要はありません。

## 環境変数による上書き

フレームワークは、`ErisPulse.*` 設定項目を**環境変数で上書き**することをサポートしています（Docker / コンテナ化 / CI 部署に適しています。`config.toml` を変更する必要はありません）。

命名規則：`ErisPulse.<セクション>.<キー>` の点分区切りパスを全大文字にし、`.` を `_` に置き換え、`ERISPULSE_` を接頭辞に追加します：

| 設定項目 | 環境変数 | 例値 |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `2` |

動作の説明：

- **優先度が最も高い**：環境変数は「設定ファイル」および「デフォルト値」を上書きし、元の値の型に応じて自動変換されます（`bool` / `int` / `float` / カンマ区切りの `list` / 文字列）
- **永続化されない**：上書きは実行時にのみ有効で、`config.toml` には書き込まれません
- **ホットアップデートがサポートされている**：実行中に環境変数を変更した後、設定監視のリロードと組み合わせて有効になります

```bash
# Docker 部署の例：config.toml を変更せずに、ポートを上書き
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> 注：`ErisPulse.server.port` などのフレームワーク設定は `get_server_config()` などの API で読み取られ、環境変数の上書きの影響を受けます。

### モジュール設定の環境変数バインディング（2.9.0+）

モジュール自身の宣言的設定（`ConfigClass`）は、フィールドレベルで環境変数をバインディングできます — `field(metadata=...)` で `env` を宣言します：

```python
@dataclass
class MyConfig(BaseConfig):
    api_key: str = field(default="", metadata={
        "description": "API キー",
        "env": "MYMODULE_API_KEY",   # 環境変数バインディング
    })
    retries: int = field(default=3, metadata={"env": "MYMODULE_RETRIES"})
```

動作の説明：

- **優先度**：環境変数 > `config.toml` > 宣言デフォルト値（設定ファイルのホットアップデート後もこの優先度が維持されます）
- **型変換**：環境変数の値はフィールドの注釈に応じて自動変換されます — `str` はそのまま、`int` / `float` / `bool`（`true` / `1` / `yes` / `on`）は自動変換、`list` / `dict` はJSON解析を経ます；変換に失敗した場合は、該当の上書きを無視し（設定ファイル/デフォルト値に戻り）、警告を出力します
- **宣言1か所、どこでも有効**：設定の読み取り、ホットアップデート、検証は同じパイプラインを使用します；設定パネルのSchemaには `env` 名が表示され、`config.toml` テンプレートには利用可能な環境変数の説明が提示されます（テンプレートには環境変数の実際の値は書き込まれず、漏洩を防ぎます）
- **完全に互換性がある**：`env` を宣言していないフィールドの動作は変わりません；フレームワークの設定パイプラインを経ていない `ConfigClass` のインスタンス化は環境変数の影響を受けません

```bash
# Docker 部署の例：config.toml を変更せずに、モジュールのキーを注入
MYMODULE_API_KEY=sk-xxx docker compose up -d
```

> **設定クラス vs モデルフィールドはどちらを使うか？** 設定クラスは「モジュールがどのように動作するか」（動作パラメータ、ホットアップデート）を管理し、ORM の `Field()` は「ユーザーがどのようなデータを生成したか」（データベーステーブル、クエリ）を管理します。両者は同一の制約語彙と検証エンジンを使用しています；対照表は [データモデル層 · どちらの宣言を使うべきか](../developer-guide/orm.md#どちらの宣言を使うべきか) を参照してください。

## 設定のホットアップデート

2.7.0 以降、フレームワークは設定のホットアップデートを**体系的にサポート**しています。外部で `config.toml` を変更した後（バックグラウンドの watcher が5秒ごとにチェック）、または `setConfig()` を呼び出した後、各コンポーネントが自動的に応答します：

| コンポーネント | ホットアップデートがサポートされている設定 | 動作 |
|------|----------------|------|
| **ログ Logger** | `logger.level` / `log_files` / `log_dir`（分割パラメータを含む）/ `memory_limit` / `format` / `exclude_levels` | 変更検出付きで自動的に再適用されます |
| **コマンドシステム CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | 次のメッセージで即座に有効になります |
| **アダプタの並列処理** | `framework.handler_max_concurrency` | 失効したキャッシュシグナルを再構築します |
| **アクティブGC** | `framework.proactive_gc_*` | 設定の変更で即座にGCタスクを再起動し、実行時に調整/無効化/再有効化がサポートされます |
| **マスターシステム Master** | `master.users` | `is_master()` のチェックは毎回リアルタイムに読み取り、再起動は不要です |
| **モジュール/アダプタの設定** | 各々の設定項目 | `on_config_update(old, new)` カスタムコールバックをトリガーします |

**再起動が必要な設定**（安全にホット切り替えできないため、変更時に「プロセスを再起動後に有効になります」という警告が出力されます）：

| 設定 | 原因 |
|------|------|
| `router.cors.*` / `router.security.*` | ミドルウェアはサービス起動時にFastAPIに書き込まれ、実行時に安全にホット切り替えできない |
| `storage.use_global_db` | SQLiteのファイルハンドルは実行時に開かれているため、パスの切り替えは安全ではない |

> **途中で編集保存に失敗した場合？** `config.toml` を編集している間に一時的な構文エラーが発生した場合、フレームワークは**前回の有効な設定を保持**して診断ログを出力し、各コンポーネントに空の設定をブロードキャストすることはありません（`on_config_update` が空値を受けてデフォルトに戻るのを防ぐため）。

### ホットアップデートの内部構造分解

「設定を変更したが、各コンポーネントはどのように知るのか？」——背後には、検出 → 再読み込み → ブロードキャストのチェーンがあります：

```mermaid
flowchart TD
    A["外部で config.toml を編集"] --> B{"誰が最初に気づく？"}
    B -->|"バックグラウンドの watcher スレッド<br/>5秒ごとに mtime をチェック"| C["_check_file_change で変更を判定"]
    B -->|"設定を読み取るとき<br/>キャッシュが60秒以上経過している"| C
    C --> D["_load_config で TOML を再解析"]
    D --> E{"解析に成功した？"}
    E -->|"失敗（構文エラー）"| F["前回の有効な設定を保持<br/>診断ログを出力し、ブロードキャストは行わない"]
    E -->|"成功"| G["lifecycle.emit config.updated<br/>old_config / new_config を含む"]
    G --> H["各コンポーネントのリスナーが応答<br/>（logger / scope / コマンド / GC ...）"]
```

**2つの検出経路**（どちらか1つで十分、両方でバックアップ）：

| 経路 | メカニズム | トリガータイミング |
|------|------|---------|
| バックグラウンド watcher | daemon スレッド `config-watcher` が **5秒** ごとに `wait` でファイル `mtime` をチェック | 外部でファイルを変更した後、最大5秒以内に |
| 慣性検出 | 任意の `getConfig()` 読取時、キャッシュが **60秒** 超えたらファイルをチェック | 次回の設定読み取り時 |

> **フレームワークは自分自身を誤って傷つけません**：`setConfig()` でファイルに書き込む際、フレームワークは「自身が書き込んだ mtime」を記録し、watcher はそれを除外して、**外部の編集**のみを変更とみなします。

**2種類の設定変更イベント**：

| イベント | トリガ | データ | 代表的なシナリオ |
|------|------|------|---------|
| `config.set` | コード / Dashboard が `setConfig()` を呼び出す | `{key, old_value, new_value}` | 単一キーの書き込み（テンプレート生成、ステート記録、実行時設定変更） |
| `config.updated` | 外部編集後の watcher/慣性検出が捕捉 | `{old_config, new_config, config_file}` | 手動で `config.toml` を編集した場合 |

> `setConfig()` はデフォルトで**5秒遅延してファイルに書き込む**（複数の書き込みを1回にまとめる）；`immediate=True` で即時書き込み。watcher が外部の変更を検出した後は、メモリキャッシュのみを更新し、**外部の変更をファイルに書き戻すことはない**。

**自動応答対象リスト**（2種類のイベントは通常両方サブスクライブし、応答内容は一致）：

| コンポーネント | 監視 | 応答 |
|------|------|------|
| Logger | `config.set` + `config.updated` | レベル/ファイル/ディレクトリ/分割/メモリ上限/フォーマット/除外レベルを再適用（変更検出付き、変更がない場合は処理しない） |
| Scope | `config.updated` | スコープバインディングのキャッシュを再構築 |
| コマンドシステム | `config.updated` | プレフィックス/大文字小文字/スペースプレフィックス/must_at_bot の解析パラメータを更新し、次のメッセージで有効になります |
| アダプタの並列処理 | `config.set` + `config.updated` | `handler_max_concurrency` が無効化され、シグナルを再構築します |
| アクティブGC | `config.set` + `config.updated` | `proactive_gc_*` でGCバックグラウンドタスクを即時再起動します |
| アダプタ | `config.updated` にルーティング | 各アダプタの `on_config_update(old, new)` カスタムコールバック |
| モジュール | `config.updated` にルーティング | 各モジュールの `on_config_update(old, new)` カスタムコールバック |
| ストレージ | `config.updated` | `use_global_db` の変更は**警告のみ**（再起動が必要） |
| ルーティング | `config.updated` | `cors.*` / `security.*` の変更は**警告のみ**（再起動が必要） |

## 設定の読み取りと削除 API

### getAllConfig：全量設定スナップショット

プライベートな `_cache` を直接読み取る代わりに（外部からプライベート属性を読み取るのはバージョン互換性の保護を受けない）：

```python
config = sdk.config.getAllConfig()     # 深いコピーのスナップショット、原地変更してもフレームワークの状態には影響しません
config["ErisPulse"]["server"]["port"]
```

ビューの口径は `getConfig` と同じです：`setConfig` / `delete` による遅延書き込みも反映され、ファイルの内容と厳密に一致します。

### delConfig：設定キーの削除

`setConfig(key, None)` は単に空に設定するだけで、キーはファイル内に保持されます；`delConfig` はファイルからキーを**削除**します：

```python
sdk.config.delConfig("ErisPulse.modules.status.OldModule")            # 遅延書き込み
sdk.config.delConfig("OneBot.deprecated_key", immediate=True)         # 即時書き込み
```

- 点分パスをサポート；キーが存在しない場合は `False` を返します
- 書き込みはコメント保持の経路を使用し、ファイルの他の内容や順序は影響を受けません
- `config.set` イベントのブロードキャストを再利用します（`new_value=None`）：アダプタ / モジュールの `on_config_update` 等既存のリスナーは変更なしで削除を感知できます

## 完全な設定例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.master]
# users は2種類の書き方ができます（どちらか1つを選択）：
#   全局マスター（すべてのプラットフォームに有効）：users = ["123456", "789012"]
#   プラットフォームごとにマスターを指定：users = { yunhu = ["123456"], telegram = ["789012"] }
users = {}

[ErisPulse.logger]
level = "INFO"
format = "rich"
log_files = []
log_dir = ""
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
# コンテナ / ファイルがマウントされていない環境では、内包PEMの内容を使用できます（pathより優先）
# ssl_cert = """-----BEGIN CERTIFICATE-----
# ...
# -----END CERTIFICATE-----"""
# ssl_key = """-----BEGIN PRIVATE KEY-----
# ...
# -----END PRIVATE KEY-----"""
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 監聴するアドレス、0.0.0.0はすべてのインターフェースを意味します |
| port | integer | 8000 | 監聴するポート番号 |
| auto_start | boolean | true | `sdk.init()` 時にルーティングサーバーを自動的に起動するかどうか。`false` に設定するとルーティングサーバーの起動をスキップします（純イベント/無WebUIの状況） |
| ssl_certfile | string | 空 | SSL証明書ファイルのパス |
| ssl_keyfile | string | 空 | SSL秘密鍵ファイルのパス |
| ssl_cert | string | 空 | **内包PEM証明書の内容**（パスではなく）。`ssl_key` とペアで使用する場合、`ssl_certfile`/`ssl_keyfile` のパスよりも優先されます；フレームワークはSSLコンテキストを構築するために一時的にファイルを書き込み、すぐに削除します |
| ssl_key | string | 空 | **内包PEM秘密鍵の内容**（パスではなく）、上記と同じ意味 |

> **ポートの占有は致命的なエラーではありません**：起動時に `port` が既に占有されていることが検出された場合、フレームワークはルーティングサーバーの起動をスキップして警告を出力し、**アダプタとモジュールは通常通り動作します**（HTTP/WS/SSEルーティングとWebUIは利用できません）。ロボットは動作するがWebUIが開かない場合のトラブルシューティングでは、ポートが使用されていることを確認してください。

## マスターシステム設定

マスターシステムは「フレームワークのマスター」アカウント（例：Bot管理者）を識別するために使用されます。`master.users` は3つの書き方をサポートしています：

```toml
[ErisPulse.master]
# 書き方1：全プラットフォームに有効なグローバルマスター（すべてのプラットフォームに有効）
users = ["123456", "789012"]

# 書き方2：特定のプラットフォームにのみマスターを指定（dict）
# users = { yunhu = ["123456"], telegram = ["789012"] }

# 書き方3：グローバルマスターとプラットフォーム専用マスターを共存させる — dict 中の global キーがグローバルマスターバケット
# users = { global = ["123456"], yunhu = ["789012"] }
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| users | array / object | 空 | マスターのアカウントリスト。`list` 形式は全プラットフォームに有効なグローバルマスター；`dict` 形式はプラットフォームごとに指定（キーがプラットフォーム名、`global` キーがグローバルマスターバケット）、値はそのプラットフォームのマスターのアカウントリスト |

> **新プラットフォームについて**：`list` 形式と `dict` 中の `global` バケットは「一度定義すれば全プラットフォームに有効」です。後で新しいプラットフォームを追加しても、設定を変更する必要はありません。プラットフォーム専用の条目は、同名（または通配符による部分一致）のプラットフォームにのみ有効です。`master.add(None, uid)` は永続化時に `global` バケットに書き込まれ、既存のプラットフォームの条目は影響を受けません。

コードでは `master.is_master(event)` または `master.is_master(platform, user_id)` を使ってチェックし、毎回呼び出すたびにリアルタイムに設定を読み取ります（ホットアップデートをサポートし、再起動は不要です）：

```python
from ErisPulse.Core import master

if master.is_master(event):
    await event.reply("マスター、こんにちは")
```

### 判定チェーンと実行時の追加・削除

マスター判定チェーンは **設定マスター → 実行時記録 → providerチェーン** です：

```python
from ErisPulse.Core import master

master.is_master(event)                      # イベントから判定
master.is_master("yunhu", "123")             # 明示的に判定
master.add("yunhu", "123")                   # 実行時に追加（デフォルトで永続化；persist=False はメモリ内のみ）
master.remove("yunhu", "123")                # 削除（デフォルトで永続化）
master.list()                                # 総合：{"global": [...], "<platform>": [...]}
```

### 自定义身份源（provider）

設定の他に、自定义身份源を登録できます：`fn(platform, user_id) -> bool`，
内建の身份源（設定 + 実行時記録）がヒットしなかった場合に順次試行し、いずれかが許可されたらマスターと判定されます。
適切なアダプタ管理者インターフェース、データベースロールなど外部の身份体系に接続するのに適しています。

登録エントリ `master.provider` はデコレータ / 関数式の2種類の書き方ができ、
登録された関数の上にある `fn.unregister()` で登録解除が可能です：

```python
from ErisPulse.Core import master

# 書き方1：デコレータ（常駐身份源、推奨）
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # 自定义判定ロジック

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # 不再需要时注销

# 書き方2：関数式（モジュール読み込み時登録 / 卸載時登録解除）
fn = master.provider(admin_provider)
fn.unregister()
```

> providerの例外はキャッチされてスキップされ、identity判定チェーンをブロックしません。
> メソッドにバインドしたインスタンスは `unregister` が付いていないため、登録/登録解除のペアが必要な場合は**モジュールレベルの関数**を使ってください。

### ユーザー優先：マスターチェーンの有効範囲はユーザーが最終決定

コマンドの `master=True` は**開発者のデフォルト**です：ユーザーは
`ErisPulse.event.overrides.command.<module>.<cmd>.master = true/false`
で覆い、厳格化または緩和できます（[統一イベント覆写設定](#統一イベント覆写設定eventoverrides)を参照、ユーザーの明示的な設定が有効になります）。

## ログ設定

```toml
[ErisPulse.logger]
level = "INFO"
log_files = []                # 明示的なログファイルリスト（log_dirと互換性あり、優先度が高い）
log_dir = ""                  # ログ出力ディレクトリ（自動的に作成）。設定するとerispulse.logに書き込み、log_rotationで自動的に分割；log_filesと互換性あり、log_filesが優先）
log_rotation = "size"         # 分割方式: "size" / "date" / "none"
log_max_size_mb = 10          # sizeモードの単ファイル上限（MB）
log_backup_count = 5          # 保持する履歴ログファイル数
log_rotation_when = "midnight"  # dateモードの分割周期: S/M/H/D/midnight
memory_limit = 1000             # 単一モジュールのメモリログの最大数（0 = メモリログを無効化）
total_memory_limit = 5000       # 全モジュールのメモリログの最大数（0 = 無制限）。超えた場合、最も古い記録を削除（最も多くの記録を持つモジュールのキューから優先的に削除）、単一モジュールのmemory_limitとは独立して有効）
exclude_levels = ["EVENT"]
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| level | string | INFO | ログレベル：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACEが最低レベル、フレームワーク内部の詳細なデバッグ情報を出力） |
| format | string | rich | ログ出力フォーマット：`rich`（カラー、デフォルト）、`plain`（カラーなし、ログ収集/パイプリダイレクトに適している）、`json`（JSON形式、ELKなどに適している） |
| log_files | array | 空 | ログ出力ファイルのリスト（明示的なパス、分割しない） |
| log_dir | string | 空 | ログ出力ディレクトリ（自動的に作成）。設定すると、erispulse.logに書き込み、log_rotationで自動的に分割；log_filesと互換性があり、log_filesが優先） |
| log_rotation | string | size | 分割方式：`size`（サイズで）、`date`（日付で）、`none`（分割しない） |
| log_max_size_mb | float | 10 | sizeモードの単ファイルサイズ上限（MB）、超過すると`.1`/`.2`のバックアップに分割 |
| log_backup_count | integer | 5 | 保持する履歴ログファイル数、超えた古いバックアップは自動的に削除 |
| log_rotation_when | string | midnight | dateモードの分割周期：`S`/`M`/`H`/`D`/`midnight`（デフォルトは毎日0時） |
| memory_limit | integer | 1000 | 単一モジュールのメモリに保持するログの最大数；`0`はメモリログのコピーを無効化（メモリに書き込まない、既存の記録は保持） |
| total_memory_limit | integer | 5000 | 全モジュールのメモリログの最大数上限；`0`は制限なし。超えた場合、ローテーション戦略に従って最も古い記録を削除（最も多くの記録を持つモジュールのキューから優先的に削除）、単一モジュールのmemory_limitとは独立して有効） |
| exclude_levels | array | 空 | 除外するログレベル。除外レベルのログは**完全に破棄**（メモリに書き込まない、ダッシュボードなどのサブスクライバーに送信しない、表示しない、ファイルに書き込まない）。ホットアップデートが可能） |

また、コード内で動的に切り替えることもできます：

```python
from ErisPulse.Core import logger

# サイズで分割：単ファイル10MB、バックアップ5個
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# 日付で分割：毎日0時でローテーション、バックアップ7個
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]
> `log_dir` および分割関連の設定は ErisPulse **2.8.0+** が必要です。

> **プライバシー保護**：メッセージの送受信内容は **EVENT** レベル（数値21）で記録されます。`exclude_levels = ["EVENT"]` を設定することで、バックエンド（例：ダッシュボードのログパネル）は各グループ/プライベートチャットのメッセージ内容を見ることができなくなり、他のレベルのログには影響しません。

> [!NOTE]
> `exclude_levels` 本特性は ErisPulse **2.8.0+** が必要です。

## 框架設定

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
| uninit_timeout | integer | 30 | エレガントなシャットダウンの総タイムアウト時間（秒）、超過後に強制終了。0 はタイムアウトを設定しないことを意味します |
| strict_mode | integer | 0 | 厳格モードのレベル、下記「厳格モード」の説明を参照 |
| handler_max_concurrency | integer | 64 | イベントハンドラの最大並行タスク数、大きく設定すると処理能力が向上しますがメモリ使用量も増加します |
| handler_queue_max_pending | integer | 4096 | イベントのピーク時のキュー制御：1プラットフォームの待機中のハンドラタスク数の上限、超過した場合、新しいイベントのハンドラタスクは直接破棄され、WARNING ログが記録されます（破棄カウントはトラブルシューティングで確認できます）；`0` は制限なしを意味します |
| offline_bot_expiry | integer | 3600 | オフライン Bot 記録の自動期限切れ時間（秒）、0 は期限切れを設定しないことを意味します |
| plugins_dir | string / list | "plugins" | 本地プラグインフォルダ（プロジェクトルートからの相対パス）；プラグインファイルの追加/削除/変更はホットリロードのウォッチャーによって自動的に検出されます |
| watch_ignore_dirs | list | 内部リスト | ホットリロードのファイル監視で無視するディレクトリ名（`.venv`/`.git`/`__pycache__` など）；空リストは内部リストを全体的に置き換えることを意味し、`[]` はディレクトリを無視しないことを意味します |
| watch_include_plugin_dirs | boolean | true | `epsdk run --reload` でプラグインディレクトリをプラグインホットリロードのウォッチャーに正確に処理させ、モジュール単位でのリロードを行い、全体の監視から除外するかどうか |
| event_dedupe | boolean | true | イベントの冪等性重複除去：同じイベント ID の重複投递（接続層の再送 / ゲートウェイの再発送）は一度だけ配信されます |
| cross_account_policy | string | "off" | 跨アカウントの重複受理ポリシー：同じ物理メッセージが複数アカウントを経由して到達した際の処理方法——`off` は関連付けしない（イベントは通常通り個別に配信される）；`mark` はコピーに最上位の `multi_receipt` フィールドを注入し、最初に受理されたイベントを指す（モジュールはこのフィールドを読み取って裁決を行う）；`drop` はコピーを配信の入口で直接破棄する（フレームワーク層での重複除去、モジュールは無感知） |

### プロアクティブ GC 設定

SDK の初期化後にプロアクティブ GC のバックグラウンドタスクを起動し、周期的に Python の GC と内部リソースの回収（オフライン Bot のクリーンアップなど）を実行します。すべてのパラメータはホットアップデートが可能で、変更時に即座にタスクを再起動します。

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | 回収間隔（秒）、小数もサポート。0 はプロアクティブ GC を無効化することを意味します |
| proactive_gc_generation | integer | 0 | 通常の回収世代（0/1/2、0..2 に制限）。`gc.collect(2)` は全量回収に等しく、デフォルトの 0 は軽量に保ちます；深度回収は `proactive_gc_full_every` によって周期的にトリガーされます |
| proactive_gc_full_every | integer | 20 | N 回ごとに全量回収を行う、0 は周期的な全量回収を無効化することを意味します。全量回収は `proactive_gc_memory_growth_mb` のしきい値によって制約されます |
| proactive_gc_memory_growth_mb | integer | 32 | 全量回収のメモリ増加しきい値（MB）：前回の全量回収後のメモリベースライン（優先 tracemalloc、次に RSS）と比較し、この値に達した場合に全量回収を実行します。0 はしきい値を設定しないことを意味します |
| proactive_gc_idle_only | boolean | false | 有効化すると、イベントのピーク時（未完了の pending handler がある）にこのラウンドでは Python GC をスキップし、停止とメッセージ処理の競合を回避します；内部リソースの回収は影響を受けません |
| proactive_gc_gen0_min | integer | 500 | 通常のラウンドで回収をトリガーする gen0 のゴミの下限：`gc.get_count()[0]` がこの値を下回る場合は直接スキップ（空回りラウンドはほぼゼロコスト）。0 は常に回収することを意味します |

> **2.7.1 変更**：デフォルトの `proactive_gc_generation` は `2` から `0` に変更され、`proactive_gc_full_every` は `0` から `20` に変更されました。以前の `generation=2` は毎ラウンドが最も重い全量回収を意味していました；新しいデフォルトは回収のカバーを保ちながら空回りコストを大幅に低減します。明示的に設定された旧値は文字通りの意味で動作します。

### 厳格モード

厳格モードは、モジュール/アダプターがロード段階で不適合または失敗した場合の処理戦略を制御します。現代のモジュール/アダプターはすべて対応する基底クラス（`BaseModule`/`BaseAdapter`）を継承する必要があります。基底クラスを継承していないコンポーネントはフレームワークのコンテキストシステムとデフォルトのクリーンアップに影響を与え、リソースリークを引き起こす可能性があります。

> **2.5.2 変更**：デフォルトのレベルは `1`（スキップ）から `0`（ゆるい）に調整され、新規ユーザーが初めて使用する際のロード問題を減らしました。基底クラスを継承していないコンポーネントは WARNING メッセージとして提示され、ロードを試みます。以前の動作を復元するには、`strict_mode = 1` を明示的に設定してください。

| レベル | 名称 | 行為 |
|------|------|------|
| 0 | ゆるい（デフォルト） | 違反は警告のみ、基底クラスを継承していないコンポーネントもロードを試みます（旧コンポーネントの互換性） |
| 1 | 厳しい-スキップ | 基底クラスを継承していないコンポーネントを拒否し、スキップし、他の部分は正常に起動します |
| 2 | 厳しい-致命的 | すべての違反を集めて一括で報告し、起動を中止します |

各レベルにおいて、「ロード/登録/初期化段階でエラーが発生する」コンポーネント自身のクラッシュは常にスキップされます。違いは以下の通りです：

- **0 → 1**：唯一の動作変化は「基底クラスを継承していない」が「ロードする」から「スキップする」に変わる点です。
- **1 → 2**：すべての違反（基底クラスを継承していない、ロード失敗、登録失敗、初期化失敗など）が致命的になり、起動チェックポイントで違反リストを一括で出力し、中止します。

#### 補償リスト

特定のコンポーネントが一時的に移行できない場合（例：依存する旧モジュールなど）、そのコンポーネントを補償リストに追加し、不適合でもゆるいモードで扱い、ロードを続けられます：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> あるコンポーネントが厳格モードで拒否された場合、ログにはロードを回復する方法（補償リストに追加するか、レベルを下げること）が明確に提示されます。

#### CLI との連携

`epsdk run` の起動前の自己検査（設定ファイルの解析性、コンポーネントの必須設定の完全性）はデフォルトで本設定に従います：0 でない場合、検査失敗で起動を拒否し、0 では警告のみで継続します。設定を変更せずに一時的に切り替えることもできます：`epsdk run --strict` は今回の自己検査と厳格レベルを同時に有効化します（レベルは昇格のみ、`ERISPULSE_FRAMEWORK_STRICT_MODE` 環境変数から実行プロセスに伝達されます）、`--no-strict` は今回の起動を一時的にゆるくし、警告のみにします。

## ストレージ設定

2.8.0 以降、ストレージエンジンは3つの非同期バックエンドをサポートし、**APIは完全に一致し、設定を1回で切り替え可能**です：

| バックエンド | ドライバー | インストール | 特徴 |
|------|------|------|------|
| SQLite（デフォルト） | aiosqlite | 開梱即用 | 零設定、単一ファイル、WAL並行 |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | 既存のMySQLインフラストラクチャ、多インスタンス共有 |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | トランザクション能力が高く、高並行 |

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite"（デフォルト）/ "mysql" / "postgres"
use_global_db = false     # 仅 SQLite：使用包内全局数据库 data/config.db

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
| backend | string | sqlite | ストレージバックエンド：`sqlite` / `mysql` / `postgres`、切り替えはコード変更なし |
| use_global_db | boolean | false | 仅 SQLite：パッケージ内のグローバルデータベースを使用するか、プロジェクト固有のデータベースを使用するか |
| storage.mysql.* | table | 見上 | MySQL接続パラメータ（host / port / user / password / database / charset / pool） |
| storage.postgres.* | table | 見上 | PostgreSQL接続パラメータ（host / port / user / password / database / pool） |

環境変数による上書きもサポート（Docker / 12-factor）：`ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`。

> [!TIP]
> - 接続パラメータを変更した後はフレームワークを再起動して有効にする必要があります；接続プールの作成が瞬時失敗した場合は指数関数的に再試行されます
> - バックエンドを切り替える前に検証スクリプトで自検査できます：`python tests/devs/test_storage_backend_verify.py --backend mysql`
> - トランザクション / ディアレクト / 自定义バックエンドなど完全な説明は[ストレージバックエンド](../advanced/storage-backends.md)を参照してください

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
| case_sensitive | boolean | true | 大文字小文字を区別するかどうか（`/Help` と `/help` が異なるコマンドとして扱われるか） |
| allow_space_prefix | boolean | false | プレフィックスとして空白文字を許可するかどうか |
| must_at_bot | boolean | false | コマンドをトリガーするには@botが必要かどうか（プライベートチャットでは制限されない） |

### メッセージ設定

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| ignore_self | boolean | true | ロボット自身のメッセージを無視するかどうか |

> イベントの重複除去は3層構造で、各層が異なる種類の重複を処理します：`event_dedupe`（フレームワーク、同じイベントIDの重複投递）→ `ignore_self`（本節、ロボット自身のメッセージ）→ `cross_account_policy`（フレームワーク、複数アカウントによる同じグループの内容レベルのコピー）。各層の役割は[アダプタのコア概念](../developer-guide/adapters/core-concepts.md)を参照してください。

## 会話受信箱設定（transcript）

```toml
[ErisPulse.transcript]
enabled = true
max_per_session = 50
ttl_hours = 168.0
self_echo = "bot"
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| enabled | boolean | true | 自動的に受信/送信メッセージを記録するかどうか（無効にすると書き込みを停止し、履歴は照会可能） |
| max_per_session | int | 50 | 1セッションに保持する件数（0 = セッションの裁断を無効化） |
| ttl_hours | float | 168.0 | 全体の保持期間（時間、0 = 永久に削除しない） |
| self_echo | string | bot | 受信 bot リエコ（`self.user_id == user_id`、OneBot `report-self-message`）の処理：`bot` = botとして記録し `meta.self_echo` を設定；`skip` = 記録しない；`user` = userとして記録（旧動作） |

> 保持戦略のリスクと監査は [会話受信箱](../advanced/transcript.md) を参照してください；帰属フィールド（`sender` / `meta`）と送信の帰属（`meta.module`）も同ドキュメントを参照してください。

## 国際化設定

```toml
[ErisPulse.i18n]
language = "auto"
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| language | string | auto | フレームワークの内臓テキストの表示言語。`auto` に設定するとシステム言語を自動検出し、`zh-CN`、`zh-TW`、`en`、`ja`、`ru` などの具体的なコードに設定することもできます |

## モジュール設定

各モジュールは設定ファイルに独自の設定を定義できます：

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

モジュール内で設定を読み取り、書き込みます：

```python
from ErisPulse import sdk

# 設定を読み取る
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# 実行時に設定を書き込む（遅延保存）
sdk.config.setConfig("MyModule.timeout", 60)

# 即時保存
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` はデフォルトで遅延書き込み（約5秒ごとに一括保存）されます。`immediate=True` を設定すると即時永続化されます。設定変更は `config.set` ライフサイクルイベントをトリガーします。

## スコープ設定（scope）

> [!NOTE]
> 本特性は ErisPulse **2.8.0+** が必要です。

スコープは「**どの範囲で有効か**」を宣言します——あるプラットフォーム / Bot / セッションでどのモジュールが有効か（① モジュール次元）、あるユーザー / グループ / Bot / アダプタのイベントを受信するかどうか（② アイデンティティ次元）、モジュールがどの出力呼び出しを行うことができるか（③ 出力次元）：

```toml
[ErisPulse.scope]
default_allow = true        # グローバルデフォルト（false = 隠式拒否の厳格モード；出力次元には影響しない）
cache_size = 1024           # LRUキャッシュサイズ

# ① モジュール次元（優先度：セッション > Bot > プラットフォーム；条目は正確 / glob / re: 正規表現）
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]
blocked = ["re:^Danger"]

# 子級バインディングは merge = true の場合、低優先度の条目と並列にマージ（デフォルトは全体を上書き）
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true

# ② アイデンティティ次元（優先度：ユーザー > セッション > Bot > アダプタ；各レベルは allow か deny のどちらか一方だけを書く）
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                 # 該当プラットフォームのすべてのイベントはエントランスで破棄される

[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]         # ユーザーのキーは glob / re: 正規表現をサポート
deny = ["u_bad", "spam_*"]

# ③ 出力次元（デフォルトは全許可；条目はインラインテーブル、条目は正確 / glob / re: 正規表現をサポート）
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                    # 全ての送信を禁止
api = { allow = ["get_*"] }               # クエリ系の標準APIのみ許可
request = { deny = true }                 # リクエストの処理を禁止
```

| 設定項目 | 型 | 説明 |
|---------|------|------|
| `scope.default_allow` | boolean | グローバルデフォルト：モジュール/アイデンティティがルールにヒットしない場合の許可/拒否（`true`） |
| `scope.cache_size` | integer | LRUキャッシュサイズ（デフォルト 1024） |
| `scope.platforms / bots / sessions` | table | ① モジュール3段階バインディング：`{modules=[...], blocked=[...], merge=bool?}` |
| `scope.identity.adapters / bots / sessions / users` | table | ② アイデンティティ4段階バインディング：`{allow=true}` / `{deny=true}` |
| `scope.actions.<module>.<action>` | table | ③ 出力ルール：`{allow=[...], deny=true|[...]}`（actionは send / api / request） |

> 詳細と実行時API（次元化 `sdk.scope.set_module()` / `set_identity()` / `set_action()`、判定 `is_allowed()` / `is_identity_allowed()` / `is_action_allowed()`、および辞書式デフォルト `get()` / `set()` / `delete()`）は[スコープ（scope）](../advanced/scope.md)を参照してください。

## 統一イベント覆写設定（event.overrides）

統一覆写システム：**イベントタイプごとに**任意のモジュールハンドラの動作を覆写し、モジュールコードを変更することなく動作をカスタマイズします。OneBot12標準タイプ（meta / message / notice / request）と拡張タイプ（command）はそれぞれ独自の覆写可能なパラメータを持ちます：

```toml
[ErisPulse.event.overrides]

# message：テキストのトリガー条件（コード内条件とAND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice / request / meta：detail_typeのホワイトリスト（条目は正確 / glob / re: 正規表現）
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command（拡張タイプ）：実装のパラメータ覆写（ユーザーが優先；無効化はacl deny）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true               # 覆写をフレームワークマスターのみに（falseなら開発者のマスター制限を解除）
hidden = true               # ヘルプリストから非表示
aliases = ["rs"]            # 生效别名

# acl（command専用）：コマンドのユーザーのホワイトリスト/ブラックリスト（コマンド名は glob / re: 正規表現、正確なキーが優先）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]  # ユーザー識別子 "platform:user_id"
deny = ["onebot11:u_bad"]

# ACLデフォルト：ACLが設定されていないコマンドを許可（true）/ 厳密に拒否（false）
acl_default_allow = true
```

| 設定項目 | 型 | 説明 |
|---------|------|------|
| `event.overrides.message.<module>` | table | テキスト条件：`{pattern="...", regex="..."}` |
| `event.overrides.notice / request.<module>` | table | `{detail_types=[...], pattern, regex}` |
| `event.overrides.meta.<module>` | table | `{detail_types=[...]}` |
| `event.overrides.command.<module>` | table | モジュールレベルのパラメータ覆写（`hidden = true` 等のスカラー） |
| `event.overrides.command.<module>.<command>` | table | コマンドレベルの覆写（コマンドレベルが優先） |
| `event.overrides.acl.<command名>` | table | ユーザーのホワイトリスト/ブラックリスト：`{allow=[...], deny=[...]}` |
| `event.overrides.acl_default_allow` | boolean | ACLデフォルト：ACLが設定されていないコマンドを許可（`true`）/ 厳密に拒否（`false`） |

> 実行時API（`from ErisPulse.Core.Event import overrides` 後、タイプのサブネームスペースに従って `overrides.message.set()` / `overrides.command.set()` / `overrides.acl.set()` など、または `sdk.Event.overrides` でアクセス）は [イベント処理入門 · イベント覆写](../getting-started/event-handling.md#イベント覆写不改模块代码覆写任意イベント类型的行为) を参照してください。

## 次に

- **L1経路に従って**：次のドキュメント [エラー捕捉](../advanced/errors.md) で、フレームワークをクラッシュさせないエラー処理の書き方を学びます
- **手動でTOMLを書きたくない**：`epsdk config` でインタラクティブな設定入力を使用して、宣言的な設定項目を記入します。[CLIコマンドリファレンス · config](cli-reference.md#config) を参照してください
- **設定ファイルを変更したくない**：環境変数で設定項目を上書きし、[デプロイガイド](deployment.md)のDockerの使い方を参照してください