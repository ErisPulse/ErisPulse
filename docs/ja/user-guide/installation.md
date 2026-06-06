# インストールと設定

本ガイドでは、ErisPulse のインストール方法とプロジェクトの設定方法について説明します。

## システム要件

- Python 3.10 以降
- pip または uv（推奨）
- 十分なディスク容量（最小 100MB）

## インストール方法

### 方法 1: pip を使用したインストール

```bash
# ErisPulse をインストール
pip install ErisPulse

# 最新バージョンにアップグレード
pip install ErisPulse --upgrade
```

### 方法 2: uv を使用したインストール（推奨）

uv は高速な Python ツールチェーンであり、開発環境で推奨されます。

#### uv のインストール

```bash
# pip を使用して uv をインストール
pip install uv

# インストールを検証
uv --version
```

#### 仮想環境の作成

```bash
# プロジェクトディレクトリを作成
mkdir my_bot && cd my_bot

# Python 3.12 をインストール
uv python install 3.12

# 仮想環境を作成
uv venv
```

#### 仮想環境のアクティベート

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### ErisPulse のインストール

```bash
# ErisPulse をインストール
uv pip install ErisPulse --upgrade
```

## プロジェクト初期化

### 対話式初期化

```bash
epsdk init
```

以下のステップに従って完了させます：
1. プロジェクト名を入力
2. ログレベルを選択
3. サーバーパラメータを設定
4. アダプタを選択
5. アダプタパラメータを設定

### クイック初期化

```bash
# クイックモードで対話設定をスキップ
epsdk init -q -n my_bot
```

### 設定の説明

初期化後、`config/config.toml` ファイルが生成されます：

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[ErisPulse.framework]
enable_lazy_loading = true

```

## モジュールのインストール

### リモートリポジトリからインストール

```bash
# 指定したモジュールをインストール
epsdk install Yunhu

# 複数のモジュールをインストール
epsdk install Yunhu Weather
```

### ローカルからインストール

```bash
# ローカルモジュールをインストール
epsdk install ./my-module
```

### 対話式インストール

```bash
# パッケージ名を指定せずに、対話式インストールを開始
epsdk install
```

## インストールの検証

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

類似した出力が表示されれば、インストールに成功しています：

```
[INFO] 正在初始化 ErisPulse...
[INFO] 适配器已加载: Yunhu
[INFO] 模块已加载: MyModule
[INFO] ErisPulse 初始化完成
```

## よくある問題

### インストールに失敗

1. Python のバージョンが 3.10 以上であることを確認してください（推奨 3.10 - 3.13）
2. `uv pip install ErisPulse` を使用して `pip install` を代替することを試してください
3. 権限エラーが表示される場合は、`pip install --user ErisPulse` を使用するか、仮想環境を使用してください
4. 企业代理環境で SSL 证书错误が発生した場合は、`pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse` を試してください
5. ネットワーク接続が正常であり、pip 源がアクセス可能であることを確認してください

### 設定エラー

1. `config.toml` の構文が正しいか確認してください（TOML 形式はインデントと引用符に敏感です）
2. 必要なすべての設定項目が記入されていることを確認してください
3. 終端ログを確認して詳細なエラー情報を取得してください
4. `epsdk init` を使用して設定ファイルを再生成してください

### モジュールインストールに失敗

1. モジュール名のスペルが正しいか確認してください（大文字と小文字は区別されます）
2. ネットワーク接続を確認してください
3. `epsdk list-remote` を使用して利用可能なモジュールのリストを表示してください
4. モジュールが現在の SDK バージョンと互換であることを確認してください

### Windows PowerShell 実行ポリシー

PowerShell で「无法加载文件...因为在此系统上禁止运行脚本（ファイルを読み込めません...このシステムでスクリプトの実行が禁止されているため）」というメッセージが表示される場合：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 次のステップ

- [CLI コマンドリファレンス](cli-reference.md) - すべてのコマンドラインコマンドについて
- [設定ファイルの説明](configuration.md) - 詳細な設定オプションについて