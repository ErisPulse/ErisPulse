# `ErisPulse/CLI/legacy` 模块

legacy.py - 旧版模块管理兼容实现

**过时**： 
此模块仅用于兼容旧版模块管理方式，新代码应使用PyPI包管理方式

## 类

### `LegacyManager`

旧版模块管理器


#### 方法

##### `_init_sources`

初始化源


##### `_validate_url`

验证URL有效性


##### `handle`

处理旧版命令


##### `handle_origin`

处理源管理命令


##### `add_source`

添加源


##### `update_sources`

更新源


##### `list_sources`

列出源


##### `del_source`

删除源


##### `enable_module`

启用模块


##### `disable_module`

禁用模块


##### `install_module`

安装模块


##### `install_local_module`

安装本地模块


##### `install_pip_dependencies`

安装pip依赖


##### `extract_and_setup_module`

解压并设置模块


##### `fetch_url`

获取URL内容


##### `uninstall_module`

卸载模块


##### `upgrade_all_modules`

升级所有模块


##### `list_modules`

列出模块

