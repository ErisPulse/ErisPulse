"""
ErisPulse CLI 显示工具

提供分页、优雅输出等 UI 组件
"""

import os
from typing import List, Any, Optional

from rich.text import Text
from rich.table import Table
from rich.box import SIMPLE

from ..console import console


def _terminal_height() -> int:
    try:
        return os.get_terminal_size().lines
    except OSError:
        return 24


def _page_size() -> int:
    return max(_terminal_height() - 6, 5)


def _input(prompt_label: str = ">") -> str:
    console.print(f"  [dim]{prompt_label}[/] ", end="")
    try:
        return input().strip()
    except (EOFError, KeyboardInterrupt):
        return "q"


def section_header(title: str):
    console.print()
    line = Text()
    line.append("  ── ", style="dim")
    line.append(title, style="bold")
    console.print(line)


def section_footer():
    console.print(Text("  " + "─" * 48, style="dim"))


def tree_item(text: str, level: int = 0, is_last: bool = False):
    indent = "    " * (level + 1)
    connector = "╰─ " if is_last else "├─ "
    line = Text()
    line.append(indent)
    line.append(connector, style="dim")
    line.append(text)
    console.print(line)


def info_line(text: str, level: int = 1):
    indent = "    " * level
    line = Text()
    line.append(indent)
    line.append("· ", style="dim")
    line.append(text)
    console.print(line)


def paginated_table(
    table: Table,
    items: List[Any],
    row_builder,
    page_size: Optional[int] = None,
) -> int:
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
            nav.append("p 上一页")
        if has_next:
            nav.append("n 下一页")
        console.print(f"[dim]  {', '.join(nav)}, q 返回[/]")
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
    items: List[Any],
    columns: list,
    row_builder,
    page_size: Optional[int] = None,
) -> List[Any]:
    if not items:
        console.print("[dim]  没有可选项[/]")
        return []

    section_header(title_text)

    ps = page_size or _page_size()
    total = len(items)
    selected_indices = set()

    def _render_table(start: int):
        table = Table(box=SIMPLE, show_lines=False, header_style="bold", pad_edge=False)
        for col in columns:
            table.add_column(**col)
        batch = items[start : start + ps]
        for i, item in enumerate(batch):
            gi = start + i
            row_builder(table, gi, item, gi in selected_indices)
        console.print(table)

    def _sel_label() -> str:
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
                nav.append("p 上一页")
            if has_next:
                nav.append("n 下一页")
            nav_text = ", ".join(nav) + ", " if nav else ""
            console.print(f"[dim]  {nav_text}Enter 确认, q 返回[/]")
        else:
            nav = []
            if has_prev:
                nav.append("p 上一页")
            if has_next:
                nav.append("n 下一页")
            nav_text = ", ".join(nav) + ", " if nav else ""
            console.print(f"[dim]  {nav_text}输入序号选择, q 返回[/]")

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
                    console.print(f"[warning]  序号 {idx + 1} 无效[/]")
        except ValueError:
            console.print("[warning]  请输入数字序号[/]")

    return [items[i] for i in sorted(selected_indices)]
