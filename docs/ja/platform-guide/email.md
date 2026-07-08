# メールプラットフォームの機能ドキュメント

EmailAdapter は SMTP/IMAP プロトコルに基づいたメールアダプターで、メールの送信、受信、処理をサポートしています。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.1.0
- メンテナー: ErisPulse

## 基本情報

- プラットフォームの概要：標準の SMTP/IMAP プロトコルを使用してメールを送受信する汎用アダプター
- アダプター名：EmailAdapter
- 複数アカウントのサポート：複数のメールアカウントを同時に設定可能
- 接続方式：IMAP 長時間ポーリングによる受信 + SMTP による送信
- 認証方式：メールアドレス + パスワード/認証コード
- OneBot12 の互換性：OneBot12 形式のメッセージ送信をサポート

## 設定説明

### グローバル設定 (EmailAdapter)

| 設定項目 | 型 | デフォルト値 | 説明 |
|--------|------|--------|------|
| `imap_server` | str | `imap.example.com` | デフォルトの IMAP サーバーのアドレス |
| `imap_port` | int | `993` | デフォルトの IMAP ポート番号 |
| `smtp_server` | str | `smtp.example.com` | デフォルトの SMTP サーバーのアドレス |
| `smtp_port` | int | `465` | デフォルトの SMTP ポート番号 |
| `ssl` | bool | `true` | SSL をデフォルトで有効にするか |
| `timeout` | int | `30` | デフォルトの接続タイムアウト（秒） |
| `poll_interval` | int | `60` | IMAP ポーリング間隔（秒） |
| `max_retries` | int | `3` | 接続失敗時の最大リトライ回数 |

### アカウント設定 (EmailAdapter.accounts)

各アカウントは独立したメールアドレスに対応します。アカウントレベルの設定はグローバル設定より優先されます。

```toml
[EmailAdapter.accounts.default]
email = "user@example.com"
password = "your-password-or-auth-code"
imap_server = "imap.example.com"    # オプション、空欄の場合はグローバルのデフォルトを使用
imap_port = 993                      # オプション
smtp_server = "smtp.example.com"    # オプション
smtp_port = 465                      # オプション
ssl = true                           # オプション
timeout = 30                         # オプション
enabled = true

[EmailAdapter.accounts.backup]
email = "backup@example.com"
password = "another-password"
enabled = true
```

## 送信可能なメッセージの種類

すべての送信メソッドはメソッドチェーン構文で実装されています：

```python
from ErisPulse.Core import adapter
mail = adapter.get("email")

# 簡単なテキストメール
await mail.Send.To("private", "to@example.com").Subject("テスト").Text("内容")

# 附件付きの HTML メール
await mail.Send.To("private", "to@example.com") \
    .Subject("HTMLメール") \
    .Cc(["cc1@example.com", "cc2@example.com"]) \
    .Attachment("report.pdf") \
    .Html("<h1>HTML内容</h1>")

# Raw_ob12 を使用して標準の OB12 メッセージを送信
await mail.Send.To("private", "to@example.com").Raw_ob12([
    {"type": "text", "data": {"text": "メール本文"}},
    {"type": "file", "data": {"file": "/path/to/attachment.pdf"}},
])

# 送信アカウントを指定（複数アカウント）
await mail.Send.Using("default").To("private", "to@example.com").Text("内容")
```

> メソッドチェーン構文を使用する際は、パラメータを設定するメソッド（Subject / Cc / Attachment など）は送信メソッド（Text / Html / Raw_ob12）の前に呼び出す必要があります。

### 基本的な送信メソッド

| メソッド | 説明 |
|------|------|
| `.Text(text: str)` | 純粋なテキストメールを送信 |
| `.Html(html: str)` | HTML 形式のメールを送信 |
| `.Raw_ob12(message, **kwargs)` | OneBot12 形式のメッセージを送信 |

### メソッドチェーンの修飾メソッド（self を返すため、組み合わせて使用可能）

| メソッド | 説明 |
|------|------|
| `.Subject(subject: str)` | メールの件名を設定 |
| `.Cc(emails: Union[str, List[str]])` | 送信先の CC アドレスを設定 |
| `.Bcc(emails: Union[str, List[str]])` | 送信先の BCC アドレスを設定 |
| `.ReplyTo(email: str)` | 回信先アドレスを設定 |
| `.Attachment(file, filename: str = None)` | 附件を追加 |

### OB12 メッセージセグメントの逆変換 (Raw_ob12)

| OB12 メッセージセグメント | メールの内容に変換 |
|------------|--------------|
| `text` | 純粋な本文 |
| `image` | 画像の附件 |
| `video` | 動画の附件 |
| `file` | ファイルの附件 |
| `audio` | 音声の附件 |
| `markdown` | HTML 本文に変換 |

## 特有のイベントタイプ

### 核心的な違い

1. メールイベントはすべて `message` タイプで、`detail_type` は固定で `private`
2. `user_id` は送信者の**純粋なメールアドレス**、`user_nickname` は送信者の表示名
3. `message` メッセージセグメントは標準の OB12 形式（text セグメント + file セグメント）
4. メールの件名は `email_subject` 拡張フィールドから取得
5. 完全な元データは `email_raw` フィールドに保存

### 新しいメールイベント (email_new)

```json
{
  "id": "<message-id@example.com>",
  "time": 1751990446,
  "type": "message",
  "detail_type": "private",
  "platform": "email",
  "self": {
    "platform": "email",
    "user_id": "bot@example.com"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "メール本文"
      }
    }
  ],
  "alt_message": "メールの件名",
  "user_id": "sender@example.com",
  "user_nickname": "Saber"
}
```

### 附件付きのメール

```json
{
  "message": [
    {
      "type": "text",
      "data": {
        "text": "添付ファイルをご覧ください"
      }
    },
    {
      "type": "file",
      "data": {
        "file_id": "document.pdf",
        "file_name": "document.pdf",
        "size": 102400
      }
    }
  ]
}
```

### 回答メールイベント (email_reply)

メールに `References` または `In-Reply-To` ヘッダーが含まれている場合、`email_raw_type` は `email_reply` になります：

```json
{
  "email_raw_type": "email_reply",
  "email_raw": {
    "references": "<original-msg-id@example.com>",
    "in_reply_to": "<original-msg-id@example.com>"
  }
}
```

## 拡張フィールドの説明

| フィールド | 型 | 説明 |
|------|------|------|
| `email_raw` | dict | 完全な元のメールデータ（subject/from/to/date/cc/bcc/text_content/html_content/attachments など） |
| `email_raw_type` | str | 元のイベントタイプ：`email_new`（新メール）または `email_reply`（回答メール） |
| `email_subject` | str | メールの件名（アクセスしやすいように） |
| `email_from` | str | 送信者の純粋なメールアドレス（アクセスしやすいように） |
| `attachments` | list | 附件データのリスト（後方互換性のために binary `data` フィールドを含む） |

## 標準的なイベントの例

### 完全なメールイベント

```json
{
  "id": "<abc123@example.com>",
  "time": 1751990446,
  "type": "message",
  "detail_type": "private",
  "platform": "email",
  "self": {
    "platform": "email",
    "user_id": "bot@example.com"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "添付ファイルをご覧ください"
      }
    },
    {
      "type": "file",
      "data": {
        "file_id": "document.pdf",
        "file_name": "document.pdf",
        "size": 102400
      }
    }
  ],
  "alt_message": "会議のお知らせ",
  "user_id": "sender@example.com",
  "user_nickname": "Sender",
  "email_subject": "会議のお知らせ",
  "email_from": "sender@example.com",
  "email_raw": {
    "subject": "会議のお知らせ",
    "from": "\"Sender\" <sender@example.com>",
    "to": "<bot@example.com>",
    "date": "Wed, 9 Jul 2026 02:00:46 +0800",
    "message_id": "<abc123@example.com>",
    "references": "",
    "in_reply_to": "",
    "cc": "",
    "bcc": "",
    "text_content": "添付ファイルをご覧ください",
    "html_content": "<p>添付ファイルをご覧ください</p>",
    "attachments": ["document.pdf"]
  },
  "email_raw_type": "email_new",
  "attachments": [
    {
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "size": 102400,
      "data": "..."
    }
  ]
}
```

## 送信メソッドの返り値

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "<sent-msg-id@example.com>",
    "time": 1751990446
  },
  "message_id": "<sent-msg-id@example.com>",
  "message": "",
  "email_raw": {
    "success": true,
    "message": "メールの送信に成功しました"
  }
}
```

## イベント処理の例

```python
from ErisPulse import sdk

@sdk.on_message(platform="email")
async def handle_email(event):
    # 送信者の純粋なメールアドレス
    sender = event["user_id"]              # sender@example.com
    
    # 送信者の表示名
    nickname = event.get("user_nickname")  # Sender
    
    # メールの件名
    subject = event.get("email_subject")   # 会議のお知らせ
    
    # 純粋なテキスト本文（最初の text セグメント）
    text = event.get_text()
    
    # 完全な元のデータ
    raw = event.get("email_raw", {})
    html = raw.get("html_content", "")
    
    # 附件の処理
    for seg in event.get("message", []):
        if seg["type"] == "file":
            filename = seg["data"]["file_name"]
            size = seg["data"]["size"]
    
    # 回答メール
    await event.reply(f"受信しました：{subject}")