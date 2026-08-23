# インストールリファレンス

> 本ページはインストール方法の**完全リファレンス**（pip / uv / Docker / トラブルシューティング）です。
> もし素早く動かしたいだけなら、[5分クイックスタート](../quick-start.md) で最も単純なフローが説明されています。

直接翻訳された完全なMarkdownコンテンツを返してください。その他の文字を含めないでください。
再度お知らせ：ドキュメントに言語切り替え行（各言語名が `` | `` で区切られた行）が含まれている場合は、上記の第8条のフォーマット要件を厳守してください。 ``[**Label**](file)`` のような間違った形式を作成しないでください。

## システム要件

- Python 3.10 以降
- pip または uv（推奨）
- 十分なディスク容量（少なくとも 100MB）

## インストール方法

### 方法 1: pip を使用してインストールする

```bash
# ErisPulse をインストール
pip install ErisPulse

# 最新版にアップグレード
pip install ErisPulse --upgrade
```

### 方法 2: uv を使用してインストールする（推奨）

uv は、より高速な Python ツールチェーンです。開発環境での使用が推奨されます。

#### uv のインストール

```bash
# pip を使用して uv をインストール
pip install uv

# インストールを確認
uv --version
```

#### 仮想環境の作成

```bash
# プロジェクトのディレクトリを作成
mkdir my_bot && cd my_bot

# Python 3.12 をインストール
uv python install 3.12

# 仮想環境を作成
uv venv
```

#### 仮想環境のアクティブ化

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### ErisPulse をインストール

```bash
# ErisPulse をインストール
uv pip install ErisPulse --upgrade

## プロジェクト初期化とモジュールのインストール

インストールが完了した後の、プロジェクトの初期化、モジュールのインストール、実行の完全な手順については、[5 分クイックスタート](../quick-start.md) を参照してください。

### 方法 3: ErisPulse-App クライアントを使用する（ターミナル不要）

Python 環境のインストールが面倒ですか？[ErisPulse-App](../ecosystem/app.md) は公式のクロスプラットフォーム クライアントです
(Android / Windows / Linux / macOS)、**スマホで直接実行**、デスクトップ版はシステムトレイへ常駐して最小化が可能です。内部に Python ランタイムと ErisPulse SDK を搭載しているため、ターミナルと手動設定は不要です。

- [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) からプラットフォームに合わせてダウンロード
  （Android `online`/`offline` APK、Windows `setup.exe`/`zip`、Linux `tar.gz`、macOS `zip`）
- App 内でインスタンスを作成して起動し、ネイティブ インターフェースでアダプターとモジュールを管理、モジュールストアを閲覧します

> 詳細な説明は [ErisPulse-App のインストールと使用方法](../ecosystem/app.md) を参照してください。

直接返事してください：翻訳後の完全なMarkdownコンテンツを返してください。その他の文字は一切含めないでください。

## インストールの検証

### インストール状況の確認

```bash
# ErisPulse のバージョンを確認
epsdk --version
```

### テストの実行

```bash
# プロジェクトを実行
epsdk run main.py
```

類似の出力が表示されれば、インストールは成功しています：

```
[INFO] ErisPulse の初期化中...
[INFO] アダプターが読み込まれました: Yunhu
[INFO] モジュールが読み込まれました: MyModule
[INFO] ErisPulse の初期化が完了しました

## よくある質問

### インストールに失敗しました

1. Python バージョンが >= 3.10（推奨 3.10 - 3.13）か確認してください
2. `pip install` の代わりに `uv pip install ErisPulse` を試してください
3. 権限エラーが表示される場合は、`pip install --user ErisPulse` を実行するか、仮想環境を使用してください
4. 企业のプロキシ環境下で SSL 証明書エラーが発生した場合は、`pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse` を試してください
5. ネットワーク接続が正常で、pip のソースにアクセスできることを確認してください

### 設定エラー

1. `config.toml` の構文が正しいか確認してください（TOML 形式はインデントと引用符に敏感です）
2. すべての必須設定項目が入力されていることを確認してください
3. 詳細なエラーメッセージについては、ターミナルのログを確認してください
4. `epsdk init` を使用して設定ファイルを再生成してください

### モジュールのインストールに失敗しました

1. モジュール名のスペルが正しいか確認してください（大文字と小文字は区別されます）
2. ネットワーク接続を確認してください
3. 利用可能なモジュールの一覧を表示するには `epsdk list-remote` を使用してください
4. モジュールが現在の SDK バージョンと互換であることを確認してください

### Windows PowerShell の実行ポリシー

PowerShell で "このシステム上でスクリプトの実行が無効になっているため、ファイルを読み込むことができません" と表示される場合は、以下を実行してください。

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

## 次のステップ

- [CLI コマンドリファレンス](cli-reference.md) - すべてのコマンドラインコマンドについて
- [設定ファイルの説明](configuration.md) - 設定オプションの詳細について

（注：原文不包含语言切换行，因此无需处理）