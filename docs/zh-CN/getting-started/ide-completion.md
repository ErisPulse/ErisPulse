# 类型存根生成（IDE 补全）

ErisPulse 通过 entry-points 动态发现模块/适配器，入口点无法在静态层面获知用户类的具体类型。
`epsdk types` 命令通过扫描已安装的模块/适配器，生成一个类型存根文件，让用户可以用这些类型作为变量标注，从而获得 IDE 补全。

## 核心设计原则

存根文件**只导出类型**，不提供任何运行时实例：

- 所有导入都在 ``TYPE_CHECKING`` 下，**零运行时开销、零行为改变**
- 类型名采用 entry-point 名的 PascalCase 形式（如 ``yunhu`` → ``Yunhu``），与传入 ``sdk.adapter.get()`` / ``sdk.module.get()`` 的名称对应
- 用户在代码里照常用 ``sdk.module.get(...)`` / ``sdk.adapter.get(...)`` 获取实例，只是用导入的类型做**变量标注**

## 基本用法

在项目根目录运行：

```bash
epsdk types
```

会在当前目录生成 `_ep_types.py`，包含所有已安装模块/适配器的类型。

## 在代码中使用

```python
from _ep_types import MyModule, Yunhu
from ErisPulse import sdk

# 用导入的类型作为变量标注，即可让 IDE 补全该类的方法
my_mod: MyModule = sdk.module.get("MyModule")
my_mod.hello()                  # ← IDE 补全 hello

my_adapter: Yunhu = sdk.adapter.get("yunhu")
await my_adapter.Send.To("group", "123").Board(...)   # ← 补全平台特有方法
```

## 工作原理

1. 扫描 `erispulse.adapter` / `erispulse.module` entry-points
2. 通过子进程在目标 Python 环境中内省，收集每个适配器/模块的实际类信息（包含模块路径与限定名）
3. 生成 `.py` 文件，其中：
   - 所有 ``from xxx import Yyy as Zzz`` 都在 ``TYPE_CHECKING`` 下
   - ``Zzz`` 是 entry-point 名的 PascalCase 形式
4. IDE 读取 ``TYPE_CHECKING`` 部分提供补全；运行时不执行任何代码

生成的存根示例：

```python
# _ep_types.py（自动生成）
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 适配器
    from MyAdapter.Core import MyAdapter as MyAdapter
    from YunhuAdapter.Core import YunhuAdapter as Yunhu

    # 模块
    from MyModule.Core import Main as MyModule

    __all__ = ['MyAdapter', 'Yunhu', 'MyModule']
```

## 命令选项

| 选项 | 说明 |
|------|------|
| `-o, --output PATH` | 指定输出文件路径（默认 `./_ep_types.py`） |
| `--force` | 覆盖已存在的存根文件 |
| `--adapters-only` | 仅扫描适配器 |
| `--modules-only` | 仅扫描模块 |

## 何时重新生成

- 安装/卸载新的模块或适配器后
- 模块/适配器更新了公开 API 后
- IDE 补全失效或类型过期时

## 与 SendDSL 标准方法的关系

`SendDSL` 基类已内置标准发送方法（Text/Image/Voice/Video/File），任何方式获取的 SendDSL 实例都能补全这些方法。
`types` 命令主要用于补全**平台特有方法**（如云湖的 `Board`、沙盒的 `Dice`）和**模块特有方法**。

## 相关文档

- [SendDSL 详解](../developer-guide/adapters/send-dsl.md) - 标准发送方法说明
- [适配器开发入门](../developer-guide/adapters/getting-started.md) - 创建适配器
