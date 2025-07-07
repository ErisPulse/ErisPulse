# `ErisPulse/__main__` 模块

# CLI 入口 (PyPI包管理版本)

提供命令行界面(CLI)用于PyPI包管理、源管理和开发调试。

## 主要功能
- PyPI包管理: 查找/安装/卸载/更新模块和适配器
- 开发调试: 热重载
- 彩色终端输出

## 主要命令
### 包管理:
    search: 搜索PyPI上的ErisPulse模块
    install: 安装模块/适配器包
    uninstall: 卸载模块/适配器包
    list: 列出已安装的模块/适配器
    upgrade: 升级所有模块/适配器

### 开发调试:
    run: 运行脚本
    --reload: 启用热重载

### 兼容性子命令(旧方式):
    legacy: 旧版模块管理命令

### 示例用法:
```
# 搜索模块
epsdk search MyModule

# 安装模块
epsdk install ErisPulse-MyModule

# 启用热重载
epsdk run main.py --reload
```

## 函数

### `start_reloader`

启动热重载监视器


### `run_script`

运行指定脚本


### `legacy_command`

旧版模块管理命令


## 类

### `PyPIManager`

管理PyPI上的ErisPulse模块和适配器


#### 方法

##### `search_packages`

搜索PyPI上的ErisPulse相关包


##### `get_installed_packages`

获取已安装的ErisPulse模块和适配器


##### `install_package`

安装或升级PyPI包


##### `uninstall_package`

卸载PyPI包


##### `upgrade_all`

升级所有ErisPulse相关包


### `ReloadHandler`

热重载处理器

