# イベントコンバーター実装ガイド

イベントコンバーター (Converter) はアダプターのコアコンポーネントの一つであり、プラットフォームのネイティブイベントを ErisPulse 統一の OneBot12 標準イベントフォーマットに変換する役割を担います。

## Converter の役割

```
プラットフォームネイティブイベント ──→ Converter.convert() ──→ OneBot12 標準イベント
```

Converter は**順方向変換**（受信方向）のみを担当します。つまり、プラットフォームのネイティブイベントデータを OneBot12 標準フォーマットに変換します。逆方向変換（送信方向）は `Send.Raw_ob12()` メソッドによって処理されます。

### コア原則

1. **ロスレス変換**：元のデータは `{platform}_raw` フィールドに完全に保持する必要があります
2. **標準互換性**：変換されたイベントは OneBot12 標準フォーマットに準拠している必要があります
3. **プラットフォーム拡張**：プラットフォーム固有のデータは `{platform}_` プレフィックスフィールドを使用して保存します

## convert() メソッド

### メソッドシグネチャ

```python
def convert(self, raw_event: dict) -> dict:
    """
    プラットフォームのネイティブイベントを OneBot12 標準フォーマットに変換します

    :param raw_event: プラットフォームのネイティブイベントデータ
    :return: OneBot12 標準フォーマットのイベント辞書
    """
    pass
```

### 戻り値の構造

変換されたイベント辞書には、以下の標準フィールドが含まれている必要があります：

```python
{
    "id": "イベントの一意のID",
    "time": 1234567890,           # Unixタイムスタンプ（秒）
    "type": "message",             # イベントタイプ
    "detail_type": "private",      # 詳細タイプ
    "platform": "myplatform",      # プラットフォーム名
    "self": {
        "platform": "myplatform",
        "user_id": "bot_user_id"
    },

    # メッセージイベントフィールド
    "user_id": "sender_id",
    "message": [...],              # OneBot12 メッセージセグメントのリスト
    "alt_message": "プレーンテキストの内容",

    # 元のデータを保持する必要があります
    "myplatform_raw": { ... },     # プラットフォームのネイティブイベントの完全なデータ
    "myplatform_raw_type": "ネイティブイベントタイプ名",
}
```

## 必須フィールドのマッピング

### 共通フィールド（すべてのイベントタイプ）

| OB12 フィールド | 型 | 説明 |
|-----------------|------|------|
| `id` | str | イベントの一意の識別子 |
| `time` | int | Unixタイムスタンプ（秒） |
| `type` | str | イベントタイプ：`message` / `notice` / `request` / `meta` |
| `detail_type` | str | 詳細タイプ：`private` / `group` / `friend` など |
| `platform` | str | プラットフォーム名、アダプターの登録名と一致 |
| `self` | dict | ボット情報：`{"platform": "...", "user_id": "..."}` |

### メッセージイベントの追加フィールド

| OB12 フィールド | 型 | 説明 |
|-----------------|------|------|
| `user_id` | str | 送信者 ID |
| `message` | list[dict] | OneBot12 メッセージセグメントのリスト |
| `alt_message` | str | プレーンテキストの代替コンテンツ |

### 通知イベントの追加フィールド

| OB12 フィールド | 型 | 説明 |
|-----------------|------|------|
| `user_id` | str | 関連ユーザー ID |
| `operator_id` | str | 操作者 ID（グループメンバーの変更など） |

## メッセージセグメントの変換

OneBot12 標準は以下のメッセージセグメントタイプを定義しています：

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

# メンション（@）
{"type": "mention", "data": {"user_id": "123"}}

# 全体メンション（@all）
{"type": "mention_all", "data": {}}

# 返信
{"type": "reply", "data": {"message_id": "msg_123"}}
```

プラットフォームがサポートしていないメッセージセグメントタイプがある場合、そのセグメントを省略するか、最も近い標準タイプに変換することができます。

## プラットフォーム拡張フィールド

プラットフォーム固有のデータは `{platform}_` プレフィックスを使用して保存し、標準フィールドとの競合を避ける必要があります：

```python
{
    # 標準フィールド
    "type": "message",
    "detail_type": "group",
    # ...

    # プラットフォーム拡張フィールド
    "myplatform_raw": { ... },          # 元のイベントデータ（必須）
    "myplatform_raw_type": "chat",      # 元のイベントタイプ（必須）

    # その他のプラットフォーム固有のフィールド
    "myplatform_group_name": "グループ名",
    "myplatform_sender_role": "admin",
}
```

> **重要**：`{platform}_raw` フィールドは必須です。ErisPulse のイベントシステムやモジュールがプラットフォームの元のデータにアクセスするために依存する可能性があります。

## 完全な例

以下は完全な Converter の実装例です：

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

## リッチメディアメッセージ変換例

実際のプラットフォームのメッセージには通常、画像、@メンション、返信などのリッチメディアコンテンツが含まれます。以下は `_convert_message_segments` が複数のメッセージタイプを処理する例です：

```python
def _convert_message_segments(self, raw_content: list) -> list:
    """プラットフォームのネイティブメッセージセグメントリストを OneBot12 標準メッセージセグメントに変換します"""
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

## よくある落とし穴

### 1. `{platform}_raw` フィールドの欠落

これが最もよくあるエラーです。元のデータフィールドの欠落により、モジュールがプラットフォーム固有の情報にアクセスできなくなります。

```python
base_event["myplatform_raw"] = raw_event        # 必須！
base_event["myplatform_raw_type"] = event_type   # 必須！
```

### 2. タイムスタンプの形式エラー

OneBot12 標準は `time` フィールドを Unix 秒単位のタイムスタンプ（整数）として要求します。もしプラットフォームがミリ秒タイムスタンプまたは ISO 形式の文字列を返す場合、変換が必要です：

```python
import time

# ミリ秒 → 秒
"time": raw_event.get("timestamp", 0) // 1000

# ISO 文字列 → 秒
"time": int(time.mktime(time.strptime(raw_event["created_at"], "%Y-%m-%dT%H:%M:%S")))
```

### 3. `self` フィールドの欠落

`self` フィールドにはボット自身の情報が含まれており、`user_id` はボットのアカウント ID です。マルチボットのシナリオではこのフィールドが重要です：

```python
"self": {
    "platform": self.platform,
    "user_id": raw_event.get("bot_id", ""),   # ボット自身の ID
}
```

### 4. detail_type に非標準の値を使用する

`detail_type` は必ず OneBot12 標準で定義された値（`private`、`group`、`friend_increase`、`group_member_increase` など）を使用してください。プラットフォーム固有の命名を使用しないでください。

### 5. 往復の整合性の確認

Converter が生成したメッセージセグメントタイプが、Send 端でサポートされるメソッドと対応していることを確認してください。例えば、Converter がプラットフォームの画像メッセージを `{"type": "image", ...}` に変換する場合、Send 端の `Image()` メソッドは画像の送信を処理できる必要があります。

## ベストプラクティス

1. **常に元のデータを保持する**：`{platform}_raw` フィールドは省略できません
2. **標準メッセージセグメントを使用する**：プラットフォームのメッセージを OneBot12 標準のメッセージセグメントに変換するように努めてください
3. **detail_type を適切に設定する**：標準タイプ（`private`/`group`/`channel` など）を使用し、独自に定義しないでください
4. **エッジケースの処理**：元のイベントに一部のフィールドが欠落している可能性があるため、`.get()` を使用して適切なデフォルト値を提供してください
5. **パフォーマンスの考慮**：`convert()` は各イベントで呼び出されるため、時間のかかる操作をその中で実行することは避けてください

## 関連ドキュメント

- [アダプターのコアコンセプト](core-concepts.md) - アダプターの全体アーキテクチャ
- [SendDSL 詳解](send-dsl.md) - 逆方向変換（送信方向）
- [イベント変換標準](../../standards/event-conversion.md) - 公式なイベント変換仕様
- [セッションタイピングシステム](../../advanced/session-types.md) - セッションタイプのマッピングルール