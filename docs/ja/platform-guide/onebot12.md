# OneBot12プラットフォームの機能ドキュメント

OneBot12Adapterは、OneBot V12プロトコルに基づいて構築されたアダプタであり、ErisPulseフレームワークのベースラインプロトコルアダプタです。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.6.2
- 維持者: ErisPulse
- プロトコルバージョン: OneBot V12
- 最終更新日: 2026-11-10

## 基本情報

- プラットフォーム概要: OneBot V12は、ErisPulseフレームワークのベースラインプロトコルである汎用的なチャットボットアプリケーションインターフェース標準です。
- アダプタ名: OneBot12Adapter
- 対応プロトコル/APIバージョン: OneBot V12
- 多アカウント対応: 完全な多アカウントアーキテクチャ、複数のOneBot12アカウントを同時に設定・実行可能

## v5 ファンタジーの更新（4.3.0）

本アダプタはv5ファンタジーに準拠しています（段階的アップグレード、API互換性保持）：

- **BaseConverterの継承**: コンバーターの共通フィールド（id/time/platform/self/raw）は、フレームワークの build_base_event によって構築され、OB11のフィールド名（echo/time/self_id）で上書きされます。
- **spawn_backgroundタスクの所有者**: Clientモードの接続タスクはRuntime.spawn_backgroundに変更され、所有者（owner）が所属し、シャットダウン時に自動的にリソースを回収します。
- **フレームワークのソフト依存**: アダプタのインストール時にErisPulseのハード依存を宣言せず、pipの解析時にフレームワークのバージョンを調整するのを避けています。実行時にErisPulse>=2.7.1を検出し、バージョンが低すぎる場合はログを出力します。
- **起動時のバージョンログ**: 初期化時にOneBot12Adapter vX.Y.Zがロードされたことを出力します。

既存の機能（4.2.0からサポート）：多アカウント、Api DSL標準アクションマッピング（get_self_info→get_login_infoなど）、Request DSL（友人/グループリクエスト承認：event.approve() / event.reject()）、EventMixin、i18n。

## 標準化の対応

本節では、ErisPulseの標準化規格に準拠したアダプタの動作について説明します。規格の詳細は、SDKドキュメントの《リクエスト操作規格》（`docs/ja/standards/request-action-spec.md`）と《APIレスポンス規格》（`docs/ja/standards/api-response.md`）を参照してください。

### リクエストイベントとRequest DSL

- **request_idの保証**: リクエストイベントの透過時に、最上位の `request_id` フィールドを保証します（原生の `request_id` が優先され、OB11スタイルの実装では `flag` フィールドにマッピングされます；両方がない場合は合成されません）。Request DSLが使用するためです。
- **デフォルトアカウントの回帰**: `Request` DSL（`handle_quick_request`アクションに基づく）が明示的に `Using()` を指定してアカウントを指定しない場合、リクエストイベントの元アカウント（`request_context`）に回帰し、イベントチェーン内で `event.approve()`/`event.reject()`が正しくルーティングされるようにします。

### call_apiのエラー処理

- アカウントが接続されていない、または接続が閉じられている場合、`call_api`は `ConnectionError`をスローせず、標準の失敗レスポンス（`status="failed"`、`retcode=33001`）を返します。
- API呼び出しがタイムアウトした場合も、標準の失敗レスポンス（`retcode=33001`）を返します。

### アカウントフィールドの両対応とsend_context

- `call_api`は、標準フィールド `account_id` と旧フィールド名 `_account_id`（標準名が優先）の両方を受け付けます；フレームワークApiDSLは自動的に適応し、モジュールコードでは `account_id` を推奨します。
- `Send`/`Recall`/`Edit`/`Batch`の全メソッドは `send_context`を読み取ります：イベントチェーン内では自動的に現在のイベントの元アカウントを使用し、明示的に `Using()`で指定したアカウントが優先されます。

### イベントフィールドの注入

- すべてのイベントに `self.account_id`（元アカウント名）が注入され、多アカウントモードではイベントが正しく元アカウントにルーティングされます。
- すべてのイベントに `onebot12_raw_type`フィールドが必須で含まれます（元のイベントタイプ、イベント変換規格に準拠）。
- 表情/ステッカーのメッセージセグメント名は `onebot12_sticker`です（`.Sticker()`メソッド内部でこのセグメントを送信します）。

### エラーコード規格

| retcode | 含意 | 発生場面 |
|---------|------|----------|
| 0 | 成功 | アクションが正常に実行された |
| 33001 | ネットワークエラー | アカウントが接続されていない、接続が閉じられている、API呼び出しのタイムアウト |
| 10002 | 対応しないアクション | バックエンドが対応していないアクションリクエスト |
| 10003 | パラメータエラー | 必要なパラメータが不足している |

> バックエンドが返した元のレスポンスデータは `onebot12_raw`フィールドに保持されます。

---

## 標準APIアクション（Api DSL）

OneBot12バックエンドは、すべてのOB12標準アクション名を原生でサポートし、Api DSLはデフォルトでcall_apiを透過的に委譲します（マッピングは不要）：

```python
from ErisPulse import sdk
ob12 = sdk.adapter.get("onebot12")

result = await ob12.Api.get_self_info()
result = await ob12.Api.get_friend_list()
await ob12.Api.delete_message(message_id="MSG_ID")

# アカウントの指定（多アカウント）
result = await ob12.Api.Using("main").get_self_info()

# プラットフォーム拡張アクション
result = await ob12.Api.call("extend_action", param=1)
```

> 対応するアクションは、バックエンドの実装（NapCat/Lagrange/LLOneBotなど）に準拠します；対応していないアクションは、エラーを返してバックエンドに透過的に返されます。

---

## リクエスト操作（Request DSL）

OneBot12標準のhandle_quick_requestアクションに基づき、友人リクエストとグループ参加招待の承認/拒否を処理します。

### Eventの便利メソッド

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

### 手動でのRequest DSLの呼び出し

```python
await ob12.Request("request_flag").accept()
await ob12.Request("request_flag").reject()
await ob12.Request("request_flag").Using("main").accept()
```

---

## 対応するメッセージ送信タイプ

すべての送信メソッドは、チェーン式の構文で実現されます。例えば：

```python
from ErisPulse.Core import adapter
onebot12 = adapter.get("onebot12")

# デフォルトアカウントを使用して送信
await onebot12.Send.To("group", group_id).Text("Hello World!")

# 特定のアカウントを指定して送信
await onebot12.Send.To("group", group_id).Account("main").Text("メインアカウントからのメッセージ")
```

### 大小文字を区別しない呼び出し

すべての送信メソッドとチェーン式修飾メソッドは、大小文字を区別しない呼び出しをサポートし、アダプタは正しい標準メソッド名に自動的にマッピングします：

```python
# 以下のすべての呼び出しは等価です
await onebot12.Send.To("user", 123).Text("hello")
await onebot12.Send.To("user", 123).text("hello")
await onebot12.Send.To("user", 123).TEXT("hello")

# チェーン式修飾メソッドも同様にサポートされます
await onebot12.Send.To("group", 123).At(456).Text("hello")
await onebot12.Send.To("group", 123).at(456).TEXT("hello")
await onebot12.Send.To("group", 123).AT(456).text("hello")
```

### 対応していないメソッドの呼び出し

存在しないメソッドを呼び出した場合、アダプタは例外をスローするのではなく、フレンドリーなテキストの応答を返します：

```python
# 対応していないメソッドを呼び出す
result = await onebot12.Send.To("user", 123).UnsupportedMethod("test")

# 返される結果は送信されたテキストメッセージです
# メッセージ内容: [対応していない送信タイプ] メソッド名: UnsupportedMethod, パラメータ: [args[0]: 'test']
```

### 基本メッセージタイプ

- `.Text(text: str)`：テキストメッセージを送信
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：画像メッセージを送信（URL、Base64、またはbytesをサポート）
- `.Audio(file: Union[str, bytes], filename: str = "audio.ogg")`：音声メッセージを送信
- `.Voice(file: Union[str, bytes], filename: str = "voice.ogg")`：音声メッセージを送信（Audioの別名、OneBot11と互換性がある）
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：動画メッセージを送信

### チェーン式修飾メソッド（selfを返してチェーン呼び出しをサポート）

- `.At(user_id: Union[str, int])`：ユーザーを@する（複数回呼び出し可能）
- `.AtAll()`：全員を@する
- `.Reply(message_id: Union[str, int])`：メッセージに返信する

### 原始メッセージの送信

- `.Raw_ob12(message: Union[Dict, List[Dict]], **kwargs)`：OneBot12の原始形式のメッセージを送信（命名規則に準拠）

### その他のメッセージタイプ

- `.Sticker(file_id: str)`：スタンプ/ステッカーを送信（`onebot12_sticker`メッセージセグメント）
- `.Location(latitude: float, longitude: float, title: str = "", content: str = "")`：位置情報を送信

### 管理機能

- `.Recall(message_id: Union[str, int])`：メッセージを撤回する
- `.Edit(message_id: Union[str, int], content: Union[str, List[Dict]])`：メッセージを編集する
- `.Raw(message_segments: List[Dict])`：OneBot12の原生メッセージセグメントを送信
- `.Batch(target_ids: List[str], message: Union[str, List[Dict]], target_type: str = "user")`：複数の宛先にメッセージを送信

## OneBot12標準イベント

OneBot12アダプタはOneBot12標準に完全に準拠しており、イベント形式は変換を必要とせず、フレームワークに直接送信されます。

### 新機能：元のイベントタイプフィールド

`standards/event-conversion.md`規格に準拠し、すべてのイベントは元のイベントタイプフィールド `onebot12_raw_type`を保持します：

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

# グループメンバーの削除
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

### リクエストイベント (Request Events)

```python
# 友人リクエスト
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "friend",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "comment": "申請メッセージ",
    "request_id": "request-flag",
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
    "request_id": "request-flag",
    "flag": "request-flag",
    "sub_type": "invite",
    "time": 1234567890
}
```

### メタイベント (Meta Events)

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

- `mode`: そのアカウントの実行モード ("server" または "client")
- `server_path`: ServerモードでのWebSocketパス
- `server_token`: Serverモードでの認証トークン（オプション）
- `client_url`: Clientモードで接続するWebSocketのURL
- `client_token`: Clientモードでの認証トークン（オプション）
- `enabled`: そのアカウントを有効にするかどうか
- `platform`: プラットフォーム識別子、デフォルトは "onebot12"
- `implementation`: 実装識別子、例えば "go-cqhttp"（オプション）

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

アカウントが設定されていない場合、アダプタは自動的に作成されます：

```toml
[OneBotv12_Adapter.accounts.default]
mode = "server"
server_path = "/onebot12"
enabled = true
platform = "onebot12"
```

## 送信メソッドの戻り値

### メッセージ送信メソッド

`.Text()`, `.Image()`, `.Raw_ob12()`などのすべてのメッセージ送信メソッドは、`asyncio.Task`オブジェクトを返し、`await`で送信結果を取得できます：

```python
task = await onebot12.Send.To("group", 123456).Text("Hello")
```

### チェーン式修飾メソッド

すべてのチェーン式修飾メソッド（`.At()`, `.AtAll()`, `.Reply()`）は`self`を返し、チェーン呼び出しが可能です：

```python
# 複数の修飾メソッドを組み合わせて使用
await onebot12.Send.To("group", 123456).Reply("msg123").At(789).At(790).Text("テキスト")
```

## APIレスポンスの標準

アダプタはErisPulseの標準化された返却規格を遵守します（`standards/api-response.md`）：

```python
# 成功レスポンス
{
    "status": "ok",              // 必須：実行ステータス
    "retcode": 0,                // 必須：返却コード（0は成功）
    "data": {                     // 必須：レスポンスデータ
        "message_id": "123456",
        "time": 1632847927.599013
    },
    "message_id": "123456",       // 必須：メッセージID（無ければ空文字列）
    "message": "",                // 必須：エラーメッセージ（成功時は空）
    "echo": "1234",               // オプション：リクエスト中のechoをそのまま返す
    "onebot12_raw": {...}        // オプション：元のレスポンスデータ
}

# 失敗レスポンス
{
    "status": "failed",           // 必須：実行ステータス
    "retcode": 10003,            // 必須：返却コード（0以外は失敗）
    "data": None,                // 必須：失敗時はnull
    "message_id": "",            // 必須：失敗時は空文字列
    "message": "必要なパラメータが不足しています",    // 必須：エラーメッセージ
    "echo": "1234",              // オプション：リクエスト中のechoをそのまま返す
    "onebot12_raw": {...}        // オプション：元のレスポンスデータ
}
```

### エラーコード規格

OneBot12標準のエラーコードに準拠します：

- **0**: 成功
- **1xxxx**: アクションリクエストエラー
- **2xxxx**: アクションハンドラーエラー
- **3xxxx**: アクション実行エラー（33001はネットワークタイムアウト）

### 多アカウント送信の構文

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

OneBot12アダプタは非同期非ブロッキング設計を採用しています：

1. メッセージ送信はイベント処理ループをブロックしません。
2. 複数の並行送信操作を同時に実行できます。
3. APIレスポンスは適切に処理されます。
4. WebSocket接続はアクティブな状態を維持します。
5. 複数のアカウントを並行して処理し、各アカウントは独立して動作します。

## エラー処理

アダプタは包括的なエラー処理メカニズムを提供します：

1. ネットワーク接続エラーは自動的に再接続されます（各アカウントごとに独立した再接続をサポートし、30秒の間隔で再接続されます）。
2. API呼び出しがタイムアウトした場合の処理（固定30秒のタイムアウト、タイムアウト時は `retcode=33001`の標準失敗レスポンスを返します）。
3. アカウントが接続されていない、または接続が閉じている場合、`call_api`は `retcode=33001`の標準失敗レスポンスを返し、`ConnectionError`をスローしません。
4. 対応していないメソッドの呼び出しは、フレンドリーなテキストの応答を返します。

## イベント処理の強化

多アカウントモードでは、すべてのイベントにアカウント情報が自動的に追加されます：

```python
{
    "type": "message",
    "onebot12_raw_type": "message",  // 元のイベントタイプ
    "detail_type": "private",
    "self": {"user_id": "123456"},  // 送信イベントのアカウントID（標準フィールド）
    "platform": "onebot12",
    // ... その他のイベントフィールド
}
```

## 管理インターフェース

```python
# すべてのアカウント情報を取得
accounts = onebot12.accounts

# アカウントの接続状態をチェック
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot12.connections.items()
}

# アカウントの有効/無効切り替え（アダプタの再起動が必要）
onebot12.accounts["test"].enabled = False
```

## OneBot12標準の機能

### メッセージセグメントの標準

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

### APIの標準

OneBot12標準API規格に準拠します：

- `send_message`: メッセージを送信
- `delete_message`: メッセージを撤回
- `edit_message`: メッセージを編集
- `get_message`: メッセージを取得
- `get_self_info`: 自身の情報を取得
- `get_user_info`: ユーザー情報を取得
- `get_group_info`: グループ情報を取得

## 最適な実践

1. **設定管理**: 複数の用途を持つロボットを分けて管理するために、多アカウント設定の使用を推奨します。
2. **エラー処理**: 常にAPI呼び出しの返り値のステータスをチェックしてください。
3. **メッセージ送信**: 適切なメッセージタイプを使用し、対応していないメッセージを送信しないようにしてください。
4. **接続監視**: 定期的に接続状態をチェックし、サービスの可用性を確保してください。
5. **パフォーマンス最適化**: バッチ送信の場合はBatchメソッドを使用し、ネットワークのオーバーヘッドを減らしてください。
6. **メソッド呼び出し**: 推奨される大文字キャメルケース（例: `.Text()`）を使用することを推奨しますが、小文字形式もサポートしており、異なるプログラミングスタイルに適応できます（この方法は旧バージョンとの互換性がありません）。