# Kookプラットフォーム特性ドキュメント

KookAdapter は、Kook（旧称开黑啦）Bot WebSocket プロトコルを基に構築されたアダプターで、Kook のすべての機能モジュールを統合し、統一されたイベント処理とメッセージ操作インターフェースを提供します。

---

## 文書情報

- 対応モジュールバージョン: 0.1.0
- メンテナ: ShanFish

## 基本情報

- プラットフォーム紹介：Kook（旧称开黑啦）は、テキスト、音声、ビデオ通信をサポートするコミュニティプラットフォームであり、完全な Bot 開発インターフェースを提供します
- アダプター名：KookAdapter
- 接続方式：WebSocket ロング接続（Kook ゲートウェイ経由）
- 認証方式：Bot Token ベースの認証
- チェーン構文修飾のサポート：`.Reply()`、`.At()`、`.AtAll()` などのチェーン構文修飾メソッドをサポート
- OneBot12互換性：OneBot12 形式メッセージの送信をサポート

## 設定説明

```toml
# config.toml
[KookAdapter]
token = "YOUR_BOT_TOKEN"     # Kook Bot Token（必須、形式: Bot xxx/xxx）
bot_id = ""                   # Bot ユーザーID（任意、未入力の場合は token から解析）
compress = true               # WebSocket 圧縮を有効にするかどうか（任意、デフォルトは true）
```

**設定項目の説明：**
- `token`：Kook Bot の Token（必須）。[Kook Developer Center](https://developer.kookapp.cn) から取得、形式は `Bot xxx/xxx`
- `bot_id`：Bot のユーザーID（任意）。未入力の場合、アダプターは token から自動的に解析を試みます。正確性を確保するために手動で入力することを推奨します
- `compress`：WebSocket データ圧縮を有効にするかどうか（任意、デフォルトは `true`）。有効にすると zlib を使用してデータを展開します

**API環境：**
- Kook API ベースアドレス：`https://www.kookapp.cn/api/v3`
- WebSocket ゲートウェイは API を通じて動的に取得：`POST /gateway/index`

## サポートされているメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実装されています。例：

```python
from ErisPulse.Core import adapter
kook = adapter.get("kook")

await kook.Send.To("group", channel_id).Text("Hello World!")
```

サポートされている送信タイプは以下の通りです：
- `.Text(text: str)`：テキストメッセージを送信します。
- `.Image(file: bytes | str)`：画像メッセージを送信します。ファイルパス、URL、バイナリデータをサポート。
- `.Video(file: bytes | str)`：ビデオメッセージを送信します。ファイルパス、URL、バイナリデータをサポート。
- `.File(file: bytes | str, filename: str = None)`：ファイルメッセージを送信します。ファイルパス、URL、バイナリデータをサポート。
- `.Voice(file: bytes | str)`：音声メッセージを送信します。ファイルパス、URL、バイナリデータをサポート。
- `.Markdown(text: str)`：KMarkdown形式メッセージを送信します。
- `.Card(card_data: dict)`：カードメッセージ（CardMessage）を送信します。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12 形式メッセージを送信します。

### チェーン構文修飾メソッド（組み合わせ可能）

チェーン構文修飾メソッドは `self` を返し、チェーン呼び出しをサポートします。必ず最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定されたメッセージへの返信（引用）。
- `.At(user_id: str)`：指定したユーザーにメンションします。複数回呼び出すことで複数のユーザーにメンションできます。
- `.AtAll()`：すべてのユーザーにメンションします。

### チェーン構文の使用例

```python
# 基本的な送信
await kook.Send.To("group", channel_id).Text("Hello")

# メッセージへの返信
await kook.Send.To("group", channel_id).Reply(msg_id).Text("返信メッセージ")

# ユーザーへのメンション
await kook.Send.To("group", channel_id).At("user_id").Text("こんにちは")

# 複数ユーザーへのメンション
await kook.Send.To("group", channel_id).At("user1").At("user2").Text("複数ユーザー@")

# 全体へのメンション
await kook.Send.To("group", channel_id).AtAll().Text("お知らせ")

# 組み合わせた使用例
await kook.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("複合メッセージ")
```

### OneBot12メッセージサポート

アダプターは OneBot12 形式のメッセージを送信することをサポートし、クロスプラットフォームメッセージ互換性を容易にします：

```python
# OneBot12 形式メッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)

# チェーン構文修飾と組み合わせ
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await kook.Send.To("group", channel_id).Reply(msg_id).Raw_ob12(ob12_msg)

# Raw_ob12 で mention と reply メッセージセグメントを使用
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
    {"type": "reply", "data": {"message_id": "msg_id"}}
]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

### 追加操作メソッド

メッセージ送信に加え、Kookアダプターは以下の操作もサポートします：

```python
# メッセージの編集（KMarkdown type=9 と CardMessage type=10 のみサポート）
await kook.Send.To("group", channel_id).Edit(msg_id, "**更新後の内容**")

# メッセージの撤回
await kook.Send.To("group", channel_id).Recall(msg_id)

# ファイルのアップロード（ファイルURLを取得）
result = await kook.Send.Upload("C:/path/to/file.jpg")
file_url = result["data"]["url"]
```

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、直接 await して送信結果を取得できます。戻り値は ErisPulse アダプターの標準化された戻り値規則に準拠します：

```python
{
    "status": "ok",           // 実行ステータス: "ok" または "failed"
    "retcode": 0,             // 戻り値コード（Kook API の code）
    "data": {...},            // レスポンスデータ
    "message_id": "xxx",      // メッセージID
    "message": "",            // エラーメッセージ
    "kook_raw": {...}         // 元のレスポンスデータ
}
```

### エラーコードの説明

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 40100 | Token が無効、または提供されていない |
| 40101 | Token が期限切れ |
| 40102 | Token と Bot が一致しない |
| 40103 | 権限が不足している |
| 40000 | パラメータエラー |
| 40400 | 対象が存在しない |
| 40300 | 操作する権限がない |
| 50000 | サーバー内部エラー |
| -1 | アダプター内部エラー |

## 固有のイベントタイプ

このプラットフォームの機能を使用するには、`platform=="kook"` を使用して検出する必要があります

### 主な違い

1. **チャンネルシステム**：Kook はサーバー（Guild）とチャンネル（Channel）の二層構造を使用しており、チャンネルがメッセージの基本送信ターゲットとなります
2. **メッセージタイプ**：Kook はテキスト(1)、画像(2)、ビデオ(3)、ファイル(4)、音声(8)、KMarkdown(9)、カードメッセージ(10)など、さまざまなメッセージタイプをサポートします
3. **プライベートメッセージシステム**：Kook はチャンネルメッセージとプライベートメッセージを区別し、異なる API エンドポイントを使用します
4. **メッセージシーケンス**：Kook WebSocket は `sn` シーケンス番号を使用してメッセージの順序性を保証し、メッセージの一時保存と順序を考慮した再アレンジをサポートします
5. **メッセージの編集と撤回**：送信済みメッセージの編集（KMarkdown および CardMessage のみ）とメッセージの撤回をサポートします

### 拡張フィールド

- すべての固有のフィールドは `kook_` プレフィックスで識別されます
- 原始データは `kook_raw` フィールドに保持されます
- `kook_raw_type` は元の Kook メッセージタイプ番号（例：`1` はテキスト、`255` は通知イベント）を識別します

### 特殊フィールドの例

```python
# チャンネルテキストメッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ユーザーID",
  "group_id": "チャンネルID",
  "channel_id": "チャンネルID",
  "message_id": "メッセージID",
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# 画像付きメッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ユーザーID",
  "group_id": "チャンネルID",
  "channel_id": "チャンネルID",
  "message_id": "メッセージID",
  "kook_raw": {...},
  "kook_raw_type": "2",
  "message": [
    {"type": "image", "data": {"file": "画像URL", "url": "画像URL"}}
  ],
  "alt_message": "画像内容"
}

# KMarkdownメッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ユーザーID",
  "group_id": "チャンネルID",
  "message_id": "メッセージID",
  "kook_raw": {...},
  "kook_raw_type": "9",
  "message": [
    {"type": "text", "data": {"text": "解析済みテキスト"}}
  ]
}

# カードメッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ユーザーID",
  "group_id": "チャンネルID",
  "message_id": "メッセージID",
  "kook_raw": {...},
  "kook_raw_type": "10",
  "message": [
    {"type": "json", "data": {"data": "カードJSON内容"}}
  ]
}

# プライベートメッセージ
{
  "type": "message",
  "detail_type": "private",
  "user_id": "ユーザーID",
  "message_id": "メッセージID",
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "プライベートメッセージ内容"}}
  ]
}
```

### メッセージセグメントタイプ

Kook のメッセージタイプは、`type` フィールドに基づいて対応するメッセージセグメントに自動的に変換されます：

| Kook type | 変換タイプ | 説明 |
|---|---|---|
| 1 | `text` | テキストメッセージ |
| 2 | `image` | 画像メッセージ |
| 3 | `video` | ビデオメッセージ |
| 4 | `file` | ファイルメッセージ |
| 8 | `record` | 音声メッセージ |
| 9 | `text` | KMarkdownメッセージ（純テキストコンテンツを抽出） |
| 10 | `json` | カードメッセージ（元のJSON） |

メッセージセグメント構造の例：
```json
{
  "type": "image",
  "data": {
    "file": "画像URL",
    "url": "画像URL"
  }
}
```

### Mentionメッセージセグメント

メッセージに@情報が含まれている場合、メッセージセグメントの前に `mention` メッセージセグメントが挿入されます：

```json
{
  "type": "mention",
  "data": {
    "user_id": "メンションされたユーザーID"
  }
}
```

### mention_allメッセージセグメント

メッセージが@全体の場合、`mention_all` メッセージセグメントが挿入されます：

```json
{
  "type": "mention_all",
  "data": {}
}
```

## WebSocket接続

### 接続フロー

1. Bot Token を使用して `POST /gateway/index` を呼び出し、WebSocket ゲートウェイアドレスを取得します
2. WebSocket ゲートウェイに接続します
3. HELLO（s=1）シグナルを受信し、接続状態を検証します
4. ハートビートループを開始します（PING、s=2、30秒ごと）
5. メッセージイベント（s=0）を受信し、`sn` シーケンス番号を使用して順序性を保証します
6. ハートビート応答 PONG（s=3）を受信します

### シグナルタイプ

| シグナル | s値 | 説明 |
|------|-----|------|
| HELLO | 1 | サーバーの歓迎シグナル、接続成功後に受信 |
| PING | 2 | クライアントのハートビート、30秒ごとに送信、現在の sn を持ちます |
| PONG | 3 | ハートビート応答 |
| RESUME | 4 | 接続復帰シグナル、sn を持ち会話を復元します |
| RECONNECT | 5 | サーバーからの再接続要求、ゲートウェイの再取得が必要 |
| RESUME_ACK | 6 | RESUME 成功応答 |

### 接続切断時の再接続

- 接続が異常で切断された場合、アダプターは自動的に再接続を試行します
- 前に `sn > 0` が存在する場合、まず RESUME（s=4）を使用して接続を復帰しようとします
- RESUME に失敗した場合、sn とメッセージキューをリセットし、新しい接続を再開します（HELLO フロー）
- RECONNECT（s=5）シグナルを受信した場合、ステータスをクリアして再接続します

### メッセージシーケンス番号機構

Kook WebSocket は `sn`（増分シーケンス番号）を使用してメッセージの順序性を保証します：

- 各メッセージイベント（s=0）を受信すると、sn が増加します
- 受信したメッセージの sn が連続していない場合、一時保存モードに入ります
- 一時保存領域内のメッセージは sn で並べ替えられ、不足しているメッセージが到着したら順序通りに処理されます
- 一時保存領域がクリアされると、一時保存モードから自動的に退出します

## 使用例

### チャンネルメッセージの処理

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

kook = sdk.adapter.get("kook")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await kook.Send.To("group", channel_id).Text("Hello!")
```

### プライベートメッセージの処理

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "private":
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await kook.Send.To("user", user_id).Text(f"あなたは言いました: {text}")
```

### 通知イベントの処理（絵文字反応など）

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "added_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"ユーザー {user_id} がメッセージ {msg_id} に絵文字反応を追加しました")

    elif sub_type == "deleted_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"ユーザー {user_id} がメッセージ {msg_id} の絵文字反応を削除しました")
```

### メディアメッセージの送信

```python
# 画像の送信（URL）
await kook.Send.To("group", channel_id).Image("https://example.com/image.png")

# 画像の送信（バイナリ）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await kook.Send.To("group", channel_id).Image(image_bytes)

# ビデオの送信
await kook.Send.To("group", channel_id).Video("https://example.com/video.mp4")

# ファイルの送信
await kook.Send.To("group", channel_id).File("https://example.com/file.pdf", filename="document.pdf")

# 音声の送信
await kook.Send.To("group", channel_id).Voice("https://example.com/voice.mp3")
```

### KMarkdownとカードメッセージの送信

```python
# KMarkdown
await kook.Send.To("group", channel_id).Markdown("**太字** *斜体* [リンク](https://example.com)")

# カードメッセージ
card = {
    "type": "card",
    "theme": "primary",
    "size": "lg",
    "modules": [
        {"type": "header", "text": {"type": "plain-text", "content": "タイトル"}},
        {"type": "section", "text": {"type": "kmarkdown", "content": "内容"}}
    ]
}
await kook.Send.To("group", channel_id).Card(card)
```

### メッセージの編集と撤回

```python
# メッセージの送信
result = await kook.Send.To("group", channel_id).Markdown("**元の内容**")
msg_id = result["data"]["msg_id"]

# メッセージの編集（KMarkdown および CardMessage のみサポート）
await kook.Send.To("group", channel_id).Edit(msg_id, "**更新後の内容**")

# メッセージの撤回
await kook.Send.To("group", channel_id).Recall(msg_id)
```

### プライベートメッセージの編集と削除通知の処理

```python
@notice.on_notice()
async def handle_private_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "updated_private_message":
        msg_id = event.get("message_id")
        content = event.get("content")
        print(f"プライベートメッセージが更新されました: {msg_id}, 新しい内容: {content}")

    elif sub_type == "deleted_private_message":
        msg_id = event.get("message_id")
        print(f"プライベートメッセージが削除されました: {msg_id}")