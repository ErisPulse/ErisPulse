---
name: erispulse-communication
description: "适用于：模块间通信（RPC/定向/广播）、HTTP/WS 客户端、连接管理。覆盖场景：**この記事を読むタイミング**：RPCによるモジュール間呼び出し、サービス契約、宛先指定イベント、またはコールドスタート時のイベントリプレイが必要な場合。必要なければ飛ばしても、他の機能の使用に影響はありません。**この記事を読むタイミング**：WebSocket/SSE 接続プール、ブロードキャストのグループ分け、モジュール間のプッシュ、または接続を確認する必要がある場合に読んでください。必要がない場合は飛ばしても、他の機能の使用には影響しません。**この記事を読む必要があるのは**：出力（outbound）の HTTP / WebSocket リクエストが必要な場合。必要ない場合はスキップしても、他の機能への影響はありません。**この記事を読むタイミング**：HTTP / WebSocket / SSE ルーティング（接続プールによるブロードキャスト含む）が必要な場合。不要であればスキップしても、他の機能の使用に影響はありません。"
---

# ErisPulse 通信与连接

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 模块间通信: 72-98 行
- RPC: module.call: 100-127 行
- サービス契約: meta.services: 129-190 行
- サービスディレクトリ: services(): 192-210 行
- 出力審査: 誰が誰を呼び出せるか: 212-226 行
- 指定イベント: lifecycle.emit の to パラメータ: 228-254 行
- ラグジュアリーなモジュールと呼び出し: 256-266 行
- クールスタート時の再再生: 268-296 行
- イベントの冪等性と重複除去: 298-307 行
- 関連ドキュメント: 309-315 行
- 连接管理: 317-338 行
- 概要: 340-367 行
- 接続プールの確認: 369-392 行
- ブロードキャストとサブスクリプション: 394-455 行
- モジュール間の渡し渡し / 再利用: 457-476 行
- 出向接続（クライアント側）: 478-491 行
- スレッド間の投递: 493-507 行
- アンロードとクリーンアップの意味: 509-514 行
- API 一覧: 516-530 行
- 関連ドキュメント: 532-537 行
- HTTP 客户端: 539-548 行
- 概要: 550-561 行
- 速習: 563-610 行
- HttpResponse: 612-633 行
- リクエストメソッド: 635-718 行
- パラメータの説明: 720-741 行
- タイムアウトとリトライ: 743-761 行
- デフォルトヘッダーのカスタマイズ: 763-773 行
- リクエスト統計: 775-786 行
- ライフサイクルイベント: 788-812 行
- コンテキストマネージャー: 814-821 行
- WebSocketクライアント: 823-930 行
- 例外体系: 932-1008 行
- アダプターでの使用: 1010-1033 行
- 最適な実践: 1035-1043 行
- 関連ドキュメント: 1045-1049 行
- 路由: 1051-1060 行
- 概要: 1062-1077 行
- 抽象型: 1079-1091 行
- デコレータルーティング（推奨）: 1093-1211 行
- 伝統的な登録方法: 1213-1278 行
- WebSocket ライフサイクルフック: 1280-1302 行
- ルーティンググループ: 1304-1319 行
- ルーティングミドルウェア: 1321-1336 行
- リクエスト関連ID（X-Request-ID）: 1338-1361 行
- レート制限: 1363-1377 行
- CORS 設定: 1379-1396 行
- セキュリティヘッダー: 1398-1411 行
- 自動ドキュメント: 1413-1427 行
- パス処理: 1429-1440 行
- システムルーティング: 1442-1461 行
- ホームエントリ: 1463-1500 行
- ライフサイクル統合: 1502-1514 行
- ベストプラクティス: 1516-1524 行
- 関連ドキュメント: 1526-1531 行

## 模块间通信

> 来源: `docs/ja/advanced/module-communication.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/advanced/module-communication.md）

# モジュール間通信

> [!TIP]
> **この記事を読むタイミング**：RPCによるモジュール間呼び出し、サービス契約、宛先指定イベント、またはコールドスタート時のイベントリプレイが必要な場合。必要なければ飛ばしても、他の機能の使用に影響はありません。

> **この記事を読んだ後には**：3層通信モデル（RPC / 宛先指定イベント / ブロードキャスト）の選択のコツ、`meta.services` によるサービス契約とサービスディレクトリ、出向き監査の設定方法、およびラグドウォーキングとコールドスタート時のイベントリプレイについて理解できます。
>
> **この記事では扱いません**：ライフサイクルイベントシステム自体の登録 / 発火 / 優先度のメカニズム（[ライフサイクル管理](lifecycle.md)を参照）；ラグドロードの設定と activate_on の宣言（[ラグドロードシステム](lazy-loading.md)を参照）。

> [!NOTE]
> 本章の内容は ErisPulse **2.8.0+** が必要です。

ErisPulse では、モジュール間には**3層の通信モデル**が存在し、「点対点 → 宛先指定 → ブロードキャスト」の順序で構成されています：

| 層 | API | 意味 | 代表的なシナリオ |
|---|---|---|---|
| **RPC** | `await sdk.module.call("Chat", "get_history", ...)` | 点対点のリクエスト-レスポンス、契約 / 監査 / タイムアウト付き | 他のモジュールの機能を呼び出す（履歴の取得、翻訳、返金など） |
| **宛先指定イベント** | `await lifecycle.emit("message_received", {...}, to="Chat")` | 指定されたモジュールが登録したライフサイクルフックにのみ配信 | 上流の状態変化を下流に通知する（「新しいメッセージを受け取りました」など） |
| **ブロードキャスト** | `await lifecycle.emit("config.updated", {...})` | フレームワーク全体で見えるライフサイクルイベント | 設定のホットアップデート、モジュールの起動 / 終了 |

{!--< tips >!--}
選択のコツ：**返り値が必要な場合は `call` を使い、特定のモジュールのフックに通知したい場合は `emit(..., to=...)` を使い、全員に通知したい場合は `emit(...)` を使う**。
{!--< /tips >!--}

## RPC: module.call

```python
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

`sdk.module.Chat.get_history(...)`（変更なし）の属性アクセスとの違いは以下の通りです：

| | `module.call()` | 属性アクセス |
|---|---|---|
| 目標が登録されていない / 有効になっていない | `ModuleNotAvailableError` をスロー | `AttributeError` をスロー |
| ラグジュアリーなモジュール | **自動的に起動**（イベント駆動モジュールはアクティベーションロックを通過） | 非同期初期化モジュールは `RuntimeError` をスロー |
| `current_owner` | **ターゲットモジュール**に帰属（内部の wait_reply / 送信 / ログは正しい帰属） | 呼び出し元に保持 |
| タイムアウト | 30秒（`timeout=` で上書き、None でタイムアウトなし） | なし |
| scope 審査 | 呼び出し元が出口のゲートを通過 `actions.<呼び出し元>.call` | なし |
| 契約検証 | `meta.services` のホワイトリスト | なし |

### エラー体系

```
ModuleError                      # モジュールシステムのエラー基底クラス
└── ModuleCallError              # 跨モジュール呼び出しの基底クラス（module / method 属性を含む）
    ├── ModuleNotAvailableError  # 目標が登録されていない / 有効になっていない / 起動に失敗
    ├── ServiceNotProvidedError  # メソッドが services ホワイトリストにない / 私的メソッド / 存在しない
    └── ModuleCallTimeoutError   # クロージャー関数がタイムアウト
```

すべて `ErisPulseError` 体系に属し、`from ErisPulse.Core import ModuleCallError` でキャッチ可能です。

## サービス契約: meta.services

サービス提供者は `get_meta()` で公開するホワイトリストを宣言します（`commands` と対称）：

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="チャット",
            services=[
                "get_history",                                       # 簡単な形
                {"name": "translate", "description": "テキストを指定された言語に翻訳する"},  # 説明付き
            ],
        )

    async def get_history(self, session_id, n=20): ...
    async def translate(self, text, target_lang): ...
    def _internal_helper(self): ...   # 下線付きメソッドは外部から呼び出し禁止
```

**開発者は無感覚なデフォルト**：

- `services` を宣言していない → **公開**メソッドはすべて `module.call()` で呼び出せる（属性アクセスと同様）、宣言は不要
- 宣言後 → ホワイトリストに絞られ、越境呼び出しは `ServiceNotProvidedError` をスロー——「これが外部に約束したメソッド」を明示する
- 制限の**主制御権はユーザー側**：`scope.actions` の設定が「誰が誰を呼び出せるか」を決定（後述の審査参照）、モジュール作者の `services` はサービス面の宣言に過ぎず、2つの層は互いに置換不可能

**サービス紹介**：各サービスに人間 / AI が読める説明を付ける——不要なら何も書かなくてよい、説明は**メソッドの docstring 首行**（フレームワークは docstring 形式を要求している）から自動取得：

```python
async def translate(self, text, target_lang):
    """テキストを指定された言語に翻訳する"""    # ← この行がサービス紹介として自動取得される
    ...
```

**パラメータ提示**：呼び出し元（特に AI エージェント）は各パラメータの意味を知る必要がある。不要なら何も書かなくてよい、提示はメソッドの docstring の **`:param:` 行**から自動取得：

```python
async def render_card(self, html, width=800, height=0):
    """HTMLを画像ファイルにレンダリングする

    :param html: レンダリングするHTMLテキスト          ← 自動的にパラメータ提示として取得される
    :param width: 画布の幅ピクセル、0は内容に応じて自動調整
    :param height: 画布の高さピクセル、0は内容に応じて自動調整
    """
```

微調整が必要な場合（docstring を上書き / 多言語対応）は dict 形式で `description` と `parameters` を宣言（両方とも i18n 辞書に対応；`parameters` は**パラメータ**と docstring をマージし、docstring が優先、宣言されたが存在しないパラメータはフィルタリングされる）：

```python
services=[
    {"name": "translate", "description": "テキストを指定された言語に翻訳する"},
    {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "会話の要約"}},
    {
        "name": "render_card",
        "description": "HTMLを画像ファイルにレンダリングする",
        "parameters": {"html": "HTMLテキスト", "width": "幅ピクセル、0は自動調整"},
    },
]
```

## サービスディレクトリ: services()

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': 'テキストを指定された言語に翻訳する',
#            'parameters': {'session_id': 'セッションID', 'n': '返却件数'}}]}

sdk.module.services("Chat")   # 指定されたモジュールのみを照会
```

- **明示的に `meta.services` を宣言したモジュール**のみをリストアップ（宣言していないモジュールはディレクトリに表示されない）
- 各サービスにはメソッドのシグネチャ文字列（`inspect.signature` から抽出）、説明文、パラメータ提示が付く
- **ラグジュアリーなモジュールもディレクトリに表示される**（サービス発見はロードより先に発生）——呼び出し元はこれにより、`call()` でターゲットモジュールを起動するかを判断できる
- トポロジーにも反映される：`sdk.module.get_topology()` の各モジュール項目に `services` フィールドが含まれる

{!--< tips >!--}
**MCP 化の道筋**：サービスディレクトリ（名前 + シグネチャ + 説明 + パラメータ提示）は MCP tool の形状に相当する——各サービスは自然に ``{"name", "description", "parameters"}`` になる。将来、フレームワークは ``services()`` を直接 MCP サーバエンドポイントとして公開し、AI がモジュールの能力を発見して呼び出せるようにする。また、``scope.actions.call`` 審査は AI 呼び出しのセキュリティゲートとして自然に機能する。
{!--< /tips >!--}

## 出力審査: 誰が誰を呼び出せるか

`module.call()` は**呼び出し元モジュール**の立場で scope の出力ゲートを通過する：

```toml
[ErisPulse.scope.actions.CallerModule.call]
deny = ["Chat.get_history"]        # CallerModule が Chat の get_history を呼び出すことを禁止
# allow = ["Chat.get_*"]           # またはホワイトリスト：get で始まるサービスのみを許可
```

- `name` の形式は `<ターゲットモジュール>.<メソッド名>`、正確な一致 / glob / `re:` 正規表現が可能
- フレームワーク層の呼び出し（owner コンテキストがない、例：起動スクリプト）は審査制約を受けない
- 拒否された呼び出しは `ModuleCallError` をスロー（TRACE ログ `core.module.call_denied`）

設定方法は [作用域（scope）](scope.md) の出力側の詳細を参照。

## 指定イベント: lifecycle.emit の to パラメータ

ライフサイクルイベントは指定送信をサポート：`to` でターゲット所有者（owner）を指定すると、イベントはその owner として登録されたフックにのみ配信される（`on_load` 内で登録されたフックは自動的に本モジュールに帰属）、他のモジュールやワイルドカード `*` ハンドラは感知しない。

```python
from ErisPulse.Core.lifecycle import lifecycle

# 投递元：イベントは Chat モジュールが登録したフックにのみ投递される
await lifecycle.emit("message_received", {"text": "hi", "from": "u1"}, to="Chat")

# 訂閱元（Chat モジュール内）：同名のフックを登録し、owner は登録時に自動的に記録される
@lifecycle.on("message_received")
async def on_message_received(data): ...

@lifecycle.on("message")          # 点式の親前缀も同様に有効（owner でフィルタリング）
async def on_any(data): ...
```

意味の詳細：

- ターゲット owner に登録されたフックがない → イベントは**静かに破棄**（**存在しない場所には送らない**）、`lifecycle.has_handlers("message_received")` で事前に検出可能
- `data` が dict の場合、`_trace_id` が自動的に付与される（既存値を上書きしない）、全トラッキングと連携
- ブロードキャストと指定は同じフック登録を共有：`emit(...)` に `to` を指定しないと全フレームワークにブロードキャスト、`to` を指定すると同一イベントはターゲットモジュールにのみ見える
- `emit_sync` / `submit_event`（互換 API）も `to=` パラメータをサポート

> [!NOTE]
> 指定イベントは軽量な通知であり、**ターゲットの検証やラグジュアリーな起動は行わない**；ターゲットの存在性検証、契約審査、または返り値が必要な場合は、[RPC: module.call](#rpcmodulecall) を使用してください。

## ラグジュアリーなモジュールと呼び出し

`module.call()` はラグジュアリーなモジュールに対して**透明な起動**を行う：

- イベント駆動ラグジュアリーなモジュール（`activate_on` で宣言）→ 活性化ロック `_activate()` を通る、活性化後はトリガースタブが自動的に登録解除
- 通常のラグジュアリーなモジュール → 同期初期化または通常のロード経路（冪等）
- 起動に失敗 → `ModuleNotAvailableError`

つまり：**呼び出し元はターゲットモジュールがロードされているかどうかを気にする必要はない**、また、ターゲットを起動するために特定のイベントを待つ必要もない。

指定イベント（`lifecycle.emit(..., to=...)`）はラグジュアリーな起動を行わない——ターゲットがロードされていないとフックが存在しない、イベントは静かに破棄される；確実に送信したい場合は `module.call()` を使用してください。

## クールスタート時の再再生

新規インストール / 再起動のモジュールは一部のチャットを逃した——`get_load_strategy(replay=...)` により、フレームワークはモジュールが準備された後、会話の受信箱に含まれる最近のメッセージを**再再生**してモジュール自身に送る：

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyAIModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=100,
            replay="5m",        # 最近の5分間を再再生（"1h" / "300"秒の形式も可）
        )

    async def on_load(self, event):
        @message.on_message()
        async def handle(e):
            if e.get("replayed"):
                # 合成イベント：コンテキストの補完のみ、送信などの副作用は発生しない
                ...
```

意味の詳細：

- データソースは[会話の受信箱](interaction.md#会話受信箱eventhistory)（`sdk.transcript.recent()`）であり、モジュールのロード完了後にバックグラウンドで実行され、起動をブロックしない
- 合成イベントには `replayed: True` フラグ、`platform / detail_type / user_id / alt_message` が含まれ、**本モジュールのハンドラにのみ分発される**——他のモジュールには再再生の影響を受けない
- 受信箱が有効 / 記録がない / 時間の宣言が不正（`replay_invalid` 警告）の場合は静かにスキップされる

## イベントの冪等性と重複除去

プラットフォームの websocket 再接続後に同じイベントが重複送信されることがよくある（同じ `event["id"]`）——配信エントリは id に基づいて LRU で重複除去（容量 4096）、同じ id のイベントは1回しか配信されない。

```toml
[ErisPulse.framework]
event_dedupe = true   # 既定で有効；テスト環境で固定 id の合成イベントを生成する場合は無効化可能
```

アダプターが**登録**（新接続のライフサイクルの起点）されたときに、自動的に重複除去キャッシュがリセットされる。

## 関連ドキュメント

- [インタラクションセッションシステム](interaction.md) - wait_reply / タイマー / マルチウェイティング / セッション排他
- [作用域（scope）](scope.md) - 出力側の審査の完全な設定
- [所有権（owner）システム](ownership.md) - 跨モジュール呼び出しで owner コンテキストがどのように貫かれるか
- [ラグジュアリーなロードシステム](lazy-loading.md) - ラグジュアリーなロードとイベント駆動のアクティベーション（activate_on）
- [ライフサイクル管理](lifecycle.md) - ブロードキャスト層のイベントバスのメカニズム

## 连接管理

> 来源: `docs/ja/advanced/connections.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/advanced/connections.md）

# 接続プールとブロードキャスト

> [!TIP]
> **この記事を読むタイミング**：WebSocket/SSE 接続プール、ブロードキャストのグループ分け、モジュール間のプッシュ、または接続を確認する必要がある場合に読んでください。必要がない場合は飛ばしても、他の機能の使用には影響しません。

> **読了後は**：3 種類の接続がどのように自動的にレジストリに登録されるか、グループサブスクリプションとブロードキャスト API、
> モジュール間での再利用とクローズ権の帰属、およびモジュールのアンロード時に接続がどのようにクリーンアップされるかがわかります。
>
> **本記事では扱いません**：WebSocket / SSE ルーティングの登録方法と接続のライフサイクルフック
> （[ルーティングマネージャー](docs/ja/router.md)を参照）；クライアントからの HTTP リクエスト（[ネットワーククライアント](docs/ja/http-client.md)を参照）。

ErisPulse における接続（サーバー側 WebSocket / SSE / クライアント出向き WebSocket）は**フレームワークレベルで一等のリソース**です：
接続の確立に伴い、自動的に統一されたレジストリに登録され、ブロードキャスト、業務グループのサブスクリプション、モジュール間での転送/再利用が可能であり、
モジュールのアンロード時にはフレームワークが自動的にクローズしてリソースを回収します。これにより、業務コード側で `_ws_clients` 集合を自前で管理する必要がなくなり、
忘れずにクリーンアップしないことでリソースリークが発生する心配もありません。

> 本文書の例はすべて**ルートインポート**の書き方（2.10+ で推奨）を前提としています：
> `from ErisPulse import connections, router, client, WebSocketConnection`

## 概要

```python
from ErisPulse import connections, router, WebSocketConnection

# サーバ側：接続は自動登録され、ハンドラ内で業務グループに参加
@router.ws("MyModule", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")            # グループ名は業務側で自由に命名
    async for msg in ws.iter_text():
        ...                             # 接続が切断された際にはフレームワークが自動的に登録を解除し、グループをクリーンアップ

# 任意の位置で：グループにブロードキャスト（成功/失敗の詳細を返す）
result = await connections.broadcast({"type": "notify"}, group="room:1")
if not result.ok:
    ...                                 # result.failed: {接続ID: 例外}

```

3種類の接続はすべて登録表に統合されます：

| kind | 来源 | 归属 owner | 说明 |
|------|------|-----------|------|
| `server` | `@router.ws(...)` / `register_websocket(...)` | ルートを登録したモジュール名 | 接続切断時に自動的に登録を解除 |
| `sse` | `@router.sse(...)` / `register_sse(...)` | ルートを登録したモジュール名 | ブロードキャストは `sse.send()` を使用 |
| `client` | `await client.ws_connect(url)` | 現在のモジュール（または明示的な `owner=`） | 接続の閉じる、リモート切断時に自動的に登録を解除；アダプターが停止した際にはフレームワークが一括して閉じる |

自動登録を不要とする場合：ルートに `track=False` を渡すか、出向接続に `track=False` を渡すことで、従来のコードの挙動は完全に維持されます。

## 接続プールの確認

```python
from ErisPulse import connections

# 特定のモジュールの接続プールを確認（「現在、あるモジュールに何本の接続があるか」）
conns = connections.list(namespace="Dashboard")
for conn in conns:
    print(conn.id, conn.kind, conn.groups, conn.meta)

# その他の条件でフィルタリング（すべての条件がAND条件）
connections.list(owner="MyAdapter", kind="client")
connections.list(group="tenant:acme")

# 全体の統計情報（各条件のカウント）
stats = connections.stats()
# {'total': 5, 'by_kind': {...}, 'by_namespace': {...}, 'by_owner': {...}, 'groups': {...}}

# 所有権監査のカウント（ownership インターフェースでも確認可能）
from ErisPulse import ownership
ownership.counts("Dashboard")   # {'connections': 3, ...}
```

各接続は以下の識別情報を読み取ることができます：`conn.id`（例: `Dashboard:1a2b3c4d`）、`conn.namespace`、`conn.owner`、`conn.kind`、`conn.groups`、`conn.meta`（業務用の自由な辞書）。

## ブロードキャストとサブスクリプション

### グループ（サブスクリプションモデル）

グループは**フラットな文字列**であり、命名は完全に業務側の合意によって行われます（ルーム / テナント / トピックなど）。ネストされた階層は命名規則で表現します（例: `tenant:acme/room:1`）。フレームワークは形式を制限しません。

両方向から操作が可能です：

```python
# 方向1：接続側が参加/退出（ハンドラ内で）
@router.ws("Chat", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")        # 等価: connections.assign(ws.id, "room:1")
    ws.leave_group("room:1")

# 方向2：管理側が割り当て（ルート側 / 他のモジュール）
connections.assign(conn_id, "tenant:acme")
connections.dismiss(conn_id, "tenant:acme")   # グループ名を指定しない場合はすべてのグループから退出
```

接続が切断された際には、すべてのグループから自動的に退出し、業務側によるクリーンアップは不要です。

### ブロードキャスト

```python
result = await connections.broadcast(
    data,                       # WS は send_json を使用；SSE は send を使用（自動的にJSONシリアライズ）
    namespace="Dashboard",      # 名前空間でフィルタリング
    group="room:1",             # グループでフィルタリング
    kind="sse",                 # 接続の種類でフィルタリング
    owner="MyAdapter",          # 所有者でフィルタリング
    ids={conn_id, ...},         # 明示的に候補集を指定（フィルタ条件は依然有効）
    exclude={conn_id},          # 特定の接続を除外
    timeout=10.0,               # 単一接続の送信タイムアウト（トータルの時間ではなく）
    concurrency=64,             # 並列送信の上限
    raise_on_error=False,       # True の場合、失敗した項目があると最初の例外を送出
)
result.total      # 目標接続の総数（除外前に）
result.sent       # 成功した接続IDのリスト
result.failed     # {接続ID: 例外オブジェクト}（タイムアウト/切断済み/送信失敗）
result.excluded   # 除外された接続ID
result.ok         # 全て送信されたか
```

フィルタ条件は **AND** で処理されます。1件の失敗は他の接続への影響はありません。`ids` に存在しない接続は `failed` にカウントされ、業務側が状況を把握できるようにします。

### ライフサイクルイベント

接続の登録/登録解除/グループ変更は標準的なライフサイクルイベントとして発行され、Dashboard などのコンポーネントはサブスクライブしてリアルタイムに表示できます：

```python
from ErisPulse import lifecycle

@lifecycle.on("connection.registered")
async def on_registered(data): ...
@lifecycle.on("connection.unregistered")
async def on_unregistered(data): ...
@lifecycle.on("connection.group.joined")
async def on_joined(data): ...
@lifecycle.on("connection.group.left")
async def on_left(data): ...
```

## モジュール間の渡し渡し / 再利用

接続はフレームワークが登録したリソースであり、どのモジュールでも接続IDを使って取得して**再利用**できます。自前で新たな接続を作成する必要も、誰が接続を作成したかを知る必要もありません：

```python
from ErisPulse import connections

conn = connections.get("Dashboard:1a2b3c4d")   # 存在しない/切断済みの場合は ConnectionNotFoundError を送出
await conn.send_json({"ping": 1})              # どのモジュールからでも送信可能
conn.join_group("someone-elses-room")          # グループ参加も可能
```

**所有権と閉じる権限**：

- 接続の `owner`（作成したモジュール）は、閉じる権限を独占します。非 owner が `close()` を呼び出すと `ConnectionPermissionError`（`from ErisPulse import ConnectionPermissionError`）が送出されます；
- 送信やグループ操作は、どのモジュールからでも許可なく実行可能です；
- owner モジュールのアンロード / アダプターの停止時に、フレームワークは**一括して閉じて登録を解除**します（サーバ側 + 出向接続）。取得した参照で送信を試みても失敗結果が返り、`connection.unregistered` イベントを監視することで感知できます；
- フレームワーク内部のリソース回収には `close(force=True)` を使用して検証を回避します。

> 説明：閉じる権限の検証は、実行時の owner コンテキスト（`owner_scope` / イベント配信 / `spawn_background` など）に依存します。コンテキストが不明な呼び出し（古いコードなど）は許可され、破壊的な影響をゼロに保ちます。新しいコードでは、owner コンテキスト内で呼び出すことで保護されます。

## 出向接続（クライアント側）

```python
from ErisPulse import client

ws = await client.ws_connect("wss://example.com/ws")
ws.id          # 登録済みで、connections で検索/ブロードキャストが可能
ws.owner       # 現在のモジュール（owner コンテキストが利用できない場合は明示的に指定）

# owner コンテキストが利用できない場合（例：ツールスレッドのコールバック）は明示的に指定し、アンロード時に自動回収されます：
ws = await client.ws_connect("wss://example.com/ws", owner="MyAdapter")
```

リモート側が切断した場合、またはローカルで `close()` を呼び出した場合、自動的に登録を解除します。モジュールのアンロード時には、フレームワークがその名下のすべての出向接続を閉じます。これにより、従来のコードで接続を自前で管理し忘れることによるリソースリークはなくなりました。

## スレッド間の投递

子スレッドから接続にアクセスする場合（ブロードキャスト / プッシュ / 閉じる）には、フレームワークの標準的なツールを使ってメインループに投递してください。**`run_coroutine_threadsafe` を手書きで使用しないでください**：

```python
from ErisPulse import run_main_loop, spawn_later, spawn_thread

# 子スレッドでブロックして結果を取得：
run_main_loop(connections.broadcast({"tick": 1}, group="room:1"), timeout=5)

# バックグラウンドスレッド + 遅延タスク（所有権の割り当て、アンロード時に自動キャンセル）：
def push_tick():
    return connections.broadcast({"tick": 1}, group="room:1")
spawn_later(30, push_tick, owner="MyModule")
```

## アンロードとクリーンアップの意味

モジュールのアンロード / アダプターの停止時の所有権回収の流れは次のように進行します：所属するバックグラウンドタスクやタイマーのキャンセル → **所属する接続の閉じて登録を解除** → `on_cleanup` フックの呼び出し → ルート/ハンドラなどの登録済みリソースの登録解除。詳細は [所有権（owner）システム](ownership.md) を参照してください。

> [!WARNING]
> 2.10以降、モジュールのアンロード時に登録された WS/SSE/出向接続が閉じられます。アンロード後に接続が生き続けることを依存している下流コンポーネント（例：旧バージョンの Dashboard プッシュ）は、これはリソースリークを防ぐ意図的な挙動であることを認識する必要があります。

## API 一覧

| API | 说明 |
|-----|------|
| `connections.get(id)` | 接続を取得（モジュール間のエントリーポイント）、存在しない場合は `ConnectionNotFoundError` を送出 |
| `connections.list(namespace=, owner=, group=, kind=)` | 接続のリストをフィルタリングして取得 |
| `connections.stats(namespace=, owner=)` | 各条件のカウント統計 |
| `connections.assign(id, *groups)` / `dismiss(id, *groups)` | 管理側によるグループ参加/退出 |
| `await connections.broadcast(data, ...)` | ブロードキャスト、`BroadcastResult` を返す |
| `await connections.close(id, force=False)` | 閉じて登録を解除（権限チェックあり） |
| `await connections.close_owner(owner)` | 指定 owner 名下のすべての接続を閉じて登録を解除（フレームワークのアンロードチェーンで呼び出される） |
| `conn.join_group(*groups)` / `conn.leave_group(*groups)` | 接続側によるグループ参加/退出 |
| `conn.send_json / send_text / iter_text / ...` | 受信/送信（サーバ側/クライアント側のインターフェースは同一） |
| `conn.meta` | 業務用メタデータ辞書 |
| `conn.close(force=False)` | 閉じる（非 owner は `ConnectionPermissionError` を送出） |

## 関連ドキュメント

- **登録サービス側 WS / SSE ルート** → [ルートマネージャー](router.md)
- **クライアント側出力 WebSocket の構築** → [ネットワーククライアント](v2/client.md)
- **モジュールのアンロード時に接続がどのように回収されるか** → [所有権（owner）システム](ownership.md)
- **接続関連の例外（`ConnectionNotFoundError` / `ConnectionPermissionError`）** → [例外体系とキャッチガイド](errors.md)

## HTTP 客户端

> 来源: `docs/ja/advanced/http-client.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/advanced/http-client.md）

# ネットワーククライアント

> [!TIP]
> **この記事を読む必要があるのは**：出力（outbound）の HTTP / WebSocket リクエストが必要な場合。必要ない場合はスキップしても、他の機能への影響はありません。

ErisPulse は、HTTP リクエスト、WebSocket 接続、および接続プール管理を統合した一貫したネットワーククライアントを提供しています。モジュールやアダプタは、**このクライアントを優先的に使用する必要があります**。`aiohttp` / `httpx` / `requests` などの外部ライブラリを直接インポートしてはいけません。

## 概要

ネットワーククライアントの主な機能は以下の通りです：

- **統一されたインターフェース**：`get` / `post` / `put` / `delete` / `patch` / `request` メソッドを提供
- **WebSocketクライアント**：`ws_connect` でクライアントWebSocket接続を確立
- **自動ログ**：すべてのリクエストに対して自動的にログと統計情報を記録
- **ライフサイクル統合**：リクエストごとに `client.request` ライフサイクルイベントがトリガーされ、WS接続は `client.ws.connect` イベントを発生
- **リトライサポート**：自動リトライの回数と間隔を設定可能
- **タイムアウト制御**：接続タイムアウトとリクエストタイムアウトを個別に設定
- **接続プールの再利用**：aiohttp.ClientSession に基づく接続プール管理
- **例外体系**：aiohttpの例外をErisPulseの例外（ClientError体系）に自動変換

## 速習

### HTTPリクエスト

```python
from ErisPulse.Core import client

# GETリクエスト
resp = await client.get("https://httpbin.org/get")
data = await resp.json()
print(resp.status)  # 200

# POSTリクエスト
resp = await client.post(
    "https://httpbin.org/post",
    json={"key": "value"},
)
data = await resp.json()
```

### WebSocket接続

```python
from ErisPulse import client   # 2.10+ からのルートインポート（ErisPulse.Core.client は深階層でも互換性あり）

ws = await client.ws_connect("wss://example.com/ws")

async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

#### 出力接続の自動プール登録（2.10+）

`ws_connect` で確立された接続は**デフォルトでフレームワークの接続プールに登録**されます（`track=False` で無効化可能）：
`connections.list(owner=...)` で確認でき、その接続にブロードキャストが可能。接続が閉じられたり、リモートが切断された場合、自動的に登録解除されます。
**モジュールのアンロード / アダプターの停止時に、フレームワークがその名下のすべての出力接続を一括で閉じる**ため、リークを防ぎます。

```python
from ErisPulse import client, connections

ws = await client.ws_connect("wss://example.com/ws")
print(ws.id, ws.owner)   # 登録済み：接続IDと所有者

# ownerコンテキストが使用できない場合（例：ツールスレッドのコールバック）は、明示的に所有者を指定し、アンロード時に自動回収されるようにする：
ws2 = await client.ws_connect("wss://example.com/ws2", owner="MyAdapter")
```

接続プールとブロードキャストの詳細は[接続プールとブロードキャスト](connections.md)を参照してください。

## HttpResponse

すべてのリクエストメソッドは `HttpResponse` オブジェクトを返します：

```python
from ErisPulse.Core import client

resp = await client.get("https://httpbin.org/get")

resp.status       # int - HTTPステータスコード (例: 200, 404)
resp.reason       # str | None - ステータス説明 (例: "OK")
resp.headers      # レスポンスヘッダー (大文字小文字を区別しない)
resp.content_type # str | None - Content-Type
resp.url          # 最終URL (リダイレクトにより変更される可能性がある)
resp.raw          # 低レベルの元のレスポンスオブジェクト (現在は aiohttp.ClientResponse)

# レスポンスボディの読み取り
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # JSONを解析
text = await resp.text("gbk")  # 指定したエンコーディング
```

## リクエストメソッド

### GET

```python
from ErisPulse.Core import client

resp = await client.get(
    "https://api.example.com/users",
    params={"page": "1", "limit": "10"},
    headers={"Authorization": "Bearer token"},
)
```

### POST

```python
from ErisPulse.Core import client

# JSONリクエストボディ
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# フォームリクエストボディ
resp = await client.post(
    "https://api.example.com/login",
    data={"username": "admin", "password": "123"},
)

# バイナリデータ
resp = await client.post(
    "https://api.example.com/upload",
    data=b"raw bytes",
    headers={"Content-Type": "application/octet-stream"},
)

# ファイルアップロード (filesパラメータを使用、aiohttpをインポートする必要はない)
# 形式: {フィールド名: ファイルオブジェクト/bytes/(filename, file)/(filename, file, content_type)}
resp = await client.post(
    "https://api.example.com/upload",
    data={"description": "プロフィール画像"},            # 任意: 通常のフォームフィールドも同時に送信可能
    files={
        "file": ("photo.png", open("photo.png", "rb"), "image/png"),
    },
)

# 簡略化された書き方: ファイルオブジェクトを直接渡す
resp = await client.post(
    "https://api.example.com/upload",
    files={"file": open("photo.png", "rb")},
)

# メモリ内のデータを直接アップロード (ファイルに落とす必要はない)
import io

resp = await client.post(
    "https://api.example.com/upload",
    files={"file": ("data.txt", io.BytesIO(b"file content"), "text/plain")},
)
```

### PUT / DELETE / PATCH

```python
from ErisPulse.Core import client

resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})
```

### 一般的なrequest

```python
from ErisPulse.Core import client

resp = await client.request(
    "OPTIONS",
    "https://api.example.com/resource",
    headers={"Origin": "https://example.com"},
)
```

## パラメータの説明

### HTTPリクエストパラメータ

| パラメータ | 型 | 説明 |
|------|------|------|
| `url` | `str` | リクエストURL |
| `params` | `dict[str, str]` | クエリパラメータ (オプション) |
| `headers` | `dict[str, str]` | 追加のリクエストヘッダー (オプション) |
| `data` | `Any` | リクエストボディ (フォームまたはバイナリデータ) (オプション) |
| `json` | `Any` | JSONリクエストボディ (オプション) |
| `files` | `dict[str, Any]` | ファイルアップロードフィールド (オプション、multipart/form-dataを自動構築) |
| `timeout` | `float` | 今回のリクエストのタイムアウト (秒) (オプション、デフォルト値を上書き) |
| `max_retries` | `int` | 今回の最大リトライ回数 (オプション、デフォルト値を上書き) |

### ws_connect パラメータ

| パラメータ | 型 | 説明 |
|------|------|------|
| `url` | `str` | WebSocketサーバーのURL |
| `headers` | `dict[str, str]` | 追加のリクエストヘッダー (オプション) |
| `heartbeat` | `float` | ハートビートの間隔 (秒) (オプション) |

## タイムアウトとリトライ

```python
from ErisPulse.Core import Client

# タイムアウトを設定したクライアントを作成
client = Client(
    timeout=60,           # リクエスト全体のタイムアウト 60秒
    connect_timeout=5,    # 接続のタイムアウト 5秒
    max_retries=3,        # 失敗時に自動リトライ 3回
    retry_delay=2,        # リトライ間隔 2秒
)

# 単一のリクエストでタイムアウトを上書き
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

> [!NOTE]
> クライアントクラスは 2.8.0 から `Client` に名前が変更されました（`sdk.client` の属性名は変更されません）；`HttpClient` は旧名として互換性の別名として残されています。古いコードは変更する必要はありません。

## デフォルトヘッダーのカスタマイズ

```python
client = Client(
    headers={
        "Authorization": "Bearer token",
        "X-App-Id": "my-app",
    },
    user_agent="MyBot/1.0",
)
```

## リクエスト統計

```python
from ErisPulse.Core import client

# 統計情報の取得
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# 統計情報のリセット
client.reset_stats()
```

## ライフサイクルイベント

### HTTPリクエストイベント

リクエストが完了するたびに `client.request` イベントがトリガーされ、監視に使用できます：

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

### WebSocket接続イベント

WebSocket接続が確立されたたびに `client.ws.connect` イベントがトリガーされます：

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.ws.connect")
async def on_ws_connect(event_data):
    print(f"WS接続: {event_data['url']}")
```

## コンテキストマネージャー

```python
# コンテキストマネージャーとして使用し、セッションを自動的に閉じる
async with Client(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## WebSocketクライアント

`client.ws_connect()` を使用して WebSocketクライアント接続を確立し、`ClientWebSocket` オブジェクトを返します。クライアントとサーバーの WebSocket は `WebSocketConnectionBase` 基底クラスを共有し、send/receive/iter のインターフェースは完全に一致します。

### 基本的な使い方

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws", heartbeat=30)

await ws.send_text("Hello")
await ws.send_bytes(b"\x00\x01\x02")
await ws.send_json({"type": "ping"})
```

### メッセージの受信

#### 高レベルメソッド（推奨）

メッセージの種類を自動的にフィルタリングし、切断時に `WebSocketDisconnect` をスローします：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import WebSocketDisconnect

ws = await client.ws_connect("wss://example.com/ws")

# 単一のメッセージ受信
text = await ws.receive_text()    # str
data = await ws.receive_bytes()   # bytes
obj = await ws.receive_json()     # dict / list

# 繰り返し受信 (切断時に自動的に停止)
async for text in ws.iter_text():
    print(text)

async for data in ws.iter_bytes():
    print(data)

async for obj in ws.iter_json():
    print(obj)
```

#### 低レベルメソッド

`receive()` と `iter_messages()` を使用して、原始メッセージの種類を処理し、TEXT / BINARY / CLOSE / ERROR を区別できます：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.websocket import WSMessage

ws = await client.ws_connect("wss://example.com/ws")

# 単一の原始メッセージ受信
msg = await ws.receive()
# msg.type  -> WSMessage.TEXT / WSMessage.BINARY / WSMessage.CLOSE / WSMessage.ERROR
# msg.data  -> str | bytes | None

# 繰り返し原始メッセージ受信 (CLOSE/ERROR で自動的に停止)
async for msg in ws.iter_messages():
    if msg.type == WSMessage.TEXT:
        print(f"テキスト: {msg.data}")
    elif msg.type == WSMessage.BINARY:
        print(f"バイナリ: {len(msg.data)} bytes")
```

### WSMessage

`WSMessage` は、低レベルライブラリに依存しない統一された WebSocketメッセージ型です：

| 属性 | 型 | 説明 |
|------|------|------|
| `type` | `str` | メッセージの種類: `WSMessage.TEXT` / `WSMessage.BINARY` / `WSMessage.CLOSE` / `WSMessage.ERROR` |
| `data` | `Any` | メッセージデータ |

### ClientWebSocket 属性

| 属性 | 型 | 説明 |
|------|------|------|
| `url` | `URL` | 接続URL |
| `headers` | `Headers` | レスポンスヘッダー |
| `closed` | `bool` | 接続が閉じられているか |
| `raw` | `object` | 低レベルの元のオブジェクト (aiohttp.ClientWebSocketResponse) |

### ライフサイクルフック

`サービス側 WebSocketConnection` と同様に、`on_disconnect` と `on_error` のコールバックがサポートされています：

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

@ws.on_disconnect
async def handle_disconnect(ws, reason="unknown"):
    print(f"接続が切断されました: {reason}")

@ws.on_error
async def handle_error(ws, error=""):
    print(f"接続エラー: {error}")
```

### 接続の閉じ方

```python
await ws.close(code=1000, reason="正常な切断")
```

## 例外体系

ErisPulse は、統一された例外階層を定義し、`sdk.client` からリクエストを発行すると、aiohttpの例外がErisPulseの例外に自動的に変換されます。

> **後方互換性**：`aiohttp.ClientSession` を直接使用する古いモジュール/アダプターは完全に影響を受けません。例外変換は `sdk.client` からリクエストを発行する場合にのみ有効で、aiohttpを直接使用するコードは `aiohttp.ClientError` などの元の例外をキャッチします。2つの方法は共存可能です。

### 例外階層

```
ErisPulseError
├── ClientError                  # HTTP/WSクライアントリクエスト例外の基底クラス
│   ├── ClientConnectionError    # 接続失敗 (DNS解決失敗、接続拒否、ネットワーク不可)
│   ├── ClientTimeoutError       # 接続タイムアウトまたはリクエストタイムアウト
│   └── HTTPStatusError          # HTTP 4xx/5xxステータスコードエラー
└── WebSocketError               # WebSocket例外の基底クラス
    └── WebSocketDisconnect      # WebSocket接続切断 (クライアントとサーバー共通)
```

### 例外のキャッチ

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import (
    ClientError,
    ClientConnectionError,
    ClientTimeoutError,
    HTTPStatusError,
    WebSocketDisconnect,
    WebSocketError,
)

# HTTPリクエストの例外処理
try:
    resp = await client.get("https://api.example.com/data")
    data = await resp.json()
except ClientConnectionError:
    print("サーバーに接続できません")
except ClientTimeoutError:
    print("リクエストがタイムアウトしました")
except ClientError as e:
    print(f"リクエストが失敗しました: {e}")

# WebSocketの例外処理
try:
    ws = await client.ws_connect("wss://example.com/ws")
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")
except WebSocketDisconnect as e:
    print(f"接続が切断されました: code={e.code}, reason={e.reason}")
except WebSocketError as e:
    print(f"WebSocketエラー: {e}")
```

### 統一的なキャッチ

`ClientError` を使用して、HTTP/WSクライアントリクエストのすべての例外を統一的にキャッチします：

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await client.get("https://api.example.com/data")
except ClientError as e:
    print(f"クライアントエラー: {e}")
```

### HTTPStatusError

リクエスト後にステータスコードをチェックして例外をスローする必要がある場合、手動で使用できます：

```python
from ErisPulse.Core.Bases.errors import HTTPStatusError

resp = await client.get("https://api.example.com/data")
if resp.status >= 400:
    raise HTTPStatusError(resp.status, await resp.text())
```

## アダプターでの使用

アダプターは、グローバルクライアントまたは独自のクライアントインスタンスを使用してプラットフォームAPIリクエストを送信できます：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases import BaseAdapter
from ErisPulse.Core.Bases.errors import ClientError

class MyAdapter(BaseAdapter):
    async def call_api(self, endpoint, **params):
        try:
            resp = await client.post(
                f"https://api.platform.com/{endpoint}",
                json=params,
                headers={"Authorization": f"Bearer {self.token}"},
            )
            return await resp.json()
        except ClientError as e:
            self.logger.error(f"API呼び出しに失敗しました: {e}")
            raise
```

> `from ErisPulse import sdk` を使用して `sdk.client` を使うことも可能で、効果は同じです。

## 最適な実践

1. **グローバルクライアントの優先使用**：`from ErisPulse.Core import client` を使用してグローバルシングルトンを取得し、フレームワークによる統一管理と監視を容易にする
2. **直接 aiohttp のインポートを避ける**：`client` を使用して `aiohttp.ClientSession` を置き換え、将来の下層実装の変更に伴うコード変更を必要としないようにする。古いコードは直接 aiohttp を使用しても正常に動作し、2つの方法は共存可能
3. **ErisPulse例外体系の使用**：`sdk.client` からのリクエストでは `aiohttp.ClientError` ではなく `ClientError` をキャッチし、特定のHTTPライブラリに依存しないコードを保証する。直接 aiohttp を使用する古いコードは影響を受けない
4. **適切なタイムアウトの設定**：APIの応答速度に応じて適切なタイムアウト時間を設定し、長時間のブロッキングを避ける
5. **リトライメカニズムの使用**：不安定なAPIにはリトライを有効にして、信頼性を高める
6. **リクエスト統計の監視**：`sdk.client.stats` または `client.request` ライフサイクルイベントを使用してリクエスト状況を監視する
7. **WebSocketの高レベルメソッドの使用**：`iter_text` / `iter_json` などの高レベルメソッドを優先し、メッセージの種類を区別する必要がある場合にのみ `iter_messages` を使用する

## 関連ドキュメント

- [ルータマネージャー](router.md) - HTTP/WebSocketサービス側ルーティング（サービス側WebSocketConnectionとクライアントは同一基底クラスを共有）
- [アダプター開発ガイド](../developer-guide/adapters/getting-started.md) - アダプターでHTTPクライアントを使用する
- [ライフサイクル管理](lifecycle.md) - リクエストイベントの監視

## 路由

> 来源: `docs/ja/advanced/router.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/advanced/router.md）

# ルーティングマネージャー

> [!TIP]
> **この記事を読むタイミング**：HTTP / WebSocket / SSE ルーティング（接続プールによるブロードキャスト含む）が必要な場合。不要であればスキップしても、他の機能の使用に影響はありません。

ErisPulse ルーティングマネージャーは、HTTP および WebSocket ルーティングを統一的に管理し、複数のアダプターによるルーティング登録とライフサイクル管理をサポートします。下層では抽象化レイヤーを介してカプセル化されており（現在は FastAPI + Uvicorn）、

## 概要

ルーティングマネージャーの主な機能：

- **デコレータによるルーティング**：`@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` デコレータによる高速登録
- **自動注入**：ルーティングハンドラは FastAPI クラスをインポートする必要がなく、フレームワークが自動的に抽象オブジェクトを注入
- **ルーティンググループ**：プレフィックスとバージョン番号付きの `RouteGroup` をサポート
- **ルーティングミドルウェア**：glob パターンマッチングによるリクエストのインターセプト
- **レート制限**：スライディングウィンドウによるリクエスト制限
- **CORS 支援**：簡単にクロスオリジンリソース共有を有効化
- **セキュリティヘッダー**：自動的にセキュリティレスポンスヘッダーを追加
- **自動ドキュメント**：OpenAPI に基づくインタラクティブなドキュメント
- **WebSocket 支援**：WebSocket 接続の完全な管理、カスタム認証、ライフサイクルフック
- **ライフサイクル統合**：ErisPulse ライフサイクルシステムとの深く統合
- **SSL/TLS 支援**：HTTPS および WSS セキュア接続をサポート
- **ホームエントリ**：モジュールをルートルート `/` に登録し、インターナショナル化をサポートするショートカットボタンを提供

## 抽象型

ErisPulse はサーバーサイド用の抽象型を提供し、モジュールが FastAPI に直接依存しないようにします：

| 抽象型 | FastAPI 対応 | 説明 |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | HTTP リクエストのラッピング、インターフェースは完全に互換性がある |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket 接続のラッピング、ライフサイクルフックを追加 |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket 接続切断の例外 |

> `WebSocketConnection` は `WebSocketConnectionBase` を継承し、クライアント側の WebSocket (`ClientWebSocket`) と同じ send/receive/iter/close インターフェースを共有します。クライアントおよびサーバーサイドの WebSocket は同じビジネスロジックコードを使用できます。
>
> `.raw` 属性を使用して、下層の FastAPI ネイティブオブジェクトにアクセスできます。FastAPI クラスを直接使用するコードも完全に互換性があります。

## デコレータルーティング（推奨）

### 登録形態：単引数（推奨）と二引数

デコレータルーティングは二つの形態をサポートしますが、**単引数を推奨**します。これはコマンド/イベントトリガーと一致し、名前空間は自動的に現在のモジュールに所属します：

```python
from ErisPulse import router

# 単引数（推奨）：自動的に 模塊名/hello → 実際のパス /my_module/hello
@router.get("/hello")
async def hello():
    return {"ok": True}

# 単引数 WebSocket：@ws("chat") → /my_module/chat
@router.ws("chat")
async def chat(ws):
    ...

# 二引数：明示的にモジュール名を指定（ルールは変わらず、モジュール間/ツールコードの登録時に使用）
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]
> 単引数の形態は、モジュール/アダプタの**ロードコンテキスト**内で登録する必要があります（ロード時にフレームワークが所属を注入）；
> 所属コンテキストがない場所で呼び出すと `ValueError` を投げ、明示的にモジュール名を渡すよう通知します。

### HTTP デコレータ

```python
from ErisPulse import router, HttpRequest

# 抽象型を明示的に指定することもできます
@router.post("/data")
async def post_data(request: HttpRequest):
    data = await request.json()
    return {"received": data}

@router.put("/data/{item_id}")
async def update_data(request):
    return {"updated": True}

@router.delete("/data/{item_id}")
async def delete_data(request):
    return {"deleted": True}
```

> **自動注入ルール**：ハンドラの最初の引数が `request` または `req` で、FastAPI 型の注釈がない場合、フレームワークは自動的に `HttpRequest` を注入します。引数がなく、またはリクエスト引数名でないハンドラには影響しません。

#### レスポンス戻り値の約束（2.10+）

ハンドラの戻り値は**タプルの約束**（推奨の書き方、明確にステータスコードを制御）をサポートし、dict/str/Response は従来通りです：

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (body, status_code) → 401 JSON
        return {"error": "unauthorized", "message": "token が無効です"}, 401
    # (body, status_code, headers) でレスポンスヘッダーも追加可能
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# または respond() ヘルパー関数の使用（message はレスポンスボディに自動的にマージされます）
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

パス/クエリパラメータは FastAPI のネイティブ注釈（`item_id: int`、`page: int = 1`）を使用します。
ミドルウェアは[ルーティングミドルウェア](#ルーティングミドルウェア)の節を参照してください。

### WebSocket デコレータ

```python
from ErisPulse import WebSocketConnection, WebSocketDisconnect

# 基本的な WebSocket（単引数の形態）
@router.ws("ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# ライフサイクルフック付きの WebSocket
@router.ws("/ws/chat")
async def chat(ws: WebSocketConnection):
    @ws.on_disconnect
    async def on_disconnect(ws, reason="unknown"):
        print(f"ユーザー切断: {reason}")

    @ws.on_error
    async def on_error(ws, error=""):
        print(f"接続エラー: {error}")

    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 認証付きの WebSocket
async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

@router.ws("secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **注意**：WebSocket ハンドラと認証ハンドラも自動注入をサポートします。引数の注釈なしでも `WebSocketConnection` を取得できます。`fastapi.WebSocket` を注釈してもネイティブオブジェクトを渡すことができますが、抽象型を使用することを推奨します。

### 接続の自動登録（接続プール、2.10+）

`@ws` / `@sse` で確立された接続は**デフォルトでフレームワークの接続プールに自動登録**されます（`track=False` でオフにできます）：
ハンドラ内では `ws.id` / `ws.join_group(...)` が使用でき、任意のモジュールは `connections.list(namespace=...)` を使用して本モジュールの接続を確認し、グループにブロードキャストできます。
[接続プールとブロードキャスト](connections.md)を参照してください。

## 伝統的な登録方法

```python
async def hello_handler(request):
    return {"message": "Hello World"}

# 基本的な登録
router.register_http_route(
    module_name="my_module",
    path="/hello",
    handler=hello_handler,
    methods=["GET"],
)

# レート制限とドキュメント情報付き
router.register_http_route(
    module_name="my_module",
    path="/api/data",
    handler=data_handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="データインターフェース",
    tags=["API"],
)
```

### WebSocket 登録

```python
from ErisPulse.Core import WebSocketConnection

async def websocket_handler(ws: WebSocketConnection):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 基本的な登録
router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# 認証付きの登録（推奨）
async def auth_handler(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)
```

**パラメータの説明：**

| パラメータ | 説明 | デフォルト値 |
|------|------|--------|
| `module_name` | モジュール名（必須） | - |
| `path` | WebSocket パス | - |
| `handler` | ハンドラ関数 | - |
| `auth_handler` | 認証関数、False を返すと自動的に接続を閉じる | `None` |
| `auto_accept` | 自動的に `accept()` するかどうか | `True` |

> **推奨**：`auth_handler` を使用して接続を確認するよう設定してください。`auto_accept=False` に設定するのは、接続フローを完全に制御する必要がある場合のみです。

## WebSocket ライフサイクルフック

`WebSocketConnection` は切断とエラーのコールバックを登録するためのメソッドを提供し、手動の try/catch は不要です：

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # デコレータ方式で登録
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"切断原因: {reason}")

    # 直接呼び出すこともできます
    async def on_err(ws, error=""):
        print(f"エラー: {error}")
    ws.on_error(on_err)

    # 通常のビジネスロジック
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```

## ルーティンググループ

```python
# プレフィックス付きのルーティンググループを作成
group = router.group("my_module", prefix="/v1")

@group.get("/users")
async def list_users(request):
    return {"users": []}

@group.post("/users")
async def create_user(request):
    return {"created": True}

# 実際のパス: /my_module/v1/users
```

## ルーティングミドルウェア

ミドルウェアは glob パターンマッチングによるパスをサポートします：

```python
@router.middleware("/my_module/*")
async def auth_middleware(request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        return {"error": "Unauthorized"}
    return await call_next(request)

@router.middleware("/my_module/admin/*")
async def admin_middleware(request, call_next):
    return await call_next(request)
```

## リクエスト関連ID（X-Request-ID）

2.7.0 以降、各 HTTP リクエストには `X-Request-ID` 関連IDが付与され、ログ/トレース連携に使用されます：

- **生成ルール**：まず、クライアントが送信した `X-Request-ID` リクエストヘッダーを優先して使用します（分散トレースの場面）；なければ、UUID を生成します
- **レスポンスヘッダー**：レスポンスに `X-Request-ID` を戻し、クライアントがリクエストとログを対応させるのを容易にします
- **ライフサイクルイベント**：`server.request` および `server.response` イベントのデータに `request_id` フィールドが追加されます

```python
# モジュール内でリクエストイベントをリッスンし、request_id でリクエスト-レスポンスを連動させる
@sdk.lifecycle.on("server.request")
async def on_request(data):
    print(f"[{data['request_id']}] {data['method']} {data['path']}")

@sdk.lifecycle.on("server.response")
async def on_response(data):
    print(f"[{data['request_id']}] -> {data['status_code']}")
```

クライアントはトレースに使用するため、ID をカスタマイズできます：

```bash
curl -H "X-Request-ID: my-trace-id" http://localhost:8080/my_module/health
```

## レート制限

ルーティングにスライディングウィンドウアルゴリズムを使用したリクエスト制限を適用します：

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

レート制限の形式は `{回数}/{時間ウィンドウ}` で、例えば `10/minute`、`100/hour` です。

## CORS 設定

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

`config.toml` で設定することもできます：

```toml
[router.cors]
allow_origins = ["https://example.com"]
allow_methods = ["GET", "POST"]
allow_headers = ["*"]
```

## セキュリティヘッダー

```python
router.setup_security_headers()
```

自動的に `X-Content-Type-Options`、`X-Frame-Options`、`X-XSS-Protection` などのセキュリティヘッダーを追加します。

`config.toml` で設定することもできます：

```toml
[router.security]
enabled = true
```

## 自動ドキュメント

Router はデフォルトで OpenAPI インタラクティブドキュメントを有効にします：

```python
# ドキュメントを無効化
router.disable_docs()

# ドキュメント情報をカスタマイズ
router.set_docs_info(
    title="My API",
    description="API ドキュメント",
    version="1.0.0"
)
```

## パス処理

ルーティングパスは自動的にモジュール名をプレフィックスとして追加し、衝突を回避します：

```python
# モジュール "my_module" にパス "/api" を登録
# 実際にアクセスするパスは "/my_module/api" になります
router.register_http_route("my_module", "/api", handler)
```

> [!WARNING]
> ルーティングパス（モジュール名プレフィックスを含む）は**大文字小文字を区別**します。登録時のモジュール名の大小文字が何であれ、実際のパスはその通りです：モジュール名が `Test` の場合、`/api` を登録した実際のパスは `/Test/api` になります。`/test/api` にアクセスすると 404 が返されます。

## システムルーティング

ルーティングマネージャーは以下のシステムルーティングを自動的に提供します：

### ヘルスチェック

```
GET /health
# 返却:
{"status": "ok", "service": "ErisPulse Router"}
```

### ホームページ

```
GET /
# 返却 ErisPulse ブランドページ
```

ルートルート `/` には ErisPulse ブランドページが表示され、ダッシュボードの可用性を自動的に検出し、エントリーボタンを追加します。

## ホームエントリ

ルーティングマネージャーは外部モジュールがルートルート `/` にショートカットエントリーボタンを登録できるようにし、ユーザーがモジュールの管理ページに素早くアクセスできるようにします。

### エントリの登録

```python
# 簡単な登録
router.register_home_entry(
    name="私のパネル",
    url="/mymodule/admin",
)

# イコン付きの登録（SVG）
router.register_home_entry(
    name="コンソール",
    url="/console",
    icon_svg='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>',
)

# 国際化をサポートする登録（i18n ディクショナリ形式）
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "私のパネル"},
    url="/mymodule/admin",
)
```

**パラメータの説明：**

| パラメータ | 型 | 説明 | 必須 |
|------|------|------|------|
| `name` | `str` / `dict` | ボタンの表示テキスト；`{"i18n": "key", "default": "テキスト"}` ディクショナリを渡すと国際化を使用 | はい |
| `url` | `str` | ボタンのリンクアドレス | はい |
| `icon_svg` | `str` | オプションの SVG イコンマーク | いいえ |

### ダッシュボードの自動登録

`sdk.Dashboard` が利用可能な場合、ルーティングマネージャーはダッシュボードのボタンをエントリーリストの先頭に自動的に追加し、手動登録は不要です。

## ライフサイクル統合

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("server.start")
async def on_server_start(event):
    print(f"サーバーが起動しました: {event['data']['base_url']}")

@lifecycle.on("server.stop")
async def on_server_stop(event):
    print("サーバーが停止しています...")
```

## ベストプラクティス

1. **抽象型を優先使用する**： `fastapi.Request` / `fastapi.WebSocket` の代わりに `HttpRequest` / `WebSocketConnection` を使用し、ハードな依存を避ける
2. **自動注入の活用**： ハンドラーの最初の引数を `request` または `req` と名付ければ、型アノテーションなしで `HttpRequest` を取得できる
3. **単一引数形式を優先**： モジュール読み込みコンテキストでは単一引数形式を優先する（自動的に名前空間に帰属）。モジュール間/ユーティリティコードでの登録時は明示的にモジュール名を渡す
4. **ルートグループの使用**： 同一モジュールの複数ルートは `group()` で整理する
5. **セキュリティへの配慮**： 機密性の高い操作には認証機構とセキュリティヘッダーを実装する
6. **適切なレート制限**： 高頻度で呼び出されるインターフェースにはレート制限を設定する
7. **ライフサイクルフックの使用**： `@ws.on_disconnect` / `@ws.on_error` で WebSocket の例外を処理し、手動の try/catch を避ける

## 関連ドキュメント

- [HTTP クライアント](http-client.md) - 内部 HTTP クライアントを使用してリクエストを送信
- [モジュール開発ガイド](../developer-guide/modules/getting-started.md) - モジュールルーティング登録について学ぶ
- [最適実践](../developer-guide/modules/best-practices.md) - ルーティングの使用に関する推奨事項
