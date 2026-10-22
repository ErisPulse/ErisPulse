# ErisPulse リクエスト操作仕様

> [!TIP]
> **このドキュメントを読むべきケース**：アダプターで友達リクエスト/グループ招待を処理する必要がある場合（リクエストイベントの変換や `accept`/`reject` の実装）、またはモジュールで `event.approve()` / `event.reject()` を使ってリクエストを承認する場合に、本文を参照してください。該当しない場合は読み飛ばしてください。

本ドキュメントは、ErisPulse アダプターにおけるリクエストイベント操作の標準化された仕様を定義します。リクエストイベントのフィールド要件、Request DSL の使用方法、およびアダプターの実装要件が含まれます。

## 1. 概要

リクエストイベント（`type: "request"`）は、OneBot12 標準で定義された特殊なイベントタイプであり、Bot が意思決定を行う必要のあるリクエスト（友達リクエスト、グループ招待など）を表します。

メッセージイベントとは異なり、リクエストイベントは**双方向のやり取り**が必要です：
1. **受信**：アダプターがプラットフォームのネイティブリクエストを標準リクエストイベントに変換する
2. **応答**：モジュールが `Request` DSL または `Event.approve()`/`Event.reject()` を通じて操作を実行する

```
プラットフォームのネイティブリクエストイベント
    │
    ▼
Converter.convert()        ← アダプター実装（正方向の変換）
    │
    ▼
標準リクエストイベント (request_id を含む)
    │
    ├─→ モジュールハンドラー @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← リクエストを承認
    │       └─→ event.reject()      ← リクエストを拒否
    │               │
    │               ▼
    │       adapter.Request(request_id).accept()
    │               │
    │               ▼
    │       BaseAdapter.Request.accept()  ← アダプターでオーバーライド
    │               │
    │               ▼
    │       プラットフォーム API 呼び出し
    │
    └─→ またはアダプター経由で直接操作
            await adapter.Request("req_id").accept()
```

## 2. リクエストイベントのフィールド要件

### 2.1 標準フィールド

リクエストイベントは、OneBot12 の標準フィールドに加えて、以下のフィールドを含む必要があります：

| フィールド | 型 | 必須 | 説明 |
|------|------|------|------|
| `request_id` | string | **強く推奨** | リクエスト識別子。承認/拒否操作に使用 |
| `user_id` | string | はい | リクエスト送信者の ID |
| `user_nickname` | string | いいえ | リクエスト送信者のニックネーム |
| `comment` | string | いいえ | リクエストの添付メッセージ |

### 2.2 `request_id` フィールド

`request_id` はリクエスト操作の中核となる識別子です：

- **用途**：操作対象のリクエストを識別し、`Request` DSL から使用される
- **生成ルール**：
  - プラットフォームのネイティブなリクエスト識別子を優先的に使用する（OneBot11 の `flag` フィールド、Telegram の `chat_invite_link` など）
  - プラットフォームにネイティブなリクエスト ID がない場合、アダプターは一意の識別子を生成する必要がある（推奨形式：`{platform}_{timestamp}_{user_id}`）
- **一意性**：同一プラットフォームの範囲内で一意であること
- **欠落時の動作**：`request_id` が欠落している場合、`event.approve()` / `event.reject()` は `ValueError` をスローする

### 2.3 リクエストイベントの例

```json
{
  "id": "evt_123456",
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
  "comment": "友達リクエストをお願いします",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. Request DSL

### 3.1 メソッドチェーン

`Request` は `Send` と同じスタイルのメソッドチェーンインターフェースを提供します：

```python
# 基本的な使い方
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Bot アカウントを指定
await adapter.Request("req_id").Using("bot1").accept()

# 備考を付ける（kwargs 経由）
await adapter.Request("req_id").accept(comment="ようこそ")
await adapter.Request("req_id").reject(comment="今は追加しません")

# 組み合わせて使用
await adapter.Request("req_id").Using("bot1").accept(comment="ようこそ")
```

### 3.2 メソッド一覧

| メソッド | 説明 | 戻り値 |
|------|------|--------|
| `Using(account_id)` | 操作を実行する Bot アカウントを指定 | `RequestDSL`（メソッドチェーン対応） |
| `accept(**kwargs)` | リクエストを承認 | `asyncio.Task`（await 後に標準レスポンスを返す） |
| `reject(**kwargs)` | リクエストを拒否 | `asyncio.Task`（await 後に標準レスポンスを返す） |

### 3.3 戻り値の形式

操作は標準 API レスポンス形式を返します：

**成功**：
```json
{
    "status": "ok",
    "retcode": 0,
    "data": null,
    "message_id": "",
    "message": ""
}
```

**失敗**：
```json
{
    "status": "failed",
    "retcode": 34001,
    "data": null,
    "message_id": "",
    "message": "リクエストが存在しないか、期限切れです"
}
```

**未実装**（アダプターが `accept`/`reject` をオーバーライドしていない場合）：
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "プラットフォーム MyAdapter はリクエスト操作 (accept) を実装していません"
}
```

## 4. Event の便利メソッド

`Event` ラップクラスは、リクエストイベントハンドラーでの使用に適した便利メソッドを提供します：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # リクエスト ID を確認
    request_id = event.get_request_id()
    if not request_id:
        print("警告：リクエストイベントに request_id がありません")
        return
    
    # リクエストを承認
    result = await event.approve()
    
    # またはリクエストを拒否
    # result = await event.reject(comment="今は友達追加しません")
    
    # 結果を確認
    if result.get("status") == "ok":
        print("操作に成功しました")
    else:
        print(f"操作に失敗しました: {result.get('message')}")
```

### 4.1 Event メソッド一覧

| メソッド | 説明 | 戻り値 |
|------|------|--------|
| `get_request_id()` | リクエスト ID を取得 | `str` |
| `approve(comment=None)` | 現在のリクエストイベントを承認 | 標準レスポンス形式 |
| `reject(comment=None)` | 現在のリクエストイベントを拒否 | 標準レスポンス形式 |

## 5. アダプター実装要件

### 5.1 コンバーターの要件

アダプターのコンバーターは、リクエストイベントを変換する際に、`request_id` フィールドを正しく設定し**なければなりません**：

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """プラットフォームのネイティブリクエストイベントを変換する"""
    return {
        "id": self._generate_event_id(raw_event),
        "time": int(time.time()),
        "type": "request",
        "detail_type": self._map_request_type(raw_event),  # "friend" または "group"
        "platform": self._platform_name,
        "self": {
            "platform": self._platform_name,
            "user_id": str(self._bot_id),
        },
        "user_id": str(raw_event.get("user_id", "")),
        "user_nickname": raw_event.get("nickname", ""),
        "comment": raw_event.get("message", ""),
        "request_id": self._extract_request_id(raw_event),  # ← 重要なフィールド
        f"{self._platform_name}_raw": raw_event,
        f"{self._platform_name}_raw_type": raw_event.get("type", ""),
    }

def _extract_request_id(self, raw_event: dict) -> str:
    """
    プラットフォームのネイティブイベントからリクエスト ID を抽出する
    
    プラットフォームのネイティブなリクエスト識別子を優先的に使用し、
    存在しない場合は一意の ID を生成する
    """
    # プラットフォームのネイティブ ID を優先的に使用
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # フォールバック：一意の ID を生成
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request 内部クラスの実装

アダプターは、`Request` 内部クラスで `accept` と `reject` をオーバーライドするだけです：

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform のリクエスト操作実装"""
        
        def accept(self, **kwargs):
            """
            リクエストを承認する
            
            :param kwargs: 拡張パラメータ。例：comment="備考"
            :return: asyncio.Task
            """
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=True,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"リクエスト操作に失敗しました: {e}",
                    }
            
            return self._create_task(_do())
        
        def reject(self, **kwargs):
            """リクエストを拒否する"""
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=False,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"リクエスト操作に失敗しました: {e}",
                    }
            
            return self._create_task(_do())
```

### 5.3 プラットフォームがリクエスト操作をサポートしていない場合

プラットフォーム自体が友達リクエスト/グループ招待操作をサポートしていない場合（一部のプラットフォームではリクエストが自動処理されるなど）、アダプターは以下の対応が可能です：

1. **`Request` 内部クラスをオーバーライドしない**：基底クラスのデフォルト実装を使用すると、`accept()`/`reject()` の呼び出し時に `retcode=10002` が返される
2. **変換時に `request_id` をスキップする**：`request_id` を生成せず、`event.approve()` に `ValueError` をスローさせる
3. **ログを記録する**：`accept`/`reject` 内で警告を記録し、適切なエラーコードを返す

### 5.4 まとめ：Send と Request の並列構成

アダプターには 2 つの並列した DSL 内部クラスがあり、それぞれが役割を担っています：

```
BaseAdapter
├── Send(SendDSL)     ← メッセージ送信
│   ├── Raw_ob12()    ← 必須実装
│   ├── Text()        ← 推奨実装
│   └── Image()       ← 必要に応じて実装
│
└── Request(RequestDSL) ← リクエスト操作
    ├── accept()        ← 必要に応じて実装
    └── reject()        ← 必要に応じて実装
```

### 5.5 アダプターの `__init__` に関する注意事項

`Request` 内部クラスの `__init__` をオーバーライドする場合は、パラメータを透過的に渡し、`super().__init__()` を呼び出す必要があります。詳細は [アダプター開発入門 - `__init__` の注意事項](../developer-guide/adapters/getting-started.md#init-注意事項) を参照してください（`Request` も同様で、パラメータは `adapter, request_id, account_id` です）。

## 6. アダプター実装チェックリスト

### 基本要件
- [ ] `__init__` をオーバーライドした場合は `super().__init__()` を呼び出していること（Send / Request ファクトリの初期化を確保）

### リクエストイベントの変換
- [ ] リクエストイベントに `request_id` フィールドが含まれている（強く推奨）
- [ ] `detail_type` が `"friend"` または `"group"` に正しくマッピングされている
- [ ] プラットフォームの生データが `{platform}_raw` フィールドに保持されている
- [ ] `request_id` の生成ルールがドキュメントに記載されている

### リクエスト操作
- [ ] `Request` 内部クラスが実装されている（プラットフォームがリクエスト操作をサポートする場合）
- [ ] `accept()` メソッドが実装されている
- [ ] `reject()` メソッドが実装されている
- [ ] 操作が標準 API レスポンス形式を返している
- [ ] サポートされていない操作は `retcode=10002` を返す
- [ ] ネットワークエラーは `retcode=33xxx` を返す（API レスポンス標準に従う）

## 7. エラーコードの拡張

リクエスト操作に関連する**アダプター実装層**の推奨エラーコード（[API レスポンス標準](api-response.md) §3.2 に従い、
`34xxx` プラットフォームエラーセグメントの下 3 桁をカスタム定義）：

| エラーコード | エラー名 | 説明 |
|-------|-------|------|
| 34001 | Request Not Found | リクエストが存在しないか、期限切れです |
| 34002 | Request Already Handled | リクエストはすでに処理されています |
| 34003 | Request Not Supported | プラットフォームはこのタイプのリクエスト操作をサポートしていません |
| 34004 | Permission Denied | Bot にはこのリクエストを処理する権限がありません（プラットフォームから返却） |

> **フレームワークコードとの境界**：上記の `340xx` は**プラットフォーム/アダプター**が返すリクエスト処理の失敗です。
> ErisPulse フレームワークは、`scope.actions` で特定のモジュールの request アクションが無効化されている場合、**アダプターを呼び出す前に**
> 直接 `34601`（Action Denied、[API レスポンス標準 §5.3](api-response.md#53-フレームワーク拡張リターンコード34xxx-プラットフォームエラーセグメントの下3桁カスタム) を参照）を返します。
> 両者は互いに代替するものではありません。まず `34601` のフレームワークゲートを通過し、その後プラットフォーム層の `340xx` エラーに到達します。

## 8. 関連ドキュメント

**リクエスト操作を実装する際に併せて参照**：
- [イベント変換標準](event-conversion.md) - 完全なイベント変換仕様（`request_id` フィールド要件を含む）
- [API レスポンス標準](api-response.md) - アダプターの API レスポンス形式標準（操作の戻り値とエラーコード）

**同一アダプターのその他の DSL**：
- [送信メソッド仕様](send-method-spec.md) - Send クラスのメソッド命名およびパラメータ仕様
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング関係