# クイックスタート

> わからない用語がありますか？[用語集](terminology.md)で分かりやすい説明を確認してください。

## ErisPulseのインストール

### ワンクリックインストールスクリプト（推奨）

インストールスクリプトは、お使いの環境（Docker、Python、uv）を自動的に検出し、最適なインストール方法を選択するようにガイドします。

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

スクリプトは以下をガイドします：

- **Docker インストール**（Dockerが検出された場合に推奨）：イメージソース（Docker Hub / GHCR）、バージョンチャンネル（安定版 / プレリリース版）、ダッシュボード管理パネルの設定、ポートの選択
- **従来のインストール**：仮想環境の自動作成、ErisPulseバージョンの選択、ダッシュボード管理パネルモジュールのオプションインストール

### Dockerを使用する

Dockerイメージには、ErisPulseフレームワークとダッシュボード管理パネルが組み込まれています。

```bash
# docker-compose.ymlをダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# ダッシュボードトークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Docker Hubが利用できませんか？</summary>

GitHub Container Registryイメージを使用するには、`docker-compose.yml`のimageを変更します：

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

起動後、`http://<host>:8000/Dashboard`にアクセスし、設定したトークンでログインします。

### pipを使用したインストール

Pythonのバージョンが3.10以上であることを確認し、pipを使用してインストールします：

```bash
pip install ErisPulse
```

[uv](https://github.com/astral-sh/uv)がインストールされている場合は、`uv pip install ErisPulse`を使用すると、より高速にインストールできます。

## プロジェクトの初期化

### インタラクティブな初期化（推奨）

```bash
epsdk init
```

これによりインタラクティブなウィザードが起動し、以下をガイドします：
- プロジェクト名の設定
- ログレベルの設定
- サーバー設定（ホストとポート）
- アダプターの選択と設定
- プロジェクト構造の作成

### クイック初期化

```bash
# プロジェクト名を指定したクイックモード
epsdk init -q -n my_bot

# またはプロジェクト名のみを指定
epsdk init -n my_bot
```

### プロジェクトの手動作成

手動でプロジェクトを作成したい場合は以下を実行します：

```bash
mkdir my_bot && cd my_bot
epsdk init
```

## モジュールのインストール

### CLI経由でのインストール

```bash
epsdk install Yunhu AIChat
```

### 利用可能なモジュールの確認

```bash
epsdk list-remote
```

### インタラクティブなインストール

パッケージ名を指定せずに実行すると、インタラクティブなインストール画面に入ります：

```bash
epsdk install
```

## プロジェクトの実行

```bash
# 通常の実行
epsdk run main.py

# ホットリロードモード（開発時に推奨）
epsdk run main.py --reload
```

## プロジェクト構造

初期化後のプロジェクト構造：

```
my_bot/
├── config/
│   └── config.toml          # 設定ファイル
└── main.py                  # エントリファイル

```

## 設定ファイル

基本的な`config.toml`の設定：

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# アダプターの設定
```

## 次のステップ

- [スタートガイド概要](getting-started/README.md) - ErisPulseの基本概念を理解する
- [最初のボットを作成](getting-started/first-bot.md) - シンプルなボットを作成する
- [ユーザーガイド](user-guide/) - 設定やモジュール管理を深く理解する
- [開発者ガイド](developer-guide/) - カスタムモジュールやアダプターを開発する