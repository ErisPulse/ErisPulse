"""
配置原子写入单元测试

测试 ConfigManager 的原子写入机制（唯一临时文件 + fsync + os.replace）
与多实例共享配置目录检测（advisory lock 告警）功能

背景（BUG-036）：旧实现使用固定名 <config>.tmp 且 rename 前不 fsync，
多实例共享配置目录时互相 truncate/rename 争抢导致配置文件丢失（空文件/ENOENT）
"""

import importlib
import os
import tempfile
import threading
from pathlib import Path

import pytest
import tomlkit

from ErisPulse.Core.config import ConfigManager
from ErisPulse.Core.constants import CONFIG_LOCK_FILE_NAME

# importlib.import_module 返回真实子模块（Core.config 包属性被全局 config 单例遮蔽）
config_module = importlib.import_module("ErisPulse.Core.config")


class TestAtomicWrite:
    """原子写入测试类"""

    @pytest.fixture
    def config_dir(self):
        """创建临时配置目录"""
        with tempfile.TemporaryDirectory() as d:
            yield d

    @pytest.fixture
    def config_manager(self, config_dir):
        """创建配置管理器实例"""
        cfg = ConfigManager(config_file=os.path.join(config_dir, "config.toml"))
        yield cfg
        self._stop(cfg)

    @staticmethod
    def _stop(manager):
        if manager._write_timer:
            manager._write_timer.cancel()
        manager._watcher_stop.set()
        # 释放实例锁（Windows 下持有中的锁文件会阻止 TemporaryDirectory 清理）
        fd = getattr(manager, "_instance_lock_fd", None)
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
            manager._instance_lock_fd = None

    def test_flush_writes_content(self, config_manager, config_dir):
        """测试 flush 后配置内容完整写入"""
        config_manager.setConfig("test.key", "hello")
        config_manager._flush_config()

        with open(os.path.join(config_dir, "config.toml"), encoding="utf-8") as f:
            doc = tomlkit.parse(f.read())
        assert doc["test"]["key"] == "hello"

    def test_no_tmp_residue_after_flush(self, config_manager, config_dir):
        """测试 flush 后无临时文件残留（含旧版固定名 config.toml.tmp）"""
        config_manager.setConfig("test.key", "value")
        config_manager._flush_config()

        leftovers = [p for p in os.listdir(config_dir) if p.endswith(".tmp")]
        assert leftovers == []
        assert not os.path.exists(os.path.join(config_dir, "config.toml.tmp"))

    def test_write_failure_preserves_original(self, config_manager, config_dir, monkeypatch):
        """测试写失败时原文件保持完整、无临时文件残留、脏键保留待重试"""
        config_manager.setConfig("keep.key", "old")
        config_manager._flush_config()
        original = Path(config_dir, "config.toml").read_text(encoding="utf-8")

        def boom(src, dst):
            raise OSError("simulated crash between write and replace")

        monkeypatch.setattr(config_module.os, "replace", boom)

        config_manager.setConfig("keep.key", "new")
        config_manager._flush_config()  # 内部捕获写失败，不抛出

        assert Path(config_dir, "config.toml").read_text(encoding="utf-8") == original
        assert [p for p in os.listdir(config_dir) if p.endswith(".tmp")] == []
        assert config_manager._dirty_keys, "写失败后脏键应保留，待下次 flush 重试"

    def test_concurrent_writers_never_corrupt(self, config_dir):
        """测试并发写入（模拟双实例）：任何时刻文件都是完整合法的 TOML"""
        cfg1 = ConfigManager(config_file=os.path.join(config_dir, "config.toml"))
        cfg2 = ConfigManager(config_file=os.path.join(config_dir, "config.toml"))
        barrier = threading.Barrier(2)

        def writer(manager, tag):
            barrier.wait()
            for i in range(20):
                manager.setConfig(f"{tag}.counter", i)
                manager._flush_config()

        t1 = threading.Thread(target=writer, args=(cfg1, "one"))
        t2 = threading.Thread(target=writer, args=(cfg2, "two"))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        text = Path(config_dir, "config.toml").read_text(encoding="utf-8")
        doc = tomlkit.parse(text)
        assert doc["one"]["counter"] in range(20)
        assert doc["two"]["counter"] in range(20)
        leftovers = [p for p in os.listdir(config_dir) if p.endswith(".tmp")]
        assert leftovers == []

        self._stop(cfg1)
        self._stop(cfg2)

    def test_lock_file_created_and_held(self, config_manager, config_dir):
        """测试初始化后在配置目录创建实例锁文件并持有"""
        assert (Path(config_dir) / CONFIG_LOCK_FILE_NAME).exists()
        assert config_manager._instance_lock_fd is not None

    def test_multi_instance_detected_warning(self, config_dir, monkeypatch):
        """测试锁被其他实例占用时记录告警（不阻塞启动）"""
        warnings = []
        monkeypatch.setattr(
            ConfigManager,
            "_log_config_error",
            staticmethod(lambda msg, level="error": warnings.append((level, msg))),
        )

        first = ConfigManager(config_file=os.path.join(config_dir, "config.toml"))
        warnings.clear()
        second = ConfigManager(config_file=os.path.join(config_dir, "config.toml"))

        assert any(level == "warning" for level, _ in warnings), "第二个实例应触发多实例告警"

        self._stop(first)
        self._stop(second)

    def test_migrate_uses_atomic_write(self, config_dir):
        """测试旧版根目录 config.toml 迁移走原子写入（目标完整、旧文件删除）"""
        legacy = Path(config_dir, "legacy_root")
        legacy.mkdir()
        (legacy / "config.toml").write_text('[old]\nkey = "value"\n', encoding="utf-8")

        old_cwd = os.getcwd()
        os.chdir(legacy)
        try:
            cfg = ConfigManager(config_file="config/config.toml")
            try:
                new_file = legacy / "config" / "config.toml"
                assert new_file.exists()
                doc = tomlkit.parse(new_file.read_text(encoding="utf-8"))
                assert doc["old"]["key"] == "value"
                assert not (legacy / "config.toml").exists()
                tmp_leftovers = [
                    p.name for p in (legacy / "config").iterdir() if p.name.endswith(".tmp")
                ]
                assert tmp_leftovers == []
            finally:
                self._stop(cfg)
        finally:
            os.chdir(old_cwd)
