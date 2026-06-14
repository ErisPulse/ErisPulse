<table>
<tr>
<td width="35%" valign="middle" align="center">

<img src=".github/assets/mascot-hero.png" width="320" alt="ErisPulse" />

</td>
<td valign="middle">

> [English](README.en.md) | **简体中文** | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

> 🎉 **v2.5.0-dev.1 现已支持多语言！** 框架核心及 CLI 界面已内置中文（简/繁）、英文、日文、俄文支持，自动检测您的系统语言!

# ErisPulse

**事件驱动的多平台机器人开发框架**

基于 OneBot12 标准接口，一次编写，多平台部署。灵活的插件系统、热重载支持和完整的开发者工具链，适用于从简单聊天机器人到复杂自动化系统的各种场景。

> 支持 Vibe Coding 工作流，让 AI 直接生成可用模块 — [查看](docs/zh-CN/ai-support/README.md)

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ErisPulse/)
[![Python](https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://pypi.org/project/ErisPulse/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/erispulse/erispulse)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=brightgreen)](https://github.com/ErisPulse/ErisPulse)
[![Downloads](https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue)](https://pypi.org/project/ErisPulse/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge)](https://github.com/astral-sh/ruff)
[![Socket](https://img.shields.io/badge/Socket-Secure-2ea043?style=for-the-badge&logo=socket&logoColor=white)](https://socket.dev/pypi/package/erispulse)

[![文档](https://img.shields.io/badge/文档-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white)](https://www.erisdev.com)
[![模块市场](https://img.shields.io/badge/模块市场-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white)](https://www.erisdev.com/#market)
[![讨论](https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github)](https://github.com/ErisPulse/ErisPulse/discussions)

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

### ⚡ 事件驱动架构

基于 OneBot12 标准的清晰事件模型，让消息处理逻辑更加直观和高效

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🌐 跨平台兼容

插件模块编写一次即可在所有平台使用，无需为不同平台重复开发

</td>
</tr>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### 🧩 模块化设计

灵活的插件系统，易于扩展和集成，支持热插拔模块管理

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🔄 热重载支持

开发时无需重启即可重新加载代码，大幅提升开发迭代效率

</td>
</tr>
</table>

---

### 快速开始

#### 一键安装脚本（推荐）

安装脚本会自动检测您的环境（Docker、Python、uv），引导选择最适合的安装方式，支持多语言（中文/English/日本語/Русский/繁體中文）。

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

<table>
<tr>
<td align="center" width="50%">

**Docker 安装演示**

<video src="https://github.com/user-attachments/assets/a367a466-4678-46a9-b101-073a86388ede" controls width="100%"></video>

</td>
<td align="center" width="50%">

**pip 安装演示**

<video src="https://github.com/user-attachments/assets/a2df4009-dba6-411e-b79d-4454a168d063" controls width="100%"></video>

</td>
</tr>
</table>

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
```

> 也可以使用上方的一键安装脚本，自动检测环境并引导配置。

#### 运行效果


##### 仪表盘：

[![在线演示](https://img.shields.io/badge/在线演示-Dashboard-FF6B9D?style=for-the-badge&logo=github&logoColor=white)](https://dashdemo.erisdev.com/)

> 💡 在线体验演示仪表盘：[DashDemo](https://dashdemo.erisdev.com/)

<table>
<tr>
<td width="50%">

<img src=".github/assets/docs/dashboard.png" alt="Dashboard 演示" />

</td>
<td width="50%">

<video src="https://github.com/user-attachments/assets/157191c4-9a84-433c-b311-0c57e3a21151" controls width="100%"></video>

</td>
</tr>
</table>


##### 同一端代码，多个平台响应：

<table>
<tr>
<td align="center" width="33%">

**Kook**

<img src=".github/assets/demo-kook.png" alt="Kook 演示" />

</td>
<td align="center" width="33%">

**QQ**

<img src=".github/assets/demo-qq.png" alt="QQ 演示" />

</td>
<td align="center" width="33%">

**云湖**

<img src=".github/assets/demo-yunhu.png" alt="云湖 演示" />

</td>
</tr>
</table>

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

#### 多轮对话示例

ErisPulse 内置了强大的多轮对话引擎，轻松实现引导式操作、信息收集等交互场景：

```python
from ErisPulse.Core.Event import command, request

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("欢迎注册！")
    
    # 多步骤收集用户信息，自动验证
    data = await conv.collect([
        {"key": "name", "prompt": "请输入姓名"},
        {"key": "age", "prompt": "请输入年龄",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "年龄必须是数字，请重新输入"},
    ])
    
    if data and await conv.confirm(f"确认注册？姓名: {data['name']}, 年龄: {data['age']}"):
        # 通过 SendDSL 主动推送通知
        await sdk.adapter.get(event.get_platform()).Send.To(
            "user", event.get_user_id()
        ).Text(f"注册成功！欢迎 {data['name']}")
        # 或 await event.reply("注册成功！")

# 自动处理好友请求
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    
    # 同意请求
    result = await event.approve()
    if result.get("status") == "ok":
        await event.reply(f"已自动通过好友请求，欢迎 {user_name}")
```

<details>
<summary>查看更多 Conversation API（分支跳转 / 选择 / 持久化）</summary>

```python
@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)
    
    # 选项式问答
    answer = await conv.choose("Python 的创造者是谁？", [
        "Guido van Rossum",
        "James Gosling", 
        "Dennis Ritchie",
    ])
    
    if answer == 0:
        await conv.say("正确！")
    elif answer is None:
        await conv.say("超时了，下次再来吧！")
    else:
        await conv.say("错误了，正确答案是 Guido van Rossum")

@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)
    
    # 分支跳转，构建复杂交互流程
    @conv.branch("main")
    async def main_menu():
        await conv.say("=== 主菜单 ===\n1. 个人信息\n2. 设置\n3. 退出")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "1":
            await conv.goto("profile")
    
    @conv.branch("profile")
    async def profile():
        await conv.say("姓名: Alice\n0. 返回")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")
    
    await conv.start()
```

详见 [Conversation 多轮对话](docs/zh-CN/advanced/conversation.md)

</details>

---

### 支持的适配器

欢迎您贡献适配器！

| 适配器 | 说明 |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook（开黑啦）即时通讯平台 |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix 去中心化通讯协议 |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 通用机器人协议 |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 标准协议 |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ 官方机器人平台 |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [沙箱](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | 网页端调试，无需接入真实平台 |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | 全球性即时通讯平台 |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [邮件](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | 邮件协议收发适配器 |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [云湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | 企业级即时通讯平台（机器人接入） |
| [云湖用户](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | 基于云湖用户协议的接入适配器 |
| [花枫咖啡馆](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |

查看 [适配器详情介绍](docs/zh-CN/platform-guide/README.md)

---

### 应用场景

<div align="center">

| 多平台机器人 | 聊天助手 | 自动化工具 | 消息转发 |
|:---:|:---:|:---:|:---:|
| 在多个平台部署<br>相同功能的机器人 | 接入 AI 聊天模块<br>实现娱乐和交互 | 消息通知、任务管理<br>数据收集 | 跨平台消息<br>同步和转发 |

</div>

---

### 贡献指南

ErisPulse 项目的健全性还需要您的一份力！我们欢迎各种形式的贡献：

1. **报告问题** — 在 [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) 提交 bug 报告
2. **功能请求** — 通过 [社区讨论](https://github.com/ErisPulse/ErisPulse/discussions) 提出新想法
3. **代码贡献** — 提交 PR 前请阅读 [代码风格](docs/zh-CN/styleguide/) 及 [贡献指南](CONTRIBUTING.md)
4. **文档改进** — 帮助完善文档和示例代码

[加入社区讨论](https://github.com/ErisPulse/ErisPulse/discussions)

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ErisPulse/ErisPulse&type=Date)](https://star-history.com/#ErisPulse/ErisPulse&Date)

---

<div align="center">

### 致谢

<img src=".github/assets/thanks.png" width="200" alt="感谢" />

本项目部分代码基于 [sdkFrame](https://github.com/runoneall/sdkFrame) · 核心适配器标准化层基于 [OneBot12 规范](https://12.onebot.dev/) · 感谢所有为开源社区做出贡献的开发者和作者

</div>
