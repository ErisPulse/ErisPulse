# 設定ファイルの説明

> [!NOTE]
> **L1コア必読** — 首ページの「読むべき経路」にある5つのコアドキュメントの1つで、モジュール開発には必須です。

> このドキュメントは、フレームワーク自身の設定ファイル `config/config.toml` について説明します。各設定セクションの役割、どの設定がホットアップデートをサポートするか、環境変数でどのように上書きできるかについてです。サードパーティモジュールの設定項目については、それぞれのモジュールのドキュメントを参照してください。

ErisPulseは、TOML形式の設定ファイル `config/config.toml` を使ってプロジェクトの設定を管理します。

## 設定ファイルの位置

設定ファイルはプロジェクトのルートディレクトリの `config/` フォルダ内にあります：

```
project/
├── config/
│   └── config.toml
├── main.py
```

### 複数インスタンスの注意点とロックファイル

フレームワークの起動時に、プロジェクトのルートディレクトリの実行状態ディレクトリ **`.erispulse/`** に `config.lock` ロックファイルを作成し、プロセス終了まで保持します（複数インスタンスが同じ設定ディレクトリを共有しているかを検出するため）。2.10以前は `config/` ディレクトリの `.erispulse_config.lock` にあり、アップグレード後に初めて起動すると自動的に削除されます。ログに「設定ファイルが他のErisPulseインスタンスによって同時に使用されている可能性がある」という警告が表示された場合、**2つ以上のErisPulseプロセスが同じ設定ファイルを書き込んでいます**（典型的なシナリオ：複数のコンテナが同じホストマシンの `config/` ディレクトリをマウントしている）— 並行書き込みは互いに上書きするため、各インスタンスに独立した設定ディレクトリを使用してください。

### 敏感な設定はバージョン管理に含めない

設定ファイルにはトークン（token / API key）などの機密情報が含まれています：フレームワークの初期化と `epsdk init` は自動的に `config/` ディレクトリに `.gitignore` を生成します（内容は一行 `*` だけ—**ディレクトリ内のすべてのファイルをバージョン管理から除外し、除外ファイル自身も除外対象になります**）。既存の `.gitignore` は上書きされません。`.erispulse/` 実行状態ディレクトリ（インスタンスロック、CLI実行状態ファイル）はローカルマシンの状態に属し、プロジェクトテンプレートの `.gitignore` は既定で除外されています。

## 設定の読み込みエラーハンドリング

フレームワークは `config.toml` を読み込む際に3つのエラー状態を区別し、**操作可能な診断情報を提供**します。デフォルト設定に静かに回帰するのではなく、警告を出します。

| エラー状態 | 発生条件 | フレームワークの動作 |
|---------|---------|---------|
| ファイルが存在しない | `config.toml` が存在しない | 正常な初回起動で、空の設定を使用（警告を出さない） |
| TOML構文エラー | ファイルは存在するが構文が無効（例：クォートが足りない、括弧が閉じられていない） | **エラー行番号/列番号と原因**を出力し、**前回の有効な設定を保持して実行を継続**（今回のファイルの変更は有効にならない） |
| 権限/その他のエラー | 読み込み権限がない、IOエラーなど | **明確な原因**を出力し、**前回の有効な設定を保持して実行を継続** |

> **「前回の有効な設定」＝デフォルト設定ではない**：ファイルが破損した場合、フレームワークは**今回の起動前の最後に解析された設定**（実行中にホットアップデートでファイルを破損させた場合は旧値を使用）を使用し、すべての設定項目を工場出荷時のデフォルトにリセットするのではなく、故障の対処時に「設定がリセットされた」と仮定しないでください。

たとえば、設定を `port = 8000`（クォートのない文字列）と誤って書いた場合、ログには次のような出力がされます：

```
[ERROR] [Config] 設定ファイル config/config.toml が構文エラー（第 3 行 第 1 列）: ...
[WARNING] [Config] 設定ファイルの読み取りに失敗しました。前回の有効な設定を使用して実行を継続します。今回のファイルの変更は有効になりません。— 修正後、再読み込みまたは再起動してください。
```

これにより、**デフォルトのINFOレベル**で問題を即座に特定でき、「なぜ設定を変更しても効果がないのか」を混乱させることはありません。

> **実行中に設定ファイルを破損させた場合？** ロボットが実行中に `config.toml` を手動編集して構文エラーを導入した場合、次回の書き込み（設定のマージ）時に「設定ファイルが破損しました（構文エラー、第 X 行）、マージ書き込みができない— まず設定ファイルを修正して再起動してください」と出力されます。混乱する「書き込みに失敗しました」ではなく、待機中の設定項目は保持され、失われることはありません。

## コメントの保持と最小限のファイル出力

config.tomlの**コメントとキーの順序は、フレームワークが書き込んだ後も完全に保持されます**：コード `setConfig()`、CLI設定ガイドの保存、またはアダプター/モジュールの初期設定テンプレート生成に関わらず、フレームワークは関連するキーのみを変更し、ユーザーが書いたコメントや整理された順序は消去や再配置されません（tomlclassの無損TOMLエンジンに基づき、未触れた内容はバイト単位で保証され、ファイルの元のCRLF/LF行末スタイルも変更されません）。

フレームワークはファイルへの書き込み内容を最小限に抑えます：

- **フレームワークのデフォルト設定は自動的にファイルに書き込まれません**：`gc`、`scope`、`transcript` などの組み込みデフォルト値はメモリ内に駐留し、config.tomlにはユーザーが明示的に設定したキーのみが含まれ、最小化されます。完全な設定項目はプロジェクト内の `config/config.full.example` を参照し、必要に応じて config.toml にコピーして変更してください（未設定の項目は一律組み込みデフォルト値を使用し、動作は変わりません）
- **`config.full.example` は自動的に維持されます**：`epsdk init` を実行したかどうかに関わらず、フレームワークを起動するたびに（`epsdk run` / `main.py`）、`config/config.full.example` が欠落している場合、自動的に完全な設定参照を生成します。ファイルの先頭行はフレームワークが維持するマークです。生成器の内容が更新された場合（新しい設定項目、新しいコンポーネントの追加など）、起動時に一度更新されます。先頭行を削除または変更すると、手動で管理し、フレームワークは上書きしません
- **アダプターやモジュールの設定テンプレート**：初期化時にコメント付きのテンプレートをファイルに書き込みます（フィールドの説明がコメントになります）。`example` とマークされたフィールドはファイルに書き込まれず、config.full.example に記録され、参考用です
- **宣言的なコメントの再読み込み**：設定ファイル内のコメントはドキュメントそのものです — `ep doctor` と設定の検証エラーの提示は、該当フィールドのファイル中のコメント原文を参照します（ユーザーがコメントを手動で変更しても、エラーメッセージはファイルの現状に従います）。エラーが発生した際は、ドキュメントを再度確認してフィールドの意味を確認する必要はありません

## 環境変数による上書き

フレームワークは環境変数を使って `ErisPulse.*` 設定項目を**上書き**できます（Docker / コンテナ化 / CI 部署に適しています。`config.toml` を変更する必要はありません）。

命名規則：ドット区切りのパス `ErisPulse.<section>.<key>` を全大文字にし、`.` を `_` に置き換え、`ERISPULSE_` を前置します：

| 設定項目 | 環境変数 | 例値 |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `2` |

動作説明：

- **優先度が最も高い**：環境変数は「設定ファイル」および「デフォルト値」を上書きし、元の値の型に応じて自動変換されます（`bool` / `int` / `float` / カンマ区切りの `list` / 文字列）
- **永続化されない**：上書きは実行中のみ有効で、`config.toml` には書き込まれません
- **ホットアップデートがサポートされる**：実行中に環境変数を変更した後、設定監視の再読み込みを組み合わせれば有効になります

```bash
# Docker 部署の例：config.toml を変更せず、直接ポートを上書き
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> 注：`ErisPulse.server.port` などのフレームワーク設定は `get_server_config()` などの API で読み取られ、すべて環境変数の上書きの影響を受けます。

### モジュール設定の環境変数バインディング（2.9.0+）

モジュール独自の宣言的設定（`ConfigClass`）は、フィールドレベルで環境変数バインディングをサポートしています — `field(metadata=...)` で `env` を宣言します：

```python
@dataclass
class MyConfig(BaseConfig):
    api_key: str = field(default="", metadata={
        "description": "API 密钥",
        "env": "MYMODULE_API_KEY",   # 環境変数バインディング
    })
    retries: int = field(default=3, metadata={"env": "MYMODULE_RETRIES"})
```

動作説明：

- **優先度**：環境変数 > `config.toml` > 宣言デフォルト値（設定ファイルのホットアップデート後もこの優先度が維持される）
- **型変換**：環境変数の値はフィールドの注釈に応じて自動変換されます — `str` はそのまま、`int` / `float` / `bool`（`true` / `1` / `yes` / `on`）は自動変換、`list` / `dict` はJSON解析を経ます；変換に失敗した場合は該当の上書きを無視して（設定ファイル/デフォルト値に戻り）警告を出力します
- **宣言1箇所、どこでも有効**：設定の読み取り、ホットアップデート、検証は同じパイプラインを使用します；設定パネルのSchemaには `env` 名が表示され、`config.toml` テンプレートのコメントには利用可能な環境変数が提示されます（テンプレートには環境変数の実際の値は書き込まれず、漏洩を防ぎます）
- **完全に互換性がある**：`env` を宣言していないフィールドの動作は変化しません；フレームワークの設定パイプラインを経ないConfigClassのインスタンス化は環境変数の影響を受けません

```bash
# Docker 部署の例：config.toml を変更せず、モジュールの鍵を直接注入
MYMODULE_API_KEY=sk-xxx docker compose up -d
```

> **設定クラス vs モデルフィールドはどちらを使うか？** 設定クラスは「モジュールがどのように動作するか」（動作パラメータ、ホットアップデート）を管理し、ORMの`Field()`は「ユーザーがどのようなデータを生成したか」（データベーステーブル、クエリ）を管理します。両者は同じ約束事表と検証エンジンを使用しています；対照表は[データモデル層 · どちらの宣言を使うべきか](../developer-guide/orm.md#どちらの宣言を使うべきか)を参照してください。

## 設定のホットアップデート

2.7.0から、フレームワークは設定のホットアップデートを**体系的にサポート**しました。外部から `config.toml` を変更した後（バックグラウンドのwatcherが5秒ごとに検出）、またはコードで `setConfig()` を呼び出した後、各コンポーネントが自動的に応答します：

| コンポーネント | ホットアップデートがサポートされる設定 | 動作 |
|------|----------------|------|
| **ログ Logger** | `logger.level` / `log_files` / `log_dir`（分割パラメータを含む）/ `memory_limit` / `format` / `exclude_levels` | 変更検出付きで自動的に再適用 |
| **コマンドシステム CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | 次のメッセージで即座に有効 |
| **アダプターの並行処理** | `framework.handler_max_concurrency` | 失効したキャッシュシグナルを破棄し、新しい値で再構築 |
| **アクティブGC** | `framework.proactive_gc_*` | 設定変更で即座にGCタスクを再起動し、実行時調整/無効化/再有効化が可能 |
| **マスターシステム Master** | `master.users` | `is_master()` のチェックで毎回リアルタイムに読み取り、再起動不要 |
| **モジュール/アダプターの設定** | 各々の設定項目 | `on_config_update(old, new)` コールバックをトリガー |

**再起動が必要な設定**（安全にホット切り替えできないため、変更時に「プロセスを再起動後に有効」という警告が出力されます）：

| 設定 | 理由 |
|------|------|
| `router.cors.*` / `router.security.*` | ミドルウェアがサービス起動時にFastAPIに書き込まれ、実行時に安全なホット切り替えができない |
| `storage.use_global_db` | SQLiteファイルハンドルが実行時に開かれているため、パスの切り替えは安全ではない |

> **途中で編集保存に失敗した場合？** `config.toml` を編集中に一時的な構文エラーが発生した場合、フレームワークは**前回の有効な設定を保持**して診断ログを出力し、各コンポーネントに空の設定をブロードキャストすることはありません（`on_config_update` が空値を受けて誤ってデフォルトに戻るのを防ぐため）。

### ホットアップデートの内部の流れを分解

「設定を変更した、各コンポーネントはどのように知るのか？」 — 背後には、検出 → 再読み込み → ブロードキャストの流れがあります：

```mermaid
flowchart TD
    A["外部から config.toml を編集"] --> B{"誰が最初に気づく？"}
    B -->|"バックグラウンドのwatcherスレッド<br/>5秒ごとにmtimeをループ検出"| C["_check_file_change で変更を判定"]
    B -->|"コードで設定を読み取るとき<br/>キャッシュが60秒以上経過"| C
    C --> D["_load_config でTOMLを再解析"]
    D --> E{"解析に成功した？"}
    E -->|"いいえ（構文エラー）"| F["前回の有効な設定を保持<br/>ブロードキャストせず、診断ログを出力"]
    E -->|"はい"| G["lifecycle.emit config.updated<br/>old_config / new_config を含む"]
    G --> H["各コンポーネントのリスナーが応答<br/>（logger / scope / コマンド / GC ...）"]
```

**2つの検出経路**（どちらかが機能すれば十分で、両方でバックアップ）：

| 経路 | メカニズム | 発動タイミング |
|------|------|---------|
| バックグラウンドのwatcher | daemonスレッド `config-watcher` が **5秒** ごとに `wait` でファイルの `mtime` をループ検出 | 外部からファイルを変更した後、最大5秒以内に |
| 慣性検出 | `getConfig()` で読み取るとき、キャッシュが **60秒** 以上経過したらまずファイルをチェック | 次回設定を読み取るとき |

> **フレームワークは自分自身を誤って傷つけない**：`setConfig()` でファイルに書き込むときは「自身が書き込んだ mtime」を記録し、watcher はそれを除外して、**外部の編集**だけを変更とみなします。

**2種類の設定変更イベント**：

| イベント | 発生元 | データ | 代表的なシナリオ |
|------|--------|------|---------|
| `config.set` | コード / Dashboard が `setConfig()` を呼び出す | `{key, old_value, new_value}` | 単一キーの書き込み（テンプレート生成、状態記録、実行時設定の変更） |
| `config.updated` | 外部編集後のwatcher/慣性検出が捕捉する | `{old_config, new_config, config_file}` | 手動で `config.toml` を編集 |

> `setConfig()` はデフォルトで**5秒遅延してファイルに書き込む**（複数の書き込みを1回にまとめる）；`immediate=True` で即時書き込み。watcher が外部の変更を検出しても、ファイルへの書き戻しは行われません。

**自動応答するコンポーネントリスト**（2種類のイベントは通常両方をサブスクライブし、応答内容は同じ）：

| コンポーネント | 監視 | 応答 |
|------|------|------|
| Logger | `config.set` + `config.updated` | レベル/ファイル/ディレクトリの分割/メモリ上限/フォーマット/無視レベルを再適用（変更検出付き、変化がなければ動かない） |
| Scope | `config.updated` | スコープバインディングのキャッシュを再構築 |
| コマンドシステム | `config.updated` | プレフィックス/大文字小文字/スペースプレフィックス/must_at_bot の解析パラメータを更新し、次のメッセージで有効 |
| アダプターの並行処理 | `config.set` + `config.updated` | `handler_max_concurrency` で失効したシグナルを破棄し、再構築 |
| アクティブGC | `config.set` + `config.updated` | `proactive_gc_*` で即時GCバックグラウンドタスクを再起動 |
| アダプター | `config.updated` にルーティング | 各アダプターの `on_config_update(old, new)` コールバック |
| モジュール | `config.updated` にルーティング | 各モジュールの `on_config_update(old, new)` コールバック |
| ストレージ | `config.updated` | `use_global_db` 変更は**警告のみ**（再起動が必要） |
| ルーター | `config.updated` | `cors.*` / `security.*` 変更は**警告のみ**（再起動が必要） |


## 設定の読み取りと削除API

### getAllConfig：全量設定スナップショット

プライベート `_cache` を直接読み取る代わりに（外部からプライベート属性を読み取るのはバージョン互換性の保護を受けない）：

```python
config = sdk.config.getAllConfig()     # 深いコピーのスナップショット、原地で変更してもフレームワークの状態に影響しない
config["ErisPulse"]["server"]["port"]
```

ビューの口径は `getConfig` と同じ：`setConfig` / `delete` で遅延書き込みされた内容も反映され、ファイルの内容と厳密に一致します。

### delConfig：設定キーの削除

`setConfig(key, None)` は値を空に設定するだけで、キーはファイルに残ります；`delConfig` はキーをファイルから**削除**します：

```python
sdk.config.delConfig("ErisPulse.modules.status.OldModule")            # 遅延書き込み
sdk.config.delConfig("OneBot.deprecated_key", immediate=True)         # 即時書き込み
```

- ドット区切りパスをサポート；キーが存在しない場合は `False` を返す
- 書き込みはコメント保持のパスを使用し、ファイルの他の内容や順序は影響を受けない
- `config.set` イベントのブロードキャストを再利用（`new_value=None`）：アダプターやモジュールの `on_config_update` などの既存のリスナーは変更なしで削除を感知できる

## 完全な設定例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.master]
# users は2種類の書き方（1つを選ぶ）：
#   グローバルマスター（すべてのプラットフォームに有効）：users = ["123456", "789012"]
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
# コンテナ / ファイルがマウントされていない状況では、内包PEM内容（ssl_certfile/ssl_keyfileのパスより優先）を指定できる
# ssl_cert = """-----BEGIN CERTIFICATE-----
# ...
# -----END CERTIFICATE-----"""
# ssl_key = """-----BEGIN PRIVATE KEY-----
# ...
# -----END PRIVATE KEY-----"""
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 監聴アドレス、0.0.0.0はすべてのインターフェースを意味する |
| port | integer | 8000 | 監聴ポート番号 |
| auto_start | boolean | true | `sdk.init()` 時にルートサーバーを自動起動するかどうか。`false`に設定するとルートサーバーの起動をスキップ（純イベント/無WebUIの状況） |
| ssl_certfile | string | 空 | SSL証明書ファイルのパス |
| ssl_keyfile | string | 空 | SSL秘密鍵ファイルのパス |
| ssl_cert | string | 空 | **内包PEM証明書内容**（パスではない）。`ssl_key`とペアで使用する場合、`ssl_certfile`/`ssl_keyfile`のパスより優先される；フレームワークはSSLコンテキストを構築した後、即座に一時ファイルを削除する |
| ssl_key | string | 空 | **内包PEM秘密鍵内容**（パスではない）、上記と同様の意味 |

> **ポートの占有は致命的なエラーではない**：起動時に `port` が既に占有されている場合、フレームワークはルートサーバーの起動をスキップして警告を出力し、**アダプターとモジュールは通常通り実行される**（HTTP/WS/SSEルートとWebUIは利用できない）。ロボットは動くがWebUIが開かない場合のトラブルシューティングでは、まずポートを確認すること。

## マスターシステム設定

マスターシステムは「フレームワークマスター」アカウント（例：Bot管理者）を識別するためのものです。`master.users` は2種類の書き方をサポートします：

```toml
[ErisPulse.master]
# 書き方1：グローバルマスター（すべてのプラットフォームに有効）
users = ["123456", "789012"]

# 書き方2：プラットフォームごとにマスターを指定（dict）
# users = { yunhu = ["123456"], telegram = ["789012"] }
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| users | array / object | 空 | マスターアカウントリスト。`list`形式はグローバルマスター（すべてのプラットフォームに有効）；`dict`形式はプラットフォームごとに指定（キーがプラットフォーム名、値がそのプラットフォームのマスターアカウントリスト） |

コードでは `master.is_master(event)` または `master.is_master(platform, user_id)` でチェックし、毎回呼び出し時にリアルタイムに設定を読み取り（ホットアップデートに対応し、再起動不要）：

```python
from ErisPulse.Core import master

if master.is_master(event):
    await event.reply("主人你好")
```

### 判定チェーンと実行時追加削除

マスター判定チェーンは **設定マスター → 実行時記録 → providerチェーン** です：

```python
from ErisPulse.Core import master

master.is_master(event)                      # イベントから判定
master.is_master("yunhu", "123")             # 明示的に判定
master.add("yunhu", "123")                   # 実行時に追加（デフォルトは永続化；persist=Falseはメモリ内のみ）
master.remove("yunhu", "123")                # 削除（デフォルトは永続化）
master.list()                                # 総合：{"global": [...], "<platform>": [...]}
```

### 自定义身份源（provider）

設定以外にも、カスタムアイデンティティソースを登録できます：`fn(platform, user_id) -> bool`、
組み込みアイデンティティソース（設定 + 実行時記録）がヒットしなかった場合に順次試され、
いずれかのproviderが許可すればマスターと判定されます。外部アイデンティティ体系（例：アダプター管理者API、データベースロール）に接続するのに適しています。

登録エントリ `master.provider` はデコレータ / 関数形式の両方で使用でき、
登録解除は登録された関数の `fn.unregister()` で行います：

```python
from ErisPulse.Core import master

# デコレータ形式（常駐アイデンティティソース、推奨）
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # 自定義判定ロジック

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # 使用停止時に登録解除

# 関数形式（モジュールロード時登録 / アンロード時登録解除）
fn = master.provider(admin_provider)
fn.unregister()
```

> providerの例外はキャッチされてスキップされ、アイデンティティ判定チェーンをブロックしません。
> インスタンスメソッドをバインディングして `unregister` を登録できないため、登録/解除のペアが必要な場合は**モジュールレベルの関数**を使用してください。

### ユーザー優先：マスターの有効範囲はユーザーが最終的に決定

コマンドの `master=True` は**開発者のデフォルト**です：ユーザーは
`ErisPulse.event.overrides.command.<module>.<cmd>.master = true/false`
を上書きして、厳しくしたり緩めたり（[統一イベント覆写設定](#統一イベント覆写設定eventoverrides)を参照）できます。ユーザーが明示的に設定した場合、それが有効になります。

## ログ設定

```toml
[ErisPulse.logger]
level = "INFO"
log_files = []                # 明示的なログファイルリスト（log_dirと互換性あり、優先度が高い）
log_dir = ""                  # ログ出力ディレクトリ（自動作成）。設定するとerispulse.logがディレクトリ内に書き込まれ、log_rotationで自動的に分割される；log_filesと互換性があり、log_filesが優先）
log_rotation = "size"         # 分割方法: "size" / "date" / "none"
log_max_size_mb = 10          # sizeモードの単ファイル上限（MB）
log_backup_count = 5          # 保持する履歴ログファイル数
log_rotation_when = "midnight"  # dateモードの分割周期: S/M/H/D/midnight（デフォルトは毎日0時）
memory_limit = 1000             # 単モジュールのメモリログの上限件数；0 = メモリログのコピーを無効化（メモリに書き込まない、既存の記録は保持）
total_memory_limit = 5000       # 全モジュールのメモリログの総上限件数；0 = 無制限。超過した場合、ローテーション戦略に従って最も古い記録を削除（最も件数が多いモジュールのキューから優先的に削除）、単モジュールのmemory_limitとは独立して有効）
exclude_levels = ["EVENT"]
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| level | string | INFO | ログレベル：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACEが最低レベルで、フレームワーク内部の詳細なデバッグ情報を出力） |
| format | string | rich | ログ出力フォーマット：`rich`（カラー、デフォルト）、`plain`（カラーなしの純粋なテキスト、ログ収集/パイプ重定向に適している）、`json`（JSON形式、ELKなどに適している） |
| log_files | array | 空 | ログ出力ファイルリスト（明示的なパス、分割しない） |
| log_dir | string | 空 | ログ出力ディレクトリ（自動作成）。設定すると、`log_rotation`で自動的に分割されたerispulse.logがディレクトリ内に書き込まれる；`log_files`と互換性があり、`log_files`が優先） |
| log_rotation | string | size | 分割方法：`size`（サイズで）、`date`（日付で）、`none`（分割しない） |
| log_max_size_mb | float | 10 | sizeモードの単ファイルサイズ上限（MB）、超過すると.1/.2のバックアップにローテーションされる |
| log_backup_count | integer | 5 | 保持する履歴ログファイル数、超過した古いバックアップは自動的に削除される |
| log_rotation_when | string | midnight | dateモードのローテーション周期：`S`/`M`/`H`/`D`/`midnight`（デフォルトは毎日0時） |
| memory_limit | integer | 1000 | 単モジュールのメモリに保持するログの件数；`0`はメモリログのコピーを無効化（メモリに書き込まない、既存の記録は保持） |
| total_memory_limit | integer | 5000 | 全モジュールのメモリログの総件数上限；`0`は制限なし。超過した場合、ローテーション戦略に従って最も古い記録を削除（最も件数が多いモジュールのキューから優先的に削除）、単モジュールの`memory_limit`とは独立して有効） |
| exclude_levels | array | 空 | 無視するログレベル。無視されたレベルのログは**完全に破棄**（メモリに書き込まない、ダッシュボードなどのサブスクライバーに送信しない、印刷しない、ファイルに書き込まない）。ホットアップデートが可能 |

また、コード内で動的に切り替えることもできます：

```python
from ErisPulse.Core import logger

# サイズで分割：単ファイル10MB、バックアップ5個
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# 日付で分割：毎日0時にローテーション、バックアップ7個
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]
> `log_dir` および分割関連の設定は ErisPulse **2.8.0+** が必要です。

> **プライバシー保護**：メッセージの送受信内容は **EVENT** レベル（数値21）で記録されます。`exclude_levels = ["EVENT"]` に設定すると、バックエンド（例：ダッシュボードのログパネル）は各グループ/プライベートチャットのメッセージ内容を見ることができなくなり、他のログレベルには影響しません。

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
| uninit_timeout | integer | 30 | エレガントシャットダウンの総タイムアウト時間（秒）、これを超えると強制終了。0はタイムアウトを設定しない |
| strict_mode | integer | 0 | エンフォースモードレベル、下記の「エクスプレスモード」を参照 |
| handler_max_concurrency | integer | 64 | イベントハンドラの最大並行タスク数、大きくすると処理能力が上がるがメモリ使用量も増える |
| handler_queue_max_pending | integer | 4096 | イベントのバースト時のキューのバックプレッシャー：単一プラットフォームの待機中のハンドラタスク数の上限、これを超えると新しいイベントのハンドラタスクは直接破棄され、WARNINGが記録される（破棄件数はトラブルシューティングで確認できる）；`0`は制限しない |
| offline_bot_expiry | integer | 3600 | オフラインBotの記録の自動期限切れ時間（秒）、0は期限切れしない |
| plugins_dir | string / list | "plugins" | ローカルプラグインのフォルダ（プロジェクトルートからの相対パス）；プラグインの追加/削除/変更はホットリロードのwatcherが自動的に検出する |
| watch_ignore_dirs | list | 内部のリスト | ホットリロードのファイル監視で無視するディレクトリ名（`.venv`/`.git`/`__pycache__`など）；空のリストは**内部のリストを上書き**し、`[]`はどのディレクトリも無視しない |
| watch_include_plugin_dirs | boolean | true | `epsdk run --reload` でプラグインディレクトリをプラグインのホットリロードwatcherに正確に処理させ、全量監視から除外するか |

### アクティブGC設定

SDKの初期化後にバックグラウンドタスクとしてアクティブGCを起動し、周期的にPythonのGCと内部リソースの回収（オフラインBotのクリーンアップなど）を実行します。すべてのパラメータはホットアップデートが可能で、変更時に即座にタスクを再起動します。

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | 回収間隔（秒）、小数も可能。0はアクティブGCを無効化 |
| proactive_gc_generation | integer | 0 | 通常の回収世代（0/1/2、0..2に制限）。注意 `gc.collect(2)` は全量回収に等しく、デフォルトは0で軽量に保つ；深い回収は `proactive_gc_full_every` で周期的に実行 |
| proactive_gc_full_every | integer | 20 | Nラウンドごとに全量回収を行う、0は周期的全量回収を無効化。全量回収は `proactive_gc_memory_growth_mb` のしきい値に従う |
| proactive_gc_memory_growth_mb | integer | 32 | 全量回収のメモリ増加しきい値（MB）：前回の全量回収後のメモリベースライン（優先 tracemalloc、次に RSS）と比較し、この値に達した場合に全量回収を実行する。0はしきい値を設定しない |
| proactive_gc_idle_only | boolean | false | 有効にすると、イベントのバースト（未完了のpending handlerがある）の場合はこのラウンドはPython GCをスキップし、メッセージ処理との競合を避ける；内部リソース回収には影響しない |
| proactive_gc_gen0_min | integer | 500 | 通常のラウンドで回収をトリガーするgen0のガベージ量の下限：`gc.get_count()[0]`がこの値より低い場合はスキップ（空回りラウンドはほぼゼロコスト）。0は常に回収する |

> **2.7.1 変更**：デフォルト `proactive_gc_generation` は `2` から `0` に調整され、`proactive_gc_full_every` は `0` から `20` に調整されました。以前は `generation=2` で毎ラウンド最重の全量回収を意味していました；新しいデフォルトでは回収カバレッジを維持しつつ、空回りのコストを大幅に削減しました。明示的に設定した旧値は文字通りの意味で動作します。

### エンフォースモード

エンフォースモードは、モジュール/アダプターがロード段階で不正な状態や失敗した場合の処理戦略を制御します。モダンなモジュール/アダプターは `BaseModule`/`BaseAdapter` を継承する必要があります。継承していないコンポーネントはフレームワークのコンテキストシステムとバックアップクリーンアップに影響し、リソースリークを引き起こす可能性があります。

> **2.5.2 変更**：デフォルトレベルは `1`（スキップ）から `0`（緩和）に調整され、新規ユーザーが初期使用時に遭遇するロード問題を減らしました。継承していないコンポーネントは警告として扱われ、ロードされます。以前の動作を復元するには、`strict_mode = 1` を明示的に設定してください。

| レベル | 名称 | 行動 |
|------|------|------|
| 0 | 緩和（デフォルト） | 不正は警告として扱われ、継承していないコンポーネントもロードされます（旧コンポーネントの互換性） |
| 1 | エンフォース-スキップ | 継承していないコンポーネントは拒否してスキップし、他のコンポーネントは正常に起動します |
| 2 | エンフォース-致命 | すべての不正（継承していない、ロード失敗、登録失敗、初期化失敗など）を致命的に扱い、起動チェックポイントで一括して不正リストを出力して起動を中断します |

各レベルで、「ロード/登録/初期化段階でエラーが発生した」コンポーネントの自身のクラッシュは常にスキップされます。違いは以下の通りです：

- **0 → 1**：唯一の動作変化は「継承していない」コンポーネントが「ロードされる」から「スキップされる」ことです。
- **1 → 2**：すべての不正（継承していない、ロード失敗、登録失敗、初期化失敗など）が致命的に扱われ、起動チェックポイントで一括して不正リストを出力して起動を中断します。

#### 拡張リスト

一部のコンポーネントが一時的に移行できない（例：依存する旧モジュール）場合、それらを拡張リストに追加することで、不正なコンポーネントも緩和モードでロードされます：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> あるコンポーネントがエンフォースモードで拒否された場合、ログにはどのように再びロードを回復するか（拡張リストに追加するか、レベルを下げること）が明確に示されます。

#### CLIとの連携

`epsdk run` の起動前の自己検証（設定ファイルの解析性、コンポーネントの必須設定の完全性）はデフォルトで本設定に従います：非0の場合は検証失敗で起動を拒否し、0の場合は警告を出して継続します。また、設定を変更せずに一時的に切り替えることもできます：`epsdk run --strict` で今回の検証とエンフォースレベルを同時に有効にします（レベルは下がらず、`ERISPULSE_FRAMEWORK_STRICT_MODE` 環境変数で実行プロセスに伝達されます）、`--no-strict` で一時的に緩和モードにし、警告のみ出します。

## ストレージ設定

2.8.0から、ストレージエンジンは3つの非同期バックエンドをサポートし、**APIは完全に一致し、設定は1つで切り替え可能**です：

| バックエンド | ドライバー | インストール | 特徴 |
|------|------|------|------|
| SQLite（デフォルト） | aiosqlite | 開梱即用 | 零設定、単一ファイル、WAL並行 |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | 既存のMySQLインフラストラクチャ、複数インスタンス共有 |
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
| storage.mysql.* | table | 上記を参照 | MySQL接続パラメータ（host / port / user / password / database / charset / pool） |
| storage.postgres.* | table | 上記を参照 | PostgreSQL接続パラメータ（host / port / user / password / database / pool） |

また、環境変数で上書きすることもできます（Docker / 12-factor）：`ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`。

> [!TIP]
> - 接続パラメータを変更した後はフレームワークを再起動して有効にする必要があります；接続プールの作成が瞬時失敗した場合は指数関数的な退避で再試行されます
> - バックエンドを切り替える前に検証スクリプトで自検証できます：`python tests/devs/test_storage_backend_verify.py --backend mysql`
> - トランザクション / ダイアレクトの違い / 自定義バックエンドなど完全な説明は[ストレージバックエンド](../advanced/storage-backends.md)を参照してください

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
| case_sensitive | boolean | true | 大文字小文字を区別するかどうか（`/Help` と `/help` は異なるコマンドか） |
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
| max_per_session | int | 50 | 1つの会話に保持する件数（0 = 会話のカットを無効化） |
| ttl_hours | float | 168.0 | 全体の保持期間（時間、0 = 永久に削除しない） |
| self_echo | string | bot | 受信したbotのエコー（`self.user_id == user_id`、OneBot `report-self-message`）の処理：`bot` = botとして記録し `meta.self_echo` をマーク；`skip` = 記録しない；`user` = userとして記録（旧動作） |

> 保持戦略のリスクと監査は [会話受信箱](../advanced/transcript.md) を参照してください；帰属フィールド（`sender` / `meta`）と送信所属（`meta.module`）も同ドキュメントを参照してください。

## 国際化設定

```toml
[ErisPulse.i18n]
language = "auto"
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| language | string | auto | フレームワークの内部テキストの表示言語。`auto` に設定するとシステム言語を自動検出、具体的な言語コード（`zh-CN`、`zh-TW`、`en`、`ja`、`ru`）を設定することもできます |

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

# 設定を読み取る
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# 実行時に設定を書き込む（遅延保存）
sdk.config.setConfig("MyModule.timeout", 60)

# 即時保存
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` はデフォルトで遅延書き込み（約5秒ごとにファイルにバッチ保存）されます。`immediate=True` で即時永続化されます。設定変更は `config.set` ライフサイクルイベントをトリガーします。

## スコープ設定（scope）

> [!NOTE]
> 本特性は ErisPulse **2.8.0+** が必要です。

スコープは「**どの範囲で有効か**」を宣言します — どのプラットフォーム / Bot / セッションでどのモジュールが使えるか（① モジュール次元）、どのユーザー / グループ / Bot / アダプターのイベントを受け取るか（② アイデンティティ次元）、どのモジュールがどの出力呼び出しを行えるか（③ 出力次元）：

```toml
[ErisPulse.scope]
default_allow = true        # グローバルデフォルト（false = 明示的に拒否、エクスプレスモードには影響しない）
cache_size = 1024           # LRUキャッシュサイズ

# ① モジュール次元（優先度：セッション > Bot > プラットフォーム；エントリは正確 / glob / re: 正規表現）
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]
blocked = ["re:^Danger"]

# 子級バインディングで merge = true の場合、低優先度のエントリと1つ1つを並列にマージ（デフォルトは全体を上書き）
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true

# ② アイデンティティ次元（優先度：ユーザー > セッション > Bot > アダプター；各レベルは allow または deny のどちらかを1つだけ書く）
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                 # 該当プラットフォームのすべてのイベントをエントリで破棄

[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]         # ユーザーのキーは glob / re: 正規表現をサポート
deny = ["u_bad", "spam_*"]

# ③ 出力次元（デフォルトは全許可；ルールはインラインテーブル、エントリは正確 / glob / re: 正規表現をサポート）
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                    # 送信を全禁止
api = { allow = ["get_*"] }               # クエリ系の標準APIのみ許可
request = { deny = true }                 # リクエスト処理を禁止
```

| 設定項目 | 型 | 説明 |
|---------|------|------|
| `scope.default_allow` | boolean | グローバルデフォルト：モジュール/アイデンティティがルールにヒットしなかった場合の許可/拒否（`true`） |
| `scope.cache_size` | integer | LRUキャッシュサイズ（デフォルト1024） |
| `scope.platforms / bots / sessions` | table | ① モジュール3段階バインディング：`{modules=[...], blocked=[...], merge=bool?}` |
| `scope.identity.adapters / bots / sessions / users` | table | ② アイデンティティ4段階バインディング：`{allow=true}` / `{deny=true}` |
| `scope.actions.<module>.<action>` | table | ③ 出力ルール：`{allow=[...], deny=true|[...]}`（actionはsend / api / request） |

> 詳細と実行時API（次元化 `sdk.scope.set_module()` / `set_identity()` / `set_action()`、判定 `is_allowed()` / `is_identity_allowed()` / `is_action_allowed()`、および辞書式デフォルト `get()` / `set()` / `delete()`）は[スコープ（scope）](../advanced/scope.md)を参照してください。

## 統一イベントオーバーライド設定（event.overrides）

統一オーバーライドシステム：イベントタイプごとに任意のモジュールハンドラの動作をオーバーライドし、モジュールコードを変更することなく実行します。OneBot12標準タイプ（meta / message / notice / request）と拡張タイプ（command）それぞれにオーバーライド可能なパラメータがあります：

```toml
[ErisPulse.event.overrides]

# message：テキストトリガー条件（コード内の条件とAND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice / request / meta：detail_typeホワイトリスト（エントリは正確 / glob / re: 正規表現をサポート）
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command（拡張タイプ）：実装パラメータのオーバーライド（ユーザーが優先；オーバーライドはacl denyで無効）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true               # フレームワークマスターのみに変更（falseで開発者のマスターリミットを開放）
hidden = true               # ヘルプリストから非表示
aliases = ["rs"]            # 生効果のエイリアス

# acl（command専用）：コマンドのユーザーホワイト/ブラックリスト（コマンド名はglob / re: 正規表現をサポート、正確なキーが優先）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]  # ユーザー識別子 "platform:user_id"
deny = ["onebot11:u_bad"]

# ACLデフォルト：ACLが設定されていないコマンドを許可（true）/ 严格拒否（false）
acl_default_allow = true
```

| 設定項目 | 型 | 説明 |
|---------|------|------|
| `event.overrides.message.<module>` | table | テキスト条件：`{pattern="...", regex="..."}` |
| `event.overrides.notice / request.<module>` | table | `{detail_types=[...], pattern, regex}` |
| `event.overrides.meta.<module>` | table | `{detail_types=[...]}` |
| `event.overrides.command.<module>` | table | モジュールレベルのパラメータオーバーライド（`hidden = true` などのスカラー値） |
| `event.overrides.command.<module>.<command>` | table | コマンドレベルのオーバーライド（コマンドレベルが優先） |
| `event.overrides.acl.<command>` | table | ユーザーホワイト/ブラックリスト：`{allow=[...], deny=[...]}` |
| `event.overrides.acl_default_allow` | boolean | ACLデフォルト：ACLが設定されていないコマンドを許可（`true`）/ 严格拒否（`false`） |

> 実行時API（`from ErisPulse.Core.Event import overrides` 後、タイプのサブネームスペースに従って `overrides.message.set()` / `overrides.command.set()` / `overrides.acl.set()` など呼び出す、または `sdk.Event.overrides` でアクセスする）は [イベント処理入門 · イベントオーバーライド](../getting-started/event-handling.md#イベントオーバーライドモジュールコードを変更せずに任意のイベントタイプの動作をオーバーライド) を参照してください。

## 次に

- **L1経路に従って**：次のドキュメント [エラー処理](../advanced/errors.md) で、フレームワークをクラッシュさせないエラー処理の書き方を学びましょう
- **手動でTOMLを書きたくない**：`epsdk config` で宣言的な設定項目をインタラクティブに入力するヘルパーを使用する、[CLIコマンドリファレンス · config](cli-reference.md#config) を参照してください
- **設定ファイルを変更したくない**：環境変数で設定項目を上書きし、[デプロイガイド](deployment.md)のDockerの使い方を参照してください