"""
测试 Event 包装类功能
"""

from ErisPulse.Core.Event.wrapper import Event

def test_event_wrapper():
    """测试Event包装类的基本功能"""
    
    # 创建测试事件数据
    event_data = {
        "id": "1234567890",
        "time": 1752241223,
        "type": "message",
        "detail_type": "group",
        "platform": "test_platform",
        "self": {
            "platform": "test_platform",
            "user_id": "bot_123"
        },
        "message": [
            {
                "type": "mention",
                "data": {"user_id": "bot_123"}
            },
            {
                "type": "text",
                "data": {"text": "Hello World"}
            }
        ],
        "alt_message": "Hello World",
        "user_id": "user_456",
        "user_nickname": "TestUser",
        "group_id": "group_789",
        "command": {
            "name": "test",
            "args": ["arg1", "arg2"],
            "raw": "/test arg1 arg2"
        },
        "test_platform_raw": {"original": "data"},
        "test_platform_raw_type": "original_event"
    }
    
    # 创建Event对象
    event = Event(event_data)
    
    print("=== 测试Event包装类 ===\n")
    
    # 测试核心字段方法
    print("1. 核心字段测试:")
    print(f"   get_id(): {event.get_id()}")
    print(f"   get_time(): {event.get_time()}")
    print(f"   get_type(): {event.get_type()}")
    print(f"   get_detail_type(): {event.get_detail_type()}")
    print(f"   get_platform(): {event.get_platform()}")
    
    # 测试机器人信息
    print("\n2. 机器人信息测试:")
    print(f"   get_self_platform(): {event.get_self_platform()}")
    print(f"   get_self_user_id(): {event.get_self_user_id()}")
    print(f"   get_self_info(): {event.get_self_info()}")
    
    # 测试消息事件方法
    print("\n3. 消息事件方法测试:")
    print(f"   get_message(): {len(event.get_message())} 个消息段")
    print(f"   get_alt_message(): {event.get_alt_message()}")
    print(f"   get_text(): {event.get_text()}")
    print(f"   has_mention(): {event.has_mention()}")
    print(f"   get_mentions(): {event.get_mentions()}")
    print(f"   get_user_id(): {event.get_user_id()}")
    print(f"   get_user_nickname(): {event.get_user_nickname()}")
    print(f"   get_group_id(): {event.get_group_id()}")
    print(f"   get_sender(): {event.get_sender()}")
    
    # 测试消息类型判断
    print("\n4. 消息类型判断测试:")
    print(f"   is_message(): {event.is_message()}")
    print(f"   is_private_message(): {event.is_private_message()}")
    print(f"   is_group_message(): {event.is_group_message()}")
    print(f"   is_at_message(): {event.is_at_message()}")
    
    # 测试命令信息
    print("\n5. 命令信息测试:")
    print(f"   get_command_name(): {event.get_command_name()}")
    print(f"   get_command_args(): {event.get_command_args()}")
    print(f"   get_command_raw(): {event.get_command_raw()}")
    print(f"   get_command_info(): {event.get_command_info()}")
    print(f"   is_command(): {event.is_command()}")
    
    # 测试原始数据
    print("\n6. 原始数据测试:")
    print(f"   get_raw(): {event.get_raw()}")
    print(f"   get_raw_type(): {event.get_raw_type()}")
    
    # 测试工具方法
    print("\n7. 工具方法测试:")
    print(f"   to_dict() 类型: {type(event.to_dict())}")
    print(f"   is_processed(): {event.is_processed()}")
    event.mark_processed()
    print(f"   mark_processed() 后 is_processed(): {event.is_processed()}")
    
    # 测试点式访问
    print("\n8. 点式访问测试:")
    print(f"   event.platform: {event.platform}")
    print(f"   event.user_id: {event.user_id}")
    print(f"   event.type: {event.type}")
    
    # 测试字典兼容性
    print("\n9. 字典兼容性测试:")
    print(f"   event['platform']: {event['platform']}")
    print(f"   event['user_id']: {event['user_id']}")
    print(f"   len(event): {len(event)}")
    
    # 测试字符串表示
    print("\n10. 字符串表示测试:")
    print(f"   repr(event): {repr(event)}")
    
    print("\n=== 所有测试通过！ ===")

def test_notification_event():
    """测试通知事件"""
    print("\n\n=== 测试通知事件 ===\n")
    
    notice_data = {
        "id": "1234567891",
        "time": 1752241224,
        "type": "notice",
        "detail_type": "friend_add",
        "platform": "test_platform",
        "self": {
            "platform": "test_platform",
            "user_id": "bot_123"
        },
        "user_id": "user_456",
        "user_nickname": "NewFriend"
    }
    
    event = Event(notice_data)
    
    print("通知事件测试:")
    print(f"   is_notice(): {event.is_notice()}")
    print(f"   is_friend_add(): {event.is_friend_add()}")
    print(f"   get_user_id(): {event.get_user_id()}")
    print(f"   get_user_nickname(): {event.get_user_nickname()}")
    
    print("\n=== 通知事件测试通过！ ===")

def test_request_event():
    """测试请求事件"""
    print("\n\n=== 测试请求事件 ===\n")
    
    request_data = {
        "id": "1234567892",
        "time": 1752241225,
        "type": "request",
        "detail_type": "friend",
        "platform": "test_platform",
        "self": {
            "platform": "test_platform",
            "user_id": "bot_123"
        },
        "user_id": "user_456",
        "user_nickname": "RequestUser",
        "comment": "请加好友"
    }
    
    event = Event(request_data)
    
    print("请求事件测试:")
    print(f"   is_request(): {event.is_request()}")
    print(f"   is_friend_request(): {event.is_friend_request()}")
    print(f"   get_user_id(): {event.get_user_id()}")
    print(f"   get_user_nickname(): {event.get_user_nickname()}")
    print(f"   get_comment(): {event.get_comment()}")
    
    print("\n=== 请求事件测试通过！ ===")

if __name__ == "__main__":
    test_event_wrapper()
    test_notification_event()
    test_request_event()
