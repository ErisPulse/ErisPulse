---
name: erispulse-config-cli
description: "适用于：配置声明式 schema、排查配置问题、使用 epsdk 命令行与部署。覆盖场景：- 接続パラメータを変更した後はフレームワークを再起動して有効にする必要があります；接続プールの作成が瞬時失敗した場合は指数関数的に再試行されます。`epsdk` コマンドの引数を忘れたとき、コンポーネント管理をスクリプトに組み込みたいとき、run / stop / restart の挙動を制御したいときに参照してください。日常的に `init` / `install` / `run` しか使わないなら、これだけ覚えておけば十分です：`epsdk <コマンド> --help` でいつでも引数の説明を確認できるため、本文全体を読み通す必要はありません。**このページを読むべきタイミング**：インストール方法（pip / uv / Docker / ErisPulse-App クライアント）を選ぶ必要があるときや、インストールに失敗してトラブルシューティングが必要なときに読んでください。とにかく最速で動かしたいだけなら、[5分クイックスタート](../quick-start.md) に最短の手順がまとめられているため、不要であればスキップしてください。**このドキュメントを読むべきタイミング**：ロボットを長期間稼働させる場合に必要です。Dockerでのデプロイ、systemd / Supervisorによるプロセス監視、リバースプロキシとSSL、バックアップとアップグレードはすべてここに記載されています。ローカル開発やデバッグの段階では不要です。"
---

# ErisPulse 配置系统与 CLI 工具链

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 配置系统: 69-80 行
- 設定ファイルの位置: 82-99 行
- 設定の読み込みエラー処理: 101-122 行
- コメントの保持と最小限の書き込み: 124-133 行
- 環境変数による上書き: 135-187 行
- 設定のホットアップデート: 189-257 行
- 設定の読み取りと削除 API: 259-283 行
- 完全な設定例: 285-337 行
- サーバー設定: 339-367 行
- マスターシステム設定: 369-446 行
- ログ設定: 448-496 行
- フレームワーク設定: 498-569 行
- ストレージ設定: 571-618 行
- イベント設定: 620-647 行
- 会話受信箱設定（transcript）: 649-666 行
- 国際化設定: 668-677 行
- モジュール設定: 679-706 行
- スコープ設定（scope）: 708-753 行
- 統一イベント覆写設定（event.overrides）: 755-795 行
- 次に: 797-801 行
- CLI 参考: 803-816 行
- パッケージ管理コマンド: 818-825 行
- 診断コマンド: 827-980 行
- 情報照会コマンド: 982-1045 行
- 設定コマンド: 1047-1098 行
- 実行制御コマンド: 1100-1200 行
- プロジェクト管理コマンド: 1202-1312 行
- 言語コマンド: 1314-1349 行
- 型スタブコマンド: 1351-1390 行
- グローバルパラメータ: 1392-1405 行
- 環境診断: 1407-1448 行
- 対話式インストール: 1450-1461 行
- よくある使い方: 1463-1590 行
- 次のステップ: 1592-1596 行
- 安装: 1598-1605 行
- システム要件: 1607-1611 行
- インストール方法: 1613-1685 行
- プロジェクトの初期化とモジュールのインストール: 1687-1698 行
- インストールの確認: 1700-1723 行
- よくある質問: 1725-1767 行
- 次のステップ: 1769-1773 行
- 部署: 1775-1784 行
- Docker 部署（推奨）: 1786-1873 行
- Dashboard 管理パネル: 1875-1901 行
- プロセス監督とハードリスタート: 1903-1912 行
- ヘルスチェック: 1914-1934 行
- リバースプロキシ: 1936-1966 行
- 手動デプロイ（pip）: 1968-2059 行
- セキュリティに関する推奨事項: 2061-2068 行
- 複数インスタンスのデプロイ: 2070-2076 行
- 更新とメンテナンス: 2078-2130 行
- 次に進む: 2132-2137 行

## 配置系统

> 来源: `docs/ja/user-guide/configuration.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/user-guide/configuration.md）

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
| uninit_timeout | integer | 30 | エレガントシャットダウンの合計タイムアウト時間（秒）、超えると強制終了。0はタイムアウトを設定しない |
| strict_mode | integer | 0 | ストリクトモードのレベル、下記の「ストリクトモード」を参照 |
| handler_max_concurrency | integer | 64 | イベントハンドラの最大並行タスク数、大きくすると処理能力は向上するがメモリ使用量も増える |
| handler_queue_max_pending | integer | 4096 | イベントのバースト時のキューのバックプレッシャー：1プラットフォームの待機中のハンドラタスク数の上限、超えると新しいイベントのハンドラタスクは即座に破棄され、WARNINGが記録されます（破棄件数はトラブルシューティングで確認可能）；`0`は制限なし |
| offline_bot_expiry | integer | 3600 | オフラインBotの記録の自動有効期限（秒）、0は期限切れにならない |
| plugins_dir | string / list | "plugins" | 本地プラグインのフォルダ（プロジェクトルートからの相対パス）；プラグインファイルの追加/削除/変更はホットリロードのwatcherが自動的に検出します |
| watch_ignore_dirs | list | 内部リスト | ホットリロードのファイル監視で無視するディレクトリ名（`.venv`/`.git`/`__pycache__`等）；空のリストは**内部リストを全体的に置換**し、`[]`はどのディレクトリも無視しない |
| watch_include_plugin_dirs | boolean | true | `epsdk run --reload` でプラグインのディレクトリをプラグインのホットリロードのwatcherに正確に処理させ、全量監視から除外するか |

### アクティブGC設定

SDKの初期化後にアクティブGCのバックグラウンドタスクが起動し、周期的にPythonのGCと内部リソースの回収（オフラインBotのクリアなど）を行います。すべてのパラメータはホットアップデートが可能で、変更時に即座にタスクを再起動します。

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | 回収間隔（秒）、小数もサポート。0はアクティブGCを無効化 |
| proactive_gc_generation | integer | 0 | 通常のラウンドの回収世代（0/1/2、0..2に制限）。`gc.collect(2)`は全量回収に相当し、デフォルトでは0で軽量に保たれる。深い回収は`proactive_gc_full_every`で周期的にトリガーされる |
| proactive_gc_full_every | integer | 20 | Nラウンドごとに全量回収を行う、0は周期的全量回収を無効化。全量回収は`proactive_gc_memory_growth_mb`のしきい値に制約される |
| proactive_gc_memory_growth_mb | integer | 32 | 全量回収のメモリ増加しきい値（MB）：前回の全量回収後のメモリベースライン（優先 tracemalloc、次に RSS）と比較し、この値に達した場合に全量回収が実行される。0はしきい値を設定しない |
| proactive_gc_idle_only | boolean | false | 有効にすると、イベントのバースト（未完了のpending handlerがある）時はこのラウンドはPython GCをスキップし、メッセージ処理との競合を避ける；内部リソースの回収は影響を受けない |
| proactive_gc_gen0_min | integer | 500 | 通常のラウンドで回収をトリガーするgen0のガベージ量の下限：`gc.get_count()[0]`がこの値を下回ると空回りのラウンドはスキップされる（空回りのラウンドはほぼゼロコスト）。0は常に回収する |

> **2.7.1 変更**：デフォルト `proactive_gc_generation` は `2` から `0` に調整され、`proactive_gc_full_every` は `0` から `20` に調整されました。以前は `generation=2` は毎ラウンド最も重い全量回収を意味しました；新しいデフォルトは回収のカバレッジを保ちながら空回りのオーバーヘッドを大幅に削減します。明示的に設定された旧値はそのままの意味で有効です。

### ストリクトモード

ストリクトモードは、モジュール/アダプタがロード段階で不正な状態や失敗した場合の処理戦略を制御します。モダンなモジュール/アダプタは `BaseModule`/`BaseAdapter` の基底クラスを継承する必要があります。基底クラスを継承していないコンポーネントはフレームワークのコンテキストシステムと兜底クリーンアップに影響を与え、リソースのリークを引き起こす可能性があります。

> **2.5.2 変更**：デフォルトレベルは `1`（スキップ）から `0`（緩和）に調整され、新規ユーザーが初めて使用する際のロード問題を減らしました。基底クラスを継承していないコンポーネントは警告として表示され、ロードされます。以前の動作を復元するには、`strict_mode = 1` を明示的に設定してください。

| レベル | 名称 | 行動 |
|------|------|------|
| 0 | 緩和（デフォルト） | 不正な設定は警告のみ、基底クラスを継承していないコンポーネントもロードされます（旧コンポーネントの互換性） |
| 1 | ストリクト-スキップ | 基底クラスを継承していないコンポーネントは拒否してスキップし、他のコンポーネントは正常に起動します |
| 2 | ストリクト-致命 | すべての不正な設定を収集して統一的に報告し、起動を中止します |

各レベルで、**「ロード/登録/初期化段階でのエラー」**というコンポーネント自身のクラッシュは常にスキップされます。違いは以下の通りです：

- **0 → 1**：唯一の動作変化は「基底クラスを継承していない」が「ロードされる」から「スキップされる」に変わる点です。
- **1 → 2**：すべての不正（基底クラスを継承していない、ロード失敗、登録失敗、初期化失敗など）が致命的になり、起動チェックポイントで一括して不正リストを出力して起動を中止します。

#### 豁免リスト

もし特定のコンポーネントが一時的に移行できない（例：依存する旧モジュールなど）場合、それらを豁免リストに追加することで、不正な設定でも緩和モードでロードされます：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> あるコンポーネントがストリクトモードで拒否された場合、ログにはどのように再びロードを回復するか（豁免リストに追加するか、レベルを下げること）が明確に示されます。

#### CLIとの連携

`epsdk run` の起動前の自己検査（設定ファイルの解析性、コンポーネントの必須設定の完全性）はデフォルトで本設定に従います：0でない場合、検査失敗で起動を拒否し、0の場合は警告を出して継続します。設定を変更せずに一時的に切り替えることもできます：`epsdk run --strict` は今回の起動で自己検査とストリクトレベルを同時に有効にします（レベルは下げず、`ERISPULSE_FRAMEWORK_STRICT_MODE` 環境変数で実行プロセスに伝達される）、`--no-strict` は今回の起動で一時的に緩和モードにし、警告のみ出力します。

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
| case_sensitive | boolean | true | 大文字小文字を区別するかどうか（`/Help` と `/help` が異なるコマンドかどうか） |
| allow_space_prefix | boolean | false | スペースをプレフィックスとして許可するかどうか |
| must_at_bot | boolean | false | コマンドをトリガーするには@botが必要かどうか（プライベートチャットは制限されない） |

### メッセージ設定

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| ignore_self | boolean | true | 自分自身のメッセージを無視するかどうか |

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

## CLI 参考

> 来源: `docs/ja/user-guide/cli-reference.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/user-guide/cli-reference.md）

# CLI コマンドリファレンス

> [!TIP]
> **いつこのドキュメントを読むべきか**：`epsdk` コマンドの引数を忘れたとき、コンポーネント管理をスクリプトに組み込みたいとき、run / stop / restart の挙動を制御したいときに参照してください。日常的に `init` / `install` / `run` しか使わないなら、これだけ覚えておけば十分です：`epsdk <コマンド> --help` でいつでも引数の説明を確認できるため、本文全体を読み通す必要はありません。

`epsdk` は ErisPulse のコマンドラインツールです。プロジェクトの初期化、モジュールとアダプターのインストール / アップグレード、コンポーネントの対話式設定、ボットの実行と停止、環境の診断が、この一つのコマンドで行えます。

> **ヒント**：`epsdk`（コマンドなし）のメインヘルプはカテゴリ別にグループ化して表示されます：**プロジェクト**（init / create / run）、**コンポーネント管理**（install / uninstall / upgrade / list / list-remote / types）、**設定と診断**（config / doctor / i18n）、**その他**（self-update / version）。

---

## パッケージ管理コマンド

| コマンド | エイリアス | パラメータ | 説明 |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | モジュール/アダプターのインストール |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | モジュール/アダプターのアンインストール |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | 指定モジュールまたはすべてをアップグレード |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | SDK 自体を更新 |

## 診断コマンド

| コマンド | エイリアス | パラメータ | 説明 |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose] [--fix]` | 環境を診断してヘルスレポートを出力。`--fix` で自動修復を試みる |

### install

ErisPulse モジュールまたはアダプターパッケージをインストールします。パッケージ名を指定しない場合は対話式インストール画面に入ります。

**エイリアス：** `i`, `add`

> **uv プロジェクト連携**（2.11.1+）：uv が管理するプロジェクト内（`uv.lock` または `[tool.uv]` が存在する場合）では、
> `install` / `upgrade` / `uninstall` は自動的に `uv add` / `uv remove` に切り替わります——依存関係は
> `pyproject.toml` と `uv.lock` に同時に書き込まれ、`uv sync` で epsdk がインストールしたコンポーネントが消えることはなくなります。失敗した場合は自動的に
> uv pip / pip 経路へフォールバックします。`--user` など uv が対応していない引数は直接 pip を使用します。ターゲット環境の解決順序：
> `ERISPULSE_PYTHON` → `UV_PROJECT_ENVIRONMENT` → プロジェクトの `.venv` → `UV_PYTHON` →
> `VIRTUAL_ENV` → 現在のインタープリター（完全な判断チェーンは `epsdk doctor` で確認できます）。

**パラメータ：**

| パラメータ | 短縮形 | 説明 |
|------|--------|------|
| `[package]...` | | インストールするパッケージ名、複数指定可 |
| `--upgrade` | `-U` | インストール時に最新バージョンへアップグレード |
| `--pre` | | プレリリース版のインストールを許可 |
| `--editable` | `-e` | 編集可能モードでインストール（パス指定が必要） |
| `--user` | | ユーザーの site-packages ディレクトリにインストール |
| `--no-deps` | | 依存関係をインストールしない |
| `--target` | `-t` | 指定ディレクトリにインストール |
| `--index-url` | | PyPI ミラーソースのアドレスを指定 |
| `--extra-index-url` | | 追加の PyPI ミラーソースアドレス（複数回指定可） |
| `--no-cache-dir` | | キャッシュを無効化 |
| `--requirement` | `-r` | requirements ファイルからインストール |
| `--constraint` | `-c` | 制約ファイルからインストール |
| `--force-reinstall` | | 強制的に再インストール |
| `--ignore-installed` | | インストール済みパッケージを無視 |
| `--compile` | | インストール後に .pyc ファイルをコンパイル |
| `--no-compile` | | インストール後に .pyc ファイルをコンパイルしない |
| `--prefix` | | 指定プレフィックスディレクトリにインストール |
| `--src` | | 編集可能インストール時に使用するソースディレクトリ |
| `--config-settings` | | ビルドバックエンドに渡す設定（複数回指定可） |
| `--no-binary` | | バイナリパッケージを使用しないよう制限（形式例 `:all:`） |
| `--only-binary` | | バイナリパッケージのみ使用に制限（形式例 `:all:`） |
| `--prefer-binary` | | バイナリパッケージを優先 |
| `--build-isolation` | | ビルド分離を有効化 |
| `--no-build-isolation` | | ビルド分離を無効化 |
| `--upgrade-strategy` | | アップグレード戦略：`eager`、`only-if-needed`、`to-satisfy-only` |
| `--break-system-packages` | | システムパッケージマネージャーが管理する Python パッケージの変更を許可 |
| `--no-uv` | | uv の代わりに pip を使用 |

**例：**

```bash
# 単一モジュールをインストール
epsdk install Weather

# 複数モジュールをインストール
epsdk install Yunhu Weather

# ミラーソースからインストールしてアップグレード
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 編集可能モードでインストール（開発モード）
epsdk install -e ./my-adapter
```

### uninstall

インストール済みの ErisPulse モジュールまたはアダプターパッケージをアンインストールします。パッケージ名を指定しない場合は対話式アンインストール画面に入ります。

**エイリアス：** `rm`, `remove`

**パラメータ：**

| パラメータ | 説明 |
|------|------|
| `<package>...` | アンインストールするパッケージ名、複数指定可 |
| `--no-uv` | uv の代わりに pip を使用 |

**例：**

```bash
# 単一モジュールをアンインストール
epsdk uninstall Weather

# 複数モジュールをアンインストール
epsdk uninstall Yunhu Weather
```

### upgrade

インストール済みの ErisPulse コンポーネントをアップグレードします。パッケージ名を指定しない場合は対話式ですべてをアップグレードします。

**エイリアス：** `up`

**パラメータ：**

| パラメータ | 短縮形 | 説明 |
|------|--------|------|
| `[package]...` | | アップグレードするパッケージ名、複数指定可 |
| `--force` | `-f` | 確認をスキップして強制アップグレード |
| `--pre` | | プレリリース版へのアップグレードを許可 |
| `--no-uv` | | uv の代わりに pip を使用 |

**例：**

```bash
# すべてのパッケージをアップグレード
epsdk upgrade

# 指定したパッケージをアップグレード
epsdk upgrade Weather

# 強制アップグレード（確認をスキップ）
epsdk upgrade -f
```

### self-update

ErisPulse SDK 自体を最新バージョンに更新します。

**エイリアス：** `su`, `update`

**パラメータ：**

| パラメータ | 短縮形 | 説明 |
|------|--------|------|
| `[version]` | | 更新先のターゲットバージョン番号を指定 |
| `--pre` | | プレリリース版への更新を許可 |
| `--force` | `-f` | 確認をスキップして強制更新 |
| `--no-uv` | | uv の代わりに pip を使用 |

**例：**

```bash
# 最新安定版に更新
epsdk self-update

# 指定したバージョンに更新
epsdk self-update 1.2.3

# プレリリース版を許可
epsdk self-update --pre

# 強制更新
epsdk self-update -f
```

> [!NOTE]
> `uv tool install ErisPulse` でインストールした場合、このコマンドは自動的に `uv tool upgrade ErisPulse` に切り替わります（バージョン指定時は `uv tool install ErisPulse==<バージョン> --force`）。pip で直接ツール環境をアップグレードすると、uv のマニフェスト復元によって消されてしまいます。
> Windows での更新は新しいコンソールウィンドウで行われます：現在の CLI はツール環境ファイルの占有を解除するため先に終了する必要があり、ウィンドウに完了の表示が出たらターミナルを開き直してください。

---

## 情報照会コマンド

| コマンド | エイリアス | パラメータ | 説明 |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | インストール済みコンポーネントの一覧表示 |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | リモートで利用可能なコンポーネントの一覧表示 |
| `version` | `ver` | | SDK と Python のバージョン情報を表示（`-V` と同等） |

### list

インストール済みの ErisPulse モジュールとアダプターを一覧表示します。

**エイリアス：** `l`, `ls`

**パラメータ：**

| パラメータ | 短縮形 | 説明 |
|------|--------|------|
| `--type` | `-t` | タイプを指定：`modules`、`adapters`、`all`（デフォルト） |
| `--outdated` | `-o` | アップグレード可能なパッケージのみ表示 |

**例：**

```bash
# インストール済みのすべてのコンポーネントを一覧表示
epsdk list

# モジュールのみ一覧表示
epsdk list -t modules

# アダプターのみ一覧表示
epsdk list -t adapters

# アップグレード可能なパッケージのみ表示
epsdk list -o
```

### list-remote

リモートリポジトリで利用可能な ErisPulse モジュールとアダプターを一覧表示します。

**エイリアス：** `lsr`

**パラメータ：**

| パラメータ | 短縮形 | 説明 |
|------|--------|------|
| `--type` | `-t` | タイプを指定：`modules`、`adapters`、`all`（デフォルト） |
| `--refresh` | `-r` | リモートパッケージリストのキャッシュを強制更新 |

**例：**

```bash
# リモートで利用可能なすべてのコンポーネントを一覧表示
epsdk list-remote

# リモートモジュールのみ一覧表示
epsdk list-remote -t modules

# キャッシュを強制更新してから一覧表示
epsdk list-remote -r
```

---

## 設定コマンド

| コマンド | エイリアス | パラメータ | 説明 |
|------|------|------|------|
| `config` | `cfg`, `conf` | `[name] [--list/-l] [--json]` | アダプター/モジュールの宣言的設定項目を対話式で設定 |

### config

アダプター/モジュールの宣言的設定項目を対話式で入力します。ウィザードはアダプター/モジュールが宣言する設定クラス（`ConfigClass` / `AccountConfigClass`）によって駆動され、フォームを自動生成して検証するため、config.toml を手書きする必要はありません。

アダプターはさらにマルチアカウント（bot アカウント）管理に対応します：アカウントの追加/編集/削除、および有効/無効の切り替え。

**エイリアス：** `cfg`, `conf`

**パラメータ：**

| パラメータ | 短縮形 | 説明 |
|------|--------|------|
| `[name]` | | 対象名（アダプターのプラットフォーム名またはモジュール名）。空欄で対話選択へ |
| `--list` | `-l` | すべての対象の設定状態のみ一覧表示し、ウィザードには入りません |
| `--json` | | すべての対象とその設定状態を JSON で出力（CI / スクリプトで利用）。ウィザードには入りません |

**例：**

```bash
# すべてのアダプター/モジュールの設定状態を確認
epsdk config --list

# 設定状態を JSON で出力（CI / スクリプトで利用）
epsdk config --json

# 対話式で対象を選択して設定
epsdk config

# 指定したアダプターを直接設定
epsdk config yunhu

# 指定したモジュールを直接設定
epsdk config MyModule
```

**説明：**

- 設定状態は 4 段階に分かれます：`準備完了`（検証通過）、`要改善`（必須項目の欠落または検証失敗）、`未設定`（一度も生成されていない）、`設定なし`（対象が設定クラスを宣言していない）
- フィールド値には出所ラベルが付きます：既存の設定がある場合は `（現在:値）` と表示され、未設定の場合は schema のデフォルト値 `（デフォルト:値）` が表示されます。そのまま Enter を押せばその値が保持されます
- シークレット系フィールド（`secret` 宣言）は入力時にエコー表示されず、Enter で設定済みの値が保持されます
- 対話選択モードでは、1 つのウィザード終了後に選択メニューへ戻ります（状態は更新済み）。複数の対象を連続して設定でき、空欄入力で終了します
- グローバルフォームの検証に失敗して再入力を中止した場合、そのウィザードは中断され、いかなる設定も書き込まれません（「有効化されているが設定が不完全」な中途半端な状態の発生を回避）
- 保存後、直ちに `config/config.toml` に書き込まれ、Dashboard と実行中の SDK のどちらからでも参照できます。実行中のアダプターが新しいアカウント設定を適用する必要がある場合は、プロセスを再起動するだけで反映されます
- `epsdk install`（対話式インストール）と `epsdk init` でアダプターのインストールに成功した後、設定宣言が検出された場合は自動的に本ウィザードへ誘導します。コマンドラインでパッケージ名を直接指定してインストールした場合は、設定ヒントの表示のみ行われます

---

## 実行制御コマンド

> [!TIP]
> `epsdk run` はプロジェクトディレクトリ下の `.venv` 仮想環境を自動検出してボットを実行します
> （`ERISPULSE_PYTHON` 環境変数でインタープリターを明示的に指定することも可能）。`epsdk install` /
> `uninstall` / `upgrade` / `list` も同様にプロジェクトの仮想環境に対して作用します。

| コマンド | エイリアス | パラメータ | 説明 |
|------|------|------|------|
| `run` | `r` | `[script] [--reload] [--strict/--no-strict]` | 指定スクリプトまたは SDK を実行 |
| `stop` | — | `[--force] [--pid PID]` | 実行中のインスタンスを停止（`epsdk run` で起動されたもの） |
| `restart` | — | `[--force] [--pid PID]` | 実行中のインスタンスを再起動（停止後、元の引数で再起動） |

### run

ErisPulse プロジェクトのスクリプトを実行、または SDK を直接起動します。ホットリロードモードをサポートします。

**エイリアス：** `r`

**パラメータ：**

| パラメータ | 説明 |
|------|------|
| `[script]` | 実行するスクリプトファイル。未指定の場合は SDK を実行 |
| `--reload` | ホットリロードモードを有効化：ファイル変更を監視し、自動的にコンポーネントレベルのコードホットリロードをトリガー（プロセス全体の再起動は不要）。デフォルトでは `.venv`/`.git` などのディレクトリを無視（`ErisPulse.framework.watch_ignore_dirs` で設定可能）。プラグインディレクトリはプラグイン用ホットリロード watcher が正確に処理 |
| `--strict` / `--no-strict` | 厳格モードを一時的にオン / オフ（今回のみ有効、設定には書き込まない）。デフォルトは `ErisPulse.framework.strict_mode` に従う |

**例：**

```bash
# SDK を直接実行
epsdk run

# 指定したスクリプトファイルを実行
epsdk run main.py

# ホットリロードモードで実行（ファイル変更で自動的にコードレベルのホットリロードをトリガー）
epsdk run main.py --reload

# SDK のホットリロードモード
epsdk run --reload

# 一時的な厳格モード：起動前セルフチェックに失敗したら即終了、フレームワークの厳格レベルは今回少なくとも 1 に引き上げられる
epsdk run main.py --strict

# 一時的な寛容モード（設定で strict_mode が有効だが、今回はとりあえず動かしたい場合）
epsdk run main.py --no-strict
```

**起動前セルフチェック：** `run` は起動前に、`config/config.toml` の解析可能性とインストール済みコンポーネントの必須設定の完全性を素早くチェックします。厳格さはデフォルトで `ErisPulse.framework.strict_mode` に従います（0 以外の場合はチェック失敗時に即終了、0 の場合は警告のみで続行）。設定ファイルの欠落は正常な初回起動とみなされ、通知のみで失敗とは判定されません。`--strict` で一時的に有効化：事前チェックに失敗すると即終了し、同時にフレームワークの厳格レベルは今回のみ少なくとも 1 に引き上げられます（非準拠コンポーネントをスキップ、`ERISPULSE_FRAMEWORK_STRICT_MODE` 環境変数を介して実行プロセスに伝達され、設定ファイルには書き込まれません）；`--no-strict` はその逆で、一時的に寛容レベルへ下げます。セルフチェック自体に異常が発生した場合は自動的にスキップされ、ネットワーク検出は含まれないため、起動をブロックしません。

> **`--reload` の監督構造**（2.11.1 以降）：`epsdk run --reload` は「監督プロセス + リロード worker 子プロセス」として実行されます。`.py` ファイルの保存によってトリガーされるホットリロードはすべて worker 内で完了します（排他直列実行、ストーム統合）；モジュール側の構文エラーは全体事前チェックで拒否され、旧インスタンスがサービスを継続します。`sdk.hard_restart()` が実行されると worker は終了コード 42 で終了し、監督プロセスが理由を表示した後、自動的にまったく新しい worker を再起動します——フレームワーク本体をアップグレードした後、新しいコードが即座に有効になります。

### stop

実行中の ErisPulse インスタンス（`epsdk run` で起動され、同じプロジェクトディレクトリで実行されているもの）を停止します。
`run` は起動時に、監督プロセスの PID、現在のフレームワーク子プロセスの PID、元の起動コマンドを
`.erispulse/runtime.json` に書き込み、`stop` はこれに基づいてインスタンスを特定します。

**停止順序：** POSIX ではまず監督プロセスに SIGINT を送信します（Ctrl+C と同じ優雅な終了パス——
finally チェーンが自動的にフレームワーク子プロセスを終了）。タイムアウト時は段階的に SIGTERM / SIGKILL へエスカレートします。Windows には
プロセスシグナルのセマンティクスがないため、まずフレームワーク子プロセスを終了させてから監督プロセスを終了します（監督者が強制終了をクラッシュと誤判定して
再起動することを避けるため）。

**パラメータ：**

| パラメータ | 説明 |
|------|------|
| `--force` | 優雅な停止をスキップし、直接強制終了 |
| `--pid PID` | 対象プロセスの PID を直接指定（実行状態ファイルを上書き。非標準の起動方法用） |

**例：**

```bash
# 現在のプロジェクトの実行インスタンスを停止
epsdk stop

# 強制終了
epsdk stop --force
```

### restart

実行中の ErisPulse インスタンスを再起動します：`stop` のセマンティクスに従って停止した後、状態ファイルに記録された
**元の起動コマンド**で再起動します（フォアグラウンドで現在のターミナルを引き継ぎ、新しいインスタンスは新しい実行状態ファイルを書き込みます）。

**パラメータ：** `stop` と同じ（`--force` / `--pid PID`）。

**例：**

```bash
# 優雅な再起動（pip でアダプター/モジュールをアップグレードした後にコードを反映；実行中のモジュールは
# sdk.reload_module / sdk.adapter.reload によるコードレベルのホットリロードも可能で、再起動は不要）
epsdk restart
```

> [!NOTE]
> `python main.py` など `epsdk run` をバイパスする起動方法では実行状態ファイルは書き込まれません——この種の
> プロセスはシステムツールで管理するか、`epsdk stop --pid <PID>` で PID を指定してください。

---

## プロジェクト管理コマンド

| コマンド | エイリアス | パラメータ | 説明 |
|------|------|------|------|
| `init` | — | `[path] [--project-name/-n <name>] [--path <dir>] [--adapter/-a <name>] [--quick/-q] [--force/-f] [--here] [--no-uv] [--no-venv]` | ErisPulse プロジェクトの初期化 |
| `create` | — | `{module,adapter,pack} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f] [--local]` | モジュール/アダプターのスキャフォールドを作成；`pack` はローカルプラグインを公開可能なプロジェクトに変換 |

### init

新しい ErisPulse プロジェクトを初期化します。対話式モードとクイックモードに対応し、2.8.4 以降は `pyproject.toml`（依存マニフェスト）を生成、オプションでプロジェクトの `.venv` 仮想環境を作成してフレームワークとアダプターをインストールし、**任意のディレクトリ指定**にも対応します。

**パラメータ：**

| パラメータ | 短縮形 | 説明 |
|------|--------|------|
| `[path]` | | ターゲットパス（親ディレクトリを含められます、例 `../apps/mybot`。名前のみの場合は `--project-name` と同等） |
| `--project-name` | `-n` | プロジェクト名 |
| `--path` | | プロジェクトの親ディレクトリ（`-n` と組み合わせて作成場所を指定） |
| `--adapter` | `-a` | プリインストールするアダプターを事前選択（繰り返し指定またはカンマ区切り可）。指定時はアダプターの問い合わせと選択をスキップ |
| `--quick` | `-q` | クイックモード、対話式ウィザードをスキップ（デフォルトで `.venv` を作成し依存関係をインストール） |
| `--force` | `-f` | 既存の設定ファイルを強制上書き |
| `--here` | | 現在のディレクトリで初期化し、サブディレクトリを作成しない |
| `--no-uv` | | uv の代わりに pip を使用 |
| `--no-venv` | | 仮想環境の作成と依存関係のインストールをスキップ |

**例：**

```bash
# 対話式で初期化
epsdk init

# クイック初期化（現在のディレクトリに my_bot/ を作成、pyproject.toml + .venv を含む）
epsdk init -q -n my_bot

# クイック初期化とアダプターのプリインストール（非対話、スクリプト / CI シナリオ向け）
epsdk init -q -n my_bot --adapter yunhu,telegram

# 任意のディレクトリを指定して初期化（../apps/mybot）
epsdk init ../apps/mybot

# 親ディレクトリとプロジェクト名を組み合わせ
epsdk init -n my_bot --path ../apps

# 既存の設定を強制上書き
epsdk init -f

# 現在のディレクトリで初期化
epsdk init --here -n my_bot

# プロジェクト構造のみ生成し、仮想環境は作成しない
epsdk init --no-venv -n my_bot
```

init の生成物：`main.py`、`pyproject.toml`（依存マニフェスト）、`config/config.toml` + `config.full.example`、`config/ssl/`、`logs/`、`.gitignore`、`README.md`；仮想環境の作成を選択した場合は追加で `.venv` が生成され、`erispulse` と選択したアダプターがその中にインストールされます。

> [!NOTE]
> `.gitignore` はグループ化されたテンプレート：Python バイトコードとビルド成果物、仮想環境と `.env`、ツールキャッシュ、エディターとシステムファイルが含まれ、**`config/` と `logs/` のランタイムディレクトリを丸ごと除外**します——`config.toml` にはアダプターのトークンなどの機密情報が含まれるため、リポジトリへの登録は推奨されません。設定の雛形を共有する場合は `config.full.example` を使用してください。

> [!WARNING]
> **`uv run epsdk run` でボットを実行しないでください**。`uv run` は `pyproject.toml` が存在しないディレクトリで実行されると**使い捨ての分離環境**を作成します——そこで `epsdk install` によってインストールしたアダプターは永続化されません。プロジェクトディレクトリ内で `epsdk run` を使用するか（プロジェクトの `.venv` を自動使用）、先に仮想環境をアクティブ化してから実行してください。

### create

ErisPulse モジュールまたはアダプターのスキャフォールドプロジェクトを作成します；`pack` サブコマンドはローカルプラグイン（`plugins/` ディレクトリ）を公開可能な標準プロジェクトに変換します。

**パラメータ：**

| パラメータ | 短縮形 | 説明 |
|------|--------|------|
| `{module,adapter,pack}` | | 作成するタイプ：`module` / `adapter` / `pack`（プラグインをプロジェクトへ変換）|
| `--name` | `-n` | プロジェクト名（PascalCase） |
| `--description` | `-d` | プロジェクトの説明 |
| `--author` | `-a` | 作者名 |
| `--email` | `-e` | 作者のメールアドレス |
| `--homepage` | | プロジェクトのホームページ URL |
| `--output` | `-o` | 出力ディレクトリ（デフォルトは現在のディレクトリ） |
| `--force` | `-f` | 既存のディレクトリを強制上書き |
| `--local` | | ローカルプラグインを作成（`module` / `adapter` で使用可能）：`plugins/<name>/` パッケージ構造を生成、パッケージング不要のインストール |

**例：**

```bash
# 対話式で作成（タイプの選択と情報入力をガイド）
epsdk create

# Module プロジェクトを直接作成
epsdk create module -n MyModule

# ローカルプラグインを作成（プロジェクトの plugins/ ディレクトリに配置され、起動時に自動検出）
epsdk create module -n MyModule --local

# ローカルアダプタープラグインを作成（同上、パッケージング不要の開発）
epsdk create adapter -n MyAdapter --local

# Adapter プロジェクトを直接作成
epsdk create adapter -n MyAdapter

# ローカルプラグインを公開可能なプロジェクトに変換（対話でプラグインを選択 → メタ情報を補完 → 標準プロジェクトを生成）
epsdk create pack

# 完全なパラメータ
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 出力ディレクトリを指定
epsdk create module -n MyModule -o ./projects

# 既存のディレクトリを強制上書き
epsdk create module -n MyModule -f
```

---

## 言語コマンド

| コマンド | エイリアス | パラメータ | 説明 |
|------|------|------|------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | CLI の表示言語の確認または切り替え |

### i18n

現在の CLI 言語の確認、サポートされている言語の一覧表示、表示言語の切り替えを行います。引数を指定しない場合は対話式選択画面に入ります。

**エイリアス：** `language`, `lang`

**パラメータ：**

| パラメータ | 短縮形 | 説明 |
|------|--------|------|
| `[lang]` | | 切り替え先の言語コード（例：`zh-CN`、`en`、`ja`、`ru`） |
| `--list` | `-l` | サポートされているすべての言語を一覧表示 |

**例：**

```bash
# 対話式で言語を選択
epsdk i18n

# 英語に切り替え
epsdk i18n en

# 日本語に切り替え
epsdk i18n ja

# サポートされているすべての言語を一覧表示
epsdk i18n --list
```

---

## 型スタブコマンド

| コマンド | エイリアス | パラメータ | 説明 |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | IDE 補完を有効にするための型スタブファイルを生成 |

### types

インストール済みの ErisPulse モジュールとアダプターをスキャンし、それらに対して `.pyi` 型スタブファイルを生成することで、IDE で正確なコード補完と型チェックのサポートを受けられます。

**エイリアス：** `t`, `stub`

**パラメータ：**

| パラメータ | 短縮形 | 説明 |
|------|--------|------|
| `--output` | `-o` | 出力パス（デフォルトは現在のディレクトリの `ep-stubs/`） |
| `--force` | | 既存のスタブファイルを強制上書き |
| `--adapters-only` | | アダプターの型スタブのみ生成 |
| `--modules-only` | | モジュールの型スタブのみ生成 |

> **注意：** `--adapters-only` と `--modules-only` は相互に排他的で、同時に指定した場合は後者が有効になります。

**例：**

```bash
# インストール済みのすべてのモジュールとアダプターの型スタブを生成
epsdk types

# アダプターのスタブのみ生成
epsdk types --adapters-only

# 指定したディレクトリに出力
epsdk types -o ./typings

# 既存のファイルを強制上書き
epsdk types --force
```

---

## グローバルパラメータ

以下のパラメータはすべてのコマンドに適用されます：

| パラメータ | 短縮形 | 説明 |
|------|--------|------|
| `--help` | `-h` | ヘルプ情報を表示 |
| `--version` | `-V` | バージョン情報を表示 |
| `--verbose` | `-v` | 詳細出力を表示（`-vv`/`-vvv` のように重ね掛け可能） |
| `--no-color` | | カラー出力を無効化（CI / ログ収集に適する） |
| `--no-banner` | | 起動 Banner をスキップ（スクリプトからの呼び出し / CI シナリオ向け。非対話ターミナルと `ERISPULSE_NO_BANNER=1` の場合は自動的にサイレント化） |
| `--yes` | `-y` | すべての対話プロンプトを自動確認（非対話実行） |

---

## 環境診断

### doctor

> [!NOTE]
> このコマンドには ErisPulse **2.7.0+** が必要です。

現在の CLI 実行環境を診断し、ヘルスレポートを出力します。「なぜインストールできない / 接続できない」類の問題の切り分けに使用します。

| パラメータ | 説明 |
|------|------|
| `--verbose` | 詳細な診断情報を表示 |
| `--fix` | 診断後に修復可能な問題の自動修復を試みる |

**チェック項目**：
- **Python**：インタープリターのバージョンとパス
- **インストールバックエンド**：`uv` と `pip` のどちらを使用しているか
- **ターゲットインタープリター**：パッケージが実際にインストールされるターゲットの Python 環境
- **設定ファイル**：`config/config.toml` が存在するか
- **コンポーネント設定**：インストール済みコンポーネントの宣言的設定の完全性（「インストールしたのに動かない」の多くは必須項目の欠落が原因）
- **設定汚染**（2.11.1+）：過去のアップグレードで残った残留キーをスキャン（旧バージョンのランタイムがバインドしていたシャドウ状態キー、遊離した設定セクション）。検出時は通知を表示
- **PyPI 接続性**：PyPI にアクセスできるか（発見されたコンポーネント数も表示）
- **システムプロキシ**：プロキシが検出されたかどうか

**自動修復（`--fix`）**：
- `config.toml` の欠落 → 現在の言語に基づいて初期設定ファイルを生成（`init` によるプロジェクト作成と同源）
- コンポーネント設定が「要改善」 → 順番に対話式設定ウィザードを起動して必須項目を補完（非対話環境では `epsdk config <名前>` の使用を促すメッセージを表示）
- 設定汚染の残留キー → 出所を明示した上で確認後に削除（tomlclass の可逆経路、コメントと順序は保持）
- Python バージョンが低すぎる、PyPI にアクセスできないなど人手による介入が必要な問題 → 対処提案のみ出力

```bash
# 環境診断を実行
epsdk doctor

# エイリアスを使用
epsdk diag

# 診断して自動修復を試みる
epsdk doctor --fix
```

---

## 対話式インストール

`epsdk install` をパッケージ名を指定せずに実行すると、対話式インストールに入ります：

```bash
epsdk install
```

対話画面で提供される項目：
1. アダプター選択
2. モジュール選択
3. カスタムインストール

## よくある使い方

### モジュールのインストール

```bash
# 単一モジュールをインストール
epsdk install Weather

# 複数モジュールをインストール
epsdk install Yunhu Weather

# モジュールをアップグレード
epsdk install Weather -U
```

### コンポーネントの一覧表示

```bash
# すべてのコンポーネントを一覧表示
epsdk list

# アダプターのみ一覧表示
epsdk list -t adapters

# アップグレード可能なコンポーネントのみ一覧表示
epsdk list -o

# リモートで利用可能なコンポーネントを確認
epsdk list-remote
```

### コンポーネントのアンインストール

```bash
# 単一コンポーネントをアンインストール
epsdk uninstall Weather

# 複数コンポーネントをアンインストール
epsdk uninstall Yunhu Weather
```

### コンポーネントの設定

```bash
# 設定状態を確認
epsdk config --list

# 対話式で対象を選択して設定
epsdk config

# 指定したアダプターを設定
epsdk config yunhu
```

### コンポーネントのアップグレード

```bash
# すべてのコンポーネントをアップグレード
epsdk upgrade

# 指定したコンポーネントをアップグレード
epsdk upgrade Weather

# 強制アップグレード
epsdk upgrade -f
```

### プロジェクトの実行

```bash
# 通常実行
epsdk run main.py

# ホットリロードモード
epsdk run main.py --reload
```

### 言語の切り替え

```bash
# 対話式で言語を選択
epsdk i18n

# 英語に直接切り替え
epsdk i18n en

# サポートされている言語を一覧表示
epsdk i18n --list
```

### 型スタブの生成

```bash
# すべての型スタブを生成
epsdk types

# モジュールの型スタブのみ生成
epsdk types --modules-only
```

### プロジェクトの初期化

```bash
# 対話式で初期化
epsdk init

# クイック初期化
epsdk init -q -n my_bot
```

### スキャフォールドの作成

```bash
# 対話式で作成（タイプの選択と情報入力をガイド）
epsdk create

# Module プロジェクトを直接作成
epsdk create module -n MyModule

# Adapter プロジェクトを直接作成
epsdk create adapter -n MyAdapter

# 完全なパラメータ
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 既存のディレクトリを強制上書き
epsdk create module -n MyModule -f
```

## 次のステップ

- **コンポーネントをインストールしたら設定の入力が必要**：`epsdk config` の対話式ウィザードを使用するか、[設定ファイルの説明](configuration.md) で手動編集
- **コードを書いたら IDE 補完が欲しい**：`epsdk types` を実行。詳細は [型スタブ生成](../getting-started/ide-completion.md) を参照
- **ボットが動かない**：まず `epsdk doctor` で環境を診断し（[環境診断](#環境診断) を参照）、長期的なデプロイの場合は [デプロイガイド](deployment.md) を参照

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
