# `ErisPulse.utils.cli` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


该模块暂无概述信息。

---

## 类列表

### `class CommandHighlighter(RegexHighlighter)`

    高亮CLI命令和参数

<div class='admonition tip'><p class='admonition-title'>提示</p><p>使用正则表达式匹配命令行参数和选项</p></div>

    
### `class CLI`

    ErisPulse命令行接口

提供完整的命令行交互功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持动态加载第三方命令
2. 支持模块化子命令系统</p></div>

    
#### 方法列表

##### `__init__()`

    初始化CLI

    ---
    
##### `_create_parser()`

    创建命令行参数解析器

:return: 配置好的ArgumentParser实例

    ---
    
##### `_get_external_commands()`

    获取所有已注册的第三方命令名称

:return: 第三方命令名称列表

    ---
    
##### `_load_external_commands(subparsers)`

    加载第三方CLI命令

:param subparsers: 子命令解析器

<dt>异常</dt><dd><code>ImportError</code> 加载命令失败时抛出</dd>

    ---
    
##### `_print_version()`

    打印版本信息

    ---
    
##### `_print_installed_packages(pkg_type: str, outdated_only: bool = False)`

    打印已安装包信息

:param pkg_type: 包类型 (modules/adapters/cli/all)
:param outdated_only: 是否只显示可升级的包

    ---
    
##### `_print_remote_packages(pkg_type: str)`

    打印远程包信息

:param pkg_type: 包类型 (modules/adapters/cli/all)

    ---
    
##### `_is_package_outdated(package_name: str, current_version: str)`

    检查包是否过时

:param package_name: 包名
:param current_version: 当前版本
:return: 是否有新版本可用

    ---
    
##### `_resolve_package_name(short_name: str)`

    解析简称到完整包名（大小写不敏感）

:param short_name: 模块/适配器简称
:return: 完整包名，未找到返回None

    ---
    
##### `_print_search_results(query: str, results: Dict[str, List[Dict[str, str]]])`

    打印搜索结果

:param query: 搜索关键词
:param results: 搜索结果

    ---
    
##### `_print_version_list(versions: List[Dict[str, Any]], include_pre: bool = False)`

    打印版本列表

:param versions: 版本信息列表
:param include_pre: 是否包含预发布版本

    ---
    
##### `_setup_watchdog(script_path: str, reload_mode: bool)`

    设置文件监控

:param script_path: 要监控的脚本路径
:param reload_mode: 是否启用重载模式

    ---
    
##### `_cleanup()`

    清理资源

    ---
    
##### `run()`

    运行CLI

<dt>异常</dt><dd><code>KeyboardInterrupt</code> 用户中断时抛出</dd>
<dt>异常</dt><dd><code>Exception</code> 命令执行失败时抛出</dd>

    ---
    
##### `_cleanup_adapters()`

    清理适配器资源

    ---
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>