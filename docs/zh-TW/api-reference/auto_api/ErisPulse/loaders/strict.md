# `ErisPulse.loaders.strict` 模块

---

## 模块概述


ErisPulse 严格模式

提供统一的模块/适配器加载合规性管理。

> **提示**
> 1. 通过 ErisPulse.framework.strict_mode 配置级别（0=宽松(默认), 1=跳过, 2=致命）
> 2. 通过 ErisPulse.framework.strict_mode_exceptions 配置豁免清单
> 3. StrictModeManager 由初始化协调器创建并注入到各加载器，确保跨加载器收集违规

---

## 类列表


### `class StrictModeLevel(IntEnum)`

严格模式级别

> **内部方法** 
内部枚举，对应配置中的 strict_mode 数值


### `class StrictModeError(Exception)`

严格模式致命错误

当严格模式级别为 2（致命）且检测到违规时，在检查点抛出此异常，
用于中止整个启动流程。

> **提示**
> 此异常不应被加载器捕获吞掉，应向上传播至初始化协调器


### `class Violation`

单条违规记录

:param name: 组件名称（entry-point name）
:param component_type: 组件类型，"module" 或 "adapter"
:param reason: 违规原因标识，如 "not_base_class", "load_failed",
    "register_failed", "init_failed", "invalid_name"
:param detail: 可选的详细描述


### `class StrictModeManager`

严格模式管理器

统一处理模块/适配器加载过程中的合规性判定与违规收集。

> **提示**
> 使用方式：
> >>> manager = StrictModeManager.from_config()
> >>> # 未继承基类时判定是否拒绝
> >>> if manager.decide(name, "module", "not_base_class"):
> ...     # 跳过该模块
> ...     pass
> >>> # 异常类失败仅记录（调用方已自行跳过）
> >>> manager.record_failure(name, "module", "load_failed", detail=str(e))
> >>> # 在检查点统一抛出致命错误
> >>> manager.raise_if_fatal()


#### 方法列表


##### `__post_init__()`

初始化豁免集合，便于快速查找

---


##### `from_config()`

从框架配置创建管理器实例

:return: 配置好的管理器实例；读取配置失败时回退到默认值

> **内部方法** 
由初始化协调器调用，读取 ErisPulse.framework.strict_mode 及豁免清单

---


##### `is_exempt(name: str, component_type: str)`

判断组件是否在豁免清单中

:param name: 组件名称
:param component_type: 组件类型
:return: 是否豁免

---


##### `decide(name: str, component_type: str, reason: str)`

报告一次可"容忍或拒绝"的违规，并返回处置决定

主要用于"未继承基类"这类违规：在宽松级别下可容忍继续加载，
在严格级别下应拒绝（跳过）。

:param name: 组件名称
:param component_type: 组件类型
:param reason: 违规原因标识
:return: True 表示应拒绝（跳过）该组件；False 表示应容忍（继续加载）

> **内部方法** 
在致命级别下，非豁免违规会同时被记录，待检查点统一抛出

---


##### `record_failure(name: str, component_type: str, reason: str, detail: str = '')`

记录一次异常类失败

与 decide 不同，此方法假定调用方已自行跳过该组件（例如捕获了异常）。
被拒绝的组件会记入 _rejections（与级别无关，用于摘要展示）；
仅在致命级别下额外记入 _violations，以便检查点统一报告并中止。

:param name: 组件名称
:param component_type: 组件类型
:param reason: 违规原因标识
:param detail: 详细描述（如异常信息）

> **内部方法** 
调用方应同时输出自己的具体错误日志，此方法不重复输出

---


##### `has_fatal_violations()`

是否存在致命级别的违规

:return: 当前为致命级别且已收集到违规时返回 True

---


##### `violations()`

已收集的致命违规列表（只读视图）

---


##### `rejections()`

被拒绝/跳过的组件列表（只读视图，与级别无关，用于摘要展示）

---


##### `raise_if_fatal()`

在检查点统一报告并抛出致命错误

当处于致命级别且收集到违规时，先打印完整违规清单，再抛出
StrictModeError 中止启动。无致命违规时直接返回。

**异常**: `StrictModeError` - 存在致命违规时抛出

---

