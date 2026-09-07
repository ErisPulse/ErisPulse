# リリースとモジュールストアガイド

開発したモジュールやアダプタを ErisPulse モジュールストアに公開し、他のユーザーが簡単に見つけてインストールできるようにします。

## モジュールストアの概要

ErisPulse モジュールストアは、集中管理されたモジュール登録表です。ユーザーは CLI ツールを使用して、コミュニティが提供するモジュールやアダプターを閲覧、検索、インストールできます。

### 一覧表示と発見

```bash
# リモートで利用可能なすべてのパッケージを一覧表示
epsdk list-remote

# モジュールのみを表示
epsdk list-remote -t modules

# アダプターのみを表示
epsdk list-remote -t adapters

# リモートパッケージ一覧を強制的に更新
epsdk list-remote -r
```

また、[ErisPulse 公式サイト](https://www.erisdev.com/#market) にアクセスして、オンラインでモジュールストアを閲覧することもできます。

### 提出可能なタイプ

| タイプ | 説明 | Entry-point 組 |
|------|------|----------------|
| モジュール (Module) | ロボットの機能を拡張し、ビジネスロジックを実装 | `erispulse.module` |
| アダプター (Adapter) | 新しいメッセージプラットフォームに接続 | `erispulse.adapter` |

## 快速配布

全体のプロセスは、3つのステップで完了します：プロジェクトの設定 → PyPI への配布 → モジュールストアへの提出。

### 1. pyproject.toml の設定

プロジェクトのディレクトリに `pyproject.toml` および `README.md` が存在することを確認し、タイプに応じて entry-points を設定してください。

#### モジュール

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "モジュールの機能説明"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [ { name = "yourname" } ]
dependencies = [
    "ErisPulse>=2.0.0",
]

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

#### アダプター

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "アダプターの機能説明"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **注意**：パッケージ名は `ErisPulse-` で始まるようにすることを推奨します。entry-point のキー名（例：`"MyModule"`）は、SDK 内でのモジュールのアクセス名として使用されます。

### 2. PyPI への配布

```bash
# ビルド + 配布（PyPI アカウントが必要）
pip install build twine
python -m build
python -m twine upload dist/*
```

配布に成功したら、インストールを確認します。

```bash
pip install ErisPulse-MyModule
```

### 3. モジュールストアへの提出

[ErisPulse モジュールストア](https://www.erisdev.com/#market) にアクセスし、「モジュールを提出」をクリックして、ログイン後にモジュール情報を入力してください。

対応しているログイン方法：**GitHub**、**Codeberg**、**云湖**、いずれかを選択してください。

入力のポイント：
- モジュール名、説明、リポジトリのアドレス
- 最低 SDK バージョン：不明な場合は、[ErisPulse の最新リリース](https://pypi.org/project/ErisPulse/) のバージョン番号を入力してください。

提出後、即座に有効になります。ユーザーはモジュールソースからインストールできます。モジュールは「未検証」と表示され、メンテナが審査を通過した後、「検証済み」に変更されます。

> **検証ステータスについて**：
> - 「未検証」は、公式の審査をまだ受けていないことを意味するだけで、モジュールに問題があるわけではありません。
> - ユーザーが `epsdk install` を使用して未検証のモジュールをインストールする際には、リスク警告が表示され、確認後にのみインストールが進められます。

### 4. 配布済みモジュールの管理

モジュールストアで「モジュールを提出」をクリックしてログイン後、「マイモジュール」タブに切り替えると、以下の操作が可能です。

- **編集** — モジュールの説明、リポジトリのアドレス、タグなどの情報を変更できます。バージョン番号は PyPI から自動的に同期されます。
- **削除** — モジュールストアからモジュールを削除します（取り消しはできません）。

> 提出したばかりのモジュールは、数分後に「マイモジュール」リストに表示されることがあります。

## モジュールの更新

1. `pyproject.toml` の `version` を更新します。
2. 再びビルドしてアップロードします: `python -m build && python -m twine upload dist/*`
3. モジュールストアは、PyPI 上の最新バージョンを自動的に同期します。

ユーザーは `epsdk upgrade MyModule` コマンドを使用して、モジュールをアップグレードできます。

## リリース前のチェックリスト

PyPI にプッシュする前に、以下の項目を一つずつ確認してください。

### コード品質

- [ ] 公開 API にはすべて型注釈が付いています（関数シグネチャと戻り値）
- [ ] 公開メソッドにはすべてドキュメント文字列（`"""..."""` 形式、`:param` / `:return` / `:raises` を含む）
- [ ] `ruff check` で警告がありません
- [ ] テストカバレッジは 80% 以上
- [ ] `pytest` で全テストケースが通過

### 兼容性

- [ ] `pyproject.toml` に最低 SDK バージョンが宣言されています：`dependencies = ["ErisPulse>=x.y.z"]`
- [ ] Python 3.10 / 3.11 / 3.12 / 3.13 でテスト済み
- [ ] 対象オペレーティングシステム（Windows / Linux / macOS、該当する場合）でテスト済み
- [ ] 循環依存がありません

### 設定

- [ ] 宣言的設定（`ConfigClass` + `BaseConfig` / `BotAccountConfig`）を使用している場合、設定フィールドに `description`（推奨 i18n 形式）と `ui` メタデータがあります
- [ ] i18n 翻訳キーを登録している場合、5 言語すべて（zh-CN / zh-TW / en / ja / ru）をカバーしています
- [ ] 敏感フィールドには `secret=True` が付いています

### ドキュメント

- [ ] `README.md` にインストール手順と基本的な使用例があります
- [ ] `README.md` に設定方法（設定ファイルの例 + 環境変数）を説明しています
- [ ] `CHANGELOG.md` にすべての変更履歴が記録されています
- [ ] アダプターはプラットフォームの機能ドキュメントを更新しています（サポートする Send タイプ、イベントタイプなど）

### リリース

- [ ] `pyproject.toml` のバージョン番号が更新されています
- [ ] ビルドが通っています：`python -m build`
- [ ] PyPI にプッシュされています：`python -m twine upload dist/*`
- [ ] インストールの検証が通っています：`pip install ErisPulse-xxx && epsdk run`

## 開発モードでのテスト

正式リリース前に、編集可能なモードを使用してローカルでテストすることができます。

```bash
epsdk install -e /path/to/MyModule
# または
pip install -e /path/to/MyModule
```

## 常見問題

### パッケージ名は `ErisPulse-` で始める必要がありますか？

必須ではありませんが、強く推奨されます。これにより、PyPI 上で ErisPulse エコシステムのパッケージをユーザーが識別しやすくなります。

### 1 つのパッケージに複数のモジュールを登録できますか？

はい、可能です。`entry-points` に複数のキーと値のペアを設定することで実現できます：

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### 審査にはどのくらい時間がかかりますか？

通常、1〜3営業日で完了します。モジュールストアの「マイモジュール」から、検証の状態を確認できます。

## Dockerイメージによるアプリケーションの配布

アプリケーションがPyPIに公開するのに適していない場合（プライベートな依存関係を含む、または事前設定が必要な環境など）、**GitHub Container Registry (GHCR)** を使ってDockerイメージを公開し、他のユーザーが `docker pull` で簡単に起動できるようにすることができます。

### 適用シーン

- あなたが**完全なロボットアプリケーション**（モジュール + 設定 + 入口スクリプト）を持っていて、ワンクリックで配布したい
- モジュール/アダプターが**プライベートパッケージ**や特別なインストール手順を必要とし、PyPIに適していない
- ユーザーの使用を容易にする**オールインクルーシブな**デプロイメント方式を提供したい

### 1. Dockerfileの作成

ErisPulse公式のイメージをベースに構築し、必要なモジュールを追加するだけです：

```dockerfile
FROM erispulse/erispulse:latest

LABEL org.opencontainers.image.title="ErisPulse-MyModule" \
      org.opencontainers.image.description="モジュールの説明" \
      org.opencontainers.image.url="https://github.com/yourname/ErisPulse-MyModule" \
      org.opencontainers.image.source="https://github.com/yourname/ErisPulse-MyModule"

COPY pyproject.toml README.md ./
COPY MyModule/ ./MyModule/

RUN uv pip install --system -e .
```

モジュールに追加のシステム依存性（例：SSHクライアントなど）が必要な場合は、`RUN uv pip install`の後に追加します：

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest`にはErisPulse、ErisPulse-Dashboard、Pythonランタイム、およびuvが既に含まれているため、再インストールは不要です。

### 2. GitHub Actionsワークフローの作成

`.github/workflows/docker-publish.yml`に作成します：

```yaml
name: Dockerイメージの公開

on:
  workflow_dispatch:
  push:
    branches:
      - main
    tags:
      - "v*"

permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository_owner }}/my-bot

jobs:
  docker-publish:
    runs-on: ubuntu-latest

    steps:
      - name: コードのチェックアウト
        uses: actions/checkout@v4

      - name: QEMUの設定 (マルチアーキテクチャ対応)
        uses: docker/setup-qemu-action@v3

      - name: Docker Buildxの設定
        uses: docker/setup-buildx-action@v3

      - name: GitHub Container Registryへのログイン
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Dockerメタデータの抽出
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: Dockerイメージのビルドとプッシュ
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Dockerfile
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

> `GITHUB_TOKEN`はGitHub Actionsによって自動的に提供されるため、手動で秘密鍵を作成する必要はありません。

### 3. ビルドのトリガー

コードをプッシュするか、タグを打つことで自動的にビルドが開始されます：

```bash
# mainブランチにプッシュしてトリガー
git push origin main

# またはタグを打ってトリガー
git tag v1.0.0
git push origin v1.0.0
```

また、GitHubリポジトリの**Actions**ページから手動でトリガーすることもできます。

### 4. イメージを公開に設定

GHCRのイメージはデフォルトで**private**です。他のユーザーがログインせずにプルできるようにするには、GitHubで公開に設定する必要があります：

1. リポジトリにアクセス → **Packages** → 対応するPackageをクリック
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. ユーザーの使用

ビルドが完了すると、ユーザーは `docker run` で1行で起動できます：

```bash
docker run -d \
  --name my-bot \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  -e TZ=Asia/Shanghai \
  -e ERISPULSE_DASHBOARD_TOKEN=your-token \
  --restart unless-stopped \
  ghcr.io/<your-username>/my-bot:latest
```

または `docker-compose.yml` を使用します：

```yaml
services:
  my-bot:
    image: ghcr.io/<your-username>/my-bot:latest
    container_name: my-bot
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
    environment:
      - TZ=Asia/Shanghai
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    restart: unless-stopped
```

### Docker Hubへの同時公開

ワークフローを拡張して、ログインステップの前にDocker Hubへのログインを追加し、`images`にDocker Hubのアドレスを追加します：

```yaml
      - name: Docker Hubへのログイン
        uses: docker/login-action@v3
        with:
          registry: docker.io
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Dockerメタデータの抽出
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            docker.io/<your-dockerhub-username>/my-bot
            ghcr.io/${{ github.repository_owner }}/my-bot
```

> `DOCKERHUB_USERNAME`と`DOCKERHUB_TOKEN`は、リポジトリの**Settings → Secrets**に追加する必要があります。

### Dockerイメージ vs PyPI公開

| 特性 | Dockerイメージ (GHCR) | PyPI公開 |
|------|---------------------|-----------|
| 分布方法 | `docker pull` でワンクリック実行 | `pip install` + 手動設定 |
| 適用範囲 | 完全なアプリケーション/ソリューション | 単一のモジュール/アダプター |
| プライベート依存 | 天然にサポート | プライベートPyPIソースが必要 |
| モジュールストア | 不適切 | モジュールストアに提出可能 |
| マルチアーキテクチャ | amd64/arm64をサポート | アーキテクチャに依存しない |

両方の方法は互いに矛盾しないため、モジュールをモジュールストアにPyPIで公開すると同時に、GHCRでオールインクルーシブなDockerイメージを提供することも可能です。