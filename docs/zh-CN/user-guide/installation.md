# 安装和配置

本指南介绍如何安装 ErisPulse 和配置你的项目。

## 系统要求

- Python 3.10 或更高版本
- pip 或 uv（推荐）
- 足够的磁盘空间（至少 100MB）

## 安装方式

### 方式一：使用 pip 安装

```bash
# 安装 ErisPulse
pip install ErisPulse

# 升级到最新版本
pip install ErisPulse --upgrade
```

### 方式二：使用 uv 安装（推荐）

uv 是一个更快的 Python 工具链，推荐用于开发环境。

#### 安装 uv

```bash
# 使用 pip 安装 uv
pip install uv

# 验证安装
uv --version
```

#### 创建虚拟环境

```bash
# 创建项目目录
mkdir my_bot && cd my_bot

# 安装 Python 3.12
uv python install 3.12

# 创建虚拟环境
uv venv
```

#### 激活虚拟环境

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### 安装 ErisPulse

```bash
# 安装 ErisPulse
uv pip install ErisPulse --upgrade
```

## 项目初始化

### 交互式初始化

```bash
epsdk init
```

按照提示完成：
1. 输入项目名称
2. 选择日志级别
3. 配置服务器参数
4. 选择适配器
5. 配置适配器参数

### 快速初始化

```bash
# 快速模式，跳过交互配置
epsdk init -q -n my_bot
```

### 配置说明

初始化后会生成 `config/config.toml` 文件：

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[ErisPulse.framework]
enable_lazy_loading = true
···

```

## 模块安装

### 从远程仓库安装

```bash
# 安装指定模块
epsdk install Yunhu

# 安装多个模块
epsdk install Yunhu Weather
```

### 从本地安装

```bash
# 安装本地模块
epsdk install ./my-module
```

### 交互式安装

```bash
# 不指定包名进入交互式安装
epsdk install
```

## 验证安装

### 检查安装

```bash
# 检查 ErisPulse 版本
epsdk --version
```

### 运行测试

```bash
# 运行项目
epsdk run main.py
```

如果看到类似的输出说明安装成功：

```
[INFO] 正在初始化 ErisPulse...
[INFO] 适配器已加载: Yunhu
[INFO] 模块已加载: MyModule
[INFO] ErisPulse 初始化完成
```

## 常见问题

### 安装失败

1. 检查 Python 版本是否 >= 3.10
2. 尝试使用 `uv` 替代 `pip`
3. 检查网络连接是否正常

### 配置错误

1. 检查 `config.toml` 语法是否正确
2. 确认所有必需的配置项都已填写
3. 查看日志获取详细错误信息

### 模块安装失败

1. 确认模块名称是否正确
2. 检查网络连接
3. 使用 `epsdk list-remote` 查看可用模块

## 下一步

- [CLI 命令参考](cli-reference.md) - 了解所有命令行命令
- [配置文件说明](configuration.md) - 详细了解配置选项