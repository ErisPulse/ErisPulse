---
name: erispulse-getting-started
description: "适用于：第一次接触 ErisPulse，想从零跑起一个机器人并理解核心概念。覆盖场景：[模块开发入门](developer-guide/modules/getting-started.md)。**1. 安装**（Python >= 3.10）：。机器人已经能跑，想写出第一个 `/hello` 命令处理器、搞懂 `sdk.run` 与命令装饰器各自在做什么。如果还没装好 ErisPulse、初始化项目，先完成 [5 分钟快速开始](../quick-start.md) 的「安装」「初始化项目」「运行项目」三步。一条消息从用户发出到机器人回复，中间经过了哪些组件？适配器和模块各自负责什么？读完这篇，写处理器时遇到的设计问题你都能自己回答，而不是只能照抄示例。想让机器人响应消息、命令、通知、请求，或要实现等待回复 / 多轮对话、排查"命令为什么没触发"时读。只想了解框架设计，看 [基础概念](basic-concepts.md) 即可。想给机器人加某个具体功能时按节查阅——持久化、定时任务、消息过滤、权限控制、批量发送，每一节都是可直接复制的完整示例。想系统学事件处理写法先看 [事件处理入门](event-handling.md)。IDE 补全不出适配器的平台特有方法（如云湖的 `Board`）或模块的自定义方法时，跑一条 `epsdk types` 命令生成类型存根即可解决。"
---

# ErisPulse 快速上手与核心概念

本技能由 ErisPulse 文档自动构建（generate-skills.py）。
仓库：https://github.com/ErisPulse/ErisPulse
各节末尾标注了来源文档路径，需要最新内容请以仓库 docs/zh-CN/ 为准。

## 文档总入口与阅读路径

> 来源: `docs/zh-CN/README.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/README.md）

# ErisPulse 文档

ErisPulse 是事件驱动的模块化异步机器人框架——业务代码只写一遍，通过适配器部署到 QQ、Telegram、Kook、云湖等多个平台，插件系统、热重载与完整开发者工具链开箱即用。

> **第一次使用?** 直接看 [5 分钟快速开始](quick-start.md) —— 从安装到运行第一个机器人，一条龙走完。

---

## 选择你的路径

根据你的目标，选择对应的学习路径。每条路径内部按由浅入深排列。

> [!IMPORTANT]
> **不需要读完所有文档。** 绝大多数开发者只需按顺序读完 **L1 核心五篇**
> （约 1–2 小时）即可独立开发 90% 的功能；其余文档全部是特定场景的按需
> 查阅资料——遇到对应需求再来翻，每篇开头都标了"什么时候需要读这篇"。
>
> **L1 核心五篇**：[模块开发入门](developer-guide/modules/getting-started.md)
> → [基础概念](getting-started/basic-concepts.md)
> → [Event 包装类](developer-guide/modules/event-wrapper.md)
> → [配置文件说明](user-guide/configuration.md)
> → [异常捕获](advanced/errors.md)
>
> 适配器作者另需：[适配器开发入门](developer-guide/adapters/getting-started.md)
> → [事件转换器](developer-guide/adapters/converter.md)
> → [SendDSL 详解](developer-guide/adapters/send-dsl.md)

### 一、我要使用机器人

让机器人跑起来、装模块、做配置。

| 进度 | 文档 | 说明 |
|------|------|------|
| **① 上手** | [5 分钟快速开始](quick-start.md) | 安装、初始化、运行 —— 唯一的起步入口 |
| App 直装 | [ErisPulse-App 客户端](ecosystem/app.md) | 官方全平台客户端：手机 / 电脑图形界面直接运行与管理，免终端 |
| ② 深入 | [创建第一个机器人](getting-started/first-bot.md) | 编写第一个命令处理器 |
| ③ 概念 | [基础概念](getting-started/basic-concepts.md) | 理解适配器/模块/事件的设计 |
| ④ 实战 | [常见任务示例](getting-started/common-tasks.md) | 存储、定时任务、权限控制 |
| 参考 | [配置文件说明](user-guide/configuration.md) · [CLI 命令](user-guide/cli-reference.md) · [部署指南](user-guide/deployment.md) | 按需查阅 |
| 参考 | [平台特性指南](platform-guide/README.md) | 各平台（云湖/QQ/Telegram…）的差异 |

### 二、我要开发模块 / 适配器

为 ErisPulse 编写可分发的扩展。

| 类型 | 入门 | 进阶 |
|------|------|------|
| **模块开发**（推荐） | [模块开发入门](developer-guide/modules/getting-started.md) | [核心概念](developer-guide/modules/core-concepts.md) · [Event 包装类](developer-guide/modules/event-wrapper.md) · [最佳实践](developer-guide/modules/best-practices.md) |
| **适配器开发** | [适配器开发入门](developer-guide/adapters/getting-started.md) | [核心概念](developer-guide/adapters/core-concepts.md) · [SendDSL 详解](developer-guide/adapters/send-dsl.md) · [事件转换器](developer-guide/adapters/converter.md) · [最佳实践](developer-guide/adapters/best-practices.md) |
| **技术标准** | [标准规范总览](standards/README.md) | 适配器开发必须遵循的 [会话类型](standards/session-types.md) · [事件转换](standards/event-conversion.md) · [发送方法](standards/send-method-spec.md) · [API 响应](standards/api-response.md) · [请求操作](standards/request-action-spec.md) 规范 |
| **测试与排查** | [模块测试（ErisPulse-Testing）](developer-guide/testing.md) | 分发决策链排查"命令为什么没触发" |
| **发布** | [发布与模块商店](developer-guide/publishing.md) | 将作品发布到 PyPI 和模块商店 |

### 三、我要深入理解原理

了解框架内部如何运作。先看架构与 API 参考，再按下面对照表进入专题。

**架构与 API 参考**

| 文档 | 说明 |
|------|------|
| [架构概览](architecture.md) | 可视化图表：核心架构、初始化流程、事件处理、生命周期、模块加载策略（含 `activate_on` 事件驱动懒激活）、本地插件文件夹与模块热重载架构（支持全部模块来源） |
| [事件系统](api-reference/event-system.md) | 五大类事件的完整 API |
| [适配器系统](api-reference/adapter-system.md) | 适配器注册、启停、API 调用 |
| [核心模块](api-reference/core-modules.md) | Storage / Config / Logger / Router 等基础能力 |

**L2 必读（写生产级模块绕不开）**

| 文档 | 说明 |
|------|------|
| [作用域（scope）](advanced/scope.md) | 三维作用域控制：模块可用性 / 事件准入 / 出站动作限制（含方法级细粒度规则、绑定继承 merge） |
| [归属权（owner）系统](advanced/ownership.md) | 资源归属与自动回收：owner 上下文、归属资源全景、卸载清理序列、设计边界与模块作者指南 |
| [生命周期管理](advanced/lifecycle.md) | 生命周期事件系统：模块 / 适配器加载、卸载、重载、禁用时各自该做什么 |
| [交互会话系统](advanced/interaction.md) | wait_reply 全解、会话定时器（remind/escalate）、多路等待（select）、会话互斥租约、收件箱、消息事务、链路追踪 |

**按场景分组（按需查阅）**

| 分组 | 文档 | 不懂首篇会踩的坑 |
|------|------|------|
| 运行启动 | [启动流程与手动控制](advanced/startup.md) · [懒加载](advanced/lazy-loading.md) | 不懂启动链路（Finder / Loader / Manager / Router），模块加载失败时只能对着日志干瞪眼 |
| 通信连接 | [模块间通信](advanced/module-communication.md) · [连接池与广播](advanced/connections.md) · [路由系统](advanced/router.md) | 不懂服务契约（`meta.services`）白名单，跨模块 `module.call` 会被 `ServiceNotProvidedError` 拒绝且不知原因 |
| 数据存储 | [存储后端](advanced/storage-backends.md) · [SQL 构建](advanced/sql-builder.md) · [HTTP 客户端](advanced/http-client.md) | 不懂连接失败冷却期语义，数据库抖动时会误判"框架挂了"（实际是存储操作快速失败、冷却后自动重连） |
| 消息对话 | [Conversation 多轮对话](advanced/conversation.md) · [会话收件箱](advanced/transcript.md) · [MessageBuilder](advanced/message-builder.md) · [国际化](advanced/i18n.md) | 不懂会话互斥租约，两个模块同时等同一用户的回复会互相踢掉 |
| 灰度影子 | [影子模块与灰度转正](advanced/shadow.md) | 不懂五道隔离闸就提前转正，影子的出站消息会外溢到真实用户 |

**概念关系总表**

分不清哪个子系统管什么时，按这张表对号入座：

| 子系统 | 回答什么问题 | 一句话口诀 |
|--------|------------|-----------|
| [通信](advanced/module-communication.md)（module-communication） | 模块之间怎么互相调用、怎么定向发事件？ | 跨模块走 `module.call`；对方声明了 `meta.services` 就只能调白名单内的方法 |
| [权限](advanced/scope.md)（scope） | 谁能用这个模块、谁能触发事件、能执行哪些动作？ | 三道闸——模块绑定、身份准入、出站限制，全部由用户配置说了算 |
| [归属](advanced/ownership.md)（ownership） | 模块卸载后，它开的连接、定时器、订阅去哪了？ | 谁注册谁归属，卸载即回收，不留悬挂资源 |
| [懒加载与休眠](advanced/lazy-loading.md)（lazy-loading） | 模块什么时候才真正加载、闲置后去哪？ | `activate_on` 用到才醒，`dormant_after` 闲置归眠 |
| [交互](advanced/interaction.md)（interaction） | 怎么等用户下一条回复、多轮收集怎么写？ | `wait_reply` 等一条、`.got()` 链收多轮，租约保证不打架 |
| [影子灰度](advanced/shadow.md)（shadow） | 新版模块怎么在不影响线上的情况下试运行？ | 影子收副本、出站只记账，`promote` 由人确认才转正 |
| [存储](advanced/storage-backends.md)（storage-backends） | 数据存哪、后端怎么换？ | 同一套存储 API，sqlite / mysql / postgres 配置切换 |

### 四、生态与官方客户端

官方客户端 + 按需安装、即装即用的生态模块（都不是框架内置功能）。

| 文档 | 说明 |
|------|------|
| [生态总览](ecosystem/README.md) | 如何安装生态模块、为什么这些不是内置功能 |
| [ErisPulse-App](ecosystem/app.md) | 官方全平台客户端（Android / Windows / Linux / macOS）：原生界面管理多个实例，**手机直接运行**，桌面托盘常驻 |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web 管理面板 + 视窗注册 API（模块可向侧边栏注册自定义页面） |
| [ErisPulse-Cron](ecosystem/cron.md) | 定时任务调度模块：一次性 / 间隔 / Cron 表达式，回调传参，SQLite 持久化，其他模块可托管定时回调 |
| [ErisPulse-Takumi](ecosystem/takumi.md) | 图片渲染（HTML / 节点树 / SVG / 动画，内置中英文字体） |

### 五、我要为 ErisPulse 贡献

让框架更好

| 文档 | 说明 |
|------|------|
| [为 ErisPulse 贡献](contributing/README.md) | 贡献方式总览：文档 / i18n / Bug / 模块 / 适配器 |
| [首次贡献](contributing/first-contribution.md) | 从 fork 到提交 PR |

---

## 高级特性版本速查表

做版本兼容判断、或接手旧项目想知道"这个能力是哪个版本引入的"时，按此表对号入座（以仓库根 [CHANGELOG.md](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md) 各版本条目为准）。

| 版本 | 引入的能力 |
|------|-----------|
| **2.7** | 生产化基座：OneBot12 标准化基类（`ApiDSL` / `BaseConverter`）、配置热更新系统化、优雅关闭与 SIGTERM/SIGHUP 信号处理、环境变量配置覆盖、生命周期回调钩子、Web 栈懒加载；2.7.1 补配置写入可靠性与 GC 分代治理 |
| **2.8** | 权限与通信骨架：作用域三维体系（scope）、交互会话基础设施（租约 / 检查点 / 消息事务 / 会话收件箱 transcript）、模块间 RPC 协议化（`module.call` / `meta.services` 服务契约 / 定向事件 emit(to=)）、多后端异步存储（sqlite / mysql / postgres，连接失败不阻塞框架）、归属权清理、配置注释保留；2.8.x 后续版本为 CLI 脚手架、子命令等打磨 |
| **2.9** | 「模块开发体验」主线（EPRFC-2026-001）：声明式命令参数（`args=` / `options=`）与命令治理（`cooldown=` / `rate_limit=`）、统一依赖注入（`Depends`）、中间件事件否决权、内置 ORM（自动迁移 + 关系映射）、影子模块灰度转正、分发决策链追踪与排查诊断、正式支持 Python 3.14 |
| **2.10** | 连接一等资源（`connections` 注册表：广播 / 业务分组 / 跨模块传递复用 / 卸载自动回收）、根导入契约（常用 API 全部可 `from ErisPulse import`）、归属权体系补全、收件箱保留策略运行时覆盖；2.10.2 适配器本地插件目录（`plugins/`）+ `epsdk create pack` + tomlclass 无损配置写入 |
| **2.11**（dev） | 「改代码 → 看效果」开发闭环：热重载默认全量语义（语法预检 + 代码身份核对 + 依赖者级联重导）、懒加载休眠（`dormant_after`）、适配器代码级热重载（`sdk.adapter.reload`）、`.got()` 命令流语法糖、`epsdk stop` / `restart` 运行时控制 |

## 开发方式

ErisPulse 支持两种开发方式：

- **模块开发（推荐）**：创建独立的模块包，通过包管理器安装，便于分发和管理。
- **嵌入式开发**：直接在项目中编写处理器，适合快速原型。详见 [快速开始](quick-start.md)。

## 其他

- [文档风格指南](styleguide/docstring.md) — 贡献文档时的写作规范
- [为 ErisPulse 贡献](contributing/README.md) — 参与项目共建的入口
- [AI 辅助开发](ai-support/README.md) — 获取供 AI 编程助手使用的项目提示词

## 获取帮助

- GitHub 仓库：[https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 问题反馈：提交 Issue
- 技术讨论：查看 Discussions

## 相关链接

- [OneBot12 标准](https://12.onebot.dev/)
- [云湖官方文档](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

## 快速开始

> 来源: `docs/zh-CN/quick-start.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/quick-start.md）

# 快速开始

> **这是你的第一步。** 5 分钟从零跑起一个 ErisPulse 机器人——先看效果，再展开每一步。

## 60 秒效果：先让机器人回你一句话

**1. 安装**（Python >= 3.10）：

```bash
pip install ErisPulse
```

**2. 初始化项目**。向导会让你设置项目名、选择要接入的平台适配器并完成配置，然后生成 `main.py` 和 `config/config.toml`：

```bash
epsdk init
```

**3. 打开 `main.py`，替换为这 9 行代码**：

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("ping", help="测试机器人是否在线")
async def ping_handler(event):
    await event.reply("Pong！机器人运行正常。")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

**4. 运行**：

```bash
epsdk run main.py
```

终端会输出框架启动日志和适配器的连接信息。这时在你接入的平台里给机器人发 `/ping`，它会回复：

> Pong！机器人运行正常。

看到这条回复，说明框架、适配器、事件处理这条链路已经打通。没跑通？直接翻到文末[遇到问题](#遇到问题)；跑通了，往下看每一步还有哪些选择。

## 安装 ErisPulse：三种方式

上面用的是最直接的 pip。按你的环境选择：

### 使用 pip 安装

确保你的 Python 版本 >= 3.10，然后使用 pip 安装：

```bash
pip install ErisPulse
```

如果你已安装 [uv](https://github.com/astral-sh/uv)，也可以使用 `uv pip install ErisPulse`，安装速度更快。

只想把 `epsdk` 命令行工具装到全局、不污染项目环境时，推荐 `uv tool install`：

```bash
uv tool install ErisPulse
```

安装后 `epsdk` 全局可用：在项目目录内运行时会自动感知项目 `.venv`（`epsdk install` 装进项目环境、`epsdk run` 用项目环境运行），框架本体由工具环境提供。详见[安装参考](user-guide/installation.md)。

### 一键安装脚本（新环境推荐）

安装脚本会自动检测您的环境（Docker、Python、uv），并引导您选择最适合的安装方式，支持多语言（中文/English/日本語/Русский/繁體中文）。

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
- **全局 CLI 安装（uv tool，推荐）**：将 `epsdk` 安装为全局命令，无需虚拟环境，uv 自动管理 Python（系统版本过低亦可）；项目目录内运行时自动感知项目 `.venv`
- **传统安装**：自动创建虚拟环境、选择 ErisPulse 版本、可选安装 Dashboard 管理面板模块

### 使用 Docker

Docker 镜像已内置 ErisPulse 框架和 Dashboard 管理面板，支持 `linux/amd64` 和 `linux/arm64` 架构。

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

### 想做群机器人（处理消息、群管、通知）

- [事件处理入门](getting-started/event-handling.md) — 消息、通知、请求事件的写法
- [常见任务示例](getting-started/common-tasks.md) — 存储、定时任务、权限控制

### 想写自己的模块 / 适配器

- [基础概念](getting-started/basic-concepts.md) — 先理解适配器 / 模块 / 事件 的设计
- [模块开发入门](developer-guide/modules/getting-started.md)
- [适配器开发入门](developer-guide/adapters/getting-started.md)
- [架构概览](architecture.md) — 可视化架构图

### 想把机器人长期跑起来

- [部署指南](user-guide/deployment.md)
- [配置文件说明](user-guide/configuration.md)

### 遇到问题

- [创建第一个机器人](getting-started/first-bot.md) — 第一个机器人的逐步详解
- [启动流程与手动控制](advanced/startup.md) — 模块 / 适配器加载失败的诊断
- [CLI 命令参考](user-guide/cli-reference.md) — `epsdk` 全部子命令

## 第一个机器人

> 来源: `docs/zh-CN/getting-started/first-bot.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/getting-started/first-bot.md）

# 创建第一个机器人

> [!TIP]
> **什么时候需要读这篇**：机器人已经能跑，想写出第一个 `/hello` 命令处理器、搞懂 `sdk.run` 与命令装饰器各自在做什么。如果还没装好 ErisPulse、初始化项目，先完成 [5 分钟快速开始](../quick-start.md) 的「安装」「初始化项目」「运行项目」三步；不需要则跳过。

跑通快速开始只是第一步——这篇带你写出第一个命令处理器，并解释每一行代码在框架里发生了什么。

## 第一步：编写第一个命令

打开 `main.py`，编写一个简单的命令处理器：

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="发送问候消息")
async def hello_handler(event):
    """处理 hello 命令"""
    user_name = event.get_user_nickname() or "朋友"
    await event.reply(f"你好，{user_name}！我是 ErisPulse 机器人。")

@command("ping", help="测试机器人是否在线")
async def ping_handler(event):
    """处理 ping 命令"""
    await event.reply("Pong！机器人运行正常。")

async def main():
    """主入口函数"""
    print("正在启动 ErisPulse...")
    
    # keep_running=True（默认）：框架阻塞维持运行，直到收到关闭信号（如 Ctrl+C）
    await sdk.run(keep_running=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### `keep_running` 参数

`sdk.run(keep_running)` 控制框架是否阻塞维持运行：

- **`keep_running=True`（默认）**：`run()` 会一直阻塞，直到收到关闭信号（如 Ctrl+C），适合纯 bot 应用。
- **`keep_running=False`**：`run()` 初始化完成后立即返回，**框架并不会卸载**——已启动的适配器/模块仍作为后台任务继续处理消息事件，你可以接着执行自己的逻辑，直到事件循环结束框架才随之关闭。例如：

```python
async def main():
    await sdk.run(keep_running=False)   # 初始化后立即返回
    # 框架已在后台运行，这里可以继续做别的事
    while True:
        await asyncio.sleep(3600)
        print("每小时检查一次")
```

> 除了 `run()` 的两种模式，还有 `init()`/`uninit()` 手动控制生命周期、单独启停适配器/路由等更精细的方式，见 [启动流程与手动控制](../advanced/startup.md)。

## 第二步：运行机器人

```bash
# 普通运行
epsdk run main.py

# 开发模式（支持热重载）
epsdk run main.py --reload
```

## 第三步：测试机器人

在你的聊天平台中发送命令：

```
/hello
```

你应该会收到机器人的回复。

## 代码说明

### 命令装饰器

```python
@command("hello", help="发送问候消息")
```

- `hello`：命令名称，用户通过 `/hello` 调用
- `help`：命令帮助说明，在 `/help` 命令中显示

### 事件参数

```python
async def hello_handler(event):
```

`event` 参数是一个 Event 对象，包含：
- 消息内容：`event.get_text()`
- 发送者信息：`event.get_user_id()`、`event.get_user_nickname()`
- 平台信息：`event.get_platform()`
- 群组信息：`event.get_group_id()`
- 原始数据：`event.get_raw()`

> 完整的 Event 对象方法请参考 [Event 包装类详解](../developer-guide/modules/event-wrapper.md)。

### 发送回复

```python
await event.reply("回复内容")
```

`event.reply()` 是一个便捷方法，用于向发送者发送消息。

## 扩展：添加更多功能

ErisPulse 提供了丰富的事件处理和数据处理能力：

- **消息监听**：使用 `@message.on_message()` 监听各类消息 → [事件处理入门](event-handling.md)
- **通知监听**：使用 `@notice.on_friend_add()` 等监听系统通知 → [事件处理入门](event-handling.md)
- **数据存储**：使用 `sdk.storage.get/set` 持久化数据 → [常见任务示例](common-tasks.md)

## 常见问题

### 命令没有响应？

1. 检查适配器是否正确配置，确认 `config/config.toml` 中适配器的 `status` 为 `true`
2. 查看终端日志输出，确认是否有错误信息（特别是 `ERROR` 级别日志）
3. 确认命令前缀是否正确（默认是 `/`），可在配置文件中查看 `[ErisPulse.event.command]` 部分
4. 确认命令名称拼写正确，注意大小写敏感性设置

### 如何修改命令前缀？

在 `config.toml` 中添加：

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### 如何支持多平台？

ErisPulse 使用 OneBot12 标准统一了不同平台的事件格式，`@command` 和 `@message` 注册的处理器会自动接收所有平台的事件。通过 `event.get_platform()` 可以区分来源平台：

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("你好！来自云湖")
    elif platform == "telegram":
        await event.reply("Hello! From Telegram")
    else:
        await event.reply("你好！")
```

> 更多多平台适配技巧请参考 [常见任务示例](common-tasks.md#多平台适配)。

## 基础概念

> 来源: `docs/zh-CN/getting-started/basic-concepts.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/getting-started/basic-concepts.md）

# 基础概念

> [!NOTE]
> **L1 核心必读**——文档首页「L1 核心五篇」中的第 2 篇（模块开发入门 → **基础概念** → Event 包装类 → 配置文件说明 → 异常捕获）。

一条消息从用户发出到机器人回复，中间经过了哪些组件？适配器和模块各自负责什么？读完这篇，写处理器时遇到的设计问题你都能自己回答，而不是只能照抄示例。

## 事件驱动架构

ErisPulse 采用事件驱动架构，所有的交互都通过事件来传递和处理。

### 事件流程

```
用户发送消息
      │
      ▼
平台接收
      │
      ▼
适配器接收平台原生事件
      │
      ▼
转换为 OneBot12 标准事件
      │
      ▼
提交到事件系统
      │
      ▼
分发给已注册的处理器
      │
      ▼
模块处理事件
      │
      ▼
通过适配器发送响应
      │
      ▼
平台显示给用户
```

### OneBot12 标准

ErisPulse 使用 OneBot12 作为核心事件标准。OneBot12 是一个通用的聊天机器人应用接口标准，定义了统一的事件格式。

所有适配器都将平台特定的事件转换为 OneBot12 格式，确保代码的一致性。

## 核心组件

### 1. SDK 对象

SDK 是所有功能的统一入口点，提供对核心组件的访问。

```python
from ErisPulse import sdk

# 访问核心模块
sdk.storage    # 存储系统
sdk.config     # 配置系统
sdk.logger     # 日志系统
sdk.adapter    # 适配器系统
sdk.module     # 模块系统
sdk.router     # 路由系统
sdk.client     # HTTP 客户端
sdk.lifecycle  # 生命周期系统
```

> [!WARNING]
> **统一从根导入**：`from ErisPulse.Core import adapter` / `import ErisPulse.Core.adapter`
> 这类写法绑定到的是**管理器实例**（`AdapterManager` 单例）而非子模块——`ErisPulse.Core`
> 包的 re-export 会遮蔽同名子模块。写测试、patch 或需要模块对象本身时，请一律使用
> `from ErisPulse import sdk` 根导入（`sdk.adapter` 即管理器实例）。

### 2. Event 对象

Event 对象封装了事件数据，提供了便捷的访问方法。

```python
@command("info")
async def info_handler(event):
    # 获取事件信息
    event_id = event.get_id()
    user_id = event.get_user_id()
    platform = event.get_platform()
    text = event.get_text()
    
    # 发送回复
    await event.reply(f"用户: {user_id}, 平台: {platform}")
```

### 3. 适配器

适配器是 ErisPulse 与外部平台之间的桥梁。

**职责：**
- 接收平台原生事件
- 转换为 OneBot12 标准格式
- 将标准格式事件发送到平台

**示例适配器：**
- Yunhu 适配器：与云湖平台通信
- Telegram 适配器：与 Telegram Bot API 通信
- OneBot11 适配器：与 OneBot11 兼容的应用通信
- Email 适配器：处理邮件收发

### 4. 模块

模块是功能扩展的基本单位，可以：

- 注册事件处理器
- 实现业务逻辑
- 调用适配器发送消息
- 使用核心模块提供的服务

#### 模块发现机制

ErisPulse 通过 Python 的 `importlib.metadata.entry_points` 发现已安装的模块。模块在 `pyproject.toml` 中声明入口点：

```toml
[project.entry-points."erispulse.module"]
MyModule = "my_package:Main"
```

SDK 初始化时会扫描所有 `erispulse.module` 组的入口点，将模块类注册到 `ModuleManager`，然后按依赖关系拓扑排序后依次初始化。

#### 最小可用模块

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")

    async def on_load(self, event):
        self.logger.info("模块已加载")

    async def on_unload(self, event):
        self.logger.info("模块已卸载")
```

#### 模块生命周期

- **注册**：SDK 发现模块类并注册到管理器
- **加载**：创建模块实例，调用 `on_load(event)`（`event = {"module_name": "MyModule"}`）
- **卸载**：调用 `on_unload(event)`，清理资源

#### 加载策略

通过 `get_load_strategy()` 声明模块的加载行为：

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # 是否懒加载（默认 True）
            priority=0        # 加载优先级，数值越大越先初始化
        )
```

- **`lazy_load=True`（默认）**：模块在首次被 `sdk.MyModule` 访问时才初始化，减少启动时间
- **`lazy_load=False`**：SDK 启动时立即初始化，适合需要监听生命周期事件或执行定时任务的模块
- **`priority`**：同优先级的模块按注册顺序加载；数值越大越先初始化

> 详细的懒加载机制说明请参考 [懒加载系统](../advanced/lazy-loading.md)。

## 事件类型

ErisPulse 支持 5 类事件：

| 事件类型 | 装饰器 | 说明 |
|---------|--------|------|
| 消息事件 | `@message.on_message()` | 用户发送的任何消息（私聊、群聊） |
| 命令事件 | `@command("name")` | 以命令前缀开头的消息（如 `/hello`） |
| 通知事件 | `@notice.on_friend_add()` 等 | 系统通知（好友添加、群成员变化等） |
| 请求事件 | `@request.on_friend_request()` 等 | 用户请求（好友请求、群邀请） |
| 元事件 | `@meta.on_connect()` 等 | 系统级事件（连接、断开、心跳） |

> 各事件类型的详细用法和代码示例请参考 [事件处理入门](event-handling.md)。

## 核心模块说明

### Storage（存储）

基于 SQLite 的键值存储系统，用于持久化数据。

```python
# 设置值
sdk.storage.set("key", "value")

# 获取值
value = sdk.storage.get("key", "default_value")

# 批量操作
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2"
})

# 事务
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Config（配置）

TOML 格式的配置文件管理。

```python
# 获取配置
config = sdk.config.getConfig("MyModule", {})

# 设置配置
sdk.config.setConfig("MyModule", {"key": "value"})

# 读取嵌套配置
value = sdk.config.getConfig("MyModule.subkey", "default")
```

### Logger（日志）

模块化日志系统。

```python
# 记录日志
sdk.logger.info("这是一条信息")
sdk.logger.warning("这是一条警告")
sdk.logger.error("这是一条错误")

# 获取子日志记录器
child_logger = sdk.logger.get_child("submodule")
child_logger.info("子模块日志")
```

**属性访问语法糖**

除了使用 `get_child()` 方法外，你还可以通过**属性访问**的方式创建子logger，这是一种更简洁的**语法糖**写法：

```python
# 通过属性访问创建子logger
sdk.logger.mymodule.info("模块消息")

# 支持嵌套访问
sdk.logger.mymodule.database.info("数据库消息")
```

### Router（路由）

HTTP 和 WebSocket 路由管理，基于 FastAPI + Uvicorn。支持装饰器路由、中间件、分组、限流、CORS。

```python
from ErisPulse.Core import HttpRequest

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}
```

> 完整的路由 API（WebSocket、中间件、速率限制、CORS 等）请参考 [路由管理器](../advanced/router.md)。

### Client（网络客户端）

统一的网络客户端，聚合了 HTTP 请求、WebSocket 连接、连接池管理、自动重试、超时控制、请求统计和生命周期事件集成。

```python
from ErisPulse.Core import client

# HTTP 请求
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# 带重试和超时
resp = await client.get(url, timeout=30, max_retries=3)

# WebSocket 连接
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

> 完整的网络客户端 API 请参考 [网络客户端](../advanced/http-client.md)。

## SendDSL 消息发送

适配器提供链式调用的消息发送接口。

### 基础发送

```python
# 获取适配器实例
yunhu = sdk.adapter.get("yunhu")

# 发送消息
await yunhu.Send.To("user", "U1001").Text("Hello")

# 指定发送账号
await yunhu.Send.Using("bot1").To("group", "G1001").Text("群消息")
```

### 链式修饰

```python
# @用户
await yunhu.Send.To("group", "G1001").At("U2001").Text("@消息")

# 回复消息
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("回复")

# @全体
await yunhu.Send.To("group", "G1001").AtAll().Text("公告")
```

### Event 回复方法

Event 对象提供了便捷的回复方法：

```python
@command("test")
async def test_handler(event):
    # 简单文本回复
    await event.reply("回复内容")
    
    # 发送图片
    await event.reply("http://example.com/image.jpg", method="Image")
    
    # 发送语音
    await event.reply("http://example.com/voice.mp3", method="Voice")
```

## 懒加载系统

ErisPulse 默认启用模块懒加载，模块只在首次被访问（如 `sdk.MyModule`）时才初始化，显著提高启动速度。

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # 启用懒加载（默认）
            priority=0        # 加载优先级，数值越大越先初始化
        )
```

**需要禁用懒加载的场景（`lazy_load=False`）：**
- 监听生命周期事件的模块（如 `core.init.complete`）
- 启动定时任务或后台服务的模块
- 需要在其他模块加载前完成初始化的模块

> 详细的懒加载机制和注意事项请参考 [懒加载系统](../advanced/lazy-loading.md)。

## 事件处理

> 来源: `docs/zh-CN/getting-started/event-handling.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/getting-started/event-handling.md）

# 事件处理入门

> [!TIP]
> **什么时候需要读这篇**：想让机器人响应消息、命令、通知、请求，或要实现等待回复 / 多轮对话、排查"命令为什么没触发"时读。只想了解框架设计，看 [基础概念](basic-concepts.md) 即可；不需要则跳过。

事件处理器就是机器人"听懂"用户并作出反应的地方——这篇按五类事件给出可直接复制的写法，并覆盖参数解析、权限、节流、多轮交互这些实战场景。

## 事件类型概览

ErisPulse 支持以下事件类型：

| 事件类型 | 说明 | 适用场景 |
|---------|------|---------|
| 消息事件 | 用户发送的任何消息 | 聊天机器人、内容过滤 |
| 命令事件 | 以命令前缀开头的消息 | 命令处理、功能入口 |
| 通知事件 | 系统通知（好友添加、群成员变化等） | 欢迎消息、状态通知 |
| 请求事件 | 用户请求（好友请求、群邀请） | 自动处理请求 |
| 元事件 | 系统级事件（连接、心跳） | 连接监控、状态检查 |

## 消息事件处理

> **提示**: 建议在事件处理器中使用 `Event` 类型注解，以获得 IDE 自动补全和类型检查支持。

```python
from ErisPulse.Core.Event import Event  # 导入事件类型用于注解
```

### 监听所有消息

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"收到 {user_id} 的消息: {text}")
```

### 监听私聊消息

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"你好，{user_id}！这是私聊消息。")
```

### 监听群聊消息

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"群 {group_id} 中 {user_id} 发送了消息")
```

### 监听@消息

```python
@message.on_at_message()
async def at_handler(event: Event):
    # 获取被@的用户列表
    mentions = event.get_mentions()
    await event.reply(f"你@了这些用户: {mentions}")
```

### 通配符与正则监听

四个消息装饰器（`on_message` / `on_private_message` / `on_group_message` /
`on_at_message`）均支持 `pattern`（glob 通配符）与 `regex`（正则），不匹配的消息
**不会触发**处理器：

```python
# glob 通配符：* 任意串、? 单字符、[seq] 字符集
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("签到成功")

# 正则：匹配金额
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"收到金额：{event.get_text()}")

# pattern 与 regex 同时给出 → 两者都须匹配
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` 同样支持这两个参数（见[等待回复](../developer-guide/modules/event-wrapper.md#等待回复功能)）。

## 命令事件处理

### 基本命令

```python
from ErisPulse.Core.Event import command

@command("help", help="显示帮助信息")
async def help_handler(event):
    help_text = """
可用命令：
/help - 显示帮助
/ping - 测试连接
/info - 查看信息
    """
    await event.reply(help_text)
```

### 命令别名

```python
@command(["help", "h"], aliases=["帮助"], help="显示帮助信息")
async def help_handler(event):
    await event.reply("帮助信息...")
```

用户可以使用以下任何方式调用：
- `/help`
- `/h`
- `/帮助`

### 命令参数

```python
@command("echo", help="回显消息")
async def echo_handler(event):
    # 获取命令参数
    args = event.get_command_args()
    
    if not args:
        await event.reply("请输入要回显的消息")
    else:
        await event.reply(f"你说了: {' '.join(args)}")
```

参数保留用户输入的原始大小写（即使配置为大小写不敏感，
命令名匹配归一也不会影响参数内容）。

### 声明式参数与选项（args= / options=）

手动解析参数需要自己处理类型转换与错误提示。声明 `args=` / `options=` 后，
框架在权限检查通过后自动解析命令参数并**按名注入处理器**；用户输入错误时
自动回复本地化提示与用法（不会抛异常崩溃），`/help <命令>` 也会自动展示用法：

```python
@command(
    "roll",
    args="<count:int> [sides:int=6]",
    options={"verbose": "-v/--verbose", "label": "--label"},
    help="掷骰子",
)
async def roll_handler(event, count: int, sides: int = 6, verbose: bool = False, label: str = ""):
    total = sum(random.randint(1, sides) for _ in range(count))
    await event.reply(f"掷了 {count} 次 {sides} 面骰，总点数：{total}")
```

`args=` 位置参数语法：`<count:int>` 必填、`[sides:int=6]` 可选（含默认值）。支持类型：

| 类型 | 示例输入 | 说明 |
|------|---------|------|
| `str` | `hello` | 文本（缺省类型） |
| `int` / `float` | `3` / `0.5` | 数值 |
| `bool` | `是` / `yes` / `はい` / `да` / `true` / `no` / `取消` | 布尔值，复用交互确认（`Event.confirm()`）的确认词表 |
| `literal` | `<mode:literal=fast|slow>` | 枚举，仅接受列出的值；可选形式默认取首个 |
| `duration` | `90s`、`1h30m`、`1d` | 时长，按秒折算为 float |
| `rest` | `<text:rest>` | 剩余全部文本（必须位于最后） |

`options=` 选项为字典式声明：键为处理器参数名，值为旗标形式（多个别名以 `/` 分隔）。
注解为 `bool` 的参数是布尔旗标（出现即 `True`）；其余（缺省按 `str`）是带值选项，
支持 `--label hello` 与 `--label=hello` 两种取值，类型跟随处理器注解。
选项先被识别剔除，剩余 token 再按 `args=` 解析（`rest` 覆盖剔除选项后的剩余文本）。

**行为要点**：

- 权限检查先于参数解析——无权限用户不会触发解析
- 解析失败（类型不符 / 缺少参数 / 参数过多 / 未知选项）自动回复本地化错误 + 用法，命令仍被认领
- 声明的参数名必须存在于处理器签名中，否则注册期抛 `ValueError`
- 不声明 `args=` / `options=` 的命令行为完全不变（向后兼容）

### 命令治理（cooldown= / rate_limit= / usage_limit= / deprecated=）

手写冷却计时、限流窗口、使用配额、废弃提示可用声明替代，四者可任意组合。

**冷却**——时长语法与 `args=` 的 `duration` 类型一致（如 `"30s"`、`"1h30m"`、`"1d"`）：

```python
@command("daily", cooldown="1d", cooldown_key="user", cooldown_reply="今天已签到")
async def daily_handler(event):
    await event.reply("签到成功！")
```

**限流**——滑动窗口声明 `"次数/窗口"`（如 `"5/minute"`、`"10/s"`、`"3/2m"`）：

```python
@command("search", rate_limit="5/minute", rate_limit_key="user")
async def search_handler(event):
    await event.reply("搜索结果")
```

**配额**——周期内总次数上限（如 `"100/day"`、`"10/hour"`、`"500/30d"`），超限拒绝执行：

```python
@command("translate", usage_limit="100/day", usage_limit_key="user",
         usage_limit_reply="今日翻译次数已用完")
async def translate_handler(event):
    ...
```

与冷却/限流不同，配额计数**经存储持久化**（KV 键 `erispulse.usage.<key>`，重启不丢）：
存储不可达时自动退化为纯内存计数并告警（此时配额重启清零）。计数随配额周期
切换自动清零，模块卸载时清理。

**废弃**——调用时自动回复废弃文案，`deprecated_reject=True` 拒绝执行：

```python
@command("oldcmd", deprecated="请用 /newcmd", deprecated_reject=True)
async def old_handler(event): ...
```

键粒度（`cooldown_key=` / `rate_limit_key=`）：`"user"`（默认，同一用户共享）、
`"session"`（同一会话共享，如同一群）、`"global"`（所有用户所有会话共享）。

**行为要点**：

- 冷却 / 限流 / 配额命中默认**静默丢弃**（对称于作用域静默）；声明 `cooldown_reply=` / `rate_limit_reply=` / `usage_limit_reply=` 后命中即回复该文案
- 命令命中即认领——治理命中的命令不会漏给低优先级消息处理器
- 治理判定位于全部权限检查与参数解析通过、实际执行前：无权限用户不触发，参数错误不消耗
- 同时声明冷却与限流时冷却先判（冷却命中不占限流窗口）；配额在冷却/限流判定之后
- `deprecated=` 默认回复文案后**继续执行**；`deprecated_reject=True` 拒绝执行（`command.executed` 钩子记 `success=False, error="deprecated"`）
- `/help` 列表与单命令帮助自动显示废弃标记与文案
- 冷却与限流状态为进程内内存，模块卸载时自动清理；跨进程共享 / 重启持久化不在范围内（**usage 配额计数除外**——经存储持久化，见上节）
- 声明在注册期校验（fail-fast）：语法非法、键粒度非白名单值、reply 未搭配主声明均抛 `ValueError`

### 处理器节流（throttle=）与防抖（debounce=）

消息处理器防刷屏声明——同键事件在间隔内至多处理一条，其余静默丢弃：

```python
from ErisPulse import sdk

@sdk.message.on_message(throttle="2s", throttle_key="user")
async def handler(event): ...
```

防抖与节流互补：**窗口内只执行最后一条**，前序待执行任务自动取消（适合
"停止输入后再处理"的搜索联想类场景）：

```python
@sdk.message.on_message(debounce="2s", debounce_key="user")
async def search(event): ...
```

`on_message` / `on_private_message` / `on_group_message` / `on_at_message`
均支持；`throttle_key=` / `debounce_key=` 与命令治理同一套键粒度
（user / session / global），时长语法与 `duration` 一致。节流与 `pattern=` /
`regex=` 等既有条件叠加生效（全部满足才触发）；间隔内丢弃仅记 TRACE 日志；
声明在注册期校验；`throttle=` 与 `debounce=` 语义互斥（同时声明抛 `ValueError`）。

> **防抖不半途掐断业务**：只有尚未越过等待窗口的待执行任务会被取消；已经
> 越窗、正在执行中的处理器不会被新事件取消（避免停在任意 await 点产生
> 部分副作用）。

### 依赖注入（Depends）

公共依赖（数据库会话、配置读取等）可抽为依赖函数，处理器以
`Depends(依赖函数)` 作为参数默认值声明，框架在调用前自动以上下文对象
调用依赖函数并按名注入：

```python
from ErisPulse.Core import Depends

async def get_session(event):
    return await sdk.module.call("DB", "get_session")

@command("admin")
async def admin_handler(event, db=Depends(get_session)):
    ...
```

默认开启**请求级缓存**：同一次事件分发内，相同依赖函数只解析一次、所有
注入点共享结果（如 `get_db` 在一次事件中只建一次数据库会话）；跨请求自动
不复用。可用 `Depends(get_db, use_cache=False)` 关闭单条依赖的缓存。

覆盖全部框架注入点——命令处理器、事件处理器（`message.on_message()` 等）、
生命周期钩子（`sdk.lifecycle.on`）、SSE 路由处理器。依赖函数的第一个参数
是注入点上下文对象（事件场景为 `Event`，生命周期为事件 `data`，
路由为 `HttpRequest` / `SseEmitter`）；同步与异步依赖函数均可声明。

**声明其它模块的服务**（语法糖）：

```python
@command("query")
async def query_handler(event, session=Depends.module("DB", "get_session")):
    ...
```

`Depends.module(模块名, 方法名, *固定参数)` 等价于在依赖函数内调用
`sdk.module.call(...)`。模块实例化（`__init__`）不在覆盖范围——实例化时无
上下文对象；FastAPI 承载的 HTTP 路由请用 FastAPI 原生 `fastapi.Depends`。

**行为要点**：

- 声明在注册期校验（fail-fast）：依赖不可调用、或与 `args=` / `options=` 参数重名时抛 `ValueError`
- 依赖函数抛出的异常与处理器自身异常同口径处理（命令自动回复错误）
- 不声明 `Depends` 的处理器零开销（分发期无任何反射）
- FastAPI 承载的 HTTP 路由请使用 FastAPI 原生 `fastapi.Depends`

### 命令组

```python
@command("admin.reload", group="admin", help="重新加载模块")
async def reload_handler(event):
    await event.reply("模块已重新加载")

@command("admin.stop", group="admin", help="停止机器人")
async def stop_handler(event):
    await event.reply("机器人已停止")
```

`group` 参数仅用于帮助列表归类；上面示例中的 `admin.reload` 是一个**整体命令名**
（点号只是命名风格，用户需输入 `/admin.reload`）。

### 子命令

命令名支持**空格分隔**的多 token 形式，实现 `/admin add`、`/admin user ban` 这样的子命令：

```python
@command("admin", help="管理命令")
async def admin_handler(event):
    await event.reply("用法：/admin add | /admin remove")

@command("admin add", help="添加管理员")
async def admin_add_handler(event):
    target = event.get_command_args()[0]
    await event.reply(f"已添加 {target}")

@command("admin remove", aliases=["a remove"], help="移除管理员")
async def admin_remove_handler(event):
    await event.reply("已移除")
```

匹配规则（**最长前缀匹配**）：

- `/admin add x` 优先命中 `admin add`，`event.get_command_args()` 返回 `["x"]`（子命令名之后的参数）
- 仅注册了 `admin` 时，`/admin add x` 命中 `admin`，`get_command_args()` 返回 `["add", "x"]`（历史行为不变）
- 别名支持多 token 形式（如 `a remove`），也可用单 token 别名（如 `a`）指向子命令
- 父子命令同时注册时，未注册的子命令输入（如 `/admin list x`）回落到父命令

**权限继承**：子命令未声明 `permission` 时，自动继承父链上最近声明了权限的祖先命令——
保护 `/admin` 即自动保护其下全部子命令；子命令自身声明的权限优先：

```python
def is_admin(event):
    return event.get_user_id() in {"user123"}

@command("admin", permission=is_admin, help="管理命令")
async def admin_handler(event):
    ...

# 无需重复声明 permission，自动继承 is_admin
@command("admin add", help="添加管理员")
async def admin_add_handler(event):
    ...
```

注意：`master=True` 与 `hidden` **不会**继承，需要时请在子命令上单独声明；
用户 ACL（黑白名单）按命令全名匹配，glob 规则如 `"admin*"` 可覆盖整组子命令。

`/help` 的命令总览中，子命令会自动挂到可见的父命令下缩进展示
（`admin` → `admin add` 缩进一级，`admin user` → `admin user ban` 缩进两级）。

### 命令权限与访问控制

命令权限分三层，从上到下逐层判定（**上层拒绝则不再看下层**）：

```python
# ① 命令权限 ACL（用户侧配置）：按命令的用户黑白名单，拒绝时回复"权限不足"
# ② master=True —— 仅框架主人可执行（框架自动检查，拒绝时回复"权限不足"）
@command("restart", master=True, help="重启模块")
async def restart_handler(event):
    await event.reply("模块已重启")

# ③ permission=调用函数 —— 命令自身的控制逻辑（返回 True 才执行）
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="管理面板")
async def panel_handler(event):
    await event.reply("欢迎来到管理面板")
```

**命令用户 ACL**（`ErisPulse.event.command.acl`）：用户可为任意命令配置用户黑白名单，
命令名支持精确与 glob 模式（如 `"roll*"`），拒绝时回复"权限不足"：

```toml
# config.toml —— 仅允许 123456 执行 restart；666 一律拒绝
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

判定顺序：`deny` 命中 → 拒绝；`allow` 非空且未命中 → 拒绝；未配置 ACL 时遵循
`event.command.default_allow`（`false` = 严格模式，无 ACL 即拒；`true` 时交给开发者默认
`master=True` / `permission`）。运行时 API（命令名支持 glob）：

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # 允许名单
command.deny_user("restart", "onebot11", "666")       # 拒绝名单
command.remove_acl("restart")                          # 清除黑白名单
command.get_acl("restart")                             # 查询当前名单
```

> 命令处理器从事件包导入：`from ErisPulse.Core.Event import command`；
> 也可经 SDK 事件包访问：`sdk.Event.command`（两者为同一单例）。
> 在模块内通常已随命令装饰器导入（`from ErisPulse.Core.Event import command`）。

跨命令 / 跨用户的**事件级**访问控制（某人 / 某群 / 某 Bot 的消息收不收）
走作用域**身份维度**（`scope.identity`）；**模块级**可用性（哪些模块能用）
走作用域**模块维度**（`scope.platforms / bots / sessions`）。
详见[作用域（scope）](../advanced/scope.md)。

> 建议：命令内部需要联动业务逻辑的用 `master=True` / `permission`；纯按用户 / 群做
> 访问控制的用作用域身份维度；控制模块可用性的用作用域模块维度。

### 命令优先级

```python
# 优先级数值越大，执行越早
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("高优先级处理器")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("低优先级处理器")
```

### 并行事件处理

ErisPulse 事件系统采用**同优先级并行、不同优先级串行**的调度模型：

```
事件到达
    ↓
priority=10 组: [处理器C || 处理器D] 并行 → 合并结果
    ↓ (如未中断)
priority=0 组: [处理器A || 处理器B] 并行 → 合并结果
    ↓
...
```

- **同优先级并行**：优先级相同的多个处理器会同时执行，提高吞吐量
- **跨级串行**：不同优先级的组按顺序执行（数值越大越先执行），确保高优先级处理器先运行
- **Copy-On-Write**：处理器无修改时不创建副本，确保零开销
- **冲突处理**：同优先级多处理器修改同一字段时，使用最后修改值并记录警告日志
- **中断机制**：任意处理器调用 `event.done()`（默认）或 `event.done(claim=False)` 后，跳过后续低优先级组。认领与阻断的区别见下文[「链路控制：认领与阻断」](#链路控制认领与阻断)

```python
# 示例：同优先级处理器并行执行
@message.on_message(priority=0)
async def handler_a(event):
    # 处理任务A
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # 与 handler_a 并行执行
    event['result_b'] = process_b()

# 不同优先级串行执行
@message.on_message(priority=10)
async def handler_c(event):
    # 优先级最高，最先执行
    pass
```

> **并发上限**：所有匹配 handler 的 Task 会**立即创建**，但通过一个信号量限制**同时在途执行数**，默认上限 **64**（`ErisPulse.framework.handler_max_concurrency`，支持热更新）。超过上限的 Task 在信号量上排队，等前面的完成后再进。事件洪峰时这就是你的「泄压阀」。
>
> **慢日志**：单个处理器耗时超过 **1 秒**时，框架会在日志打 WARNING（`handler_slow`）。`wait_reply` 的等待时间会从耗时里剔除，不会因为「等人回复」误报慢。

## 中间件：分发前改写与否决

中间件在事件分发**之前**顺序执行，防火墙、限流、事件脱敏等场景的正统实现点：

```python
from ErisPulse.Core import adapter

@adapter.middleware
async def firewall(data):
    if _is_banned(data.get("user_id")):
        return False          # 否决：事件被丢弃，不进入任何处理器，无出站副作用
    data["checked"] = True    # 返回 dict：改写载荷（与历史行为一致）
    # 返回 None：放行，载荷不变（历史行为）
    return data
```

| 返回值 | 行为 |
|--------|------|
| `False` | **否决**：事件立即丢弃，不进入任何处理器 |
| `dict` | 改写事件载荷后继续分发 |
| `None` | 放行，载荷不变 |

否决时框架输出 TRACE 日志并触发 `adapter.event.blocked` 生命周期钩子（携带中间件名与完整事件），供审计「事件为什么没响应」。

## 命令分发决策链：为什么命令没触发

一条命令消息依次经过：**命令文本判定 → 命令名/别名命中（未命中附拼写建议）→ 命中即认领 → 作用域 → 用户 ACL → 主人 → 权限 → 冷却/限流 → 配额（usage）→ 废弃（deprecated，notice/rejected）→ 参数解析 → 执行**（中间件可在事件层否决，见上一节）。任何一步不满足即终止；治理命中（冷却/限流/配额）默认静默丢弃，权限类拒绝会回复用户，废弃按声明回复或拒绝。

测试中 `ErisPulse-Testing` 的 `dispatch()` 直接返回这条决策链（`DispatchTrace`，`trace.explain()` 输出逐行因果），生产环境可用 `ErisPulse.Core.Event.start_dispatch_trace()` 采集同样的记录。

此外 `ErisPulse.runtime` 提供两组排查诊断 API：`explain_module(模块名)` 回答"模块为什么没加载"（未注册 / 懒加载 / 配置禁用 / 依赖缺失 / SDK 版本不满足，逐项给原因），`explain_event(事件)` 回答"事件为什么没响应"（适配器未注册 / 身份拉黑 / 模块会话屏蔽 / 命令未命中）；配 `format_report()` 渲染人类可读结论。

## 作用域过滤：为什么我的模块没收到消息

事件到达后有两道**静默**过滤（都不回复、不报错）：

1. **身份维度**（`ErisPulse.scope.identity`）：事件进入分发入口时，按 用户 > 群 > Bot > 适配器 判定收不收。
   被拒绝的**整个事件**直接丢弃，任何处理器（含命令分发器）都不会触发。
2. **模块维度**（`ErisPulse.scope`）：事件到达某模块的处理器/命令时，按 会话 > Bot > 平台 判定
   该模块是否可用，**不通过就静默跳过**。

```toml
# 例1：某群所有消息不传播
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# 例2：把 MyModule 屏蔽在某个 Bot
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

此时该群的消息到达时，`MyModule` 的命令与事件处理器**都不会被调度**。这不是 bug，是过滤机制——排查「模块没反应」时优先检查作用域的身份与模块绑定。

- 过滤日志只在 **TRACE** 级可见（`core.scope.identity_denied` / `core.scope.denied`），默认 INFO 看不到任何痕迹
- 框架级处理器（如命令分发器 `scope_exempt=True`）不受**模块维度**影响，但受**身份维度**影响（整个事件已丢弃）
- 命令执行前还有第三道：命令用户 ACL（拒绝时回复"权限不足"，见上节）
- 第四道是**事件覆写**（见下节）

> [!NOTE]
> **作用域过滤与事件认领（claim）的关系**：两道静默过滤都发生在处理器
> **调度之前**——被过滤跳过的处理器没有机会执行，自然也不参与
> `event.done()` / `mark_processed()` 的认领状态。事件是否已被认领，
> 只由**实际执行**的处理器（命令命中认领、回复命中认领、显式调用）决定；
> 作用域拒绝本身既不认领也不阻断（静默跳过，消息继续走完剩余分发链）。

> 作用域配置、匹配语法、运行时 API 见 [作用域（scope）](../advanced/scope.md)。

## 事件覆写：不改模块代码，覆写任意事件类型的行为

> [!NOTE]
> 本特性需要 ErisPulse **2.8.0+**。

事件处理器在注册时声明的参数（`pattern` / `regex` / `master` / `hidden` 等）只是**开发者默认**。
统一覆写系统让用户按**事件类型**覆写任意模块的行为——OneBot12 标准类型
（meta / message / notice / request）与 ErisPulse 扩展类型（command）各自拥有专属的可覆写参数：

| 事件类型 | 可覆写参数 | 作用 |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | 文本触发条件 + 消息子类型白名单 |
| `notice` | `detail_types` / `pattern` / `regex` | 通知子类型白名单 + 文本条件 |
| `request` | `detail_types` / `pattern` / `regex` | 请求子类型白名单 + 文本条件 |
| `meta` | `detail_types` | 元事件子类型白名单（connect / heartbeat 等） |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | 命令实现参数（用户优先） |
| `acl`（command 专属） | `allow` / `deny` | 命令用户黑白名单（按命令名 glob） |

```toml
# message：覆写文本触发条件（与代码内条件 AND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice：只响应特定通知子类型
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command：覆写实现参数（用户优先——可收紧或放开开发者默认）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl：命令用户黑白名单（跨命令 glob）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACL 兜底（false = 严格模式：无 ACL 即拒）
acl_default_allow = true
```

运行时 API（`from ErisPulse.Core.Event import overrides` 或 `sdk.Event.overrides`，
**类型子命名空间**——每类型对称的 `set` / `get` / `delete` 三件套）：

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # message 文本条件
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # 命令参数
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # 命令用户黑名单

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # 恢复开发者默认
```

- 覆写条件与处理器代码内条件**同时生效**（AND 语义）；`command` 参数与开发者声明**深合并**（覆写优先）
- `detail_types`：事件缺 `detail_type` 时放行（不误杀未知事件）
- `pattern` / `regex`：无文本的事件（connect / heartbeat 等）不受约束，直接放行
- `command` 覆写键 `master` 同步映射存储键 `must_master`；禁用命令统一走 `acl` deny
- **键名映射说明**：`overrides.command.set("My", "restart", master=True)` 的参数名
  `master` 仅为配置别名，实际存储键与 `get()` 返回值中的键名统一为 **`must_master`**
  （`get()` 返回 `{"must_master": true}`）——运行时判断读取的是存储键，请勿按
  `master` 键名读取
- 配置改了立即生效（热更新），格式校验告警（未知参数 / 坏条目忽略）

## 链路控制：认领与阻断

> [!NOTE]
> `event.done()` / `event.mark_processed()` 的 `claim=` / `stop=` 参数本特性需要 ErisPulse **2.7.1+**。

ErisPulse 将「认领」与「阻断」两个正交语义解耦，通过 `event.done()` 统一控制，便于在命令处理周围叠加日志、审计、权限等观察层。

**两个概念的准确定义：**

- **认领（claim）**：标记事件已被本处理器处理（写入 `_processed`）。命令分发器看到已认领的事件会**跳过去重**——避免同一消息被多个命令处理器重复处理。典型场景：命令匹配成功后认领，阻止命令分发器再介入。
- **阻断（stop）**：阻止事件向**更低优先级**处理器传播（写入 `_propagation_stopped`）。低优先级处理器（如 `on_message`）将不再看到该事件。典型场景：高优先级处理器已完整处理事件，不希望低优先级再执行。

| `event.done(...)` | 认领 | 阻断 | 场景 |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | 命令 / 处理器处理完的标准做法 |
| `event.done(stop=False)` | ✔ | ✘ | 仅认领，让低优先级观察者（日志 / 统计）继续看到 |
| `event.done(claim=False)` | ✘ | ✔ | 仅阻断（如防火墙 / 限流），但不做命令去重 |

`event.done(claim=, stop=)` 是 `event.mark_processed(claim=, stop=)` 的别名，二者参数与行为完全等价。

```python
@command("help")
async def help_cmd(event):
    event.done()            # 认领 + 阻断（命令处理完的标准做法）

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # 仅认领：低优先级仍会执行（日志 / 统计）

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # 仅阻断：低优先级不执行，但不做去重
```

### 命令与回复的 block 配置

**命令命中即认领**：消息一旦匹配到已注册命令名（含子命令/别名），无论后续作用域或权限判定结果如何，都会被认领并默认阻断传播——被权限拒绝的命令不会再漏给低优先级消息处理器（消除"命令被拒后 on_message 又响应一次"的双重响应）。

可通过配置放行阻断，让低优先级观察者（日志 / 审计 / 权限）也能看到这些消息：

```toml
[ErisPulse.event.command]
block = false   # 命令消息继续流向低优先级处理器（认领不受影响，不会重复消费）

[ErisPulse.event.wait_reply]
block = false   # 被 wait_reply 消费的回复继续流向低优先级处理器
```

> 注意：`block` 只控制**阻断**（stop），不影响**认领**（claim）——命中的命令永远不会被消息处理器重复消费；未命中任何命令的消息照常流向消息处理器。

## 通知事件处理

### 好友添加

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "新朋友"
    await event.reply(f"欢迎添加我为好友，{nickname}！")
```

### 群成员增加

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"欢迎新成员 {user_id} 加入群 {group_id}")
```

### 群成员减少

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"成员 {user_id} 离开了群 {group_id}")
```

## 请求事件处理

### 好友请求

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"收到好友请求: {user_id}, 附言: {comment}")
    
    # 可以通过适配器 API 处理请求
    # 具体实现请参考各适配器文档
```

### 群邀请请求

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"收到群 {group_id} 的邀请，来自 {user_id}")
```

## 元事件处理

### 连接事件

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} 平台已连接")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"{platform} 平台已断开连接")
```

### 心跳事件

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} 心跳检测")
```

### Bot 状态查询

当适配器发送 meta 事件后，框架自动追踪 Bot 状态，你可以随时查询：

```python
from ErisPulse import sdk

# 检查某个 Bot 是否在线
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot 在线")

# 列出当前所有在线 Bot
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# 获取完整状态摘要
summary = sdk.adapter.get_status_summary()
```

## 交互式处理

### 使用 reply 方法发送回复

`event.reply()` 方法支持多种修饰参数，方便发送带有 @、回复等功能的消息：

```python
# 简单回复
await event.reply("你好")

# 发送不同类型的消息
await event.reply("http://example.com/image.jpg", method="Image")  # 图片
await event.reply("http://example.com/voice.mp3", method="Voice")  # 语音

# @单个用户
await event.reply("你好", at_users=["user123"])

# @多个用户
await event.reply("大家好", at_users=["user1", "user2", "user3"])

# 回复消息
await event.reply("回复内容", reply_to="msg_id")

# @全体成员
await event.reply("公告", at_all=True)

# 组合使用：@用户 + 回复消息
await event.reply("内容", at_users=["user1"], reply_to="msg_id")
```

### 等待用户回复

```python
@command("ask", help="询问用户")
async def ask_handler(event):
    await event.reply("请输入你的名字:")
    
    # 等待用户回复，超时时间 30 秒
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")
    else:
        await event.reply("等待超时，请重新输入。")
```

> [!TIP]
> **等待期间命令仍然可用**（2.8.3+）：以命令前缀开头且命中已注册命令的
> 消息（如 `/cancel`）会**执行命令**而非作为回复内容，等待继续挂起——
> 用户可以随时取消/切换，命令执行完仍可继续回复。需要"等待吞掉一切文本"
> 的旧行为时：配置 `ErisPulse.event.wait_reply.cmdpass = true`，或单次
> `wait_reply(cmdpass=True)`。

### 带验证的等待回复

```python
@command("age", help="询问年龄")
async def age_handler(event):
    def validate_age(event_data):
        """验证年龄是否有效"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("请输入你的年龄 (0-150):")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"你的年龄是 {age} 岁")
    else:
        await event.reply("输入无效或超时")
```

### 带回调的等待回复

```python
@command("confirm", help="确认操作")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["是", "yes", "y"]:
            await event.reply("操作已确认！")
        else:
            await event.reply("操作已取消。")
    
    await event.reply("确认执行此操作吗？(是/否)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### 确认对话 (confirm)

等待用户确认或否定，自动识别内置中英文确认词：

```python
@command("confirm", help="确认操作")
async def confirm_handler(event):
    if await event.confirm("确定要执行此操作吗？"):
        await event.reply("已确认，执行中...")
    else:
        await event.reply("已取消")

# 自定义确认词
if await event.confirm("继续吗？", yes_words={"go", "继续"}, no_words={"stop", "停止"}):
    pass
```

### 选择菜单 (choose)

用户可回复选项编号或选项文本：

```python
@command("choose", help="选择")
async def choose_handler(event):
    choice = await event.choose(
        "请选择颜色：",
        ["红色", "绿色", "蓝色"]
    )
    
    if choice is not None:
        colors = ["红色", "绿色", "蓝色"]
        await event.reply(f"你选择了：{colors[choice]}")
    else:
        await event.reply("超时未选择")
```

**合并模式**：`merge_prompt=True` 时将选项拼入提示消息，用用户指定的 `method` 一条消息发送：

```python
# 用 Markdown 发送合并后的提示 + 选项
choice = await event.choose(
    "## 请选择颜色\n{options}\n请回复编号",
    ["红色", "绿色", "蓝色"],
    method="Markdown",
    merge_prompt=True,
)
```

> `{options}` 占位符控制选项插入位置；不写则追加到 prompt 末尾。
> 可通过 `placeholder` 参数自定义占位符（如 `placeholder="[choices]"`）。
> `options_format="auto"`（默认）根据 method 自动选择样式：Markdown→无序列表，Html→有序列表，其他→纯文本列表。
> 文本类方法（Text/Markdown/Html 等）默认合并选项到末尾；非文本方法（Image 等）默认拆分为两条消息。

### 收集表单 (collect)

多步骤收集用户输入：

```python
@command("register", help="注册")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "请输入姓名："},
        {"key": "age", "prompt": "请输入年龄：", 
         "validator": lambda e: e.get_text().isdigit()},
        {"key": "email", "prompt": "请输入邮箱："}
    ])
    
    if data:
        await event.reply(f"注册成功！\n姓名：{data['name']}\n年龄：{data['age']}\n邮箱：{data['email']}")
    else:
        await event.reply("注册超时或输入无效")
```

### 等待任意事件 (wait_for)

等待满足条件的任意事件，不限于同一用户：

```python
@command("wait_member", help="等待新成员")
async def wait_member_handler(event):
    await event.reply("等待群成员加入...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"欢迎新成员：{evt.get_user_id()}")
    else:
        await event.reply("等待超时")
```

### 多轮对话 (conversation)

创建可交互的多轮对话上下文：

```python
@command("survey", help="问卷调查")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("欢迎参与问卷调查！")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("对话超时，再见！")
            break
        
        text = reply.get_text()
        
        if text == "退出":
            await conv.say("再见！")
            break
        
        await conv.say(f"你说了：{text}，继续输入或回复'退出'结束")
```

### 内置确认词

ErisPulse 内置了中英文确认词集合：

- **确认词** (`CONFIRM_YES_WORDS`): 是、yes、y、确认、确定、好、好的、ok、true、对、嗯、行、同意、没问题...
- **否定词** (`CONFIRM_NO_WORDS`): 否、no、n、取消、不、不要、不行、cancel、false、错、拒绝、不可以...

## 事件数据访问

### Event 对象常用方法

```python
@command("info")
async def info_handler(event):
    # 基础信息
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # 发送者信息
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # 消息内容
    message_segments = event.get_message()
    alt_message = event.get_alt_message()
    text = event.get_text()
    
    # 群组信息
    group_id = event.get_group_id()
    
    # 机器人信息
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # 原始数据
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # 平台信息
    platform = event.get_platform()
    
    # 消息类型判断
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # 命令信息
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### 平台扩展方法

除了内置方法外，各平台适配器还会注册平台专有方法，方便你访问平台特有的数据。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # 根据平台调用专有方法
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram 专有方法
    elif platform == "email":
        subject = event.get_subject()           # 邮件专有方法
```

如果不确定平台是否注册了某个方法，可以查询某个平台注册了哪些方法：

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> 各平台注册的专有方法请参阅对应的 [平台文档](../platform-guide/)。

## 事件处理最佳实践

### 1. 异常处理

```python
@command("process")
async def process_handler(event):
    try:
        # 业务逻辑
        result = await do_some_work()
        await event.reply(f"结果: {result}")
    except ValueError as e:
        # 预期的业务错误
        await event.reply(f"参数错误: {e}")
    except Exception as e:
        # 未预期的错误
        sdk.logger.error(f"处理失败: {e}")
        await event.reply("处理失败，请稍后重试")
```

### 2. 日志记录

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"处理消息: {user_id} - {text}")
    
    # 使用模块自己的日志
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"详细调试信息")
```

### 3. 条件处理

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """条件处理 - 在处理器内部判断"""
    # 只处理特定用户的消息
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # 只处理包含特定关键词的消息
    if "关键词" not in event.get_text():
        return
    
    await event.reply("条件满足，处理消息")
```

## 常见任务

> 来源: `docs/zh-CN/getting-started/common-tasks.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/getting-started/common-tasks.md）

# 常见任务示例

> [!TIP]
> **什么时候需要读这篇**：想给机器人加某个具体功能时按节查阅——持久化、定时任务、消息过滤、权限控制、批量发送，每一节都是可直接复制的完整示例。想系统学事件处理写法先看 [事件处理入门](event-handling.md)；不需要则跳过。

## 内容列表

1. 数据持久化
2. 定时任务
3. 消息过滤
4. 多平台适配
5. 消息发送进阶（重试/超时/批量）
6. 权限控制
7. 消息统计
8. 搜索功能
9. 图片处理

## 数据持久化

### 简单计数器

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="查看命令调用次数")
async def count_handler(event):
    # 获取计数
    count = sdk.storage.get("command_count", 0)
    
    # 增加计数
    count += 1
    sdk.storage.set("command_count", count)
    
    await event.reply(f"这是第 {count} 次调用此命令")
```

### 用户数据存储

```python
@command("profile", help="查看个人资料")
async def profile_handler(event):
    user_id = event.get_user_id()
    
    # 获取用户数据
    user_data = sdk.storage.get(f"user:{user_id}", {
        "nickname": "",
        "join_date": None,
        "message_count": 0
    })
    
    profile_text = f"""
昵称: {user_data['nickname']}
加入时间: {user_data['join_date']}
消息数: {user_data['message_count']}
    """
    
    await event.reply(profile_text.strip())

@command("setnick", help="设置昵称")
async def setnick_handler(event):
    user_id = event.get_user_id()
    args = event.get_command_args()
    
    if not args:
        await event.reply("请输入昵称")
        return
    
    # 更新用户数据
    user_data = sdk.storage.get(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    sdk.storage.set(f"user:{user_id}", user_data)
    
    await event.reply(f"昵称已设置为: {' '.join(args)}")
```

## 定时任务

### 简单定时器

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command
import asyncio

class TimerModule:
    def __init__(self):
        self.sdk = sdk
        self._tasks = []
    
    async def on_load(self, event):
        """模块加载时启动定时任务"""
        self._start_timers()
        
        @command("timer", help="定时器管理")
        async def timer_handler(event):
            await event.reply("定时器正在运行中...")
    
    def _start_timers(self):
        """启动定时任务"""
        # 每 60 秒执行一次
        task = asyncio.create_task(self._every_minute())
        self._tasks.append(task)
        
        # 每天凌晨执行
        task = asyncio.create_task(self._daily_task())
        self._tasks.append(task)
    
    async def _every_minute(self):
        """每分钟执行的任务"""
        self.sdk.logger.info("每分钟任务执行")
        # 你的逻辑...
    
    async def _daily_task(self):
        """每天凌晨执行的任务（注：基于 UTC 时间计算，如需本地时间请自行调整）"""
        import time
        
        while True:
            # 计算到凌晨的时间
            now = time.time()
            midnight = now + (86400 - now % 86400)
            
            await asyncio.sleep(midnight - now)
            
            # 执行任务
            self.sdk.logger.info("每日任务执行")
            # 你的逻辑...
```

### 使用生命周期事件

```python
@sdk.lifecycle.on("core.init.complete")
async def init_complete_handler(event_data):
    """SDK 初始化完成后启动定时任务"""
    import asyncio
    
    async def daily_reminder():
        """每日提醒"""
        await asyncio.sleep(86400)  # 24小时
        sdk.logger.info("执行每日任务")
    
    # 启动后台任务
    asyncio.create_task(daily_reminder())
```

## 消息过滤

### 关键词过滤

```python
from ErisPulse.Core.Event import message

blocked_words = ["垃圾", "广告", "钓鱼"]

@message.on_message()
async def filter_handler(event):
    text = event.get_text()
    
    # 检查是否包含敏感词
    for word in blocked_words:
        if word in text:
            sdk.logger.warning(f"拦截敏感消息: {word}")
            return  # 不处理此消息
    
    # 正常处理消息
    await event.reply(f"收到: {text}")
```

### 黑名单过滤

```python
# 从配置或存储加载黑名单
blacklist = sdk.storage.get("user_blacklist", [])

@message.on_message()
async def blacklist_handler(event):
    user_id = event.get_user_id()
    
    if user_id in blacklist:
        sdk.logger.info(f"黑名单用户: {user_id}")
        return  # 不处理
    
    # 正常处理
    await event.reply(f"你好，{user_id}")
```

## 多平台适配

### 平台特定响应

```python
@command("help", help="显示帮助")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("云湖平台帮助...")
    elif platform == "telegram":
        await event.reply("Telegram platform help...")
    elif platform == "onebot11":
        await event.reply("OneBot11 help...")
    else:
        await event.reply("通用帮助信息")
```

### 平台特性检测

```python
@command("rich", help="发送富文本消息")
async def rich_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        # 云湖支持 HTML
        yunhu = sdk.adapter.get("yunhu")
        await yunhu.Send.To("user", event.get_user_id()).Html(
            "<b>加粗文本</b><i>斜体文本</i>"
        )
    elif platform == "telegram":
        # Telegram 支持 Markdown
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.To("user", event.get_user_id()).Markdown(
            "**加粗文本** *斜体文本*"
        )
    else:
        # 其他平台使用纯文本
        await event.reply("加粗文本 斜体文本")
```

## 消息发送进阶（重试/超时/批量）

除了简单的 `event.reply()`，你还可以通过适配器的 Send DSL 实现更复杂的发送场景：失败自动重试、超时取消、成功后执行逻辑、批量发送多条消息。

> 下面的示例用 `event.get_detail_type()` 和 `event.get_target_id()` 从事件中获取目标类型和 ID（群聊自动取 group_id，私聊自动取 user_id），避免硬编码。

### 发送成功后执行逻辑

```python
@command("pay", help="模拟支付")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # 发送成功后才扣积分
    await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
           .Hook(lambda r: sdk.storage.set(f"points:{user_id}", -10))
           .Text("支付成功，已扣除 10 积分"))
```

### 失败重试 + 超时取消

```python
@command("notice", help="发送重要通知")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 最多重试 3 次，每次超时 10 秒
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"通知发送失败: {ctx.error}"))
            .Text("这是一条重要通知"))
    # 不等待，后台发送
```

### 批量发送多条消息

一条链路发多条消息，统一执行：

```python
@command("announce", help="发送公告")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 构建多条消息，统一发送（默认并行）
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 今日公告")
                    .Image("https://example.com/banner.jpg")
                    .Text("详细内容见上方图片")
                    .Retry(2)            # 失败的条目各自重试
                    .send_all())
    sdk.logger.info(f"批量发送完成，共 {len(results)} 条")
```

> 更完整的规则与批量说明请参考 [平台特性指南](../platform-guide/README.md#发送规则装饰器)。

## 权限控制

### 管理员检查

```python
# 配置主人列表
MASTERS = ["user123", "user456"]

def is_master(user_id):
    """检查是否为框架主人"""
    return user_id in MASTERS

@command("master", help="框架主人命令")
async def master_handler(event):
    user_id = event.get_user_id()
    
    if not is_master(user_id):
        await event.reply("权限不足，此命令仅框架主人可用")
        return
    
    await event.reply("框架主人命令执行成功")

@command("addmaster", help="添加框架主人")
async def addmaster_handler(event):
    if not is_master(event.get_user_id()):
        return
    
    args = event.get("text", "").split()
    if len(args) < 2:
        await event.reply("用法: /addmaster <用户ID>")
        return
    
    new_master = args[0]
    MASTERS.append(new_master)
    await event.reply(f"已添加框架主人: {new_master}")
```

### 群组权限

```python
@command("groupinfo", help="查看群组信息")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("此命令仅限群聊使用")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"群组 ID: {group_id}, 你的 ID: {user_id}")
```

## 消息统计

### 消息计数

> **注意**：以下示例使用 `sdk.storage.get/set` 进行简单计数。在高并发场景下，建议使用 `sdk.storage.transaction()` 保证原子性。

```python
@message.on_message()
async def count_handler(event):
    # 获取统计
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    # 更新统计
    stats["total"] += 1
    
    user_id = event.get_user_id()
    stats["by_user"][user_id] = stats["by_user"].get(user_id, 0) + 1
    
    # 保存
    sdk.storage.set("message_stats", stats)

@command("stats", help="查看消息统计")
async def stats_handler(event):
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    top_users = sorted(
        stats["by_user"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    top_text = "\n".join(
        f"{uid}: {count} 条消息" for uid, count in top_users
    )
    
    await event.reply(f"总消息数: {stats['total']}\n\n活跃用户:\n{top_text}")
```

## 搜索功能

### 简单搜索

> **注意**：以下示例使用内存列表存储消息历史，**程序重启后数据会丢失**。生产环境建议使用 `sdk.storage` 或 SQLite 表进行持久化存储。

```python
from ErisPulse.Core.Event import command, message

# 存储消息历史
message_history = []

@message.on_message()
async def store_handler(event):
    """存储消息用于搜索"""
    user_id = event.get_user_id()
    text = event.get_text()
    
    message_history.append({
        "user_id": user_id,
        "text": text,
        "time": event.get_time()
    })
    
    # 限制历史记录数量
    if len(message_history) > 1000:
        message_history.pop(0)

@command("search", help="搜索消息")
async def search_handler(event):
    args = event.get_command_args()
    
    if not args:
        await event.reply("请输入搜索关键词")
        return
    
    keyword = " ".join(args)
    results = []
    
    # 搜索历史记录
    for msg in message_history:
        if keyword in msg["text"]:
            results.append(msg)
    
    if not results:
        await event.reply("未找到匹配的消息")
        return
    
    # 显示结果
    result_text = f"找到 {len(results)} 条匹配消息:\n\n"
    for i, msg in enumerate(results[:10], 1):  # 最多显示 10 条
        result_text += f"{i}. {msg['text']}\n"
    
    await event.reply(result_text)
```

## 图片处理

### 图片下载和存储

```python
from ErisPulse.Core import client

@message.on_message()
async def image_handler(event):
    """处理图片消息"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            if file_url:
                # 推荐使用 SDK 内置客户端下载图片
                resp = await client.get(file_url)
                if resp.status == 200:
                    image_data = await resp.read()
                    
                    # 存储到文件
                    filename = f"images/{event.get_time()}.jpg"
                    with open(filename, "wb") as f:
                        f.write(image_data)
                    
                    sdk.logger.info(f"图片已保存: {filename}")
                    await event.reply("图片已保存")
```

### 图片识别示例

> **注意**：以下示例使用占位 API 地址，实际使用时请替换为你自己的图片识别服务。

```python
from ErisPulse.Core import client

@command("identify", help="识别图片")
async def identify_handler(event):
    """识别消息中的图片"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            # 调用图片识别 API
            result = await _identify_image(file_url)
            
            await event.reply(f"识别结果: {result}")
            return
    
    await event.reply("未找到图片")

async def _identify_image(url):
    """调用图片识别 API（示例）- 使用 SDK 内置客户端"""
    resp = await client.post(
        "https://api.example.com/identify",
        json={"url": url}
    )
    data = await resp.json()
    return data.get("description", "识别失败")
```

## IDE 补全

> 来源: `docs/zh-CN/getting-started/ide-completion.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/getting-started/ide-completion.md）

# 类型存根生成（IDE 补全）

> [!TIP]
> **什么时候需要读这篇**：IDE 补全不出适配器的平台特有方法（如云湖的 `Board`）或模块的自定义方法时，跑一条 `epsdk types` 命令生成类型存根即可解决；不需要则跳过。

ErisPulse 通过 entry-points 动态发现模块/适配器，入口点无法在静态层面获知用户类的具体类型。
`epsdk types` 命令通过扫描已安装的模块/适配器，生成一个类型存根文件，让用户可以用这些类型作为变量标注，从而获得 IDE 补全。

## 核心设计原则

存根文件**只导出类型**，不提供任何运行时实例：

- 所有导入都在 ``TYPE_CHECKING`` 下，**零运行时开销、零行为改变**
- 类型名采用 entry-point 名的 PascalCase 形式（如 ``yunhu`` → ``Yunhu``），与传入 ``sdk.adapter.get()`` / ``sdk.module.get()`` 的名称对应
- 用户在代码里照常用 ``sdk.module.get(...)`` / ``sdk.adapter.get(...)`` 获取实例，只是用导入的类型做**变量标注**

## 基本用法

在项目根目录运行：

```bash
epsdk types
```

会在当前目录生成 `_ep_types.py`，包含所有已安装模块/适配器的类型。

## 在代码中使用

```python
from _ep_types import MyModule, Yunhu
from ErisPulse import sdk

# 用导入的类型作为变量标注，即可让 IDE 补全该类的方法
my_mod: MyModule = sdk.module.get("MyModule")
my_mod.hello()                  # ← IDE 补全 hello

my_adapter: Yunhu = sdk.adapter.get("yunhu")
await my_adapter.Send.To("group", "123").Board(...)   # ← 补全平台特有方法
```

## 工作原理

1. 扫描 `erispulse.adapter` / `erispulse.module` entry-points
2. 通过子进程在目标 Python 环境中内省，收集每个适配器/模块的实际类信息（包含模块路径与限定名）
3. 生成 `.py` 文件，其中：
   - 所有 ``from xxx import Yyy as Zzz`` 都在 ``TYPE_CHECKING`` 下
   - ``Zzz`` 是 entry-point 名的 PascalCase 形式
4. IDE 读取 ``TYPE_CHECKING`` 部分提供补全；运行时不执行任何代码

生成的存根示例：

```python
# _ep_types.py（自动生成）
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 适配器
    from MyAdapter.Core import MyAdapter as MyAdapter
    from YunhuAdapter.Core import YunhuAdapter as Yunhu

    # 模块
    from MyModule.Core import Main as MyModule

    __all__ = ['MyAdapter', 'Yunhu', 'MyModule']
```

## 命令选项

| 选项 | 说明 |
|------|------|
| `-o, --output PATH` | 指定输出文件路径（默认 `./_ep_types.py`） |
| `--force` | 覆盖已存在的存根文件 |
| `--adapters-only` | 仅扫描适配器 |
| `--modules-only` | 仅扫描模块 |

## 何时重新生成

- 安装/卸载新的模块或适配器后
- 模块/适配器更新了公开 API 后
- IDE 补全失效或类型过期时

## 与 SendDSL 标准方法的关系

`SendDSL` 基类已内置标准发送方法（Text/Image/Voice/Video/File），任何方式获取的 SendDSL 实例都能补全这些方法。
`types` 命令主要用于补全**平台特有方法**（如云湖的 `Board`、沙盒的 `Dice`）和**模块特有方法**。
