# クイックスタート

> **これが最初の一歩です。** ErisPulse ボットを 5 分でゼロから起動させましょう。

## ErisPulse のインストール

### クイックインストールスクリプト（推奨）

インストールスクリプトは、Docker、Python、uv などの環境を自動検出し、最適なインストール方法を案内します。

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

スクリプトは以下のステップをガイドします：

- **Docker のインストール**（Docker を検出した場合に推奨）：イメージリポジトリ（Docker Hub / GHCR）、バージョンチャンネル（安定版 / 須公開版）、Dashboard 管理パネルの設定、ポート設定
- **従来型のインストール**：仮想環境の自動作成、ErisPulse バージョンの選択、Dashboard 管理パネルモジュールのオプションインストール

### Docker を使用する

Docker イメージには ErisPulse フレームワークと Dashboard 管理パネルが内蔵されています。

```bash
# docker-compose.yml のダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboard トークンの設定と起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Docker Hub が利用できませんか？</summary>

GitHub Container Registry のイメージを使用するには、`docker-compose.yml` 内の image を次のように変更します：

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

起動後、`http://<host>:8000/Dashboard` にアクセスし、設定したトークンでログインします。

### pip を使用してインストールする

Python のバージョンが >= 3.10 であることを確認し、pip を使用してインストールします：

```bash
pip install ErisPulse
```

[uv](https://github.com/astral-sh/uv) を既にインストールしている場合は、`uv pip install ErisPulse` を使用することもでき、インストールが高速になります。

## プロジェクトの初期化

### インタラクティブな初期化（推奨）

```bash
epsdk init
```

これにより、インタラクティブなウィザードが起動し、以下の設定をガイドします：
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

### 手動でプロジェクトを作成する

手動でプロジェクトを作成する場合は：

```bash
mkdir my_bot && cd my_bot
epsdk init
```

## モジュールのインストール

### CLI からインストール

```bash
epsdk install Yunhu AIChat
```

### 利用可能なモジュールを表示

```bash
epsdk list-remote
```

### インタラクティブなインストール

パッケージ名を指定しない場合、インタラクティブなインストール画面が開きます：

```bash
epsdk install
```

## プロジェクトの実行

```bash
# 通常の実行
epsdk run main.py

# ホットリロードモード（開発時推奨）
epsdk run main.py --reload
```

## IDE 自動補完の有効化（オプション）

ErisPulse は動的にモジュール/アダプターを検出するため、IDE はデフォルトではプラットフォーム固有のメソッドを補完できません。
以下のコマンドを実行して型スタブを生成します：

```bash
epsdk types
```

生成後、インポートした型を変数の型として指定すると、正確な補完が利用可能になります（詳細は [IDE 自動補完ガイド](docs/ja/getting-started/ide-completion.md) を参照してください）：

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # プラットフォーム固有のメソッドの補完
```

## プロジェクト構造

初期化後のプロジェクト構造：

```
my_bot/
├── config/
│   └── config.toml          # 設定ファイル
└── main.py                  # エントリーファイル

```

## 設定ファイル

基本的な `config.toml` 設定：

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

ボットを動かしたら、必要に応じて続けることができます。

**フレームワークの仕組みについて知りたい？**
- [基礎概念](docs/ja/getting-started/basic-concepts.md) — アダプター / モジュール / イベント の設計
- [アーキテクチャ概要](docs/ja/architecture.md) — アーキテクチャ図の可視化

**より多くの機能を実装したい？**
- [一般的なタスクの例](docs/ja/getting-started/common-tasks.md) — ストレージ、定期タスク、権限管理
- [イベント処理入門](docs/ja/getting-started/event-handling.md) — メッセージ、通知、リクエスト処理

**独自のモジュール / アダプターを開発したい？**
- [モジュール開発入門](docs/ja/developer-guide/modules/getting-started.md)
- [アダプター開発入門](docs/ja/developer-guide/adapters/getting-started.md)

**必要に応じて参照：**
- [設定ファイルの説明](docs/ja/user-guide/configuration.md) · [CLI コマンド](docs/ja/user-guide/cli-reference.md) · [デプロイガイド](docs/ja/user-guide/deployment.md)