# 設定ファイルの説明

> [!NOTE]
> **L1 コア必読**——トップページ「読むべき経路」の5つのコアドキュメントの1つ、モジュール開発に必須。

> 本ドキュメントは、フレームワーク自身の設定ファイル `config/config.toml` について説明します：各設定セクションが何を管理するか、どの設定がホットリロードをサポートするか、環境変数でどのように上書きできるか。サードパーティのモジュールの設定項目は、モジュール独自のドキュメントを参照してください。

ErisPulse は、プロジェクトの設定を管理するために TOML 形式の設定ファイル `config/config.toml` を使用します。

## 設定ファイルの位置

設定ファイルは、プロジェクトのルートディレクトリの `config/` フォルダ内に配置されます：

```
project/
├── config/
│   └── config.toml
├── main.py
```

### 複数インスタンスの注意事項とロックファイル

フレームワークが起動する際、プロジェクトのルートの実行ステータスディレクトリ **`.erispulse/`** に `config.lock` ロックファイルを作成し、プロセス終了まで保持します（複数インスタンスが設定ディレクトリを共有しているかを検出するため；2.10 以前は `config/` ディレクトリの `.erispulse_config.lock` が、アップグレード後に最初の起動時に自動的に削除されます）。ログに「設定ファイルが他の ErisPulse インスタンスによって同時に使用されている可能性がある」という警告が表示された場合、**2つ以上の ErisPulse プロセスが同じ設定ファイルを書き込んでいる**ことを意味します（典型的なシナリオ：複数のコンテナが同じホストマシンの `config/` ディレクトリをマウントしている）——並行書き込みは互いに上書きするため、各インスタンスに独立した設定ディレクトリを使用してください。

### 敏感な設定はバージョン管理に含めない

設定ファイルにはトークン（token / API key）などの機密情報が含まれます：フレームワークの初期化と `epsdk init` は、`config/` ディレクトリ内に `.gitignore` を自動的に生成します（内容は一行だけ `*` ——**ディレクトリ内のすべてのファイルをバージョン管理から除外し、除外ファイル自身も除外対象に含まれる**）。既存の `.gitignore` は上書きされません。`.erispulse/` 実行ステータスディレクトリ（インスタンスロック、CLI 実行ステータスファイル）も、ローカルマシンの状態に属するため、プロジェクトテンプレートの `.gitignore` は既定で除外されています。

## 設定の読み込みエラー処理

フレームワークは `config.toml` を読み込む際に、3つのエラー状態を区別し、**操作可能な診断情報を提供**します。デフォルト設定に静かに戻るのではなく、警告を出力します：

| エラー状態 | 発生条件 | フレームワークの動作 |
|---------|---------|---------|
| ファイルが存在しない | `config.toml` が存在しない | 正常な初回起動では、空の設定を使用し、警告を出さない |
| TOMLの構文エラー | ファイルは存在するが、形式が無効（例：クォートが足りない、括弧が閉じられていない） | **行番号/列番号と原因**を出力し、**前回の有効な設定を保持して実行を継続**（今回のファイルの変更は有効にならない） |
| 権限/その他のエラー | 読み取り権限がない、IOエラーなど | **明確な原因**を出力し、**前回の有効な設定を保持して実行を継続** |

> **「前回の有効な設定」= デフォルト設定ではない**：ファイルが破損した場合、フレームワークは**今回の起動前の最後に解析された有効な設定**（実行中にホットリロードでファイルを破損させた場合は、以前の値を保持）を使用し、すべての設定項目を出荷時のデフォルトに戻すことはありません。故障の対処では、設定がリセットされたと仮定しないでください。

たとえば、設定を `port = 8000`（クォートのない文字列）と誤って記述した場合、ログには次のような出力がされます：

```
[ERROR] [Config] 設定ファイル config/config.toml の構文エラー（第 3 行 第 1 列）: ...
[WARNING] [Config] 設定ファイルの読み取りに失敗しました。前回の有効な設定を使用して実行を継続し、今回のファイルの変更は有効になりません——修正して再度読み込みまたは再起動してください
```

このように、**デフォルトの INFO レベル**で問題をすぐに特定でき、「なぜ設定を変更しても効果がないのか」と困惑する必要がありません。

> **実行中に設定ファイルを破損させた場合？** ロボットが実行中に `config.toml` を手動編集して構文エラーを導入した場合、フレームワークは次回の書き込み（設定のマージ）時に「設定ファイルが破損しました（構文エラー、第 X 行）、マージ書き込みができない——まず設定ファイルを修正して再起動してください」と出力し、「書き込みに失敗しました」という困惑するメッセージを出力しません。書き込まれる設定項目は保持され、失われることはありません。

## コメントの保持と最小限の書き込み

config.toml の**コメントとキーの順序は、フレームワークが書き込んだ後も完全に保持されます**：コード `setConfig()`、CLI 設定ウィザードの保存、またはアダプター/モジュールの最初の設定テンプレート生成において、フレームワークは関連するキーのみを変更し、ユーザーが書いたコメントや整理された順序は削除や並べ替えされません（tomlclass による無損失 TOML エンジンのため、未触碰の内容はバイト単位で保全され、ファイルの元の CRLF/LF 改行スタイルも変更されません）。

フレームワークは書き込み内容を最小限に抑えます：

- **フレームワークのデフォルト設定は自動的に書き込まれない**：`gc`、`scope`、`transcript` などの組み込みのデフォルト値はメモリ内に駐留し、config.toml には明示的に設定したキーのみが含まれ、最小限になります。完全な設定項目は、プロジェクト内の `config/config.full.example` を参照してください。必要に応じて `config.toml` にコピーして編集してください（未設定の項目は一律組み込みのデフォルト値を使用し、動作は変わりません）。
- **`config.full.example` の自動維持**：`epsdk init` を実行したかどうかに関係なく、フレームワークを起動するたび（`epsdk run` / `main.py`）に、`config/config.full.example` が欠落している場合、自動的に生成されます。ファイルの先頭行はフレームワークが維持するマークです。生成器の内容が更新された場合（新しい設定項目、新しいコンポーネントの追加など）、起動時に更新されます。先頭行を削除または変更すると、手動で管理され、フレームワークは上書きしません。
- **アダプター/モジュールの設定テンプレート**：最初の初期化時に、コメント付きのテンプレートとしてファイルに書き込まれます（フィールドの説明がコメントとして記録されます）。`example` とマークされたフィールドは書き込まれず、`config.full.example` に記録され、参照用です。
- **宣言的なコメントの再読**：設定ファイル内のコメントがドキュメントそのものになります——`ep doctor` と設定の検証に失敗した時のメッセージは、該当フィールドのファイル内のコメント原文を引用します（ユーザーがコメントを手動で変更した場合でも、メッセージはファイルの現状に従い、エラー時にドキュメントを再確認する必要がありません）。

## 環境変数による上書き

フレームワークは、**環境変数**を用いて `ErisPulse.*` 設定項目を上書きする機能を提供しています（Docker / コンテナ化 / CI 部署に適しています。`config.toml` を変更する必要がありません）。

命名規則：`ErisPulse.<セクション>.<キー>` のピリオド区切りパスを大文字にし、`.` を `_` に置き換え、`ERISPULSE_` を接頭辞として追加します：

| 設定項目 | 環境変数 | 例値 |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `2` |

動作説明：

- **優先度が最も高い**：環境変数は「設定ファイル」および「デフォルト値」を上書きし、元の値の型に応じて自動変換されます（`bool` / `int` / `float` / コマ区切りの `list` / 文字列）
- **永続化されない**：上書きは実行中にのみ有効で、`config.toml` には書き込まれません
- **ホットリロードがサポートされている**：実行中に環境変数を変更した後、設定監視のリロードを組み合わせることで有効になります

```bash
# Docker 部署の例：config.toml を変更せずに、ポートを上書きする
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> 注：`ErisPulse.server.port` などのフレームワーク設定は `get_server_config()` などの API で読み取られ、環境変数の上書きの影響を受けます。

### モジュール設定の環境変数バインディング（2.9.0+）

モジュールの独自の宣言的設定（`ConfigClass`）は、フィールドレベルで環境変数をバインディングできます——`field(metadata=...)` で `env` を宣言します：

```python
@dataclass
class MyConfig(BaseConfig):
    api_key: str = field(default="", metadata={
        "description": "API キー",
        "env": "MYMODULE_API_KEY",   # 環境変数バインディング
    })
    retries: int = field(default=3, metadata={"env": "MYMODULE_RETRIES"})
```

動作説明：

- **優先度**：環境変数 > `config.toml` > 宣言のデフォルト値（設定ファイルのホットリロード後もこの優先度を保持）
- **型変換**：環境変数の値はフィールドの注釈に応じて自動変換されます——`str` はそのまま、`int` / `float` / `bool`（`true` / `1` / `yes` / `on`）は自動変換、`list` / `dict` は JSON 解析に従い、変換に失敗した場合はその上書きを無視して（設定ファイル / デフォルト値に戻り）警告を出力
- **宣言1か所、どこでも有効**：設定の読み取り、ホットリロード、検証は同じパイプラインを使用；設定パネルの Schema は `env` 名をマークし、`config.toml` テンプレートのコメントは利用可能な環境変数を提示します（テンプレートは環境変数の実際の値を書き込まないため、漏洩を防ぎます）
- **完全に互換性がある**：`env` を宣言していないフィールドの動作は変化しない；フレームワークの設定パイプラインを経ない `ConfigClass` のインスタンス化は環境変数の影響を受けない

```bash
# Docker 部署の例：config.toml を変更せずに、モジュールの秘密鍵を注入する
MYMODULE_API_KEY=sk-xxx docker compose up -d
```

> **設定クラス vs モデルフィールドはどちらを使うか？** 設定クラスは「モジュールがどのように動作するか」（動作パラメータ、ホットリロード）を管理し、ORM の `Field()` は「ユーザーがどのようなデータを生成したか」（データベーステーブル、クエリ）を管理します。両者は同一の制約語表と検証エンジンを使用しています；対照表は [データモデル層 · どちらの宣言を使うべきか](../developer-guide/orm.md#どちらの宣言を使うべきか) を参照してください。

## 設定のホットリロード

2.7.0 以降、フレームワークは設定のホットリロードを**体系的にサポート**しています。外部から `config.toml` を変更した後（バックグラウンドの watcher が 5 秒ごとに検出）、またはコードで `setConfig()` を呼び出した後、各コンポーネントは自動的に応答します：

| コンポーネント | ホットリロードがサポートされる設定 | 動作 |
|------|----------------|------|
| **ログ Logger** | `logger.level` / `log_files` / `log_dir`（分割パラメータを含む）/ `memory_limit` / `format` / `exclude_levels` | 変更検出付きで自動的に再適用 |
| **コマンドシステム CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | 次のメッセージで即座に有効 |
| **アダプターの並行処理** | `framework.handler_max_concurrency` | キャッシュシグナルを無効化し、新しい値で再構築 |
| **アクティブ GC** | `framework.proactive_gc_*` | 設定の変更で即座に GC タスクを再起動し、実行時の調整/無効化/再有効化が可能 |
| **マスターシステム Master** | `master.users` | `is_master()` 検査は毎回リアルタイムで読み取り、再起動は不要 |
| **モジュール/アダプターの設定** | 各自の設定項目 | `on_config_update(old, new)` コールバックをトリガー |

**再起動が必要な設定**（安全にホット切り替えできないため、変更時に「プロセスを再起動後に有効」という警告が表示される）：

| 設定 | 理由 |
|------|------|
| `router.cors.*` / `router.security.*` | ミドルウェアがサービス起動時に FastAPI に書き込まれ、実行中に安全にホット切り替えできない |
| `storage.use_global_db` | SQLite ファイルハンドルが実行時に開かれているため、パスの切り替えは安全ではない |

> **途中で編集保存に失敗した場合？** `config.toml` を編集中に一時的な構文エラーが発生した場合、フレームワークは**前回の有効な設定を保持**し、診断ログを出力します。各コンポーネントに空の設定をブロードキャストして（`on_config_update` が空値を受けてデフォルトに戻る誤動作を防ぐ）`on_config_update` に空値を渡すことはありません。

### ホットリロードの内部プロセス分解

「設定を変更した、各コンポーネントはどうやって知るのか？」——背後には検出 → 再読み込み → ブロードキャストのプロセスがあります：

```mermaid
flowchart TD
    A["外部から config.toml を編集"] --> B{"誰が最初に気づく？"}
    B -->|"バックグラウンドの watcher スレッド<br/>5 秒ごとに mtime をループチェック"| C["_check_file_change で変更を判定"]
    B -->|"コードで設定を読み取るとき<br/>キャッシュが 60 秒以上経過"| C
    C --> D["_load_config で TOML を再解析"]
    D --> E{"解析に成功した？"}
    E -->|"いいえ（構文エラー）"| F["前回の有効な設定を保持<br/>ブロードキャストはせず、診断ログを出力"]
    E -->|"はい"| G["lifecycle.emit config.updated<br/>old_config / new_config を含む"]
    G --> H["各コンポーネントのリスナーが応答<br/>（logger / scope / コマンド / GC ...）"]
```

**2つの検出経路**（どちらか1つで十分、両方でバックアップ）：

| 経路 | メカニズム | 発生タイミング |
|------|------|---------|
| バックグラウンド watcher | daemon スレッド `config-watcher` が **5 秒**ごとに `wait` でファイルの `mtime` をループチェック | 外部でファイルを変更した後、最大 5 秒以内に |
| 慣性検出 | 任意の `getConfig()` 読み取り時、キャッシュが **60 秒**以上経過していれば、まずファイルをチェック | 次回の設定の読み取り時 |

> **フレームワークは自分自身を誤って傷つけない**：`setConfig()` でファイルに書き込む際、自身が書き込んだ `mtime` を記録し、watcher はそれを除外して、**外部の編集**のみを変更とみなします。

**2種類の設定変更イベント**：

| イベント | トリガー | データ | 代表的なシナリオ |
|------|--------|------|---------|
| `config.set` | コード / Dashboard が `setConfig()` を呼び出す | `{key, old_value, new_value}` | 単一キーの書き込み（テンプレート生成、状態記録、実行時の設定変更） |
| `config.updated` | 外部編集後に watcher/慣性検出が捕捉 | `{old_config, new_config, config_file}` | 手動で `config.toml` を編集 |

> `setConfig()` はデフォルトで**5秒遅延してファイルに書き込む**（複数の書き込みを1回にまとめる）。`immediate=True` で即時書き込み。watcher が外部の変更を検出した後は、メモリのキャッシュを更新するだけで、**外部の変更をファイルに書き戻すことはない**。

**自動応答コンポーネントリスト**（2種類のイベントは通常両方をサブスクライブし、応答内容は一致）：

| コンポーネント | 監視 | 応答 |
|------|------|------|
| Logger | `config.set` + `config.updated` | レベル/ファイル/ディレクトリの分割/メモリ上限/フォーマット/除外レベルを再適用（変更検出付き、変更なしは動かない） |
| Scope | `config.updated` | スコープバインディングのキャッシュを再構築 |
| コマンドシステム | `config.updated` | プレフィックス/大文字小文字/スペースプレフィックス/must_at_bot の解析パラメータを更新し、次のメッセージで有効 |
| アダプターの並行処理 | `config.set` + `config.updated` | `handler_max_concurrency` で無効化し、シグナルを再構築 |
| アクティブ GC | `config.set` + `config.updated` | `proactive_gc_*` で即時 GC バックグラウンドタスクを再起動 |
| アダプター | `config.updated` にルーティング | 各アダプターの `on_config_update(old, new)` コールバック |
| モジュール | `config.updated` にルーティング | 各モジュールの `on_config_update(old, new)` コールバック |
| ストレージ | `config.updated` | `use_global_db` 変更は**警告のみ**（再起動が必要） |
| ルーター | `config.updated` | `cors.*` / `security.*` 変更は**警告のみ**（再起動が必要） |


## 設定の読み取りと削除 API

### getAllConfig：全量設定スナップショット

プライベート `_cache` の直接読み取り（外部からプライベート属性を読み取るのはバージョン互換性の保護を受けない）を代替します：

```python
config = sdk.config.getAllConfig()     # 深いコピーのスナップショット、原地変更はフレームワークの状態に影響しない
config["ErisPulse"]["server"]["port"]
```

ビューポートは `getConfig` と同じです：遅延書き込み後のファイル内容と厳密に一致します。

### delConfig：設定キーの削除

`setConfig(key, None)` は値を空にしているだけで、キーはファイルに残ります；`delConfig` はキーをファイルから**削除**します：

```python
sdk.config.delConfig("ErisPulse.modules.status.OldModule")            # 遅延書き込み
sdk.config.delConfig("OneBot.deprecated_key", immediate=True)         # 即時書き込み
```

- ドット区切りパスをサポート；キーが存在しない場合は `False` を返す
- 書き込みはコメント保持経路を使用し、ファイルの他の内容や順序は影響を受けない
- `config.set` イベントブロードキャストを再利用（`new_value=None`）：アダプターやモジュールの `on_config_update` などの既存のリスナーは変更なしで削除を感知できる

## 完全な設定例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.master]
# users は2つの書式（選択肢）がサポートされています：
#   全局マスター（すべてのプラットフォームで有効）：users = ["123456", "789012"]
#   プラットフォームごとに指定：users = { yunhu = ["123456"], telegram = ["789012"] }
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
# コンテナ / ファイルがマウントされていない環境では、内臓 PEM コンテンツを使用（path に優先）
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
| auto_start | boolean | true | `sdk.init()` 時にルーティングサーバーを自動的に起動するかどうか。`false` に設定するとルーティングサーバーの起動をスキップ（純粋なイベント/無 WebUI のシナリオ） |
| ssl_certfile | string | 空 | SSL 証明書ファイルのパス |
| ssl_keyfile | string | 空 | SSL 秘密鍵ファイルのパス |
| ssl_cert | string | 空 | **内臓 PEM 証明書内容**（パスではない）。`ssl_key` とペアで使用する場合、`ssl_certfile`/`ssl_keyfile` パスよりも優先される；フレームワークは SSL コンテキストを構築して即座に一時ファイルを削除する |
| ssl_key | string | 空 | **内臓 PEM 秘密鍵内容**（パスではない）、上記と同じ意味 |

> **ポートの占有は致命的なエラーではない**：起動時に `port` が既に占有されている場合、フレームワークはルーティングサーバーの起動をスキップして警告を出力し、**アダプターとモジュールは通常通り実行される**（HTTP/WS/SSE ルーティングと WebUI は利用できない）。ロボットは動くが WebUI が開かない場合のトラブルシューティングでは、まずポートを確認すること。

## マスターシステム設定

マスターシステムは、**フレームワークマスター**アカウント（例：Bot管理者）を識別するために使用されます。`master.users` は2つの書式をサポートしています：

```toml
[ErisPulse.master]
# 書式1：グローバルマスター（すべてのプラットフォームで有効）
users = ["123456", "789012"]

# 書式2：プラットフォームごとに指定（dict）
# users = { yunhu = ["123456"], telegram = ["789012"] }
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| users | array / object | 空 | マスターアカウントリスト。`list` 形式はグローバルマスター（すべてのプラットフォームで有効）；`dict` 形式はプラットフォームごとに指定（キーがプラットフォーム名、値がそのプラットフォームのマスターアカウントリスト） |

コードでは `master.is_master(event)` または `master.is_master(platform, user_id)` でチェックし、毎回呼び出し時にリアルタイムで設定を読み込み（ホットリロードに対応、再起動不要）：

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
master.add("yunhu", "123")                   # 実行時に追加（デフォルトは永続化；persist=False はメモリ内のみ）
master.remove("yunhu", "123")                # 削除（デフォルトは永続化）
master.list()                                # 総合：{"global": [...], "<platform>": [...]}
```

### 自定义アイデンティティソース（provider）

設定以外にも、カスタムアイデンティティソースを登録できます：`fn(platform, user_id) -> bool`、
組み込みのアイデンティティソース（設定 + 実行時記録）がヒットしなかった場合、順次試行し、いずれかが許可された場合、マスターと判定されます。
アダプターの管理者インターフェース、データベースの役割などの外部アイデンティティ体系に適しています。

登録エントリ `master.provider` はデコレータ / 関数式の2種類の書き方ができ、
登録された関数は `fn.unregister()` で登録解除できます：

```python
from ErisPulse.Core import master

# 書き方1：デコレータ（常駐アイデンティティソース、推奨）
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # 自定義判定ロジック

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # 不要になったら登録解除

# 書き方2：関数式（モジュールロード期に登録 / ロード解除期に登録解除）
fn = master.provider(admin_provider)
fn.unregister()
```

> provider の例外はキャッチされてスキップされ、アイデンティティ判定チェーンをブロックしません。
> インスタンスメソッドをバインドして `unregister` を登録することはできず、登録/登録解除のペアが必要な場合は**モジュールレベルの関数**を使用してください。

### ユーザー優先：マスターの有効範囲はユーザーが最終的に決定

コマンドの `master=True` は**開発者のデフォルト**です：ユーザーは
`ErisPulse.event.overrides.command.<module>.<cmd>.master = true/false`
をオーバーライドして、厳格化または緩和（[一括イベントオーバーライド設定](#一括イベントオーバーライド設定eventoverrides)）できます。ユーザーの明示的な設定が有効です。

## ログ設定

```toml
[ErisPulse.logger]
level = "INFO"
log_files = []                # 明示的なログファイルリスト（log_dir と互換性があり、優先度が高い）
log_dir = ""                  # ログ出力ディレクトリ（自動的に作成）。設定すると、erispulse.log に自動的に分段ラウンドローテーションされる；log_files と互換性があり、log_files が優先）
log_rotation = "size"         # 分段方式: "size" / "date" / "none"
log_max_size_mb = 10          # size モードの単ファイル上限（MB）
log_backup_count = 5          # 保持する履歴ログファイル数
log_rotation_when = "midnight"  # date モードのラウンドローテーション周期: S/M/H/D/midnight（デフォルトは毎日0時）
memory_limit = 1000             # 単モジュールのメモリ内ログ条数上限（0 = メモリログコピーをオフにする）
total_memory_limit = 5000       # 全モジュールのメモリログ総条数上限（0 = 制限なし）。超えた場合、ラウンドローテーション戦略に従って最も古い記録を削除（最も条数の多いモジュールのキューから優先的に削除）、単モジュールの memory_limit とは独立して有効）
exclude_levels = ["EVENT"]
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| level | string | INFO | ログレベル：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACE が最低レベルで、フレームワーク内部の詳細なデバッグ情報を出力） |
| format | string | rich | ログ出力フォーマット：`rich`（カラー、デフォルト）、`plain`（カラーなしの純文本、ログ収集/パイプ重定向に適している）、`json`（JSON形式、ELKなどに適している） |
| log_files | array | 空 | ログ出力ファイルリスト（明示的なパス、分割しない） |
| log_dir | string | 空 | ログ出力ディレクトリ（自動的に作成）。設定すると、ディレクトリ内に `erispulse.log` を書き込み、`log_rotation` に従って自動的に分割される；`log_files` と互換性があり、`log_files` が優先） |
| log_rotation | string | size | 分段方式：`size`（サイズで）、`date`（日付で）、`none`（分割しない） |
| log_max_size_mb | float | 10 | size モードの単ファイルサイズ上限（MB）、超過すると `.1`/`.2` のバックアップにラウンドローテーションされる |
| log_backup_count | integer | 5 | 保持する履歴ログファイル数、超えた古いバックアップは自動的に削除される |
| log_rotation_when | string | midnight | date モードのラウンドローテーション周期：`S`/`M`/`H`/`D`/`midnight`（デフォルトは毎日0時） |
| memory_limit | integer | 1000 | 単モジュールのメモリ内に保持されるログ条数；`0` はメモリログコピーをオフにする（メモリに書き込まない、既存の記録は保持） |
| total_memory_limit | integer | 5000 | 全モジュールのメモリログ総条数上限；`0` は制限しない。超えた場合、ラウンドローテーション戦略に従って最も古い記録を削除（最も条数の多いモジュールのキューから優先的に削除）、単モジュールの `memory_limit` とは独立して有効） |
| exclude_levels | array | 空 | 除外するログレベル。除外レベルのログは**完全に破棄**（メモリに書き込まない、ダッシュボードなどのサブスクライバーに送信しない、出力しない、ファイルに書き込まない）。ホットリロードに対応 |

コード内でも動的に切り替え可能です：

```python
from ErisPulse.Core import logger

# サイズで分割：1ファイル10MB、5個保持
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# 日付で分割：毎日0時でラウンドローテーション、7個保持
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]
> `log_dir` および分割関連の設定は ErisPulse **2.8.0+** が必要です。

> **プライバシー保護**：メッセージの送受信内容は **EVENT** 等級（数値 21）で記録されます。`exclude_levels = ["EVENT"]` を設定すると、バックエンド（例：ダッシュボードのログパネル）が各グループ/プライベートチャットのメッセージ内容を見ることができなくなり、他の等級のログには影響しません。

> [!NOTE]
> `exclude_levels` 本機能は ErisPulse **2.8.0+** が必要です。

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
| uninit_timeout | integer | 30 | エレガントシャットダウンの総タイムアウト時間（秒）、超過後は強制終了。0 はタイムアウトを設定しない |
| strict_mode | integer | 0 | エンジニアモードレベル、下記「エクスプレスモード」の説明を参照 |
| handler_max_concurrency | integer | 64 | イベントハンドラの最大並行タスク数、大きくすると処理能力は向上するがメモリ使用量も増加する |
| handler_queue_max_pending | integer | 4096 | イベントの過負荷入隊制限：1プラットフォームの待機中のハンドラタスク数の上限、超過した場合、新しいイベントのハンドラタスクは直接破棄され、WARNING が記録される（破棄件数はトラブルシューティングで確認可能）；0 は制限しない |
| offline_bot_expiry | integer | 3600 | オフライン Bot 記録の自動期限切れ時間（秒）、0 は期限切れしない |
| plugins_dir | string / list | "plugins" | 本地プラグインのフォルダ（プロジェクトルートからの相対パス）；プラグインの追加/削除/変更はホットリロードの watcher が自動的に検出する |
| watch_ignore_dirs | list | 内部リスト | ホットリロードのファイル監視で無視するディレクトリ名（`.venv`/`.git`/`__pycache__` 等）；空のリストは**内部リストを全体的に置換**し、`[]` はどのディレクトリも無視しない |
| watch_include_plugin_dirs | boolean | true | `epsdk run --reload` がプラグインディレクトリをプラグインのホットリロード watcher に正確に処理させ、全量監視から除外するかどうか |

### アクティブ GC 設定

SDK 初期化後にバックグラウンドタスクが起動し、定期的に Python GC と内部リソースの回収（オフライン Bot のクリーンアップなど）を行う。すべてのパラメータはホットリロードに対応し、変更時にタスクを即座に再起動する。

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | 回収間隔（秒）、小数もサポート。0 はアクティブ GC を無効にする |
| proactive_gc_generation | integer | 0 | 通常のラウンドの GC 分代（0/1/2、0..2 に制限）。`gc.collect(2)` は全量 GC に等しい、デフォルトは 0 で軽量に保つ；深い GC は `proactive_gc_full_every` で定期的に実行 |
| proactive_gc_full_every | integer | 20 | N 輪ごとに全量 GC を実行する、0 は周期的な全量 GC を無効にする。全量 GC は `proactive_gc_memory_growth_mb` のしきい値によって制限される |
| proactive_gc_memory_growth_mb | integer | 32 | 全量 GC のメモリ増加しきい値（MB）：前回の全量 GC 後のメモリベースライン（優先 tracemalloc、次に RSS）と比較し、この値に達した場合に全量 GC を実行する。0 はしきい値を設定しない |
| proactive_gc_idle_only | boolean | false | 有効にすると、イベントの過負荷（未完了の pending handler がある）の時は、このラウンドは Python GC をスキップし、メッセージ処理との競合を避ける；内部リソースの回収には影響しない |
| proactive_gc_gen0_min | integer | 500 | 通常のラウンドで GC を実行する gen0 のゴミ量の下限：`gc.get_count()[0]` がこの値より小さい場合は、空のラウンドはほぼゼロコストでスキップする。0 は常に GC を実行する |

> **2.7.1 変更**：デフォルト `proactive_gc_generation` は `2` から `0` に調整され、`proactive_gc_full_every` は `0` から `20` に調整されました。以前は `generation=2` は毎ラウンド最も重い全量 GC を意味しました；新しいデフォルトは、回収カバレッジを維持しつつ、空のラウンドのオーバーヘッドを大幅に低減します。明示的に設定された旧値は文字通りの意味で動作します。

### エクスプレスモード

エクスプレスモードは、モジュール/アダプターが読み込み段階で不正な設定や失敗した場合の処理戦略を制御します。現代のモジュール/アダプターは `BaseModule`/`BaseAdapter` を継承する必要があります。継承していないコンポーネントはフレームワークのコンテキストシステムと兜底クリーンアップに影響し、リソースリークを引き起こす可能性があります。

> **2.5.2 変更**：デフォルトレベルは `1`（スキップ）から `0`（緩和）に調整され、新規ユーザーが初期使用時に遭遇する読み込み問題を減らしました。継承していないコンポーネントは警告として表示され、読み込みを試みます。以前の動作を復元するには、`strict_mode = 1` を明示的に設定してください。

| レベル | 名称 | 動作 |
|------|------|------|
| 0 | 緩和（デフォルト） | 不正な設定は警告のみ、`BaseModule`/`BaseAdapter` を継承していないコンポーネントも読み込みを試みる（旧コンポーネントとの互換性） |
| 1 | エクスプレス-スキップ | `BaseModule`/`BaseAdapter` を継承していないコンポーネントを拒否してスキップし、他のコンポーネントは正常に起動する |
| 2 | エクスプレス-致命 | すべての不正な設定を収集し、起動チェックポイントで一括してエラーリストを出力して起動を中断する |

各レベルで、**読み込み/登録/初期化段階でエラーが発生したコンポーネントは**、起動をスキップする。違いは以下の通りです：

- **0 → 1**：唯一の動作変化は「`BaseModule`/`BaseAdapter` を継承していない」コンポーネントが「読み込みを試みる」から「スキップする」に変わる。
- **1 → 2**：すべての不正な設定（`BaseModule`/`BaseAdapter` を継承していない、読み込み失敗、登録失敗、初期化失敗など）が致命的になり、起動チェックポイントでエラーリストを一括して出力して起動を中断する。

#### 補償リスト

一部のコンポーネントが一時的に移行できない場合（依存する旧モジュールなど）、そのコンポーネントを補償リストに追加することで、不正な設定でも緩和モードで読み込みを継続できます：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> あるコンポーネントがエクスプレスモードで拒否された場合、ログは明確に読み込みを回復する方法を提示します（補償リストに追加するか、レベルを下げること）。

#### CLI との連動

`epsdk run` の起動前の自己検査（設定ファイルの可解析性、コンポーネントの必須設定の完全性）はデフォルトで本設定に従います：0 でない場合、検査失敗で起動を拒否し、0 の場合は警告のみで継続します。設定を変更せずに一時的に切り替えることもできます：`epsdk run --strict` は今回の自己検査とエクスプレスモードを同時に有効にします（レベルは上げるだけ、`ERISPULSE_FRAMEWORK_STRICT_MODE` 環境変数で実行プロセスに伝達）、`--no-strict` は今回の起動を一時的に緩和して警告のみにします。

## ストレージ設定

2.8.0 以降、ストレージエンジンは3つの非同期バックエンドをサポートし、**APIは完全に一致し、設定は1回の切り替えで可能**です：

| バックエンド | ドライバー | インストール | 特徴 |
|------|------|------|------|
| SQLite（デフォルト） | aiosqlite | すぐに使用可能 | 零設定、単一ファイル、WAL並行 |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | 既存の MySQL インフラストラクチャ、複数インスタンス共有 |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | トランザクション能力強、高並行 |

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

環境変数による上書きもサポート（Docker / 12-factor）：`ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`。

> [!TIP]
> - 接続パラメータを変更した後はフレームワークの再起動が必要；接続プールの作成が一時的に失敗すると指数関数的に再試行される
> - バックエンドを切り替える前に検証スクリプトで自検証できる：`python tests/devs/test_storage_backend_verify.py --backend mysql`
> - トランザクション / ディアレクトの違い / 自定義バックエンドなどの完全な説明は[ストレージバックエンド](../advanced/storage-backends.md)を参照してください

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
| must_at_bot | boolean | false | コマンドをトリガーするには@Botが必要かどうか（プライベートチャットは制限されない） |

### メッセージ設定

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| ignore_self | boolean | true | 自身のメッセージを無視するかどうか |

## 会話の受信箱設定（transcript）

```toml
[ErisPulse.transcript]
enabled = true
max_per_session = 50
ttl_hours = 168.0
self_echo = "bot"
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| enabled | boolean | true | 自動で入力/出力メッセージを記録するかどうか（無効にすると書き込みを停止し、履歴は照会可能） |
| max_per_session | int | 50 | 1セッションに保持する条数（0 = セッションの切り替えを無効にする） |
| ttl_hours | float | 168.0 | 全体の保持期間（時間、0 = 永久に削除しない） |
| self_echo | string | bot | 入力 bot リエコ（`self.user_id == user_id`、OneBot `report-self-message`）の処理：`bot` = botとして記録し、`meta.self_echo` をマーク；`skip` = 記録しない；`user` = userとして記録（旧動作） |

> 保持戦略のリスクと監査は [会話の受信箱](../advanced/transcript.md) を参照してください。帰属フィールド（`sender` / `meta`）と出力の帰属（`meta.module`）も同ドキュメントを参照してください。

## 国際化設定

```toml
[ErisPulse.i18n]
language = "auto"
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| language | string | auto | フレームワークの内部テキストの表示言語。`auto` に設定するとシステム言語を自動検出、具体的なコード（`zh-CN`、`zh-TW`、`en`、`ja`、`ru`）に設定することもできる |

## モジュール設定

各モジュールは設定ファイルで独自の設定を定義できます：

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

モジュール内で設定を読み取り、書き込みします：

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

> `setConfig` はデフォルトで遅延書き込み（約5秒ごとに一括保存）を使用し、`immediate=True` で即時永続化。設定の変更は `config.set` ライフサイクルイベントをトリガーする。

## スコープ設定（scope）

> [!NOTE]
> 本機能は ErisPulse **2.8.0+** が必要です。

スコープは「**どの範囲で有効か**」を宣言します——あるプラットフォーム / Bot / セッションでどのモジュールが有効か（① モジュール次元）、あるユーザー / グループ / Bot / アダプターのイベントを受信するかどうか（② アイデンティティ次元）、モジュールがどの出力呼び出しを実行できるか（③ 出力次元）：

```toml
[ErisPulse.scope]
default_allow = true        # グローバルデフォルト（false = 隠蔽的な拒否の厳密モード；出力次元には影響しない）
cache_size = 1024           # LRU キャッシュサイズ

# ① モジュール次元（優先度：セッション > Bot > プラットフォーム；エントリは正確 / glob / re: 正則）
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]
blocked = ["re:^Danger"]

# 子級のバインディングは merge = true の場合、低優先度のエントリと逐次並列（デフォルトは全体の上書き）
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true

# ② アイデンティティ次元（優先度：ユーザー > セッション > Bot > アダプター；各レベルは allow または deny のどちらかを書く）
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                 # 該当プラットフォームのすべてのイベントをエントリで破棄

[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]         # ユーザーのキーは glob / re: 正則がサポートされる
deny = ["u_bad", "spam_*"]

# ③ 出力次元（デフォルトで全許可；ルールはインラインテーブル、エントリは正確 / glob / re: 正則がサポートされる）
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                    # 送信を全禁止
api = { allow = ["get_*"] }               # 限定された標準APIのみ許可
request = { deny = true }                 # リクエスト処理を禁止
```

| 設定項目 | 型 | 説明 |
|---------|------|------|
| `scope.default_allow` | boolean | グローバルデフォルト：モジュール/アイデンティティがルールにヒットしない場合の許可/拒否（`true`） |
| `scope.cache_size` | integer | LRU キャッシュサイズ（デフォルト 1024） |
| `scope.platforms / bots / sessions` | table | ① モジュールの3段階バインディング：`{modules=[...], blocked=[...], merge=bool?}` |
| `scope.identity.adapters / bots / sessions / users` | table | ② アイデンティティの4段階バインディング：`{allow=true}` / `{deny=true}` |
| `scope.actions.<module>.<action>` | table | ③ 出力ルール：`{allow=[...], deny=true|[...]}`（アクションは send / api / request） |

> 詳細と実行時 API（次元化 `sdk.scope.set_module()` / `set_identity()` / `set_action()`、判定 `is_allowed()` / `is_identity_allowed()` / `is_action_allowed()`、および辞書式のデフォルト `get()` / `set()` / `delete()`）は[スコープ（scope）](../advanced/scope.md)を参照してください。

## 一括イベントオーバーライド設定（event.overrides）

一括オーバーライドシステム：**イベントタイプ**ごとに任意のモジュールハンドラの動作をオーバーライドし、モジュールのコードを変更せずに実現します。OneBot12 標準タイプ（meta / message / notice / request）と拡張タイプ（command）はそれぞれ独自のオーバーライド可能なパラメータを持っています：

```toml
[ErisPulse.event.overrides]

# message：テキストのトリガー条件（コード内の条件と AND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice / request / meta：detail_type ホワイトリスト（エントリは正確 / glob / re: 正則がサポートされる）
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command（拡張タイプ）：実装のパラメータオーバーライド（ユーザー優先；無効化は acl deny）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true               # フレームワークマスターのみに変更（false は開発者のマスターリストを開放）
hidden = true               # ヘルプリストから非表示
aliases = ["rs"]            # 生效のエイリアス

# acl（command専用）：コマンドのユーザーホワイト/ブラックリスト（コマンド名は glob / re: 正則がサポートされる、正確なキーが優先）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]  # ユーザー識別子 "platform:user_id"
deny = ["onebot11:u_bad"]

# ACL デフォルト：ACL が設定されていないコマンドの許可（true）/ 厳密な拒否（false）
acl_default_allow = true
```

| 設定項目 | 型 | 説明 |
|---------|------|------|
| `event.overrides.message.<module>` | table | テキスト条件：`{pattern="...", regex="..."}` |
| `event.overrides.notice / request.<module>` | table | `{detail_types=[...], pattern, regex}` |
| `event.overrides.meta.<module>` | table | `{detail_types=[...]}` |
| `event.overrides.command.<module>` | table | モジュールレベルのパラメータオーバーライド（`hidden = true` などのスカラー） |
| `event.overrides.command.<module>.<command>` | table | コマンドレベルのオーバーライド（コマンドレベルが優先） |
| `event.overrides.acl.<command名>` | table | ユーザーホワイト/ブラックリスト：`{allow=[...], deny=[...]}` |
| `event.overrides.acl_default_allow` | boolean | ACL デフォルト：ACL が設定されていないコマンドの許可（`true`）/ 厳密な拒否（`false`） |

> 実行時 API（`from ErisPulse.Core.Event import overrides` の後、タイプのサブネームスペースにアクセスして `overrides.message.set()` / `overrides.command.set()` / `overrides.acl.set()` など、または `sdk.Event.overrides` からアクセス）は [イベント処理入門 · イベントオーバーライド](../getting-started/event-handling.md#イベントオーバーライドモジュールコードを変更せずに任意のイベントタイプの動作をオーバーライド) を参照してください。

## 次に

- **L1経路に従って**：次のドキュメント [例外のキャッチ](../advanced/errors.md) で、フレームワークをクラッシュさせないエラーハンドリングの書き方を学ぶ
- **手動でTOMLを書きたくない**：`epsdk config` でインタラクティブな設定入力ウィザードを使用して、宣言的な設定項目を入力する。[CLIコマンドリファレンス · config](cli-reference.md#config) を参照
- **設定ファイルを変更したくない**：環境変数で設定項目を上書きし、[デプロイガイド](deployment.md) の Docker の使い方と組み合わせる