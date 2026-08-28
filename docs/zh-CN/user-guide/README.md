# 用户使用指南

本指南帮助你安装、配置和管理 ErisPulse 项目。

## 内容列表

| 文档 | 说明 |
|------|------|
| [安装和配置](installation.md) | 系统要求、安装方式（pip/uv/Docker）、验证安装 |
| [ErisPulse-App 手机/桌面客户端](../ecosystem/app.md) | 官方客户端：手机 / 桌面直接运行，原生界面管理 ErisPulse 实例 |
| [CLI 命令参考](cli-reference.md) | `epsdk` 命令行工具的完整使用说明 |
| [配置文件说明](configuration.md) | `config/config.toml` 各配置项的详细说明 |
| [部署指南](deployment.md) | Docker 部署、systemd 服务、SSL 配置 |

## 快速参考

### 常用命令

| 命令 | 说明 |
|------|------|
| `epsdk init` | 初始化项目（`-q` 快速模式，`-n` 指定名称） |
| `epsdk install <包名>` | 安装模块/适配器（不带参数进入交互模式） |
| `epsdk config <名称>` | 交互式配置适配器/模块的声明式配置项 |
| `epsdk run main.py` | 运行项目（`--reload` 热重载模式） |
| `epsdk list` | 列出已安装的模块/适配器 |
| `epsdk upgrade <包名>` | 升级模块/适配器 |
| `epsdk doctor` | 诊断环境（Python/后端/配置/PyPI 连通性） |

> 完整的命令列表和参数说明请参考 [CLI 命令参考](cli-reference.md)。

### 常见配置位置

| 配置项 | 说明 | 详见 |
|--------|------|------|
| `[ErisPulse.server]` | 服务器配置（主机、端口） | [配置文件说明](configuration.md#服务器配置) |
| `[ErisPulse.logger]` | 日志配置（级别、输出文件） | [配置文件说明](configuration.md#日志配置) |
| `[ErisPulse.framework]` | 框架配置（懒加载） | [配置文件说明](configuration.md#框架配置) |
| `[ErisPulse.event.command]` | 命令事件配置（前缀） | [配置文件说明](configuration.md#事件配置) |
| `[适配器名]` | 各适配器的特定配置 | [平台特性指南](../platform-guide/) |

## 相关文档

- [快速开始](../quick-start.md) - 快速入门指南
- [新手入门](../getting-started/) - 入门教程
- [开发者指南](../developer-guide/) - 开发自定义模块和适配器
- [API 参考](../api-reference/) - API 文档
