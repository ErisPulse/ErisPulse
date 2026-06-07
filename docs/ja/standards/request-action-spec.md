# ErisPulse リクエスト操作仕様書

このドキュメントでは、ErisPulse アダプターにおけるリクエストイベント操作の標準化仕様を定義しています。これには、リクエストイベントのフィールド要件、Request DSL（ドメイン固有言語）の使用方法、およびアダプターの実装要件が含まれます。

## 1. 概要

リクエストイベント（`type: "request"`）は、OneBot12 標準で定義される特殊なイベントタイプで、Bot が決定を下す必要があるリクエスト（友達申請、グループ招待など）を表します。

メッセージイベントとは異なり、リクエストイベントには**双方向の相互作用**が必要です：
1. **受信**：アダプターがプラットフォームのネイティブリクエストを標準のリクエストイベントに変換します
2. **応答**：モジュールが `Request` DSL または `Event.approve()` / `Event.reject()` を使用して操作を実行します

```
プラットフォームのネイティブリクエストイベント
    │
    ▼
Converter.convert()        ← アダプターの実装（正の変換）
    │
    ▼
標準リクエストイベント (含 request_id)
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
    │       BaseAdapter.Request.accept()  ← アダプターのオーバーライド
    │               │
    │               ▼
    │       プラットフォーム API の呼び出し
    │
    └─→ またはアダプター経由で直接操作
            await adapter.Request("req_id").accept()
```

## 2. リクエストイベントフィールド要件

### 2.1 標準フィールド

リクエストイベントには、OneBot12 標準のフィールドに加えて、以下のフィールドが含まれている必要があります。

| フィールド | 型 | 必須 | 説明 |
|------|------|------|------|
| `request_id` | string | **強く推奨** | 操作を承認/拒否するためのリクエスト識別子 |
| `user_id` | string | 是 | リクエスト送信者のID |
| `user_nickname` | string | 否 | リクエスト送信者のニックネーム |
| `comment` | string | 否 | リクエストへの付加メッセージ |

### 2.2 `request_id` フィールド

`request_id` はリクエスト操作の中心的な識別子です。

- **用途**：操作可能なリクエストを識別し、`Request` DSL で使用します
- **生成ルール**：
  - プラットフォームのネイティブリクエスト識別子（OneBot11 の `flag` フィールド、Telegram の `chat_invite_link` など）を優先して使用します
  - プラットフォームにネイティブリクエストIDがない場合は、アダプターが一意の識別子を生成する必要があります（推奨フォーマット：`{platform}_{timestamp}_{user_id}`）
- **一意性**：同じプラットフォーム内で一意である必要があります
- **欠損時の挙動**：`request_id` が存在しない場合、`event.approve()` / `event.reject()` は `ValueError` をスローします

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
  "comment": "友達申請をお願いします",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. Request DSL

### 3.1 チェーンメソッド (Chain calls)

`Request` は、`Send` スタイルと整合したチェーンメソッドインターフェースを提供します：

```python
# 基本の使用法
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Bot アカウントを指定
await adapter.Request("req_id").Using("bot1").accept()

# 注釈の追加 (kwargs経由)
await adapter.Request("req_id").accept(comment="ようこそ")
await adapter.Request("req_id").reject(comment="しばらくお待ちください")

# 組み合わせて使用
await adapter.Request("req_id").Using("bot1").accept(comment="ようこそ")
```

### 3.2 メソッド一覧

| メソッド | 説明 | 戻り値 |
|------|------|--------|
| `Using(account_id)` | 操作を実行する Bot アカウントを指定 | `RequestDSL`（チェーンメソッド対応） |
| `accept(**kwargs)` | リクエストを承認 | `asyncio.Task`（await 後に標準レスポンスを返す） |
| `reject(**kwargs)` | リクエストを拒否 | `asyncio.Task`（await 後に標準レスポンスを返す） |

### 3.3 戻り値の形式

操作は標準の API レスポンス形式を返します。

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
    "message": "リクエストの有効期限が切れているか存在しません"
}
```

**未実装**（アダプターが `accept`/`reject` をオーバーライドしていない）：
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "プラットフォーム MyAdapter がリクエスト操作 (accept) を実装していません"
}
```

## 4. Event 便利メソッド

`Event` ラッパークラスは、リクエストイベントハンドラーで使用するのに適した便利なメソッドを提供します。

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # リクエストIDを取得
    request_id = event.get_request_id()
    if not request_id:
        print("警告：リクエストイベントに request_id がありません")
        return
    
    # リクエストを承認
    result = await event.approve()
    
    # またはリクエストを拒否
    # result = await event.reject(comment="しばらくお待ちください")
    
    # 結果を確認
    if result.get("status") == "ok":
        print("操作成功")
    else:
        print(f"操作失敗: {result.get('message')}")
```

### 4.1 Eventメソッド一覧

| メソッド | 説明 | 戻り値 |
|------|------|--------|
| `get_request_id()` | リクエストIDを取得 | `str` |
| `approve(comment=None)` | 現在のリクエストイベントを承認 | 標準レスポンス形式 |
| `reject(comment=None)` | 現在のリクエストイベントを拒否 | 標準レスポンス形式 |

## 5. アダプター実装要件

### 5.1 コンバーター要件

アダプターのコンバーターはリクエストイベントを変換する際、**必ず** `request_id` フィールドを正しく設定する必要があります。

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """プラットフォームのネイティブリクエストイベントを変換"""
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
    プラットフォームのネイティブイベントからリクエストIDを抽出
    
    プラットフォームのネイティブリクエスト識別子を優先し、なければ一意IDを生成します
    """
    # プラットフォームのネイティブIDを優先して使用
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # フォールバック：一意IDを生成
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request内部クラスの実装

アダプターは、`Request` 内部クラスで `accept` と `reject` をオーバーライドします。

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform リクエスト操作の実装"""
        
        def accept(self, **kwargs):
            """
            リクエストを承認
            
            :param kwargs: 拡張パラメータ、例: comment="注釈"
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
                        "message": f"リクエスト操作に失敗: {e}",
                    }
            
            return self._create_task(_do())
        
        def reject(self, **kwargs):
            """リクエストを拒否"""
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
                        "message": f"リクエスト操作に失敗: {e}",
                    }
            
            return self._create_task(_do())
```

### 5.3 プラットフォームがリクエスト操作をサポートしていない場合

プラットフォーム自体が友達申請/グループ招待操作をサポートしていない場合（一部のプラットフォームはリクエストを自動処理する場合など）、アダプターは以下のいずれかの手法を取ることができます。

1. **`Request` 内部クラスをオーバーライドしない**：基本クラスのデフォルト実装を使用し、`accept()`/`reject()` を呼び出した際に `retcode=10002` を返します
2. **変換時に `request_id` をスキップする**：`request_id` を生成せず、`event.approve()` で `ValueError` がスローされるようにします
3. **ログを出力する**：`accept`/`reject` で警告を記録し、適切なエラーコードを返します

### 5.4 まとめ：Send と Request の並行処理

アダプターには並行して存在する2つの DSL 内部クラスがあり、それぞれが役割を担っています。

```
BaseAdapter
├── Send(SendDSL)     ← メッセージ送信
│   ├── Raw_ob12()    ← 実装必須
│   ├── Text()        ← 推奨実装
│   └── Image()       ← 必要に応じて実装
│
└── Request(RequestDSL) ← リクエスト操作
    ├── accept()        ← 必要に応じて実装
    └── reject()        ← 必要に応じて実装
```

### 5.5 アダプター `__init__` の注意事項

`Request` 内部クラスの `__init__` をオーバーライドする場合、引数を透過し `super().__init__()` を呼び出す必要があります。詳細は [アダプター開発入門 - `__init__` の注意事項](../../developer-guide/adapters/getting-started.md#init-注意事项) を参照してください（`Request` も同様で、パラメータは `adapter, request_id, account_id` です）。

## 6. アダプター実装チェックリスト

### 基本的要件
- [ ] `__init__` をオーバーライドした場合、`super().__init__()` を呼び出しているか（Send / Request ファクトリの初期化を確保）

### リクエストイベントの変換
- [ ] リクエストイベントに `request_id` フィールドが含まれている（強く推奨）
- [ ] `detail_type` が正しく `"friend"` または `"group"` にマップされている
- [ ] プラットフォームの元のデータが `{platform}_raw` フィールドに保持されている
- [ ] `request_id` の生成ルールが文書化されている

### リクエスト操作
- [ ] `Request` 内部クラスが実装されている（プラットフォームがリクエスト操作をサポートする場合）
- [ ] `accept()` メソッドが実装されている
- [ ] `reject()` メソッドが実装されている
- [ ] 操作が標準の API レスポンス形式を返す
- [ ] サポートされていない操作は `retcode=10002` を返す
- [ ] ネットワークエラーは `retcode=33xxx` を返す（API レスポンス標準に従う）

## 7. エラーコードの拡張

リクエスト操作に関連する推奨されるエラーコード（[API レスポンス標準](api-response.md) §3.2 に従います）：

| エラーコード | エラー名 | 説明 |
|-------|-------|------|
| 34001 | Request Not Found | リクエストが存在しないか有効期限が切れています |
| 34002 | Request Already Handled | リクエストは既に処理されました |
| 34003 | Request Not Supported | プラットフォームがこのタイプのリクエスト操作をサポートしていません |
| 34004 | Permission Denied | Bot にこのリクエストを処理する権限がありません |

## 8. 関連ドキュメント

- [イベント変換標準](event-conversion.md) - 完全なイベント変換仕様
- [API レスポンス標準](api-response.md) - アダプター API レスポンス形式の標準
- [送信メソッド仕様](send-method-spec.md) - Send クラスのメソッド命名とパラメータ仕様
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング関係