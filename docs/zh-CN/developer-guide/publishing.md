# 发布与模块商店指南

将你开发的模块或适配器发布到 ErisPulse 模块商店，让其他用户可以方便地发现和安装。

## 模块商店概述

ErisPulse 模块商店是一个集中式的模块注册表，用户可以通过 CLI 工具浏览、搜索和安装社区贡献的模块、适配器。

### 浏览与发现

```bash
# 列出远程可用的所有包
epsdk list-remote

# 只查看模块
epsdk list-remote -t modules

# 只查看适配器
epsdk list-remote -t adapters

# 强制刷新远程包列表
epsdk list-remote -r
```

你也可以访问 [ErisPulse 官网](https://www.erisdev.com/#market) 在线浏览模块商店。

### 支持的提交类型

| 类型 | 说明 | Entry-point 组 |
|------|------|----------------|
| 模块 (Module) | 扩展机器人功能、实现业务逻辑 | `erispulse.module` |
| 适配器 (Adapter) | 连接新的消息平台 | `erispulse.adapter` |

## 发布流程

整个发布流程分为四个步骤：准备项目 → 发布到 PyPI → 提交到模块商店 → 审核上线。

### Step 1: 准备项目

确保你的项目包含以下文件：

```
MyModule/
├── pyproject.toml      # 项目配置（必须）
├── README.md           # 项目说明（必须）
├── LICENSE             # 开源许可证（推荐）
└── MyModule/
    ├── __init__.py     # 包入口
    └── ...
```

### Step 2: 配置 pyproject.toml

根据你要发布的类型，正确配置 `entry-points`：

#### 模块

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "模块功能描述"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [ { name = "yourname" } ]
dependencies = [
    "ErisPulse>=2.0.0",
]

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

#### 适配器

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "适配器功能描述"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **注意**：包名建议以 `ErisPulse-` 开头，便于用户识别。Entry-point 的键名（如 `"MyModule"`）将作为模块在 SDK 中的访问名称。

### Step 3: 发布到 PyPI

```bash
# 安装构建工具
pip install build twine

# 构建分发包
python -m build

# 发布到 PyPI
python -m twine upload dist/*
```

发布成功后，确认你的包可以通过 `pip install` 安装：

```bash
pip install ErisPulse-MyModule
```

### Step 4: 提交到 ErisPulse 模块商店

在确认包已发布到 PyPI 后，前往 [ErisPulse-ModuleRepo](https://github.com/ErisPulse/ErisPulse-ModuleRepo/issues/new?template=module_submission.md) 提交申请。

填写以下信息：

#### 提交类型

选择你要提交的类型：
- 模块 (Module)
- 适配器 (Adapter)

#### 基本信息

| 字段 | 说明 | 示例 |
|------|------|------|
| **名称** | 模块/适配器名称 | Weather |
| **描述** | 简短功能描述 | 天气查询模块，支持全球城市 |
| **作者** | 你的名字或 GitHub 用户名 | MyName |
| **仓库地址** | 代码仓库 URL | https://github.com/MyName/MyModule |

#### 技术信息

| 字段 | 说明 |
|------|------|
| **最低 SDK 版本要求** | 如 `>=2.0.0`（如适用） |
| **依赖项** | 除 ErisPulse 外的额外依赖（如适用） |

#### 标签

用逗号分隔，帮助用户搜索发现你的模块。例如：`天气, 查询, 工具`

#### 检查清单

提交前请确认：
- 代码遵循 ErisPulse 开发规范
- 包含适当的文档（README.md）
- 包含测试用例（如适用）
- 已在 PyPI 发布

### Step 5: 审核与上线

提交后，维护者会审核你的申请。审核要点：

1. 包可以在 PyPI 上正常安装
2. Entry-point 配置正确，能被 SDK 正确发现
3. 功能与描述一致
4. 不存在安全问题或恶意代码
5. 不与已有模块严重冲突

审核通过后，你的模块会自动出现在模块商店中。

## 更新已发布模块

当你更新模块版本时：

1. 更新 `pyproject.toml` 中的 `version`
2. 重新构建并上传到 PyPI：
   ```bash
   python -m build
   python -m twine upload dist/*
   ```
3. 模块商店会自动同步 PyPI 上的最新版本信息

用户可以通过以下命令升级：

```bash
epsdk upgrade MyModule
```

## 开发模式测试

在正式发布前，你可以使用可编辑模式在本地测试：

```bash
# 以可编辑模式安装
epsdk install -e /path/to/MyModule

# 或使用 pip
pip install -e /path/to/MyModule
```

## 常见问题

### Q: 包名必须以 `ErisPulse-` 开头吗？

不强制，但强烈推荐。这有助于用户在 PyPI 上识别 ErisPulse 生态的包。

### Q: 一个包可以注册多个模块吗？

可以。在 `entry-points` 中配置多个键值对即可：

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### Q: 如何指定最低 SDK 版本要求？

在 `pyproject.toml` 的 `dependencies` 中设置：

```toml
dependencies = [
    "ErisPulse>=2.0.0",
]
```

模块商店会检查版本兼容性，防止用户安装不兼容的模块。

### Q: 审核需要多长时间？

通常在 1-3 个工作日内完成。你可以在 Issue 中查看审核进度。

## 通过 Docker 镜像分发应用

如果你的应用不适合发布到 PyPI（如包含私有依赖、需要预配置环境），可以通过 **GitHub Container Registry (GHCR)** 发布 Docker 镜像，让其他用户 `docker pull` 一键启动。

### 适用场景

- 你有一个**完整的机器人应用**（模块 + 配置 + 入口脚本），想一键分发
- 模块/适配器依赖**私有包**或有特殊安装流程，不适合 PyPI
- 想提供**开箱即用**的部署方案，降低用户使用门槛

### 1. 创建 Dockerfile

基于 ErisPulse 官方镜像构建：

```dockerfile
FROM python:3.13-slim AS production

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    ERISPULSE_DASHBOARD_TOKEN=""

WORKDIR /app

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY . .

VOLUME ["/app/config"]
EXPOSE 8000

CMD ["epsdk", "run", "main.py"]
```

如果模块未发布到 PyPI，可以直接把模块源码复制进镜像：

```dockerfile
FROM python:3.13-slim AS production

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

RUN uv pip install --system ErisPulse ErisPulse-Dashboard

COPY my_modules/ /app/my_modules/
COPY main.py .
COPY config/ /app/config/

RUN uv pip install --system -e /app/my_modules/MyModule

VOLUME ["/app/config"]
EXPOSE 8000

CMD ["epsdk", "run", "main.py"]
```

### 2. 创建 GitHub Actions 工作流

在 `.github/workflows/docker-publish.yml` 中创建：

```yaml
name: 发布 Docker 镜像

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
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 设置 QEMU (多架构支持)
        uses: docker/setup-qemu-action@v3

      - name: 设置 Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: 登录 GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: 提取 Docker 元数据
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: 构建并推送 Docker 镜像
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

> `GITHUB_TOKEN` 由 GitHub Actions 自动提供，无需手动创建密钥。

### 3. 触发构建

推送代码或打 Tag 即可自动构建：

```bash
# 推送到 main 分支触发
git push origin main

# 或打 Tag 触发
git tag v1.0.0
git push origin v1.0.0
```

也可在 GitHub 仓库的 **Actions** 页面手动触发。

### 4. 设置镜像为公开

GHCR 镜像默认为 **private**，需要在 GitHub 设置为 Public 后其他用户才能免登录拉取：

1. 进入仓库 → **Packages** → 点击对应 Package
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. 用户使用

构建完成后，其他用户可以直接运行：

```bash
docker pull ghcr.io/<your-username>/my-bot:latest

docker run -d \
  --name my-bot \
  -p 8000:8000 \
  -v ./config:/app/config \
  -e ERISPULSE_DASHBOARD_TOKEN=your-token \
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

### 同时发布到 Docker Hub

扩展工作流，添加 Docker Hub 登录步骤，并在 `images` 中增加 Docker Hub 地址：

```yaml
      - name: 登录 Docker Hub
        uses: docker/login-action@v3
        with:
          registry: docker.io
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: 提取 Docker 元数据
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            docker.io/<your-dockerhub-username>/my-bot
            ghcr.io/${{ github.repository_owner }}/my-bot
```

> 需要在仓库 **Settings → Secrets** 中添加 `DOCKERHUB_USERNAME` 和 `DOCKERHUB_TOKEN`。

### Docker 镜像 vs PyPI 发布

| 特性 | Docker 镜像 (GHCR) | PyPI 发布 |
|------|---------------------|-----------|
| 分发方式 | `docker pull` 一键运行 | `pip install` + 手动配置 |
| 适用范围 | 完整应用/解决方案 | 单个模块/适配器 |
| 私有依赖 | 天然支持 | 需要私有 PyPI 源 |
| 模块商店 | 不适用 | 可提交到模块商店 |
| 多架构 | 支持 amd64/arm64 | 与架构无关 |

两种方式不冲突——你可以同时通过 PyPI 发布模块到模块商店，又通过 GHCR 提供开箱即用的 Docker 镜像。
