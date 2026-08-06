"""
ErisPulse CLI 显示工具

提供分页、优雅输出等 UI 组件
"""

import os
from collections.abc import Callable
from typing import Any

from rich.box import SIMPLE
from rich.markup import escape
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from ..console import console
from ..i18n import i18n


def _terminal_height() -> int:
    """
    获取终端高度（行数）

    :return: [int] 终端高度，获取失败时返回 24
    """
    try:
        return os.get_terminal_size().lines
    except OSError:
        return 24


def _page_size() -> int:
    """
    根据终端高度计算每页显示的行数

    :return: [int] 每页显示行数，最小为 5
    """
    return max(_terminal_height() - 6, 5)


def _input(prompt_label: str = ">") -> str:
    """
    读取用户输入，遇到EOF或中断时返回 "q"

    :param prompt_label: [str] 提示标签 (默认: ">")
    :return: [str] 用户输入内容（已去除首尾空白）
    """
    # 转义富文本标记
    escaped = escape(prompt_label)
    console.print(f"  [dim]{escaped}[/] ", end="")
    try:
        return input().strip()
    except (EOFError, KeyboardInterrupt):
        return "q"


def prompt_validated(
    message: str,
    default: str = "",
    validate: Callable[[str], bool | str | None] | None = None,
    error_msg: str | None = None,
) -> str:
    """
    交互式输入，校验失败时保留上次输入并重新提示，直到通过校验。

    :param message: [str] 提示文本
    :param default: [str] 初始默认值（也作为校验失败后保留的可编辑值） (默认: "")
    :param validate: [Callable] 校验函数；返回 True/None 表示通过，
                     返回 False 使用 error_msg，返回字符串则作为本次错误提示 (默认: None)
    :param error_msg: [str] validate 返回 False 时的默认错误提示
    :return: [str] 通过校验的输入值
    """
    value = default
    if error_msg is None:
        error_msg = i18n.t("cli.display.invalid_input")
    while True:
        result = Prompt.ask(message, default=value)
        if validate is None:
            return result
        check = validate(result)
        if check is True or check is None:
            return result
        msg = check if isinstance(check, str) else error_msg
        console.print(f"[error]  {msg}[/]")
        value = result  # 保留输入，下次作为默认值显示供修改


def section_header(title: str):
    """
    打印格式化的分节标题

    :param title: [str] 标题文本
    """
    console.print()
    line = Text()
    line.append("  ── ", style="dim")
    line.append(title, style="bold")
    console.print(line)


def section_footer():
    """打印格式化的分节结束分隔线"""
    console.print(Text("  " + "─" * 48, style="dim"))


def tree_item(text: str, level: int = 0, is_last: bool = False):
    """
    打印树形结构的层级项

    :param text: [str] 显示文本
    :param level: [int] 层级深度 (默认: 0)
    :param is_last: [bool] 是否为同级最后一项 (默认: False)
    """
    indent = "    " * (level + 1)
    connector = "╰─ " if is_last else "├─ "
    line = Text()
    line.append(indent)
    line.append(connector, style="dim")
    line.append(text)
    console.print(line)


def info_line(text: str, level: int = 1):
    """
    打印带缩进和项目符号的信息行

    :param text: [str] 显示文本
    :param level: [int] 缩进层级 (默认: 1)
    """
    indent = "    " * level
    line = Text()
    line.append(indent)
    line.append("· ", style="dim")
    line.append(text)
    console.print(line)


def paginated_table(
    table: Table,
    items: list[Any],
    row_builder,
    page_size: int | None = None,
) -> int:
    """
    将列表项分页渲染到表格中，支持翻页交互

    :param table: [Table] 表格模板（用于列样式）
    :param items: [List[Any]] 待渲染的数据项列表
    :param row_builder: [Callable] 行构建函数，接收 (table, index, item)
    :param page_size: [Optional[int]] 每页行数，为空则自动计算 (默认: None)
    :return: [int] 已展示的项数
    """
    total = len(items)
    if total == 0:
        return 0

    ps = page_size or _page_size()
    page_start = 0

    while True:
        t = Table(
            box=table.box,
            show_lines=table.show_lines,
            header_style=table.header_style,
            pad_edge=table.pad_edge,
        )
        for col in table.columns:
            t.add_column(
                col.header, style=col.style, width=col.width, min_width=col.min_width
            )
        batch = items[page_start : page_start + ps]
        for idx_offset, item in enumerate(batch):
            row_builder(t, page_start + idx_offset, item)
        console.print(t)

        has_prev = page_start > 0
        has_next = page_start + ps < total
        if not has_prev and not has_next:
            break

        nav = []
        if has_prev:
            nav.append(i18n.t("cli.display.nav_prev"))
        if has_next:
            nav.append(i18n.t("cli.display.nav_next"))
        console.print(f"[dim]  {', '.join(nav)}, {i18n.t('cli.display.nav_return')}[/]")
        choice = _input(">")
        if choice.lower() == "q":
            break
        if choice.lower() == "n" and has_next:
            page_start += ps
        elif choice.lower() == "p" and has_prev:
            page_start = max(0, page_start - ps)

    return min(page_start + ps, total)


def interactive_select_table(
    title_text: str,
    items: list[Any],
    columns: list,
    row_builder,
    page_size: int | None = None,
) -> list[Any]:
    """
    渲染可交互多选的分页表格，支持按序号选择、翻页与确认

    :param title_text: [str] 表格标题
    :param items: [List[Any]] 待选择的数据项列表
    :param columns: [list] 表格列配置列表
    :param row_builder: [Callable] 行构建函数，接收 (table, index, item, selected)
    :param page_size: [Optional[int]] 每页行数，为空则自动计算 (默认: None)
    :return: [List[Any]] 用户选中的数据项列表
    """
    if not items:
        console.print(f"[dim]  {i18n.t('cli.display.no_items')}[/]")
        return []

    section_header(title_text)

    ps = page_size or _page_size()
    total = len(items)
    selected_indices = set()

    def _render_table(start: int):
        """
        渲染并打印从指定索引起的一页表格

        :param start: [int] 起始索引
        """
        table = Table(box=SIMPLE, show_lines=False, header_style="bold", pad_edge=False)
        for col in columns:
            table.add_column(**col)
        batch = items[start : start + ps]
        for i, item in enumerate(batch):
            gi = start + i
            row_builder(table, gi, item, gi in selected_indices)
        console.print(table)

    def _sel_label() -> str:
        """
        生成输入提示标签，附带已选序号

        :return: [str] 提示标签
        """
        if not selected_indices:
            return ">"
        sel_str = ",".join(str(i + 1) for i in sorted(selected_indices))
        return f"({sel_str}) >"

    page_start = 0
    _render_table(page_start)

    while True:
        has_prev = page_start > 0
        has_next = page_start + ps < total

        if selected_indices:
            nav = []
            if has_prev:
                nav.append(i18n.t("cli.display.nav_prev"))
            if has_next:
                nav.append(i18n.t("cli.display.nav_next"))
            nav_text = ", ".join(nav) + ", " if nav else ""
            console.print(f"[dim]  {nav_text}{i18n.t('cli.display.nav_confirm')}[/]")
        else:
            nav = []
            if has_prev:
                nav.append(i18n.t("cli.display.nav_prev"))
            if has_next:
                nav.append(i18n.t("cli.display.nav_next"))
            nav_text = ", ".join(nav) + ", " if nav else ""
            console.print(f"[dim]  {nav_text}{i18n.t('cli.display.nav_select')}[/]")

        choice = _input(_sel_label())

        if choice.lower() == "q":
            return (
                [items[i] for i in sorted(selected_indices)] if selected_indices else []
            )

        if choice.strip() == "":
            if selected_indices:
                return [items[i] for i in sorted(selected_indices)]
            continue

        if choice.lower() == "n" and has_next:
            page_start += ps
            _render_table(page_start)
            continue

        if choice.lower() == "p" and has_prev:
            page_start = max(0, page_start - ps)
            _render_table(page_start)
            continue

        try:
            for part in choice.split(","):
                idx = int(part.strip()) - 1
                if 0 <= idx < total:
                    selected_indices.add(idx)
                else:
                    console.print(
                        f"[warning]  {i18n.t('cli.display.invalid_choice', idx=idx + 1)}[/]"
                    )
        except ValueError:
            console.print(f"[warning]  {i18n.t('cli.display.enter_number')}[/]")

    return [items[i] for i in sorted(selected_indices)]
