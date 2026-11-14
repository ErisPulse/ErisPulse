# リリースとモジュールストアのガイド

> [!TIP]
> **この記事を読む必要があるのはいつか**：作品を PyPI / モジュールストアに公開する場合。必要ない場合は飛ばしても、他の機能の使用に支障はありません。

ErisPulse モジュールストアに開発したモジュールやアダプターを公開し、他のユーザーが簡単に発見してインストールできるようにしましょう。

## モジュールストアの概要

ErisPulse モジュールストアは、集中管理されたモジュール登録表です。ユーザーは CLI ツールを使って、コミュニティが提供したモジュールやアダプターを閲覧、検索、インストールできます。

### 閲覧と発見

```bash
# リモートに利用可能なすべてのパッケージを表示
epsdk list-remote

# モジュールのみを表示
epsdk list-remote -t modules

# アダプターのみを表示
epsdk list-remote -t adapters

# リモートパッケージリストを強制的に更新
epsdk list-remote -r
```

ErisPulse 公式サイト ([https://www.erisdev.com/#market](https://www.erisdev.com/#market)) や [ErisPulse Workbench](https://workbench.erisdev.com/) の「モジュールリスト」からオンラインでモジュールストアを閲覧することもできます。

### 提出可能なタイプ

| タイプ | 説明 | Entry-point 組 |
|------|------|----------------|
| モジュール (Module) | ロボットの機能拡張、業務ロジックの実装 | `erispulse.module` |
| アダプター (Adapter) | 新しいメッセージプラットフォームとの接続 | `erispulse.adapter` |

## 速攻リリース

3ステップで完了：プロジェクトの設定 → PyPI へのリリース → モジュールストアへの提出

### 1. pyproject.toml の設定

プロジェクトディレクトリに `pyproject.toml`、`README.md` が存在することを確認し、タイプに応じて entry-points を設定します。

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

### 2. PyPI へのリリース

```bash
# ビルド + リリース（PyPI アカウントが必要）
pip install build twine
python -m build
python -m twine upload dist/*
```

リリースが成功したら、インストールを確認します。

```bash
pip install ErisPulse-MyModule
```

### 3. モジュールストアに提出（ErisPulse Workbench）

モジュールの収録と認証はすべて **ErisPulse Workbench** で行います：**[https://workbench.erisdev.com/](https://workbench.erisdev.com/)**。提出後、`repository_dispatch` でモジュールインデックスリポジトリに配信され、ワークフローが完了するとストアに反映されます（通常数分以内）。

#### 方法1：ウェブサイトから提出（初回推奨）

1. ウェブワークベンチを開き、**GitHub / Codeberg** アカウントでログインします（過去のモジュールは、モジュール詳細ページの「このモジュールを認証」から所有権を取得できます）
2. 左メニューの「新規モジュールを提出」→ フォームに記入：名称 / タイプ（module · adapter）/ PyPI パッケージ名 / 説明（10文字以上）/ 作者 / リポジトリアドレス（github.com または codeberg.org）/ カテゴリ（1 ツール · 2 エンタメ · 3 管理 · 4 通知 · 5 AI · 6 プラットフォーム · 7 分析）/ タグ / 最低 SDK バージョン
3. 提出すると即時有効化され、「未検証」と表示されます（公式審査がまだで、ユーザーがインストール時にリスク警告を確認する必要があります）；「認証審査」が通ると「検証済み」になります

#### 方法2：API による自主提出（CLI / CI 環境）

**① アクセストークンの生成**：ワークベンチの「オープンインターフェース → アクセストークン」ページ → 名前を記入 →「トークン生成」。形式は `epat_` + 40桁の16進数で、**生成時に一度だけ表示されます**；二段階認証を有効にしているアカウントは「動的コード不要」にチェックを付けると、以降のセキュアなエンドポイントで `totp_code` を要求されなくなります。

**② 要求の形式**：

```http
Authorization: Bearer epat_…
Content-Type: application/json
```

リクエストボディは **UTF-8 エンコードの JSON** でなければなりません。Windows 終端ではデフォルトの GBK で、日本語が UTF-8 以外のバイトに変換され、サーバーは拒否します（`415 ENCODING_INVALID` とエラーメッセージが表示され、問題のあるフィールドが明示されます）—— 事前に `chcp 65001` を実行するか、リクエストボディを UTF-8 ファイルに保存して `curl --data-binary @body.json` で送信してください。

**③ モジュールの提出**：

```bash
curl -X POST https://workbench.erisdev.com/api/modules/submit \
  -H "Authorization: Bearer epat_…" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MyModule",
    "type": "module",
    "package": "ErisPulse-MyModule",
    "description": "モジュール説明、10文字以上",
    "author": "Your Name",
    "repository": "https://github.com/you/MyModule",
    "category": 1,
    "tags": ["ツール"],
    "i18n": ["ja", "en"],
    "min_sdk_version": ">=2.7.0"
  }'
```

**④ 検索と管理**：`GET /api/modules/ops?name=MyModule&type=module` で提出・審査の進捗を確認できます；`POST /api/modules/manage` で編集 / 転正 / 削除ができます；`POST /api/modules/batch` で一括操作が可能です。完全なエンドポイント一覧は、ワークベンチの「使用文書」（トークン / 所有権の認証 / モジュール管理 / FAQ）をご覧ください。

### 4. 既にリリースしたモジュールの管理

ワークベンチの「モジュールリスト」にログイン → 自分のモジュールの詳細ページで、説明、リポジトリ、タグなどを編集できます（バージョン番号は PyPI から自動同期されます）、削除、所有権の認証を開始できます；API 側は `manage` / `batch` エンドポイントを使用します。

> 提出したばかりのモジュールは、リストに反映されるまで数分かかる場合があります。

## 既にリリースしたモジュールの更新

1. `pyproject.toml` の `version` を更新
2. 再びビルドしてアップロード：`python -m build && python -m twine upload dist/*`
3. モジュールストアは自動的に PyPI 上の最新バージョンを同期します

ユーザーは `epsdk upgrade MyModule` でアップデートできます。

## リリース前のチェックリスト

PyPI にプッシュする前に、以下の項目を一つ一つ確認してください：

### コード品質

- [ ] 公開 API に型注釈を付与（関数の引数と戻り値）
- [ ] 公開メソッドにドキュメント文字列を付与（`"""..."""` 形式、`:param` / `:return` / `:raises` を含む）
- [ ] `ruff check` で警告が発生しない
- [ ] テストカバレッジは 80% 以上
- [ ] `pytest` ですべてのテストが通る

### 兼容性

- [ ] `pyproject.toml` に最低 SDK バージョンを宣言：`dependencies = ["ErisPulse>=x.y.z"]`
- [ ] `get_meta()` の `ModuleMeta(min_sdk_version="x.y.z")` で実行時の最低 SDK バージョンを宣言（アダプターはクラス属性 `min_sdk_version` を使用）—— ユーザー環境の SDK が低すぎる場合、フレームワークはロード時に明確なエラーを表示してロードをスキップし、不明なランタイムエラーを回避します
- [ ] Python 3.10 / 3.11 / 3.12 / 3.13 でテスト
- [ ] 対象オペレーティングシステム（Windows / Linux / macOS、該当する場合）でテスト
- [ ] 循環インポートの依存がない

### 設定

- [ ] 宣言的設定（`ConfigClass` + `BaseConfig` / `BotAccountConfig`）を使用する場合、設定フィールドに `description`（i18n 形式が推奨）と `ui` メタデータを付与
- [ ] i18n 翻訳キーを登録している場合、5言語すべて（zh-CN / zh-TW / en / ja / ru）をカバー
- [ ] 敏感なフィールドには `secret=True` を付与

### ドキュメント

- [ ] `README.md` にインストール方法と基本的な使用例を記載
- [ ] `README.md` に設定方法（設定ファイルの例 + 環境変数）を記載
- [ ] `CHANGELOG.md` にすべての変更を記録
- [ ] アダプターはプラットフォームの機能ドキュメントを更新（サポートする Send タイプ、イベントタイプなど）

### リリース

- [ ] `pyproject.toml` のバージョン番号を更新
- [ ] ビルドが通る：`python -m build`
- [ ] PyPI にアップロード：`python -m twine upload dist/*`
- [ ] インストールの検証が通る：`pip install ErisPulse-xxx && epsdk run`

## 開発モードでのテスト

正式リリース前に、ローカルで編集可能なモードでテストできます：

```bash
epsdk install -e /path/to/MyModule
# または
pip install -e /path/to/MyModule
```

## 一般的な質問

### パッケージ名は `ErisPulse-` で始める必要があるか？

必須ではありませんが、強く推奨します。これは PyPI 上で ErisPulse エコシステムのパッケージをユーザーが識別しやすくするためです。

### 1つのパッケージで複数のモジュールを登録できるか？

できます。`entry-points` に複数のキーと値を設定できます：

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### 審査にはどのくらい時間がかかるか？

通常 1〜3 営業日で完了します。モジュールストアの「マイモジュール」で検証ステータスを確認できます。

## Docker イメージでアプリケーションを配布する

PyPI に公開するのに適していない場合（プライベート依存、事前設定環境が必要な場合）、**GitHub Container Registry (GHCR)** を使って Docker イメージを公開し、他のユーザーが `docker pull` で一発起動できるようにできます。

### 適用シーン

- あなたが**完全なロボットアプリケーション**（モジュール + 設定 + 入口スクリプト）を持っていて、ワンクリックで配布したい
- モジュール/アダプターが**プライベートパッケージ**や特別なインストールフローを必要とするため、PyPI に適していない
- ユーザーの使用を容易にする**オールインワン**のデプロイメントを提供したい

### 1. Dockerfile の作成

ErisPulse 公式イメージをベースに、あなたのモジュールを追加するだけです：

```dockerfile
FROM erispulse/erispulse:latest

LABEL org.opencontainers.image.title="ErisPulse-MyModule" \
      org.opencontainers.image.description="モジュール説明" \
      org.opencontainers.image.url="https://github.com/yourname/ErisPulse-MyModule" \
      org.opencontainers.image.source="https://github.com/yourname/ErisPulse-MyModule"

COPY pyproject.toml README.md ./
COPY MyModule/ ./MyModule/

RUN uv pip install --system -e .
```

モジュールに追加のシステム依存（例：SSH クライアントなど）が必要な場合は、`RUN uv pip install` の後に追加します：

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` には ErisPulse、ErisPulse-Dashboard、Python 実行環境、uv が含まれているため、再度インストールする必要はありません。

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

      - name: QEMU のセットアップ (多アーキテクチャ対応)
        uses: docker/setup-qemu-action@v3

      - name: Docker Buildx のセットアップ
        uses: docker/setup-buildx-action@v3

      - name: GitHub Container Registry にログイン
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

> `GITHUB_TOKEN` は GitHub Actions が自動提供するため、手動でキーを作成する必要はありません。

### 3. ビルドのトリガー

コードをプッシュするか、タグを打つと自動的にビルドされます：

```bash
# main ブランチにプッシュしてトリガー
git push origin main

# またはタグを打ってトリガー
git tag v1.0.0
git push origin v1.0.0
```

GitHub リポジトリの **Actions** ページから手動でトリガーすることもできます。

### 4. イメージを公開に設定

GHCR イメージはデフォルトで **private** です。他のユーザーがログインせずにプルできるようにするには、GitHub で公開に設定する必要があります：

1. リポジトリにアクセス → **Packages** → 対応するパッケージをクリック
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. ユーザーの使用

ビルドが完了したら、ユーザーは `docker run` で一行で起動できます：

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

### Docker Hub にも同時に公開する

ワークフローを拡張し、ログインステップの前に Docker Hub にログインし、`images` に Docker Hub のアドレスを追加します：

```yaml
      - name: Docker Hub にログイン
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

### Docker イメージ vs PyPI リリース

| 特性 | Docker イメージ (GHCR) | PyPI リリース |
|------|---------------------|-----------|
| 分布方法 | `docker pull` で一発起動 | `pip install` + 手動設定 |
| 適用範囲 | 完全なアプリケーション/ソリューション | 単一のモジュール/アダプター |
| プライベート依存 | 天然にサポート | プライベート PyPI ソースが必要 |
| モジュールストア | 不適切 | モジュールストアに提出可能 |
| 多アーキテクチャ | amd64/arm64 をサポート | アーキテクチャに依存しない |

両方の方法は互いに矛盾しません——モジュールを PyPI でモジュールストアに公開すると同時に、GHCR でオールインワンの Docker イメージを提供することも可能です。

## 次に進む

### リリース前に品質を確保する

- [モジュールテスト（ErisPulse-Testing）](testing.md) — 上記のチェックリストを自動テストで実行する
- [モジュールのベストプラクティス](modules/best-practices.md) / [アダプターのベストプラクティス](adapters/best-practices.md) — リリース前のエンジニアリングの仕上げ

### リリース後にユーザーが使いやすいようにする

- [CLI コマンド](../user-guide/cli-reference.md) — ユーザー側の `epsdk install` / `epsdk upgrade` の動作
- [プラットフォーム特性ガイド](../platform-guide/README.md) — アダプター開発者がプラットフォームドキュメントを維持する場所