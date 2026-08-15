# CLIコマンドリファレンス

ErisPulseコマンドラインツール（`epsdk`）は、プロジェクト管理およびパッケージ管理機能を提供します。

> **ヒント**：すべてのコマンドは `epsdk <コマンド> --help` を使用して、詳細なパラメータ説明を確認できます。

---

[**English**](docs/en/quick-start.md) | [**日本語**](docs/ja/quick-start.md) | [**简体中文**](docs/ja/quick-start.md)

## パッケージ管理コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | モジュール/アダプターのインストール |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | モジュール/アダプターのアンインストール |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | 指定されたモジュールまたはすべてのモジュールをアップグレード |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | SDK 自体の更新 |

## 診断コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose]` | 環境を診断し、健康レポートを出力します |

### install

ErisPulse モジュールまたはアダプタパッケージをインストールします。パッケージ名を指定しない場合、対話形式のインストールインターフェースに移行します。

**別名：** `i`, `add`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[package]...` | | インストールするパッケージ名。複数指定可能 |
| `--upgrade` | `-U` | インストール時に最新バージョンにアップグレードします |
| `--pre` | | プレリリース版のインストールを許可します |
| `--editable` | `-e` | 編集可能なモードでインストールします（パスを指定する必要があります） |
| `--user` | | ユーザーの site-packages ディレクトリにインストールします |
| `--no-deps` | | 依存関係をインストールしません |
| `--target` | `-t` | 指定したディレクトリにインストールします |
| `--index-url` | | PyPI ミラーサーバの URL を指定します |
| `--extra-index-url` | | 追加の PyPI ミラーサーバの URL（複数指定可能） |
| `--no-cache-dir` | | キャッシュを無効にします |
| `--requirement` | `-r` | requirements ファイルからインストールします |
| `--constraint` | `-c` | 制約ファイルからインストールします |
| `--force-reinstall` | | 強制的に再インストールします |
| `--ignore-installed` | | 既にインストール済みのパッケージを無視します |
| `--compile` | | インストール後に .pyc ファイルをコンパイルします |
| `--no-compile` | | インストール後に .pyc ファイルをコンパイルしません |
| `--prefix` | | 指定したプレフィックスディレクトリにインストールします |
| `--src` | | 編集可能なインストール時に使用するソースコードディレクトリ |
| `--config-settings` | | ビルドバックエンドに渡す設定（複数指定可能） |
| `--no-binary` | | 二進数パッケージの使用を制限します（`:all:` の形式） |
| `--only-binary` | | 二進数パッケージのみを使用するように制限します（`:all:` の形式） |
| `--prefer-binary` | | 二進数パッケージを優先的に選択します |
| `--build-isolation` | | ビルドの隔離を有効にします |
| `--no-build-isolation` | | ビルドの隔離を無効にします |
| `--upgrade-strategy` | | アップグレード戦略：`eager`、`only-if-needed`、`to-satisfy-only` |
| `--break-system-packages` | | システムパッケージマネージャが管理する Python パッケージの変更を許可します |
| `--no-uv` | | uv の代わりに pip を使用します |

**例：**

```bash
# 単一モジュールのインストール
epsdk install Weather

# 複数モジュールのインストール
epsdk install Yunhu Weather

# ミラーサーバからインストールし、アップグレード
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 編集可能なモードでインストール（開発モード）
epsdk install -e ./my-adapter
```

### uninstall

インストール済みの ErisPulse モジュールまたはアダプタパッケージをアンインストールします。パッケージ名を指定しない場合、対話形式のアンインストールインターフェースに移行します。

**別名：** `rm`, `remove`

**パラメータ：**

| パラメータ | 説明 |
|------|------|
| `<package>...` | アンインストールするパッケージ名。複数指定可能 |
| `--no-uv` | uv の代わりに pip を使用します |

**例：**

```bash
# 単一モジュールのアンインストール
epsdk uninstall Weather

# 複数モジュールのアンインストール
epsdk uninstall Yunhu Weather
```

### upgrade

インストール済みの ErisPulse コンポーネントをアップグレードします。パッケージ名を指定しない場合、すべてを対話形式でアップグレードします。

**別名：** `up`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[package]...` | | アップグレードするパッケージ名。複数指定可能 |
| `--force` | `-f` | 強制的にアップグレードし、確認をスキップします |
| `--pre` | | プレリリース版へのアップグレードを許可します |
| `--no-uv` | | uv の代わりに pip を使用します |

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

ErisPulse SDK 自身を最新バージョンに更新します。

**別名：** `su`, `update`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[version]` | | 更新する対象のバージョン番号を指定します |
| `--pre` | | プレリリース版への更新を許可します |
| `--force` | `-f` | 強制的に更新し、確認をスキップします |
| `--no-uv` | | uv の代わりに pip を使用します |

**例：**

```bash
# 最新の安定版に更新
epsdk self-update

# 指定バージョンに更新
epsdk self-update 1.2.3

# プレリリース版を許容
epsdk self-update --pre

# 強制更新
epsdk self-update -f

## 情報照会コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | インストール済みのコンポーネントを一覧表示します |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | リモートで利用可能なコンポーネントを一覧表示します |

### list

インストール済みの ErisPulse モジュールとアダプタを表示します。

**別名:** `l`, `ls`

**パラメータ:**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--type` | `-t` | タイプを指定: `modules`、`adapters`、`all`（デフォルト） |
| `--outdated` | `-o` | 更新可能なパッケージのみ表示します |

**例:**

```bash
# インストール済みのすべてのコンポーネントを表示
epsdk list

# モジュールのみを表示
epsdk list -t modules

# アダプタのみを表示
epsdk list -t adapters

# 更新可能なパッケージのみを表示
epsdk list -o
```

### list-remote

リモートリポジトリで利用可能な ErisPulse モジュールとアダプタを表示します。

**別名:** `lsr`

**パラメータ:**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--type` | `-t` | タイプを指定: `modules`、`adapters`、`all`（デフォルト） |
| `--refresh` | `-r` | リモートパッケージリストのキャッシュを強制的に更新します |

**例:**

```bash
# リモートで利用可能なすべてのコンポーネントを表示
epsdk list-remote

# リモートモジュールのみを表示
epsdk list-remote -t modules

# キャッシュを強制的に更新した後に表示
epsdk list-remote -r

## 実行コントロールコマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `run` | `r` | `[script] [--reload]` | 指定されたスクリプトまたは SDK を実行 |

### run

ErisPulse プロジェクトのスクリプトを実行するか、SDK を直接起動します。ホットリロードモードをサポートしています。

**別名:** `r`

**パラメータ:**

| パラメータ | 説明 |
|------|------|
| `[script]` | 実行するスクリプトファイル。指定しない場合は SDK を実行します。 |
| `--reload` | ホットリロードモードを有効にします。ファイルの変更を監視して自動的に再起動します。 |

**例:**

```bash
# SDK を直接実行
epsdk run

# 指定されたスクリプトファイルを実行
epsdk run main.py

# ホットリロードモードで実行（ファイルの変更で自動的に再起動）
epsdk run main.py --reload

# SDK のホットリロードモード
epsdk run --reload
```

---

docs/ja/quick-start.md

## プロジェクト管理コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `init` | — | `[--project-name/-n <name>] [--quick/-q] [--force/-f] [--here] [--no-uv]` | ErisPulse プロジェクトを初期化します |
| `create` | — | `{module,adapter} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f]` | モジュール/アダプターのスキャフォールディングを作成します |

### init

新しい ErisPulse プロジェクトを初期化します。インタラクティブモードとクイックモードをサポートしています。

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--project-name` | `-n` | プロジェクト名 |
| `--quick` | `-q` | クイックモード、インタラクティブガイドをスキップします |
| `--force` | `-f` | 既存の設定ファイルを強制的に上書きします |
| `--here` | | 現在のディレクトリで初期化し、サブディレクトリを作成しません |
| `--no-uv` | | uv の代わりに pip を使用します |

**例：**

```bash
# インタラクティブな初期化
epsdk init

# クイック初期化
epsdk init -q -n my_bot

# 既存の設定を強制的に上書き
epsdk init -f

# 現在のディレクトリで初期化
epsdk init --here -n my_bot
```

### create

ErisPulse モジュールまたはアダプターのスキャフォールディングプロジェクトを作成します。

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `{module,adapter}` | | 作成するタイプ：`module` または `adapter` |
| `--name` | `-n` | プロジェクト名（PascalCase） |
| `--description` | `-d` | プロジェクトの説明 |
| `--author` | `-a` | 作者名 |
| `--email` | `-e` | 作者のメールアドレス |
| `--homepage` | | プロジェクトのホームページ URL |
| `--output` | `-o` | 出力ディレクトリ（デフォルトは現在のディレクトリ） |
| `--force` | `-f` | 既存のディレクトリを強制的に上書きします |
| `--local` | | ローカルプラグインを作成します（`module` のみ利用可能）：`plugins/<name>/` パッケージ構造を生成し、ビルドせずにインストールできます |

**例：**

```bash
# インタラクティブな作成（タイプの選択と情報入力のガイド付き）
epsdk create

# Module プロジェクトを直接作成
epsdk create module -n MyModule

# ローカルプラグインを作成（`plugins/` ディレクトリに配置され、起動時に自動的に検出され、ホットリロードがサポートされます）
epsdk create module -n MyModule --local

# Adapter プロジェクトを直接作成
epsdk create adapter -n MyAdapter

# 完全なパラメータ
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 出力ディレクトリを指定
epsdk create module -n MyModule -o ./projects

# 既存のディレクトリを強制的に上書き
epsdk create module -n MyModule -f

## 言語コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | CLIの表示言語を確認または切り替える |

### i18n

現在のCLI言語を確認し、サポートされている言語の一覧を表示し、表示言語を切り替える。パラメータを指定しない場合は、インタラクティブな選択画面に移行する。

**別名：** `language`, `lang`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `[lang]` | | 切り替える言語コード（例：`zh-CN`、`en`、`ja`、`ru`） |
| `--list` | `-l` | すべてのサポート言語を表示する |

**例：**

```bash
# インタラクティブに言語を選択
epsdk i18n

# 英語に切り替える
epsdk i18n en

# 日本語に切り替える
epsdk i18n ja

# すべてのサポート言語を表示する
epsdk i18n --list

## タイプ・スタブ・コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | IDE補完を有効にするためのタイプ・スタブ・ファイルを生成します |

### types

インストール済みの ErisPulse モジュールとアダプタをスキャンし、`.pyi` タイプ・スタブ・ファイルを生成します。これにより、IDE で正確なコード補完と型検査のサポートが得られます。

**別名：** `t`, `stub`

**パラメータ：**

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--output` | `-o` | 出力パス（デフォルトは現在のディレクトリの `ep-stubs/`） |
| `--force` | | 既存のスタブ・ファイルを上書きします |
| `--adapters-only` | | アダプタのタイプ・スタブのみを生成します |
| `--modules-only` | | モジュールのタイプ・スタブのみを生成します |

> **注意：** `--adapters-only` と `--modules-only` は排他的です。両方指定した場合、後者（`--modules-only`）が有効になります。

**例：**

```bash
# インストール済みのすべてのモジュールとアダプタのタイプ・スタブを生成します
epsdk types

# アダプタのスタブのみを生成します
epsdk types --adapters-only

# 指定したディレクトリに出力します
epsdk types -o ./typings

# 既存のファイルを強制的に上書きします
epsdk types --force
```

---

**重要：** パスの置換ルール  
- ドキュメント内のリンクにある `docs/ja/` を `docs/ja/` に置換します  
- 例：`docs/ja/quick-start.md` は `docs/ja/quick-start.md` に変更します  
- 非現在言語版のファイルを指すリンク（`README.xx.md` 形式のリンク）は、変更しないでください  
- これにより、リンクが正しい言語のドキュメント版を指すようにします

## グローバルパラメータ

以下のパラメータはすべてのコマンドに適用されます：

| パラメータ | 短パラメータ | 説明 |
|------|--------|------|
| `--help` | `-h` | ヘルプ情報を表示します |
| `--version` | `-V` | バージョン情報を表示します |
| `--verbose` | `-v` | 詳細出力を表示します（`-vv`/`-vvv` で重ねて使用可能） |
| `--no-color` | | カラフルな出力を無効にします（CI / ログ収集に適しています） |
| `--yes` | `-y` | すべてのインタラクティブなプロンプトに自動的に確認します（インタラクティブでない実行） |

---

[**English**](docs/ja/quick-start.md) | [**中文**](docs/ja/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## 環境診断

### doctor

現在の CLI 実行環境を診断し、健康レポートを出力します。これは「なぜインストールできない / 接続できないか」などの問題を解決するために使用します。

| パラメータ | 説明 |
|------|------|
| `--verbose` | 詳細な診断情報を表示します |

**チェック項目**:
- **Python**：解釈器のバージョンとパス
- **インストールバックエンド**：`uv` または `pip` の使用
- **目標解釈器**：パッケージが実際にインストールされる Python 環境
- **設定ファイル**：`config/config.toml` が存在するか
- **PyPI への接続性**：PyPI にアクセスできるか（発見されたコンポーネント数を表示）
- **システムプロキシ**：プロキシが検出されているか

```bash
# 実行環境の診断
epsdk doctor

# 別名を使用
epsdk diag
```

---

[**English**](docs/en/quick-start.md) | [**日本語**](docs/ja/quick-start.md) | [**简体中文**](docs/ja/quick-start.md)

## インタラクティブインストール

`epsdk install` をパッケージ名を指定せずに実行すると、インタラクティブインストールモードになります：

```bash
epsdk install
```

インタラクティブインターフェースでは、以下のオプションが利用できます：
1. アダプタの選択
2. モジュールの選択
3. カスタムインストール

[**English**](docs/ja/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## 一般的使い方

### モジュールのインストール

```bash
# 単一のモジュールをインストール
epsdk install Weather

# 複数のモジュールをインストール
epsdk install Yunhu Weather

# モジュールをアップグレード
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

# リモートで利用可能なコンポーネントを確認
epsdk list-remote
```

### コンポーネントのアンインストール

```bash
# 単一のコンポーネントをアンインストール
epsdk uninstall Weather

# 複数のコンポーネントをアンインストール
epsdk uninstall Yunhu Weather
```

### コンポーネントのアップグレード

```bash
# すべてのコンポーネントをアップグレード
epsdk upgrade

# 指定されたコンポーネントをアップグレード
epsdk upgrade Weather

# 強制的にアップグレード
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

# 英語に直接切り替え
epsdk i18n en

# 対応している言語の一覧表示
epsdk i18n --list
```

### タイプのスタブ生成

```bash
# すべてのタイプのスタブを生成
epsdk types

# モジュールのタイプのスタブのみを生成
epsdk types --modules-only
```

### プロジェクトの初期化

```bash
# 対話形式での初期化
epsdk init

# クイック初期化
epsdk init -q -n my_bot
```

### フレームワークの作成

```bash
# 対話形式での作成（タイプの選択と情報の入力をガイド）
epsdk create

# Module プロジェクトを直接作成
epsdk create module -n MyModule

# Adapter プロジェクトを直接作成
epsdk create adapter -n MyAdapter

# 完全なパラメータ
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 既存のディレクトリを強制的に上書き
epsdk create module -n MyModule -f