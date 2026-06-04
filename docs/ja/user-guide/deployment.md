# デプロイメントガイド

ErisPulse ボットを本番環境にデプロイするためのベストプラクティス。

## Docker デプロイ（推奨）

ErisPulse は公式な Docker イメージを提供しており、ErisPulse フレームワークと Dashboard 管理パネルが内蔵されており、`linux/amd64` および `linux/arm64` アーキテクチャをサポートしています。

### クイックスタート

```bash
# イメージをプル
docker pull erispulse/erispulse:latest

# docker-compose.yml をダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboard ログイントークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

起動後、`http://localhost:8000/Dashboard` にアクセスし、設定したトークンをパスワードとして使用してログインしてください。

### 国内イメージミラーサイトの高速化

Docker Hub にアクセスできない場合は、GitHub Container Registry からイメージをプルできます：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

ghcr.io イメージを使用する場合、`docker-compose.yml` の `image` を変更する必要があります：

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
| `ERISPULSE_PORT` | `8000` | Dashboard ポートマッピング |
| `ERISPULSE_DASHBOARD_TOKEN` | 自動生成 | Dashboard ログイントークン（強く推奨） |
| `TZ` | `Asia/Shanghai` | タイムゾーン |

### データの永続化

`./config` ディレクトリは設定ファイルとデータベースがマウントされており、以下が含まれます：

- `config/config.toml` — 設定ファイル
- `config/config.db` — SQLite ストレージデータベース

## Dashboard 管理パネル

ErisPulse Docker イメージには Dashboard モジュールが内蔵されており、Web での可視化管理インターフェースを提供します。

### 機能の概要

| 機能 | 説明 |
|------|------|
| 仪表盘 | システム概要、CPU/メモリ監視、稼働時間、イベント統計 |
| 机器人管理 | 各プラットフォームのボットのオンライン状態と情報を確認 |
| 事件查看 | リアルタイムイベントストリーム（プラットフォームやタイプによるフィルタリングに対応） |
| 日志查看 | モジュールやレベルでフィルタリングできるログビューア |
| 模块管理 | インストール済みモジュールとアダプターの表示、読み込み、アンロード |
| 模块商店 | リモートで利用可能なパッケージを閲覧し、ワンクリックでインストール |
| 配置编辑 | `config.toml` をオンラインで編集 |
| 存储管理 | Key-Value ストレージデータの閲覧と編集 |
| 备份 | 設定とストレージデータのエクスポート/インポート |
| 审计日志 | すべての管理操作を記録 |

### Dashboard からのモジュールインストール

Dashboard にはモジュールストア機能が統合されており、以下の操作が可能です：

1. **ストアからインストール**: リモートモジュール一覧を参照し、必要なモジュールをワンクリックでインストール
2. **ローカルパッケージをアップロード**: `.whl` または `.zip` ファイルを直接アップロードしてインストールし、個人開発のモジュールを簡単にテストできます

> **モジュール開発者のテストフロー**: Docker でデプロイした後、Dashboard の「ローカルパッケージをアップロード」機能を使用して、ビルドした `.whl` ファイルを直接アップロードしてテストできます。手動でコンテナを操作する必要はありません。

## ヘルスチェック

SDK にはヘルスチェックエンドポイントが内蔵されています：

```bash
# ヘルスチェック
curl http://localhost:8000/health
```

Docker ヘルスチェックは `docker-compose.yml` に追加できます：

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

Nginx などのリバースプロキシを使用して Dashboard を公開する場合：

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

    # WebSocket サポート（Dashboard のリアルタイムイベントストリームに必要）
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

Docker を使用しない場合、手動デプロイも可能です。

### プロダクション環境の設定

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

管理：

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

1. **Dashboard トークンを設定する**: 強力なランダムトークンを使用し、デフォルト値を使用しないでください
2. **ポートをパブリックネットワークに公開しない**: リバースプロキシ + SSL を使用しない限り、Dashboard ポートはイントラネット（社内ネットワーク）に制限してください
3. **データディレクトリを保護する**: `config/` ディレクトリには設定とデータベースが含まれるため、適切なファイル権限を設定してください
4. **定期的な更新**: `epsdk self-update` を使用するか、最新の Docker イメージをプルしてください
5. **root ユーザーで実行しない**: 手動デプロイ時には専用ユーザーを作成してください
6. **Docker 再起動戦略を使用する**: `restart: unless-stopped` を使用して、異常終了後の自動再起動を確保してください

## マルチインスタンスデプロイ

複数のボットインスタンスを実行する場合：

1. 各インスタンスで独立したプロジェクトディレクトリと `docker-compose.yml` を使用する
2. 異なるポート番号を使用する: `ERISPULSE_PORT=8001`
3. 異なるコンテナ名を使用する: `container_name: erispulse-bot2`

## 更新とメンテナンス

### Docker 方式

```bash
# 最新イメージをプル
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

定期的に `config/` ディレクトリをバックアップする：

```bash
# Docker デプロイ
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# または Dashboard の「バックアップ」機能を使用してエクスポート