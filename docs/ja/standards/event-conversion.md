# アダプタ標準化変換規格

## 1. 核心原則
1. 严格的互換性：すべての標準フィールドはOneBot12仕様に完全に準拠する必要があります。
2. 明確な拡張：プラットフォーム固有の機能には必ず {platform}_ 前置きを付ける必要があります（例：yunhu_form）。
3. データの完全性：元のイベントデータは {platform}_raw フィールドに、元のイベントタイプは {platform}_raw_type フィールドに保持する必要があります。
4. 時間の統一：すべてのタイムスタンプは10桁のUnixタイムスタンプ（秒単位）に変換する必要があります。
5. プラットフォームの統一：platform項目の命名は、ErisPulseで登録した名称/別称と一致する必要があります。

## 2. 標準フィールド要件

### 2.1 必須フィールド
| フィールド | 型 | 説明 |
|------|------|------|
| id | string | イベントの一意の識別子 |
| time | integer | Unixタイムスタンプ（秒単位） |
| type | string | イベントの種類 |
| detail_type | string | イベントの詳細な種類（[会話タイプ標準](session-types.md)を参照） |
| platform | string | プラットフォーム名 |
| self | object | ロボット自身の情報 |
| self.platform | string | プラットフォーム名 |
| self.user_id | string | ロボットのユーザーID |

**detail_type の規格**：
- ErisPulse 標準会話タイプを使用する必要があります（[会話タイプ標準](session-types.md)を参照）
- 対応するタイプ：`private`, `group`, `user`, `channel`, `guild`, `thread`
- アダプターは、プラットフォーム固有のタイプを標準タイプにマッピングする責任があります

### 2.2 メッセージイベントフィールド
| フィールド | 型 | 説明 |
|------|------|------|
| message | array | メッセージセグメントの配列 |
| alt_message | string | メッセージセグメントの代替テキスト |
| user_id | string | ユーザーID |
| user_nickname | string | ユーザーのニックネーム（オプション） |

### 2.3 通知イベントフィールド
| フィールド | 型 | 説明 |
|------|------|------|
| user_id | string | ユーザーID |
| user_nickname | string | ユーザーのニックネーム（オプション） |
| operator_id | string | 操作者のID（オプション） |

### 2.4 要求イベントフィールド
| フィールド | 型 | 説明 |
|------|------|------|
| user_id | string | ユーザーID |
| user_nickname | string | ユーザーのニックネーム（オプション） |
| comment | string | 要求の付言（オプション） |
| request_id | string | 要求の識別子（**強く推奨**、同意/拒否操作に使用） |

**`request_id` フィールドの説明**：
- `request_id` は要求イベントの一意の操作識別子であり、`HandleRequest` DSL を使用して同意/拒否操作を実行するために使用されます
- アダプターは、要求イベントを変換する際に、プラットフォーム固有の要求識別子をこのフィールドにマッピングする必要があります
- プラットフォームに要求IDがない場合、アダプターは一意の識別子（例：タイムスタンプ+ユーザーIDのハッシュ）を生成する必要があります
- `request_id` が欠落している場合、`event.approve()` / `event.reject()` は `ValueError` をスローします

## 3. イベント形式の例

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
        "text": "抽選 超大賞"
      }
    }
  ],
  "alt_message": "抽選 超大賞",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽選",
    "args": "超大賞"
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

### 3.3 要求イベント (request)
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
  "comment": "友達追加してください",
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. 消息セグメント標準

### 4.1 標準メッセージセグメント

標準メッセージセグメントには**プラットフォームプレフィックスを付与する必要はありません**。

| タイプ | 説明 | data フィールド |
|------|------|----------|
| `text` | 純粋なテキスト | `text: str` |
| `image` | 画像 | `file: str/bytes`, `url: str` |
| `audio` | 音声 | `file: str/bytes`, `url: str` |
| `video` | 動画 | `file: str/bytes`, `url: str` |
| `file` | ファイル | `file: str/bytes`, `url: str`, `filename: str` |
| `mention` | ユーザーへのメンション | `user_id: str`, `user_name: str` |
| `reply` | メッセージへの返信 | `message_id: str` |
| `face` | スタンプ | `id: str` |
| `location` | 位置情報 | `latitude: float`, `longitude: float` |
| `keyboard` | ボタン/インラインキーボード | `rows: list[list[button]]`（4.1.1参照） |

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.1.1 keyboard ボタン/インラインキーボードセグメント（クロスプラットフォーム互換）

ボタン/インラインキーボードは、Telegram / 云湖 / QQBot / Kook / Discord などの複数のプラットフォームで対応しており、**クロスプラットフォームで共通する概念**です。したがって、プラットフォームプレフィックスなしの標準メッセージセグメントとして扱います。アダプタは、標準セグメントをプラットフォーム固有の構造に変換する必要があります。一方、プラットフォーム固有の拡張セグメント（例: `telegram_inline_keyboard`）はそのまま透かし（透伝）されます。

```json
{
  "type": "keyboard",
  "data": {
    "rows": [
      [
        {"label": "選択肢A", "type": "callback", "data": "vote:A"},
        {"label": "公式サイト", "type": "link", "data": "https://example.com"}
      ]
    ]
  }
}
```

**フィールドの説明：**

| フィールド | 型 | 必須 | 説明 |
|------|------|------|------|
| `rows` | 2次元配列 | はい | 各サブ配列が1行のボタンを表す |
| `rows[][].label` | str | はい | ボタンに表示するテキスト |
| `rows[][].type` | str | はい | `callback`（クリック時にデータを返す） / `link`（URLに移動） |
| `rows[][].data` | str | はい | コールバックデータ（type=callback）または移動先URL（type=link） |
| `rows[][].*` | Any | いいえ | プラットフォーム固有のオプションフィールド（例: `web_app`、`menus`）、アダプタは対応能力に応じてマッピングまたは無視する |

**アダプタの変換例**（完全なマッピングとインタラクションコールバックイベントの標準は [クロスプラットフォームインタラクションコンポーネント標準](docs/ja/standardization-guide.md)を参照してください）：

| プラットフォーム | 標準セグメント → プラットフォーム固有 |
|------|------------------|
| Telegram | `inline_keyboard`：`[{text, callback_data \| url}]` |
| 云湖 | `buttons`：`[{label, action_type: 2=コールバック \| 1=移動, ...}]` |
| QQBot | `keyboard.content.rows`：`[{label, type: 2=コールバック \| 0=移動, data}]`（markdown形式のメッセージが必要） |
| Kook | カードの action-group モジュール |
| Discord | components：`action_row` + `buttons`（custom_id/url） |

### 4.2 プラットフォーム拡張メッセージセグメント

プラットフォーム固有のメッセージセグメントには、**プラットフォームプレフィックスを付与する必要があります**。

```json
// 云湖 - フォーム
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "登録フォーム"}}

// Telegram - スタンプ
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**拡張メッセージセグメントの要件：**
1. **data内部のフィールドにプレフィックスを付与しない**：`{"type": "yunhu_form", "data": {"form_id": "..."}}` ではなく `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2. **降格（代替）対応を提供する**：モジュールが拡張メッセージセグメントを認識できない場合、アダプタは `alt_message` にテキストによる代替を提供する
3. **ドキュメントの完全性**：各拡張メッセージセグメントは、アダプタのドキュメントで `type`、`data` の構造と使用シーンを明確に説明する必要がある

## 5. 未知イベントの処理

イベントの種類が識別できない場合、警告イベントを生成する必要があります：

```json
{
  "id": "1234567893",
  "time": 1752241223,
  "type": "unknown",
  "platform": "yunhu",
  "yunhu_raw": {...},
  "yunhu_raw_type": "unknown",
  "warning": "サポートされていないイベントタイプ: special_event",
  "alt_message": "このシステムではこのイベントタイプはサポートされていません。"
}
```

## 6. 拡張名命名規則

### 6.1 フィールド名

**規則**: `{platform}_{field_name}`

```
プラットフォーム接頭辞    フィールド名            完全なフィールド名
────────    ───────          ──────────
yunhu       command           yunhu_command
telegram    sticker_file_id   telegram_sticker_file_id
onebot11    anonymous         onebot11_anonymous
email       subject           email_subject
```

**要件**:
- `platform` は、アダプタ登録時のプラットフォーム名と完全に一致する必要があります（大文字小文字を区別）
- `field_name` は `snake_case` で命名する
- `__` で始まるダブルアンダースコアは使用禁止（Python 予約）
- 標準フィールド名（`type`、`time`、`message` など）と重複しないこと

### 6.2 メッセージセグメント型名

**規則**: `{platform}_{segment_type}`

標準のメッセージセグメント型（`text`、`image`、`audio`、`video`、`mention`、`reply` など）には、プラットフォーム接頭辞を追加しないでください。プラットフォーム固有のメッセージセグメント型のみ接頭辞を追加する必要があります。

### 6.3 元データフィールド名

以下のフィールド名は**予約フィールド**であり、すべてのアダプタは以下の要件を遵守する必要があります：

| 予約フィールド | 型 | 説明 |
|---------|------|------|
| `{platform}_raw` | `any` | プラットフォームの元のイベントデータの完全なコピー |
| `{platform}_raw_type` | `string` | プラットフォームの元のイベントタイプの識別子 |

**要件**:
- `{platform}_raw` は、参照ではなく元データのディープコピーである必要があります
- `{platform}_raw_type` は文字列型である必要があります。プラットフォームが数値型を使用している場合でも、文字列に変換する必要があります
- これらの2つのフィールドは、すべてのイベントで**必ず存在する**必要があります（取得できない場合は `null` と空文字列 `""` とする）

### 6.4 プラットフォーム固有フィールドの例

```json
{
  "yunhu_command": {
    "name": "抽奖",
    "args": "超级大奖"
  },
  "yunhu_form": {
    "form_id": "123456"
  },
  "telegram_sticker": {
    "file_id": "CAACAgIAAxkBAA..."
  }
}
```

### 6.5 嵌套拡張フィールド

拡張フィールドは単純な値でも、ネストされたオブジェクトでも構いません：

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

**ネストされたフィールドの要件**:
- トップレベルのキーには必ずプラットフォーム接頭辞を付ける
- ネストされた内部フィールドには、プラットフォーム接頭辞を追加しない
- ネストの深さは3層を超えないようにすることを推奨

### 6.6 `self` フィールドの拡張

`self` オブジェクトの標準必須フィールド（`platform`、`user_id`）は §2.1 を参照してください。以下は ErisPulse が拡張したオプションフィールドです：

| フィールド | 型 | 説明 |
|------|------|------|
| `self.user_name` | `string` | ロボットのニックネーム |
| `self.avatar` | `string` | ロボットのアバター URL |
| `self.account_id` | `string` | マルチアカウントモードにおけるアカウント識別子 |

> **Bot 状態の追跡**: アダプタは `type: "meta"` イベントを送信して、フレームワークに Bot の接続状態を通知します。サポートされる `detail_type`: `connect`（オンライン）、`heartbeat`（ハートビート）、`disconnect`（オフライン）。システムは、この `detail_type` から `self` フィールドの Bot 元情報を取り出して自動的に状態を追跡します。また、通常のイベントにおける `self` フィールドも自動的に Bot を検出します。詳細は [アダプタシステム API - Bot 状態管理](../api-reference/adapter-system.md) を参照してください。

## 7. セッションタイプ拡張

ErisPulse は OneBot12 標準の `private`、`group` の上に以下のセッションタイプを拡張しています。

| タイプ | OneBot12 標準 | ErisPulse 拡張 | 説明 |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | 1対1のプライベートチャット |
| `group` | ✅ | — | グループチャット |
| `user` | — | ✅ | ユーザータイプ（Telegram など） |
| `channel` | — | ✅ | チャンネル（放送型） |
| `guild` | — | ✅ | サーバー/コミュニティ |
| `thread` | — | ✅ | トピック/サブチャンネル |

**アダプタ独自のタイプ拡張**：

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# アダプタ起動時に登録
register_custom_type(
    receive_type="email",      # 受信イベント中の detail_type
    send_type="email",         # 送信時の対象タイプ
    id_field="email_id",       # 対応するIDフィールド名
    platform="email"           # プラットフォーム識別子
)
```

**独自タイプの要件**：
- アダプタの `start()` 時に登録し、`shutdown()` 時に登録解除する必要があります
- `receive_type` は標準タイプと重複しないようにする必要があります
- `id_field` は `{対象}_id` の命名規則に従う必要があります

> 完全なセッションタイプ定義とマッピング関係は、[セッションタイプ標準](docs/ja/session-types.md)を参照してください。

## 8. モジュール開発者ガイド

### 8.1 拡張フィールドのアクセス

```python
from ErisPulse.Core.Event import message

@message()
async def handle_message(event):
    # 標準フィールドのアクセス
    text = event.get_text()
    user_id = event.get_user_id()

    # プラットフォーム拡張フィールドのアクセス - 方法1: 直接 get
    yunhu_command = event.get("yunhu_command")

    # プラットフォーム拡張フィールドのアクセス - 方法2: 点式アクセス (Event ラッパークラス)
    # event.yunhu_command

    # 送信元データのアクセス
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

### 8.3 最適な実践方法

1. **標準フィールドの優先使用**: 拡張フィールドが必ず存在すると仮定しないこと
2. **プラットフォームの判定**: 拡張フィールドの存在によってプラットフォームを推測するのではなく、`event.get_platform()` を使用すること
3. **エラーハンドリング**: 拡張メッセージセグメントを処理できない場合は、`alt_message` をバックアップとして使用すること
4. **プレフィックスのハードコーディングを避ける**: `platform` 変数を使って動的に文字列を連結すること

```python
# ✅ 推奨
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ 推奨されない
raw_data = event.get("yunhu_raw")
```

### 8.4 要求イベントの処理

モジュール開発者は、`event.approve()` および `event.reject()` を使用して要求イベントを処理することができます。

```python
from ErisPulse.Core.Event import request

# フレンドリクエスト: 自動的に承認
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # 承認リクエスト
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"{user_name} からのフレンドリクエストを承認しました")
    else:
        print(f"フレンドリクエストの承認に失敗しました: {result.get('message')}")

# グループ招待: 条件に応じて決定
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # 拒否リクエスト
    result = await event.reject(comment="暫定的に新しいグループに参加しません")
```

**アダプターを介した直接操作**（イベントハンドラ以外の場面に適用可能）:

```python
from ErisPulse import adapter

# request_id を使用して直接操作
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# 特定の Bot アカウントで操作
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# 備考を付けて操作
await adapter.myplatform.Request("req_abc123").accept(comment="ようこそ")
```

## 9. notice / request イベントのセッションタイプ推論

### 9.1 問題の背景

notice イベントと request イベントの `detail_type` は**意味論的なサブタイプ**（例: `group_member_increase`、`friend_increase`）であり、セッションタイプ（例: `group`、`private`）ではありません。

```
type        detail_type                  含意            セッションタイプ
────        ───────────                  ────            ────────
message     group                        群チャットメッセージ         group（detail_type がセッションタイプ）
message     private                      プライベートチャットメッセージ         private（detail_type がセッションタイプ）
notice      group_member_increase        群メンバーの増加       group（group_id から推論）
notice      friend_increase              友達の増加         private（user_id から推論）
request     friend                       友達リクエスト         private（user_id から推論）
request     group                        群リクエスト           group（detail_type がセッションタイプ）
```

### 9.2 推論ルール

`infer_receive_type()` の推論順序は以下の通りです：

1. `detail_type` が既知のセッションタイプ（`private`/`group`/`channel`/`guild`/`thread`/`user`）である場合、そのまま使用する
2. `detail_type` がカスタムセッションタイプである場合、そのまま使用する
3. それ以外（notice/request の意味論的サブタイプ）の場合、ID フィールドに基づいて推論する：
   - `group_id` がある → `"group"`
   - `channel_id` がある → `"channel"`
   - `guild_id` がある → `"guild"`
   - `thread_id` がある → `"thread"`
   - `user_id` がある → `"private"`

### 9.3 `event.reply()` の送信先推論

notice/request イベントにおける `event.reply()` の送信先は、セッションタイプの推論によって決まります：

- グループ通知イベント（`group_id` を含む）→ グループに返信
- 友達通知イベント（`user_id` だけを含む）→ ユーザーのプライベートチャットに返信

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() はグループ（group/group_789）に送信
    await event.reply("ようこそ！")

    # 管理者に通知する場合（プライベートチャット）、明示的に送信先を指定する：
    await adapter.Send.To("user", "admin_id").Text(f"新メンバー {user_id} が {group_id} に参加しました")
```

### 9.4 アダプタ開発の推奨事項

notice/request イベントにおいて、正しい ID フィールドが含まれていることを確認してください：

| detail_type | 必須の ID フィールド | 推論されるセッションタイプ |
|-------------|-------------------|---------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend`（リクエスト） | `user_id` | `private` |
| `group`（リクエスト） | `group_id` | `group` |

## 10. 関連ドキュメント

- [各プラットフォームの機能ドキュメント](../platform-guide/README.md) - ここでは、各プラットフォームの機能や既知の拡張イベントやメッセージセグメントなどについて説明しています。
- [会話タイプの標準](session-types.md) - 会話タイプの定義とマッピング関係
- [送信メソッドの規格](send-method-spec.md) - Send クラスのメソッド命名、パラメータ規格および逆変換の要件
- [API 応答の標準](api-response.md) - アダプターの API 応答形式の標準
- [API アクションの標準](api-action-spec.md) - OneBot12 標準 API アクションの統一インターフェース