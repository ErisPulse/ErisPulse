# 用户使用指南

本指南帮助你安装、配置和管理 ErisPulse 项目。

## 内容列表

1. [安装和配置](installation.md) - 安装 ErisPulse 和配置项目
2. [CLI 命令参考](cli-reference.md) - 命令行工具的完整使用说明
3. [配置文件说明](configuration.md) - 配置文件的详细说明

## 快速参考

### 常用命令

| 命令 | 说明 | 示例 |
|-------|------|------|
| `epsdk init` | 初始化项目 | `epsdk init -q -n my_bot` |
| `epsdk install` | 安装模块/适配器 | `epsdk install Yunhu` |
| `epsdk run` | 运行项目 | `epsdk run main.py --reload` |
| `epsdk list` | 列出已安装的模块 | `epsdk list -t modules` |
| `epsdk upgrade` | 升级模块 | `epsdk upgrade Yunhu` |

### 常见配置位置

| 配置项 | 说明 |
|--------|------|
| `[ErisPulse.server]` | 服务器配置（主机、端口） |
| `[ErisPulse.logger]` | 日志配置（级别、输出文件） |
| `[ErisPulse.framework]` | 框架配置（懒加载） |
| `[ErisPulse.event.command]` | 命令事件配置（前缀） |
| `[适配器名]` | 各适配器的特定配置 |

### 项目目录结构

```
project/
├── config/
│   └── config.toml          # 项目配置文件
├── main.py                  # 项目入口文件
└── requirements.txt          # 依赖列表
```

## 开发模式

### 热重载模式

开发时使用热重载模式，代码修改后自动重载：

```bash
epsdk run main.py --reload
```

### 普通运行模式

生产环境使用普通运行模式：

```bash
epsdk run main.py
```

## 常见任务

### 安装新模块

```bash
# 从远程仓库安装
epsdk install Yunhu Weather

# 从本地目录安装
epsdk install ./my-module

# 交互式安装
epsdk install
```

### 查看可用模块

```bash
# 列出所有模块
epsdk list

# 只列出适配器
epsdk list -t adapters

# 只列出模块
epsdk list -t modules

# 列出远程可用模块
epsdk list-remote
```

### 升级模块

```bash
# 升级指定模块
epsdk upgrade Yunhu

# 升级所有模块
epsdk upgrade
```

### 卸载模块

```bash
# 卸载指定模块
epsdk uninstall Yunhu

# 卸载多个模块
epsdk uninstall Yunhu Weather
```

## 相关文档

- [快速开始](../quick-start.md) - 快速入门指南
- [新手入门](../getting-started/) - 入门教程
- [开发者指南](../developer-guide/) - 开发自定义模块和适配器
- [API 参考](../api-reference/) - API 文档
