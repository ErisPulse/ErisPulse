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


##### `_status(ok: bool) -> str`（staticmethod）

生成诊断项的状态标记文本（OK / FAIL，不使用 emoji）

- **ok** (`bool`): 诊断项是否正常

**返回值** (`str`): 带样式的状态标记文本

---

