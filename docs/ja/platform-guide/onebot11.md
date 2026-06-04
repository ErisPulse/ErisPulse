# OneBot11プラットフォーム特性ドキュメント

OneBot11Adapter は OneBot V11 プロトコルに基づいて構築されたアダプターです。

---

## ドキュメント情報

- 対応モジュールバージョン: 3.6.0
- メンテナー: ErisPulse

## 基本情報

- プラットフォーム概要：OneBot はチャットボットアプリケーションインターフェース標準です
- アダプター名：OneBotAdapter
- サポートするプロトコル/APIバージョン：OneBot V11
- 複数アカウントサポート：デフォルトで複数アカウントアーキテクチャを採用し、複数のOneBotアカウントの同時設定と実行をサポートします
- 旧設定との互換性：旧バージョンの設定フォーマットと互換性があり、移行のリマインダーを提供します（自動移行ではありません）

## サポートするメッセージ送信タイプ

すべての送信メソッドはメソッドチェーン構文によって実装されています。例：
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# デフォルトアカウントで送信
await onebot.Send.To("group", group_id).Text("Hello World!")

# 特定のアカウントを指定して送信
await onebot.Send.Using("main").To("group", group_id).Text("主アカウントからのメッセージ")

# メソッドチェーン修飾：ユーザーへのメンション + 返信
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("返信メッセージ")

# 全員へのメンション
await onebot.Send.To("group", group_id).AtAll().Text("アナウンスメッセージ")
```

### 基本送信メソッド

- `.Text(text: str)`：プレーンテキストメッセージを送信します。
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：画像を送信します（URL、Base64、またはbytesをサポート）。
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`：音声メッセージを送信します。
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：動画メッセージを送信します。
- `.Face(id: Union[str, int])`：QQのスタンプ/顔文字を送信します。
- `.File(file: Union[str, bytes], filename: str = "file.dat")`：ファイルを送信します（タイプを自動判定）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します（自動的にOB11に変換）。
- `.Recall(message_id: Union[str, int])`：メッセージを取り消します。

### メソッドチェーン修飾メソッド（組み合わせ可能）

メソッドチェーン修飾メソッドは `self` を返し、メソッドチェーン呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります：

- `.At(user_id: Union[str, int], name: str = None)`：指定したユーザーにメンションします（複数回呼び出し可能）。
- `.AtAll()`：全員にメンションします。
- `.Reply(message_id: Union[str, int])`：指定したメッセージに返信します。

### メソッドチェーン呼び出しの例

```python
# 基本送信
await onebot.Send.To("group", 123456).Text("Hello")

# 単一ユーザーにメンション
await onebot.Send.To("group", 123456).At(789012).Text("こんにちは")

# 複数ユーザーにメンション
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("皆さんこんにちは")

# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)
```

### サポートされていないタイプの処理

未定義の送信メソッドが呼び出された場合、アダプターはテキストプロンプトを返します：
```python
# 存在しないメソッドを呼び出し
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# 実際の送信: "[サポートされていない送信タイプ] メソッド名: SomeUnsupportedMethod, パラメータ: [...]"
```

## 固有のイベントタイプ

OneBot11イベントはOneBot12プロトコルに変換されます。標準フィールドはOneBot12プロトコルに完全に準拠していますが、以下の違いがあります：

### 主要な違い

1. 固有のイベントタイプ：
   - CQコード拡張イベント：onebot11_cq_{type}
   - 名誉変更イベント：onebot11_honor
   - Pokeイベント：onebot11_poke
   - 群レッドパッケージラッキーキングイベント：onebot11_lucky_king

2. 拡張フィールド：
   - すべての固有フィールドは `onebot11_` プレフィックスで識別されます
   - 元のCQコードメッセージは `onebot11_raw_message` フィールドに保持されます
   - 元のイベントデータは `onebot11_raw` フィールドに保持されます

### 特殊フィールドの例

```python
// 名誉変更イベント
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "onebot11_honor_type": "talkative",
  "onebot11_operation": "set"
}

// Pokeイベント
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678",
  "onebot11_poke_type": "normal"
}

// 群レッドパッケージラッキーキングイベント
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// CQコードメッセージセグメント
{
  "type": "message",
  "message": [
    {
      "type": "onebot11_face",
      "data": {"id": "123"}
    },
    {
      "type": "onebot11_shake",
      "data": {} 
    }
  ]
}
```

### 拡張フィールドの説明

- すべての固有フィールドは `onebot11_` プレフィックスで識別されます
- 元のCQコードメッセージは `onebot11_raw_message` フィールドに保持されます
- 元のイベントデータは `onebot11_raw` フィールドに保持されます
- メッセージ内容のCQコードは対応するメッセージセグメントに変換されます
- 返信メッセージには `reply` タイプのメッセージセグメントが追加されます
- メンション(@)メッセージには `mention` タイプのメッセージセグメントが追加されます

## 設定オプション

OneBotアダプターは各アカウントに対して以下のオプションを個別に設定します：

### アカウント設定
- `mode`: このアカウントの実行モード ("server" または "client")
- `server_path`: ServerモードでのWebSocketパス
- `server_token`: Serverモードでの認証Token（オプション）
- `client_url`: Clientモードで接続するWebSocketアドレス
- `client_token`: Clientモードでの認証Token（オプション）
- `enabled`: このアカウントを有効にするかどうか

### 内蔵デフォルト値
- 再接続間隔：30秒
- API呼び出しタイムアウト：30秒
- 最大リトライ回数：3回

### 設定例
```toml
[OneBotv11_Adapter.accounts.main]
mode = "server"
server_path = "/onebot-main"
server_token = "main_token"
enabled = true

[OneBotv11_Adapter.accounts.backup]
mode = "client"
client_url = "ws://127.0.0.1:3002"
client_token = "backup_token"
enabled = true

[OneBotv11_Adapter.accounts.test]
mode = "client"
client_url = "ws://127.0.0.1:3003"
enabled = false
```

### デフォルト設定
アカウントが設定されていない場合、アダプターは自動的に作成します：
```toml
[OneBotv11_Adapter.accounts.default]
mode = "server"
server_path = "/"
enabled = true
```

## 送信メソッドの戻り値

すべての送信メソッドはTaskオブジェクトを返し、直接 `await` して送信結果を取得できます。戻り値はErisPulseアダプターの標準化された戻り値仕様に従います：

```python
{
    "status": "ok",           // 実行ステータス
    "retcode": 0,             // リターンコード
    "data": {...},            // レスポンスデータ
    "self": {...},            // 自身の情報
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "onebot_raw": {...}       // 元のレスポンスデータ
}
```

### 複数アカウント送信構文

```python
# アカウント選択メソッド
await onebot.Send.Using("main").To("group", 123456).Text("主アカウントメッセージ")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# API呼び出し方法
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

## 非同期処理メカニズム

OneBotアダプターは非同期ノンブロッキング設計を採用し、以下を保証します：
1. メッセージ送信がイベント処理ループをブロックしないこと
2. 複数の同時送信操作が並行して行えること
3. APIレスポンスがタイムリーに処理されること
4. WebSocket接続がアクティブな状態を維持すること
5. 複数アカウントの並行処理、各アカウントが独立して実行されること

## エラー処理

アダプターは完全なエラー処理メカニズムを提供します：
1. ネットワーク接続例外の自動再接続（各アカウントの独立した再接続をサポート、間隔は30秒）
2. API呼び出しタイムアウト処理（固定30秒タイムアウト）
3. メッセージ送信失敗時のリトライ（最大3回までリトライ）

## イベント処理の強化

複数アカウントモードでは、すべてのイベントにアカウント情報が自動的に追加されます：
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "main"},  // 追加：イベントを送信したアカウントID（標準フィールド）
    "platform": "onebot11",
    // ... その他のイベントフィールド
}
```

## 管理インターフェース

```python
# すべてのアカウント情報を取得
accounts = onebot.accounts

# アカウントの接続状態を確認
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# アカウントを動的に有効化/無効化（アダプターの再起動が必要）
onebot.accounts["test"].enabled = False