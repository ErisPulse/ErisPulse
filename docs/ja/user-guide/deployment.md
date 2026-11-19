# 部署ガイド

> [!TIP]
> **この記事を読むべきタイミング**：ロボットを長期間稼働させる場合——Docker 部署、systemd / Supervisor プロセス監視、リバースプロキシと SSL、バックアップとアップグレードはすべてここにあります。ローカル開発やデバッグ段階では必要ありません。

ロボットの開発が完了したのは始まりに過ぎません。この記事では、サーバー上に安定的にホストするための 3 つのデプロイ方法（Docker / systemd / Supervisor）と、リバースプロキシ、セキュリティ強化、バックアップをカバーしています。

## Docker 部署（推奨）

ErisPulse は公式の Docker イメージを提供しており、ErisPulse フレームワークと Dashboard 管理パネルが内蔵されています。`linux/amd64` と `linux/arm64` アーキテクチャをサポートしています。

### 早速起動

```bash
# イメージの取得
docker pull erispulse/erispulse:latest

# docker-compose.yml のダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboard のログイントークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

起動後、`http://localhost:8000/Dashboard` にアクセスし、設定したトークンをパスワードとしてログインします。

### 国内でのイメージ加速

Docker Hub にアクセスできない場合は、GitHub Container Registry を使用してイメージを取得できます：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

`ghcr.io` のイメージを使用する場合、`docker-compose.yml` 内の `image` を変更する必要があります：

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
      # Python パッケージディレクトリの永続化
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - LANG=${LANG:-en_US.UTF-8}
      - ERISPULSE_LANG=${ERISPULSE_LANG:-}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    init: true
    # エレガントなシャットダウンはフレームワーク内のシグナル処理（SIGTERM）で完了、ここでは停止の幅広い時間制限のみ制御
    stop_grace_period: 30s
    restart: on-failure:5
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

> 以上はリポジトリのルートにある [docker-compose.yml](https://github.com/ErisPulse/ErisPulse/blob/main/docker-compose.yml) と一致しています（リポジトリのバージョンには、イメージ加速と環境変数の説明コメントが追加されています）。直接ダウンロードして使用することを推奨します。

### 環境変数

| 変数 | デフォルト値 | 説明 |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Dashboard のポートマッピング |
| `ERISPULSE_TAG` | `latest` | イメージのタグ（バージョンを固定したい場合は具体的なバージョン番号を設定） |
| `CONTAINER_NAME` | `erispulse` | コンテナ名（複数インスタンスのデプロイ時にインスタンスを区別） |
| `ERISPULSE_DASHBOARD_TOKEN` | 自動生成 | Dashboard のログイントークン（強く設定することを推奨） |
| `TZ` | `Asia/Shanghai` | タイムゾーン |
| `LANG` | `en_US.UTF-8` | システム言語、起動時のインターフェース言語を自動検出 |
| `ERISPULSE_LANG` | 空 | 強制的な起動時のインターフェース言語：`zh` / `zh_TW` / `en` / `ja` / `ru`（`LANG` を上書き） |

### データの永続化

`./config` ディレクトリは設定ファイルとデータベースをマウントしており、以下の内容を含んでいます：

- `config/config.toml` — 設定ファイル
- `config/config.db` — SQLite ストレージデータベース
- `config/.packages` — Python site-packages の永続化ボリューム、フレームワーク、アダプタ、およびインストールされたモジュールを保存（最初の起動時にエントリポイントがイメージ内に含まれるバックアップから自動的に初期化され、以降のモジュールのインストールとフレームワークのホットアップデートはこのディレクトリに書き込まれます）

> **フレームワークのアップグレード（pre/rc を含む）とイメージの自己修復**：エントリポイントは、各コンテナ起動時にコアパッケージの整合性を自己チェックし、破損した場合は「ユーザーがインストールしたバージョンを優先」する原則で修復します——永続ボリューム内に明示的にインストール/アップグレードされたバージョン（例：Dashboard でインストールされた pre バージョン）は PyPI から**同じバージョンを再インストール**し、静かにイメージ内バージョンに戻ることはありません。したがって、Dashboard でフレームワークをアップグレードした後、任意回のコンテナ再起動でも目標バージョンを維持します。

## Dashboard 管理パネル

ErisPulse Docker イメージには Dashboard モジュールが内蔵されており、Web ベースの視覚的な管理インターフェースを提供します。

### 機能概要

| 機能 | 説明 |
|------|------|
| ダッシュボード | システム概要、CPU/メモリの監視、稼働時間、イベント統計 |
| ロボット管理 | 各プラットフォームのロボットのオンライン状態と情報を表示 |
| イベントの表示 | 実時イベントストリーム、タイプとプラットフォームでフィルタリング可能 |
| ログの表示 | モジュールとレベルでフィルタリングされたログビューアー |
| モジュール管理 | インストール済みのモジュールとアダプタを表示、ロード、アンロード |
| モジュールストア | リモートで利用可能なパッケージを閲覧してワンクリックでインストール |
| 設定の編集 | `config.toml` をオンラインで編集 |
| ストレージ管理 | Key-Value ストレージデータを閲覧および編集 |
| バックアップ | 設定とストレージデータのエクスポート/インポート |
| 審査ログ | すべての管理操作を記録 |

### Dashboard でモジュールをインストール

Dashboard にはモジュールストア機能が統合されており、以下の方法でモジュールをインストールできます：

1. **ストアからインストール**：リモートのモジュールリストを閲覧し、必要なモジュールを選択してワンクリックでインストール
2. **ローカルパッケージのアップロード**：`.whl` または `.zip` ファイルを直接アップロードしてインストール、開発中のモジュールのテストに便利

> **モジュール開発者の高速テストフロー**：Docker 部署後、Dashboard の「ローカルパッケージのアップロード」機能を使って、ビルドした `.whl` ファイルを直接アップロードしてテストを行うことができます。コンテナを手動で操作する必要はありません。

## プロセス監視とハードリスタート

ErisPulse のハードリスタート (`sdk.hard_restart()`) は**外部監視者**がプロセスの終了コードが 42 のときにプロセスを再起動することに依存しています——SDK 自体は新しいプロセスを起動しません。プロダクション環境では監視者を設定する必要があります。そうでないと、ハードリスタート後にプロセスが自動的に復活しません：

- Docker：公式の compose は `restart: on-failure:5` を使用しています——非ゼロ終了コードは再起動（ハードリスタートの終了コード 42 を上書き）、連続 5 回の上限で死循環を防ぎます；無制限に再起動したい場合は `unless-stopped` に変更してください
- systemd：`Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord：42 を再起動可能な終了コードに追加
- 純粋な Python でカスタム監視者を作成：`Popen` のループ + `returncode == 42` の検出

各監視者の完全な設定例と終了コード 42 の契約に関する説明は [起動フロー → 監視者ガイド](../advanced/startup.md#監視者ガイド) を参照してください。

### コンテナ内の再起動（PID 1 インスタンス）

> このセクションの機能は ErisPulse **2.12+** が必要です。

フレームワークがコンテナの主プロセス（PID 1）として実行されている場合、`epsdk restart` はプロセスを終了して再起動しません——PID 1 を終了するとコンテナが終了します。この場合、フレームワークプロセスに `SIGUSR1` を送信し、フレームワーク内でコンポーネントレベルのソフトリスタート（`sdk.restart()`）を行います：`ep i <パッケージ>` で新しくインストールされたアダプタやアップグレードされたモジュールのコードは即座にホットリロードされ有効になります。

- フレームワーク自身の更新、構造的な設定変更が必要な場合は、コンテナを再起動します：`docker restart <コンテナ>`
- `epsdk stop` は PID 1 インスタンスでは終了の意味です——コンテナも停止します（`restart` ポリシーに従って自動的に再起動するかどうかを決定）

## ヘルスチェック

SDK にはヘルスチェックエンドポイントが内蔵されています：

```bash
# ヘルスチェック
curl http://localhost:8000/health
```

公式の docker-compose.yml にはすでにヘルスチェックが内蔵されています。独自の compose ファイルを作成する際は、以下の例を参考にしてください：

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

Nginx などのリバースプロキシを通じて Dashboard を公開する必要がある場合：

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

    # WebSocket のサポート（Dashboard の実時イベントストリームに必要）
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

Docker を使用しない場合、手動でデプロイすることもできます。

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

### uv tool による分離デプロイ（CLI とプロジェクト環境の分離）

`uv tool install` は `epsdk` を**独立したツール環境**としてインストールし、CLI 自身とプロジェクト依存関係を完全に分離します：CLI のアップグレードはプロジェクトの `.venv` を触らず、プロジェクトの依存関係の変更も CLI に影響しません。

```bash
# 1. グローバルに CLI をインストール（自動的に epsdk / ep コマンドが利用可能になります）
uv tool install ErisPulse

# 2. プロジェクト内にロボットの依存関係のみを配置（.venv は uv で管理）
cd /opt/erispulse-bot
uv add erispulse ErisPulse-Adapter-Yunhu   # 必要に応じてアダプタを追加

# 3. CLI を使って実行（自動的にプロジェクトの .venv の解釈子を検出して使用）
epsdk run main.py
```

動作の要点：

- `epsdk run` の対象解釈子の解析順序は：`ERISPULSE_PYTHON` 環境変数 → プロジェクト `.venv` → 現在の解釈子；ツール環境は CLI だけを保持し、コンポーネント（アダプタ/モジュール）はプロジェクトの `.venv` にインストールするべきです
- `epsdk install` / `uninstall` / `upgrade` / `list` も同様にプロジェクトの `.venv` に作用し、ツール環境を汚染しません
- CLI のアップグレード：`uv tool upgrade ErisPulse`（または `epsdk self-update`、uv tool 環境下では自動的に `uv tool upgrade` に切り替わります）；プロジェクトの依存関係のアップグレード：プロジェクトディレクトリ内で `uv sync` / `uv add` を実行し、互いに影響しません
- サーバー環境ではツール環境は uv で統一管理されます（`uv tool list` で確認、`uv tool upgrade --all` で一括アップグレード）、手動でグローバルな pip パッケージを管理する必要はありません
- プロジェクトのないディレクトリで `uv run epsdk ...` を実行する場合、**一時的な隔離環境**に落ちます（インストールしたコンポーネントは永続化されません）；サーバーでは常に `epsdk` を直接呼び出すか、まず `cd` でプロジェクトディレクトリに移動するべきです

## セキュリティに関する推奨事項

1. **Dashboard トークンの設定**：強力なランダムなトークンを使用し、デフォルト値は使用しないでください。
2. **ポートをパブリックに公開しない**：リバースプロキシ + SSL を使用しない限り、Dashboard のポートをローカルネットワークに限定してください。
3. **データディレクトリの保護**：`config/` ディレクトリには設定とデータベースが含まれており、適切なファイル権限を設定してください。
4. **定期的な更新**：`epsdk self-update` を使用するか、最新の Docker イメージを取得してください。
5. **root で実行しない**：手動でのデプロイ時には専用ユーザーを作成してください。
6. **Docker の再起動ポリシーの使用**：公式の compose では `restart: on-failure:5` が設定されており、例外的な終了（ハードリセット終了コード 42 を含む）後も自動的に再起動されます。
7. **API ドキュメントエンドポイントの無効化**：`/docs`、`/redoc`、`/openapi.json` はデフォルトで有効で認証がされていないため、パブリック環境で展開する場合は `router.disable_docs()` を呼び出して無効化してください。
8. **Webhook の署名検証**：スキャフォールディングで生成された `verify_request` はデフォルトで許可されていますが、パブリックなコールバックを接続する前に、署名またはトークン検証を実装する必要があります。
9. **セキュリティモデルの境界**：マスター/スコープ体系はプラットフォーム側のユーザーを制約します。ロードされたモジュールは信頼できるコードと見なされます（スコープが設定されていない場合はデフォルトで許可され、モジュールはプロバイダーを登録できます）。信頼できないモジュールをロードしないでください。

## 多インスタンスデプロイ

複数のロボットインスタンスを実行する場合：

1. 各インスタンスは独立したプロジェクトディレクトリと `docker-compose.yml` を使用します。
2. 異なるポート番号を使用します：`ERISPULSE_PORT=8001`
3. 異なるコンテナ名を使用します：`container_name: erispulse-bot2`

> **ストレージバックエンドの注意点**：インスタンス間でステート（セッション受信箱 / ダイアログチェックポイント / コマンドクールダウン）は共有されません（すべてインスタンスのメモリ状態です）。
> 既定の SQLite は単一ファイルのバックエンドであり、**複数インスタンスで同時に開くことはできません**。各インスタンスの `config/` ディレクトリは独立している必要があります。mysql / postgres に切り替えても、それぞれ独立したデータベースになります。現在のバージョンでは、複数インスタンスによる協調（セッション共有 / ロードバランシング）はサポートしていません。同じグループに複数インスタンスが存在する場合、それぞれが個別に応答します。重複を防ぐには、プラットフォーム側または業務側で独自に重複除去を行う必要があります。

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
# CLI ツール環境のアップグレード
uv tool upgrade ErisPulse

# プロジェクト依存関係のアップグレード（プロジェクトディレクトリ内で実行）
uv sync
```

### 実行時ホットリロードサーバー設定

リスニングアドレス / ポート / SSL 証明書を変更した後は、プロセスを再起動せずに実行します。任意のコルーチンで `router.reload()` を呼び出します：

```python
await sdk.router.reload(port=9000)                                # ポート変更
await sdk.router.reload(ssl_cert=new_pem, ssl_key=new_key)        # 証明書のホット交換（証明書の更新シーン）
await sdk.router.reload(host="0.0.0.0", port=9000)                # 省略引数は現在の設定を引き継ぐ
```

- 同じ FastAPI アプリケーションを再利用し、モジュールが登録した HTTP / WebSocket / SSE ルートはすべて保持されます
- 新しい設定（証明書が構築可能、ポートが利用可能）を先に検証してから切り替えます；失敗した場合は旧設定でサービスを復元して `False` を返し、戻り値が `False` = 旧サービスが利用可能であることを保証します
- サーバーが実行されていない場合は `False` を返します（初期起動は `sdk.router.start()` を使用してください）

### バックアップ

定期的に `config/` ディレクトリをバックアップします：

```bash
# Docker 部署
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# または Dashboard の「バックアップ」機能を使ってエクスポート
```

## 次のステップ

- **デプロイ後に可視化管理をしたい**：[ErisPulse-Dashboard](../ecosystem/dashboard.md) をインストールし、ブラウザ上でモジュール、ログ、設定を管理します
- **環境に問題があると疑う**：まず `epsdk doctor` を実行して健康状態レポートを出力し、[CLI コマンドリファレンス · doctor](cli-reference.md#doctor) を参照します
- **フレームワークとコンポーネントの設定を調整したい**：[設定ファイルの説明](configuration.md)を参照し、環境変数の上書きは特にコンテナデプロイに適しています