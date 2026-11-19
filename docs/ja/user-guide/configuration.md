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

## 設定のホットアップデート

2.7.0以降、フレームワークは設定のホットアップデートを**体系的にサポート**しています。外部で `config.toml` を変更した後（バックグラウンドの watcher が5秒ごとにチェック）、またはコードで `setConfig()` を呼び出した後、各コンポーネントは自動的に反応します：

| コンポーネント | ホットアップデートをサポートする設定 | 動作 |
|------|----------------|------|
| **ロガー Logger** | `logger.level` / `log_files` / `log_dir`（分割パラメータ含む）/ `memory_limit` / `format` / `exclude_levels` | 変更検出付きで自動的に再適用 |
| **コマンドシステム CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | 次のメッセージで即座に有効 |
| **アダプタの並列処理** | `framework.handler_max_concurrency` | キャッシュされた信号量を無効化し、新しい値で再構築 |
| **アクティブGC** | `framework.proactive_gc_*` | 設定の変更でGCタスクを即座に再起動し、実行時の調整/無効化/再有効化をサポート |
| **マスターシステム Master** | `master.users` | `is_master()` 検査は毎回リアルタイムで読み取り、再起動は不要 |
| **モジュール/アダプタの設定** | 各々の設定項目 | `on_config_update(old, new)` カルバックをトリガー |

**再起動が必要な設定**（安全にホット切り替えできないため、変更時に「プロセスを再起動後に有効」という警告が出力されます）：

| 設定 | 理由 |
|------|------|
| `router.cors.*` / `router.security.*` | ミドルウェアはサービス起動時にFastAPIに書き込まれ、実行時に安全にホット切り替えできない |
| `storage.use_global_db` | SQLiteファイルハンドルは実行時にすでに開かれているため、パスの切り替えは安全ではない |
| `storage.sqlite.busy_timeout` | busy_timeoutはPRAGMAを経由して接続の確立時に適用されるため、既に開かれた接続は設定の更新に従わない |

> **途中で編集保存に失敗した？** `config.toml` を編集している間に一時的な構文エラーが発生した場合、フレームワークは**前回の有効な設定を保持**して診断ログを出力し、各コンポーネントに空の設定をブロードキャストすることはありません（`on_config_update` が空値を受け取って誤ってデフォルトに戻るのを防ぐため）。

### ホットアップデートの内部処理の分解

「設定を変更した、各コンポーネントはどのように知るのか？」——背後には検出→再読み込み→ブロードキャストの処理が存在します：

```mermaid
flowchart TD
    A["外部で config.toml を編集"] --> B{"誰が最初に発見する？"}
    B -->|"バックグラウンドの watcher スレッド<br/>5秒ごとに mtime をループチェック"| C["_check_file_change で変更を判定"]
    B -->|"設定を読み取るとき<br/>キャッシュが60秒以上経過している"| C
    C --> D["_load_config で TOML を再解析"]
    D --> E{"解析に成功する？"}
    E -->|"いいえ（構文エラー）"| F["前回の有効な設定を保持<br/>診断ログを出力してブロードキャストしない"]
    E -->|"はい"| G["lifecycle.emit config.updated<br/>old_config / new_config を含む"]
    G --> H["各コンポーネントのリスナーが反応<br/>（logger / scope / コマンド / GC ...）"]
```

**2つの検出経路**（どちらか1つで十分、両方で兜底）：

| 経路 | メカニズム | 発動タイミング |
|------|------|---------|
| バックグラウンドの watcher | daemonスレッド `config-watcher` が **5秒** `wait` でファイルの `mtime` をループチェック | 外部でファイルを変更した後、最大5秒以内に |
| 慣性検出 | 任意の `getConfig()` 読取時に、キャッシュが **60秒**以上経過している場合、ファイルをチェック | 次回の設定の読み取り時 |

> **フレームワークは自分自身を誤って傷つけない**：`setConfig()` でファイルを書き込む際、フレームワークは「自身が書き込んだ mtime」を記録し、watcher はそれを除外して、**外部の編集**のみを変更とみなします。

**2種類の設定変更イベント**：

| イベント | トリガー | データ | 代表的なシナリオ |
|------|--------|------|---------|
| `config.set` | コード / Dashboard が `setConfig()` を呼び出す | `{key, old_value, new_value}` | 単一キーの書き込み（テンプレート生成、状態記録、実行時の設定変更） |
| `config.updated` | 外部編集後に watcher/慣性検出が検出 | `{old_config, new_config, config_file}` | 手動で `config.toml` を編集 |

> `setConfig()` はデフォルトで**5秒遅延でファイルに書き込み**（複数の書き込みを1度にまとめ）、`immediate=True` で即時書き込み。watcher が外部の変更を検出した後、メモリキャッシュを更新するだけで、**外部の変更をファイルに書き戻すことはない**。

**自動応答側のリスト**（2種類のイベントは通常両方をサブスクライブし、応答内容は一致）：

| コンポーネント | 監視 | 応答 |
|------|------|------|
| Logger | `config.set` + `config.updated` | レベル/ファイル/ディレクトリの分割/メモリ上限/フォーマット/除外レベルを再適用（変更検出付き、変化がなければ動かない） |
| Scope | `config.updated` | スコープバインディングのキャッシュを再構築 |
| コマンドシステム | `config.updated` | プレフィックス/大文字小文字/スペースプレフィックス/must_at_bot の解析パラメータを更新し、次のメッセージで有効 |
| アダプタの並列処理 | `config.set` + `config.updated` | `handler_max_concurrency` は信号量を無効化して再構築 |
| アクティブGC | `config.set` + `config.updated` | `proactive_gc_*` は即時GCバックグラウンドタスクを再起動 |
| アダプタ | `config.updated` にルーティング | 各アダプタの `on_config_update(old, new)` カルバック |
| モジュール | `config.updated` にルーティング | 各モジュールの `on_config_update(old, new)` カルバック |
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
# users には2種類の書き方が選べます（どちらか1つ）：
#   全てのプラットフォームに適用されるグローバルマスター：users = ["123456", "789012"]
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
log_files = []                # 明示的なログファイルのリスト（log_dirと互換性があり、優先度が高い）
log_dir = ""                  # ログ出力ディレクトリ（設定すると自動的に分割ローテーションされる）
log_rotation = "size"         # 分割方法: "size" / "date" / "none"
log_max_size_mb = 10          # sizeモードの単ファイル上限（MB）
log_backup_count = 5          # 保持する履歴ログファイル数
log_rotation_when = "midnight"  # dateモードのローテーション周期: S/M/H/D/midnight
memory_limit = 1000             # 単一モジュールのメモリログの条数上限（0 = メモリログのコピーを無効化）
total_memory_limit = 5000       # 全てのモジュールのメモリログの総条数上限（0 = 無制限）
exclude_levels = ["EVENT"]
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| level | string | INFO | ログレベル: TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACEが最低レベルで、フレームワーク内部の詳細なデバッグ情報を出力） |
| format | string | rich | ログ出力形式: `rich`（デフォルト、カラー付き）、`plain`（カラーなしの純文本、ログ収集/パイプラインリダイレクトに適している）、`json`（JSON形式、ELKなどに適している） |
| log_files | array | 空 | ログ出力ファイルのリスト（明示的なパス、分割されない） |
| log_dir | string | 空 | ログ出力ディレクトリ（自動作成）。設定すると、`log_rotation`に従って`erispulse.log`に書き込まれ、`log_files`と互換性があり、`log_files`が優先される） |
| log_rotation | string | size | 分割方法: `size`（サイズで）、`date`（日付で）、`none`（分割しない） |
| log_max_size_mb | float | 10 | sizeモードの単ファイルサイズ上限（MB）、超過すると`.1`/`.2`のバックアップにローテーションされる |
| log_backup_count | integer | 5 | 保持する履歴ログファイル数、古いバックアップは自動的に削除される |
| log_rotation_when | string | midnight | dateモードのローテーション周期: `S`/`M`/`H`/`D`/`midnight`（デフォルトは毎日0時） |
| memory_limit | integer | 1000 | 単一モジュールのメモリに保持するログの条数；`0`はメモリログのコピーを無効化（メモリに書き込まない、既存の記録は保持） |
| total_memory_limit | integer | 5000 | 全てのモジュールのメモリログの総条数上限；`0`は制限なし。超えた場合、ローテーション戦略に従って最も古い記録を削除（最も条数の多いモジュールのキューから優先的に削除）、単一モジュールの`memory_limit`とは独立に有効 |
| exclude_levels | array | 空 | ログレベルを除外する。除外されたログレベルは**完全に破棄**（メモリに書き込まない、ダッシュボードなどのサブスクライバに送信しない、出力しない、ファイルに書き込まない）。ホットアップデートに対応 |

コードで動的に切り替えることもできます：

```python
from ErisPulse.Core import logger

# サイズで分割: 単ファイル10MB、バックアップ5個
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# 日付で分割: 毎日0時にローテーション、バックアップ7個
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]
> `log_dir` および分割関連の設定は ErisPulse **2.8.0+** が必要です。

> **プライバシー保護**：メッセージの送受信内容は **EVENT 等級**（数値 21）で記録されます。`exclude_levels = ["EVENT"]` を設定すると、バックエンド（例：ダッシュボードのログパネル）は各グループ/プライベートチャットのメッセージ内容を見ることができなくなり、他の等級のログには影響しません。

設定ファイル（ホットアップデートに対応）のほか、実行時に同等の機能をコードで切り替えることもできます——`/privacy on|off` などの管理コマンドを作る際に、設定を書く必要はありません：

```python
from ErisPulse import logger

logger.exclude_level("EVENT")        # 実行時にログ等級を除外（exclude_levels設定と同じ意味）
logger.allow_level("EVENT")          # 等級を再許可
logger.list_excluded_levels()        # 現在除外されている等級を確認
logger.set_format("json")            # 出力をJSON形式に変更（format設定キーと同じ効果）
```

> [!NOTE]
> `exclude_levels` のこの機能は ErisPulse **2.8.0+** が必要です。

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
| uninit_timeout | integer | 30 | エレガントシャットダウンの総タイムアウト時間（秒）、これを超えると強制終了。0はタイムアウトを設けない |
| strict_mode | integer | 0 | エンジニアモードのレベル、下記の「エンジニアモード」を参照 |
| handler_max_concurrency | integer | 64 | イベントハンドラの最大並列タスク数、大きくすると処理能力が上がるがメモリ使用量も増える |
| handler_queue_max_pending | integer | 4096 | イベントのバースト時のキューの背圧：1つのプラットフォームの待機中のハンドラタスク数の上限、超過すると新しいイベントのハンドラタスクは直接破棄され、WARNINGが記録される（破棄数はトラブルシューティングで確認できる）；`0`は制限しない |
| offline_bot_expiry | integer | 3600 | オフラインBotの記録の自動期限切れ時間（秒）、0は期限切れしない |
| plugins_dir | string / list | "plugins" | ローカルプラグインのフォルダ（プロジェクトルートからの相対パス）；プラグインの追加/削除/変更はホットリロードのwatcherが自動的に検出する |
| watch_ignore_dirs | list | 内部リスト | ホットリロードのファイル監視で無視するフォルダ名（`.venv`/`.git`/`__pycache__`など）；空のリストは**内部リストを全体置換**し、`[]`はどのフォルダも無視しない |
| watch_include_plugin_dirs | boolean | true | `epsdk run --reload` でプラグインフォルダをプラグインのホットリロードのwatcherに正確に処理させ、全量監視から除外するか |
| event_dedupe | boolean | true | イベントの冪等性重複除去：同じイベントIDの重複投下（接続層の再送/ゲートウェイの再送）は1回だけ配信される |
| cross_account_policy | string | "off" | 跨アカウントの重複受理ポリシー：同じ物理メッセージが複数アカウント経由で到達した際の処理——`off`は無関係（イベントは通常通り個別に配信、デフォルト）；`mark`は副本来源の`multi_receipt`フィールドに最初の受理イベントを注入して通常通り配信し、モジュールはそのフィールドを読んで裁決する；`drop`は副本来源を配信入口で直接破棄（フレームワーク層で重複除去、モジュールは無感覚）。メンションの対象が自身のアカウント（`user_id` / `account_id`）にヒットする副本来源は除外（メンション優待）；ポリシーはホットアップデートに対応し、変更は即座に有効 |
| session_accounts | table | {} | セッションアカウントのバインディング：`{"プラットフォーム名": {"セッションID": "アカウントbot_id"}}`、セッションを特定のアカウントにバインドし、そのアカウントのみが配信される、他のアカウントの副本来源は破棄される（`cross_account_policy`とは別に有効、設定即有効；メンション優待は保持）；リアルタイムで設定を読み取り、ホットアップデートで有効 |

### アクティブGC設定

SDKの初期化後にアクティブGCバックグラウンドタスクを起動し、周期的にPythonのGCと内部リソースの回収（オフラインBotのクリーンアップなど）を実行します。すべてのパラメータはホットアップデートに対応し、変更時にタスクを即座に再起動します。

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | 回収間隔（秒）、小数もサポート。0はアクティブGCを無効化 |
| proactive_gc_generation | integer | 0 | 通常のラウンドのGC世代（0/1/2、0..2に制限）。注意 `gc.collect(2)` は全量GCに相当し、デフォルトは0で軽量に保つ；深いGCは `proactive_gc_full_every` で周期的に実行 |
| proactive_gc_full_every | integer | 20 | Nラウンドごとに全量GCを実行、0は周期的な全量GCを無効化。全量GCは `proactive_gc_memory_growth_mb` のしきい値に制約される |
| proactive_gc_memory_growth_mb | integer | 32 | 全量GCのメモリ増加しきい値（MB）：前回の全量GC後のメモリベースライン（優先 tracemalloc、次に RSS）と比較し、この値に達した場合に全量GCを実行。0はしきい値を設けない |
| proactive_gc_idle_only | boolean | false | 有効にすると、イベントバースト（未完了のpending handlerがある）の場合は、このラウンドはPython GCを飛ばし、メッセージ処理との競合を避ける；内部リソースの回収は影響を受けない |
| proactive_gc_gen0_min | integer | 500 | 通常のラウンドでGCを実行するgen0のガベージ量の下限：`gc.get_count()[0]`がこの値を下回ると、空のラウンドは無駄なオーバーヘッドがなく飛ばす。0は常にGCを実行 |

> **2.7.1の変更**：デフォルトの `proactive_gc_generation` は `2` から `0` に調整され、`proactive_gc_full_every` は `0` から `20` に調整されました。以前は `generation=2` で毎ラウンド最も重い全量GCを実行していましたが、新しいデフォルトでは回収カバレッジを維持しつつ、空のラウンドのオーバーヘッドを大幅に低減します。明示的に設定された旧値は文字通りの意味で有効です。

### エンジニアモード

エンジニアモードは、モジュール/アダプターのロード段階で不正な設定や失敗した場合の処理戦略を制御します。モダンなモジュール/アダプターはすべて対応する基底クラス（`BaseModule`/`BaseAdapter`）を継承するべきです。基底クラスを継承していないコンポーネントは、フレームワークのコンテキストシステムと兜底クリーンアップに影響を与え、リソースリークを引き起こす可能性があります。

> **2.5.2の変更**：デフォルトレベルは `1`（スキップ）から `0`（緩和）に調整され、新規ユーザーが初めて使用する際のロード問題を減らしました。基底クラスを継承していないコンポーネントは警告として提示され、ロードされます。以前の動作を復元するには、`strict_mode = 1` を明示的に設定してください。

| レベル | 名称 | 動作 |
|------|------|------|
| 0 | 緩和（デフォルト） | 不正な設定は警告のみ、基底クラスを継承していないコンポーネントもロードされます（旧コンポーネントとの互換性） |
| 1 | エンジニア-スキップ | 基底クラスを継承していないコンポーネントは拒否してスキップし、他のものは正常に起動します |
| 2 | エンジニア-致命 | すべての不正な設定を収集して一括で報告し、起動チェックポイントで起動を中止します |

各レベルで、ロード/登録/初期化段階でエラーが発生したコンポーネント自身のクラッシュは常にスキップされます。違いは以下の通りです：

- **0 → 1**：唯一の動作変化は「基底クラスを継承していない」が「ロードされる」から「スキップされる」になることです。
- **1 → 2**：すべての不正な設定（基底クラスを継承していない、ロード失敗、登録失敗、初期化失敗など）が致命的になり、起動チェックポイントで一括して不正なリストを出力して起動を中止します。

#### 例外リスト

特定のコンポーネントが一時的に移行できない（たとえば、依存する古いモジュールなど）場合、例外リストに追加することで、不正な設定でも緩和モードでロードされます：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> あるコンポーネントがエンジニアモードで拒否された場合、ログには再びロードする方法（例外リストに追加するか、レベルを下げること）が明確に提示されます。

#### CLIとの連動

`epsdk run` の起動前の自己検証（設定ファイルの解析性、コンポーネントの必須設定の完全性）はデフォルトで本設定に従います：非0の場合は検証失敗で起動を拒否し、0の場合は警告を出して継続します。設定を変更せずに一時的に切り替えることもできます：`epsdk run --strict` は今回の検証とエンジニアモードを同時に有効にします（レベルは下げず、`ERISPULSE_FRAMEWORK_STRICT_MODE` 環境変数を通じて実行プロセスに伝導されます）、`--no-strict` は一時的に緩和モードに設定し、警告のみになります。

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