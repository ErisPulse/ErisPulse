![](./.github/assets/erispulse_logo.png)
**ErisPulse** 是基于 [Framer](https://github.com/FramerOrg/Framer) 构建的异步机器人开发框架。

## 合作伙伴
[![FramerOrg](https://img.shields.io/badge/合作伙伴-FramerOrg-blue?style=flat-square)](https://github.com/FramerOrg)

### 框架选型指南
| 需求          | 推荐框架       | 理由                          |
|-------------------|----------------|-----------------------------|
| 轻量化/底层模块化 | [Framer](https://github.com/FramerOrg/Framer) | 高度解耦的模块化设计          |
| 全功能机器人开发  | ErisPulse      | 开箱即用的完整解决方案        |


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
    # 这里可以添加自定义逻辑

if __name__ == "__main__":
    asyncio.run(main())
```

## 导航
- [开发者指南](docs/DEVELOPMENT.md)
- [底层方法与接口](docs/REFERENCE.md)
- [命令行工具](docs/CLI.md)
- [源配置指南](docs/ORIGIN.md)
- [更新日志](docs/CHANGELOG.md)
> [GitHub 社区](https://github.com/ErisPulse/ErisPulse/discussions)

## 🤝 贡献

欢迎任何形式的贡献！无论是报告 bug、提出新功能请求，还是直接提交代码，都非常感谢。
