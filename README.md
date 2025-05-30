> ⚠️ **注意：2.0 之前的版本已统一标记为 Alpha（阿尔法）版本，当前 ErisPulse 仍处于探索阶段，API 和功能可能会有较大变动。请谨慎用于生产环境。**

# 🚀 ErisPulse - 异步机器人开发框架

基于 [RyhBotPythonSDK V2](https://github.com/runoneall/RyhBotPythonSDK2) 构建，由 [sdkFrame](https://github.com/runoneall/sdkFrame) 提供支持的异步机器人开发框架。

## ✨ 核心特性
- 完全异步架构设计
- 模块化插件系统
- 多协议支持
- 模块热更新
- 跨平台兼容

## 📦 安装

```bash
pip install ErisPulse --upgrade
```

**系统要求**：
- Python ≥ 3.7
- pip ≥ 20.0

## 🚀 快速开始

```python
import asyncio
from ErisPulse import sdk, logger

async def main():
    sdk.init()
    logger.info("ErisPulse 已启动")
    # 这里可以添加自定义逻辑 | 如模块的 AddHandle，AddTrigger 等

if __name__ == "__main__":
    asyncio.run(main())
```

## 🛠️ 常用命令

```bash
epsdk update                # 更新模块源
epsdk install AIChat        # 安装模块
epsdk enable AIChat         # 启用模块
epsdk list                  # 查看所有模块
```
更多命令详见 [命令行工具文档](docs/CLI.md)。

## 🧩 模块开发

你可以通过实现自定义模块扩展 ErisPulse 功能。详见 [开发指南](docs/DEVELOPMENT.md)。

## 📖 文档导航
- [开发指南](docs/DEVELOPMENT.md) - 完整的开发文档
- [命令行工具](docs/CLI.md) - CLI 使用手册
- [源配置指南](docs/ORIGIN.md) - 模块源配置说明
- [更新日志](docs/CHANGELOG.md) - 版本更新历史
- [底层API](docs/REFERENCE.md) - 方法与接口