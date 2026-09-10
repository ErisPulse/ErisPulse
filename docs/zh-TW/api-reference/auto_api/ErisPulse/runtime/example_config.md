# `ErisPulse.runtime.example_config` 模块

---

## 模块概述


config.full.example 完整配置参考生成器（runtime / CLI 共用）

框架运行（``sdk.run`` / ``epsdk run``）与 ``epsdk init`` 都通过本模块
生成 ``config/config.full.example``：静态框架配置段 + 已安装适配器/模块的
声明式配置段（含 ``example`` 字段），为用户提供完整配置参考。

文件自维护约定（首行标记控制刷新）：
- 首行为本模块写出的 ``gen=`` 标记行 → 每次框架启动检测到生成器版本变化时
  自动刷新（新增配置项 / 新装组件的配置段会补进来）
- 用户删除/改动首行标记 → 视为手动接管，框架不再触碰该文件

> **内部方法**

---

## 函数列表


### `_scaffold_text()`

获取文案工具实例（CLI 上下文；惰性导入避免拉高 CLI 包）

---


### `render_full_example(adapter_list = None, st = None)`

生成完整的配置示例文本

首行为自维护标记（供运行时按 gen 刷新判定）；其后为静态框架配置段
（文案跟随 CLI / Core 语言，缺失回退英文）与已安装组件声明式配置段。
无适配器列表时给出通用示例适配器注释。

- **adapter_list** (`适配器名称列表（``epsdk`): init`` 从商店抓取；None 用示例）
- **st** (`ScaffoldText`): 实例（None 时按当前语言构造）
**返回值**: 完整配置示例字符串

---


### `_component_sections(st)`

渲染已安装适配器/模块的声明式配置段（追加到 full.example 末尾）

复用配置向导的发现机制（entry-points + 本地插件目录），
对声明了 ConfigClass 的组件用 ``dataclass_to_toml_with_comments(include_example=True)``
渲染带注释模板——含 ``example`` 字段（这类字段不自动写入 config.toml，
仅记录在本示例文件中供用户按需启用）。

- **st** (`ScaffoldText`): 文案工具实例
**返回值**: 行列表（无已配置组件时为空）

---


### `ensure_full_example(config_dir: str | Path | None = None)`

确保 config.full.example 存在 / 随生成器版本刷新

- 文件不存在 → 生成（覆盖"直接 run / 未 init"用户没有配置参考的问题）
- 首行为本模块标记且 ``gen`` 与当前不一致 → 刷新（补新增配置项与组件段）
- 首行非本模块标记（用户手动接管）或 gen 一致 → 不触碰

- **config_dir** (`配置目录（None`): 时取 ``cwd/config``）
**返回值** (`被写入的路径；无需写入时返回`): None

---

