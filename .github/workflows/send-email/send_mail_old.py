import requests
import os
import json

recipients = json.loads(os.getenv("RECIPIENTS_JSON"))
resend_api_key = os.getenv("RESEND_API_KEY")
feishu_smtp_password = os.getenv("FEISHU_SMTP_PASSWORD")
subject = os.getenv("SUBJECT")
content = os.getenv("CONTENT")
print(f"📬 收件人列表: {recipients}")
response = requests.post(
    "https://api.resend.com/emails",
    headers={
        "Authorization": f"Bearer {resend_api_key}",
        "Content-Type": "application/json",
    },
    json={
        "from": "ErisPulse <noreply@anran.xyz>",
        "to": recipients,
        "subject": subject,
        "html": content,
    },
)

if response.status_code == 200:
    print("💌 魔法信件已成功寄出！")
else:
    print(f"❌ 发送失败: {response.text}")
    exit(1)
