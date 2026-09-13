# モジュール商店への公開ガイド

ErisPulse モジュール商店に開発したモジュールやアダプタを公開し、他のユーザーが簡単に発見してインストールできるようにしましょう。

## モジュール商店の概要

ErisPulse モジュール商店は、集中管理されたモジュール登録表です。ユーザーは CLI ツールを使用して、コミュニティが提供するモジュールやアダプタを閲覧、検索、インストールできます。

### 閲覧と発見

```bash
# リモートに利用可能なすべてのパッケージをリスト表示
epsdk list-remote

# モジュールのみ表示
epsdk list-remote -t modules

# アダプタのみ表示
epsdk list-remote -t adapters

# リモートパッケージリストを強制的に更新
epsdk list-remote -r
```

また、[ErisPulse 公式サイト](https://www.erisdev.com/#market)にアクセスして、オンラインでモジュール商店を閲覧することもできます。

### 提出可能なタイプ

| タイプ | 説明 | エントリポイントのグループ |
|------|------|----------------|
| モジュール (Module) | ロボットの機能拡張、ビジネスロジックの実装 | `erispulse.module` |
| アダプタ (Adapter) | 新しいメッセージプラットフォームへの接続 | `erispulse.adapter` |

## 速攻公開

公開プロセスは以下の3ステップで完了します：プロジェクトの設定 → PyPI への公開 → モジュール商店への登録。

### 1. pyproject.toml の設定

プロジェクトディレクトリに `pyproject.toml`、`README.md` を含め、タイプに応じて entry-points を設定してください。

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

#### アダプタ

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "アダプタの機能説明"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **注意**：パッケージ名は `ErisPulse-` で始めるのが推奨です。エントリポイントのキー名（例：`"MyModule"`）は、SDK 内でのモジュールのアクセス名として使用されます。

### 2. PyPI への公開

```bash
# ビルド + 公開（PyPI アカウントが必要）
pip install build twine
python -m build
python -m twine upload dist/*
```

公開が成功したら、インストールを確認します：

```bash
pip install ErisPulse-MyModule
```

### 3. モジュール商店への登録

[ErisPulse 模块商店](https://www.erisdev.com/#market)にアクセスし、「モジュールを登録」をクリックして、ログイン後、モジュール情報を入力してください。

サポートされているログイン方法：**GitHub**、**Codeberg**、**云湖**、いずれかを選択してください。

入力のポイント：
- モジュール名、説明、リポジトリのアドレス
- 最低 SDK バージョン：わからない場合は、[ErisPulse 最新リリース版](https://pypi.org/project/ErisPulse/)のバージョン番号を入力してください

登録後、即座に有効になり、ユーザーはモジュールソースからインストールできます。モジュールは「未検証」と表示され、メンテナの審査が通ると「検証済み」に変わります。

> **検証ステータスについて**：
> - 「未検証」は公式の審査がまだ行われていないことを意味し、モジュールに問題があるわけではありません
> - ユーザーが `epsdk install` で未検証モジュールをインストールする際、リスク警告が表示され、確認後にインストールを進めることができます

### 4. 公開済みモジュールの管理

モジュール商店で「モジュールを登録」をクリックし、ログイン後、「私のモジュール」タブに切り替えると、以下のことができます：

- **編集** — モジュールの説明、リポジトリのアドレス、タグなどの情報を変更できます。バージョン番号は PyPI から自動的に同期されます
- **削除** — モジュール商店からモジュールを削除します（取り消しはできません）

> 新しく登録したモジュールは、「私のモジュール」リストに表示されるまで数分かかる場合があります。

## 公開済みモジュールの更新

1. `pyproject.toml` の `version` を更新
2. 再びビルドしてアップロード：`python -m build && python -m twine upload dist/*`
3. モジュール商店は自動的に PyPI 上の最新バージョンを同期します

ユーザーは `epsdk upgrade MyModule` でアップグレードできます。

## 公開前のチェックリスト

PyPI に送信する前に、以下の項目を1つずつ確認してください：

### コード品質

- [ ] すべての公開 API に型注釈（関数シグネチャと戻り値）
- [ ] すべての公開メソッドにドキュメント文字列（`"""..."""` 形式、`:param` / `:return` / `:raises` を含む）
- [ ] `ruff check` で警告がない
- [ ] テストカバレッジが 80% 以上
- [ ] `pytest` で全テストが通過

### 兼容性

- [ ] `pyproject.toml` に最低 SDK バージョンを宣言：`dependencies = ["ErisPulse>=x.y.z"]`
- [ ] `get_meta()` の `ModuleMeta(min_sdk_version="x.y.z")` で実行時の最低 SDK バージョンを宣言（アダプタはクラス属性 `min_sdk_version` を使用）— ユーザー環境の SDK が低すぎると、フレームワークは読み込み時に明確なエラーを発生させ、ランタイムエラーを回避します
- [ ] Python 3.10 / 3.11 / 3.12 / 3.13 でテスト済み
- [ ] 対象オペレーティングシステム（Windows / Linux / macOS、該当する場合）でテスト済み
- [ ] 循環インポート依存がない

### 設定

- [ ] 宣言的設定（`ConfigClass` + `BaseConfig` / `BotAccountConfig`）を使用している場合、設定フィールドに `description`（i18n 形式を推奨）と `ui` メタデータを含む
- [ ] i18n 翻訳キーを登録している場合、5か国語（zh-CN / zh-TW / en / ja / ru）をすべてカバーしている
- [ ] 敏感フィールドは `secret=True` とマーク

### ドキュメント

- [ ] `README.md` にインストール方法と基本的な使用例を記載
- [ ] `README.md` に設定方法（設定ファイルの例 + 環境変数）を記載
- [ ] `CHANGELOG.md` にすべての変更を記録
- [ ] アダプタはプラットフォームの機能ドキュメントを更新（サポートする Send タイプ、イベントタイプなど）

### 公開

- [ ] `pyproject.toml` のバージョン番号を更新
- [ ] ビルドが通る：`python -m build`
- [ ] PyPI に送信：`python -m twine upload dist/*`
- [ ] インストールの検証が通る：`pip install ErisPulse-xxx && epsdk run`

## 開発モードでのテスト

正式公開前に、ローカルで編集可能なモードでテストできます：

```bash
epsdk install -e /path/to/MyModule
# または
pip install -e /path/to/MyModule
```

## 一般的な質問

### パッケージ名は `ErisPulse-` で始める必要がありますか？

必須ではありませんが、強く推奨します。これにより、ユーザーが PyPI 上で ErisPulse エコシステムのパッケージを識別しやすくなります。

### 1つのパッケージで複数のモジュールを登録できますか？

できます。`entry-points` に複数のキーと値を設定できます：

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### 審査にはどのくらい時間がかかりますか？

通常 1〜3 営業日で完了します。モジュール商店の「私のモジュール」で検証ステータスを確認できます。

## Docker イメージによるアプリケーションの配布

PyPI に公開するのに適さないアプリケーション（例：プライベート依存、事前設定環境が必要な場合）は、**GitHub Container Registry (GHCR)** を使って Docker イメージを公開し、他のユーザーが `docker pull` でワンクリックで起動できるようにすることができます。

### 適用場面

- あなたが**完全なロボットアプリケーション**（モジュール + 設定 + エントリスクリプト）を持っていて、ワンクリックで配布したい
- モジュール/アダプタが**プライベートパッケージ**や特別なインストールプロセスを必要とするため、PyPI には適さない
- **出荷時から使用可能な**デプロイメント・ソリューションを提供して、ユーザーの使用のハードルを下げたい

### 1. Dockerfile の作成

ErisPulse 公式イメージをベースに、あなたのモジュールを追加するだけです：

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

モジュールに追加のシステム依存（例：SSHクライアントなど）が必要な場合は、`RUN uv pip install` の後に追加します：

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` には ErisPulse、ErisPulse-Dashboard、Pythonランタイム、uv が含まれており、再びインストールする必要はありません。

### 2. GitHub Actions ワークフローの作成

`.github/workflows/docker-publish.yml` に作成します：

```yaml
name: Docker イメージの公開

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
      - name: コードをチェックアウト
        uses: actions/checkout@v4

      - name: QEMU のセットアップ (マルチアーキテクチャ対応)
        uses: docker/setup-qemu-action@v3

      - name: Docker Buildx のセットアップ
        uses: docker/setup-buildx-action@v3

      - name: GitHub Container Registry にログイン
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Docker のメタデータを取得
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: Docker イメージをビルドしてプッシュ
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

> `GITHUB_TOKEN` は GitHub Actions によって自動的に提供されるため、手動でキーを作成する必要はありません。

### 3. ビルドの起動

コードをプッシュするか、タグを打つことで自動的にビルドされます：

```bash
# main ブランチにプッシュして起動
git push origin main

# またはタグを打って起動
git tag v1.0.0
git push origin v1.0.0
```

GitHub リポジトリの **Actions** ページから手動で起動することもできます。

### 4. イメージを公開に設定

GHCR イメージはデフォルトで **private** です。他のユーザーがログインなしでプルできるようにするには、GitHub で公開に設定する必要があります：

1. リポジトリにアクセス → **Packages** → 対応するパッケージをクリック
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. ユーザーの使用

ビルドが完了したら、ユーザーは `docker run` で1行で起動できます：

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

または `docker-compose.yml` を使用：

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

### Docker Hub への同時公開

ワークフローを拡張して、ログイン手順の前に Docker Hub にログインし、`images` に Docker Hub アドレスを追加します：

```yaml
      - name: Docker Hub にログイン
        uses: docker/login-action@v3
        with:
          registry: docker.io
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Docker のメタデータを取得
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            docker.io/<your-dockerhub-username>/my-bot
            ghcr.io/${{ github.repository_owner }}/my-bot
```

> `DOCKERHUB_USERNAME` と `DOCKERHUB_TOKEN` は、リポジトリの **Settings → Secrets** に追加する必要があります。

### Docker イメージ vs PyPI 公開

| 特性 | Docker イメージ (GHCR) | PyPI 公開 |
|------|---------------------|-----------|
| 分布方法 | `docker pull` でワンクリック実行 | `pip install` + 手動設定 |
| 適用範囲 | 完全なアプリケーション/ソリューション | 単一モジュール/アダプタ |
| プライベート依存 | 天然にサポート | プライベート PyPI ソースが必要 |
| モジュール商店 | 不適切 | モジュール商店に登録可能 |
| マルチアーキテクチャ | amd64/arm64 をサポート | アーキテクチャに依存しない |

両方の方法は互いに矛盾しません。モジュール商店に PyPI でモジュールを公開すると同時に、GHCR でワンクリック可能な Docker イメージを提供することも可能です。