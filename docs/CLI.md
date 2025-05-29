# ErisPulse CLI 命令手册

## 模块管理
**全局参数说明**：  
`--init`：执行命令前先初始化模块状态 

| 命令       | 参数                      | 描述                                  | 示例                          |
|------------|---------------------------|---------------------------------------|-------------------------------|
| `enable`   | `<module> [--init]`       | 激活指定模块                          | `epsdk enable chatgpt --init`       |
| `disable`  | `<module> [--init]`       | 停用指定模块                          | `epsdk disable weather`             |
| `list`     | `[--module=<name>] [--init]` | 列出模块（可筛选）                   | `epsdk list --module=payment`       |
| `update`   | -                         | 更新模块索引                           | `epsdk update`                      |
| `upgrade`  | `[--force] [--init]`      | 升级模块（`--force` 强制覆盖）        | `epsdk upgrade --force --init`      |
| `install`  | `<module...> [--init]`    | 安装一个或多个模块（逗号分隔）        | `epsdk install translator,analyzer` |
| `uninstall`| `<module> [--init]`       | 移除指定模块                          | `epsdk uninstall old-module --init` |

## 源管理
| 命令 | 参数 | 描述 | 示例 |
|------|------|------|------|
| `origin add` | `<url>` | 添加源 | `epsdk origin add https://example.com/source.json` |
| `origin list` | - | 源列表 | `epsdk origin list` |
| `origin del` | `<url>` | 删除源 | `epsdk origin del https://example.com/source.json` |

---

## 依赖环境

- 需要 Python 3.7 及以上
- 依赖包：`aiohttp`, `rich`, `prompt_toolkit`
- 建议使用虚拟环境管理依赖

---

## 常见问题与用法示例

### 1. 批量操作
支持通配符批量启用/禁用/安装/卸载模块，例如：
```bash
epsdk enable mod*      # 启用所有以 mod 开头的模块
epsdk uninstall *test* # 卸载所有包含 test 的模块
```

### 2. 交互式提示
部分命令支持交互式确认和自动补全（如安装/卸载/源管理），如遇到多源选择时会提示选择。

---

## 进阶用法
- 支持通过 ep、epsdk、ErisPulse、ErisPulse-CLI 任意命令调用 CLI。
- 支持通过 --init 参数强制初始化模块数据库。
- 支持 pip 依赖自动安装与卸载。

---

## 反馈与支持
如遇到 CLI 使用问题，请在 GitHub Issues 提交反馈。