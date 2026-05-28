<table>
<tr>
<td width="35%" valign="middle" align="center">

<img src=".github/assets/mascot-hero.png" width="320" alt="ErisPulse" />

</td>
<td valign="middle">

[English](README.en.md) | **简体中文** | [繁體中文](README.zh-TW.md)

# ErisPulse

**事件驱动的多平台机器人开发框架**

基于 OneBot12 标准接口，一次编写，多平台部署。灵活的插件系统、热重载支持和完整的开发者工具链，适用于从简单聊天机器人到复杂自动化系统的各种场景。

> 支持 Vibe Coding 工作流，让 AI 直接生成可用模块 — [查看](docs/zh-CN/ai-support/README.md)

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/ErisPulse/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/r/erispulse/erispulse)
[![License](https://img.shields.io/github/license/ErisPulse/ErisPulse?style=flat-square)](https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=flat-square)](https://github.com/ErisPulse/ErisPulse)
[![Downloads](https://img.shields.io/pypi/dm/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[![文档](https://img.shields.io/badge/文档-erisdev.com-0a0a0a?style=flat-square)](https://www.erisdev.com)
[![模块市场](https://img.shields.io/badge/模块市场-erisdev.com-0a0a0a?style=flat-square)](https://www.erisdev.com/#market)
[![讨论](https://img.shields.io/badge/GitHub-Discussions-0a0a0a?style=flat-square&logo=github)](https://github.com/ErisPulse/ErisPulse/discussions)

</td>
</tr>
</table>

---

<div align="center">

### 核心特性

</div>

<table>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### 事件驱动架构

基于 OneBot12 标准的清晰事件模型，让消息处理逻辑更加直观和高效

</td>
<td width="50%" align="center" valign="top">
<br/>

### 跨平台兼容

插件模块编写一次即可在所有平台使用，无需为不同平台重复开发

</td>
</tr>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### 模块化设计

灵活的插件系统，易于扩展和集成，支持热插拔模块管理

</td>
<td width="50%" align="center" valign="top">
<br/>

### 热重载支持

开发时无需重启即可重新加载代码，大幅提升开发迭代效率

</td>
</tr>
</table>

---

### 支持的适配器

<div align="center">
<img src=".github/assets/adapter-showcase.png" width="520" alt="支持的适配器" />

欢迎您贡献适配器！

| 适配器 | 说明 |
|--------|------|
| [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook（开黑啦）即时通讯平台 |
| [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix 去中心化通讯协议 |
| [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 通用机器人协议 |
| [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 标准协议 |
| [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ 官方机器人平台 |
| [沙箱](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | 网页端调试，无需接入真实平台 |
| [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | 全球性即时通讯平台 |
| [邮件](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | 邮件协议收发适配器 |
| [云湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | 企业级即时通讯平台（机器人接入） |
| [云湖用户](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | 基于云湖用户协议的接入适配器 |
| [花枫咖啡馆](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |

查看 [适配器详情介绍](docs/zh-CN/platform-guide/README.md)

</div>

---

### 快速开始

#### 使用 Docker (推荐)

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

<details>
<summary>使用预发布版本 (Dev)</summary>

设置 `ERISPULSE_CHANNEL=dev` 即可使用预发布版本：

```bash
# 方式一：使用环境变量（推荐）
ERISPULSE_CHANNEL=dev ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d

# 方式二：构建 dev 镜像
ERISPULSE_BUILD_TARGET=dev docker compose up -d --build
```

如需启动时自动更新到最新版本（无论 stable 还是 dev），显式设置 `ERISPULSE_UPDATE_ON_START=true`：

```bash
ERISPULSE_CHANNEL=dev ERISPULSE_UPDATE_ON_START=true docker compose up -d
```

也可以拉取预构建的 dev 镜像：

```bash
docker pull erispulse/erispulse:dev
```

</details>

<details>
<summary>Docker 环境变量</summary>

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ERISPULSE_CHANNEL` | `stable` | 版本通道：`stable`（稳定版）或 `dev`（预发布版） |
| `ERISPULSE_UPDATE_ON_START` | `false` | 容器启动时是否自动更新到最新版本（需显式启用） |
| `ERISPULSE_DASHBOARD_TOKEN` | 空 | Dashboard 登录令牌 |
| `ERISPULSE_PORT` | `8000` | Dashboard 端口映射 |
| `TZ` | `Asia/Shanghai` | 容器时区 |

> 启用 `ERISPULSE_UPDATE_ON_START=true` 可确保即使镜像较旧，容器也能在启动时自动获取最新版本。

</details>

#### 1Panel 应用商店

通过 [1Panel](https://1panel.cn) 应用商店一键安装 ErisPulse，详见 [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel)。

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

#### 使用 pip 安装

```bash
pip install ErisPulse

# 国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ErisPulse

# 使用 uv 安装
uv pip install ErisPulse
```

![安装演示](.github/assets/docs/install_pip.gif)

> 如果您的 Python 版本低于 3.10，可以使用一键安装脚本自动配置环境。详见 [安装脚本说明](scripts/install/)。

#### 初始化项目

```bash
# 交互式初始化
epsdk init

# 快速初始化（指定项目名称）
epsdk init -q -n my_bot
```

#### 创建第一个机器人

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

---

### 应用场景

<div align="center">

| 多平台机器人 | 聊天助手 | 自动化工具 | 消息转发 |
|:---:|:---:|:---:|:---:|
| 在多个平台部署<br>相同功能的机器人 | 接入 AI 聊天模块<br>实现娱乐和交互 | 消息通知、任务管理<br>数据收集 | 跨平台消息<br>同步和转发 |

</div>

---

### 文档与资源

| 简体中文 | English | 繁體中文 |
|:---:|:---:|:---:|
| [文档入口](docs/zh-CN/README.md) | [Documentation](docs/en/README.md) | [文檔入口](docs/zh-TW/README.md) |

| 平台 | 主站点 | 备用站点 |
|------|--------|---------|
| 文档 | [erisdev.com](https://www.erisdev.com/#docs) | [Cloudflare](https://erispulse.pages.dev/#docs) · [GitHub](https://erispulse.github.io/#docs) · [Netlify](https://erispulse.netlify.app/#docs) |
| 模块市场 | [erisdev.com](https://www.erisdev.com/#market) | [Cloudflare](https://erispulse.pages.dev/#market) · [GitHub](https://erispulse.github.io/#market) · [Netlify](https://erispulse.netlify.app/#market) |

---

### 贡献指南

ErisPulse 项目的健全性还需要您的一份力！我们欢迎各种形式的贡献：

1. **报告问题** — 在 [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) 提交 bug 报告
2. **功能请求** — 通过 [社区讨论](https://github.com/ErisPulse/ErisPulse/discussions) 提出新想法
3. **代码贡献** — 提交 PR 前请阅读 [代码风格](docs/zh-CN/styleguide/) 及 [贡献指南](CONTRIBUTING.md)
4. **文档改进** — 帮助完善文档和示例代码

[加入社区讨论](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### 致谢

<img src=".github/assets/thanks.png" width="200" alt="感谢" />

本项目部分代码基于 [sdkFrame](https://github.com/runoneall/sdkFrame) · 核心适配器标准化层基于 [OneBot12 规范](https://12.onebot.dev/) · 感谢所有为开源社区做出贡献的开发者和作者

</div>
