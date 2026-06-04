# アダプター標準化変換仕様

## 1. コア原則
1. 厳密な互換性：すべての標準フィールドはOneBot12仕様に完全に従う必要があります
2. 明確な拡張：プラットフォーム固有の機能には {platform}_ プレフィックスを追加する必要があります（例：yunhu_form）
3. データの完全性：元のイベントデータは {platform}_raw フィールドに保持し、元のイベントタイプは {platform}_raw_type フィールドに保持する必要があります
4. 時間の統一：すべてのタイムスタンプは10桁のUnixタイムスタンプ（秒単位）に変換する必要があります
5. プラットフォームの統一：platform項目の命名は、ErisPulseで登録した名前/エイリアスと一致する必要があります

## 2. 標準フィールド要件

### 2.1 必須フィールド
| フィールド | タイプ | 説明 |
|------|------|------|
| id | string | イベント固有識別子 |
| time | integer | Unixタイムスタンプ（秒単位） |
| type | string | イベントタイプ |
| detail_type | string | イベント詳細タイプ（詳細は[セッションタイプ標準](session-types.md)を参照） |
| platform | string | プラットフォーム名 |
| self | object | ボット自身の情報 |
| self.platform | string | プラットフォーム名 |
| self.user_id | string | ボットのユーザーID |

**detail_type 仕様**：
- ErisPulse標準のセッションタイプを使用する必要があります（詳細は[セッションタイプ標準](session-types.md)を参照）
- サポートされるタイプ：`private`, `group`, `user`, `channel`, `guild`, `thread`
- アダプターはプラットフォームのネイティブタイプを標準タイプにマッピングする責任があります

### 2.2 メッセージイベントフィールド
| フィールド | タイプ | 説明 |
|------|------|------|
| message | array | メッセージセグメント配列 |
| alt_message | string | メッセージセグメントの代替テキスト |
| user_id | string | ユーザーID |
| user_nickname | string | ユーザーニックネーム（任意） |

### 2.3 通知イベントフィールド
| フィールド | タイプ | 説明 |
|------|------|------|
| user_id | string | ユーザーID |
| user_nickname | string | ユーザーニックネーム（任意） |
| operator_id | string | 操作者ID（任意） |

### 2.4 リクエストイベントフィールド
| フィールド | タイプ | 説明 |
|------|------|------|
| user_id | string | ユーザーID |
| user_nickname | string | ユーザーニックネーム（任意） |
| comment | string | リクエストの付言（任意） |
| request_id | string | リクエスト識別子（**強く推奨**、リクエストの承認/拒否操作に使用） |

**`request_id` フィールドの説明**：
- `request_id` はリクエストイベントの固有の操作識別子であり、`HandleRequest` DSLを通じて承認/拒否操作を実行するために使用されます
- アダプターは、リクエストイベントを変換する際に、プラットフォームのネイティブなリクエスト識別子をこのフィールドにマッピングする必要があります
- プラットフォーム自体にリクエストIDがない場合、アダプターは固有の識別子を生成する必要があります（例：タイムスタンプ+ユーザーIDに基づくハッシュなど）
- `request_id` が欠落している場合、`event.approve()` / `event.reject()` は `ValueError` をスローします

## 3. イベントフォーマット例

### 3.1 メッセージイベント
```json
{
  "id": "1234567890",
  "time": 1752241223,
  "type": "message",
  "detail_type": "group",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "抽選 スーパープライズ"
      }
    }
  ],
  "alt_message": "抽選 スーパープライズ",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽選",
    "args": "スーパープライズ"
  }
}
```

### 3.2 通知イベント
```json
{
  "id": "1234567891",
  "time": 1752241224,
  "type": "notice",
  "detail_type": "group_member_increase",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "operator_id": "",
  "yunhu_raw": {...},
  "yunhu_raw_type": "bot.followed"
}
```

### 3.3 リクエストイベント
```json
{
  "id": "1234567892",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "フレンド追加してください",
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. メッセージセグメント標準

### 4.1 標準メッセージセグメント

標準メッセージセグメントタイプにはプラットフォームプレフィックスを**追加しません**：

| タイプ | 説明 | data フィールド |
|------|------|----------|
| `text` | プレーンテキスト | `text: str` |
| `image` | 画像 | `file: str/bytes`, `url: str` |
| `audio` | 音声 | `file: str/bytes`, `url: str` |
| `video` | 動画 | `file: str/bytes`, `url: str` |
| `file` | ファイル | `file: str/bytes`, `url: str`, `filename: str` |
| `mention` | @ユーザー | `user_id: str`, `user_name: str` |
| `reply` | 返信 | `message_id: str` |
| `face` | 絵文字 | `id: str` |
| `location` | 位置情報 | `latitude: float`, `longitude: float` |

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.2 プラットフォーム拡張メッセージセグメント

プラットフォーム固有のメッセージセグメントにはプラットフォームプレフィックスを追加する必要があります：

```json
// Yunhu - フォーム
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "申込フォーム"}}

// Telegram - ステッカー
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**拡張メッセージセグメント要件**：
1. **data内部のフィールドにはプレフィックスを付けない**：`{"type": "yunhu_form", "data": {"form_id": "..."}}` とし、`{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}` とはしない
2. **フォールバック手段の提供**：モジュールが拡張メッセージセグメントを認識できない可能性があるため、アダプターは `alt_message` でテキストの代替を提供する必要があります
3. **ドキュメントの完全性**：各拡張メッセージセグメントについて、アダプターのドキュメントで `type`、`data` 構造、使用シナリオを説明する必要があります

## 5. 未知のイベント処理

認識できないイベントタイプの場合、警告イベントを生成する必要があります：
```json
{
  "id": "1234567893",
  "time": 1752241223,
  "type": "unknown",
  "platform": "yunhu",
  "yunhu_raw": {...},
  "yunhu_raw_type": "unknown",
  "warning": "Unsupported event type: special_event",
  "alt_message": "This event type is not supported by this system."
}
```

---

## 6. 拡張命名規則

### 6.1 フィールド命名

**ルール**：`{platform}_{field_name}`

```
プラットフォームプレフィックス    フィールド名            完全なフィールド名
────────                        ───────                 ──────────
yunhu                           command                 yunhu_command
telegram                        sticker_file_id         telegram_sticker_file_id
onebot11                        anonymous               onebot11_anonymous
email                           subject                 email_subject
```

**要件**：
- `platform` はアダプター登録時のプラットフォーム名と完全に一致する必要があります（大文字小文字を区別）
- `field_name` は `snake_case` で命名します
- 二重アンダースコア `__` で始まる名前は禁止されています（Python予約済み）
- 標準フィールドと同名（`type`、`time`、`message` など）は禁止されています

### 6.2 メッセージセグメントタイプの命名

**ルール**：`{platform}_{segment_type}`

標準メッセージセグメントタイプ（`text`、`image`、`audio`、`video`、`mention`、`reply` など）にはプラットフォームプレフィックスを追加**してはいけません**。プラットフォーム固有のメッセージセグメントタイプのみプレフィックスを追加する必要があります。

### 6.3 生データフィールドの命名

以下のフィールド名は**予約フィールド**であり、すべてのアダプターが従う必要があります：

| 予約フィールド | タイプ | 説明 |
|---------|------|------|
| `{platform}_raw` | `any` | プラットフォームの元のイベントデータの完全なコピー |
| `{platform}_raw_type` | `string` | プラットフォームの元のイベントタイプ識別子 |

**要件**：
- `{platform}_raw` は元のデータのディープコピーである必要があり、参照ではありません
- `{platform}_raw_type` は文字列である必要があり、プラットフォームが数値型を使用している場合でも文字列に変換する必要があります
- これら2つのフィールドはすべてのイベントに**必ず存在する**必要があります（取得できない場合は `null` と空文字列 `""`）

### 6.4 プラットフォーム固有フィールドの例

```json
{
  "yunhu_command": {
    "name": "抽選",
    "args": "スーパープライズ"
  },
  "yunhu_form": {
    "form_id": "123456"
  },
  "telegram_sticker": {
    "file_id": "CAACAgIAAxkBAA..."
  }
}
```

### 6.5 ネストされた拡張フィールド

拡張フィールドは単純な値にすることも、ネストされたオブジェクトにすることもできます：

```json
{
  "telegram_chat": {
    "id": 123456,
    "type": "supergroup",
    "title": "My Group"
  },
  "telegram_forward_from": {
    "user_id": "789",
    "user_name": "ForwardUser"
  }
}
```

**ネストされたフィールドの要件**：
- トップレベルのキーにはプラットフォームプレフィックスを付ける必要があります
- ネストされた内部フィールドにはプラットフォームプレフィックスを**追加しません**
- ネストの深さは3レベルを超えないことを推奨します

### 6.6 `self` フィールドの拡張

`self` オブジェクトの標準必須フィールド（`platform`、`user_id`）については §2.1 を参照してください。以下はErisPulse拡張の任意フィールドです：

| フィールド | タイプ | 説明 |
|------|------|------|
| `self.user_name` | `string` | ボットのニックネーム |
| `self.avatar` | `string` | ボットのアバターURL |
| `self.account_id` | `string` | マルチアカウントモードでのアカウント識別子 |

> **Botステータス追跡**：アダプターは `type: "meta"` イベントを送信することで、フレームワークにBotの接続ステータスを通知します。サポートされる `detail_type`：`connect`（オンライン）、`heartbeat`（ハートビート）、`disconnect`（オフライン）。システムは自動的に `self` フィールドからBotのメタ情報を抽出してステータスを追跡します。さらに、通常のイベント内の `self` フィールドからもBotが自動的に検出されます。詳細は[アダプターシステムAPI - Botステータス管理](../api-reference/adapter-system.md)を参照してください。

---

## 7. セッションタイプの拡張

ErisPulseは、OneBot12標準の `private`、`group` に基づいて、以下のセッションタイプを拡張しています：

| タイプ | OneBot12 標準 | ErisPulse 拡張 | 説明 |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | 1対1プライベートチャット |
| `group` | ✅ | — | グループチャット |
| `user` | — | ✅ | ユーザータイプ（Telegramなど） |
| `channel` | — | ✅ | チャンネル（ブロードキャスト形式） |
| `guild` | — | ✅ | サーバー/コミュニティ |
| `thread` | — | ✅ | トピック/サブチャンネル |

**アダプターのカスタムタイプ拡張**：

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# アダプター起動時に登録
register_custom_type(
    receive_type="email",      # 受信イベントの detail_type
    send_type="email",         # 送信時のターゲットタイプ
    id_field="email_id",       # 対応する ID フィールド名
    platform="email"           # プラットフォーム識別子
)
```

**カスタムタイプの要件**：
- アダプターの `start()` 時に登録し、`shutdown()` 時に登録解除する必要があります
- `receive_type` は標準タイプと重複する名前にしないでください
- `id_field` は `{ターゲット}_id` の命名パターンに従う必要があります

> 完全なセッションタイプの定義とマッピング関係については、[セッションタイプ標準](session-types.md)を参照してください。

---

## 8. モジュール開発者ガイド

### 8.1 拡張フィールドへのアクセス

```python
from ErisPulse.Core.Event import message

@message()
async def handle_message(event):
    # 標準フィールドへのアクセス
    text = event.get_text()
    user_id = event.get_user_id()

    # プラットフォーム拡張フィールドへのアクセス - 方法1：直接 get
    yunhu_command = event.get("yunhu_command")

    # プラットフォーム拡張フィールドへのアクセス - 方法2：ドット記法アクセス（Event ラッパークラス）
    # event.yunhu_command

    # 生データへのアクセス
    raw_data = event.get("yunhu_raw")
    raw_type = event.get_raw_type()

    # プラットフォームの判定
    platform = event.get_platform()
    if platform == "yunhu":
        pass
    elif platform == "telegram":
        pass
```

### 8.2 拡張メッセージセグメントの処理

```python
@message()
async def handle_message(event):
    message_segments = event.get("message", [])

    for segment in message_segments:
        seg_type = segment.get("type")
        seg_data = segment.get("data", {})

        if seg_type == "text":
            text = seg_data["text"]
        elif seg_type.startswith("yunhu_"):
            if seg_type == "yunhu_form":
                form_id = seg_data["form_id"]
        elif seg_type.startswith("telegram_"):
            if seg_type == "telegram_sticker":
                file_id = seg_data["file_id"]
```

### 8.3 ベストプラクティス

1. **標準フィールドを優先して使用**：拡張フィールドが常に存在すると仮定しないでください
2. **プラットフォームの判定**：拡張フィールドの有無から推測するのではなく、`event.get_platform()` を通じてプラットフォームを判定してください
3. **優雅なフォールバック**：拡張メッセージセグメントを処理できない場合は、`alt_message` をフォールバックとして使用してください
4. **プレフィックスのハードコーディングを避ける**：`platform` 変数を使用して動的に結合してください

```python
# ✅ 推奨
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ 非推奨
raw_data = event.get("yunhu_raw")
```

### 8.4 リクエストイベントの処理

モジュール開発者は、`event.approve()` と `event.reject()` を使用してリクエストイベントを操作できます：

```python
from ErisPulse.Core.Event import request

# フレンドリクエスト：自動承認
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # リクエストを承認
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"{user_name} のフレンドリクエストを承認しました")
    else:
        print(f"フレンドリクエストの承認に失敗しました: {result.get('message')}")

# グループ招待：条件に基づいて決定
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # リクエストを拒否
    result = await event.reject(comment="現在新しいグループには参加していません")
```

**アダプターを通じた直接操作**（非イベントハンドラーシナリオに適用）：

```python
from ErisPulse import adapter

# request_id を通じた直接操作
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# Botアカウントを指定した操作
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# 備考を添付
await adapter.myplatform.Request("req_abc123").accept(comment="ようこそ")
```

---

## 9. 関連ドキュメント

- [各プラットフォーム特性ドキュメント](../platform-guide/README.md) - 各プラットフォームの特性、既知の拡張イベント、メッセージセグメントなどを理解するためにアクセスできます。
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング関係
- [送信メソッド仕様](send-method-spec.md) - Sendクラスのメソッド命名、パラメータ仕様、および逆変換要件
- [APIレスポンス標準](api-response.md) - アダプターAPIレスポンスフォーマット標準