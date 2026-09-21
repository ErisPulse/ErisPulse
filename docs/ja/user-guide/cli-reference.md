# CLI コマンドリファレンス

ErisPulse コマンドラインツール（`epsdk`）は、プロジェクト管理とパッケージ管理機能を提供します。

> **ヒント**：すべてのコマンドは `epsdk <コマンド> --help` で詳細なパラメータ説明を確認できます。

---

## パッケージ管理コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | モジュール/アダプタのインストール |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | モジュール/アダプタのアンインストール |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | 指定されたモジュールまたはすべてをアップグレード |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | SDK 自体の更新 |

## ディアグノスティックコマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose]` | 環境を診断し、ヘルスレポートを出力 |

### install

ErisPulse モジュールまたはアダプタパッケージをインストールします。パッケージ名を指定しない場合は、対話式のインストール画面に移行します。

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
| `--index-url` | | PyPI ミラーのURLを指定 |
| `--extra-index-url` | | 追加の PyPI ミラーのURL（複数指定可能） |
| `--no-cache-dir` | | キャッシュを無効化 |
| `--requirement` | `-r` | requirements ファイルからインストール |
| `--constraint` | `-c` | 制約ファイルからインストール |
| `--force-reinstall` | | 強制的に再インストール |
| `--ignore-installed` | | 既にインストール済みのパッケージを無視 |
| `--compile` | | インストール後に .pyc ファイルをコンパイル |
| `--no-compile` | | インストール後に .pyc ファイルをコンパイルしない |
| `--prefix` | | 指定したプレフィックスディレクトリにインストール |
| `--src` | | 編集可能なインストール時に使用するソースコードディレクトリ |
| `--config-settings` | | ビルドバックエンドに渡す設定（複数指定可能） |
| `--no-binary` | | 二進数パッケージの使用を制限（形式は `:all:` のよう） |
| `--only-binary` | | 二進数パッケージのみを使用する（形式は `:all:` のよう） |
| `--prefer-binary` | | 二進数パッケージを優先 |
| `--build-isolation` | | ビルドの分離を有効化 |
| `--no-build-isolation` | | ビルドの分離を無効化 |
| `--upgrade-strategy` | | アップグレード戦略：`eager`、`only-if-needed`、`to-satisfy-only` |
| `--break-system-packages` | | システムパッケージマネージャーが管理する Python パッケージの変更を許可 |
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

インストール済みの ErisPulse モジュールまたはアダプタパッケージをアンインストールします。パッケージ名を指定しない場合は、対話式のアンインストール画面に移行します。

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

インストール済みの ErisPulse コンポーネントをアップグレードします。パッケージ名を指定しない場合は、対話式で全アップグレードを行います。

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
# すべてのパッケージをアップグレード
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
| `[version]` | | 更新するターゲットバージョン番号を指定 |
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

---

## 情報照会コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | インストール済みのコンポーネントをリスト表示 |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | リモートリポジトリに利用可能なコンポーネントをリスト表示 |

### list

インストール済みの ErisPulse モジュールとアダプタをリスト表示します。

**別名：** `l`, `ls`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--type` | `-t` | タイプを指定：`modules`、`adapters`、`all`（デフォルト） |
| `--outdated` | `-o` | アップグレード可能なパッケージのみを表示 |

**例：**

```bash
# すべてのインストール済みコンポーネントをリスト表示
epsdk list

# モジュールのみをリスト表示
epsdk list -t modules

# アダプタのみをリスト表示
epsdk list -t adapters

# アップグレード可能なパッケージのみを表示
epsdk list -o
```

### list-remote

リモートリポジトリに利用可能な ErisPulse モジュールとアダプタをリスト表示します。

**別名：** `lsr`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--type` | `-t` | タイプを指定：`modules`、`adapters`、`all`（デフォルト） |
| `--refresh` | `-r` | リモートパッケージリストのキャッシュを強制的に更新 |

**例：**

```bash
# すべてのリモート利用可能なコンポーネントをリスト表示
epsdk list-remote

# リモートのモジュールのみをリスト表示
epsdk list-remote -t modules

# キャッシュを強制的に更新してリスト表示
epsdk list-remote -r
```

---

## 設定コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `config` | `cfg`, `conf` | `[name] [--list/-l]` | 対話形式でアダプタ/モジュールの宣言的設定項目を設定 |

### config

対話形式でアダプタ/モジュールの宣言的設定項目を設定します。アダプタ/モジュールが宣言した設定クラス（`ConfigClass` / `AccountConfigClass`）によって導かれる向導が、表形式を生成し、検証を行い、config.toml を手動で書く必要がありません。

アダプタは追加の多アカウント（botアカウント）管理もサポート：アカウントの追加/編集/削除、および有効化/無効化のスイッチ。

**別名：** `cfg`, `conf`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[name]` | | ターゲット名（アダプタプラットフォーム名またはモジュール名）、空欄で対話選択に移行 |
| `--list` | `-l` | すべてのターゲットの設定状態をリスト表示し、向導には移行しない |

**例：**

```bash
# すべてのアダプタ/モジュールの設定状態を表示
epsdk config --list

# 対話選択でターゲットを設定
epsdk config

# 指定アダプタを直接設定
epsdk config yunhu

# 指定モジュールを直接設定
epsdk config MyModule
```

**説明：**

- 設定状態は4段階：`完了`（検証通過）、`未完了`（必須項目が不足または検証失敗）、`未設定`（設定が生成されていない）、`未設定`（ターゲットが設定クラスを宣言していない）
- フィールド値にはソースが付与：既存設定は `（現在:値）`、未設定時は schema のデフォルト値 `（デフォルト:値）` が表示；直接 Enter で値を保持
- `secret` として宣言されたキー型フィールドは、入力時に値を表示せず、Enter で既に設定された値を保持
- 対話選択モードでは、1つの向導が終了すると、状態が更新された選択メニューに戻り、複数ターゲットを連続して設定可能、空欄で終了
- グローバルフォームの検証が失敗し、再入力を放棄した場合、今回の向導は中止され、設定は一切書き込まれない（「有効化されているが設定が不完全」の半完成状態を避ける）
- 保存後、`config/config.toml` に即時書き込まれ、Dashboard と実行中の SDK で確認可能；実行中のアダプタが新しいアカウント設定を適用するには、プロセスを再起動する必要がある
- `epsdk install`（対話インストール）または `epsdk init` でアダプタをインストールした後、設定宣言を検出すると、自動的に本向導に誘導される；コマンドラインでパッケージ名を直接指定してインストールした場合は、設定の提示のみ表示される

---

## 実行制御コマンド

> [!TIP]
> `epsdk run` は、プロジェクトディレクトリの `.venv` 仮想環境を自動的に検出して使用してロボットを実行します
> （`ERISPULSE_PYTHON` 環境変数で解釈子を明示的に指定することも可能）。`epsdk install` /
> `uninstall` / `upgrade` / `list` もプロジェクト仮想環境に作用します。

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `run` | `r` | `[script] [--reload]` | 指定スクリプトまたは SDK を実行 |

### run

ErisPulse プロジェクトスクリプトまたは SDK を実行します。ホットリロードモードをサポートします。

**別名：** `r`

**パラメータ：**

| パラメータ | 説明 |
|------|------|
| `[script]` | 実行するスクリプトファイル、指定しない場合は SDK を実行 |
| `--reload` | ホットリロードモードを有効化、ファイル変更を監視して自動的に再起動 |

**例：**

```bash
# SDK を直接実行
epsdk run

# 指定スクリプトファイルを実行
epsdk run main.py

# ホットリロードモードで実行（ファイル変更で自動再起動）
epsdk run main.py --reload

# SDK のホットリロードモード
epsdk run --reload
```

---

## プロジェクト管理コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `init` | — | `[path] [--project-name/-n <name>] [--path <dir>] [--quick/-q] [--force/-f] [--here] [--no-uv] [--no-venv]` | ErisPulse プロジェクトを初期化 |
| `create` | — | `{module,adapter} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f]` | モジュール/アダプタのフットスタジプロジェクトを作成 |

### init

新しい ErisPulse プロジェクトを初期化します。対話形式とクイックモードをサポートし、2.8.4 以降は `pyproject.toml`（依存関係リスト）、任意のディレクトリに作成可能な `.venv` 仮想環境の生成、およびフレームワークとアダプタのインストールをサポートします。

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[path]` | | ターゲットパス（親ディレクトリを含む、例: `../apps/mybot`；純粋な名前は `--project-name` に等しい） |
| `--project-name` | `-n` | プロジェクト名 |
| `--path` | | プロジェクトの親ディレクトリ（`-n` と組み合わせて作成位置を指定） |
| `--quick` | `-q` | クイックモード、対話形式の向導をスキップ（デフォルトで `.venv` を作成し、依存関係をインストール） |
| `--force` | `-f` | 既存の設定ファイルを強制的に上書き |
| `--here` | | 現在のディレクトリで初期化し、サブディレクトリを作成しない |
| `--no-uv` | | uv の代わりに pip を使用 |
| `--no-venv` | | 仮想環境の作成と依存関係のインストールをスキップ |

**例：**

```bash
# 対話形式で初期化
epsdk init

# クイックモードで初期化（現在のディレクトリに my_bot/ を作成し、pyproject.toml + .venv を含む）
epsdk init -q -n my_bot

# 任意のディレクトリに初期化（../apps/mybot）
epsdk init ../apps/mybot

# 親ディレクトリとプロジェクト名を組み合わせて作成
epsdk init -n my_bot --path ../apps

# 既存の設定ファイルを強制的に上書き
epsdk init -f

# 現在のディレクトリで初期化
epsdk init --here -n my_bot

# プロジェクト構造のみを生成し、仮想環境を作成しない
epsdk init --no-venv -n my_bot
```

init の成果物：`main.py`、`pyproject.toml`（依存関係リスト）、`config/config.toml` + `config.full.example`、`config/ssl/`、`logs/`、`.gitignore`、`README.md`；仮想環境の作成を選択した場合は、`.venv` を生成し、`erispulse` と選択したアダプタをその中にインストールします。

> [!WARNING]
> **`uv run epsdk run` を使用してロボットを実行しないでください**。`uv run` は `pyproject.toml` がないディレクトリで実行すると**一時的な隔離環境**を作成します——その中で `epsdk install` でインストールしたアダプタは永続化されません。プロジェクトディレクトリ内で `epsdk run` を使用してください（自動的にプロジェクトの `.venv` を使用）、または仮想環境をアクティベートしてから実行してください。

### create

ErisPulse モジュールまたはアダプタのフットスタジプロジェクトを作成します。

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `{module,adapter}` | | 作成するタイプ：`module` または `adapter` |
| `--name` | `-n` | プロジェクト名（PascalCase） |
| `--description` | `-d` | プロジェクトの説明 |
| `--author` | `-a` | 作者の名前 |
| `--email` | `-e` | 作者のメールアドレス |
| `--homepage` | | プロジェクトのホームページ URL |
| `--output` | `-o` | 出力ディレクトリ（デフォルトは現在のディレクトリ） |
| `--force` | `-f` | 既存のディレクトリを強制的に上書き |
| `--local` | | ローカルプラグインを作成（`module` でのみ利用可能）：`plugins/<name>/` パッケージ構造を生成し、パッケージ化なしでインストール可能 |

**例：**

```bash
# 対話形式で作成（タイプの選択と情報を入力する向導）
epsdk create

# モジュールプロジェクトを直接作成
epsdk create module -n MyModule

# ローカルプラグインを作成（プロジェクトの plugins/ ディレクトリに配置し、起動時に自動検出、ホットリロードをサポート）
epsdk create module -n MyModule --local

# アダプタプロジェクトを直接作成
epsdk create adapter -n MyAdapter

# 完全なパラメータ
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 出力ディレクトリを指定
epsdk create module -n MyModule -o ./projects

# 既存のディレクトリを強制的に上書き
epsdk create module -n MyModule -f
```

---

## 言語コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | CLIの表示言語を確認または切り替える |

### i18n

現在の CLI 言語を確認し、利用可能な言語をリスト表示し、表示言語を切り替えます。パラメータを指定しない場合は、対話形式の選択画面に移行します。

**別名：** `language`, `lang`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[lang]` | | 切り替える言語コード（例：`zh-CN`、`en`、`ja`、`ru`） |
| `--list` | `-l` | 利用可能なすべての言語をリスト表示 |

**例：**

```bash
# 対話形式で言語を選択
epsdk i18n

# 英語に切り替える
epsdk i18n en

# 日本語に切り替える
epsdk i18n ja

# 利用可能なすべての言語をリスト表示
epsdk i18n --list
```

---

## タイプストアブコマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | IDE補完を有効にするためのタイプストアブファイルを生成 |

### types

インストール済みの ErisPulse モジュールとアダプタをスキャンし、それらの `.pyi` タイプストアブファイルを生成することで、IDE での正確なコード補完と型チェックを可能にします。

**別名：** `t`, `stub`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--output` | `-o` | 出力パス（デフォルトは現在のディレクトリの `ep-stubs/`） |
| `--force` | | 既存のストアブファイルを強制的に上書き |
| `--adapters-only` | | アダプタのタイプストアブのみを生成 |
| `--modules-only` | | モジュールのタイプストアブのみを生成 |

> **注意：** `--adapters-only` と `--modules-only` は互いに排他的で、両方指定した場合、後者（`--modules-only`）が優先されます。

**例：**

```bash
# すべてのインストール済みのモジュールとアダプタのタイプストアブを生成
epsdk types

# アダプタのストアブのみを生成
epsdk types --adapters-only

# 指定ディレクトリに出力
epsdk types -o ./typings

# 既存ファイルを強制的に上書き
epsdk types --force
```

---

## グローバルパラメータ

以下のパラメータはすべてのコマンドに適用されます：

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--help` | `-h` | ヘルプ情報を表示 |
| `--version` | `-V` | バージョン情報を表示 |
| `--verbose` | `-v` | 詳細な出力を表示（`-vv`/`-vvv` で重ねる） |
| `--no-color` | | 色付き出力を無効化（CI / ログ収集に適している） |
| `--yes` | `-y` | すべての対話式プロンプトを自動的に確認（非対話実行） |

---

## 環境診断

### doctor

> [!NOTE]
> 本コマンドは ErisPulse **2.7.0+** が必要です。

現在の CLI 実行環境を診断し、ヘルスレポートを出力します。これは「なぜインストールできない / 接続できない」類の問題を診断するのに使用します。

| パラメータ | 説明 |
|------|------|
| `--verbose` | 詳細な診断情報を表示 |

**チェック項目**：
- **Python**：解釈子のバージョンとパス
- **インストールバックエンド**：`uv` か `pip` を使用しているか
- **ターゲット解釈子**：パッケージが実際にインストールされたターゲット Python 環境
- **設定ファイル**：`config/config.toml` が存在するか
- **PyPI 通信性**：PyPI にアクセスできるか（発見されたコンポーネント数を表示）
- **システムプロキシ**：プロキシが検出されているか

```bash
# 実行環境の診断
epsdk doctor

# 別名を使用
epsdk diag
```

---

## 対話形式のインストール

`epsdk install` をパッケージ名を指定せずに実行すると、対話形式のインストールに移行します：

```bash
epsdk install
```

対話インターフェースでは以下を提供します：
1. アダプタの選択
2. モジュールの選択
3. 自定義インストール

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

### コンポーネントのリスト表示

```bash
# すべてのコンポーネントをリスト表示
epsdk list

# アダプタのみをリスト表示
epsdk list -t adapters

# アップグレード可能なコンポーネントのみをリスト表示
epsdk list -o

# リモートで利用可能なコンポーネントを表示
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

# 対話形式でターゲットを設定
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
# 普通の実行
epsdk run main.py

# ホットリロードモード
epsdk run main.py --reload
```

### 言語の切り替え

```bash
# 対話形式で言語を選択
epsdk i18n

# 直接英語に切り替える
epsdk i18n en

# 利用可能な言語をリスト表示
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

### フットスタジの作成

```bash
# 対話形式で作成（タイプの選択と情報を入力する向導）
epsdk create

# モジュールプロジェクトを直接作成
epsdk create module -n MyModule

# アダプタプロジェクトを直接作成
epsdk create adapter -n MyAdapter

# 完全なパラメータ
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 既存ディレクトリを強制的に上書き
epsdk create module -n MyModule -f
```