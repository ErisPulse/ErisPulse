# `ErisPulse.Core.Event.governance` 模块

---

## 模块概述


ErisPulse 命令治理模块

命令治理（EPRFC-2026-001 方向七）的声明解析与运行时判定，自 CommandHandler 拆分：
注册期解析（parse_rate_limit / parse_usage / usage_period_key）、冷却作用域键计算，
以及分发期三段判定——冷却（cooldown=）/ 滑动窗口限流（rate_limit=）/ 自然周期配额
（usage_limit=）。状态表由 :class:`GovernanceGate` 持有，CommandHandler 以组合方式
挂载并经同名 property 透出，既有访问路径不变。

> **提示**
> 1. 注册期：parse_rate_limit("5/minute") / parse_usage("3/day") 解析声明（fail-fast）
> 2. 分发期：gate.check_cooldown / check_rate_limit / check_usage 返回 True 即已拦截（静默或已回复）
> 3. 键粒度白名单复用 ``constants.GOVERNANCE_KEY_KINDS``（与 throttle 共用，本模块不重复定义）

---

## 函数列表


### `parse_rate_limit(spec: str)`

解析限流声明（如 ``"5/minute"``、``"10/s"``）为 (次数, 窗口秒)

滑动窗口语义：窗口内至多放行 ``次数`` 次，超出静默丢弃。单位支持
second / minute / hour / day（含单字母缩写与可选数值前缀，大小写不敏感）。

- **spec** (`限流声明字符串`): **返回值** (`(limit,`): window_seconds)
**异常**: `ValueError` - 语法非法或数值非正时

---


### `parse_usage(spec: str)`

解析配额声明（如 ``"3/day"``）为 (次数, 周期单位)

自然周期语义：周期边界对齐本地时区的自然分钟 / 小时 / 日（如 day 为
当日 00:00 起，次日自动重置），与 :func:`parse_rate_limit` 的滑动窗口
相区分（rate_limit 防瞬时刷屏，usage_limit 管业务配额）。

- **spec** (`配额声明字符串`): **返回值** (`(limit,`): unit)；语法非法时返回错误描述字符串（调用方包装 ValueError）

---


### `usage_period_key(unit: str)`

计算当前自然周期的标识键（本地时区）

> **内部方法**
供分发期配额判定使用；周期切换键随之变化即自动重置

- **unit** (`周期单位（minute`): / hour / day）
**返回值** (`周期键（如`): ``"2026-09-21"``）

---


### `cooldown_scope_key(kind: str, event: 'Event')`

> **内部方法**
计算冷却作用域键（复用 ``platform:bot:目标`` 会话键体系）

- **kind** (`粒度（user`): / session / global，注册期已校验）
- **event** (`事件数据`): **返回值**: 作用域键字符串

---


## 类列表


### `class GovernanceGate`

命令治理状态与判定

持有冷却 / 限流 / 配额三张进程内状态表，提供分发期三段判定与生命周期清理。
由 CommandHandler 组合持有（``self._gate``），状态表经其同名 property 透出。

> **内部方法**
判定均位于全部权限检查与参数解析通过之后、实际执行之前：
无权限用户不触发计时，参数错误不消耗；命中默认静默丢弃
（命令已认领，不漏给低优先级消息处理器），声明了 ``*_reply=`` 时回复。


#### 方法列表


##### `clear_command(main_name: str)`

> **内部方法**
按命令主名前缀清理三张状态表（模块卸载自动清理）

- **main_name**: 命令主名

---


##### `clear_all()`

> **内部方法** 清空全部治理状态（_clear_commands 调用）

---


##### `async check_cooldown(main_name: str, actual_cmd_name: str, effective: dict[str, Any], event: 'Event', send_reply: Any)`

> **内部方法**
冷却判定（cooldown=）：执行前即开始计时，实际冷却窗口不受处理耗时影响

- **main_name** (`命令主名（状态表键前缀）`): - **actual_cmd_name**: 实际调用的命令名（日志 / trace 展示）
- **effective** (`合并覆写后的命令生效参数`): - **event**: 事件数据
- **send_reply** (`回复回调（``await`): send_reply(event, text)``）
**返回值** (`True`): 表示已拦截（静默丢弃或已回复）

---


##### `async check_rate_limit(main_name: str, actual_cmd_name: str, effective: dict[str, Any], event: 'Event', send_reply: Any)`

> **内部方法**
限流判定（rate_limit=，滑动窗口）：与冷却同位次序——权限与参数通过后、
实际执行前计数；窗口满时默认静默丢弃（可选回复）

- **main_name** (`命令主名（状态表键前缀）`): - **actual_cmd_name**: 实际调用的命令名（日志 / trace 展示）
- **effective** (`合并覆写后的命令生效参数`): - **event**: 事件数据
- **send_reply** (`回复回调（``await`): send_reply(event, text)``）
**返回值** (`True`): 表示已拦截（静默丢弃或已回复）

---


##### `async check_usage(main_name: str, actual_cmd_name: str, effective: dict[str, Any], event: 'Event', send_reply: Any)`

> **内部方法**
配额判定（usage=，自然周期）：与限流同位次序；计数经 storage KV
持久化（重启不丢），存储异常时回退进程内内存计数（不阻塞命令）

- **main_name** (`命令主名（状态表键前缀）`): - **actual_cmd_name**: 实际调用的命令名（日志 / trace 展示）
- **effective** (`合并覆写后的命令生效参数`): - **event**: 事件数据
- **send_reply** (`回复回调（``await`): send_reply(event, text)``）
**返回值** (`True`): 表示已拦截（静默丢弃或已回复）

---

