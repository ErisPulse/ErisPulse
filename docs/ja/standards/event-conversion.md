# アダプター標準化変換仕様

## 1. コア原則
1. **厳格な互換性**：すべての標準フィールドは OneBot12 仕様を完全に遵守する必要がある
2. **明確な拡張**：プラットフォーム固有の機能は `{platform}_` プレフィックスを追加する必要がある（例：yunhu_form）
3. **データ整合性**：元のイベントデータは `{platform}_raw` フィールドに、元のイベントタイプは `{platform}_raw_type` フィールドに保持する必要がある
4. **時間の統一**：すべてのタイムスタンプは 10 桁の Unix タイムスタンプ（秒単位）に変換する必要がある
5. **プラットフォームの統一**：`platform` 項目の命名は、ErisPulse で登録された名前/別名と一致させる必要がある

## 2. 標準フィールド要件

### 2.1 必須フィールド
| フィールド | タイプ | 説明 |
|------|------|------|
| id | string | イベント固有の識別子 |
| time | integer | Unix タイムスタンプ（秒単位） |
| type | string | イベントタイプ |
| detail_type | string | イベント詳細タイプ（詳細は[セッションタイプ標準](session-types.md)を参照） |
| platform | string | プラットフォーム名 |
| self | object | ロボット自身の情報 |
| self.platform | string | プラットフォーム名 |
| self.user_id | string | ロボットのユーザーID |

**`detail_type` 規格**：
- ErisPulse 標準のセッションタイプを使用する必要がある（詳細は [セッションタイプ標準](session-types.md) を参照）
- サポートされるタイプ：`private`、`group`、`user`、`channel`、`guild`、`thread`
- アダプターはプラットフォームのネイティブタイプを標準タイプにマッピングする責任を持つ

### 2.2 メッセージイベントフィールド
| フィールド | タイプ | 説明 |
|------|------|------|
| message | array | メッセージセグメントの配列 |
| alt_message | string | メッセージセグメントの代替テキスト |
| user_id | string | ユーザーID |
| user_nickname | string | ユーザーのニックネーム（任意） |

### 2.3 通知イベントフィールド
| フィールド | タイプ | 説明 |
|------|------|------|
| user_id | string | ユーザーID |
| user_nickname | string | ユーザーのニックネーム（任意） |
| operator_id | string | 操作者ID（任意） |

### 2.4 リクエストイベントフィールド
| フィールド | タイプ | 説明 |
|------|------|------|
| user_id | string | ユーザーID |
| user_nickname | string | ユーザーのニックネーム（任意） |
| comment | string | リクエストの補足コメント（任意） |
| request_id | string | リクエスト識別子（**強く推奨**、承諾/拒否操作に使用） |

**`request_id` フィールドの説明**：
- `request_id` はリクエストイベントの唯一の操作識別子であり、`HandleRequest` DSL を介して承諾/拒否操作を実行するために使用される
- アダプターはリクエストイベントを変換する際、プラットフォームのネイティブリクエストIDをこのフィールドにマッピングする必要がある
- プラットフォーム自体にリクエストIDがない場合、アダプターは一意の識別子を生成する必要がある（タイムスタンプ+ユーザーIDに基づくハッシュなど）
- `request_id` が欠落している場合、`event.approve()` / `event.reject()` は `ValueError` をスローする

## 3. イベントフォーマットの例

### 3.1 メッセージイベント (message)
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
        "text": "抽選 スーパープレゼント"
      }
    }
  ],
  "alt_message": "抽選 スーパープレゼント",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽選",
    "args": "スーパープレゼント"
  }
}
```

### 3.2 通知イベント (notice)
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

### 3.3 リクエストイベント (request)
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
  "comment": "友達申請",
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. メッセージセグメントの標準

### 4.1 標準メッセージセグメント

標準メッセージセグメントタイプには**プラットフォームプレフィックスを追加しません**：

| タイプ | 説明 | data フィールド |
|------|------|----------|
| `text` | 純テキスト | `text: str` |
| `image` | 画像 | `file: str/bytes`, `url: str` |
| `audio` | 音声 | `file: str/bytes`, `url: str` |
| `video` | 動画 | `file: str/bytes`, `url: str` |
| `file` | ファイル | `file: str/bytes`, `url: str`, `filename: str` |
| `mention` | ユーザーへのメンション | `user_id: str`, `user_name: str` |
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
// 雲湖 - フォーム
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "参加申し込み"}}

// Telegram - スタンプ
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**拡張メッセージセグメントの要件**：
1. **data 内部フィールドにプレフィックスを追加しない**：`{"type": "yunhu_form", "data": {"form_id": "..."}}` とし、`{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}` としない
2. **フォールバック手段を提供する**：モジュールが拡張メッセージセグメントを認識できない場合があるため、アダプターは `alt_message` にテキストの代替を提供する必要がある
3. **ドキュメントを完全に記述する**：各拡張メッセージセグメントについては、アダプターのドキュメントで `type`、`data` 構造と使用シナリオを説明する必要がある

## 5. 不明イベントの処理

認識できないイベントタイプについては、警告イベントを生成する必要があります：
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
────────    ───────          ──────────
yunhu       command           yunhu_command
telegram    sticker_file_id   telegram_sticker_file_id
onebot11    anonymous         onebot11_anonymous
email       subject           email_subject
```

**要件**：
- `platform` はアダプターの登録時のプラットフォーム名と完全に一致している必要がある（大文字・小文字を区別する）
- `field_name` は `snake_case` 命名を使用する
- 二重アンダースコア `__` で始まる名前は禁止する（Python で予約されているため）
- 標準フィールドと同じ名前（`type`、`time`、`message` など）の使用は禁止する

### 6.2 メッセージセグメントタイプ命名

**ルール**：`{platform}_{segment_type}`

標準メッセージセグメントタイプ（`text`、`image`、`audio`、`video`、`mention`、`reply` など）には**プラットフォームプレフィックスを追加しない**。プラットフォーム固有のメッセージセグメントタイプの場合にのみ、プレフィックスを追加する必要がある。

### 6.3 原始データフィールド命名

以下のフィールド名は**予約フィールド**であり、すべてのアダプターが遵守する必要があります：

| 予約フィールド | タイプ | 説明 |
|---------|------|------|
| `{platform}_raw` | `any` | プラットフォームの元のイベントデータの完全なコピー |
| `{platform}_raw_type` | `string` | プラットフォームの元のイベントタイプ識別子 |

**要件**：
- `{platform}_raw` は元のデータのディープコピーであり、参照ではない必要がある
- `{platform}_raw_type` は文字列である必要があり、プラットフォームが数値タイプを使用していても文字列に変換する必要がある
- これら2つのフィールドはすべてのイベントに**存在しなければならない**（取得できない場合は `null` と空文字列 `""`）

### 6.4 プラットフォーム固有のフィールド例

```json
{
  "yunhu_command": {
    "name": "抽選",
    "args": "スーパープレゼント"
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

拡張フィールドは単純な値でも、ネストされたオブジェクトでもよい：

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

**ネストフィールドの要件**：
- トップレベルのキーにはプラットフォームプレフィックスを付ける必要がある
- ネスト内部のフィールドには**プラットフォームプレフィックスを追加しない**
- ネストの深さは 3 層を超えないことを推奨する

### 6.6 `self` フィールドの拡張

`self` オブジェクトの標準必須フィールド（`platform`、`user_id`）は §2.1 を参照。以下は ErisPulse による拡張の任意フィールドです：

| フィールド | タイプ | 説明 |
|------|------|------|
| `self.user_name` | `string` | ロボットのニックネーム |
| `self.avatar` | `string` | ロボットのアバター URL |
| `self.account_id` | `string` | マルチアカウントモードのアカウント識別子 |

> **Bot 状態追跡**：アダプターは `type: "meta"` イベントを送信してフレームワークに Bot の接続状態を通知します。サポートされる `detail_type`：`connect`（接続開始）、`heartbeat`（ハートビート）、`disconnect`（切断）。システムは自動的に `self` フィールドの Bot メタ情報を抽出して状態追跡を行います。さらに、一般イベント内の `self` フィールドからも Bot が自動的に検出されます。詳細は [アダプターシステム API - Bot 状態管理](../api-reference/adapter-system.md) を参照。

---

## 7. セッションタイプの拡張

ErisPulse は OneBot12 標準の `private`、`group` に加え、以下のセッションタイプを拡張しています：

| タイプ | OneBot12 標準 | ErisPulse 拡張 | 説明 |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | 1対1のプライベートチャット |
| `group` | ✅ | — | グループチャット |
| `user` | — | ✅ | ユーザータイプ（Telegram など） |
| `channel` | — | ✅ | チャンネル（ブロードキャスト形式） |
| `guild` | — | ✅ | サーバー/コミュニティ |
| `thread` | — | ✅ | スレッド/サブチャンネル |

**アダプターのカスタムタイプ拡張**：

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# アダプター起動時に登録
register_custom_type(
    receive_type="email",      # 受信イベントにおける detail_type
    send_type="email",         # 送信時のターゲットタイプ
    id_field="email_id",       # 対応する ID フィールド名
    platform="email"           # プラットフォーム識別子
)
```

**カスタムタイプの要件**：
- アダプターの `start()` 時に登録し、`shutdown()` 時に解除する必要がある
- `receive_type` は標準タイプと重複しないようにする必要がある
- `id_field` は `{ターゲット}_id` の命名規則に従う必要がある

> 完全なセッションタイプの定義とマッピング関係については [セッションタイプ標準](session-types.md) を参照してください。

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

    # プラットフォーム拡張フィールドへのアクセス - 方法1: 直接 get
    yunhu_command = event.get("yunhu_command")

    # プラットフォーム拡張フィールドへのアクセス - 方法2: ドット記法（Event ラッパークラス）
    # event.yunhu_command

    # 原始データへのアクセス
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

1. **標準フィールドを優先して使用する**：拡張フィールドが必ず存在すると仮定しない
2. **プラットフォームの判定**：拡張フィールドの存在によってプラットフォームを推測するのではなく、`event.get_platform()` を使用して判定する
3. **優雅なフォールバック（デグレード）**：拡張メッセージセグメントを処理できない場合は、`alt_message` を使用してフォールバックとする
4. **プレフィックスをハードコーディングしない**：`platform` 変数を使用して動的に連結する

```python
# ✅ 推奨
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ 推奨しない
raw_data = event.get("yunhu_raw")
```

### 8.4 リクエストイベントの処理

モジュール開発者は `event.approve()` と `event.reject()` を使用してリクエストイベントを操作できます：

```python
from ErisPulse.Core.Event import request

# 友達リクエスト：自動承諾
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # リクエストを承諾する
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"既に {user_name} の友達リクエストを承諾しました")
    else:
        print(f"友達リクエストの承諾に失敗しました: {result.get('message')}")

# グループ招待：条件に応じて決定する
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # リクエストを拒否する
    result = await event.reject(comment="新しいグループには参加しません")
```

**アダプターを介した直接操作**（イベントハンドラー以外のシナリオで適用）：

```python
from ErisPulse import adapter

# request_id を介して直接操作する
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# 特定の Bot アカウントで操作する
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# 注釈を付ける
await adapter.myplatform.Request("req_abc123").accept(comment="ようこそ")
```

---

## 9. notice / request イベントのセッションタイプ推論

### 9.1 問題背景

notice イベントと request イベントの `detail_type` は**意味的サブタイプ**（例：`group_member_increase`、`friend_increase`）であり、セッションタイプ（例：`group`、`private`）ではない。

```
type        detail_type                  意味            セッションタイプ
────        ───────────                  ────            ────────
message     group                        グループメッセージ  group（detail_type がセッションタイプ）
message     private                      プライベートメッセージ private（detail_type がセッションタイプ）
notice      group_member_increase        グループメンバー追加 group（group_id から推論が必要）
notice      friend_increase              友達追加           private（user_id から推論が必要）
request     friend                       友達リクエスト      private（user_id から推論が必要）
request     group                        グループリクエスト  group（detail_type がセッションタイプ）
```

### 9.2 推論ルール

`infer_receive_type()` の推論順序：

1. `detail_type` が既知のセッションタイプ（`private`/`group`/`channel`/`guild`/`thread`/`user`）の場合、そのまま使用
2. `detail_type` がカスタムセッションタイプの場合、そのまま使用
3. それ以外の場合（notice/request の意味的サブタイプ）、ID フィールドに基づいて推論する：
   - `group_id` がある → `"group"`
   - `channel_id` がある → `"channel"`
   - `guild_id` がある → `"guild"`
   - `thread_id` がある → `"thread"`
   - `user_id` がある → `"private"`

### 9.3 `event.reply()` ターゲットの推論

notice/request イベント内の `event.reply()` の送信ターゲットは、セッションタイプの推論によって決定されます：

- グループ通知イベント（`group_id` を含む）→ **グループ**に返信
- 友達通知イベント（`user_id` のみ含む）→ **ユーザーのプライベートチャット**に返信

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() はグループに送信される（group/group_789）
    await event.reply("グループへようこそ！")

    # 管理者に通知する場合（プライベートチャット）、明示的にターゲットを指定する：
    await adapter.Send.To("user", "admin_id").Text(f"新規メンバー {user_id} が {group_id} に参加しました")
```

### 9.4 アダプター開発の推奨事項

notice/request イベントに正しい ID フィールドが含まれていることを確認する：

| detail_type | 必須な ID フィールド | 推論されたセッションタイプ |
|-------------|-------------------|---------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend`（リクエスト） | `user_id` | `private` |
| `group`（リクエスト） | `group_id` | `group` |

---

## 10. 関連ドキュメント

- [各プラットフォーム特性ドキュメント](../platform-guide/README.md) - 各プラットフォームの特性、既知の拡張イベントやメッセージセグメントなどを確認できます。
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング関係
- [送信メソッド仕様](send-method-spec.md) - Send クラスのメソッド命名、パラメータ規格、および逆変換の要件
- [API レスポンス標準](api-response.md) - アダプター API レスポンスフォーマット規格
- [API アクション標準](api-action-spec.md) - OneBot12 標準 API アクションの統一インターフェース