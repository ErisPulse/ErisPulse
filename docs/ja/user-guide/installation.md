# インストールと設定

このガイドでは、ErisPulse のインストール方法とプロジェクトの設定方法について説明します。

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

1. Python のバージョンが 3.10 以上であることを確認してください
2. `uv` を使用するよう試してください
3. ネットワーク接続が正常であることを確認してください

### 設定エラー

1. `config.toml` の構文が正しいか確認してください
2. 必要なすべての設定項目が記入されていることを確認してください
3. ログを確認して詳細なエラー情報を取得してください

### モジュールインストールに失敗

1. モジュール名が正しいか確認してください
2. ネットワーク接続を確認してください
3. `epsdk list-remote` を使用して利用可能なモジュールを確認してください

## 次のステップ

- [CLI コマンドリファレンス](cli-reference.md) - すべてのコマンドラインコマンドについて
- [設定ファイルの説明](configuration.md) - 詳細な設定オプションについて