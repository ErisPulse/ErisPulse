"""
ErisPulse 自动循环翻译器

在 CI 中实现：检测 → 删除问题缓存 → 翻译 → 再检测 → 循环直到完成或达到最大轮次

使用方法:
    python -m scripts.tools auto-translate
    python -m scripts.tools auto-translate --max-rounds 5
    python -m scripts.tools auto-translate --time-budget 270

{!--< tips >!--}
1. 尽力而为语义：部分文件翻译失败 / 质检不过不判整体失败（返回 0）——
   已完成的译文照常入库，问题文件由缓存机制在下一轮自动重译；
   结尾输出机器可读标记 ``TRANSLATE_FAILED=`` / ``REMAINING_FILES=``
   供 CI 步骤解析（子命令输出全部实时透传，不在 CI 里"假死"）
2. ``--time-budget`` 为**总预算**（分钟）：每轮按剩余时间分配，接近耗尽停止调度
{!--< /tips >!--}
"""

import argparse
import asyncio
import re
import subprocess
import sys
import time

from .common import Logger


def stream_command(cmd: list[str]) -> tuple[int, list[str]]:
    """运行命令：输出实时透传到 stdout（CI 可见进度），同时收集行供解析

    :param cmd: 完整命令（含 python -m 前缀）
    :return: (退出码, 输出行列表)
    """
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    lines: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        lines.append(line.rstrip("\n"))
    process.wait()
    return process.returncode, lines


def _parse_int(lines: list[str], pattern: str) -> int:
    """从输出行中解析最后一个匹配 ``pattern``（含一个捕获组）的整数"""
    value = 0
    regex = re.compile(pattern)
    for line in lines:
        match = regex.search(line)
        if match:
            value = int(match.group(1))
    return value


def check_translation(fix: bool = False) -> tuple[int, int]:
    """运行翻译质量检查

    :param fix: 是否删除问题文件的翻译缓存
    :return: (退出码, 错误数)
    """
    cmd = ["python", "-m", "scripts.tools", "check", "translation"]
    if fix:
        cmd.append("--fix")
    exit_code, lines = stream_command(cmd)
    error_count = _parse_int(lines, r"错误[:：]\s*(\d+)")
    return exit_code, error_count


def translate(time_budget: float = 0, force: bool = False) -> tuple[int, int]:
    """运行单轮翻译

    :param time_budget: 本轮时间预算（分钟），0 表示不限
    :param force: 是否强制重译全部文件
    :return: (退出码, 剩余文件数)
    """
    cmd = ["python", "-m", "scripts.tools", "translate"]
    if time_budget > 0:
        cmd.extend(["--time-budget", str(time_budget)])
    if force:
        cmd.append("--force")
    exit_code, lines = stream_command(cmd)
    remaining = _parse_int(lines, r"REMAINING_FILES=(\d+)")
    return exit_code, remaining


async def auto_translate_loop(
    max_rounds: int = 10,
    total_time_budget: float = 0,
    force_first_round: bool = False,
) -> tuple[bool, int]:
    """自动循环翻译主循环

    :param max_rounds: 最大轮次
    :param total_time_budget: 总时间预算（分钟），0 表示不限
    :param force_first_round: 第一轮是否强制重译
    :return: (是否有失败, 剩余文件数)
    """
    Logger.log("=" * 60)
    Logger.log("ErisPulse 自动循环翻译")
    Logger.log("=" * 60)
    Logger.log(f"最大轮次: {max_rounds}")
    if total_time_budget > 0:
        Logger.log(f"总时间预算: {total_time_budget} 分钟")
    else:
        Logger.log("总时间预算: 无限制")
    Logger.log("")

    start_time = time.time()
    saw_failure = False
    last_remaining = 0
    total_rounds = 0

    for round_no in range(1, max_rounds + 1):
        total_rounds = round_no
        elapsed_min = (time.time() - start_time) / 60

        # 总预算余量：每轮按剩余分配，不足 5 分钟不再调度新轮
        if total_time_budget > 0:
            left_min = total_time_budget - elapsed_min
            if round_no > 1 and left_min < 5:
                Logger.log(f"总预算余量 {left_min:.0f} 分钟，停止调度新轮")
                break
        else:
            left_min = 0

        Logger.log("")
        Logger.log("=" * 60)
        Logger.log(f"第 {round_no}/{max_rounds} 轮 (已用时: {elapsed_min:.1f} 分钟)")
        Logger.log("=" * 60)

        # 步骤 1: 检查并删除问题缓存
        Logger.log("")
        Logger.log("[步骤 1] 检查翻译质量并删除问题缓存...")
        _check_exit, error_count = check_translation(fix=True)
        Logger.log(f"检查完成: 发现 {error_count} 个错误")

        # 步骤 2: 翻译
        Logger.log("")
        Logger.log("[步骤 2] 执行翻译...")
        translate_exit, last_remaining = translate(
            time_budget=left_min,
            force=(force_first_round and round_no == 1),
        )
        Logger.log(f"翻译完成: 剩余 {last_remaining} 个文件")
        if translate_exit != 0:
            saw_failure = True

        # 步骤 3: 验证
        Logger.log("")
        Logger.log("[步骤 3] 验证翻译质量...")
        _verify_exit, verify_errors = check_translation(fix=False)
        Logger.log(f"验证完成: {verify_errors} 个错误")

        if verify_errors == 0 and last_remaining == 0 and not saw_failure:
            Logger.log("")
            Logger.log("所有翻译完成！")
            break

    Logger.log("")
    Logger.log("=" * 60)
    Logger.log("翻译总结")
    Logger.log("=" * 60)
    Logger.log(f"总轮次: {total_rounds}")
    Logger.log(f"总耗时: {(time.time() - start_time) / 60:.1f} 分钟")

    _final_exit, final_errors = check_translation(fix=False)
    Logger.log(f"最终检查: {final_errors} 个错误")
    if final_errors > 0:
        # 问题译文缓存已被各轮 --fix 清除，下一轮运行自动重译——不判整体失败
        saw_failure = True
        Logger.log("仍有质检错误：相关缓存已清除，下一轮运行将自动重译")

    # 机器可读标记（CI 步骤 grep 协议，与 translate.py 的 REMAINING_FILES 同风格）
    Logger.log(f"TRANSLATE_FAILED={1 if saw_failure else 0}")
    Logger.log(f"REMAINING_FILES={last_remaining}")
    return saw_failure, last_remaining


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description="ErisPulse 自动循环翻译器")
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=10,
        help="最大翻译轮次 (默认: 10)",
    )
    parser.add_argument(
        "--time-budget",
        type=float,
        default=0,
        help="总时间预算（分钟），0 表示无限制 (默认: 0)",
    )
    parser.add_argument(
        "--force-first",
        action="store_true",
        help="第一轮强制重新翻译",
    )

    args = parser.parse_args(argv)

    asyncio.run(
        auto_translate_loop(
            max_rounds=args.max_rounds,
            total_time_budget=args.time_budget,
            force_first_round=args.force_first,
        )
    )
    # 尽力而为：失败信息经 TRANSLATE_FAILED 标记传递，退出码恒 0（保证产物入库）
    return 0


if __name__ == "__main__":
    sys.exit(main())
