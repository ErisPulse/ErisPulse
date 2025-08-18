# ErisPulse 示例模块

这是一个 ErisPulse 示例模块，演示了如何创建和使用 ErisPulse 模块。

## 功能特性

- 基本模块结构示例
- 配置管理示例
- Event 模块使用示例
  - 命令处理器 (`/hello`, `/help`, `/echo`)
  - 消息处理器 (私聊消息)
  - 通知处理器 (好友添加)

## 安装

```bash
pip install -e .
```

## 使用
安装模块后，在 ErisPulse 项目中启用模块即可使用相关功能。

可用命令
- /hello - 发送问候消息
- /help 或 /h - 显示帮助信息
- /echo <内容> - 回显消息

## 开发
参考 ErisPulse 模块开发指南 了解更多信息。