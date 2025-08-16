import asyncio
from ErisPulse import sdk
from ErisPulse.Core.Event import command

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