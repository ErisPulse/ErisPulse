# ErisPulse API アクション仕様

本ドキュメントは、ErisPulse アダプターにおける **OneBot12 標準 API アクション**の統一インターフェース仕様を定義するものであり、モジュール開発者は標準インターフェース向けにプログラミングし、アダプターがプラットフォームのネイティブ API へマッピングすることを可能にします。

## 1. 設計背景

ErisPulse では、メッセージセグメント（メッセージ送受信）とイベントフォーマットは既に完全に OneBot12 標準に準拠していますが、**API アクション呼び出し**（ユーザー情報取得、グループ一覧取得、メッセージの巻き戻しなど）は以前は統一されていませんでした。そのため、モジュール開発者は各プラットフォームごとに異なる `call_api` 呼び出しを記述する必要がありました。

`ApiDSL` は、強型の標準アクションメソッドを提供することで、この問題を解決します：

```
モジュールコード（クロスプラットフォーム統一）             アダプター実装（プラットフォーム固有）
─────────────────              ──────────────────
adapter.Api.get_user_info("123")  →  アダプター call_api / オーバーライド
adapter.Api.get_group_list()      →  アダプター call_api / オーバーライド
adapter.Api.delete_message("id")  →  アダプター call_api / オーバーライド
```

## 2. 三層の並列構造 DSL

ErisPulse アダプターには、それぞれの役割を持つ 3 つの並列 DSL 内部クラスがあります：

```
BaseAdapter
├── Send(SendDSL)       ← メッセージ送信（Text/Image/Raw_ob12）
├── Request(RequestDSL)  ← リクエスト操作（accept/reject）
└── Api(ApiDSL)          ← 標準 API アクション（情報照会/グループ管理/メッセージ管理/ファイル操作）★
```

| DSL | 役割 | メソッドスタイル | 戻り値 |
|-----|------|---------|--------|
| `Send` | メッセージ送信 | チェーン式 + `asyncio.Task` | 標準レスポンス |
| `Request` | リクエストイベントの処理 | `asyncio.Task` | 標準レスポンス |
| `Api` | 照会/管理操作 | `async` メソッド | 標準レスポンス |

## 3. 標準アクション一覧

### 3.1 ユーザー関連

| メソッド | OB12 アクション | パラメータ | data 戻り値 |
|------|----------|------|----------|
| `get_self_info()` | `get_self_info` | なし | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | なし | `list[get_user_info 响应]` |

### 3.2 グループ関連

| メソッド | OB12 アクション | パラメータ | data 戻り値 |
|------|----------|------|----------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | なし | `list[get_group_info 响应]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info 响应]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | なし |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | なし |

### 3.3 メッセージ管理

| メソッド | OB12 アクション | パラメータ | 説明 |
|------|----------|------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | メッセージの巻き戻し/削除 |

> **メッセージ送信**（`send_message`）は `SendDSL` の `Raw_ob12` によって処理されるため、`ApiDSL` では重複しません。

### 3.4 ファイル操作

| メソッド | OB12 アクション | パラメータ | data 戻り値 |
|------|----------|------|----------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

`upload_file` の `type` パラメータ：
- `"url"`：URL からアップロード（`url` を提供する必要があります）
- `"path"`：ローカルパスからアップロード（`path` を提供する必要があります）
- `"data"`：バイナリデータからアップロード（`data` を提供する必要があります）

### 3.5 一般的な拡張アクション

| メソッド | 説明 |
|------|------|
| `call(action, **params)` | プラットフォーム拡張アクション用のエスケープハッチ。OB12 拡張命名規則 `{prefix}.{action}` に従います |

## 4. 使用方法

### 4.1 基本的な呼び出し

```python
from ErisPulse import adapter

# ユーザー情報の取得（クロスプラットフォーム統一）
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"ユーザー名: {user_name}")

# グループ一覧の取得
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# メッセージの巻き戻し
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 Bot アカウントの指定（マルチアカウントモード）

```python
# 指定された Bot アカウントを使用して操作を実行
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 プラットフォーム拡張アクション

```python
# プラットフォーム固有の拡張アクションの呼び出し（{prefix}.{action} の命名を推奨）
result = await adapter.telegram.Api.call(
    "telegram.send_sticker",
    sticker_id="CAACAgIAAxkBAA...",
)
```

### 4.4 イベントハンドラーでの使用

```python
from ErisPulse.Core.Event import message

@message()
async def handle(event):
    # 送信者の詳細情報を取得
    user_id = event.get_user_id()
    platform = event.get_platform()

    result = await getattr(adapter, platform).Api.get_user_info(user_id)
    if result["status"] == "ok":
        user_name = result["data"]["user_name"]
        await event.reply(f"こんにちは、{user_name}！")
```

## 5. アダプター実装

### 5.1 デフォルト動作（設定不要）

`ApiDSL` のデフォルト実装では、標準アクション名をそのまま `endpoint` として `adapter.call_api()` に渡します：

```python
# ApiDSL のデフォルト実装は以下と同等です：
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**適用シーン**：アダプターのバックエンド自体が OneBot12 の実装である（NapCat、Lagrange など）、`call_api` は標準アクション名を自然にサポートします。

### 5.2 標準メソッドのオーバーライド（プラットフォームネイティブ API へのマッピング）

アダプターは単一の標準メソッドをオーバーライドし、プラットフォームネイティブ API にマッピングすることができます：

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform 標準 API アクション実装"""

        async def get_user_info(self, user_id: str) -> dict:
            # プラットフォームネイティブ API にマッピング
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                return self._adapter.make_error(retcode=34001, message="ユーザーが存在しません")

            user = raw["data"]
            return self._adapter.make_response(
                data={
                    "user_id": str(user["id"]),
                    "user_name": user.get("nick", ""),
                    "user_displayname": user.get("display_name", ""),
                    "user_remark": user.get("remark", ""),
                },
                raw=raw,
            )

        async def get_friend_list(self) -> dict:
            raw = await self._adapter._request("GET", "/friends")
            friends = [
                {
                    "user_id": str(u["id"]),
                    "user_name": u.get("nick", ""),
                    "user_displayname": u.get("display_name", ""),
                    "user_remark": u.get("remark", ""),
                }
                for u in raw.get("data", [])
            ]
            return self._adapter.make_response(data=friends, raw=raw)
```

### 5.3 サポートしていないアクション

アダプターでオーバーライドされていない標準メソッドは、デフォルト実装（`call_api` へ委譲）になります。もし `call_api` もそのアクションをサポートしていない場合は、標準エラーレスポンスを返す必要があります：

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"アクションがサポートされていません: {endpoint}")
    # ... プラットフォーム API 呼び出し
```

モジュール開発者は、返り値の `retcode` でサポート判定ができます：

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("このプラットフォームは友達リストの取得をサポートしていません")
```

## 6. レスポンス形式

すべての `ApiDSL` メソッドは、標準 API レスポンス形式を返します（詳細は [API レスポンス標準](api-response.md) を参照）：

```json
{
    "status": "ok",
    "retcode": 0,
    "data": { ... },
    "message_id": "",
    "message": "",
    "myplatform_raw": { ... }
}
```

> **注意**：情報照会アクションの `message_id` は空文字列です（メッセージ送信アクションのみ `message_id` を持ちます）。

## 7. SendDSL / RequestDSL との関係

| 場面 | 使用する DSL | 例 |
|------|---------|------|
| メッセージ送信 | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| リクエストの承認/拒否 | `Request` | `adapter.Request("req_id").accept()` |
| ユーザー/グループ情報の取得 | `Api` | `adapter.Api.get_user_info("123")` |
| メッセージの巻き戻し | `Api` | `adapter.Api.delete_message("msg_id")` |
| グループから退出 | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. アダプター実装チェックリスト

### 標準アクション
- [ ] `call_api` が標準アクション名を処理できる（または対応する `ApiDSL` メソッドをオーバーライド）
- [ ] サポートされていないアクションは `retcode=10002` を返す
- [ ] 戻り値は標準 API レスポンス形式に従う
- [ ] `data` フィールドには OB12 標準定義のフィールドが含まれる

### 拡張アクション
- [ ] プラットフォーム拡張アクションは `{prefix}.{action}` の命名を使用する
- [ ] 拡張アクションのパラメータとレスポンスは、OB12 アクションリクエスト/レスポンス構造に従う

## 9. 関連ドキュメント

- [API レスポンス標準](docs/ja/api-response.md) - アダプター API レスポンス形式標準
- [送信メソッド仕様](docs/ja/send-method-spec.md) - Send クラスのメソッド命名およびパラメータ仕様
- [リクエスト操作仕様](docs/ja/request-action-spec.md) - Request DSL の使用方法
- [イベント変換標準](docs/ja/event-conversion.md) - イベント形式およびメッセージセグメント標準