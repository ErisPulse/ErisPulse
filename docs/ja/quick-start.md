# クイックスタート

> **これがあなたの最初の一歩です。** 5分で ErisPulse ボットをゼロから構築しましょう。

## ErisPulse のインストール

### クイックインストールスクリプト（推奨）

インストールスクリプトは、環境（Docker、Python、uv）を自動的に検出し、最適なインストール方法を案内します。

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

スクリプトは、以下の手順を案内します。

- **Docker インストール**（Docker を検出した場合に推奨）：レジストリ（Docker Hub / GHCR）、バージョンチャンネル（安定版 / ベータ版）、Dashboard 管理パネルの設定、ポート設定の選択
- **従来のインストール**：仮想環境の自動作成、ErisPulse のバージョン選択、Dashboard 管理パネルモジュールのオプションインストール

### Docker を使用する

Docker イメージには、ErisPulse フレームワークと Dashboard 管理パネルがすでに組み込まれています。

```bash
# docker-compose.yml のダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboard トークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Docker Hub が使用できない場合？</summary>

GitHub Container Registry のイメージを使用するには、`docker-compose.yml` で `image` を以下のように変更します。

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

起動後、`http://<host>:8000/Dashboard` にアクセスし、設定したトークンでログインします。

### pip を使用してインストールする

Python のバージョンが >= 3.10 であることを確認し、pip を使用してインストールします。

```bash
pip install ErisPulse
```

[uv](https://github.com/astral-sh/uv) を既にインストールしている場合は、`uv pip install ErisPulse` を使用することもできます。こちらの方がインストール速度が速いです。

## プロジェクトの初期化

### インタラクティブ初期化（推奨）

```bash
epsdk init
```

これによりインタラクティブなウィザードが起動し、以下の手順をガイドします：
- プロジェクト名の設定
- ログレベルの設定
- サーバー設定（ホストとポート）
- アダプタの選択と設定
- プロジェクト構造の作成

### クイック初期化

```bash
# プロジェクト名を指定するクイックモード
epsdk init -q -n my_bot

# またはプロジェクト名のみ指定
epsdk init -n my_bot
```

### 手動でのプロジェクト作成

手動でプロジェクトを作成する場合：

```bash
mkdir my_bot && cd my_bot
epsdk init

## モジュールのインストール

### CLI によるインストール

```bash
epsdk install Yunhu AIChat
```

### 使用可能なモジュールを確認する

```bash
epsdk list-remote
```

### インタラクティブなインストール

パッケージ名を指定しない場合、インタラクティブなインストール画面に入ります：

```bash
epsdk install

## プロジェクトの実行

```bash
# 通常実行
epsdk run main.py

# リロードモード（開発時におすすめ）
epsdk run main.py --reload

## IDE補完の有効化（オプション）

ErisPulse の動的発見モジュール/アダプタについて、IDE はデフォルトでプラットフォーム固有のメソッドを補完できません。
次のコマンドを実行して型スタブを生成します。

```bash
epsdk types
```

生成後、インポートした型を変数としてアノテーションすれば、正確な補完が得られます（詳細は [IDE 補完ガイド](docs/ja/getting-started/ide-completion.md) を参照）：

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # プラットフォーム固有のメソッドを補完

## プロジェクト構造

初期化後のプロジェクト構造：

```
my_bot/
├── config/
│   └── config.toml          # 設定ファイル
└── main.py                  # エントリーポイント

## 設定ファイル

基本的な `config.toml` 設定：

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# アダプタ設定

## 次のステップ

ロボットが起動した後、必要に応じて以下を続行できます：

**フレームワークの仕組みを知りたい？**
- [基本概念](getting-started/basic-concepts.md) — アダプタ / モジュール / イベント の設計
- [アーキテクチャ概要](architecture.md) — 可視化アーキテクチャ図

**より多くの機能を実装したい？**
- [一般的なタスクの例](getting-started/common-tasks.md) — ストレージ、定期タスク、権限制御
- [イベント処理の入門](getting-started/event-handling.md) — メッセージ、通知、リクエスト処理

**独自のモジュール / アダプタを開発したい？**
- [モジュール開発の入門](developer-guide/modules/getting-started.md)
- [アダプタ開発の入門](developer-guide/adapters/getting-started.md)

**必要に応じて参照：**
- [設定ファイルの説明](user-guide/configuration.md) · [CLI コマンド](user-guide/cli-reference.md) · [デプロイメントガイド](user-guide/deployment.md)