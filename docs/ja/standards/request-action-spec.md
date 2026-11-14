# ErisPulse リクエスト操作規格

> [!TIP]
> **このドキュメントを読むタイミング**：アダプタが友人リクエスト/グループ招待（リクエストイベントの変換、`accept`/`reject`の実装、異質なエンドポイントのリクエストタイプコンテキスト保持）を処理する必要がある場合、またはモジュールで `event.approve()` / `event.reject()` を使用してリクエストを承認する場合に本文を参照してください。必要がない場合はスキップしてください。

本文書では、ErisPulseアダプタにおけるリクエストイベント操作の標準化された規格を定義します。これには、リクエストイベントのフィールド要件、Request DSLの使用方法、およびアダプタ実装要件が含まれます。

## 1. 概要

リクエストイベント（`type: "request"`）は、OneBot12標準で定義された特別なイベントタイプで、Botが決定を下す必要があるリクエスト（例：友人リクエスト、グループ招待など）を表します。

メッセージイベントとは異なり、リクエストイベントは**双方向の対話**を必要とします：
1. **受信**：アダプタがプラットフォームのネイティブリクエストを標準リクエストイベントに変換
2. **応答**：モジュールが`Request` DSLまたは`Event.approve()`/`Event.reject()`を使用して操作を実行

```
プラットフォームネイティブリクエストイベント
    │
    ▼
Converter.convert()        ← アダプタ実装（正方向変換）
    │
    ▼
標準リクエストイベント (request_idを含む)
    │
    ├─→ モジュールハンドラ @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← リクエストを承認
    │       └─→ event.reject()      ← リクエストを拒否
    │               │
    │               ▼
    │       adapter.Request(request_id).accept()
    │               │
    │               ▼
    │       BaseAdapter.Request.accept()  ← アダプタがオーバーライド
    │               │
    │               ▼
    │       プラットフォームAPI呼び出し
    │
    └─→ または直接アダプタ操作
            await adapter.Request("req_id").accept()
```

## 2. リクエストイベントのフィールド要件

### 2.1 標準フィールド

リクエストイベントは、OneBot12標準フィールドに加えて、以下のフィールドも含む必要があります：

| フィールド | 型 | 必須 | 説明 |
|------|------|------|------|
| `request_id` | string | **強く推奨** | リクエスト操作に使用する識別子 |
| `user_id` | string | はい | リクエストを発起したユーザーID |
| `user_nickname` | string | いいえ | リクエストを発起したユーザーのニックネーム |
| `comment` | string | いいえ | リクエストの付言 |

### 2.2 `request_id` フィールド

`request_id`はリクエスト操作の中心的な識別子です：

- **用途**：`Request` DSLで使用する可操作なリクエストを識別
- **生成ルール**：
  - まず、プラットフォームのネイティブリクエスト識別子（OneBot11の`flag`フィールド、Telegramの`chat_invite_link`など）を使用
  - プラットフォームにネイティブリクエストIDがない場合、アダプタは一意な識別子を生成する必要があります（推奨形式：`{platform}_{timestamp}_{user_id}`）
- **一意性**：同一プラットフォーム範囲内で一意である必要があります
- **欠落時の動作**：`request_id`が欠落している場合、`event.approve()` / `event.reject()`は`ValueError`を送出します

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
  "comment": "友人を追加してください",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. Request DSL

### 3.1 チェーン呼び出し

`Request`は`Send`スタイルと同様のチェーン呼び出しインターフェースを提供します：

```python
# 基本的な使用法
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Botアカウントを指定
await adapter.Request("req_id").Using("bot1").accept()

# 付言を指定（キーワード引数で）
await adapter.Request("req_id").accept(comment="ようこそ")
await adapter.Request("req_id").reject(comment="一時的に追加できません")

# 組み合わせて使用
await adapter.Request("req_id").Using("bot1").accept(comment="ようこそ")
```

### 3.2 メソッド一覧

| メソッド | 説明 | 戻り値 |
|------|------|--------|
| `Using(account_id)` | 操作を実行するBotアカウントを指定 | `RequestDSL`（チェーン呼び出し可能） |
| `accept(**kwargs)` | リクエストを承認 | `asyncio.Task`（await後に標準応答を返す） |
| `reject(**kwargs)` | リクエストを拒否 | `asyncio.Task`（await後に標準応答を返す） |

### 3.3 戻り値の形式

操作は標準API応答形式を返します：

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

**未実装**（アダプタが`_do_accept`/`_do_reject`をオーバーライドしていない場合）：
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

`Event`ラッパークラスは、リクエストイベントハンドラで使用する便利メソッドを提供します：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # リクエストIDを取得
    request_id = event.get_request_id()
    if not request_id:
        print("警告：リクエストイベントにrequest_idがありません")
        return
    
    # リクエストを承認
    result = await event.approve()
    
    # またはリクエストを拒否
    # result = await event.reject(comment="一時的に友人を追加できません")
    
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
| `approve(comment=None)` | 現在のリクエストイベントを承認 | 標準応答形式 |
| `reject(comment=None)` | 現在のリクエストイベントを拒否 | 標準応答形式 |

## 5. アダプタ実装要件

### 5.1 転換器要件

リクエストイベントを転換するアダプタの転換器は、**必ず**`request_id`フィールドを正しく設定する必要があります：

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """プラットフォームネイティブリクエストイベントを転換"""
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
    プラットフォームネイティブイベントからリクエストIDを抽出
    
    まずプラットフォームネイティブIDを使用し、なければ一意なIDを生成
    """
    # まずプラットフォームネイティブIDを使用
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # フォールバック：一意なIDを生成
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request 内部クラス実装

基底クラスの`accept()` / `reject()`は公開エントリーポイント：内部にscope認証ゲート（`scope.actions.<owner>.request`、無効化時は34601拒否応答を返す）とタスクラッパーを含みます。**アダプタは公開エントリーポイントをオーバーライドしないでください**。オーバーライドすると認証ゲートを迂回します。アダプタは`_do_accept` / `_do_reject`（非同期メソッド、直接標準応答dictを返す）をオーバーライドします。

> **多アカウントへの注意**：`_do_accept` / `_do_reject`内では`call_api`をアダプタ自身が呼び出すため、アカウントは自動的に注入されません。アカウントは`self.request_context.get("account_id")`から取得（`Using()`で明示指定 > イベントチェーン自動バインド、Sendの`send_context`と同口径）し、`account_id`パラメータとして`call_api`に渡す必要があります。そうしないと、多アカウント展開時にデフォルトアカウントに送信され、`request_id`がそのアカウントのセッションに存在しないため、プラットフォームは`invalid`と報告し、典型的な故障形態は「アカウント1のみ操作可能」となります。

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform リクエスト操作実装"""
        
        async def _do_accept(self, **kwargs) -> dict:
            """
            リクエストを承認
            
            :param kwargs: 拡張パラメータ、例：comment="備考"
            :return: 標準応答形式 dict
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
                    "message": f"リクエスト操作失敗: {e}",
                }
        
        async def _do_reject(self, **kwargs) -> dict:
            """リクエストを拒否（_do_acceptと同構造：approve=False）"""
```

### 5.3 リクエストタイプコンテキスト保持（異質なエンドポイントアダプタは必須）

#### 5.3.1 契約のギャップ

`Request` DSLは状態を持たないハンドルです：呼び出し元は`request_id`のみを持っています（[§3](#3-request-dsl)）。リクエストタイプは呼び出しパラメータに含まれません。しかし、多くのプラットフォームの承認/拒否エンドポイントは**異質**です。OneBot11系を例にすると：

| リクエストタイプ | エンドポイント |
|---|---|
| 友人追加 | `set_friend_add_request(flag, approve)` |
| グループ申請 / グループ招待 | `set_group_add_request(flag, sub_type, approve)`、`sub_type ∈ {"add", "invite"}` |

呼び出し元は`request_id`しか知らず、エンドポイント選択にはタイプが必要です。このコンテキストはアダプタが補完する必要があります：リクエストイベントはアダプタが受け取り、変換するものであり、タイプ情報は変換時に既に手元にあります。また、`request_id`に対応するリクエストタイプは変化しません。アダプタが独自に保持しない場合、エンドポイントを推測したり、呼び出し元に非標準パラメータを渡す必要が生じます。典型的な故障形態は、**グループ招待が友人エンドポイントに送信され、flagがuser_idとしてプロトコル側で解析されてエラーになる**ことです。

#### 5.3.2 規格要件

プラットフォームエンドポイントが異質（承認/拒否はリクエストタイプに応じてルーティングする必要がある）のアダプタは、`accept` / `reject`実装が以下の条件を満たす必要があります：

1. **イベント側保持**：アダプタがリクエストイベントを受け取るエントリーポイントで、`request_id → {リクエストタイプ, sub_type, group_id, アカウント}`をインスタンス内キャッシュに書き込み、不要なエントリを定期的にクリアする
2. **操作側ルーティング**：`_do_accept` / `_do_reject`内のエンドポイント選択順序は**kwargsの明示的パラメータ > キャッシュ > フォールバックデフォルトエンドポイント + WARNING**。タイプが不明な場合はログを出力し（可観測性）、静かにエンドポイントを選択してはならない
3. **kwargsの予約名**：明示的なオーバーライドパラメータは`request_type` / `sub_type` / `group_id`（アンダースコアなし、跨アダプタで同名同義）とし、`_request_type`などの非公開名は使用しない（標準呼び出し元は渡さない）
4. **アカウントの読み取りと所属チェック**：操作アカウントは基底クラス属性`self.request_context.get("account_id")`から取得（`Using()`で明示指定 > イベントチェーン自動バインド、Sendの`send_context`と同口径）。保持されたイベント到着アカウントはイベントチェーンが欠落した場合のフォールバック（例：ポーリング合成イベント、再起動後の再構築）。**アカウントインスタンスに解析できない場合は即時失敗**（34005を返す）し、デフォルトアカウントに静かに回帰してはならない。回帰すると操作が間違った接続に送信され（flagがデフォルトアカウントのセッションに存在せず、プラットフォームは`invalid`と報告し、多アカウントでは「アカウント1のみ操作可能」という不思議な故障になる）
5. **デフォルト永続化**：保持メディアはデフォルトでフレームワークの統一ストレージ（`self.sdk.storage`）**単一キーの整ブロックスナップショット**。リクエストは低頻度の承認イベント（友人/グループ招待、メッセージ流ではない）であり、イベント到着時に即時書き込み（DB内の足跡は常に1つのキー）。起動時に一度読み込み、実行時の読み取りはオーバーヘッドゼロ。ストレージが利用できない場合はメモリのみに降格（WARNING）、イベントフローをブロックしない
6. **処理後のクリア**：操作が成功したら`request_id`のエントリを削除し、スナップショットを即時書き込み

単一のリクエストエンドポイントを持つプラットフォーム（統一`/set_request`）は保持する必要がない。本節はアダプタ実装の口径であり、`Request` DSL契約は影響を受けない。

#### 5.3.3 統一条目フィールド（メディア依存）

コンテキスト条目は以下の統一フィールド形状で保持する。**フィールド形状は相互運用契約**：メモリdict、KV value、ORM行はすべて同じ形状で保存し、今後の跨アダプタ集約や移行時に形状が一致するようにする。ストレージメディアは選択可能で、メディアの変更によってフィールドの意味が変わらないようにする。

| フィールド | 型 | 必須 | 意味とソース |
|---|---|---|---|
| `request_type` | `str` | はい | リクエストタイプ、イベント`detail_type`（`"friend"` / `"group"`）から取得 |
| `sub_type` | `str \| None` | グループリクエストに必須 | グループリクエストのサブタイプ `"add"` / `"invite"`、プラットフォームネイティブイベントから取得（OB11系`sub_type`） |
| `group_id` | `str \| None` | グループリクエストに必須 | 目標グループID、プラットフォームネイティブイベントから取得 |
| `account` | `str \| None` | 多アカウントに必須 | イベント到着アカウント、イベント`self.user_id`から取得 |
| `ts` | `float` | はい | イベント到着Unixタイムスタンプ（秒）、TTL判定の基準 |

条目一貫性ルール：

- **1対1対応**：1つの`request_id`は1つの条目に対応する。同じ`request_id`の重複イベントは上書きされる（멱등性）
- **処理後の削除**：操作が成功したら条目を削除
- **TTL**：`ts`を基準に、プラットフォーム側のリクエスト有効期限をカバーする1時間程度を推奨。期限切れは未保持扱いとし、フォールバックデフォルトエンドポイント + WARNING
- **キー名（KV永続化時）**：`{アダプタ設定キー}:request_ctx:{request_id}`、跨アダプタの衝突を避ける

#### 5.3.4 参考実装（統一ストレージ単一キースナップショット、デフォルト）

保持メディアは**デフォルトでフレームワークの統一ストレージ**（`self.sdk.storage`）：リクエストイベントは承認系の低頻度イベント（友人/グループ招待、メッセージ流ではない）であり、**イベント到着時に即時書き込み**することで、書き込み負荷を生じない。ストレージ形式は**単一キーの整ブロックスナップショット**：上下文辞書全体を1つのキーとして1回で書き込む（DB内の足跡は常に1つのキー、処理に伴い自動的に収束）。逐個flag分キーにはしない。再起動後は起動時に一度読み込み、実行時の読み取りはオーバーヘッドゼロ。

```python
import time

from ErisPulse.Core import BaseAdapter, RequestDSL


class MyAdapter(BaseAdapter):
    """リクエストエンドポイントが異質なプラットフォーム（友人とグループリクエストが分離）"""

    _REQ_CTX_TTL = 86400   # 保持秒数（プラットフォーム側flag有効期限をカバー、再起動でも失わない）
    _REQ_CTX_MAX = 512     # 条目容量上限

    def __init__(self, sdk=None):
        super().__init__(sdk)
        self._request_ctx: dict[str, dict] = {}   # request_id → リクエストコンテキスト（メモリ状態）
        self._ctx_key = f"{self._get_config_key()}:request_ctx"   # 単一キーの整ブロックスナップショット

    async def start(self):
        # 起動時の読み込み（再起動後も承認可能）；ストレージが利用できない場合はコールドスタート処理
        try:
            loaded = self.sdk.storage.get(self._ctx_key, {}) or {}
            now = time.time()
            self._request_ctx = {k: v for k, v in loaded.items()
                                 if now - v.get("ts", 0) <= self._REQ_CTX_TTL}
        except Exception as e:
            self.logger.warning(f"リクエストコンテキストの読み込み失敗（コールドスタート処理）: {e}")
            self._request_ctx = {}

    def _persist_ctx(self) -> None:
        """単一キーの整ブロックスナップショットを書き込み（ストレージが利用できない場合はメモリのみに降格、イベントフローをブロックしない）"""
        try:
            self.sdk.storage.set(self._ctx_key, self._request_ctx)
        except Exception as e:
            self.logger.warning(f"リクエストコンテキストの書き込み失敗（メモリのみに降格）: {e}")

    def remember_request(self, request_id: str, *, request_type: str,
                         sub_type: str | None = None, group_id: str | None = None,
                         account: str | None = None) -> None:
        """イベント側でリクエストコンテキストを保持（アダプタがリクエストイベントを受け取るエントリーポイントで呼び出す）"""
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
            "account": account,             # イベント到着アカウント（イベントのself.user_id / 代理アカウント名）
            "ts": now,
        }
        self._persist_ctx()

    class Request(RequestDSL):
        """エンドポイントルーティング：kwargsの明示的パラメータ > キャッシュ > フォールバックデフォルトエンドポイント + WARNING"""

        def _route(self, **kwargs) -> dict:
            ctx = {k: kwargs[k] for k in ("request_type", "sub_type", "group_id") if kwargs.get(k)}
            cached = self._adapter._request_ctx.get(self._request_id, {})
            if not ctx.get("request_type"):
                ctx.update({k: v for k, v in cached.items()
                            if k in ("request_type", "sub_type", "group_id") and v})
                ctx.setdefault("account", cached.get("account"))
            if not ctx.get("request_type"):
                self._adapter.logger.warning(f"リクエスト {self._request_id} のタイプが不明、友人エンドポイントにフォールバック")
                ctx["request_type"] = "friend"
            return ctx

        def _resolve_or_fail(self, account):
            """
            承認アカウントの所属チェック：解析失敗は即時失敗（34005）、デフォルトアカウントにフォールバックしない。

            デフォルトアカウントにフォールバックすると、操作が間違った接続に送信され（flagがそのアカウントのセッションに存在せず、
            プラットフォームは`invalid`と報告し、"アカウント1のみ操作可能"という不思議な故障になる）。
            """
            if not account:
                return None, None            # アカウント情報が一切ない場合はデフォルトアカウントの意味を維持
            name, inst = self._adapter._resolve_account(account)
            hit = str(account) == str(name) or str(account) == str(getattr(inst, "bot_id", "") or "")
            if not hit:
                self._adapter.logger.warning(
                    f"リクエスト {self._request_id} のアカウント {account} がアカウントインスタンスに解析できない、デフォルトアカウントへのフォールバックを拒否")
                return None, "34005"
            return (name, inst), None

        async def _do_accept(self, **kwargs) -> dict:
            """リクエストを承認；kwargsのタイプルーティングはrequest_type / sub_type / group_idで明示的にオーバーライド可能"""
            return await self._do_action(approve=True, **kwargs)

        async def _do_reject(self, **kwargs) -> dict:
            """リクエストを拒否（_do_acceptと同構造：approve=False）"""
            return await self._do_action(approve=False, **kwargs)

        async def _do_action(self, approve: bool, **kwargs) -> dict:
            ctx = self._route(**kwargs)
            account = self.request_context.get("account_id") or ctx.get("account")
            resolved, fail = self._resolve_or_fail(account)
            if fail:
                return {
                    "status": "failed", "retcode": 34005, "data": None,
                    "message_id": "", "message": f"リクエストアカウント {account} がアカウントインスタンスに解析できない",
                }
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
                    "status": "failed", "retcode": 34001, "data": None,
                    "message_id": "", "message": f"リクエスト操作失敗: {e}",
                }
            if response["status"] == "ok":
                self._adapter._request_ctx.pop(self._request_id, None)   # 処理後のクリア
                self._adapter._persist_ctx()
            return response
```

#### 5.3.5 バウンダリと降格

**降格の意味**：統一ストレージが利用できない（接続失敗クールダウン期のfast-fail）場合、書き込みはメモリのみに降格（WARNINGで可観測）、イベントは通常配信される。再起動後は条目が失われ、タイプ不明のフォールバック + WARNING経路をたどる。

**同等のメディア**：ビルトインORM（`request_id`主キーでテーブル作成、[データモデル層](../developer-guide/orm.md)参照）は意味的に同等で、アダプタは必要に応じて選択可能。追加のファイルや新しい依存関係は導入しない。

**マルチインスタンスの境界**：本規格はマルチプロセスインスタンスの協調をカバーしない。ErisPulseは単一プロセスマルチbotモデル（複数アカウントが同一プロセス内、リクエストは所属アカウントと天然に同側）であり、統一ストレージで再起動の意味を満たす。跨インスタンス共有（複数プロセスでアカウントを分散）が必要な場合は別途プロジェクトを立てる。

### 5.4 プラットフォームがリクエスト操作をサポートしていない場合

プラットフォームが友人リクエスト/グループ招待操作をサポートしていない場合（一部のプラットフォームはリクエストを自動処理する）、アダプタは以下のいずれかを行うことができます：

1. **`Request`内部クラスをオーバーライドしない**：基底クラスのデフォルト実装を使用し、`accept()`/`reject()`を呼び出すと`retcode=10002`を返す
2. **`request_id`を生成しない**：`request_id`を生成せず、`event.approve()`が`ValueError`を送出するようにする
3. **ログを記録する**：`_do_accept`/`_do_reject`で警告を記録し、適切なエラーコードを返す

### 5.5 まとめ：SendとRequestの並行

アダプタには2つの並行するDSL内部クラスがあり、それぞれが役割を分担しています：

```
BaseAdapter
├── Send(SendDSL)     ← メッセージ送信
│   ├── Raw_ob12()    ← 必須実装
│   ├── Text()        ← 推奨実装
│   └── Image()       ← 必要に応じて実装
│
└── Request(RequestDSL) ← リクエスト操作
    ├── accept()        ← 公開エントリーポイント（scopeゲート + タスクラッパー、オーバーライドしない）
    ├── reject()        ← 公開エントリーポイント（同上）
    ├── _do_accept()    ← 必要に応じてオーバーライド
    └── _do_reject()    ← 必要に応じてオーバーライド
```

### 5.6 アダプタ`__init__`の注意事項

`Request`内部クラスの`__init__`をオーバーライドする場合、引数を透過的に渡し、`super().__init__()`を呼び出す必要があります。詳しくは[アダプタ開発入門 - `__init__`の注意事項](../developer-guide/adapters/getting-started.md#init-の注意事項)（`Request`も同様、引数は`adapter, request_id, account_id`）を参照してください。

## 6. アダプタ実装チェックリスト

### 基本要件
- [ ] `__init__`をオーバーライドした場合、`super().__init__()`を呼び出している（Send / Requestファクトリーの初期化を確実にする）

### リクエストイベント変換
- [ ] リクエストイベントに`request_id`フィールドが含まれている（強く推奨）
- [ ] `detail_type`が`"friend"`または`"group"`に正しくマッピングされている
- [ ] `{platform}_raw`フィールドにプラットフォームの元のデータを保持している
- [ ] `request_id`の生成ルールがドキュメントに記載されている

### リクエスト操作
- [ ] `Request`内部クラスが実装されている（プラットフォームがリクエスト操作をサポートしている場合）
- [ ] `_do_accept()` / `_do_reject()`がオーバーライドされている（公開エントリーポイント`accept()` / `reject()`はオーバーライドしない——scope認証ゲートを迂回する）
- [ ] 操作は標準API応答形式を返す
- [ ] サポートしていない操作は`retcode=10002`を返す
- [ ] ネットワークエラーは`retcode=33xxx`（API応答標準に準拠）を返す

### リクエストタイプコンテキスト保持（異質なエンドポイントプラットフォーム、§5.3参照）
- [ ] リクエストイベントのエントリーポイントで`request_id → {リクエストタイプ, sub_type, group_id, アカウント}`のコンテキストを保持している
- [ ] 条目のフィールドは§5.3.3の統一条目フィールド表と一致している（`ts`タイムスタンプを含む；`request_id`は1対1対応、処理後に削除）
- [ ] `accept` / `reject`のエンドポイントルーティング順序はkwargsの明示的パラメータ > キャッシュ > フォールバックデフォルトエンドポイント + WARNING
- [ ] タイプのオーバーライドパラメータは保留名`request_type` / `sub_type` / `group_id`（`_request_type`などの非公開名は使用しない）を使用している
- [ ] キャッシュにはTTLと容量上限があり、操作が成功した後に該当条目を削除している
- [ ] 多アカウント：操作アカウントは`self.request_context.get("account_id")`から読み取っている（`Using()` > イベントチェーンのフォールバック、Sendの`send_context`と同口径）；保持されたアカウントはイベントチェーンが欠落した場合のフォールバック（例：ポーリング合成イベント、再起動後の再構築）
- [ ] 承認アカウントの解析失敗は即時失敗（34005）、デフォルトアカウントにフォールバックしない
- [ ] デフォルトは統一ストレージの単一キーのスナップショット：起動時に読み込み、イベント到着/処理後に書き込み、ストレージが利用できない場合はメモリのみに降格（WARNING）、イベントフローをブロックしない

単一のリクエストエンドポイントを持つプラットフォーム（統一`/set_request`）は保持する必要がない。本節はアダプタ実装の口径であり、`Request` DSL契約は影響を受けない。

## 7. エラーコードの拡張

リクエスト操作に関連する**アダプタ実装層**の推奨エラーコード（[API応答標準](api-response.md)§3.2に準拠し、`34xxx`プラットフォームエラーセグメントの下3桁にカスタム定義）：

| エラーコード | エラーネーム | 説明 |
|-------|-------|------|
| 34001 | Request Not Found | リクエストが存在しないまたは期限切れ |
| 34002 | Request Already Handled | リクエストは既に処理済み |
| 34003 | Request Not Supported | プラットフォームはこのタイプのリクエスト操作をサポートしていない |
| 34004 | Permission Denied | Botはこのリクエストを処理する権限がない（プラットフォームが返す） |
| 34005 | Request Account Unresolved | リクエスト所属アカウントがアカウントインスタンスに解析できない（即時失敗、デフォルトアカウントにフォールバックしない） |

> **フレームワークコードとの境界**：上記の`340xx`は**プラットフォーム/アダプタ**が返すリクエスト処理失敗です。ErisPulseフレームワークは`scope.actions`でモジュールの`request`アクションを禁止した場合、**アダプタを呼び出す前に**直接`34601`（Action Denied、[API応答標準§5.3](api-response.md#53-フレームワーク拡張返却コード34xxx-プラットフォームエラーセグメントの下3桁にカスタム定義)）を返します。これらは互いに代替ではなく、まず`34601`フレームワークゲートを通過し、次にプラットフォーム層の`340xx`エラーに到達します。

## 8. 関連ドキュメント

**リクエスト操作を実装する際に併せて参照するべきドキュメント**：
- [イベント変換標準](event-conversion.md) - 完全なイベント変換規格（`request_id`フィールド要件を含む）
- [API応答標準](api-response.md) - アダプタAPI応答形式の標準（操作返却値とエラーコード）
- [ストレージバックエンド](../advanced/storage-backends.md) - 起動後にリクエストコンテキストを永続化する必要がある場合の統一KVストレージ

**同一アダプタの他のDSL**：
- [送信メソッド規格](send-method-spec.md) - Sendクラスのメソッド命名とパラメータ規格
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング関係