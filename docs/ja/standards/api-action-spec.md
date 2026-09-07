# ErisPulse API 動作標準

本文書では、ErisPulse アダプターにおける **OneBot12 標準 API 動作**の統一インターフェース仕様を定義し、モジュール開発者が標準インターフェースを対象にプログラミングできるようにし、アダプターがプラットフォームのネイティブ API にマッピングする責任を負います。

> **対象範囲**：OneBot12 標準動作において、`ApiDSL` はユーザー / グループ / チャンネル（Guild）/
> メッセージ管理 / 元（Meta）の一般的なインターフェースを強型メソッドとして提供します（`send_message` は
> `SendDSL.Raw_ob12` が担当します）。ファイルリソース動作（`upload_file` / `get_file` / フラグメント）は、
> 降格透かし転送としてのみ保持されます。詳細は §3.5 を参照してください。プラットフォーム拡張動作は、
> `Api.call("prefix.action", ...)` を使用したエスケープハッチで呼び出されます。動作のパラメータと返り値の構造は、OneBot12 規格（リポジトリ内の `onebot/specs/interface/`）に準拠します。

## 1. 設計の背景

ErisPulse では、メッセージセグメント（メッセージの送受信）とイベント形式は既に完全に OneBot12 標準に準拠していますが、**API アクションの呼び出し**（例：ユーザー情報の取得、グループリストの取得、メッセージの撤回など）は、以前は統一されていませんでした。モジュール開発者は、各プラットフォームごとに異なる `call_api` の呼び出しを書く必要がありました。

`ApiDSL` は、強タイプの標準アクションメソッドを提供することで、この問題を解決します：

```
モジュールコード（プラットフォーム間で統一）        适配器実装（プラットフォーム固有）
─────────────────              ──────────────────
adapter.Api.get_user_info("123")  →  适配器 call_api / オーバーライド
adapter.Api.get_group_list()      →  适配器 call_api / オーバーライド
adapter.Api.delete_message("id")  →  适配器 call_api / オーバーライド
```

## 2. 3層のDSL並列構造

ErisPulse アダプタには、それぞれ異なる役割を持つ3つの並列のDSL内部クラスがあります：

```
BaseAdapter
├── Send(SendDSL)       ← メッセージ送信（Text/Image/Raw_ob12）
├── Request(RequestDSL)  ← 要求操作（accept/reject）
└── Api(ApiDSL)          ← 標準APIアクション（ユーザー/グループ/チャンネル/メッセージ管理/ファイル/メタ）★
```

| DSL | 職責 | メソッドスタイル | 戻り値 |
|-----|------|---------|--------|
| `Send` | メッセージ送信 | チェーン式 + `asyncio.Task` | 標準レスポンス |
| `Request` | 要求イベントの処理 | `asyncio.Task` | 標準レスポンス |
| `Api` | クエリ/管理操作 | `async` メソッド | 標準レスポンス |

## 3. 標準アクション一覧

### 3.1 ユーザー関連

| メソッド | OB12 アクション | パラメータ | data 返却値 |
|------|----------|------|----------|
| `get_self_info()` | `get_self_info` | 無 | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | 無 | `list[get_user_info 応答]` |

### 3.2 グループ関連

| メソッド | OB12 アクション | パラメータ | data 返却値 |
|------|----------|------|----------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | 無 | `list[get_group_info 応答]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info 応答]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | 無 |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | 無 |

### 3.3 メッセージ管理

| メソッド | OB12 アクション | パラメータ | 説明 |
|------|----------|------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | メッセージの撤回/削除 |

> **メッセージ送信**（`send_message`）は `SendDSL` の `Raw_ob12` で処理され、`ApiDSL` には重複して記載されていない。

### 3.4 チャンネル（Guild）関連

OneBot12 のチャンネル体系は二段階構造：**チャンネル（guild）** と **サブチャンネル（channel）**。

| メソッド | OB12 アクション | パラメータ | data 返却値 |
|------|----------|------|----------|
| `get_guild_info(guild_id)` | `get_guild_info` | `guild_id: str` | `guild_id`, `guild_name` |
| `get_guild_list()` | `get_guild_list` | 無 | `list[get_guild_info 応答]` |
| `set_guild_name(guild_id, guild_name)` | `set_guild_name` | `guild_id: str`, `guild_name: str` | 無 |
| `get_guild_member_info(guild_id, user_id)` | `get_guild_member_info` | `guild_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_guild_member_list(guild_id)` | `get_guild_member_list` | `guild_id: str` | `list[get_guild_member_info 応答]` |
| `leave_guild(guild_id)` | `leave_guild` | `guild_id: str` | 無 |
| `get_channel_info(guild_id, channel_id)` | `get_channel_info` | `guild_id: str`, `channel_id: str` | `channel_id`, `channel_name` |
| `get_channel_list(guild_id, *, joined_only)` | `get_channel_list` | `guild_id: str`, `joined_only: bool=false` | `list[get_channel_info 応答]` |
| `set_channel_name(guild_id, channel_id, channel_name)` | `set_channel_name` | `guild_id`, `channel_id`, `channel_name` | 無 |
| `get_channel_member_info(guild_id, channel_id, user_id)` | `get_channel_member_info` | `guild_id`, `channel_id`, `user_id` | `user_id`, `user_name`, `user_displayname` |
| `get_channel_member_list(guild_id, channel_id)` | `get_channel_member_list` | `guild_id`, `channel_id` | `list[get_channel_member_info 応答]` |
| `leave_channel(guild_id, channel_id)` | `leave_channel` | `guild_id`, `channel_id` | 無 |

> チャンネル体系はグループ（group）とは独立：Discord / QQ チャンネル / Kook などのプラットフォームはチャンネルインターフェースを実装し、従来の QQ / WeChat はグループインターフェースを実装する。両者は同時に存在するか、またはそのいずれかのみが存在する。

### 3.5 ファイルリソース操作

> **[!WARNING]**
> **ファイルリソースモデル（file_id 二段階式）は ErisPulse では「降格利用可能」**：
> ErisPulse のファイル送受信は「先に file_id を取得してから参照」のモデルを経由しない。モジュールがファイルを送信する際は `SendDSL.File(file, filename)` を使用する（URL / パス / バイナリ**送信時に直接送信**、[送信方法規格](send-method-spec.md)を参照）。本節の `upload_file` / `get_file` / 分片アクションは、プラットフォーム固有の `file_id` ファイルリソース機能に依存しており、**汎用性が不足**している。適切なアダプタが後端でその機能を備えている場合にのみ透過的に実装可能であり、フレームワークに内蔵されたアダプタは実装せず、実装を推奨しない。呼び出し時には通常 `retcode=10002` を返す。モジュールが複数のプラットフォーム間でファイルを送信する必要がある場合は、`SendDSL.File` を使用し、file_id に依存しないようにする。
> 
> **展望**：`file_id` リソースモデルをフレームワーク層に標準化することが将来の方向性であるが、現時点では提供されていない。

整包転送（小ファイル）：

| メソッド | OB12 アクション | パラメータ | data 返却値 |
|------|----------|------|----------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

`upload_file` の `type` パラメータ：
- `"url"`：URL からアップロード（`url` を提供する必要がある）
- `"path"`：ローカルパスからアップロード（`path` を提供する必要がある）
- `"data"`：バイナリデータからアップロード（`data` を提供する必要がある）

#### 3.5.1 分片転送（大ファイル、上記の降格範囲に属する）

OneBot12 の分片アクションは `stage` で段階を区別する。`ApiDSL` では同一アクションの三段階または二段階を独立したメソッドに分割し（`offset` はバイトオフセット、`data` は JSON 中で Base64 で表現される）、下表は参照用に残すのみであり、アダプタは実装する必要も義務もありません：

**分片アップロード三段階**：`prepare` → `transfer`（各片を繰り返し送信）→ `finish`

| メソッド | 対応 stage | パラメータ | data 返却値 |
|------|-----------|------|----------|
| `upload_file_fragmented_prepare(name, total_size)` | `prepare` | `name: str`, `total_size: int` | `file_id`（転送中使用） |
| `upload_file_fragmented_transfer(file_id, offset, data)` | `transfer` | `file_id`, `offset: int`, `data: bytes` | 無 |
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

**分片ダウンロード二段階**：`prepare` → `transfer`（各片を繰り返し取得）

| メソッド | 対応 stage | パラメータ | data 返却値 |
|------|-----------|------|----------|
| `get_file_fragmented_prepare(file_id)` | `prepare` | `file_id` | `name`, `total_size`, `sha256` |
| `get_file_fragmented_transfer(file_id, offset, size)` | `transfer` | `file_id`, `offset: int`, `size: int` | `data`（今回の分片のバイト） |

### 3.6 メタ（Meta）アクション

メタアクションは具体的なアカウントに依存せず、`Using()` で Bot を指定する必要がない。

| メソッド | OB12 アクション | パラメータ | data 返却値 |
|------|----------|------|----------|
| `get_latest_events(limit, timeout)` | `get_latest_events` | `limit: int=0`, `timeout: int=0` | イベントオブジェクト配列（メタイベントを含まない） |
| `get_supported_actions()` | `get_supported_actions` | 無 | `list[str]` 支持するアクション名 |
| `get_status()` | `get_status` | 無 | `good: bool`, `bots: list[{self, online, ...}]` |
| `get_version()` | `get_version` | 無 | `impl`, `version`, `onebot_version` |

### 3.7 一般拡張アクション

| メソッド | 説明 |
|------|------|
| `call(action, **params)` | プラットフォーム拡張アクションのエスケープハッチであり、OB12 拡張命名規則 `{prefix}.{action}` に従う |

## 4. 使用方法

### 4.1 基本呼び出し

```python
from ErisPulse import adapter

# ユーザー情報を取得（プラットフォーム間で統一）
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"ユーザー名: {user_name}")

# グループリストを取得
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# メッセージの撤回
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 指定 Bot アカウント（複数アカウントモード）

```python
# 指定された Bot アカウントを使用して操作を実行
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 プラットフォーム拡張アクション

```python
# プラットフォーム固有の拡張アクションを呼び出す（{prefix}.{action} の命名を推奨）
result = await adapter.telegram.Api.call(
    "telegram.send_sticker",
    sticker_id="CAACAgIAAxkBAA...",
)
```

### 4.4 イベントハンドラ内で使用

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

## 5. アダプターの実装

### 5.1 デフォルト動作（ゼロ設定）

`ApiDSL` のデフォルト実装は、標準アクション名を `endpoint` として `adapter.call_api()` に直接渡します：

```python
# ApiDSL のデフォルト実装は以下のコードと同等です：
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**適用場面**：アダプターの下層バックエンドが OneBot12 標準アクションプロトコルに従っている場合、
`call_api` は標準アクション名（例：プロトコルに従うサービスに直接接続）を天然にサポートします。

### 5.2 標準メソッドのオーバーライド（プラットフォーム固有の API へのマッピング）

アダプターは個々の標準メソッドをオーバーライドし、プラットフォーム固有の API にマッピングできます：

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform 標準 API アクションの実装"""

        async def get_user_info(self, user_id: str) -> dict:
            # プラットフォーム固有の API にマッピング
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                return self._adapter.make_error(retcode=34600, message="ユーザーが存在しません")

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

### 5.3 未サポートのアクション

アダプターがカバーしていない標準メソッドはデフォルト実装（`call_api` に委譲）を実行します。もし `call_api` がそのアクションをサポートしていない場合、標準のエラーレスポンスを返す必要があります：

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"サポートされていないアクション: {endpoint}")
    # ... プラットフォーム API 呼び出し
```

モジュール開発者は、返り値の `retcode` を使ってサポート状況を判断できます：

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("このプラットフォームは友達リストの取得をサポートしていません")
```

## 6. 応答形式

すべての `ApiDSL` メソッドは、標準的な API 応答形式を返します（詳細は [API 応答の標準](api-response.md) を参照してください）。

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

> **注意**：情報照会系のアクションでは `message_id` は空文字列になります（`message_id` はメッセージ送信系のアクションにのみ存在します）。

## 7. SendDSL / RequestDSL との関係

| ステージ | DSL の使用 | 例 |
|------|---------|------|
| メッセージの送信 | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| リクエストの承認/拒否 | `Request` | `adapter.Request("req_id").accept()` |
| ユーザー/グループ情報の取得 | `Api` | `adapter.Api.get_user_info("123")` |
| メッセージの撤回 | `Api` | `adapter.Api.delete_message("msg_id")` |
| グループからの退出 | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. アダプター実装チェックリスト

### 標準アクション
- [ ] `call_api` は標準アクション名を処理できる（または対応する `ApiDSL` メソッドをオーバーライド）
- [ ] 対応しないアクションは `retcode=10002` を返す
- [ ] 戻り値は標準 API 応答形式に従う
- [ ] `data` フィールドには OB12 で定義されたフィールドを含む
- [ ] チャンネルプラットフォームは `get_guild_*` / `get_channel_*` / `leave_guild` / `leave_channel` を実装する
- [ ] 元アクション（`get_status` / `get_version` / `get_supported_actions`）は推奨実装
- [ ] **ファイル送信は `SendDSL.File`（直接送信）を使用**；ファイルリソースアクション（upload_file/get_file/分割）は**必須実装ではなく、バックエンドに `file_id` リソース能力がある場合にのみ透過する**

### 拡張アクション
- [ ] プラットフォーム拡張アクションは `{prefix}.{action}` の命名を使用
- [ ] 拡張アクションのパラメータと応答は、OB12 アクションリクエスト/応答構造に従う

## 9. 関連ドキュメント

- [API 応答標準](api-response.md) - アダプタ API 応答形式の標準
- [送信メソッド規格](send-method-spec.md) - Send クラスのメソッド命名とパラメータ規格
- [リクエスト操作規格](request-action-spec.md) - Request DSL の使用方法
- [イベント変換標準](event-conversion.md) - イベント形式とメッセージセグメントの標準