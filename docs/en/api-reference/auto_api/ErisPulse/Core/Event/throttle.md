# `ErisPulse.Core.Event.throttle` 模块

---

## 模块概述


事件处理器节流（throttle=，EPRFC-2026-001 方向八）

同一键（用户 / 会话 / 全局）上的事件在最小间隔内只放行一条，其余静默
丢弃——手写防刷屏逻辑的声明式替代。实现为既有处理器条件机制上的框架
包装器：装饰器注册期生成一个条件函数，与其它条件（detail_type /
pattern / regex）组合。

> **提示**
> 1. 时长语法与命令 ``cooldown=`` / ``args=`` duration 一致（``2s`` / ``1h30m``）
> 2. 节流状态存放于条件闭包内，处理器注销后随闭包被 GC 自动回收
> 3. 命中丢弃仅输出 TRACE 日志（对称于作用域静默）

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

