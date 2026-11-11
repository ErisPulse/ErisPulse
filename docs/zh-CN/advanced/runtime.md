# runtime 工具带

> [!TIP]
> **什么时候需要读这篇**：想一站式了解 `ErisPulse.runtime` 包提供了哪些
> 可直接 import 的运行时工具时。各能力的详细用法在对应主题文档，本页是
> 速查索引 + 少量无主题归属能力的用法说明。

`ErisPulse.runtime` 是框架的聚合导出层：把散落在各模块的运行时工具收进
单一入口，脚本、模块、适配器代码统一 `from ErisPulse.runtime import X`
取用，不必记深层路径。

## 能力速查表

| 类别 | 名字 | 用途 | 详见 |
|------|------|------|------|
| 归属权 | `bind_owner` | 把 owner 上下文缝进回调 / 线程入口 | [归属权系统](ownership.md) |
| 归属权 | `owner_scope` / `get_current_owner` | 代码块级归属上下文 | [归属权系统](ownership.md) |
| 归属权 | `get_owner_tasks` / `cancel_owner_tasks` | 查询 / 取消某 owner 的后台任务 | [归属权系统](ownership.md) |
| 后台任务 | `spawn_background` / `spawn_later` / `spawn_thread` | 后台协程 / 延迟任务 / 线程任务 | [生命周期管理](lifecycle.md) |
| 后台任务 | `cancel_all_background_tasks` / `run_main_loop` | 后台任务收口与主循环注册 | [生命周期管理](lifecycle.md) |
| 事件上下文 | `get_current_trace_id` | 读取当前链路追踪 ID | [链路追踪](interaction.md#链路追踪trace-id) |
| 事件上下文 | `get_send_receipts` | 读取消息事务的发送回执账本 | [消息事务](interaction.md#消息事务message_tx) |
| 事件上下文 | `get_current_event_account` / `get_current_caller` / `get_handler_waits` | 事件账户 / 调用方 / 等待表读取 | [交互会话系统](interaction.md) |
| 内存 | `snapshot` / `log_snapshot` | 带 label 的 RSS + tracemalloc 快照（自动算增量） | [内存诊断](performance.md#内存诊断) |
| 内存 | `get_rss_mb` / `get_traced_mb` | 当前进程内存读数 | [内存诊断](performance.md#内存诊断) |
| 配置解析 | `dict_to_dataclass` | dict → 类型安全 dataclass 实例 | 见下节 |
| 配置解析 | `dataclass_to_defaults_dict` / `dataclass_to_toml_with_comments` | dataclass → 默认值 dict / 带 TOML 序列化 | [声明式配置](../developer-guide/configuration.md) |
| 排障 | `explain_module` / `explain_event` / `explain_trace` | 模块 / 事件 / 消息链路诊断 | [启动排查](startup.md) 与 [事件处理](../getting-started/event-handling.md) |
| 排障 | `format_diagnostic_block` / `log_diagnostic` / `extract_user_frame` | 异常诊断块渲染与用户帧提取 | [启动流程](startup.md) |
| 异常兜底 | `setup_exception_handling` / `global_exception_handler` | 全局异常处理器挂载 | [启动流程](startup.md) |
| 安全 | `redact_secret` | 日志 / 报告中的敏感值脱敏 | [启动流程](startup.md) |
| 指标 | `metrics` / `MetricsRegistry` | 运行指标注册表（`/metrics` 端点数据源） | [部署指南](../user-guide/deployment.md) |

## dict_to_dataclass：dict → 类型安全对象

声明式 dataclass 配置的"反方向"——把任意 dict（API 响应、webhook
payload、用户输入）按声明解析成类型安全实例，替代手写
`data.get("x", default)` 链：

```python
from dataclasses import dataclass, field
from ErisPulse.runtime import dict_to_dataclass

@dataclass
class WebhookPayload:
    order_id: str
    amount: float = 0.0
    tags: list = field(default_factory=list)
    remark: str = ""

payload = dict_to_dataclass(WebhookPayload, {
    "order_id": "A-1024",
    "amount": "99.5",          # str → float 自动转换
    "unknown_key": "忽略",      # 未声明字段自动忽略
})
payload.amount                   # 99.5（float）
```

- 类型转换（str → int/float 等）、默认值填充、嵌套 dataclass 递归填充
- 环境变量覆盖：字段 `metadata={"env": "NAME"}` 时优先级 环境变量 > 数据 > 默认值
- 声明式配置类（`ConfigClass` / `BaseConfig`）的热更新回调内部即由它完成
  dict → 配置对象的转换

## 相关文档

- [声明式配置](../developer-guide/configuration.md) - ConfigClass / BaseConfig 声明式配置
- [归属权（owner）系统](ownership.md) - 资源归属与自动回收
- [生命周期管理](lifecycle.md) - 后台任务与主循环
