import asyncio
import time
from ErisPulse import sdk
from ErisPulse.Core.Event import command, message, notice, meta

# 测试命令处理
@command("test", help="测试命令", usage="/test [参数]")
async def test_command(event):
    platform = event["platform"]
    user_id = event["user_id"]
    
    reply = "收到测试命令，无参数"
    
    adapter = getattr(sdk.adapter, platform)
    await adapter.Send.To("user", user_id).Text(reply)
    sdk.logger.info(f"处理测试命令: {event}")

# 测试消息事件处理
@message.on_message()
async def handle_all_messages(event):
    sdk.logger.info(f"收到消息事件: {event['alt_message']}")

@message.on_private_message()
async def handle_private_messages(event):
    sdk.logger.info(f"收到私聊消息，来自用户: {event['user_id']}")

@message.on_group_message()
async def handle_group_messages(event):
    sdk.logger.info(f"收到群消息，群: {event['group_id']}，用户: {event['user_id']}")

# 测试通知事件处理
@notice.on_friend_add()
async def handle_friend_add(event):
    sdk.logger.info(f"新好友添加: {event['user_id']}")
    
    platform = event["platform"]
    user_id = event["user_id"]
    adapter = getattr(sdk.adapter, platform)
    await adapter.Send.To("user", user_id).Text("感谢添加我为好友！")

@notice.on_group_increase()
async def handle_group_increase(event):
    sdk.logger.info(f"新成员加入群: {event['group_id']}，用户: {event['user_id']}")

# 测试元事件处理
@meta.on_connect()
async def handle_connect(event):
    sdk.logger.info(f"平台 {event['platform']} 连接成功")

@meta.on_disconnect()
async def handle_disconnect(event):
    sdk.logger.info(f"平台 {event['platform']} 断开连接")

# 测试中间件
@message.handler.middleware
async def message_middleware(event):
    sdk.logger.info(f"消息中间件处理: {event['message_id']}")
    return event

@command.handler.middleware
async def command_middleware(event):
    sdk.logger.info(f"命令中间件处理: {event}")
    return event

async def main():
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

if __name__ == "__main__":
    asyncio.run(main())