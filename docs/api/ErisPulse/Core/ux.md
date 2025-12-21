# `ErisPulse.Core.ux` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse UX优化模块

提供更友好的初始化和API接口，简化常用操作

---

## 类列表

### `class UXManager`

    UX优化管理器

提供用户友好的界面和简化操作

    
#### 方法列表

##### async `async _fetch_available_adapters()`

    从云端获取可用适配器列表

:return: 适配器名称到描述的映射

    ---
    
##### `welcome(version: str = None)`

    显示欢迎信息

:param version: 框架版本号

    ---
    
##### `show_status()`

    显示系统状态概览

    ---
    
##### `list_modules(detailed: bool = False)`

    列出所有模块状态

:param detailed: 是否显示详细信息

    ---
    
##### `list_adapters(detailed: bool = False)`

    列出所有适配器状态

:param detailed: 是否显示详细信息

    ---
    
##### `init_project(project_name: str, adapter_list: List[str] = None)`

    初始化新项目

:param project_name: 项目名称
:param adapter_list: 需要初始化的适配器列表
:return: 是否初始化成功

    ---
    
##### `interactive_init(project_name: str = None, force: bool = False)`

    交互式初始化项目，包括项目创建和配置设置

:param project_name: 项目名称，可为None
:param force: 是否强制覆盖现有配置
:return: 是否初始化成功

    ---
    
##### `_configure_adapters_interactive_sync(project_path: str = None)`

    交互式配置适配器的同步版本，从云端获取适配器列表

:param project_path: 项目路径，用于加载项目特定的配置

    ---
    
##### async `async _configure_adapters_interactive(project_path: str = None)`

    交互式配置适配器，从云端获取适配器列表

:param project_path: 项目路径，用于加载项目特定的配置

    ---
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>