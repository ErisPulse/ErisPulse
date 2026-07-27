"""
ErisPulse 通用配置 Schema 模块（向后兼容 shim）

实际定义已迁移至 :mod:`ErisPulse.Core.Bases.config_schema`。
本模块通过 ``__getattr__`` 懒加载，避免在 runtime 包初始化阶段触发
``Core.Bases.__init__`` 的完整加载链（会引入 lifecycle → runtime 循环）。

{!--< internal-use >!--}
新增代码请从 ``ErisPulse.Core.Bases`` 导入。
{!--< /internal-use >!--}
"""

__all__ = [
    "AdapterConfig",  # noqa: F822  ← BaseConfig 的别名
    "BaseConfig",  # noqa: F822
    "BotAccountConfig",  # noqa: F822
    "I18nConfig",  # noqa: F822
    "dataclass_to_defaults_dict",  # noqa: F822
    "dataclass_to_toml_with_comments",  # noqa: F822
    "dict_to_dataclass",  # noqa: F822
    "get_config_schema",  # noqa: F822
    "register_config_i18n",  # noqa: F822
    "resolve_config_schema",  # noqa: F822
    "validate_config",  # noqa: F822
]


def __getattr__(name: str):
    """懒加载：首次访问时从 Core.Bases.config_schema 导入"""
    if name in __all__:
        from ..Core.Bases.config_schema import __dict__ as _src

        if name in _src:
            value = _src[name]
            globals()[name] = value  # 缓存，后续访问直接命中
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
