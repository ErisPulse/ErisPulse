# `ErisPulse.CLI.utils.package_manager` 模块

---

## 模块概述


ErisPulse SDK 包管理器

提供包安装、卸载、升级和查询功能

---

## 函数列表


### `_parse_version(version: str)`

将版本号解析为结构化组件（PEP 440 子集，纯标准库）。

与 :meth:`PackageManager._version_key` / :meth:`PackageManager._is_pre_release`
共用同一解析口径，避免不同正则导致判定分歧（如 ``1.0c2`` 此前在
``_is_pre_release`` 与 ``_version_key`` 间判定口径不一致）。

- **version** (`str`): 版本号字符串
**返回值** (`Optional[dict`): ] 含 epoch/release/pre_type/pre_num/post/local 的字典，
         无法解析时返回 None

---


## 类列表


### `class PackageManager`

ErisPulse包管理器

提供包安装、卸载、升级和查询功能

> **提示**
> 1. 支持本地和远程包管理
> 2. 包含1小时缓存机制


#### 方法列表


##### `_sanitize_proxy_url(url: str)`

对代理URL中的密码进行脱敏处理

- **url** (`str`): 原始代理URL
**返回值** (`str`): 密码被替换为 *** 的脱敏URL

---


##### `__init__()`

初始化包管理器，设置缓存、查找器、代理与 uv 相关状态

---


##### `_parse_size(size_str: str)`

将带单位的尺寸字符串解析为字节数

- **size_str** (`str`): 尺寸字符串，如 "10MB"
**返回值** (`float`): 对应的字节数，无法解析时返回 0

---


##### `_get_system_proxy()`

获取系统代理配置，优先读取环境变量，其次读取Windows注册表

**返回值** (`Optional[Dict[str, str`): ]] 代理配置字典，无代理时返回 None

---


##### `_parse_windows_proxy(proxy_server: str)`

解析Windows注册表中的代理服务器字符串为协议到URL的映射

- **proxy_server** (`str`): Windows代理服务器字符串
**返回值** (`Dict[str, str`): ] 协议到代理URL的映射

---


##### `_get_proxy_for_url(url: str)`

根据URL的协议获取对应的代理地址

- **url** (`str`): 目标URL
**返回值** (`Optional[str`): ] 对应的代理URL，无匹配代理时返回 None

---


##### `_build_subprocess_env()`

构建子进程环境变量，未设置时注入系统代理配置

**返回值** (`Dict[str, str`): ] 包含代理配置的环境变量字典

---


##### `_http_get(url: str, timeout: int = 15)`

发起HTTP GET请求并返回响应文本，自动应用系统代理

- **url** (`str`): 请求URL
- **timeout** (`int`): 超时时间(秒) (默认: 15)
**返回值** (`Optional[str`): ] 响应文本，请求失败时返回 None

---


##### `_fetch_remote_packages_sync(url: str)`

同步获取并解析远程包列表JSON

- **url** (`str`): 远程包列表URL
**返回值** (`Optional[dict`): ] 解析后的包列表字典，失败时返回 None

---


##### `async _fetch_remote_packages(url: str)`

异步获取远程包列表

- **url** (`str`): 远程包列表URL
**返回值** (`Optional[dict`): ] 解析后的包列表字典，失败时返回 None

---


##### `async get_remote_packages(force_refresh: bool = False)`

获取远程包列表，带缓存机制

- **force_refresh** (`bool`): 是否强制刷新缓存 (默认: False)
**返回值** (`dict`): 包含 modules 和 adapters 信息的字典

---


##### `get_installed_packages()`

获取已安装的模块和适配器信息

**返回值** (`Dict[str, Dict[str, Dict[str, str`): ]] 包含 modules 和 adapters 信息的字典

---


##### `_is_module_enabled(module_name: str)`

检查指定模块是否已启用

- **module_name** (`str`): 模块名称
**返回值** (`bool`): 模块已启用返回 True，无法判断时默认返回 True

---


##### `_normalize_name(name: str)`

将名称标准化为小写并去除首尾空白

- **name** (`str`): 原始名称
**返回值** (`str`): 标准化后的名称

---


##### `async _find_package_by_alias(alias: str)`

通过别名查找实际的包名，依次匹配已安装包和远程包

- **alias** (`str`): 别名或包名
**返回值** (`Optional[str`): ] 实际的包名，未找到时返回 None

---


##### `_find_installed_package_by_name(name: str)`

在已安装的模块和适配器中按名称查找实际包名

- **name** (`str`): 包名或别名
**返回值** (`Optional[str`): ] 已安装的实际包名，未找到时返回 None

---


##### `async check_package_updates()`

检查已安装包的可用更新

**返回值** (`Dict[str, Tuple[str, str`): ]] 包名到(当前版本, 最新版本)的映射

---


##### `_get_pypi_version_sync(package_name: str)`

同步从PyPI获取指定包的最新版本号

- **package_name** (`str`): 包名
**返回值** (`Optional[str`): ] 最新版本号，失败时返回 None

---


##### `async _get_pypi_package_version(package_name: str, force_refresh: bool = False)`

异步获取指定包的PyPI最新版本，带缓存机制

- **package_name** (`str`): 包名
- **force_refresh** (`bool`): 是否强制刷新缓存 (默认: False)
**返回值** (`Optional[str`): ] 最新版本号，失败时返回 None

---


##### `_is_uv_disabled()`

是否禁用 uv：CLI --no-uv 优先，其次环境变量 ERISPULSE_NO_UV

---


##### `_detect_uv()`

检测可用的 uv 命令。

优先使用 PATH 上的独立 uv 二进制（用户可能是全局安装，
而非作为 pip 包安装在当前环境），其次回退到 python -m uv。

**返回值** (`Optional[List[str`): ]] 形如 ["uv"] 或 [python, "-m", "uv"] 的命令前缀；未找到返回 None

---


##### `_get_uv_command()`

返回应使用的 uv 命令前缀。

当通过 --no-uv 禁用或 uv 不可用时返回 None。

**返回值** (`Optional[List[str`): ]] uv 命令前缀或 None

---


##### `_get_target_python()`

返回应当作为安装目标的 Python 解释器路径。

若用户激活了虚拟环境 (VIRTUAL_ENV) 但 epsdk 自身运行在别处
（例如通过 pipx 全局安装），则返回该虚拟环境的 Python，
以确保包安装到用户期望的环境中而非全局。

**返回值** (`str`): 目标 Python 解释器路径

---


##### `_execute_backend(base_cmd: list[str], args: list[str], description: str, backend: str)`

使用指定的后端 (uv/pip) 执行命令并实时输出到当前终端。

- **base_cmd** (`List[str`): ] 后端命令前缀，如 ["uv", "pip"] 或 [python, "-m", "pip"]
- **args** (`List[str`): ] 传递给后端的子命令与参数
- **description** (`str`): 展示给用户的操作描述
- **backend** (`str`): 后端名称 (uv/pip)，用于展示与错误提示
**返回值** (`bool`): 执行成功返回 True

---


##### `_build_install_command(package_spec: str, upgrade: bool = True)`

构建安装命令（uv 优先，回退 pip），供各安装场景复用。

策略：
1. 优先使用 uv（自动识别独立二进制或 python -m uv），
   并通过 ``--python`` 显式指定目标解释器，确保安装到用户期望的环境
   （特别是 epsdk 经 pipx 全局安装、用户包需装到项目 venv 的场景）；
2. uv 不可用时回退到 pip，目标 Python 解析为当前虚拟环境的解释器，
   避免安装到全局环境。

- **package_spec** (`str`): 包描述，如 "ErisPulse==1.0.0"
- **upgrade** (`bool`): 是否添加 --upgrade 参数 (默认: True)
**返回值** (`Tuple[List[str`): , str]] (完整安装命令列表, 后端名称 uv/pip)

---


##### `_run_pip_command_with_output(args: list[str], description: str)`

执行 pip 类操作 (install/uninstall)。

策略：
1. 优先使用 uv（自动识别独立二进制或 python -m uv）；
   通过 ``--python`` 显式指定目标解释器，确保安装到用户期望的环境
   （特别是 epsdk 经 pipx 全局安装、用户包需装到项目 venv 的场景）。
   install 子命令复用 :meth:`_build_install_command` 构建完整命令。
2. uv 不可用或执行失败时，回退到 pip，
   并将目标 Python 解析为当前虚拟环境的解释器，
   避免安装到全局环境。

- **args** (`List[str`): ] pip 子命令与参数，如 ["install", "--upgrade", pkg]
- **description** (`str`): 展示给用户的操作描述
**返回值** (`bool`): 执行成功返回 True

---


##### `_ensure_pip_available(target_python: str)`

确保目标 Python 环境可用 pip

uv 创建的 venv 默认不含 pip（uv 自身可装包）。当 uv 不可用或执行失败需
回退到 pip 时，必须先检测 pip 是否可用，否则会出现
“No module named pip” 的错误。这里通过 ``python -m ensurepip`` 自举安装。

- **target_python** (`str`): 目标 Python 解释器路径
**返回值** (`bool`): pip 可用返回 True，无法 bootstrap 返回 False

---


##### `_version_key(version: str)`

将版本号解析为可比较的元组键

遵循项目命名规则排序：正式版 > post > rc > beta > alpha > dev；
epoch 优先于一切 release 段；本地版本 (+local) 不影响主排序，
但同一版本号带 local 段者 > 不带 local 段者。
例如 2.4.5-dev.1 先于 2.4.5 正式版，1.0 < 1.0.post1 < 1.1。

- **version** (`str`): 版本号字符串
**返回值** (`tuple`): 可直接用于排序/比较的元组键

---


##### `_compare_versions(version1: str, version2: str)`

比较两个版本号的大小

- **version1** (`str`): 第一个版本号
- **version2** (`str`): 第二个版本号
**返回值** (`int`): version1 大于/等于/小于 version2 时分别返回 1/0/-1

---


##### `_check_sdk_compatibility(min_sdk_version: str)`

检查当前SDK版本是否满足最低版本要求

- **min_sdk_version** (`str`): 所需的最低SDK版本
**返回值** (`Tuple[bool, str`): ] (是否兼容, 提示信息)

---


##### `async _get_package_info(package_name: str)`

从远程包列表中获取指定包的详细信息

- **package_name** (`str`): 包名
**返回值** (`Optional[Dict[str, Any`): ]] 包信息字典，未找到时返回 None

---


##### `install_package(package_names: list[str], upgrade: bool = False, pre: bool = False, extra_pip_args: list[str] | None = None)`

安装一个或多个包，支持别名映射、未验证包确认和SDK兼容性检查

- **package_names** (`List[str`): ] 待安装的包名或别名列表
- **upgrade** (`bool`): 是否升级已安装的包 (默认: False)
- **pre** (`bool`): 是否允许预发布版本 (默认: False)
- **extra_pip_args** (`Optional[List[str`): ]] 附加的pip参数 (默认: None)
**返回值** (`bool`): 全部安装成功返回 True

---


##### `install_direct(pip_args: list[str], description: str = 'pip install')`

直接使用给定参数执行pip安装

- **pip_args** (`List[str`): ] pip install 的参数列表
- **description** (`str`): 展示给用户的操作描述 (默认: "pip install")
**返回值** (`bool`): 执行成功返回 True

---


##### `uninstall_package(package_names: list[str], skip_confirm: bool = False)`

卸载一个或多个包，支持别名映射和确认提示

- **package_names** (`List[str`): ] 待卸载的包名或别名列表
- **skip_confirm** (`bool`): 是否跳过确认提示 (默认: False)
**返回值** (`bool`): 全部卸载成功返回 True

---


##### `upgrade_all()`

检查并升级所有有可用更新的ErisPulse包

**返回值** (`bool`): 全部升级成功返回 True

---


##### `upgrade_package(package_names: list[str], pre: bool = False)`

升级指定包到最新版本

- **package_names** (`List[str`): ] 待升级的包名或别名列表
- **pre** (`bool`): 是否允许预发布版本 (默认: False)
**返回值** (`bool`): 全部升级成功返回 True

---


##### `search_package(query: str)`

在已安装和远程包中搜索匹配查询的包

- **query** (`str`): 搜索关键词
**返回值** (`Dict[str, List[Dict[str, str`): ]] 包含 installed 和 remote 匹配结果的字典

---


##### `get_installed_version()`

获取已安装的ErisPulse SDK版本号

**返回值** (`str`): SDK版本号，无法获取时返回 "unknown"

---


##### `_get_pypi_versions_sync()`

同步从PyPI获取ErisPulse的所有可用版本，按版本号降序排列

**返回值** (`List[Dict[str, Any`): ]] 版本信息列表，失败时返回空列表

---


##### `async get_pypi_versions()`

异步获取ErisPulse在PyPI上的所有可用版本

**返回值** (`List[Dict[str, Any`): ]] 版本信息列表，失败时返回空列表

---


##### `_is_pre_release(version: str)`

判断版本号是否为预发布版本

与 :meth:`_version_key` 复用同一解析口径（:func:`_parse_version`）：
仅当版本含预发布段 (dev/alpha/beta/rc/c/pre) 时返回 True；
post 版本 (1.0.post1) 与本地版本 (1.0+local) 不计为预发布。

- **version** (`str`): 版本号字符串
**返回值** (`bool`): 是预发布版本返回 True

---


##### `update_self(target_version: str | None = None, force: bool = False)`

更新ErisPulse SDK到指定版本或最新版本

- **target_version** (`Optional[str`): ] 目标版本号，为空则更新到最新版本 (默认: None)
- **force** (`bool`): 是否强制更新到当前已安装的目标版本 (默认: False)
**返回值** (`bool`): 更新成功返回 True

---

