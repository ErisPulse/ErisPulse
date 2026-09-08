# モジュール間通信

> [!NOTE]
> 本章の内容は ErisPulse **2.8.0+** が必要です。

ErisPulse のモジュール間には**3層の通信モデル**があり、「点対点 → 定向 → ブロードキャスト」の順序で配置されています：

| 層 | API | 意味 | 代表的な場面 |
|---|---|---|---|
| **RPC** | `await sdk.module.call("Chat", "get_history", ...)` | 点対点のリクエスト-レスポンス、契約 / 審計 / タイムアウト付き | 他のモジュールの機能を呼び出す（履歴の取得、翻訳、返金など） |
| **定向イベント** | `await sdk.module.emit_to("Chat", "message_received", {...})` | 指定されたモジュールに送信される通知 | 上流の状態変化を下流に通知する（「新しいメッセージを受け取りました」など） |
| **ブロードキャスト** | `await lifecycle.emit("config.updated", {...})` | フレームワーク全体で見えるライフサイクルイベント | 設定のホットアップデート、モジュールの起動 / 停止 |

{!--< tips >!--}
選択の口訣：**戻り値が必要な場合は `call` を使い、1つのモジュールに通知したい場合は `emit_to` を使い、全員に通知したい場合は `lifecycle` を使う**。
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

## 定向イベント：emit_to

```python
# 投递元：対象モジュールが有効化されたことを確認した後、イベントは module.<名前>.<イベント> の名前空間に送信されます
await sdk.module.emit_to("Chat", "message_received", {"text": "hi", "from": "u1"})

# 訂正元（Chat モジュール内）：名前空間に従ってフックを登録します
from ErisPulse.Core.lifecycle import lifecycle

@lifecycle.on("module.Chat.message_received")
async def on_message_received(data): ...

@lifecycle.on("module.Chat")          # または、このモジュールのすべての定向イベントを受け取ります
async def on_any(data): ...
```

意味の詳細：

- 対象が登録されていない / 有効化されていない場合 → `ModuleNotAvailableError`（**存在しない場所には送信されません**）
- 対象が遅延ロードモジュールの場合 → **まず起動してから投递します**（定向イベントはアクティベーションの源であり、`activate_on` の意味と一致します）
- `data` が dict の場合、自動的に `_trace_id` を付加します（既存の値は上書きされません）、全トラッキング連携が可能です

## 懒惰ロードと呼び出し

`module.call()` および `emit_to()` は、**遅延ロードモジュールに対して透明な起動**を提供します：

- イベント駆動型遅延モジュール（`activate_on` で宣言）→ 活性化ロック `_activate()` を通る。活性化後、トリガースタブは自動的に登録解除される。
- 通常の遅延モジュール → 同期初期化または通常のロード経路（冪等性）
- 起動失敗 → `ModuleNotAvailableError`（`call`）/ 活性化失敗（`emit_to`）

つまり、**呼び出し元は、対象モジュールが既にロードされているかどうかを気にする必要がなく、また、特定のイベントを待つ必要もない**。

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