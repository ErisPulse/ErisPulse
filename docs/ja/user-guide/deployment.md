# 部署ガイド

ErisPulse ロボットを本番環境にデプロイするためのベストプラクティス。

## Docker 部署（推奨）

ErisPulse は、ErisPulse フレームワークと Dashboard 管理パネルを内蔵した公式の Docker イメージを提供しており、`linux/amd64` および `linux/arm64` アーキテクチャをサポートしています。

### 速攻起動

```bash
# イメージの取得
docker pull erispulse/erispulse:latest

# docker-compose.yml のダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboard のログイントークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

起動後、`http://localhost:8000/Dashboard` にアクセスし、設定したトークンをパスワードとしてログインしてください。

### 国内用のイメージ加速

Docker Hub にアクセスできない場合は、GitHub Container Registry を使ってイメージを取得できます：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

ghcr.io のイメージを使用する場合は、`docker-compose.yml` の `image` を変更する必要があります：

```yaml
services:
  erispulse:
    image: ghcr.io/erispulse/erispulse:latest
```

### docker-compose.yml

```yaml
services:
  erispulse:
    image: erispulse/erispulse:latest
    container_name: erispulse
    ports:
      - "${ERISPULSE_PORT:-8000}:8000"
    volumes:
      - ./config:/app/config
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    restart: unless-stopped
```

### 環境変数

| 変数 | デフォルト値 | 説明 |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Dashboard のポートマッピング |
| `ERISPULSE_DASHBOARD_TOKEN` | 自動生成 | Dashboard のログイントークン（設定を強く推奨） |
| `TZ` | `Asia/Shanghai` | タイムゾーン |

### データの永続化

`./config` ディレクトリは、設定ファイルとデータベースをマウントしており、以下を含みます：

- `config/config.toml` — 設定ファイル
- `config/config.db` — SQLite ストレージデータベース
- `config/.packages` — Python site-packages の永続化ボリューム。フレームワーク、アダプター、およびインストール済みモジュールを保存します（最初の起動時にエントリポイントがイメージ内に含まれるバックアップから自動的に初期化され、その後のモジュールインストールとフレームワークのホットアップデートはこのディレクトリに書き込まれます）。

## Dashboard 管理面板

ErisPulse Docker イメージには、Web による視覚化管理インターフェースを提供する Dashboard モジュールが内蔵されています。

### 機能概要

| 機能 | 説明 |
|------|------|
| 仪表盘 | システム概要、CPU/メモリの監視、稼働時間、イベント統計 |
| ロボット管理 | 各プラットフォームのロボットのオンライン状態と情報を表示 |
| 事件查看 | 実時イベントのストリーム、タイプやプラットフォームごとのフィルタリングが可能 |
| ログ查看 | モジュールとレベルごとのフィルタリングが可能なログビューア |
| モジュール管理 | インストール済みのモジュールとアダプターの表示、読み込み、アンロード |
| モジュールストア | リモートで利用可能なパッケージを閲覧し、ワンクリックでインストール可能 |
| 配置編集 | `config.toml` のオンライン編集 |
| ストレージ管理 | キー値ストアデータの閲覧と編集 |
| バックアップ | 設定とストレージデータのエクスポート/インポート |
| 審計ログ | すべての管理操作の記録 |

### Dashboard によるモジュールのインストール

Dashboard にはモジュールストア機能が統合されており、以下の方法でモジュールをインストールできます。

1. **ストアからインストール**：リモートのモジュールリストを閲覧し、必要なモジュールを選択してワンクリックでインストール
2. **ローカルパッケージのアップロード**：`.whl` または `.zip` ファイルを直接アップロードしてインストール。個人開発のモジュールをテストするのに便利です。

> **モジュール開発者のための迅速なテストフロー**：Docker でデプロイした後、Dashboard の「ローカルパッケージのアップロード」機能を使用して、ビルドした `.whl` ファイルを直接アップロードしてテストできます。コンテナを手動で操作する必要がありません。

## プロセス監督とハードリスタート

ErisPulse のハードリスタート (`sdk.hard_restart()`) は、**外部の監督者**がプロセスの終了コードが 42 のときにプロセスを再起動することに依存しています。SDK 自身は新しいプロセスを起動しません。本番環境では監督者の設定が必須です。監督者が設定されていない場合、ハードリスタート後にプロセスは自動的に復旧しません。

- Docker: `restart: unless-stopped`（終了コードが 42 を含む場合もすべて再起動）
- systemd: `Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord: 42 を再起動可能な終了コードに追加
- 純粋な Python によるカスタム監督者: `Popen` のループ + `returncode == 42` の検出

各監督者の完全な設定例と終了コード 42 の契約に関する説明は、[起動プロセス → 監督者ガイド](../advanced/startup.md#監督者ガイド)をご覧ください。

## ヘルスチェック

SDK には、ヘルスチェック用エンドポイントが内蔵されています。

```bash
# ヘルスチェック
curl http://localhost:8000/health
```

Docker でのヘルスチェックは、`docker-compose.yml` に追加することで可能です。

```yaml
services:
  erispulse:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## リバースプロキシ

Nginx などのリバースプロキシ経由で Dashboard を公開する必要がある場合：

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

    # WebSocket のサポート（Dashboard のリアルタイムイベントストリームが必要）
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

SSL は Let's Encrypt を使用できます：

```bash
sudo certbot --nginx -d bot.example.com
```

## 手動デプロイ（pip）

Docker を使用しない場合でも、手動でデプロイすることができます。

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

`/etc/systemd/system/erispulse-bot.service` を作成します：

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

管理コマンド：

```bash
sudo systemctl daemon-reload
sudo systemctl start erispulse-bot
sudo systemctl enable erispulse-bot
sudo journalctl -u erispulse-bot -f
```

### Supervisor

`/etc/supervisor/conf.d/erispulse-bot.conf` を作成します：

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

## セキュリティに関する推奨事項

1. **Dashboard トークンの設定**：強力なランダムなトークンを使用し、デフォルト値は使用しないでください。
2. **ポートをパブリックに公開しない**：リバースプロキシ + SSL を使用しない限り、Dashboard のポートをローカルネットワークに限定してください。
3. **データディレクトリの保護**：`config/` ディレクトリには設定情報やデータベースが含まれているため、適切なファイル権限を設定してください。
4. **定期的なアップデート**：`epsdk self-update` を使用するか、最新の Docker イメージをプルしてください。
5. **root で実行しない**：手動でデプロイする場合は、専用のユーザーを作成してください。
6. **Docker のリスタートポリシーの使用**：`restart: unless-stopped` を使用して、異常終了後に自動的に再起動されるようにしてください。

## マルチインスタンスデプロイ

複数のロボットインスタンスを実行する場合：

1. 各インスタンスは独立したプロジェクトディレクトリと `docker-compose.yml` を使用します。
2. 異なるポート番号を使用します: `ERISPULSE_PORT=8001`
3. 異なるコンテナ名を使用します: `container_name: erispulse-bot2`

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

### バックアップ

`config/` ディレクトリを定期的にバックアップしてください：

```bash
# Docker 部署の場合
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# または Dashboard の「バックアップ」機能を使用してエクスポート
```