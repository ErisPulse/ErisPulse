import asyncio
import json
from ErisPulse import sdk
from ErisPulse.Core.Event import command, message, notice, request, meta

# 全局状态变量
echo_status = False
admin_users = ["5197892", "admin2"]  # 示例管理员用户ID

@command("test", help="测试命令", usage="/test [参数]")
async def test_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        type = "group"
        id = event["group_id"]
    else:
        type = "user"
        id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    await adapter.Send.To(type, id).Text("收到测试命令")
    sdk.logger.info(f"处理测试命令: {event}")

@command("help", help="帮助命令", usage="/help")
async def help_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        type = "group"
        id = event["group_id"]
    else:
        type = "user"
        id = event["user_id"]

    adapter = getattr(sdk.adapter, platform)
    await adapter.Send.To(type, id).Text(command.help())

@command("echo", help="控制事件回显", usage="/echo <on|off>")
async def echo_control_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        type = "group"
        id = event["group_id"]
    else:
        type = "user"
        id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    
    alt_message = event["alt_message"].strip()
    args = alt_message.split()[1:]
    
    global echo_status
    
    if not args:
        status_text = "开启" if echo_status else "关闭"
        await adapter.Send.To(type, id).Text(f"Echo当前状态: {status_text}")
        return
    
    subcommand = args[0].lower()
    
    if subcommand == "on":
        echo_status = True
        await adapter.Send.To(type, id).Text("Echo已开启")
    elif subcommand == "off":
        echo_status = False
        await adapter.Send.To(type, id).Text("Echo已关闭")
    else:
        await adapter.Send.To(type, id).Text("无效参数，请使用 'on' 或 'off'")

@command(["alias", "别名"], aliases=["a"], help="别名命令测试", usage="/alias 或 /a")
async def alias_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        type = "group"
        id = event["group_id"]
    else:
        type = "user"
        id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    used_name = event["command"]["name"]
    await adapter.Send.To(type, id).Text(f"通过别名 '{used_name}' 调用了命令")

@command("admin", group="admin", help="管理员命令组测试", usage="/admin")
async def admin_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        type = "group"
        id = event["group_id"]
    else:
        type = "user"
        id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    await adapter.Send.To(type, id).Text("管理员命令执行成功")

@command("hidden", hidden=True, help="隐藏命令", usage="/hidden")
async def hidden_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        type = "group"
        id = event["group_id"]
    else:
        type = "user"
        id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    await adapter.Send.To(type, id).Text("这是一个隐藏命令")

@command("permission", help="权限检查测试", usage="/permission")
def check_permission(event):
    user_id = event.get("user_id")
    return user_id in admin_users

@command("permission", permission=check_permission, help="需要权限的命令", usage="/permission")
async def permission_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        type = "group"
        id = event["group_id"]
    else:
        type = "user"
        id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    await adapter.Send.To(type, id).Text("权限检查通过，命令执行成功")

@command("args", help="参数测试命令", usage="/args <参数1> [参数2] ...")
async def args_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        type = "group"
        id = event["group_id"]
    else:
        type = "user"
        id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    
    args = event["command"]["args"]
    if not args:
        await adapter.Send.To(type, id).Text("未提供参数")
    else:
        args_str = ", ".join(args)
        await adapter.Send.To(type, id).Text(f"接收到参数: {args_str}")

@sdk.adapter.on("message")
async def echo_message(event):
    global echo_status
    platform = event["platform"]

    if echo_status:
        try:
            adapter = getattr(sdk.adapter, platform)
            
            if event.get("detail_type") == "group":
                target_type = "group"
                target_id = event["group_id"]
            else:
                target_type = "user"
                target_id = event["user_id"]
            
            event_copy = event.copy()
            platform_raw_key = f"{platform}_raw"
            if platform_raw_key in event_copy:
                del event_copy[platform_raw_key]
            
            event_str = json.dumps(event_copy, ensure_ascii=False, indent=2)
            if len(event_str) > 1000:
                event_str = event_str[:1000] + "... (内容过长已截断)"
            
            await adapter.Send.To(target_type, target_id).Text(f"Event内容:\n{event_str}")
        except Exception as e:
            sdk.logger.error(f"Echo回显失败: {e}")

    return event

# 消息事件处理测试
@message.on_message(priority=10)
async def message_handler(event):
    sdk.logger.info(f"消息处理器收到事件: {event.get('alt_message')}")

@message.on_private_message()
async def private_message_handler(event):
    sdk.logger.info(f"收到私聊消息，来自用户: {event.get('user_id')}")

@message.on_group_message()
async def group_message_handler(event):
    sdk.logger.info(f"收到群消息，群: {event.get('group_id')}，用户: {event.get('user_id')}")

# 通知事件处理测试
@notice.on_friend_add()
async def friend_add_handler(event):
    sdk.logger.info(f"新好友添加: {event.get('user_id')}")

@notice.on_group_increase()
async def group_increase_handler(event):
    sdk.logger.info(f"新成员加入群: {event.get('group_id')}，用户: {event.get('user_id')}")

# 请求事件处理测试
@request.on_friend_request()
async def friend_request_handler(event):
    sdk.logger.info(f"收到好友请求，来自用户: {event.get('user_id')}")

# 元事件处理测试
@meta.on_connect()
async def connect_handler(event):
    sdk.logger.info(f"平台 {event.get('platform')} 连接成功")

@meta.on_disconnect()
async def disconnect_handler(event):
    sdk.logger.info(f"平台 {event.get('platform')} 断开连接")

async def main():
    try:
        isInit = await sdk.init_task()
        
        if not isInit:
            sdk.logger.error("ErisPulse 初始化失败，请检查日志")
            return
        
        await sdk.adapter.startup()
        
        # 保持程序运行(不建议修改)
        await asyncio.Event().wait()
    except Exception as e:
        sdk.logger.error(e)
    except KeyboardInterrupt:
        sdk.logger.info("正在停止程序")
    finally:
        await sdk.adapter.shutdown()

if __name__ == "__main__":
    asyncio.run(main())