# メールプラットフォーム特性ドキュメント

MailAdapterはSMTP/IMAPプロトコルに基づいたメールアダプタであり、メールの送信、受信、および処理をサポートしています。

---

## ドキュメント情報

*   対応モジュールバージョン: 1.0.0
*   メンテナ: ErisPulse


## サポートされているメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実装されています。例：
```python
from ErisPulse.Core import adapter
mail = adapter.get("email")

# シンプルなテキストメール
await mail.Send.Using("from@example.com").To("to@example.com").Subject("テスト").Text("内容")

# 添付ファイル付きのHTMLメール
await mail.Send.Using("from@example.com")
    .To("to@example.com")
    .Subject("HTMLメール")
    .Cc(["cc1@example.com", "cc2@example.com"])
    .Attachment("report.pdf")
    .Html("<h1>HTMLコンテンツ</h1>")

# 注意：チェーン構文を使用する場合、パラメータメソッド（Text、Html）は送信メソッドの前に設定する必要があります。
```

サポートされている送信タイプは以下の通りです：
*   `.Text(text: str)`：プレーンテキストメールを送信
*   `.Html(html: str)`：HTML形式のメールを送信
*   `.Attachment(file: str, filename: str = None)`：添付ファイルを追加
*   `.Cc(emails: Union[str, List[str]])`：CC（カーボンコピー）を設定
*   `.Bcc(emails: Union[str, List[str]])`：BCC（ブラインドカーボンコピー）を設定
*   `.ReplyTo(email: str)`：返信先アドレスを設定

### 固有パラメータの説明

| パラメータ       | 型               | 説明                          |
|----------------|-------------------|------------------------------|
| Subject        | str               | メール件名                      |
| From           | str               | 送信者アドレス（Usingで設定）    |
| To             | str               | 宛先アドレス                    |
| Cc             | str または List[str] | CCアドレスのリスト              |
| Bcc            | str または List[str] | BCCアドレスのリスト             |
| Attachment     | str または Path    | 添付ファイルのパス              |

## 固有のイベントタイプ

メール受信イベントの形式：
```python
{
  "type": "message",
  "detail_type": "private",  # メールはデフォルトでプライベートチャット
  "platform": "email",
  "self": {"platform": "email", "user_id": account_id},
  "message": [
    {
      "type": "text",
      "data": {
        "text": f"Subject: {subject}\nFrom: {from_}\n\n{text_content}"
      }
    }
  ],
  "email_raw": {
    "subject": subject,
    "from": from_,
    "to": to,
    "date": date,
    "text_content": text_content,
    "html_content": html_content,
    "attachments": [att["filename"] for att in attachments]
  },
  "attachments": [  # 添付データのリスト
    {
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "size": 1024,
      "data": b"..."  # 添付ファイルのバイナリデータ
    }
  ]
}
```

## 拡張フィールドの説明

*   `email_raw`: 原始メールデータを含む
*   `attachments`: 添付データのリスト

## OneBot12プロトコル変換の説明

メールイベントをOneBot12プロトコルに変換する際の主な相違点：

### 主な相違点

1.  固有のフィールド：
    *   `email_raw`: 原始メールデータを含む
    *   `attachments`: 添付データのリスト

2.  特別な処理：
    *   メールの件名と送信者情報はメッセージテキスト内に含まれます
    *   添付データはバイナリ形式で提供されます
    *   HTMLコンテンツはemail_rawフィールド内に保持されます

### 例

```python
{
  "type": "message",
  "platform": "email",
  "message": [
    {
      "type": "text",
      "data": {
        "text": "Subject: 会議通知\nFrom: sender@example.com\n\n添付ファイルをご確認ください"
      }
    }
  ],
  "email_raw": {
    "subject": "会議通知",
    "from": "sender@example.com",
    "to": "receiver@example.com",
    "html_content": "<p>添付ファイルをご確認ください</p>",
    "attachments": ["document.pdf"]
  },
  "attachments": [
    {
      "filename": "document.pdf",
      "data": b"...",  # 添付ファイルのバイナリデータ
      "size": 1024
    }
  ]
}