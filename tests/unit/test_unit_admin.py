"""
管理员管理系统单元测试

测试 AdminManager 的配置解析、is_admin 检查、运行时增删等功能。
"""

from unittest.mock import patch

from ErisPulse.Core.admin import AdminManager


class TestAdminManager:
    """AdminManager 核心功能测试"""

    def test_no_admins_returns_false(self):
        """无管理员配置时 is_admin 返回 False"""
        mgr = AdminManager()
        with patch("ErisPulse.Core.admin.get_admin_config", return_value={"users": {}}):
            assert mgr.is_admin("yunhu", "123") is False

    def test_dict_format_platform_specific(self):
        """dict 格式：按平台指定管理员"""
        mgr = AdminManager()
        config = {"users": {"yunhu": ["123", "456"], "telegram": ["789"]}}
        with patch("ErisPulse.Core.admin.get_admin_config", return_value=config):
            assert mgr.is_admin("yunhu", "123") is True
            assert mgr.is_admin("yunhu", "456") is True
            assert mgr.is_admin("telegram", "789") is True
            # 平台不匹配
            assert mgr.is_admin("telegram", "123") is False
            assert mgr.is_admin("yunhu", "789") is False

    def test_list_format_global(self):
        """list 格式：全局管理员，所有平台生效"""
        mgr = AdminManager()
        config = {"users": ["123", "456"]}
        with patch("ErisPulse.Core.admin.get_admin_config", return_value=config):
            assert mgr.is_admin("yunhu", "123") is True
            assert mgr.is_admin("telegram", "456") is True
            assert mgr.is_admin("any_platform", "123") is True
            assert mgr.is_admin("yunhu", "999") is False

    def test_dict_with_single_string_id(self):
        """dict 中某个平台的值不是 list 而是单个字符串"""
        mgr = AdminManager()
        config = {"users": {"yunhu": "123"}}
        with patch("ErisPulse.Core.admin.get_admin_config", return_value=config):
            assert mgr.is_admin("yunhu", "123") is True

    def test_is_admin_from_event(self):
        """从事件对象提取 platform 和 user_id"""
        mgr = AdminManager()
        config = {"users": {"yunhu": ["123"]}}

        class FakeEvent:
            def get_platform(self):
                return "yunhu"

            def get_user_id(self):
                return "123"

        with patch("ErisPulse.Core.admin.get_admin_config", return_value=config):
            assert mgr.is_admin(FakeEvent()) is True

    def test_is_admin_from_event_not_admin(self):
        """事件对象不是管理员"""
        mgr = AdminManager()
        config = {"users": {"yunhu": ["123"]}}

        class FakeEvent:
            def get_platform(self):
                return "yunhu"

            def get_user_id(self):
                return "999"

        with patch("ErisPulse.Core.admin.get_admin_config", return_value=config):
            assert mgr.is_admin(FakeEvent()) is False

    def test_empty_user_id_returns_false(self):
        """空 user_id 返回 False"""
        mgr = AdminManager()
        with patch("ErisPulse.Core.admin.get_admin_config", return_value={"users": {}}):
            assert mgr.is_admin("yunhu", "") is False
            assert mgr.is_admin("yunhu", None) is False

    def test_empty_platform_with_dict_config(self):
        """dict 配置下空平台不匹配"""
        mgr = AdminManager()
        config = {"users": {"yunhu": ["123"]}}
        with patch("ErisPulse.Core.admin.get_admin_config", return_value=config):
            assert mgr.is_admin("", "123") is False


class TestAdminRuntime:
    """运行时增删测试"""

    def test_add_platform_specific(self):
        """运行时添加指定平台管理员"""
        mgr = AdminManager()
        mgr.reset()
        with patch("ErisPulse.Core.admin.get_admin_config", return_value={"users": {}}):
            assert mgr.is_admin("yunhu", "999") is False
            mgr.add("yunhu", "999")
            assert mgr.is_admin("yunhu", "999") is True
            assert mgr.is_admin("telegram", "999") is False

    def test_add_global(self):
        """运行时添加全局管理员"""
        mgr = AdminManager()
        mgr.reset()
        with patch("ErisPulse.Core.admin.get_admin_config", return_value={"users": {}}):
            mgr.add(None, "888")
            assert mgr.is_admin("yunhu", "888") is True
            assert mgr.is_admin("telegram", "888") is True
            assert mgr.is_admin("any", "888") is True

    def test_remove(self):
        """移除运行时管理员"""
        mgr = AdminManager()
        mgr.reset()
        with patch("ErisPulse.Core.admin.get_admin_config", return_value={"users": {}}):
            mgr.add("yunhu", "999")
            assert mgr.is_admin("yunhu", "999") is True
            assert mgr.remove("yunhu", "999") is True
            assert mgr.is_admin("yunhu", "999") is False
            # 再次移除返回 False
            assert mgr.remove("yunhu", "999") is False

    def test_remove_global(self):
        """移除全局运行时管理员"""
        mgr = AdminManager()
        mgr.reset()
        with patch("ErisPulse.Core.admin.get_admin_config", return_value={"users": {}}):
            mgr.add(None, "888")
            assert mgr.remove(None, "888") is True
            assert mgr.is_admin("yunhu", "888") is False

    def test_reset_clears_runtime(self):
        """reset 清空运行时管理员"""
        mgr = AdminManager()
        mgr.add("yunhu", "999")
        mgr.add(None, "888")
        mgr.reset()
        with patch("ErisPulse.Core.admin.get_admin_config", return_value={"users": {}}):
            assert mgr.is_admin("yunhu", "999") is False
            assert mgr.is_admin("yunhu", "888") is False

    def test_config_and_runtime_combined(self):
        """配置管理员 + 运行时管理员同时生效"""
        mgr = AdminManager()
        mgr.reset()
        config = {"users": {"yunhu": ["123"]}}
        with patch("ErisPulse.Core.admin.get_admin_config", return_value=config):
            # 配置中的
            assert mgr.is_admin("yunhu", "123") is True
            # 运行时添加的
            mgr.add("telegram", "456")
            assert mgr.is_admin("telegram", "456") is True
            # 互不影响
            assert mgr.is_admin("telegram", "123") is False
            assert mgr.is_admin("yunhu", "456") is False


class TestAdminList:
    """list() 方法测试"""

    def test_list_empty(self):
        """无管理员时 list 返回空字典"""
        mgr = AdminManager()
        mgr.reset()
        with patch("ErisPulse.Core.admin.get_admin_config", return_value={"users": {}}):
            assert mgr.list() == {}

    def test_list_dict_config(self):
        """dict 配置的 list 输出"""
        mgr = AdminManager()
        mgr.reset()
        config = {"users": {"yunhu": ["123", "456"], "telegram": ["789"]}}
        with patch("ErisPulse.Core.admin.get_admin_config", return_value=config):
            result = mgr.list()
            assert result["yunhu"] == ["123", "456"]
            assert result["telegram"] == ["789"]
            assert "global" not in result

    def test_list_global_config(self):
        """list 格式配置的 list 输出"""
        mgr = AdminManager()
        mgr.reset()
        config = {"users": ["123", "456"]}
        with patch("ErisPulse.Core.admin.get_admin_config", return_value=config):
            result = mgr.list()
            assert result["global"] == ["123", "456"]

    def test_list_with_runtime_additions(self):
        """list 包含运行时添加的管理员"""
        mgr = AdminManager()
        mgr.reset()
        config = {"users": {"yunhu": ["123"]}}
        with patch("ErisPulse.Core.admin.get_admin_config", return_value=config):
            mgr.add("telegram", "789")
            mgr.add(None, "999")
            result = mgr.list()
            assert "123" in result["yunhu"]
            assert "789" in result["telegram"]
            assert "999" in result["global"]
