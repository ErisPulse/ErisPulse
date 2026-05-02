<div align="center">

[English](README.en.md) | [简体中文](README.md) | [繁體中文](README.zh-TW.md)

</div>

<table>
<tr>
<td width="35%" valign="middle" align="center">
<img src=".github/assets/erispulse_logo_1024.png" width="280" alt="ErisPulse" />
</td>
<td width="65%" valign="middle">

# ErisPulse

**事件驱动的多平台机器人开发框架**

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Python Versions](https://img.shields.io/pypi/pyversions/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Docker Pulls](https://img.shields.io/docker/pulls/erispulse/erispulse?style=flat-square&logo=docker&label=pulls)](https://hub.docker.com/r/erispulse/erispulse)
[![Docker Pulls](https://img.shields.io/docker/pulls/wsu2059/erispulse?style=flat-square&logo=docker&label=pulls)](https://hub.docker.com/r/erispulse/erispulse)
[![Docker Version](https://img.shields.io/docker/v/erispulse/erispulse?style=flat-square&logo=docker&label=docker)](https://hub.docker.com/r/erispulse/erispulse)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

</td>
</tr>
</table>

---

## 简介

ErisPulse 是一个基于 Python 的事件驱动型多平台机器人开发框架。通过统一的 OneBot12 标准接口，您可以一次编写代码，同时在云湖、Telegram、OneBot 等多个平台部署相同功能的机器人。框架提供灵活的模块(`插件`)系统、热重载支持和完整的开发者工具链，适用于从简单聊天机器人到复杂自动化系统的各种场景。

## 核心特性

- **事件驱动架构** - 基于 OneBot12 标准的清晰事件模型
- **跨平台兼容** - 插件模块编写一次即可在所有平台使用
- **模块化设计** - 灵活的插件系统，易于扩展和集成
- **热重载支持** - 开发时无需重启即可重新加载代码
- **完整工具链** - 提供 CLI 工具、包管理和自动化脚本

## 支持的适配器

欢迎您贡献适配器！

| 适配器 | 说明 |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" width="20" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook（开黑啦）即时通讯平台 |
| <img src=".github/assets/adapter_logo/matrix.svg" width="20" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix 去中心化通讯协议 |
| <img src=".github/assets/adapter_logo/onebot.png" width="20" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 通用机器人协议 |
| <img src=".github/assets/adapter_logo/onebot.png" width="20" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 标准协议 |
| <img src=".github/assets/adapter_logo/qqbot.svg" width="20" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ 官方机器人平台 |
| <img src=".github/assets/adapter_logo/sandbox.png" width="20" /> [沙箱](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | 网页端调试，无需接入真实平台 |
| <img src=".github/assets/adapter_logo/telegram.svg" width="20" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | 全球性即时通讯平台 |
| <img src=".github/assets/adapter_logo/email.svg" width="20" /> [邮件](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | 邮件协议收发适配器 |
| <img src=".github/assets/adapter_logo/yunhu.png" width="20" /> [云湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | 企业级即时通讯平台（机器人接入） |
| <img src=".github/assets/adapter_logo/yunhu.png" width="20" /> [云湖用户](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | 基于云湖用户协议的接入适配器 |

查看 [适配器详情介绍](docs/zh-CN/platform-guide/README.md)

## 快速开始

### 使用 Docker (推荐)

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Docker Hub不可用？</summary>

如果 Docker Hub 无法访问，可以使用 GitHub Container Registry：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

使用 ghcr.io 镜像时，需要修改 `docker-compose.yml` 中的 image：
```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

<details>
<summary>快速启动</summary>

```bash
# 下载 docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# 设置 Dashboard 登录令牌并启动
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

> 镜像内置 ErisPulse 框架和 Dashboard 管理面板，支持 `linux/amd64` 和 `linux/arm64` 架构。

启动后访问 `http://<host>:<port>/Dashboard`，使用设置的令牌作为密码登录 Dashboard 管理面板。

</details>

### 使用 pip 安装

```bash
pip install ErisPulse

# 国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ErisPulse

# 使用 uv 安装
uv pip install ErisPulse
```

![安装演示](.github/assets/docs/install_pip.gif)

> 如果您的 Python 版本低于 3.10，可以使用一键安装脚本自动配置环境。详见 [安装脚本说明](scripts/install/)。

### 初始化项目

```bash
# 交互式初始化
epsdk init

# 快速初始化（指定项目名称）
epsdk init -q -n my_bot
```

### 创建第一个机器人

创建 `main.py` 文件：

<table>
<tr>
<td width="50%" valign="top">

**命令处理器**

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="发送问候消息")
async def hello_handler(event):
    user_name = event.get_user_nickname() or "朋友"
    await event.reply(f"你好，{user_name}！")

@command("ping", help="测试机器人是否在线")
async def ping_handler(event):
    await event.reply("Pong！机器人运行正常。")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

</td>
<td width="50%" valign="top">

**效果说明**

发送 `/hello`

机器人回复：`你好，{用户名}！`

---

发送 `/ping`

机器人回复：`Pong！机器人运行正常。`

---

**运行方式**

```bash
epsdk run main.py
# 或开发模式
epsdk run main.py --reload
```

</td>
</tr>
</table>

更多详细说明请参阅：
- [快速开始指南](docs/zh-CN/quick-start.md)
- [入门指南](docs/zh-CN/getting-started/)

## 应用场景

- **多平台机器人** - 在多个平台部署相同功能的机器人
- **聊天助手** - 接入 AI 聊天模块，实现娱乐和交互
- **自动化工具** - 消息通知、任务管理、数据收集
- **消息转发** - 跨平台消息同步和转发

## 文档资源

| 简体中文 | English | 繁體中文 |
|----------------|----------------|----------------|
| [文档入口](docs/zh-CN/README.md) | [Documentation](docs/en/README.md) | [文檔入口](docs/zh-TW/README.md) |

## 外部资源

| 平台 | 主站点 | 备用站点 |
|------|--------|---------|
| 文档 | [erisdev.com](https://www.erisdev.com/#docs) | [Cloudflare](https://erispulse.pages.dev/#docs) • [GitHub](https://erispulse.github.io/#docs) • [Netlify](https://erispulse.netlify.app/#docs) |
| 模块市场 | [erisdev.com](https://www.erisdev.com/#market) | [Cloudflare](https://erispulse.pages.dev/#market) • [GitHub](https://erispulse.github.io/#market) • [Netlify](https://erispulse.netlify.app/#market) |

## 贡献指南

ErisPulse 项目的健全性还需要您的一份力！我们欢迎各种形式的贡献，包括但不限于：

1. **报告问题**
   在 [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) 提交 bug 报告

2. **功能请求**
   通过 [社区讨论](https://github.com/ErisPulse/ErisPulse/discussions) 提出新想法

3. **代码贡献**
   提交 Pull Request 前请阅读我们的 [代码风格](docs/zh-CN/styleguide/) 以及 [贡献指南](CONTRIBUTING.md)

4. **文档改进**
   帮助完善文档和示例代码

[加入社区讨论](https://github.com/ErisPulse/ErisPulse/discussions)

---

## 致谢

- 本项目部分代码基于 [sdkFrame](https://github.com/runoneall/sdkFrame)
- 核心适配器标准化层基于 [OneBot12 规范](https://12.onebot.dev/)
- 感谢所有为开源社区做出贡献的开发者和作者
