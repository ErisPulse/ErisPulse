# ErisPulse CLI 命令手册

## 官方 CLI 命令手册

### 包管理命令

| 命令       | 参数                      | 描述                                  | 示例                          |
|------------|---------------------------|---------------------------------------|-------------------------------|
| `install`  | `<package>... [--upgrade/-U] [--pre]` | 安装模块/适配器包（支持多个包）      | `epsdk install Yunhu Weather`  |
|            |                           | 支持远程包简称自动解析                | `epsdk install Yunhu -U` |
| `uninstall`| `<package>...`            | 卸载模块/适配器包（支持多个包）       | `epsdk uninstall old-module1 old-module2`  |
| `upgrade`  | `[package]... [--force/-f] [--pre]` | 升级指定模块/适配器或所有包         | `epsdk upgrade --force`       |
| `search`   | `<query> [--installed/-i] [--remote/-r]` | 搜索模块/适配器包             | `epsdk search github`         |
| `self-update` | `[version] [--pre] [--force/-f]` | 更新ErisPulse SDK本身           | `epsdk self-update`           |

### 模块管理命令

| 命令       | 参数       | 描述                  | 示例                  |
|------------|------------|-----------------------|-----------------------|
| `enable`   | `<module>` | 启用已安装的模块      | `epsdk enable chat`   |
| `disable`  | `<module>` | 禁用已安装的模块      | `epsdk disable stats` |

### 信息查询命令

| 命令          | 参数                      | 描述                                  | 示例                          |
|---------------|---------------------------|---------------------------------------|-------------------------------|
| `list`        | `[--type/-t <type>]`      | 列出已安装的模块/适配器               | `epsdk list --type=modules`   |
|               | `[--outdated/-o]`         | 仅显示可升级的包                      | `epsdk list -o`               |
|               |                           | `--type`: `modules`/`adapters`/`cli`/`all`  | `epsdk list -t adapters`      |
| `list-remote` | `[--type/-t <type>]`      | 列出远程可用的模块和适配器            | `epsdk list-remote`           |
|               | `[--refresh/-r]`          | 强制刷新远程包列表                    | `epsdk list-remote -r`        |
|               |                           | `--type`: `modules`/`adapters`/`cli`/`all`  | `epsdk list-remote -t all`    |

### 运行控制命令

| 命令       | 参数                      | 描述                                  | 示例                          |
|------------|---------------------------|---------------------------------------|-------------------------------|
| `run`      | `<script> [--reload] [--no-reload]` | 运行指定脚本                    | `epsdk run main.py`           |
|            |                           | `--reload`: 启用热重载模式            | `epsdk run app.py --reload`   |

### 项目管理命令

| 命令       | 参数                      | 描述                                  | 示例                          |
|------------|---------------------------|---------------------------------------|-------------------------------|
| `init`     | `[--project-name/-n <name>]` | 交互式初始化新的 ErisPulse 项目  | `epsdk init -n my_bot`       |
|            | `[--quick/-q]`             | 快速模式，跳过交互配置            | `epsdk init -q -n my_bot`      |
|            | `[--force/-f]`             | 强制覆盖现有配置                  | `epsdk init -f`               |
| `status`   | `[--type/-t <type>]`       | 显示 ErisPulse 系统状态        | `epsdk status`                |
|            |                           | `--type`: `modules`/`adapters`/`all` | `epsdk status -t modules`     |


## 第三方 CLI 模块扩展

ErisPulse 支持第三方 CLI 模块扩展，开发者可以创建自定义命令来扩展 CLI 功能。

如需开发第三方 CLI 模块，请参考开发文档：
`docs/development/cli.md`

该文档详细介绍了：
- 如何创建 CLI 扩展模块
- 命令注册机制
- 参数处理最佳实践
- 输出格式规范
- 错误处理指南

## 技术细节

- 优先使用 `uv` 进行包管理 (如果已安装)
- 支持多源远程仓库查询
- 热重载模式支持:
  - 开发模式: 监控所有 `.py` 文件变化
  - 普通模式: 仅监控 `config.toml` 变更
- 自动检查模块的最低SDK版本要求
- 支持通过简称安装/卸载远程包

## 反馈与支持

如遇到 CLI 使用问题，请在 GitHub Issues 提交反馈。