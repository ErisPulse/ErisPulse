"""
围栏损坏缓存清理：扫描各语言译文，凡围栏行数与 zh-CN 源不一致的文件，
删除其翻译缓存（.github/.translate_cache/<lang>/<rel>.cache），
使 CI 下轮用修复后的翻译脚本重新翻译。

用法: python scripts/tools/invalidate_fence_broken_cache.py [--dry-run]
"""

import argparse
import io
import os
import re
import sys

FENCE = re.compile(r"^`{3,}", re.MULTILINE)
SOURCE_LANG = "zh-CN"
TARGET_LANGS = ["en", "ja", "ru", "zh-TW"]
CACHE_DIR = ".github/.translate_cache"


def count_fences(text: str) -> int:
    return len(FENCE.findall(text))


def cache_paths_for(rel: str, lang: str):
    """返回该文件+语言对应的可能缓存路径（嵌套与扁平两种命名）"""
    nested = os.path.join(CACHE_DIR, lang, rel + ".cache")
    flat = os.path.join(CACHE_DIR, rel + ".cache")
    return [nested, flat]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    broken = []
    for lang in TARGET_LANGS:
        src_root = f"docs/{SOURCE_LANG}"
        for dp, dn, fn in os.walk(src_root):
            for f in fn:
                if not f.endswith(".md"):
                    continue
                src_path = os.path.join(dp, f)
                rel = os.path.relpath(src_path, src_root).replace("\\", "/")
                tgt_path = os.path.join("docs", lang, rel)
                if not os.path.exists(tgt_path):
                    continue
                try:
                    s = io.open(src_path, encoding="utf-8").read()
                    t = io.open(tgt_path, encoding="utf-8").read()
                except Exception as e:
                    print(f"[READ-ERR] {lang}/{rel}: {e}")
                    continue
                sf, tf = count_fences(s), count_fences(t)
                if sf != tf:
                    broken.append((lang, rel, sf, tf))

        # 根 README（源 README.zh-CN.md -> README.<lang>.md，扁平缓存）
        if os.path.exists(f"README.{lang}.md") and os.path.exists(
            "README.zh-CN.md"
        ):
            s = io.open("README.zh-CN.md", encoding="utf-8").read()
            t = io.open(f"README.{lang}.md", encoding="utf-8").read()
            sf, tf = count_fences(s), count_fences(t)
            if sf != tf:
                broken.append((lang, "README.md(root)", sf, tf))

    print(f"共发现 {len(broken)} 个围栏损坏的译文文件")
    removed = 0
    for lang, rel, sf, tf in broken:
        print(f"  [BROKEN] {lang}/{rel}  源{sf} != 译{tf}")
        if rel == "README.md(root)":
            candidates = [
                os.path.join(CACHE_DIR, f"README.{lang}.md.cache"),
                os.path.join(CACHE_DIR, "README.md.cache"),
            ]
        else:
            candidates = cache_paths_for(rel, lang)
        for c in candidates:
            if os.path.exists(c):
                if args.dry_run:
                    print(f"    [DRY] 将删除缓存 {c}")
                else:
                    os.remove(c)
                    print(f"    [FIX] 已删除缓存 {c}")
                    removed += 1
                break

    print(f"\n完成：{len(broken)} 个损坏文件，删除 {removed} 个缓存")
    return 0


if __name__ == "__main__":
    sys.exit(main())
