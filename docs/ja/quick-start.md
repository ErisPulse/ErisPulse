# 速習

> 理解できない用語に出会いましたか？ [用語集](terminology.md) を参照してわかりやすい説明を入手してください。

## ErisPulse のインストール

### 1 クリックインストールスクリプト（推奨）

インストールスクリプトは、環境（Docker、Python、uv）を自動的に検出し、最適なインストール方法を選択します。

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

スクリプトは以下の手順をガイドします：

- **Docker インストール**（Docker が検出された場合推奨）：イメージソース（Docker Hub / GHCR）、バージョンチャネル（安定版 / プリリリース版）、Dashboard 管理パネルの設定、ポート設定
- **従来のインストール**：仮想環境の自動作成、ErisPulse バージョンの選択、オプションで Dashboard 管理パネルモジュールのインストール

### Docker を使用する

Docker イメージには、ErisPulse フレームワークと Dashboard 管理パネルが既に含まれています。

```bash
# docker-compose.yml をダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboard トークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Docker Hub が利用できない場合？</summary>

GitHub Container Registry イメージを使用する場合は、`docker-compose.yml` の image を次のように変更します：

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

起動後、`http://<host>:8000/Dashboard` にアクセスし、設定したトークンでログインします。

### pip を使用したインストール

Python のバージョンが 3.10 以上であることを確認し、pip を使用してインストールします：

```bash
pip install ErisPulse
```

既に [uv](https://github.com/astral-sh/uv) をインストールしている場合は、`uv pip install ErisPulse` を使用することもでき、インストール速度が速くなります。

## プロジェクトの初期化

### インタラクティブ初期化（推奨）

```bash
epsdk init
```

これにより、インタラクティブなガイドが開始され、以下の手順がガイドされます：
- プロジェクト名の設定
- ログレベルの設定
- サーバーの設定（ホストとポート）
- アダプタの選択と設定
- プロジェクト構造の作成

### 速攻初期化

```bash
# プロジェクト名を指定した速攻モード
epsdk init -q -n my_bot

# または、プロジェクト名のみを指定
epsdk init -n my_bot
```

### 手動でプロジェクトを作成する

手動でプロジェクトを作成したい場合は：

```bash
mkdir my_bot && cd my_bot
epsdk init
```

## モジュールのインストール

### CLI でインストールする

```bash
epsdk install Yunhu AIChat
```

### 利用可能なモジュールを表示する

```bash
epsdk list-remote
```

### インタラクティブインストール

パッケージ名を指定しない場合は、インタラクティブインストール画面になります：

```bash
epsdk install
```

## プロジェクトの実行

```bash
# 通常実行
epsdk run main.py

# ホットリロードモード（開発時に推奨）
epsdk run main.py --reload
```

## IDE の補完を有効にする（オプション）

ErisPulse はモジュール/アダプタを動的に発見しますが、IDE はデフォルトではプラットフォーム固有のメソッドを補完できません。以下のコマンドを実行して型のスタブを生成します：

```bash
epsdk types
```

生成後、インポートした型を変数の型として指定することで、正確な補完が得られます（[IDE 補完ガイド](./getting-started/ide-completion.md)を参照してください）：

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
└── main.py                  # エントリーポイント

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
# アダプタの設定
```

## 次のステップ

- [入門ガイド](getting-started/README.md) - ErisPulse の基本概念を理解する
- [最初のボットを作成する](getting-started/first-bot.md) - 簡単なボットを作成する
- [ユーザー使用ガイド](user-guide/) - 設定やモジュール管理について詳しく学ぶ
- [開発者ガイド](developer-guide/) - 自作モジュールやアダプタの開発について学ぶ