# `ErisPulse.CLI.commands.doctor` 模块

---

## 模块概述


Doctor 命令实现

运行环境诊断，输出 ErisPulse CLI 的 Python / 后端 / 配置 / 网络健康状态。

---

## 类列表


### `class DoctorCommand(Command)`

doctor 命令

诊断当前环境：Python 版本、安装后端（uv/pip）、目标解释器、
配置文件、PyPI 连通性与代理设置。


#### 方法列表


##### `__init__()`

初始化 DoctorCommand，创建包管理器实例

---


##### `_collect_diagnosis() -> tuple[list, bool, dict]`

运行全部诊断项并收集结果

**返回值**: ([tuple]) 三元组 ``(rows, failed, fix_context)``：

    rows 为 (状态, 标签, 详情) 行列表；failed 为是否存在失败项；
    fix_context 携带 ``--fix`` 所需的上下文（缺失配置路径、待完善
    目标列表、不可自动修复项提示）。

---


##### `_scan_config_pollution(config_path: Path) -> 'list[tuple[str, str, str]]'`

扫描历史升级遗留的配置污染（只读，不做任何修改）

两类已知模式：
1. **影子状态残留**（BUG-034 / #432 时代）：``ErisPulse.{modules,adapters}.status``
   下以 ``_shadow`` 结尾的键——运行时绑定曾以影子键落盘，现行版本已改
   用内存覆盖层，残留键只会误导排障
2. **游离配置节**（BUG-046 时代）：``ErisPulse.<X>`` 顶层嵌套节既不是
   框架自身节，也没有对应组件状态键——多由嵌套模板漂移把组件配置
   写到了错误层级产生

- **config_path** (`Path`): 配置文件路径

**返回值** (`(键路径, 来源 bug 标识, 一句话说明)`): 列表；无污染 / 文件不存在为空

---


##### `_fix_config_pollution(pollution: 'list[tuple[str, str, str]]') -> None`

清理历史配置污染（tomlclass 无损路径：注释/顺序/行尾逐字节保真）

- **pollution** (`list`): ``_scan_config_pollution`` 的发现列表

---


##### `_print_report(rows: list, failed: bool)`

输出诊断报告表格与失败项摘要

- **rows** (`list`): (状态, 标签, 详情) 行列表
- **failed** (`bool`): 是否存在失败项

---


##### `_attempt_fixes(fix_context: dict)`

对可自动修复的诊断失败项执行修复

修复范围：缺失的 ``config.toml``（与 init 建项同源生成）与"待完善"
组件配置（逐个拉起交互式向导）。Python 版本、网络连通等需人工
介入的项仅输出行动建议。修复动作逐项即时反馈，不在完成后重跑
全套诊断（避免重复网络探测）。

- **fix_context** (`dict`): ``_collect_diagnosis`` 返回的修复上下文

---


##### `_resolve_python_chain() -> 'list[tuple[str, str]]'`

**内部方法**
解释器解析决策链展示（逐级命中/未设置）

**返回值** (`(i18n 键, 详情)`): 列表

---


##### `_uv_project_rows() -> 'list[tuple[str, str, str]]'`

**内部方法**
uv 项目面板行：uv 版本 / UV_* 变量 / 项目判定依据

**返回值** (`(状态, 标签, 详情)`): 行列表

---


##### `_status(ok: bool) -> str`（staticmethod）

生成诊断项的状态标记文本（OK / FAIL，不使用 emoji）

- **ok** (`bool`): 诊断项是否正常

**返回值** (`str`): 带样式的状态标记文本

---

