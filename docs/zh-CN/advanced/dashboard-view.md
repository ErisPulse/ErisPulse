# Dashboard 视窗注册

Dashboard 支持其他 ErisPulse 模块将自定义的管理页面注册到 Dashboard 的侧边栏中。注册后，用户可以直接在 Dashboard 中切换到该模块的专属视窗页面，无需额外开发独立的前端界面。

> **前提条件**
>
> Dashboard 视窗注册是**可选功能**，需要安装并加载 [ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) 模块。
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
from fastapi.responses import JSONResponse

async def _api_data(self, request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return JSONResponse({"data": "hello"})
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
