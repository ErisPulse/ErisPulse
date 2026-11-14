# 設定ファイルの説明

> [!NOTE]
> **L1 コア必読**——トップページ「読むべき道筋」の5つのコアドキュメントの1つ、モジュール開発に必須。

> 本ドキュメントでは、フレームワーク自身の設定ファイル `config/config.toml` について説明します：各設定セクションの役割、どの設定がホット更新をサポートしているか、環境変数でどのように上書きできるか。サードパーティのモジュールの設定項目は、各モジュールの独自ドキュメントを参照してください。

ErisPulseは、`config/config.toml`というTOML形式の設定ファイルを使用して、プロジェクトの設定を管理します。

## 設定ファイルの位置

設定ファイルはプロジェクトのルートディレクトリの `config/` フォルダ内にあります：

```
project/
├── config/
│   └── config.toml
├── main.py
```

### 複数インスタンスの注意点とロックファイル

フレームワークの起動時に、プロジェクトルートの実行状態ディレクトリ **`.erispulse/`** 内に `config.lock` ロックファイルを作成し、プロセス終了まで保持します（複数インスタンスが同じ設定ディレクトリを共有しているかを検出するため；2.10以前は `config/` ディレクトリの `.erispulse_config.lock` が、アップグレード後に最初の起動時に自動的に削除されます）。ログに「設定ファイルが他のErisPulseインスタンスによって同時に使用されている可能性がある」という警告が出力された場合、**2つ以上のErisPulseプロセスが同じ設定ファイルを書き込んでいる**ことになります（典型的なケース：複数のコンテナが同じホストマシンの `config/` ディレクトリをマウントしている）——同時書き込みは互いに上書きするため、各インスタンスに独立した設定ディレクトリを使用してください。

### 敏感な設定はバージョン管理に含めない

設定ファイルにはトークン（token / API key）などの機密情報が含まれます：フレームワークの初期化と `epsdk init` は、`config/` ディレクトリに `.gitignore` を自動生成します（内容は一行だけ `*` —— **ディレクトリ内のすべてのファイルがバージョン管理対象外になり、無視するファイル自身も除外されます**）；既存の `.gitignore` は上書きされません。`.erispulse/` 実行状態ディレクトリ（インスタンスロック、CLI実行状態ファイル）もローカルマシンの状態に属し、プロジェクトテンプレートの `.gitignore` は既定で無視されています。

## 設定読み込みエラー処理

フレームワークは `config.toml` を読み込む際に、3つのエラー状態を区別し、**操作可能な診断情報を提供**します。静かにデフォルト設定に回帰するのではなく、警告を出力します。

| エラー状態 | 触発条件 | フレームワークの動作 |
|---------|---------|---------|
| ファイルが存在しない | `config.toml` が存在しない | 正常な初回起動、静かに空の設定を使用（警告を出力しない） |
| TOML構文エラー | ファイルは存在するが形式が無効（例：引用符が欠けている、括弧が閉じられていない） | **行番号/列番号と原因**を出力し、**前回の有効な設定を保持して実行を継続**（今回のファイルの変更は有効にならない） |
| 権限/その他のエラー | 読み込み権限がない、IOエラーなど | **明確な原因**を出力し、**前回の有効な設定を保持して実行を継続** |

> **「前回の有効な設定」はデフォルト設定とは異なる**：ファイルが破損した場合、フレームワークは**今回の起動前の最後に解析成功した設定**（実行中にホット更新でファイルを破損させた場合は、旧値を保持）を使用します。故障の対処では、設定がリセットされたと仮定しないでください。

たとえば、`port = 8000`（引用符のない文字列）のように設定を誤って書いた場合、ログは次のように出力されます：

```
[ERROR] [Config] 設定ファイル config/config.toml の構文エラー（第 3 行 第 1 列）: ...
[WARNING] [Config] 設定ファイルの読み込みに失敗しました。前回の有効な設定を使用して実行を継続します。今回のファイルの変更は有効になりません——修復後、再読み込みまたは再起動してください。
```

このように、**デフォルトのINFOレベル**で即座に問題を特定できます。なぜ設定の変更が有効にならないのか困惑する必要はありません。

> **実行中に設定ファイルを破損させた？** ロボットが実行中に `config.toml` を手動編集して構文エラーを導入した場合、フレームワークは次回の書き込み（設定のマージ）時に「設定ファイルが破損しました（構文エラー、第 X 行）、マージ書き込みができない——まず設定ファイルを修復して再起動してください」と出力します。混乱する「書き込み失敗」ではなく、待機中の設定項目は保持され、失われることはありません。

## コメントの保持と最小限の書き込み

config.tomlの**コメントとキーの順序は、フレームワークが書き込んだ後も完全に保持されます**：コード `setConfig()`、CLI設定ウィザードの保存、またはアダプタ/モジュールの初期設定テンプレートの生成など、フレームワークは対象のキーのみを変更します。あなたが書いたコメントや整理された順序は、抹消や再配置されることはありません（tomlclassの無損TOMLエンジンを使用、未触れた内容はバイト単位で保証、ファイルの元のCRLF/LF改行スタイルも変更されません）。

フレームワークは書き込み内容を最小限に抑えます：

- **フレームワークのデフォルト設定は自動的に書き込まれない**：`gc`、`scope`、`transcript`などの組み込みデフォルト値はメモリに駐留し、config.tomlには明示的に設定したキーのみが含まれ、最小化されます。完全な設定項目はプロジェクト内の `config/config.full.example` を参照し、必要に応じてconfig.tomlにコピーして変更してください（設定されていない項目は一律組み込みデフォルト値を使用し、動作は変化しません）
- **`config.full.example` の自動維持**：`epsdk init` を実行したかどうかにかかわらず、フレームワークを起動する（`epsdk run` / `main.py`）と、`config/config.full.example` が欠落している場合、自動的に完全な設定参照が生成されます；ファイルの先頭行にはフレームワークが維持するマークが付いており、生成器の内容が更新（新しい設定項目、新規インストールのコンポーネントなど）された場合、起動時に1回更新されます；先頭行を削除/変更すると、手動で管理し、フレームワークは上書きしません
- **アダプタ/モジュールの設定テンプレート**：初期化時にコメント付きのテンプレートが書き込まれます（フィールドの説明がコメントとして記述されます）；`example` というマークが付いたフィールドは書き込まれず、config.full.example に記録され、参照用です
- **宣言的なコメントの読み込み**：設定ファイル内のコメントはドキュメントそのもの——`ep doctor` と設定検証の失敗通知は、ファイル内の該当フィールドのコメント原文を参照します（コメントを手動で変更した場合でも、通知はファイルの現状に従います）。エラーが出たときに、ドキュメントを再読む必要はありません

## 環境変数による上書き

フレームワークは、`ErisPulse.*` 設定項目を**環境変数で上書き**することをサポートしています（Docker / コンテナ化 / CI 部署に適しています、`config.toml` を変更する必要はありません）。

命名規則：点区切りパス `ErisPulse.<section>.<key>` を大文字にし、`.` を `_` に置換し、`ERISPULSE_` を接頭語として付けます：

| 設定項目 | 環境変数 | 例値 |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `2` |

動作の説明：

- **優先度が最も高い**：環境変数は「設定ファイル」および「デフォルト値」を上書きし、元の値の型に応じて自動変換（`bool` / `int` / `float` / カンマ区切りの `list` / 文字列）
- **永続化されない**：上書きは実行中にのみ有効であり、`config.toml` には書き込まれない
- **ホット更新がサポートされている**：実行中に環境変数を変更した後、設定監視の再読み込みと組み合わせて有効になります

```bash
# Docker 部署の例：config.tomlを変更せず、直接ポートを上書き
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> 注：`ErisPulse.server.port` などのフレームワーク設定は `get_server_config()` などのAPIで読み取られ、環境変数の上書きの影響を受けます。

### モジュール設定の環境変数バインディング（2.9.0+）

モジュール自身の宣言的設定（`ConfigClass`）は、フィールドレベルの環境変数バインディングをサポートしています——`field(metadata=...)` で `env` を宣言します：

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

- **優先度**：環境変数 > `config.toml` > 宣言デフォルト値（設定ファイルのホット更新後もこの優先度が維持される）
- **型変換**：環境変数の値はフィールドの注釈に応じて自動変換される——`str` はそのまま、`int` / `float` / `bool`（`true` / `1` / `yes` / `on`）は自動変換、`list` / `dict` はJSON解析を行う；変換に失敗した場合は、その上書きは無視され（設定ファイル/デフォルト値に戻り）、警告が出力される
- **宣言1か所、どこでも有効**：設定の読み取り、ホット更新、検証は同じパイプラインを使用する；設定パネルのSchemaは `env` 名を示し、`config.toml` テンプレートのコメントも利用可能な環境変数を示す（テンプレートには環境変数の実際の値は書き込まれず、漏洩を防ぐ）
- **完全な互換性**：`env` を宣言していないフィールドは動作が変わらない；フレームワークの設定パイプラインを経ないConfigClassの直接インスタンス化は環境変数の影響を受けない

```bash
# Docker 部署の例：config.tomlを変更せず、モジュールのキーを直接注入
MYMODULE_API_KEY=sk-xxx docker compose up -d
```

> **設定クラス vs モデルフィールド、どちらを使うか？** 設定クラスは「モジュールがどのように動作するか」（動作パラメータ、ホット更新）を管理し、ORMの `Field()` は「ユーザーがどのようなデータを生成したか」（データベーステーブル、クエリ）を管理する。両者は同一の制約語彙と検証エンジンを使用している；対照表は[データモデル層 · どちらの宣言を使うか](../developer-guide/orm.md#どちらの宣言を使うか)を参照してください。

## 設定のホット更新

2.7.0から、フレームワークは設定のホット更新を**体系的にサポート**するようになりました。外部から `config.toml` を変更した後（バックグラウンドのwatcherが5秒ごとにチェック）、またはコードで `setConfig()` を呼び出した後、各コンポーネントは自動的に応答します：

| コンポーネント | ホット更新がサポートされている設定 | 動作 |
|------|----------------|------|
| **ログ Logger** | `logger.level` / `log_files` / `log_dir`（セグメントパラメータを含む）/ `memory_limit` / `format` / `exclude_levels` | 変更検出付きで自動的に再適用 |
| **コマンドシステム CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | 次のメッセージで即時有効 |
| **アダプタの並列処理** | `framework.handler_max_concurrency` | キャッシュシグナルを無効化し、新値で再構築 |
| **アクティブGC** | `framework.proactive_gc_*` | 設定変更で即時GCタスクを再起動し、実行時調整/無効化/再有効化が可能 |
| **マスターシステム Master** | `master.users` | `is_master()` 検査は毎回リアルタイムで読み取り、再起動不要 |
| **モジュール/アダプタ設定** | 各々の設定項目 | `on_config_update(old, new)` コールバックをトリガー |

**再起動が必要な設定**（安全にホット切り替えできない、変更時に「プロセスを再起動後に有効」という警告が出力される）：

| 設定 | 理由 |
|------|------|
| `router.cors.*` / `router.security.*` | 中間件はサービス起動時にFastAPIに書き込まれ、実行時に安全にホット切り替えできない |
| `storage.use_global_db` | SQLiteのファイルハンドルは実行時に開かれているため、パスの切り替えは安全ではない |

> **途中で編集保存に失敗した？** `config.toml` の編集時に一時的な構文エラーが発生した場合、フレームワークは**前回の有効な設定を保持**し、診断ログを出力します。各コンポーネントに空の設定をブロードキャストして（`on_config_update` が空値を受けて誤ってデフォルトに戻るのを防ぐ）`config.toml` の変更が有効にならないようにします。

### ホット更新の内部プロセスの分解

「設定を変更した、各コンポーネントはどのように知るのか？」——背後には検出 → 再読み込み → ブロードキャストのプロセスがあります：

```mermaid
flowchart TD
    A["外部から config.toml を編集"] --> B{"誰が最初に気づく？"}
    B -->|"バックグラウンドのwatcherスレッド<br/>5秒ごとにmtimeをポーリングする"| C["_check_file_change で変更を判定"]
    B -->|"コードで設定を読み取るとき<br/>キャッシュが60秒以上経過している"| C
    C --> D["_load_config でTOMLを再解析"]
    D --> E{"解析に成功した？"}
    E -->|"失敗（構文エラー）"| F["前回の有効な設定を保持<br/>ブロードキャストは行わず、診断ログを出力"]
    E -->|"成功"| G["lifecycle.emit config.updated<br/>old_config / new_config を含む"]
    G --> H["各コンポーネントのリスナーが応答<br/>（logger / scope / コマンド / GC ...）"]
```

**2つの検出経路**（どちらか1つで十分、両方でバックアップ）：

| 経路 | 機制 | 触発タイミング |
|------|------|---------|
| バックグラウンドのwatcher | daemonスレッド `config-watcher` が**5秒**ごとに `wait` でファイルの `mtime` をポーリング | 外部でファイルを編集した後、最大5秒以内に |
| 慣性検出 | 任意の `getConfig()` が読み取るとき、キャッシュが**60秒**以上経過している場合はまずファイルをチェック | 次回の設定読み取り時 |

> **フレームワークは自分自身を誤って傷つけない**：`setConfig()` でファイルを書き込むときは、自身が書き込んだ `mtime` を記録し、watcher はそれを除外して、**外部の編集**のみを変更とみなします。

**2種類の設定変更イベント**：

| イベント | トリガー | データ | 代表的なシーン |
|------|--------|------|---------|
| `config.set` | コード / Dashboard が `setConfig()` を呼び出す | `{key, old_value, new_value}` | 単一キーの書き込み（テンプレート生成、状態記録、実行時の設定変更） |
| `config.updated` | 外部編集後のwatcher/慣性検出が検出 | `{old_config, new_config, config_file}` | 手動で `config.toml` を編集した場合 |

> `setConfig()` はデフォルトで**5秒遅延してファイルに書き込む**（複数の書き込みを1回にまとめる）；`immediate=True` で即時書き込み。watcher が外部の変更を検出した後は、メモリのキャッシュを更新するだけで、**外部の変更をファイルに書き戻すことはしない**。

**自動応答するコンポーネント一覧**（2つのイベントは通常両方をサブスクライブし、応答内容は同じ）：

| コンポーネント | 監視 | 応答 |
|------|------|------|
| Logger | `config.set` + `config.updated` | レベル/ファイル/ディレクトリセグメント/メモリ上限/フォーマット/除外レベルを再適用（変更検出付き、変更がない場合は動かない） |
| Scope | `config.updated` | スコープバインディングのキャッシュを再構築 |
| コマンドシステム | `config.updated` | プレフィックス/大文字小文字/スペースプレフィックス/must_at_bot のパラメータを再解析し、次のメッセージで有効 |
| アダプタの並列処理 | `config.set` + `config.updated` | `handler_max_concurrency` でシグナルを無効化し、再構築 |
| アクティブGC | `config.set` + `config.updated` | `proactive_gc_*` でGCバックグラウンドタスクを即時再起動 |
| アダプタ | `config.updated` にルーティング | 各アダプタの `on_config_update(old, new)` コールバック |
| モジュール | `config.updated` にルーティング | 各モジュールの `on_config_update(old, new)` コールバック |
| ストレージ | `config.updated` | `use_global_db` の変更は**警告のみ**（再起動が必要） |
| ルーター | `config.updated` | `cors.*` / `security.*` の変更は**警告のみ**（再起動が必要） |

## 設定の読み取りと削除API

### getAllConfig：全量設定のスナップショット

外部から `_cache` を直接読み取るのを避ける（外部からプライベート属性を読み取るのはバージョン互換性の保護を受けない）：

```python
config = sdk.config.getAllConfig()     # 深いコピーのスナップショット、原地変更してもフレームワークの状態に影響しない
config["ErisPulse"]["server"]["port"]
```

ビューの口径は `getConfig` と同じ：`setConfig` / `delete` による遅延書き込みも反映され、ファイルの内容と厳密に一致する。

### delConfig：設定キーの削除

`setConfig(key, None)` は値を空にするだけで、キーはファイルに残る；`delConfig` はキーをファイルから**削除**する：

```python
sdk.config.delConfig("ErisPulse.modules.status.OldModule")            # 遅延書き込み
sdk.config.delConfig("OneBot.deprecated_key", immediate=True)         # 即時書き込み
```

- ドット区切りパスをサポート；キーが存在しない場合は `False` を返す
- 書き込みはコメント保持の経路を使用、ファイルの他の内容と順序は影響を受けない
- `config.set` イベントのブロードキャストを再利用（`new_value=None`）：アダプタ / モジュールの `on_config_update` などの既存のリスナーは変更なしで削除を感知できる

## 完全な設定例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.master]
# users は2種類の書式が使用可能（どちらか1つを選択）
#   全局のマスター（すべてのプラットフォームに効果）：users = ["123456", "789012"]
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
# コンテナ / ファイルがマウントされていない環境では、内包PEMの内容を使用（ssl_certfile/keyfileのパスよりも優先）
# ssl_cert = """-----BEGIN CERTIFICATE-----
# ...
# -----END CERTIFICATE-----"""
# ssl_key = """-----BEGIN PRIVATE KEY-----
# ...
# -----END PRIVATE KEY-----"""
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 監聴するアドレス、0.0.0.0はすべてのインターフェースを意味する |
| port | integer | 8000 | 監聴するポート番号 |
| auto_start | boolean | true | sdk.init()の際に自動的にルーティングサーバーを起動するかどうか。falseに設定するとルーティングサーバーの起動をスキップ（純粋なイベント処理/WebUIなしの状況） |
| ssl_certfile | string | 空 | SSL証明書ファイルのパス |
| ssl_keyfile | string | 空 | SSL秘密鍵ファイルのパス |
| ssl_cert | string | 空 | **内包PEM証明書の内容**（パスではない）。ssl_keyとペアで使用する場合、ssl_certfile/ssl_keyfileのパスよりも優先される。フレームワークはSSLコンテキストを構築するために一時的にファイルを落として、すぐに削除する |
| ssl_key | string | 空 | **内包PEM秘密鍵の内容**（パスではない）、上記と同じ意味 |

> **ポートの占有は致命的なエラーではない**：起動時にportが既に占有されていることが検出された場合、フレームワークはルーティングサーバーの起動をスキップして警告を出力し、**アダプタとモジュールは照常動作する**（HTTP/WS/SSEルーティングとWebUIは利用できない）。ロボットは動くがWebUIが開かないという問題を解決する際には、まずポートを確認すること。

## マスターシステム設定

マスターシステムは「フレームワークマスター」アカウント（Bot管理者）を識別するために使用します。`master.users` は3種類の書式をサポートしています：

```toml
[ErisPulse.master]
# 書式1：全プラットフォームに効果するグローバルマスター（後で追加されるプラットフォームも含む）
users = ["123456", "789012"]

# 書式2：プラットフォームごとにマスターを指定（dict）
# users = { yunhu = ["123456"], telegram = ["789012"] }

# 書式3：グローバルマスターとプラットフォーム専用マスターを共存させる——dict中のglobalキーがグローバルマスターバケツ
# users = { global = ["123456"], yunhu = ["789012"] }
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| users | array / object | 空 | マスターのアカウントリスト。list形式は全プラットフォームに効果するグローバルマスター；dict形式はプラットフォームごとに指定（キーがプラットフォーム名、globalキーがグローバルマスターバケツ）、値は該当プラットフォームのマスターのアカウントリスト |

> **新プラットフォームについて**：list形式とdict中のglobalバケツは「定義1回、全プラットフォームに効果」であり、後で新プラットフォームを接続する必要がない；プラットフォーム専用の条目は、同名（含む前綴/通配符寛容一致）のプラットフォームにのみ効果する。master.add(None, uid)の永続化時にglobalバケツに書き込まれ、既存のプラットフォームの条目には影響しない。

コードでは `master.is_master(event)` または `master.is_master(platform, user_id)` でチェックし、毎回呼び出し時にリアルタイムで設定を読み取る（ホット更新に対応し、再起動不要）：

```python
from ErisPulse.Core import master

if master.is_master(event):
    await event.reply("マスター、こんにちは")
```

### 判定チェーンと実行時追加削除

マスター判定チェーンは**設定マスター → 実行時記録 → providerチェーン**です：

```python
from ErisPulse.Core import master

master.is_master(event)                      # イベントから判定
master.is_master("yunhu", "123")             # 明示的に判定
master.add("yunhu", "123")                   # 実行時に追加（デフォルトは永続化；persist=Falseはメモリのみ）
master.remove("yunhu", "123")                # 削除（デフォルトは永続化）
master.list()                                # 総合：{"global": [...], "<platform>": [...]}
```

### 自定義アイデンティティソース（provider）

設定の他に、独自のアイデンティティソースを登録できます：`fn(platform, user_id) -> bool`、
組み込みアイデンティティソース（設定 + 実行時記録）がヒットしなかった場合、順次試行し、いずれかのproviderが許可すればマスターと判定されます。
アダプタの管理者インターフェース、データベースの役割など外部アイデンティティシステムと接続するのに適しています。

登録エントリ `master.provider` はデコレータ / 関数式の2種類の書き方ができ、
登録解除は登録された関数の上の `fn.unregister()` を通じて行います：

```python
from ErisPulse.Core import master

# 書き方1：デコレータ（常駐アイデンティティソース、推奨）
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # 自定義判定ロジック

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # 不要になったら登録解除

# 書き方2：関数式（モジュールロード期に登録 / アンロード期に登録解除）
fn = master.provider(admin_provider)
fn.unregister()
```

> providerの例外はキャッチされてスキップされ、アイデンティティ判定チェーンをブロックしません。
> インスタンスメソッドをバインドした関数は `unregister` が付与できないため、登録/登録解除のペアが必要な場面では**モジュールレベルの関数**を使用してください。

### ユーザー優先：マスターの有効範囲はユーザーが最終決定

コマンドの `master=True` は**開発者のデフォルト**です：ユーザーは
`ErisPulse.event.overrides.command.<module>.<cmd>.master = true/false`
で絞り込みや緩和を上書きできます（[統一イベントオーバーライド設定](#統一イベントオーバーライド設定eventoverrides)を参照、ユーザーの明示的な設定が有効）。

## ログ設定

```toml
[ErisPulse.logger]
level = "INFO"
log_files = []                # 明示的なログファイルリスト（log_dirと互換性あり、優先度が高い）
log_dir = ""                  # ログ出力ディレクトリ（設定すると自動的にセグメントローテーション）
log_rotation = "size"         # セグメント方法: "size" / "date" / "none"
log_max_size_mb = 10          # sizeモードの単ファイル上限（MB）
log_backup_count = 5          # 保持する履歴ログファイル数
log_rotation_when = "midnight"  # dateモードのローテーション周期: S/M/H/D/midnight
memory_limit = 1000             # 単一モジュールのメモリログ条数上限（0 = メモリログコピーを無効化）
total_memory_limit = 5000       # 全てのモジュールのメモリログ総条数上限（0 = 制限なし）。超えた場合、ローテーション戦略に従って最も古い記録を削除（最も条数が多いモジュールのキューから優先的に削除）、単一モジュールのmemory_limitとは独立して有効）
exclude_levels = ["EVENT"]
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| level | string | INFO | ログレベル：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACE が最低レベル、フレームワーク内部の詳細なデバッグ情報を出力） |
| format | string | rich | ログ出力フォーマット：`rich`（カラー、デフォルト）、`plain`（カラーなしの純文本、ログ収集/パイプライン再転送に適している）、`json`（JSON形式、ELKなどに適している） |
| log_files | array | 空 | ログ出力ファイルのリスト（明示的なパス、セグメントしない） |
| log_dir | string | 空 | ログ出力ディレクトリ（自動作成）。設定すると、ディレクトリ内に `erispulse.log` を書き込み、`log_rotation` に従って自動的にセグメントする；`log_files` と互換性があり、`log_files` が優先される |
| log_rotation | string | size | セグメント方法：`size`（サイズで）、`date`（日付で）、`none`（セグメントしない） |
| log_max_size_mb | float | 10 | sizeモードの単ファイルサイズ上限（MB）、超過後は `.1`/`.2` にバックアップ |
| log_backup_count | integer | 5 | 保持する履歴ログファイル数、超えた古いバックアップは自動的に削除される |
| log_rotation_when | string | midnight | dateモードのローテーション周期：`S`/`M`/`H`/`D`/`midnight`（デフォルトは毎日0時） |
| memory_limit | integer | 1000 | 単一モジュールにメモリに保持するログ条数；`0` はメモリログコピーを無効化（メモリに書き込まない、既存の記録は保持される） |
| total_memory_limit | integer | 5000 | 全てのモジュールのメモリログ総条数上限；`0` は制限なし。超えた場合、ローテーション戦略に従って最も古い記録を削除（最も条数が多いモジュールのキューから優先的に削除）、単一モジュールの `memory_limit` とは独立して有効） |
| exclude_levels | array | 空 | ログレベルを無視する。無視されたログレベルは**完全に破棄**（メモリに書き込まない、ダッシュボードなどのサブスクライバーに送信しない、出力しない、ファイルに書き込まない）。ホット更新が可能 |

また、コードで動的に切り替えることも可能です：

```python
from ErisPulse.Core import logger

# サイズでセグメント：1ファイル10MB、5個保持
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# 日付でセグメント：毎日0時ローテーション、7個保持
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]
> `log_dir` とセグメント関連の設定は ErisPulse **2.8.0+** が必要です。

> **プライバシー保護**：メッセージの送受信内容は **EVENT** レベル（数値 21）で記録されます。`exclude_levels = ["EVENT"]` に設定することで、バックエンド（ダッシュボードのログパネル）が各グループ/プライベートチャットのメッセージ内容を見ることができなくなり、他のログレベルには影響しません。

設定ファイル（ホット更新が可能）だけでなく、実行時にコードで同等の機能を切り替えることもできます——`/privacy on|off` などの管理コマンドを作る必要はありません：

```python
from ErisPulse import logger

logger.exclude_level("EVENT")        # 実行時に特定のログレベルを無視（exclude_levels設定と同じ意味）
logger.allow_level("EVENT")          # そのログレベルを再有効化
logger.list_excluded_levels()        # 現在無視されているログレベルを確認
logger.set_format("json")            # JSON形式の出力に切り替え（format設定と同じ効果）
```

> [!NOTE]
> `exclude_levels` この機能は ErisPulse **2.8.0+** が必要です。

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
| uninit_timeout | integer | 30 | エレガントなシャットダウンの総タイムアウト時間（秒）、これを超えると強制終了。0はタイムアウトを設けない |
| strict_mode | integer | 0 | エスカレーションモードのレベル、下の「エスカレーションモード」を参照 |
| handler_max_concurrency | integer | 64 | イベントハンドラの最大並行タスク数、大きくすると処理能力は上がるがメモリ使用量も増える |
| handler_queue_max_pending | integer | 4096 | イベントのバースト時のキューのバックプレッシャー：1プラットフォームの待機中のハンドラタスク数の上限、超えた場合、新しいイベントのハンドラタスクは直接破棄され、WARNINGを記録する（破棄数はトラブルシューティングで確認可能）；0は上限なし |
| offline_bot_expiry | integer | 3600 | オフラインBotの記録の自動期限切れ時間（秒）、0は期限切れしない |
| plugins_dir | string / list | "plugins" | ローカルプラグインのフォルダ（プロジェクトルートからの相対パス）；プラグインの追加/削除/変更はホットリロードのwatcherによって自動的に検出される |
| watch_ignore_dirs | list | 内部リスト | ホットリロードのファイル監視で無視するディレクトリ名（`.venv`/`.git`/`__pycache__`等）；空リストは**内部リストを全体置換**、`[]`はどのディレクトリも無視しない |
| watch_include_plugin_dirs | boolean | true | `epsdk run --reload` でプラグインのディレクトリをプラグインのホットリロードのwatcherに正確に処理させ、全量監視から除外するかどうか |
| event_dedupe | boolean | true | イベントの冪等性重複除去：同じイベントIDの重複投递（接続層の再送/ゲートウェイの再発）は1回だけ配信される |
| cross_account_policy | string | "off" | 跨アカウントの重複受付ポリシー：同じ物理メッセージが複数のアカウントを通って到達した場合の処理——`off`は無関係（イベントは照常配信）；`mark`は副本来たイベントに`multi_receipt`フィールドを注入して（最初の受付イベントを指す）配信を照常行い、モジュールはそのフィールドを読んで裁決する；`drop`は副本来たイベントを配信の入口で直接破棄（フレームワーク層で重複除去、モジュールは無感覚） |

### アクティブGC設定

SDKの初期化後にアクティブGCバックグラウンドタスクが起動し、周期的にPythonのGCと内部リソースの回収（オフラインBotのクリーンアップなど）を行う。すべてのパラメータはホット更新が可能で、変更時にタスクを即時再起動する。

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | 回収の間隔（秒）、小数点以下も可能。0はアクティブGCを無効化 |
| proactive_gc_generation | integer | 0 | 通常のラウンドのGC世代（0/1/2、0..2に制限）。注意：`gc.collect(2)`は全量GCに相当し、デフォルトは0で軽量に保つ；深いGCは`proactive_gc_full_every`で周期的にトリガーされる |
| proactive_gc_full_every | integer | 20 | Nラウンドごとに全量GCを行う、0は周期的な全量GCを無効化。全量GCは`proactive_gc_memory_growth_mb`のしきい値に制約される |
| proactive_gc_memory_growth_mb | integer | 32 | 全量GCのメモリ増加のしきい値（MB）：前回の全量GC後のメモリベースライン（優先tracemalloc、次にRSS）と比較し、この値に達した場合に全量GCを実行する。0はしきい値を設けない |
| proactive_gc_idle_only | boolean | false | 有効にすると、イベントのバースト（未完了のpending handlerがある）のラウンドではPythonのGCをスキップし、メッセージ処理との競合を避ける；内部リソースの回収には影響しない |
| proactive_gc_gen0_min | integer | 500 | 通常のラウンドのGCのgen0のガベージ量の下限：`gc.get_count()[0]`がこの値より低い場合はスキップ（空のラウンドはほぼゼロコスト）。0は常にGCする |

> **2.7.1 変更**：デフォルトの `proactive_gc_generation` は `2` から `0` に調整され、`proactive_gc_full_every` は `0` から `20` に調整されました。以前は `generation=2` は毎ラウンド最重の全量GCを意味していました；新しいデフォルトはカバーゲージを維持しながら空のラウンドのオーバーヘッドを大幅に低下させます。明示的に設定された以前の値は文字通りの意味で有効です。

### エスカレーションモード

エスカレーションモードは、モジュール/アダプターがロード段階で不正または失敗した場合の処理戦略を制御します。現代のモジュール/アダプターは、それぞれの基底クラス（`BaseModule`/`BaseAdapter`）を継承する必要があります。基底クラスを継承していないコンポーネントは、フレームワークのコンテキストシステムとバックアップクリーンアップに影響を与え、リソースリークを引き起こす可能性があります。

> **2.5.2 変更**：デフォルトのレベルは `1`（スキップ）から `0`（緩和）に調整され、新規ユーザーが初期使用時に遭遇するロード問題を減らしました。基底クラスを継承していないコンポーネントは、警告を出力して試みるだけで、直接拒否されません。旧来の動作を復元するには、`strict_mode = 1` を明示的に設定してください。

| レベル | 名称 | 動作 |
|------|------|------|
| 0 | 緩和（デフォルト） | 不正は警告のみ、基底クラスを継承していないコンポーネントも試みる（旧コンポーネントの互換性） |
| 1 | エスカレーション-スキップ | 基底クラスを継承していないコンポーネントを拒否してスキップし、他の部分は正常に起動する |
| 2 | エスカレーション-致命 | すべての不正を収集して統一的に報告し、起動チェックポイントで一括して中止する |

各レベルで、「ロード/登録/初期化段階でエラーが発生した」コンポーネント自身のクラッシュは常にスキップされます。違いは以下の通りです：

- **0 → 1**：唯一の動作の違いは「基底クラスを継承していない」が「試みる」から「スキップ」になることです。
- **1 → 2**：すべての不正（基底クラスを継承していない、ロード失敗、登録失敗、初期化失敗など）が致命に昇格し、起動チェックポイントで不正リストを集めて一括して中止されます。

#### 例外リスト

いくつかのコンポーネントが一時的に移行できない場合（たとえば、依存する旧モジュールなど）、例外リストに追加することで、不正なコンポーネントでも緩和モードで読み込まれます：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> あるコンポーネントがエスカレーションモードで拒否された場合、ログには再び読み込まれる方法（例外リストに追加するか、レベルを下げること）が明確に提示されます。

#### CLIとの連携

`epsdk run` の起動前の自己検証（設定ファイルの解析性、コンポーネントの必須設定の完全性）はデフォルトでこの設定に従います：0でない場合、検証に失敗すると起動を拒否します。0の場合は警告を出して続行します。設定を変更せずに一時的に切り替えることもできます：`epsdk run --strict` は今回の起動時に自己検証とエスカレーションレベルを同時に有効にします（レベルは上げるだけ、`ERISPULSE_FRAMEWORK_STRICT_MODE` 環境変数で実行プロセスに伝達されます）、`--no-strict` は今回の起動時に緩和モードに設定し、警告のみ出力します。

## ストレージ設定

2.8.0からストレージエンジンは3種類の非同期バックエンドをサポートし、**APIは完全に一致し、設定は1回の切り替えで可能**です：

| バックエンド | ドライバー | インストール | 特徴 |
|------|------|------|------|
| SQLite（デフォルト） | aiosqlite | 開梱即用 | 零設定、単ファイル、WAL並列 |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | 既存のMySQLインフラストラクチャ、多インスタンス共有 |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | トランザクション能力が強く、高並列 |

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
| backend | string | sqlite | ストレージバックエンド：`sqlite` / `mysql` / `postgres`、切り替えでコード変更なし |
| use_global_db | boolean | false | 仅 SQLite：パッケージ内グローバルデータベースを使用するか、プロジェクト独自のデータベースを使用するか |
| storage.mysql.* | table | 上記参照 | MySQL接続パラメータ（host / port / user / password / database / charset / pool） |
| storage.postgres.* | table | 上記参照 | PostgreSQL接続パラメータ（host / port / user / password / database / pool） |

環境変数での上書きもサポート（Docker / 12-factor）：`ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`。

> [!TIP]
> - 接続パラメータを変更した後はフレームワークを再起動して有効にする必要がある；接続プールの作成が瞬時失敗すると指数関数的に再試行する
> - バックエンドを切り替える前に検証スクリプトで自検査を行う：`python tests/devs/test_storage_backend_verify.py --backend mysql`
> - トランザクション / ディアレクトの違い / 自定義バックエンドなど詳細な説明は[ストレージバックエンド](../advanced/storage-backends.md)を参照

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
| case_sensitive | boolean | true | 大文字小文字を区別するか（`/Help` と `/help` が異なるコマンドになるか） |
| allow_space_prefix | boolean | false | スペースをプレフィックスとして許可するか |
| must_at_bot | boolean | false | コマンドをトリガーするには@botが必要か（プライベートチャットは制限されない） |

### メッセージ設定

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| ignore_self | boolean | true | 自身のメッセージを無視するか |

> イベントの重複除去は3層で、各層は1種類の重複を処理：`event_dedupe`（framework、同じイベントIDの重複投递）→ `ignore_self`（本節、自身のメッセージ）→ `cross_account_policy`（framework、多アカウントの内容レベルのコピー）。各層の役割は[アダプターのコアコンセプト](../developer-guide/adapters/core-concepts.md)を参照。

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
| enabled | boolean | true | 自動的に受信/送信メッセージを記録するか（無効にすると書き込みを停止し、履歴は照会可能） |
| max_per_session | int | 50 | 1セッションに保持する条数（0 = このセッションの裁断を無効化） |
| ttl_hours | float | 168.0 | グローバル保持時間（時間、0 = 永久に削除しない） |
| self_echo | string | bot | 受信botエコー（`self.user_id == user_id`、OneBotの`report-self-message`など）の処理：`bot` = botとして記録し`meta.self_echo`をマーク；`skip` = 記録しない；`user` = userとして記録（旧動作） |

> 保持戦略のリスクと監査は[会話受信箱](../advanced/transcript.md)を参照；帰属フィールド（`sender` / `meta`）と送信所属（`meta.module`）も同文書を参照。

## 国際化設定

```toml
[ErisPulse.i18n]
language = "auto"
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| language | string | auto | フレームワークの内部テキストの表示言語。`auto`に設定するとシステム言語を自動検出し、`zh-CN`、`zh-TW`、`en`、`ja`、`ru`などの具体的なコードに設定することもできる |

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

> `setConfig` はデフォルトで遅延書き込み（約5秒毎に一括保存）を使用し、`immediate=True`で即時永続化する。設定の変更は`config.set`ライフサイクルイベントをトリガーする。

## スコープ設定（scope）

> [!NOTE]
> 本特性は ErisPulse **2.8.0+** が必要です。

スコープは「**どの範囲で有効か**」を宣言します——特定のプラットフォーム / Bot / セッション内でどのモジュールが有効か（① モジュール次元）、特定のユーザー / グループ / Bot / アダプターのイベントを受信するか（② アイデンティティ次元）、モジュールがどの出力呼び出しを実行できるか（③ 出力次元）：

```toml
[ErisPulse.scope]
default_allow = true        # グローバルなデフォルト（false = 明示的な拒否の厳格モード；出力次元には影響しない）
cache_size = 1024           # LRUキャッシュサイズ

# ① モジュール次元（優先度：セッション > Bot > プラットフォーム；エントリは正確/glob/正規表現: 正規表現）
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]
blocked = ["re:^Danger"]

# 子レベルのバインディングはmerge = trueの時に低優先度のエントリと逐次並列（デフォルトは全体の上書き）
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true

# ② アイデンティティ次元（優先度：ユーザー > セッション > Bot > アダプター；各レベルはallowまたはdenyのいずれかを記述）
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                 # 該当プラットフォームの全てのイベントをエントリで破棄

[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]         # ユーザーのキーはglob/正規表現: 正規表現をサポート
deny = ["u_bad", "spam_*"]

# ③ 出力次元（デフォルトは全許可；ルールはインラインテーブル、エントリは正確/glob/正規表現: 正規表現をサポート）
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                    # 送信を全禁止
api = { allow = ["get_*"] }               # クエリ系の標準APIのみ許可
request = { deny = true }                 # リクエストの処理を禁止
```

| 設定項目 | 型 | 説明 |
|---------|------|------|
| `scope.default_allow` | boolean | グローバルなデフォルト：モジュール/アイデンティティがルールにヒットしなかった場合の許可/拒否（`true`） |
| `scope.cache_size` | integer | LRUキャッシュサイズ（デフォルト 1024） |
| `scope.platforms / bots / sessions` | table | ① モジュールの3段階バインディング：`{modules=[...], blocked=[...], merge=bool?}` |
| `scope.identity.adapters / bots / sessions / users` | table | ② アイデンティティの4段階バインディング：`{allow=true}` / `{deny=true}` |
| `scope.actions.<module>.<action>` | table | ③ 出力のルール：`{allow=[...], deny=true|[...]}`（actionはsend/api/request） |

> 詳細と実行時API（次元化の`sdk.scope.set_module()` / `set_identity()` / `set_action()`、判定の`is_allowed()` / `is_identity_allowed()` / `is_action_allowed()`、および辞書式のデフォルト`get()` / `set()` / `delete()`）は[スコープ（scope）](../advanced/scope.md)を参照してください。

## 統一イベントオーバーライド設定（event.overrides）

統一オーバーライドシステム：**イベントタイプ**ごとに任意のモジュールハンドラの動作をオーバーライドし、モジュールコードを変更せずに動作を変更します。OneBot12標準タイプ（meta / message / notice / request）と拡張タイプ（command）それぞれに独自のオーバーライド可能なパラメータがあります：

```toml
[ErisPulse.event.overrides]

# message：テキストのトリガ条件（コード内の条件とAND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice / request / meta：detail_typeのホワイトリスト（エントリは正確/glob/正規表現: 正規表現をサポート）
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command（拡張タイプ）：実装パラメータのオーバーライド（ユーザーの優先；無効化はacl denyで）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true               # 仅框架主人（false则放开开发者的主人限制）
hidden = true               # ヘルプリストで非表示
aliases = ["rs"]            # 生效の別名

# acl（command専用）：コマンドのユーザーのホワイトリスト/ブラックリスト（コマンド名はglob/正規表現: 正規表現、正確なキーが優先）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]  # ユーザー識別子 "platform:user_id"
deny = ["onebot11:u_bad"]

# ACLデフォルト：ACLの設定されていないコマンドを許可（true）/厳密に拒否（false）
acl_default_allow = true
```

| 設定項目 | 型 | 説明 |
|---------|------|------|
| `event.overrides.message.<module>` | table | テキスト条件：`{pattern="...", regex="..."}` |
| `event.overrides.notice / request.<module>` | table | `{detail_types=[...], pattern, regex}` |
| `event.overrides.meta.<module>` | table | `{detail_types=[...]}` |
| `event.overrides.command.<module>` | table | モジュールレベルのパラメータオーバーライド（`hidden = true`などのスカラー値） |
| `event.overrides.command.<module>.<command>` | table | コマンドレベルのオーバーライド（コマンドレベルが優先） |
| `event.overrides.acl.<command名>` | table | ユーザーのホワイトリスト/ブラックリスト：`{allow=[...], deny=[...]}` |
| `event.overrides.acl_default_allow` | boolean | ACLデフォルト：ACLが設定されていないコマンドを許可（`true`）/厳密に拒否（`false`） |

> 実行時API（`from ErisPulse.Core.Event import overrides`の後、各タイプのサブ名前空間で`overrides.message.set()` / `overrides.command.set()` / `overrides.acl.set()`などを呼び出し、または`sdk.Event.overrides`でアクセス）は[イベント処理入門・イベントオーバーライド](../getting-started/event-handling.md#イベントオーバーライドモジュールコードを変更せずに任意のイベントタイプの動作をオーバーライド)を参照してください。

## 次に進む

- **L1の道筋に従って**：次のドキュメント[エラーハンドリング](../advanced/errors.md)、フレームワークをクラッシュさせないエラー処理の書き方を学ぶ
- **手動でTOMLを書きたくない**：`epsdk config`のインタラクティブな設定ツールを使用して宣言的な設定項目を入力する、[CLIコマンドリファレンス・config](cli-reference.md#config)を参照
- **設定ファイルを変更したくない**：環境変数で設定項目を上書きし、[デプロイガイド](deployment.md)のDockerの使い方を参照