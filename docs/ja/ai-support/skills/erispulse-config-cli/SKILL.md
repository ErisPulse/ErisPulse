---
name: erispulse-config-cli
description: "适用于：配置声明式 schema、排查配置问题、使用 epsdk 命令行与部署。覆盖场景：- 接続パラメータを変更した後はフレームワークを再起動して有効にする必要があります；接続プールの作成が瞬時失敗した場合は指数関数的な退避で再試行されます。**このドキュメントを読むタイミング**：`epsdk` コマンドの引数を忘れてしまったとき、またはスクリプトにコンポーネント管理を組み込みたい場合、あるいは `run` / `stop` / `restart` の動作を制御したいときに参照してください。通常は `init` / `install` / `run` のみを使用する場合は、`epsdk <コマンド> --help` という1つのコマンドを覚えておくだけで十分です。いつでも引数の説明を確認できますので、このドキュメントを全文読む必要はありません。**このページを読むべきタイミング**：インストール方法（pip / uv / Docker / ErisPulse-App クライアント）を選ぶ必要があるときや、インストールに失敗してトラブルシューティングが必要なときに読んでください。とにかく最速で動かしたいだけなら、[5分クイックスタート](../quick-start.md) に最短の手順がまとめられているため、不要であればスキップしてください。**このドキュメントを読むべきタイミング**：ロボットを長期間稼働させる場合に必要です。Dockerでのデプロイ、systemd / Supervisorによるプロセス監視、リバースプロキシとSSL、バックアップとアップグレードはすべてここに記載されています。ローカル開発やデバッグの段階では不要です。"
---

# ErisPulse 配置系统与 CLI 工具链

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 配置系统

> 来源: `docs/ja/user-guide/configuration.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/user-guide/configuration.md）

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
