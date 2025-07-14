# 快速开始

## 安装ErisPulse

### 使用 pip 安装
```bash
pip install ErisPulse
```

### 更先进的安装方法
> 我们全面采用 [`uv`](https://github.com/astral-sh/uv) 作为 Python 工具链, 所以需要先安装 uv。

### 1. 安装 uv

#### 通用方法 (pip):
```bash
pip install uv
```

#### macOS/Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

验证安装:
```bash
uv --version
```

### 2. 创建虚拟环境,并安装 ErisPulse 及官方CLI

```bash
uv python install 3.12              # 安装 Python 3.12
uv venv                             # 创建虚拟环境
source .venv/bin/activate           # 激活环境 (Windows: .venv\Scripts\activate)
uv pip install ErisPulse[cli] --upgrade  # 安装框架
```

---

## 初始化项目

1. 创建项目目录并进入：

```bash
mkdir my_bot && cd my_bot
```

2. 初始化 SDK 并生成配置文件：

```bsah
epsdk init
# 或 ep-init
```

这将在当前目录下自动生成 `env.py` 配置模板文件, 以及最简程序入口 `main.py`。

---

## 安装模块

你可以通过 CLI 安装所需模块：

```bash
# 一般情况下,需要先更新源: epsdk update
epsdk install YunhuAdapter OneBotAdapter AIChat
```

你也可以手动编写模块逻辑，参考开发者文档进行模块开发。

---

## 运行你的机器人
运行我们自动生成的程序入口：
```bash
epsdk run main.py
```

或者使用热重载模式（开发时推荐）：

```bash
epsdk run main.py --reload
```
