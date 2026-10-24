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
