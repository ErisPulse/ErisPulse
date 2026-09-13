"""
SDK 版本解析与比较

框架内唯一的版本号解析/比较实现（PEP 440 子集，纯标准库，不依赖 packaging），
供加载器在组件加载时执行运行时最低 SDK 版本检查
（组件以 ``get_meta().min_sdk_version`` 或类属性 ``min_sdk_version`` 声明），
CLI 包管理器（``CLI/utils/package_manager.py``）亦复用同一解析口径。

{!--< tips >!--}
1. 组件声明 ``min_sdk_version = "2.8.1"`` 后，SDK 低于该版本时加载期将被明确报错并跳过
2. 未声明、当前版本未知或任一侧无法解析时一律放行——版本检查绝不阻塞框架启动
{!--< /tips >!--}
"""

import re
from typing import Any, Final

_SDK_DIST_NAME: Final[str] = "ErisPulse"
_UNKNOWN_VERSION: Final[str] = "unknown"

# 版本号解析正则（PEP 440 子集）：
# 支持 epoch (1!)、release 段、预发布后缀 (dev/a/alpha/b/beta/rc/c/pre)、
# post 版本 (1.0.postN) 与本地版本 (1.0+local)。
# 例如 2.5.0-dev.1 / 2.5.0a1 / 1.0rc1 / 1.0.post1 / 1.0+local / 1!1.0 均可解析。
# 不支持的格式（如 1.0.post1.dev1 这类 post 后跟 dev）由 parse_version 返回 None 退化处理。
_VERSION_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*v?(?P<epoch>\d+!)?(?P<release>\d+(?:\.\d+)*)"
    r"(?:[-._]?(?P<pre>dev|alpha|beta|rc|a|b|c|pre)[-._]?(?P<num>\d*))?"
    r"(?:[-._]?post[-._]?(?P<post>\d+))?"
    r"(?:\+(?P<local>[a-zA-Z0-9]+(?:[.-][a-zA-Z0-9]+)*))?",
    re.IGNORECASE,
)
# 预发布类型排序权重：正式版 > rc > beta > alpha > dev
_PRE_RELEASE_RANK: Final[dict[str, int]] = {
    "dev": 0,
    "alpha": 1,
    "a": 1,
    "beta": 2,
    "b": 2,
    "rc": 3,
    "c": 3,
    "pre": 3,
}


def parse_version(version: str) -> dict[str, Any] | None:
    """
    将版本号解析为结构化组件（PEP 440 子集，纯标准库）

    :param version: str 版本号字符串
    :return: dict 含 epoch/release/pre_type/pre_num/post/local 的字典，
             无法解析时返回 None
    """
    match = _VERSION_RE.match(str(version).strip().lstrip("vV"))
    if not match:
        return None
    return {
        "epoch": int((match.group("epoch") or "0").rstrip("!") or 0),
        "release": match.group("release"),
        "pre_type": match.group("pre"),
        "pre_num": match.group("num"),
        "post": match.group("post"),
        "local": match.group("local"),
    }


def version_key(version: str) -> tuple[Any, ...]:
    """
    将版本号解析为可比较的元组键

    遵循项目命名规则排序：正式版 > post > rc > beta > alpha > dev；
    epoch 优先于一切 release 段；本地版本 (+local) 不影响主排序，
    但同一版本号带 local 段者 > 不带 local 段者。
    例如 2.4.5-dev.1 先于 2.4.5 正式版，1.0 < 1.0.post1 < 1.1。

    :param version: str 版本号字符串
    :return: tuple 逐段可比较的比较键元组
    """
    parsed = parse_version(version)
    if parsed is None:
        # 无法解析时退化为字符串比较，保证不抛异常
        return (0, (0, 0, 0, 0), (1,), (0,), ((1, str(version).lower()),))

    release = tuple(int(x) for x in parsed["release"].split("."))
    # release 段对齐到固定长度，确保 (2.5) 与 (2.5.0) 能正确比较
    padded = release + (0,) * max(0, 4 - len(release))

    pre_type = parsed["pre_type"]
    if pre_type is None:
        # 正式版：预发布键恒大于任何预发布版本
        pre_key = (1,)
    else:
        rank = _PRE_RELEASE_RANK.get(pre_type.lower(), 1)
        pre_num = int(parsed["pre_num"] or 0)
        pre_key = (0, rank, pre_num)

    # post 段（无 post 记为 post0，保证 1.0 == 1.0.post0 < 1.0.post1）
    post_num = int(parsed["post"] or 0)
    post_key = (post_num,)

    local = parsed["local"]
    if local:
        # 本地段按 "数值段 < 字母段" 分组，避免 int/str 直接比较抛异常
        local_key = tuple(
            (0, int(part)) if part.isdigit() else (1, part.lower())
            for part in local.split(".")
        )
    else:
        local_key = ()

    return (parsed["epoch"], padded, pre_key, post_key, local_key)


def compare_versions(version_a: str, version_b: str) -> int:
    """
    比较两个版本号

    :param version_a: str 版本号 A
    :param version_b: str 版本号 B
    :return: int A < B 返回负数，相等返回 0，A > B 返回正数；
             任一侧无法解析时退化为字符串比较，保证不抛异常
    """
    key_a = version_key(version_a)
    key_b = version_key(version_b)
    if key_a > key_b:
        return 1
    if key_a < key_b:
        return -1
    return 0


def check_min_sdk_version(min_required: str) -> tuple[bool, str, str, bool]:
    """
    检查当前 SDK 版本是否满足组件声明的最低版本要求

    :param min_required: str 组件声明的最低 SDK 版本（如 ``"2.8.1"``）
    :return: tuple[bool, str, str, bool]
        (是否满足, 当前 SDK 版本, 规范化后的要求版本, 声明是否可解析)；
        声明为空、当前版本未知或声明无法解析时视为满足
        （放行，解析标记为 False），版本检查绝不阻塞框架启动
    """
    current = _get_sdk_version()
    required = min_required.strip()
    if not required:
        return True, current, required, True
    if current == _UNKNOWN_VERSION:
        return True, current, required, True
    if parse_version(required) is None or parse_version(current) is None:
        return True, current, required, False
    return compare_versions(current, required) >= 0, current, required, True


def _get_sdk_version() -> str:
    """
    获取当前安装的 ErisPulse SDK 版本

    经包元数据读取（与 :data:`ErisPulse.__version__` 同源），避免依赖根包导入。

    :return: str 版本号；元数据不可用时返回 "unknown"
    """
    import importlib.metadata

    try:
        return importlib.metadata.version(_SDK_DIST_NAME)
    except Exception:
        return _UNKNOWN_VERSION
