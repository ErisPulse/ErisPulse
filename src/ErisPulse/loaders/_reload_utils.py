"""
热重载共用工具：字节码缓存清理与卸载前语法预检

模块与适配器两条重载管线共用的唯一实现；两侧薄封装只负责收集候选
源文件与提供各自的 i18n 文案键。
"""

import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ..Core.constants import MODULE_RELOAD_PRECHECK_MAX_FILES
from ..Core.i18n import i18n
from ..Core.logger import logger

__all__ = [
    "clear_source_caches",
    "clear_source_caches_for_files",
    "expand_source_files",
    "precheck_source_files",
    "precheck_source_trees",
]


def expand_source_files(file_attrs: Iterable[Any]) -> "list[Path]":
    """
    把一组 ``__file__`` 候选展开为源文件列表

    包入口（``__init__.py``）递归展开为包内全部 ``.py``；单文件仅接受
    ``.py`` 后缀（C 扩展 / 内存模块天然跳过）。

    :param file_attrs: ``__file__`` 属性值候选（None / 空值自动跳过）
    :return: 去重后的源文件路径列表
    """
    source_files: list[Path] = []
    seen: set[str] = set()
    for file_attr in file_attrs:
        if not file_attr:
            continue
        path = Path(file_attr)
        if path.name == "__init__.py":
            files = sorted(path.parent.rglob("*.py"))
        elif path.suffix == ".py":
            files = [path]
        else:
            continue
        for f in files:
            key = str(f)
            if key not in seen:
                seen.add(key)
                source_files.append(f)
    return source_files


def clear_source_caches(mods: Iterable[Any]) -> None:
    """
    清除模块对象对应源文件的字节码缓存（``__pycache__``/*.pyc）

    同秒内且字节数不变的源码改写不会使 pyc 失效（mtime 秒级粒度 +
    size 校验），purge ``sys.modules`` 后重导入仍会命中旧字节码——
    重载路径必须显式清除，保证「改完代码再 reload 必定读到新代码」。

    :param mods: 模块对象（或 None）的可迭代集合
    """
    import importlib.util

    for mod in mods:
        file_attr = getattr(mod, "__file__", None) if mod else None
        if not file_attr:
            continue
        path = Path(file_attr)
        if path.name == "__init__.py":
            candidates = sorted(path.parent.rglob("*.py"))
        else:
            candidates = [path]
        for py in candidates:
            try:
                cache = importlib.util.cache_from_source(str(py))
                if cache:
                    Path(cache).unlink(missing_ok=True)
            except Exception:
                pass


def clear_source_caches_for_files(source_files: Iterable[Path]) -> None:
    """
    按源文件路径直接清除字节码缓存（``__pycache__``/*.pyc）

    与 :func:`clear_source_caches` 的区别：不依赖 ``sys.modules`` 中
    仍存在对应模块对象——适合在卸载/purge **之前**、只有文件路径
    可用的场景（如整体重载的统一预清理）。

    :param source_files: 源文件路径列表
    """
    import importlib.util

    for py in source_files:
        try:
            cache = importlib.util.cache_from_source(str(py))
            if cache:
                Path(cache).unlink(missing_ok=True)
        except Exception:
            pass


def module_objects_by_names(names: "list[str]") -> "list[Any]":
    """
    按顶层模块名从 ``sys.modules`` 收集现存模块对象

    :param names: 顶层模块名列表
    :return: 找到的模块对象（缺失名跳过）
    """
    return [mod for name in names if (mod := sys.modules.get(name)) is not None]


def check_reload_identity(*, new_class: Any, old_class: Any, label: str, i18n_key: str) -> bool:
    """
    重载后的类身份核对：新旧类对象是否不同

    新旧类均非空时按 ``is`` 比对；身份未变化说明进程内可能仍运行旧代码
    （如 C 扩展等清不掉的缓存），告警提示。

    :param new_class: 重载后注册表中的类对象
    :param old_class: 重载前快照中的类对象
    :param label: 组件名（日志用）
    :param i18n_key: 身份未变化告警的文案键（调用方按组件类型提供）
    :return: identity_changed（True = 代码确实换新）
    """
    identity_changed = bool(
        new_class is not None and old_class is not None and new_class is not old_class
    )
    if new_class is not None and new_class is old_class:
        logger.warning(i18n.t(i18n_key, name=label))
    return identity_changed


def _is_encoding_error(e: BaseException) -> bool:
    """
    判断预检异常是否为源码编码问题（如 GBK 文件被按 UTF-8 读取）

    {!--< internal-use >!--}
    """
    msg = str(getattr(e, "msg", "") or e)
    return "Non-UTF-8" in msg or "encoding problem" in msg or "codec" in msg


def _parse_single_source(py: Path) -> str | None:
    """
    对单个源文件做严格语法预检（bytes 直读，走 PEP 263 coding 声明解码）

    {!--< internal-use >!--}

    :param py: 源文件路径
    :return: 失败描述（"路径:行号: 错误"），None = 通过
    """
    import ast

    source = py.read_bytes()
    try:
        ast.parse(source, filename=str(py))
    except (SyntaxError, ValueError, UnicodeDecodeError) as e:
        text = f"{py}:{getattr(e, 'lineno', '?')}: {getattr(e, 'msg', None) or e}"
        if _is_encoding_error(e):
            text = f"{text} ({i18n.t('loader.module.precheck_bad_encoding')})"
        return text
    return None


def precheck_source_files(label: str, source_files: "list[Path]", *, i18n_key: str) -> bool:
    """
    卸载前语法预检：对源文件列表逐文件 ``ast.parse``

    预检失败（语法错误）即拒绝重载——旧实例未卸载、继续服务，语法
    错误永远不会把组件推进"半死状态"。超过文件数上限
    （``MODULE_RELOAD_PRECHECK_MAX_FILES``）时跳过预检并记 debug，
    交由快照回滚兜底。

    源码按 bytes 严格解码（PEP 263 coding 声明优先、默认 UTF-8），
    非 UTF-8 的源文件在预检阶段即报错并附「另存为 UTF-8」指引，
    不再虚假通过。

    :param label: 组件名（日志用）
    :param source_files: 待检源文件列表（空列表直接通过）
    :param i18n_key: 预检失败日志的文案键（调用方按组件类型提供）
    :return: 是否通过（True = 允许继续重载流程）
    """
    if not source_files:
        return True
    try:
        for checked, py in enumerate(source_files, start=1):
            if checked > MODULE_RELOAD_PRECHECK_MAX_FILES:
                logger.debug(
                    i18n.t("loader.precheck.skipped_max_files", label=label, count=checked - 1)
                )
                return True
            failure = _parse_single_source(py)
            if failure is not None:
                logger.error(i18n.t(i18n_key, name=label, error=failure))
                return False
        return True
    except Exception as e:
        # 预检基础设施失败（文件不可读/路径异常等）不阻断重载——快照回滚兜底
        logger.debug(i18n.t("loader.precheck.unavailable", label=label, error=e))
        return True


def precheck_source_trees(
    label: str,
    source_trees: "list[tuple[str, list[Path]]]",
    *,
    i18n_key: str,
) -> "list[str]":
    """
    汇总式卸载前语法预检：遍历全部源码树，收集所有失败（不首个即停）

    供整体重载（``reload_all`` / ``sdk.restart()``）在卸载**任何**模块前
    使用：任一失败即由调用方拒绝整轮重载，全部旧实例继续服务。每棵树
    独立受 ``MODULE_RELOAD_PRECHECK_MAX_FILES`` 约束。

    :param label: 整体操作名（日志用，如 "restart"）
    :param source_trees: (组件名, 该组件源文件列表) 列表
    :param i18n_key: 汇总失败日志的文案键
    :return: 失败描述列表（空列表 = 全部通过；基础设施异常时同样返回
        空列表并记 debug，交由快照回滚兜底）
    """
    failures: list[str] = []
    try:
        for tree_label, files in source_trees:
            if not files:
                continue
            for checked, py in enumerate(files, start=1):
                if checked > MODULE_RELOAD_PRECHECK_MAX_FILES:
                    logger.debug(
                        i18n.t(
                            "loader.precheck.skipped_max_files",
                            label=tree_label, count=checked - 1,
                        )
                    )
                    break
                failure = _parse_single_source(py)
                if failure is not None:
                    failures.append(failure)
        if failures:
            logger.error(
                i18n.t(i18n_key, name=label, count=len(failures), details="\n  ".join(failures))
            )
        return failures
    except Exception as e:
        # 预检基础设施失败不阻断重载——单模块快照回滚兜底
        logger.debug(i18n.t("loader.precheck.unavailable", label=label, error=e))
        return []
