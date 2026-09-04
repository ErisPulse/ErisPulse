# ErisPulse 要求操作規格

本ドキュメントは、ErisPulseアダプターにおける要求イベント操作の標準化された規格を定義しており、要求イベントのフィールド要件、Request DSL の使用方法、およびアダプター実装要件について説明します。

## 1. 概要

要求イベント（`type: "request"`）は、OneBot12標準で定義された特殊なイベントタイプであり、Botが決定を行う必要がある要求（例：友達申請、グループ招待など）を表します。

メッセージイベントとは異なり、要求イベントは**双方向のインタラクション**を必要とします：
1. **受信**：アダプターがプラットフォームの原生要求を標準要求イベントに変換する
2. **応答**：モジュールが `Request` DSL または `Event.approve()`/`Event.reject()` を使用して操作を実行する

```
プラットフォームの原生要求イベント
    │
    ▼
Converter.convert()        ← アダプター実装（正方向変換）
    │
    ▼
標準要求イベント (request_id を含む)
    │
    ├─→ モジュール処理器 @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← 要求を承認
    │       └─→ event.reject()      ← 要求を拒否
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
    └─→ またはアダプター操作を直接使用
            await adapter.Request("req_id").accept()
```

## 2. 要求イベントのフィールド要件

### 2.1 標準フィールド

要求イベントは、OneBot12標準フィールドに加えて、以下のフィールドを含む必要があります：

| フィールド | 型 | 必須 | 説明 |
|------|------|------|------|
| `request_id` | string | **強く推奨** | 要求操作に使用される要求識別子 |
| `user_id` | string | はい | 要求を発起したユーザーID |
| `user_nickname` | string | いいえ | 要求を発起したユーザーのニックネーム |
| `comment` | string | いいえ | 要求に付随するコメント |

### 2.2 `request_id` フィールド

`request_id` は、要求操作の中心的な識別子です：

- **用途**：`Request` DSL で使用される操作可能な要求を識別
- **生成ルール**：
  - プラットフォームの原生要求識別子（例：OneBot11 の `flag` フィールド、Telegram の `chat_invite_link` など）を優先的に使用
  - プラットフォームに原生要求IDがない場合、アダプターは一意の識別子を生成する（推奨形式：`{platform}_{timestamp}_{user_id}`）
- **一意性**：同一プラットフォーム範囲内で一意である
- **欠落時の動作**：`request_id` が欠落している場合、`event.approve()` / `event.reject()` は `ValueError` をスローする

### 2.3 要求イベントの例

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

`Request` は `Send` と同様のチェーン呼び出しインターフェースを提供します：

```python
# 基本的な使用法
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Botアカウントを指定
await adapter.Request("req_id").Using("bot1").accept()

# メッセージを付けて（kwargsを使用）
await adapter.Request("req_id").accept(comment="ようこそ")
await adapter.Request("req_id").reject(comment="今は追加できません")

# 組み合わせて使用
await adapter.Request("req_id").Using("bot1").accept(comment="ようこそ")
```

### 3.2 メソッド一覧

| メソッド | 説明 | 戻り値 |
|------|------|--------|
| `Using(account_id)` | 操作を実行する Botアカウントを指定 | `RequestDSL`（チェーン呼び出し可能） |
| `accept(**kwargs)` | 要求を承認 | `asyncio.Task`（await 後に標準レスポンスを返す） |
| `reject(**kwargs)` | 要求を拒否 | `asyncio.Task`（await 後に標準レスポンスを返す） |

### 3.3 戻り値形式

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
    "message": "要求が期限切れまたは存在しません"
}
```

**未実装**（アダプターが `accept`/`reject` をオーバーライドしていない場合）：
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "プラットフォーム MyAdapter は要求操作 (accept) を実装していません"
}
```

## 4. Event 便利メソッド

`Event` ラッパークラスには、要求イベントハンドラで使用する便利メソッドが用意されています：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # 要求IDを取得
    request_id = event.get_request_id()
    if not request_id:
        print("警告：要求イベントに request_id がありません")
        return
    
    # 要求を承認
    result = await event.approve()
    
    # または要求を拒否
    # result = await event.reject(comment="今は友達を追加できません")
    
    # 結果を確認
    if result.get("status") == "ok":
        print("操作成功")
    else:
        print(f"操作失敗: {result.get('message')}")
```

### 4.1 Event メソッド一覧

| メソッド | 説明 | 戻り値 |
|------|------|--------|
| `get_request_id()` | 要求IDを取得 | `str` |
| `approve(comment=None)` | 現在の要求イベントを承認 | 標準レスポンス形式 |
| `reject(comment=None)` | 現在の要求イベントを拒否 | 標準レスポンス形式 |

## 5. アダプター実装要件

### 5.1 転換器要件

アダプターの転換器は、要求イベントを転換する際に、**必ず** `request_id` フィールドを正しく設定する必要があります：

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """プラットフォームの原生要求イベントを転換"""
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
    プラットフォームの原生イベントから要求IDを抽出
    
    プラットフォームの原生IDを優先し、存在しない場合は一意のIDを生成
    """
    # プラットフォームの原生IDを優先
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # フェールバック：一意のIDを生成
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request 内部クラス実装

アダプターは `Request` 内部クラスで `accept` と `reject` をオーバーライドするだけで実現できます：

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform 要求操作実装"""
        
        def accept(self, **kwargs):
            """
            要求を承認
            
            :param kwargs: 拡張パラメータ、例: comment="備考"
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
                        "message": f"要求操作失敗: {e}",
                    }
            
            return self._create_task(_do())
        
        def reject(self, **kwargs):
            """要求を拒否"""
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
                        "message": f"要求操作失敗: {e}",
                    }
            
            return self._create_task(_do())
```

### 5.3 プラットフォームが要求操作をサポートしない場合

プラットフォームが友達申請/グループ招待操作をサポートしていない場合（例：一部のプラットフォームでは要求が自動処理される）、アダプターは以下の対応が可能です：

1. **`Request` 内部クラスをオーバーライドしない**：基底クラスのデフォルト実装を使用し、`accept()`/`reject()` を呼び出すと `retcode=10002` を返す
2. **`request_id` を生成しない**：`request_id` を生成せず、`event.approve()` が `ValueError` をスローするようにする
3. **ログを記録**：`accept`/`reject` で警告を記録し、適切なエラーコードを返す

### 5.4 総括：Send と Request は並列

アダプターには、それぞれの役割を果たす2つの並列の DSL 内部クラスがあります：

```
BaseAdapter
├── Send(SendDSL)     ← メッセージ送信
│   ├── Raw_ob12()    ← 必須実装
│   ├── Text()        ← 推奨実装
│   └── Image()       ← 必要に応じて実装
│
└── Request(RequestDSL) ← 要求操作
    ├── accept()        ← 必要に応じて実装
    └── reject()        ← 必要に応じて実装
```

### 5.5 アダプター `__init__` の注意事項

`Request` 内部クラスの `__init__` をオーバーライドする際は、引数を転送し、`super().__init__()` を呼び出す必要があります。詳細は [アダプター開発入門 - `__init__` の注意事項](../developer-guide/adapters/getting-started.md#init-の注意事項)（`Request` も同様、引数は `adapter, request_id, account_id`）を参照してください。

## 6. アダプター実装チェックリスト

### 基本要件
- [ ] `__init__` をオーバーライドした場合、`super().__init__()` を呼び出しているか（Send / Request ファクトリーの初期化を確実にする）

### 要求イベントの転換
- [ ] 要求イベントに `request_id` フィールドが含まれているか（強く推奨）
- [ ] `detail_type` が正しく `"friend"` または `"group"` にマッピングされているか
- [ ] プラットフォームの元データが `{platform}_raw` フィールドに保持されているか
- [ ] `request_id` の生成ルールがドキュメントに記載されているか

### 要求操作
- [ ] `Request` 内部クラスが実装されているか（プラットフォームが要求操作をサポートしている場合）
- [ ] `accept()` メソッドが実装されているか
- [ ] `reject()` メソッドが実装されているか
- [ ] 操作は標準 API レスポンス形式を返しているか
- [ ] サポートしていない操作は `retcode=10002` を返しているか
- [ ] ネットワークエラーは `retcode=33xxx` を返しているか（API レスポンス標準に従う）

## 7. エラーコードの拡張

要求操作に関連する**アダプター実装層**の推奨エラーコード（[API レスポンス標準](api-response.md) §3.2 に従い、`34xxx` プラットフォームエラーセグメントの下3桁を独自に定義）：

| エラーコード | エラーネーム | 説明 |
|-------|-------|------|
| 34001 | Request Not Found | 要求が存在しない、または期限切れ |
| 34002 | Request Already Handled | 要求はすでに処理済み |
| 34003 | Request Not Supported | プラットフォームがこのタイプの要求操作をサポートしていない |
| 34004 | Permission Denied | Bot がこの要求を処理する権限がない（プラットフォームが返した） |

> **フレームワークコードとの境界**：上記の `340xx` は**プラットフォーム/アダプター**が返す要求処理の失敗です。  
> ErisPulseフレームワークが `scope.actions` で特定のモジュールの request 動作を禁止した場合、**アダプターを呼び出す前に**直接 `34601`（Action Denied、[API レスポンス標準 §5.3](api-response.md#53-フレームワーク拡張返却コード34xxx-プラットフォームエラーセグメントの下3桁を独自に定義)）を返します。  
> これらは互いに補完するものではなく、まず `34601` フレームワークのチェックを通過し、次にプラットフォーム層の `340xx` エラーに到達します。

## 8. 関連ドキュメント

- [イベント転換標準](event-conversion.md) - 完全なイベント転換規格
- [API レスポンス標準](api-response.md) - アダプターの API レスポンス形式標準
- [送信メソッド規格](send-method-spec.md) - Send クラスのメソッド命名と引数規格
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング関係