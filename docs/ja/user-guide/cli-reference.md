# CLI コマンドリファレンス

ErisPulse コマンドラインツール（`epsdk`）は、プロジェクト管理とパッケージ管理機能を提供します。

> **ヒント**：すべてのコマンドは `epsdk <コマンド> --help` で詳細なパラメータ説明を確認できます。

---

## パッケージ管理コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | モジュール/アダプターのインストール |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | モジュール/アダプターのアンインストール |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | 指定モジュールまたは全モジュールのアップグレード |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | SDK 自体の更新 |

## ディアグノスティクスコマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose]` | 環境診断とヘルスレポートの出力 |

### install

ErisPulse モジュールまたはアダプターパッケージをインストールします。パッケージ名を指定しない場合は、対話形式のインストール画面に移行します。

**別名：** `i`, `add`

**パラメータ：**

| パラメータ | 短引数 | 説明 |
|------|--------|------|
| `[package]...` | | インストールするパッケージ名。複数指定可 |
| `--upgrade` | `-U` | 最新バージョンにアップグレードしてインストール |
| `--pre` | | プリリリース版のインストールを許可 |
| `--editable` | `-e` | 編集可能なモードでインストール（パスを指定する必要あり） |
| `--user` | | ユーザーの site-packages ディレクトリにインストール |
| `--no-deps` | | 依存関係をインストールしない |
| `--target` | `-t` | 指定ディレクトリにインストール |
| `--index-url` | | PyPI イメージソースの URL |
| `--extra-index-url` | | 追加 PyPI イメージソースの URL（複数指定可） |
| `--no-cache-dir` | | キャッシュディレクトリを使用しない |
| `--requirement` | `-r` | requirements ファイルからインストール |
| `--constraint` | `-c` | 約束ファイルからインストール |
| `--force-reinstall` | | 強制的に再インストール |
| `--ignore-installed` | | 既にインストール済みのパッケージを無視 |
| `--compile` | | インストール後に .pyc ファイルをコンパイル |
| `--no-compile` | | インストール後に .pyc ファイルをコンパイルしない |
| `--prefix` | | 指定プレフィックスディレクトリにインストール |
| `--src` | | 編集可能なインストール時に使用するソースコードディレクトリ |
| `--config-settings` | | ビルドバックエンドに渡す設定（複数指定可） |
| `--no-binary` | | 二進数パッケージの使用を制限（形式は `:all:` のよう） |
| `--only-binary` | | 二進数パッケージのみを使用（形式は `:all:` のよう） |
| `--prefer-binary` | | 二進数パッケージを優先 |
| `--build-isolation` | | ビルドの分離を有効化 |
| `--no-build-isolation` | | ビルドの分離を無効化 |
| `--upgrade-strategy` | | アップグレード戦略：`eager`、`only-if-needed`、`to-satisfy-only` |
| `--break-system-packages` | | システムパッケージマネージャーが管理する Python パッケージを変更可能 |
| `--no-uv` | | uv ではなく pip を使用 |

**例：**

```bash
# 単一モジュールのインストール
epsdk install Weather

# 複数モジュールのインストール
epsdk install Yunhu Weather

# イメージソースからインストールしてアップグレード
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 編集可能なモードでインストール（開発モード）
epsdk install -e ./my-adapter
```

### uninstall

インストール済みの ErisPulse モジュールまたはアダプターパッケージをアンインストールします。パッケージ名を指定しない場合は、対話形式のアンインストール画面に移行します。

**別名：** `rm`, `remove`

**パラメータ：**

| パラメータ | 説明 |
|------|------|
| `<package>...` | アンインストールするパッケージ名。複数指定可 |
| `--no-uv` | uv ではなく pip を使用 |

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

| パラメータ | 短引数 | 説明 |
|------|--------|------|
| `[package]...` | | アップグレードするパッケージ名。複数指定可 |
| `--force` | `-f` | 強制アップグレード。確認をスキップ |
| `--pre` | | プリリリース版へのアップグレードを許可 |
| `--no-uv` | | uv ではなく pip を使用 |

**例：**

```bash
# 全パッケージのアップグレード
epsdk upgrade

# 指定パッケージのアップグレード
epsdk upgrade Weather

# 強制アップグレード（確認をスキップ）
epsdk upgrade -f
```

### self-update

ErisPulse SDK 自体を最新版に更新します。

**別名：** `su`, `update`

**パラメータ：**

| パラメータ | 短引数 | 説明 |
|------|--------|------|
| `[version]` | | 更新対象のバージョン番号 |
| `--pre` | | プリリリース版への更新を許可 |
| `--force` | `-f` | 強制更新。確認をスキップ |
| `--no-uv` | | uv ではなく pip を使用 |

**例：**

```bash
# 最新の安定版に更新
epsdk self-update

# 指定バージョンに更新
epsdk self-update 1.2.3

# プリリリース版を許可
epsdk self-update --pre

# 強制更新
epsdk self-update -f
```

---

## 情報照会コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | インストール済みのコンポーネントを表示 |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | リモートリポジトリで利用可能なコンポーネントを表示 |

### list

インストール済みの ErisPulse モジュールとアダプターを表示します。

**別名：** `l`, `ls`

**パラメータ：**

| パラメータ | 短引数 | 説明 |
|------|--------|------|
| `--type` | `-t` | タイプ指定：`modules`、`adapters`、`all`（デフォルト） |
| `--outdated` | `-o` | 更新可能なパッケージのみ表示 |

**例：**

```bash
# インストール済みのすべてのコンポーネントを表示
epsdk list

# モジュールのみ表示
epsdk list -t modules

# アダプターのみ表示
epsdk list -t adapters

# 更新可能なパッケージのみ表示
epsdk list -o
```

### list-remote

リモートリポジトリで利用可能な ErisPulse モジュールとアダプターを表示します。

**別名：** `lsr`

**パラメータ：**

| パラメータ | 短引数 | 説明 |
|------|--------|------|
| `--type` | `-t` | タイプ指定：`modules`、`adapters`、`all`（デフォルト） |
| `--refresh` | `-r` | リモートパッケージリストのキャッシュを強制的に更新 |

**例：**

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
| `config` | `cfg`, `conf` | `[name] [--list/-l]` | 対話形式でアダプター/モジュールの宣言的設定項目を設定 |

### config

対話形式でアダプター/モジュールの宣言的設定項目を入力します。アダプター/モジュールが宣言した設定クラス（`ConfigClass` / `AccountConfigClass`）によって、自動的にフォームが生成され、検証が行われ、config.toml を手動で書く必要がありません。

アダプターは追加の多アカウント（botアカウント）管理もサポート：アカウントの追加/編集/削除、および有効化/無効化の切り替え。

**別名：** `cfg`, `conf`

**パラメータ：**

| パラメータ | 短引数 | 説明 |
|------|--------|------|
| `[name]` | | 目標名（アダプタープラットフォーム名またはモジュール名）。空欄の場合は対話形式で選択 |
| `--list` | `-l` | 設定状態を一覧表示するだけ。対話形式には移行しない |

**例：**

```bash
# すべてのアダプター/モジュールの設定状態を表示
epsdk config --list

# 対話形式で目標を選択して設定
epsdk config

# 指定アダプターを直接設定
epsdk config yunhu

# 指定モジュールを直接設定
epsdk config MyModule
```

**説明：**

- 設定状態は4段階に分類されます：`既に準備完了`（検証通過）、`未完成`（必須項目が不足または検証失敗）、`未設定`（未生成）、`設定なし`（目標が設定クラスを宣言していない）
- フィールド値にソースが付いて表示されます：既に設定済みは `（現在:値）`、未設定は schema のデフォルト値が `（デフォルト:値）` として表示されます。直接 Enter を押すとその値を保持します
- `secret` と宣言された鍵類のフィールドは入力時に表示されず、Enter を押すと既に設定された値を保持します
- 対話形式で、1つのフォームが終了すると選択メニューに戻ります（状態は更新済み）、複数の目標を連続して設定でき、空欄で終了します
- グローバルフォームの検証が失敗し、再入力を放棄した場合、今回の対話は中断され、設定は一切書き込まれません（「有効化済みだが設定が不完全」の半完成状態を避ける）
- 保存後、`config/config.toml` に即時書き込まれ、ダッシュボードと実行中の SDK で共通で確認できます。実行中のアダプターが新しいアカウント設定を適用するには、プロセスを再起動する必要があります
- `epsdk install`（対話形式のインストール）と `epsdk init` でアダプターをインストール成功後、設定の宣言を検出すると自動的に本対話に導きます。コマンドラインで直接パッケージ名を指定してインストールする場合は、設定の提示のみ出力されます

---

## 実行制御コマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `run` | `r` | `[script] [--reload]` | 指定スクリプトまたは SDK を実行 |

### run

ErisPulse プロジェクトのスクリプトまたは SDK を実行します。ホットリロードモードもサポート。

**別名：** `r`

**パラメータ：**

| パラメータ | 説明 |
|------|------|
| `[script]` | 実行するスクリプトファイル。指定しない場合は SDK を実行 |
| `--reload` | ホットリロードモードを有効化。ファイルの変更を監視して自動的に再起動 |

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
| `init` | — | `[--project-name/-n <name>] [--quick/-q] [--force/-f] [--here] [--no-uv]` | ErisPulse プロジェクトを初期化 |
| `create` | — | `{module,adapter} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f]` | モジュール/アダプターのフットスタジプロジェクトを作成 |

### init

新しい ErisPulse プロジェクトを初期化します。対話形式とクイックモードをサポート。

**パラメータ：**

| パラメータ | 短引数 | 説明 |
|------|--------|------|
| `--project-name` | `-n` | プロジェクト名 |
| `--quick` | `-q` | クイックモード。対話形式の向導をスキップ |
| `--force` | `-f` | 既存の設定ファイルを上書き |
| `--here` | | 現在のディレクトリで初期化。サブディレクトリを作成しない |
| `--no-uv` | | uv ではなく pip を使用 |

**例：**

```bash
# 対話形式で初期化
epsdk init

# クイックモードで初期化
epsdk init -q -n my_bot

# 既存の設定ファイルを強制的に上書き
epsdk init -f

# 現在のディレクトリで初期化
epsdk init --here -n my_bot
```

### create

ErisPulse モジュールまたはアダプターのフットスタジプロジェクトを作成します。

**パラメータ：**

| パラメータ | 短引数 | 説明 |
|------|--------|------|
| `{module,adapter}` | | 作成するタイプ：`module` または `adapter` |
| `--name` | `-n` | プロジェクト名（PascalCase） |
| `--description` | `-d` | プロジェクトの説明 |
| `--author` | `-a` | 作者名 |
| `--email` | `-e` | 作者のメールアドレス |
| `--homepage` | | プロジェクトのホームページ URL |
| `--output` | `-o` | 出力ディレクトリ（デフォルトは現在のディレクトリ） |
| `--force` | `-f` | 既存のディレクトリを上書き |
| `--local` | | ローカルプラグインを作成（`module` にのみ有効）：`plugins/<name>/` パッケージ構造を生成し、パッケージングなしでインストール可能 |

**例：**

```bash
# 対話形式で作成（タイプの選択と情報を入力する向導）
epsdk create

# Module プロジェクトを直接作成
epsdk create module -n MyModule

# ローカルプラグインを作成（プロジェクトの plugins/ ディレクトリに配置し、起動時に自動検出、ホットリロード対応）
epsdk create module -n MyModule --local

# Adapter プロジェクトを直接作成
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
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | CLI の表示言語を確認または切り替え |

### i18n

CLI の現在の言語を確認し、サポートされている言語をリストアップし、表示言語を切り替えます。パラメータを指定しない場合は対話形式で選択画面に移行します。

**別名：** `language`, `lang`

**パラメータ：**

| パラメータ | 短引数 | 説明 |
|------|--------|------|
| `[lang]` | | 切り替えたい言語コード（例: `zh-CN`、`en`、`ja`、`ru`） |
| `--list` | `-l` | サポートされているすべての言語をリストアップ |

**例：**

```bash
# 対話形式で言語を選択
epsdk i18n

# 英語に切り替え
epsdk i18n en

# 日本語に切り替え
epsdk i18n ja

# サポートされているすべての言語をリストアップ
epsdk i18n --list
```

---

## タイプストアブコマンド

| コマンド | 別名 | パラメータ | 説明 |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | IDE の補完を有効にするためのタイプストアブファイルを生成 |

### types

インストール済みの ErisPulse モジュールとアダプターをスキャンし、それらに `.pyi` タイプストアブファイルを生成します。これにより、IDE で正確なコード補完と型検査が可能になります。

**別名：** `t`, `stub`

**パラメータ：**

| パラメータ | 短引数 | 説明 |
|------|--------|------|
| `--output` | `-o` | 出力パス（デフォルトは現在のディレクトリの `ep-stubs/`） |
| `--force` | | 既存のストアブファイルを上書き |
| `--adapters-only` | | アダプターのタイプストアブのみ生成 |
| `--modules-only` | | モジュールのタイプストアブのみ生成 |

> **注意：** `--adapters-only` と `--modules-only` は互いに排他的で、両方指定した場合は後者（`--modules-only`）が有効になります。

**例：**

```bash
# インストール済みのすべてのモジュールとアダプターにタイプストアブを生成
epsdk types

# アダプターのタイプストアブのみ生成
epsdk types --adapters-only

# 指定ディレクトリに出力
epsdk types -o ./typings

# 既存ファイルを強制的に上書き
epsdk types --force
```

---

## グローバルパラメータ

以下のパラメータはすべてのコマンドに適用されます：

| パラメータ | 短引数 | 説明 |
|------|--------|------|
| `--help` | `-h` | ヘルプ情報を表示 |
| `--version` | `-V` | バージョン情報を表示 |
| `--verbose` | `-v` | 詳細な出力を表示（`-vv`/`-vvv` で重ねて使用可） |
| `--no-color` | | カラーアウトプットを無効化（CI / ログ収集に適） |
| `--yes` | `-y` | すべての対話プロンプトを自動的に確認（非対話実行） |

---

## 環境診断

### doctor

> [!NOTE]
> 本コマンドは ErisPulse **2.7.0+** が必要です。

現在の CLI 実行環境を診断し、ヘルスレポートを出力します。"なぜインストールできない / 接続できない" などの問題を診断するのに使用します。

| パラメータ | 説明 |
|------|------|
| `--verbose` | 詳細な診断情報を表示 |

**チェック項目：**
- **Python**：実行環境のバージョンとパス
- **インストールバックエンド**：`uv` か `pip` を使用しているか
- **ターゲット実行環境**：パッケージが実際にインストールされた Python 環境
- **設定ファイル**：`config/config.toml` が存在するか
- **PyPI 接続性**：PyPI にアクセスできるか（発見されたコンポーネント数を表示）
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

対話画面では以下の機能が提供されます：
1. アダプターの選択
2. モジュールの選択
3. カスタムインストール

## 一般的な使用方法

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
# すべてのコンポーネントを表示
epsdk list

# アダプターのみ表示
epsdk list -t adapters

# 更新可能なコンポーネントのみ表示
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
# 普通の実行
epsdk run main.py

# ホットリロードモード
epsdk run main.py --reload
```

### 言語の切り替え

```bash
# 対話形式で言語を選択
epsdk i18n

# 直接英語に切り替え
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

### フットスタジの作成

```bash
# 対話形式で作成（タイプの選択と情報を入力する向導）
epsdk create

# Module プロジェクトを直接作成
epsdk create module -n MyModule

# Adapter プロジェクトを直接作成
epsdk create adapter -n MyAdapter

# 完全なパラメータ
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 強制的に既存のディレクトリを上書き
epsdk create module -n MyModule -f
```