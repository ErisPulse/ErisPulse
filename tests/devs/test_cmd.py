import asyncio
import json
from ErisPulse import sdk
from ErisPulse.Core.Event import command, message, notice, request, meta

echo_handlers = {}
# 管理员用户ID列表
admin_users = ["5197892", "admin2"]

# 权限检查函数
def is_admin(event):
    user_id = event.get("user_id")
    return user_id in admin_users

@command("test", help="测试命令", usage="test [参数]")
async def test_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        target_type = "group"
        target_id = event["group_id"]
    else:
        target_type = "user"
        target_id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    await adapter.Send.To(target_type, target_id).Text("收到测试命令")
    sdk.logger.info(f"处理测试命令: {event}")

@command(["alias", "别名"], aliases=["a"], help="别名命令测试", usage="alias 或 a")
async def alias_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        target_type = "group"
        target_id = event["group_id"]
    else:
        target_type = "user"
        target_id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    used_name = event["command"]["name"]
    await adapter.Send.To(target_type, target_id).Text(f"通过别名 '{used_name}' 调用了命令")

@command("admin", group="admin", help="管理员命令组测试", usage="admin")
async def admin_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        target_type = "group"
        target_id = event["group_id"]
    else:
        target_type = "user"
        target_id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    await adapter.Send.To(target_type, target_id).Text("管理员命令执行成功")

@command("hidden", hidden=True, help="隐藏命令", usage="hidden")
async def hidden_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        target_type = "group"
        target_id = event["group_id"]
    else:
        target_type = "user"
        target_id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    await adapter.Send.To(target_type, target_id).Text("这是一个隐藏命令")

@command("echo", help="开关回显命令", usage="echo <on|off>")
async def echo_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        target_type = "group"
        target_id = event["group_id"]
    else:
        target_type = "user"
        target_id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    
    args = event["command"]["args"]
    if not args:
        await adapter.Send.To(target_type, target_id).Text("用法: echo <on|off>")
        return
    
    action = args[0].lower()
    handler_key = f"{target_type}_{target_id}_{platform}"
    
    if action == "on":
        # 如果已经存在echo处理器，先注销它
        if handler_key in echo_handlers:
            try:
                message.remove_message_handler(echo_handlers[handler_key])
            except Exception as e:
                sdk.logger.warning(f"注销旧的echo处理器时出错: {e}")
        
        # 注册新的echo消息处理器
        echo_handler = message.on_message()(echo_message_handler)
        echo_handlers[handler_key] = echo_handler
        
        await adapter.Send.To(target_type, target_id).Text("Echo功能已开启")
    elif action == "off":
        # 注销echo消息处理器
        if handler_key in echo_handlers:
            try:
                message.remove_message_handler(echo_handlers[handler_key])
                del echo_handlers[handler_key]
                await adapter.Send.To(target_type, target_id).Text("Echo功能已关闭")
            except Exception as e:
                sdk.logger.error(f"注销echo处理器时出错: {e}")
                await adapter.Send.To(target_type, target_id).Text("关闭Echo功能时发生错误")
        else:
            await adapter.Send.To(target_type, target_id).Text("Echo功能未开启")
    else:
        await adapter.Send.To(target_type, target_id).Text("无效参数，请使用 'on' 或 'off'")

async def echo_message_handler(event):
    sdk.logger.info(f"处理Echo命令: {event}")
    # 避免echo处理器处理命令消息，防止无限循环
    if event.get("command"):
        return
    
    platform = event["platform"]

    event_copy = event.copy()
    keys_to_remove = []
    for key in event_copy.keys():
        if key.endswith("_raw"):
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del event_copy[key]
    
    # 发送事件内容
    if event.get("detail_type") == "group":
        target_type = "group"
        target_id = event["group_id"]
    else:
        target_type = "user"
        target_id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    
    event_json = json.dumps(event_copy, ensure_ascii=False, indent=2)
    await adapter.Send.To(target_type, target_id).Text(f"Echo事件内容:\n{event_json}")

@command("permission", permission=is_admin, help="需要权限的命令", usage="permission")
async def permission_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        target_type = "group"
        target_id = event["group_id"]
    else:
        target_type = "user"
        target_id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    await adapter.Send.To(target_type, target_id).Text("权限检查通过，命令执行成功")

@command("args", help="参数测试命令", usage="args <参数1> [参数2] ...")
async def args_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        target_type = "group"
        target_id = event["group_id"]
    else:
        target_type = "user"
        target_id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    
    args = event["command"]["args"]
    if not args:
        await adapter.Send.To(target_type, target_id).Text("未提供参数")
    else:
        args_str = ", ".join(args)
        await adapter.Send.To(target_type, target_id).Text(f"接收到参数: {args_str}")

@command("ask", help="交互式询问命令", usage="ask")
async def ask_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        target_type = "group"
        target_id = event["group_id"]
    else:
        target_type = "user"
        target_id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    
    # 询问用户姓名
    await adapter.Send.To(target_type, target_id).Text("请输入姓名:")
    name_event = await command.wait_reply(event, timeout=30.0)
    
    if not name_event:
        await adapter.Send.To(target_type, target_id).Text("您没有在规定时间内回复，操作已取消。")
        return
    
    # 提取姓名
    name = ""
    for segment in name_event.get("message", []):
        if segment.get("type") == "text":
            name = segment.get("data", {}).get("text", "").strip()
            break
    
    if not name:
        await adapter.Send.To(target_type, target_id).Text("未收到有效姓名，操作已取消。")
        return
    
    # 询问用户年龄
    await adapter.Send.To(target_type, target_id).Text(f"您好 {name}，请输入年龄:")
    age_event = await command.wait_reply(event, timeout=30.0)
    
    if not age_event:
        await adapter.Send.To(target_type, target_id).Text("您没有在规定时间内回复，操作已取消。")
        return
    
    # 提取年龄
    age = ""
    for segment in age_event.get("message", []):
        if segment.get("type") == "text":
            age = segment.get("data", {}).get("text", "").strip()
            break
    
    # 验证年龄是否为数字
    if not age.isdigit():
        await adapter.Send.To(target_type, target_id).Text("年龄必须是数字，操作已取消。")
        return
    
    age_num = int(age)
    
    # 询问用户身份
    await adapter.Send.To(target_type, target_id).Text(f"您好 {name}，请输入身份:")
    identity_event = await command.wait_reply(event, timeout=30.0)
    
    if not identity_event:
        await adapter.Send.To(target_type, target_id).Text("您没有在规定时间内回复，操作已取消。")
        return
    
    # 提取身份信息
    identity = ""
    for segment in identity_event.get("message", []):
        if segment.get("type") == "text":
            identity = segment.get("data", {}).get("text", "").strip()
            break
    
    if not identity:
        await adapter.Send.To(target_type, target_id).Text("未收到有效身份信息，操作已取消。")
        return
    
    # 生成结果消息
    result_msg = f"{name}，{age_num}岁，是个{identity}"
    await adapter.Send.To(target_type, target_id).Text(result_msg)
    
    sdk.logger.info(f"收集到用户信息: {name}, {age_num}岁, 身份: {identity}")

@command("confirm", help="确认操作命令", usage="confirm")
async def confirm_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        target_type = "group"
        target_id = event["group_id"]
    else:
        target_type = "user"
        target_id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    
    # 定义验证函数，只接受"是"或"否"
    def validate_yes_no(reply_event):
        text_content = ""
        for segment in reply_event.get("message", []):
            if segment.get("type") == "text":
                text_content = segment.get("data", {}).get("text", "").strip().lower()
                break
        return text_content in ["是", "否", "yes", "no", "y", "n"]
    
    # 定义回调函数
    async def handle_confirmation(reply_event):
        text_content = ""
        for segment in reply_event.get("message", []):
            if segment.get("type") == "text":
                text_content = segment.get("data", {}).get("text", "").strip().lower()
                break
        
        if text_content in ["是", "yes", "y"]:
            await adapter.Send.To(target_type, target_id).Text("操作已确认！正在执行...")
            # 模拟执行操作
            await asyncio.sleep(1)
            await adapter.Send.To(target_type, target_id).Text("操作执行完成！")
        else:
            await adapter.Send.To(target_type, target_id).Text("操作已取消。")
    
    # 发送确认请求并等待回复
    await command.wait_reply(
        event, 
        prompt="您确定要执行此重要操作吗？请输入'是'或'否':",
        timeout=30.0,
        callback=handle_confirmation,
        validator=validate_yes_no
    )

@command("config", permission=is_admin, help="配置管理命令", usage="config <key> [value]")
async def config_command(event):
    platform = event["platform"]
    
    if event.get("detail_type") == "group":
        target_type = "group"
        target_id = event["group_id"]
    else:
        target_type = "user"
        target_id = event["user_id"]
    
    adapter = getattr(sdk.adapter, platform)
    args = event["command"]["args"]
    
    if len(args) == 0:
        await adapter.Send.To(target_type, target_id).Text("用法: config <key> [value]")
        return
    
    key = args[0]
    
    if len(args) == 1:
        # 获取配置值
        value = sdk.storage.get(key, "未设置")
        await adapter.Send.To(target_type, target_id).Text(f"配置 {key} = {value}")
    else:
        # 设置配置值
        value = " ".join(args[1:])
        sdk.storage.set(key, value)
        await adapter.Send.To(target_type, target_id).Text(f"配置 {key} 已设置为 {value}")

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
    
    # 发送欢迎消息
    platform = event["platform"]
    user_id = event["user_id"]
    
    try:
        adapter = getattr(sdk.adapter, platform)
        await adapter.Send.To("user", user_id).Text("欢迎添加我为好友！")
    except Exception as e:
        sdk.logger.error(f"发送欢迎消息失败: {e}")

@notice.on_group_increase()
async def group_increase_handler(event):
    sdk.logger.info(f"新成员加入群: {event.get('group_id')}，用户: {event.get('user_id')}")
    
    # 发送欢迎消息
    platform = event["platform"]
    group_id = event["group_id"]
    user_id = event["user_id"]
    
    try:
        adapter = getattr(sdk.adapter, platform)
        await adapter.Send.To("group", group_id).Text(f"欢迎新成员 <@{user_id}> 加入群聊！")
    except Exception as e:
        sdk.logger.error(f"发送群欢迎消息失败: {e}")

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