# `ErisPulse.utils.package_manager` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse SDK 包管理器

提供包安装、卸载、升级和查询功能

---

## 类列表

### `class PackageManager`

    ErisPulse包管理器

提供包安装、卸载、升级和查询功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持本地和远程包管理
2. 包含1小时缓存机制</p></div>

    
#### 方法列表

##### `__init__()`

    初始化包管理器

    ---
    
##### async `async _fetch_remote_packages(url: str)`

    从指定URL获取远程包数据

:param url: 远程包数据URL
:return: 解析后的JSON数据，失败返回None

<dt>异常</dt><dd><code>ClientError</code> 网络请求失败时抛出</dd>
<dt>异常</dt><dd><code>JSONDecodeError</code> JSON解析失败时抛出</dd>

    ---
    
##### async `async get_remote_packages(force_refresh: bool = False)`

    获取远程包列表，带缓存机制

:param force_refresh: 是否强制刷新缓存
:return: 包含模块和适配器的字典

:return:
    dict: {
        "modules": {模块名: 模块信息},
        "adapters": {适配器名: 适配器信息},
        "cli_extensions": {扩展名: 扩展信息}
    }

    ---
    
##### `get_installed_packages()`

    获取已安装的包信息

:return: 已安装包字典，包含模块、适配器和CLI扩展

:return:
    dict: {
        "modules": {模块名: 模块信息},
        "adapters": {适配器名: 适配器信息},
        "cli_extensions": {扩展名: 扩展信息}
    }

    ---
    
##### `_is_module_enabled(module_name: str)`

    检查模块是否启用

:param module_name: 模块名称
:return: 模块是否启用

<dt>异常</dt><dd><code>ImportError</code> 核心模块不可用时抛出</dd>

    ---
    
##### `_normalize_name(name: str)`

    标准化包名，统一转为小写以实现大小写不敏感比较

:param name: 原始名称
:return: 标准化后的名称

    ---
    
##### async `async _find_package_by_alias(alias: str)`

    通过别名查找实际包名（大小写不敏感）

:param alias: 包别名
:return: 实际包名，未找到返回None

    ---
    
##### `_find_installed_package_by_name(name: str)`

    在已安装包中查找实际包名（大小写不敏感）

:param name: 包名或别名
:return: 实际包名，未找到返回None

    ---
    
##### `_run_pip_command_with_output(args: List[str], description: str)`

    执行pip命令并捕获输出

:param args: pip命令参数列表
:param description: 进度条描述
:return: (是否成功, 标准输出, 标准错误)

    ---
    
##### `_compare_versions(version1: str, version2: str)`

    比较两个版本号

:param version1: 版本号1
:param version2: 版本号2
:return: 1 if version1 > version2, -1 if version1 < version2, 0 if equal

    ---
    
##### `_check_sdk_compatibility(min_sdk_version: str)`

    检查SDK版本兼容性

:param min_sdk_version: 所需的最小SDK版本
:return: (是否兼容, 当前版本信息)

    ---
    
##### async `async _get_package_info(package_name: str)`

    获取包的详细信息（包括min_sdk_version等）

:param package_name: 包名或别名
:return: 包信息字典

    ---
    
##### `install_package(package_names: List[str], upgrade: bool = False, pre: bool = False)`

    安装指定包（支持多个包）

:param package_names: 要安装的包名或别名列表
:param upgrade: 是否升级已安装的包
:param pre: 是否包含预发布版本
:return: 安装是否成功

    ---
    
##### `uninstall_package(package_names: List[str])`

    卸载指定包（支持多个包，支持别名）

:param package_names: 要卸载的包名或别名列表
:return: 卸载是否成功

    ---
    
##### `upgrade_all()`

    升级所有已安装的ErisPulse包

:return: 升级是否成功

<dt>异常</dt><dd><code>KeyboardInterrupt</code> 用户取消操作时抛出</dd>

    ---
    
##### `upgrade_package(package_names: List[str], pre: bool = False)`

    升级指定包（支持多个包）

:param package_names: 要升级的包名或别名列表
:param pre: 是否包含预发布版本
:return: 升级是否成功

    ---
    
##### `search_package(query: str)`

    搜索包（本地和远程）

:param query: 搜索关键词
:return: 匹配的包信息

    ---
    
##### `get_installed_version()`

    获取当前安装的ErisPulse版本

:return: 当前版本号

    ---
    
##### async `async get_pypi_versions()`

    从PyPI获取ErisPulse的所有可用版本

:return: 版本信息列表

    ---
    
##### `_is_pre_release(version: str)`

    判断版本是否为预发布版本

:param version: 版本号
:return: 是否为预发布版本

    ---
    
##### `update_self(target_version: str = None, force: bool = False)`

    更新ErisPulse SDK本身

:param target_version: 目标版本号，None表示更新到最新版本
:param force: 是否强制更新
:return: 更新是否成功

    ---
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>