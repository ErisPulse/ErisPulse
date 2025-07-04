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
YUNHU_GROUP_ID = "635409929"  # None 表示不发群聊

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
        buttons = [
            [{"text": "复制", "actionType": 2, "value": "xxxx"}],
            [{"text": "点击跳转", "actionType": 1, "url": "http://www.baidu.com"}]
        ]

        # 文本消息 + 按钮
        response_text = await yunhu.Send.To("user", YUNHU_USER_ID).Text("【启动通知】SDK已启动 - 带按钮文本消息", buttons=buttons)
        print("文本消息发送返回值:", response_text)

        # HTML 消息
        response_html = await yunhu.Send.To("user", YUNHU_USER_ID).Html("<b>这是一条HTML消息</b>")
        print("HTML消息发送返回值:", response_html)

        # Markdown 消息
        response_md = await yunhu.Send.To("user", YUNHU_USER_ID).Markdown("# 这是一条Markdown消息")
        print("Markdown消息发送返回值:", response_md)

        # 图片消息
        if TEST_IMAGE_PATH.exists():
            with open(TEST_IMAGE_PATH, "rb") as f:
                image_data = f.read()
                response_image = await yunhu.Send.To("user", YUNHU_USER_ID).Image(image_data)
                print("图片消息发送返回值:", response_image)

        # 视频消息
        if TEST_VIDEO_PATH.exists():
            with open(TEST_VIDEO_PATH, "rb") as f:
                video_data = f.read()
                response_video = await yunhu.Send.To("user", YUNHU_USER_ID).Video(video_data)
                print("视频消息发送返回值:", response_video)

        # 文件消息
        if TEST_DOCUMENT_PATH.exists():
            with open(TEST_DOCUMENT_PATH, "rb") as f:
                file_data = f.read()
                response_file = await yunhu.Send.To("user", YUNHU_USER_ID).File(file_data)
                print("文件消息发送返回值:", response_file)

        # 批量发送测试
        test_user_ids = [YUNHU_USER_ID, "5197893", "5197894"]  # 模拟多个用户ID
        
        # 1. 文本消息批量发送
        response_batch_text = await yunhu.Send.To("user", test_user_ids).Text("批量文本测试消息")
        print("批量文本消息发送返回值:", response_batch_text)
        
        # 2. HTML消息批量发送
        response_batch_html = await yunhu.Send.To("user", test_user_ids).Html("<b>批量HTML测试消息</b>")
        print("批量HTML消息发送返回值:", response_batch_html)
        
        # 3. Markdown消息批量发送
        response_batch_md = await yunhu.Send.To("user", test_user_ids).Markdown("# 批量Markdown测试消息")
        print("批量Markdown消息发送返回值:", response_batch_md)
        
        # 4. 图片批量发送
        if TEST_IMAGE_PATH.exists():
            with open(TEST_IMAGE_PATH, "rb") as f:
                image_data = f.read()
                response_batch_image = await yunhu.Send.To("user", test_user_ids).Image(image_data)
                print("批量图片消息发送返回值:", response_batch_image)
        # 5. 文件批量发送
        if TEST_DOCUMENT_PATH.exists():
            with open(TEST_DOCUMENT_PATH, "rb") as f:
                file_data = f.read()
                response_batch_file = await yunhu.Send.To("user", test_user_ids).File(file_data)
                print("批量文件消息发送返回值:", response_batch_file)
                
        # 6. 保留原Batch方法测试(已弃用)
        response_batch_old = await yunhu.Send.To("user", YUNHU_USER_ID).Batch([YUNHU_USER_ID], "旧批量方法测试消息")
        print("旧批量方法发送返回值:", response_batch_old)

        # 编辑消息（需要 msg_id）
        if 'response_text' in locals() and 'msgId' in response_text.get('data', {}).get('messageInfo', {}):
            msg_id = response_text['data']['messageInfo']['msgId']
            response_edit = await yunhu.Send.To("user", YUNHU_USER_ID).Edit(msg_id, "这是编辑后的消息")
            print("编辑消息发送返回值:", response_edit)

        # 撤回消息（需要 msg_id）
        if 'msg_id' in locals():
            response_recall = await yunhu.Send.To("user", YUNHU_USER_ID).Recall(msg_id)
            print("撤回消息发送返回值:", response_recall)
        
        # 流式消息
        async def stream_generator():
            for i in range(3):
                yield f"流式片段{i}".encode('utf-8')
                await asyncio.sleep(1)

        response_stream = await yunhu.Send.To("user", YUNHU_USER_ID).Stream("text", stream_generator())
        print("流式消息发送返回值:", response_stream)

        # 群聊消息
        if YUNHU_GROUP_ID:
            response_group_text = await yunhu.Send.To("group", YUNHU_GROUP_ID).Text("【群聊通知】SDK已启动")
            print("群聊文本消息发送返回值:", response_group_text)

            if TEST_IMAGE_PATH.exists():
                with open(TEST_IMAGE_PATH, "rb") as f:
                    image_data = f.read()
                    response_group_image = await yunhu.Send.To("group", YUNHU_GROUP_ID).Image(image_data)
                    print("群聊图片消息发送返回值:", response_group_image)

            if TEST_VIDEO_PATH.exists() is None:
                with open(TEST_VIDEO_PATH, "rb") as f:
                    video_data = f.read()
                    response_group_video = await yunhu.Send.To("group", YUNHU_GROUP_ID).Video(video_data)
                    print("群聊视频消息发送返回值:", response_group_video)

    else:
        # 关闭时发送关闭通知
        response_shutdown = await yunhu.Send.To("user", YUNHU_USER_ID).Text("【关闭通知】SDK已关闭")
        print("关闭通知消息发送返回值:", response_shutdown)

        if YUNHU_GROUP_ID:
            response_group_shutdown = await yunhu.Send.To("group", YUNHU_GROUP_ID).Text("【关闭通知】SDK已关闭")
            print("群聊关闭通知消息发送返回值:", response_group_shutdown)
async def main():
    sdk.init()
    try:
        sdk.logger.set_output_file("test.log")
        await sdk.adapter.startup()
        await asyncio.sleep(1)
        # await telegram_test(True)
        # await qq_test(True)
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