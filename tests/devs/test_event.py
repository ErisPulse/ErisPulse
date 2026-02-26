"""
事件系统测试脚本

包含以下测试内容：
1. 事件处理系统测试（命令、消息、通知、元事件）
2. Event包装类基础功能测试
3. Event包装类扩展功能测试
"""

import asyncio
import time
from ErisPulse import sdk
from ErisPulse.Core.Event import command, message, notice, meta

# ==================== 第一部分：事件处理系统测试 ====================

# 测试命令处理
@command("test", help="测试命令", usage="/test [参数]")
async def test_command(event):
    """测试命令处理功能"""
    platform = event["platform"]
    user_id = event["user_id"]
    
    reply = "收到测试命令，无参数"
    
    adapter = getattr(sdk.adapter, platform)
    await adapter.Send.To("user", user_id).Text(reply)
    sdk.logger.info(f"处理测试命令: {event}")

# 测试消息事件处理
@message.on_message()
async def handle_all_messages(event):
    """处理所有消息事件"""
    sdk.logger.info(f"收到消息事件: {event['alt_message']}")

@message.on_private_message()
async def handle_private_messages(event):
    """处理私聊消息事件"""
    sdk.logger.info(f"收到私聊消息，来自用户: {event['user_id']}")

@message.on_group_message()
async def handle_group_messages(event):
    """处理群消息事件"""
    sdk.logger.info(f"收到群消息，群: {event['group_id']}，用户: {event['user_id']}")

# 测试通知事件处理
@notice.on_friend_add()
async def handle_friend_add(event):
    """处理好友添加通知"""
    sdk.logger.info(f"新好友添加: {event['user_id']}")
    
    platform = event["platform"]
    user_id = event["user_id"]
    adapter = getattr(sdk.adapter, platform)
    await adapter.Send.To("user", user_id).Text("感谢添加我为好友！")

@notice.on_group_increase()
async def handle_group_increase(event):
    """处理群成员增加通知"""
    sdk.logger.info(f"新成员加入群: {event['group_id']}，用户: {event['user_id']}")

# 测试元事件处理
@meta.on_connect()
async def handle_connect(event):
    """处理连接成功事件"""
    sdk.logger.info(f"平台 {event['platform']} 连接成功")

@meta.on_disconnect()
async def handle_disconnect(event):
    """处理断开连接事件"""
    sdk.logger.info(f"平台 {event['platform']} 断开连接")

# 测试中间件
@message.handler.middleware
async def message_middleware(event):
    """消息中间件"""
    sdk.logger.info(f"消息中间件处理: {event['message_id']}")
    return event

@command.handler.middleware
async def command_middleware(event):
    """命令中间件"""
    sdk.logger.info(f"命令中间件处理: {event}")
    return event

async def test_event_system():
    """运行事件处理系统测试"""
    try:
        isInit = await sdk.init_task()
        
        if not isInit:
            sdk.logger.error("ErisPulse 初始化失败，请检查日志")
            return
        
        await sdk.adapter.startup()
        
        # 模拟发送测试事件
        test_event = {
            "id": "test_event_123",
            "time": int(time.time()),
            "type": "message",
            "detail_type": "private",
            "platform": "yunhu",
            "self": {"platform": "yunhu", "user_id": "bot_123"},
            "message_id": "test_msg_456",
            "message": [{"type": "text", "data": {"text": "/test 测试参数"}}],
            "alt_message": "/test 测试参数",
            "user_id": "user_789"
        }
        await sdk.adapter.emit(test_event)
        
        # 保持程序运行
        await asyncio.Event().wait()
    except Exception as e:
        sdk.logger.error(f"测试程序出错: {e}")
    except KeyboardInterrupt:
        sdk.logger.info("正在停止测试程序")
    finally:
        await sdk.adapter.shutdown()


# ==================== 第二部分：Event包装类基础功能测试 ====================

from ErisPulse.Core.Event.wrapper import Event

def test_event_wrapper_basic():
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
    
    print("=== 测试Event包装类基础功能 ===\n")
    
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
    
    print("\n=== Event包装类基础功能测试通过 ===")

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
    
    print("\n=== 通知事件测试通过 ===")

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
    
    print("\n=== 请求事件测试通过 ===")


# ==================== 第三部分：Event包装类扩展功能测试 ====================

def test_get_adapter_and_target():
    """测试 _get_adapter_and_target 方法的各种情况"""
    print("\n\n=== 测试 _get_adapter_and_target 方法 ===\n")
    
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
            "expected_detail_type": "user",
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
            "expected_detail_type": "group",
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
                print(f"   通过")
            else:
                print(f"   失败")
                print(f"     期望 detail_type: {test_case['expected_detail_type']}, 实际: {detail_type}")
                print(f"     期望 target_id: {test_case['expected_target_id']}, 实际: {target_id}")
        except Exception as e:
            print(f"   失败: {e}")
        print()
    
    # 清理
    delattr(adapter_module, 'test')
    
    print("=== _get_adapter_and_target 方法测试完成 ===\n")

def test_new_getter_methods():
    """测试新增的 getter 方法"""
    print("\n\n=== 测试新增的 getter 方法 ===\n")
    
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
    print("\n\n=== 测试兼容性处理 ===\n")
    
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
        "group_id": "group_789"
    })
    
    try:
        adapter_instance, detail_type, target_id = event1._get_adapter_and_target()
        print(f"   detail_type: {detail_type}")
        print(f"   target_id: {target_id}")
        print(f"   成功获取目标 ID")
    except Exception as e:
        print(f"   失败: {e}")
    
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
    })
    
    try:
        adapter_instance, detail_type, target_id = event2._get_adapter_and_target()
        print(f"   detail_type: {detail_type}")
        print(f"   target_id: {target_id}")
        print(f"   应该抛出异常但没有")
    except ValueError as e:
        print(f"   正确抛出异常: {e}")
    
    # 清理
    delattr(adapter_module, 'test')
    
    print("\n=== 兼容性处理测试完成 ===\n")


# ==================== 主函数 ====================

if __name__ == "__main__":
    import sys
    
    # 根据参数选择运行哪个测试
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        
        if test_type == "system":
            print("运行事件处理系统测试\n")
            asyncio.run(test_event_system())
        elif test_type == "basic":
            print("运行Event包装类基础功能测试\n")
            test_event_wrapper_basic()
            test_notification_event()
            test_request_event()
        elif test_type == "extended":
            print("运行Event包装类扩展功能测试\n")
            test_get_adapter_and_target()
            test_new_getter_methods()
            test_compatibility_handling()
        elif test_type == "wrapper":
            print("运行Event包装类完整测试\n")
            test_event_wrapper_basic()
            test_notification_event()
            test_request_event()
            test_get_adapter_and_target()
            test_new_getter_methods()
            test_compatibility_handling()
        else:
            print("未知的测试类型")
            print("可用选项:")
            print("  system   - 事件处理系统测试")
            print("  basic    - Event包装类基础功能测试")
            print("  extended - Event包装类扩展功能测试")
            print("  wrapper  - Event包装类完整测试")
            print("\n默认运行事件处理系统测试")
            asyncio.run(test_event_system())
    else:
        # 默认运行事件处理系统测试
        asyncio.run(test_event_system())