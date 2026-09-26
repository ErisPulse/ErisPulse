# `ErisPulse.Core.ownership` 模块

---

## 模块概述


ErisPulse 归属权统一门面

归属权（owner）系统对外的统一入口。框架各子系统（路由 / 处理器 / 命令 /
任务 / 覆写 / 生命周期 / 主人身份源……）各自维护按 owner 注册的资源，
本模块把它们聚合为四个动词，替代散落在各子系统上形态不一的清理与查询 API：

- :func:`ownership.reclaim` / :func:`ownership.reclaim_sync` —— 统一注销
  owner 名下的全部资源（模块卸载 / 禁用 / 失败回滚共用的回收路径）
- :func:`ownership.counts` —— 按 owner 统计在册资源（审计的计数面）
- :func:`ownership.orphans` —— 孤儿扫描：资源在册而 owner 已注销（泄漏实锤）
- :func:`ownership.audit` —— 泄漏审计（计数 + 孤儿 + 可选 gc 实例普查）

各子系统既有的 ``*_by_owner`` 注销函数保持不变，作为本门面的内部 SPI；
新增可回收资源时，子系统提供注销函数并登记进 :func:`reclaim_sync` 的
步骤表、在 :func:`counts` 提供只读计数，门面与审计器即自动覆盖。

> **提示**
> 1. reclaim 的注销顺序固定（归属任务 / 外部清理钩子先行，注册类资源随后），
> 每步独立容错——单步失败不阻断其余回收（与卸载流程兜底风格一致）
> 2. counts / orphans 只读，无任何清理副作用
> 3. audit(deep=True) 会 ``gc.collect()`` 并做 weakref 实例存活普查——存在
> 全局暂停开销，仅显式调用（``epsdk audit --deep``）

---

## 类列表


### `class OwnershipManager`

归属权管理器（单例）

聚合各子系统的 owner 归属资源：统一注销（reclaim）、只读计数（counts）、
孤儿扫描（orphans）、泄漏审计（audit），以及影子 owner 判定面
（is_shadow / register_shadow / unregister_shadow——影子模块机制，
见 ``Core/shadow`` 与 docs/zh-CN/advanced/shadow.md）。
子系统内部表通过惰性导入访问，避免加载链耦合（与 module.py 清理链的
既有风格一致）。


#### 方法列表


##### `register_shadow(owner: str)`

登记影子 owner（ShadowManager 装配影子模块时调用）

- **owner** (`影子`): owner 名（如 ``"roll_shadow"``）

---


##### `unregister_shadow(owner: str)`

移除影子 owner 登记（影子转正 / 放弃时调用）

- **owner** (`影子`): owner 名

---


##### `is_shadow(owner: 'str | None')`

判定 owner 是否为影子模块 owner（八道隔离闸的统一判定入口）

- **owner** (`owner`): 名
**返回值** (`是否为已登记的影子`): owner

---


##### `shadow_owners()`

当前全部影子 owner（只读视图）

**返回值** (`影子`): owner 名集合

---


##### `async reclaim(owner: str)`

统一注销 owner 名下的全部资源（异步完整版）

顺序：取消归属后台任务 → 触发外部清理钩子（on_cleanup）→ 注销全部
注册类资源。模块卸载 / 禁用的标准回收路径。

- **owner** (`owner`): 名（模块名或适配器平台名）
**返回值** (`各类资源注销数量（键见`): :meth:`reclaim_sync`，另含
         ``tasks_cancelled`` / ``cleanups_run``）

**示例**:
```python
>>> from ErisPulse.Core import ownership
>>> await ownership.reclaim("roll")
```

---


##### `async reclaim_tasks(owner: str)`

注销 owner 的进行中工作：归属后台任务取消 + 外部清理钩子触发

- **owner** (`owner`): 名
**返回值** (`{"tasks_cancelled":`): int, "cleanups_run": int}

---


##### `reclaim_sync(owner: str)`

注销 owner 的全部注册类资源（同步版，不含任务取消）

涵盖：i18n 翻译域、路由（命名空间 + owner 兜底）、适配器事件处理器、
自定义会话类型、平台事件方法注入、事件覆写、scope 覆写、命令与
四类事件处理器、交互会话等待、主人身份源、生命周期钩子。
每步独立容错，单步失败不阻断后续回收。

- **owner** (`owner`): 名（模块名或适配器平台名）
**返回值** (`各类资源注销数量`): 
**示例**:
```python
>>> ownership.reclaim_sync("roll")
{"routes_http": 2, "commands": 1, ...}
```

---


##### `counts(owner: 'str | None' = None)`

统计 owner 在册的归属资源（只读，无副作用）

- **owner** (`owner`): 名；None 时返回全部 owner 的计数
**返回值** (```owner```): 给定时为 {资源类: 数量}；None 时为
         {owner: {资源类: 数量}}（未挂任何资源的 owner 不出现）

**示例**:
```python
>>> ownership.counts("roll")
{"commands": 1, "lifecycle_hooks": 2}
```

---


##### `orphans()`

孤儿 owner 扫描：资源仍在册、而 owner（模块 / 适配器）已注销

这是资源泄漏的实锤信号——清理链对"有注册存根的 owner"生效，
孤儿资源（如工具模块私有容器持有的句柄、第三方库内部的引用）
框架无法自动回收，但本扫描让它们**可见**。

**返回值** (`{"owner": str, "total": int, "resources": {资源类: 数量}}, ...`): 按 owner 名排序；无孤儿时为空列表

**示例**:
```python
>>> from ErisPulse.Core import ownership
>>> ownership.orphans()
[{"owner": "ghost_module", "total": 2, "resources": {"commands": 1, ...}}]
```

---


##### `audit(owner: 'str | None' = None, deep: bool = False)`

泄漏审计：计数 + 孤儿扫描（+ 可选 gc 实例普查）

- **owner** (`目标`): owner（模块名）；None 时审计全局（全部 owner 计数）
- **deep** (`对模块实例做`): weakref 存活普查——``gc.collect()`` 后检查
             实例是否可回收，不可回收时给出引用方类型（有全局暂停
             开销，仅显式使用）
**返回值** (`审计报告`): dict（owner / counts / orphans / 深普查结果）

**示例**:
```python
>>> ownership.audit("roll", deep=True)
{"owner": "roll", "counts": {...}, "orphans": [], "instance_recyclable": True}
```

---

