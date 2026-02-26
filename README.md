# ErisPulse - 异步机器人开发框架

<img src=".github/assets/erispulse_logo_1024.png" alt="ErisPulse Logo" width="100%" style="max-height: 300px; object-fit: contain;">

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Python Versions](https://img.shields.io/pypi/pyversions/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Socket Badge](https://socket.dev/api/badge/pypi/package/ErisPulse/latest)](https://socket.dev/pypi/package/ErisPulse)

ErisPulse 是一个事件驱动的多平台机器人开发框架。通过统一的适配器系统和标准化事件模型，让模块一次编写，即可在多个平台运行。

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

- **事件驱动** - 基于 OneBot12 标准的清晰事件模型
- **一次编写，全平台运行** - 插件模块编写一次即可在所有平台使用
- **模块化设计** - 灵活的插件系统，易于扩展开发
- **热重载** - 支持热重载，无需重启即可reload系统

## 应用场景

- **多平台机器人** - 在多个平台部署相同功能的机器人
- **聊天助手** - 接入自己的AI聊天模块，实现娱乐、交互机器人
- **自动化工具** - 消息通知、任务管理、数据收集
- **消息转发** - 跨平台消息同步和转发
> 你还能做更多更多，多到没有想象的边界 www

## 支持的适配器
> 也欢迎你贡献适配器 TwT~

- [云湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) - 企业级即时通讯平台（机器人账户）
- [云湖用户](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) - 基于云湖用户账户的适配器
- [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) - 全球性即时通讯软件
- [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) - 通用机器人接口标准
- [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) - OneBot12 标准
- [邮件](https://github.com/ErisPulse/ErisPulse-EmailAdapter) - 邮件收发处理
- [沙箱](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) - 网页调试界面，无需接入实际平台

> 查看[适配器详情介绍](docs-new/platform-guide/README.md)

## 文档资源

| 平台 | 主站点 | 备用站点 |
|------|--------|---------|
| 文档 | [erisdev.com](https://www.erisdev.com/#docs) | [Cloudflare](https://erispulse.pages.dev/#docs) • [GitHub](https://erispulse.github.io/#docs) • [Netlify](https://erispulse.netlify.app/#docs) |
| 模块市场 | [erisdev.com](https://www.erisdev.com/#market) | [Cloudflare](https://erispulse.pages.dev/#market) • [GitHub](https://erispulse.github.io/#market) • [Netlify](https://erispulse.netlify.app/#market) |

## 快速开始

### 一键安装脚本

#### Windows (PowerShell):

```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

#### macOS/Linux:

```bash
curl -sSL https://get.erisdev.com/install.sh | tee install.sh >/dev/null && chmod +x install.sh && ./install.sh
```

## 开发与测试

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

> 提示：ErisPulse 使用 Python 3.13 开发，兼容 Python 3.10+

**快速开始**：[快速开始指南](docs-new/quick-start.md) | [入门指南](docs-new/getting-started/)

## 项目结构

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
├── devs/                    # 开发工具
├── docs/                    # 文档
├── tests/                   # 测试代码
├── scripts/                 # 脚本文件
└── config.toml              # 默认配置文件
```

## 贡献指南

我们欢迎各种形式的贡献，包括但不限于:

1. 报告问题  
   在 [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) 提交bug报告

2. 功能请求  
   通过 [社区讨论](https://github.com/ErisPulse/ErisPulse/discussions) 提出新想法

3. 代码贡献  
   提交 Pull Request 前请阅读我们的 [代码风格](docs/styleguide/docstring_spec.md) 以及 [贡献指南](CONTRIBUTING.md)

4. 文档改进  
   帮助完善文档和示例代码

[加入社区讨论](https://github.com/ErisPulse/ErisPulse/discussions)

---

[![](https://starchart.cc/ErisPulse/ErisPulse.svg?variant=adaptive)](https://starchart.cc/ErisPulse/ErisPulse)