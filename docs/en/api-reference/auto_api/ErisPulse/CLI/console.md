# `ErisPulse.CLI.console` 模块

---

## 模块概述


CLI 控制台模块

提供全局 Rich 控制台实例、主题样式与启动 Banner。

> **提示**
> 1. 所有 CLI 输出统一使用全局 `console` 实例，保证样式一致
> 2. 通过 `print_banner()` 输出一次性 Banner（仅首次生效）

---

## 函数列表


### `print_banner()`

输出 ErisPulse 启动 Banner

根据终端宽度选择完整版或精简版 Banner，且仅在首次调用时输出。

---


### `print_suggestion(title: str, suggestions: list[str], hint: str | None = None)`

输出错误提示与建议

统一 CLI 错误输出的视觉层次：错误标题 → 建议命令 → 补充提示。

- **title** (`str`): 错误标题（一句话说明发生了什么）
- **suggestions** (`list[str`): ] 建议的命令/名称列表（如 ["epsdk init", "epsdk install xxx"]）
- **hint** (`str | None`): 补充提示（可选，如“浏览可用包：epsdk list-remote”）

---


## 类列表


### `class CommandHighlighter(RegexHighlighter)`

高亮CLI命令和参数

> **提示**
> 使用正则表达式匹配命令行参数和选项

