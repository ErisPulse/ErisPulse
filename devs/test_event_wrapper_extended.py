"""
测试 Event 包装类的扩展功能
测试 _get_adapter_and_target 方法和新的 getter 方法
"""

from ErisPulse.Core.Event.wrapper import Event

def test_get_adapter_and_target():
    """测试 _get_adapter_and_target 方法的各种情况"""
    print("=== 测试 _get_adapter_and_target 方法 ===\n")
    
    test_cases = [
        {
            "name": "标准私聊消息",
            "data": {
                "id": "1",
                "time": 1234567890,
                "type": "message",
                "detail_type": "private",
                "platform": "test",
                "self": {"platform": "test", "user_id": "bot_123"},
                "user_id": "user_456"
            },
            "expected_detail_type": "user",  # 事件 detail_type "private" 映射为发送目标 "user"
            "expected_target_id": "user_456"
        },
        {
            "name": "标准群聊消息",
            "data": {
                "id": "2",
                "time": 1234567890,
                "type": "message",
                "detail_type": "group",
                "platform": "test",
                "self": {"platform": "test", "user_id": "bot_123"},
                "user_id": "user_456",
                "group_id": "group_789"
            },
            "expected_detail_type": "group",
            "expected_target_id": "group_789"
        },
        {
            "name": "频道消息",
            "data": {
                "id": "3",
                "time": 1234567890,
                "type": "message",
                "detail_type": "channel",
                "platform": "test",
                "self": {"platform": "test", "user_id": "bot_123"},
                "user_id": "user_456",
                "channel_id": "channel_123"
            },
            "expected_detail_type": "channel",
            "expected_target_id": "channel_123"
        },
        {
            "name": "服务器消息",
            "data": {
                "id": "4",
                "time": 1234567890,
                "type": "message",
                "detail_type": "guild",
                "platform": "test",
                "self": {"platform": "test", "user_id": "bot_123"},
                "user_id": "user_456",
                "guild_id": "guild_456"
            },
            "expected_detail_type": "guild",
            "expected_target_id": "guild_456"
        },
        {
            "name": "话题消息",
            "data": {
                "id": "5",
                "time": 1234567890,
                "type": "message",
                "detail_type": "thread",
                "platform": "test",
                "self": {"platform": "test", "user_id": "bot_123"},
                "user_id": "user_456",
                "thread_id": "thread_789"
            },
            "expected_detail_type": "thread",
            "expected_target_id": "thread_789"
        },
        {
            "name": "兼容 user 类型",
            "data": {
                "id": "6",
                "time": 1234567890,
                "type": "message",
                "detail_type": "user",
                "platform": "test",
                "self": {"platform": "test", "user_id": "bot_123"},
                "user_id": "user_456"
            },
            "expected_detail_type": "user",
            "expected_target_id": "user_456"
        },
        {
            "name": "Telegram supergroup",
            "data": {
                "id": "7",
                "time": 1234567890,
                "type": "message",
                "detail_type": "supergroup",
                "platform": "test",
                "self": {"platform": "test", "user_id": "bot_123"},
                "user_id": "user_456",
                "group_id": "group_789"
            },
            "expected_detail_type": "group",  # supergroup 映射为 group
            "expected_target_id": "group_789"
        }
    ]
    
    # 模拟适配器
    class MockAdapter:
        pass
    
    import ErisPulse.Core.adapter as adapter_module
    adapter_module.test = MockAdapter()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}:")
        event = Event(test_case['data'])
        try:
            adapter_instance, detail_type, target_id = event._get_adapter_and_target()
            print(f"   detail_type: {detail_type}")
            print(f"   target_id: {target_id}")
            
            if detail_type == test_case['expected_detail_type'] and target_id == test_case['expected_target_id']:
                print(f"   ✓ 测试通过")
            else:
                print(f"   ✗ 测试失败")
                print(f"     期望 detail_type: {test_case['expected_detail_type']}, 实际: {detail_type}")
                print(f"     期望 target_id: {test_case['expected_target_id']}, 实际: {target_id}")
        except Exception as e:
            print(f"   ✗ 测试失败: {e}")
        print()
    
    # 清理
    delattr(adapter_module, 'test')
    
    print("=== _get_adapter_and_target 测试完成 ===\n")

def test_new_getter_methods():
    """测试新增的 getter 方法"""
    print("=== 测试新增的 getter 方法 ===\n")
    
    # 测试频道事件
    channel_event = Event({
        "id": "1",
        "time": 1234567890,
        "type": "message",
        "detail_type": "channel",
        "platform": "test",
        "self": {"platform": "test", "user_id": "bot_123"},
        "user_id": "user_456",
        "channel_id": "channel_123"
    })
    
    print("频道事件测试:")
    print(f"   get_channel_id(): {channel_event.get_channel_id()}")
    print(f"   get_guild_id(): {channel_event.get_guild_id()}")
    print(f"   get_thread_id(): {channel_event.get_thread_id()}")
    
    # 测试服务器事件
    guild_event = Event({
        "id": "2",
        "time": 1234567890,
        "type": "message",
        "detail_type": "guild",
        "platform": "test",
        "self": {"platform": "test", "user_id": "bot_123"},
        "user_id": "user_456",
        "guild_id": "guild_456"
    })
    
    print("\n服务器事件测试:")
    print(f"   get_channel_id(): {guild_event.get_channel_id()}")
    print(f"   get_guild_id(): {guild_event.get_guild_id()}")
    print(f"   get_thread_id(): {guild_event.get_thread_id()}")
    
    # 测试话题事件
    thread_event = Event({
        "id": "3",
        "time": 1234567890,
        "type": "message",
        "detail_type": "thread",
        "platform": "test",
        "self": {"platform": "test", "user_id": "bot_123"},
        "user_id": "user_456",
        "thread_id": "thread_789"
    })
    
    print("\n话题事件测试:")
    print(f"   get_channel_id(): {thread_event.get_channel_id()}")
    print(f"   get_guild_id(): {thread_event.get_guild_id()}")
    print(f"   get_thread_id(): {thread_event.get_thread_id()}")
    
    print("\n=== 新增 getter 方法测试完成 ===\n")

def test_compatibility_handling():
    """测试兼容性处理"""
    print("=== 测试兼容性处理 ===\n")
    
    # 模拟适配器
    class MockAdapter:
        pass
    
    import ErisPulse.Core.adapter as adapter_module
    adapter_module.test = MockAdapter()
    
    # 测试当 channel_id 为空时，尝试使用 group_id
    print("1. 频道类型，但 channel_id 为空，有 group_id:")
    event1 = Event({
        "id": "1",
        "time": 1234567890,
        "type": "message",
        "detail_type": "channel",
        "platform": "test",
        "self": {"platform": "test", "user_id": "bot_123"},
        "user_id": "user_456",
        "group_id": "group_789"  # 没有 channel_id，但有 group_id
    })
    
    try:
        adapter_instance, detail_type, target_id = event1._get_adapter_and_target()
        print(f"   detail_type: {detail_type}")
        print(f"   target_id: {target_id}")
        print(f"   ✓ 成功获取目标 ID")
    except Exception as e:
        print(f"   ✗ 失败: {e}")
    
    print()
    
    # 测试当所有可能的 ID 都为空时
    print("2. 频道类型，但所有可能的 ID 都为空:")
    event2 = Event({
        "id": "2",
        "time": 1234567890,
        "type": "message",
        "detail_type": "channel",
        "platform": "test",
        "self": {"platform": "test", "user_id": "bot_123"},
        "user_id": "user_456"
        # 没有 channel_id、group_id、guild_id
    })
    
    try:
        adapter_instance, detail_type, target_id = event2._get_adapter_and_target()
        print(f"   detail_type: {detail_type}")
        print(f"   target_id: {target_id}")
        print(f"   ✗ 应该抛出异常但没有")
    except ValueError as e:
        print(f"   ✓ 正确抛出异常: {e}")
    
    # 清理
    delattr(adapter_module, 'test')
    
    print("\n=== 兼容性处理测试完成 ===\n")

if __name__ == "__main__":
    test_get_adapter_and_target()
    test_new_getter_methods()
    test_compatibility_handling()
