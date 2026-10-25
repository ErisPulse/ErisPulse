---
name: erispulse-config-cli
description: "适用于：配置声明式 schema、排查配置问题、使用 epsdk 命令行与部署。覆盖场景：- 接続パラメータを変更した後はフレームワークの再起動が必要；接続プールの作成が一時的に失敗すると指数関数的に再試行される。**このドキュメントを読むタイミング**：`epsdk` コマンドの引数を忘れてしまったとき、またはスクリプトにコンポーネント管理を組み込みたい場合、あるいは `run` / `stop` / `restart` の動作を制御したいときに参照してください。通常は `init` / `install` / `run` のみを使用する場合は、`epsdk <コマンド> --help` という1つのコマンドを覚えておくだけで十分です。いつでも引数の説明を確認できますので、このドキュメントを全文読む必要はありません。**このページを読むべきタイミング**：インストール方法（pip / uv / Docker / ErisPulse-App クライアント）を選ぶ必要があるときや、インストールに失敗してトラブルシューティングが必要なときに読んでください。とにかく最速で動かしたいだけなら、[5分クイックスタート](../quick-start.md) に最短の手順がまとめられているため、不要であればスキップしてください。**このドキュメントを読むべきタイミング**：ロボットを長期間稼働させる場合に必要です。Dockerでのデプロイ、systemd / Supervisorによるプロセス監視、リバースプロキシとSSL、バックアップとアップグレードはすべてここに記載されています。ローカル開発やデバッグの段階では不要です。"
---

# ErisPulse 配置系统与 CLI 工具链

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 配置系统

> 来源: `docs/ja/user-guide/configuration.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/user-guide/configuration.md）

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

## CLI 参考

> 来源: `docs/ja/user-guide/cli-reference.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/user-guide/cli-reference.md）

# CLI コマンドリファレンス

> [!TIP]
> **このドキュメントを読むタイミング**：`epsdk` コマンドの引数を忘れてしまったとき、またはスクリプトにコンポーネント管理を組み込みたい場合、あるいは `run` / `stop` / `restart` の動作を制御したいときに参照してください。通常は `init` / `install` / `run` のみを使用する場合は、`epsdk <コマンド> --help` という1つのコマンドを覚えておくだけで十分です。いつでも引数の説明を確認できますので、このドキュメントを全文読む必要はありません。

`epsdk` は ErisPulse のコマンドラインツールです。プロジェクトの初期化、モジュールやアダプタのインストール / アップグレード、コンポーネントの対話的設定、ロボットの起動と停止、環境の診断など、すべてをこの1つのコマンドで行います。

> **ヒント**：`epsdk`（コマンドなし）のヘルプはカテゴリ別にグループ化されて表示されます：**プロジェクト**（init / create / run）、**コンポーネント管理**（install / uninstall / upgrade / list / list-remote / types）、**設定と診断**（config / doctor / i18n）、**その他**（self-update / version）。

## パッケージ管理コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | モジュール/アダプタのインストール |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | モジュール/アダプタのアンインストール |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | 指定したモジュールまたはすべてをアップグレード |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | SDK 自体の更新 |

## 診断コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose] [--fix]` | 環境を診断し、健全性レポートを出力します。`--fix` は自動的に修正を試みます |

### install

ErisPulse モジュールまたはアダプタパッケージをインストールします。パッケージ名を指定しない場合は、対話形式のインストールインターフェースに移行します。

**別名：** `i`, `add`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[package]...` | | インストールするパッケージ名、複数指定可能 |
| `--upgrade` | `-U` | インストール時に最新バージョンにアップグレード |
| `--pre` | | プレリリース版のインストールを許可 |
| `--editable` | `-e` | 編集可能なモードでインストール（パスを指定する必要あり） |
| `--user` | | ユーザーの site-packages ディレクトリにインストール |
| `--no-deps` | | 依存関係をインストールしない |
| `--target` | `-t` | 指定したディレクトリにインストール |
| `--index-url` | | PyPI ミラーサーバーのURLを指定 |
| `--extra-index-url` | | 余分な PyPI ミラーサーバーのURL（複数指定可能） |
| `--no-cache-dir` | | キャッシュを無効化 |
| `--requirement` | `-r` | requirements ファイルからインストール |
| `--constraint` | `-c` | 制約ファイルからインストール |
| `--force-reinstall` | | 強制的に再インストール |
| `--ignore-installed` | | 既にインストールされたパッケージを無視 |
| `--compile` | | インストール後に .pyc ファイルをコンパイル |
| `--no-compile` | | インストール後に .pyc ファイルをコンパイルしない |
| `--prefix` | | 指定したプレフィックスディレクトリにインストール |
| `--src` | | 編集可能なインストール時に使用するソースコードディレクトリ |
| `--config-settings` | | ビルドバックエンドに渡す設定（複数指定可能） |
| `--no-binary` | | 二進位パッケージの使用を制限（`:all:` の形式） |
| `--only-binary` | | 二進位パッケージのみを使用する（`:all:` の形式） |
| `--prefer-binary` | | 二進位パッケージを優先 |
| `--build-isolation` | | ビルド隔離を有効化 |
| `--no-build-isolation` | | ビルド隔離を無効化 |
| `--upgrade-strategy` | | インストール戦略：`eager`、`only-if-needed`、`to-satisfy-only` |
| `--break-system-packages` | | システムパッケージマネージャーが管理する Python パッケージを変更を許可 |
| `--no-uv` | | uv の代わりに pip を使用 |

**例：**

```bash
# 単一モジュールのインストール
epsdk install Weather

# 複数モジュールのインストール
epsdk install Yunhu Weather

# ミラーからインストールしてアップグレード
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 編集可能なモードでインストール（開発モード）
epsdk install -e ./my-adapter
```

### uninstall

インストール済みの ErisPulse モジュールまたはアダプタパッケージをアンインストールします。パッケージ名を指定しない場合は、対話形式のアンインストールインターフェースに移行します。

**別名：** `rm`, `remove`

**パラメータ：**

| パラメータ | 説明 |
|------|------|
| `<package>...` | アンインストールするパッケージ名、複数指定可能 |
| `--no-uv` | uv の代わりに pip を使用 |

**例：**

```bash
# 単一モジュールのアンインストール
epsdk uninstall Weather

# 複数モジュールのアンインストール
epsdk uninstall Yunhu Weather
```

### upgrade

インストール済みの ErisPulse コンポーネントをアップグレードします。パッケージ名を指定しない場合は、対話形式で全アップグレードを行います。

**別名：** `up`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[package]...` | | アップグレードするパッケージ名、複数指定可能 |
| `--force` | `-f` | 強制アップグレード、確認をスキップ |
| `--pre` | | プレリリース版へのアップグレードを許可 |
| `--no-uv` | | uv の代わりに pip を使用 |

**例：**

```bash
# 全てのパッケージをアップグレード
epsdk upgrade

# 指定パッケージをアップグレード
epsdk upgrade Weather

# 強制アップグレード（確認をスキップ）
epsdk upgrade -f
```

### self-update

ErisPulse SDK 自体を最新バージョンに更新します。

**別名：** `su`, `update`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[version]` | | 更新するターゲットバージョンを指定 |
| `--pre` | | プレリリース版への更新を許可 |
| `--force` | `-f` | 強制更新、確認をスキップ |
| `--no-uv` | | uv の代わりに pip を使用 |

**例：**

```bash
# 最新の安定版に更新
epsdk self-update

# 指定バージョンに更新
epsdk self-update 1.2.3

# プレリリース版を許可
epsdk self-update --pre

# 強制更新
epsdk self-update -f
```

> [!NOTE]
> `uv tool install ErisPulse` でインストールする場合、このコマンドは自動的に `uv tool upgrade ErisPulse`（バージョン指定時は `uv tool install ErisPulse==<バージョン> --force`）に変更されます。直接 pip でツール環境をアップグレードすると、uv のリストアによってツール環境のファイルが上書きされます。
> Windows での更新は新しいコマンドプロンプトウィンドウで行われます：現在の CLI はツール環境のファイルの使用を解除するために終了する必要があります。ウィンドウのプロンプトが完了したら、ターミナルを再起動してください。

---

## 情報照会コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | インストール済みのコンポーネントを一覧表示 |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | リモートで利用可能なコンポーネントを一覧表示 |
| `version` | `ver` | | SDK と Python のバージョン情報を表示（`-V` と同等） |

### list

ErisPulse モジュールとアダプタを一覧表示します。

**別名：** `l`, `ls`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--type` | `-t` | 指定するタイプ：`modules`、`adapters`、`all`（デフォルト） |
| `--outdated` | `-o` | アップグレード可能なパッケージのみ表示 |

**例：**

```bash
# インストール済みのすべてのコンポーネントを一覧表示
epsdk list

# モジュールのみを一覧表示
epsdk list -t modules

# アダプタのみを一覧表示
epsdk list -t adapters

# アップグレード可能なパッケージのみを表示
epsdk list -o
```

### list-remote

リモートリポジトリで利用可能な ErisPulse モジュールとアダプタを一覧表示します。

**別名：** `lsr`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--type` | `-t` | 指定するタイプ：`modules`、`adapters`、`all`（デフォルト） |
| `--refresh` | `-r` | リモートパッケージリストのキャッシュを強制的に更新 |

**例：**

```bash
# リモートで利用可能なすべてのコンポーネントを一覧表示
epsdk list-remote

# リモートのモジュールのみを一覧表示
epsdk list-remote -t modules

# キャッシュを強制的に更新して表示
epsdk list-remote -r
```

---

## 設定コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `config` | `cfg`, `conf` | `[name] [--list/-l] [--json]` | アダプタ/モジュールの宣言的設定項目を対話形式で設定 |

### config

アダプタ/モジュールの宣言的設定項目を対話形式で設定します。アダプタ/モジュールが宣言した設定クラス（`ConfigClass` / `AccountConfigClass`）によって、自動的にフォームが生成され、検証が行われます。`config.toml` を手動で書く必要はありません。

アダプタは追加で、複数のアカウント（botアカウント）の管理をサポートしています：アカウントの追加/編集/削除、および有効化/無効化のスイッチ。

**別名：** `cfg`, `conf`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[name]` | | 対象の名前（アダプタのプラットフォーム名またはモジュール名）、空欄の場合は対話形式で選択 |
| `--list` | `-l` | 対象の設定状態を一覧表示し、対話形式に入らない |
| `--json` | | 全ての対象とその設定状態を JSON 形式で出力（CI / スクリプト用）、対話形式に入らない |

**例：**

```bash
# すべてのアダプタ/モジュールの設定状態を表示
epsdk config --list

# 設定状態を JSON 形式で出力（CI / スクリプト用）
epsdk config --json

# 対話形式で対象を選択して設定
epsdk config

# 指定アダプタを直接設定
epsdk config yunhu

# 指定モジュールを直接設定
epsdk config MyModule
```

**説明：**

- 設定状態は4段階に分類されます：`完了`（検証通過）、`未完了`（必須項目が欠落または検証失敗）、`未設定`（未生成）、`無設定`（設定クラスが宣言されていない）
- フィールド値にはソースが表示されます：既に設定されている場合は `（現在:値）`、未設定の場合は schema のデフォルト値 `（デフォルト:値）` が表示されます。直接 Enter すると、その値が保持されます。
- シークレットフィールド（`secret` と宣言）は、入力時に表示されず、Enter で既存の値を保持します。
- 対話形式で選択した場合、1つのフォームが終了すると状態が更新され、選択メニューに戻り、複数の対象を連続して設定できます。空欄で終了します。
- グローバルフォームの検証が失敗し、再入力を放棄した場合、今回の対話は中止され、設定は一切書き込まれません（「有効化されているが設定が不完全」の半完成状態を避けるため）。
- 保存後、`config/config.toml` に即時書き込まれ、ダッシュボードと実行中の SDK で確認できます。実行中のアダプタが新しいアカウントの設定を適用するには、プロセスを再起動する必要があります。
- `epsdk install`（対話形式のインストール）または `epsdk init` でアダプタをインストールした後、設定宣言が検出された場合、自動的に本対話形式の設定に誘導されます。コマンドラインで直接パッケージ名を指定してインストールした場合、設定の提示のみ表示されます。

---

## 実行コントロールコマンド

> [!TIP]
> `epsdk run` は、プロジェクトディレクトリ内の `.venv` 仮想環境を自動的に検出して、その環境でロボットを実行します。
> （または `ERISPULSE_PYTHON` 環境変数を使って解釈器を明示的に指定することもできます。）`epsdk install` /
> `uninstall` / `upgrade` / `list` も同様に、プロジェクトの仮想環境に対して作用します。

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `run` | `r` | `[script] [--reload] [--strict/--no-strict]` | 指定されたスクリプトまたは SDK を実行します。|
| `stop` | — | `[--force] [--pid PID]` | `epsdk run` によって起動された実行中のインスタンスを停止します。|
| `restart` | — | `[--force] [--pid PID]` | 実行中のインスタンスを再起動します（停止後、元のパラメータで再起動します）。|

### run

ErisPulse プロジェクトのスクリプトを実行するか、SDK を直接起動します。ホットリロードモードをサポートしています。

**別名：** `r`

**パラメータ：**

| パラメータ | 説明 |
|------|------|
| `[script]` | 実行するスクリプトファイル。指定しない場合は SDK を実行します。|
| `--reload` | ホットリロードモードを有効にします。ファイルの変更を監視し、コンポーネントレベルのコードのホットリロードを自動的にトリガーします（ホットリロードシステムと連動し、プロセス全体の再起動は不要です）。|
| `--strict` / `--no-strict` | 一時的に厳格モードを有効または無効にします（本次のみ有効、設定ファイルには書き込まれません）。デフォルトは `ErisPulse.framework.strict_mode` に従います。|

**例：**

```bash
# SDK を直接実行します
epsdk run

# 指定したスクリプトファイルを実行します
epsdk run main.py

# ホットリロードモードで実行します（ファイルの変更でコードレベルのホットリロードが自動的にトリガーされます）
epsdk run main.py --reload

# SDK のホットリロードモード
epsdk run --reload

# 一時的な厳格モード：起動前の自己検証に失敗した場合、即座に終了します。フレームワークの厳格レベルを今回の実行で少なくとも 1 に上げます
epsdk run main.py --strict

# 一時的な緩和モード（設定で strict_mode が有効になっているが、今回は先に実行したい場合）
epsdk run main.py --no-strict
```

**起動前の自己検証：** `run` は起動前に `config/config.toml` の解析性と、インストール済みのコンポーネントの必須設定の完全性を迅速にチェックします。厳格性はデフォルトで `ErisPulse.framework.strict_mode` に従います（0 でない場合、チェックに失敗すると終了し、0 の場合は警告のみで継続します）。設定ファイルが欠落している場合は、正常な初期起動と見なし、警告のみを表示して失敗とは判定しません。`--strict` で一時的に厳格モードを有効にすると、事前チェックに失敗した場合に即座に終了し、フレームワークの厳格レベルを今回の実行で少なくとも 1 に上げます（不適合なコンポーネントはスキップし、`ERISPULSE_FRAMEWORK_STRICT_MODE` 環境変数を通じて実行プロセスに伝達され、設定ファイルには書き込まれません）。`--no-strict` はその逆で、一時的に緩和されます。自己検証自体が異常な場合は自動的にスキップされ、ネットワークの探査は含まれず、起動をブロックすることはありません。

### stop

`epsdk run` によって起動され、同じプロジェクトディレクトリで実行された ErisPulse インスタンスを停止します。
`run` は、監督プロセスの PID、現在のフレームワークの子プロセスの PID、および元の起動コマンドを
`.erispulse/runtime.json` に書き込みます。`stop` は、このファイルに基づいてインスタンスを特定します。

**停止順序：** POSIX 環境では、監督プロセスに SIGINT を送信します（Ctrl+C と同じ優雅な終了経路——
finally チェーンが自動的にフレームワークの子プロセスを終了します）。タイムアウトが発生した場合は、SIGTERM / SIGKILL に段階的に昇格します。Windows 環境では、プロセス信号の意味論がないため、まずフレームワークの子プロセスを終了し、次に監督プロセスを終了します（監督者が強制終了をクラッシュと誤認して再起動しないようにします）。

**パラメータ：**

| パラメータ | 説明 |
|------|------|
| `--force` | 優雅な停止をスキップし、強制的に終了します。|
| `--pid PID` | 直接ターゲットプロセスの PID を指定します（実行状態ファイルを上書きし、非標準の起動方法に使用します）。|

**例：**

```bash
# 現在のプロジェクトの実行インスタンスを停止します
epsdk stop

# 強制的に終了します
epsdk stop --force
```

### restart

実行中の ErisPulse インスタンスを再起動します。`stop` の意味に従って停止した後、状態ファイルに記録された
**元の起動コマンド**で再起動します（フォアグラウンドで現在のターミナルを引き継ぎ、新しいインスタンスは新しい実行状態ファイルを書き込みます）。

**パラメータ：** `stop` と同じ（`--force` / `--pid PID`）。

**例：**

```bash
# 優雅に再起動します（pip でアダプタ/モジュールをアップグレードした後にコードの変更を反映する場合；実行中のモジュールは
# sdk.reload_module / sdk.adapter.reload でコードレベルのホットリロードも可能で、再起動は不要です）
epsdk restart
```

> [!NOTE]
> `python main.py` など、`epsdk run` を経由しない起動方法では実行状態ファイルが書き込まれません。このような
> プロセスは、システムツールで管理するか、`epsdk stop --pid <PID>` を使って PID を指定してください。

## プロジェクト管理コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `init` | — | `[path] [--project-name/-n <name>] [--path <dir>] [--adapter/-a <name>] [--quick/-q] [--force/-f] [--here] [--no-uv] [--no-venv]` | ErisPulse プロジェクトを初期化 |
| `create` | — | `{module,adapter,pack} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f] [--local]` | モジュール/アダプタのフットスタジアムを作成；`pack` はローカルプラグインを公開可能なプロジェクトに変換します |

### init

新しい ErisPulse プロジェクトを初期化します。対話形式とクイックモードをサポートし、2.8.4 以降は `pyproject.toml`（依存関係リスト）、任意のディレクトリに作成可能な仮想環境 `.venv` の生成とフレームワークおよびアダプタのインストールをサポートします。

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[path]` | | 目標パス（親ディレクトリを含む可能性あり、例：`../apps/mybot`；純粋な名前は `--project-name` と同等） |
| `--project-name` | `-n` | プロジェクト名 |
| `--path` | | プロジェクトの親ディレクトリ（`-n` と組み合わせて作成位置を指定） |
| `--adapter` | `-a` | 事前にインストールするアダプタ（複数指定可能、またはカンマ区切りで指定）、指定した場合はアダプタの問い合わせと選択をスキップ |
| `--quick` | `-q` | クイックモード、対話形式のガイドをスキップ（デフォルトで `.venv` を作成し、依存関係をインストール） |
| `--force` | `-f` | 既存の設定ファイルを上書き |
| `--here` | | 現在のディレクトリで初期化し、サブディレクトリを作成しない |
| `--no-uv` | | uv の代わりに pip を使用 |
| `--no-venv` | | 仮想環境の作成と依存関係のインストールをスキップ |

**例：**

```bash
# 対話形式で初期化
epsdk init

# クイックモードで初期化（現在のディレクトリに `my_bot/` を作成し、`pyproject.toml` + `.venv` を含む）
epsdk init -q -n my_bot

# クイックモードで初期化し、事前にアダプタをインストール（対話形式をスキップ、スクリプト / CI 環境）
epsdk init -q -n my_bot --adapter yunhu,telegram

# 任意のディレクトリで初期化（`../apps/mybot`）
epsdk init ../apps/mybot

# 親ディレクトリとプロジェクト名を組み合わせて指定
epsdk init -n my_bot --path ../apps

# 既存の設定ファイルを上書き
epsdk init -f

# 現在のディレクトリで初期化
epsdk init --here -n my_bot

# プロジェクト構造のみを作成し、仮想環境を作成しない
epsdk init --no-venv -n my_bot
```

init の成果物：`main.py`、`pyproject.toml`（依存関係リスト）、`config/config.toml` + `config.full.example`、`config/ssl/`、`logs/`、`.gitignore`、`README.md`；仮想環境を作成した場合は `.venv` を生成し、`erispulse` と選択したアダプタをその中にインストールします。

> [!NOTE]
> `.gitignore` はグループ形式のテンプレートです：Python のバイトコードとビルド成果物、仮想環境と `.env`、ツールのキャッシュ、エディタとシステムファイル、そして**`config/` と `logs/` の実行時ディレクトリを全体的に除外**します。`config.toml` にはアダプタのトークンなどの機密情報が含まれているため、リポジトリに含めるべきではありません。共有する設定の骨格は `config.full.example` を使用してください。

> [!WARNING]
> **`uv run epsdk run` を使用してロボットを実行しないでください**。`uv run` は `pyproject.toml` がないディレクトリで実行すると**一時的な隔離環境**を作成します。その中で `epsdk install` でインストールしたアダプタは永続化されません。プロジェクトディレクトリ内で `epsdk run` を使用してください（自動的にプロジェクトの `.venv` を使用し、または仮想環境をアクティベートしてから実行してください）。

### create

ErisPulse モジュールまたはアダプタのフットスタジアムプロジェクトを作成します。`pack` サブコマンドはローカルプラグイン（`plugins/` ディレクトリ）を公開可能な標準プロジェクトに変換します。

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `{module,adapter,pack}` | | 作成するタイプ：`module` / `adapter` / `pack`（プラグインをプロジェクトに変換） |
| `--name` | `-n` | プロジェクト名（PascalCase） |
| `--description` | `-d` | プロジェクトの説明 |
| `--author` | `-a` | 作者名 |
| `--email` | `-e` | 作者のメールアドレス |
| `--homepage` | | プロジェクトのホームページ URL |
| `--output` | `-o` | 出力ディレクトリ（デフォルトは現在のディレクトリ） |
| `--force` | `-f` | 既存のディレクトリを上書き |
| `--local` | | ローカルプラグインを作成（`module` / `adapter` で使用可能）：`plugins/<name>/` パッケージ構造を生成し、パッケージ化せずにインストール可能 |

**例：**

```bash
# 対話形式で作成（タイプの選択と情報を入力するガイド）
epsdk create

# Module プロジェクトを直接作成
epsdk create module -n MyModule

# ローカルプラグインを作成（プロジェクトの `plugins/` ディレクトリに配置し、起動時に自動的に検出される）
epsdk create module -n MyModule --local

# ローカルアダプタプラグインを作成（同上、パッケージ化せずに開発可能）
epsdk create adapter -n MyAdapter --local

# Adapter プロジェクトを直接作成
epsdk create adapter -n MyAdapter

# ローカルプラグインを公開可能なプロジェクトに変換（対話形式でプラグインを選択 → 元情報の補完 → 標準プロジェクトの生成）
epsdk create pack

# 完全なパラメータ
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 出力ディレクトリを指定
epsdk create module -n MyModule -o ./projects

# 既存のディレクトリを上書き
epsdk create module -n MyModule -f
```

---

## 言語コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | CLI の表示言語を確認または切り替え |

### i18n

現在の CLI 言語を確認、サポートされている言語の一覧を表示、表示言語を切り替えます。パラメータを指定しない場合は、対話形式の選択画面に移行します。

**別名：** `language`, `lang`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[lang]` | | 切り替える言語コード（例：`zh-CN`、`en`、`ja`、`ru`） |
| `--list` | `-l` | すべてのサポートされている言語を一覧表示 |

**例：**

```bash
# 対話形式で言語を選択
epsdk i18n

# 英語に切り替え
epsdk i18n en

# 日本語に切り替え
epsdk i18n ja

# すべてのサポートされている言語を一覧表示
epsdk i18n --list
```

---

## タイプストアブコマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | IDE の補完と型チェックを有効にするため、タイプストアブファイルを生成 |

### types

インストール済みの ErisPulse モジュールとアダプタをスキャンし、`.pyi` タイプストアブファイルを生成します。これにより、IDE で正確なコード補完と型チェックが可能になります。

**別名：** `t`, `stub`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--output` | `-o` | 出力パス（デフォルトは現在のディレクトリの `ep-stubs/`） |
| `--force` | | 既存のストアブファイルを上書き |
| `--adapters-only` | | アダプタのタイプストアブのみを生成 |
| `--modules-only` | | モジュールのタイプストアブのみを生成 |

> **注意：** `--adapters-only` と `--modules-only` は排他的です。両方指定した場合、後者（`--modules-only`）が優先されます。

**例：**

```bash
# すべてのインストール済みのモジュールとアダプタにタイプストアブを生成
epsdk types

# アダプタのストアブのみを生成
epsdk types --adapters-only

# 指定ディレクトリに出力
epsdk types -o ./typings

# 既存のファイルを上書き
epsdk types --force
```

---

## グローバルパラメータ

以下のパラメータはすべてのコマンドに適用されます：

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--help` | `-h` | ヘルプ情報を表示 |
| `--version` | `-V` | バージョン情報を表示 |
| `--verbose` | `-v` | 詳細出力を表示（`-vv`/`-vvv` で重ねる） |
| `--no-color` | | 色付き出力を無効化（CI / ログ収集に適しています） |
| `--no-banner` | | スタートバナーをスキップ（スクリプト化呼び出し / CI 環境；非対話端末と `ERISPULSE_NO_BANNER=1` では自動的に静音） |
| `--yes` | `-y` | すべての対話的プロンプトを自動的に確認（非対話実行） |

---

## 環境診断

### doctor

> [!NOTE]
> このコマンドは ErisPulse **2.7.0+** が必要です。

現在の CLI 実行環境を診断し、健全性レポートを出力します。"なぜインストールできない / 接続できないか" などの問題を診断するのに使用します。

| パラメータ | 説明 |
|------|------|
| `--verbose` | 詳細な診断情報を表示 |
| `--fix` | 診断後に自動的に修正可能な問題を修正します |

**チェック項目：**
- **Python**：解釈器のバージョンとパス
- **インストールバックエンド**：`uv` または `pip` を使用
- **ターゲット解釈器**：パッケージが実際にインストールされる Python 環境
- **設定ファイル**：`config/config.toml` が存在するか
- **コンポーネント設定**：インストール済みコンポーネントの宣言的設定の完全性（"インストールは完了したが起動できない"の多くは必須項目が欠落しているため）
- **PyPI 接続性**：PyPI にアクセスできるか（発見されたコンポーネント数を表示）
- **システムプロキシ**：プロキシが検出されているか

**自動修正（`--fix`）**：
- `config.toml` が欠落 → 現在の言語に応じた初期設定ファイルを生成（`init` でプロジェクトを作成するのと同じソース）
- コンポーネントの設定が「未完了」→ 1つずつ対話形式の設定向導を起動し、必須項目を補完（非対話環境では `epsdk config <名称>` を使用するよう提示）
- Python バージョンが低すぎる、PyPI にアクセスできないなどの人為介入が必要な問題 → 修正のための行動提案のみを出力

```bash
# 実行環境の診断
epsdk doctor

# 別名を使用
epsdk diag

# 診断して自動的に修正を試みる
epsdk doctor --fix
```

---

## 対話形式でのインストール

`epsdk install` をパッケージ名を指定せずに実行すると、対話形式のインストールに移行します：

```bash
epsdk install
```

対話インターフェースは以下の内容を提供します：
1. アダプタの選択
2. モジュールの選択
3. 自由なインストール

## 一般的な使い方

### モジュールのインストール

```bash
# 単一モジュールのインストール
epsdk install Weather

# 複数モジュールのインストール
epsdk install Yunhu Weather

# モジュールのアップグレード
epsdk install Weather -U
```

### コンポーネントの一覧表示

```bash
# すべてのコンポーネントを一覧表示
epsdk list

# アダプタのみを一覧表示
epsdk list -t adapters

# アップグレード可能なコンポーネントのみを一覧表示
epsdk list -o

# リモートで利用可能なコンポーネントを一覧表示
epsdk list-remote
```

### コンポーネントのアンインストール

```bash
# 単一コンポーネントのアンインストール
epsdk uninstall Weather

# 複数コンポーネントのアンインストール
epsdk uninstall Yunhu Weather
```

### コンポーネントの設定

```bash
# 設定状態を表示
epsdk config --list

# 対話形式で対象を選択して設定
epsdk config

# 指定アダプタを直接設定
epsdk config yunhu
```

### コンポーネントのアップグレード

```bash
# すべてのコンポーネントをアップグレード
epsdk upgrade

# 指定コンポーネントをアップグレード
epsdk upgrade Weather

# 強制アップグレード
epsdk upgrade -f
```

### プロジェクトの実行

```bash
# 普通に実行
epsdk run main.py

# ホットリロードモードで実行（ファイル変更で自動的に再起動）
epsdk run main.py --reload
```

### 言語の切り替え

```bash
# 対話形式で言語を選択
epsdk i18n

# 英語に直接切り替え
epsdk i18n en

# 利用可能な言語を一覧表示
epsdk i18n --list
```

### タイプストアブの生成

```bash
# すべてのタイプストアブを生成
epsdk types

# モジュールのタイプストアブのみを生成
epsdk types --modules-only
```

### プロジェクトの初期化

```bash
# 対話形式で初期化
epsdk init

# クイックモードで初期化
epsdk init -q -n my_bot
```

### フットスタジアムの作成

```bash
# 対話形式で作成（タイプの選択と情報を入力するガイド）
epsdk create

# Module プロジェクトを直接作成
epsdk create module -n MyModule

# Adapter プロジェクトを直接作成
epsdk create adapter -n MyAdapter

# 完全なパラメータ
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 既存のディレクトリを上書き
epsdk create module -n MyModule -f
```

## 次のステップ

- **コンポーネントのインストール後、設定を記入する必要があります**：`epsdk config` によるインタラクティブなガイドを使用するか、[設定ファイルの説明](configuration.md)を参照して手動で編集してください。
- **コードを書き終えて IDE の補完が欲しい場合**：`epsdk types` を実行し、[型のスタブ生成](../getting-started/ide-completion.md)を参照してください。
- **ロボットが起動しない場合**：まず `epsdk doctor` を実行して環境を診断してください（[環境診断](#環境診断)を参照）。長期的なデプロイが必要な場合は、[デプロイガイド](deployment.md)をご覧ください。

## 安装

> 来源: `docs/ja/user-guide/installation.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/user-guide/installation.md）

# インストールリファレンス

> [!TIP]
> **このページを読むべきタイミング**：インストール方法（pip / uv / Docker / ErisPulse-App クライアント）を選ぶ必要があるときや、インストールに失敗してトラブルシューティングが必要なときに読んでください。とにかく最速で動かしたいだけなら、[5分クイックスタート](../quick-start.md) に最短の手順がまとめられているため、不要であればスキップしてください。

## システム要件

- Python 3.10 – 3.14（3.14t のフリースレッド / GIL なしビルドは実験的なサポートであり、フレームワーク側では実験的な CI スモークテストにより継続的に監視していますが、正式な保証は行いません）
- pip または uv（推奨）
- 十分なディスク容量（最低 100MB）

## インストール方法

### 方法 1: pip を使用したインストール

```bash
# ErisPulse のインストール
pip install ErisPulse

# 最新バージョンへのアップグレード
pip install ErisPulse --upgrade
```

### 方法 2: uv を使用したインストール（推奨）

uv はより高速な Python ツールチェーンであり、開発環境での使用が推奨されています。

#### uv のインストール

```bash
# pip を使用して uv をインストール
pip install uv

# インストールの確認
uv --version
```

#### 仮想環境の作成

```bash
# プロジェクトディレクトリの作成
mkdir my_bot && cd my_bot

# Python 3.12 のインストール
uv python install 3.12

# 仮想環境の作成
uv venv
```

#### 仮想環境の有効化

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### ErisPulse のインストール

```bash
# ErisPulse のインストール
uv pip install ErisPulse --upgrade
```

### 方法 3: uv tool を使用したインストール（グローバル CLI、推奨）

`epsdk` をグローバルなコマンドラインツールとして使用したい場合、`uv tool install` が最もクリーンな方法です。epsdk は独立したツール環境で動作し、プロジェクト環境を汚染しません。

```bash
# インストール（.venv をアクティブ化する必要なく、epsdk をすぐに使用可能）
uv tool install ErisPulse

# アップグレード（または `epsdk self-update` を直接実行すると、このプロセスが自動的に実行されます）
uv tool upgrade ErisPulse
```

> [!NOTE]
> ツール環境内の `epsdk` は、プロジェクトディレクトリ内で実行された際に、自動的にプロジェクトの `.venv` を認識します。  
> `epsdk install` はコンポーネントをプロジェクト環境にインストールし、`epsdk run` はプロジェクト環境を使用してロボットを実行します。  
> フレームワーク本体はツール環境から提供され、両者は互いに干渉しません。  
> 一括インストールスクリプト（`get.erisdev.com/install.sh` / `install.ps1`）のメニューには、「グローバル CLI インストール（uv tool）」のオプションも用意されており、uv の自動インストールと手順のガイドが提供されます。

## プロジェクトの初期化とモジュールのインストール

インストールが完了したら、プロジェクトの初期化、モジュールのインストール、実行の全手順は、[5分間で始める](../quick-start.md)を参照してください。

### 方法4：ErisPulse-Appクライアントを使用する（ターミナル不要）

Python環境をインストールしたくないですか？[ErisPulse-App](../ecosystem/app.md) は公式の全プラットフォーム対応クライアントです（Android / Windows / Linux / macOS）。**スマートフォンで直接実行**でき、デスクトップ版はシステムトレイに最小化して常駐させることができます。Python実行環境とErisPulse SDKが内蔵されており、ターミナルや手動設定は不要です。

- [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) から、プラットフォームに応じてダウンロードを選択してください（Android `online`/`offline` APK、Windows `setup.exe`/`zip`、Linux `tar.gz`、macOS `zip`）
- App内でインスタンスを作成して起動し、ネイティブのインターフェースでアダプタとモジュールを管理し、モジュールストアを閲覧します

> 詳細な説明は、[ErisPulse-Appのインストールと使用方法](../ecosystem/app.md)をご覧ください。

## インストールの確認

### インストールの確認

```bash
# ErisPulse のバージョンを確認
epsdk --version
```

### テストの実行

```bash
# プロジェクトを実行
epsdk run main.py
```

上記のような出力が表示された場合、インストールが正常に完了しています。

```
[INFO] ErisPulse の初期化を開始しています...
[INFO] アダプタをロードしました: Yunhu
[INFO] モジュールをロードしました: MyModule
[INFO] ErisPulse の初期化が完了しました
```

## よくある質問

### インストールに失敗する場合

1. Pythonのバージョンがサポート範囲内か確認してください（3.10 ～ 3.14 をサポート。3.14t のフリースレッド / GIL フリービルドは実験的サポートであり、正式な保証はありません）
2. `pip install` の代わりに `uv pip install ErisPulse` を試してください
3. 権限エラーが表示される場合は、`pip install --user ErisPulse` を試すか、仮想環境を使用してください
4. 企業プロキシ環境でSSL証明書エラーが発生する場合は、`pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse` を試してください
5. ネットワーク接続が正常で、pip のパッケージソースにアクセスできることを確認してください

### 設定エラー

1. `config.toml` の構文が正しいか確認してください（TOML形式はインデントや引用符に敏感です）
2. 必須の設定項目がすべて記入されていることを確認してください
3. ターミナルのログで詳細なエラー情報を確認してください
4. `epsdk init` を使用して設定ファイルを再生成してください

### モジュールのインストールに失敗する場合

1. モジュール名のスペルが正しいか確認してください（大文字・小文字は区別されます）
2. ネットワーク接続を確認してください
3. `epsdk list-remote` で利用可能なモジュール一覧を確認してください
4. モジュールが現在使用中の SDK バージョンと互換性があることを確認してください

### Windows PowerShell の実行ポリシー

PowerShell で「このシステムではスクリプトの実行が無効になっているため、ファイルを読み込むことができません」というようなメッセージが表示される場合：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Debian/Ubuntu での仮想環境作成の失敗

インストールスクリプトが「仮想環境の作成に失敗しました」というメッセージを表示し、エラー情報に `ensurepip is not available` が含まれている場合、Debian/Ubuntu ではデフォルトで `python3-venv` がインストールされていないことが原因です（システムの Python では `ensurepip` が無効化されています）：

```bash
sudo apt install python3.13-venv   # 実際の Python バージョンに対応するパッケージをインストール
# または汎用メタパッケージをインストール：
sudo apt install python3-venv
```

インストール後、インストールスクリプトを再実行してください。最新のインストールスクリプトは、この問題を検出すると自動的に確認を行い、対応するシステムパッケージのインストールを試みます。また、uv を使用することもできます（`uv venv` は `ensurepip` に依存しません）。

## 次のステップ

- **インストール後にプロジェクトを初期化し、アダプターをインストールする**：[5分クイックスタート](../quick-start.md) に沿って残りの手順を完了しましょう
- **日常的にコマンドラインでコンポーネントを管理する**：[CLI コマンドリファレンス](cli-reference.md) を参照
- **トークンの設定やポートの調整**：[設定ファイルの説明](configuration.md) をご覧ください

## 部署

> 来源: `docs/ja/user-guide/deployment.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/user-guide/deployment.md）

# 部署ガイド

> [!TIP]
> **このドキュメントを読むべきタイミング**：ロボットを長期間稼働させる場合に必要です。Dockerでのデプロイ、systemd / Supervisorによるプロセス監視、リバースプロキシとSSL、バックアップとアップグレードはすべてここに記載されています。ローカル開発やデバッグの段階では不要です。

ロボットの開発が完了したのは始まりに過ぎません。このドキュメントでは、サーバー上で安定して稼働させるために必要な3つのデプロイ方法（Docker / systemd / Supervisor）、およびリバースプロキシ、セキュリティ強化、バックアップについて説明します。

## Docker 部署（推奨）

ErisPulse は公式の Docker イメージを提供しており、ErisPulse フレームワークと Dashboard 管理パネルが内蔵されており、`linux/amd64` および `linux/arm64` アーキテクチャをサポートしています。

### 速攻起動

```bash
# イメージを取得
docker pull erispulse/erispulse:latest

# docker-compose.yml をダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboard のログイントークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

起動後、`http://localhost:8000/Dashboard` にアクセスし、設定したトークンをパスワードとしてログインします。

### 国内用のイメージ加速

Docker Hub にアクセスできない場合は、GitHub Container Registry を使用してイメージを取得できます：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

ghcr.io のイメージを使用する場合、`docker-compose.yml` の `image` を変更する必要があります：

```yaml
services:
  erispulse:
    image: ghcr.io/erispulse/erispulse:latest
```

### docker-compose.yml

```yaml
services:
  erispulse:
    image: erispulse/erispulse:${ERISPULSE_TAG:-latest}
    container_name: ${CONTAINER_NAME:-erispulse}
    ports:
      - "${ERISPULSE_PORT:-8000}:8000"
    volumes:
      - ./config:/app/config
      # 永続化 Python パッケージディレクトリ
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - LANG=${LANG:-en_US.UTF-8}
      - ERISPULSE_LANG=${ERISPULSE_LANG:-}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    init: true
    # シグナル処理による優雅な停止（SIGTERM）、ここでは停止の猶予期間のみ制御
    stop_grace_period: 30s
    restart: on-failure:5
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

> 以上はリポジトリのルートにある [docker-compose.yml](https://github.com/ErisPulse/ErisPulse/blob/main/docker-compose.yml) と同一です（リポジトリのバージョンには、イメージ加速と環境変数に関する注釈が追加されています）。直接ダウンロードして使用することを推奨します。

### 環境変数

| 変数 | デフォルト値 | 説明 |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Dashboard のポートマッピング |
| `ERISPULSE_TAG` | `latest` | イメージタグ（バージョンを固定したい場合は具体的なバージョン番号を指定） |
| `CONTAINER_NAME` | `erispulse` | コンテナ名（複数インスタンスを展開する場合、インスタンスを識別） |
| `ERISPULSE_DASHBOARD_TOKEN` | 自動生成 | Dashboard のログイントークン（強く設定することを推奨） |
| `TZ` | `Asia/Shanghai` | タイムゾーン |
| `LANG` | `en_US.UTF-8` | システム言語、起動時のインターフェース言語を自動検出 |
| `ERISPULSE_LANG` | 空 | 起動時のインターフェース言語を強制指定：`zh` / `zh_TW` / `en` / `ja` / `ru`（`LANG` を上書き） |

### データの永続化

`./config` ディレクトリは設定ファイルとデータベースをマウントしており、以下の内容を含みます：

- `config/config.toml` — 設定ファイル
- `config/config.db` — SQLite によるデータベース
- `config/.packages` — Python site-packages の永続化ボリューム、フレームワーク、アダプター、およびインストールされたモジュールを保存（最初の起動時にエントリーポイントがイメージ内に含まれるバックアップから自動的に初期化され、以降のモジュールのインストールやフレームワークのホットアップデートはこのディレクトリに書き込まれます）

> **フレームワークのアップグレード（pre/rc 含む）とイメージの自己修復**：エントリーポイントは、コンテナの起動時に毎回コアパッケージの整合性を自己チェックし、破損した場合は「ユーザーがインストールしたバージョンを優先」する原則で修復します。永続ボリューム内に明示的にインストールまたはアップグレードされたバージョン（例：Dashboard でインストールした pre バージョン）は、PyPI から**同じバージョンを再インストール**し、静かにイメージ内に含まれるバージョンにロールバックすることはありません。したがって、Dashboard でフレームワークをアップグレードした後、任意回のコンテナ再起動でも目標バージョンが維持されます。

## Dashboard 管理パネル

ErisPulse Docker イメージには、Web 可視化管理インターフェースを提供する Dashboard モジュールが内蔵されています。

### 機能概要

| 機能 | 説明 |
|------|------|
| ダッシュボード | システム概要、CPU/メモリ監視、実行時間、イベント統計 |
| ロボット管理 | 各プラットフォームのロボットのオンライン状態と情報を表示 |
| イベントの表示 | 実時イベントストリーム、タイプとプラットフォームでフィルタリング可能 |
| ログの表示 | モジュールとレベルでフィルタリングされたログビューアー |
| モジュール管理 | インストールされたモジュールとアダプタを表示、ロード、アンロード |
| モジュールストア | リモートで利用可能なパッケージを閲覧し、ワンクリックでインストール |
| 設定編集 | `config.toml` のオンライン編集 |
| ストレージ管理 | Key-Value ストレージデータの閲覧と編集 |
| バックアップ | 設定とストレージデータのエクスポート/インポート |
| 審計ログ | すべての管理操作を記録 |

### Dashboard からモジュールをインストール

Dashboard にはモジュールストア機能が統合されており、以下の方法でモジュールをインストールできます：

1. **ストアからインストール**：リモートのモジュールリストを閲覧し、必要なモジュールをワンクリックでインストール
2. **ローカルパッケージのアップロード**：`.whl` または `.zip` ファイルを直接アップロードしてインストールし、開発中のモジュールをテストするのに便利です

> **モジュール開発者の高速テストフロー**：Docker 部署後、Dashboard の「ローカルパッケージのアップロード」機能を使って、ビルドした `.whl` ファイルを直接アップロードしてテストできます。コンテナの手動操作は不要です。

## プロセス監督とハードリスタート

ErisPulse のハードリスタート（`sdk.hard_restart()`）は、**外部監督者**がプロセスの終了コードが 42 のときにプロセスを再起動することに依存しています。SDK 自身は新しいプロセスを起動しません。本番環境では監督者の設定が必須です。監督者が設定されていない場合、ハードリスタート後にプロセスは自動的に復帰しません：

- Docker：公式の compose では `restart: on-failure:5` を使用しています。これは、非ゼロの終了コードでプロセスを再起動します（ハードリスタートの終了コード 42 を上書きします）。連続5回の上限は、無限ループを防ぐためです。再起動回数を無制限にしたい場合は、`unless-stopped` に変更してください。
- systemd：`Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord：42 を再起動可能な終了コードに追加します。
- 純粋な Python によるカスタム監督者：`Popen` のループ + `returncode == 42` の検出

各監督者の完全な設定例と終了コード 42 の契約内容については、[起動プロセス → 監督者ガイド](../advanced/startup.md#監督者ガイド)をご覧ください。

## ヘルスチェック

SDK には、ヘルスチェック用エンドポイントが内蔵されています：

```bash
# ヘルスチェック
curl http://localhost:8000/health
```

公式の docker-compose.yml には、以下のヘルスチェックが既に内蔵されています。独自の compose ファイルを作成する際には、こちらを参考にしてください：

```yaml
services:
  erispulse:
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

## リバースプロキシ

Nginx などのリバースプロキシを使用して Dashboard を公開する必要がある場合：

```nginx
server {
    listen 80;
    server_name bot.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket 支援（Dashboard の実時イベントストリームが必要）
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

SSL には Let's Encrypt を使用できます：

```bash
sudo certbot --nginx -d bot.example.com
```

## 手動デプロイ（pip）

Docker を使用しない場合、手動でデプロイすることも可能です。

### 本番環境の設定

```toml
# config/config.toml

[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"
log_files = ["app.log"]
memory_limit = 5000

[ErisPulse.framework]
enable_lazy_loading = true
```

### systemd (Linux)

`/etc/systemd/system/erispulse-bot.service` を作成：

```ini
[Unit]
Description=ErisPulse Bot
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/opt/erispulse-bot
ExecStart=/opt/erispulse-bot/venv/bin/epsdk run main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

管理：

```bash
sudo systemctl daemon-reload
sudo systemctl start erispulse-bot
sudo systemctl enable erispulse-bot
sudo journalctl -u erispulse-bot -f
```

### Supervisor

`/etc/supervisor/conf.d/erispulse-bot.conf` を作成：

```ini
[program:erispulse-bot]
command=/opt/erispulse-bot/venv/bin/python -m ErisPulse run main.py
directory=/opt/erispulse-bot
user=bot
autostart=true
autorestart=true
stderr_logfile=/var/log/erispulse-bot/err.log
stdout_logfile=/var/log/erispulse-bot/out.log
```

### uv tool による分離デプロイ（CLI とプロジェクト環境の分離）

`uv tool install` は `epsdk` を**独立したツール環境**としてインストールし、CLI 自身とプロジェクト依存関係を完全に分離します：CLI のアップグレードはプロジェクトの `.venv` に影響を与えず、プロジェクトの依存関係の変更も CLI に影響を与えません。

```bash
# 1. グローバルに CLI をインストール（自動的に epsdk / ep コマンドを公開）
uv tool install ErisPulse

# 2. プロジェクト内にロボットの依存関係のみを配置（.venv は uv で管理）
cd /opt/erispulse-bot
uv add erispulse ErisPulse-Adapter-Yunhu   # 必要に応じてアダプタを追加

# 3. CLI を使用して実行（プロジェクトの .venv に含まれる解釈子を自動的に検出）
epsdk run main.py
```

動作の要点：

- `epsdk run` の対象解釈子の検出順序：`ERISPULSE_PYTHON` 環境変数 → プロジェクトの `.venv` → 現在の解釈子；ツール環境自体は CLI にのみ対応し、コンポーネント（アダプタ/モジュール）はプロジェクトの `.venv` にインストールする必要があります
- `epsdk install` / `uninstall` / `upgrade` / `list` はすべてプロジェクトの `.venv` に作用し、ツール環境を汚染しません
- CLI のアップグレード：`uv tool upgrade ErisPulse`（または `epsdk self-update` を直接実行し、uv tool 環境では自動的に `uv tool upgrade` に切り替わります）；プロジェクトの依存関係のアップグレード：プロジェクトディレクトリ内で `uv sync` / `uv add` を実行し、互いに影響しません
- サーバー環境では、ツール環境は uv で統一管理されます（`uv tool list` で確認、`uv tool upgrade --all` で一括アップグレード）；グローバルな pip パッケージの手動管理は不要です
- プロジェクトのないディレクトリで `uv run epsdk ...` を実行した場合、一時的な隔離環境に移行し、インストールされたコンポーネントは永続化されません；サーバーでは常に `epsdk` を直接呼び出すか、まず `cd` でプロジェクトディレクトリに移動してください

## セキュリティに関する推奨事項

1. **Dashboard トークンの設定**：強力なランダムなトークンを使用し、デフォルト値は使用しないでください。
2. **ポートをインターネットに公開しない**：リバースプロキシ + SSL を使用しない限り、Dashboard のポートをローカルネットワーク内に限定してください。
3. **データディレクトリを保護する**：`config/` ディレクトリには設定とデータベースが含まれているため、適切なファイル権限を設定してください。
4. **定期的なアップデート**：`epsdk self-update` を使用するか、最新の Docker イメージを取得してください。
5. **root で実行しない**：手動でデプロイする場合は、専用のユーザーを作成してください。
6. **Docker の再起動ポリシーを使用する**：公式の compose では `restart: on-failure:5` が設定されており、エラー終了（ハードリスタート終了コード 42 を含む）後に自動的に再起動されます。

## 複数インスタンスのデプロイ

複数のロボットインスタンスを実行する場合：

1. 各インスタンスは独立したプロジェクトディレクトリと `docker-compose.yml` を使用する
2. 異なるポート番号を使用する：`ERISPULSE_PORT=8001`
3. 異なるコンテナ名を使用する：`container_name: erispulse-bot2`

## 更新とメンテナンス

### Docker 方式

```bash
# 最新のイメージを取得
docker compose pull

# 新しいイメージを使用して再起動
docker compose up -d
```

### pip 方式

```bash
epsdk self-update
epsdk upgrade
```

### uv tool 方式

```bash
# CLI ツール環境をアップグレード
uv tool upgrade ErisPulse

# プロジェクト依存関係のアップグレード（プロジェクトディレクトリ内で実行）
uv sync
```

### 実行時ホットリロードでサーバーの設定を再読み込み

リスニングアドレス / ポート / SSL 証明書を変更した後、プロセスを再起動せずに実行できます。任意のコルーチン内で `router.reload()` を呼び出します：

```python
await sdk.router.reload(port=9000)                                # ポートを変更
await sdk.router.reload(ssl_cert=new_pem, ssl_key=new_key)        # 証明書のホット交換（証明書の更新シナリオ）
await sdk.router.reload(host="0.0.0.0", port=9000)                # 省略されたパラメータは現在の設定を引き継ぐ
```

- 同じ FastAPI アプリケーションを再利用し、モジュールが登録した HTTP / WebSocket / SSE ルートはすべて保持されます
- 新しい設定（証明書の構築、ポートの利用可能）を検証してから切り替えます。失敗した場合は、古い設定でサービスを復元して `False` を返し、`False` の返却は古いサービスが利用可能であることを保証します
- サーバーが実行されていない場合は `False` を返します（最初の起動は `sdk.router.start()` を使用してください）

### バックアップ

定期的に `config/` ディレクトリをバックアップします：

```bash
# Docker 部署の場合
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# または Dashboard の「バックアップ」機能を使用してエクスポート
```

## 次に進む

- **可視化管理したい場合**：[ErisPulse-Dashboard](../ecosystem/dashboard.md) をインストールし、ブラウザ上でモジュールを管理し、ログを確認し、設定を変更します。
- **環境に問題があると疑う場合**：まず `epsdk doctor` を実行して健全性レポートを出力します。[CLI コマンドリファレンス · doctor](cli-reference.md#doctor) を参照してください。
- **フレームワークとコンポーネントの設定を調整したい場合**：[設定ファイルの説明](configuration.md)を確認してください。環境変数によるオーバーライドは特にコンテナデプロイに適しています。
