# リリースとモジュールストアガイド

> [!TIP]
> **いつこのドキュメントを読むべきか**：作品を PyPI / モジュールストアにリリースする場合。必要なければスキップしても、他の機能の利用には影響しません。


開発したモジュールやアダプターを ErisPulse モジュールストアにリリースすることで、他のユーザーが簡単に発見・インストールできるようになります。

## モジュールストアの概要

ErisPulse モジュールストアは集中型のモジュールレジストリであり、ユーザーは CLI ツールを使ってコミュニティが提供するモジュールやアダプターを閲覧・検索・インストールできます。

### 閲覧と検索

```bash
# リモートで利用可能なすべてのパッケージを一覧表示
epsdk list-remote

# モジュールのみ表示
epsdk list-remote -t modules

# アダプターのみ表示
epsdk list-remote -t adapters

# リモートパッケージリストを強制更新
epsdk list-remote -r
```

[ErisPulse 公式サイト](https://www.erisdev.com/#market) にアクセスして、オンラインでモジュールストアを閲覧することもできます。

### サポートされている提出タイプ

| タイプ | 説明 | Entry-point グループ |
|------|------|----------------|
| モジュール (Module) | ボット機能の拡張、ビジネスロジックの実装 | `erispulse.module` |
| アダプター (Adapter) | 新しいメッセージプラットフォームへの接続 | `erispulse.adapter` |

## クイックリリース

全体のプロセスは 3 つのステップのみです：プロジェクトの設定 → PyPI へのリリース → モジュールストアへの提出。

### 1. pyproject.toml の設定

プロジェクトディレクトリに `pyproject.toml` と `README.md` が含まれていることを確認し、タイプに応じて entry-points を設定します：

#### モジュール

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "モジュール機能の説明"
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
description = "アダプター機能の説明"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **注意**：パッケージ名は `ErisPulse-` で始めることを推奨します。ユーザーが識別しやすくなります。Entry-point のキー名（例：`"MyModule"`）は、SDK 内でモジュールにアクセスする際の名前として使用されます。

### 2. PyPI へのリリース

```bash
# ビルド + リリース（PyPI アカウントが必要）
pip install build twine
python -m build
python -m twine upload dist/*
```

リリースが成功したら、インストールを検証します：

```bash
pip install ErisPulse-MyModule
```

### 3. モジュールストアへの提出

[ErisPulse モジュールストア](https://www.erisdev.com/#market) にアクセスし、「モジュールを提出」をクリックして、ログイン後にモジュール情報を入力するだけです。

サポートされているログイン方式：**GitHub**、**Codeberg**、**云湖**、いずれかを選択できます。

記入のポイント：
- モジュール名、説明、リポジトリ URL
- 最低 SDK バージョン：不明な場合は、[ErisPulse 最新リリース](https://pypi.org/project/ErisPulse/) のバージョン番号を記入すれば OK です

提出後すぐに有効になり、ユーザーはモジュールソースからインストールできます。モジュールは「未検証」としてマークされ、メンテナーによる審査が通ると「検証済み」に変わります。

> **検証ステータスについて**：
> - 「未検証」は公式審査をまだ受けていないことを示すだけで、モジュールに問題があることを意味しません
> - ユーザーが `epsdk install` で未検証モジュールをインストールする際にはリスク警告が表示され、確認後にインストールを続行できます

### 4. リリース済みモジュールの管理

モジュールストアで「モジュールを提出」をクリックしてログインすると、「マイモジュール」タブに切り替えて、以下の操作ができます：

- **編集** — モジュールの説明、リポジトリ URL、タグなどの情報を変更。バージョン番号は PyPI から自動同期されます
- **削除** — モジュールストアからモジュールを削除（取り消し不可）

> 提出したばかりのモジュールが「マイモジュール」リストに表示されるまで、数分かかる場合があります。

## リリース済みモジュールの更新

1. `pyproject.toml` の `version` を更新
2. 再ビルドしてアップロード：`python -m build && python -m twine upload dist/*`
3. モジュールストアは PyPI 上の最新バージョンを自動同期します

ユーザーは `epsdk upgrade MyModule` でアップグレードできます。

## リリース前チェックリスト

PyPI にプッシュする前に、以下の項目を一つずつ確認してください：

### コード品質

- [ ] すべての公開 API に型アノテーションがある（関数シグネチャと戻り値）
- [ ] すべての公開メソッドに docstring がある（`"""..."""` 形式、`:param` / `:return` / `:raises` を含む）
- [ ] `ruff check` に合格（警告なし）
- [ ] テストカバレッジ ≥ 80%
- [ ] `pytest` の全テストケースに合格

### 互換性

- [ ] `pyproject.toml` で最低 SDK バージョンを宣言している：`dependencies = ["ErisPulse>=x.y.z"]`
- [ ] モジュールが `get_meta()` の `ModuleMeta(min_sdk_version="x.y.z")` で実行時の最低 SDK バージョンを宣言している（アダプターはクラス属性 `min_sdk_version` を使用）——ユーザー環境の SDK バージョンが低すぎる場合、フレームワークがロード時に明確なエラーを出してスキップし、原因を特定しにくいランタイム例外を発生させないようにするため
- [ ] Python 3.10 / 3.11 / 3.12 / 3.13 でテストした
- [ ] 対象 OS でテストした（Windows / Linux / macOS、該当する場合）
- [ ] 循環インポート依存がない

### 設定

- [ ] 宣言的設定（`ConfigClass` + `BaseConfig` / `BotAccountConfig`）を使用する場合、設定フィールドに `description`（i18n 形式を推奨）と `ui` メタデータがある
- [ ] i18n 翻訳キーを登録した場合、すべての 5 言語（zh-CN / zh-TW / en / ja / ru）をカバーしている
- [ ] 機密フィールドに `secret=True` をマークしている

### ドキュメント

- [ ] `README.md` にインストール手順と基本的な使用例がある
- [ ] `README.md` に設定方法が記載されている（設定ファイル例 + 環境変数）
- [ ] `CHANGELOG.md` にすべての変更が記録されている
- [ ] アダプターのプラットフォーム機能ドキュメントを更新した（対応する Send タイプ、イベントタイプなど）

### リリース

- [ ] `pyproject.toml` のバージョン番号を更新した
- [ ] ビルドに合格：`python -m build`
- [ ] PyPI にプッシュ済み：`python -m twine upload dist/*`
- [ ] インストール検証に合格：`pip install ErisPulse-xxx && epsdk run`

## 開発モードでのテスト

正式なリリース前に、編集可能モード（editable mode）でローカルテストができます：

```bash
epsdk install -e /path/to/MyModule
# または
pip install -e /path/to/MyModule
```

## よくある質問

### パッケージ名は必ず `ErisPulse-` で始める必要がありますか？

必須ではありませんが、強く推奨します。ユーザーが PyPI 上で ErisPulse エコシステムのパッケージを識別しやすくなります。

### 1 つのパッケージで複数のモジュールを登録できますか？

できます。`entry-points` に複数のキーと値のペアを設定するだけです：

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### 審査にはどのくらい時間がかかりますか？

通常 1〜3 営業日以内に完了します。モジュールストアの「マイモジュール」で検証ステータスを確認できます。

## Docker イメージによるアプリの配布

アプリが PyPI へのリリースに適さない場合（プライベート依存関係を含む、事前設定済み環境が必要など）、**GitHub Container Registry (GHCR)** で Docker イメージを公開することで、他のユーザーが `docker pull` でワンクリック起動できるようになります。

### 適用シナリオ

- **完全なボットアプリケーション**（モジュール + 設定 + エントリースクリプト）があり、ワンクリックで配布したい
- モジュール/アダプターが**プライベートパッケージ**に依存していたり、特殊なインストール手順があり、PyPI に適さない
- **すぐに使える**デプロイソリューションを提供し、ユーザーの利用ハードルを下げたい

### 1. Dockerfile の作成

ErisPulse 公式イメージをベースにビルドし、自分のモジュールを追加するだけです：

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

モジュールに追加のシステム依存関係（SSH クライアントなど）が必要な場合は、`RUN uv pip install` の後に追加します：

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` には ErisPulse、ErisPulse-Dashboard、Python ランタイム、uv が既に含まれているため、再インストールは不要です。

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
      - name: コードのチェックアウト
        uses: actions/checkout@v4

      - name: QEMU のセットアップ（マルチアーキテクチャ対応）
        uses: docker/setup-qemu-action@v3

      - name: Docker Buildx のセットアップ
        uses: docker/setup-buildx-action@v3

      - name: GitHub Container Registry へのログイン
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Docker メタデータの抽出
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: Docker イメージのビルドとプッシュ
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

> `GITHUB_TOKEN` は GitHub Actions が自動的に提供するため、手動でシークレットを作成する必要はありません。

### 3. ビルドのトリガー

コードをプッシュするか、タグを打つだけで自動ビルドされます：

```bash
# main ブランチへのプッシュでトリガー
git push origin main

# またはタグを打ってトリガー
git tag v1.0.0
git push origin v1.0.0
```

GitHub リポジトリの **Actions** ページから手動でトリガーすることもできます。

### 4. イメージを公開設定にする

GHCR イメージはデフォルトで **private** です。GitHub で Public に設定しないと、他のユーザーはログインなしでプルできません：

1. リポジトリに入る → **Packages** → 該当する Package をクリック
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. ユーザーの使用

ビルドが完了すると、ユーザーは `docker run` の 1 行で起動できます：

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

ワークフローを拡張し、ログインステップの前に Docker Hub ログインを追加し、`images` に Docker Hub アドレスを追加します：

```yaml
      - name: Docker Hub へのログイン
        uses: docker/login-action@v3
        with:
          registry: docker.io
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Docker メタデータの抽出
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            docker.io/<your-dockerhub-username>/my-bot
            ghcr.io/${{ github.repository_owner }}/my-bot
```

> リポジトリの **Settings → Secrets** に `DOCKERHUB_USERNAME` と `DOCKERHUB_TOKEN` を追加する必要があります。

### Docker イメージ vs PyPI リリース

| 特徴 | Docker イメージ (GHCR) | PyPI リリース |
|------|---------------------|-----------|
| 配布方法 | `docker pull` でワンクリック実行 | `pip install` + 手動設定 |
| 適用範囲 | 完全なアプリ/ソリューション | 単一のモジュール/アダプター |
| プライベート依存関係 | 標準で対応 | プライベート PyPI ソースが必要 |
| モジュールストア | 対象外 | モジュールストアに提出可能 |
| マルチアーキテクチャ | amd64/arm64 対応 | アーキテクチャに依存しない |

2 つの方法は競合しません——PyPI 経由でモジュールをモジュールストアにリリースすると同時に、GHCR 経由ですぐに使える Docker イメージを提供することもできます。

## 次のステップ

### リリース前に品質を確保する

- [モジュールテスト（ErisPulse-Testing）](testing.md) — 自動テストで上記のチェックリストを先に一通り実行
- [モジュールのベストプラクティス](modules/best-practices.md) / [アダプターのベストプラクティス](adapters/best-practices.md) — リリース前のエンジニアリング仕上げ

### リリース後にユーザーが使えるようにする

- [CLI コマンド](../user-guide/cli-reference.md) — ユーザー側の `epsdk install` / `epsdk upgrade` の動作
- [プラットフォーム機能ガイド](../platform-guide/README.md) — アダプター作者がプラットフォームドキュメントを整備するための参照先