"""
Config 异步接口测试
"""

import asyncio
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from ErisPulse.Core.config import ConfigManager


def sec(title):
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print(f"{'=' * 50}")


def ok(msg=""):
    print(f"  ✓ {msg}")


def test_agetConfig():
    """异步获取配置"""
    sec("agetConfig")
    cfg = ConfigManager(tempfile.mktemp(suffix=".toml"))
    cfg.setConfig("test.key", "hello")

    value = asyncio.run(cfg.agetConfig("test.key"))
    assert value == "hello"; ok(f"agetConfig → {value!r}")

    value = asyncio.run(cfg.agetConfig("test.missing", "default"))
    assert value == "default"; ok("agetConfig + default → 'default'")

    print()


def test_asetConfig():
    """异步设置配置"""
    sec("asetConfig")
    cfg = ConfigManager(tempfile.mktemp(suffix=".toml"))

    result = asyncio.run(cfg.asetConfig("a.b", 100))
    assert result is True; ok("asetConfig 返回 True")
    assert cfg.getConfig("a.b") == 100; ok("同步读取验证: 100")

    print()


def test_aforce_save():
    """异步强制保存"""
    sec("aforce_save")
    cfg = ConfigManager(tempfile.mktemp(suffix=".toml"))
    cfg.setConfig("x", 1)

    asyncio.run(cfg.aforce_save())
    ok("aforce_save 不抛异常")

    # reload 后值还在
    cfg_reload = ConfigManager(cfg.CONFIG_FILE)
    assert cfg_reload.getConfig("x") == 1; ok("文件持久化验证成功")

    print()


def test_areload():
    """异步重新加载"""
    sec("areload")
    cfg = ConfigManager(tempfile.mktemp(suffix=".toml"))
    cfg.setConfig("y", 999, immediate=True)
    cfg.setConfig("y", 0)  # 内存中修改，未持久化

    asyncio.run(cfg.areload())
    assert cfg.getConfig("y") == 999; ok("reload 恢复为文件中的值 999")

    print()


if __name__ == "__main__":
    test_agetConfig()
    test_asetConfig()
    test_aforce_save()
    test_areload()
    print(f"{'=' * 50}")
    print("  全部测试通过 ✓")
    print(f"{'=' * 50}")
