"""
ErisPulse i18n 常量定义

集中管理国际化相关的常量。
"""

# 支持的语言列表（顺序即优先级）
SUPPORTED_LANGUAGES = [
    "zh-CN",  # 简体中文
    "zh-TW",  # 繁体中文
    "en",  # 英文
    "ja",  # 日文
    "ru",  # 俄文
]

# 默认语言（无法检测时的兜底语言）
# 框架原生语言为中文，因此以简体中文作为兜底
DEFAULT_LANGUAGE = "zh-CN"

# 回退语言（当当前语言缺少某个翻译键时的第一回退）
# 使用 en 作为回退，因为它是覆盖最广的通用语言
FALLBACK_LANGUAGE = "en"


__all__ = [
    "SUPPORTED_LANGUAGES",
    "DEFAULT_LANGUAGE",
    "FALLBACK_LANGUAGE",
]
