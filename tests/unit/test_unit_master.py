"""
框架主人管理系统单元测试

测试 MasterManager 的配置解析、is_master 检查、运行时增删等功能。
"""

from unittest.mock import patch

from ErisPulse.Core.master import MasterManager


class TestMasterManager:
    """MasterManager 核心功能测试"""

    def test_no_masters_returns_false(self):
        """无主人配置时 is_master 返回 False"""
        mgr = MasterManager()
        with patch("ErisPulse.Core.master.get_master_config", return_value={"users": {}}):
            assert mgr.is_master("yunhu", "123") is False

    def test_dict_format_platform_specific(self):
        """dict 格式：按平台指定主人"""
        mgr = MasterManager()
        config = {"users": {"yunhu": ["123", "456"], "telegram": ["789"]}}
        with patch("ErisPulse.Core.master.get_master_config", return_value=config):
            assert mgr.is_master("yunhu", "123") is True
            assert mgr.is_master("yunhu", "456") is True
            assert mgr.is_master("telegram", "789") is True
            assert mgr.is_master("telegram", "123") is False
            assert mgr.is_master("yunhu", "789") is False

    def test_list_format_global(self):
        """list 格式：全局主人，所有平台生效"""
        mgr = MasterManager()
        config = {"users": ["123", "456"]}
        with patch("ErisPulse.Core.master.get_master_config", return_value=config):
            assert mgr.is_master("yunhu", "123") is True
            assert mgr.is_master("telegram", "456") is True
            assert mgr.is_master("any_platform", "123") is True
            assert mgr.is_master("yunhu", "999") is False

    def test_dict_with_single_string_id(self):
        """dict 中某个平台的值不是 list 而是单个字符串"""
        mgr = MasterManager()
        config = {"users": {"yunhu": "123"}}
        with patch("ErisPulse.Core.master.get_master_config", return_value=config):
            assert mgr.is_master("yunhu", "123") is True

    def test_is_master_from_event(self):
        """从事件对象提取 platform 和 user_id"""
        mgr = MasterManager()
        config = {"users": {"yunhu": ["123"]}}

        class FakeEvent:
            def get_platform(self):
                return "yunhu"
            def get_user_id(self):
                return "123"

        with patch("ErisPulse.Core.master.get_master_config", return_value=config):
            assert mgr.is_master(FakeEvent()) is True

    def test_is_master_from_event_not_master(self):
        """事件对象不是主人"""
        mgr = MasterManager()
        config = {"users": {"yunhu": ["123"]}}

        class FakeEvent:
            def get_platform(self):
                return "yunhu"
            def get_user_id(self):
                return "999"

        with patch("ErisPulse.Core.master.get_master_config", return_value=config):
            assert mgr.is_master(FakeEvent()) is False

    def test_empty_user_id_returns_false(self):
        """空 user_id 返回 False"""
        mgr = MasterManager()
        with patch("ErisPulse.Core.master.get_master_config", return_value={"users": {}}):
            assert mgr.is_master("yunhu", "") is False
            assert mgr.is_master("yunhu", None) is False

    def test_empty_platform_with_dict_config(self):
        """dict 配置下空平台不匹配"""
        mgr = MasterManager()
        config = {"users": {"yunhu": ["123"]}}
        with patch("ErisPulse.Core.master.get_master_config", return_value=config):
            assert mgr.is_master("", "123") is False


class TestMasterRuntime:
    """运行时增删测试（persist=False）"""

    def test_add_platform_specific(self):
        """运行时添加指定平台主人"""
        mgr = MasterManager()
        mgr.reset()
        with patch("ErisPulse.Core.master.get_master_config", return_value={"users": {}}):
            assert mgr.is_master("yunhu", "999") is False
            mgr.add("yunhu", "999", persist=False)
            assert mgr.is_master("yunhu", "999") is True
            assert mgr.is_master("telegram", "999") is False

    def test_add_global(self):
        """运行时添加全局主人"""
        mgr = MasterManager()
        mgr.reset()
        with patch("ErisPulse.Core.master.get_master_config", return_value={"users": {}}):
            mgr.add(None, "888", persist=False)
            assert mgr.is_master("yunhu", "888") is True
            assert mgr.is_master("telegram", "888") is True
            assert mgr.is_master("any", "888") is True

    def test_remove(self):
        """移除运行时主人"""
        mgr = MasterManager()
        mgr.reset()
        with patch("ErisPulse.Core.master.get_master_config", return_value={"users": {}}):
            mgr.add("yunhu", "999", persist=False)
            assert mgr.is_master("yunhu", "999") is True
            assert mgr.remove("yunhu", "999", persist=False) is True
            assert mgr.is_master("yunhu", "999") is False
            assert mgr.remove("yunhu", "999", persist=False) is False

    def test_remove_global(self):
        """移除全局运行时主人"""
        mgr = MasterManager()
        mgr.reset()
        with patch("ErisPulse.Core.master.get_master_config", return_value={"users": {}}):
            mgr.add(None, "888", persist=False)
            assert mgr.remove(None, "888", persist=False) is True
            assert mgr.is_master("yunhu", "888") is False

    def test_reset_clears_runtime(self):
        """reset 清空运行时主人"""
        mgr = MasterManager()
        mgr.add("yunhu", "999", persist=False)
        mgr.add(None, "888", persist=False)
        mgr.reset()
        with patch("ErisPulse.Core.master.get_master_config", return_value={"users": {}}):
            assert mgr.is_master("yunhu", "999") is False
            assert mgr.is_master("yunhu", "888") is False

    def test_config_and_runtime_combined(self):
        """配置主人 + 运行时主人同时生效"""
        mgr = MasterManager()
        mgr.reset()
        config = {"users": {"yunhu": ["123"]}}
        with patch("ErisPulse.Core.master.get_master_config", return_value=config):
            assert mgr.is_master("yunhu", "123") is True
            mgr.add("telegram", "456", persist=False)
            assert mgr.is_master("telegram", "456") is True
            assert mgr.is_master("telegram", "123") is False
            assert mgr.is_master("yunhu", "456") is False


class TestMasterList:
    """list() 方法测试"""

    def test_list_empty(self):
        """无主人时 list 返回空字典"""
        mgr = MasterManager()
        mgr.reset()
        with patch("ErisPulse.Core.master.get_master_config", return_value={"users": {}}):
            assert mgr.list() == {}

    def test_list_dict_config(self):
        """dict 配置的 list 输出"""
        mgr = MasterManager()
        mgr.reset()
        config = {"users": {"yunhu": ["123", "456"], "telegram": ["789"]}}
        with patch("ErisPulse.Core.master.get_master_config", return_value=config):
            result = mgr.list()
            assert result["yunhu"] == ["123", "456"]
            assert result["telegram"] == ["789"]
            assert "global" not in result

    def test_list_global_config(self):
        """list 格式配置的 list 输出"""
        mgr = MasterManager()
        mgr.reset()
        config = {"users": ["123", "456"]}
        with patch("ErisPulse.Core.master.get_master_config", return_value=config):
            result = mgr.list()
            assert result["global"] == ["123", "456"]

    def test_list_with_runtime_additions(self):
        """list 包含运行时添加的主人"""
        mgr = MasterManager()
        mgr.reset()
        config = {"users": {"yunhu": ["123"]}}
        with patch("ErisPulse.Core.master.get_master_config", return_value=config):
            mgr.add("telegram", "789", persist=False)
            mgr.add(None, "999", persist=False)
            result = mgr.list()
            assert "123" in result["yunhu"]
            assert "789" in result["telegram"]
            assert "999" in result["global"]

    def test_config_master_live_reload(self):
        """主人配置无需重启即可生效：每次 is_master 检查都实时读取配置"""
        mgr = MasterManager()
        with patch(
            "ErisPulse.Core.master.get_master_config",
            side_effect=[
                {"users": ["10001"]},
                {"users": ["10001"]},
                {"users": ["20002"]},
                {"users": ["20002"]},
            ],
        ):
            # 第一次读取：旧配置
            assert mgr.is_master("yunhu", "10001") is True
            assert mgr.is_master("yunhu", "20002") is False
            # 配置变更后（模拟编辑 config.toml），无需重启即感知新主人
            assert mgr.is_master("yunhu", "10001") is False
            assert mgr.is_master("yunhu", "20002") is True
