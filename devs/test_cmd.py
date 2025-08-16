import asyncio
import json
from ErisPulse import sdk
from ErisPulse.Core.Event import command

echo_status = False

@command("test", help="测试命令", usage="/test [参数]")
async def test_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group" or event.get("type") == "group":
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
    
    if event.get("detail_type") == "group" or event.get("type") == "group":
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
    
    if event.get("detail_type") == "group" or event.get("type") == "group":
        type = "group"
        id = event["group_id"]
    else:
        type = "user"
        id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    
    # 解析参数
    alt_message = event["alt_message"].strip()
    args = alt_message.split()[1:]
    
    global echo_status
    
    if not args:
        # 没有参数，显示当前状态
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