# ErisPulse セッションタイプ標準

このドキュメントでは、ErisPulse がサポートするセッションタイプ標準を定義します。これには、受信イベントタイプと送信ターゲットタイプが含まれます。

言語切り替え行（各言語名が `` | `` で区切られている行）がドキュメントに含まれる場合、上記のルール 8 に厳密に従ってください。``[**ラベル**](ファイル)`` というような間違った形式を出力しないでください。

## 1. 核心概念

### 1.1 受信タイプ && 送信タイプ

ErisPulse は、2 種類の会話タイプを区別します：

- **受信タイプ（Receive Type）**：イベントの `detail_type` フィールドで使用される、受信用のタイプ
- **送信タイプ（Send Type）**：メッセージを送信する際の `Send.To()` メソッドの対象タイプ

### 1.2 タイプのマッピング関係

```
受信タイプ (detail_type)     送信タイプ (Send.To)
─────────────────        ────────────────
private                 →        user
group                   →        group
channel                 →        channel
guild                   →        guild
thread                  →        thread
user                    →        user
```

**重要な点**：
- `private` は受信時のタイプであり、送信時には `user` を使用する必要があります
- `group`、`channel`、`guild`、`thread` は受信時と送信時のタイプが同じです
- システムは自動的にタイプ変換を行います。手動での処理は不要です（つまり、受信したタイプをそのまま送信に使用できます）。実際には、これらのタイプ変換について心配する必要はありません。Event のラッパークラスが存在するため、`event.reply()` メソッドを使用することで、タイプ変換を意識することなく送信できます。

## 2. 標準会話タイプ

### 2.1 OneBot12 標準タイプ

#### private
- **受信タイプ**: `private`
- **送信タイプ**: `user`
- **説明**: 1対1のプライベートチャットメッセージ
- **IDフィールド**: `user_id`
- **対応プラットフォーム**: プライベートチャットをサポートするすべてのプラットフォーム

#### group
- **受信タイプ**: `group`
- **送信タイプ**: `group`
- **説明**: グループチャットメッセージ。Telegram supergroup などのさまざまな形式のグループを含む
- **IDフィールド**: `group_id`
- **対応プラットフォーム**: グループチャットをサポートするすべてのプラットフォーム

#### user
- **受信タイプ**: `user`
- **送信タイプ**: `user`
- **説明**: ユーザータイプ。一部のプラットフォーム（例: Telegram）ではプライベートチャットを `user` として表現する
- **IDフィールド**: `user_id`
- **対応プラットフォーム**: Telegram などのプラットフォーム

### 2.2 ErisPulse 拡張タイプ

#### channel
- **受信タイプ**: `channel`
- **送信タイプ**: `channel`
- **説明**: チャンネルメッセージ。複数ユーザーへのブロードキャストメッセージをサポート
- **IDフィールド**: `channel_id`
- **対応プラットフォーム**: Discord, Telegram, Line など

#### guild
- **受信タイプ**: `guild`
- **送信タイプ**: `guild`
- **説明**: サーバー/コミュニティメッセージ。通常は Discord Guild レベルのイベントに使用
- **IDフィールド**: `guild_id`
- **対応プラットフォーム**: Discord など

#### thread
- **受信タイプ**: `thread`
- **送信タイプ**: `thread`
- **説明**: トピック/サブチャンネルメッセージ。コミュニティ内のサブディスカッションエリアに使用
- **IDフィールド**: `thread_id`
- **対応プラットフォーム**: Discord Threads, Telegram Topics など

## 3. プラットフォーム型のマッピング

### 3.1 マッピングの原則

アダプターは、プラットフォームのネイティブ型を ErisPulse 標準型にマッピングする役割を担います：

```
プラットフォームネイティブ型 → ErisPulse 標準型 → 送信型
```

### 3.2 一般的なプラットフォームのマッピング例

#### Telegram
```
Telegram型             ErisPulse 受信型     送信型
─────────────────      ────────────────       ───────────
private                private                user
group                  group                  group
supergroup             group                  group  # group にマッピング
channel                channel                channel
```

#### Discord
```
Discord型              ErisPulse 受信型     送信型
─────────────────      ────────────────       ───────────
Direct Message         private               user
Text Channel           channel               channel
Guild                  guild                 guild
Thread                 thread                thread
```

#### OneBot11
```
OneBot11型            ErisPulse 受信型     送信型
─────────────────      ────────────────       ───────────
private                private               user
group                  group                 group
discuss                group                 group  # group にマッピング

## 4. 自定义型の拡張

### 4.1 自定型の登録

アダプターは、独自のセッション型を登録することができます。

```python
from ErisPulse.Core.Event import register_custom_type

# 自定型の登録
register_custom_type(
    receive_type="my_custom_type",
    send_type="custom",
    id_field="custom_id",
    platform="MyPlatform"
)
```

### 4.2 自定型の使用

登録後、システムは自動的にその型の変換と推論を処理します。

```python
# 自動推論
receive_type = infer_receive_type(event, platform="MyPlatform")
# 戻り値: "my_custom_type"

# 送信型への変換
send_type = convert_to_send_type(receive_type, platform="MyPlatform")
# 戻り値: "custom"

# 対応するIDの取得
target_id = get_target_id(event, platform="MyPlatform")
# 戻り値: event["custom_id"]
```

### 4.3 自定型の解除登録

```python
from ErisPulse.Core.Event import unregister_custom_type

unregister_custom_type("my_custom_type", platform="MyPlatform")

## 5. 自動型推論

イベントに明確な `detail_type` フィールドがない場合、システムは存在する ID フィールドに基づいて型を自動的に推論します：

> [!NOTE]
> **2.7.0+ の動作変更**：`detail_type` は**既知の会話タイプ**（標準またはカスタム）である場合にのみ直接採用されます。notice/request イベントの `detail_type`（例: `group_member_increase`、`friend_increase`）は**意味論的サブタイプ**であり、会話タイプではなく、ID フィールドに基づいて正しい会話タイプが推論されます。

### 5.1 推論優先度

```
優先度（高から低）：
1. group_id     → group
2. channel_id   → channel
3. guild_id     → guild
4. thread_id    → thread
5. user_id      → private
```

### 5.2 使用例

```python
# イベントに group_id のみがある
event = {"group_id": "123", "user_id": "456"}
receive_type = infer_receive_type(event)
# 戻り値: "group"（group_id を優先して使用）

# イベントに user_id のみがある
event = {"user_id": "123"}
receive_type = infer_receive_type(event)
# 戻り値: "private"

# notice イベントの detail_type は意味論的サブタイプであり、2.7.0+ では ID フィールドから推論される
event = {"type": "notice", "detail_type": "group_member_increase", "group_id": "123"}
receive_type = infer_receive_type(event)
# 戻り値: "group"（"group_member_increase" ではなく）

## 6. API 使用例

### 6.1 メッセージ送信

```python
from ErisPulse import adapter

# ユーザーに送信
await adapter.myplatform.Send.To("user", "123").Text("Hello")

# グループに送信
await adapter.myplatform.Send.To("group", "456").Text("Hello")

# 自動変換 private → user（推奨されない、互換性の問題が発生する可能性がある）
await adapter.myplatform.Send.To("private", "789").Text("Hello")
# 内部では自動的に Send.To("user", "789") に変換される # 直接 user を会話タイプとして使用するのがより優れた選択である
```

### 6.2 イベントの返信

```python
from ErisPulse.Core.Event import Event

# Event.reply() は自動的に型変換を処理する
await event.reply("返信内容")
# 内部では自動的に正しい送信タイプが使用される
```

### 6.3 コマンド処理

```python
from ErisPulse.Core.Event import command

@command(name="test")
async def handle_test(event):
    # システムが自動的に会話タイプを処理する
    # group_id か user_id を手動で判断する必要はない
    await event.reply("コマンドが正常に実行されました")

## 7. コア API リファレンス

### 7.1 タイプ変換

```python
from ErisPulse.Core.Event import convert_to_send_type, convert_to_receive_type

# 受信タイプ → 送信タイプ
convert_to_send_type("private")  # → "user"
convert_to_send_type("group")    # → "group"

# 送信タイプ → 受信タイプ
convert_to_receive_type("user")   # → "private"
convert_to_receive_type("group")  # → "group"
```

### 7.2 ID フィールドのクエリ

```python
from ErisPulse.Core.Event import get_id_field, get_receive_type

get_id_field("group")    # → "group_id"
get_id_field("private")  # → "user_id"

get_receive_type("group_id")  # → "group"
get_receive_type("user_id")   # → "private"
```

### 7.3 送信情報のワンステップ取得

```python
from ErisPulse.Core.Event import get_send_type_and_target_id

event = {"detail_type": "private", "user_id": "123"}
send_type, target_id = get_send_type_and_target_id(event)
# send_type = "user", target_id = "123"

# 直接 Send.To() に使用
await adapter.Send.To(send_type, target_id).Text("Hello")
```

### 7.4 目標 ID の取得

```python
from ErisPulse.Core.Event import get_target_id

event = {"detail_type": "group", "group_id": "456"}
get_target_id(event)  # → "456"

## 8. ユーティリティメソッド

```python
from ErisPulse.Core.Event import (
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)

is_standard_type("private")     # True
is_standard_type("custom_type") # False

is_valid_send_type("user")      # True
is_valid_send_type("invalid")   # False

get_standard_types()  # {"private", "group", "channel", "guild", "thread", "user"}
get_send_types()      # {"user", "group", "channel", "guild", "thread"}

clear_custom_types()                # 全てのカスタムタイプをクリア
clear_custom_types(platform="discord")  # 指定されたプラットフォームのカスタムタイプのみをクリア

## 9. 最適実践

### 7.1 アダプター開発者

1. **標準マッピングの使用**：可能な限り標準型にマッピングし、新規型を作成しないこと。
2. **正しい変換**：受信型と送信型のマッピング関係が正しくなっていることを確認すること。
3. **元のデータの保持**：`{platform}_raw` に元のイベント型を保持すること。
4. **ドキュメントの説明**：アダプターのドキュメントに型マッピング関係を説明すること。

### 7.2 モジュール開発者

1. **ツールメソッドの使用**：`get_send_type_and_target_id()` などのツールメソッドを使用すること。
2. **ハードコーディングの回避**：`if group_id else "private"` のようなコードを書かないこと。
3. **すべての型を考慮**：コードは `private`/`group` だけでなく、すべての標準型をサポートすること。
4. **柔軟な設計**：直接フィールドにアクセスするのではなく、イベントラッパーの方法を使用すること。

### 7.3 型推論

- **detail_type の優先使用**：明確なフィールドがある場合は、推論を行わないこと。
- **推論の適切な使用**：明確な型がない場合にのみ使用すること。
- **優先順位の注意**：推論の優先順位を理解し、予期しない結果を避けること。

[**English**](docs/ja/9-best-practices.md)

## 10. よくある質問

### Q1: なぜ送信時に private を user に変換する必要があるのですか？

A: これは OneBot12 標準の要件です。`private` は受信時の概念であり、送信時には `user` を使用する方が意味的に適切です。

### Q2: 新しい会話タイプをどのようにサポートしますか？

A: `register_custom_type()` を使用してカスタムタイプを登録するか、または標準タイプの `channel`、`guild` などを直接使用します。

### Q3: イベントに detail_type がない場合はどうすればよいですか？

A: システムは存在する ID フィールドに基づいて自動的に推論します。優先順位は、group > channel > guild > thread > user です。

### Q4: アダプタは Telegram supergroup をどのようにマッピングしますか？

A: アダプタの変換ロジックの中で、`supergroup` を標準の `group` タイプにマッピングします。

### Q5: 電子メールなどの特殊なプラットフォームはどのように処理しますか？

A: 一般的でない、またはプラットフォーム固有のタイプについては、`{platform}_raw` と `{platform}_raw_type` を使用して元のデータを保持し、アダプタが独自に処理します。

[**English**](docs/en/faq.md) | [**日本語**](docs/ja/faq.md) | [**简体中文**](docs/ja/faq.md) | [**繁體中文**](docs/zh-TW/faq.md) | [**한국어**](docs/ko/faq.md) | [**русский**](docs/ru/faq.md) | [**Español**](docs/es/faq.md) | [**Deutsch**](docs/de/faq.md) | [**français**](docs/fr/faq.md) | [**português**](docs/pt/faq.md) | [**italiano**](docs/it/faq.md) | [**ไทย**](docs/th/faq.md) | [**Bahasa Indonesia**](docs/id/faq.md) | [**العربية**](docs/ar/faq.md) | [**Türkçe**](docs/tr/faq.md) | [**עברית**](docs/he/faq.md) | [**فارسی**](docs/fa/faq.md) | [**Tiếng Việt**](docs/vi/faq.md) | [**magyar**](docs/hu/faq.md) | [**Nederlands**](docs/nl/faq.md) | [**Svenska**](docs/sv/faq.md) | [**Dansk**](docs/da/faq.md) | [**suomi**](docs/fi/faq.md) | [**Polski**](docs/pl/faq.md) | [**čeština**](docs/cs/faq.md) | [**ελληνικά**](docs/el/faq.md) | [**български**](docs/bg/faq.md) | [**hrvatski**](docs/hr/faq.md) | [**lietuvių**](docs/lt/faq.md) | [**latviešu**](docs/lv/faq.md) | [**українська**](docs/uk/faq.md) | [**български**](docs/bg/faq.md) | [**română**](docs/ro/faq.md) | [**slovenčina**](docs/sk/faq.md) | [**slovenščina**](docs/sl/faq.md) | [**Eesti**](docs/et/faq.md) | [**Norsk**](docs/no/faq.md)

## 11. 関連ドキュメント

- [イベント変換標準](event-conversion.md) - イベント変換の完全な規格
- [送信メソッド規格](send-method-spec.md) - Send クラスのメソッド命名とパラメータの規格
- [アダプタ開発ガイド](../developer-guide/adapters/) - アダプタ開発の完全なガイド

**言語:** [**English**](../en/README.md) | [**日本語**](../ja/README.md) | [**简体中文**](../zh-CN/README.md)