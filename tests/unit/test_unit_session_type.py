"""
会话类型管理模块单元测试

测试会话类型的注册、转换、推断等功能
"""

import pytest
from ErisPulse.Core.Event.session_type import (
    # 标准类型常量
    RECEIVE_TYPES,
    SEND_TYPES,
    
    # 自定义类型注册
    register_custom_type,
    unregister_custom_type,
    
    # 类型获取方法
    get_id_field,
    get_receive_type,
    convert_to_send_type,
    convert_to_receive_type,
    
    # 自动推断方法
    infer_receive_type,
    get_target_id,
    get_send_type_and_target_id,
    
    # 工具方法
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)


class TestStandardTypes:
    """测试标准类型常量"""
    
    def test_receive_types_exist(self):
        """测试接收类型常量存在"""
        assert "private" in RECEIVE_TYPES
        assert "group" in RECEIVE_TYPES
        assert "user" in RECEIVE_TYPES
        assert "channel" in RECEIVE_TYPES
        assert "guild" in RECEIVE_TYPES
        assert "thread" in RECEIVE_TYPES
    
    def test_send_types_exist(self):
        """测试发送类型常量存在"""
        assert "user" in SEND_TYPES
        assert "group" in SEND_TYPES
        assert "channel" in SEND_TYPES
        assert "guild" in SEND_TYPES
        assert "thread" in SEND_TYPES
        assert "private" not in SEND_TYPES  # private 不在发送类型中


class TestTypeConversion:
    """测试类型转换"""
    
    def test_convert_private_to_user(self):
        """测试 private → user 转换"""
        assert convert_to_send_type("private") == "user"
        assert convert_to_send_type("private", "test_platform") == "user"
    
    def test_convert_user_to_user(self):
        """测试 user → user 转换"""
        assert convert_to_send_type("user") == "user"
    
    def test_convert_group_to_group(self):
        """测试 group → group 转换"""
        assert convert_to_send_type("group") == "group"
    
    def test_convert_channel_to_channel(self):
        """测试 channel → channel 转换"""
        assert convert_to_send_type("channel") == "channel"
    
    def test_convert_guild_to_guild(self):
        """测试 guild → guild 转换"""
        assert convert_to_send_type("guild") == "guild"
    
    def test_convert_thread_to_thread(self):
        """测试 thread → thread 转换"""
        assert convert_to_send_type("thread") == "thread"
    
    def test_convert_send_to_receive_user(self):
        """测试 user → private 转换"""
        assert convert_to_receive_type("user") == "private"
    
    def test_convert_send_to_receive_group(self):
        """测试 group → group 转换"""
        assert convert_to_receive_type("group") == "group"


class TestTypeInference:
    """测试类型推断"""
    
    def test_infer_from_group_id(self):
        """测试根据 group_id 推断类型"""
        event = {"group_id": "123", "user_id": "456"}
        assert infer_receive_type(event) == "group"
    
    def test_infer_from_channel_id(self):
        """测试根据 channel_id 推断类型"""
        event = {"channel_id": "789", "user_id": "456"}
        assert infer_receive_type(event) == "channel"
    
    def test_infer_from_guild_id(self):
        """测试根据 guild_id 推断类型"""
        event = {"guild_id": "101", "user_id": "456"}
        assert infer_receive_type(event) == "guild"
    
    def test_infer_from_thread_id(self):
        """测试根据 thread_id 推断类型"""
        event = {"thread_id": "202", "user_id": "456"}
        assert infer_receive_type(event) == "thread"
    
    def test_infer_from_user_id(self):
        """测试根据 user_id 推断类型"""
        event = {"user_id": "456"}
        assert infer_receive_type(event) == "private"
    
    def test_infer_with_detail_type(self):
        """测试优先使用 detail_type"""
        event = {
            "detail_type": "group",
            "group_id": "123",
            "channel_id": "456"
        }
        assert infer_receive_type(event) == "group"
    
    def test_infer_empty_event(self):
        """测试空事件"""
        event = {}
        # 空事件返回默认值 'private'
        assert infer_receive_type(event) == "private"


class TestTargetId:
    """测试目标ID获取"""
    
    def test_get_target_id_from_group(self):
        """测试从群组事件获取目标ID"""
        event = {"group_id": "123", "user_id": "456"}
        assert get_target_id(event, "test_platform") == "123"
    
    def test_get_target_id_from_channel(self):
        """测试从频道事件获取目标ID"""
        event = {"channel_id": "789", "user_id": "456"}
        assert get_target_id(event, "test_platform") == "789"
    
    def test_get_target_id_from_private(self):
        """测试从私聊事件获取目标ID"""
        event = {"user_id": "456"}
        assert get_target_id(event, "test_platform") == "456"
    
    def test_get_target_id_with_detail_type(self):
        """测试根据 detail_type 获取目标ID"""
        event = {
            "detail_type": "channel",
            "channel_id": "789",
            "user_id": "456"
        }
        assert get_target_id(event, "test_platform") == "789"


class TestSendTypeAndTargetId:
    """测试发送类型和目标ID获取"""
    
    def test_from_private_event(self):
        """测试从私聊事件获取"""
        event = {
            "detail_type": "private",
            "user_id": "456"
        }
        send_type, target_id = get_send_type_and_target_id(event, "test_platform")
        assert send_type == "user"
        assert target_id == "456"
    
    def test_from_group_event(self):
        """测试从群聊事件获取"""
        event = {
            "detail_type": "group",
            "group_id": "123",
            "user_id": "456"
        }
        send_type, target_id = get_send_type_and_target_id(event, "test_platform")
        assert send_type == "group"
        assert target_id == "123"
    
    def test_from_channel_event(self):
        """测试从频道事件获取"""
        event = {
            "detail_type": "channel",
            "channel_id": "789",
            "user_id": "456"
        }
        send_type, target_id = get_send_type_and_target_id(event, "test_platform")
        assert send_type == "channel"
        assert target_id == "789"


class TestCustomTypes:
    """测试自定义类型"""
    
    def setup_method(self):
        """每个测试前清理自定义类型"""
        clear_custom_types()
    
    def teardown_method(self):
        """每个测试后清理自定义类型"""
        clear_custom_types()
    
    def test_register_custom_type(self):
        """测试注册自定义类型"""
        register_custom_type(
            receive_type="custom_type",
            send_type="custom_send",
            id_field="custom_id",
            platform="TestPlatform"
        )
        
        # 验证转换
        assert convert_to_send_type("custom_type", "TestPlatform") == "custom_send"
        assert get_id_field("custom_type", "TestPlatform") == "custom_id"
    
    def test_unregister_custom_type(self):
        """测试注销自定义类型"""
        register_custom_type(
            receive_type="custom_type",
            send_type="custom_send",
            id_field="custom_id",
            platform="TestPlatform"
        )
        
        # 先验证存在
        assert convert_to_send_type("custom_type", "TestPlatform") == "custom_send"
        
        # 注销
        unregister_custom_type("custom_type", "TestPlatform")
        
        # 再次注销应该不会报错
        unregister_custom_type("custom_type", "TestPlatform")
    
    def test_custom_type_inference(self):
        """测试自定义类型推断"""
        register_custom_type(
            receive_type="custom_type",
            send_type="custom_send",
            id_field="custom_id",
            platform="TestPlatform"
        )
        
        event = {
            "custom_id": "999",
            "user_id": "456"
        }
        
        # 由于自定义类型优先级较低，应该推断为 private
        assert infer_receive_type(event, "TestPlatform") == "private"
        
        # 但如果明确指定 detail_type，可以获取对应字段
        assert get_target_id({"detail_type": "custom_type", "custom_id": "999"}, "TestPlatform") == "999"


class TestUtilityMethods:
    """测试工具方法"""
    
    def test_is_standard_type(self):
        """测试标准类型判断"""
        assert is_standard_type("private") is True
        assert is_standard_type("group") is True
        assert is_standard_type("channel") is True
        assert is_standard_type("unknown") is False
    
    def test_is_valid_send_type(self):
        """测试发送类型验证"""
        assert is_valid_send_type("user") is True
        assert is_valid_send_type("group") is True
        assert is_valid_send_type("channel") is True
        assert is_valid_send_type("private") is False
    
    def test_get_standard_types(self):
        """测试获取标准类型列表"""
        types = get_standard_types()
        assert "private" in types
        assert "group" in types
        assert "channel" in types
        assert "guild" in types
        assert "thread" in types
        assert "user" in types
    
    def test_get_send_types(self):
        """测试获取发送类型列表"""
        types = get_send_types()
        assert "user" in types
        assert "group" in types
        assert "channel" in types
        assert "guild" in types
        assert "thread" in types
        assert "private" not in types
    
    def test_clear_custom_types(self):
        """测试清理自定义类型"""
        register_custom_type(
            receive_type="custom_type",
            send_type="custom_send",
            id_field="custom_id",
            platform="TestPlatform"
        )
        
        # 验证存在
        assert convert_to_send_type("custom_type", "TestPlatform") == "custom_send"
        
        # 清理自定义类型
        clear_custom_types()
        
        # 清理后，尝试获取标准类型的转换应该仍然正常工作
        assert convert_to_send_type("private", "TestPlatform") == "user"
        assert convert_to_send_type("group", "TestPlatform") == "group"
