# イベントコンバーター実装ガイド

イベントコンバーター (Converter) はアダプターのコアコンポーネントの一つであり、プラットフォームのネイティブイベントを ErisPulse の統一された OneBot12 標準イベント形式に変換します。

## Converter の責務

```
プラットフォームのネイティブイベント ──→ Converter.convert() ──→ OneBot12 標準イベント
```

Converter は**正方向変換**（受信方向）のみを担当し、プラットフォームのネイティブイベントデータを OneBot12 標準形式に変換します。逆方向変換（送信方向）は `Send.Raw_ob12()` メソッドで処理されます。

### 核心原則

1. **無損変換**：元のデータは `{platform}_raw` フィールドに完全に保持される必要があります
2. **標準互換性**：変換後のイベントは OneBot12 標準形式に準拠している必要があります
3. **プラットフォーム拡張**：プラットフォーム固有のデータは `{platform}_` で始まるフィールドに格納されます

## BaseConverter 基底クラス（推奨）

2.7.0 以降、フレームワークは `BaseConverter` 基底クラス（`ErisPulse.Core.Bases`）を提供しており、OneBot12 イベントの**共通フィールド構築**と**一般的なメッセージセグメントの補助**をカプセル化しています。これにより、コンバーターは型マッピングに集中することができます：

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

`build_base_event()` で埋め込まれる共通フィールド：

| フィールド | 情報源 |
|------|------|
| `id` | `raw_event["event_id"]`、不足時は自動生成された UUID |
| `time` | `raw_event["timestamp"]`、不足時は現在時刻 |
| `platform` | コンストラクタで渡された `platform` |
| `self` | `{"platform": ..., "user_id": raw_event["bot_id"]}` |
| `{platform}_raw` | 元のイベント（「無損変換」の原則を満たす） |
| `{platform}_raw_type` | 元のイベントの型 |

一般的なメッセージセグメント補助メソッド（すべて静的メソッドで、直接再利用可能）：

```python
converter.text("hi")          # {"type": "text", "data": {"text": "hi"}}
converter.at("123456")        # {"type": "at", "data": {"user_id": "123456"}}
converter.image("file.png")   # {"type": "image", "data": {"file": "file.png"}}
```

> 手動実装する場合、`build_base_event` の共通フィールド構築は繰り返し書く必要がある定型コードですが、`BaseConverter` を使用することでこの部分を省略でき、自然に「無損変換」（元のイベントは常に `{platform}_raw` に格納される）が満たされます。

## convert() メソッド

### メソッド署名

```python
def convert(self, raw_event: dict) -> dict:
    """
    プラットフォームのネイティブイベントを OneBot12 標準形式に変換する

    :param raw_event: プラットフォームのネイティブイベントデータ
    :return: OneBot12 標準形式のイベント辞書
    """
    pass
```

### 戻り値の構造

変換後のイベント辞書には以下の標準フィールドが含まれている必要があります：

```python
{
    "id": "イベントのユニークID",
    "time": 1234567890,           # Unix タイムスタンプ（秒）
    "type": "message",             # イベントの型
    "detail_type": "private",      # 詳細の型
    "platform": "myplatform",      # プラットフォームの名前
    "self": {
        "platform": "myplatform",
        "user_id": "bot_user_id"
    },

    # メッセージイベントのフィールド
    "user_id": "sender_id",
    "message": [...],              # OneBot12 メッセージセグメントのリスト
    "alt_message": "プレーンテキストの内容",

    # 元のデータを保持する必要がある
    "myplatform_raw": { ... },     # プラットフォームのネイティブイベントの完全なデータ
    "myplatform_raw_type": "元のイベントの型名",
}
```

## 必須フィールドのマッピング

### 一般的なフィールド（すべてのイベント型に共通）

| OB12 フィールド | 型 | 説明 |
|-----------|------|------|
| `id` | str | イベントの一意の識別子 |
| `time` | int | Unix タイムスタンプ（秒） |
| `type` | str | イベントの型：`message` / `notice` / `request` / `meta` |
| `detail_type` | str | 詳細の型：`private` / `group` / `friend` など |
| `platform` | str | プラットフォームの名前、アダプター登録名と一致する |
| `self` | dict | ロボットの情報：`{"platform": "...", "user_id": "..."}` |

### メッセージイベントの追加フィールド

| OB12 フィールド | 型 | 説明 |
|-----------|------|------|
| `user_id` | str | 送信者の ID |
| `message` | list[dict] | OneBot12 メッセージセグメントのリスト |
| `alt_message` | str | プレーンテキストの代替内容 |

### 通知イベントの追加フィールド

| OB12 フィールド | 型 | 説明 |
|-----------|------|------|
| `user_id` | str | 関連するユーザーの ID |
| `operator_id` | str | 操作者の ID（例：グループメンバーの変更） |

## メッセージセグメントの変換

OneBot12 標準では以下のメッセージセグメントの型が定義されています：

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

プラットフォームがサポートしていないメッセージセグメントの型がある場合は、そのセグメントを省略するか、最も近い標準型に変換することができます。

## プラットフォーム拡張フィールド

プラットフォーム固有のデータは、`{platform}_` で始まるフィールドに格納し、標準フィールドとの衝突を避ける必要があります：

```python
{
    # 標準フィールド
    "type": "message",
    "detail_type": "group",
    # ...

    # プラットフォームの拡張フィールド
    "myplatform_raw": { ... },          # 元のイベントのデータ（必須）
    "myplatform_raw_type": "chat",      # 元のイベントの型（必須）

    # その他のプラットフォーム固有のフィールド
    "myplatform_group_name": "グループ名",
    "myplatform_sender_role": "管理者",
}
```

> **重要**：`{platform}_raw` フィールドは必須であり、ErisPulse のイベントシステムやモジュールは、このフィールドを介してプラットフォームの元のデータにアクセスする可能性があります。

## 完全な実装例

以下は完全な Converter 実装の例です：

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

## ファイブメディアメッセージの変換例

実際のプラットフォームのメッセージには、画像、@メンション、返信などのファイブメディアコンテンツが含まれていることがよくあります。以下は `_convert_message_segments` が複数のメッセージ型を処理する例です：

```python
def _convert_message_segments(self, raw_content: list) -> list:
    """プラットフォームのネイティブメッセージセグメントリストを OneBot12 標準メッセージセグメントに変換する"""
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
                "data": {"text": f"[サポートされていないメッセージ型: {item_type}]"}
            })

    return segments
```

## 一般的な落とし穴

### 1. `{platform}_raw` フィールドの欠落

これは最も一般的なエラーです。元のデータフィールドが欠けていると、モジュールがプラットフォーム固有の情報をアクセスできなくなります。

```python
base_event["myplatform_raw"] = raw_event        # 必須！
base_event["myplatform_raw_type"] = event_type   # 必須！
```

### 2. タイムスタンプ形式の誤り

OneBot12 標準では `time` フィールドは Unix 秒単位のタイムスタンプ（整数）である必要があります。プラットフォームがミリ秒単位のタイムスタンプや ISO 形式の文字列を返す場合、変換する必要があります：

```python
import time

# ミリ秒 → 秒
"time": raw_event.get("timestamp", 0) // 1000

# ISO 文字列 → 秒
"time": int(time.mktime(time.strptime(raw_event["created_at"], "%Y-%m-%dT%H:%M:%S")))
```

### 3. `self` フィールドの欠落

`self` フィールドにはロボット自身の情報が含まれ、`user_id` はロボットのアカウント ID です。複数の Bot が存在する状況ではこのフィールドが重要です：

```python
"self": {
    "platform": self.platform,
    "user_id": raw_event.get("bot_id", ""),   # ロボット自身の ID
}
```

### 4. `detail_type` に非標準の値を使用

`detail_type` には OneBot12 標準で定義された値（例：`private`、`group`、`friend_increase`、`group_member_increase` など）を使用する必要があります。プラットフォーム固有の命名は使用しないでください。

### 5. 往復の一貫性

Converter が生成するメッセージセグメントの型と Send 端のサポートするメソッドが対応していることを確認してください。たとえば、Converter がプラットフォームの画像メッセージを `{"type": "image", ...}` に変換した場合、Send 端の `Image()` メソッドは画像の送信に対応している必要があります。

## 最善の実践

1. **常に元のデータを保持する**：`{platform}_raw` フィールドは省略しないでください
2. **標準メッセージセグメントを使用する**：可能な限りプラットフォームのメッセージを OneBot12 標準メッセージセグメントに変換してください
3. **`detail_type` を適切に設定する**：標準の型（`private`/`group`/`channel` など）を使用し、独自に定義しないでください
4. **境界条件を処理する**：元のイベントに特定のフィールドが欠けている可能性があるため、`.get()` を使用し、適切なデフォルト値を提供してください
5. **パフォーマンスの考慮**：`convert()` は各イベントで呼び出されるため、ここで時間のかかる処理を行わないでください

## 関連ドキュメント

- [アダプターのコアコンセプト](core-concepts.md) - アダプターの全体的なアーキテクチャ
- [SendDSL 詳解](send-dsl.md) - 逆方向変換（送信方向）
- [イベント変換の標準](../../standards/event-conversion.md) - 正式なイベント変換の規格
- [セッション型システム](../../advanced/session-types.md) - セッション型のマッピングルール