# スコープ（scope）

> [!NOTE]  
> この機能は ErisPulse **2.8.0+** が必要です。

スコープは以下の4つの質問に答えます：**どのモジュールが利用可能か、誰のイベントを受け取るか、特定のモジュールがどのようなテキストを処理するか、モジュールが外部に対してどのような操作ができるか**。  
権限はすべてユーザーに委ねられます。モジュール／アダプタ／プロセッサ／出力呼び出しの登録の**上位**（設定 `ErisPulse.scope` または実行時 `sdk.scope`）で一括して宣言し、イベントパイプラインはエントリ、プロセッサフィルタ、出力ゲートで自動的に読み取り実行します。

| 維度 | 控制対象 | 拒否動作 | 設定パス |
|------|---------|---------|---------|
| **① モジュール** | 利用可能なモジュール（プラットフォーム／Bot／セッションの3段階） | 静かに無視（返信せず、対象外） | `scope.platforms / bots / sessions` |
| **② 身分** | イベントの受信対象（アダプタ／Bot／セッション／ユーザーの4段階） | エントリで完全に破棄（静かに） | `scope.identity.*` |
| **③ 出力** | モジュールがどのような出力呼び出し（メッセージ／API／リクエスト、メソッドレベルのホワイト／ブラックリスト）を実行できるか | 失敗応答（`retcode=34601`） | `scope.actions` |

> **関連システム**：コマンドは特別なメッセージイベントプロセッサであり、そのユーザーのホワイト／ブラックリスト（ACL）と実装パラメータの上書きはコマンドシステムが独自に管理します（`ErisPulse.event.command`）。  
> [イベント処理の入門](../getting-started/event-handling.md) および [設定ガイド](../user-guide/configuration.md) を参照してください。

{!--< tips >!--}
1. `from ErisPulse.Core import scope` をインポートしてシングルトンを使用（`sdk.scope` は同じオブジェクト）
2. 判定：`scope.is_allowed(...)` / `scope.is_identity_allowed(...)` / `scope.is_action_allowed(...)` はそれぞれ ①②③ の3つのゲートに対応
3. 読み書き：次元化されたパラメータメソッド（IDEで補完可能）——  
   `scope.set_module(...)` / `scope.set_identity(...)` / `scope.set_action(...)`；  
   また、辞書形式のバックアップメソッドとして `scope.get(path)` / `scope.set(path, v)` / `scope.delete(path)` もあります
4. イベントプロセッサのテキスト条件の上書きは  
   [イベント処理の入門 · イベント上書き](../getting-started/event-handling.md#イベント覆写不改模块代码覆写任意事件类型的行为) を参照してください；  
   コマンドのACL / パラメータの上書きは [イベント処理の入門](../getting-started/event-handling.md) を参照してください
{!--< /tips >!--}

## マッチングエントリの構文（全システムで一貫）

スコープ内のすべての「名前のリスト」（モジュール名、アイデンティティキー、出力エントリ）は、同一のマッチング構文（`ErisPulse.Core.text_match`）を使用します。

| 構文 | 例 | 説明 |
|------|------|------|
| 精確名 | `"Chat"` | 完全一致、**大文字小文字を区別しない** |
| glob | `"Tool*"`、`"spam_*"` | `*` 任意の文字列 / `?` 1文字 / `[seq]` 文字集合、大文字小文字を区別しない |
| 正規表現 | `"re:^Danger.*"` | `re:` で始まるプレフィックスを宣言、正規表現 `search` によるマッチ、デフォルトで大文字小文字を区別しない |

- 不正な正規表現は**静かにマッチしないものとして扱われる**（エラーは発生せず、クラッシュもしない）
- デコレータ引数（`pattern=` / `regex=`）は固定された意味を持つ：`pattern` は glob、`regex` は正規表現のソースコード（`re:` プレフィックスなし）；スコープ設定内の正規表現エントリには**必ず** `re:` プレフィックスを付ける必要がある

## グローバルデフォルト：`default_allow`

`default_allow` は**グローバルで唯一**のデフォルトスイッチ（デフォルト値は `true`）で、
2つの判定の次元に統一的に効果を及ぼします：

- **モジュール次元**：どのバインディングにもマッチしない場合 → `default_allow` が許可 / 拒否を決定します。
- **アイデンティティ次元**：どのポリシーにもマッチしない場合 → `default_allow` が許可 / 拒否を決定します。

`false` に設定すると「暗黙の拒否」の厳密モードが有効になります。つまり、ホワイトリスト方式での管理となり、
**明示的に許可されていないものはすべて拒否**されます。

> **例外**：③ 出力次元は `default_allow` の影響を受けません。これは独立した制限スイッチであり、
> デフォルトではすべて許可され、明示的なルールによってのみ制限されます（フレームワーク層の `owner` が空の呼び出しは常に許可されます）。
> これにより、厳密なグローバルモードでも、すべてのモジュールのメッセージ返信が意図せず切断されることはありません。
> コマンド ACL には独立した `ErisPulse.event.command.default_allow` デフォルトスイッチがあり、互いに影響しません。

## 設定ファイル

```toml
[ErisPulse.scope]
default_allow = true        # グローバルなデフォルト（false = 厳密モードで暗黙的に拒否）
cache_size = 1024           # LRU キャッシュのサイズ

# ── ① モジュール次元（優先度：セッション > Bot > プラットフォーム）──
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]   # ホワイトリスト：正確な名前 / glob / re: 正規表現
blocked = ["re:^Danger"]
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Chat"]
merge = true                  # プラットフォームレベルのバインドに追加（デフォルトでは全体を上書き）
[ErisPulse.scope.sessions.onebot11."789012345"]
modules = ["Chat"]

# ── ② 身元次元（優先度：ユーザー > セッション > Bot > アダプター）──
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                   # アダプターのイベントをすべて破棄
[ErisPulse.scope.identity.bots.onebot11."123456"]
deny = true
[ErisPulse.scope.identity.sessions.onebot11."g_blocked"]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]           # ユーザーのキーには glob / re: 正規表現が使用可能
deny = ["u_bad", "spam_*"]

# ── ③ 出力次元（デフォルトでは全許可、明示的に制限する場合のみ禁止）──
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                                    # 送信を完全に禁止
api = { allow = ["get_*"] }                               # クエリ系の標準APIのみ許可
request = { deny = true }                                 # リクエスト処理を禁止
```

## ① モジュール次元

あるコンテキストの中で、どのモジュールが利用可能かを回答します。デフォルトではすべて開放されており、設定がバインドされた後にフィルタリングが始まります。**モジュールとアダプタは一切変更する必要がありません。**

```mermaid
flowchart TD
    A["イベントが特定モジュールのハンドラ/コマンドに到達"] --> B{"scope.is_allowed<br/>(platform, bot, module, session)"}
    B --> C{"解析の優先順位：セッションレベル > Bot レベル > プラットフォームレベル<br/>（子レベルで merge = true の場合、各レベルで逐次合併）"}
    C -->|"一致する"| D["blocked が一致 → 拒否<br/>modules が空でない → 仅白名单が許可<br/>両方空 → default_allow"]
    C -->|"一致しない"| E["default_allow（デフォルトは true = 許可）"]
    D -->|"拒否"| Z["静かに無視<br/>（返信、認証なし、TRACE ログのみ）"]
```

- **解析の優先順位：セッションレベル > Bot レベル > プラットフォームレベル**。高優先順位のバインドは低優先順位を**全体的に上書き**します。  
  子レベルで `merge = true` を指定した場合、低優先順位との**各項目の合併**（modules / blocked それぞれ独立に合併）になります。`merge` 自体は制御キーであり、項目としてはカウントされません。
- **静かに無視の意味**：フィルタリングされたモジュールのコマンドやハンドラはトリガーされず、返信や認証も行わず、誤ったコマンド間のマッチングを防ぎます。`core.scope.denied` での TRACE レベルのログのみが表示されます。
- **フレームワークレベルのハンドラ**（`scope_exempt=True` または owner が空）は影響を受けません。モジュール名が空（フレームワーク層のリソース）の場合は常に許可されます。
- **セッション感知のヘルプとコマンド照会**：コマンド照会 API（`command.help` / `get_command` / `get_commands` / `get_group_commands` / `get_visible_commands`、および `module.get_commands_overview`）は、オプションの `event=` または明示的な `platform=` / `bot_id=` / `session_id=` キーワードをサポートしています。現在のセッションで利用できないモジュールのコマンドは、結果に表示されなくなります（`get_command` は None を返し、単一コマンドのヘルプは「未登録」として扱われ、静かに無視の意味と一致します）。コンテキストを渡さない場合は、全量の動作を維持します。

### バインドの継承（merge）

デフォルトの上書きは明確で予測可能です。上位レベルの設定に**追加**したい場合は、子レベルで `merge = true` を指定します：

```toml
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool"]      # プラットフォームレベル：Chat、Tool のみ許可

[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true                    # この Bot で実際の有効な設定 = ["Chat", "Tool", "Music"]
```

- 合併のルール：`modules` と `blocked` は**独立に合併**されます。バインド内では `blocked` が `modules` よりも優先されます。
- チェーンの合併：プラットフォーム → Bot → セッションの順に各レベルで独立して `merge` または上書きを決定します。

## ② 身元次元（イベントの受入）

「誰のイベントを受け入れるか」を回答します。拒否されたイベントは**配信の入口で完全に破棄され**、ミドルウェアや任意のハンドラ（フレームワークレベルを含む）には一切渡りません。TRACE レベルのログでのみ確認可能（`core.scope.identity_denied`）です。

- **解析優先度：ユーザー > 会話 > Bot > アダプタ**。最も具体的に設定された戦略を優先します。`deny` は `allow` より優先されます。
- 各階層のバインディングは二元的な戦略です：`{ allow = true }` または `{ deny = true }`
- ユーザーのキーは glob / 正規表現をサポートしています（例：`"spam_*"` で一括してスパムユーザーをブロック）
- 一般的な用途として、上位階層で `deny` し、個別に `allow` することで「例外的に許可」を実現します：

```toml
[ErisPulse.scope.identity.adapters.onebot11]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]   # アダプタレベルで拒否されても、u_admin のイベントは許可されます
```

## ③ 出站次元（制限モジュールが発信する呼び出し）

モジュールが**発信する出力アクション**を制限：メッセージ送信 / 標準 API 動作 / 要求操作。  
3つのアクションはそれぞれ下層の DSL に対応：`Event.reply` と `Send`（send）、`Api` / `call_api`（api）、  
`Request` の accept/reject（request）。イベントハンドラ実行中にモジュールが発信する出力呼び出しは  
モジュールの所有者（owner）を含み、本次元が一括して判定します。

### 規則の形式（インライン表）

各アクションの規則はインライン表で表されます：`{ allow = [...], deny = true|[...] }`。  
同一アクションには1つの規則しか設定できません（TOML のキーは重複不可、全禁止と細粒度の2択）：

```toml
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                                  # 全ての送信を禁止（Event.reply / Send DSL）
# またはメソッドレベルの細粒度設定：send = { allow = ["Text", "Image*"], deny = ["File"] }
api = { allow = ["get_*"] }                             # クエリ系の標準 API 動作のみ許可
# またはアクションレベルのブラックリスト：api = { deny = ["set_*", "leave_*"] }
request = { deny = true }                               # 要求の accept/reject を禁止
```

- `send` の項目は**送信メソッド名**（`Text` / `Image` / `File` ...）に一致します。  
- `api` の項目は**標準アクション名**（`get_group_info` / `set_group_name` ...）に一致します。  
- 項目は正確な名前 / glob / `re:` 正規表現（全システムと統一された構文で、大文字小文字は区別しません）。  
- `allow` に1つの文字列を記述することは、1つの項目のリストと等価です：`send = { allow = "Text" }`。

### 判定の意味

**デフォルトはすべて許可**——設定がなければ、または owner が空（フレームワーク層の内部呼び出し）の場合はすべて許可されます。  
設定規則がある場合は、以下の順序で判定されます：

1. `deny = true` → 拒否  
2. `deny` リストに呼び出し名が一致 → 拒否  
3. `allow` リストが空でないかつ呼び出し名が一致しない（または呼び出しに名前がない）→ 拒否  
4. それ以外は許可

拒否された呼び出しはネットワークリクエストを一切行わず、標準の失敗レスポンスを返します  
（`retcode = 34601`、[api-response §5.3](../standards/api-response.md#53-フレームワーク拡張返却コード34xxx-プラットフォームエラーセグメントの下3桁のカスタマイズ)）。  
3つのアクションは互いに独立しており、そのうち1つだけを制限することも可能です。

```python
# 実行時 API
sdk.scope.set_action("MyModule", "send", deny=True)              # 全てのメッセージ送信を禁止
sdk.scope.set_action("MyModule", "send", allow=["Text"])         # テキスト送信のみ許可
sdk.scope.is_action_allowed("MyModule", "send", name="Image")    # False
sdk.scope.is_action_allowed("MyModule", "api", name="get_user_info")  # 規則に従って判定
sdk.scope.delete_action("MyModule", "send")                      # 許可を復元
sdk.scope.get_action("MyModule", "send")                         # そのアクションの現在のルール
```

## 実行時API

スコープ実行時APIは3層構成です：**判定**（3つの質問）、**多次元の読み書き**（各次元ごとに `set` / `get` / `delete` パラメータ化メソッド、全タイプの署名が注釈付き、IDEによる補完可能）、**辞書式のデフォルト**（ドット区切りパスで任意のセクションに直接アクセス）。

```python
from ErisPulse import sdk

scope = sdk.scope
```

### 判定（3つの質問）

```python
scope.is_allowed("onebot11", "123456", "Chat")                 # ① モジュール次元
scope.is_allowed("onebot11", "123456", "Chat", "789012345")    # 会話レベルを含む
scope.is_allowed("onebot11", "123456", None)                   # フレームワーク層のリソース -> True

scope.is_identity_allowed("onebot11", "123456", "group_9", "u1")   # ② 身元次元

scope.is_action_allowed("MyModule", "send")                    # ④ 出力次元
scope.is_action_allowed("MyModule", "send", name="Image")      # メソッドレベルの細分化
```

### ① モジュール次元

```python
# バインディング（パラメータによって階層が決定される：session_id > bot_id > プラットフォームレベル）
scope.set_module("onebot11", bot_id="123456", modules=["Chat", "Tool*"])
scope.set_module("onebot11", blocked=["re:^Danger"])                       # プラットフォームレベル
scope.set_module("onebot11", bot_id="123456", session_id="g9", modules=["Chat"])  # 会話レベル
scope.set_module("onebot11", bot_id="123456", modules=["Music"], merge=True)      # 現在のエントリと並列
scope.set_module("onebot11", bot_id="123456", modules=["Chat"], persist=False)    # 実行時のみ

# 読み取り / 削除
scope.get_module("onebot11", bot_id="123456")   # {"modules": ["Chat"], "blocked": []}
scope.delete_module("onebot11", bot_id="123456")
```

> `merge=True` は**書き込み時の並列**（該当レベルの既存バインディングとエントリを併合）です。階層間の解析期における `merge = true` 設定キーは上記の[バインディング継承](#binding-inheritance-merge)を参照してください。これらは独立したメカニズムです。

### ② 身元次元

```python
# バインディング戦略（パラメータによって階層が決定される：user > session > bot > adapter；allow / deny のどちらかを指定）
scope.set_identity("onebot11", user_id="u_bad", deny=True)
scope.set_identity("onebot11", user_id="spam_*", deny=True)    # キーはglob / re: 正規表現をサポート
scope.set_identity("onebot11", bot_id="123456", session_id="g9", allow=True)

# 読み取り / 削除
scope.get_identity("onebot11", user_id="u_bad")   # {"deny": True}
scope.delete_identity("onebot11", user_id="u_bad")
```

### ③ 出力次元

```python
# 制限ルールの設定（allow: str|list; deny: bool|str|list; 全ルールの置換語義）
scope.set_action("MyModule", "send", deny=True)                    # 送信を完全に禁止
scope.set_action("MyModule", "send", allow=["Text"])               # 送信可能なのはテキストのみ
scope.set_action("MyModule", "api", deny=["set_*", "leave_*"])     # 管理系APIを禁止

# 読み取り / 削除
scope.get_action("MyModule", "send")       # {"allow": ["Text"]} 元のルール
scope.delete_action("MyModule", "send")    # 単一アクションの削除
scope.delete_action("MyModule")            # モジュールの全アクション制限の削除
```

### 一般的な操作

```python
scope.get("platforms")   # 辞書式のデフォルト：ドット区切りパスで任意のセクションを読み取る
scope.topology()         # 全量設定ツリー（ダッシュボード用）
scope.stats()
# {"module_calls": .., "module_filtered": .., "identity_checks": .., "identity_denied": ..,
#  "action_checks": .., "action_denied": .., "cache_hits": .., "cache_misses": ..}
scope.reset_stats()
scope.clear()           # 全設定をクリア（メモリ内でのみ有効）
```

### 高度な操作：辞書式ドット区切りパスのデフォルト

多次元メソッドは日常的なシナリオをカバーします。任意のノード（または将来追加される次元）に直接アクセスする必要がある場合、辞書式APIを使用します。`get` / `set` / `delete` はドット区切りパスを受け取り、辞書の深さを併合し、書き込み後に即座に読み取りが可能です。また、`scope[path]` / `scope[path] = v` / `del scope[path]` / `path in scope` のプロトコルも提供します：

```python
scope.set("bots.onebot11.123456", {"modules": ["Chat"], "blocked": []})
scope.set("identity.users.onebot11.u_bad", {"deny": True})
scope.get("actions.MyModule.send")

scope["platforms.onebot11"]        # 読み取り（存在しない場合KeyErrorを投げる）
scope["platforms.onebot11"] = {...}  # 書き込み
del scope["platforms.onebot11"]      # 削除
"actions.MyModule" in scope          # 存在確認
```

## キャッシュとホットアップデート

- `is_allowed` / `is_identity_allowed` / `is_action_allowed` の結果には **LRU キャッシュ**が付与されています
  （`scope.cache_size` でサイズを調整可能）、`set` / `delete` /
  設定のホットアップデート（`config.updated` / `config.set`）により自動的に無効になります
- すべての次元の設定は**即座に有効**になります。再起動は不要です
- スコープは「イベントごとに」判断され、イベント間で状態を保持しません：設定が変更されると、次のイベントは新しいルールに従います

## 設定形式の検証

ロード時またはホットリロード時に、各セクションの設定形式を検証します。型が間違っているセクション（例：`platforms` が文字列として記述された場合）、不正な出力ルール（例：`allow` が数値として記述された場合）、未知のアクション名、未知の最上位キー（例：`alow` がスペルミスされた場合）は、**WARNING** として出力され、対応するセクションまたは項目は無視されます。ただし、他の合法的な設定は通常通り有効になります。間違った記述が静かに無効になることはなくなります。

## よくある質問と注意点

### 1. 設定の階層と上書き

- モジュールの階層：セッションレベル > Bot レベル > プラットフォームレベル。**全体的な上書き**（子レベルで `merge = true` の場合、各項目が集合としてマージされる）。
  例えば「プラットフォームで Chat を許可し、Bot で Music を追加したい」場合は、Bot レベルで `merge = true` を設定するか、両方を明示的にリストに追加する。
- 身元の階層：ユーザー > セッション > Bot > アダプター。**最も具体的な設定されたポリシー**が優先される（例外として許可することも可能）。
- コマンドのユーザーのホワイトリスト/ブラックリスト：完全一致のコマンド名が glob キーに優先される（`event.command.acl` を参照）。

### 2. モジュール/コマンドが反応しない場合

まず、モジュール自体ではなく作用域を疑う：

```python
from ErisPulse import sdk

print(sdk.scope.is_allowed(event.get_platform(), bot_id, "MyModule", session_id))
print(sdk.scope.is_identity_allowed(event.get_platform(), bot_id, session_id, user_id))
print(sdk.scope.stats())   # module_filtered / identity_denied > 0 であれば、静かにフィルタリングされている
```

フィルタリングは**静かに**行われる（モジュールの階層と身元の階層では返信がなく、ルールを露出しない）。ただし、統計は蓄積される。
コマンドの階層で ACL に拒否された場合は、「権限がありません」という明示的な返信が返される。

### 3. 出力アクションが拒否された場合のトラブルシューティング

```python
from ErisPulse import sdk

print(sdk.scope.get("actions.MyModule"))
print(sdk.scope.stats())   # action_denied > 0 であれば、呼び出しがブロックされている
```

ブロックは**明示的**に行われる：拒否された呼び出しは `retcode = 34601` の標準的な失敗レスポンスを返す（ネットワークリクエストは発生しない）。

### 4. セッション識別子のプラットフォーム間の隔離

`(platform, session_id)` の組み合わせが一意の識別子となる。`scope.sessions.onebot11."789"` は onebot11 上でのみ有効であり、telegram 上で同じ `789` のセッションには影響しない。身元の階層におけるユーザーのキーも同様である。

## 拓扑ツリー API

`ModuleManager.get_topology()` と `AdapterManager.get_topology()` は、モジュール/アダプターの所属関係データを提供します。  
`sdk.get_topology()` は、スコープ（scope）を含むデータを一括で取得します。

```python
from ErisPulse import sdk

topology = sdk.get_topology()
# {
#   "modules": {                                   # モジュール → 所有するリソース
#     "Chat": {
#       "loaded": True, "enabled": True,
#       "commands": ["chat", "translate"],
#       "handlers": {"message": 2, "notice": 1},
#       "routes": {"http": ["/Chat/api"], "ws": [], "sse": []},
#       "lifecycle_hooks": 3,
#     }
#   },
#   "adapters": {                                  # アダプター → Bot → スコープ
#     "onebot11": {
#       "status": "started", "enabled": True,
#       "bots": {"123456": {"status": "online", "scope": {...}}},
#       "scope": {"modules": [...], "blocked": [...]},
#     }
#   },
#   "scope": {                                     # スコープ（モジュール / 身分 / 出力アクション）
#     "platforms": {...}, "bots": {...}, "sessions": {...},
#     "identity": {"adapters": {...}, "bots": {...}, "sessions": {...}, "users": {...}},
#     "actions": {...},
#   },
# }
```

- モジュールのトポロジーは、登録されたコマンド、イベントハンドラ、HTTP/WS/SSE ルート、ライフサイクルフックを統合し、モジュールリソースツリーの描画に便利です。
- アダプターのトポロジーは、各アダプターのステータス、所属する Bot のステータス、プラットフォームレベル/Bot レベルのスコープバインディング（モジュール次元）を統合します。