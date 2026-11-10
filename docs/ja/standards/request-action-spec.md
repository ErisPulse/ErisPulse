# ErisPulse リクエスト操作仕様

> [!TIP]
> **このドキュメントを読むべきタイミング**：アダプターでフレンドリクエスト/グループ招待を処理する必要がある場合（リクエストイベントの変換、`accept`/`reject` の実装、異種エンドポイントにおけるリクエストタイプコンテキストの保持を含む）、またはモジュール内で `event.approve()` / `event.reject()` を使ってリクエストを承認・拒否する場合に、本文を参照してください。不要な場合は読み飛ばして構いません。

本ドキュメントは、ErisPulse アダプターにおけるリクエストイベント操作の標準化仕様を定義します。リクエストイベントのフィールド要件、Request DSL の使用方法、アダプター実装要件を含みます。

## 1. 概要

リクエストイベント（`type: "request"`）は、OneBot12 標準で定義された特殊なイベントタイプであり、Bot が判断を下す必要のあるリクエスト（フレンドリクエスト、グループ招待など）を表します。

メッセージイベントとは異なり、リクエストイベントには**双方向のやり取り**が必要です：
1. **受信**：アダプターがプラットフォームネイティブのリクエストを標準リクエストイベントに変換する
2. **応答**：モジュールが `Request` DSL または `Event.approve()`/`Event.reject()` を通じて操作を実行する

```
プラットフォームネイティブのリクエストイベント
    │
    ▼
Converter.convert()        ← アダプター実装（正方向変換）
    │
    ▼
標準リクエストイベント（request_id を含む）
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
    │       BaseAdapter.Request.accept()  ← アダプターによるオーバーライド
    │               │
    │               ▼
    │       プラットフォーム API 呼び出し
    │
    └─→ またはアダプターを通じて直接操作
            await adapter.Request("req_id").accept()
```

## 2. リクエストイベントのフィールド要件

### 2.1 標準フィールド

リクエストイベントは OneBot12 標準フィールドを必ず含める必要があるほか、以下のフィールドも含める必要があります：

| フィールド | 型 | 必須 | 説明 |
|------|------|------|------|
| `request_id` | string | **強く推奨** | 承認/拒否操作に使用されるリクエスト識別子 |
| `user_id` | string | はい | リクエスト送信者の ID |
| `user_nickname` | string | いいえ | リクエスト送信者のニックネーム |
| `comment` | string | いいえ | リクエストの添え書き |

### 2.2 `request_id` フィールド

`request_id` はリクエスト操作の核心となる識別子です：

- **用途**：操作可能なリクエストを識別し、`Request` DSL で使用する
- **生成ルール**：
  - プラットフォームネイティブのリクエスト識別子を優先的に使用する（OneBot11 の `flag` フィールド、Telegram の `chat_invite_link` など）
  - プラットフォームにネイティブのリクエスト ID がない場合、アダプターは一意の識別子を生成する必要がある（推奨形式：`{platform}_{timestamp}_{user_id}`）
- **一意性**：同一プラットフォームの範囲内で一意である必要がある
- **欠落時の挙動**：`request_id` が欠落している場合、`event.approve()` / `event.reject()` は `ValueError` をスローします

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
  "comment": "フレンド追加をお願いします",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. Request DSL

### 3.1 メソッドチェーン呼び出し

`Request` は `Send` と同じスタイルのメソッドチェーン呼び出しインターフェースを提供します：

```python
# 基本的な使い方
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Bot アカウントを指定
await adapter.Request("req_id").Using("bot1").accept()

# 備考を添える（kwargs 経由）
await adapter.Request("req_id").accept(comment="ようこそ")
await adapter.Request("req_id").reject(comment="今は追加しない")

# 組み合わせて使用
await adapter.Request("req_id").Using("bot1").accept(comment="ようこそ")
```

### 3.2 メソッド一覧

| メソッド | 説明 | 戻り値 |
|------|------|--------|
| `Using(account_id)` | 操作を実行する Bot アカウントを指定 | `RequestDSL`（メソッドチェーン呼び出し対応） |
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
    "message": "リクエストが期限切れまたは存在しません"
}
```

**未実装**（アダプターが `_do_accept`/`_do_reject` をオーバーライドしていない場合）：
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "プラットフォーム MyAdapter はリクエスト操作（accept）を実装していません"
}
```

## 4. Event の便利メソッド

`Event` ラッパークラスは便利メソッドを提供しており、リクエストイベントハンドラーでの使用に適しています：

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
    # result = await event.reject(comment="今はフレンドを追加しない")
    
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

アダプターのコンバーターは、リクエストイベントを変換する際、`request_id` フィールドを**必ず**正しく設定する必要があります：

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """プラットフォームネイティブのリクエストイベントを変換する"""
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
    プラットフォームネイティブイベントからリクエスト ID を抽出する
    
    プラットフォームネイティブのリクエスト識別子を優先的に使用し、
    なければ一意の ID を生成する
    """
    # プラットフォームネイティブの ID を優先的に使用
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

基底クラスの `accept()` / `reject()` は公開エントリーポイントです：scope 認証ゲート（`scope.actions.<owner>.request`、無効化されている場合は 34601 の拒否レスポンスを直接返す）とタスクラッピングが組み込まれています。**アダプターは公開エントリーポイントをオーバーライドしないでください**——オーバーライドすると認証ゲートをバイパスしてしまいます。アダプターは `_do_accept` / `_do_reject`（非同期メソッド、標準レスポンス dict を直接返す）をオーバーライドします。

> **マルチアカウントに関する注意**：`_do_accept` / `_do_reject` 内ではアダプター自身が `call_api` を呼び出すため、アカウントは自動的に注入されません——アカウントは `self.request_context.get("account_id")` で取得し（`Using()` による明示的指定 > イベントチェーンによる自動バインド、Send の `send_context` と同じ方式）、`account_id` パラメータとして `call_api` に渡してください。そうしないと、マルチアカウント環境ではデフォルトアカウントにフォールバックしてしまいます。

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform のリクエスト操作実装"""
        
        async def _do_accept(self, **kwargs) -> dict:
            """
            リクエストを承認する
            
            :param kwargs: 拡張パラメータ、例：comment="備考"
            :return: 標準レスポンス形式の dict
            """
            try:
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    account_id=self.request_context.get("account_id"),
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
        
        async def _do_reject(self, **kwargs) -> dict:
            """リクエストを拒否する（_do_accept と同構造：approve=False）"""
```

### 5.3 リクエストタイプコンテキストの保持（異種エンドポイントアダプターでは必須）

#### 5.3.1 契約のギャップ

`Request` DSL はステートレスなハンドルです：呼び出し側が保持するのは `request_id` のみであり（[§3](#3-request-dsl)）、リクエストタイプは呼び出しパラメータに含まれません。一方、多くのプラットフォームでは承認/拒否のエンドポイントが**異種**になっています——OneBot11 系を例にすると：

| リクエストタイプ | エンドポイント |
|---|---|
| フレンド追加 | `set_friend_add_request(flag, approve)` |
| グループ申請 / グループ招待 | `set_group_add_request(flag, sub_type, approve)`、`sub_type ∈ {"add", "invite"}` |

呼び出し側は `request_id` しか知りませんが、エンドポイントの選択にはタイプが必要です。このコンテキストを補完できるのはアダプターだけです：リクエストイベントはもともとアダプターが受信して変換するものであり（タイプ情報は変換時に手元にある）、1 つの `request_id` に対応するリクエストタイプは変わりません。アダプターが自ら保持しない場合、エンドポイントを推測するか、呼び出し側が非標準パラメータを渡すことに依存するしかありません——典型的な障害形態は、**グループ招待がフレンドエンドポイントに送られる**ことで、flag がプロトコル側で user_id として解釈されエラーになります。

#### 5.3.2 仕様要件

プラットフォームのエンドポイントが異種（承認/拒否がリクエストタイプごとのルーティングを必要とする）であるアダプターでは、`accept` / `reject` の実装は以下を満たす必要があります：

1. **イベント側での保持**：アダプターがリクエストイベントを受信するエントリーポイントで、`request_id → {リクエストタイプ, sub_type, group_id, アカウント}` をインスタンス内キャッシュに書き込み（統一フィールドは §5.3.3 参照）、併せて期限切れエントリをクリーンアップする
2. **操作側でのルーティング**：`_do_accept` / `_do_reject` 内のエンドポイント選択順序は、**kwargs による明示的引数指定 > キャッシュ > デフォルトエンドポイントへのフォールバック + WARNING 記録**です——タイプが未知の場合は必ずログを出力すること（可観測性）。エンドポイントをサイレントに選択してはなりません
3. **kwargs の予約名**：明示的な上書きパラメータは `request_type` / `sub_type` / `group_id` と統一命名します（アンダースコア接頭辞なし、アダプター間で同名同義）；`_request_type` のようなプライベートな命名規約は使用しません（標準的な呼び出し側は渡しません）
4. **アカウントの取得**：操作アカウントは基底クラス属性 `self.request_context.get("account_id")` で統一的に取得します（`Using()` による明示的指定 > イベントチェーンによる自動バインド、Send の `send_context` と同じ方式）；キャッシュに保持されたイベント到着時のアカウントは、イベントチェーンが欠落した場合のフォールバックとして使用します（ポーリングによる合成イベント、再起動をまたぐ再構築など）
5. **処理後のクリーンアップ**：操作の送信が成功した後、キャッシュから該当する `request_id` を削除する

単一のリクエストエンドポイントを持つプラットフォーム（統一された `/set_request` など）では保持は不要で、透過的に渡すだけで構いません。本節はアダプター実装のガイドラインであり、`Request` DSL の契約には影響しません。

#### 5.3.3 統一エントリフィールド（媒体非依存）

コンテキストエントリは以下の統一フィールド形状で保持します。**フィールド形状は相互運用契約です**：メモリ内 dict、KV value、ORM の行はいずれも同一の形状で保存され、後のアダプター間での集約や移行時にも形状が一致します。ストレージ媒体は自由に選択でき、媒体によってフィールドの意味が変わることはありません。

| フィールド | 型 | 必須 | 意味とソース |
|---|---|---|---|
| `request_type` | `str` | はい | リクエストタイプ、イベントの `detail_type` から取得（`"friend"` / `"group"`） |
| `sub_type` | `str \| None` | グループリクエストでは必須 | グループリクエストのサブタイプ `"add"` / `"invite"`、プラットフォームネイティブイベントから取得（OB11 系の `sub_type`） |
| `group_id` | `str \| None` | グループリクエストでは必須 | ターゲットグループの ID、プラットフォームネイティブイベントから取得 |
| `account` | `str \| None` | マルチアカウントでは必須 | イベント到着時のアカウント、イベントの `self.user_id` から取得 |
| `ts` | `float` | はい | イベント到着の Unix タイムスタンプ（秒）、TTL 判定の基準 |

エントリの一貫性ルール：

- **一一対応**：1 つの `request_id` には最大 1 つのエントリが対応します；同一 `request_id` の重複イベントは上書き書き込みします（冪等）
- **処理後の削除**：操作の送信が成功した時点でエントリを削除します
- **TTL**：`ts` を基準とし、1 時間程度を推奨します（プラットフォーム側のリクエスト有効期間をカバー）；期限切れは未保持と同等とみなし、デフォルトエンドポイントへのフォールバック + WARNING を適用します
- **キー名（KV 永続化時）**：`{アダプター設定キー}:request_ctx:{request_id}`、アダプター間の衝突を回避します

#### 5.3.4 リファレンス実装（メモリキャッシュ）

```python
import time

from ErisPulse.Core import BaseAdapter, RequestDSL


class MyAdapter(BaseAdapter):
    """リクエストエンドポイントが異種のプラットフォーム（フレンドとグループリクエストでエンドポイントが分かれている）"""

    _REQ_CTX_TTL = 3600    # コンテキスト保持秒数、プラットフォーム側のリクエスト有効期間をカバーできれば十分
    _REQ_CTX_MAX = 512     # キャッシュ容量の上限

    def __init__(self, sdk=None):
        super().__init__(sdk)
        self._request_ctx: dict[str, dict] = {}   # request_id → リクエストコンテキスト

    def remember_request(self, request_id: str, *, request_type: str,
                         sub_type: str | None = None, group_id: str | None = None,
                         account: str | None = None) -> None:
        """イベント側でリクエストコンテキストを保持する（アダプターがリクエストイベントを受信するエントリーポイントで呼び出す）"""
        now = time.time()
        expired = [k for k, c in self._request_ctx.items() if now - c["ts"] > self._REQ_CTX_TTL]
        for k in expired:
            self._request_ctx.pop(k)
        while len(self._request_ctx) >= self._REQ_CTX_MAX:
            self._request_ctx.pop(min(self._request_ctx, key=lambda k: self._request_ctx[k]["ts"]))
        self._request_ctx[request_id] = {
            "request_type": request_type,   # "friend" / "group"
            "sub_type": sub_type,           # グループリクエストのサブタイプ："add" / "invite"
            "group_id": group_id,
            "account": account,             # イベント到着時のアカウント（イベントの self.user_id）
            "ts": now,
        }

    class Request(RequestDSL):
        """エンドポイントルーティング：kwargs による明示的引数指定 > キャッシュ > デフォルトエンドポイントへのフォールバック + WARNING"""

        def _route(self, **kwargs) -> dict:
            ctx = {k: kwargs[k] for k in ("request_type", "sub_type", "group_id") if kwargs.get(k)}
            cached = self._adapter._request_ctx.get(self._request_id, {})
            if not ctx.get("request_type"):
                ctx.update({k: v for k, v in cached.items()
                            if k in ("request_type", "sub_type", "group_id") and v})
                ctx.setdefault("account", cached.get("account"))
            if not ctx.get("request_type"):
                self._adapter.logger.warning(f"リクエスト {self._request_id} のタイプが不明のため、フレンドエンドポイントにフォールバックします")
                ctx["request_type"] = "friend"
            return ctx

        async def _do_accept(self, **kwargs) -> dict:
            """リクエストを承認する；kwargs のタイプルーティングは request_type / sub_type / group_id で明示的に上書き可能"""
            return await self._do_action(approve=True, **kwargs)

        async def _do_reject(self, **kwargs) -> dict:
            """リクエストを拒否する（_do_accept と同構造：approve=False）"""
            return await self._do_action(approve=False, **kwargs)

        async def _do_action(self, approve: bool, **kwargs) -> dict:
            ctx = self._route(**kwargs)
            account = self.request_context.get("account_id") or ctx.get("account")
            try:
                if ctx["request_type"] == "group":
                    result = await self._adapter.call_api(
                        endpoint="/set_group_add_request",
                        flag=self._request_id,
                        sub_type=ctx.get("sub_type") or "add",
                        approve=approve,
                        account_id=account,
                    )
                else:
                    result = await self._adapter.call_api(
                        endpoint="/set_friend_add_request",
                        flag=self._request_id,
                        approve=approve,
                        account_id=account,
                    )
                response = {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            except Exception as e:
                response = {
                    "status": "failed",
                    "retcode": 34001,
                    "data": None,
                    "message_id": "",
                    "message": f"リクエスト操作に失敗しました: {e}",
                }
            if response["status"] == "ok":
                self._adapter._request_ctx.pop(self._request_id, None)   # 処理後のクリーンアップ
            return response
```

#### 5.3.5 再起動をまたぐ永続化（オプション）

プロセス内メモリ + TTL で大半のシナリオはカバーできます：リクエストが到着してから処理されるまで通常は数秒～数分であり、プラットフォーム側にはもともと有効期限があり、再起動でキャッシュを失う期間はごくわずかです（フォールバックエンドポイント + WARNING により可観測性は確保されています）。アダプターが「処理の瞬間にちょうど再起動する」ことを懸念する場合にのみ、コンテキストを永続化媒体に保存します。媒体は以下のいずれかを自由に選択でき、いずれも §5.3.3 の統一フィールド形状で保存します：

- **KV ストレージ**：`self.sdk.storage`（フレームワーク統一 KV ストレージ、バックエンドの切り替えは [ストレージバックエンド](../advanced/storage-backends.md) を参照）：

  ```python
  # イベント入口：書き込み（key は §5.3.3 のキー名ルールを参照）
  key = f"{self._get_config_key()}:request_ctx:{request_id}"
  self.sdk.storage.set(key, {"request_type": "group", "sub_type": "invite",
                             "group_id": group_id, "account": self_id, "ts": time.time()})

  # 操作側：読み込み + クリーンアップ
  ctx = self.sdk.storage.get(key)
  self.sdk.storage.delete(key)
  ```

  ストレージ層はエントリの有効期限を管理しません：エントリ自体が `ts` を持っており、読み取り側が期限切れと判断した場合は未保持とみなします（フォールバック + WARNING を適用）；処理後は必ず `delete` してください。

- **組み込み ORM**：`Model` / `Field` 宣言的モデル（2.9+ で組み込み、[データモデル層](../developer-guide/orm.md) を参照）は等価な媒体として使用でき、テーブルは統一フィールド表に従ってカラムを作成します（`request_id` を主キー）。2 点に注意してください：`create_table` は `IF NOT EXISTS` の冪等であり、その後のフィールドの変更に伴う既存テーブルの移行はアダプター自身が行う必要があります；テーブルはアダプター固有のデータであり、アダプター間で共有されるテーブルではありません。

いずれの媒体を選択した場合でも：**永続化の書き込み失敗がイベントフローをブロックしてはなりません**——ストレージバックエンドが利用不可の場合（クールダウン期間の fast-fail）はメモリのみの保持にダウングレードし、イベントは通常どおり配信されます；2 つの永続化媒体はいずれもオプションであり、デフォルトはメモリで十分であり、新しい外部依存関係は追加されません。

### 5.4 プラットフォームがリクエスト操作をサポートしていない場合

プラットフォーム自体がフレンドリクエスト/グループ招待の操作をサポートしていない場合（一部のプラットフォームはリクエストを自動処理するなど）、アダプターは以下のことができます：

1. **`Request` 内部クラスをオーバーライドしない**：基底クラスのデフォルト実装を使用し、`accept()`/`reject()` の呼び出し時に `retcode=10002` を返す
2. **変換時に `request_id` をスキップする**：`request_id` を生成せず、`event.approve()` に `ValueError` をスローさせる
3. **ログを記録する**：`_do_accept` / `_do_reject` 内で警告を記録し、適切なエラーコードを返す

### 5.5 まとめ：Send と Request の並行

アダプターには 2 つの並行する DSL 内部クラスがあり、それぞれが役割を担っています：

```
BaseAdapter
├── Send(SendDSL)     ← メッセージ送信
│   ├── Raw_ob12()    ← 実装必須
│   ├── Text()        ← 実装推奨
│   └── Image()       ← 必要に応じて実装
│
└── Request(RequestDSL) ← リクエスト操作
    ├── accept()        ← 公開エントリーポイント（scope ゲート + タスクラッパー、オーバーライド禁止）
    ├── reject()        ← 公開エントリーポイント（同上）
    ├── _do_accept()    ← 必要に応じてオーバーライド
    └── _do_reject()    ← 必要に応じてオーバーライド
```

### 5.6 アダプター `__init__` の注意点

`Request` 内部クラスの `__init__` をオーバーライドする場合は、パラメータをそのまま渡し、`super().__init__()` を呼び出す必要があります。詳細は [アダプター開発入門 - `__init__` の注意点](../developer-guide/adapters/getting-started.md#init-注意事项) を参照してください（`Request` も同様、パラメータは `adapter, request_id, account_id`）。

## 6. アダプター実装チェックリスト

### 基本要件
- [ ] `__init__` をオーバーライドした場合、`super().__init__()` を呼び出している（Send / Request ファクトリの初期化を確保）

### リクエストイベントの変換
- [ ] リクエストイベントに `request_id` フィールドが含まれている（強く推奨）
- [ ] `detail_type` が `"friend"` または `"group"` に正しくマッピングされている
- [ ] プラットフォームの生データを `{platform}_raw` フィールドに保持している
- [ ] `request_id` の生成ルールがドキュメントに記載されている

### リクエスト操作
- [ ] `Request` 内部クラスが実装されている（プラットフォームがリクエスト操作をサポートしている場合）
- [ ] `_do_accept()` / `_do_reject()` がオーバーライドされている（公開エントリーポイント `accept()` / `reject()` はオーバーライドしないこと——scope 認証ゲートをバイパスしてしまうため）
- [ ] 操作が標準 API レスポンス形式を返す
- [ ] サポートされていない操作は `retcode=10002` を返す
- [ ] ネットワークエラーは `retcode=33xxx` を返す（API レスポンス標準に従う）

### リクエストタイプコンテキストの保持（異種エンドポイントプラットフォーム、§5.3 参照）
- [ ] リクエストイベントの入口で `request_id → {リクエストタイプ, sub_type, group_id, アカウント}` のコンテキストを保持している
- [ ] エントリのフィールドが §5.3.3 の統一フィールド表と一致している（`ts` タイムスタンプを含む；`request_id` との一一対応、処理後の削除）
- [ ] `accept` / `reject` のエンドポイントルーティング順序が kwargs による明示的引数指定 > キャッシュ > デフォルトエンドポイントへのフォールバック + WARNING になっている
- [ ] タイプ上書きパラメータに予約名 `request_type` / `sub_type` / `group_id` を使用している（`_request_type` のようなプライベートな命名規約は使用しない）
- [ ] キャッシュに TTL と容量上限があり、操作の送信成功後に該当するエントリをクリーンアップしている
- [ ] マルチアカウント：操作アカウントを `self.request_context.get("account_id")` で取得している（`Using()` > イベントチェーンのフォールバック）、キャッシュされたアカウントをイベントチェーン欠落時のフォールバックとして使用
- [ ] 永続化媒体を使用する場合：書き込み失敗時はメモリのみの保持にダウングレードし、イベントフローをブロックしない

## 7. エラーコードの拡張

リクエスト操作に関連する**アダプター実装層**の推奨エラーコード（[API レスポンス標準](api-response.md) §3.2 に従い、`34xxx` プラットフォームエラーセグメントの下 3 桁をカスタム）：

| エラーコード | エラー名 | 説明 |
|-------|-------|------|
| 34001 | Request Not Found | リクエストが存在しないか、期限切れです |
| 34002 | Request Already Handled | リクエストはすでに処理されています |
| 34003 | Request Not Supported | プラットフォームはこのタイプのリクエスト操作をサポートしていません |
| 34004 | Permission Denied | Bot にはこのリクエストを処理する権限がありません（プラットフォームが返す） |

> **フレームワークコードとの境界**：上記の `340xx` は**プラットフォーム/アダプター**が返すリクエスト処理の失敗です；
> ErisPulse フレームワークは、`scope.actions` でモジュールの request アクションが無効化されている場合、**アダプターを呼び出す前に**
> 直接 `34601`（Action Denied、[API レスポンス標準 §5.3](api-response.md#53-框架扩展返回码34xxx-平台错误段的低三位自定义) を参照）を返します；
> 両者は互いに代替関係にはありません：まず `34601` のフレームワークゲートを通過し、その後にプラットフォーム層の `340xx` エラーに該当します。

## 8. 関連ドキュメント

**リクエスト操作の実装時に併せて参照**：
- [イベント変換標準](event-conversion.md) - 完全なイベント変換仕様（`request_id` フィールド要件を含む）
- [API レスポンス標準](api-response.md) - アダプター API レスポンス形式標準（操作の戻り値とエラーコード）
- [ストレージバックエンド](../advanced/storage-backends.md) - 再起動をまたいでリクエストコンテキストを保持する必要がある場合の統一 KV ストレージ

**同一アダプターのその他の DSL**：
- [送信メソッド仕様](send-method-spec.md) - Send クラスのメソッド命名とパラメータ仕様
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング関係