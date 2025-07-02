# ErisPulse CLI 命令手册

## 模块管理
**说明**：
- `--init`参数：执行命令前先初始化模块状态
- 支持通配符批量启用/禁用/安装/卸载模块

| 命令       | 参数                      | 描述                                  | 示例                          |
|------------|---------------------------|---------------------------------------|-------------------------------|
| `enable`   | `<module> [--init]`       | 激活指定模块                          | `epsdk enable chatgpt --init`       |
| `disable`  | `<module> [--init]`       | 停用指定模块                          | `epsdk disable weather`             |
| `list`     | `[--module=<name>] [--init]` | 列出模块（可筛选）                   | `epsdk list --module=payment`       |
| `update`   | -                         | 更新模块索引                           | `epsdk update`                      |
| `upgrade`  | `[--force] [--init]`      | 升级模块（`--force` 强制覆盖）        | `epsdk upgrade --force --init`      |
| `install`  | `<module...> [--init]`    | 安装一个或多个模块（空格分隔），支持本地目录路径 | `epsdk install YunhuAdapter OpenAI`<br>`epsdk install .`<br>`epsdk install /path/to/module` |
| `uninstall`| `<module> [--init]`       | 移除指定模块                          | `epsdk uninstall old-module --init` |
| `init`    | -                         | 初始化sdk | `epsdk init`                        |
| `run` | `<script> [--reload]` | 运行指定脚本（支持热重载） | `epsdk run main.py --reload` |

## 源管理
| 命令 | 参数 | 描述 | 示例 |
|------|------|------|------|
| `origin add` | `<url>` | 添加源 | `epsdk origin add https://erisdev.com/map.json` |
| `origin list` | - | 源列表 | `epsdk origin list` |
| `origin del` | `<url>` | 删除源 | `epsdk origin del https://erisdev.com/map.json` |

---

## 反馈与支持
如遇到 CLI 使用问题，请在 GitHub Issues 提交反馈。