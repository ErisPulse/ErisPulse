"""统一 CLI 入口：``python -m scripts.tools <组> <名> [参数]``

分发为「手工解析组名 + 子命令名，剩余参数原样透传给目标模块的 main(argv)」——
各子命令的 argparse 在自身 main 内解析（含各自的 --help），外层不做嵌套
argparse（嵌套会让组级 --help 吞掉子命令级 --help）。

直接运行模块（``python scripts/tools/checks/bare_params.py``）同样可用：
main 无 argv 时回退 sys.argv[1:]。
"""

from __future__ import annotations

import sys

from .checks import CHECKS
from .generators import GENERATORS

USAGE = """\
用法: python -m scripts.tools <组> <名> [参数...]

组:
  check         工程棘轮检查（import-layers / bare-params / silent-except /
                i18n-locales / docs-links / translation / release-check）
  gen           文档生成器（api-docs / ai-prompts / docs-index / skills / type-stubs）
  translate     文档翻译器（透传 translate.py 全部参数，--help 查看详情）
  auto-translate 自动循环翻译（检测→翻译→验证→循环直到完成）

示例:
  python -m scripts.tools check import-layers
  python -m scripts.tools gen ai-prompts --lang zh-CN
  python -m scripts.tools translate --time-budget 30
  python -m scripts.tools auto-translate --max-rounds 5
"""


def main(argv: list[str] | None = None) -> int:
    """统一入口分发器

    :param argv: 参数列表（不含程序名）；None 时取 sys.argv[1:]
    :return: 目标子命令的退出码
    """
    args = list(sys.argv[1:] if argv is None else argv)

    if not args or args[0] in ("-h", "--help"):
        print(USAGE)
        return 0

    group = args.pop(0)
    if group == "check":
        registry = CHECKS
        group_help = "可用检查: " + ", ".join(sorted(registry))
    elif group == "gen":
        registry = GENERATORS
        group_help = "可用生成器: " + ", ".join(sorted(registry))
    elif group == "translate":
        import asyncio

        from .translate import main as translate_main

        return int(asyncio.run(translate_main(args)) or 0)
    elif group == "auto-translate":
        import asyncio

        from .auto_translate import main as auto_translate_main

        return int(asyncio.run(auto_translate_main(args)) or 0)
    else:
        print(f"未知组: {group}\n\n{USAGE}", file=sys.stderr)
        return 2

    if not args or args[0] in ("-h", "--help"):
        print(f"用法: python -m scripts.tools {group} <名> [参数...]\n{group_help}")
        return 0

    name = args.pop(0)
    entry = registry.get(name)
    if entry is None:
        print(
            f"未知子命令: {group} {name}\n{group_help}",
            file=sys.stderr,
        )
        return 2

    _help_text, fn = entry
    return int(fn(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
