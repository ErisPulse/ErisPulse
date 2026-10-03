# `ErisPulse.CLI.utils.interactive` 模块

---

## 模块概述


CLI 交互式提示统一封装

所有命令的 yes/no 确认与列表选择统一经此模块发出，职责：

1. 消费全局 ``--yes/-y`` 参数：assume-yes 模式下确认类提示自动返回 True、
   列表选择自动取默认项（此前该参数仅在帮助文本中承诺、从未被任何命令读取）
2. 非 TTY（管道 / CI / 重定向）且未启用 assume-yes 时抛出
   :class:`NonInteractiveError` 明确报错——rich 的 Confirm/Prompt 在关闭的
   stdin 上会以 EOFError 崩溃或永久挂起

自由文本输入（搜索词 / 版本号 / 配置字段值等无法推断答案的提示）不经此
封装，保持交互行为不变。

> **提示**
> 用法（命令实现中替换 Confirm.ask / 列表选择 Prompt.ask）：
> ```python
> from .interactive import confirm, select
> if confirm("继续安装？", default=False): ...
> choice = select("选择模板", choices=["1", "2"], default="1")
> ```
>

---

## 函数列表


### `set_assume_yes(value: bool) -> None`

设置 assume-yes 模式（由 CLI 主入口在解析 ``--yes/-y`` 后调用）

- **value**: 是否自动确认所有交互提示

---


### `assume_yes() -> bool`

查询 assume-yes 模式状态

**返回值**: 是否处于自动确认模式

---


### `_is_interactive() -> bool`

判断当前是否为可交互环境

**返回值** (`stdin`): 为 TTY 时返回 True

---


### `_require_interactive() -> None`

非交互环境且未启用 assume-yes 时抛出明确错误

**异常**: `NonInteractiveError` - stdin 非 TTY 且未启用 ``--yes/-y``

---


### `confirm(message: str, *, default: bool = False, **kwargs) -> bool`

yes/no 确认提示（统一入口）

assume-yes 模式（``--yes/-y``）下直接返回 True；非 TTY 且未启用
assume-yes 时抛出 :class:`NonInteractiveError`。

- **message**: 提示文案（可含 Rich 标记）
- **default**: 用户直接回车时的默认取值（交互模式下透传给 Confirm）
- **kwargs**: 其余参数透传 rich Confirm.ask

**返回值**: 用户是否确认

**异常**: `NonInteractiveError` - 非交互环境且未启用 ``--yes/-y``

---


### `select(message: str, *, choices: list | None = None, default: str | None = None, **kwargs) -> str`

列表选择提示（统一入口）

assume-yes 模式（``--yes/-y``）或非 TTY 环境下自动取默认项；
无默认项可选时抛出 :class:`NonInteractiveError`（无法推断答案）。

- **message**: 提示文案（可含 Rich 标记）
- **choices**: 合法选项列表（透传 rich Prompt.ask）
- **default**: 默认选项
- **kwargs**: 其余参数透传 rich Prompt.ask

**返回值**: 用户选择的选项（或自动应答的默认项）

**异常**: `NonInteractiveError` - 无法自动应答且无默认项

---


## 类列表


### `class NonInteractiveError(RuntimeError)`

非交互环境遇到无法自动应答的交互提示

在 ``--yes/-y`` 未启用且 stdin 非 TTY 时抛出，提示改用 ``-y``
或在 TTY 中运行（由 CLI 主入口捕获并作为错误输出）。

