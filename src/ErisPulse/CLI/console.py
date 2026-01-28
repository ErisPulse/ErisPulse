import sys
from rich.console import Console
from rich.theme import Theme
from rich.highlighter import RegexHighlighter

# 确保在Windows上启用颜色
if sys.platform == "win32":
    from colorama import init
    init()

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
    force_terminal=True,
    highlighter=CommandHighlighter()
)

__all__ = [
    "console",
]