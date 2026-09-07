# ErisPulse リクエスト操作規格

本ドキュメントでは、ErisPulseアダプターにおけるリクエストイベント操作の標準化された規格を定義します。これには、リクエストイベントのフィールド要件、Request DSLの使用方法、アダプター実装要件が含まれます。

## 1. 概要

リクエストイベント（`type: "request"`）は、OneBot12標準で定義された特殊なイベントタイプで、Botに意思決定を求めるリクエスト（友達申請、グループ招待など）を表します。

メッセージイベントとは異なり、リクエストイベントは**双方向のやり取り**が必要です：
1. **受信**：アダプターがプラットフォームの原生リクエストを標準リクエストイベントに変換
2. **応答**：モジュールが`Request` DSLまたは`Event.approve()`/`Event.reject()`を使って操作を実行

```
プラットフォーム原生リクエストイベント
    │
    ▼
Converter.convert()        ← アダプター実装（正方向変換）
    │
    ▼
標準リクエストイベント (request_idを含む)
    │
    ├─→ モジュール処理器 @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← 申請を承認
    │       └─→ event.reject()      ← 申請を拒否
    │               │
    │               ▼
    │       adapter.Request(request_id).accept()
    │               │
    │               ▼
    │       BaseAdapter.Request.accept()  ← アダプターのオーバーライド
    │               │
    │               ▼
    │       プラットフォームAPI呼び出し
    │
    └─→ または直接アダプター操作で実行
            await adapter.Request("req_id").accept()
```

## 2. リクエストイベントのフィールド要件

### 2.1 標準フィールド

リクエストイベントには、OneBot12標準フィールドに加えて、以下のフィールドを含める必要があります：

| フィールド | 型 | 必須 | 説明 |
|------|------|------|------|
| `request_id` | string | **強く推奨** | 操作用のリクエスト識別子 |
| `user_id` | string | はい | リクエスト発起者のID |
| `user_nickname` | string | いいえ | リクエスト発起者のニックネーム |
| `comment` | string | いいえ | リクエストの備考 |

### 2.2 `request_id` フィールド

`request_id`はリクエスト操作の中心となる識別子です：

- **用途**：`Request` DSLで使用される、操作可能なリクエストを識別
- **生成ルール**：
  - まず、プラットフォームの原生リクエスト識別子を使用（OneBot11の`flag`フィールド、Telegramの`chat_invite_link`など）
  - プラットフォームに原生リクエストIDがない場合、ユニークな識別子を生成（推奨形式：`{platform}_{timestamp}_{user_id}`）
- **一意性**：同じプラットフォーム内では一意である
- **欠落時の動作**：`request_id`が欠落している場合、`event.approve()` / `event.reject()`は`ValueError`を送出

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
  "comment": "友達申請してください",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. Request DSL

### 3.1 チェーン呼び出し

`Request`は`Send`と同様のチェーン呼び出しインターフェースを提供します：

```python
# 基本的な使い方
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Botアカウントを指定
await adapter.Request("req_id").Using("bot1").accept()

# 备考を指定（kwargsで）
await adapter.Request("req_id").accept(comment="ようこそ")
await adapter.Request("req_id").reject(comment="今は追加できません")

# 組み合わせ
await adapter.Request("req_id").Using("bot1").accept(comment="ようこそ")
```

### 3.2 メソッド一覧

| メソッド | 説明 | 戻り値 |
|------|------|--------|
| `Using(account_id)` | 操作実行用のBotアカウントを指定 | `RequestDSL`（チェーン呼び出し可能） |
| `accept(**kwargs)` | リクエストを承認 | `asyncio.Task`（await後に標準レスポンスを返す） |
| `reject(**kwargs)` | リクエストを拒否 | `asyncio.Task`（await後に標準レスポンスを返す） |

### 3.3 戻り値の形式

操作は標準APIレスポンス形式を返します：

**成功時**：
```json
{
    "status": "ok",
    "retcode": 0,
    "data": null,
    "message_id": "",
    "message": ""
}
```

**失敗時**：
```json
{
    "status": "failed",
    "retcode": 34001,
    "data": null,
    "message_id": "",
    "message": "リクエストが期限切れまたは存在しません"
}
```

**未実装時**（アダプターが`accept`/`reject`をオーバーライドしていない場合）：
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "プラットフォーム MyAdapter はリクエスト操作 (accept) を実装していません"
}
```

## 4. Event 便利メソッド

`Event`ラッパークラスには、リクエストイベントハンドラで使用する便利メソッドが用意されています：

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
    # result = await event.reject(comment="今は友達追加できません")
    
    # 結果を確認
    if result.get("status") == "ok":
        print("操作成功")
    else:
        print(f"操作失敗: {result.get('message')}")
```

### 4.1 Event メソッド一覧

| メソッド | 説明 | 戻り値 |
|------|------|--------|
| `get_request_id()` | リクエストIDを取得 | `str` |
| `approve(comment=None)` | 現在のリクエストイベントを承認 | 標準レスポンス形式 |
| `reject(comment=None)` | 現在のリクエストイベントを拒否 | 標準レスポンス形式 |

## 5. アダプター実装要件

### 5.1 転換器要件

アダプターの転換器は、リクエストイベントを転換する際に、**必ず**`request_id`フィールドを正しく設定する必要があります：

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """プラットフォーム原生リクエストイベントを転換"""
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
    プラットフォーム原生イベントからリクエストIDを抽出
    
    まずプラットフォームの原生IDを使用し、ない場合はユニークIDを生成
    """
    # まずプラットフォームの原生IDを使用
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # デフォルト：ユニークIDを生成
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request 内部クラス実装

アダプターは`Request`内部クラスで`accept`と`reject`をオーバーライドするだけで実装できます：

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform リクエスト操作実装"""
        
        def accept(self, **kwargs):
            """
            リクエストを承認
            
            :param kwargs: 扩張パラメータ、comment="備考"など
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
                        "message": f"リクエスト操作失敗: {e}",
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
                        "message": f"リクエスト操作失敗: {e}",
                    }
            
            return self._create_task(_do())
```

### 5.3 プラットフォームがリクエスト操作をサポートしていない場合

プラットフォームが友達申請/グループ招待操作をサポートしていない場合（一部のプラットフォームでは申請を自動処理する場合）、アダプターは以下のように対応できます：

1. **`Request`内部クラスをオーバーライドしない**：基底クラスのデフォルト実装を使用し、`accept()`/`reject()`を呼び出すと`retcode=10002`を返す
2. **`request_id`を生成しない**：`request_id`を生成せず、`event.approve()`が`ValueError`を送出するようにする
3. **ログを記録する**：`accept`/`reject`で警告を記録し、適切なエラーコードを返す

### 5.4 まとめ：Send と Request は並列

アダプターには、それぞれ異なる役割を持つ2つのDSL内部クラスがあります：

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

### 5.5 アダプター `__init__` の注意事項

`Request`内部クラスの`__init__`をオーバーライドする際は、引数を透過的に渡し、`super().__init__()`を呼び出す必要があります。詳しくは[アダプター開発入門 - `__init__`の注意事項](../developer-guide/adapters/getting-started.md#init-の注意事項)（`Request`も同様、引数は`adapter, request_id, account_id`）をご覧ください。

## 6. アダプター実装チェックリスト

### 基本要件
- [ ] `__init__`をオーバーライドした場合、`super().__init__()`を呼び出しているか（Send / Requestファクトリーの初期化を確保）

### リクエストイベントの転換
- [ ] リクエストイベントに`request_id`フィールドが含まれているか（強く推奨）
- [ ] `detail_type`が`"friend"`または`"group"`に正しくマッピングされているか
- [ ] プラットフォームの元データが`{platform}_raw`フィールドに保持されているか
- [ ] `request_id`の生成ルールがドキュメントに説明されているか

### リクエスト操作
- [ ] `Request`内部クラスが実装されているか（プラットフォームがリクエスト操作をサポートしている場合）
- [ ] `accept()`メソッドが実装されているか
- [ ] `reject()`メソッドが実装されているか
- [ ] 操作が標準APIレスポンス形式を返しているか
- [ ] 対応していない操作は`retcode=10002`を返しているか
- [ ] ネットワークエラーは`retcode=33xxx`（APIレスポンス標準に従う）を返しているか

## 7. エラーコードの拡張

リクエスト操作に関連する**アダプター実装層**の推奨エラーコード（[APIレスポンス標準](api-response.md) §3.2に従い、`34xxx`プラットフォームエラーセグメントの下3桁を独自に定義）：

| エラーコード | エラーネーム | 説明 |
|-------|-------|------|
| 34001 | Request Not Found | リクエストが存在しない、または期限切れ |
| 34002 | Request Already Handled | リクエストは既に処理済み |
| 34003 | Request Not Supported | プラットフォームがこのタイプのリクエスト操作をサポートしていない |
| 34004 | Permission Denied | Botがこのリクエストを処理する権限がない（プラットフォームが返す） |

> **フレームワークコードとの境界**：上記の`340xx`は**プラットフォーム/アダプター**が返すリクエスト処理失敗です。ErisPulseフレームワークが`scope.actions`で特定のモジュールのリクエスト操作を禁止した場合、**アダプターを呼び出す前に**直接`34601`（Action Denied、[APIレスポンス標準 §5.3](api-response.md#53-フレームワーク拡張返却コード34xxx-プラットフォームエラーセグメントの下3桁を独自に定義)）を返します。この2つは互いに補完するものであり、まず`34601`フレームワークのチェックを通過し、その後プラットフォーム層の`340xx`エラーに到達します。

## 8. 関連ドキュメント

- [イベント転換標準](event-conversion.md) - 完全なイベント転換規格
- [APIレスポンス標準](api-response.md) - アダプターAPIレスポンス形式の標準
- [送信メソッド規格](send-method-spec.md) - Sendクラスのメソッド命名と引数の規格
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング関係