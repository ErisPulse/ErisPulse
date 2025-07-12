# ErisPulse - 异步机器人开发框架

![ErisPulse Logo](.github/assets/erispulse_logo.png)

[![FramerOrg](https://img.shields.io/badge/合作伙伴-FramerOrg-blue?style=flat-square)](https://github.com/FramerOrg)
[![Python Versions](https://img.shields.io/pypi/pyversions/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)

> 文档站: 
[![Docs-Main](https://img.shields.io/badge/docs-main_site-blue?style=flat-square)](https://www.erisdev.com/docs.html)
[![Docs-CF Pages](https://img.shields.io/badge/docs-cloudflare-blue?style=flat-square)](https://erispulse.pages.dev/docs.html)
[![Docs-GitHub](https://img.shields.io/badge/docs-github-blue?style=flat-square)](https://erispulse.github.io/docs.html)
[![Docs-Netlify](https://img.shields.io/badge/docs-netlify-blue?style=flat-square)](https://erispulse.netlify.app/docs.htm)


## 核心特性

| 特性 | 描述 |
|------|------|
| **异步架构** | 完全基于 async/await 的异步设计 |
| **模块化系统** | 灵活的插件和模块管理 |
| **热重载** | 开发时自动重载，无需重启 |
| **错误管理** | 统一的错误处理和报告系统 |
| **配置管理** | 灵活的配置存储和访问 |

---

## 快速开始

### 一键安装脚本

我们提供了一键安装脚本，支持所有主流平台：

#### Windows (PowerShell):

```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

#### macOS/Linux:
```bash
curl -sSL https://get.erisdev.com/install.sh | tee install.sh >/dev/null && chmod +x install.sh && ./install.sh
```

---

## 测试与开发

### 克隆项目并进入目录

```bash
git clone -b Develop/v2 https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
```

### 使用 `uv` 同步项目环境

```bash
uv sync

# 启动虚拟环境
source .venv/bin/activate   
# Windows: .venv\Scripts\activate
```

> `ErisPulse` 目前正在使用 `python3.13` 进行开发(所以您同步环境时会自动安装 `3.13`)，但也可以使用其他版本(版本不应低于 `3.10`)。

### 安装依赖并开始

```bash
uv pip install -e .
```

这将以“开发模式”安装 SDK，所有本地修改都会立即生效。

### 验证安装

运行以下命令确认 SDK 正常加载：

```bash
python -c "from ErisPulse import sdk; sdk.init()"
```

### 运行测试

我们提供了一个交互式测试脚本，可以帮助您快速验证SDK功能：

```bash
uv run devs/test.py
```

测试功能包括:
- 日志系统测试
- 环境配置测试
- 错误管理测试
- 工具函数测试
- 适配器功能测试

### 开发模式 (热重载)
```bash
epsdk run your_script.py --reload
```

---

## 🤝 贡献指南

我们欢迎各种形式的贡献，包括但不限于:

1. **报告问题**  
   在 [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) 提交bug报告

2. **功能请求**  
   通过 [社区讨论](https://github.com/ErisPulse/ErisPulse/discussions) 提出新想法

3. **代码贡献**  
   提交 Pull Request 前请阅读我们的 [开发指南](docs/DEVELOPMENT.md)

4. **文档改进**  
   帮助完善文档和示例代码

---

[加入社区讨论 →](https://github.com/ErisPulse/ErisPulse/discussions)
