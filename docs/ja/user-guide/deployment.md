# 部署ガイド

ErisPulse ロボットを本番環境にデプロイするためのベストプラクティス。

## Docker 部署（推奨）

ErisPulse は公式の Docker イメージを提供しており、ErisPulse フレームワークと Dashboard 管理パネルが内蔵されています。`linux/amd64` および `linux/arm64` アーキテクチャをサポートしています。

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

`ghcr.io` のイメージを使用する場合、`docker-compose.yml` の `image` を変更する必要があります：

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
      # Python パッケージディレクトリの永続化
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    init: true
    stop_grace_period: 30s
    restart: unless-stopped
```

> 上記の設定および健全性チェック、タイムゾーンと言語環境変数が含まれている、リポジトリのルートにある [docker-compose.yml](https://github.com/ErisPulse/ErisPulse/blob/main/docker-compose.yml) を直接使用することを推奨します。

### 環境変数

| 変数 | デフォルト値 | 説明 |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Dashboard のポートマッピング |
| `ERISPULSE_DASHBOARD_TOKEN` | 自動生成 | Dashboard のログイントークン（強く設定することを推奨） |
| `TZ` | `Asia/Shanghai` | タイムゾーン |
| `LANG` | `en_US.UTF-8` | システム言語、起動時の言語を自動検出 |
| `ERISPULSE_LANG` | 空 | 起動時の言語を強制指定：`zh` / `zh_TW` / `en` / `ja` / `ru`（`LANG` を上書き） |

### データの永続化

`./config` ディレクトリは設定ファイルとデータベースをマウントしており、以下の内容を含んでいます：

- `config/config.toml` — 設定ファイル
- `config/config.db` — SQLite ストレージデータベース
- `config/.packages` — Python site-packages の永続化ボリューム、フレームワーク、アダプター、およびインストールされたモジュールを保存（初期起動時にエントリポイントがイメージ内に含まれるバックアップから自動的に初期化し、その後のモジュールインストールやフレームワークのホットアップデートはこのディレクトリに書き込まれます）

> **フレームワークのアップグレード（pre/rc を含む）とイメージの自己修復**：エントリポイントは、各コンテナ起動時に、コアパッケージの整合性を自動的にチェックします。破損した場合、"ユーザーがインストールしたバージョンを優先"する原則に基づき、修復が行われます。永続ボリューム内に明示的にインストール/アップグレードされたバージョン（例：Dashboard でインストールされた pre バージョン）は、PyPI から**同バージョンを再インストール**されます。静かにイメージ内に含まれるバージョンに戻ることはありません。したがって、Dashboard でフレームワークをアップグレードした後、任意回のコンテナ再起動でも、目標バージョンを維持することができます。

## Dashboard 管理面板

ErisPulse Docker イメージには、Web による視覚化管理インターフェースを提供する Dashboard モジュールが内蔵されています。

### 機能概要

| 機能 | 説明 |
|------|------|
| 仪表盘 | システム概要、CPU/メモリ監視、稼働時間、イベント統計 |
| ロボット管理 | 各プラットフォームのロボットのオンライン状態と情報を表示 |
| 事件表示 | 実時イベントストリーム、タイプやプラットフォームでフィルタリング可能 |
| ログ表示 | モジュールとレベルでフィルタリング可能なログビューア |
| モジュール管理 | インストール済みのモジュールとアダプターの表示、読み込み、アンロード |
| モジュールストア | リモートで利用可能なパッケージを閲覧し、ワンクリックでインストール |
| 設定編集 | `config.toml` のオンライン編集 |
| ストレージ管理 | Key-Value ストレージデータの閲覧と編集 |
| バックアップ | 設定とストレージデータのエクスポート/インポート |
| 審計ログ | すべての管理操作を記録 |

### Dashboard によるモジュールのインストール

Dashboard にはモジュールストア機能が統合されており、以下の方法でモジュールをインストールできます。

1. **ストアからインストール**：リモートのモジュールリストを閲覧し、必要なモジュールを選択してワンクリックでインストール
2. **ローカルのパッケージをアップロード**：`.whl` または `.zip` ファイルを直接アップロードしてインストール。個人開発のモジュールをテストする際に便利です。

> **モジュール開発者のための迅速なテストフロー**：Docker でデプロイ後、Dashboard の「ローカルパッケージのアップロード」機能を使って、ビルドした `.whl` ファイルを直接アップロードしてテストを行えます。コンテナの手動操作は不要です。

## プロセス監督とハードリスタート

ErisPulse のハードリスタート（`sdk.hard_restart()`）は、**外部監督者**がプロセスの終了コードが 42 のときにプロセスを再起動することに依存しています。SDK 自体は新しいプロセスを起動しません。本番環境では監督者の設定を必須とし、そうでなければハードリスタート後にプロセスが自動的に復旧しません。

- Docker: `restart: unless-stopped`（終了コードが何であれ、42 を含むすべての終了コードで再起動）
- systemd: `Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord: 42 を再起動可能な終了コードに追加
- 純粋な Python によるカスタム監督者: `Popen` のループ + `returncode == 42` の検出

各監督者の完全な設定例と終了コード 42 の契約に関する説明は、[起動フロー → 監督者ガイド](../advanced/startup.md#監督者ガイド)をご覧ください。

## ヘルスチェック

SDK には、ヘルスチェック用エンドポイントが内蔵されています：

```bash
# ヘルスチェック
curl http://localhost:8000/health
```

Docker でのヘルスチェックは、`docker-compose.yml` に追加することで設定できます：

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

Nginx などのリバースプロキシを使用してダッシュボードを公開する必要がある場合：

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

    # WebSocket のサポート（ダッシュボードのリアルタイムイベントストリームが必要）
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

Docker を使わずに、手動でデプロイすることも可能です。

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

1. **Dashboard トークンの設定**：強力なランダムトークンを使用し、デフォルト値を使用しないでください。
2. **ポートをパブリックに公開しない**：リバースプロキシ + SSL を使用しない限り、Dashboard のポートをローカルネットワークに制限してください。
3. **データディレクトリを保護する**：`config/` ディレクトリには設定とデータベースが含まれているため、適切なファイル権限を設定してください。
4. **定期的なアップデート**：`epsdk self-update` を使用するか、最新の Docker イメージを取得してください。
5. **root で実行しない**：手動でデプロイする場合は、専用のユーザーを作成してください。
6. **Docker のリスタートポリシーを使用する**：`restart: unless-stopped` を使用して、異常終了後に自動的に再起動するようにしてください。

## 多インスタンスデプロイ

複数のロボットインスタンスを実行する場合：

1. 各インスタンスは独立したプロジェクトディレクトリと `docker-compose.yml` を使用します。
2. 異なるポート番号を使用します：`ERISPULSE_PORT=8001`
3. 異なるコンテナ名を使用します：`container_name: erispulse-bot2`

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