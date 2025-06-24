![](./.github/assets/erispulse_logo.png)
**ErisPulse** 是基于 [Framer](https://github.com/FramerOrg/Framer) 构建的异步机器人开发框架。

[![FramerOrg](https://img.shields.io/badge/合作伙伴-FramerOrg-blue?style=flat-square)](https://github.com/FramerOrg)
[![License](https://img.shields.io/github/license/ErisPulse/ErisPulse?style=flat-square)](https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE)

[![Python Versions](https://img.shields.io/pypi/pyversions/ErisPulse?style=flat-square)](https://pypi.org/project/ErisPulse/)

> 文档站:

[![Docs-Main](https://img.shields.io/badge/docs-main_site-blue?style=flat-square)](https://www.erisdev.com/docs.html)
[![Docs-CF Pages](https://img.shields.io/badge/docs-cloudflare-blue?style=flat-square)](https://erispulse.pages.dev/docs.html)
[![Docs-GitHub](https://img.shields.io/badge/docs-github-blue?style=flat-square)](https://erispulse.github.io/docs.html)
[![Docs-Netlify](https://img.shields.io/badge/docs-netlify-blue?style=flat-square)](https://erispulse.netlify.app/docs.htm)

- [GitHub 社区讨论](https://github.com/ErisPulse/ErisPulse/discussions)

### 框架选型指南
| 需求          | 推荐框架       | 理由                          |
|-------------------|----------------|-----------------------------|
| 轻量化/底层模块化 | [Framer](https://github.com/FramerOrg/Framer) | 高度解耦的模块化设计          |
| 全功能机器人开发  | ErisPulse      | 开箱即用的完整解决方案        |

## ✨ 核心特性
- ⚡ 完全异步架构设计（async/await）
- 🧩 模块化插件系统
- 🔁 支持python热重载
- 🛑 统一的错误管理
- 🛠️ 灵活的配置管理

## 📦 安装

```bash
pip install ErisPulse --upgrade
```

---

## 开发者快速入门

ErisPulse SDK 支持使用 [`uv`](https://github.com/astral-sh/uv) 进行完整的开发环境管理。你可以**无需手动安装 Python**，直接通过 `uv` 下载 Python、创建虚拟环境并开始开发。

### 安装 `uv`

#### macOS / Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

验证是否安装成功：
```bash
uv --version
```

### 克隆项目并进入目录

```bash
git clone https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
```

### 使用 `uv` 自动下载 Python 并创建虚拟环境

```bash
uv python install 3.12          # 自动下载并安装 Python 3.12
uv venv                         # 创建默认 .venv 虚拟环境
source .venv/bin/activate    
# Windows: .venv\Scripts\activate
```

> ✅ 如果你切换分支或需要不同 Python 版本，只需替换 `3.12` 为其他版本即可。

### 安装依赖并开始开发

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

测试脚本提供以下功能：
- 日志功能测试
- 环境配置测试  
- 错误管理测试
- 工具函数测试
- 适配器功能测试
- 版本信息查看

### 开始开发

你可以通过 CLI 工具进行模块调试、热重载开发等操作：

```bash
epsdk run your_script.py --reload
```

---

## 🤝 贡献

欢迎任何形式的贡献！无论是报告 bug、提出新功能请求，还是直接提交代码，都非常感谢。