# 発行とモジュールストアガイド

> [!TIP]
> **この記事を読むタイミング**：作品を PyPI / モジュールストアに発行する場合。不要であれば飛ばしても、他の機能の使用に影響はありません。

開発したモジュールやアダプターを ErisPulse モジュールストアに発行し、他のユーザーが簡単に見つけたりインストールしたりできるようにしましょう。

## モジュールストア概要

ErisPulse モジュールストアは、モジュールやアダプターを一元的に登録し、ユーザーが CLI ツールを使ってコミュニティが提供したモジュールやアダプターを閲覧、検索、インストールできる仕組みです。

### 閲覧と発見

```bash
# すべてのリモートで利用可能なパッケージをリストアップ
epsdk list-remote

# モジュールのみを表示
epsdk list-remote -t modules

# アダプターのみを表示
epsdk list-remote -t adapters

# リモートパッケージリストを強制的に更新
epsdk list-remote -r
```

また、[ErisPulse 公式サイト](https://www.erisdev.com/#market)または[ErisPulse Workbench](https://workbench.erisdev.com/)の「モジュールリスト」でオンラインでモジュールストアを閲覧することもできます。Workbench のアカウント、モジュール管理、ホスティングドメインなどの機能は、[ErisPulse Workbench](../ecosystem/workbench.md)をご覧ください。

### 提出可能なタイプ

| タイプ | 説明 | Entry-point 組 |
|------|------|----------------|
| モジュール (Module) | ロボットの機能拡張、ビジネスロジックの実装 | `erispulse.module` |
| アダプター (Adapter) | 新しいメッセージプラットフォームへの接続 | `erispulse.adapter` |

## 速攻発行

発行プロセスは、3 つのステップで完了します：プロジェクトの設定 → PyPI への発行 → モジュールストアへの登録。

### 1. pyproject.toml の設定

プロジェクトのルートに `pyproject.toml`、`README.md` が存在することを確認し、タイプに応じて entry-points を設定します。

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

> **注意**：パッケージ名は `ErisPulse-` で始めるのが推奨です。Entry-point のキー名（例：`"MyModule"`）は、SDK 内でのモジュールのアクセス名になります。

### 2. PyPI への発行

```bash
# ビルド + 発行（PyPI アカウントが必要）
pip install build twine
python -m build
python -m twine upload dist/*
```

発行が成功した後、インストールを確認します：

```bash
pip install ErisPulse-MyModule
```

### 3. モジュールストアへの登録（ErisPulse Workbench）

モジュールの収録と認証はすべて **ErisPulse Workbench** で行います：**[https://workbench.erisdev.com/](https://workbench.erisdev.com/)**。登録後、`repository_dispatch` でモジュールインデックスリポジトリに配信され、ワークフローが完了するとストアに追加されます（通常数分）。Workbench のログイン、トークン、所有権の認証、ホスティングドメインについては、[ErisPulse Workbench](../ecosystem/workbench.md)をご覧ください。

#### 方法1：Web フォームによる登録（初回推奨）

1. Workbench にアクセスし、**GitHub / Codeberg** アカウントでログインします（過去のモジュールは、モジュール詳細ページの「このモジュールを認証」から所有権を取得できます）。
2. 左側の「新規モジュールの登録」→ フォームに記入：名前 / タイプ（module · adapter）/ PyPI パッケージ名 / 説明（10 字以上）/ 作者 / リポジトリアドレス（github.com または codeberg.org）/ カテゴリ（1 ツール · 2 娯楽 · 3 管理 · 4 通知 · 5 AI · 6 プラットフォーム · 7 分析）/ タグ / 最低 SDK バージョン
3. 登録すると即時有効となり、「未検証」にマークされます（公式の審査がまだ完了していないことを意味し、ユーザーがインストール時にリスク警告が表示され、確認が必要です）。「認証審査」が通ると「検証済み」に変わります。

#### 方法2：API による自主登録（CLI / CI 環境）

**① アクセストークンの生成**：Workbench の「API → アクセストークン」ページで、名前を入力し、「トークンの生成」をクリックします。形式は `epat_` + 40 文字の16進数で、**生成時に一度だけ表示されます**。2段階認証を有効にしているアカウントは「動的コード不要」にチェックを入れることで、その後のセキュアな API では `totp_code` を要求されなくなります。

**② リクエストの要件**：

```http
Authorization: Bearer epat_…
Content-Type: application/json
```

リクエストボディは **UTF-8 エンコードの JSON** でなければなりません。Windows のデフォルトは GBK で、日本語が UTF-8 でないバイト列として書き込まれ、サーバー側で拒否されます（エラーコード `415 ENCODING_INVALID` が返され、問題が指摘されます）—— 事前に `chcp 65001` を実行するか、リクエストボディを UTF-8 ファイルに保存し、`curl --data-binary @body.json` で送信してください。

**③ モジュールの登録**：

```bash
curl -X POST https://workbench.erisdev.com/api/modules/submit \
  -H "Authorization: Bearer epat_…" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MyModule",
    "type": "module",
    "package": "ErisPulse-MyModule",
    "description": "モジュールの説明、10 字以上",
    "author": "Your Name",
    "repository": "https://github.com/you/MyModule",
    "category": 1,
    "tags": ["ツール"],
    "i18n": ["ja", "en"],
    "min_sdk_version": ">=2.7.0"
  }'
```

**④ 状態の確認と管理**：`GET /api/modules/ops?name=MyModule&type=module` で登録・審査の進捗を確認できます。`POST /api/modules/manage` で編集・認証・削除が可能。`POST /api/modules/batch` で一括操作が可能です。詳細なエンドポイント一覧は、Workbench の「使用方法」ドキュメント（トークン / 所有権認証 / モジュール管理 / FAQ）をご覧ください。

### 4. 発行済みモジュールの管理

Workbench の「モジュールリスト」にログインし、自分のモジュールの詳細ページで、説明、リポジトリ、タグなどを編集できます（バージョン番号は PyPI から自動同期されます）。削除や所有権の認証も可能です。API 側では `manage` / `batch` エンドポイントを使用します。

> 初めて登録したモジュールは、リストに反映されるまで数分かかる場合があります。

## 既に発行済みのモジュールを更新する

1. `pyproject.toml` の `version` を更新します。
2. 再びビルドしてアップロードします：`python -m build && python -m twine upload dist/*`
3. モジュールストアは、PyPI 上の最新バージョンを自動的に同期します。

ユーザーは `epsdk upgrade MyModule` でアップデートできます。

## 発行前のチェックリスト

PyPI に送信する前に、以下の項目を1つずつ確認してください。

### コード品質

- [ ] すべての公開 API に型注釈（関数シグネチャと戻り値）
- [ ] すべての公開メソッドにドキュメント文字列（`"""..."""` 形式、`:param` / `:return` / `:raises` を含む）
- [ ] `ruff check` で警告がありません
- [ ] テストカバレッジが 80% 以上
- [ ] `pytest` で全てのテストが通過

### 兼容性

- [ ] `pyproject.toml` に最低 SDK バージョンを宣言：`dependencies = ["ErisPulse>=x.y.z"]`
- [ ] `get_meta()` の `ModuleMeta(min_sdk_version="x.y.z")` で実行時の最低 SDK バージョンを宣言（アダプターは `min_sdk_version` クラス属性を使用）—— SDK が古い場合、フレームワークはロード時に明確なエラーを表示し、実行時に見つかりにくい例外を回避します。
- [ ] Python 3.10 / 3.11 / 3.12 / 3.13 でテスト済み
- [ ] 対象オペレーティングシステム（Windows / Linux / macOS、該当する場合）でテスト済み
- [ ] 循環インポートの依存がない

### 設定

- [ ] 宣言的設定（`ConfigClass` + `BaseConfig` / `BotAccountConfig`）を使用している場合、設定フィールドに `description`（i18n 形式が推奨）と `ui` メタデータを記載
- [ ] i18n 翻訳キーを登録している場合、5 言語すべて（zh-CN / zh-TW / en / ja / ru）をカバー
- [ ] 敏感なフィールドは `secret=True` とマーク

### ドキュメント

- [ ] `README.md` にインストール方法と基本的な使用例を記載
- [ ] `README.md` に設定方法（設定ファイルの例 + 環境変数）を記載
- [ ] `CHANGELOG.md` にすべての変更履歴を記載
- [ ] アダプターの更新は、プラットフォームの特徴ドキュメント（サポートする Send タイプ、イベントタイプなど）を更新

### 発行

- [ ] `pyproject.toml` のバージョン番号を更新
- [ ] ビルドが成功：`python -m build`
- [ ] PyPI にアップロード：`python -m twine upload dist/*`
- [ ] インストールの確認が成功：`pip install ErisPulse-xxx && epsdk run`

## 開発モードでのテスト

正式に発行する前に、ローカルで編集可能なモードでテストできます：

```bash
epsdk install -e /path/to/MyModule
# または
pip install -e /path/to/MyModule
```

## よくある質問

### パッケージ名は `ErisPulse-` で始める必要がありますか？

必須ではありませんが、ErisPulse エコシステムのパッケージと識別できるように、強く推奨されます。

### 1 つのパッケージに複数のモジュールを登録できますか？

可能です。`entry-points` に複数のキー/値を記載できます：

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### 審査にはどのくらい時間がかかりますか？

通常、1〜3営業日で完了します。モジュールストアの「マイモジュール」で検証ステータスを確認できます。

## Docker イメージによるアプリケーションの配布

PyPI に発行するには不適切なアプリケーション（プライベート依存、事前設定が必要など）は、**GitHub Container Registry (GHCR)** に Docker イメージを発行し、他のユーザーが `docker pull` でワンクリックで起動できるようにすることができます。

### 適用場面

- あなたは**完全なロボットアプリケーション**（モジュール + 設定 + エントリースクリプト）を持っていて、ワンクリックで配布したい
- モジュール/アダプターが**プライベートパッケージ**や特別なインストール手順を必要とし、PyPI には適していない
- **開梱即使用**のデプロイメント方式を提供し、ユーザーの使用のハードルを下げたい

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

モジュールに追加のシステム依存（SSH クライアントなど）が必要な場合は、`RUN uv pip install` の後に追加してください：

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` には ErisPulse、ErisPulse-Dashboard、Python 実行時環境、uv が含まれているため、再度インストールする必要はありません。

### 2. GitHub Actions ワークフローの作成

`.github/workflows/docker-publish.yml` に作成します：

```yaml
name: Docker イメージの発行

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

      - name: QEMU の設定 (多アーキテクチャ対応)
        uses: docker/setup-qemu-action@v3

      - name: Docker Buildx の設定
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

> `GITHUB_TOKEN` は GitHub Actions が自動的に提供するため、手動でキーを作成する必要はありません。

### 3. ビルドのトリガー

コードをプッシュするか、タグを打つことで自動的にビルドされます：

```bash
# main ブランチにプッシュしてトリガー
git push origin main

# またはタグを打ってトリガー
git tag v1.0.0
git push origin v1.0.0
```

GitHub リポジトリの **Actions** ページからも手動でトリガーできます。

### 4. イメージを公開する

GHCR イメージはデフォルトで **private** ですが、GitHub で公開設定に変更する必要があります。他のユーザーがログインせずにプルできるようになります：

1. リポジトリにアクセス → **Packages** → 対応する Package をクリック
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. ユーザーの使用

ビルドが完了後、ユーザーは `docker run` で1行で起動できます：

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

### Docker Hub への同時発行

ワークフローを拡張し、ログインステップの前に Docker Hub へのログインを追加し、`images` に Docker Hub アドレスを追加します：

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

> `DOCKERHUB_USERNAME` と `DOCKERHUB_TOKEN` は、リポジトリの **Settings → Secrets** に追加する必要があります。

### Docker イメージ vs PyPI 発行

| 特性 | Docker イメージ (GHCR) | PyPI 発行 |
|------|---------------------|-----------|
| 分配方法 | `docker pull` でワンクリック実行 | `pip install` + 手動設定 |
| 適用範囲 | 完全なアプリケーション/ソリューション | 単一モジュール/アダプター |
| プライベート依存 | 天然にサポート | プライベート PyPI ソースが必要 |
| モジュールストア | 適用不可 | モジュールストアに登録可能 |
| 多アーキテクチャ | amd64/arm64 をサポート | アーキテクチャに依存しない |

両方の方法は互いに矛盾せず、モジュールを PyPI でモジュールストアに発行すると同時に、GHCR で開梱即使用の Docker イメージを提供することも可能です。

## 次に進む

### 発行前に品質チェック

- [モジュールテスト（ErisPulse-Testing）](testing.md) — 上記のチェックリストを自動テストで実行
- [モジュールのベストプラクティス](modules/best-practices.md) / [アダプターのベストプラクティス](adapters/best-practices.md) — 発行前のエンジニアリングの最終調整

### 発行後にユーザーに使ってもらう

- [CLI コマンド](../user-guide/cli-reference.md) — ユーザー側の `epsdk install` / `epsdk upgrade` の動作
- [プラットフォーム特性ガイド](../platform-guide/README.md) — アダプター開発者がプラットフォームドキュメントを維持する場所