# 📦 `ErisPulse.__main__` 模块

*自动生成于 2025-07-19 19:31:39*

---

## 🛠️ 函数

### `start_reloader`

启动热重载监控

:param script_path: str 要监控的脚本路径
:param reload_mode: bool 是否启用完整重载模式 (默认: False)

---

### `get_erispulse_version`

获取当前安装的ErisPulse版本

:return: str ErisPulse版本号或"unknown version"

---

### `main`

CLI主入口

解析命令行参数并执行相应命令

---

## 🏛️ 类

### `PyPIManager`

PyPI包管理器

负责与PyPI交互，包括搜索、安装、卸载和升级ErisPulse模块/适配器


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

##### `uv_install_package`

优先使用uv安装包

:param package_name: str 要安装的包名
:param upgrade: bool 是否升级已安装的包 (默认: False)
:return: bool 安装是否成功

---

##### `install_package`

安装指定包 (修改后优先尝试uv)

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

---

### `ReloadHandler`

热重载处理器

监控文件变化并自动重启脚本


#### 🧰 方法

##### `start_process`

启动/重启被监控的进程

---

##### `on_modified`

文件修改事件处理

:param event: FileSystemEvent 文件系统事件对象

---


*文档最后更新于 2025-07-19 19:31:39*