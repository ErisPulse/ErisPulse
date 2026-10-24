"""
ErisPulse 自动循环翻译器

在 CI 中实现：检测 → 删除问题缓存 → 翻译 → 再检测 → 循环直到完成或达到最大轮次

使用方法:
    python scripts/tools/auto-translate.py
    python scripts/tools/auto-translate.py --max-rounds 5
    python scripts/tools/auto-translate.py --time-budget 270
"""

import argparse
import asyncio
import subprocess
import sys
import time

from .common import Logger


def run_command(cmd: list[str], capture_output: bool = False) -> tuple[int, str]:
    """运行命令并返回退出码和输出"""
    result = subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        encoding="utf-8",
    )
    return result.returncode, result.stdout if capture_output else ""


def check_translation(fix: bool = False) -> tuple[int, int]:
    """运行翻译质量检查，返回 (退出码, 错误数)"""
    cmd = ["python", "-m", "scripts.tools", "check", "translation"]
    if fix:
        cmd.append("--fix")
    
    exit_code, output = run_command(cmd, capture_output=True)
    
    # 解析错误数
    error_count = 0
    for line in output.split("\n"):
        if "错误:" in line or "errors:" in line.lower():
            import re
            match = re.search(r"(\d+)", line)
            if match:
                error_count = int(match.group(1))
    
    return exit_code, error_count


def translate(time_budget: float = 0, force: bool = False) -> tuple[int, int]:
    """运行翻译，返回 (退出码, 剩余文件数)"""
    cmd = ["python", "-m", "scripts.tools", "translate"]
    if time_budget > 0:
        cmd.extend(["--time-budget", str(time_budget)])
    if force:
        cmd.append("--force")
    
    exit_code, output = run_command(cmd, capture_output=True)
    
    # 解析剩余文件数
    remaining = 0
    for line in output.split("\n"):
        if "REMAINING_FILES=" in line:
            import re
            match = re.search(r"REMAINING_FILES=(\d+)", line)
            if match:
                remaining = int(match.group(1))
    
    return exit_code, remaining


async def auto_translate_loop(
    max_rounds: int = 10,
    time_budget_per_round: float = 0,
    force_first_round: bool = False,
):
    """自动循环翻译"""
    Logger.log("=" * 60)
    Logger.log("ErisPulse 自动循环翻译")
    Logger.log("=" * 60)
    Logger.log(f"最大轮次: {max_rounds}")
    Logger.log(f"每轮时间预算: {time_budget_per_round} 分钟" if time_budget_per_round > 0 else "每轮时间预算: 无限制")
    Logger.log("")
    
    start_time = time.time()
    total_rounds = 0
    
    for round_no in range(1, max_rounds + 1):
        total_rounds = round_no
        elapsed_min = (time.time() - start_time) / 60
        
        Logger.log("")
        Logger.log("=" * 60)
        Logger.log(f"第 {round_no}/{max_rounds} 轮 (已用时: {elapsed_min:.1f} 分钟)")
        Logger.log("=" * 60)
        
        # 步骤 1: 检查并删除问题缓存
        Logger.log("")
        Logger.log("[步骤 1] 检查翻译质量并删除问题缓存...")
        check_exit, error_count = check_translation(fix=True)
        Logger.log(f"检查完成: 发现 {error_count} 个错误")
        
        # 步骤 2: 翻译
        Logger.log("")
        Logger.log("[步骤 2] 执行翻译...")
        is_first_round = (round_no == 1)
        translate_exit, remaining = translate(
            time_budget=time_budget_per_round,
            force=(force_first_round and is_first_round)
        )
        Logger.log(f"翻译完成: 剩余 {remaining} 个文件")
        
        # 步骤 3: 验证
        Logger.log("")
        Logger.log("[步骤 3] 验证翻译质量...")
        verify_exit, verify_errors = check_translation(fix=False)
        Logger.log(f"验证完成: {verify_errors} 个错误")
        
        # 判断是否完成
        if verify_errors == 0 and translate_exit == 0 and remaining == 0:
            Logger.log("")
            Logger.log("所有翻译完成！")
            break
        
        # 检查是否还有时间
        if time_budget_per_round > 0 and elapsed_min > time_budget_per_round * max_rounds * 0.9:
            Logger.log("")
            Logger.log("⚠️ 接近总时间预算，停止循环")
            break
    
    Logger.log("")
    Logger.log("=" * 60)
    Logger.log("翻译总结")
    Logger.log("=" * 60)
    Logger.log(f"总轮次: {total_rounds}")
    Logger.log(f"总耗时: {(time.time() - start_time) / 60:.1f} 分钟")
    
    # 最终检查
    final_exit, final_errors = check_translation(fix=False)
    Logger.log(f"最终检查: {final_errors} 个错误")
    
    if final_errors > 0:
        Logger.log("⚠️ 仍有错误，可能需要人工检查")
        return 1
    
    Logger.log("全部完成！")
    return 0


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="ErisPulse 自动循环翻译器")
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=10,
        help="最大翻译轮次 (默认: 10)"
    )
    parser.add_argument(
        "--time-budget",
        type=float,
        default=0,
        help="每轮时间预算（分钟），0 表示无限制 (默认: 0)"
    )
    parser.add_argument(
        "--force-first",
        action="store_true",
        help="第一轮强制重新翻译"
    )
    
    args = parser.parse_args(argv)
    
    exit_code = asyncio.run(auto_translate_loop(
        max_rounds=args.max_rounds,
        time_budget_per_round=args.time_budget,
        force_first_round=args.force_first,
    ))
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
