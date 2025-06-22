![](./.github/assets/erispulse_logo.png)
**ErisPulse** 是基于 [Framer](https://github.com/FramerOrg/Framer) 构建的异步机器人开发框架。

[![FramerOrg](https://img.shields.io/badge/合作伙伴-FramerOrg-blue?style=flat-square)](https://github.com/FramerOrg)
[![License](https://img.shields.io/github/license/ErisPulse/ErisPulse?style=flat-square)](https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE)

[![Python Versions](https://img.shields.io/pypi/pyversions/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)

> 文档站:

[![Docs-Main](https://img.shields.io/badge/docs-main_site-blue?style=flat-square)](https://www.erisdev.com/docs)
[![Docs-CF Pages](https://img.shields.io/badge/docs-cloudflare-blue?style=flat-square)](https://erispulse.pages.dev/docs)
[![Docs-GitHub](https://img.shields.io/badge/docs-github-blue?style=flat-square)](https://erispulse.github.io/docs)
[![Docs-Netlify](https://img.shields.io/badge/docs-netlify-blue?style=flat-square)](https://erispulse.netlify.app/docs)
[![Docs-Vercel](https://img.shields.io/badge/docs-vercel-blue?style=flat-square)](https://erispulse.vercel.app/docs)

- [GitHub 社区讨论](https://github.com/ErisPulse/ErisPulse/discussions)

### 框架选型指南
| 需求          | 推荐框架       | 理由                          |
|-------------------|----------------|-----------------------------|
| 轻量化/底层模块化 | [Framer](https://github.com/FramerOrg/Framer) | 高度解耦的模块化设计          |
| 全功能机器人开发  | ErisPulse      | 开箱即用的完整解决方案        |

## ✨ 核心特性
- ⚡ 完全异步架构设计（async/await）
- 🧩 模块化插件系统
- � 内置日志系统
- 🛑 统一的错误管理
- 🛠️ 灵活的配置管理

## 📦 安装

```bash
pip install ErisPulse --upgrade
```

---

### 如果你具有以下需求，建议使用 `uv` 进行开发：
- 进行模块开发
- 调试 ErisPulse SDK
- 对 ErisPulse SDK 进行二次开发
- 提交 Pull Request（PR）

```bash
git clone https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
uv pip install -e .
```

> **说明**：
> - `-e` 表示可编辑安装，方便本地修改即时生效

## 🤝 贡献

欢迎任何形式的贡献！无论是报告 bug、提出新功能请求，还是直接提交代码，都非常感谢。