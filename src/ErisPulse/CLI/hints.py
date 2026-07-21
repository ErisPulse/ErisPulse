"""
ErisPulse CLI 友好提示引擎

CLI 完全独立于框架本体（包括 ``runtime.hints``）。本模块提供 CLI 专用的
模糊匹配 / 拼写建议能力，避免 CLI 反向依赖框架运行时。

{!--< tips >!--}
1. best_match_with_prefix: 用于"未知命令 → 你是不是想用 xxx"场景，
   对前缀匹配（如 ``ins`` → ``install``）给予加成。
2. 其余函数与框架 runtime.hints 行为一致，便于跨模块复用思路。
{!--< /tips >!--}
"""

from __future__ import annotations

import difflib
from collections.abc import Sequence


def suggest_similar(
    name: str,
    candidates: Sequence[str],
    *,
    max_suggestions: int = 3,
    cutoff: float = 0.5,
) -> list[str]:
    """
    找出与给定名称最相似的候选词

    使用 difflib 进行模糊匹配，不区分大小写比较、返回原始大小写。

    :param name: 用户输入的（可能有误的）名称
    :param candidates: 候选词列表
    :param max_suggestions: 最多返回的建议数量
    :param cutoff: 相似度阈值 (0.0 ~ 1.0)，低于此值的候选会被过滤
    :return: 按相似度从高到低排序的建议列表（保留原始大小写）
    """
    name_lower = name.lower()
    matcher = difflib.SequenceMatcher(None, name_lower)
    scored: list[tuple[float, str]] = []
    for candidate in candidates:
        matcher.set_seq2(candidate.lower())
        ratio = matcher.ratio()
        if ratio >= cutoff:
            scored.append((ratio, candidate))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:max_suggestions]]


def best_match(
    name: str,
    candidates: Sequence[str],
    *,
    cutoff: float = 0.6,
) -> str | None:
    """
    返回单个最佳匹配建议

    :param name: 用户输入的名称
    :param candidates: 候选词列表
    :param cutoff: 相似度阈值（默认 0.6，确保只返回高置信度匹配）
    :return: 最佳匹配的候选词，无匹配时返回 None
    """
    matches = suggest_similar(name, candidates, max_suggestions=1, cutoff=cutoff)
    return matches[0] if matches else None


def best_match_with_prefix(
    name: str,
    candidates: Sequence[str],
    *,
    cutoff: float = 0.5,
    prefix_bonus: float = 0.85,
) -> str | None:
    """
    带前缀加成的模糊匹配

    当输入是候选词的前缀时（如 ins -> install），给予更高的相似度分数。
    专用于 CLI 子命令拼写纠错场景。

    :param name: 用户输入的名称
    :param candidates: 候选词列表
    :param cutoff: 基础相似度阈值
    :param prefix_bonus: 当输入是候选前缀时使用的固定高分（应大于 cutoff）
    :return: 最佳匹配的候选词，无匹配时返回 None
    """
    name_lower = name.lower()
    best: str | None = None
    best_score: float = cutoff

    for candidate in candidates:
        cand_lower = candidate.lower()
        # 前缀匹配：直接使用 prefix_bonus 作为分数（通常远高于普通 ratio）
        if cand_lower.startswith(name_lower) and name_lower:
            if prefix_bonus > best_score:
                best_score = prefix_bonus
                best = candidate
            continue
        ratio = difflib.SequenceMatcher(None, name_lower, cand_lower).ratio()
        if ratio > best_score:
            best_score = ratio
            best = candidate

    return best


def suggest_for_exception(exc: BaseException) -> str | None:
    """
    为 CLI 命令执行中的异常生成场景化提示

    根据 Python 异常类型返回对应的 i18n key，由调用方翻译为最终提示。
    仅覆盖 CLI 场景下高频出现的异常类型，与框架 runtime.hints 的职责区分。

    :param exc: 捕获的异常实例
    :return: i18n key 字符串，不匹配时返回 None
    """
    # FileNotFoundError 必须在 OSError 之前检查（继承关系）
    if isinstance(exc, FileNotFoundError):
        return "cli.hints.file_not_found"
    if isinstance(exc, PermissionError):
        return "cli.hints.permission_denied"
    # ConnectionError 涵盖 ConnectionRefusedError / ConnectionResetError 等
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return "cli.hints.network_error"
    if isinstance(exc, ModuleNotFoundError):
        return "cli.hints.module_not_installed"
    return None


__all__ = [
    "best_match",
    "best_match_with_prefix",
    "suggest_for_exception",
    "suggest_similar",
]
