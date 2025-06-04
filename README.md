![](./.github/assets/erispulse_logo.png)

基于 [RyhBotPythonSDK V2](https://github.com/runoneall/RyhBotPythonSDK2) 构建，由 [sdkFrame](https://github.com/runoneall/sdkFrame) 提供支持的异步机器人开发框架。

## ✨ 核心特性
- ⚡ 完全异步架构设计（async/await）
- 🧩 模块化插件系统
- 📜 内置日志系统
- 🛑 统一的错误管理
- 🛠️ 灵活的配置管理

## 📦 安装

```bash
pip install ErisPulse --upgrade
```

**要求**：Python ≥ 3.7，pip ≥ 20.0

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

## 导航
- [开发指南](docs/DEVELOPMENT.md) - 完整的开发文档
- [命令行工具](docs/CLI.md) - CLI 使用手册
- [源配置指南](docs/ORIGIN.md) - 模块源配置说明
- [更新日志](docs/CHANGELOG.md) - 版本更新历史
- [底层API](docs/REFERENCE.md) - 方法与接口
- [GitHub Discussions](https://github.com/ErisPulse/ErisPulse/discussions)

## 🤝 贡献

欢迎任何形式的贡献！无论是报告 bug、提出新功能请求，还是直接提交代码，都非常感谢。

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。
