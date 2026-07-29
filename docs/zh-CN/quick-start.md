# 快速开始

> **这是你的第一步。** 用 5 分钟从零跑起一个 ErisPulse 机器人。
>
> 遇到不理解的术语?查看 [术语表](terminology.md)。

## 安装 ErisPulse

### 一键安装脚本（推荐）

安装脚本会自动检测您的环境（Docker、Python、uv），并引导您选择最适合的安装方式。

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
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

## 启用 IDE 补全（可选）

ErisPulse 动态发现模块/适配器，IDE 默认无法补全平台特有方法。
运行以下命令生成类型存根：

```bash
epsdk types
```

生成后用导入的类型作为变量标注即可获得精确补全（详见 [IDE 补全指南](./getting-started/ide-completion.md)）：

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # 补全平台特有方法
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

机器人跑起来后，你可以按需继续：

**想了解框架怎么运作?**
- [基础概念](getting-started/basic-concepts.md) — 适配器 / 模块 / 事件 的设计
- [架构概览](architecture.md) — 可视化架构图

**想实现更多功能?**
- [常见任务示例](getting-started/common-tasks.md) — 存储、定时任务、权限控制
- [事件处理入门](getting-started/event-handling.md) — 消息、通知、请求处理

**想开发自己的模块 / 适配器?**
- [模块开发入门](developer-guide/modules/getting-started.md)
- [适配器开发入门](developer-guide/adapters/getting-started.md)

**按需查阅:**
- [配置文件说明](user-guide/configuration.md) · [CLI 命令](user-guide/cli-reference.md) · [部署指南](user-guide/deployment.md)
