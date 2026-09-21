# CLIコマンドリファレンス

ErisPulseコマンドラインツール（`epsdk`）は、プロジェクト管理とパッケージ管理機能を提供します。

> **ヒント**：すべてのコマンドは `epsdk <コマンド> --help` で詳細なパラメータ説明を確認できます。

---

## パッケージ管理コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | モジュール/アダプターのインストール |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | モジュール/アダプターのアンインストール |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | 指定されたモジュールまたはすべてのアップグレード |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | SDK自体の更新 |

## ディアグノスティックコマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose]` | 環境を診断し、ヘルスレポートを出力 |

### install

ErisPulseモジュールまたはアダプターパッケージをインストールします。パッケージ名を指定しない場合は、対話形式のインストールインターフェースに入ります。

**別名:** `i`, `add`

**パラメータ:**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[package]...` | | インストールするパッケージ名、複数指定可 |
| `--upgrade` | `-U` | 最新バージョンにアップグレードしてインストール |
| `--pre` | | プレリリース版をインストール可能 |
| `--editable` | `-e` | 編集可能なモードでインストール（パスを指定） |
| `--user` | | ユーザーのsite-packagesディレクトリにインストール |
| `--no-deps` | | 依存関係をインストールしない |
| `--target` | `-t` | 指定したディレクトリにインストール |
| `--index-url` | | PyPIのミラーサーバーのURLを指定 |
| `--extra-index-url` | | 追加のPyPIミラーサーバーのURL（複数指定可） |
| `--no-cache-dir` | | キャッシュを無効化 |
| `--requirement` | `-r` | requirementsファイルからインストール |
| `--constraint` | `-c` | 制約ファイルからインストール |
| `--force-reinstall` | | 強制的に再インストール |
| `--ignore-installed` | | 既にインストール済みのパッケージを無視 |
| `--compile` | | インストール後に.pycファイルをコンパイル |
| `--no-compile` | | インストール後に.pycファイルをコンパイルしない |
| `--prefix` | | 指定した接頭辞ディレクトリにインストール |
| `--src` | | 編集可能なインストール時に使用するソースコードディレクトリ |
| `--config-settings` | | ビルドバックエンドに渡す設定（複数指定可） |
| `--no-binary` | | 二進数パッケージの使用を制限（形式: `:all:`） |
| `--only-binary` | | 二進数パッケージのみを使用（形式: `:all:`） |
| `--prefer-binary` | | 二進数パッケージを優先 |
| `--build-isolation` | | ビルドの隔離を有効化 |
| `--no-build-isolation` | | ビルドの隔離を無効化 |
| `--upgrade-strategy` | | アップグレード戦略: `eager`、`only-if-needed`、`to-satisfy-only` |
| `--break-system-packages` | | システムパッケージマネージャーが管理するPythonパッケージを変更可能 |
| `--no-uv` | | uvの代わりにpipを使用 |

**例:**

```bash
# 単一モジュールのインストール
epsdk install Weather

# 複数モジュールのインストール
epsdk install Yunhu Weather

# ミラーサーバーからインストールしてアップグレード
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 編集可能なモードでインストール（開発モード）
epsdk install -e ./my-adapter
```

### uninstall

インストール済みのErisPulseモジュールまたはアダプターパッケージをアンインストールします。パッケージ名を指定しない場合は、対話形式のアンインストールインターフェースに入ります。

**別名:** `rm`, `remove`

**パラメータ:**

| パラメータ | 说明 |
|------|------|
| `<package>...` | アンインストールするパッケージ名、複数指定可 |
| `--no-uv` | uvの代わりにpipを使用 |

**例:**

```bash
# 単一モジュールのアンインストール
epsdk uninstall Weather

# 複数モジュールのアンインストール
epsdk uninstall Yunhu Weather
```

### upgrade

インストール済みのErisPulseコンポーネントをアップグレードします。パッケージ名を指定しない場合は、対話形式で全アップグレードを行います。

**別名:** `up`

**パラメータ:**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[package]...` | | アップグレードするパッケージ名、複数指定可 |
| `--force` | `-f` | 強制アップグレード、確認をスキップ |
| `--pre` | | プレリリース版へのアップグレードを許可 |
| `--no-uv` | | uvの代わりにpipを使用 |

**例:**

```bash
# 全てのパッケージをアップグレード
epsdk upgrade

# 指定パッケージをアップグレード
epsdk upgrade Weather

# 強制アップグレード（確認をスキップ）
epsdk upgrade -f
```

### self-update

ErisPulse SDKを最新バージョンに更新します。

**別名:** `su`, `update`

**パラメータ:**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[version]` | | 更新する目標バージョン番号 |
| `--pre` | | プレリリース版への更新を許可 |
| `--force` | `-f` | 強制更新、確認をスキップ |
| `--no-uv` | | uvの代わりにpipを使用 |

**例:**

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
> `uv tool install ErisPulse`でインストールする場合、このコマンドは自動的に`uv tool upgrade ErisPulse`に変更されます（バージョン指定時は`uv tool install ErisPulse==<バージョン> --force`）。pipで直接アップグレードすると、uvの清单が元に戻され、ツール環境が破棄されます。  
> Windowsでは、更新は新しいコマンドプロンプトウィンドウで行われます：現在のCLIはツール環境ファイルの占有を解除するために終了する必要があります。ウィンドウのプロンプトが完了したら、ターミナルを再起動してください。

---

## 情報照会コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | インストール済みのコンポーネントを表示 |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | リモートリポジトリに利用可能なコンポーネントを表示 |
| `version` | `ver` | | SDKとPythonのバージョン情報を表示（`-V`と同等） |

### list

インストール済みのErisPulseモジュールとアダプターを表示します。

**別名:** `l`, `ls`

**パラメータ:**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--type` | `-t` | 指定のタイプ：`modules`、`adapters`、`all`（デフォルト） |
| `--outdated` | `-o` | アップグレード可能なパッケージのみ表示 |

**例:**

```bash
# インストール済みのすべてのコンポーネントを表示
epsdk list

# モジュールのみ表示
epsdk list -t modules

# アダプターのみ表示
epsdk list -t adapters

# アップグレード可能なパッケージのみ表示
epsdk list -o
```

### list-remote

リモートリポジトリに利用可能なErisPulseモジュールとアダプターを表示します。

**別名:** `lsr`

**パラメータ:**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--type` | `-t` | 指定のタイプ：`modules`、`adapters`、`all`（デフォルト） |
| `--refresh` | `-r` | リモートパッケージリストのキャッシュを強制的に更新 |

**例:**

```bash
# リモートで利用可能なすべてのコンポーネントを表示
epsdk list-remote

# リモートのモジュールのみ表示
epsdk list-remote -t modules

# キャッシュを強制的に更新して表示
epsdk list-remote -r
```

---

## 設定コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `config` | `cfg`, `conf` | `[name] [--list/-l]` | アダプター/モジュールの宣言的設定項目を対話形式で設定 |

### config

アダプター/モジュールの宣言的設定項目を対話形式で入力します。アダプター/モジュールが宣言した設定クラス（`ConfigClass` / `AccountConfigClass`）によって、自動的にフォームが生成され、検証が行われ、config.tomlを手動で書く必要がありません。

アダプターは追加の多アカウント（botアカウント）管理もサポートしています：アカウントの追加/編集/削除、および有効化/無効化の切り替え。

**別名:** `cfg`, `conf`

**パラメータ:**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[name]` | | 目標名（アダプターのプラットフォーム名またはモジュール名）、空欄で対話形式を選択 |
| `--list` | `-l` | 対話形式に入らず、すべての目標の設定状態を表示する |

**例:**

```bash
# すべてのアダプター/モジュールの設定状態を表示
epsdk config --list

# 対話形式で目標を選択して設定
epsdk config

# 指定のアダプターを直接設定
epsdk config yunhu

# 指定のモジュールを直接設定
epsdk config MyModule
```

**説明:**

- 設定状態は4段階に分かれています：`完了`（検証通過）、`未完了`（必須項目が不足または検証失敗）、`未設定`（未生成）、`設定なし`（目標が設定クラスを宣言していない）
- フィールド値にはソースが表示されます：既に設定されている場合は`（現在:値）`、未設定の場合はschemaのデフォルト値`（デフォルト:値）`を表示；直接Enterすると、その値を保持します
- `secret`と宣言されたキー類のフィールドは、入力時に表示されず、Enterで既に設定された値を保持します
- 対話形式選択モードでは、1つのフォームが終了すると選択メニューに戻ります（状態は更新済み）、複数の目標を連続して設定でき、空欄で終了します
- グローバルフォームの検証が失敗し、再入力を放棄した場合、今回の対話は中止され、設定は一切書き込まれません（不完全な設定で有効化された半完成状態を避ける）
- 保存後、`config/config.toml`に即時書き込まれ、ダッシュボードと実行中のSDKで確認できます；実行中のアダプターが新しいアカウント設定を適用するには、プロセスを再起動する必要があります
- `epsdk install`（対話形式インストール）または`epsdk init`でアダプターをインストールした後、設定が宣言されていることを検出すると、自動的に本対話に誘導されます；コマンドラインで直接パッケージ名を指定してインストールした場合は、設定の提示のみ表示されます

---

## 実行制御コマンド

> [!TIP]
> `epsdk run`は、プロジェクトディレクトリの`.venv`仮想環境を自動的に検出し、使用してロボットを実行します
> （`ERISPULSE_PYTHON`環境変数で解釈器を明示的に指定することもできます）。`epsdk install` /
> `uninstall` / `upgrade` / `list`もプロジェクト仮想環境に作用します。

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `run` | `r` | `[script] [--reload]` | 指定されたスクリプトまたはSDKを実行 |

### run

ErisPulseプロジェクトスクリプトまたはSDKを実行します。ホットリロードモードをサポートします。

**別名:** `r`

**パラメータ:**

| パラメータ | 说明 |
|------|------|
| `[script]` | 実行するスクリプトファイル、指定しない場合はSDKを実行 |
| `--reload` | ホットリロードモードを有効化、ファイルの変更を監視して自動的に再起動 |

**例:**

```bash
# SDKを直接実行
epsdk run

# 指定されたスクリプトファイルを実行
epsdk run main.py

# ホットリロードモードで実行（ファイル変更で自動再起動）
epsdk run main.py --reload

# SDKのホットリロードモード
epsdk run --reload
```

---

## プロジェクト管理コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `init` | — | `[path] [--project-name/-n <name>] [--path <dir>] [--quick/-q] [--force/-f] [--here] [--no-uv] [--no-venv]` | ErisPulseプロジェクトを初期化 |
| `create` | — | `{module,adapter} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f]` | モジュール/アダプターのフットスタンドを作成 |

### init

新しいErisPulseプロジェクトを初期化します。対話形式とクイックモードをサポートし、2.8.4以降は`pyproject.toml`（依存関係リスト）、任意のディレクトリに作成する機能を備えています。

**パラメータ:**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[path]` | | 目標パス（親ディレクトリを含む、例: `../apps/mybot`；純粋な名前は`--project-name`と同等） |
| `--project-name` | `-n` | プロジェクト名 |
| `--path` | | プロジェクトの親ディレクトリ（`-n`と組み合わせて作成位置を指定） |
| `--quick` | `-q` | クイックモード、対話形式のウィザードをスキップ（デフォルトで`.venv`を作成し、依存関係をインストール） |
| `--force` | `-f` | 既存の設定ファイルを強制的に上書き |
| `--here` | | 現在のディレクトリで初期化し、サブディレクトリを作成しない |
| `--no-uv` | | uvの代わりにpipを使用 |
| `--no-venv` | | 仮想環境の作成と依存関係のインストールをスキップ |

**例:**

```bash
# 対話形式で初期化
epsdk init

# クイックモードで初期化（現在のディレクトリにmy_bot/を作成し、pyproject.toml + .venvを含む）
epsdk init -q -n my_bot

# 任意のディレクトリで初期化（../apps/mybot）
epsdk init ../apps/mybot

# 父ディレクトリとプロジェクト名を組み合わせて作成
epsdk init -n my_bot --path ../apps

# 既存の設定ファイルを強制的に上書き
epsdk init -f

# 現在のディレクトリで初期化
epsdk init --here -n my_bot

# 仮想環境を作成せず、プロジェクト構造のみ生成
epsdk init --no-venv -n my_bot
```

initの成果物：`main.py`、`pyproject.toml`（依存関係リスト）、`config/config.toml` + `config.full.example`、`config/ssl/`、`logs/`、`.gitignore`、`README.md`；仮想環境を作成する場合、`.venv`が生成され、`erispulse`と選択したアダプターがインストールされます。

> [!NOTE]
> `.gitignore`はグループ形式のテンプレートです：Pythonのバイトコードとビルド成果物、仮想環境と`.env`、ツールのキャッシュ、エディタとシステムファイル、そして**`config/`と`logs/`の実行時ディレクトリを全体的に除外**します——`config.toml`にはアダプターのトークンなどの機密情報が含まれており、リポジトリに含めるのは推奨されません；共有する設定の骨格は`config.full.example`を使用してください。

> [!WARNING]
> **`uv run epsdk run`でロボットを実行しないでください**。`uv run`は`pyproject.toml`のないディレクトリで実行すると**一時的な隔離環境**を作成します——その中で`epsdk install`でインストールしたアダプターは永続化されません。プロジェクトディレクトリ内で`epsdk run`を使用してください（自動的にプロジェクトの`.venv`を使用し、または仮想環境をアクティブにしてから実行してください）。

### create

ErisPulseモジュールまたはアダプターのフットスタンドプロジェクトを作成します。

**パラメータ:**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `{module,adapter}` | | 作成するタイプ：`module`または`adapter` |
| `--name` | `-n` | プロジェクト名（PascalCase） |
| `--description` | `-d` | プロジェクトの説明 |
| `--author` | `-a` | 作者の名前 |
| `--email` | `-e` | 作者のメールアドレス |
| `--homepage` | | プロジェクトのホームページURL |
| `--output` | `-o` | 出力ディレクトリ（デフォルトは現在のディレクトリ） |
| `--force` | `-f` | 既存のディレクトリを強制的に上書き |
| `--local` | | ローカルプラグインを作成する（`module`のみ利用可能）：`plugins/<name>/`パッケージ構造を生成し、パッケージ化なしでインストール可能 |

**例:**

```bash
# 対話形式で作成（タイプの選択と情報の入力を誘導）
epsdk create

# 直接Moduleプロジェクトを作成
epsdk create module -n MyModule

# ローカルプラグインを作成（プロジェクトのplugins/ディレクトリに配置し、起動時に自動発見、ホットリロードに対応）
epsdk create module -n MyModule --local

# 直接Adapterプロジェクトを作成
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

現在のCLIの言語を確認し、サポートされている言語をリストアップし、表示言語を切り替えます。パラメータを指定しない場合は、対話形式の選択画面に入ります。

**別名:** `language`, `lang`

**パラメータ:**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[lang]` | | 切り替える言語コード（例: `zh-CN`、`en`、`ja`、`ru`） |
| `--list` | `-l` | すべてのサポートされている言語をリストアップ |

**例:**

```bash
# 対話形式で言語を選択
epsdk i18n

# 英語に切り替える
epsdk i18n en

# 日本語に切り替える
epsdk i18n ja

# すべてのサポートされている言語をリストアップ
epsdk i18n --list
```

---

## タイプストアブコマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | IDE補完を有効にするためのタイプストアブファイルを生成 |

### types

インストール済みのErisPulseモジュールとアダプターをスキャンし、`.pyi`タイプストアブファイルを生成して、IDEでの正確なコード補完と型チェックを可能にします。

**別名:** `t`, `stub`

**パラメータ:**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--output` | `-o` | 出力パス（デフォルトは現在のディレクトリの`ep-stubs/`） |
| `--force` | | 既存のストアブファイルを強制的に上書き |
| `--adapters-only` | | アダプターのタイプストアブのみ生成 |
| `--modules-only` | | モジュールのタイプストアブのみ生成 |

> **注意:** `--adapters-only` と `--modules-only` は排他で、両方指定した場合、後者のみが有効になります。

**例:**

```bash
# すべてのインストール済みのモジュールとアダプターのタイプストアブを生成
epsdk types

# アダプターのストアブのみ生成
epsdk types --adapters-only

# 指定ディレクトリに出力
epsdk types -o ./typings

# 既存のファイルを強制的に上書き
epsdk types --force
```

---

## グローバルパラメータ

以下のパラメータはすべてのコマンドに適用されます：

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--help` | `-h` | ヘルプ情報を表示 |
| `--version` | `-V` | バージョン情報を表示 |
| `--verbose` | `-v` | 詳細な出力を表示（`-vv`/`-vvv`と重ねて使用可） |
| `--no-color` | | カラーアウトプットを無効化（CI / ログ収集に適している） |
| `--no-banner` | | スタートバナーをスキップ（スクリプト呼び出し / CI環境；非対話端末と`ERISPULSE_NO_BANNER=1`では自動的に静かになる） |
| `--yes` | `-y` | すべての対話プロンプトを自動的に確認（非対話実行） |

---

## 環境診断

### doctor

> [!NOTE]
> 本コマンドはErisPulse **2.7.0+** が必要です。

現在のCLI実行環境を診断し、ヘルスレポートを出力します。"なぜインストールできない / 接続できない"などの問題を診断するのに使用します。

| パラメータ | 说明 |
|------|------|
| `--verbose` | 詳細な診断情報を表示 |

**チェック項目**:
- **Python**：解釈器のバージョンとパス
- **インストール後端**：`uv`か`pip`か
- **ターゲット解釈器**：パッケージが実際にインストールされたターゲットPython環境
- **設定ファイル**：`config/config.toml`が存在するか
- **PyPI接続性**：PyPIにアクセスできるか（発見されたコンポーネント数を表示）
- **システムプロキシ**：プロキシが検出されたか

```bash
# 実行環境の診断
epsdk doctor

# 別名を使用
epsdk diag
```

---

## 対話形式でのインストール

`epsdk install`をパッケージ名を指定せずに実行すると、対話形式のインストールに入ります：

```bash
epsdk install
```

対話インターフェースでは以下の機能が提供されます：
1. アダプターの選択
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

### コンポーネントのリスト表示

```bash
# すべてのコンポーネントを表示
epsdk list

# アダプターのみ表示
epsdk list -t adapters

# アップグレード可能なコンポーネントのみ表示
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

# 対話形式で目標を選択して設定
epsdk config

# 指定アダプターを直接設定
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
# 通常の実行
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

# サポートされている言語をリストアップ
epsdk i18n --list
```

### タイプストアブの生成

```bash
# すべてのタイプストアブを生成
epsdk types

# モジュールのタイプストアブのみ生成
epsdk types --modules-only
```

### プロジェクトの初期化

```bash
# 対話形式で初期化
epsdk init

# クイックモードで初期化
epsdk init -q -n my_bot
```

### フットスタンドの作成

```bash
# 対話形式で作成（タイプの選択と情報の入力を誘導）
epsdk create

# 直接Moduleプロジェクトを作成
epsdk create module -n MyModule

# 直接Adapterプロジェクトを作成
epsdk create adapter -n MyAdapter

# 完全なパラメータ
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 強制的に既存のディレクトリを上書き
epsdk create module -n MyModule -f
```