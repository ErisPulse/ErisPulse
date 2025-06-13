import asyncio
from ErisPulse import sdk


async def test_mail_adapter():
    try:
        sdk.init()
        await sdk.adapter.startup()

        # 监听新邮件事件
        @sdk.adapter.mail.on("mail_received")
        async def on_message(event):
            sdk.logger.info(f"收到邮件：{event}")

        recipient = "wsu2059@qq.com"
        subject = "来自 ErisPulse 的测试邮件"
        body = "这是一封通过 MailAdapter 发送的测试邮件。"

        sdk.logger.info(f"正在尝试发送邮件至 {recipient}")
        task = sdk.adapter.mail.Send.To("email", recipient).Text(body, subject=subject)
        result = await task

        if result is None:
            sdk.logger.info("邮件发送成功！")
        else:
            sdk.logger.warning("邮件发送过程中出现警告或错误。")

        await asyncio.Event().wait()
    except Exception as e:
        sdk.logger.error(f"测试过程中发生错误: {e}")
        sdk.raiserr.CaughtExternalError(f"测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_mail_adapter())
    print("测试通过")