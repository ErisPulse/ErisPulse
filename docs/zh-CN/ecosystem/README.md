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
>

---

## 推荐模块与官方客户端

| 项目 | 类型 | 用途 | 文档 |
|------|------|------|------|
| [ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App) | 官方客户端 | 官方全平台客户端（Android / Windows / Linux / macOS）：原生界面创建 / 运行 / 管理多个实例，内置模块商店与事件构建器；**手机直接运行**，桌面托盘常驻 | [ErisPulse-App 安装与使用](app.md) |
| [ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) | 模块 | Web 管理面板：模块启停、配置编辑、日志查看、事件监控；支持其他模块向侧边栏注册自定义视窗 | [Dashboard 使用与视窗注册](dashboard.md) |
| [ErisPulse-Takumi](https://github.com/ccd2s/ErispulseTakumi)（作者 [@ccd2s](https://github.com/ccd2s)） | 模块 | 图片渲染：HTML / 节点树 / Jinja / SVG / 动画，基于 [takumi-py](https://github.com/BalconyJH/takumi-py)；内置中英文字体，开箱即用 | [Takumi 图片渲染](takumi.md) |

---

## 我也想把自己的模块列在这里？

欢迎推荐优质的、可被广泛复用的 ErisPulse 生态模块。要求：

1. 已发布到 [PyPI](https://pypi.org/)，且包名以 `ErisPulse-` 开头
2. 提供基本的 README 与使用示例
3. 积极维护，对 Issue 有响应

满足以上条件的模块作者可以通过 PR 在本目录下新增 `<模块名>.md` 文档，并在本表的「推荐模块」中追加一行。
