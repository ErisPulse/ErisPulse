import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr, formatdate

# 邮箱配置信息
EMAIL_HOST = "smtp.feishu.cn"  # SMTP服务器地址
EMAIL_PORT_SSL = 465  # SSL加密端口
USERNAME = "noreply@ns1.loc.cc"  # 邮箱地址
PASSWORD = os.getenv("FEISHU_SMTP_PASSWORD")  # IMAP/SMTP密码


def send_email(
    subject, content, receivers, content_type="html", sender_name="ErisPulse通知"
):
    """
    发送邮件到多个收件人，支持HTML格式

    参数:
    :param subject: 邮件主题
    :param content: 邮件内容(HTML或纯文本)
    :param receivers: 收件人列表，如 ["user1@example.com", "user2@example.com"]
    :param content_type: 邮件类型，"html" 或 "plain"
    :param sender_name: 发件人显示名称
    """
    # 创建邮件对象
    msg = MIMEMultipart()
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((str(Header(sender_name, "utf-8")), USERNAME))
    msg["To"] = ", ".join(receivers)  # 多个收件人用逗号分隔
    msg["Date"] = formatdate(localtime=True)

    # 添加邮件正文
    if content_type == "html":
        body = MIMEText(content, "html", "utf-8")
    else:
        body = MIMEText(content, "plain", "utf-8")
    msg.attach(body)

    try:
        # 创建SSL加密连接
        with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT_SSL) as server:
            server.login(USERNAME, PASSWORD)
            server.sendmail(USERNAME, receivers, msg.as_string())
            print(f"邮件成功发送给 {len(receivers)} 位收件人")
            return True
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")
        return False


if __name__ == "__main__":
    receivers = json.loads(os.getenv("RECIPIENTS_JSON"))
    print(f"收件人列表: {receivers}")

    send_email(
        subject=os.getenv("SUBJECT"),
        content=os.getenv("CONTENT"),
        receivers=receivers,
        content_type="html",
    )
