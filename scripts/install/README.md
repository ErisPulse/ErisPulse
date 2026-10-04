# ErisPulse 一键安装脚本

## 适用场景

当您希望快速部署 ErisPulse 时，推荐使用一键安装脚本。脚本会自动检测您的环境并引导选择最适合的安装方式。

脚本支持三种安装模式：

### Docker 安装（推荐）
- 自动检测 Docker 和 docker compose（已安装但未运行时会提示启动后重试）
- 支持选择 Docker Hub 或 GitHub Container Registry 镜像源
- 版本通道当前提供 stable（dev 预发布通道暂未提供，菜单中已标注）
- 可选配置 Dashboard 管理面板
- 自动生成 `docker-compose.yml` 和 `.env` 配置文件

### 全局 CLI 安装（uv tool，推荐）
- 通过 `uv tool install` 将 `epsdk` 安装为全局命令，无需虚拟环境
- uv 自动管理 Python（系统 Python 过低或缺失时自动安装）
- 项目目录内运行时自动感知项目 `.venv`，全局一份 epsdk 服务所有项目

### 传统安装（pip/uv + 虚拟环境）
- 自动检测 Python 版本（>= 3.10）
- 自动使用 uv（如果已安装）或 pip
- 创建独立的虚拟环境
- 支持选择 ErisPulse 版本
- 可选安装 Dashboard 管理面板模块

## 快速开始

### Windows

打开 PowerShell，执行以下命令：

```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

### macOS / Linux

打开终端，执行以下命令：

```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

## 使用说明

### 安装流程

1. 运行安装脚本
2. 脚本自动检测环境（Docker、Python、uv）
3. 选择安装方式：
   - **Docker 安装（推荐）**：如果检测到 Docker
   - **全局 CLI 安装（uv tool，推荐）**：全局命令行工具，无需虚拟环境
   - **传统安装**：使用 Python 虚拟环境
4. 根据引导完成配置
5. 安装完成后即可使用

### Docker 安装模式

Docker 模式会自动生成以下文件：

**docker-compose.yml**
```yaml
services:
  erispulse:
    image: erispulse/erispulse:latest
    container_name: ${CONTAINER_NAME:-erispulse}
    ports:
      - "${ERISPULSE_PORT:-8000}:8000"
    volumes:
      - ./config:/app/config
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    env_file:
      - .env
    restart: unless-stopped
```

**.env**
```env
ERISPULSE_DASHBOARD_TOKEN=your-token
TZ=Asia/Shanghai
```

> site-packages 挂载用于持久化经 Dashboard 热更新安装的模块与适配器，更新镜像后不丢失；时区可在 `.env` 中按需修改（如 `Asia/Tokyo`、`Europe/Berlin`）。

Docker 管理命令：
```bash
docker compose logs -f          # 查看日志
docker compose down             # 停止服务
docker compose restart          # 重启服务
docker compose pull && docker compose up -d  # 更新镜像
```

### 全局 CLI 安装模式

安装完成后 `epsdk` 即为全局命令，**无需激活任何虚拟环境**，在项目目录内直接使用：

```bash
epsdk init                  # 初始化项目（自动创建项目 .venv）
epsdk install <模块名>      # 组件安装进项目 .venv
epsdk run                   # 使用项目 .venv 运行机器人
epsdk self-update           # 更新框架（自动走 uv tool upgrade 通道）
```

若终端找不到 `epsdk`，请将 uv 的工具目录加入 PATH：

- Windows: `%USERPROFILE%\.local\bin`
- macOS/Linux: `~/.local/bin`

### 传统安装模式

安装完成后，激活虚拟环境：

Windows (PowerShell):
```powershell
.\.venv\Scripts\activate.ps1
```

macOS/Linux:
```bash
source .venv/bin/activate
```

退出虚拟环境：
```bash
deactivate
```

## 技术支持

遇到问题？请通过以下方式获取帮助：

- 查看 [完整文档](https://www.erisdev.com/#docs)
- 在 [GitHub Discussions](https://github.com/ErisPulse/ErisPulse/discussions) 提问
- 在 [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) 报告问题

## 相关链接

- [ErisPulse 主页](https://github.com/ErisPulse/ErisPulse)
- [PyPI 页面](https://pypi.org/project/ErisPulse/)
- [Docker Hub](https://hub.docker.com/r/erispulse/erispulse)
- [官方文档](https://www.erisdev.com)
- [uv 工具链](https://github.com/astral-sh/uv)