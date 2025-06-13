from ErisPulse import sdk
import asyncio
from typing import Dict, Any

async def main():
    sdk.init()
    try:
        await sdk.adapter.startup()
        # OneBot 适配器处理
        # if hasattr(sdk.adapter, "QQ"):
        if 1 == 2:
            await asyncio.sleep(5)
            qq_adapter = sdk.adapter.QQ

            @qq_adapter.on("message")
            async def handle_qq_message(data):
                sdk.logger.info("接收到QQ消息事件:")
                sdk.logger.info(data)

            @qq_adapter.on("request")
            async def handle_qq_request(data):
                sdk.logger.info("接收到QQ请求事件:")
                sdk.logger.info(data)

            @qq_adapter.on("notify")
            async def handle_qq_notify(data):
                sdk.logger.info("接收到QQ通知事件:")
                sdk.logger.info(data)

            await qq_adapter.send("group", 782199153, "Hello from SDK!")
            await qq_adapter.call_api("send_msg", 
                message_type="group", 
                group_id=782199153, 
                message="Hello from SDKCallAPI!"
            )

        # 云湖适配器处理 - 完整事件处理
        if hasattr(sdk.adapter, "Yunhu"):
            yunhu_adapter = sdk.adapter.Yunhu
            def parse_sender_info(data: Dict[str, Any]) -> str:
                """解析发送者信息"""
                sender = data["event"]["sender"]
                return (
                    f"发送者: {sender['senderNickname']}({sender['senderId']}) "
                    f"类型: {sender['senderType']} 等级: {sender['senderUserLevel']}"
                )

            def parse_chat_info(data: Dict[str, Any]) -> str:
                """解析会话信息"""
                chat = data["event"]["chat"]
                return f"会话: {chat['chatType']}({chat['chatId']})"

            # 普通消息事件
            @yunhu_adapter.on("message")
            async def handle_normal_message(data: Dict[str, Any]):
                sdk.logger.info("=== 普通消息事件 ===")
                sdk.logger.info(parse_sender_info(data))
                sdk.logger.info(parse_chat_info(data))

                message  = data["event"]["message"]
                sender   = data["event"]["sender"]

                sdk.logger.info(
                    f"消息ID: {message['msgId']} 类型: {message['contentType']}\n"
                    f"内容: {message['content']['text']}"
                )

                await yunhu_adapter.send(
                    sender['senderType'],
                    sender['senderId'],
                    f"[ECHO] {message['content']['text']}"
                )

            @yunhu_adapter.on("command")
            async def handle_command_message(data: Dict[str, Any]):
                sdk.logger.info("=== 指令消息事件 ===")
                message = data["event"]["message"]
                sender  = data["event"]["sender"]
                sdk.logger.info(
                    f"指令ID: {message.get('commandId')} "
                    f"指令名称: {message.get('commandName')}\n"
                    f"内容: {message['content']['text']}"
                )

                await yunhu_adapter.send(
                    sender['senderType'],
                    sender['senderId'],
                    f"收到指令: {message.get('commandName')}, 内容: {message['content']['text']}"
                )

            @yunhu_adapter.on("follow")
            async def handle_follow_event(data: Dict[str, Any]):
                sdk.logger.info("=== 关注事件 ===")
                user = data["event"]["user"]
                sdk.logger.info(
                    f"新关注: {user['userNickname']}({user['userId']})"
                )
                await yunhu_adapter.send(
                    "user",
                    user["userId"],
                    "感谢关注！发送 '帮助' 获取使用指南"
                )

            @yunhu_adapter.on("unfollow")
            async def handle_unfollow_event(data: Dict[str, Any]):
                sdk.logger.info("=== 取消关注事件 ===")
                user = data["event"]["user"]
                sdk.logger.warning(
                    f"用户取关: {user['userNickname']}({user['userId']})"
                )

            @yunhu_adapter.on("group_join")
            async def handle_group_join(data: Dict[str, Any]):
                sdk.logger.info("=== 加入群事件 ===")
                event = data["event"]
                sdk.logger.info(
                    f"用户 {event['user']['userNickname']} "
                    f"加入群 {event['group']['groupId']}"
                )
                await yunhu_adapter.send(
                    "group",
                    event["group"]["groupId"],
                    f"欢迎 {event['user']['userNickname']} 加入本群！"
                )

            @yunhu_adapter.on("group_leave")
            async def handle_group_leave(data: Dict[str, Any]):
                sdk.logger.info("=== 退出群事件 ===")
                event = data["event"]
                sdk.logger.info(
                    f"用户 {event['user']['userNickname']} "
                    f"退出群 {event['group']['groupId']}"
                )


            # 系统启动后发送测试消息
            await yunhu_adapter.send(
                "user",
                "5197892",
                "SDK Is Running..."
            )

        # 保持程序运行
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await sdk.adapter.shutdown()

if __name__ == "__main__":
    asyncio.run(main())