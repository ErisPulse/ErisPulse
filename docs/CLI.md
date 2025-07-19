# ErisPulse 官方 CLI 命令手册

## 命令概述

ErisPulse CLI 提供以下命令组：

## 命令参考

### 包管理命令

| 命令       | 参数                      | 描述                                  | 示例                          |
|------------|---------------------------|---------------------------------------|-------------------------------|
| `install`  | `<package> [--upgrade/-U]` | 安装模块/适配器包                     | `epsdk install Yunhu`  |
|            |                           | 支持远程包简称自动解析                | `epsdk install Yunhu -U` |
| `uninstall`| `<package>`               | 卸载模块/适配器包                     | `epsdk uninstall old-module`  |
| `upgrade`  | `[--force/-f]`            | 升级所有模块/适配器                   | `epsdk upgrade --force`       |

### 模块管理命令

| 命令       | 参数       | 描述                  | 示例                  |
|------------|------------|-----------------------|-----------------------|
| `enable`   | `<module>` | 启用已安装的模块      | `epsdk enable chat`   |
| `disable`  | `<module>` | 禁用已安装的模块      | `epsdk disable stats` |

### 信息查询命令

| 命令          | 参数                      | 描述                                  | 示例                          |
|---------------|---------------------------|---------------------------------------|-------------------------------|
| `list`        | `[--type/-t <type>]`      | 列出已安装的模块/适配器               | `epsdk list --type=modules`   |
|               |                           | `--type`: `modules`/`adapters`/`all`  | `epsdk list -t adapters`      |
| `list-remote` | `[--type/-t <type>]`      | 列出远程可用的模块和适配器            | `epsdk list-remote`           |
|               |                           | `--type`: `modules`/`adapters`/`all`  | `epsdk list-remote -t all`    |

### 运行控制命令

| 命令       | 参数                      | 描述                                  | 示例                          |
|------------|---------------------------|---------------------------------------|-------------------------------|
| `run`      | `<script> [--reload]`     | 运行指定脚本                          | `epsdk run main.py`           |
|            |                           | `--reload`: 启用热重载模式            | `epsdk run app.py --reload`   |

## 高级用法

### 安装远程模块
CLI会自动检查远程仓库中的模块简称：
```bash
# 安装远程模块("Yunhu" 是远程适配器 "ErisPulse-YunhuAdapter" 的简称)
epsdk install Yunhu

# 升级安装远程模块
epsdk install Yunhu --upgrade
```

### 批量升级
强制升级所有模块(跳过确认):
```bash
epsdk upgrade --force
```

### 开发模式运行
使用热重载运行脚本，自动检测文件变化:
```bash
epsdk run dev.py --reload
```

### 模块管理
```bash
# 启用模块
epsdk enable chat-module

# 禁用模块
epsdk disable old-module
```

## 技术细节

- 优先使用 `uv` 进行包管理 (如果已安装)
- 支持多源远程仓库查询
- 热重载模式支持:
  - 开发模式: 监控所有 `.py` 文件变化
  - 普通模式: 仅监控 `config.toml` 变化

## 反馈与支持

如遇到 CLI 使用问题，请在 GitHub Issues 提交反馈。