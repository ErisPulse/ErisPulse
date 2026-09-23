# 模块排查指南

模块"没反应"时，按症状分为三类问题，每类都有对应的框架诊断工具（RFC EPRFC-2026-001 方向五）：

| 症状 | 诊断工具 | 定位层面 |
|------|---------|---------|
| 模块没加载 | `ErisPulse.runtime.explain_module(name)` | 注册与加载链 |
| 事件没响应 | `ErisPulse.runtime.explain_event(event)` | 分发入口检查 |
| 命令没触发 | 分发决策链（测试侧 `DispatchTrace` / 框架内置 `trace`） | 命令判定链 |

两个诊断函数均为**纯读**操作，不改任何状态，可在任意时刻调用；返回机器可读 dict，配 `format_report()` 渲染为人类可读文本。

## 场景一：模块没加载

```python
from ErisPulse.runtime import explain_module, format_report

report = explain_module("MyModule")
print(format_report(report))
```

`explain_module()` 逐项检查并给出结论，覆盖以下原因：

| 检查项 | 说明 |
|-------|------|
| 未注册 | 包未安装、entry-point 组名错误，或注册名与查询名不一致 |
| 懒加载未实例化 | **正常状态而非故障**：懒加载模块首次被调用（`module.call` / 命令触发等）时才实例化 |
| 配置禁用 | `ErisPulse.modules.status.<模块名> = false`（未配置即默认启用） |
| 依赖未加载 | 模块声明的 `depends` 列表中有模块未就绪 |
| SDK 版本不满足 | 模块元数据声明的 `min_sdk_version` 高于当前框架版本 |
| on_load 异常 | 注册正常但未加载且无上述原因——检查启动日志中模块名对应的 ERROR 记录 |

返回 dict 的结构化字段：`registered` / `loaded` / `lazy` / `enabled`（`None` 表示未配置即默认启用）/ `missing_dependencies` / `sdk_version_ok` / `conclusion`（一句话结论）/ `reasons`（原因列表）。

## 场景二：事件没响应

```python
from ErisPulse.runtime import explain_event, format_report

report = explain_event(event)   # 处理器内拿到的 Event 或原始事件 dict
print(format_report(report))
```

`explain_event()` 按分发入口的实际检查顺序输出结论：

1. **平台适配器未注册**：`platform` 对应的适配器实例不存在——事件根本没进框架。
2. **身份维度被作用域拒绝**：用户 / 会话 / Bot / 适配器被拉黑——事件在分发入口被完全丢弃。作用域配置见[模块配置](../user-guide/configuration.md)。
3. **模块被会话屏蔽**：区分当前会话 `available_modules`（可用）与 `blocked_modules`（被作用域屏蔽）。
4. **文本形如命令但未命中**：带命令前缀但不是任何注册命令——检查前缀配置与命令名。

入口检查全部通过仍无响应时，结论会指引继续检查两处：

- **处理器过滤条件**：`detail_type` / `pattern=` / `regex=` 等条件不满足；
- **中间件否决**：中间件显式返回 `False` 会在事件层面丢弃，并触发 `adapter.event.blocked` 生命周期钩子（携带中间件名与完整事件）——可注册该钩子审计"是谁丢弃了事件"。

## 场景三：命令没触发（分发决策链）

一条带前缀的消息要真正执行命令，需依次通过：命令文本判定 → 命令命中（未命中附拼写建议）→ 作用域 → 用户 ACL → 主人检查 → 权限函数 → 冷却 / 限流 / 用量静默丢弃 → 废弃拒绝与提示 → 参数解析 → 执行。框架把每个判定点记录为因果链，给出"为什么没触发"的结论。

### 测试中：TestBot.dispatch 返回 DispatchTrace

推荐用测试复现问题后直接读因果链（工具用法见[模块测试](testing.md)）：

```python
trace = await bot.dispatch(create_command_event("dailyx", user_id="123"))

trace.verdict          # executed / rejected / dropped / failed / no_match / passed
print(trace.explain()) # 逐行因果说明（当前语言）
trace.assert_no_match()
```

### 框架内置 trace 模块

决策链由 `ErisPulse.Core.Event.trace` 提供，默认**零开销**——未处于采集上下文时判定点直接跳过，生产路径无感知：

```python
from ErisPulse.Core.Event import (
    start_dispatch_trace,
    format_dispatch_trace,
    final_verdict,
)

with start_dispatch_trace() as records:
    ...  # 采集上下文内发生的分发（含其派生的处理器任务）

print(format_dispatch_trace(records))   # 人类可读因果链（当前语言）
print(final_verdict(records))           # 总结论
```

`final_verdict()` 的取值：

| 结论 | 含义 |
|------|------|
| `executed` | 命令已执行 |
| `rejected` | 被权限类判定拒绝（作用域 / ACL / 主人 / 权限函数） |
| `dropped` | 被静默丢弃（冷却 / 限流 / 用量 / 中间件否决） |
| `failed` | 执行出错 |
| `no_match` | 带前缀但未命中任何命令 |
| `passed` | 非命令文本，放行给消息处理器 |

记录为机器可读 dict（`stage` / `verdict` / `message_key` / `params`），自定义展示时可按 `stage` 过滤（如只看 `cooldown`）。

### 治理类静默命中的辨别

`cooldown=` / `rate_limit=` / `usage_limit=` 命中时**默认静默丢弃**（命令仍被认领，不漏给低优先级处理器），容易误判为"命令坏了"：现象是部分用户可用、部分用户无响应，且决策链中出现对应 `stage` 的 `dropped` 记录。`deprecated=` 命令则表现为调用时自动回复废弃文案（`deprecated_reject=True` 时拒绝执行）。

## 通用建议

- 排查前先把日志调到 `DEBUG` / `TRACE`（配置见[开发者指南](README.md#调试技巧)），可以看到模块加载、路由注册、事件分发等框架内部流程；
- `explain_module` / `explain_event` 随时可调、纯读无副作用，适合直接挂到运维命令或管理面板；
- "命令没触发"类问题优先写一个 `DispatchTrace` 断言测试复现——`assert_executed` / `assert_rejected` 等断言失败时会自动附上完整因果链。
