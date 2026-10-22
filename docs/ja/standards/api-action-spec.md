# ErisPulse API アクション標準

> [!TIP]
> **このドキュメントを読むべきケース**：アダプタに Api DSL の標準アクション（get_user_info / delete_message など）を実装する場合や、モジュールからこれらの標準アクションをクロスプラットフォームで呼び出す際にパラメータや data フィールドを確認する必要がある場合に、本文を参照してください。必要なければ読み飛ばして構いません。

このドキュメントは、ErisPulse アダプタにおける **OneBot12 標準 API アクション**の統一インターフェース仕様を定義するものであり、モジュール開発者が標準インターフェースに向けてプログラミングできるようにし、プラットフォームネイティブ API へのマッピングはアダプタが担います。

> **カバー範囲**：OneBot12 標準アクションのうち、`ApiDSL` はユーザー / グループ / ギルド（Guild）/
> メッセージ管理 / メタ（Meta）の通常インターフェースに対する強い型付けのメソッドを提供します（`send_message` は
> `SendDSL.Raw_ob12` が担当）。ファイルリソースアクション（`upload_file` / `get_file` / チャンク転送）は
> フォールバック用の透過転送としてのみ保持されており、§3.5 の説明を参照してください。プラットフォーム拡張アクションは `Api.call("prefix.action", ...)`
> というエスケープハッチで呼び出します。アクションのパラメータと返却構造は OneBot12 仕様（リポジトリ内 `onebot/specs/interface/`）に準拠します。

## 1. 設計背景

ErisPulse では、メッセージセグメント（メッセージの送受信）とイベント形式はすでに完全に OneBot12 標準に準拠していますが、**API アクション呼び出し**（ユーザー情報の取得、グループリストの取得、メッセージの取り消しなど）はこれまで統一されておらず、モジュール開発者はプラットフォームごとに異なる `call_api` 呼び出しを書く必要がありました。

`ApiDSL` は、強い型付けの標準アクションメソッドを提供することでこの問題を解決します：

```
モジュールコード（クロスプラットフォーム統一）      アダプタ実装（プラットフォーム固有）
─────────────────              ──────────────────
adapter.Api.get_user_info("123")  →  アダプタ call_api / オーバーライド
adapter.Api.get_group_list()      →  アダプタ call_api / オーバーライド
adapter.Api.delete_message("id")  →  アダプタ call_api / オーバーライド
```

## 2. 三層 DSL 並列構造

ErisPulse アダプタには、それぞれの役割を持つ 3 つの並列な DSL 内部クラスがあります：

```
BaseAdapter
├── Send(SendDSL)       ← メッセージ送信（Text/Image/Raw_ob12）
├── Request(RequestDSL)  ← リクエスト操作（accept/reject）
└── Api(ApiDSL)          ← 標準 API アクション（ユーザー/グループ/ギルド/メッセージ管理/ファイル/メタ）★
```

| DSL | 責務 | メソッドスタイル | 戻り値 |
|-----|------|---------|--------|
| `Send` | メッセージ送信 | チェーン + `asyncio.Task` | 標準レスポンス |
| `Request` | リクエストイベントの処理 | `asyncio.Task` | 標準レスポンス |
| `Api` | クエリ/管理操作 | `async` メソッド | 標準レスポンス |

## 3. 標準アクション一覧

### 3.1 ユーザー関連

| メソッド | OB12 アクション | パラメータ | data の戻り値 |
|------|----------|------|----------|
| `get_self_info()` | `get_self_info` | なし | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | なし | `list[get_user_info レスポンス]` |

### 3.2 グループ関連

| メソッド | OB12 アクション | パラメータ | data の戻り値 |
|------|----------|------|----------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | なし | `list[get_group_info レスポンス]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info レスポンス]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | なし |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | なし |

### 3.3 メッセージ管理

| メソッド | OB12 アクション | パラメータ | 説明 |
|------|----------|------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | メッセージの取り消し/削除 |

> **メッセージ送信**（`send_message`）は `SendDSL` の `Raw_ob12` が処理するため、`ApiDSL` では重複して提供しません。

### 3.4 ギルド（Guild）関連

OneBot12 のギルド体系は 2 つの階層に分かれています：**ギルド（guild）** と **サブチャンネル（channel）**。

| メソッド | OB12 アクション | パラメータ | data の戻り値 |
|------|----------|------|----------|
| `get_guild_info(guild_id)` | `get_guild_info` | `guild_id: str` | `guild_id`, `guild_name` |
| `get_guild_list()` | `get_guild_list` | なし | `list[get_guild_info レスポンス]` |
| `set_guild_name(guild_id, guild_name)` | `set_guild_name` | `guild_id: str`, `guild_name: str` | なし |
| `get_guild_member_info(guild_id, user_id)` | `get_guild_member_info` | `guild_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_guild_member_list(guild_id)` | `get_guild_member_list` | `guild_id: str` | `list[get_guild_member_info レスポンス]` |
| `leave_guild(guild_id)` | `leave_guild` | `guild_id: str` | なし |
| `get_channel_info(guild_id, channel_id)` | `get_channel_info` | `guild_id: str`, `channel_id: str` | `channel_id`, `channel_name` |
| `get_channel_list(guild_id, *, joined_only)` | `get_channel_list` | `guild_id: str`, `joined_only: bool=false` | `list[get_channel_info レスポンス]` |
| `set_channel_name(guild_id, channel_id, channel_name)` | `set_channel_name` | `guild_id`, `channel_id`, `channel_name` | なし |
| `get_channel_member_info(guild_id, channel_id, user_id)` | `get_channel_member_info` | `guild_id`, `channel_id`, `user_id` | `user_id`, `user_name`, `user_displayname` |
| `get_channel_member_list(guild_id, channel_id)` | `get_channel_member_list` | `guild_id`, `channel_id` | `list[get_channel_member_info レスポンス]` |
| `leave_channel(guild_id, channel_id)` | `leave_channel` | `guild_id`, `channel_id` | なし |

> ギルド体系とグループ（group）は互いに独立しています：Discord / QQ ギルド / Kook などのプラットフォームはギルドインターフェースを実装し、
> 従来の QQ / WeChat はグループインターフェースを実装します。両方が同時に存在する場合もあれば、どちらか一方のみの場合もあります。

### 3.5 ファイルリソース操作

> [!WARNING]
> **ファイルリソースモデル（file_id 二段階方式）は ErisPulse では「フォールバック対応」に位置付けられます**：
> ErisPulse のファイル送受信は「先にアップロードして file_id を取得してから参照する」モデルを採用していません。モジュールがファイルを送信するには
> `SendDSL.File(file, filename)` を使用します（URL / パス / バイトを**送信時に直接送信**、
> [送信メソッド仕様](send-method-spec.md) を参照）。
> 本節の `upload_file` / `get_file` / チャンク転送アクションはプラットフォーム固有の `file_id` ファイルリソース
> 機能に依存しており、**汎用性が不十分**です。アダプタのバックエンドが元々この機能を備えている場合にのみ透過転送が可能で、フレームワーク内蔵の
> アダプタでは**実装せず、実装も推奨しません**。呼び出した場合は通常 `retcode=10002` が返されます。
> モジュールがクロスプラットフォームでファイルを送信する必要がある場合は、`SendDSL.File` を使用し、file_id に依存しないでください。
>
> **展望**：`file_id` リソースモデルのフレームワーク層への標準化は今後の方向性ですが、現行バージョンでは提供されません。

一括転送（小ファイル）：

| メソッド | OB12 アクション | パラメータ | data の戻り値 |
|------|----------|------|----------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

`upload_file` の `type` パラメータ：
- `"url"`：URL 経由でアップロード（`url` の指定が必要）
- `"path"`：ローカルパス経由でアップロード（`path` の指定が必要）
- `"data"`：バイナリデータ経由でアップロード（`data` の指定が必要）

#### 3.5.1 チャンク転送（大きなファイル、上記のフォールバック範囲に該当）

OneBot12 のチャンクアクションは `stage` でフェーズを区別します。`ApiDSL` は同一アクションの 3 段階/2 段階を独立したメソッドに分割します
（`offset` はバイトオフセット、`data` は JSON 内では Base64）。以下の表は参照用に保持しているだけで、
アダプタが実装する必要はなく、強制的に実装すべきでもありません：

**チャンクアップロードの 3 ステップ**：`prepare` → `transfer`（チャンクごとにループ）→ `finish`

| メソッド | 対応 stage | パラメータ | data の戻り値 |
|------|-----------|------|----------|
| `upload_file_fragmented_prepare(name, total_size)` | `prepare` | `name: str`, `total_size: int` | `file_id`（転送中に使用） |
| `upload_file_fragmented_transfer(file_id, offset, data)` | `transfer` | `file_id`, `offset: int`, `data: bytes` | なし |
| `upload_file_fragmented_finish(file_id, sha256)` | `finish` | `file_id`, `sha256: str`（ファイル全体の検証） | `file_id` |

```python
total = os.path.getsize(path)
r = await adapter.Api.upload_file_fragmented_prepare(os.path.basename(path), total)
fid = r["data"]["file_id"]
offset = 0
with open(path, "rb") as f:
    while chunk := f.read(65536):
        await adapter.Api.upload_file_fragmented_transfer(fid, offset, chunk)
        offset += len(chunk)
sha256 = hashlib.sha256(open(path, "rb").read()).hexdigest()
await adapter.Api.upload_file_fragmented_finish(fid, sha256)
```

**チャンクダウンロードの 2 ステップ**：`prepare` → `transfer`（ループでチャンクを取得）

| メソッド | 対応 stage | パラメータ | data の戻り値 |
|------|-----------|------|----------|
| `get_file_fragmented_prepare(file_id)` | `prepare` | `file_id` | `name`, `total_size`, `sha256` |
| `get_file_fragmented_transfer(file_id, offset, size)` | `transfer` | `file_id`, `offset: int`, `size: int` | `data`（今回のチャンクのバイト） |

### 3.6 メタ（Meta）アクション

メタアクションは特定のアカウントを対象としないため、`Using()` で Bot を指定する必要はありません。

| メソッド | OB12 アクション | パラメータ | data の戻り値 |
|------|----------|------|----------|
| `get_latest_events(limit, timeout)` | `get_latest_events` | `limit: int=0`, `timeout: int=0` | イベントオブジェクトの配列（メタイベントを除く） |
| `get_supported_actions()` | `get_supported_actions` | なし | `list[str]` サポート対象のアクション名 |
| `get_status()` | `get_status` | なし | `good: bool`, `bots: list[{self, online, ...}]` |
| `get_version()` | `get_version` | なし | `impl`, `version`, `onebot_version` |

### 3.7 汎用拡張アクション

| メソッド | 説明 |
|------|------|
| `call(action, **params)` | プラットフォーム拡張アクションのエスケープハッチ。OB12 拡張命名規則 `{prefix}.{action}` に従う |

## 4. 使用方法

### 4.1 基本的な呼び出し

```python
from ErisPulse import adapter

# ユーザー情報の取得（クロスプラットフォーム統一）
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"ユーザー名: {user_name}")

# グループリストの取得
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# メッセージの取り消し
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 Bot アカウントの指定（マルチアカウントモード）

```python
# 指定した Bot アカウントで操作を実行
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 プラットフォーム拡張アクション

```python
# プラットフォーム固有の拡張アクションを呼び出し（{prefix}.{action} の命名を推奨）
result = await adapter.telegram.Api.call(
    "telegram.send_sticker",
    sticker_id="CAACAgIAAxkBAA...",
)
```

### 4.4 イベントハンドラでの使用

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
        await event.reply(f"こんにちは、{user_name}さん！")
```

## 5. アダプタの実装

### 5.1 デフォルト動作（設定不要）

`ApiDSL` のデフォルト実装は、標準アクション名を `endpoint` としてそのまま `adapter.call_api()` に渡します：

```python
# ApiDSL のデフォルト実装は以下と等価：
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**適用シーン**：アダプタの基盤となるバックエンド自体が OneBot12 標準アクションプロトコルに準拠している場合、
`call_api` は標準アクション名をそのままサポートします（同プロトコルに準拠したサーバーに直接接続する場合など）。

### 5.2 標準メソッドのオーバーライド（プラットフォームネイティブ API へのマッピング）

アダプタは個々の標準メソッドをオーバーライドし、プラットフォームネイティブ API にマッピングできます：

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform 標準 API アクション実装"""

        async def get_user_info(self, user_id: str) -> dict:
            # プラットフォームネイティブ API にマッピング
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                # プラットフォーム側エラー：341xx～345xx の下 3 桁をカスタムで使用（346xx はフレームワーク予約のため使用禁止）
                return self._adapter.make_error(retcode=34400, message="ユーザーが存在しません")

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

### 5.3 未対応のアクション

アダプタがオーバーライドしていない標準メソッドはデフォルト実装（`call_api` への委譲）になります。`call_api` もそのアクションをサポートしていない場合は、標準エラーレスポンスを返すべきです：

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"未対応のアクション: {endpoint}")
    # ... プラットフォーム API 呼び出し
```

モジュール開発者は戻り値の `retcode` でサポートされているかどうかを判断できます：

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("このプラットフォームはフレンドリストの取得に対応していません")
```

## 6. レスポンス形式

すべての `ApiDSL` メソッドは標準 API レスポンス形式を返します（詳細は [API レスポンス標準](api-response.md) を参照）：

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

> **注意**：情報照会系アクションの `message_id` は空文字列です（メッセージ送信系アクションのみが `message_id` を持ちます）。

## 7. SendDSL / RequestDSL との関係

| シナリオ | 使用する DSL | 例 |
|------|---------|------|
| メッセージ送信 | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| リクエストの承認/拒否 | `Request` | `adapter.Request("req_id").accept()` |
| ユーザー/グループ情報の取得 | `Api` | `adapter.Api.get_user_info("123")` |
| メッセージの取り消し | `Api` | `adapter.Api.delete_message("msg_id")` |
| グループ退出 | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. アダプタ実装チェックリスト

### 標準アクション
- [ ] `call_api` が標準アクション名を処理できること（または対応する `ApiDSL` メソッドをオーバーライド）
- [ ] 未対応のアクションは `retcode=10002` を返すこと
- [ ] 戻り値が標準 API レスポンス形式に準拠していること
- [ ] `data` フィールドに OB12 標準定義のフィールドが含まれていること
- [ ] ギルドプラットフォームは `get_guild_*` / `get_channel_*` / `leave_guild` / `leave_channel` を実装すること
- [ ] メタアクション（`get_status` / `get_version` / `get_supported_actions`）の実装を推奨
- [ ] **ファイルの送受信は `SendDSL.File`（直接送信）を使用**。ファイルリソースアクション（upload_file/get_file/チャンク転送）は**実装必須ではない**。バックエンドが `file_id` リソース機能を備える場合にのみ透過転送が必要

### 拡張アクション
- [ ] プラットフォーム拡張アクションは `{prefix}.{action}` の命名を使用
- [ ] 拡張アクションのパラメータとレスポンスも OB12 アクションのリクエスト/レスポンス構造に準拠

## 9. 関連ドキュメント

**Api DSL の戻り値実装時に併せて参照**：
- [API レスポンス標準](api-response.md) - アダプタ API レスポンス形式標準

**同一アダプタのその他の DSL**：
- [送信メソッド仕様](send-method-spec.md) - Send クラスのメソッド命名とパラメータ仕様
- [リクエスト操作仕様](request-action-spec.md) - Request DSL の使用方法

**イベント側の関連資料**：
- [イベント変換標準](event-conversion.md) - イベント形式とメッセージセグメント標準