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


##### `_status(ok: bool)`

生成诊断项的状态标记文本（OK / FAIL，不使用 emoji）

- **ok** (`bool`): 诊断项是否正常
**返回值** (`str`): 带样式的状态标记文本

---

