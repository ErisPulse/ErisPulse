# インストールのリファレンス

> 本文は、インストール方法の**完全なリファレンス**です（pip / uv / Docker / 問題解決）。
> すぐに実行したい場合は、[5 分鐘で始める](../quick-start.md)が最も簡易な手順をカバーしています。

## システム要件

- Python 3.10 以上
- pip または uv（推奨）
- 十分なディスク容量（少なくとも 100MB）

## インストール方法

### 方法1：pipを使用したインストール

```bash
# ErisPulseのインストール
pip install ErisPulse

# 最新バージョンへのアップグレード
pip install ErisPulse --upgrade
```

### 方法2：uvを使用したインストール（推奨）

uvはより高速なPythonツールチェーンであり、開発環境での使用が推奨されます。

#### uvのインストール

```bash
# pipを使用してuvをインストール
pip install uv

# インストールの確認
uv --version
```

#### 仮想環境の作成

```bash
# プロジェクトディレクトリの作成
mkdir my_bot && cd my_bot

# Python 3.12のインストール
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

#### ErisPulseのインストール

```bash
# ErisPulseのインストール
uv pip install ErisPulse --upgrade
```

## プロジェクトの初期化とモジュールのインストール

インストールが完了した後、プロジェクトの初期化、モジュールのインストール、実行の完全な手順は、[5 分間のクイックスタート](../quick-start.md)を参照してください。

### 方法 3：ErisPulse-App クライアントの使用（ターミナル不要）

Python 環境をインストールしたくないですか？[ErisPulse-App](../ecosystem/app.md) は公式の全プラットフォーム対応クライアント（Android / Windows / Linux / macOS）で、**スマートフォンで直接実行可能**、デスクトップ版ではシステムトレイに最小化してバックグラウンド常駐が可能です。内蔵の Python 実行時環境と ErisPulse SDK を搭載しており、ターミナルや手動設定は不要です：

- [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) から、プラットフォームに応じてダウンロードしてください（Android は `online`/`offline` APK、Windows は `setup.exe`/`zip`、Linux は `tar.gz`、macOS は `zip`）
- App 内でインスタンスを作成して起動し、ネイティブのインターフェースでアダプタやモジュールを管理し、モジュールストアを閲覧します

> 詳細な説明は、[ErisPulse-App のインストールと使用方法](../ecosystem/app.md)をご覧ください。

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

以下のような出力が表示されれば、インストールが成功したことを意味します：

```
[INFO] ErisPulse の初期化を開始しています...
[INFO] アダプタがロードされました: Yunhu
[INFO] モジュールがロードされました: MyModule
[INFO] ErisPulse の初期化が完了しました
```

## 常見問題

### インストール失敗

1. Python のバージョンが 3.10 以上であるか確認してください（推奨バージョンは 3.10 - 3.13）
2. `pip install` の代わりに `uv pip install ErisPulse` を試してください
3. 権限エラーが発生した場合は、`pip install --user ErisPulse` を試すか、仮想環境を使用してください
4. 企業のプロキシ環境で SSL 証明書エラーが発生した場合は、`pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse` を試してください
5. ネットワーク接続が正常であることを確認し、pip のソースがアクセス可能であることを確認してください

### 設定エラー

1. `config.toml` の構文が正しいか確認してください（TOML 形式はインデントや引用符に敏感です）
2. 必須の設定項目がすべて入力されているか確認してください
3. 端末ログを確認して詳細なエラーメッセージを取得してください
4. `epsdk init` を使用して設定ファイルを再生成してください

### モジュールのインストール失敗

1. モジュール名のスペルが正しいか確認してください（大文字小文字が区別されます）
2. ネットワーク接続を確認してください
3. `epsdk list-remote` を使用して利用可能なモジュール一覧を確認してください
4. モジュールが現在使用している SDK バージョンと互換性があるか確認してください

### Windows PowerShell 実行ポリシー

PowerShell で「ファイルをロードできません。このシステムではスクリプトの実行が禁止されています」というメッセージが表示された場合：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Debian/Ubuntu 仮想環境の作成失敗

インストールスクリプトで「仮想環境の作成に失敗しました」と表示され、エラーメッセージに `ensurepip is not available` が含まれている場合、Debian/Ubuntu ではデフォルトで `python3-venv` がインストールされていないため（システム Python の `ensurepip` が無効化されています）：

```bash
sudo apt install python3.13-venv   # 実際の Python バージョンに応じて対応するパッケージをインストール
# または汎用的なメタパッケージをインストール：
sudo apt install python3-venv
```

インストール後、インストールスクリプトを再実行してください。新しいインストールスクリプトでは、この問題が検出された場合、対応するシステムパッケージの自動インストールを促すか、`ensurepip` に依存しない `uv`（`uv venv`）を使用することもできます。

## 次のステップ

- [CLI コマンドリファレンス](cli-reference.md) - すべてのコマンドラインコマンドについて学びます
- [設定ファイルについて](configuration.md) - 設定オプションの詳細を学びます