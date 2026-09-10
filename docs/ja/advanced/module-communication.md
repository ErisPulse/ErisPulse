# モジュール間通信

> [!NOTE]
> 本章の内容は ErisPulse **2.8.0+** が必要です。

ErisPulse のモジュール間には**3つの通信モデル**があり、"点対点 → 定向 → ブロードキャスト"の順序で配置されています：

| 層 | API | 語義 | 典型的な場面 |
|---|---|---|---|
| **RPC** | `await sdk.module.call("Chat", "get_history", ...)` | 点対点のリクエスト-レスポンス、契約 / 審計 / タイムアウト付き | 他のモジュールの機能を呼び出す（履歴の取得、翻訳、返金など） |
| **定向イベント** | `await lifecycle.emit("message_received", {...}, to="Chat")` | 指定されたモジュールが登録したライフサイクルフックにのみ配信 | 上流の状態変化を下流に通知する（"新しいメッセージを受け取りました"） |
| **ブロードキャスト** | `await lifecycle.emit("config.updated", {...})` | フレームワーク全体で見えるライフサイクルイベント | 設定のホット更新、モジュールの起動・停止 |

{!--< tips >!--}
選択の口訣：**返り値が必要な場合は `call` を使い、特定のモジュールのフックに通知する場合は `emit(..., to=...)` を使い、全員に通知する場合は `emit(...)` を使う**。
{!--< /tips >!--}

## RPC：module.call

```python
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

裸属性访问 `sdk.module.Chat.get_history(...)`（保持不变）与 `module.call()` 的差异：

| | `module.call()` | 裸属性アクセス |
|---|---|---|
| 目標が登録されていない / 有効化されていない | `ModuleNotAvailableError` をスロー | `AttributeError` をスロー |
| ラグジュアリーなモジュール | **自動的に起動**（イベント駆動モジュールはアクティベーションロックを経由） | 非同期初期化モジュールが `RuntimeError` をスロー |
| `current_owner` | **対象モジュール**に帰属（内部の `wait_reply` / 送信 / ログは正しく所有者に属する） | 呼び出し元のまま |
| タイムアウト | デフォルト 30 秒（`timeout=` で上書き、`None` で無制限） | なし |
| scope 審査 | 呼び出し元の出力ゲート `actions.<呼び出し元>.call` | なし |
| 契約検証 | `meta.services` のホワイトリスト | なし |

### 例外体系

```
ModuleError                      # モジュールシステムの例外基底クラス
└── ModuleCallError              # モジュール間呼び出しの基底クラス（module / method 属性を含む）
    ├── ModuleNotAvailableError  # 目標が登録されていない / 有効化されていない / 起動に失敗
    ├── ServiceNotProvidedError  # メソッドが services ホワイトリストにない / 私有メソッド / 存在しない
    └── ModuleCallTimeoutError   # コルーチンメソッドのタイムアウト
```

すべて `ErisPulseError` 体系に属し、`from ErisPulse.Core import ModuleCallError` でキャッチ可能です。

## サービス契約：meta.services

サービス提供者は `get_meta()` で公開する白リストを宣言します（`commands` フィールドと対称）：

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
    def _internal_helper(self): ...   # アンダースコア付きメソッドは外部からの呼び出しを常に禁止
```

**開発者にとっては無視されるのがデフォルト**：

- `services` を宣言していない場合 → すべての**公開**メソッドは `module.call()` で呼び出せる（属性アクセスと同様に、宣言不要）
- 宣言した場合 → 白リストに絞られ、範囲外の呼び出しは `ServiceNotProvidedError` を送出する——「これらが外部に約束されたメソッド」を明示するため
- 制限の**主なコントロール権はユーザー側**にある：`scope.actions` 設定が「誰が誰を呼び出せるか」を決定する（下記の監査を参照），
  モジュール作者の `services` はサービス面の宣言に過ぎず、2つの層は互いに代替できない

**サービスの説明**：各サービスに人間やAIが読める説明をつける——不要なら何も書かなくてもよい。
説明は自動的に**メソッドの docstring の最初の行**を取る（フレームワークは docstring 形式を要求している）：

```python
async def translate(self, text, target_lang):
    """テキストを指定された言語に翻訳する"""    # ← この行が自動的にサービスの説明になる
    ...
```

docstring に上書きしたい、または多言語に対応したいなどの細かい制御が必要な場合は、dict 形式で description を宣言する（i18n 辞書に対応）：

```python
services=[
    {"name": "translate", "description": "テキストを指定された言語に翻訳する"},
    {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "会話の要約"}},
]
```

## サービスディレクトリ: services()

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': 'テキストを指定された言語に翻訳する'}]}

sdk.module.services("Chat")   # 指定されたモジュールのみを照会
```

- `meta.services` が**明示的に宣言**されたモジュールのみをリストアップ（宣言されていないモジュールはディレクトリに表示されない）
- 各サービスにはメソッドの署名文字列（`inspect.signature` から抽出）と説明文が付属
- トポロジーにも対応：`sdk.module.get_topology()` の各モジュール項目には `services` フィールドが含まれる

{!--< tips >!--}
**MCP 化の道筋**：サービスディレクトリ（名前 + 署名 + 説明）は、MCP ツールの構造に自然に適合する——
各サービスは天然に ``{"name", "description", "parameters"}`` の形をとる。
将来、フレームワークは ``services()`` を直接 MCP サーバーエンドポイントとして公開し、AI がモジュールの機能を発見して呼び出すことが可能になる。
また、``scope.actions.call`` の監査は、AI 呼び出しのセキュリティゲートとして自然に機能する。
{!--< /tips >!--}

## 出向監査：誰が誰を呼び出すか

`module.call()` のたびに、**呼び出し元モジュール**の身分としてスコープの出向ゲートを通過します：

```toml
[ErisPulse.scope.actions.CallerModule.call]
deny = ["Chat.get_history"]        # CallerModule が Chat の get_history を呼び出すことを禁止
# allow = ["Chat.get_*"]           # またはホワイトリスト：get で始まる Chat のサービスのみを許可
```

- `name` の形式は `<対象モジュール>.<メソッド名>` で、正確な一致、ワイルドカード、`re:` 正規表現がサポートされています
- フレームワーク層の呼び出し（owner コンテキストがない、起動スクリプトなど）は監査制約の対象外です
- 拒否された呼び出しは `ModuleCallError` を送出します（TRACE ログ `core.module.call_denied`）

設定方法は [スコープ（scope）](docs/ja/scope.md) の出向の観点を参照してください。

## 定向イベント: lifecycle.emit の to パラメータ

ライフサイクルイベントは、`to` パラメータで送信先の所有者（owner）を指定することで、特定のオーナーにイベントを送信できます。この場合、イベントはそのオーナーとして登録されたフック（モジュールが `on_load` 内で登録するフックは自動的に自身のモジュールに属します）にのみ配信され、他のモジュールやワイルドカード `*` のハンドラはイベントを感知しません。

```python
from ErisPulse.Core.lifecycle import lifecycle

# 送信側：イベントは Chat モジュールが登録したフックにのみ送信されます
await lifecycle.emit("message_received", {"text": "hi", "from": "u1"}, to="Chat")

# 受信側（Chat モジュール内）：同名のフックを登録し、owner は登録時に自動的に記録されます
@lifecycle.on("message_received")
async def on_message_received(data): ...

@lifecycle.on("message")          # 点式の親プレフィックスも同様に有効（owner でフィルタリング）
async def on_any(data): ...
```

動作の詳細：

- 指定されたオーナーに登録されたフックがない場合 → イベントは**静かに破棄**されます（**存在しない場所に送信されません**）。  
  事前に `lifecycle.has_handlers("message_received")` を使用して存在を確認できます。
- `data` が dict の場合、自動的に `_trace_id` を追加します（既存の値は上書きされません）。これにより、全トラッキングフローと連携できます。
- ブロードキャストと定向は、同じフック登録システムを使用します：`emit(...)` に `to=` を指定しない場合、イベントはフレームワーク全体にブロードキャストされます。`to=` を指定すると、同一イベントは対象モジュールのみに表示されます。
- `emit_sync` / `submit_event`（互換 API）も `to=` パラメータをサポートします。

> [!NOTE]  
> 定向イベントは軽量な通知であり、**送信先の存在確認や遅延起動は行いません**。送信先の存在確認、契約の監査、または戻り値が必要な場合は、[RPC: module.call](#rpcmodulecall) を使用してください。

## 慢的ロードと呼び出し

`module.call()` は、**遅延ロードモジュールに対して透明な起動**を提供します：

- イベント駆動の遅延モジュール（`activate_on` で宣言）→ 活性化ロック `_activate()` を通ります。活性化後、トリガースタブは自動的に登録解除されます。
- 通常の遅延モジュール → 同期初期化または通常のロード経路（冪等性）
- 起動失敗 → `ModuleNotAvailableError`

つまり、**呼び出し元は対象モジュールが既にロードされているかどうかを気にする必要がなく、またその起動のために特定のイベントを待つ必要もありません。**

対象イベント（`lifecycle.emit(..., to=...)`）は遅延起動を行いません。対象がロードされていない場合、フックは存在せず、イベントは静かに破棄されます。確実に送信する必要がある場合は、`module.call()` を使用してください。

## クールスタートリプレイ

新規インストール / 再起動のモジュールが一部のチャットを逃した場合、`get_load_strategy(replay=...)` により、フレームワークはモジュールが準備完了した後に、セッション受信箱内の最近のメッセージを**そのモジュール自身にリプレイ**します。

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyAIModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=100,
            replay="5m",        # 最近の 5 分間をリプレイ ("1h" / "300" 秒の書き方も可能です)
        )

    async def on_load(self, event):
        @message.on_message()
        async def handle(e):
            if e.get("replayed"):
                # 合成イベント: コンテキストのみ補完、送信などの副作用は発生しない
                ...
```

意味の詳細:

- データソースは[セッション受信箱](interaction.md#会話受信箱eventhistory) (`sdk.transcript.recent()`) です。
  モジュールの読み込み完了後にバックグラウンドで実行され、起動をブロックしません。
- 合成イベントには `replayed: True` のフラグと、`platform / detail_type / user_id / alt_message` が完全に含まれており、**本モジュールのハンドラにのみ配信されます**。他のモジュールはリプレイの影響を受けません。
- 受信箱が有効でない / 記録がない / 時間長の宣言が不正な場合 (`replay_invalid` 警告) は、静かにスキップされます。

## イベントの冪等性と重複除去

プラットフォームの WebSocket 再接続後に、同じイベント（同じ `event["id"]`）が頻繁に再送されることがあります。イベントの配信エントリポイントでは、ID に基づいて LRU 重複除去（容量 4096）が行われ、同じ ID のイベントは一度だけ配信されます。

```toml
[ErisPulse.framework]
event_dedupe = true   # デフォルトで有効。テスト環境では固定 ID で合成イベントを作成する場合は無効にできます。
```

アダプタが**登録**（新しい接続のライフサイクルの起点）される際に、自動的に重複除去キャッシュがリセットされます。

## 関連ドキュメント

- [インタラクティブセッションシステム](interaction.md) - wait_reply / タイマ / マルチウェイト / セッションの排他制御
- [スコープ（scope）](scope.md) - 出力次元監査の完全な設定
- [所有権（owner）システム](ownership.md) - owner コンテキストがモジュール間呼び出しをどのように貫くか
- [ラジロードシステム](lazy-loading.md) - ラジロードとイベント駆動ラジアクティベーション（activate_on）
- [ライフサイクル管理](lifecycle.md) - ブロードキャスト層イベントバスのメカニズム