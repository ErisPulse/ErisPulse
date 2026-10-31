# アダプター標準化変換仕様

> [!TIP]
> **この文書を読むべきとき**：アダプターでプラットフォームネイティブイベントを OneBot12 標準イベントに変換する際——必須フィールド、メッセージセグメント構造、拡張フィールド命名（`{platform}_` プレフィックス）、セッションタイプ推定を確認するときに、この文書を参照してください。不要な場合は読み飛ばしてください。

## 1. コア原則
1. 厳格な互換性：すべての標準フィールドは OneBot12 仕様に完全に準拠しなければならない
2. 明確な拡張：プラットフォーム固有機能には {platform}_ プレフィックスを追加しなければならない（例：yunhu_form）
3. データの完全性：元のイベントデータは {platform}_raw フィールドに保持しなければならず、元のイベントタイプは {platform}_raw_type フィールドに保持しなければならない
4. 時間の統一：すべてのタイムスタンプは 10 桁の Unix タイムスタンプ（秒単位）に変換しなければならない
5. プラットフォームの統一：platform 項目の命名は、ErisPulse に登録した名前/別名と一致しなければならない

## 2. 標準フィールド要件

### 2.1 必須フィールド
| フィールド | 型 | 説明 |
|------|------|------|
| id | string | イベントの一意識別子 |
| time | integer | Unix タイムスタンプ（秒単位） |
| type | string | イベントタイプ |
| detail_type | string | イベントの詳細タイプ（詳細は[セッションタイプ標準](session-types.md)を参照） |
| platform | string | プラットフォーム名 |
| self | object | ボット自身の情報 |
| self.platform | string | プラットフォーム名 |
| self.user_id | string | ボットのユーザー ID |

**detail_type 仕様**：
- ErisPulse 標準セッションタイプを使用しなければならない（詳細は [セッションタイプ標準](session-types.md) を参照）
- サポートされるタイプ：`private`、`group`、`user`、`channel`、`guild`、`thread`
- アダプターは、プラットフォームネイティブタイプを標準タイプへマッピングする責任を負う

### 2.2 メッセージイベントフィールド
| フィールド | 型 | 説明 |
|------|------|------|
| message | array | メッセージセグメント配列 |
| alt_message | string | メッセージセグメントの代替テキスト |
| user_id | string | ユーザー ID |
| user_nickname | string | ユーザーニックネーム（任意） |

### 2.3 通知イベントフィールド
| フィールド | 型 | 説明 |
|------|------|------|
| user_id | string | ユーザー ID |
| user_nickname | string | ユーザーニックネーム（任意） |
| operator_id | string | 操作者 ID（任意） |

### 2.4 リクエストイベントフィールド
| フィールド | 型 | 説明 |
|------|------|------|
| user_id | string | ユーザー ID |
| user_nickname | string | ユーザーニックネーム（任意） |
| comment | string | リクエストの添えメッセージ（任意） |
| request_id | string | リクエスト識別子（**強く推奨**、リクエストの承認/拒否操作に使用） |

**`request_id` フィールドの説明**：
- `request_id` はリクエストイベントの一意の操作識別子であり、`HandleRequest` DSL による承認/拒否操作の実行に使用される
- アダプターはリクエストイベントの変換時に、プラットフォームネイティブのリクエスト識別子をこのフィールドにマッピングすべきである
- プラットフォーム自体にリクエスト ID がない場合、アダプターは一意の識別子を生成すべきである（例：タイムスタンプ＋ユーザー ID に基づくハッシュ）
- `request_id` が欠落している場合、`event.approve()` / `event.reject()` は `ValueError` をスローする

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
        "text": "抽選 スーパー大賞"
      }
    }
  ],
  "alt_message": "抽選 スーパー大賞",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽選",
    "args": "スーパー大賞"
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
  "comment": "フレンド申請をお願いします",
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. メッセージセグメント標準

### 4.1 標準メッセージセグメント

標準メッセージセグメントにプラットフォームプレフィックスは**不要**です。

| タイプ | 説明 | data フィールド |
|------|------|----------|
| `text` | プレーンテキスト | `text: str` |
| `image` | 画像 | `file`, `url: str` |
| `audio` | 音声 | `file`, `url: str` |
| `video` | 動画 | `file`, `url: str` |
| `file` | ファイル | `file`, `url: str`, `filename: str` |
| `mention` | @ユーザー | `user_id: str`, `user_name: str` |
| `reply` | 返信 | `message_id: str` |
| `face` | 絵文字 | `id: str` |
| `location` | 位置情報 | `latitude: float`, `longitude: float` |
| `keyboard` | ボタン/インラインキーボード | `rows: list[list[button]]`（4.1.1 を参照） |

**メディアセグメントの `file` フィールド形式**（送信方向、`image` / `audio` / `video` / `file` 共通）：

| 形態 | 例 | アダプター要件 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/a.png` | **必須**で受け付ける |
| ローカルファイルパス | `/tmp/a.png`、`C:\tmp\a.png` | **必須**で受け付ける |
| バイナリデータ | `bytes` | **必須**で受け付ける |
| `file://` URI / Base64 / Data URI | `file:///tmp/a.png`、`data:image/png;base64,...` | **推奨**で受け付ける |

> メディア送信プロトコルの全体（形態判定順序、ファイル名導出、能力ダウングレードの段階）については
> [送信メソッド仕様 §2.1](send-method-spec.md#21-媒体消息发送协议image--voice--video--file) を参照してください。

**フィールドの方向セマンティクス**：

- `file`：**送信方向**のコンテンツソース（上述の形態）；**受信方向**では、アダプターがプラットフォームから取得可能な形態を記入する
  （通常はダウンロード可能な URL、または `get_file` 系アクションで利用可能なリソース識別子）
- `url`：受信方向のプラットフォーム返却リンク（アダプターはプラットフォームイベントの変換時に可能な限り記入し、モジュールが直接利用できるようにする）；送信方向では省略可能
- `filename`：`file` セグメントのファイル名（送信方向では任意、省略時はアダプターが
  [送信メソッド仕様 §2.1.3](send-method-spec.md) の導出順序に従って生成；受信方向ではプラットフォームの元のファイル名を記入することが**推奨**される）

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.1.1 keyboard ボタン/インラインキーボードセグメント（クロスプラットフォーム共通）

ボタン/インラインキーボードは複数のプラットフォーム（Telegram / 云湖 / QQBot / Kook / Discord など）に対応機能が存在し、**クロスプラットフォーム共通の概念**であるため、標準メッセージセグメント（プラットフォームプレフィックスなし）として扱われます。アダプターは標準セグメントをプラットフォームネイティブ構造に変換してください。プラットフォームネイティブの拡張セグメント（例：`telegram_inline_keyboard`）は引き続きそのまま透過します。

```json
{
  "type": "keyboard",
  "data": {
    "rows": [
      [
        {"label": "選択肢A", "type": "callback", "data": "vote:A"},
        {"label": "公式サイト",   "type": "link",     "data": "https://example.com"}
      ]
    ]
  }
}
```

**フィールドの説明：**

| フィールド | 型 | 必須 | 説明 |
|------|------|------|------|
| `rows` | 二次元配列 | はい | 各サブ配列が 1 行のボタンに対応 |
| `rows[][].label` | str | はい | ボタンの表示テキスト |
| `rows[][].type` | str | はい | `callback`（クリックでデータを返送）/ `link`（URL へジャンプ） |
| `rows[][].data` | str | はい | コールバックデータ（type=callback）またはジャンプ先アドレス（type=link） |
| `rows[][].*` | Any | いいえ | プラットフォーム固有の任意フィールド（例：`web_app`、`menus`）。アダプターは能力に応じてマッピングまたは無視する |

**アダプター変換リファレンス**（完全なマッピングとインタラクションコールバックイベント標準については [クロスプラットフォームインタラクションコンポーネント標準](standardization-guide.md) を参照）：

| プラットフォーム | 標準セグメント → プラットフォームネイティブ |
|------|------------------|
| Telegram | `inline_keyboard`：`[{text, callback_data \| url}]` |
| 云湖 | `buttons`：`[{label, action_type: 2=コールバック \| 1=ジャンプ, ...}]` |
| QQBot | `keyboard.content.rows`：`[{label, type: 2=コールバック \| 0=ジャンプ, data}]`（markdown タイプのメッセージが必要） |
| Kook | カードの action-group モジュール |
| Discord | components：`action_row` + `buttons`（custom_id/url） |

### 4.2 プラットフォーム拡張メッセージセグメント

プラットフォーム固有のメッセージセグメントにはプラットフォームプレフィックスを追加する必要があります：

```json
// 云湖 - フォーム
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "申込フォーム"}}

// Telegram - スタンプ
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**拡張メッセージセグメントの要件**：
1. **data 内部のフィールドにはプレフィックスを付けない**：`{"type": "yunhu_form", "data": {"form_id": "..."}}` とするべきであり、`{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}` としてはならない
2. **フォールバック手段を提供する**：モジュールは拡張メッセージセグメントを認識できない可能性があるため、アダプターは `alt_message` にテキストによる代替を提供すべきである
3. **ドキュメントの完備**：各拡張メッセージセグメントについて、`type`、`data` の構造および使用シーンをアダプターのドキュメントで説明しなければならない

## 5. 不明なイベントの処理

識別できないイベントタイプについては、警告イベントを生成すべきです：
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

## 6. 拡張命名規約

### 6.1 フィールド命名

**ルール**：`{platform}_{field_name}`

```
プラットフォームプレフィックス   フィールド名         完全なフィールド名
──────────                   ───────            ──────────
yunhu       command           yunhu_command
telegram    sticker_file_id   telegram_sticker_file_id
onebot11    anonymous         onebot11_anonymous
email       subject           email_subject
```

**要件**：
- `platform` はアダプター登録時のプラットフォーム名と完全に一致しなければならない（大文字小文字を区別）
- `field_name` は `snake_case` 命名を使用する
- ダブルアンダースコア `__` で始まる名前は禁止（Python の予約）
- 標準フィールドと同名にすることは禁止（例：`type`、`time`、`message` など）

### 6.2 メッセージセグメントタイプ命名

**ルール**：`{platform}_{segment_type}`

標準メッセージセグメントタイプ（`text`、`image`、`audio`、`video`、`mention`、`reply` など）にプラットフォームプレフィックスを追加しては**なりません**。プラットフォーム固有のメッセージセグメントタイプのみがプレフィックスを追加する必要があります。

### 6.3 生データフィールド命名

以下のフィールド名は**予約フィールド**であり、すべてのアダプターが従わなければなりません：

| 予約フィールド | 型 | 説明 |
|---------|------|------|
| `{platform}_raw` | `any` | プラットフォーム元イベントデータの完全なコピー |
| `{platform}_raw_type` | `string` | プラットフォーム元イベントタイプの識別子 |

**要件**：
- `{platform}_raw` は元データのディープコピーでなければならず、参照であってはならない
- `{platform}_raw_type` は文字列でなければならず、プラットフォームが数値型を使用している場合でも文字列に変換すること
- これら 2 つのフィールドはすべてのイベントに**存在しなければならない**（取得できない場合は `null` と空文字列 `""`）

### 6.4 プラットフォーム固有フィールドの例

```json
{
  "yunhu_command": {
    "name": "抽選",
    "args": "スーパー大賞"
  },
  "yunhu_form": {
    "form_id": "123456"
  },
  "telegram_sticker": {
    "file_id": "CAACAgIAAxkBAA..."
  }
}
```

### 6.5 ネストした拡張フィールド

拡張フィールドは単純な値でも、ネストしたオブジェクトでもかまいません：

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
- トップレベルのキーにはプラットフォームプレフィックスを付けなければならない
- ネストした内部フィールドにはプラットフォームプレフィックスを**追加しない**
- ネストの深さは 3 層を超えないことを推奨

### 6.6 `self` フィールドの拡張

`self` オブジェクトの標準必須フィールド（`platform`、`user_id`）は §2.1 を参照してください。以下は ErisPulse が拡張した任意フィールドです：

| フィールド | 型 | 説明 |
|------|------|------|
| `self.user_name` | `string` | ボットのニックネーム |
| `self.avatar` | `string` | ボットのアバター URL |
| `self.account_id` | `string` | マルチアカウントモードにおけるアカウント識別子 |

> **Bot 状態トラッキング**：アダプターは `type: "meta"` イベントを送信することで、フレームワークに Bot の接続状態を通知します。サポートされる `detail_type`：`connect`（オンライン）、`heartbeat`（ハートビート）、`disconnect`（オフライン）。システムはそこから `self` フィールドの Bot メタ情報を自動的に抽出し、状態をトラッキングします。また、通常のイベント内の `self` フィールドからも Bot が自動的に検出されます。詳細は [アダプターシステム API - Bot 状態管理](../api-reference/adapter-system.md) を参照してください。

---

## 7. セッションタイプの拡張

ErisPulse は OneBot12 標準の `private`、`group` をベースに、以下のセッションタイプを拡張しました：

| タイプ | OneBot12 標準 | ErisPulse 拡張 | 説明 |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | 1対1のプライベートチャット |
| `group` | ✅ | — | グループチャット |
| `user` | — | ✅ | ユーザータイプ（Telegram など） |
| `channel` | — | ✅ | チャンネル（ブロードキャスト型） |
| `guild` | — | ✅ | サーバー/コミュニティ |
| `thread` | — | ✅ | トピック/サブチャンネル |

**アダプターのカスタムタイプ拡張**：

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# アダプター起動時に登録する
register_custom_type(
    receive_type="email",      # 受信イベントにおける detail_type
    send_type="email",         # 送信時のターゲットタイプ
    id_field="email_id",       # 対応する ID フィールド名
    platform="email"           # プラットフォーム識別子
)
```

**カスタムタイプの要件**：
- アダプターの `start()` 時に登録し、`shutdown()` 時に登録解除しなければならない
- `receive_type` は標準タイプと同名にすべきではない
- `id_field` は `{ターゲット}_id` の命名パターンに従うべきである

> セッションタイプの完全な定義とマッピング関係については [セッションタイプ標準](session-types.md) を参照してください。

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

    # プラットフォーム拡張フィールドへのアクセス - 方法2：ドットアクセス（Event ラッパークラス）
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

1. **標準フィールドを優先して使用する**：拡張フィールドが必ず存在すると仮定しないこと
2. **プラットフォーム判定**：`event.get_platform()` によってプラットフォームを判定し、拡張フィールドの存在有無から推測しないこと
3. **グレースフルデグラデーション**：拡張メッセージセグメントを処理できない場合は、`alt_message` をフォールバックとして使用すること
4. **プレフィックスをハードコードしない**：`platform` 変数を使って動的に連結すること

```python
# ✅ 推奨
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ 非推奨
raw_data = event.get("yunhu_raw")
```

### 8.4 リクエストイベントの処理

モジュール開発者は `event.approve()` および `event.reject()` を通じてリクエストイベントに対する操作を行うことができます：

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

# グループ招待：条件に応じて判断
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # リクエストを拒否
    result = await event.reject(comment="当分の間、新しいグループに参加しません")
```

**アダプターを通じた直接操作**（イベントハンドラー以外のシーンに適用）：

```python
from ErisPulse import adapter

# request_id による直接操作
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# Bot アカウントを指定して操作
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# 備考を添える
await adapter.myplatform.Request("req_abc123").accept(comment="ようこそ")
```

---

## 9. notice / request イベントのセッションタイプ推定

### 9.1 問題の背景

notice イベントと request イベントの `detail_type` は**セマンティックサブタイプ**（例：`group_member_increase`、`friend_increase`）であり、セッションタイプ（例：`group`、`private`）ではありません。

```
type        detail_type                  意味                セッションタイプ
────        ───────────                  ────                ────────
message     group                        グループメッセージ     group（detail_type がそのままセッションタイプ）
message     private                      プライベートメッセージ  private（detail_type がそのままセッションタイプ）
notice      group_member_increase        グループメンバー増加   group（group_id からの推定が必要）
notice      friend_increase              フレンド増加          private（user_id からの推定が必要）
request     friend                       フレンドリクエスト     private（user_id からの推定が必要）
request     group                        グループリクエスト     group（detail_type がそのままセッションタイプ）
```

### 9.2 推定ルール

`infer_receive_type()` の推定順序：

1. `detail_type` が既知のセッションタイプ（`private`/`group`/`channel`/`guild`/`thread`/`user`）である場合は、そのまま使用する
2. `detail_type` がカスタムセッションタイプである場合は、そのまま使用する
3. それ以外の場合（notice/request のセマンティックサブタイプ）、ID フィールドに基づいて推定する：
   - `group_id` がある → `"group"`
   - `channel_id` がある → `"channel"`
   - `guild_id` がある → `"guild"`
   - `thread_id` がある → `"thread"`
   - `user_id` がある → `"private"`

### 9.3 `event.reply()` のターゲット推定

notice/request イベントにおける `event.reply()` の送信ターゲットは、セッションタイプの推定によって決まります：

- グループ通知イベント（`group_id` を含む）→ **グループ**に返信
- フレンド通知イベント（`user_id` のみを含む）→ **ユーザーのプライベートチャット**に返信

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() はグループに送信（group/group_789）
    await event.reply("グループへようこそ！")

    # 管理者に通知する場合（プライベートチャット）、ターゲットを明示的に指定：
    await adapter.Send.To("user", "admin_id").Text(f"新しいメンバー {user_id} が {group_id} に参加しました")
```

### 9.4 アダプター開発の推奨事項

notice/request イベントに正しい ID フィールドが含まれるようにしてください：

| detail_type | 含まれるべき ID フィールド | 推定されるセッションタイプ |
|-------------|-------------------|---------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend`（リクエスト） | `user_id` | `private` |
| `group`（リクエスト） | `group_id` | `group` |

---

## 10. 関連ドキュメント

**コンバーター実装時に併せて参照**：
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング関係
- [API レスポンス標準](api-response.md) - アダプター API レスポンス形式の標準

**同一アダプターの送信側**：
- [送信メソッド仕様](send-method-spec.md) - Send クラスのメソッド命名、パラメータ仕様および逆変換の要件
- [API アクション標準](api-action-spec.md) - OneBot12 標準 API アクションの統一インターフェース

**各プラットフォームの既知の拡張イベントとメッセージセグメントの確認**：
- [各プラットフォーム特性ドキュメント](../platform-guide/README.md) - このドキュメントにアクセスすることで、各プラットフォームの特性や既知の拡張イベント、メッセージセグメントなどを知ることができます。