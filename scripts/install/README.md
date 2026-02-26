# ErisPulse 一键安装脚本

## 适用场景

当您的系统满足以下条件时，推荐使用一键安装脚本：
- 有网络连接环境
- Python 版本低于 3.10 或未安装 Python
- 希望自动配置符合要求的开发环境

脚本会自动完成以下操作：
1. 检测并安装符合要求的 Python 环境
2. 安装 [uv](https://github.com/astral-sh/uv)（快速 Python 工具链）
3. 创建独立的虚拟环境
4. 安装 ErisPulse 框架

## 快速开始

### Windows

打开 PowerShell，执行以下命令：

```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

### macOS / Linux

打开终端，执行以下命令：

```bash
curl -fsSL https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/scripts/install/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

## 使用说明

### 安装流程

1. 运行安装脚本
2. 脚本检测系统环境和 Python 版本
3. 询问是否安装 uv（推荐）
4. 选择要安装的 ErisPulse 版本
5. 确认安装选项
6. 自动创建虚拟环境并安装
7. 安装完成后自动激活虚拟环境

### 安装后的操作

安装完成后，脚本会自动激活虚拟环境。您可以：

```bash
# 查看帮助
epsdk -h

# 初始化项目
epsdk init

# 查看可用模块
epsdk list-remote

# 安装模块
epsdk install <模块名>
```

### 虚拟环境管理

**激活虚拟环境：**

Windows (PowerShell):
```powershell
.\.venv\Scripts\activate.ps1
```

macOS/Linux:
```bash
source .venv/bin/activate
```

**退出虚拟环境：**

所有平台：
```bash
deactivate
```


## 技术支持

遇到问题？请通过以下方式获取帮助：

- 查看 [完整文档](https://www.erisdev.com/#docs)
- 在 [GitHub Discussions](https://github.com/ErisPulse/ErisPulse/discussions) 提问
- 在 [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) 报告问题

## 相关链接

- [ErisPulse 主页](https://github.com/ErisPulse/ErisPulse)
- [PyPI 页面](https://pypi.org/project/ErisPulse/)
- [官方文档](https://www.erisdev.com)
- [uv 工具链](https://github.com/astral-sh/uv)