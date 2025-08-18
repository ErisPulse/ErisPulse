# ErisPulse - 异步机器人开发框架

![ErisPulse Logo](.github/assets/erispulse_logo.png)

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Python Versions](https://img.shields.io/pypi/pyversions/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)
[![Socket Badge](https://socket.dev/api/badge/pypi/package/ErisPulse/2.1.15?artifact_id=tar-gz)](https://socket.dev/pypi/package/ErisPulse/overview/2.1.15/tar-gz)

## 文档资源

| 平台 | 主站点 | 备用站点 |
|------|--------|---------|
| 文档 | [erisdev.com](https://www.erisdev.com/#docs) | [Cloudflare](https://erispulse.pages.dev/#docs) • [GitHub](https://erispulse.github.io/#docs) • [Netlify](https://erispulse.netlify.app/#docs) |
| 模块市场 | [erisdev.com](https://www.erisdev.com/#market) | [Cloudflare](https://erispulse.pages.dev/#market) • [GitHub](https://erispulse.github.io/#market) • [Netlify](https://erispulse.netlify.app/#market) |

## 核心特性

| 特性 | 描述 |
|:-----|:-----|
| 异步架构 | 完全基于 async/await 的异步设计 |
| 模块化系统 | 灵活的插件和模块管理 |
| 热重载 | 开发时自动重载，无需重启 |
| 错误管理 | 统一的错误处理和报告系统 |
| 配置管理 | 灵活的配置存储和访问 |

## 快速开始

### 一键安装脚本

#### Windows (PowerShell):

```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

#### macOS/Linux:

```bash
curl -sSL https://get.erisdev.com/install.sh | tee install.sh >/dev/null && chmod +x install.sh && ./install.sh
```

## 开发与测试

### 1. 克隆项目

```bash
git clone -b Develop/v2 https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
```

### 2. 环境搭建

使用 uv 同步项目环境:

```bash
uv sync

# 激活虚拟环境
source .venv/bin/activate   # macOS/Linux
# Windows: .venv\Scripts\activate
```

说明: ErisPulse 使用 Python 3.13 开发，但兼容 Python 3.10+

### 3. 安装依赖

```bash
uv pip install -e .
```

这将以"开发模式"安装 SDK，所有本地修改都会立即生效。

### 4. 验证安装

运行以下命令确认 SDK 正常加载：

```bash
python -c "from ErisPulse import sdk; sdk.init()"
```

### 5. 运行测试

我们提供了一个交互式测试脚本，可以帮助您快速验证SDK功能(于开发中)：

```bash
uv run devs/test.py
```

测试功能包括:
- 日志系统测试
- 环境配置测试
- 错误管理测试
- 工具函数测试
- 适配器功能测试

## 贡献指南

我们欢迎各种形式的贡献，包括但不限于:

1. 报告问题  
   在 [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) 提交bug报告

2. 功能请求  
   通过 [社区讨论](https://github.com/ErisPulse/ErisPulse/discussions) 提出新想法

3. 代码贡献  
   提交 Pull Request 前请阅读我们的 [代码风格](docs/StyleGuide/DocstringSpec.md) 以及 [贡献指南](CONTRIBUTING.md)

4. 文档改进  
   帮助完善文档和示例代码

[加入社区讨论](https://github.com/ErisPulse/ErisPulse/discussions)

---

[![](https://starchart.cc/ErisPulse/ErisPulse.svg?variant=adaptive)](https://starchart.cc/ErisPulse/ErisPulse)
