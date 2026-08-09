"""
主动 GC 决策逻辑单元测试

验证 SDK 的主动 GC 配置读取/钳制、全量回收内存增长门控、
事件洪峰检测与配置变更重启联动。
"""

from unittest.mock import Mock, patch

from ErisPulse.sdk import SDK


class TestReadGcConfig:
    """_read_gc_config 配置读取与钳制"""

    def test_defaults_when_no_config(self):
        """无配置时返回常量默认值"""
        with patch("ErisPulse.runtime.get_framework_config", return_value={}):
            cfg = SDK._read_gc_config()
        assert cfg == (
            300,  # interval
            0,    # generation（默认 0，常规轻量回收）
            20,   # full_every
            32,   # memory_growth_mb
            False,  # idle_only
            500,  # gen0_min
        )

    def test_reads_configured_values(self):
        """读取配置值"""
        fw = {
            "proactive_gc_interval": 60,
            "proactive_gc_generation": 1,
            "proactive_gc_full_every": 5,
            "proactive_gc_memory_growth_mb": 64,
            "proactive_gc_idle_only": True,
            "proactive_gc_gen0_min": 0,
        }
        with patch("ErisPulse.runtime.get_framework_config", return_value=fw):
            cfg = SDK._read_gc_config()
        assert cfg == (60, 1, 5, 64, True, 0)

    def test_clamps_out_of_range_values(self):
        """越界值被钳制：generation 限制 0..2，负值归零"""
        fw = {
            "proactive_gc_interval": -5,
            "proactive_gc_generation": 9,
            "proactive_gc_full_every": -1,
            "proactive_gc_memory_growth_mb": -3,
            "proactive_gc_idle_only": True,
            "proactive_gc_gen0_min": -10,
        }
        with patch("ErisPulse.runtime.get_framework_config", return_value=fw):
            cfg = SDK._read_gc_config()
        assert cfg[0] == 0    # interval 负值 → 0（禁用）
        assert cfg[1] == 2    # generation 9 → 2
        assert cfg[2] == 0
        assert cfg[3] == 0
        assert cfg[4] is True
        assert cfg[5] == 0


class TestRunFullGcCollection:
    """_run_full_gc_collection 内存增长门控"""

    def test_first_run_establishes_baseline(self):
        """首次全量回收建立基线并执行回收"""
        fake_gc = Mock()
        fake_gc.collect.return_value = 42
        with patch("ErisPulse.runtime.memory.get_traced_mb", return_value=100.0), patch(
            "ErisPulse.runtime.memory.get_rss_mb", return_value=200.0
        ):
            collected, baseline = SDK._run_full_gc_collection(fake_gc, None, 32)
        assert collected == 42
        assert baseline == 100.0
        fake_gc.collect.assert_called_once()

    def test_skip_when_growth_below_threshold(self):
        """内存增长低于门限时跳过全量回收且基线不变"""
        fake_gc = Mock()
        fake_gc.collect.return_value = 0
        with patch("ErisPulse.runtime.memory.get_traced_mb", return_value=110.0):
            collected, baseline = SDK._run_full_gc_collection(fake_gc, 100.0, 32)
        assert collected == 0
        assert baseline == 100.0
        fake_gc.collect.assert_not_called()

    def test_collect_when_growth_above_threshold(self):
        """内存增长达到门限时执行全量回收并更新基线"""
        fake_gc = Mock()
        fake_gc.collect.return_value = 7
        with patch("ErisPulse.runtime.memory.get_traced_mb", return_value=150.0):
            collected, baseline = SDK._run_full_gc_collection(fake_gc, 100.0, 32)
        assert collected == 7
        assert baseline == 150.0
        fake_gc.collect.assert_called_once()

    def test_growth_mb_zero_disables_gate(self):
        """growth_mb=0 不设门限，始终回收"""
        fake_gc = Mock()
        fake_gc.collect.return_value = 1
        with patch("ErisPulse.runtime.memory.get_traced_mb", return_value=100.0):
            collected, _ = SDK._run_full_gc_collection(fake_gc, 100.0, 0)
        assert collected == 1
        fake_gc.collect.assert_called_once()

    def test_no_memory_source_falls_back_to_collect(self):
        """traced/RSS 均不可用时仍执行回收"""
        fake_gc = Mock()
        fake_gc.collect.return_value = 3
        with patch("ErisPulse.runtime.memory.get_traced_mb", return_value=None), patch(
            "ErisPulse.runtime.memory.get_rss_mb", return_value=None
        ):
            collected, _ = SDK._run_full_gc_collection(fake_gc, 100.0, 32)
        assert collected == 3
        fake_gc.collect.assert_called_once()


class TestHasHandlerBacklog:
    """_has_handler_backlog 洪峰检测"""

    def test_true_when_pending_tasks_exist(self):
        """存在 pending handler task 时返回 True"""
        from ErisPulse.Core.adapter import adapter as _adapter_mgr

        with patch.object(_adapter_mgr, "_pending_handler_tasks", {object()}):
            assert SDK._has_handler_backlog() is True

    def test_false_when_no_pending_tasks(self):
        """无 pending handler task 时返回 False"""
        from ErisPulse.Core.adapter import adapter as _adapter_mgr

        with patch.object(_adapter_mgr, "_pending_handler_tasks", set()):
            assert SDK._has_handler_backlog() is False


class TestConfigChangeRestart:
    """_on_gc_config_event 配置变更重启联动"""

    async def test_restart_on_config_change(self):
        """事件循环内配置变化时触发 _start_proactive_gc"""
        sdk = SDK()
        old_cfg = (300, 0, 20, 32, False, 500)
        new_cfg = (60, 0, 20, 32, False, 500)
        sdk._gc_config_snapshot = old_cfg
        with patch.object(
            SDK, "_read_gc_config", return_value=new_cfg
        ), patch.object(SDK, "_start_proactive_gc") as mock_start:
            sdk._on_gc_config_event({})
        mock_start.assert_called_once()

    async def test_no_restart_when_unchanged(self):
        """配置未变化时不重启"""
        sdk = SDK()
        cfg = (300, 0, 20, 32, False, 500)
        sdk._gc_config_snapshot = cfg
        with patch.object(
            SDK, "_read_gc_config", return_value=cfg
        ), patch.object(SDK, "_start_proactive_gc") as mock_start:
            sdk._on_gc_config_event({})
        mock_start.assert_not_called()

    async def test_no_restart_when_snapshot_none(self):
        """快照为 None（GC 已停止）时不重启"""
        sdk = SDK()
        sdk._gc_config_snapshot = None
        with patch.object(
            SDK, "_read_gc_config", return_value=(300, 0, 20, 32, False, 500)
        ), patch.object(SDK, "_start_proactive_gc") as mock_start:
            sdk._on_gc_config_event({})
        mock_start.assert_not_called()

    def test_restart_scheduled_on_main_loop_from_thread(self):
        """后台线程触发时调度回主循环执行重启"""
        sdk = SDK()
        sdk._gc_config_snapshot = (300, 0, 20, 32, False, 500)
        fake_loop = Mock()
        fake_loop.is_running.return_value = True
        with patch.object(
            SDK, "_read_gc_config", return_value=(60, 0, 20, 32, False, 500)
        ), patch.object(SDK, "_start_proactive_gc") as mock_start, patch(
            "ErisPulse.runtime.tasks._get_main_loop", return_value=fake_loop
        ):
            sdk._on_gc_config_event({})

        # 无运行中事件循环，重启被调度到主循环（延迟执行），立即调用被阻止
        mock_start.assert_not_called()
        fake_loop.call_soon_threadsafe.assert_called_once()

    def test_no_restart_when_no_loop_available(self):
        """无主循环且无运行中事件循环时跳过重启"""
        sdk = SDK()
        sdk._gc_config_snapshot = (300, 0, 20, 32, False, 500)
        with patch.object(
            SDK, "_read_gc_config", return_value=(60, 0, 20, 32, False, 500)
        ), patch.object(SDK, "_start_proactive_gc") as mock_start, patch(
            "ErisPulse.runtime.tasks._get_main_loop", return_value=None
        ):
            sdk._on_gc_config_event({})
        mock_start.assert_not_called()
