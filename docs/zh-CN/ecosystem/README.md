# 生态模块

ErisPulse 框架本身只提供核心能力（事件系统、模块系统、配置、路由、日志等），**不内置** GUI、图片渲染、可视化等"重型"功能。这些能力由社区维护的 **第三方模块** 提供，按需安装即可。

> [!IMPORTANT]
> 本目录下所有文档描述的模块 **都需要单独安装**，不是 ErisPulse 框架自带的：
>
> ```bash
> epsdk install <模块名>
> ```
>

---

## 推荐模块

| 模块 | 用途 | 文档 |
|------|------|------|
| [ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) | Web 管理面板：模块启停、配置编辑、日志查看、事件监控；支持其他模块向侧边栏注册自定义视窗 | [Dashboard 使用与视窗注册](dashboard.md) |
| [ErisPulse-Takumi](https://github.com/ccd2s/ErispulseTakumi)（作者 [@ccd2s](https://github.com/ccd2s)） | 图片渲染：HTML / 节点树 / Jinja / SVG / 动画，基于 [takumi-py](https://github.com/BalconyJH/takumi-py)；内置中英文字体，开箱即用 | [Takumi 图片渲染](takumi.md) |

---

## 我也想把自己的模块列在这里？

欢迎推荐优质的、可被广泛复用的 ErisPulse 生态模块。要求：

1. 已发布到 [PyPI](https://pypi.org/)，且包名以 `ErisPulse-` 开头
2. 提供基本的 README 与使用示例
3. 积极维护，对 Issue 有响应

满足以上条件的模块作者可以通过 PR 在本目录下新增 `<模块名>.md` 文档，并在本表的「推荐模块」中追加一行。
