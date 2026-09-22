# `ErisPulse.Core.Event.throttle` 模块

---

## 模块概述


事件处理器节流（throttle=）与防抖（debounce=，EPRFC-2026-001 方向八）

同一键（用户 / 会话 / 全局）上的事件在最小间隔内只放行一条，其余静默
丢弃（throttle）；或窗口内只执行最后一条、取消前序（debounce）——手写
防刷屏 / 防抖逻辑的声明式替代。

> **提示**
> 1. throttle 实现为处理器条件机制上的框架包装器（条件函数与 detail_type /
> pattern / regex 组合）；debounce 实现为处理器调用包装器（窗口内新事件
> 取消前序的待执行任务）
> 2. 时长语法与命令 ``cooldown=`` / ``args=`` duration 一致（``2s`` / ``1h30m``）
> 3. throttle 状态存放于条件闭包内，处理器注销后随闭包被 GC 自动回收；
> debounce 的待执行任务随闭包存活，模块卸载后至多一个窗口期内自然结束
> 4. throttle 命中丢弃仅输出 TRACE 日志（对称于作用域静默）

---

## 函数列表


### `_scope_key(kind: str, event: Any)`

计算节流作用域键（复用 ``platform:bot:目标`` 会话键体系）

- **kind** (`粒度（user`): / session / global，装饰期已校验）
- **event** (`事件数据（Event`): 包装或原始 dict 均可）
**返回值**: 作用域键字符串

---


### `make_throttle_condition(throttle: str, throttle_key: str = 'user', handler_name: str = '')`

构造节流条件函数（处理器条件机制的包装器）

- **throttle** (`节流间隔声明（如`): ``"2s"`` / ``"1h30m"``，与 duration 语法一致）
- **throttle_key** (`键粒度：``user``（默认）/`): ``session`` / ``global``
- **handler_name** (`处理器名（TRACE`): 日志展示用）
**返回值** (`条件函数——间隔已过返回`): True（放行并刷新时间戳），
    间隔内返回 False（处理器被跳过，事件静默丢弃）
**异常**: `ValueError` - 声明非法（时长语法 / 粒度白名单）时装饰期抛出

---


### `make_debounce_wrapper(func: Callable, debounce: str, debounce_key: str = 'user', handler_name: str = '')`

构造防抖调用包装器（窗口内同键事件只执行最后一条）

事件到达时取消同键前序的待执行任务，重新计时；窗口耗尽后才真正执行
最后一条事件的处理。``functools.wraps`` 保留原签名（``__wrapped__``），
使注册期 ``extract_depends`` 仍能从原函数提取 Depends 声明。

- **func** (`原事件处理器（async）`): - **debounce**: 防抖窗口声明（如 ``"2s"``，duration 语法）
- **debounce_key** (`键粒度：``user``（默认）/`): ``session`` / ``global``
- **handler_name** (`处理器名（日志展示用）`): **返回值** (`async`): 包装器——立即返回，真实执行延迟到窗口耗尽
**异常**: `ValueError` - 声明非法（时长语法 / 粒度白名单）时装饰期抛出

---

