# 快速开始

## 安装 ErisPulse

### 使用 pip 安装

确保你的 Python 版本 >= 3.10，然后使用 pip 安装 ErisPulse：

```bash
pip install ErisPulse
```

### 使用 uv 安装（推荐）

`uv` 是一个更快的 Python 工具链，推荐使用：

#### 安装 uv

```bash
pip install uv
```

#### 创建项目并安装

```bash
uv python install 3.12              # 安装 Python 3.12
uv venv                             # 创建虚拟环境
.venv\Scripts\activate               # 激活环境 (Windows)
# source .venv/bin/activate          # Linux/Mac
uv pip install ErisPulse --upgrade  # 安装框架
```

## 初始化项目

### 交互式初始化（推荐）

```bash
epsdk init
```

这将启动一个交互式向导，引导您完成：
- 项目名称设置
- 日志级别配置
- 服务器配置（主机和端口）
- 适配器选择和配置
- 项目结构创建

### 快速初始化

```bash
# 指定项目名称的快速模式
epsdk init -q -n my_bot

# 或者只指定项目名称
epsdk init -n my_bot
```

### 手动创建项目

如果更喜欢手动创建项目：

```bash
mkdir my_bot && cd my_bot
epsdk init
```

## 安装模块

### 通过 CLI 安装

```bash
epsdk install Yunhu AIChat
```

### 查看可用模块

```bash
epsdk list-remote
```

### 交互式安装

不指定包名时进入交互式安装界面：

```bash
epsdk install
```

## 运行项目

```bash
# 普通运行
epsdk run main.py

# 热重载模式（开发时推荐）
epsdk run main.py --reload
```

## 项目结构

初始化后的项目结构：

```
my_bot/
├── config/
│   └── config.toml          # 配置文件
└── main.py                  # 入口文件

```

## 配置文件

基本的 `config.toml` 配置：

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# 适配器配置
```

## 下一步

- [入门指南总览](getting-started/README.md) - 了解 ErisPulse 的基本概念
- [创建第一个机器人](getting-started/first-bot.md) - 创建一个简单的机器人
- [用户使用指南](user-guide/) - 深入了解配置和模块管理
- [开发者指南](developer-guide/) - 开发自定义模块和适配器