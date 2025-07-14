# `ErisPulse/__main__` 模块

# CLI 入口

提供命令行界面(CLI)用于包管理和启动入口。

## 主要命令
### 包管理:
    search: 搜索PyPI上的ErisPulse模块
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

## 类

### `PyPIManager`

管理PyPI上的ErisPulse模块和适配器

