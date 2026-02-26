<div align="center">

<img src=".github/assets/erispulse_logo_1024.png" width="100%" alt="ErisPulse" />

# ErisPulse

_事件驱动的多平台机器人开发框架_

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Python Versions](https://img.shields.io/pypi/pyversions/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Socket Badge](https://socket.dev/api/badge/pypi/package/ErisPulse/latest)](https://socket.dev/pypi/package/ErisPulse)

</div>

---

## 简介

ErisPulse 是一个基于 Python 的事件驱动型多平台机器人开发框架。通过统一的 OneBot12 标准接口，您可以一次编写代码，同时在云湖、Telegram、OneBot 等多个平台部署相同功能的机器人。框架提供灵活的模块(`插件`)系统、热重载支持和完整的开发者工具链，适用于从简单聊天机器人到复杂自动化系统的各种场景。

## 快速示例

```python
import asyncio
from ErisPulse import sdk
from ErisPulse.Core.Event import command

# 注册命令 - 一次编写，多平台运行
@command("hello")
async def hello(event):
    await event.reply("你好！来自 ErisPulse")

# 启动框架
asyncio.run(sdk.run(keep_running=True))
```

## 核心特性

- **事件驱动架构** - 基于 OneBot12 标准的清晰事件模型
- **跨平台兼容** - 插件模块编写一次即可在所有平台使用
- **模块化设计** - 灵活的插件系统，易于扩展和集成
- **热重载支持** - 开发时无需重启即可重新加载代码
- **完整工具链** - 提供 CLI 工具、包管理和自动化脚本

## 快速开始

### 安装

**方式一：使用 pip 安装**

```bash
pip install ErisPulse
```

**方式二：一键安装脚本**

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS/Linux:
```bash
curl -sSL https://get.erisdev.com/install.sh | tee install.sh >/dev/null && chmod +x install.sh && ./install.sh
```

### 初始化项目

```bash
# 交互式初始化
epsdk init

# 快速初始化（指定项目名称）
epsdk init -q -n my_bot
```

### 创建第一个机器人

创建 `main.py` 文件：

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="发送问候消息")
async def hello_handler(event):
    user_name = event.get_user_nickname() or "朋友"
    await event.reply(f"你好，{user_name}！我是 ErisPulse 机器人。")

@command("ping", help="测试机器人是否在线")
async def ping_handler(event):
    await event.reply("Pong！机器人运行正常。")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

### 运行项目

```bash
# 普通运行
epsdk run main.py

# 开发模式（支持热重载）
epsdk run main.py --reload
```

### 测试机器人

在已配置的聊天平台中发送 `/hello` 或 `/ping` 命令，您应该会收到机器人的回复。

更多详细说明请参阅：
- [快速开始指南](docs/quick-start.md)
- [入门指南](docs/getting-started/)

## 应用场景

- **多平台机器人** - 在多个平台部署相同功能的机器人
- **聊天助手** - 接入 AI 聊天模块，实现娱乐和交互
- **自动化工具** - 消息通知、任务管理、数据收集
- **消息转发** - 跨平台消息同步和转发

## 支持的适配器

欢迎您贡献适配器！

- [云湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) - 企业级即时通讯平台（机器人账户）
- [云湖用户](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) - 基于云湖用户账户的适配器
- [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) - 全球性即时通讯软件
- [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) - 通用机器人接口标准
- [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) - OneBot12 标准
- [邮件](https://github.com/ErisPulse/ErisPulse-EmailAdapter) - 邮件收发处理
- [沙箱](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) - 网页调试界面，无需接入实际平台

查看 [适配器详情介绍](docs/platform-guide/README.md)

## 文档资源

| 平台 | 主站点 | 备用站点 |
|------|--------|---------|
| 文档 | [erisdev.com](https://www.erisdev.com/#docs) | [Cloudflare](https://erispulse.pages.dev/#docs) • [GitHub](https://erispulse.github.io/#docs) • [Netlify](https://erispulse.netlify.app/#docs) |
| 模块市场 | [erisdev.com](https://www.erisdev.com/#market) | [Cloudflare](https://erispulse.pages.dev/#market) • [GitHub](https://erispulse.github.io/#market) • [Netlify](https://erispulse.netlify.app/#market) |

## 开发指南

如果您想为 ErisPulse 贡献代码，请按照以下步骤操作：

### 克隆项目

```bash
git clone -b Develop/v2 https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
```

### 环境搭建

使用 `uv` 同步项目环境：

```bash
uv sync
# 激活虚拟环境: source .venv/bin/activate (macOS/Linux) 或 .venv\Scripts\activate (Windows)
```

提示：ErisPulse 使用 Python 3.13 开发，兼容 Python 3.10+

### 项目结构

```
ErisPulse/
├── src/
│   └── ErisPulse/           # 核心源代码
│       ├── Core/            # 核心模块
│       │   ├── Bases/       # 基础类定义
│       │   ├── Event/       # 事件系统
│       │   └── ...          # 其他核心组件
│       └── __init__.py      # SDK入口点
├── examples/                # 示例代码
├── docs/                   # 文档
├── tests/                  # 测试代码
└── scripts/                # 脚本文件
```

## 贡献指南

我们欢迎各种形式的贡献，包括但不限于：

1. **报告问题**
   在 [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) 提交 bug 报告

2. **功能请求**
   通过 [社区讨论](https://github.com/ErisPulse/ErisPulse/discussions) 提出新想法

3. **代码贡献**
   提交 Pull Request 前请阅读我们的 [代码风格](docs/styleguide/docstring_spec.md) 以及 [贡献指南](CONTRIBUTING.md)

4. **文档改进**
   帮助完善文档和示例代码

[加入社区讨论](https://github.com/ErisPulse/ErisPulse/discussions)

---

## 致谢

- 本项目部分代码基于 [sdkFrame](https://github.com/runoneall/sdkFrame)
- 核心适配器标准化层基于 [OneBot12 规范](https://12.onebot.dev/)
- 感谢所有为开源社区做出贡献的开发者和作者