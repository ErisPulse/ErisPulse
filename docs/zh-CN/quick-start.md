# 快速开始

> 遇到不理解的术语？查看 [术语表](terminology.md) 获取通俗易懂的解释。

## 安装 ErisPulse

### 一键安装脚本（推荐）

安装脚本会自动检测您的环境（Docker、Python、uv），并引导您选择最适合的安装方式。

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh | bash
```

脚本会引导您完成：

- **Docker 安装**（检测到 Docker 时推荐）：选择镜像源（Docker Hub / GHCR）、版本通道（稳定版 / 预发布版）、Dashboard 管理面板配置、端口设置
- **传统安装**：自动创建虚拟环境、选择 ErisPulse 版本、可选安装 Dashboard 管理面板模块

### 使用 Docker

Docker 镜像已内置 ErisPulse 框架和 Dashboard 管理面板。

```bash
# 下载 docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# 设置 Dashboard 令牌并启动
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Docker Hub 不可用？</summary>

使用 GitHub Container Registry 镜像，修改 `docker-compose.yml` 中的 image：

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

启动后访问 `http://<host>:8000/Dashboard`，使用设置的令牌登录。

### 使用 pip 安装

确保你的 Python 版本 >= 3.10，然后使用 pip 安装：

```bash
pip install ErisPulse
```

如果你已安装 [uv](https://github.com/astral-sh/uv)，也可以使用 `uv pip install ErisPulse`，安装速度更快。

## 初始化项目

### 交互式初始化（推荐）

```bash
epsdk init
```

这将启动一个交互式向导，引导您完成：
- 项目名称设置
- 日志级别配置
- 服务器配置（主机和端口）
- 适配器选择和配置
- 项目结构创建

### 快速初始化

```bash
# 指定项目名称的快速模式
epsdk init -q -n my_bot

# 或者只指定项目名称
epsdk init -n my_bot
```

### 手动创建项目

如果更喜欢手动创建项目：

```bash
mkdir my_bot && cd my_bot
epsdk init
```

## 安装模块

### 通过 CLI 安装

```bash
epsdk install Yunhu AIChat
```

### 查看可用模块

```bash
epsdk list-remote
```

### 交互式安装

不指定包名时进入交互式安装界面：

```bash
epsdk install
```

## 运行项目

```bash
# 普通运行
epsdk run main.py

# 热重载模式（开发时推荐）
epsdk run main.py --reload
```

## 项目结构

初始化后的项目结构：

```
my_bot/
├── config/
│   └── config.toml          # 配置文件
└── main.py                  # 入口文件

```

## 配置文件

基本的 `config.toml` 配置：

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# 适配器配置
```

## 下一步

- [入门指南总览](getting-started/README.md) - 了解 ErisPulse 的基本概念
- [创建第一个机器人](getting-started/first-bot.md) - 创建一个简单的机器人
- [用户使用指南](user-guide/) - 深入了解配置和模块管理
- [开发者指南](developer-guide/) - 开发自定义模块和适配器
