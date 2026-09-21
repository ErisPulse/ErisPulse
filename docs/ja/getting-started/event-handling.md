# イベント処理入門

このガイドでは、ErisPulseにおける各種イベントの処理方法について説明します。

## イベントの種類概要

ErisPulseは以下のイベントの種類をサポートしています：

| イベントの種類 | 説明 | 適用場面 |
|---------|------|---------|
| メッセージイベント | ユーザーが送信したすべてのメッセージ | チャットボット、コンテンツフィルタ |
| コマンドイベント | コマンド接頭辞で始まるメッセージ | コマンド処理、機能の入口 |
| 通知イベント | システム通知（友達追加、グループメンバー変更など） | メッセージの歓迎、ステータス通知 |
| 要求イベント | ユーザーの要求（友達リクエスト、グループ招待） | 要求の自動処理 |
| メタイベント | システムレベルのイベント（接続、ハートビート） | 接続監視、ステータスチェック |

## メッセージイベントの処理

> **ヒント**: IDEの自動補完と型チェックのサポートを得るため、イベントハンドラで`Event`型の注釈を使用することを推奨します。

```python
from ErisPulse.Core.Event import Event  # Event型の注釈用にインポート
```

### すべてのメッセージを監視

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"{user_id}からのメッセージを受信: {text}")
```

### プライベートメッセージを監視

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"こんにちは、{user_id}！これはプライベートメッセージです。")
```

### グループメッセージを監視

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"グループ {group_id} で {user_id} がメッセージを送信しました")
```

### @メッセージを監視

```python
@message.on_at_message()
async def at_handler(event: Event):
    # @されたユーザーのリストを取得
    mentions = event.get_mentions()
    await event.reply(f"あなたはこれらのユーザーを@しました: {mentions}")
```

### ワイルドカードと正規表現の監視

`on_message` / `on_private_message` / `on_group_message` /
`on_at_message`の4つのメッセージデコレータは`pattern`（globワイルドカード）と`regex`（正規表現）をサポートし、一致しないメッセージは**処理がトリガーされません**：

```python
# globワイルドカード：* 任意の文字列、? 1文字、[seq] 文字集合
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("签到成功")

# 正規表現：金額をマッチ
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"受信金額：{event.get_text()}")

# pattern と regex 両方指定 → 両方一致する必要がある
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply`もこの2つのパラメータをサポートします（[返信の待ち機能](../developer-guide/modules/event-wrapper.md#返信の待ち機能)を参照）。

## コマンドイベントの処理

### 基本コマンド

```python
from ErisPulse.Core.Event import command

@command("help", help="ヘルプ情報を表示")
async def help_handler(event):
    help_text = """
利用可能なコマンド:
/help - ヘルプを表示
/ping - 接続をテスト
/info - 情報を表示
    """
    await event.reply(help_text)
```

### コマンドの別名

```python
@command(["help", "h"], aliases=["help", "h"], help="ヘルプ情報を表示")
async def help_handler(event):
    await event.reply("ヘルプ情報...")
```

ユーザーは以下のいずれかの方法で呼び出すことができます：
- `/help`
- `/h`
- `/help`

### コマンドの引数

```python
@command("echo", help="メッセージを繰り返す")
async def echo_handler(event):
    # コマンド引数を取得
    args = event.get_command_args()
    
    if not args:
        await event.reply("繰り返すメッセージを入力してください")
    else:
        await event.reply(f"あなたが言った: {' '.join(args)}")
```

引数は、大文字小文字を無視する設定に関わらず、ユーザー入力のままの形式で保持されます（コマンド名のマッチングは統一されますが、引数の内容には影響しません）。

### 宣言的引数とオプション（args= / options=）

手動で引数を解析するには、自分で型変換とエラーメッセージの提示を行う必要があります。`args=` / `options=`を宣言すると、フレームワークは権限チェックを通過した後にコマンド引数を自動的に解析し、**名前でハンドラに注入**します。ユーザーの入力が間違っている場合は、ローカライズされたエラーメッセージと使い方を自動的に返し、例外でクラッシュすることはありません。`/help <コマンド>`も自動的に使い方を表示します：

```python
@command(
    "roll",
    args="<count:int> [sides:int=6]",
    options={"verbose": "-v/--verbose", "label": "--label"},
    help="サイコロを振る",
)
async def roll_handler(event, count: int, sides: int = 6, verbose: bool = False, label: str = ""):
    total = sum(random.randint(1, sides) for _ in range(count))
    await event.reply(f"{count}回 {sides}面サイコロを振った、合計点数：{total}")
```

`args=`の位置引数の構文は、`<count:int>`は必須、`[sides:int=6]`はオプション（デフォルト値付き）です。サポートされる型は以下の通りです：

| 型 | 入力例 | 説明 |
|------|---------|------|
| `str` | `hello` | テキスト（デフォルト型） |
| `int` / `float` | `3` / `0.5` | 数値 |
| `bool` | `是` / `yes` / `はい` / `да` / `true` / `no` / `取消` | ブール値、相互確認（`Event.confirm()`）の確認語を再利用 |
| `literal` | `<mode:literal=fast|slow>` | 列挙、指定された値のみを受け入れる；オプション形式はデフォルトで最初の値を取る |
| `duration` | `90s`、`1h30m`、`1d` | 時間、秒に換算してfloatで |
| `rest` | `<text:rest>` | 残りの全テキスト（最後に来なければならない） |

`options=`は辞書形式で宣言：キーはハンドラの引数名、値はフラグ形式（複数の別名は`/`で区切る）。`bool`の注釈を持つ引数はブールフラグ（出現すれば`True`）；それ以外（デフォルトは`str`）は値付きオプションで、`--label hello`と`--label=hello`の両方の値を受け入れ、型はハンドラの注釈に従う。オプションはまず認識されて除外され、残りのトークンは`args=`で解析される（`rest`はオプションを除外した後の残りのテキストを覆う）。

**動作の要点**：

- 権限チェックは引数解析より先に実行される——権限のないユーザーはトリガーされない
- 解析失敗（型が合わない / 引数が足りない / 引数が多すぎる / 未知のオプション）は、ローカライズされたエラーメッセージと使い方を自動的に返し、コマンドは認識される
- 宣言された引数名はハンドラの署名に存在しなければならない、そうでなければ登録時に`ValueError`を投げる
- `args=` / `options=`を宣言しないコマンドは、動作に変化がない（後方互換性）

### コマンドの管理（cooldown= / rate_limit= / deprecated=）

手動でクールダウンやリクエスト制限、廃止のメッセージを宣言で置き換えられる、これらは任意に組み合わせることができる。

**クールダウン**——時長の構文は`args=`の`duration`型と同じ（例: `"30s"`、`"1h30m"`、`"1d"`）：

```python
@command("daily", cooldown="1d", cooldown_key="user", cooldown_reply="今日すでにサインインしました")
async def daily_handler(event):
    await event.reply("サインイン成功！")
```

**リクエスト制限**——スライディングウィンドウの宣言は`"回数/時間"`（例: `"5/minute"`、`"10/s"`、`"3/2m"`）：

```python
@command("search", rate_limit="5/minute", rate_limit_key="user")
async def search_handler(event):
    await event.reply("検索結果")
```

**廃止**——呼び出し時に自動的に廃止メッセージを返し、`deprecated_reject=True`で実行を拒否する：

```python
@command("oldcmd", deprecated="新しいコマンド /newcmd を使用してください", deprecated_reject=True)
async def old_handler(event): ...
```

キーの粒度（`cooldown_key=` / `rate_limit_key=`）：`"user"`（デフォルト、同一ユーザーが共有）、`"session"`（同一セッションが共有、同じグループのように）、`"global"`（すべてのユーザーとセッションが共有）。

**動作の要点**：

- クールダウン / リクエスト制限がヒットした場合、**静かに無視**される（作用域に応じて静かに）；`cooldown_reply=` / `rate_limit_reply=`を宣言した場合、ヒットしたときにその文言を返す
- コマンドがヒットした時点で認識される——管理がヒットしたコマンドは低優先度のメッセージハンドラに漏れることはない
- 管理判定はすべての権限チェックと引数解析が通過し、実際の実行前に実行される：権限のないユーザーはトリガーされず、引数のエラーは消費されない
- クールダウンとリクエスト制限を同時に宣言した場合、クールダウンが先に判定される（クールダウンがヒットした場合、リクエスト制限のウィンドウは占有されない）
- `deprecated=`はデフォルトで返す文言の後に**実行を続ける**；`deprecated_reject=True`で実行を拒否する（`command.executed`のフックは`success=False, error="deprecated"`を記録）
- `/help`のリストと単一コマンドのヘルプは自動的に廃止マークと文言を表示
- 状態はプロセス内メモリに保持され、モジュールのアンロード時に自動的にクリアされる；マルチプロセス間の共有やリスタート後の永続化は対象外
- 宣言は登録時に検証される（fail-fast）：構文が不正、キー粒度がホワイトリスト外、replyが主宣言と組み合わされていない場合、`ValueError`を投げる

### ハンドラのスロットリング（throttle=）

メッセージハンドラのスパム防止宣言——同じキーのイベントは間隔内に1件のみ処理され、残りは静かに無視される：

```python
from ErisPulse import sdk

@sdk.message.on_message(throttle="2s", throttle_key="user")
async def handler(event): ...
```

`on_message` / `on_private_message` / `on_group_message` / `on_at_message`
はすべてサポートしている；`throttle_key=`はコマンド管理と同じキー粒度（user / session / global）で、時長の構文は`duration`と同じ。スロットリングは`pattern=` / `regex=`などの既存の条件と重複して有効になる（すべて満たす場合にトリガーされる）；間隔内に無視されたイベントはTRACEログに記録されるだけ；宣言は登録時に検証される。

### 依存注入（Depends）

共通の依存（データベースセッション、設定の読み取りなど）は依存関数として抽出でき、ハンドラは
`Depends(依存関数)`をデフォルト値として宣言し、フレームワークは呼び出し前にコンテキストオブジェクトを使って依存関数を呼び出し、名前で注入する：

```python
from ErisPulse.Core import Depends

async def get_session(event):
    return await sdk.module.call("DB", "get_session")

@command("admin")
async def admin_handler(event, db=Depends(get_session)):
    ...
```

デフォルトで**リクエストレベルのキャッシュ**が有効：1回のイベント配信内では、同じ依存関数は1回だけ解析され、すべての注入ポイントで結果を共有する（`get_db`が1回のイベントで1回だけデータベースセッションを生成する）。リクエスト間では自動的に再利用されない。`Depends(get_db, use_cache=False)`で1つの依存のキャッシュを無効にできる。

フレームワークのすべての注入ポイントをカバーする——コマンドハンドラ、イベントハンドラ（`message.on_message()`など）、ライフサイクルフック（`sdk.lifecycle.on`）、SSEルートハンドラ。依存関数の最初の引数は注入ポイントのコンテキストオブジェクト（イベントの場合は`Event`、ライフサイクルの場合はイベント`data`、ルートの場合は`HttpRequest` / `SseEmitter`）である。同期と非同期の依存関数を宣言できる。

**他のモジュールのサービスを宣言する**（糖衣構文）：

```python
@command("query")
async def query_handler(event, session=Depends.module("DB", "get_session")):
    ...
```

`Depends.module(モジュール名, メソッド名, *固定引数)`は、依存関数内で`sdk.module.call(...)`を呼ぶのと同等。モジュールのインスタンス化（`__init__`）はカバー対象外——インスタンス化時にはコンテキストオブジェクトがない。FastAPIが提供するHTTPルートはFastAPIの元の`fastapi.Depends`を使用すること。

**動作の要点**：

- 宣言は登録時に検証される（fail-fast）：依存が呼び出せない、または`args=` / `options=`の引数と重複する場合、`ValueError`を投げる
- 依存関数が投げた例外とハンドラ自身の例外は同口径で処理される（コマンドは自動的にエラーを返す）
- `Depends`を宣言しないハンドラはゼロオーバーヘッド（配分時にいかなるリフレクションも行わない）
- FastAPIが提供するHTTPルートはFastAPIの元の`fastapi.Depends`を使用すること

### コマンドグループ

```python
@command("admin.reload", group="admin", help="モジュールを再読み込み")
async def reload_handler(event):
    await event.reply("モジュールが再読み込まれました")

@command("admin.stop", group="admin", help="ロボットを停止")
async def stop_handler(event):
    await event.reply("ロボットが停止されました")
```

`group`パラメータはヘルプリストの分類にのみ使用される；上記の例における`admin.reload`は**一つの全体のコマンド名**（ドットは命名スタイルであり、ユーザーは`/admin.reload`を入力する必要がある）。

### サブコマンド

コマンド名は**スペース区切りの複数トークン**形式をサポートし、`/admin add`、`/admin user ban`のようなサブコマンドを実現できる：

```python
@command("admin", help="管理コマンド")
async def admin_handler(event):
    await event.reply("使い方：/admin add | /admin remove")

@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    target = event.get_command_args()[0]
    await event.reply(f"追加しました：{target}")

@command("admin remove", aliases=["a remove"], help="管理者を削除")
async def admin_remove_handler(event):
    await event.reply("削除しました")
```

マッチングルール（**最長プレフィックスマッチ**）：

- `/admin add x` は `admin add` に優先的にマッチし、`event.get_command_args()` は `["x"]`（サブコマンド名以降の引数）を返す
- `admin` だけが登録されている場合、`/admin add x` は `admin` にマッチし、`get_command_args()` は `["add", "x"]`（歴史的な動作）を返す
- 別名は複数トークン形式（`a remove`）もサポートし、単一トークンの別名（`a`）もサブコマンドに指定できる
- 親子コマンドが同時に登録されている場合、未登録のサブコマンド入力（例：`/admin list x`）は親コマンドに降格する

**権限の継承**：サブコマンドに`permission`を宣言していない場合、自動的に直近で権限を宣言した祖先コマンドを継承する——`/admin`を保護すれば、その下のすべてのサブコマンドも自動的に保護される；サブコマンド自身が宣言した権限が優先される：

```python
def is_admin(event):
    return event.get_user_id() in {"user123"}

@command("admin", permission=is_admin, help="管理コマンド")
async def admin_handler(event):
    ...

# permissionを再宣言する必要はない、is_adminを自動的に継承する
@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    ...
```

注意：`master=True` と `hidden` は**継承されない**、必要であればサブコマンドで個別に宣言する必要がある；ユーザーACL（ホワイトリスト/ブラックリスト）はコマンドの全名でマッチし、glob規則（例：`"admin*"`）は一括でサブコマンドをカバーできる。

`/help`のコマンド一覧では、サブコマンドは可視の親コマンドの下にインデント表示される（`admin` → `admin add`は1段階インデント、`admin user` → `admin user ban`は2段階インデント）。

### コマンドの権限とアクセス制御

コマンドの権限は3層に分かれ、上から下へ順に判定される（**上層が拒否すれば下層は見ない**）：

```python
# ① コマンド権限ACL（ユーザー側の設定）：コマンドごとのユーザーのホワイトリスト/ブラックリスト、拒否時は「権限不足」を返す
# ② master=True —— フレームワークのオーナーのみ実行可能（フレームワークが自動的にチェックし、拒否時は「権限不足」を返す）
@command("restart", master=True, help="モジュールを再起動")
async def restart_handler(event):
    await event.reply("モジュールが再起動されました")

# ③ permission=呼び出し関数 —— コマンド自身の制御ロジック（Trueを返す場合に実行）
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="管理パネル")
async def panel_handler(event):
    await event.reply("管理パネルへようこそ")
```

**コマンドユーザーACL**（`ErisPulse.event.command.acl`）：ユーザーは任意のコマンドにユーザーのホワイトリスト/ブラックリストを設定でき、コマンド名は正確またはglobパターン（例：`"roll*"`）をサポートし、拒否時は「権限不足」を返す：

```toml
# config.toml —— restartを123456のみ実行可能に；666は一律拒否
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

判定順序：`deny`がヒット → 拒否；`allow`が非空でヒットしない → 拒否；ACLが設定されていない場合は
`event.command.default_allow`（`false` = 严格モード、ACLがない場合は拒否；`true`の場合は開発者のデフォルト`master=True` / `permission`）に従う。実行時API（コマンド名はglobをサポート）：

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # 允許リスト
command.deny_user("restart", "onebot11", "666")       # 拒絶リスト
command.remove_acl("restart")                          # ホワイトリスト/ブラックリストを削除
command.get_acl("restart")                             # 現在のリストを取得
```

> コマンドハンドラはイベントパッケージからインポートする：`from ErisPulse.Core.Event import command`；
> またはSDKイベントパッケージからアクセスする：`sdk.Event.command`（これらは同一のシングルトン）。
> モジュール内では通常、コマンドデコレータからインポートされる（`from ErisPulse.Core.Event import command`）。

コマンド間・ユーザー間の**イベントレベル**のアクセス制御（特定の人のメッセージを受け取るか否か）
は作用域**アイデンティティ次元**（`scope.identity`）を通じて行う；**モジュールレベル**の可用性（どのモジュールが使えるか）
は作用域**モジュール次元**（`scope.platforms / bots / sessions`）を通じて行う。
[作用域（scope）](../advanced/scope.md)を参照。

> 建議：コマンド内部でビジネスロジックを連動させる場合は`master=True` / `permission`を使用する；純粋にユーザー／グループで
> アクセス制御を行う場合は作用域アイデンティティ次元を使用する；モジュールの可用性を制御する場合は作用域モジュール次元を使用する。

### コマンドの優先度

```python
# 優先度の数値が大きいほど、実行が早くなる
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("高優先度のハンドラ")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("低優先度のハンドラ")
```

### 並列イベント処理

ErisPulseのイベントシステムは**同優先度並列、異なる優先度直列**のスケジューリングモデルを採用している：

```
イベント到着
    ↓
priority=10 組: [ハンドラC || ハンドラD] 並列 → 結果を結合
    ↓ (中断されていない場合)
priority=0 組: [ハンドラA || ハンドラB] 並列 → 結果を結合
    ↓
...
```

- **同優先度並列**：優先度が同じ複数のハンドラは同時に実行され、スループットが向上する
- **跨級直列**：異なる優先度の組は順序で実行される（数値が大きいほど先に実行）、高優先度ハンドラが先に実行されるようにする
- **Copy-On-Write**：ハンドラが変更しない場合はコピーを作成せず、ゼロオーバーヘッドを確保する
- **競合処理**：同優先度の複数ハンドラが同じフィールドを変更した場合、最後に変更された値を使用し、警告ログを記録する
- **中断メカニズム**：任意のハンドラが`event.done()`（デフォルト）または`event.done(claim=False)`を呼び出した後、以降の低優先度の組をスキップする。認領とブロックの違いは下記の[「リンク制御：認領とブロック」](#リンク制御認領とブロック)を参照

```python
# 例：同優先度ハンドラが並列で実行される
@message.on_message(priority=0)
async def handler_a(event):
    # 作業Aを処理
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # handler_aと並列で実行
    event['result_b'] = process_b()

# 異なる優先度で直列で実行される
@message.on_message(priority=10)
async def handler_c(event):
    # 最も優先度が高い、最初に実行される
    pass
```

> **並行上限**：すべてのマッチするハンドラのTaskは**即座に作成**されるが、シグナル量によって**同時に実行される数**を制限する。デフォルト上限は **64**（`ErisPulse.framework.handler_max_concurrency`、ホットアップデート可能）。上限を超えたTaskはシグナル量で待機し、前の処理が完了してから進む。イベントの洪水時にはこれが「圧力調整弁」になる。
>
> **遅いログ**：単一のハンドラが1秒以上かかる場合、フレームワークはログにWARNINGを出す（`handler_slow`）。`wait_reply`の待機時間は処理時間から差し引かれるため、「返信を待つ」ことで誤って遅いと判定されることはない。

## スコープフィルタリング：なぜ私のモジュールはメッセージを受け取らないのか

イベントが到着した後、2つの**静かな**フィルタリングがある（どちらも返信せず、エラーも出さない）：

1. **アイデンティティ次元**（`ErisPulse.scope.identity`）：イベントが配分のエントランスに到達した時点で、ユーザー > グループ > ボット > アダプターの順に受信するかどうかを判定する。
   拒否された**イベント全体**は直接破棄され、どのハンドラ（コマンドディスパッチャーを含む）もトリガーされない。
2. **モジュール次元**（`ErisPulse.scope`）：イベントが特定のモジュールのハンドラ/コマンドに到達した時点で、セッション > ボット > プラットフォームの順にそのモジュールが利用可能かどうかを判定し、**通過しない場合は静かにスキップ**される。

```toml
# 例1：特定のグループのすべてのメッセージを伝播しない
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# 例2：MyModuleを特定のボットから遮断
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

この場合、そのグループのメッセージが到着したときに、`MyModule`のコマンドとイベントハンドラは**すべてがスケジュールされない**。これはバグではなく、フィルタリング機構である——「モジュールが反応しない」問題を調査する際には、まず作用域のアイデンティティとモジュールのバインディングを確認する。

- フィルタリングのログは**TRACE**レベルでしか表示されない（`core.scope.identity_denied` / `core.scope.denied`）、デフォルトのINFOでは痕跡が見えない
- フレームワークレベルのハンドラ（コマンドディスパッチャー `scope_exempt=True`）は**モジュール次元**の影響を受けないが、**アイデンティティ次元**の影響を受ける（イベント全体が破棄されている）
- コマンド実行前に3番目のフィルタがある：コマンドユーザーACL（拒否時は「権限不足」を返す、上節参照）
- 4番目のフィルタは**イベントオーバーライド**（下節参照）

> [!NOTE]
> **作用域フィルタリングとイベント認領（claim）の関係**：2つの静かなフィルタはハンドラの**スケジューリング前**に発生する——フィルタでスキップされたハンドラは実行されず、認領状態に参加しない。イベントが認領されたかどうかは、**実行された**ハンドラ（コマンドが認領した、返信が認領した、明示的に呼び出した）によってのみ決まる；作用域拒否は認領もブロックもしない（静かにスキップし、メッセージは残りの配分チェーンを完了する）。

> 作用域の設定、マッチングの構文、実行時APIは [作用域（scope）](../../advanced/scope.md) を参照。

## イベントオーバーライド：モジュールのコードを変更せずに、任意のイベントタイプの動作を上書き

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要。

イベントハンドラは登録時に宣言されたパラメータ（`pattern` / `regex` / `master` / `hidden` など）は**開発者のデフォルト**にすぎない。
一括上書きシステムは、イベントタイプごとに任意のモジュールの動作を上書きできるようにユーザーに許可を与える——OneBot12標準タイプ
（meta / message / notice / request）と ErisPulse 拡張タイプ（command）はそれぞれ固有の上書き可能なパラメータを持つ：

| イベントタイプ | 上書き可能なパラメータ | 作用 |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | テキストトリガー条件 + メッセージサブタイプホワイトリスト |
| `notice` | `detail_types` / `pattern` / `regex` | 通知サブタイプホワイトリスト + テキスト条件 |
| `request` | `detail_types` / `pattern` / `regex` | 要求サブタイプホワイトリスト + テキスト条件 |
| `meta` | `detail_types` | メタイベントサブタイプホワイトリスト（connect / heartbeat など） |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | コマンド実装パラメータ（ユーザー優先） |
| `acl`（command専用） | `allow` / `deny` | コマンドユーザーホワイトリスト/ブラックリスト（コマンド名glob） |

```toml
# message：テキストトリガー条件を上書き（コード内の条件とAND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice：特定の通知サブタイプのみを応答
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command：実装パラメータを上書き（ユーザー優先——絞り込むか、許可を広げる）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl：コマンドユーザーホワイトリスト/ブラックリスト（跨コマンドglob）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACLのデフォルト（false = 严格モード：ACLがない場合は拒否）
acl_default_allow = true
```

実行時API（`from ErisPulse.Core.Event import overrides` または `sdk.Event.overrides`，
**タイプのサブネームスペース**——各タイプに対称的な `set` / `get` / `delete` 三件セット）：

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # messageのテキスト条件
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # コマンドパラメータ
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # コマンドユーザーブラックリスト

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # 開発者のデフォルトに戻す
```

- 上書き条件とハンドラコード内の条件は**同時に有効**（ANDの意味）；`command`パラメータは開発者の宣言と**深くマージ**（上書きが優先）
- `detail_types`：イベントに`detail_type`が欠けていたら通過（未知のイベントを誤って殺さない）
- `pattern` / `regex`：テキストのないイベント（connect / heartbeat など）は制約を受けず、直接通過
- `command`上書きのキー`master`は同期的にストレージキー`must_master`にマッピング；コマンドの禁止は`acl`のdenyを通じて行う
- **キー名のマッピング説明**：`overrides.command.set("My", "restart", master=True)`のパラメータ名
  `master`は設定の別名にすぎず、実際のストレージキーと`get()`の返り値のキー名は**`must_master`**に統一されている
  （`get()`は`{"must_master": true}`を返す）——実行時の判定はストレージキーを読み取るため、
  `master`キー名で取得しないでください
- 設定は変更したら即座に有効（ホットアップデート）、形式の検証は警告（未知のパラメータ / 壊れた項目は無視）

## リンク制御：認領とブロック

> [!NOTE]
> `event.done()` / `event.mark_processed()` の `claim=` / `stop=` パラメータはこの機能には ErisPulse **2.7.1+** が必要。

ErisPulseは「認領」と「ブロック」の2つの正交的な概念を分離し、`event.done()`で統一的に制御することで、コマンド処理の周囲にログ、監査、権限などの観測層を重ねることが可能になる。

**2つの概念の正確な定義：**

- **認領（claim）**：イベントがこのハンドラによって処理されたことをマークする（`_processed`に書き込む）。コマンドディスパッチャーは認領されたイベントを見ると**重複を避ける**——同じメッセージが複数のコマンドハンドラに重複して処理されない。典型的なシナリオ：コマンドがマッチした後に認領し、コマンドディスパッチャーの介入を阻止する。
- **ブロック（stop）**：イベントを**より低い優先度**のハンドラに伝播しないように阻止する（`_propagation_stopped`に書き込む）。低優先度のハンドラはこのイベントを見なくなる。典型的なシナリオ：高優先度のハンドラがイベントを完全に処理した後、低優先度のハンドラが実行されないようにする。

| `event.done(...)` | 認領 | ブロック | シナリオ |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | コマンド / ハンドラ処理完了の標準的なやり方 |
| `event.done(stop=False)` | ✔ | ✘ | 認領のみ：低優先度は引き続き見る（ログ / 統計） |
| `event.done(claim=False)` | ✘ | ✔ | ブロックのみ（例：ファイアウォール / 限流）、認領は行わない |

`event.done(claim=, stop=)` は `event.mark_processed(claim=, stop=)` の別名で、パラメータと動作は完全に等価である。

```python
@command("help")
async def help_cmd(event):
    event.done()            # 認領 + ブロック（コマンド処理完了の標準的なやり方）

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # 認領のみ：低優先度は引き続き実行される（ログ / 統計）

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # ブロックのみ：低優先度は実行されない、認領は行わない
```

### コマンドと返信の block 設定

**コマンドがマッチしたら認領**：メッセージが登録されたコマンド名（サブコマンド/別名を含む）にマッチすると、その後の作用域や権限判定結果に関係なく、認領され、デフォルトでブロックされる——権限拒否されたコマンドは、低優先度のメッセージハンドラに漏れることなく、二重応答されない（「コマンドが拒否された後に on_message が再度反応する」二重応答を回避）。

ブロックを解除して、低優先度の観測者（ログ / 審査 / 権限）がこれらのメッセージを見られるようにするには、設定でブロックを解除する：

```toml
[ErisPulse.event.command]
block = false   # コマンドメッセージは低優先度ハンドラに流れ続ける（認領は影響しない、重複消費はしない）

[ErisPulse.event.wait_reply]
block = false   # wait_reply で消費された返信は低優先度ハンドラに流れ続ける
```

> 注意：`block`は**ブロック**（stop）の制御にのみ作用し、**認領**（claim）には影響しない——マッチしたコマンドは決してメッセージハンドラに重複消費されない；コマンドにマッチしないメッセージは通常通りメッセージハンドラに流れ続ける。

## 通知イベントの処理

### 友達追加

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "新朋友"
    await event.reply(f"欢迎添加我为好友，{nickname}！")
```

### グループメンバーの増加

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"欢迎新成员 {user_id} 加入群 {group_id}")
```

### グループメンバーの減少

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"成员 {user_id} 离开了群 {group_id}")
```

## 要求イベントの処理

### 友達リクエスト

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"收到好友请求: {user_id}, 附言: {comment}")
    
    # 通过适配器 API 处理请求
    # 具体实现请参考各适配器文档
```

### グループ招待リクエスト

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"收到群 {group_id} 的邀请，来自 {user_id}")
```

## メタイベントの処理

### 接続イベント

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} 平台已连接")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"{platform} 平台已断开连接")
```

### ハートビートイベント

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} 心跳检测")
```

### Bot 状態の照会

適切なアダプターがメタイベントを送信すると、フレームワークは自動的にBotの状態を追跡し、いつでも照会できるようになります：

```python
from ErisPulse import sdk

# 指定されたBotがオンラインかどうかを確認
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot is online")

# 現在オンラインのすべてのBotをリストアップ
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# 完全な状態の概要を取得
summary = sdk.adapter.get_status_summary()
```

## 交互処理

### replyメソッドを使って返信を送信

`event.reply()`メソッドは、@や返信などの修飾パラメータをサポートし、メッセージの送信を便利にする：

```python
# 簡単な返信
await event.reply("你好")

# 異なるタイプのメッセージを送信
await event.reply("http://example.com/image.jpg", method="Image")  # 画像
await event.reply("http://example.com/voice.mp3", method="Voice")  # 音声

# 単一のユーザーを@する
await event.reply("你好", at_users=["user123"])

# 複数のユーザーを@する
await event.reply("大家好", at_users=["user1", "user2", "user3"])

# メッセージに返信する
await event.reply("返信内容", reply_to="msg_id")

# @全員
await event.reply("公告", at_all=True)

# 組み合わせ: @ユーザー + 返信メッセージ
await event.reply("内容", at_users=["user1"], reply_to="msg_id")
```

### ユーザーの返信を待つ

```python
@command("ask", help="询问用户")
async def ask_handler(event):
    await event.reply("请输入你的名字:")
    
    # ユーザーの返信を待つ、タイムアウト時間30秒
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")
    else:
        await event.reply("等待超时，请重新输入。")
```

> [!TIP]
> **待機中でもコマンドは使用可能**（2.8.3+）：コマンド接頭辞で始まり、登録されたコマンドにマッチする
> メッセージ（例：`/cancel`）は**返信内容**として処理されず、待機は継続する——
> ユーザーはいつでもキャンセル/切り替えでき、コマンド実行後も返信を続けることができる。以前の「すべてのテキストを待つ」
> 行動が必要な場合は：設定 `ErisPulse.event.wait_reply.cmdpass = true`、または単回
> `wait_reply(cmdpass=True)`。

### バリデーション付きの待機返信

```python
@command("age", help="询问年龄")
async def age_handler(event):
    def validate_age(event_data):
        """年齢が有効かを検証"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("请输入你的年龄 (0-150):")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"你的年龄是 {age} 岁")
    else:
        await event.reply("输入无效或超时")
```

### コールバック付きの待機返信

```python
@command("confirm", help="确认操作")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["是", "yes", "y"]:
            await event.reply("操作已确认！")
        else:
            await event.reply("操作已取消。")
    
    await event.reply("确认执行此操作吗？(是/否)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### 確認ダイアログ (confirm)

ユーザーの確認または否定を待つ、自動的に組み込みの確認語を認識する：

```python
@command("confirm", help="确认操作")
async def confirm_handler(event):
    if await event.confirm("确定要执行此操作吗？"):
        await event.reply("已确认，执行中...")
    else:
        await event.reply("已取消")

# 自定义确认语
if await event.confirm("继续吗？", yes_words={"go", "继续"}, no_words={"stop", "停止"}):
    pass
```

### 選択メニュー (choose)

ユーザーは選択番号または選択項目を返信できる：

```python
@command("choose", help="选择")
async def choose_handler(event):
    choice = await event.choose(
        "请选择颜色：",
        ["红色", "绿色", "蓝色"]
    )
    
    if choice is not None:
        colors = ["红色", "绿色", "蓝色"]
        await event.reply(f"你选择了：{colors[choice]}")
    else:
        await event.reply("超时未选择")
```

**マージモード**：`merge_prompt=True`の場合は、オプションをプロンプトに統合し、`method`で指定された方法で1つのメッセージとして送信する：

```python
# Markdownで統合されたプロンプト + オプションを送信
choice = await event.choose(
    "## 请选择颜色\n{options}\n请回复编号",
    ["红色", "绿色", "蓝色"],
    method="Markdown",
    merge_prompt=True,
)
```

> `{options}`の占位符はオプションの挿入位置を制御する；書かなければプロンプトの末尾に追加する。
> `placeholder`パラメータで占位符をカスタマイズできる（例：`placeholder="[choices]"`）。
> `options_format="auto"`（デフォルト）は`method`に応じてスタイルを自動選択する：Markdown→無序リスト、Html→有序リスト、その他→テキストリスト。
> テキスト系メソッド（Text/Markdown/Htmlなど）はデフォルトでオプションを末尾に統合する；非テキスト系メソッド（Imageなど）はデフォルトで2つのメッセージに分割する。

### フォーム収集 (collect)

複数ステップでユーザー入力を収集する：

```python
@command("register", help="注册")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "请输入姓名："},
        {"key": "age", "prompt": "请输入年龄：", 
         "validator": lambda e: e.get_text().isdigit()},
        {"key": "email", "prompt": "请输入邮箱："}
    ])
    
    if data:
        await event.reply(f"注册成功！\n姓名：{data['name']}\n年龄：{data['age']}\n邮箱：{data['email']}")
    else:
        await event.reply("注册超时或输入无效")
```

### 任意イベントを待つ (wait_for)

条件を満たす任意のイベントを待つ、同一ユーザーに限定されない：

```python
@command("wait_member", help="等待新成员")
async def wait_member_handler(event):
    await event.reply("等待群成员加入...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"欢迎新成员：{evt.get_user_id()}")
    else:
        await event.reply("等待超时")
```

### 多段会話 (conversation)

インタラクティブな多段会話コンテキストを作成する：

```python
@command("survey", help="问卷调查")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("欢迎参与问卷调查！")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("对话超时，再见！")
            break
        
        text = reply.get_text()
        
        if text == "退出":
            await conv.say("再见！")
            break
        
        await conv.say(f"你说了：{text}，继续输入或回复'退出'结束")
```

### 内置確認語

ErisPulseは中英の確認語の集合を内蔵している：

- **確認語** (`CONFIRM_YES_WORDS`): 是、yes、y、确认、确定、好、好的、ok、true、对、嗯、行、同意、没问题...
- **否定語** (`CONFIRM_NO_WORDS`): 否、no、n、取消、不、不要、不行、cancel、false、错、拒绝、不可以...

## イベントデータのアクセス

### Eventオブジェクトの一般的なメソッド

```python
@command("info")
async def info_handler(event):
    # 基本情報
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # 送信者情報
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # メッセージ内容
    message_segments = event.get_message()
    alt_message = event.get_alt_message()
    text = event.get_text()
    
    # グループ情報
    group_id = event.get_group_id()
    
    # ロボット情報
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # 原始データ
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # プラットフォーム情報
    platform = event.get_platform()
    
    # メッセージタイプの判定
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # コマンド情報
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### プラットフォーム拡張メソッド

内蔵メソッドのほか、各プラットフォームアダプターはプラットフォーム固有のメソッドを登録し、プラットフォーム特有のデータにアクセスできるようにする。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # プラットフォームに応じて固有メソッドを呼び出す
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram固有メソッド
    elif platform == "email":
        subject = event.get_subject()           # 電子メール固有メソッド
```

プラットフォームが特定のメソッドを登録しているかどうかを確認するには、特定のプラットフォームが登録したメソッドを照会できる：

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> 各プラットフォームが登録する固有メソッドについては、対応する [プラットフォームのドキュメント](../platform-guide/) を参照してください。

## イベント処理のベストプラクティス

### 1. エラーハンドリング

```python
@command("process")
async def process_handler(event):
    try:
        # ビジネスロジック
        result = await do_some_work()
        await event.reply(f"結果: {result}")
    except ValueError as e:
        # 予期されたビジネスエラー
        await event.reply(f"パラメータエラー: {e}")
    except Exception as e:
        # 予期されないエラー
        sdk.logger.error(f"処理失敗: {e}")
        await event.reply("処理失敗、後で再試行してください")
```

### 2. ログ記録

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"メッセージを処理: {user_id} - {text}")
    
    # モジュール固有のログを使用
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"詳細なデバッグ情報")
```

### 3. 条件処理

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """条件処理 - ハンドラ内で判定"""
    # 特定のユーザーのメッセージだけを処理
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # 特定のキーワードを含むメッセージだけを処理
    if "关键词" not in event.get_text():
        return
    
    await event.reply("条件が満たされた、メッセージを処理します")
```

## 次に進む

- [一般的なタスクの例](common-tasks.md) - 学習する（メッセージ送信の高度な機能：リトライ/タイムアウト/バッチ）
- [プラットフォームの特性ガイド](../platform-guide/README.md) - Send DSLチェーン送信、送信ルール、バッチ構築の完全な説明
- [Eventラッパークラスの詳細](../developer-guide/modules/event-wrapper.md) - Eventオブジェクトの詳細を理解する
- [ユーザー使用ガイド](../user-guide/) - 設定とモジュール管理を理解する