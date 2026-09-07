# イベントコンバーター実装ガイド

イベントコンバーター (Converter) は、アダプターのコアコンポーネントの一つであり、プラットフォームのネイティブイベントを ErisPulse 統一の OneBot12 標準イベント形式に変換する役割を担います。

## Converter の責任

```
プラットフォームのネイティブイベント ──→ Converter.convert() ──→ OneBot12 標準イベント
```

Converter は**正方向の変換**（受信方向）のみを担当し、プラットフォームのネイティブイベントデータを OneBot12 標準形式に変換します。逆方向の変換（送信方向）は `Send.Raw_ob12()` メソッドで処理されます。

### 核心原則

1. **無損変換**：元のデータはすべて `{platform}_raw` フィールドに完全に保持される必要があります
2. **標準互換性**：変換後のイベントは OneBot12 標準形式に準拠している必要があります
3. **プラットフォーム拡張**：プラットフォーム固有のデータは `{platform}_` で始まるフィールドに格納されます

## BaseConverter 基底クラス（推奨）

2.7.0 以降、フレームワークは `BaseConverter` 基底クラス（`ErisPulse.Core.Bases`）を提供しており、OneBot12 イベントの**共通フィールド構築**と**一般的なメッセージセグメント補助**をカプセル化しています。これにより、コンバーターは型マッピングにのみ集中できます。

```python
from ErisPulse.Core.Bases import BaseConverter


class MyConverter(BaseConverter):
    def __init__(self):
        super().__init__(platform="myplatform")

    def convert(self, raw_event: dict) -> dict | None:
        if not isinstance(raw_event, dict):
            return None
        event_type = raw_event.get("type", "")
        base = self.build_base_event(raw_event, event_type)  # id/time/platform/self/raw
        if event_type == "message":
            base["type"] = "message"
            base["detail_type"] = "group" if raw_event.get("group_id") else "private"
            base["user_id"] = str(raw_event.get("sender_id", ""))
            base["message"] = [self.text(raw_event.get("content", ""))]
            base["alt_message"] = raw_event.get("content", "")
            return base
        return None
```

`build_base_event()` で既に埋め込まれている共通フィールド：

| フィールド | 情報源 |
|------|------|
| `id` | `raw_event["event_id"]`、不足時は UUID を自動生成 |
| `time` | `raw_event["timestamp"]`、不足時は現在時刻 |
| `platform` | コンストラクタで渡された `platform` |
| `self` | `{"platform": ..., "user_id": raw_event["bot_id"]}` |
| `{platform}_raw` | 原始イベント（「無損失変換」の原則を満たす） |
| `{platform}_raw_type` | 原始イベントの型 |

一般的なメッセージセグメント補助メソッド（すべて静的メソッドで、直接再利用可能）：

```python
converter.text("hi")          # {"type": "text", "data": {"text": "hi"}}
converter.at("123456")        # {"type": "at", "data": {"user_id": "123456"}}
converter.image("file.png")   # {"type": "image", "data": {"file": "file.png"}}
```

> 手動実装では、`build_base_event` の共通フィールド構築は繰り返し書く必要のある定型コードです。`BaseConverter` を使用することで、この部分を省略でき、また「無損失変換」（原始イベントは常に `{platform}_raw` に格納される）を自然に満たします。

## convert() メソッド

### メソッド署名

```python
def convert(self, raw_event: dict) -> dict:
    """
    プラットフォーム固有のイベントを OneBot12 標準フォーマットに変換します。

    :param raw_event: プラットフォーム固有のイベントデータ
    :return: OneBot12 標準フォーマットのイベント辞書
    """
    pass
```

### 戻り値構造

変換後のイベント辞書には、以下の標準フィールドが含まれている必要があります：

```python
{
    "id": "イベントの唯一ID",
    "time": 1234567890,           # Unix タイムスタンプ（秒）
    "type": "message",             # イベントの種類
    "detail_type": "private",      # 詳細な種類
    "platform": "myplatform",      # プラットフォーム名
    "self": {
        "platform": "myplatform",
        "user_id": "bot_user_id"
    },

    # メッセージイベントのフィールド
    "user_id": "送信者のID",
    "message": [...],              # OneBot12 メッセージセグメントのリスト
    "alt_message": "プレーンテキストの内容",

    # 原始データを保持する必要がある
    "myplatform_raw": { ... },     # プラットフォーム固有のイベントの完全なデータ
    "myplatform_raw_type": "プラットフォーム固有のイベントタイプ名",
}
```

## 必須フィールドのマッピング

### 一般的なフィールド（すべてのイベントタイプ）

| OB12 フィールド | 型 | 説明 |
|-----------|------|------|
| `id` | str | イベントの一意の識別子 |
| `time` | int | Unix タイムスタンプ（秒） |
| `type` | str | イベントの種類：`message` / `notice` / `request` / `meta` |
| `detail_type` | str | 詳細なタイプ：`private` / `group` / `friend` など |
| `platform` | str | プラットフォーム名。アダプターの登録名と同じ |
| `self` | dict | ロボット情報：`{"platform": "...", "user_id": "..."}` |

### メッセージイベントの追加フィールド

| OB12 フィールド | 型 | 説明 |
|-----------|------|------|
| `user_id` | str | 送信者の ID |
| `message` | list[dict] | OneBot12 メッセージセグメントのリスト |
| `alt_message` | str | 純粋なテキストの代替内容 |

### 通知イベントの追加フィールド

| OB12 フィールド | 型 | 説明 |
|-----------|------|------|
| `user_id` | str | 関連するユーザーの ID |
| `operator_id` | str | 操作者の ID（例：グループメンバーの変更時） |

## メッセージセグメントの変換

OneBot12 標準では、以下のメッセージセグメントタイプが定義されています：

```python
# テキスト
{"type": "text", "data": {"text": "Hello"}}

# 画像
{"type": "image", "data": {"file": "https://example.com/img.jpg"}}

# 音声
{"type": "audio", "data": {"file": "https://example.com/audio.mp3"}}

# 動画
{"type": "video", "data": {"file": "https://example.com/video.mp4"}}

# ファイル
{"type": "file", "data": {"file": "https://example.com/doc.pdf"}}

# @メンション
{"type": "mention", "data": {"user_id": "123"}}

# @全員
{"type": "mention_all", "data": {}}

# 返信
{"type": "reply", "data": {"message_id": "msg_123"}}
```

プラットフォームがサポートしていないメッセージセグメントタイプがある場合、そのセグメントを省略するか、最も近い標準タイプに変換することができます。

## プラットフォーム拡張フィールド

プラットフォーム固有のデータは、標準フィールドとの競合を避けるために `{platform}_` という接頭辞を使用して保存してください。

```python
{
    # 標準フィールド
    "type": "message",
    "detail_type": "group",
    # ...

    # プラットフォーム拡張フィールド
    "myplatform_raw": { ... },          # 原始イベントデータ（必須）
    "myplatform_raw_type": "chat",      # 原始イベントの種類（必須）

    # その他のプラットフォーム固有のフィールド
    "myplatform_group_name": "群名称",
    "myplatform_sender_role": "admin",
}
```

> **重要**：`{platform}_raw` フィールドは必須です。ErisPulse のイベントシステムやモジュールは、プラットフォームの元のデータにアクセスするためにこのフィールドに依存することがあります。

## 完整例

以下は Converter の完全な実装例です：

```python
class MyConverter:
    def __init__(self, platform: str):
        self.platform = platform

    def convert(self, raw_event: dict) -> dict:
        event_type = raw_event.get("type", "")

        base_event = {
            "id": raw_event.get("id", ""),
            "time": raw_event.get("timestamp", 0),
            "platform": self.platform,
            "self": {
                "platform": self.platform,
                "user_id": raw_event.get("self_id", ""),
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": event_type,
        }

        if event_type == "chat":
            return self._convert_message(raw_event, base_event)
        elif event_type == "notification":
            return self._convert_notice(raw_event, base_event)
        elif event_type == "request":
            return self._convert_request(raw_event, base_event)

        return base_event

    def _convert_message(self, raw: dict, base: dict) -> dict:
        base["type"] = "message"
        base["detail_type"] = "group" if raw.get("group_id") else "private"
        base["user_id"] = raw.get("sender_id", "")
        base["message"] = self._convert_message_segments(raw.get("content", ""))
        base["alt_message"] = raw.get("content", "")

        if raw.get("group_id"):
            base["group_id"] = raw["group_id"]

        return base

    def _convert_message_segments(self, content: str) -> list:
        segments = []
        if content:
            segments.append({"type": "text", "data": {"text": content}})
        return segments

    def _convert_notice(self, raw: dict, base: dict) -> dict:
        base["type"] = "notice"
        notification_type = raw.get("notification_type", "")

        if notification_type == "member_join":
            base["detail_type"] = "group_member_increase"
            base["user_id"] = raw.get("user_id", "")
            base["group_id"] = raw.get("group_id", "")
            base["operator_id"] = raw.get("operator_id", "")
        elif notification_type == "friend_add":
            base["detail_type"] = "friend_increase"
            base["user_id"] = raw.get("user_id", "")

        return base

    def _convert_request(self, raw: dict, base: dict) -> dict:
        base["type"] = "request"
        request_type = raw.get("request_type", "")

        if request_type == "friend":
            base["detail_type"] = "friend"
            base["user_id"] = raw.get("user_id", "")
            base["comment"] = raw.get("message", "")
        elif request_type == "group_invite":
            base["detail_type"] = "group"
            base["group_id"] = raw.get("group_id", "")
            base["user_id"] = raw.get("inviter_id", "")

        return base
```

## 富媒体メッセージ変換の例

実際のプラットフォームのメッセージには、画像、@メンション、返信などの富媒体コンテンツが含まれることが多いです。以下は、`_convert_message_segments` が複数のメッセージタイプを処理する例です：

```python
def _convert_message_segments(self, raw_content: list) -> list:
    """プラットフォーム固有のメッセージセグメントリストを OneBot12 標準のメッセージセグメントに変換する"""
    segments = []

    for item in raw_content:
        item_type = item.get("type", "")

        if item_type == "text":
            segments.append({
                "type": "text",
                "data": {"text": item.get("content", "")}
            })

        elif item_type == "image":
            file_url = item.get("url") or item.get("file_id", "")
            segments.append({
                "type": "image",
                "data": {"file": file_url}
            })

        elif item_type == "at":
            segments.append({
                "type": "mention",
                "data": {"user_id": item.get("target_id", "")}
            })

        elif item_type == "reply":
            segments.append({
                "type": "reply",
                "data": {"message_id": item.get("reply_to_id", "")}
            })

        elif item_type == "at_all":
            segments.append({"type": "mention_all", "data": {}})

        else:
            segments.append({
                "type": "text",
                "data": {"text": f"[サポートされていないメッセージタイプ: {item_type}]"}
            })

    return segments
```

## 常見の落とし穴

### 1. `{platform}_raw` フィールドの欠落

これは最も一般的なエラーです。元データフィールドが欠落していると、モジュールがプラットフォーム固有の情報をアクセスできなくなります。

```python
base_event["myplatform_raw"] = raw_event        # 必須！
base_event["myplatform_raw_type"] = event_type   # 必須！
```

### 2. 時間スタンプの形式エラー

OneBot12 標準では、`time` フィールドは Unix 秒単位の時間スタンプ（整数）である必要があります。もしプラットフォームがミリ秒単位の時間スタンプや ISO 形式の文字列を返している場合、変換が必要です。

```python
import time

# ミリ秒 → 秒
"time": raw_event.get("timestamp", 0) // 1000

# ISO 文字列 → 秒
"time": int(time.mktime(time.strptime(raw_event["created_at"], "%Y-%m-%dT%H:%M:%S")))
```

### 3. `self` フィールドの欠落

`self` フィールドには、ロボット自身の情報が含まれており、`user_id` はロボットのアカウント ID です。複数の Bot が存在する状況では、このフィールドは非常に重要です。

```python
"self": {
    "platform": self.platform,
    "user_id": raw_event.get("bot_id", ""),   # ロボット自身の ID
}
```

### 4. `detail_type` に非標準の値を使用

`detail_type` には、OneBot12 標準で定義された値、例えば `private`、`group`、`friend_increase`、`group_member_increase` などを使用する必要があります。プラットフォーム固有の命名は使用しないでください。

### 5. 送受信の一貫性

Converter が生成するメッセージセグメントの型が、Send 端でサポートされているメソッドに対応していることを確認してください。たとえば、Converter がプラットフォームの画像メッセージを `{"type": "image", ...}` に変換した場合、Send 端の `Image()` メソッドは画像の送信を処理できる必要があります。

## 最佳実践

1. **常に元のデータを保持する**：`{platform}_raw` フィールドは省略しないでください。
2. **標準メッセージセグメントを使用する**：可能な限りプラットフォームのメッセージを OneBot12 標準メッセージセグメントに変換してください。
3. **detail_type を適切に設定する**：標準の型（`private`/`group`/`channel` など）を使用し、独自に定義しないでください。
4. **境界ケースを処理する**：元のイベントにフィールドが欠けている可能性があるため、`.get()` を使用し、適切なデフォルト値を提供してください。
5. **パフォーマンスの考慮**：`convert()` は各イベントで呼び出されるため、ここで処理に時間がかかる操作を避けてください。

## 関連ドキュメント

- [アダプタのコアコンセプト](core-concepts.md) - アダプタの全体的なアーキテクチャ
- [SendDSLの詳細](send-dsl.md) - 逆変換（送信方向）
- [イベント変換の標準](../../standards/event-conversion.md) - 公式のイベント変換規格
- [セッション型システム](../../standards/session-types.md) - セッション型のマッピングルール