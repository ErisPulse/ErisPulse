# `ErisPulse.runtime.frame_config_schema` 模块

---

## 模块概述


ErisPulse 框架默认配置声明（``ErisPulse.framework`` 节唯一真相源）

默认值单源化：框架节的手写字典 / full.example 静态模板 / 文案表 /
文档表格全部从本声明派生（B1-4 逐步切换消费端）。运行时消费面不变——
:mod:`ErisPulse.runtime.frame_config` 用 :func:`dataclass_to_defaults_dict`
把声明折叠为字典默认值，合并快照 / env 覆盖 / 热更新机制照旧按字典工作。

声明类为裸 dataclass（不继承 Core.Bases 的 BaseConfig）：框架节默认值
折叠与模板渲染只依赖 ``fields()``，去基可让本模块在 Core 装配期内被
frame_config 惰性导入而不触发 Bases 包全量装配（无循环导入）。

description 使用 i18n 字典格式（``{"i18n": key, "default": 兜底文本}``）；
对应五语言翻译键在 B1-4 生成器切换批次随渲染面一并注册。

调优常量批次（B1-2）：``txn_*`` / ``sync_warn_cooldown`` / ``cross_receipt_window``
/ ``handler_slow_threshold`` 为第一批"立即生效"型——消费点运行时经
:func:`ErisPulse.runtime.frame_config.get_framework_value` 惰性读取，
Core/constants 同名常量保持为声明默认值（兼容直接引用方，不再新增）。

---

## 函数列表


### `_fold_defaults(config_class: type) -> dict[str, Any]`

把 dataclass 声明折叠为默认值字典（下划线前缀与 example 字段排除）

---


### `framework_defaults() -> dict[str, Any]`

FrameworkConfig 声明折叠（结果缓存）

本模块自带折叠、零 Core 依赖——供 frame_config 在 Core 装配窗口内
（Logger 构造触发快照构建）安全调用。

---


## 类列表


### `class StrictModeExceptionsConfig`

strict_mode 放行名单：名单内组件不参与严格模式校验


### `class StrictConfig`

严格模式作用域开关：按域开启严格校验（级别语义随 strict_mode）


### `class AutoReloadConfig`

已安装发行版热重载：来源包文件变化后自动重载对应模块 / 适配器（升级即生效）

监控范围 ACL（与 strict_mode_exceptions / watch_ignore_dirs 同族）：
deny 优先于 allow；allow 为空表示"除 deny 外全部已加载组件"。


### `class FrameworkConfig`

框架运行参数：加载行为、严格模式、性能与主动 GC、去重与多账户策略

