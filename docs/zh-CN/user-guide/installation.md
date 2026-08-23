# 安装参考

> 本文是安装方式的**完整参考**（pip / uv / Docker / 故障排查）。
> 如果你只想快速跑起来，[5 分钟快速开始](../quick-start.md) 已经覆盖了最简流程。

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

## 项目初始化与模块安装

安装完成后，项目初始化、模块安装、运行的完整流程见 [5 分钟快速开始](../quick-start.md)。

### 方式三：使用 ErisPulse-App 客户端（免终端）

不想装 Python 环境？[ErisPulse-App](../ecosystem/app.md) 是官方全平台客户端
（Android / Windows / Linux / macOS），**手机直接运行**，桌面版支持最小化到
系统托盘后台常驻；内置 Python 运行时与 ErisPulse SDK，无需终端与手动配置：

- 从 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 按平台选择下载
  （Android `online`/`offline` APK、Windows `setup.exe`/`zip`、Linux `tar.gz`、macOS `zip`）
- 在 App 内创建并启动实例，通过原生界面管理适配器与模块、浏览模块商店

> 完整说明见 [ErisPulse-App 安装与使用](../ecosystem/app.md)。

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

1. 检查 Python 版本是否 >= 3.10（推荐 3.10 - 3.13）
2. 尝试使用 `uv pip install ErisPulse` 替代 `pip install`
3. 如果提示权限错误，尝试 `pip install --user ErisPulse` 或使用虚拟环境
4. 如果在企业代理环境下遇到 SSL 证书错误，尝试 `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse`
5. 确保网络连接正常，pip 源可访问

### 配置错误

1. 检查 `config.toml` 语法是否正确（TOML 格式对缩进和引号敏感）
2. 确认所有必需的配置项都已填写
3. 查看终端日志获取详细错误信息
4. 使用 `epsdk init` 重新生成配置文件

### 模块安装失败

1. 确认模块名称拼写正确（大小写敏感）
2. 检查网络连接
3. 使用 `epsdk list-remote` 查看可用模块列表
4. 确认模块与你当前 SDK 版本兼容

### Windows PowerShell 执行策略

如果 PowerShell 提示"无法加载文件...因为在此系统上禁止运行脚本"：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 下一步

- [CLI 命令参考](cli-reference.md) - 了解所有命令行命令
- [配置文件说明](configuration.md) - 详细了解配置选项