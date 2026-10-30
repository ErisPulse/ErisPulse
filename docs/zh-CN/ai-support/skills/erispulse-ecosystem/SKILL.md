---
name: erispulse-ecosystem
description: "适用于：了解生态组件（Dashboard/Cron/AI 模块等）与各平台适配器的接入差异。覆盖场景：ErisPulse 框架本身只提供核心能力（事件系统、模块系统、配置、路由、日志等），**不内置** GUI、图片渲染、可视化等"重型"功能。这些能力由社区维护的 **第三方模块** 提供，按需安装即可。当你想用网页可视化管理机器人（启停模块、编辑配置、看日志、监控事件流），或想为自己的模块注册一个 Dashboard 管理页面时读这篇。当你的模块需要定时/延时触发逻辑（定时提醒、周期监控、Cron 表达式调度），且希望任务在框架重启后不丢失时读这篇。当你想给机器人加 AI 智能体能力（工具循环、流式对话、MCP、长期记忆），或想把自己模块的服务暴露给智能体调用时读这篇。当你想让 Claude Desktop 等支持 MCP 的 AI 客户端直接操控你的机器人——发消息、看消息、调模块、管适配器、观测事件流——时读这篇。此部分由各适配器开发者维护，用于说明该适配器与 OneBot12 标准的差异和扩展功能。请参考以下各平台的详细文档：。"
---

# ErisPulse 生态与多平台

本技能由 ErisPulse 文档自动构建（generate-skills.py）。
仓库：https://github.com/ErisPulse/ErisPulse
各节末尾标注了来源文档路径，需要最新内容请以仓库 docs/zh-CN/ 为准。

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 生态总览: 55-74 行
- 推荐模块: 76-126 行
- 官方客户端（独立程序）: 128-138 行
- 我也想把自己的模块列在这里？: 140-148 行
- Dashboard: 150-177 行
- 工作原理: 179-190 行
- 注册 API: 192-230 行
- 两种注入模式: 232-265 行
- 侧边栏分组: 267-293 行
- 常用 CSS 类名: 295-330 行
- 认证与 API 调用: 332-354 行
- 完整模块示例: 356-466 行
- 注销视窗: 468-480 行
- 注意事项: 482-492 行
- 定时任务: 494-514 行
- 功能速览: 516-525 行
- 快速开始: 527-545 行
- API 概览: 547-602 行
- 模块卸载时的行为: 604-611 行
- 相关链接: 613-618 行
- AI 对话模块: 620-638 行
- 核心能力: 640-659 行
- 模块扩展: 661-731 行
- 事件订阅: 733-745 行
- 作为服务被调用: 747-753 行
- 配套插件: 755-765 行
- 界面: 767-775 行
- MCP 桥: 777-795 行
- 工作原理: 797-808 行
- Claude Desktop 接入: 810-828 行
- 14 个工具一览: 830-840 行
- 安全要点: 842-851 行
- 平台指南索引: 853-870 行
- 平台特定功能: 872-896 行
- 通用接口: 898-1078 行
- 标准格式: 1080-1136 行
- 参考链接: 1138-1148 行
- 参与贡献: 1150-1159 行

## 生态总览

> 来源: `docs/zh-CN/ecosystem/README.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/ecosystem/README.md）

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

想让群里有一个会干活的 AI 助手，而不是只会关键词回复？QvQChat 是通用智能体：工具循环覆盖收发消息 / 代码执行 / 电脑操作 / 生图 / 语音 / MCP / 子智能体，支持流式对话与串行工具回放，内置 Dashboard 视窗。还有 QvQStalker（旁听插话）、QvQMemes（表情包）、QvQCompanion（拟人陪伴）三个配套插件。

```bash
epsdk install ErisPulse-QvQChat
```

文档：[QvQChat 智能体](qvqchat.md) ｜ 项目主页：[GitHub](https://github.com/wsu2059q/ErisPulse-QvQChat)

### ErisPulse-ApiMCP：让 AI 客户端操控机器人

在用 Claude Desktop、Claude Code 这类支持 MCP 的 AI 客户端？ApiMCP 把机器人运行时反向开放成 14 个 MCP 工具：AI 可以直接替你收发消息、调用已装模块、查看平台状态、订阅群聊事件——机器人变成 AI 的"手和眼"。

```bash
epsdk install ErisPulse-ApiMCP
```

文档：[ApiMCP 使用指南](apimcp.md) ｜ 项目主页：[GitHub](https://github.com/wsu2059q/ErisPulse-ApiMCP)

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

## Dashboard

> 来源: `docs/zh-CN/ecosystem/dashboard.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/ecosystem/dashboard.md）

# ErisPulse-Dashboard

> [!TIP]
> **什么时候需要读这篇**：当你想用网页可视化管理机器人（启停模块、编辑配置、看日志、监控事件流），或想为自己的模块注册一个 Dashboard 管理页面时读这篇。不需要则跳过。

[ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) 是ErisDev直接维护的 **Web 管理面板模块**，为 ErisPulse 提供可视化的运行时管理界面：模块启停、配置编辑、日志查看、事件流监控等。

> [!IMPORTANT]
> Dashboard **不是** ErisPulse 框架的内置功能，需要单独安装：
>
> ```bash
> epsdk install Dashboard
> ```

Dashboard 还支持其他 ErisPulse 模块将自定义的管理页面注册到侧边栏。注册后，用户可以直接在 Dashboard 中切换到该模块的专属视窗页面，无需额外开发独立的前端界面。

> [!NOTE]
> 视窗注册是**可选功能**。
>
> - 如果 Dashboard 模块**未安装**或**未加载**，调用 `sdk.Dashboard.register_view()` 会抛出异常
> - 请务必使用 `try/except` 包裹注册代码，确保模块本身的其他功能不受影响
> - 建议在注册前检查 Dashboard 是否可用：`hasattr(sdk, 'Dashboard') and sdk.Dashboard`

---

## 工作原理

```
模块 on_load()
  → 调用 sdk.Dashboard.register_view(...)
  → Dashboard 后端存储视窗信息
  → WebSocket 通知前端
  → 前端动态创建侧边栏导航项 + 页面容器
  → 用户点击即可查看模块视窗
```

---

## 注册 API

```python
sdk.Dashboard.register_view(
    id="MyModule",                    # 必填，唯一标识
    title="我的模块",                  # 中文名称
    title_en="My Module",             # 英文名称
    icon_svg='<svg>...</svg>',        # 侧边栏图标 SVG
    html_content='<div>...</div>',     # 页面 HTML 内容
    js_content='function xxx() {}',    # 页面 JavaScript 逻辑
    css_content='.my-style {}',        # 可选自定义 CSS
    iframe_url='',                     # iframe 模式 URL（与 html_content 二选一）
    loader="loadMyModuleView",         # 切换到该页面时调用的 JS 函数名
    group="group_extensions",          # 侧边栏分组
    group_title="",                    # 自定义分组中文名
    group_title_en="",                 # 自定义分组英文名
)
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | `str` | 是 | 视窗唯一标识，建议使用模块名称 |
| `title` | `str` | 否 | 中文显示名称，默认使用 `id` |
| `title_en` | `str` | 否 | 英文显示名称，默认使用 `title` |
| `icon_svg` | `str` | 否 | 侧边栏图标的完整 SVG 字符串 |
| `html_content` | `str` | 否* | 注入模式的页面 HTML 内容 |
| `js_content` | `str` | 否 | 页面 JavaScript 代码 |
| `css_content` | `str` | 否 | 页面自定义 CSS 样式 |
| `iframe_url` | `str` | 否* | iframe 模式的 URL，设置后忽略 `html_content` |
| `loader` | `str` | 否 | 页面激活时自动调用的 JS 函数名 |
| `group` | `str` | 否 | 侧边栏分组标识，默认 `group_extensions` |
| `group_title` | `str` | 否 | 自定义分组的中文标题 |
| `group_title_en` | `str` | 否 | 自定义分组的英文标题 |

> *`html_content` 和 `iframe_url` 至少提供一个，否则页面为空白。

---

## 两种注入模式

### 模式一：HTML/JS 注入（推荐）

直接提供 HTML、JS、CSS 字符串，Dashboard 会将内容注入到页面中。该模式与 Dashboard 样式完全一致，推荐使用 Dashboard 提供的 CSS 类名。

```python
sdk.Dashboard.register_view(
    id="HelloPage",
    title="你好页面", title_en="Hello",
    icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>',
    html_content='<h1 class="page-title">Hello World</h1><div class="card"><div class="card-body">这是一个示例页面</div></div>',
    group="group_tools",
)
```

> 完整的天气模块示例（包含 API 路由、JS 交互等）请见下方 [完整模块示例](#完整模块示例)。

### 模式二：iframe 嵌入

模块提供自己的 HTML 页面 URL（需自行注册路由），Dashboard 以 iframe 方式嵌入。适合需要完全独立 UI 或复杂交互的场景。

```python
sdk.Dashboard.register_view(
    id="MyVisualizer",
    title="数据可视化", title_en="Data Visualizer",
    iframe_url="/MyVisualizer/view",
    group="group_tools",
)
```

> iframe 模式会自动在 URL 后追加 `token` 参数用于认证。

---

## 侧边栏分组

模块可指定视窗所在的侧边栏分组。Dashboard 内置以下分组：

| 分组标识 | 中文名 | 位置 |
|---------|--------|------|
| `group_overview` | 概览 | 第1组 |
| `group_events` | 事件 | 第2组 |
| `group_extensions` | 扩展 | 第3组（默认） |
| `group_system` | 系统 | 第4组 |
| `group_tools` | 工具 | 第5组 |

指定内置分组名，模块视窗会追加到该分组末尾：

```python
group="group_tools"  # 追加到"工具"分组
```

也可以使用自定义分组名（不以 `group_` 开头），Dashboard 会自动创建新分组：

```python
group="my_group",
group_title="我的分组",
group_title_en="My Group",
```

---

## 常用 CSS 类名

模块视窗使用 HTML 注入模式时，可直接使用 Dashboard 已有的 CSS 类名来保持视觉一致性：

| 类名 | 用途 |
|------|------|
| `page-title` | 页面标题，如 `<h1 class="page-title">标题</h1>` |
| `card` | 卡片容器 |
| `card-header` | 卡片标题栏 |
| `card-body` | 卡片内容区域 |
| `grid-2` | 两列网格布局 |
| `grid-3` | 三列网格布局 |
| `btn` | 基础按钮 |
| `btn-primary` | 主按钮（蓝色） |
| `btn-secondary` | 次要按钮 |
| `btn-icon` | 图标按钮 |
| `btn-danger` | 危险操作按钮 |

Dashboard 使用 CSS 变量控制主题色，你可以在模块视窗中直接引用：

| CSS 变量 | 用途 |
|----------|------|
| `var(--bg-p)` | 主背景色 |
| `var(--bg-s)` | 次背景色 |
| `var(--bg-t)` | 三级背景色（卡片等） |
| `var(--tx-p)` | 主文字色 |
| `var(--tx-s)` | 次文字色 |
| `var(--tx-t)` | 辅助文字色 |
| `var(--bd)` | 边框色 |
| `var(--accent)` | 强调色 |
| `var(--ok-c)` | 成功色 |
| `var(--er-c)` | 错误色 |

这些变量会根据 Dashboard 的亮色/暗色主题自动切换，模块无需额外处理。

---

## 认证与 API 调用

在模块视窗的 JS 中调用模块自己的 API 时，需要携带 Dashboard 的 Token 进行认证：

```javascript
var token = localStorage.getItem('__ep_tk__');
var resp = await fetch('/YourModule/api/data', {
    headers: { 'Authorization': 'Bearer ' + token }
});
var data = await resp.json();
```

模块的 API 端点可以自行决定是否验证 Token。如果需要验证，可以从请求头中提取：

```python
async def _api_data(self, request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return {"error": "Unauthorized"}, 401
    return {"data": "hello"}
```

---

## 完整模块示例

以下是一个完整的天气模块示例，展示如何注册视窗、提供 API 数据、以及在卸载时清理资源：

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command


class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("Weather")
        self.config = self._load_config()

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(lazy_load=False, priority=50)

    async def on_load(self, event):
        self._register_routes()
        self._register_dashboard_view()
        self.logger.info("天气模块已加载")

    async def on_unload(self, event):
        self._unregister_routes()
        if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
            self.sdk.Dashboard.unregister_view("Weather")
        self.logger.info("天气模块已卸载")

    def _load_config(self):
        config = self.sdk.config.getConfig("Weather")
        if not config:
            default = {"city": "北京", "api_key": ""}
            self.sdk.config.setConfig("Weather", default)
            return default
        return config

    def _register_routes(self):
        r = self.sdk.router
        r.register_http_route("Weather", "/api/current",
                              handler=self._api_current, methods=["GET"])

    def _unregister_routes(self):
        r = self.sdk.router
        try:
            r.unregister_http_route("Weather", "/api/current")
        except Exception:
            pass

    async def _api_current(self, request):
        return {
            "city": self.config.get("city", "北京"),
            "temp": 25,
            "humidity": 60,
        }

    def _register_dashboard_view(self):
        try:
            dashboard = self.sdk.Dashboard
            dashboard.register_view(
                id="Weather",
                title="天气", title_en="Weather",
                icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
                html_content='''
                    <h1 class="page-title">天气查询</h1>
                    <p style="color:var(--tx-s);margin-bottom:16px">查看当前天气信息</p>
                    <div class="grid-2">
                        <div class="card">
                            <div class="card-header">当前天气</div>
                            <div class="card-body">
                                <div id="weather-info" style="font-size:14px;color:var(--tx-s)">点击刷新加载</div>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-header">操作</div>
                            <div class="card-body">
                                <button class="btn btn-primary" onclick="refreshWeather()">刷新</button>
                            </div>
                        </div>
                    </div>
                ''',
                js_content='''
                    async function loadWeatherView() { await refreshWeather(); }
                    async function refreshWeather() {
                        var el = document.getElementById('weather-info');
                        if (!el) return;
                        el.textContent = '加载中...';
                        try {
                            var resp = await fetch('/Weather/api/current', {
                                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('__ep_tk__') }
                            });
                            var data = await resp.json();
                            el.innerHTML = '<p>城市: ' + (data.city || '--') + '</p>' +
                                           '<p>温度: ' + (data.temp || '--') + '°C</p>' +
                                           '<p>湿度: ' + (data.humidity || '--') + '%</p>';
                        } catch (e) {
                            el.textContent = '加载失败: ' + e.message;
                        }
                    }
                ''',
                loader="loadWeatherView",
                group="group_tools",
            )
        except Exception as e:
            self.logger.warning(f"注册 Dashboard 视窗失败: {e}")
```

---

## 注销视窗

模块卸载时应调用 `unregister_view()` 清理已注册的视窗：

```python
async def on_unload(self, event):
    if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
        self.sdk.Dashboard.unregister_view("Weather")
```

注销后 Dashboard 前端会通过 WebSocket 实时移除侧边栏导航项和页面内容，无需用户刷新。

---

## 注意事项

1. **加载顺序** — Dashboard 的加载优先级为 `99999`（高优先级），你的模块优先级应低于此值（如 `50`），确保 Dashboard 先加载完成
2. **防御性编程** — 注册视窗时使用 `try/except` 包裹，因为 Dashboard 模块可能未安装或未加载
3. **资源清理** — 在 `on_unload` 中调用 `unregister_view()` 移除已注册的视窗
4. **ID 唯一性** — `id` 参数在整个 Dashboard 中必须唯一，建议直接使用模块名称
5. **SVG 图标** — `icon_svg` 应为完整的 `<svg>` 标签，建议尺寸使用 `viewBox="0 0 24 24"`，使用 `stroke="currentColor"` 继承 Dashboard 主题色
6. **JS 函数命名** — `js_content` 中的函数名应具有唯一性（如 `loadWeatherView`），避免与其他模块冲突
7. **动态更新** — 模块注册/注销视窗后，Dashboard 前端会通过 WebSocket 实时更新侧边栏，无需刷新页面

---

## 定时任务

> 来源: `docs/zh-CN/ecosystem/cron.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/ecosystem/cron.md）

# ErisPulse-Cron

> [!TIP]
> **什么时候需要读这篇**：当你的模块需要定时/延时触发逻辑（定时提醒、周期监控、Cron 表达式调度），且希望任务在框架重启后不丢失时读这篇。不需要则跳过。

[ErisPulse-Cron](https://github.com/wsu2059q/ErisPulse-Cron) 是 ErisPulse 生态的**定时任务调度模块**，为其他模块提供统一的定时任务 API：支持一次性定时、间隔循环、Cron 表达式三种任务类型，回调传参，SQLite 持久化（重启不丢任务）。

> [!IMPORTANT]
> Cron **不是** ErisPulse 框架的内置功能，需要单独安装：
>
> ```bash
> epsdk install Cron
> ```

安装后通过 `sdk.Cron` 访问全部接口。

---

## 功能速览

- **三种定时类型**：一次性（`once`）、间隔循环（`interval`）、Cron 表达式（`cron`）
- **回调传参**：创建时传入 `callback_data`，触发时原样返回，方便识别任务来源
- **持久化**：任务存储在 SQLite（经 `sdk.storage`），框架重启后自动恢复
- **错过策略**：立即触发 / 跳过 / 重新调度，可按任务选择
- **任务管理**：暂停、恢复、取消、手动触发、清理过期任务
- **Dashboard 集成**：已安装 [ErisPulse-Dashboard](dashboard.md) 时自动注册管理视窗

---

## 快速开始

```python
from ErisPulse import sdk

# 1. 注册回调处理器
@sdk.Cron.on_trigger
async def handle_trigger(info):
    data = info["callback_data"]
    print(f"任务触发: {info['task_id']}, 数据: {data}")

# 2. 创建定时任务
task_id = sdk.Cron.once(
    delay=60,
    callback_data={"type": "reminder", "msg": "该喝水了"},
)
```

---

## API 概览

### 创建任务

```python
# 一次性：延迟 600 秒触发
sdk.Cron.once(delay=600, callback_data={"order_id": "123"}, label="订单超时提醒")

# 间隔循环：每 300 秒触发，最多 100 次
sdk.Cron.interval(interval_seconds=300, callback_data={"monitor": "server-1"}, max_runs=100)

# Cron 表达式：工作日每天 9:30
sdk.Cron.cron(expression="30 9 * * 1-5", callback_data={"type": "daily_report"})

# 通用可选参数：trigger_at（绝对时间戳）、delay（首次延迟）、timezone、
# max_runs（0=无限）、label、source（创建者模块名）、missed_policy（错过策略）
```

常用 Cron 表达式：`*/5 * * * *`（每 5 分钟）、`0 8 * * *`（每天早 8 点）、`30 9 * * 1-5`（工作日 9:30）、`0 0 1 * *`（每月 1 号）。

### 回调

```python
@sdk.Cron.on_trigger
async def my_handler(info):
    # info 含 task_id / task_type / callback_data / label / source /
    # run_count / max_runs / created_at / last_run / trigger_time
    ...
```

支持注册多个 handler，全部依次调用，单个 handler 异常不影响其他 handler。

### 管理任务

```python
sdk.Cron.cancel(task_id)                  # 取消
sdk.Cron.pause(task_id)                   # 暂停
sdk.Cron.resume(task_id)                  # 恢复（reschedule=True 重新计算下次触发）
await sdk.Cron.trigger_now(task_id)       # 手动立即触发（不影响原计划）
sdk.Cron.get_task(task_id)                # 查看单个任务
sdk.Cron.list_tasks(source="MyModule")    # 列出任务（支持 source/status/task_type 过滤）
sdk.Cron.delete_task(task_id)             # 删除任务记录
sdk.Cron.cleanup()                        # 清理 7 天前的已完成/已取消任务
```

### 错过策略（missed_policy）

框架重启后，对于错过触发时间的任务：

| 策略 | 行为 |
|------|------|
| `fire_immediately` | 立即触发（默认） |
| `skip` | 跳过本次，等下次 |
| `reschedule` | 从当前时间重新计算下次触发 |

---

## 模块卸载时的行为

Cron 的任务数据是**持久化资产**：任务创建方模块被卸载或禁用不会删除已创建的任务。但该模块注册的回调句柄会被清理——基于归属权系统的[外部清理钩子](../advanced/ownership.md#工具模块指南托管其它模块的句柄)，Cron 在替其他模块托管回调时会自动记名，对方模块被卸载/禁用时自动抛弃其回调句柄，保证对方模块实例可以被正常回收。

- 任务创建方**重载**后重新 `on_trigger` 即恢复接收触发
- 不再需要的任务可用 `sdk.Cron.cancel(task_id)` / `delete_task(task_id)` 清理

---

## 相关链接

- [GitHub 仓库](https://github.com/wsu2059q/ErisPulse-Cron)
- [PyPI 页面](https://pypi.org/project/ErisPulse-Cron/)

---

## AI 对话模块

> 来源: `docs/zh-CN/ecosystem/qvqchat.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/ecosystem/qvqchat.md）

# ErisPulse-QvQChat 通用智能体

> [!TIP]
> **什么时候需要读这篇**：当你想给机器人加 AI 智能体能力（工具循环、流式对话、MCP、长期记忆），或想把自己模块的服务暴露给智能体调用时读这篇。不需要则跳过。

[ErisPulse-QvQChat](https://pypi.org/project/ErisPulse-QvQChat/) 是一个 **通用智能体模块**，围绕工具循环构建：收发消息、调用生态模块服务、编写并运行代码、操作电脑、生成图片语音、管理定时任务与长期记忆——全部通过同一套工具协议完成。

> [!IMPORTANT]
> QvQChat 需要单独安装：
>
> ```bash
> epsdk install ErisPulse-QvQChat
> ```
>
> 同时需要在「模型池」添加至少一个 OpenAI 兼容模型（Base URL、API Key、模型名）。

## 核心能力

| 能力 | 说明 |
|---|---|
| 工具循环 | 模型输出工具调用 → 并发执行 → 结果回填 → 继续推理，直到给出最终回答 |
| 流式对话 | SSE 逐字输出，工具步骤实时可见；刷新 / 切走再回来，进度不丢 |
| 上下文压缩 | 超过 token 阈值自动把旧对话压缩为摘要（默认 128000 估算，可自定义） |
| 生态服务桥 | 自动发现模块声明的服务并转为工具，装卸模块即增减能力 |
| MCP 客户端 | stdio 与 Streamable HTTP，MCP 工具并入同一工具集 |
| 子智能体 | `spawn_agent` 派出独立会话的子智能体探索任务，只汇报结论 |
| 进程内执行 | `run_python_sdk` 主进程内运行 Python，直接访问运行时对象 |
| 电脑操作 | 三级安全沙箱（strict / standard / permissive），危险操作确认，全程审计 |
| 视觉理解 | 图片自动注入模型（不支持图片时自动剥离重试） |
| 附件 | 任意文件按 hash 去重落盘，路径交给 AI 自行处理；Ctrl+V 粘贴截图 |
| 分享会话 | 临时只读链接（有效期 + token 预算），导出 Markdown |
| 定时任务 | cron / 一次性 / 间隔，持久化，权限随创建者 |
| 会话接管 | 管理员可让智能体独占一个会话 |
| 人格系统 | 系统提示词 + 开场对话 + 工具白名单，可按会话绑定 |
| 长期记忆 | 每会话记忆条目，按相似度检索注入 |
| AI 自动命名 | 会话首轮回复后自动生成简短标题 |

## 模块扩展

任何 ErisPulse 模块声明 `services` 即自动成为 QvQChat 的工具，无需专门接口：

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class Main(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(name="Draw", services=[
            {"name": "draw", "description": "根据描述生成图片，返回图片 URL"},
        ])

    async def draw(self, prompt: str, size: str = "1024x1024"):
        return {"image_url": "https://..."}
```

服务的方法签名自动映射为工具的 JSON Schema 参数定义，docstring 首行作为参数说明。

### 深度集成（可选）

模块可以额外实现以下任意服务，每个服务**独立可选**——一个模块可以只做人格扩展，也可以只注入提示词：

#### `qvq_prompts()` → 注入系统提示词

返回 `list[str]` 或 `list[{"text": str, "priority": int}]`，按 `priority` 升序拼接。

```python
async def qvq_prompts(self):
    return [
        {"text": "画图后用 send_message 把图片发给用户。", "priority": 10},
        {"text": "支持的风格：动漫、写实、水彩、像素。", "priority": 20},
    ]
```

#### `qvq_personas()` → 注册人格预设

返回人格列表，id 自动加 `ext.<模块名>.` 前缀，模块卸载自动清理。适合专门提供人格扩展的模块（如情感陪伴、翻译专员、代码审查员等）。

```python
async def qvq_personas(self):
    return [
        {"id": "companion", "name": "暖男", "system": "你是一个温暖体贴的聊天伙伴..."},
        {"id": "coder", "name": "代码导师", "system": "...", "tools": ["read_file", "run_python"]},
    ]
```

`tools` 可选限定该人格可用的工具子集。

#### `qvq_schemas()` → 显式参数 schema

返回 `dict[服务名, JSON Schema]`，覆盖方法签名推断。参数复杂或需要严格校验时使用。

```python
async def qvq_schemas(self):
    return {
        "draw": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "画面描述"},
                "size": {"type": "string", "enum": ["512x512", "1024x1024"]},
            },
            "required": ["prompt"],
        },
    }
```

### 刷新时机

深度集成服务的刷新时机：启动、模块装卸、Dashboard「工具」页手动刷新。

## 事件订阅

QvQChat 广播两个生命周期事件：

| 事件 | 时机 | 载荷 |
|---|---|---|
| `qvq.message` | 收到用户消息 | `chat_key` `platform` `sender_id` `sender_name` `text` `is_group` |
| `qvq.replied` | 回复发出后 | `chat_key` `reply` `tools` |

```python
async def setup(self):
    sdk.lifecycle.on("qvq.message", self.on_message)
```

## 作为服务被调用

| 服务 | 签名 | 说明 |
|---|---|---|
| `chat` | `(session_id, prompt, persona="")` | 与智能体对话，返回文本 |
| `run_prompt` | `(chat_key, prompt, ...)` | 运行提示词，结果可发送到目标会话 |
| `get_status` | `()` | 运行状态摘要 |

## 配套插件

三个独立模块扩展了 QvQChat，也顺带演示了扩展点能做什么——装上 QvQChat 后按需加装：

| 插件 | 干什么 |
|---|---|
| [ErisPulse-QvQStalker](https://github.com/wsu2059q/ErisPulse-QvQStalker) | 旁听群聊自动插话：热度跟踪、五层判定和冲动值共同决定智能体何时开口，15 项行为参数在设置页直接调 |
| [ErisPulse-QvQMemes](https://github.com/wsu2059q/ErisPulse-QvQMemes) | 给智能体一个表情包习惯：`send_sticker` 工具让模型自己挑该发哪张，群图片自动收录并由视觉模型打标签 |
| [ErisPulse-QvQCompanion](https://github.com/wsu2059q/ErisPulse-QvQCompanion) | 拟人化陪伴：语气人设注入、冲动值主动开口、静默时段与每日上限 |

三个插件都通过上文「模块扩展」的约定服务接入，本身也是扩展写法的参考实现。

## 界面

通过 `/QvQChat/view` 独立访问，或嵌入 Dashboard 侧边栏。

![概览](https://raw.githubusercontent.com/wsu2059q/ErisPulse-QvQChat/main/.github/assets/overview.png)

![对话](https://raw.githubusercontent.com/wsu2059q/ErisPulse-QvQChat/main/.github/assets/chat.png)

---

## MCP 桥

> 来源: `docs/zh-CN/ecosystem/apimcp.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/ecosystem/apimcp.md）

# ErisPulse-ApiMCP 用 AI 客户端操控机器人

> [!TIP]
> **什么时候需要读这篇**：当你想让 Claude Desktop 等支持 MCP 的 AI 客户端直接操控你的机器人——发消息、看消息、调模块、管适配器、观测事件流——时读这篇。不需要则跳过。

[ErisPulse-ApiMCP](https://github.com/wsu2059q/ErisPulse-ApiMCP) 把机器人运行时能力经 **MCP（Model Context Protocol）** 开放给 AI 客户端：装上之后，Claude Desktop 里就多出 14 个工具，AI 可以替你收发消息、排查模块问题、订阅群聊事件——机器人从"你管理的程序"变成"AI 的手和眼"。

> [!IMPORTANT]
> ApiMCP 需要单独安装，且**必须显式配置 token** 后桥才启用：
>
> ```bash
> epsdk install ErisPulse-ApiMCP
> ```
>
> 在 `config.toml` 的 `[ApiMCP]` 节设置 `token = "长随机串"`（或环境变量 `ERISPULSE_APIMCP_TOKEN`）。未配置时除探活外所有端点返回 503，避免令牌静默泄漏。

## 工作原理

两层结构，机器人本体不引入任何 AI 依赖：

- **机器人进程内**：ApiMCP 模块在框架内置 HTTP server 上挂一个 REST 桥（`/apimcp/*`，token 鉴权，默认限流 30 请求/分钟）
- **独立进程**：`erispulse-apimcp` 命令用官方 `mcp` SDK 起 stdio server，把 MCP 工具调用转发到机器人 HTTP 桥

```
Claude Desktop ──MCP(stdio)──► erispulse-apimcp ──HTTP──► 机器人进程 REST 桥 ──► sdk.*
```

机器人不在线或桥未配置时，工具返回可读错误与排查指引，不抛栈。

## Claude Desktop 接入

编辑 `claude_desktop_config.json`（Windows: `%APPDATA%\Claude\`；macOS: `~/Library/Application Support/Claude/`）：

```json
{
  "mcpServers": {
    "erispulse": {
      "command": "erispulse-apimcp",
      "env": {
        "ERISPULSE_APIMCP_URL": "http://127.0.0.1:8000",
        "ERISPULSE_APIMCP_TOKEN": "你的token"
      }
    }
  }
}
```

保存后完全重启 Claude Desktop，工具列表出现 `erispulse` 服务器即接入成功。任何支持 MCP stdio server 的客户端（Claude Code、Cursor 等）都能用同样方式接入。

## 14 个工具一览

| 类别 | 工具 | 说明 |
|---|---|---|
| 模块 | `list_modules` / `get_module_info` / `call_module` / `reload_module` | 查看与调用已装模块的公开服务，触发热重载 |
| 适配器 | `list_adapters` / `get_adapter_status` / `reload_adapter` | 平台在线状态；适配器重载默认禁用 |
| 消息 | `send_message` / `recent_messages` | 向任意平台发文本/图/音/视/文件；经 [transcript](../advanced/transcript.md) 回看最近消息 |
| 事件 | `subscribe_events` / `unsubscribe` / `poll_events` | 订阅消息/通知等事件，环形缓冲（默认 1000 条），增量轮询 |
| 运行时 | `get_topology` / `sdk_health` | 运行时拓扑（已脱敏）与健康摘要 |

一个典型用法：AI 先 `subscribe_events(["message"])`，然后周期性 `poll_events` 观察群里在聊什么，决定要不要 `send_message` 插话或 `call_module` 触发某个模块的能力。

## 安全要点

- **token 即完全控制权**：能读消息、发消息、调白名单内模块方法。切勿提交仓库或贴到公开频道；多租户场景请拆多个机器人实例
- **最小授权**：`module_call_whitelist` 收窄可调用模块（支持 `模块.方法` 精确放行），`send_target_whitelist` 收窄发送目标（如只允许发某个群），`allow_adapter_reload` 保持默认关闭
- **只监听本机**：仅本机使用时把框架 HTTP server 设为 `server.host = "127.0.0.1"`；跨机器必须内网 + 反向代理加 TLS
- 输出经过键名级净化（密钥/路径类键整键丢弃）；深度净化是模块自身责任，敏感会话勿开放订阅

完整配置项（缓冲容量、回溯窗口、事件类型白名单等）与 REST 端点明细见[项目 README](https://github.com/wsu2059q/ErisPulse-ApiMCP)。

---

## 平台指南索引

> 来源: `docs/zh-CN/platform-guide/README.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-CN/platform-guide/README.md）

# ErisPulse PlatformFeatures 文档

> 基线协议：[OneBot12](https://12.onebot.dev/) 
> 
> 本文档为**平台特定功能指南**，包含：
> - 各适配器支持的Send方法链式调用示例
> - 平台特有的事件/消息格式说明
> 
> 通用使用方法请参考：
> - [基础概念](../getting-started/basic-concepts.md)
> - [事件转换标准](../standards/event-conversion.md)  
> - [API响应规范](../standards/api-response.md)

---

## 平台特定功能

此部分由各适配器开发者维护，用于说明该适配器与 OneBot12 标准的差异和扩展功能。请参考以下各平台的详细文档：

- [维护说明](maintain-notes.md)

- [云湖平台特性](yunhu.md)
- [云湖用户平台特性](yunhu_user.md)
- [Telegram平台特性](telegram.md)
- [OneBot11平台特性](onebot11.md)
- [OneBot12平台特性](onebot12.md)
- [SnowLuma平台特性](snowluma.md)
- [邮件平台特性](email.md)
- [Kook(开黑啦)平台特性](kook.md)
- [Matrix平台特性](matrix.md)
- [企业微信平台特性](wecom.md)
- [QQ官方机器人平台特性](qqbot.md)
- [花枫咖啡馆](ideaura.md)
- [Discord](discord.md)
- [Webhook协议桥](webhook.md)
- [微信公众号](wechatmp.md)

> 此外还有 `sandbox` 适配器，但此适配器无需维护平台特性文档

---

## 通用接口

### Send 链式调用
所有适配器都支持以下标准调用方式：

> **注意：** 文档中的 `{AdapterName}` 需替换为实际适配器名称（如 `yunhu`、`telegram`、`onebot11`、`email` 等）。

1. 指定类型和ID: `To(type,id).Func()`
   ```python
   # 获取适配器实例
   my_adapter = adapter.get("{AdapterName}")
   
   # 发送消息
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # 例如：
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. 仅指定ID: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # 例如：
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. 指定发送账号: `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # 例如：
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. 直接调用: `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("Broadcast message")
   
   # 例如：
   email = adapter.get("email")
   await email.Send.Text("Broadcast message")
   ```

#### 异步发送与结果处理

Send DSL 的方法返回 `asyncio.Task` 对象，这意味着您可以选择是否立即等待结果：

```python
# 获取适配器实例
my_adapter = adapter.get("{AdapterName}")

# 不等待结果，消息在后台发送
task = my_adapter.Send.To("user", "123").Text("Hello")

# 如果需要获取发送结果，稍后可以等待
result = await task
```

#### 发送规则装饰器

在实际开发中，经常需要：发送成功后才执行后续逻辑、失败自动重试、超时取消、发送进度监控等。Send DSL 内置了一套发送规则装饰器，通过链式方法附加规则：

| 方法 | 说明 |
|--------|------|
| `.Hook(callback)` | 发送成功后执行的回调（可多次调用） |
| `.Retry(times=1)` | 失败自动重试 N 次（含首次共 N+1 次） |
| `.Timeout(seconds)` | 单次发送超时，超时取消（可与 Retry 叠加） |
| `.Defer(seconds)` | 延迟发送（进程内定时，不持久化） |
| `.OnProgress(callback)` | 各阶段进度回调，传入 SendContext |
| `.OnError(callback)` | 最终失败时的错误回调（仅触发一次） |

```python
yunhu = adapter.get("yunhu")

# 发送成功后才扣积分
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("消费成功"))

# 失败重试 + 超时取消 + 进度监控
def on_progress(ctx):
    print(f"阶段: {ctx.stage}, 尝试: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # 最多重试 3 次
        .Timeout(10)           # 每次超时 10 秒
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("重要通知"))
```

规则方法返回 `self`，必须放在发送方法（Text/Image 等）之前调用。`SendContext` 包含 `stage`（pending/sending/retrying/success/failed/timeout）、`attempt`、`elapsed`、`error`、`result` 等字段，便于监控。

#### 批量构建模式（Build）

一条链路中构建多个发送方法，最后统一执行。适用于“一口气发多条消息”的场景：

```python
yunhu = adapter.get("yunhu")

# 构建多条消息，统一发送
results = await (yunhu.Send.To("user", "123")
                .Build()                     # 进入构建模式
                .Text("通知一")
                .Image("pic.jpg")
                .Text("通知二")
                .send_all())                 # 统一执行
# results = [Text结果, Image结果, Text结果]
```

`.send_all()` 默认**并行**执行（并发发送，效率高）。需要保证消息到达顺序时调用 `.Sequential()` 串行执行：

```python
# 串行执行（保证顺序）+ 失败重试
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # 按顺序依次发送
       .Retry(2)                     # 失败的条目各自重试
       .Text("第一条").Text("第二条")
       .send_all())
```

批量执行采用**失败继续**策略：某条失败不会中断其他条，失败的条目自动重试。批量也支持整批的 `Hook`（全部成功后触发）、`OnError`（有失败时触发）、`OnProgress`（进度回调）。

> 更详细的规则与批量构建说明请参考 [SendDSL 详解](../developer-guide/adapters/send-dsl.md)。

### 事件监听
有三种事件监听方式：

1. 平台原生事件监听：
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"收到{AdapterName}原生事件: {data}")
   ```

2. OneBot12标准事件监听：
   ```python
   from ErisPulse.Core import adapter, logger

   # 监听OneBot12标准事件
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"收到标准事件: {data}")

   # 监听特定平台的标准事件
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"收到{AdapterName}标准事件: {data}")
   ```

3. Event模块监听：
    `Event`的事件基于 `adapter.on()` 函数，因此`Event`提供的事件格式是一个OneBot12标准事件

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="发送问候消息", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"收到消息: {event}")
    async def notice_handler(event):
        logger.info(f"收到通知: {event}")
    async def request_handler(event):
        logger.info(f"收到请求: {event}")
    async def command_handler(event):
        logger.info(f"收到命令: {event}")
    ```

其中，最推荐的是使用 `Event` 模块进行事件处理，因为 `Event` 模块提供了丰富的事件类型，以及丰富的事件处理方法。

---

## 标准格式
为方便参考，这里给出了简单的事件格式，如果需要详细信息，请参考上方的链接。

> **注意：** 以下格式为基础 OneBot12 标准格式，各适配器可能在此基础上有扩展字段。具体请参考各适配器的特定功能说明。

### 标准事件格式
所有适配器必须实现的事件转换格式：
```json
{
  "id": "event_123",
  "time": 1752241220,
  "type": "message",
  "detail_type": "group",
  "platform": "example_platform",
  "self": {"platform": "example_platform", "user_id": "bot_123"},
  "message_id": "msg_abc",
  "message": [
    {"type": "text", "data": {"text": "你好"}}
  ],
  "alt_message": "你好",
  "user_id": "user_456",
  "user_nickname": "ExampleUser",
  "group_id": "group_789"
}
```

### 标准响应格式
#### 消息发送成功
```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "1234",
    "time": 1632847927.599013
  },
  "message_id": "1234",
  "message": "",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

#### 消息发送失败
```json
{
  "status": "failed",
  "retcode": 10003,
  "data": null,
  "message_id": "",
  "message": "缺少必要参数",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

---

## 参考链接
ErisPulse 项目：
- [主库](https://github.com/ErisPulse/ErisPulse/)
- [Yunhu 适配器库](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Telegram 适配器库](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [OneBot 适配器库](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

相关官方文档：
- [OneBot V11 协议文档](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API 官方文档](https://core.telegram.org/bots/api)
- [云湖官方文档](https://www.yhchat.com/document/1-3)

## 参与贡献

我们欢迎更多开发者参与编写和维护适配器文档！请按照以下步骤提交贡献：
1. Fork [ErisPuls](https://github.com/ErisPulse/ErisPulse) 仓库。
2. 在 `docs/platform-features/` 目录下创建一个 Markdown 文件，并命名格式为 `<平台名称>.md`。
3. 在本 `README.md` 文件中添加对您贡献的适配器的链接以及相关官方文档。
4. 提交 Pull Request。

感谢您的支持！
