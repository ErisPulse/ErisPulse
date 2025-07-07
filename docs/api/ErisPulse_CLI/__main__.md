# `ErisPulse_CLI/__main__` 模块

# CLI 入口

提供命令行界面(CLI)用于模块管理、源管理和开发调试。

## 主要功能
- 模块管理: 安装/卸载/启用/禁用
- 源管理: 添加/删除/更新源
- 热重载: 开发时自动重启
- 彩色终端输出

## 主要命令
### 模块管理:
    init: 初始化SDK
    install: 安装模块
    uninstall: 卸载模块
    enable: 启用模块
    disable: 禁用模块
    list: 列出模块
    update: 更新模块列表
    upgrade: 升级模块

### 源管理:
    origin add: 添加源
    origin del: 删除源  
    origin list: 列出源

### 开发调试:
    run: 运行脚本
    --reload: 启用热重载

### 示例用法:

```
# 安装模块
epsdk install MyModule

# 启用热重载
epsdk run main.py --reload

# 管理源
epsdk origin add https://example.com/map.json
```
