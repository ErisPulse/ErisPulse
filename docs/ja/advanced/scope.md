# 統一制御面（scope）

> [!NOTE]
> 本機能は ErisPulse **2.8.0+** が必要です。

統一制御面は以下の6つの質問に答える：**どのモジュールが利用可能か、誰のイベントを受信するか、
誰が特定のコマンドを実行できるか、
特定のモジュールがどのようなテキストを処理するか、実装パラメータを上書きするか、
モジュールがどのような出力アクションを発行しないようにするか**。
制御権はすべてユーザーに委ねられ、モジュール / 适配器 / コマンド / ハンドラの登録の**上層**（設定
`ErisPulse.scope` または実行時 `sdk.scope`）で一括宣言され、イベントパイプラインは各段階で自動的に読み取り実行されます。

制御面は従来の複数の権限システムを統合し、2.8.0以降の権限/アクセス制御の**唯一**のエントリポイントです：

| 次元 | 制御対象 | 拒否動作 | 設定経路 |
|------|---------|---------|---------|
| **① モジュール** | 利用可能なモジュール（プラットフォーム / Bot / セッションの3段階） | 静かに無視（返信せず、認識しない） | `scope.platforms / bots / sessions` |
| **② 身元** | イベントの受信/拒否（適応器 / Bot / セッション / ユーザーの4段階） | 入口で完全に破棄（静かに） | `scope.identity.*` |
| **③ コマンド** | 特定のコマンドを誰が実行できるか（コマンド名は glob をサポート） | 「権限不足」の返信（明示的） | `scope.commands` |
| **④ ハンドラ** | 特定のモジュールのイベントハンドラがテキストでフィルタリングするか | トリガーしない（静かに） | `scope.handlers` |
| **⑤ オーバーライド** | モジュール/コマンドの実装パラメータの上書き（master/hidden/aliases/prefix） | ——（パラメータのみ変更） | `scope.overrides` |
| **⑥ 出力アクション** | モジュールが送信するメッセージ / 標準APIの呼び出し / リクエストの処理を禁止 | 失敗応答（`retcode=34601`） | `scope.actions` |

{!--< tips >!--}
1. `from ErisPulse.Core import scope` でシングルトンをインポート（`sdk.scope` は同じオブジェクト）
2. `scope.is_allowed(platform, bot_id, module, session_id)` でモジュールが利用可能か判定
3. `scope.is_identity_allowed(platform, bot_id, session_id, user_id)` でイベントが許可されるか判定
4. `scope.allow_user("roll*", platform, uid)` / `deny_user(...)` でコマンド ACL を設定（glob をサポート）
5. `scope.override("MyModule", "restart", master=True)` で実装パラメータを上書き
6. `scope.set_action("MyModule", "send", False)` でモジュールの返信/送信を禁止
7. `scope.get_stats()` でフィルタ統計を確認；`scope.get_topology()` でトポロジーを確認
{!--< /tips >!--}

## マッチング条目構文（全システム共通）

制御面のすべての「名前リスト」（モジュール名、身元キー、コマンド名）は同一のマッチング構文
（`ErisPulse.Core.text_match`）を使用します：

| 構文 | 例 | 説明 |
|------|------|------|
| 精確名 | `"Chat"` | 完全一致比較、**大文字小文字を区別しない** |
| glob | `"Tool*"`、`"spam_*"` | `*` 任意の文字列 / `?` 1文字 / `[seq]` 文字集合、大文字小文字を区別しない |
| 正規表現 | `"re:^Danger.*"` | `re:` 前置詞で宣言、正規表現 `search` で一致、デフォルトで大文字小文字を区別しない |

- 不正な正規表現は**静かに降格**して「一致しない」（エラーをスローせず、クラッシュしない）
- デコレータ引数（`pattern=` / `regex=`）は固定の意味：`pattern` は glob、`regex` は正規表現ソース
  （`re:` 前置詞なし）；制御面の設定内の正規表現項目は**必ず** `re:` 前置詞を付ける

## グローバルデフォルト：`default_allow`

`default_allow` は**グローバルで唯一**のデフォルトスイッチ（デフォルト `true`）で、
3つの判定次元に一括適用されます：

- **モジュール次元**：どのバインディングにも一致しない → `default_allow` で許可 / 拒否を決定
- **身元次元**：どの戦略にも一致しない → `default_allow` で許可 / 拒否を決定
- **コマンド次元**：ACL が設定されていない → `default_allow=true` は開発者のデフォルト権限チェーンに委ねる；
  `false`（厳密モード）は ACL が設定されていないコマンドは拒否

`false` に設定すると「暗黙の拒否」厳密モードが有効になり、**明示的に許可されていないものはすべて拒否**されます。

> **例外**：⑥ 出力アクション次元は `default_allow` の影響を受けません——これは独立した制限スイッチで、
> 既定ではすべて許可され、明示的に `false` に設定した場合のみ禁止（フレームワーク層の owner が空の呼び出しは常に許可）。
> このように厳密なグローバルモードは、すべてのモジュールのメッセージ返信を意図せず遮断することはありません。

## 設定ファイル

```toml
[ErisPulse.scope]
default_allow = true        # グローバルデフォルト（false = 暗黙の拒否厳密モード）
cache_size = 1024           # LRU キャッシュサイズ

# ── ① モジュール次元（優先度：セッション > Bot > プラットフォーム）──
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]   # ホワイトリスト：正確名 / glob / re: 正規表現
blocked = ["re:^Danger"]
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Chat"]
[ErisPulse.scope.sessions.onebot11."789012345"]
modules = ["Chat"]

# ── ② 身元次元（優先度：ユーザー > セッション > Bot > 適応器）──
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                   # 適応器全体のイベントを完全に破棄
[ErisPulse.scope.identity.bots.onebot11."123456"]
deny = true
[ErisPulse.scope.identity.sessions.onebot11."g_blocked"]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]           # ユーザー識別子は glob / re: 正規表現をサポート
deny = ["u_bad", "spam_*"]

# ── ③ コマンド次元（コマンド名は glob をサポート）──
[ErisPulse.scope.commands."roll*"]
allow = ["onebot11:u_vip"]    # ユーザー識別子 "platform:user_id"
deny = ["onebot11:u_bad"]

# ── ④ ハンドラ/テキスト次元 ──
[ErisPulse.scope.handlers.MyModule]
pattern = "签到*"             # コード内の pattern/regex 条件と AND
regex = "re:\\d+\\s*元"

# ── ⑤ 実装パラメータの上書き ──
[ErisPulse.scope.overrides.MyModule.restart]
master = true                 # フレームワークの所有者に限定
hidden = true                 # ヘルプで非表示
aliases = ["rs"]              # 別名を追加
prefix = "!"                  # トリガ前接を追加

# ── ⑥ 出力アクション次元（デフォルトはすべて許可、明示的に禁止する場合のみ制限）──
[ErisPulse.scope.actions.MyModule]
send = false                  # MyModule の返信/送信を禁止
api = false                   # MyModule の標準APIの呼び出しを禁止（call 逃げ口も含む）
request = false               # MyModule のリクエスト操作 accept/reject を禁止
```

## ① モジュール次元

「特定のコンテキストで、どのモジュールが利用可能か」を回答します。デフォルトではすべて開放；バインディングを設定した後からフィルタリングを開始し、
**モジュールと適応器は一切変更不要**です。

```mermaid
flowchart TD
    A["イベントがモジュールのハンドラ/コマンドに到達"] --> B{"scope.is_allowed<br/>(platform, bot, module, session)"}
    B --> C{"有効なバインディングを検索<br/>セッションレベル > Bot レベル > プラットフォームレベル"}
    C -->|"一致"| D["blocked に一致 → 拒否<br/>modules が空でない → ホワイトリストのみ許可<br/>どちらも空 → default_allow"]
    C -->|"一致しない"| E["default_allow（デフォルト true = 許可）"]
    D -->|"拒否"| Z["静かに無視<br/>（返信せず、認識せず、TRACE ログのみ表示）"]
```

- **優先度の解析：セッションレベル > Bot レベル > プラットフォームレベル**、高優先度のバインディングは低優先度を**全体的に上書き**します
- **静かの意味**：フィルタリングされたモジュールのコマンドとハンドラはトリガーされず、返信も認識されません（コマンド間の誤一致を防ぐため）、
  TRACE レベルのログのみ表示（`core.scope.denied`）
- **フレームワークレベルのハンドラ**（`scope_exempt=True` または owner が空）は影響を受けません；モジュール名が空（フレームワーク層のリソース）は常に許可されます

## ② 身元次元（イベントの入力）

「誰のイベントを受信するか」を回答します。拒否されたイベントは**入力の分岐点で完全に破棄**されます——
ミドルウェアやすべてのハンドラ（フレームワークレベルを含む）には到達せず、TRACE レベルのログのみ表示（`core.scope.identity_denied`）されます。

- **優先度の解析：ユーザー > セッション > Bot > 適応器**、最も具体的に設定された戦略を採用します；deny は allow より優先されます
- 各レベルのバインディングは二元戦略：`{ allow = true }` または `{ deny = true }`
- ユーザー識別子は glob / 正規表現をサポート（例：`"spam_*"` で一括的にスパムユーザーをブロック）
- 一般的な用途——上位レベルで deny し、個別に allow して「例外の許可」を行う：

```toml
[ErisPulse.scope.identity.adapters.onebot11]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]   # 適応器レベルで拒否しても、u_admin のイベントは許可されます
```

## ③ コマンド次元（コマンド ACL）

「誰が特定のコマンドを実行できるか」を回答します。判定順序：**deny に一致 → 拒否；allow ホワイトリストが空でないかつ一致しない → 拒否；いずれも設定されていない → `default_allow` に従う**（`true` は開発者のデフォルト権限チェーンに委ねる）。
拒否されたコマンドは「権限不足」の明示的な返信を返します。

- コマンド名は glob をサポート：`"roll*"` は `roll`、`roll_dice` などの一連のコマンドを1つのルールでカバー
- 精確なキーは glob キーに優先されます（`commands.roll` が一致した場合、`commands."roll*"` はチェックされません）
- ユーザー識別子のフォーマットは `"platform:user_id"`（フレームワークの所有者システムと一致）
- この次元は**ユーザー側の追加のゲート**であり、コマンドの `master` / `permission` パラメータと連動します：
  ACL が通過した後も、開発者が宣言したデフォルト権限チェーンを実行します（このデフォルトチェーンは ⑤ で上書き調整できます）

## ④ ハンドラ/テキスト次元

特定のモジュールで「どのようなテキストを処理するか」をフィルタリングします：モジュールに `pattern` / `regex` を設定した後、
そのモジュールのすべてのイベントハンドラはテキストが一致する場合にのみトリガーされます（コード内の条件と AND、両方を満たす必要があります）。
モジュールのコードを変更することなく、そのトリガー範囲を狭めることができます。

```toml
[ErisPulse.scope.handlers.ChatModule]
pattern = "闲聊*"     # ChatModule のハンドラは「闲聊*」で始まるメッセージにのみ反応
```

## ⑤ 実装パラメータの上書き

モジュール/コマンドの登録の**上層**で実装パラメータを上書きし、モジュールのコードを変更せずに：

```toml
[ErisPulse.scope.overrides.MyModule.restart]
master = true      # 既定の所有者制限を解除（false に設定して開放することも可能）
hidden = true      # ヘルプリストで非表示
aliases = ["rs"]   # 有効な別名
```

> 上書きは**ユーザー優先**に従います：開発者が宣言した `master` / `hidden` などの値はデフォルト値に過ぎず、
> ユーザーがここで明示的に設定した場合はユーザーの設定が優先されます（厳格化も開放も可能です）。
> 上書きは**実装パラメータ**（master / hidden / aliases / prefix / help / usage など）のみを変更します。
> **1つのコマンドを無効にする**ことはここでは行いません——統一してコマンド次元の deny（`scope.commands` または
> `scope.deny_user()`）で行い、2つの「無効」の意味が衝突しないようにします。

## ⑥ 出力アクション次元（モジュールの出力呼び出し禁止）

モジュールが**発行する出力アクション**を制約します：メッセージ送信 / 標準APIアクション / リクエスト操作。
3つのアクションはそれぞれの下層DSLに対応します：`Event.reply` と `Send`（send）、`Api` / `call_api`（api）、
`Request` の accept/reject（request）。イベントハンドラ実行中にモジュールが発行する出力呼び出しにはモジュールの所有者が含まれ、
この次元で一括判定されます。

```toml
[ErisPulse.scope.actions.MyModule]
send = false      # MyModule の返信/送信を禁止
api = false       # MyModule の標準APIアクションの呼び出しを禁止（call 逃げ口も含む）
request = false   # MyModule のリクエストイベントに対する accept/reject を禁止
```

判定の意味：**デフォルトはすべて許可**——未設定、または owner が空（フレームワーク層の内部呼び出し）はすべて許可；
ユーザーが明示的に `false` に設定した場合のみ拒否し、拒否された呼び出しはネットワークリクエストを開始せず、
代わりに標準の失敗応答（`retcode = 34601`、[api-response §5.3](../standards/api-response.md#53-フレームワーク拡張返却コード34xxx-プラットフォームエラー部の下3桁の独自定義) を参照）を返します。3つのアクションは互いに独立しており、1つだけ禁止することも可能です。

```python
# 実行時API
sdk.scope.set_action("MyModule", "send", False)   # メッセージ送信を禁止
sdk.scope.is_action_allowed("MyModule", "send")   # False
sdk.scope.unset_action("MyModule", "send")        # 許可を復元
sdk.scope.get_action_rules("MyModule")            # {"send": False, "api": True, "request": True}
```

## 実行時API

### モジュール次元

```python
from ErisPulse import sdk

# 判定
sdk.scope.is_allowed("onebot11", "123456", "Chat")
sdk.scope.is_allowed("onebot11", "123456", "Chat", "789012345")
sdk.scope.is_allowed("onebot11", "123456", None)      # フレームワーク層のリソース -> True

# バインディング / リリース
sdk.scope.bind_module("onebot11", "123456", modules=["Chat", "Tool*"])
sdk.scope.bind_module("onebot11", blocked=["Danger"])             # プラットフォームレベル
sdk.scope.bind_module("onebot11", "123456", "789012345", modules=["Chat"])  # セッションレベル
sdk.scope.bind_module("onebot11", "123456", modules=["Music"], merge=True)  # 合併
sdk.scope.bind_module("onebot11", "123456", modules=["Chat"], persist=False)  # 実行時のみ
sdk.scope.unbind_module("onebot11", "123456")

# 照会
sdk.scope.get("onebot11", "123456")   # {"modules": ["Chat"], "blocked": []}
```

### 身元次元

```python
# イベントの許可判定
sdk.scope.is_identity_allowed("onebot11", "123456", "group_9", "u1")

# 戦略のバインディング（階層はパラメータで決まる：user > session > bot > adapter）
sdk.scope.bind_identity("onebot11", user_id="u_bad", deny=True)
sdk.scope.bind_identity("onebot11", user_id="spam_*", deny=True)   # glob
sdk.scope.bind_identity("onebot11", "123456", "group_9", allow=True)
sdk.scope.unbind_identity("onebot11", user_id="u_bad")

# ユーザーブラックリストの便利なAPI
sdk.scope.block_user("onebot11", "u_bad")
sdk.scope.is_user_blocked("onebot11", "u_bad")
sdk.scope.get_blocked_users()        # {"onebot11": ["u_bad"]}
sdk.scope.unblock_user("onebot11", "u_bad")
```

### コマンド次元

```python
sdk.scope.is_command_allowed("roll", "onebot11", "u1")
sdk.scope.allow_user("roll*", "onebot11", "u_vip")   # コマンド名は glob をサポート
sdk.scope.deny_user("roll*", "onebot11", "u_bad")
sdk.scope.get_acl("roll*")
sdk.scope.remove_acl("roll*")

# コマンドシステムのファサード経由でも（同等の委任）
from ErisPulse.Core.Event import command
command.allow_user("restart", "onebot11", "123456")
```

### ハンドラとオーバーライド次元

```python
sdk.scope.bind_handler("MyModule", pattern="签到*", regex=r"\d+号")
sdk.scope.unbind_handler("MyModule")

sdk.scope.override("MyModule", "restart", master=True, hidden=True)
sdk.scope.get_override("MyModule", "restart")
sdk.scope.remove_override("MyModule", "restart")
```

### 一般

```python
sdk.scope.list_bindings()   # 全バインディング
sdk.scope.get_topology()    # トポロジー（ダッシュボード用）
sdk.scope.get_stats()
# {"module_calls": .., "module_filtered": .., "identity_checks": .., "identity_denied": ..,
#  "command_checks": .., "command_denied": .., "action_checks": .., "action_denied": ..,
#  "cache_hits": .., "cache_misses": ..}
sdk.scope.reset_stats()
sdk.scope.clear()           # 全バインディングをクリア（メモリ内のみ有効）
```

## 所有者とカスタム身元ソース（provider）

所有者システムは「誰がフレームワークの所有者か」を回答します：コマンドの `master=True` パラメータと業務層の
`master.is_master()` は同一の身元判定を使用し、判定チェーンは
**設定の所有者 → 実行時記録 → providerチェーン**です。

所有者設定（`ErisPulse.master.users`、グローバル list とプラットフォームごとの dict がサポート）は
[設定文書](../user-guide/configuration.md#所有者システムの設定)を参照してください；本節では身元判定APIと拡張ポイントに焦点を当てます。

### 判定と実行時の追加・削除

```python
from ErisPulse.Core import master

master.is_master(event)                      # イベントから判定
master.is_master("yunhu", "123")             # 明示的に判定
master.add("yunhu", "123")                   # 実行時に追加（デフォルトは永続化；persist=False はメモリ内のみ）
master.remove("yunhu", "123")                # 削除（デフォルトは永続化）
master.list()                                # 総合：{"global": [...], "<platform>": [...]}
```

### カスタム身元ソース（provider）

設定に加えて、カスタム身元ソースも登録できます：`fn(platform, user_id) -> bool`、
ビルトイン身元ソース（設定 + 実行時記録）が一致しない場合、順次試され、いずれかの provider が許可すれば所有者と判定されます。
適応器管理者インターフェース、データベースロールなどの外部身元体系に接続するのに適しています。

登録エントリ `master.provider` はデコレータ / 関数式の2種類の書き方ができ、
登録解除は登録された関数の `fn.unregister()` を通じて行います：

```python
from ErisPulse.Core import master

# 書き方1：デコレータ（常駐身元ソース、推奨）
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # 自作の判定ロジック

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # 不要になったら登録解除

# 書き方2：関数式（モジュールロード時に登録 / アンロード時に登録解除）
fn = master.provider(admin_provider)
fn.unregister()
```

> provider での例外はキャッチされ、判定チェーンをブロックしません。
> インスタンスメソッドを登録する場合は `unregister` が付与されないため、登録/解除のペアが必要な場合は**モジュールレベルの関数**を使用してください。

### ユーザー優先：所有者の適用範囲はユーザーが最終的に決定

コマンドの `master=True` は**開発者のデフォルト**に過ぎません：ユーザーは制御面
`ErisPulse.scope.overrides.<module>.<cmd>.master = true/false`
で絞り込みや解放を上書きできます（上記の ⑤ 実装パラメータの上書きを参照、ユーザーが明示的に設定すれば即座に有効）。

## キャッシュとホットアップデート

- `is_allowed` / `is_identity_allowed` の結果は **LRU キャッシュ**（`scope.cache_size` で調整可能）付きで、
  `bind_*` / `unbind_*` / 設定のホットアップデート（`config.updated` / `config.set`）で自動的に無効になります
- すべての次元の設定は**即座に有効**され、再起動は不要
- 制御面は「イベントごとに」判定されるため、イベント間で状態を保持しません：設定が変わると、次のイベントは新しいルールに従います

## 一般的な問題と注意事項

### 1. 設定の階層と上書き

- モジュール次元：セッションレベル > Bot レベル > プラットフォームレベル、**全体を上書き**します。例：プラットフォームで Chat を許可し、Bot で Music を追加したい場合、Bot レベルで両方をリストアップする必要があります
- 身元次元：ユーザー > セッション > Bot > 適応器、**最も具体的に設定された**戦略を採用します（例外の許可が可能です）
- コマンド次元：正確なコマンド名が glob キーに優先されます

### 2. モジュールコードの変更ではなく、制御面の使用を優先

モジュールで宣言したのは「開発者のデフォルト」（`master=True`、`permission=...`、`pattern=...`）；
制御面で宣言したのは「ユーザーの最終決定」。実装パラメータの上書きは**ユーザー優先**に従います：
ユーザーが明示的に `master = true/false` を設定すると即座に有効になります（絞り込みも解放も可能です）。
開発者が設定していない制限はユーザーが独自に絞り込むことができます。禁止/許可の制御はコマンド deny / 身元 allow で行います。

### 3. モジュール/コマンドが反応しない

まず制御面が原因かどうかを疑うべきです：

```python
from ErisPulse import sdk

print(sdk.scope.is_allowed(event.get_platform(), bot_id, "MyModule", session_id))
print(sdk.scope.is_identity_allowed(event.get_platform(), bot_id, session_id, user_id))
print(sdk.scope.get_stats())   # module_filtered / identity_denied > 0 なら静かにフィルタリングされている
```

フィルタリングは**静か**です（モジュール次元と身元次元は返信せず、誤ったコマンドの一致を防ぐため）、
ただし統計はカウントされます；コマンド次元で ACL に拒否された場合は「権限不足」の明示的な返信がされます。

### 4. セッション識別子はプラットフォームごとに隔離

`(platform, session_id)` の組み合わせが唯一の識別子です。`scope.sessions.onebot11."789"`
は onebot11 でのみ作用し、telegram 上で同様の `789` のセッションには影響しません。身元次元のユーザー識別子も同様です。

## トポロジツリーAPI

`ModuleManager.get_topology()` と `AdapterManager.get_topology()` はモジュール/適応器の所属関係データを提供し、
`sdk.get_topology()` は制御面の5次元を含む一括集約を提供します：

```python
from ErisPulse import sdk

topology = sdk.get_topology()
# {
#   "modules": {                                   # モジュール → 持つリソース
#     "Chat": {
#       "loaded": True, "enabled": True,
#       "commands": ["chat", "translate"],
#       "handlers": {"message": 2, "notice": 1},
#       "routes": {"http": ["/Chat/api"], "ws": [], "sse": []},
#       "lifecycle_hooks": 3,
#     }
#   },
#   "adapters": {                                  # 適応器 → Bot → スコープ
#     "onebot11": {
#       "status": "started", "enabled": True,
#       "bots": {"123456": {"status": "online", "scope": {...}}},
#       "scope": {"modules": [...], "blocked": [...]},
#     }
#   },
#   "scope": {                                     # 統一制御面（5次元）
#     "platforms": {...}, "bots": {...}, "sessions": {...},
#     "identity": {"adapters": {...}, "bots": {...}, "sessions": {...}, "users": {...}},
#     "commands": {...}, "handlers": {...}, "overrides": {...},
#   },
# }
```

- モジュールのトポロジーは、登録されたコマンド、イベントハンドラ、HTTP/WS/SSEルート、ライフサイクルフックを統合し、
  モジュールリソースツリーを描くのに便利です。
- 適応器のトポロジーは、各適応器のステータス、所属するBotのステータス、プラットフォームレベル/Botレベルのスコープバインディングを統合します。