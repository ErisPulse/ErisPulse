# `ErisPulse.runtime.troubleshoot` 模块

---

## 模块概述


模块排查诊断（EPRFC-2026-001 方向五·场景一 / 二）

回答两类"没反应"问题的诊断 API：

- :func:`explain_module`——模块没加载：依赖缺失 / 被配置禁用 / SDK 版本
  不满足 / 懒加载未实例化，逐项给出结构化原因
- :func:`explain_event`——事件没响应：适配器未注册 / 身份被作用域拉黑 /
  各已加载模块的作用域可用性 / 命令是否命中，输出判定结论

> **提示**
> 1. 两个函数均为纯读诊断，不改任何状态
> 2. 返回 dict（机器可读），配 :func:`format_report` 渲染为人类可读文本

---

## 函数列表


### `explain_module(name: str)`

诊断"模块为什么没加载"（场景一）

- **name** (`模块注册名`): **返回值** (`结构化诊断结果——``registered``（类是否已注册）、``loaded```): （是否已加载）、``lazy``（懒加载策略）、``enabled``（配置启用状态，
    None 表示未配置即默认启用）、``missing_dependencies``（未就绪依赖）、
    ``sdk_version_ok``（SDK 版本是否满足，无法判定时为 None）、
    ``conclusion``（一句话结论）、``reasons``（原因列表）

---


### `explain_event(event: dict[str, Any])`

诊断"事件为什么没响应"（场景二）

- **event** (`事件数据（dict`): 或 Event 包装）
**返回值** (`结构化诊断结果——``adapter_registered``（平台适配器是否已注册）、`): ``identity_allowed``（身份维度是否放行）、``available_modules``（当前
    会话可用的已加载模块）、``blocked_modules``（被作用域屏蔽的模块）、
    ``command_like``（文本是否形如命令）、``command_registered``（命令是否
    已注册）、``conclusion``、``reasons``

---


### `format_report(result: dict[str, Any])`

将诊断结果渲染为人类可读文本

- **result** (`:func:`explain_module``): 或 :func:`explain_event` 的返回值
**返回值** (`多行文本（结论`): + 原因列表）

---

