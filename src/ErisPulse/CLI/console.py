import sys
from rich.console import Console
from rich.theme import Theme
from rich.highlighter import RegexHighlighter

BANNER = (
    "\n\n"
    "███████╗██████╗ ██╗███████╗██████╗ ██╗   ██╗██╗     ███████╗███████╗\n"
    "██╔════╝██╔══██╗██║██╔════╝██╔══██╗██║   ██║██║     ██╔════╝██╔════╝\n"
    "█████╗  ██████╔╝██║███████╗██████╔╝██║   ██║██║     ███████╗█████╗  \n"
    "██╔══╝  ██╔══██╗██║╚════██║██╔═══╝ ██║   ██║██║     ╚════██║██╔══╝  \n"
    "███████╗██║  ██║██║███████║██║     ╚██████╔╝███████╗███████║███████╗\n"
    "╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚═╝      ╚═════╝ ╚══════╝╚══════╝╚══════╝\n"
    "\n\n"
)

_BANNER_MINI = (
    "\n\n"
    "███████╗██████╗ ███████╗██████╗ ██╗  ██╗\n"
    "██╔════╝██╔══██╗██╔════╝██╔══██╗██║ ██╔╝\n"
    "█████╗  ██████╔╝███████╗██║  ██║█████╔╝ \n"
    "██╔══╝  ██╔═══╝ ╚════██║██║  ██║██╔═██╗ \n"
    "███████╗██║     ███████║██████╔╝██║  ██╗\n"
    "╚══════╝╚═╝     ╚══════╝╚═════╝ ╚═╝  ╚═╝\n"
    "\n\n"
)


_banner_printed = False

def print_banner():
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
theme = Theme({
    "info": "dim cyan",
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "title": "bold magenta",
    "default": "default",
    "progress": "green",
    "progress.remaining": "white",
    "cmd": "bold blue",
    "param": "italic cyan",
    "switch": "bold yellow",
    "module": "bold green",
    "adapter": "bold yellow",
    "cli": "bold magenta",
})

# 全局控制台实例
console = Console(
    theme=theme, 
    color_system="auto", 
    highlighter=CommandHighlighter()
)

__all__ = [
    "console",
    "print_banner",
]