# アダプタ標準変換規格

> [!TIP]
> **このドキュメントを読むべきタイミング**：アダプタ内でプラットフォームのネイティブイベントを OneBot12 標準イベントに変換する際、必須フィールド、メッセージセグメント構造、拡張フィールド命名規則（`{platform}_` プレフィックス）、会話タイプの推論を確認する必要がある場合。不要であれば飛ばしてください。

## 1. 核心原則

1. **厳密な互換性**：すべての標準フィールドは OneBot12 規格に完全に準拠する。
2. **明確な拡張**：プラットフォーム固有の機能は `{platform}_` プレフィックスを付ける（例：yunhu_form）。
3. **データの完全性**：元のイベントデータは `{platform}_raw` フィールドに、元のイベントタイプは `{platform}_raw_type` フィールドに保持する。
4. **時間の統一**：すべてのタイムスタンプは 10 位の Unix タイムスタンプ（秒単位）に変換する。
5. **プラットフォームの統一**：`platform` 項目の命名は、ErisPulse に登録した名前/別称と一致する。

## 2. 標準フィールド要件

### 2.1 必須フィールド
| フィールド | 型 | 説明 |
|------|------|------|
| id | string | イベントの一意な識別子 |
| time | integer | Unix タイムスタンプ（秒単位） |
| type | string | イベントのタイプ |
| detail_type | string | イベントの詳細タイプ（[会話タイプ標準](session-types.md)を参照） |
| sub_type | string | イベントのサブタイプ |
| platform | string | プラットフォーム名 |
| self | object | ロボット自身の情報 |
| self.platform | string | プラットフォーム名 |
| self.user_id | string | ロボットのユーザーID |

> **OneBot12 基準**：`self.platform` / `self.user_id` とメッセージイベントの `message_id` は OneBot12 基準で定義されたフィールドであり、フレームワークは基準定義を直接採用し、独自の拡張キー（`self.account_id` は動的アカウントが user_id を取得する前に代用する限定拡張キー、§6 を参照）を導入しない。

**detail_type 規格**：
- ErisPulse 標準会話タイプを使用する（[会話タイプ標準](session-types.md)を参照）
- 対応するタイプ：`private`, `group`, `user`, `channel`, `guild`, `thread`
- アダプタは、プラットフォームのネイティブタイプを標準タイプにマッピングする。

### 2.2 メッセージイベントフィールド
| フィールド | 型 | 説明 |
|------|------|------|
| message_id | string | メッセージID（OneBot12 基準必須フィールド、アダプタはイベントの最上層に生成する） |
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
| comment | string | 要求のコメント（オプション） |
| request_id | string | 要求の識別子（**強く推奨**、同意/拒否操作に使用） |

**`request_id` フィールドの説明**：
- `request_id` は要求イベントの唯一の操作識別子であり、`Request` DSL を通じて同意/拒否操作に使用される。
- アダプタは、プラットフォームのネイティブの要求識別子をこのフィールドにマッピングする。
- プラットフォームに要求IDがない場合、アダプタはユニークな識別子（例：タイムスタンプ+ユーザーIDのハッシュ）を生成する。
- `request_id` が欠落している場合、`event.approve()` / `event.reject()` は `ValueError` をスローする。

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
        "text": "抽奖 超级大奖"
      }
    }
  ],
  "alt_message": "抽奖 超级大奖",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽奖",
    "args": "超级大奖"
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
  "comment": "请加好友",
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. メッセージセグメント標準

### 4.1 標準メッセージセグメント

標準メッセージセグメントにはプラットフォームのプレフィックスを付けない。

| タイプ | 説明 | data フィールド |
|------|------|----------|
| `text` | 純テキスト | `text: str` |
| `image` | 画像 | `file`, `url: str` |
| `voice` | 音声（即時録音の音声、`audio` とは区別） | `file`, `url: str` |
| `audio` | 音楽（再生可能な音楽ファイル、`voice` とは区別） | `file`, `url: str` |
| `video` | 動画 | `file`, `url: str` |
| `file` | ファイル | `file`, `url: str`, `filename: str` |
| `mention` | @ユーザー | `user_id: str`, `user_name: str` |
| `mention_all` | @全員 | data フィールドなし |
| `reply` | 返信 | `message_id: str`, `user_id: str`（返信の元送信者、受信方向はアダプタが可能な限り記入） |
| `location` | 位置 | `latitude: float`, `longitude: float`, `title: str`（オプション）, `content: str`（オプション） |
| `face` | 表情（ErisPulse 跨プラットフォーム拡張セグメント） | `id: str` |
| `keyboard` | ボタン/インラインキーボード（ErisPulse 跨プラットフォーム拡張セグメント） | `rows: list[list[button]]`（4.1.1 参照） |

> **OneBot12 基準とのフィールドマッピング**：メディアセグメント（`image` / `voice` / `audio` / `video` / `file`）は OneBot12 基準では `file_id: str` である。本標準の `file`（送信形態の超集合：URL / 本地パス / bytes）と `url`（受信回路）は、アダプタによってプラットフォームの `file_id` リソースに双方向にマッピングされる。`face` / `keyboard` は OneBot12 基準の外の拡張セグメントである。

**メディアセグメント `file` フィールド形式**（送信方向、`image` / `audio` / `video` / `file` に共通）：

| 形態 | 例 | アダプタの要件 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/a.png` | **必須** |
| 本地ファイルパス | `/tmp/a.png`、`C:\tmp\a.png` | **必須** |
| 二進数データ | `bytes` | **必須** |
| `file://` URI / Base64 / Data URI | `file:///tmp/a.png`、`data:image/png;base64,...` | **推奨** |

> 完全なメディア送信プロトコル（形態判定順序、ファイル名推論、能力降格の段階）は
> [送信方法規格 §2.1](send-method-spec.md#21-媒体消息发送协议image--voice--video--file) を参照。

**フィールドの方向意味**：

- `file`：**送信方向**のコンテンツソース（上記の形態）；**受信方向**はアダプタが可能な限りプラットフォームで取得可能な形態を記入する
  （通常はダウンロード可能な URL、または `get_file` 類のアクションで利用可能なリソース識別子）
- `url`：受信方向のプラットフォームの回路（アダプタがプラットフォームのイベントを変換する際に可能な限り記入し、モジュールが直接取得できるようにする）；送信方向は記入しなくてもよい
- `filename`：`file` セグメントのファイル名（送信方向はオプション、欠落時はアダプタが
  [送信方法規格 §2.1.3](send-method-spec.md) の推論順序に従って生成する；受信方向は**プラットフォームの元のファイル名を記入する**）

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.1.1 keyboard ボタン/インラインキーボードセグメント（跨プラットフォーム共通）

ボタン/インラインキーボードは、Telegram / 云湖 / QQBot / Kook / Discord 等の複数のプラットフォームで対応しており、**跨プラットフォーム共通概念**であるため、標準メッセージセグメント（プラットフォームのプレフィックスなし）として扱う。アダプタは標準セグメントを
プラットフォームのネイティブ構造に変換する。プラットフォームのネイティブ拡張セグメント（例：`telegram_inline_keyboard`）はそのまま透かす。

```json
{
  "type": "keyboard",
  "data": {
    "rows": [
      [
        {"label": "选项A", "type": "callback", "data": "vote:A"},
        {"label": "官网",   "type": "link",     "data": "https://example.com"}
      ]
    ]
  }
}
```

**フィールドの説明**：

| フィールド | 型 | 必須 | 説明 |
|------|------|------|------|
| `rows` | 二次元配列 | はい | 各サブ配列が一行のボタン |
| `rows[][].label` | str | はい | ボタンの表示テキスト |
| `rows[][].type` | str | はい | `callback`（クリックでデータを戻す）/ `link`（URL にジャンプ） |
| `rows[][].data` | str | はい | コールバックデータ（type=callback）またはジャンプアドレス（type=link） |
| `rows[][].*` | Any | いいえ | プラットフォーム特有のオプションフィールド（例：`web_app`、`menus`）、アダプタは能力に応じてマッピングまたは無視する |

**アダプタの変換参考**（完全なマッピングとインタラクティブコールバックイベントの標準は [跨プラットフォームインタラクティブコンポーネント標準](standardization-guide.md) を参照）：

| プラットフォーム | 標準セグメント → プラットフォームのネイティブ |
|------|------------------|
| Telegram | `inline_keyboard`：`[{text, callback_data \| url}]` |
| 云湖 | `buttons`：`[{label, action_type: 2=コールバック \| 1=ジャンプ, ...}]` |
| QQBot | `keyboard.content.rows`：`[{label, type: 2=コールバック \| 0=ジャンプ, data}]`（markdown メッセージ形式が必要） |
| Kook | カードの action-group モジュール |
| Discord | components：`action_row` + `buttons`（custom_id/url） |

### 4.2 プラットフォーム拡張メッセージセグメント

プラットフォーム固有のメッセージセグメントにはプラットフォームのプレフィックスを付ける：

```json
// 云湖 - フォーム
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "报名表"}}

// Telegram - ステッカー
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**拡張メッセージセグメントの要件**：
1. **data 内部のフィールドはプレフィックスを付けない**：`{"type": "yunhu_form", "data": {"form_id": "..."}}` ではなく `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2. **降格のソリューションを提供する**：モジュールが拡張メッセージセグメントを認識できない場合、アダプタは `alt_message` にテキストの代替を提供する
3. **ドキュメントの完全性**：各拡張メッセージセグメントは、`type`、`data` の構造、使用場面をアダプタのドキュメントで説明する必要がある

## 5. 未知イベントの処理

認識できないイベントタイプに対しては、警告イベントを生成する：
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
プラットフォーム前缀    フィールド名            完全フィールド名
────────    ───────          ──────────
yunhu       command           yunhu_command
telegram    sticker_file_id   telegram_sticker_file_id
onebot11    anonymous         onebot11_anonymous
email       subject           email_subject
```

**要件**：
- `platform` はアダプタ登録時のプラットフォーム名と完全一致する（大文字小文字を区別）
- `field_name` は `snake_case` 命名を使用
- `__` で始まる名前は禁止（Python が予約）
- 標準フィールド（例：`type`、`time`、`message` など）と同名の名前は禁止

### 6.2 メッセージセグメントタイプ命名

**ルール**：`{platform}_{segment_type}`

標準メッセージセグメントタイプ（`text`、`image`、`audio`、`video`、`mention`、`reply` など）は**プラットフォームのプレフィックスを付けない**。プラットフォーム固有のメッセージセグメントタイプのみプレフィックスを付ける。

### 6.3 原始データフィールド命名

以下のフィールド名は**予約フィールド**であり、すべてのアダプタは以下の要件を遵守する：

| 予約フィールド | 型 | 説明 |
|---------|------|------|
| `{platform}_raw` | `any` | プラットフォームの元のイベントデータの完全なコピー |
| `{platform}_raw_type` | `string` | プラットフォームの元のイベントタイプの識別子 |

**要件**：
- `{platform}_raw` は元のデータの深いコピー（参照ではなく）である必要がある
- `{platform}_raw_type` は文字列である必要がある（プラットフォームが数値型を使用している場合も文字列に変換する）
- これらのフィールドはすべてのイベントで**存在する必要がある**（取得できない場合は `null` と空文字列 `""` とする）

### 6.4 プラットフォーム特有のフィールドの例

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

**ネストされたフィールドの要件**：
- トップレベルのキーにはプラットフォームのプレフィックスを付ける
- ネストされた内部のフィールドには**プラットフォームのプレフィックスを付けない**
- ネストの深さは 3 層を超えないように推奨

### 6.6 `self` フィールドの拡張

`self` オブジェクトの標準の必須フィールド（`platform`、`user_id`）は §2.1 を参照。以下は ErisPulse が拡張したオプションフィールドである：

| フィールド | 型 | 説明 |
|------|------|------|
| `self.user_name` | `string` | ロボットのニックネーム |
| `self.avatar` | `string` | ロボットのアバターのURL |
| `self.account_id` | `string` | **限定拡張キー（アカウント名の代用）**：動的に注入されたアカウントが `user_id` を取得する前に、アカウント名/アカウント識別子で代用して記入し、イベントの所属を保証する。`self.user_id` が利用可能になったら優先的に記入する。フレームワークは `account_id or user_id` の口径で両方を互換的に扱う——アカウント名の代用時は `reply()` がアカウント名マッチングで正しいアカウントにルーティングされる |

> **実行時境界：イベントは常に `self.user_id` を保持する必要がある**（バインドが確立していない期間も含む）。接続層がバインドテーブルを戻し、connect meta が到着する前に受信したイベントは、ロボットの `user_id` が取得されていない場合はアカウント名で `self.account_id` を代用して注入する（フレームワークは `account_id or user_id` の口径で解析し、アカウント名はアカウント名マッチングルーターで正しいアカウントに戻る）。取得済みの場合は優先的に `self.user_id` を記入する——フレームワークはイベントの任意の段階で「このイベントはどのアカウントから来たのか」を判断できる必要がある。欠落した場合の結果は明確である：`event.reply()` にアカウントを注入せず、アカウントが指定されていない送信は最初の有効なアカウントに降格し、複数アカウントのアダプタでは「デフォルトアカウントから発信された」と表現される。

> **Bot 状態の追跡**：アダプタは `type: "meta"` イベントを送信してフレームワークに Bot の接続状態を通知する。サポートされる `detail_type`：`connect`（オンライン）、`heartbeat`（ハートビート）、`disconnect`（オフライン）。システムはこの中から `self` フィールドの Bot 元情報を自動抽出して状態を追跡する。また、通常のイベントの `self` フィールドも自動的に Bot を発見する。[アダプタシステム API - Bot 状態管理](../api-reference/adapter-system.md)を参照。

---

## 7. 会話タイプの拡張

ErisPulse は OneBot12 標準の `private`、`group` の上に以下の会話タイプを拡張している：

| タイプ | OneBot12 標準 | ErisPulse 拡張 | 説明 |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | 1対1のプライベートチャット |
| `group` | ✅ | — | グループチャット |
| `user` | — | ✅ | ユーザータイプ（Telegram など） |
| `channel` | — | ✅ | チャンネル（放送型） |
| `guild` | — | ✅ | サーバー/コミュニティ |
| `thread` | — | ✅ | トピック/サブチャンネル |

**アダプタのカスタムタイプ拡張**：

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# アダプタ起動時に登録
register_custom_type(
    receive_type="email",      # 受信イベントの detail_type
    send_type="email",         # 送信時の対象タイプ
    id_field="email_id",       # 対応する ID フィールド名
    platform="email"           # プラットフォーム識別子
)
```

**カスタムタイプの要件**：
- アダプタの `start()` 時に登録し、`shutdown()` 時に登録解除する
- `receive_type` は標準タイプと重複しない
- `id_field` は `{対象}_id` の命名パターンに従う

> 完全な会話タイプの定義とマッピング関係は [会話タイプ標準](session-types.md) を参照。

---

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

    # プラットフォーム拡張フィールドのアクセス - 方法2: ポイント式アクセス（Event 包装クラス）
    # event.yunhu_command

    # 原始データのアクセス
    raw_data = event.get("yunhu_raw")
    raw_type = event.get_raw_type()

    # プラットフォームの判断
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

### 8.3 最適実践

1. **標準フィールドを優先する**：拡張フィールドが必ず存在すると仮定しない
2. **プラットフォームの判断**：拡張フィールドの存在でプラットフォームを推論するのではなく、`event.get_platform()` を使用する
3. **優雅な降格**：拡張メッセージセグメントを処理できない場合は、`alt_message` をバックアップとして使用する
4. **プレフィックスをハードコードしない**：`platform` 変数を使用して動的に結合する

```python
# ✅ 推奨
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ 推奨しない
raw_data = event.get("yunhu_raw")
```

### 8.4 要求イベントの処理

モジュール開発者は `event.approve()` と `event.reject()` を使用して要求イベントを操作できる：

```python
from ErisPulse.Core.Event import request

# フレンドリクエスト：自動で承認
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # 承認
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"{user_name} のフレンドリクエストを承認しました")
    else:
        print(f"フレンドリクエストの承認に失敗しました: {result.get('message')}")

# グループリクエスト：条件に応じて決定
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # 拒否
    result = await event.reject(comment="暫定的に新しいグループに参加しません")
```

**アダプタ経由での直接操作**（イベントハンドラ外のシナリオに適用）：

```python
from ErisPulse import adapter

# request_id で直接操作
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# 特定の Bot アカウントで操作
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# コメントを付けて
await adapter.myplatform.Request("req_abc123").accept(comment="ようこそ")
```

---

## 9. notice / request イベントの会話タイプ推論

### 9.1 問題の背景

notice イベントと request イベントの `detail_type` は**意味のサブタイプ**（例：`group_member_increase`、`friend_increase`）であり、会話タイプ（例：`group`、`private`）ではない。

```
type        detail_type                  含義            会話タイプ
────        ───────────                  ────            ────────
message     group                        グループメッセージ         group（detail_type が会話タイプ）
message     private                      プライベートメッセージ         private（detail_type が会話タイプ）
notice      group_member_increase        グループメンバー増加       group（group_id から推論）
notice      friend_increase              フレンド増加         private（user_id から推論）
request     friend                       フレンドリクエスト         private（user_id から推論）
request     group                        グループリクエスト           group（detail_type が会話タイプ）
```

### 9.2 推論ルール

`infer_receive_type()` の推論順序：

1. `detail_type` が既知の会話タイプ（`private`/`group`/`channel`/`guild`/`thread`/`user`）の場合、そのまま使用
2. `detail_type` がカスタム会話タイプの場合、そのまま使用
3. それ以外（notice/request の意味のサブタイプ）の場合、ID フィールドから推論：
   - `group_id` があれば → `"group"`
   - `channel_id` があれば → `"channel"`
   - `guild_id` があれば → `"guild"`
   - `thread_id` があれば → `"thread"`
   - `user_id` があれば → `"private"`

### 9.3 `event.reply()` の送信先推論

notice/request イベントにおける `event.reply()` の送信先は会話タイプの推論で決定される：

- グループ通知イベント（`group_id` がある）→ グループに返信
- フレンド通知イベント（`user_id` だけがある）→ ユーザーのプライベートチャットに返信

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() はグループ（group/group_789）に送信
    await event.reply("ようこそ！")

    # 管理者に通知したい場合（プライベートチャット）、送信先を明示的に指定する：
    await adapter.Send.To("user", "admin_id").Text(f"新メンバー {user_id} が {group_id} に参加しました")
```

### 9.4 アダプタ開発の推奨

notice/request イベントに正しい ID フィールドを含めるようにする：

| detail_type | 必須の ID フィールド | 推論される会話タイプ |
|-------------|-------------------|---------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend`（リクエスト） | `user_id` | `private` |
| `group`（リクエスト） | `group_id` | `group` |

---

## 10. 関連ドキュメント

**変換器を実装する際に併せて参照**：
- [会話タイプ標準](session-types.md) - 会話タイプの定義とマッピング関係
- [API レスポンス標準](api-response.md) - アダプタ API レスポンス形式の標準

**同じアダプタの送信側**：
- [送信方法規格](send-method-spec.md) - Send クラスのメソッド命名、パラメータ規格および逆変換要件
- [API アクション標準](api-action-spec.md) - OneBot12 標準 API アクションの統一インターフェース

**各プラットフォームの既知の拡張イベントとメッセージセグメントを確認**：
- [各プラットフォームの特徴ドキュメント](../platform-guide/README.md) - 各プラットフォームの特徴や既知の拡張イベント、メッセージセグメントなどを確認できるドキュメントにアクセスできます。