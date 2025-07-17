# 📦 `ErisPulse.__main__` 模块

*自动生成于 2025-07-17 16:39:14*

---

## 模块概述

# CLI 入口

提供命令行界面(CLI)用于包管理和启动入口。

## 主要命令
### 包管理:
    install: 安装模块/适配器包
    uninstall: 卸载模块/适配器包
    list: 列出已安装的模块/适配器
    list-remote: 列出远程PyPI上的ErisPulse模块和适配器
    upgrade: 升级所有模块/适配器

### 启动:
    run: 运行脚本
    --reload: 启用热重载

### 示例用法:
```
# 安装模块
epsdk install Yunhu

# 启用热重载
epsdk run main.py --reload
```

---

## 🛠️ 函数

### `start_reloader`

启动热重载监控

:param script_path: str 要监控的脚本路径

💡 **提示**：

1. 监控脚本所在目录和modules目录
2. 按Ctrl+C可停止监控

---

### `run_script`

运行指定脚本

:param script_path: str 要运行的脚本路径
:param reload: bool 是否启用热重载 (默认: False)

⚠️ **可能抛出**: `FileNotFoundError` - 当脚本不存在时抛出

---

### `get_erispulse_version`

获取当前安装的ErisPulse版本

:return: str ErisPulse版本号或"unknown version"

---

### `main`

CLI主入口

解析命令行参数并执行相应命令

💡 **提示**：

1. 使用argparse处理命令行参数
2. 支持彩色输出和表格显示
3. 提供详细的错误处理

---

## 🏛️ 类

### `PyPIManager`

PyPI包管理器

负责与PyPI交互，包括搜索、安装、卸载和升级ErisPulse模块/适配器

💡 **提示**：

1. 支持多个远程源作为备份
2. 自动区分模块和适配器
3. 提供详细的错误处理


#### 🧰 方法

##### 🔹 `async` `get_remote_packages`

获取远程包列表

从配置的远程源获取所有可用的ErisPulse模块和适配器

:return: 
    Dict[str, Dict]: 包含模块和适配器的字典
        - modules: 模块字典 {模块名: 模块信息}
        - adapters: 适配器字典 {适配器名: 适配器信息}
        
⚠️ **可能抛出**: `ClientError` - 当网络请求失败时抛出
:raises asyncio.TimeoutError: 当请求超时时抛出

---

##### `get_installed_packages`

获取已安装的包信息

:return: 
    Dict[str, Dict[str, Dict[str, str]]]: 已安装包字典
        - modules: 已安装模块 {模块名: 模块信息}
        - adapters: 已安装适配器 {适配器名: 适配器信息}

---

##### `install_package`

安装指定包

:param package_name: str 要安装的包名
:param upgrade: bool 是否升级已安装的包 (默认: False)
:return: bool 安装是否成功

---

##### `uninstall_package`

卸载指定包

:param package_name: str 要卸载的包名
:return: bool 卸载是否成功

---

##### `upgrade_all`

升级所有已安装的ErisPulse包

:return: bool 升级是否成功

💡 **提示**：

1. 会先列出所有可升级的包
2. 需要用户确认才会执行升级

---

### `ReloadHandler`

热重载处理器

监控文件变化并自动重启脚本

💡 **提示**：

1. 基于watchdog实现文件监控
2. 有1秒的防抖延迟
3. 会终止旧进程并启动新进程


#### 🧰 方法

##### `start_process`

启动/重启被监控的进程

⚠️ **内部方法**：

---

##### `on_modified`

文件修改事件处理

:param event: FileSystemEvent 文件系统事件对象

---


*文档最后更新于 2025-07-17 16:39:14*