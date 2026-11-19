# 發布與模組商店指南

> [!TIP]
> **什麼時候需要讀這篇**：將作品發布到 PyPI / 模組商店時。不需要則跳過，不影響其它功能的使用。

將你開發的模組或配接器發布到 ErisPulse 模組商店，讓其他使用者可以方便地發現和安裝。

## 模組商店概述

ErisPulse 模組商店是一個集中式的模組註冊表，使用者可以透過 CLI 工具瀏覽、搜尋和安裝社群貢獻的模組、配接器。

### 瀏覽與發現

```bash
# 列出遠端可用的所有套件
epsdk list-remote

# 只檢視模組
epsdk list-remote -t modules

# 只檢視配接器
epsdk list-remote -t adapters

# 強制重新整理遠端套件清單
epsdk list-remote -r
```

你也可以造訪 [ErisPulse 官網](https://www.erisdev.com/#market) 或 [ErisPulse Workbench](https://workbench.erisdev.com/) 的「模組清單」線上瀏覽模組商店。

### 支援的提交類型

| 類型 | 說明 | Entry-point 組 |
|------|------|----------------|
| 模組 | 擴充機器人功能、實作業務邏輯 | `erispulse.module` |
| 配接器 | 連接新的訊息平台 | `erispulse.adapter` |

## 快速發布

整個過程只需要三步：設定專案 → 發布到 PyPI → 提交到模組商店。

### 1. 設定 pyproject.toml

確保專案目錄包含 `pyproject.toml`、`README.md`，並根據類型設定 entry-points：

#### 模組

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "模組功能描述"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [ { name = "yourname" } ]
dependencies = [
    "ErisPulse>=2.0.0",
]

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

#### 配接器

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "配接器功能描述"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **注意**：套件名稱建議以 `ErisPulse-` 開頭，便於使用者識別。Entry-point 的鍵名（如 `"MyModule"`）將作為模組在 SDK 中的存取名稱。

### 2. 發布到 PyPI

```bash
# 建置 + 發布（需要 PyPI 帳號）
pip install build twine
python -m build
python -m twine upload dist/*
```

發布成功後驗證安裝：

```bash
pip install ErisPulse-MyModule
```

### 3. 提交到模組商店（ErisPulse Workbench）

模組收錄與認證統一由 **ErisPulse Workbench** 承載：**[https://workbench.erisdev.com/](https://workbench.erisdev.com/)**。提交後經 `repository_dispatch` 下發到模組索引儲存庫，workflow 完成即入商店（通常數分鐘）。

#### 方式一：網頁提交（推薦首次使用）

1. 開啟工作台，用 **GitHub / Codeberg** 帳號登入（歷史時期的模組可在模組詳情頁走「認領此模組」找回歸屬）
2. 左側「提交新模組」→ 按表單填寫：名稱 / 類型（module · adapter）/ PyPI 套件名稱 / 描述（≥10 字元）/ 作者 / 儲存庫地址（github.com 或 codeberg.org）/ 分類（1 工具 · 2 娛樂 · 3 管理 · 4 通知 · 5 AI · 6 平台 · 7 分析）/ 標籤 / 最低 SDK 版本
3. 提交即生效並標記「未驗證」（僅表示尚未官方審核，使用者安裝時會收到風險提示需確認）；「認證審核」通過後轉為「已驗證」

#### 方式二：API 自主提交（CLI / CI 場景）

**① 產生存取權杖**：工作台「開放介面 → 存取權杖」頁 → 填寫名稱 →「產生權杖」。格式為 `epat_` + 40 位十六進位，**僅產生時顯示一次**；開啟兩步驟驗證的帳戶可勾選「免動態碼」，之後敏感介面不再要求 `totp_code`。

**② 呼叫慣例**：

```http
Authorization: Bearer epat_…
Content-Type: application/json
```

請求主體必須為 **UTF-8 編碼的 JSON**。Windows 終端機預設 GBK，中文會被寫成非 UTF-8 位元組，伺服器端直接拒絕（報錯 `415 ENCODING_INVALID` 並指出問題欄位）——先執行 `chcp 65001`，或把請求主體存成 UTF-8 檔案後用 `curl --data-binary @body.json` 提交。

**③ 提交模組**：

```bash
curl -X POST https://workbench.erisdev.com/api/modules/submit \
  -H "Authorization: Bearer epat_…" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MyModule",
    "type": "module",
    "package": "ErisPulse-MyModule",
    "description": "模組描述，至少 10 字元",
    "author": "Your Name",
    "repository": "https://github.com/you/MyModule",
    "category": 1,
    "tags": ["工具"],
    "i18n": ["zh", "en"],
    "min_sdk_version": ">=2.7.0"
  }'
```

**④ 查詢與管理**：`GET /api/modules/ops?name=MyModule&type=module` 查提交/審核進度；`POST /api/modules/manage` 編輯 / 轉正 / 刪除；`POST /api/modules/batch` 批次操作。完整端點表見工作台內建「使用文件」（權杖 / 歸屬認領 / 模組管理 / FAQ）。

### 4. 管理已發布的模組

登入工作台「模組清單」→ 自己的模組詳情頁，可編輯描述、儲存庫、標籤等（版本號自動從 PyPI 同步）、刪除模組、發起歸屬認領；API 側走 `manage` / `batch` 端點。

> 剛提交的模組可能需要幾分鐘才會出現在清單中。

## 更新已發布模組

1. 更新 `pyproject.toml` 中的 `version`
2. 重新建置並上傳：`python -m build && python -m twine upload dist/*`
3. 模組商店會自動同步 PyPI 上的最新版本

使用者透過 `epsdk upgrade MyModule` 即可升級。

## 發布前檢查清單

在推送到 PyPI 之前，請逐項確認以下內容：

### 程式碼品質

- [ ] 所有公開 API 有型別註解（函式簽名和回傳值）
- [ ] 所有公開方法有文件字串（`"""..."""` 格式，包含 `:param` / `:return` / `:raises`）
- [ ] 通過 `ruff check`（無警告）
- [ ] 測試覆蓋率 ≥ 80%
- [ ] 通過 `pytest` 全部用例

### 相容性

- [ ] `pyproject.toml` 宣告了最低 SDK 版本：`dependencies = ["ErisPulse>=x.y.z"]`
- [ ] 模組在 `get_meta()` 的 `ModuleMeta(min_sdk_version="x.y.z")` 宣告了執行階段最低 SDK 版本（配接器用類別屬性 `min_sdk_version`）——使用者環境 SDK 過低時框架在載入階段明確報錯並跳過，而非報出難以定位的執行階段例外
- [ ] 測試了 Python 3.10 / 3.11 / 3.12 / 3.13
- [ ] 測試了目標作業系統（Windows / Linux / macOS，如適用）
- [ ] 無循環匯入依賴

### 設定

- [ ] 如果使用宣告式設定（`ConfigClass` + `BaseConfig` / `BotAccountConfig`），設定欄位有 `description`（推薦 i18n 格式）和 `ui` 中繼資料
- [ ] 如果註冊了 i18n 翻譯鍵，已涵蓋所有 5 種語言（zh-CN / zh-TW / en / ja / ru）
- [ ] 敏感欄位標記了 `secret=True`

### 文件

- [ ] `README.md` 有安裝說明和基本使用範例
- [ ] `README.md` 說明了設定方式（設定檔範例 + 環境變數）
- [ ] `CHANGELOG.md` 記錄了所有變更
- [ ] 配接器更新了平台特性文件（支援的 Send 類型、事件類型等）

### 發布

- [ ] `pyproject.toml` 版本號已更新
- [ ] 建置通過：`python -m build`
- [ ] 已推送到 PyPI：`python -m twine upload dist/*`
- [ ] 安裝驗證通過：`pip install ErisPulse-xxx && epsdk run`

## 開發模式測試

在正式發布前，可以使用可編輯模式在本機測試：

```bash
epsdk install -e /path/to/MyModule
# 或
pip install -e /path/to/MyModule
```

## 常見問題

### 套件名稱必須以 `ErisPulse-` 開頭嗎？

不強制，但強烈推薦。這有助於使用者在 PyPI 上識別 ErisPulse 生態的套件。

### 一個套件可以註冊多個模組嗎？

可以。在 `entry-points` 中設定多個鍵值對即可：

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### 審核需要多長時間？

通常在 1-3 個工作天內完成。你可以在模組商店「我的模組」中查看驗證狀態。

## 透過 Docker 映像散佈應用程式

如果你的應用程式不適合發布到 PyPI（如包含私有依賴、需要預先設定環境），可以透過 **GitHub Container Registry (GHCR)** 發布 Docker 映像，讓其他使用者 `docker pull` 一鍵啟動。

### 適用場景

- 你有一個**完整的機器人應用程式**（模組 + 設定 + 進入點腳本），想一鍵散佈
- 模組/配接器依賴**私有套件**或有特殊安裝流程，不適合 PyPI
- 想提供**開箱即用**的部署方案，降低使用者使用門檻

### 1. 建立 Dockerfile

基於 ErisPulse 官方映像建置，只需加入你的模組即可：

```dockerfile
FROM erispulse/erispulse:latest

LABEL org.opencontainers.image.title="ErisPulse-MyModule" \
      org.opencontainers.image.description="模組描述" \
      org.opencontainers.image.url="https://github.com/yourname/ErisPulse-MyModule" \
      org.opencontainers.image.source="https://github.com/yourname/ErisPulse-MyModule"

COPY pyproject.toml README.md ./
COPY MyModule/ ./MyModule/

RUN uv pip install --system -e .
```

如果模組需要額外的系統依賴（如 SSH 用戶端等），在 `RUN uv pip install` 之後加入：

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` 已包含 ErisPulse、ErisPulse-Dashboard、Python 執行環境和 uv，無需重複安裝。

### 2. 建立 GitHub Actions 工作流程

在 `.github/workflows/docker-publish.yml` 中建立：

```yaml
name: 發布 Docker 映像

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
      - name: 檢出程式碼
        uses: actions/checkout@v4

      - name: 設定 QEMU (多架構支援)
        uses: docker/setup-qemu-action@v3

      - name: 設定 Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: 登入 GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: 擷取 Docker 中繼資料
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: 建置並推送 Docker 映像
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

> `GITHUB_TOKEN` 由 GitHub Actions 自動提供，無需手動建立密鑰。

### 3. 觸發建置

推送程式碼或打 Tag 即可自動建置：

```bash
# 推送到 main 分支觸發
git push origin main

# 或打 Tag 觸發
git tag v1.0.0
git push origin v1.0.0
```

也可在 GitHub 儲存庫的 **Actions** 頁面手動觸發。

### 4. 將映像設為公開

GHCR 映像預設為 **private**，需要在 GitHub 設為 Public 後其他使用者才能免登入拉取：

1. 進入儲存庫 → **Packages** → 點擊對應 Package
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. 使用者使用

建置完成後，使用者可以用 `docker run` 一行啟動：

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

或使用 `docker-compose.yml`：

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

### 同時發布到 Docker Hub

擴充工作流程，在登入步驟前加入 Docker Hub 登入，並在 `images` 中增加 Docker Hub 位址：

```yaml
      - name: 登入 Docker Hub
        uses: docker/login-action@v3
        with:
          registry: docker.io
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: 擷取 Docker 中繼資料
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            docker.io/<your-dockerhub-username>/my-bot
            ghcr.io/${{ github.repository_owner }}/my-bot
```

> 需要在儲存庫 **Settings → Secrets** 中加入 `DOCKERHUB_USERNAME` 和 `DOCKERHUB_TOKEN`。

### Docker 映像 vs PyPI 發布

| 特性 | Docker 映像 (GHCR) | PyPI 發布 |
|------|---------------------|-----------|
| 散佈方式 | `docker pull` 一鍵執行 | `pip install` + 手動設定 |
| 適用範圍 | 完整應用程式/解決方案 | 單一模組/配接器 |
| 私有依賴 | 天然支援 | 需要私有 PyPI 來源 |
| 模組商店 | 不適用 | 可提交到模組商店 |
| 多架構 | 支援 amd64/arm64 | 與架構無關 |

兩種方式不衝突——你可以同時透過 PyPI 發布模組到模組商店，又透過 GHCR 提供開箱即用的 Docker 映像。

## 下一步

### 發布前為品質把關

- [模組測試（ErisPulse-Testing）](testing.md) — 用自動化測試先跑一遍上面的檢查清單
- [模組最佳實踐](modules/best-practices.md) / [配接器最佳實踐](adapters/best-practices.md) — 發布前的工程化收尾

### 發布後讓使用者用起來

- [CLI 指令](../user-guide/cli-reference.md) — 使用者側 `epsdk install` / `epsdk upgrade` 的行為
- [平台特性指南](../platform-guide/README.md) — 配接器作者維護平台文件的落點