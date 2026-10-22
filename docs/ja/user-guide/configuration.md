# 設定ファイルの説明

> [!NOTE]
> **L1 コア必読**——トップページの「学習パス」にある5つのコアドキュメントの1つで、モジュール開発に必須です。

> このドキュメントでは、フレームワーク自体の設定ファイル `config/config.toml` について説明します。各設定セクションが何を管理しているか、どのセクションがホットリロードに対応しているか、環境変数で上書きする方法などです。サードパーティモジュールの設定項目については、各モジュール自身のドキュメントを参照してください。

ErisPulse は、TOML 形式の設定ファイル `config/config.toml` を使用してプロジェクトの設定を管理します。

## 設定ファイルの位置

設定ファイルはプロジェクトのルートディレクトリの `config/` フォルダ内にあります：

```
project/
├── config/
│   └── config.toml
├── main.py
```

### 複数インスタンスの注意点とロックファイル

フレームワークを起動する際、プロジェクトのルートの実行状態ディレクトリ **`.erispulse/`** に `config.lock` ロックファイルを作成し、プロセス終了まで保持します（複数インスタンスが共有する設定ディレクトリを検出するため；2.10 以前は `config/` ディレクトリの `.erispulse_config.lock` にあり、アップグレード後に初めて起動すると自動的に削除されます）。ログに「設定ファイルが他の ErisPulse インスタンスによって同時に使用されている可能性がある」という警告が出力された場合、**2つ以上の ErisPulse プロセスが同じ設定ファイルを書き込んでいる**ことを意味します（典型的なシナリオ：複数のコンテナが同じホストマシンの `config/` ディレクトリをマウントしている）——並行書き込みは互いに上書きするため、各インスタンスに独立した設定ディレクトリを使用してください。

### 敏感な設定はバージョン管理に含めない

設定ファイルにはトークン（token / API key）などの機密情報が含まれます：フレームワークの初期化と `epsdk init` は自動的に `config/` ディレクトリに `.gitignore`（内容は一行のみ `*`——**ディレクトリ内のすべてのファイルをバージョン管理から除外し、除外ファイル自身も除外対象に含まれる**）を生成します；既存の `.gitignore` は上書きされません。`.erispulse/` 実行状態ディレクトリ（インスタンスロック、CLI 実行状態ファイル）も同様にローカルマシンの状態に属し、プロジェクトテンプレートの `.gitignore` は既定で除外されています。

## 設定の読み込みエラー処理

フレームワークは `config.toml` を読み込む際に、3つのエラー状態を区別し、**操作可能な診断情報を提供**します。デフォルト値に静かに回復するのではなく、警告を出力します。

| エラー状態 | 発生条件 | フレームワークの動作 |
|---------|---------|---------|
| ファイルが存在しない | `config.toml` が存在しない | 正常な初期起動で、空の設定を使用（警告を出力しない） |
| TOML 形式エラー | ファイルは存在するが形式が無効（例：引用符が欠けている、括弧が閉じていない） | **行番号/列番号と原因**を出力し、**前回の有効な設定を保持して実行を継続**（今回のファイルの変更は有効にならない） |
| 権限/その他のエラー | 読み取り権限がない、IO エラーなど | **明確な原因**を出力し、**前回の有効な設定を保持して実行を継続** |

> **「前回の有効な設定」はデフォルト値とは異なる**：ファイルが破損した場合、フレームワークは**今回の起動前の最後に成功した設定**（実行中にホット更新でファイルを破損させた場合は旧値を保持）を使用します。障害対処の際、「設定がリセットされた」と仮定しないでください。

たとえば、`port = 8000`（引用符のない文字列）と誤って記述した場合、ログには次のような出力がされます：

```
[ERROR] [Config] 設定ファイル config/config.toml の形式エラー（第 3 行 第 1 列）: ...
[WARNING] [Config] 設定ファイルの読み取りに失敗しました。前回の有効な設定を使用して実行を継続します。今回のファイルの変更は有効になりません。修正後、再度読み込みまたは再起動してください。
```

これにより、**デフォルトの INFO レベル**で問題をすぐに特定でき、「なぜ設定を変更しても効果がないのか」を混乱させません。

> **実行中に設定ファイルを破損させた場合？** ロボットの実行中に `config.toml` を手動編集して構文エラーを導入した場合、フレームワークは次回の書き込み（設定のマージ）時に「設定ファイルが破損しました（構文エラー、第 X 行）、マージ書き込みができないため、設定ファイルを修正して再起動してください」と出力します。混乱する「書き込みに失敗しました」ではなく、待機中の設定項目は保持され、失われることはありません。

## コメントの保持と最小限の書き込み

config.toml の**コメントとキーの順序は、フレームワークが書き込んだ後も完全に保持されます**：コード `setConfig()`、CLI 設定ウィザードの保存、またはアダプタ/モジュールの初期設定テンプレート生成において、フレームワークは対象のキーのみを変更し、ユーザーが書いたコメントや整理された順序は削除や再配置されません（tomlclass による無損失 TOML エンジンを使用、未触れた内容はバイト単位で保証、ファイルの CRLF/LF 行末スタイルも変更されません）。

フレームワークは書き込み内容を最小限に抑えます：

- **フレームワークのデフォルト設定は自動的に書き込まれません**：`gc`、`scope`、`transcript` などの組み込みデフォルト値はメモリ内に保持され、config.toml には明示的に設定されたキーのみが含まれ、最小限に保たれます。完全な設定項目はプロジェクト内の `config/config.full.example` を参照し、必要に応じて config.toml にコピーして編集してください（未設定の項目は一律組み込みデフォルト値を使用し、動作は変わりません）。
- **`config.full.example` は自動的に維持されます**：`epsdk init` を実行したかどうかに関わらず、フレームワークを起動するたびに（`epsdk run` / `main.py`）、`config/config.full.example` が存在しない場合、自動的に完全な設定の参考を生成します。ファイルの先頭行はフレームワークが維持するマーカーであり、生成器の内容が更新された場合（例：新しい設定項目、新しくインストールされたコンポーネント）、起動時に一度更新されます。先頭行を削除または変更すると、手動で管理し、フレームワークは上書きしません。
- **アダプタ/モジュールの設定テンプレート**：初期化時にコメント付きのテンプレートを書き込みます（フィールドの説明がコメントになります）；`example` というマークが付いているフィールドは書き込まれず、`config.full.example` に記録され、参考用です。
- **宣言的なコメントの再読み込み**：設定ファイル内のコメントはドキュメントそのものです——`ep doctor` と設定の検証エラーの提示は、該当フィールドのファイル中のコメント原文を引用します（ユーザーがコメントを変更しても、エラーメッセージはファイルの現状に従います）。エラー時に、再びドキュメントを調べてフィールドの意味を確認する必要はありません。

## 環境変数による上書き

フレームワークは環境変数によって `ErisPulse.*` 設定項目を**上書き**することをサポートしています（Docker / コンテナ化 / CI 部署に適しています。`config.toml` を変更する必要はありません）。

命名規則：点分パス `ErisPulse.<section>.<key>` をすべて大文字にし、`.` を `_` に置き換え、`ERISPULSE_` を前置します：

| 設定項目 | 環境変数 | 例値 |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `2` |

動作の説明：

- **優先度が最も高い**：環境変数は「設定ファイル」および「デフォルト値」を上書きし、元の値の型に応じて自動的に変換します（`bool` / `int` / `float` / カンマ区切りの `list` / 文字列）
- **永続化されない**：上書きは実行中にのみ有効で、`config.toml` には書き込まれません
- **ホット更新がサポートされている**：実行中に環境変数を変更した後、設定の監視のリロードと組み合わせて有効になります

```bash
# Docker 部署の例：config.toml を変更せず、直接ポートを上書き
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> 注：`ErisPulse.server.port` のようなフレームワークの設定は `get_server_config()` などの API で読み取られ、すべて環境変数の上書きの影響を受けます。

### モジュールの設定の環境変数バインディング（2.9.0+）

モジュール独自の宣言的な設定（`ConfigClass`）は、フィールドレベルの環境変数バインディングをサポートしています——`field(metadata=...)` で `env` を宣言します：

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

- **優先度**：環境変数 > `config.toml` > 宣言デフォルト値（設定ファイルのホット更新後もこの優先度を維持）
- **型変換**：環境変数の値はフィールドの注釈に応じて自動的に変換されます——`str` はそのまま、`int` / `float` / `bool`（`true` / `1` / `yes` / `on`）は自動的に変換、`list` / `dict` は JSON 解析を通じて変換されます；変換に失敗した場合は、該当の上書きを無視し（設定ファイル / デフォルト値に戻り）、警告を出力します
- **宣言1か所、どこでも有効**：設定の読み取り、ホット更新、検証は同じパイプラインを使用します；設定パネルの Schema は `env` 名をマークし、`config.toml` テンプレートのコメントも利用可能な環境変数を提示します（テンプレートには環境変数の実際の値は書き込まれず、漏洩を防ぎます）
- **完全に互換性がある**：`env` を宣言していないフィールドの動作は変わりません；フレームワークの設定パイプラインを経ていない `ConfigClass` のインスタンス化は環境変数の影響を受けません

```bash
# Docker 部署の例：config.toml を変更せず、モジュールのキーを直接注入
MYMODULE_API_KEY=sk-xxx docker compose up -d
```

> **設定クラス vs モデルフィールドはどちらを使うか？** 設定クラスは「モジュールがどのように動作するか」（動作パラメータ、ホット更新）を管理し、ORM の `Field()` は「ユーザーがどのようなデータを生成したか」（データベーステーブル、クエリ）を管理します。両者は同一の約束事表と検証エンジンを使用しています；対照表は [データモデル層 · どちらの宣言を使うか](../developer-guide/orm.md#どちらの宣言を使うか) を参照してください。

## 設定のホット更新

2.7.0 以降、フレームワークは設定のホット更新を**体系的にサポート**しています。外部で `config.toml` を変更した後（バックグラウンドの watcher が 5 秒ごとにチェック）、またはコードで `setConfig()` を呼び出した後、各コンポーネントが自動的に応答します：

| コンポーネント | ホット更新がサポートされている設定 | 動作 |
|------|----------------|------|
| **ログ Logger** | `logger.level` / `log_files` / `log_dir`（分割パラメータを含む）/ `memory_limit` / `format` / `exclude_levels` | 変更検出付きで自動的に再適用されます |
| **コマンドシステム CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | 次のメッセージで即座に有効になります |
| **アダプタの並行処理** | `framework.handler_max_concurrency` | 失効したキャッシュ信号をリセットし、新しい値で再構築します |
| **アクティブ GC** | `framework.proactive_gc_*` | 設定の変更で即座に GC タスクを再起動し、実行時に調整/無効化/再有効化がサポートされます |
| **マスター システム Master** | `master.users` | `is_master()` のチェックで毎回リアルタイムに読み取り、再起動は不要です |
| **モジュール/アダプタの設定** | 各自の設定項目 | `on_config_update(old, new)` コールバックをトリガーします |

**再起動が必要な設定**（安全にホット切り替えできないため、変更時に「プロセスを再起動後に有効になる」という警告が出力されます）：

| 設定 | 理由 |
|------|------|
| `router.cors.*` / `router.security.*` | ミドルウェアはサービスの起動時に FastAPI に書き込まれ、実行中に安全にホット切り替えできない |
| `storage.use_global_db` | SQLite ファイルハンドルは実行時に開かれているため、パスの切り替えは安全ではない |

> **途中で編集保存に失敗した場合？** `config.toml` を編集している間に一時的な構文エラーが発生した場合、フレームワークは**前回の有効な設定を保持**し、診断ログを出力します。各コンポーネントに空の設定をブロードキャストすることはありません（`on_config_update` が空値を誤ってデフォルトに戻すのを防ぎます）。

### ホット更新の内部の詳細

「設定を変更した後、各コンポーネントはどのように知るのか？」——背後には、検出 → 再ロード → ブロードキャストのチェーンがあります：

```mermaid
flowchart TD
    A["外部で config.toml を編集"] --> B{"誰が最初に発見するか？"}
    B -->|"バックグラウンドの watcher スレッド<br/>5秒ごとに mtime をルーペンする"| C["_check_file_change で変更を判定"]
    B -->|"コードで設定を読み取るとき<br/>キャッシュが60秒以上経過している"| C
    C --> D["_load_config で TOML を再解析"]
    D --> E{"解析に成功したか？"}
    E -->|"いいえ（構文エラー）"| F["前回の有効な設定を保持<br/>ブロードキャストは行わず、診断ログを出力"]
    E -->|"はい"| G["lifecycle.emit config.updated<br/>old_config / new_config を持参"]
    G --> H["各コンポーネントのリスナーが応答<br/>（logger / scope / コマンド / GC ...）"]
```

**2つの検出経路**（どちらか1つで十分、どちらもバックアップになります）：

| 経路 | メカニズム | 発動タイミング |
|------|------|---------|
| バックグラウンド watcher | daemon スレッド `config-watcher` が **5秒** `wait` でファイル `mtime` をルーペン | 外部でファイルを変更した後、最大5秒以内に |
| 慣性検出 | 任意の `getConfig()` 読取時に、キャッシュが **60秒**以上経過していればファイルをチェック | 次回の設定の読み取り時に |

> **フレームワークは自分自身を誤って傷つけません**：`setConfig()` で書き込む際、自身が書き込んだ `mtime` を記録し、watcher はそれを除外して、**外部の編集のみを変更とみなします**。

**2種類の設定変更イベント**：

| イベント | 発動者 | データ | 典型的なシナリオ |
|------|--------|------|---------|
| `config.set` | コード / Dashboard が `setConfig()` を呼び出す | `{key, old_value, new_value}` | 単一キーの書き込み（テンプレート生成、状態記録、実行時の設定変更） |
| `config.updated` | 外部編集後に watcher/慣性検出が捕捉 | `{old_config, new_config, config_file}` | 手動で `config.toml` を編集した場合 |

> `setConfig()` はデフォルトで**5秒遅延して書き込み**（複数の書き込みをマージ）されます。`immediate=True` で即時書き込み。watcher が外部の変更を検出した後は、メモリのキャッシュを更新するだけで、**ファイルへの書き戻しは行いません**。

**自動応答対象リスト**（2種類のイベントは通常両方サブスクライブし、応答内容は一致します）：

| コンポーネント | 監視 | 応答 |
|------|------|------|
| Logger | `config.set` + `config.updated` | レベル/ファイル/ディレクトリ分割/メモリ上限/フォーマット/無視レベルを再適用（変更検出付き、変更なしでは動かない） |
| Scope | `config.updated` | スコープバインディングのキャッシュを再構築 |
| コマンドシステム | `config.updated` | プレフィックス/大文字小文字/スペースプレフィックス/must_at_bot の解析パラメータを更新し、次のメッセージで有効になります |
| アダプタの並行処理 | `config.set` + `config.updated` | `handler_max_concurrency` で失効した信号を再構築 |
| アクティブ GC | `config.set` + `config.updated` | `proactive_gc_*` で即座に GC バックグラウンドタスクを再起動 |
| アダプタ | `on_config_update` にルーティング | 各アダプタの `on_config_update(old, new)` コールバック |
| モジュール | `on_config_update` にルーティング | 各モジュールの `on_config_update(old, new)` コールバック |
| ストレージ | `config.updated` | `use_global_db` 変更は**警告のみ**（再起動が必要） |
| ルーター | `config.updated` | `cors.*` / `security.*` 変更は**警告のみ**（再起動が必要） |

## 設定の読み取りと削除 API

### getAllConfig：全量設定のスナップショット

プライベート属性 `_cache` を直接読み取る代わりに（外部からプライベート属性を読み取るのはバージョン互換性の保護を受けない）：

```python
config = sdk.config.getAllConfig()     # 深いコピーのスナップショット、元の場所を変更してもフレームワークの状態に影響しない
config["ErisPulse"]["server"]["port"]
```

ビューの口径は `getConfig` と同じ：`setConfig` / `delete` による遅延書き込みは反映され、ファイルの内容と厳密に一致します。

### delConfig：設定キーの削除

`setConfig(key, None)` は単に空に設定し、キーはファイル内に保持されます；`delConfig` はキーをファイルから**削除**します：

```python
sdk.config.delConfig("ErisPulse.modules.status.OldModule")            # 遅延書き込み
sdk.config.delConfig("OneBot.deprecated_key", immediate=True)         # 即時書き込み
```

- 点分パスをサポート；キーが存在しない場合は `False` を返す
- 書き込みはコメント保持の経路を再利用し、ファイルの他の内容や順序は影響を受けません
- `config.set` イベントのブロードキャストを再利用（`new_value=None`）：アダプタ / モジュールの `on_config_update` などの既存のリスナーは変更なしで削除を感知できます

## 完全な設定例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.master]
# users は2種類の書式（1つを選ぶ）：
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
# 容器 / ファイルがマウントされていない場合は、内包 PEM コンテンツを使用（優先度は certfile/keyfile パスより高い）
# ssl_cert = """-----BEGIN CERTIFICATE-----
# ...
# -----END CERTIFICATE-----"""
# ssl_key = """-----BEGIN PRIVATE KEY-----
# ...
# -----END PRIVATE KEY-----"""
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 監聴アドレス、0.0.0.0 はすべてのインターフェースを意味する |
| port | integer | 8000 | 監聴ポート番号 |
| auto_start | boolean | true | `sdk.init()` 時にルーティングサーバーを自動的に起動するかどうか。`false` に設定するとルーティングサーバーの起動をスキップ（純粋なイベント/WebUI なしのシナリオ） |
| ssl_certfile | string | 空 | SSL 証明書ファイルのパス |
| ssl_keyfile | string | 空 | SSL 秘密鍵ファイルのパス |
| ssl_cert | string | 空 | **内包 PEM 証明書コンテンツ**（パスではなく）。`ssl_key` とペアで使用する場合、`ssl_certfile`/`ssl_keyfile` パスよりも優先され、フレームワークは SSL コンテキストを構築するために一時的に書き込み、すぐに一時ファイルを削除します |
| ssl_key | string | 空 | **内包 PEM 秘密鍵コンテンツ**（パスではなく）、上記と同じ意味 |

> **ポートの占有は致命的なエラーではない**：起動時に `port` が既に占有されている場合、フレームワークはルーティングサーバーの起動をスキップし、警告を出力しますが、**アダプタとモジュールは通常通り動作します**（HTTP/WS/SSE ルーティングと WebUI は利用できません）。ロボットは動作するが WebUI が開かない場合の原因を確認する際は、ポートを確認してください。

## マスターシステム設定

マスターシステムは「フレームワークのマスター」アカウント（例：Bot管理者）を識別するために使用します。`master.users` は2種類の書式をサポートしています：

```toml
[ErisPulse.master]
# 書式1：グローバルマスター（すべてのプラットフォームに有効）
users = ["123456", "789012"]

# 書式2：プラットフォームごとにマスターを指定（dict）
# users = { yunhu = ["123456"], telegram = ["789012"] }
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| users | array / object | 空 | マスターアカウントリスト。`list` 形式はグローバルマスター（すべてのプラットフォームに有効）；`dict` 形式はプラットフォームごとに指定（キーはプラットフォーム名、値はそのプラットフォームのマスターアカウントリスト） |

コードでは `master.is_master(event)` または `master.is_master(platform, user_id)` でチェックし、毎回呼び出すたびに設定をリアルタイムに読み取ります（ホット更新に対応し、再起動は不要です）：

```python
from ErisPulse.Core import master

if master.is_master(event):
    await event.reply("マスター、こんにちは")
```

### 判定チェーンと実行時追加

マスター判定チェーンは **設定マスター → 実行時記録 → provider チェーン** です：

```python
from ErisPulse.Core import master

master.is_master(event)                      # イベントから判定
master.is_master("yunhu", "123")             # 明示的に判定
master.add("yunhu", "123")                   # 実行時に追加（デフォルトで永続化；persist=False はメモリ内のみ）
master.remove("yunhu", "123")                # 削除（デフォルトで永続化）
master.list()                                # 総合：{"global": [...], "<platform>": [...]}
```

### 自定義アイデンティティソース（provider）

設定以外にも、独自のアイデンティティソースを登録できます：`fn(platform, user_id) -> bool`。組み込みアイデンティティソース（設定 + 実行時記録）が一致しなかった場合、順次試行し、いずれかの provider が許可された場合、マスターと判定されます。適切なアダプタ管理者インターフェース、データベースロールなどの外部アイデンティティ体系に接続するのに適しています。

登録エントリ `master.provider` はデコレータ / 関数式の2種類の書き方ができ、アンロックは登録された関数の `fn.unregister()` を通じて行います：

```python
from ErisPulse.Core import master

# 書き方1：デコレータ（常駐アイデンティティソース、推奨）
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # 自定義判定ロジック

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # 使用しない場合、アンロック

# 書き方2：関数式（モジュールロード期に登録 / アンロード期にアンロック）
fn = master.provider(admin_provider)
fn.unregister()
```

> provider での例外はキャッチされてスキップされ、アイデンティティ判定チェーンをブロックしません。インスタンスメソッドをバインドした `unregister` は持たず、登録/アンロックのペアが必要な場合は**モジュールレベルの関数**を使用してください。

### ユーザー優先：マスターの有効範囲はユーザーが最終決定

コマンドの `master=True` は**開発者のデフォルト**です：ユーザーは
`ErisPulse.event.overrides.command.<module>.<cmd>.master = true/false`
を上書きして厳しくしたり緩めたりできます（[統一イベントオーバーライド設定](#統一イベントオーバーライド設定eventoverrides) を参照、ユーザーの明示的な設定が有効になります）。

## ログ設定

```toml
[ErisPulse.logger]
level = "INFO"
log_files = []                # 明示的なログファイルリスト（log_dir と互換性あり、優先度が高くなる）
log_dir = ""                  # ログ出力ディレクトリ（自動作成）。設定すると、erispulse.log に自動的に分割され、log_rotation に従って自動的に分割される；log_files と互換性があり、log_files が優先される）
log_rotation = "size"         # 分割方法: "size" / "date" / "none"
log_max_size_mb = 10          # size モードの単一ファイルの上限（MB）
log_backup_count = 5          # 保持する履歴ログファイルの数
log_rotation_when = "midnight"  # date モードの分割周期: S/M/H/D/midnight（デフォルトは毎日0時）
memory_limit = 1000
exclude_levels = ["EVENT"]
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| level | string | INFO | ログレベル：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACE は最低レベルで、フレームワーク内部の詳細なデバッグ情報を出力） |
| format | string | rich | ログ出力フォーマット：`rich`（カラー、デフォルト）、`plain`（純粋なテキスト、色なし、ログの収集/パイプのリダイレクトに適している）、`json`（JSON形式、ELKなどに適している） |
| log_files | array | 空 | ログ出力ファイルのリスト（明示的なパス、分割しない） |
| log_dir | string | 空 | ログ出力ディレクトリ（自動作成）。設定すると、log_dir 内の `erispulse.log` に書き込まれ、log_rotation に従って自動的に分割される；log_files と互換性があり、log_files が優先される） |
| log_rotation | string | size | 分割方法：`size`（サイズで）、`date`（日付で）、`none`（分割しない） |
| log_max_size_mb | float | 10 | size モードの単一ファイルのサイズ上限（MB）、超過すると .1/.2 などのバックアップに分割される |
| log_backup_count | integer | 5 | 保持する履歴ログファイルの数、最も古いバックアップが自動的に削除される |
| log_rotation_when | string | midnight | date モードの分割周期：`S`/`M`/`H`/`D`/`midnight`（デフォルトは毎日0時） |
| memory_limit | integer | 1000 | メモリに保持するログの件数 |
| exclude_levels | array | 空 | ログレベルを無視する。無視されたレベルのログは**完全に破棄される**（メモリに書き込まれず、ダッシュボードなどのサブスクライバーに送信されず、表示されず、ファイルに書き込まれない）。ホット更新に対応する |

コード内で動的に切り替えることもできます：

```python
from ErisPulse.Core import logger

# サイズで分割：1ファイル10MB、5件保持
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# 日付で分割：毎日0時にローテーション、7件保持
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]
> `log_dir` および分割関連の設定は ErisPulse **2.8.0+** が必要です。

> **プライバシー保護**：メッセージの送受信内容は **EVENT レベル**（数値 21）で記録されます。`exclude_levels = ["EVENT"]` を設定すると、バックエンド（例：ダッシュボードのログパネル）が各グループ/プライベートチャットのメッセージ内容を見ることができなくなり、他のレベルのログには影響しません。

> [!NOTE]
> `exclude_levels` 本特性は ErisPulse **2.8.0+** が必要です。

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
| enable_lazy_loading | boolean | true | モジュールのラジーロードを有効にするかどうか |
| uninit_timeout | integer | 30 | グラスローズの総タイムアウト時間（秒）、これを超えると強制終了する。0 はタイムアウトを設定しないことを意味する |
| strict_mode | integer | 0 | 严格モードのレベル、下の「厳格モード」の説明を参照 |
| handler_max_concurrency | integer | 64 | イベントハンドラの最大並行タスク数、大きくするとスループットが向上するがメモリ使用量も増える |
| offline_bot_expiry | integer | 3600 | オフライン Bot 記録の自動期限時間（秒）、0 は期限を設定しないことを意味する |

### アクティブ GC 設定

SDK の初期化後にアクティブ GC バックグラウンドタスクを起動し、定期的に Python の GC と内部リソースの回収（オフライン Bot のクリーンアップなど）を実行します。すべてのパラメータはホット更新に対応し、変更時にタスクを即座に再起動します。

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | 回収間隔（秒）、小数もサポート。0 はアクティブ GC を無効にする |
| proactive_gc_generation | integer | 0 | 通常のラウンドのガベージ回収世代（0/1/2、0..2に制限）。注意 `gc.collect(2)` は全量回収に相当し、デフォルトは 0 で軽量に保たれる；深い回収は `proactive_gc_full_every` で周期的に実行される |
| proactive_gc_full_every | integer | 20 | N 回ごとに全量回収を行う、0 は周期的な全量回収を無効にする。全量回収は `proactive_gc_memory_growth_mb` のしきい値に制約される |
| proactive_gc_memory_growth_mb | integer | 32 | 全量回収のメモリ増加しきい値（MB）：前回の全量回収後のメモリベースライン（tracemallocを優先し、次にRSS）と比較し、この値に達した場合に全量回収を実行する。0 はしきい値を設定しない |
| proactive_gc_idle_only | boolean | false | 有効にすると、イベントの激増時（未完了のpending handlerがある）には、このラウンドはPython GCをスキップし、メッセージ処理との競合を回避する。内部リソース回収は影響を受けない |
| proactive_gc_gen0_min | integer | 500 | 通常のラウンドで回収をトリガーする gen0 ゴミの量の下限：`gc.get_count()[0]` がこの値より低い場合はスキップする（空回りのラウンドはほぼゼロコスト）。0 は常に回収する |

> **2.7.1 変更**：デフォルト `proactive_gc_generation` は `2` から `0` に調整され、`proactive_gc_full_every` は `0` から `20` に調整されました。以前は `generation=2` は毎ラウンド最も重い全量回収を意味していました；新しいデフォルトは回収のカバレッジを維持しながら空回りのコストを大幅に削減します。明示的に設定された旧値は文字通りの意味で動作します。

### 厳格モード

厳格モードは、モジュール/アダプタのロード段階で不適切または失敗した場合の処理戦略を制御します。現代のモジュール/アダプタは、それぞれの基底クラス（`BaseModule`/`BaseAdapter`）を継承する必要があります。基底クラスを継承していないコンポーネントは、フレームワークのコンテキストシステムとバックアップのクリーンアップに影響を与え、リソースリークを引き起こす可能性があります。

> **2.5.2 変更**：デフォルトレベルは `1`（スキップ）から `0`（緩和）に調整され、新規ユーザーの初期使用時のロード問題を減らしました。基底クラスを継承していないコンポーネントは、警告として表示され、ロードを試みるだけでなく、直接拒否されます。以前の動作を回復するには、`strict_mode = 1` を明示的に設定してください。

| レベル | 名称 | 行動 |
|------|------|------|
| 0 | 緩和（デフォルト） | 不正は警告のみ、基底クラスを継承していないコンポーネントもロードされる（旧コンポーネントの互換性） |
| 1 | 厳格-スキップ | 基底クラスを継承していないコンポーネントを拒否してスキップし、他の正常な起動 |
| 2 | 厳格-致命 | すべての不正を収集して一括で報告し、起動チェックポイントで全体を停止 |

各レベルで、「ロード/登録/初期化段階でエラー」が発生したコンポーネント自身のクラッシュは常にスキップされます。違いは以下の通りです：

- **0 → 1**：唯一の動作変化は「基底クラスを継承していない」が「ロードされる」から「スキップされる」になることです。
- **1 → 2**：すべての不正（基底クラスを継承していない、ロード失敗、登録失敗、初期化失敗など）が致命的になり、起動チェックポイントで一括して不正リストを出力して停止されます。

#### 豁免リスト

一部のコンポーネントが一時的に移行できない場合（例：依存する旧モジュール）、豁免リストに追加することで、不正なコンポーネントでも緩和モードでロードし続けることができます：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> コンポーネントが厳格モードで拒否された場合、ログはどのようにしてロードを回復するかを明確に示します（豁免リストに追加するか、レベルを下げること）。

#### CLI との連携

`epsdk run` の起動前の自己検証（設定ファイルの解析性、コンポーネントの必須設定の完全性）はデフォルトで本設定に従います：非 0 の場合、検証失敗で起動を拒否し、0 の場合、警告を出して継続します。また、設定を変更せずに一時的に切り替えることもできます：`epsdk run --strict` で今回は自己検証と厳格モードを同時に有効にします（レベルは下がらない、`ERISPULSE_FRAMEWORK_STRICT_MODE` 環境変数を通じて実行プロセスに伝達）、`--no-strict` で一時的に緩和モードにし、警告のみになります。

## ストレージ設定

2.8.0 以降、ストレージエンジンは 3 つの非同期バックエンドをサポートし、**API は完全に一致、設定は 1 クリックで切り替え**：

| バックエンド | ドライバー | インストール | 特徴 |
|------|------|------|------|
| SQLite（デフォルト） | aiosqlite | 開梱即用 | 零設定、単一ファイル、WAL 並行 |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | 既存の MySQL 基礎インフラ、多インスタンス共有 |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | トランザクション力が強く、高並行 |

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
| use_global_db | boolean | false | 仅 SQLite：パッケージ内グローバルデータベースを使用するか、プロジェクト固有のデータベースを使用するか |
| storage.mysql.* | table | 上記参照 | MySQL 接続パラメータ（host / port / user / password / database / charset / pool） |
| storage.postgres.* | table | 上記参照 | PostgreSQL 接続パラメータ（host / port / user / password / database / pool） |

また、環境変数による上書きもサポートしています（Docker / 12-factor）：`ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`。

> [!TIP]
> - 接続パラメータを変更した後はフレームワークの再起動が必要です；接続プールの作成が一時的に失敗した場合、指数関数的な退避を繰り返し再試行します
> - バックエンドを切り替える前に検証スクリプトで自検査できます：`python tests/devs/test_storage_backend_verify.py --backend mysql`
> - トランザクション / ディアレクトの違い / 自定義バックエンドの完全な説明は[ストレージバックエンド](../advanced/storage-backends.md)を参照してください

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
| case_sensitive | boolean | true | 大文字小文字を区別するかどうか（`/Help` と `/help` が異なるコマンドになるか） |
| allow_space_prefix | boolean | false | スペースをプレフィックスとして許可するかどうか |
| must_at_bot | boolean | false | コマンドをトリガーするには@Botが必要かどうか（プライベートチャットは制限されない） |

### メッセージ設定

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| ignore_self | boolean | true | 自分のメッセージを無視するかどうか |

## 国際化設定

```toml
[ErisPulse.i18n]
language = "auto"
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| language | string | auto | フレームワークが内部テキストを表示する言語。`auto` に設定するとシステム言語を自動検出する、具体的なコード（`zh-CN`、`zh-TW`、`en`、`ja`、`ru`）に設定することもできる |

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

# 実行時に設定を書き込み（遅延保存）
sdk.config.setConfig("MyModule.timeout", 60)

# ファイルに即時保存
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` はデフォルトで遅延書き込み（約5秒ごとにバッチ保存）されます。`immediate=True` で即時永続化。設定の変更は `config.set` ライフサイクルイベントをトリガーします。

## スコープ設定（scope）

> [!NOTE]
> 本特性は ErisPulse **2.8.0+** が必要です。

スコープは「**どの範囲で有効か**」を宣言します——あるプラットフォーム / Bot / セッションでどのモジュールが使えるか（① モジュール次元）、あるユーザー / グループ / Bot / アダプタのイベントを受信するかしないか（② アイデンティティ次元）、モジュールがどの出力呼び出しを行えるか（③ 出力次元）：

```toml
[ErisPulse.scope]
default_allow = true        # グローバルデフォルト（false = 隠蔽拒否厳格モード；出力次元には影響しない）
cache_size = 1024           # LRU キャッシュサイズ

# ① モジュール次元（優先度：セッション > Bot > プラットフォーム；条目は正確 / glob / re: 正則）
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]
blocked = ["re:^Danger"]

# 子継承は merge = true で低優先度と逐条目並列（デフォルトは全体上書き）
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true

# ② アイデンティティ次元（優先度：ユーザー > セッション > Bot > アダプタ；各レベルは allow または deny のみ）
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                 # 該当プラットフォームのすべてのイベントを入口で破棄
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]         # ユーザーキーは glob / re: 正則に対応
deny = ["u_bad", "spam_*"]

# ③ 出力次元（デフォルトは全許可；ルールはインライン表、条目は正確 / glob / re: 正則に対応）
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                    # 送信を全禁止
api = { allow = ["get_*"] }               # クエリ系標準APIのみ許可
request = { deny = true }                 # リクエスト処理を禁止
```

| 設定項目 | 型 | 説明 |
|---------|------|------|
| `scope.default_allow` | boolean | グローバルデフォルト：モジュール/アイデンティティがルールに合致しない場合の許可/拒否（`true`） |
| `scope.cache_size` | integer | LRU キャッシュサイズ（デフォルト 1024） |
| `scope.platforms / bots / sessions` | table | ① モジュール三次元バインディング：`{modules=[...], blocked=[...], merge=bool?}` |
| `scope.identity.adapters / bots / sessions / users` | table | ② アイデンティティ四次元バインディング：`{allow=true}` / `{deny=true}` |
| `scope.actions.<module>.<action>` | table | ③ 出力ルール：`{allow=[...], deny=true|[...]}`（アクションは send / api / request） |

> 詳細と実行時 API（次元化 `sdk.scope.set_module()` / `set_identity()` / `set_action()`、判定 `is_allowed()` / `is_identity_allowed()` / `is_action_allowed()`、および辞書式デフォルト `get()` / `set()` / `delete()`）は[スコープ（scope）](../advanced/scope.md)を参照してください。

## 統一イベントオーバーライド設定（event.overrides）

統一オーバーライドシステム：イベントの**タイプ**ごとに任意のモジュールハンドラの動作をオーバーライドし、モジュールのコードを変更せずに実現します。OneBot12 標準タイプ（meta / message / notice / request）と拡張タイプ（command）はそれぞれ独自のオーバーライド可能なパラメータを持ちます：

```toml
[ErisPulse.event.overrides]

# message：テキストのトリガー条件（コード内の条件と AND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice / request / meta：detail_type ホワイトリスト（条目は正確 / glob / re: 正則に対応）
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command（拡張タイプ）：パラメータのオーバーライドを実現（ユーザーが優先；無効化は acl deny を使う）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true               # フレームワークマスターのみに設定（false で開発者のマスター制限を解除）
hidden = true               # ヘルプリストから非表示
aliases = ["rs"]            # 生効果のエイリアス

# acl（command 専用）：コマンドのユーザーホワイトリスト/ブラックリスト（コマンド名は glob / re: 正則に対応、正確なキーが優先）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]  # ユーザー識別子 "platform:user_id"
deny = ["onebot11:u_bad"]

# ACL デフォルト：ACL が設定されていないコマンドの許可（true）/ 厳密拒否（false）
acl_default_allow = true
```

| 設定項目 | 型 | 説明 |
|---------|------|------|
| `event.overrides.message.<module>` | table | テキスト条件：`{pattern="...", regex="..."}` |
| `event.overrides.notice / request.<module>` | table | `{detail_types=[...], pattern, regex}` |
| `event.overrides.meta.<module>` | table | `{detail_types=[...]}` |
| `event.overrides.command.<module>` | table | モジュールレベルのパラメータオーバーライド（`hidden = true` などのスカラー） |
| `event.overrides.command.<module>.<command>` | table | コマンドレベルのオーバーライド（コマンドレベルが優先） |
| `event.overrides.acl.<command名>` | table | ユーザーホワイトリスト/ブラックリスト：`{allow=[...], deny=[...]}` |
| `event.overrides.acl_default_allow` | boolean | ACL デフォルト：ACL が設定されていないコマンドの許可（`true`）/ 厳密拒否（`false`） |

> 実行時 API（`from ErisPulse.Core.Event import overrides` 後、タイプのサブネームスペースで `overrides.message.set()` / `overrides.command.set()` / `overrides.acl.set()` などを呼び出す、または `sdk.Event.overrides` でアクセス）
> 詳細は [イベント処理入門 · イベントオーバーライド](../getting-started/event-handling.md#イベントオーバーライドしないでモジュールコードを変更せずに任意のイベントタイプの動作をオーバーライド) を参照してください。

## 次のステップ

- **L1 パスで継続**：次は [例外のキャッチ](../advanced/errors.md)。フレームワークをダウンさせないエラー処理の書き方を学びましょう
- **TOML を手書きしたくない場合**：`epsdk config` のインタラクティブウィザードで宣言型の設定項目を入力できます。詳しくは [CLI コマンドリファレンス · config](cli-reference.md#config) を参照
- **デプロイ時に設定ファイルを変更したくない場合**：環境変数で設定項目を上書きし、[デプロイガイド](deployment.md) の Docker の使い方と組み合わせてください