# インストールの参考

> 本文はインストール方法の**完全な参考**（pip / uv / Docker / 故障トラブルシューティング）です。  
> もしすぐに実行したい場合は、[5 分で始める](../quick-start.md)が最もシンプルな手順をカバーしています。

## システム要件

- Python 3.10 以上
- pip または uv（推奨）
- 十分なディスク容量（少なくとも 100MB）

## インストール方法

### 方法1: pip を使用したインストール

```bash
# ErisPulse のインストール
pip install ErisPulse

# 最新バージョンへのアップグレード
pip install ErisPulse --upgrade
```

### 方法2: uv を使用したインストール（推奨）

uv はより高速な Python ツールチェーンであり、開発環境での使用が推奨されます。

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

## プロジェクト初期化とモジュールのインストール

インストールが完了した後、プロジェクトの初期化、モジュールのインストール、実行の完全な手順は [5 分で始める](../quick-start.md) を参照してください。

## インストールの確認

### インストールの確認

```bash
# ErisPulse のバージョン確認
epsdk --version
```

### テストの実行

```bash
# プロジェクトの実行
epsdk run main.py
```

次のような出力が表示されればインストールが成功しています：

```
[INFO] ErisPulse の初期化を開始しています...
[INFO] アダプタがロードされました: Yunhu
[INFO] モジュールがロードされました: MyModule
[INFO] ErisPulse の初期化が完了しました
```

## 一般的な問題

### インストール失敗

1. Python のバージョンが 3.10 以上であるか確認してください（推奨は 3.10 - 3.13）
2. `pip install` の代わりに `uv pip install ErisPulse` を試してください
3. パーミッションエラーが発生した場合は、`pip install --user ErisPulse` を試すか、仮想環境を使用してください
4. 企業のプロキシ環境で SSL 証明書エラーが発生した場合は、`pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse` を試してください
5. ネットワーク接続が正常であることを確認し、pip ソースにアクセス可能であることを確認してください

### 設定エラー

1. `config.toml` の構文が正しいか確認してください（TOML 形式はインデントや引用符に敏感です）
2. 必須の設定項目がすべて記入されていることを確認してください
3. ターミナルログを確認して詳細なエラー情報を取得してください
4. `epsdk init` を使用して設定ファイルを再生成してください

### モジュールのインストール失敗

1. モジュール名のスペルが正しいか確認してください（大文字小文字が区別されます）
2. ネットワーク接続を確認してください
3. `epsdk list-remote` を使用して利用可能なモジュール一覧を確認してください
4. モジュールが現在の SDK バージョンと互換性があるか確認してください

### Windows PowerShell の実行ポリシー

PowerShell で「ファイルをロードできません...このシステムではスクリプトの実行が禁止されています」というメッセージが表示された場合：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 次のステップ

- [CLI コマンドの参考](cli-reference.md) - すべてのコマンドラインコマンドについて
- [設定ファイルの説明](configuration.md) - 詳細な設定オプションについて