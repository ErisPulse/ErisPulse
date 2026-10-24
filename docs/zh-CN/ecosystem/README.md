# 生态模块

ErisPulse 框架本身只提供核心能力（事件系统、模块系统、配置、路由、日志等），**不内置** GUI、图片渲染、可视化等"重型"功能。这些能力由社区维护的 **第三方模块** 提供，按需安装即可。

> [!IMPORTANT]
> 本目录下的文档分为两类，安装方式不同：
>
> - **模块**（如 Dashboard / Takumi）使用 `epsdk install` 安装：
>
>   ```bash
>   epsdk install <模块名>
>   ```
>
> - **独立程序**（如 ErisPulse-App 客户端）直接从对应 GitHub Releases 下载安装，无需 `epsdk`。

---

## 推荐模块

### ErisPulse-Dashboard：浏览器里的管理面板

机器人挂在服务器上，启停模块、改配置、看日志还得登终端？Dashboard 把这些搬进浏览器：模块启停、配置编辑、日志查看、事件监控；其他模块还能向侧边栏注册自定义视窗，管理页面集中在同一处。

```bash
epsdk install Dashboard
```

文档：[Dashboard 使用与视窗注册](dashboard.md) ｜ 项目主页：[PyPI](https://pypi.org/project/ErisPulse-Dashboard/)

### ErisPulse-Cron：定时任务

要每天定时发签到提醒、按 Cron 表达式跑周期任务、每隔几分钟轮询一次数据？Cron 提供一次性 / 间隔 / Cron 表达式三种任务类型，回调传参，SQLite 持久化（重启不丢任务）。

```bash
epsdk install Cron
```

文档：[Cron 定时任务](cron.md) ｜ 项目主页：[GitHub](https://github.com/wsu2059q/ErisPulse-Cron)

### ErisPulse-QvQChat：通用智能体

想让群里有一个会干活的 AI 助手，而不是只会关键词回复？QvQChat 是通用智能体：工具循环覆盖收发消息 / 代码执行 / 电脑操作 / 生图 / 语音 / MCP / 子智能体，支持流式对话与串行工具回放，内置 Dashboard 视窗。

```bash
epsdk install ErisPulse-QvQChat
```

文档：[QvQChat 智能体](qvqchat.md) ｜ 项目主页：[GitHub](https://github.com/wsu2059q/ErisPulse-QvQChat)

### ErisPulse-Takumi：图片渲染

排行榜、战报、日程卡这类要"发图"的场景，写个模板渲染成图片发进群里即可：支持 HTML / 节点树 / Jinja / SVG / 动画（基于 [takumi-py](https://github.com/BalconyJH/takumi-py)），内置中英文字体，开箱即用。

```bash
epsdk install Takumi
```

文档：[Takumi 图片渲染](takumi.md) ｜ 项目主页：[GitHub](https://github.com/ccd2s/ErispulseTakumi)（作者 [@ccd2s](https://github.com/ccd2s)）

## 官方客户端（独立程序）

### ErisPulse-App：手机上直接跑机器人

没有常开的服务器，也想随时创建实例、装模块、看事件流？ErisPulse-App 是官方全平台客户端（Android / Windows / Linux / macOS）：原生界面创建 / 运行 / 管理多个机器人实例，内置模块商店与事件构建器，**手机直接运行**，桌面托盘常驻。

所有平台的安装包均从 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 下载，无需 `epsdk`。

文档：[ErisPulse-App 安装与使用](app.md)

---

## 我也想把自己的模块列在这里？

欢迎推荐优质的、可被广泛复用的 ErisPulse 生态模块。要求：

1. 已发布到 [PyPI](https://pypi.org/)，且包名以 `ErisPulse-` 开头
2. 提供基本的 README 与使用示例
3. 积极维护，对 Issue 有响应

满足以上条件的模块作者可以通过 PR 在本目录下新增 `<模块名>.md` 文档，并在上方推荐列表中补充对应小节。
