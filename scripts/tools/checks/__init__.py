"""工程棘轮检查组：CI code-quality-check / 发布闸门的子命令注册表。

键为 ``python -m scripts.tools check <名>`` 的子命令名；
值为 ``(帮助文案, main 函数)``——main 接收 ``argv`` 列表（不含组名/子命令名）。
"""

from . import bare_params, docs_links, i18n_locales, import_layers, release_check, silent_except, translation

CHECKS = {
    "import-layers": ("导入分层棘轮检查（loaders/runtime/Core 禁向内依赖）", import_layers.main),
    "bare-params": ("裸参数棘轮检查（行为参数必须进 Core/constants.py）", bare_params.main),
    "silent-except": ("静默吞异常棘轮检查（except pass 必须留痕或入基线）", silent_except.main),
    "i18n-locales": ("i18n 五语言键集合一致性检查", i18n_locales.main),
    "docs-links": ("文档死链检查", docs_links.main),
    "translation": ("翻译产物质检（提示词残留 / 围栏 / 长度比）", translation.main),
    "release-check": ("发布闸门：版本号 / CHANGELOG 条目核对", release_check.main),
}

__all__ = ["CHECKS"]
