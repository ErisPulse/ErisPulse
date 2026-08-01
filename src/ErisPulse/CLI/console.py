"""
CLI 控制台模块

提供全局 Rich 控制台实例、主题样式与启动 Banner。

{!--< tips >!--}
1. 所有 CLI 输出统一使用全局 `console` 实例，保证样式一致
2. 通过 `print_banner()` 输出一次性 Banner（仅首次生效）
{!--< /tips >!--}
"""

from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.theme import Theme

BANNER = (
    "\n\n"
    "███████╗██████╗ ██╗███████╗██████╗ ██╗   ██╗██╗     ███████╗███████╗\n"
    "██╔════╝██╔══██╗██║██╔════╝██╔══██╗██║   ██║██║     ██╔════╝██╔════╝\n"
    "█████╗  ██████╔╝██║███████╗██████╔╝██║   ██║██║     ███████╗█████╗  \n"
    "██╔══╝  ██╔══██╗██║╚════██║██╔═══╝ ██║   ██║██║     ╚════██║██╔══╝  \n"
    "███████╗██║  ██║██║███████║██║     ╚██████╔╝███████╗███████║███████╗\n"
    "╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚═╝      ╚═════╝ ╚══════╝╚══════╝╚══════╝\n"
    "\n"
)

_BANNER_MINI = (
    "\n\n"
    "███████╗██████╗ ███████╗██████╗ ██╗  ██╗\n"
    "██╔════╝██╔══██╗██╔════╝██╔══██╗██║ ██╔╝\n"
    "█████╗  ██████╔╝███████╗██║  ██║█████╔╝ \n"
    "██╔══╝  ██╔═══╝ ╚════██║██║  ██║██╔═██╗ \n"
    "███████╗██║     ███████║██████╔╝██║  ██╗\n"
    "╚══════╝╚═╝     ╚══════╝╚═════╝ ╚═╝  ╚═╝\n"
    "\n"
)


_banner_printed = False


def print_banner():
    """
    输出 ErisPulse 启动 Banner

    根据终端宽度选择完整版或精简版 Banner，且仅在首次调用时输出。
    """
    global _banner_printed
    if _banner_printed:
        return
    _banner_printed = True
    width = console.width
    if width >= 75:
        console.print(BANNER, style="bold white", highlight=False)
    else:
        console.print(_BANNER_MINI, style="bold white", highlight=False)


class CommandHighlighter(RegexHighlighter):
    """
    高亮CLI命令和参数

    {!--< tips >!--}
    使用正则表达式匹配命令行参数和选项
    {!--< /tips >!--}
    """

    highlights = [
        r"(?P<switch>\-\-?\w+)",
        r"(?P<option>\[\w+\])",
        r"(?P<command>\b\w+\b)",
    ]


# 主题配置
theme: Theme = Theme(
    {
        "info": "#A0B0C0",
        "success": "#A5D6A7",
        "warning": "#FFCC80",
        "error": "#FFCDD2",
        "title": "#7DBFE0",
        "default": "default",
        "progress": "#A5D6A7",
        "progress.remaining": "#283545",
        "cmd": "#90CAF9",
        "param": "#80CBC4",
        "switch": "#FFCC80",
        "module": "#80CBC4",
        "adapter": "#7DBFE0",
        "cli": "#A0B0C0",
        "hint": "#CE93D8",
    }
)

# 全局控制台实例
console: Console = Console(theme=theme, color_system="auto", highlighter=CommandHighlighter())


def print_suggestion(title: str, suggestions: list[str], hint: str | None = None) -> None:
    """
    输出错误提示与建议

    统一 CLI 错误输出的视觉层次：错误标题 → 建议命令 → 补充提示。

    :param title: [str] 错误标题（一句话说明发生了什么）
    :param suggestions: [list[str]] 建议的命令/名称列表（如 ["epsdk init", "epsdk install xxx"]）
    :param hint: [str | None] 补充提示（可选，如“浏览可用包：epsdk list-remote”）
    """
    console.print(f"[error]✗ {title}[/]")
    console.print()
    console.print("[hint]Did you mean this?[/]" if len(suggestions) == 1 else "[hint]Did you mean one of these?[/]")
    console.print()
    for s in suggestions:
        console.print(f"    [cmd]{s}[/]")
    if hint:
        console.print()
        console.print(f"[dim]{hint}[/]")
    console.print()


__all__ = [
    "console",
    "print_banner",
    "print_suggestion",
]
