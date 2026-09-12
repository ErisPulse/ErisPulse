# OneBot12プラットフォーム仕様ドキュメント

OneBot12Adapter は、OneBot V12 プロトコルに基づいて構築されたアダプターであり、ErisPulse フレームワークの基本プロトコルアダプターです。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.3.0
- メンテナ: ErisPulse
- プロトコルバージョン: OneBot V12

## 基本情報

- プラットフォーム概要: OneBot V12 は、ErisPulseフレームワークのベースラインプロトコルである汎用的なチャットボットアプリケーションインターフェース標準です。
- アダプタ名: OneBot12Adapter
- 対応するプロトコル/APIバージョン: OneBot V12
- 多アカウント対応: 完全な多アカウントアーキテクチャを採用しており、複数のOneBot12アカウントを同時に設定・実行することができます。

## v5 フレームワークの更新（4.3.0）

このアダプタは v5 フレームワークに準拠しました（段階的なアップグレード、API は互換性があります）：

- **BaseConverter 継承**：コンバーターの共通フィールド（id/time/platform/self/raw）は、フレームワークの build_base_event によって構築され、OB11 のフィールド名（echo/time/self_id）に従って上書きされます。
- **spawn_background でのタスクの所有**：Client モードの接続タスクは、asyncio.spawn_background を使用し、タスクの所有者を明示的に指定し、シャットダウン時に自動的にリソースを回収します。
- **フレームワークのソフト依存**：アダプタのインストール時に ErisPulse をハード依存として宣言しなくなりました。これにより、pip の解析時にフレームワークのバージョンが誤って調整されるのを回避します。実行時に ErisPulse >= 2.7.1 を検出し、バージョンが低すぎる場合はログで警告を出します。
- **起動時のバージョンログ**：初期化時に OneBotAdapter v4.3.0 がロードされたことを出力します。

既存の機能（4.2.0 以降でサポート）：複数アカウント、Api DSL の標準アクションマッピング（get_self_info→get_login_info など）、Request DSL（友人/グループリクエストの承認：event.approve() / event.reject()）、EventMixin、i18n。

## 標準Apiアクション（Api DSL）

OneBot12 バックエンドは、OB12の標準アクション名をすべてネイティブでサポートしています。Api DSL はデフォルトで call_api を直接透過的に委譲します（マッピングは不要です）：

```python
from ErisPulse import sdk
ob12 = sdk.adapter.get("onebot12")

result = await ob12.Api.get_self_info()
result = await ob12.Api.get_friend_list()
await ob12.Api.delete_message(message_id="MSG_ID")

# アカウントを指定（複数アカウント）
result = await ob12.Api.Using("main").get_self_info()

# プラットフォーム拡張アクション
result = await ob12.Api.call("extend_action", param=1)
```

> アクションのサポートは、バックエンドの実装（NapCat/Lagrange/LLOneBot など）に準じます。サポートされていないアクションは、バックエンドがエラーを返し透過的に転送します。

## リクエスト操作（Request DSL）

OneBot12 標準の handle_quick_request 動作に基づき、フレンドリクエストとグループ参加招待の承認/拒否を処理します。

### Event 便利メソッド

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    if event.get("platform") != "onebot12":
        return
    comment = event.get("comment", "")
    if comment == "passphrase":
        await event.approve()      # 承認
    else:
        await event.reject()       # 拒否
```

### 手動による Request DSL 呼び出し

```python
await ob12.Request("request_flag").accept()
await ob12.Request("request_flag").reject()
await ob12.Request("request_flag").Using("main").accept()
```

## 支持するメッセージ送信タイプ

すべての送信メソッドは、チェーン式の構文で実装されています。例：

```python
from ErisPulse.Core import adapter
onebot12 = adapter.get("onebot12")

# デフォルトのアカウントを使って送信
await onebot12.Send.To("group", group_id).Text("Hello World!")

# 特定のアカウントを使って送信
await onebot12.Send.To("group", group_id).Account("main").Text("来自主アカウントのメッセージ")
```

### 大文字小文字を区別しない呼び出し

すべての送信メソッドとチェーン式修飾メソッドは、大文字小文字を区別しない呼び出しをサポートしており、アダプターは正しい標準メソッド名に自動的にマッピングします：

```python
# 以下すべての呼び出し方法は等価です
await onebot12.Send.To("user", 123).Text("hello")
await onebot12.Send.To("user", 123).text("hello")
await onebot12.Send.To("user", 123).TEXT("hello")

# チェーン式修飾メソッドも同様にサポート
await onebot12.Send.To("group", 123).At(456).Text("hello")
await onebot12.Send.To("group", 123).at(456).TEXT("hello")
await onebot12.Send.To("group", 123).AT(456).text("hello")
```

### 支持されていないメソッドの呼び出し

存在しないメソッドを呼び出した場合、アダプターは例外をスローするのではなく、ユーザーにわかりやすいテキストのメッセージを返します：

```python
# 支持されていないメソッドを呼び出す
result = await onebot12.Send.To("user", 123).UnsupportedMethod("test")

# 戻り値は送信されたテキストメッセージです
# メッセージ内容: [サポートされていない送信タイプ] メソッド名: UnsupportedMethod, パラメータ: [args[0]: 'test']
```

### 基本的なメッセージタイプ

- `.Text(text: str)`：純粋なテキストメッセージを送信します
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：画像メッセージを送信します（URL、Base64、またはbytesをサポート）
- `.Audio(file: Union[str, bytes], filename: str = "audio.ogg")`：音声メッセージを送信します
- `.Voice(file: Union[str, bytes], filename: str = "voice.ogg")`：音声メッセージを送信します（OneBot11と互換性のあるAudioの別名）
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：ビデオメッセージを送信します

### チェーン式修飾メソッド（selfを返してチェーン式呼び出しをサポート）

- `.At(user_id: Union[str, int])`：ユーザーを@します（複数回呼び出すことが可能です）
- `.AtAll()`：全員を@します
- `.Reply(message_id: Union[str, int])`：メッセージに返信します

### 原始メッセージ送信

- `.Raw_ob12(message: Union[Dict, List[Dict]], **kwargs)`：OneBot12の原始形式メッセージを送信します（命名規則に準拠）

### その他のメッセージタイプ

- `.Sticker(file_id: str)`：スタンプ/ステッカーを送信します
- `.Location(latitude: float, longitude: float, title: str = "", content: str = "")`：位置情報を送信します

### 管理機能

- `.Recall(message_id: Union[str, int])`：メッセージを撤回します
- `.Edit(message_id: Union[str, int], content: Union[str, List[Dict]])`：メッセージを編集します
- `.Raw(message_segments: List[Dict])`：OneBot12の原生メッセージセグメントを送信します
- `.Batch(target_ids: List[str], message: Union[str, List[Dict]], target_type: str = "user")`：一括でメッセージを送信します

## OneBot12標準イベント

OneBot12アダプターはOneBot12標準を完全に遵守しており、イベント形式の変換は不要で、フレームワークに直接送信されます。

### 新機能：元のイベントタイプフィールド

`standards/event-conversion.md` 規格に準拠し、すべてのイベントには元のイベントタイプフィールド `onebot12_raw_type` が保持されます：

```python
{
    "id": "event-id",
    "type": "message",              # イベントタイプ
    "onebot12_raw_type": "message", # 元のイベントタイプ（typeと同じ）
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}
```

### メッセージイベント (Message Events)

```python
# プライベートチャットメッセージ
{
    "id": "event-id",
    "type": "message",
    "onebot12_raw_type": "message",
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}

# グループチャットメッセージ
{
    "id": "event-id",
    "type": "message",
    "onebot12_raw_type": "message",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "group_id": "group-id",
    "message": [{"type": "text", "data": {"text": "Hello group"}}],
    "alt_message": "Hello group",
    "time": 1234567890
}
```

### 通知イベント (Notice Events)

```python
# グループメンバーの追加
{
    "id": "event-id",
    "type": "notice",
    "onebot12_raw_type": "notice",
    "detail_type": "group_member_increase",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "approve",
    "time": 1234567890
}

# グループメンバーの削減
{
    "id": "event-id",
    "type": "notice",
    "onebot12_raw_type": "notice",
    "detail_type": "group_member_decrease",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "leave",
    "time": 1234567890
}
```

### 要求イベント (Request Events)

```python
# フレンドリクエスト
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "friend",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "comment": "申請メッセージ",
    "flag": "request-flag",
    "time": 1234567890
}

# グループ招待リクエスト
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "comment": "申請メッセージ",
    "flag": "request-flag",
    "sub_type": "invite",
    "time": 1234567890
}
```

### 元イベント (Meta Events)

```python
# ライフサイクルイベント
{
    "id": "event-id",
    "type": "meta_event",
    "onebot12_raw_type": "meta_event",
    "detail_type": "lifecycle",
    "self": {"user_id": "bot-id"},
    "sub_type": "enable",
    "time": 1234567890
}

# ハートビートイベント
{
    "id": "event-id",
    "type": "meta_event",
    "onebot12_raw_type": "meta_event",
    "detail_type": "heartbeat",
    "self": {"user_id": "bot-id"},
    "interval": 5000,
    "status": {"online": true},
    "time": 1234567890
}
```

## 設定オプション

### アカウント設定

各アカウントは以下のオプションを個別に設定できます：

- `mode`: このアカウントの実行モード ("server" または "client")
- `server_path`: ServerモードにおけるWebSocketのパス
- `server_token`: Serverモードにおける認証トークン（オプション）
- `client_url`: Clientモードで接続するWebSocketのアドレス
- `client_token`: Clientモードにおける認証トークン（オプション）
- `enabled`: アカウントを有効にするかどうか
- `platform`: プラットフォーム識別子、デフォルトは "onebot12"
- `implementation`: 実装識別子、例: "go-cqhttp"（オプション）

### 設定例

```toml
[OneBotv12_Adapter.accounts.main]
mode = "server"
server_path = "/onebot12-main"
server_token = "main_token"
enabled = true
platform = "onebot12"
implementation = "go-cqhttp"

[OneBotv12_Adapter.accounts.backup]
mode = "client"
client_url = "ws://127.0.0.1:3002"
client_token = "backup_token"
enabled = true
platform = "onebot12"
implementation = "shinonome"

[OneBotv12_Adapter.accounts.test]
mode = "client"
client_url = "ws://127.0.0.1:3003"
enabled = false
```

### デフォルト設定

アカウントの設定が一切ない場合、アダプターは自動的に以下のようにデフォルトアカウントを作成します：

```toml
[OneBotv12_Adapter.accounts.default]
mode = "server"
server_path = "/onebot12"
enabled = true
platform = "onebot12"
```

## 送信メソッドの戻り値

### メッセージ送信メソッド
すべてのメッセージ送信メソッド（例：`.Text()`, `.Image()`, `.Raw_ob12()` など）は、`asyncio.Task` オブジェクトを返します。これにより、送信結果を直接 await で取得できます。

```python
task = await onebot12.Send.To("group", 123456).Text("Hello")
```

### チェーン修飾メソッド
すべてのチェーン修飾メソッド（例：`.At()`, `.AtAll()`, `.Reply()`）は、`self` を返し、チェーン呼び出しをサポートします。

```python
# 複数の修飾メソッドを組み合わせて使用
await onebot12.Send.To("group", 123456).Reply("msg123").At(789).At(790).Text("テキスト")
```

## APIレスポンス標準

アダプターは ErisPulse の標準化された返却規格（`standards/api-response.md`）に準拠しています：

```python
# 成功時のレスポンス
{
    "status": "ok",              # 必須：実行ステータス
    "retcode": 0,                # 必須：返却コード（0は成功を示す）
    "data": {                     # 必須：レスポンスデータ
        "message_id": "123456",
        "time": 1632847927.599013
    },
    "message_id": "123456",       # 必須：メッセージID（存在しない場合は空文字列）
    "message": "",                # 必須：エラーメッセージ（成功時は空）
    "echo": "1234",               # オプション：リクエスト中のechoをそのまま返す
    "onebot12_raw": {...}        # オプション：元のレスポンスデータ
}

# 失敗時のレスポンス
{
    "status": "failed",           # 必須：実行ステータス
    "retcode": 10003,            # 必須：返却コード（0以外は失敗を示す）
    "data": None,                # 必須：失敗時はnull
    "message_id": "",            # 必須：失敗時は空文字列
    "message": "必要なパラメータが不足しています",    # 必須：エラーメッセージ
    "echo": "1234",              # オプション：リクエスト中のechoをそのまま返す
    "onebot12_raw": {...}        # オプション：元のレスポンスデータ
}
```

### エラーコード規格

OneBot12 の標準エラーコードに準拠します：

- **0**: 成功
- **1xxxx**: 動作要求エラー
- **2xxxx**: 動作処理エラー
- **3xxxx**: 動作実行エラー（33001はネットワークタイムアウト）

### 複数アカウントによる送信構文

```python
# アカウント選択方法
await onebot12.Send.Using("main").To("group", 123456).Text("メインアカウントのメッセージ")
await onebot12.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# API呼び出し方法
await onebot12.call_api("send_message", account_id="main", 
    detail_type="group", group_id=123456, 
    content=[{"type": "text", "data": {"text": "Hello"}}])
```

## 非同期処理メカニズム

OneBot12アダプターは非同期非ブロッキング設計を採用しています：

1. メッセージ送信はイベント処理ループをブロックしません
2. 複数の並行送信操作を同時に実行できます
3. APIの応答を即時に処理できます
4. WebSocket接続はアクティブな状態を維持します
5. 複数アカウントの並行処理が可能で、各アカウントは独立して動作します

## エラー処理

アダプタは包括的なエラー処理メカニズムを提供します：

1. ネットワーク接続異常時の自動再接続（各アカウントごとに個別に再接続が可能、間隔は30秒）
2. API呼び出しのタイムアウト処理（固定30秒のタイムアウト）
3. メッセージ送信失敗時の自動リトライ（最大3回のリトライ）
4. 対応していないメソッドの呼び出しは、親しみやすいテキストのメッセージを返します

## イベント処理の強化

複数アカウントモードでは、すべてのイベントにアカウント情報が自動的に追加されます：

```python
{
    "type": "message",
    "onebot12_raw_type": "message",  // 元のイベントタイプ
    "detail_type": "private",
    "self": {"user_id": "123456"},  // イベントを送信したアカウントID（標準フィールド）
    "platform": "onebot12",
    // ... その他のイベントフィールド
}
```

## 管理インターフェース

```python
# すべてのアカウント情報を取得
accounts = onebot12.accounts

# アカウントの接続状態を確認
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot12.connections.items()
}

# アカウントの動的有効化/無効化（アダプタの再起動が必要）
onebot12.accounts["test"].enabled = False
```

## OneBot12標準機能

### メッセージセグメント標準

OneBot12は標準化されたメッセージセグメント形式を使用します：

```python
# テキストメッセージセグメント
{"type": "text", "data": {"text": "Hello"}}

# 画像メッセージセグメント
{"type": "image", "data": {"file_id": "image-id"}}

# メンションメッセージセグメント
{"type": "mention", "data": {"user_id": "user-id", "user_name": "Username"}}

# 返信メッセージセグメント
{"type": "reply", "data": {"message_id": "msg-id"}}
```

### API標準

OneBot12標準API規格に従います：

- `send_message`: メッセージ送信
- `delete_message`: メッセージ撤回
- `edit_message`: メッセージ編集
- `get_message`: メッセージ取得
- `get_self_info`: 自身の情報を取得
- `get_user_info`: ユーザー情報を取得
- `get_group_info`: グループ情報を取得

## 最佳実践

1. **設定管理**: さまざまな用途のロボットを分けて管理するために、複数アカウントの設定を使用することを推奨します。
2. **エラー処理**: API呼び出しの返り値ステータスを常にチェックしてください。
3. **メッセージ送信**: 送信可能なメッセージの種類を使用し、サポートされていないメッセージを送信しないようにしてください。
4. **接続監視**: 接続状態を定期的にチェックし、サービスの可用性を確保してください。
5. **パフォーマンス最適化**: バッチ送信時は `Batch` メソッドを使用し、ネットワークのオーバーヘッドを減らしてください。
6. **メソッド呼び出し**: 標準の大文字キャメルケース命名法（例: `.Text()`）を使用することを推奨しますが、異なるプログラミングスタイルとの互換性を考慮して小文字形式もサポートしています（この形式は旧バージョンとの互換性が失われる可能性があります）。