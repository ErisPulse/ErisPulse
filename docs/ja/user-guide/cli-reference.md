# CLI コマンドリファレンス

ErisPulse コマンドラインツール（`epsdk`）は、プロジェクト管理およびパッケージ管理機能を提供します。

> **ヒント**: すべてのコマンドは `epsdk <command> --help` で詳細なパラメータ説明を確認できます。

---

## パッケージ管理コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | モジュール/アダプタをインストール |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | モジュール/アダプタをアンインストール |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | 指定したモジュールをアップグレード、またはすべてをアップグレード |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | SDK 自体を更新 |

## 診断コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose]` | 環境を診断し、ヘルスレポートを出力 |

### install

ErisPulse モジュールまたはアダプタパッケージをインストールします。パッケージ名を指定しない場合、対話型インストール画面になります。

**エイリアス:** `i`, `add`

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `[package]...` | | インストールするパッケージ名。複数指定可能 |
| `--upgrade` | `-U` | インストール時に最新バージョンへアップグレード |
| `--pre` | | プリリリース版のインストールを許可 |
| `--editable` | `-e` | 編集可能モードでインストール（パスを指定必要） |
| `--user` | | ユーザーの site-packages ディレクトリへインストール |
| `--no-deps` | | 依存関係をインストールしない |
| `--target` | `-t` | 指定のディレクトリへインストール |
| `--index-url` | | PyPI ミラーソースアドレスを指定 |
| `--extra-index-url` | | 追加の PyPI ミラーソースアドレス（複数指定可能） |
| `--no-cache-dir` | | キャッシュを無効化 |
| `--requirement` | `-r` | requirements ファイルからインストール |
| `--constraint` | `-c` | constraint ファイルからインストール |
| `--force-reinstall` | | 強制的に再インストール |
| `--ignore-installed` | | 既にインストール済みのパッケージを無視 |
| `--compile` | | インストール後、.pyc ファイルをコンパイル |
| `--no-compile` | | インストール後、.pyc ファイルをコンパイルしない |
| `--prefix` | | 指定のプレフィックスディレクトリへインストール |
| `--src` | | 編集可能インストール時のソースディレクトリ |
| `--config-settings` | | ビルドバックエンドへ渡す設定（複数指定可能） |
| `--no-binary` | | バイナリパッケージを使用しないように制限（`:all:` のような形式） |
| `--only-binary` | | バイナリパッケージのみ使用するように制限（`:all:` のような形式） |
| `--prefer-binary` | | バイナリパッケージを優先 |
| `--build-isolation` | | ビルド隔離を有効化 |
| `--no-build-isolation` | | ビルド隔離を無効化 |
| `--upgrade-strategy` | | アップグレード戦略：`eager`、`only-if-needed`、`to-satisfy-only` |
| `--break-system-packages` | | システムパッケージマネージャーが管理する Python パッケージの変更を許可 |
| `--no-uv` | | uv の代わりに pip を使用 |

**例:**

```bash
# 単一のモジュールをインストール
epsdk install Weather

# 複数のモジュールをインストール
epsdk install Yunhu Weather

# ミラーソースからインストールしてアップグレード
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 編集可能モードでインストール（開発モード）
epsdk install -e ./my-adapter
```

### uninstall

既にインストールされた ErisPulse モジュールまたはアダプタパッケージをアンインストールします。パッケージ名を指定しない場合、対話型アンインストール画面になります。

**エイリアス:** `rm`, `remove`

**引数:**

| 引数 | 説明 |
|------|------|
| `<package>...` | アンインストールするパッケージ名。複数指定可能 |
| `--no-uv` | uv の代わりに pip を使用 |

**例:**

```bash
# 単一のモジュールをアンインストール
epsdk uninstall Weather

# 複数のモジュールをアンインストール
epsdk uninstall Yunhu Weather
```

### upgrade

既にインストールされた ErisPulse コンポーネントをアップグレードします。パッケージ名を指定しないと、対話型で全件をアップグレードします。

**エイリアス:** `up`

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `[package]...` | | アップグレードするパッケージ名。複数指定可能 |
| `--force` | `-f` | 強制的にアップグレード、確認をスキップ |
| `--pre` | | プリリリース版へのアップグレードを許可 |
| `--no-uv` | | uv の代わりに pip を使用 |

**例:**

```bash
# すべてのパッケージをアップグレード
epsdk upgrade

# 指定したパッケージをアップグレード
epsdk upgrade Weather

# 強制アップグレード（確認をスキップ）
epsdk upgrade -f
```

### self-update

ErisPulse SDK 自体を最新バージョンへ更新します。

**エイリアス:** `su`, `update`

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `[version]` | | 更新対象のバージョン番号を指定 |
| `--pre` | | プリリリース版への更新を許可 |
| `--force` | `-f` | 強制的に更新、確認をスキップ |
| `--no-uv` | | uv の代わりに pip を使用 |

**例:**

```bash
# 最新の安定版へ更新
epsdk self-update

# 指定バージョンへ更新
epsdk self-update 1.2.3

# プリリリース版を許可
epsdk self-update --pre

# 強制更新
epsdk self-update -f
```

---

## 情報照会コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | インストール済みコンポーネントを一覧表示 |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | リモートで利用可能なコンポーネントを一覧表示 |

### list

インストール済みの ErisPulse モジュールとアダプタを一覧表示します。

**エイリアス:** `l`, `ls`

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `--type` | `-t` | タイプを指定：`modules`、`adapters`、`all`（デフォルト） |
| `--outdated` | `-o` | アップグレード可能なパッケージのみ表示 |

**例:**

```bash
# インストール済みのすべてのコンポーネントを一覧表示
epsdk list

# モジュールのみを一覧表示
epsdk list -t modules

# アダプタのみを一覧表示
epsdk list -t adapters

# アップグレード可能なパッケージのみ表示
epsdk list -o
```

### list-remote

リモートリポジトリで利用可能な ErisPulse モジュールとアダプタを一覧表示します。

**エイリアス:** `lsr`

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `--type` | `-t` | タイプを指定：`modules`、`adapters`、`all`（デフォルト） |
| `--refresh` | `-r` | リモートパッケージリストキャッシュを強制的に更新 |

**例:**

```bash
# すべてのリモート利用可能コンポーネントを一覧表示
epsdk list-remote

# リモートモジュールのみを一覧表示
epsdk list-remote -t modules

# キャッシュを強制的に更新して一覧表示
epsdk list-remote -r
```

---

## 実行制御コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `run` | `r` | `[script] [--reload]` | 指定したスクリプトまたは SDK を実行 |

### run

ErisPulse プロジェクトスクリプトを実行、または SDK を直接起動します。ホットリロードモードに対応しています。

**エイリアス:** `r`

**引数:**

| 引数 | 説明 |
|------|------|
| `[script]` | 実行するスクリプトファイル。指定しない場合は SDK を実行 |
| `--reload` | ホットリロードモードを有効化。ファイルの変更を監視し、自動的に再起動 |

**例:**

```bash
# SDK を直接実行
epsdk run

# 指定したスクリプトファイルを実行
epsdk run main.py

# ホットリロードモードで実行（ファイル変更時に自動再起動）
epsdk run main.py --reload

# SDK ホットリロードモード
epsdk run --reload
```

---

## プロジェクト管理コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `init` | — | `[--project-name/-n <name>] [--quick/-q] [--force/-f] [--here] [--no-uv]` | ErisPulse プロジェクトを初期化 |
| `create` | — | `{module,adapter} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f]` | モジュール/アダプタのスキャフォールドを作成 |

### init

新しい ErisPulse プロジェクトを初期化します。対話モードとクイックモードをサポートしています。

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `--project-name` | `-n` | プロジェクト名 |
| `--quick` | `-q` | クイックモード。対話ウィザードをスキップ |
| `--force` | `-f` | 既存の設定ファイルを強制的に上書き |
| `--here` | | 現在のディレクトリで初期化。サブディレクトリを作成しない |
| `--no-uv` | | uv の代わりに pip を使用 |

**例:**

```bash
# 対話型で初期化
epsdk init

# クイック初期化
epsdk init -q -n my_bot

# 既存の設定を強制的に上書き
epsdk init -f

# 現在のディレクトリで初期化
epsdk init --here -n my_bot
```

### create

ErisPulse モジュールまたはアダプタのスキャフォールドプロジェクトを作成します。

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `{module,adapter}` | | 作成するタイプ：`module` または `adapter` |
| `--name` | `-n` | プロジェクト名（PascalCase） |
| `--description` | `-d` | プロジェクトの説明 |
| `--author` | `-a` | 作者名 |
| `--email` | `-e` | 作者のメールアドレス |
| `--homepage` | | プロジェクトのホームページ URL |
| `--output` | `-o` | 出力ディレクトリ（デフォルトは現在のディレクトリ） |
| `--force` | `-f` | 既存のディレクトリを強制的に上書き |

**例:**

```bash
# 対話型で作成（タイプと情報入力の誘導）
epsdk create

# Module プロジェクトを直接作成
epsdk create module -n MyModule

# Adapter プロジェクトを直接作成
epsdk create adapter -n MyAdapter

# 完全な引数
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 出力ディレクトリを指定
epsdk create module -n MyModule -o ./projects

# 既存のディレクトリを強制的に上書き
epsdk create module -n MyModule -f
```

---

## 言語コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | CLI 表示言語の確認または切り替え |

### i18n

現在の CLI 言語を確認、サポートされている言語を一覧表示、表示言語を切り替えます。パラメータを指定しない場合、対話型の選択画面になります。

**エイリアス:** `language`, `lang`

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `[lang]` | | 切り替える言語コード（例: `zh-CN`、`en`、`ja`、`ru`） |
| `--list` | `-l` | サポートされているすべての言語を一覧表示 |

**例:**

```bash
# 対話型で言語を選択
epsdk i18n

# 英語へ切り替え
epsdk i18n en

# 日本語へ切り替え
epsdk i18n ja

# サポートされている言語を一覧表示
epsdk i18n --list
```

---

## 型スタブコマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | IDE 自補のための型スタブファイルを生成 |

### types

インストール済みの ErisPulse モジュールとアダプタをスキャンし、`.pyi` 型スタブファイルを生成して、IDE で正確なコード補完と型チェックのサポートを得ます。

**エイリアス:** `t`, `stub`

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `--output` | `-o` | 出力先パス（デフォルトは現在のディレクトリ下の `ep-stubs/`） |
| `--force` | | 既存のスタブファイルを強制的に上書き |
| `--adapters-only` | | アダプタの型スタブのみ生成 |
| `--modules-only` | | モジュールの型スタブのみ生成 |

> **注意:** `--adapters-only` と `--modules-only` は排他的です。両方を同時に指定した場合、後者が有効になります。

**例:**

```bash
# すべてのインストール済みモジュールとアダプタに対して型スタブを生成
epsdk types

# アダプタのスタブのみ生成
epsdk types --adapters-only

# 指定したディレクトリへ出力
epsdk types -o ./typings

# 既存のファイルを強制的に上書き
epsdk types --force
```

---

## 全体パラメータ

以下のパラメータはすべてのコマンドに適用されます：

| パラメータ | 短引数 | 説明 |
|------|--------|------|
| `--help` | `-h` | ヘルプ情報を表示 |
| `--version` | `-V` | バージョン情報を表示 |
| `--verbose` | `-v` | 詳細な出力を表示（`-vv`/`-vvv` で累積） |
| `--no-color` | | 色の出力を無効化（CI / ログ収集向け） |
| `--yes` | `-y` | すべての対話プロンプトを自動確認（非対話実行時） |

---

## 環境診断

### doctor

現在の CLI 実行環境を診断し、ヘルスレポートを出力します。「なぜインストールできない / 接続できないのか」といった問題の原因特定に使用します。

| パラメータ | 説明 |
|------|------|
| `--verbose` | 詳細な診断情報を表示 |

**確認項目**:
- **Python**: インタプリタのバージョンとパス
- **インストールバックエンド**: `uv` または `pip` を使用
- **ターゲットインタプリタ**: パッケージが実際にインストールされる Python 環境
- **設定ファイル**: `config/config.toml` が存在するか
- **PyPI 接続性**: PyPI へのアクセス可否（見つかったコンポーネント数を表示）
- **システムプロキシ**: プロキシの検出有無

```bash
# 実行環境診断
epsdk doctor

# エイリアスを使用
epsdk diag
```

---

## 対話型インストール

`epsdk install` でパッケージ名を指定せずに実行すると対話型インストールになります：

```bash
epsdk install
```

対話画面では以下が提供されます：
1. アダプタ選択
2. モジュール選択
3. カスタムインストール

## よく使われる使用例

### モジュールをインストール

```bash
# 単一のモジュールをインストール
epsdk install Weather

# 複数のモジュールをインストール
epsdk install Yunhu Weather

# モジュールをアップグレード
epsdk install Weather -U
```

### コンポーネントを一覧表示

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

### コンポーネントをアンインストール

```bash
# 単一のコンポーネントをアンインストール
epsdk uninstall Weather

# 複数のコンポーネントをアンインストール
epsdk uninstall Yunhu Weather
```

### コンポーネントをアップグレード

```bash
# すべてのコンポーネントをアップグレード
epsdk upgrade

# 指定したコンポーネントをアップグレード
epsdk upgrade Weather

# 強制アップグレード
epsdk upgrade -f
```

### プロジェクトを実行

```bash
# 通常の実行
epsdk run main.py

# ホットリロードモード
epsdk run main.py --reload
```

### 言語を切り替え

```bash
# 対話型で言語を選択
epsdk i18n

# 英語へ直接切り替え
epsdk i18n en

# サポートされている言語を一覧表示
epsdk i18n --list
```

### 型スタブを生成

```bash
# すべての型スタブを生成
epsdk types

# モジュールの型スタブのみ生成
epsdk types --modules-only
```

### プロジェクトを初期化

```bash
# 対話型で初期化
epsdk init

# クイック初期化
epsdk init -q -n my_bot
```

### スキャフォールドを作成

```bash
# 対話型で作成（タイプと情報入力の誘導）
epsdk create

# Module プロジェクトを直接作成
epsdk create module -n MyModule

# Adapter プロジェクトを直接作成
epsdk create adapter -n MyAdapter

# 完全な引数
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 既存のディレクトリを強制的に上書き
epsdk create module -n MyModule -f