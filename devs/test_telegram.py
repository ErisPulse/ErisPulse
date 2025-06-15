import asyncio
import os
from ErisPulse import sdk
import aiohttp
from pathlib import Path

# 配置文件路径
CURRENT_DIR = Path(__file__).parent / "test_files"
TEST_IMAGE_PATH = CURRENT_DIR / "test.jpg"
TEST_VIDEO_PATH = CURRENT_DIR / "test.mp4"
TEST_DOCUMENT_PATH = CURRENT_DIR / "test.docx"

# 你的 Telegram 用户ID
MY_USER_ID = "6117725680"

async def test_telegram_adapter():
    try:
        # 初始化 SDK
        sdk.init()
        await sdk.adapter.startup()
        # 确保 Telegram 适配器已注册
        if not hasattr(sdk.adapter, "telegram"):
            sdk.logger.error("Telegram 适配器未注册，请检查模块加载状态")
            return

        telegram = sdk.adapter.telegram

        # 示例：发送文本消息给指定用户
        text_result = await telegram.send("user", MY_USER_ID, "Hello from ErisPulse SDK - Text Message!")
        sdk.logger.info(f"文本消息发送结果：{text_result}")

        # # 示例：发送图片消息
        # if TEST_IMAGE_PATH.exists():
        #     with open(TEST_IMAGE_PATH, "rb") as f:
        #         image_data = f.read()
        #     img_result = await telegram.Send.To("user", MY_USER_ID).Image(image_data)
        #     sdk.logger.info(f"图片发送结果：{img_result}")
        # else:
        #     sdk.logger.warning("测试图片不存在，跳过图片发送")

        # # 示例：发送视频消息
        # if TEST_VIDEO_PATH.exists():
        #     with open(TEST_VIDEO_PATH, "rb") as f:
        #         video_data = f.read()
        #     video_result = await telegram.Send.To("user", MY_USER_ID).Video(video_data)
        #     sdk.logger.info(f"视频发送结果：{video_result}")
        # else:
        #     sdk.logger.warning("测试视频不存在，跳过视频发送")

        # # 示例：发送文档消息
        # if TEST_DOCUMENT_PATH.exists():
        #     with open(TEST_DOCUMENT_PATH, "rb") as f:
        #         document_data = f.read()
        #     doc_result = await telegram.Send.To("user", MY_USER_ID).Document(document_data)
        #     sdk.logger.info(f"文档发送结果：{doc_result}")
        # else:
        #     sdk.logger.warning("测试文档不存在，跳过文档发送")

        # # 示例：编辑消息
        # message_id = img_result.get("result", {}).get("message_id")
        # if message_id:
        #     edit_result = await telegram.Send.To("user", MY_USER_ID).Edit(message_id, "This is an edited message.")
        #     sdk.logger.info(f"消息编辑结果：{edit_result}")

        # # 示例：删除消息
        # if message_id:
        #     delete_result = await telegram.Send.To("user", MY_USER_ID).DeleteMessage(message_id)
        #     sdk.logger.info(f"消息删除结果：{delete_result}")

        # # 示例：获取聊天信息
        # chat_info = await telegram.Send.To("user", MY_USER_ID).GetChat()
        # sdk.logger.info(f"聊天信息：{chat_info}")

        @sdk.adapter.telegram.on("message")
        async def on_message(event):
            sdk.logger.info(f"收到消息：{event}")

        await asyncio.Event().wait()
    except Exception as e:
        sdk.logger.error(f"测试过程中发生错误: {e}")
        sdk.raiserr.CaughtExternalError(f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_telegram_adapter())
    print("测试通过")