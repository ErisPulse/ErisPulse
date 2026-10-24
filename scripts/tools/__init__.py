"""ErisPulse 仓库工具集（工程棘轮检查 / 文档生成 / 翻译 / 发布闸门）。

统一入口：``python -m scripts.tools <组> <名> [参数]``（见 ``__main__.py``）。

组与子命令::

    check   import-layers | bare-params | silent-except | i18n-locales
            | docs-links | translation | release-check
    gen     api-docs | ai-prompts | docs-index | skills | type-stubs
    translate   （透传 translate.py 全部参数）

各模块约定：导出 ``main(argv: list[str] | None = None)``，内部 argparse
以 ``parse_args(argv)`` 解析（无参时回退 sys.argv[1:]，直接运行模块仍可用）。
"""
