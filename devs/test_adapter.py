from ErisPulse import sdk
import asyncio
from pathlib import Path

# 测试文件路径
CURRENT_DIR = Path(__file__).parent / "test_files"
TEST_IMAGE_PATH = CURRENT_DIR / "test.jpg"
TEST_VIDEO_PATH = CURRENT_DIR / "test.mp4"
TEST_DOCUMENT_PATH = CURRENT_DIR / "test.docx"

# 各平台测试配置
TELEGRAM_USER_ID = "6117725680"
TELEGRAM_GROUP_ID = "-1001234567890"  # None 表示不发群聊

QQ_USER_ID = "123456789"
QQ_GROUP_ID = "782199153"  # None 表示不发群聊

YUNHU_USER_ID = "5197892"
YUNHU_GROUP_ID = "987654321"  # None 表示不发群聊

async def telegram_test(startup: bool):
    if not hasattr(sdk.adapter, "telegram"):
        return
    telegram = sdk.adapter.telegram
    if startup:
        await telegram.Send.To("user", TELEGRAM_USER_ID).Text("【启动通知】SDK已启动 - Telegram文本消息")
        if TEST_IMAGE_PATH.exists():
            with open(TEST_IMAGE_PATH, "rb") as f:
                await telegram.Send.To("user", TELEGRAM_USER_ID).Image(f.read())
        if TEST_VIDEO_PATH.exists():
            with open(TEST_VIDEO_PATH, "rb") as f:
                await telegram.Send.To("user", TELEGRAM_USER_ID).Video(f.read())
        if TEST_DOCUMENT_PATH.exists():
            with open(TEST_DOCUMENT_PATH, "rb") as f:
                await telegram.Send.To("user", TELEGRAM_USER_ID).Document(f.read())
        if TELEGRAM_GROUP_ID:
            await telegram.Send.To("group", TELEGRAM_GROUP_ID).Text("【启动通知】SDK已启动 - Telegram群聊文本消息")
            if TEST_IMAGE_PATH.exists():
                with open(TEST_IMAGE_PATH, "rb") as f:
                    await telegram.Send.To("group", TELEGRAM_GROUP_ID).Image(f.read())
            if TEST_VIDEO_PATH.exists():
                with open(TEST_VIDEO_PATH, "rb") as f:
                    await telegram.Send.To("group", TELEGRAM_GROUP_ID).Video(f.read())
            if TEST_DOCUMENT_PATH.exists():
                with open(TEST_DOCUMENT_PATH, "rb") as f:
                    await telegram.Send.To("group", TELEGRAM_GROUP_ID).Document(f.read())
    else:
        await telegram.Send.To("user", TELEGRAM_USER_ID).Text("【关闭通知】SDK已关闭")
        if TELEGRAM_GROUP_ID:
            await telegram.Send.To("group", TELEGRAM_GROUP_ID).Text("【关闭通知】SDK已关闭")

async def qq_test(startup: bool):
    if not hasattr(sdk.adapter, "QQ"):
        return
    qq = sdk.adapter.QQ
    if startup:
        await asyncio.sleep(5)
        await qq.Send.To("user", QQ_USER_ID).Text("【启动通知】SDK已启动 - QQ文本消息")
        if TEST_IMAGE_PATH.exists():
            with open(TEST_IMAGE_PATH, "rb") as f:
                await qq.Send.To("user", QQ_USER_ID).Image(f.read())
        if TEST_VIDEO_PATH.exists():
            with open(TEST_VIDEO_PATH, "rb") as f:
                await qq.Send.To("user", QQ_USER_ID).Video(f.read())
        if TEST_DOCUMENT_PATH.exists():
            with open(TEST_DOCUMENT_PATH, "rb") as f:
                await qq.Send.To("user", QQ_USER_ID).Document(f.read())
        if QQ_GROUP_ID:
            await qq.Send.To("group", QQ_GROUP_ID).Text("【启动通知】SDK已启动 - QQ群聊文本消息")
            if TEST_IMAGE_PATH.exists():
                with open(TEST_IMAGE_PATH, "rb") as f:
                    await qq.Send.To("group", QQ_GROUP_ID).Image(f.read())
            if TEST_VIDEO_PATH.exists():
                with open(TEST_VIDEO_PATH, "rb") as f:
                    await qq.Send.To("group", QQ_GROUP_ID).Video(f.read())
            if TEST_DOCUMENT_PATH.exists():
                with open(TEST_DOCUMENT_PATH, "rb") as f:
                    await qq.Send.To("group", QQ_GROUP_ID).Document(f.read())
    else:
        await qq.Send.To("user", QQ_USER_ID).Text("【关闭通知】SDK已关闭")
        if QQ_GROUP_ID:
            await qq.Send.To("group", QQ_GROUP_ID).Text("【关闭通知】SDK已关闭")

async def yunhu_test(startup: bool):
    if not hasattr(sdk.adapter, "Yunhu"):
        return
    yunhu = sdk.adapter.Yunhu
    if startup:
        await yunhu.Send.To("user", YUNHU_USER_ID).Text("【启动通知】SDK已启动 - 云湖文本消息")
        if TEST_IMAGE_PATH.exists():
            with open(TEST_IMAGE_PATH, "rb") as f:
                await yunhu.Send.To("user", YUNHU_USER_ID).Image(f.read())
        if TEST_VIDEO_PATH.exists():
            with open(TEST_VIDEO_PATH, "rb") as f:
                await yunhu.Send.To("user", YUNHU_USER_ID).Video(f.read())
        if YUNHU_GROUP_ID:
            await yunhu.Send.To("group", YUNHU_GROUP_ID).Text("【启动通知】SDK已启动 - 云湖群聊文本消息")
            if TEST_IMAGE_PATH.exists():
                with open(TEST_IMAGE_PATH, "rb") as f:
                    await yunhu.Send.To("group", YUNHU_GROUP_ID).Image(f.read())
            if TEST_VIDEO_PATH.exists():
                with open(TEST_VIDEO_PATH, "rb") as f:
                    await yunhu.Send.To("group", YUNHU_GROUP_ID).Video(f.read())
    else:
        await yunhu.Send.To("user", YUNHU_USER_ID).Text("【关闭通知】SDK已关闭")
        if YUNHU_GROUP_ID:
            await yunhu.Send.To("group", YUNHU_GROUP_ID).Text("【关闭通知】SDK已关闭")

async def main():
    sdk.init()
    try:
        sdk.logger.set_output_file("test.log")
        await sdk.adapter.startup()
        await asyncio.sleep(1)
        await telegram_test(True)
        await qq_test(True)
        await yunhu_test(True)
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        sdk.logger.info("收到关闭信号，准备发送关闭通知...")
        await telegram_test(False)
        await qq_test(False)
        await yunhu_test(False)
    except Exception as e:
        sdk.logger.error(f"测试过程中发生错误: {str(e)}")
        raise  # 重新抛出异常以便调试

if __name__ == "__main__":
    asyncio.run(main())