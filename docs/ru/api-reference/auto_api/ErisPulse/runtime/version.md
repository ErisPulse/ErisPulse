# `ErisPulse.runtime.version` 模块

---

## 模块概述


SDK 版本解析与比较

框架内唯一的版本号解析/比较实现（PEP 440 子集，纯标准库，不依赖 packaging），
供加载器在组件加载时执行运行时最低 SDK 版本检查
（组件以 ``get_meta().min_sdk_version`` 或类属性 ``min_sdk_version`` 声明），
CLI 包管理器（``CLI/utils/package_manager.py``）亦复用同一解析口径。

> **提示**
> 1. 组件声明 ``min_sdk_version = "2.8.1"`` 后，SDK 低于该版本时加载期将被明确报错并跳过
> 2. 未声明、当前版本未知或任一侧无法解析时一律放行——版本检查绝不阻塞框架启动

---

## 函数列表


### `parse_version(version: str)`

将版本号解析为结构化组件（PEP 440 子集，纯标准库）

- **version** (`str`): 版本号字符串
**返回值** (`dict`): 含 epoch/release/pre_type/pre_num/post/local 的字典，
         无法解析时返回 None

---


### `version_key(version: str)`

将版本号解析为可比较的元组键

遵循项目命名规则排序：正式版 > post > rc > beta > alpha > dev；
epoch 优先于一切 release 段；本地版本 (+local) 不影响主排序，
但同一版本号带 local 段者 > 不带 local 段者。
例如 2.4.5-dev.1 先于 2.4.5 正式版，1.0 < 1.0.post1 < 1.1。

- **version** (`str`): 版本号字符串
**返回值** (`tuple`): 逐段可比较的比较键元组

---


### `compare_versions(version_a: str, version_b: str)`

比较两个版本号

- **version_a** (`str`): 版本号 A
- **version_b** (`str`): 版本号 B
**返回值** (`int`): A < B 返回负数，相等返回 0，A > B 返回正数；
         任一侧无法解析时退化为字符串比较，保证不抛异常

---


### `check_min_sdk_version(min_required: str)`

检查当前 SDK 版本是否满足组件声明的最低版本要求

- **min_required** (`str`): 组件声明的最低 SDK 版本（如 ``"2.8.1"``）
**返回值** (`tuple[bool,`): str, str, bool]
    (是否满足, 当前 SDK 版本, 规范化后的要求版本, 声明是否可解析)；
    声明为空、当前版本未知或声明无法解析时视为满足
    （放行，解析标记为 False），版本检查绝不阻塞框架启动

---


### `_get_sdk_version()`

获取当前安装的 ErisPulse SDK 版本

经包元数据读取（与 :data:`ErisPulse.__version__` 同源），避免依赖根包导入。

**返回值** (`str`): 版本号；元数据不可用时返回 "unknown"

---

