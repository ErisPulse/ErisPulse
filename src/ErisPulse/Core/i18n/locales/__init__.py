"""
ErisPulse 内置翻译数据包

按语言组织翻译数据，每种语言对应一个模块文件。

{!--< internal-use >!--}
框架内置翻译，外部模块请通过 i18n.register() 注册自己的翻译。
{!--< /internal-use >!--}
"""

# 文件名 -> 语言代码映射
_LOCALE_FILES = {
    "zh-CN": "zh_cn",
    "zh-TW": "zh_tw",
    "en": "en",
    "ja": "ja",
    "ru": "ru",
}


def get_translations(lang_code: str) -> dict[str, str]:
    """
    获取指定语言的内置翻译数据

    :param lang_code: 语言代码，如 "zh-CN", "en"
    :return: dict[str, str] 翻译键值对

    {!--< internal-use >!--}
    {!--< /internal-use >!--}
    """
    file_key = _LOCALE_FILES.get(lang_code)
    if file_key is None:
        return {}

    import importlib

    try:
        mod = importlib.import_module(f".{file_key}", package=__name__)
        return getattr(mod, "TRANSLATIONS", {})
    except (ImportError, AttributeError):
        return {}


__all__ = ["get_translations"]
