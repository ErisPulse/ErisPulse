# 部署ガイド

> [!TIP]
> **このドキュメントを読むべきタイミング**：ロボットを長期間稼働させる場合に必要です。Dockerでのデプロイ、systemd / Supervisorによるプロセス監視、リバースプロキシとSSL、バックアップとアップグレードはすべてここに記載されています。ローカル開発やデバッグの段階では不要です。

ロボットの開発が完了したのは始まりに過ぎません。このドキュメントでは、サーバー上で安定して稼働させるために必要な3つのデプロイ方法（Docker / systemd / Supervisor）、およびリバースプロキシ、セキュリティ強化、バックアップについて説明します。

## Docker 部署（推奨）

ErisPulse は公式の Docker イメージを提供しており、ErisPulse フレームワークと Dashboard 管理パネルが内蔵されており、`linux/amd64` および `linux/arm64` アーキテクチャをサポートしています。

### 速攻起動

```bash
# イメージを取得
docker pull erispulse/erispulse:latest

# docker-compose.yml をダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboard のログイントークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

起動後、`http://localhost:8000/Dashboard` にアクセスし、設定したトークンをパスワードとしてログインします。

### 国内用のイメージ加速

Docker Hub にアクセスできない場合は、GitHub Container Registry を使用してイメージを取得できます：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

ghcr.io のイメージを使用する場合、`docker-compose.yml` の `image` を変更する必要があります：

```yaml
services:
  erispulse:
    image: ghcr.io/erispulse/erispulse:latest
```

### docker-compose.yml

```yaml
services:
  erispulse:
    image: erispulse/erispulse:${ERISPULSE_TAG:-latest}
    container_name: ${CONTAINER_NAME:-erispulse}
    ports:
      - "${ERISPULSE_PORT:-8000}:8000"
    volumes:
      - ./config:/app/config
      # 永続化 Python パッケージディレクトリ
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - LANG=${LANG:-en_US.UTF-8}
      - ERISPULSE_LANG=${ERISPULSE_LANG:-}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    init: true
    # シグナル処理による優雅な停止（SIGTERM）、ここでは停止の猶予期間のみ制御
    stop_grace_period: 30s
    restart: on-failure:5
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

> 以上はリポジトリのルートにある [docker-compose.yml](https://github.com/ErisPulse/ErisPulse/blob/main/docker-compose.yml) と同一です（リポジトリのバージョンには、イメージ加速と環境変数に関する注釈が追加されています）。直接ダウンロードして使用することを推奨します。

### 環境変数

| 変数 | デフォルト値 | 説明 |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Dashboard のポートマッピング |
| `ERISPULSE_TAG` | `latest` | イメージタグ（バージョンを固定したい場合は具体的なバージョン番号を指定） |
| `CONTAINER_NAME` | `erispulse` | コンテナ名（複数インスタンスを展開する場合、インスタンスを識別） |
| `ERISPULSE_DASHBOARD_TOKEN` | 自動生成 | Dashboard のログイントークン（強く設定することを推奨） |
| `TZ` | `Asia/Shanghai` | タイムゾーン |
| `LANG` | `en_US.UTF-8` | システム言語、起動時のインターフェース言語を自動検出 |
| `ERISPULSE_LANG` | 空 | 起動時のインターフェース言語を強制指定：`zh` / `zh_TW` / `en` / `ja` / `ru`（`LANG` を上書き） |

### データの永続化

`./config` ディレクトリは設定ファイルとデータベースをマウントしており、以下の内容を含みます：

- `config/config.toml` — 設定ファイル
- `config/config.db` — SQLite によるデータベース
- `config/.packages` — Python site-packages の永続化ボリューム、フレームワーク、アダプター、およびインストールされたモジュールを保存（最初の起動時にエントリーポイントがイメージ内に含まれるバックアップから自動的に初期化され、以降のモジュールのインストールやフレームワークのホットアップデートはこのディレクトリに書き込まれます）

> **フレームワークのアップグレード（pre/rc 含む）とイメージの自己修復**：エントリーポイントは、コンテナの起動時に毎回コアパッケージの整合性を自己チェックし、破損した場合は「ユーザーがインストールしたバージョンを優先」する原則で修復します。永続ボリューム内に明示的にインストールまたはアップグレードされたバージョン（例：Dashboard でインストールした pre バージョン）は、PyPI から**同じバージョンを再インストール**し、静かにイメージ内に含まれるバージョンにロールバックすることはありません。したがって、Dashboard でフレームワークをアップグレードした後、任意回のコンテナ再起動でも目標バージョンが維持されます。

## Dashboard 管理パネル

ErisPulse Docker イメージには、Web 可視化管理インターフェースを提供する Dashboard モジュールが内蔵されています。

### 機能概要

| 機能 | 説明 |
|------|------|
| ダッシュボード | システム概要、CPU/メモリ監視、実行時間、イベント統計 |
| ロボット管理 | 各プラットフォームのロボットのオンライン状態と情報を表示 |
| イベントの表示 | 実時イベントストリーム、タイプとプラットフォームでフィルタリング可能 |
| ログの表示 | モジュールとレベルでフィルタリングされたログビューアー |
| モジュール管理 | インストールされたモジュールとアダプタを表示、ロード、アンロード |
| モジュールストア | リモートで利用可能なパッケージを閲覧し、ワンクリックでインストール |
| 設定編集 | `config.toml` のオンライン編集 |
| ストレージ管理 | Key-Value ストレージデータの閲覧と編集 |
| バックアップ | 設定とストレージデータのエクスポート/インポート |
| 審計ログ | すべての管理操作を記録 |

### Dashboard からモジュールをインストール

Dashboard にはモジュールストア機能が統合されており、以下の方法でモジュールをインストールできます：

1. **ストアからインストール**：リモートのモジュールリストを閲覧し、必要なモジュールをワンクリックでインストール
2. **ローカルパッケージのアップロード**：`.whl` または `.zip` ファイルを直接アップロードしてインストールし、開発中のモジュールをテストするのに便利です

> **モジュール開発者の高速テストフロー**：Docker 部署後、Dashboard の「ローカルパッケージのアップロード」機能を使って、ビルドした `.whl` ファイルを直接アップロードしてテストできます。コンテナの手動操作は不要です。

## プロセス監督とハードリスタート

ErisPulse のハードリスタート（`sdk.hard_restart()`）は、**外部監督者**がプロセスの終了コードが 42 のときにプロセスを再起動することに依存しています。SDK 自身は新しいプロセスを起動しません。本番環境では監督者の設定が必須です。監督者が設定されていない場合、ハードリスタート後にプロセスは自動的に復帰しません：

- Docker：公式の compose では `restart: on-failure:5` を使用しています。これは、非ゼロの終了コードでプロセスを再起動します（ハードリスタートの終了コード 42 を上書きします）。連続5回の上限は、無限ループを防ぐためです。再起動回数を無制限にしたい場合は、`unless-stopped` に変更してください。
- systemd：`Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord：42 を再起動可能な終了コードに追加します。
- 純粋な Python によるカスタム監督者：`Popen` のループ + `returncode == 42` の検出

各監督者の完全な設定例と終了コード 42 の契約内容については、[起動プロセス → 監督者ガイド](../advanced/startup.md#監督者ガイド)をご覧ください。

## ヘルスチェック

SDK には、ヘルスチェック用エンドポイントが内蔵されています：

```bash
# ヘルスチェック
curl http://localhost:8000/health
```

公式の docker-compose.yml には、以下のヘルスチェックが既に内蔵されています。独自の compose ファイルを作成する際には、こちらを参考にしてください：

```yaml
services:
  erispulse:
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

## リバースプロキシ

Nginx などのリバースプロキシを使用して Dashboard を公開する必要がある場合：

```nginx
server {
    listen 80;
    server_name bot.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket 支援（Dashboard の実時イベントストリームが必要）
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

SSL には Let's Encrypt を使用できます：

```bash
sudo certbot --nginx -d bot.example.com
```

## 手動デプロイ（pip）

Docker を使用しない場合、手動でデプロイすることも可能です。

### 本番環境の設定

```toml
# config/config.toml

[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"
log_files = ["app.log"]
memory_limit = 5000

[ErisPulse.framework]
enable_lazy_loading = true
```

### systemd (Linux)

`/etc/systemd/system/erispulse-bot.service` を作成：

```ini
[Unit]
Description=ErisPulse Bot
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/opt/erispulse-bot
ExecStart=/opt/erispulse-bot/venv/bin/epsdk run main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

管理：

```bash
sudo systemctl daemon-reload
sudo systemctl start erispulse-bot
sudo systemctl enable erispulse-bot
sudo journalctl -u erispulse-bot -f
```

### Supervisor

`/etc/supervisor/conf.d/erispulse-bot.conf` を作成：

```ini
[program:erispulse-bot]
command=/opt/erispulse-bot/venv/bin/python -m ErisPulse run main.py
directory=/opt/erispulse-bot
user=bot
autostart=true
autorestart=true
stderr_logfile=/var/log/erispulse-bot/err.log
stdout_logfile=/var/log/erispulse-bot/out.log
```

### uv tool による分離デプロイ（CLI とプロジェクト環境の分離）

`uv tool install` は `epsdk` を**独立したツール環境**としてインストールし、CLI 自身とプロジェクト依存関係を完全に分離します：CLI のアップグレードはプロジェクトの `.venv` に影響を与えず、プロジェクトの依存関係の変更も CLI に影響を与えません。

```bash
# 1. グローバルに CLI をインストール（自動的に epsdk / ep コマンドを公開）
uv tool install ErisPulse

# 2. プロジェクト内にロボットの依存関係のみを配置（.venv は uv で管理）
cd /opt/erispulse-bot
uv add erispulse ErisPulse-Adapter-Yunhu   # 必要に応じてアダプタを追加

# 3. CLI を使用して実行（プロジェクトの .venv に含まれる解釈子を自動的に検出）
epsdk run main.py
```

動作の要点：

- `epsdk run` の対象解釈子の検出順序：`ERISPULSE_PYTHON` 環境変数 → プロジェクトの `.venv` → 現在の解釈子；ツール環境自体は CLI にのみ対応し、コンポーネント（アダプタ/モジュール）はプロジェクトの `.venv` にインストールする必要があります
- `epsdk install` / `uninstall` / `upgrade` / `list` はすべてプロジェクトの `.venv` に作用し、ツール環境を汚染しません
- CLI のアップグレード：`uv tool upgrade ErisPulse`（または `epsdk self-update` を直接実行し、uv tool 環境では自動的に `uv tool upgrade` に切り替わります）；プロジェクトの依存関係のアップグレード：プロジェクトディレクトリ内で `uv sync` / `uv add` を実行し、互いに影響しません
- サーバー環境では、ツール環境は uv で統一管理されます（`uv tool list` で確認、`uv tool upgrade --all` で一括アップグレード）；グローバルな pip パッケージの手動管理は不要です
- プロジェクトのないディレクトリで `uv run epsdk ...` を実行した場合、一時的な隔離環境に移行し、インストールされたコンポーネントは永続化されません；サーバーでは常に `epsdk` を直接呼び出すか、まず `cd` でプロジェクトディレクトリに移動してください

## セキュリティに関する推奨事項

1. **Dashboard トークンの設定**：強力なランダムなトークンを使用し、デフォルト値は使用しないでください。
2. **ポートをインターネットに公開しない**：リバースプロキシ + SSL を使用しない限り、Dashboard のポートをローカルネットワーク内に限定してください。
3. **データディレクトリを保護する**：`config/` ディレクトリには設定とデータベースが含まれているため、適切なファイル権限を設定してください。
4. **定期的なアップデート**：`epsdk self-update` を使用するか、最新の Docker イメージを取得してください。
5. **root で実行しない**：手動でデプロイする場合は、専用のユーザーを作成してください。
6. **Docker の再起動ポリシーを使用する**：公式の compose では `restart: on-failure:5` が設定されており、エラー終了（ハードリスタート終了コード 42 を含む）後に自動的に再起動されます。

## 複数インスタンスのデプロイ

複数のロボットインスタンスを実行する場合：

1. 各インスタンスは独立したプロジェクトディレクトリと `docker-compose.yml` を使用する
2. 異なるポート番号を使用する：`ERISPULSE_PORT=8001`
3. 異なるコンテナ名を使用する：`container_name: erispulse-bot2`

## 更新とメンテナンス

### Docker 方式

```bash
# 最新のイメージを取得
docker compose pull

# 新しいイメージを使用して再起動
docker compose up -d
```

### pip 方式

```bash
epsdk self-update
epsdk upgrade
```

### uv tool 方式

```bash
# CLI ツール環境をアップグレード
uv tool upgrade ErisPulse

# プロジェクト依存関係のアップグレード（プロジェクトディレクトリ内で実行）
uv sync
```

### 実行時ホットリロードでサーバーの設定を再読み込み

リスニングアドレス / ポート / SSL 証明書を変更した後、プロセスを再起動せずに実行できます。任意のコルーチン内で `router.reload()` を呼び出します：

```python
await sdk.router.reload(port=9000)                                # ポートを変更
await sdk.router.reload(ssl_cert=new_pem, ssl_key=new_key)        # 証明書のホット交換（証明書の更新シナリオ）
await sdk.router.reload(host="0.0.0.0", port=9000)                # 省略されたパラメータは現在の設定を引き継ぐ
```

- 同じ FastAPI アプリケーションを再利用し、モジュールが登録した HTTP / WebSocket / SSE ルートはすべて保持されます
- 新しい設定（証明書の構築、ポートの利用可能）を検証してから切り替えます。失敗した場合は、古い設定でサービスを復元して `False` を返し、`False` の返却は古いサービスが利用可能であることを保証します
- サーバーが実行されていない場合は `False` を返します（最初の起動は `sdk.router.start()` を使用してください）

### バックアップ

定期的に `config/` ディレクトリをバックアップします：

```bash
# Docker 部署の場合
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# または Dashboard の「バックアップ」機能を使用してエクスポート
```

## 次に進む

- **可視化管理したい場合**：[ErisPulse-Dashboard](../ecosystem/dashboard.md) をインストールし、ブラウザ上でモジュールを管理し、ログを確認し、設定を変更します。
- **環境に問題があると疑う場合**：まず `epsdk doctor` を実行して健全性レポートを出力します。[CLI コマンドリファレンス · doctor](cli-reference.md#doctor) を参照してください。
- **フレームワークとコンポーネントの設定を調整したい場合**：[設定ファイルの説明](configuration.md)を確認してください。環境変数によるオーバーライドは特にコンテナデプロイに適しています。