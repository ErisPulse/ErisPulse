# `ErisPulse.CLI.commands.config` 模块

---

## 模块概述


Config 命令实现

交互式配置适配器/模块（schema 驱动向导，含适配器多账户管理）

---

## 类列表


### `class ConfigCommand(Command)`

config 命令

交互式配置适配器/模块；适配器支持多账户（bot 账户）管理


#### 方法列表


##### `_run_named(targets, name: str, config)`

按名称定位目标并直接进入向导

- **targets** (`ConfigTarget`): 列表
- **name** (`目标名（适配器平台名/模块名，或适配器配置键）`): - **config**: ConfigManager 实例

---


##### `_status_text(status: str)`

将状态常量渲染为带颜色的显示文本

- **status** (`get_target_status`): 返回的状态常量
**返回值** (`rich`): 标记的状态文本

---


##### `_print_status_table(targets, config)`

打印全部目标及其配置状态表

- **targets** (`ConfigTarget`): 列表
- **config** (`ConfigManager`): 实例

---


##### `_interactive_select(targets, config)`

交互式选择目标并进入向导（可连续配置多个）

- **targets** (`ConfigTarget`): 列表
- **config** (`ConfigManager`): 实例

---

