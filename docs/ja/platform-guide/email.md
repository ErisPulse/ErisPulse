# メールプラットフォーム機能ドキュメント

EmailAdapter は SMTP/IMAP プロトコルベースのメールアダプターで、メールの送信・受信・処理をサポートします。

---

## ドキュメント情報

- 対応モジュールバージョン： 4.3.2
- メンテナー: ErisPulse
- 最終更新： 2026-11-10

## 基本情報

- プラットフォーム概要：標準 SMTP/IMAP プロトコルでメールを送受信する汎用アダプター
- アダプター名：EmailAdapter
- マルチアカウント対応：複数のメールアカウントの同時設定をサポート
- 接続方式：IMAP ロングポーリング受信 + SMTP 送信
- 認証方式：メールアドレス + パスワード/認証コード
- OneBot12 互換：OneBot12 形式メッセージの送信に対応

## 設定説明

### グローバル設定（EmailAdapter）

| 設定項目 | 型 | デフォルト値 | 説明 |
|--------|------|--------|------|
| `imap_server` | str | `imap.example.com` | デフォルトの IMAP サーバーアドレス |
| `imap_port` | int | `993` | デフォルトの IMAP ポート |
| `smtp_server` | str | `smtp.example.com` | デフォルトの SMTP サーバーアドレス |
| `smtp_port` | int | `465` | デフォルトの SMTP ポート |
| `ssl` | bool | `true` | デフォルトで SSL を有効にするかどうか |
| `timeout` | int | `30` | デフォルトの接続タイムアウト（秒） |
| `poll_interval` | int | `60` | IMAP ポーリング間隔（秒） |
| `max_retries` | int | `3` | 接続失敗時の最大リトライ回数 |

### アカウント設定（EmailAdapter.accounts）

各アカウントは 1 つの独立したメールボックスに対応します。アカウントレベルの設定はグローバル設定よりも優先されます。

```toml
[EmailAdapter.accounts.default]
email = "user@example.com"
password = "your-password-or-auth-code"
imap_server = "imap.example.com"    # 任意。空欄の場合はグローバルデフォルトを使用
imap_port = 993                      # 任意
smtp_server = "smtp.example.com"    # 任意
smtp_port = 465                      # 任意
ssl = true                           # 任意
timeout = 30                         # 任意
enabled = true

[EmailAdapter.accounts.backup]
email = "backup@example.com"
password = "another-password"
enabled = true
```

## v5 パラダイム更新（4.2.0）

- **Api DSL 最小セット**：get_self_info（メールアドレス）/get_status/get_version/get_supported_actions
- **spawn_background タスクの所属**：IMAP ポーリングタスクは runtime.spawn_background を使用するように変更
- **フレームワークのソフト依存**：実行時に ErisPulse>=2.7.1 を検出して通知、起動時にバージョンログを出力
- インポートパスを Core.Bases に更新。_load_accounts は維持（グローバルデフォルト値のマージは本アダプター固有のロジック）

## 標準化対応（4.3.2）

レスポンス構造とエラーコードは [API レスポンス仕様](../standards/api-response.md) に準拠しています。

### イベントとレスポンスフィールド

- **メッセージイベントにトップレベルの `message_id` を補完**：メールの `Message-ID` ヘッダーから取得
- **`Message-ID` のないメールイベントの id は uuid にフォールバック**：イベントの `id` と `message_id` が空になることがなくなり、id の重複によってイベントが下流の重複排除で破棄されるのを回避
- **`get_self_info` の生データはレスポンスのトップレベル `email_raw` に格納**、標準フィールドには `user_id`（メールアドレス）が含まれます

### HTML 送信メソッド

- `.Html(html: str)`：HTML 形式のメールを送信
- `.HTML(html: str)`：`.Html()` のエイリアス（標準 Send メソッドの命名規則と一貫性を維持）

### エラーコード仕様

| retcode | 意味 | 説明 |
|---------|------|------|
| 0 | 成功 | — |
| 33001 | ネットワークエラー | SMTP/IMAP 接続系の失敗（タイムアウト、接続拒否など） |
| 34100 | プラットフォーム失敗 | SMTP による拒否（受信者/送信者/データ/認証の拒否）。元のエラーは `email_raw` に保持されます |
| 10003 | パラメーターエラー | パラメーターの欠落または無効 |

### アカウントとマルチアカウント

- `Send` は `send_context` を読み取ります（イベントアカウントへのフォールバック）：イベントコンテキストから `Send` を呼び出す場合、デフォルトで送信元アカウントにフォールバックします
- マルチアカウントでの送信は `Send.Using("アカウント名")` で明示的に指定します

---


### 対応済みプラットフォーム機能

- **受信**：IMAP ポーリングによるメール受信（本文/HTML/添付ファイルをメッセージセグメントに解析）、未読の増分検出
- **送信**：SMTP によるメール送信（Subject/Text/Html/Cc/Bcc/ReplyTo/Attachment）、マルチアカウント対応
- **API**：アカウント情報と実行状態（最小セット）。メールの取り消しやグループなどの概念は適用外

---

## 対応するメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実装されています：

```python
from ErisPulse.Core import adapter
mail = adapter.get("email")

# シンプルなテキストメール
await mail.Send.To("private", "to@example.com").Subject("テスト").Text("本文")

# 添付ファイル付き HTML メール
await mail.Send.To("private", "to@example.com") \
    .Subject("HTMLメール") \
    .Cc(["cc1@example.com", "cc2@example.com"]) \
    .Attachment("report.pdf") \
    .Html("<h1>HTML本文</h1>")

# Raw_ob12 で標準 OB12 メッセージを送信
await mail.Send.To("private", "to@example.com").Raw_ob12([
    {"type": "text", "data": {"text": "メール本文"}},
    {"type": "file", "data": {"file": "/path/to/attachment.pdf"}},
])

# 送信アカウントを指定（マルチアカウント）
await mail.Send.Using("default").To("private", "to@example.com").Text("本文")
```

> 注意：チェーン構文を使用する場合、パラメーターメソッド（Subject / Cc / Attachment など）は、送信メソッド（Text / Html / Raw_ob12）の前に呼び出す必要があります。

### 基本送信メソッド

| メソッド | 説明 |
|------|------|
| `.Text(text: str)` | プレーンテキストのメールを送信 |
| `.Html(html: str)` | HTML 形式のメールを送信（`.HTML(html)` はエイリアス） |
| `.MergeForward(nodes, title)` | 統合転送メールを送信（本文は `<details>` の折りたたみ HTML カード、件名はデフォルトでタイトルを使用） |
| `.Raw_ob12(message, **kwargs)` | OneBot12 形式のメッセージを送信 |

### チェーン修飾メソッド（self を返し、組み合わせて使用可能）

| メソッド | 説明 |
|------|------|
| `.Subject(subject: str)` | メールの件名を設定 |
| `.Cc(emails: Union[str, List[str]])` | CC アドレスを設定 |
| `.Bcc(emails: Union[str, List[str]])` | BCC アドレスを設定 |
| `.ReplyTo(email: str)` | 返信先アドレスを設定 |
| `.Attachment(file, filename: str = None)` | 添付ファイルを追加 |

### OB12 メッセージセグメントの逆変換（Raw_ob12）

| OB12 メッセージセグメント | メール内容への変換 |
|------------|--------------|
| `text` | プレーンテキスト本文 |
| `image` | 画像の添付ファイル |
| `video` | 動画の添付ファイル |
| `file` | ファイルの添付 |
| `audio` | 音声の添付ファイル |
| `markdown` | HTML 本文に変換 |

## 固有のイベントタイプ

### 主な相違点

1. メールイベントはすべて `message` タイプであり、`detail_type` は固定で `private` です
2. `user_id` は送信者の**純粋なメールアドレス**、`user_nickname` は送信者の表示名です
3. `message` メッセージセグメントは標準 OB12 形式（text セグメント + file セグメント）です
4. メールの件名は `email_subject` 拡張フィールドから取得できます
5. 完全な生データは `email_raw` フィールドに保持されます

### 新着メールイベント（email_new）

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
  "message_id": "<message-id@example.com>",
  "message": [
    {
      "type": "text",
      "data": {
        "text": "メール本文の内容"
      }
    }
  ],
  "alt_message": "メール件名",
  "user_id": "sender@example.com",
  "user_nickname": "Saber"
}
```

### 添付ファイル付きのメール

```json
{
  "message": [
    {
      "type": "text",
      "data": {
        "text": "添付ファイルをご確認ください"
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

### 返信メールイベント（email_reply）

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
| `email_raw` | dict | 完全な元メールデータ（subject/from/to/date/cc/bcc/text_content/html_content/attachments など） |
| `email_raw_type` | str | 元のイベントタイプ：`email_new`（新着メール）または `email_reply`（返信メール） |
| `email_subject` | str | メール件名（簡易アクセス用） |
| `email_from` | str | 送信者の純粋なメールアドレス（簡易アクセス用） |
| `attachments` | list | 添付ファイルデータのリスト（バイナリの `data` フィールドを含む、後方互換用） |

## 標準イベント例

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
  "message_id": "<abc123@example.com>",
  "message": [
    {
      "type": "text",
      "data": {
        "text": "添付ファイルをご確認ください"
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
    "text_content": "添付ファイルをご確認ください",
    "html_content": "<p>添付ファイルをご確認ください</p>",
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

## 送信メソッドの戻り値

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
    "message": "Email sent successfully"
  }
}
```

## イベント処理の例

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_email(event):
    if event.get("platform") != "email":
        return
    # 送信者の純粋なメールアドレス
    sender = event["user_id"]              # sender@example.com
    
    # 送信者の表示名
    nickname = event.get("user_nickname")  # Sender
    
    # メール件名
    subject = event.get("email_subject")   # 会議のお知らせ
    
    # プレーンテキスト本文（最初の text セグメント）
    text = event.get_text()
    
    # 完全な生データ
    raw = event.get("email_raw", {})
    html = raw.get("html_content", "")
    
    # 添付ファイルの処理
    for seg in event.get("message", []):
        if seg["type"] == "file":
            filename = seg["data"]["file_name"]
            size = seg["data"]["size"]
    
    # メールへの返信
    await event.reply(f"受信しました：{subject}")
```