"""
CLI 内置翻译数据加载器

{!--< internal-use >!--}
{!--< /internal-use >!--}
"""

_LOCALE_FILES = {
    "zh-CN": "zh_cn",
    "zh-TW": "zh_tw",
    "en": "en",
    "ja": "ja",
    "ru": "ru",
}


def get_translations(lang_code: str) -> dict[str, str]:
    file_key = _LOCALE_FILES.get(lang_code)
    if file_key is None:
        return {}
    import importlib

    try:
        mod = importlib.import_module(f".{file_key}", package=__name__)
        return getattr(mod, "TRANSLATIONS", {})
    except (ImportError, AttributeError):
        return {}
