# 花楓カフェ（Ideaura）プラットフォーム特性ドキュメント

IdeauraAdapterは、花楓カフェ（Allons）プラットフォームのAPIに基づいて構築されたアダプターであり、すべてのプラットフォーム機能モジュールを統合し、統一されたイベント処理およびメッセージ操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュール: ErisPulse-Ideaura
- メンテナ: ErisPulse

## 基本情報

- プラットフォーム紹介：花楓カフェ（Allons）はインスタントメッセージングプラットフォームです
- アダプター名：IdeauraAdapter
- マルチアカウントサポート：email/passwordによる複数アカウントの設定をサポート
- メソッドチェーンサポート：`.At()`、`.AtAll()`、`.Reply()`などのメソッドチェーンによる修飾をサポート
- OneBot12互換：OneBot12形式のメッセージ送信をサポート

## サポートするメッセージ送信タイプ

すべての送信メソッドはメソッドチェーン構文によって実装されています。例えば：
```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

サポートされている送信タイプは以下の通りです：
- `.Text(text: str)`：純粋なテキストメッセージを送信します。
- `.Image(file, filename: str = None)`：画像メッセージを送信します。bytes/URL/ローカルパスをサポートしています。
- `.Video(file, filename: str = None)`：動画メッセージを送信します。bytes/URL/ローカルパスをサポートしています。
- `.File(file, filename: str = None)`：ファイルメッセージを送信します。bytes/URL/ローカルパスをサポートしています。
- `.Voice(file, filename: str = None)`：音声メッセージを送信します（ファイルとして送信されます）。
- `.Face(face_id: str)`：絵文字を送信します（純粋なテキスト形式の絵文字として送信されます）。
- `.Markdown(text: str)`：Markdown形式のメッセージを送信します。
- `.Html(html: str)`：HTML形式のメッセージを送信します。
- `.Edit(message_id: str, text: str, content_type: str = "text")`：既存のメッセージを編集します。
- `.Recall(message_id: str)`：メッセージを取り消します。

### メソッドチェーンによる修飾（組み合わせ可能）

メソッドチェーンによる修飾メソッドは `self` を返し、チェーン呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります：

- `.At(user_id: str, name: str = None)`：指定したユーザーを@します。
- `.AtAll()`：全員を@します。
- `.Reply(message_id: str)`：指定したメッセージに返信します。

### メソッドチェーン呼び出しの例

```python
# 基本的な送信
await ideaura.Send.To("user", user_id).Text("Hello")

# ユーザーを@する
await ideaura.Send.To("group", "chatroom").At("456").Text("@李四 こんにちは")

# 複数人を@する
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@複数人")

# メッセージに返信する
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("返信メッセージ")

# 返信 + @
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("返信して@する")
```

### 異なるターゲットへの送信

```python
# チャットルームに送信
await ideaura.Send.To("group", "chatroom").Text("チャットルームメッセージ")

# トピックに送信
await ideaura.Send.To("group", "topic_id").Text("トピックメッセージ")

# プライベートメッセージを送信
await ideaura.Send.To("user", "user_id").Text("プライベートメッセージ")
```

### OneBot12メッセージサポート

アダプターはOneBot12形式のメッセージ送信をサポートしており、クロスプラットフォームのメッセージ互換性に役立ちます：

- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します。

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# メソッドチェーンによる修飾と組み合わせ
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

## 送信メソッドの戻り値

すべての送信メソッドはTaskオブジェクトを返し、直接 `await` することで送信結果を取得できます。戻り値はErisPulseアダプターの標準化された戻り値仕様に従います：

```python
{
    "status": "ok",           // 実行ステータス
    "retcode": 0,             // リターンコード
    "data": {...},            // レスポンスデータ
    "self": {...},            // 自身の情報（user_idを含む）
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "ideaura_raw": {...}      // 生のレスポンスデータ
}
```

## 固有のイベントタイプ

このプラットフォームの特性を使用する前に、`platform=="ideaura"` で検出する必要があります。

### 主要な相違点

1. 固有のイベントタイプ：
    - メッセージ編集：ideaura_message_edit
    - メッセージ取り消し：ideaura_message_recall
    - メッセージ転送：ideaura_message_forward
    - メッセージ既読：ideaura_message_read
    - 友達拒否：ideaura_friend_rejected
    - 友達オンライン：ideaura_friend_online
    - 友達オフライン：ideaura_friend_offline
    - ユーザーステータス変更：ideaura_user_status_change
    - 転送メッセージセグメント：ideaura_forwarded
    - 編集マークセグメント：ideaura_edited
    - Markdownメッセージセグメント：ideaura_markdown
    - HTMLメッセージセグメント：ideaura_html
2. 拡張フィールド：
    - すべての固有フィールドは `ideaura_` プレフィックスで識別されます
    - 生データは `ideaura_raw` フィールドに保持されます
    - `self.user_id` は現在のアカウントのユーザーIDを示します

### メッセージ編