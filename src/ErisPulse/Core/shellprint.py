import sys

class Shell_Printer:
    # ANSI 颜色代码
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    BG_BLUE = "\033[44m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_RED = "\033[41m"

    def __init__(self):
        pass

    @classmethod
    def _get_color(cls, level):
        return {
            "info": cls.CYAN,
            "success": cls.GREEN,
            "warning": cls.YELLOW,
            "error": cls.RED,
            "title": cls.MAGENTA,
            "default": cls.RESET,
        }.get(level, cls.RESET)

    @classmethod
    def panel(cls, msg: str, title: str = None, level: str = "info") -> None:
        color = cls._get_color(level)
        width = 70
        border_char = "─" * width
        
        if level == "error":
            border_char = "═" * width
            msg = f"{cls.RED}✗ {msg}{cls.RESET}"
        elif level == "warning":
            border_char = "─" * width
            msg = f"{cls.YELLOW}⚠ {msg}{cls.RESET}"
        
        title_line = ""
        if title:
            title = f" {title.upper()} "
            title_padding = (width - len(title)) // 2
            left_pad = " " * title_padding
            right_pad = " " * (width - len(title) - title_padding)
            title_line = f"{cls.DIM}┌{left_pad}{cls.BOLD}{color}{title}{cls.RESET}{cls.DIM}{right_pad}┐{cls.RESET}\n"
        
        lines = []
        for line in msg.split("\n"):
            if len(line) > width - 4:
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) + 1 > width - 4:
                        lines.append(f"{cls.DIM}│{cls.RESET} {current_line.ljust(width-4)} {cls.DIM}│{cls.RESET}")
                        current_line = word
                    else:
                        current_line += (" " + word) if current_line else word
                if current_line:
                    lines.append(f"{cls.DIM}│{cls.RESET} {current_line.ljust(width-4)} {cls.DIM}│{cls.RESET}")
            else:
                lines.append(f"{cls.DIM}│{cls.RESET} {line.ljust(width-4)} {cls.DIM}│{cls.RESET}")
        
        if level == "error":
            border_style = "╘"
        elif level == "warning":
            border_style = "╧"
        else:
            border_style = "└"
        bottom_border = f"{cls.DIM}{border_style}{border_char}┘{cls.RESET}"
        
        panel = f"{title_line}"
        panel += f"{cls.DIM}├{border_char}┤{cls.RESET}\n"
        panel += "\n".join(lines) + "\n"
        panel += f"{bottom_border}\n"
        
        print(panel)

    @classmethod
    def table(cls, headers, rows, title=None, level="info") -> None:
        color = cls._get_color(level)
        if title:
            print(f"{cls.BOLD}{color}== {title} =={cls.RESET}")
        
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        fmt = "│".join(f" {{:<{w}}} " for w in col_widths)
        
        top_border = "┌" + "┬".join("─" * (w+2) for w in col_widths) + "┐"
        print(f"{cls.DIM}{top_border}{cls.RESET}")
        
        header_line = fmt.format(*headers)
        print(f"{cls.BOLD}{color}│{header_line}│{cls.RESET}")
        
        separator = "├" + "┼".join("─" * (w+2) for w in col_widths) + "┤"
        print(f"{cls.DIM}{separator}{cls.RESET}")
        
        for row in rows:
            row_line = fmt.format(*row)
            print(f"│{row_line}│")
        
        bottom_border = "└" + "┴".join("─" * (w+2) for w in col_widths) + "┘"
        print(f"{cls.DIM}{bottom_border}{cls.RESET}")

    @classmethod
    def progress_bar(cls, current, total, prefix="", suffix="", length=50):
        filled_length = int(length * current // total)
        percent = min(100.0, 100 * (current / float(total)))
        bar = f"{cls.GREEN}{'█' * filled_length}{cls.WHITE}{'░' * (length - filled_length)}{cls.RESET}"
        sys.stdout.write(f"\r{cls.BOLD}{prefix}{cls.RESET} {bar} {cls.BOLD}{percent:.1f}%{cls.RESET} {suffix}")
        sys.stdout.flush()
        if current == total:
            print()

    @classmethod
    def confirm(cls, msg, default=False) -> bool:
        yes_options = {'y', 'yes'}
        no_options = {'n', 'no'}
        default_str = "Y/n" if default else "y/N"
        prompt = f"{cls.BOLD}{msg}{cls.RESET} [{cls.CYAN}{default_str}{cls.RESET}]: "
        
        while True:
            ans = input(prompt).strip().lower()
            if not ans:
                return default
            if ans in yes_options:
                return True
            if ans in no_options:
                return False
            print(f"{cls.YELLOW}请输入 'y' 或 'n'{cls.RESET}")

    @classmethod
    def ask(cls, msg, choices=None, default="") -> str:
        prompt = f"{cls.BOLD}{msg}{cls.RESET}"
        if choices:
            prompt += f" ({cls.CYAN}{'/'.join(choices)}{cls.RESET})"
        if default:
            prompt += f" [{cls.BLUE}默认: {default}{cls.RESET}]"
        prompt += ": "
        
        while True:
            ans = input(prompt).strip()
            if not ans and default:
                return default
            if not choices or ans in choices:
                return ans
            print(f"{cls.YELLOW}请输入有效选项: {', '.join(choices)}{cls.RESET}")

    @classmethod
    def status(cls, msg, success=True):
        symbol = f"{cls.GREEN}✓" if success else f"{cls.RED}✗"
        print(f"\r{symbol}{cls.RESET} {msg}")

shellprint = Shell_Printer()