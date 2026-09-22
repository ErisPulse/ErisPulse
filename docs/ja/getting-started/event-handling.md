# イベント処理入門

このガイドでは、ErisPulse における各種イベントの処理方法について説明します。

## イベントの種類概要

ErisPulse は以下のイベントの種類をサポートしています：

| イベントの種類 | 説明 | 適用場面 |
|---------|------|---------|
| メッセージイベント | ユーザーが送信する任意のメッセージ | チャットボット、コンテンツフィルタリング |
| コマンドイベント | コマンドプレフィックスで始まるメッセージ | コマンド処理、機能の入口 |
| 通知イベント | システム通知（友達追加、グループメンバー変更など） | メッセージの歓迎、ステータス通知 |
| 要求イベント | ユーザーの要求（友達リクエスト、グループ招待） | 要求の自動処理 |
| メタイベント | システムレベルのイベント（接続、ハートビート） | 接続監視、ステータスのチェック |

## メッセージイベントの処理

> **ヒント**: イベントハンドラで `Event` クラスの型注釈を使用することを推奨します。これにより、IDEの自動補完と型チェックがサポートされます。

```python
from ErisPulse.Core.Event import Event  # イベントの型注釈に使用するイベントのインポート
```

### すべてのメッセージを監視

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"{user_id} からのメッセージを受け取りました: {text}")
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

### ワイルドカードと正規表現による監視

`on_message` / `on_private_message` / `on_group_message` /
`on_at_message` の4つのメッセージデコレータは、`pattern`（globワイルドカード）と `regex`（正規表現）をサポートしています。一致しないメッセージは **ハンドラをトリガーしません**：

```python
# globワイルドカード：* 任意の文字列、? 1文字、[seq] 文字集合
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("签到成功")

# 正規表現：金額を一致させる
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"受け取った金額：{event.get_text()}")

# pattern と regex が両方指定された場合 → 両方一致する必要があります
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` はこの2つのパラメータもサポートしています（[待機返信機能](../developer-guide/modules/event-wrapper.md#待機返信機能)を参照）。

## コマンドイベントの処理

### 基本的なコマンド

```python
from ErisPulse.Core.Event import command

@command("help", help="ヘルプ情報を表示")
async def help_handler(event):
    help_text = """
利用可能なコマンド：
/help - ヘルプを表示
/ping - 接続をテスト
/info - 情報を表示
    """
    await event.reply(help_text)
```

### コマンドのエイリアス

```python
@command(["help", "h"], aliases=["帮助"], help="ヘルプ情報を表示")
async def help_handler(event):
    await event.reply("ヘルプ情報...")
```

ユーザーは以下のいずれかの方法で呼び出すことができます：
- `/help`
- `/h`
- `/帮助`

### コマンドの引数

```python
@command("echo", help="メッセージを繰り返す")
async def echo_handler(event):
    # コマンドの引数を取得
    args = event.get_command_args()
    
    if not args:
        await event.reply("繰り返すメッセージを入力してください")
    else:
        await event.reply(f"あなたが言った: {' '.join(args)}")
```

引数はユーザー入力のままの形式で保持されます（大文字小文字を無視するように設定しても、コマンド名の一致は大文字小文字を無視しますが、引数の内容には影響しません）。

### 宣言式引数とオプション（args= / options=）

手動で引数を解析するには、自分で型変換とエラーメッセージの提示を行う必要があります。`args=` / `options=` を宣言すると、フレームワークは権限チェックが通った後にコマンド引数を自動的に解析し、**名前でハンドラに注入**します。ユーザーの入力が間違っている場合は、自動的にローカライズされたエラーメッセージと使い方を表示し、例外が発生してクラッシュすることはありません。`/help <コマンド>` は自動的に使い方を表示します：

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

`args=` の位置引数の構文：`<count:int>` 必須、`[sides:int=6]` 任意（デフォルト値付き）。サポートされる型：

| 型 | 例 | 説明 |
|------|---------|------|
| `str` | `hello` | 文本（デフォルトの型） |
| `int` / `float` | `3` / `0.5` | 数値 |
| `bool` | `はい` / `yes` / `はい` / `да` / `true` / `no` / `取消` | ブール値、対話確認（`Event.confirm()`）の確認語の再利用 |
| `literal` | `<mode:literal=fast|slow>` | 列挙、指定された値のみ受け入れる；オプション形式ではデフォルトで最初の値を取る |
| `duration` | `90s`、`1h30m`、`1d` | 時間、秒に換算されたfloat |
| `rest` | `<text:rest>` | 残りのすべてのテキスト（最後に位置する必要があります） |

`options=` は辞書形式で宣言されます：キーはハンドラの引数名、値はフラグ形式（複数の別名は `/` で区切る）。注釈が `bool` のパラメータはブールフラグ（出現即 `True`）です；それ以外（デフォルトは `str`）は値付きオプションで、`--label hello` と `--label=hello` の両方の値の取り方が可能で、型はハンドラの注釈に従います。オプションは最初に識別されて除外され、残りのトークンは `args=` に従って解析されます（`rest` はオプションを除外した後の残りのテキストを覆います）。

**動作の要点**：

- 権限チェックは引数解析より先に行われます。権限のないユーザーはトリガーされません。
- 解析失敗（型が合わない / 必須パラメータが不足 / パラメータが多すぎる / 知らないオプション）は、自動的にローカライズされたエラーと使い方を返し、コマンドは認識されます。
- 宣言されたパラメータ名はハンドラの署名に存在しなければなりません。存在しない場合は登録時に `ValueError` を投げます。
- `args=` / `options=` を宣言しないコマンドは、動作が完全に変化しません（後方互換性）。

### コマンドの管理（cooldown= / rate_limit= / deprecated=）

手動でクールダウンの計時、リミットのウィンドウ、廃止のメッセージを宣言で置き換えることができます。これらは任意に組み合わせることができます。

**クールダウン**——時間の形式は `args=` の `duration` 型と同じです（例：`"30s"`、`"1h30m"`、`"1d"`）：

```python
@command("daily", cooldown="1d", cooldown_key="user", cooldown_reply="今日すでにサインインしました")
async def daily_handler(event):
    await event.reply("サインイン成功！")
```

**リミット**——スライディングウィンドウの宣言 `"回数/時間"`（例：`"5/minute"`、`"10/s"`、`"3/2m"`）：

```python
@command("search", rate_limit="5/minute", rate_limit_key="user")
async def search_handler(event):
    await event.reply("検索結果")
```

**廃止**——呼び出されたときに自動的に廃止のメッセージを返し、`deprecated_reject=True` で実行を拒否します：

```python
@command("oldcmd", deprecated="代わりに /newcmd を使用してください", deprecated_reject=True)
async def old_handler(event): ...
```

キーの粒度（`cooldown_key=` / `rate_limit_key=`）：`"user"`（デフォルト、同じユーザーが共有）、`"session"`（同じセッションが共有、同じグループのように）、`"global"`（すべてのユーザー、すべてのセッションが共有）。

**動作の要点**：

- クールダウン / リミットがヒットした場合、デフォルトでは**静かに破棄**されます（作用域に応じて静かに）；`cooldown_reply=` / `rate_limit_reply=` を宣言した場合、ヒットするとその文章を返します。
- コマンドがヒットした時点で認領されます——管理がヒットしたコマンドは、低優先度のメッセージハンドラに漏れることはありません。
- 管理の判定は、すべての権限チェックと引数解析が成功し、実際の実行の前にあります：権限のないユーザーはトリガーされず、引数のエラーは消費されません。
- クールダウンとリミットを同時に宣言した場合、クールダウンが先に判定されます（クールダウンがヒットした場合、リミットのウィンドウは占有されません）。
- `deprecated=` はデフォルトで返す文章を返した後**実行を継続**します；`deprecated_reject=True` で実行を拒否します（`command.executed` フックは `success=False, error="deprecated"` として記録されます）。
- `/help` のリストと単一コマンドのヘルプは、自動的に廃止のマークと文章を表示します。
- 状態はプロセス内のメモリ内にあり、モジュールのアンロード時に自動的にクリアされます。プロセス間の共有、リスタート後の永続化は含まれません。
- 宣言は登録時に検証されます（fail-fast）：構文が不正、キーの粒度がホワイトリストの値でない、replyが主宣言と併用されていない場合は `ValueError` を投げます。

### ハンドラのスロットリング（throttle=）とデバウンス（debounce=）

メッセージハンドラのスパム防止宣言——同じキーのイベントは、間隔内に1つだけ処理され、残りは静かに破棄されます：

```python
from ErisPulse import sdk

@sdk.message.on_message(throttle="2s", throttle_key="user")
async def handler(event): ...
```

デバウンスとスロットリングは補完的です：**ウィンドウ内では最後の1つだけ実行**され、前の待機中のタスクは自動的にキャンセルされます（検索の自動補完などの「入力停止後に処理する」場面に適しています）：

```python
@sdk.message.on_message(debounce="2s", debounce_key="user")
async def search(event): ...
```

`on_message` / `on_private_message` / `on_group_message` / `on_at_message` はすべてサポートしています；`throttle_key=` / `debounce_key=` はコマンド管理と同じキー粒度（user / session / global）で、時間の形式は `duration` と同じです。スロットリングと `pattern=` / `regex=` などの既存の条件は重複して有効になります（すべて満たす場合にのみトリガー）；間隔内に破棄されたものは TRACE ログに記録されます；宣言は登録時に検証されます；`throttle=` と `debounce=` は意味的に排他的です（両方宣言すると `ValueError` を投げます）。

### 依存注入（Depends）

共通の依存（データベースセッション、設定の読み取りなど）は依存関数として抽出できます。ハンドラは `Depends(依存関数)` としてデフォルト値を宣言し、フレームワークはイベントのコンテキストオブジェクトを使って依存関数を自動的に呼び出し、名前で注入します：

```python
from ErisPulse.Core import Depends

async def get_session(event):
    return await sdk.module.call("DB", "get_session")

@command("admin")
async def admin_handler(event, db=Depends(get_session)):
    ...
```

デフォルトでは**リクエストレベルのキャッシュ**が有効です：同じイベントの配信内では、同じ依存関数は1回だけ解析され、すべての注入ポイントで結果を共有します（`get_db` は1回のイベントで1回だけデータベースセッションを確立します）；リクエスト間では自動的に再利用されません。`Depends(get_db, use_cache=False)` で1つの依存のキャッシュを無効にできます。

フレームワークの注入ポイントをすべて上書きします——コマンドハンドラ、イベントハンドラ（`message.on_message()` など）、ライフサイクルフック（`sdk.lifecycle.on`）、SSEルートハンドラ。依存関数の最初の引数は注入ポイントのコンテキストオブジェクトです（イベントの場合は `Event`、ライフサイクルの場合はイベント `data`、ルートの場合は `HttpRequest` / `SseEmitter`）；同期と非同期の依存関数は宣言できます。

**他のモジュールのサービスを宣言する**（構文糖衣）：

```python
@command("query")
async def query_handler(event, session=Depends.module("DB", "get_session")):
    ...
```

`Depends.module(モジュール名, メソッド名, *固定引数)` は、依存関数内で `sdk.module.call(...)` を呼び出すのと同じです。モジュールのインスタンス化（`__init__`）は対象外です——インスタンス化の際にはコンテキストオブジェクトがありません。FastAPIが提供するHTTPルートは、FastAPIの元の `fastapi.Depends` を使用してください。

**動作の要点**：

- 宣言は登録時に検証されます（fail-fast）：依存が呼び出せない場合、または `args=` / `options=` のパラメータと重複する場合は `ValueError` を投げます。
- 依存関数が投げた例外とハンドラ自身の例外は、同口径で処理されます（コマンドは自動的にエラーを返します）。
- `Depends` を宣言しないハンドラはゼロオーバーヘッドです（配分時にリフレクションは一切ありません）。
- FastAPIが提供するHTTPルートは、FastAPIの元の `fastapi.Depends` を使用してください。

### コマンドグループ

```python
@command("admin.reload", group="admin", help="モジュールを再ロード")
async def reload_handler(event):
    await event.reply("モジュールが再ロードされました")

@command("admin.stop", group="admin", help="ロボットを停止")
async def stop_handler(event):
    await event.reply("ロボットが停止されました")
```

`group` パラメータはヘルプリストの分類にのみ使用されます。上記の例では `admin.reload` は**全体のコマンド名**です（ドットは命名スタイルであり、ユーザーは `/admin.reload` を入力する必要があります）。

### サブコマンド

コマンド名は**スペースで区切られた**複数のトークン形式をサポートし、`/admin add`、`/admin user ban` のようなサブコマンドを実現できます：

```python
@command("admin", help="管理コマンド")
async def admin_handler(event):
    await event.reply("使い方：/admin add | /admin remove")

@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    target = event.get_command_args()[0]
    await event.reply(f"追加しました: {target}")

@command("admin remove", aliases=["a remove"], help="管理者を削除")
async def admin_remove_handler(event):
    await event.reply("削除しました")
```

マッチングルール（**最長プレフィックスマッチ**）：

- `/admin add x` は `admin add` に優先的にマッチし、`event.get_command_args()` は `["x"]` を返します（サブコマンド名以降の引数）。
- `admin` だけが登録されている場合、`/admin add x` は `admin` にマッチし、`get_command_args()` は `["add", "x"]` を返します（過去の動作は変化しません）。
- 別名は複数トークン形式（`a remove`）もサポートし、単一トークンの別名（`a`）もサブコマンドに指定できます。
- 親子コマンドが同時に登録されている場合、登録されていないサブコマンドの入力（例：`/admin list x`）は親コマンドに降格します。

**権限継承**：サブコマンドが `permission` を宣言していない場合、自動的に親コマンドで最も最近権限を宣言した祖先コマンドを継承します——`/admin` を保護すれば、その下のすべてのサブコマンドも自動的に保護されます；サブコマンド自身が宣言した権限が優先されます：

```python
def is_admin(event):
    return event.get_user_id() in {"user123"}

@command("admin", permission=is_admin, help="管理コマンド")
async def admin_handler(event):
    ...

# permissionの宣言を繰り返す必要はありません、自動的にis_adminを継承します
@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    ...
```

注意：`master=True` と `hidden` **は継承されません**、必要に応じてサブコマンドで個別に宣言してください；ユーザーACL（ホワイトリスト/ブラックリスト）はコマンドの全名でマッチし、globルールは`"admin*"`のようにサブコマンド全体をカバーできます。

`/help`のコマンド一覧では、可視の親コマンドの下に自動的にインデントで表示されます（`admin` → `admin add`は1段階インデント、`admin user` → `admin user ban`は2段階インデント）。

### コマンドの権限とアクセス制御

コマンドの権限は3層に分かれ、上から下へ順に判定されます（**上層が拒否すると下層は見られません**）：

```python
# ① コマンドの権限ACL（ユーザー側の設定）：コマンドのユーザーのホワイトリスト/ブラックリスト、拒否時は「権限不足」を返す
# ② master=True —— フレームワークのオーナーのみ実行可能（フレームワークが自動的にチェック、拒否時は「権限不足」を返す）
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

**コマンドユーザーACL**（`ErisPulse.event.command.acl`）：ユーザーは任意のコマンドにユーザーのホワイトリスト/ブラックリストを設定できます。コマンド名は正確なマッチとglobパターン（例：`"roll*"`）をサポートし、拒否時は「権限不足」を返します：

```toml
# config.toml —— restartを実行できるのは123456のみ；666は一律拒否
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

判定順序：`deny`がヒット → 拒否；`allow`が空でヒットしない → 拒否；ACLが設定されていない場合は、`event.command.default_allow`（`false` = 严格モード、ACLがないと拒否；`true`の場合は開発者のデフォルト`master=True` / `permission`）に従います。実行時API（コマンド名はglobをサポート）：

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # 允許リスト
command.deny_user("restart", "onebot11", "666")       # 拒否リスト
command.remove_acl("restart")                          # ホワイトリスト/ブラックリストを削除
command.get_acl("restart")                             # 現在のリストを取得
```

> コマンドハンドラはイベントパッケージからインポートされます：`from ErisPulse.Core.Event import command`；`sdk.Event.command`（どちらも同一シングルトン）を経由してアクセスすることもできます。モジュール内では通常`from ErisPulse.Core.Event import command`でインポートされます。

コマンド間・ユーザー間の**イベントレベル**のアクセス制御（特定の人の、特定のグループの、特定のBotのメッセージを受け取るか）は**スコープのアイデンティティ次元**（`scope.identity`）で行います；**モジュールレベル**の可用性（どのモジュールが使えるか）は**スコープのモジュール次元**（`scope.platforms / bots / sessions`）で行います。
詳細は[スコープ（scope）](../advanced/scope.md)を参照してください。

> 建議：コマンド内部でビジネスロジックを連動させる場合は`master=True` / `permission`を使用してください；純粋にユーザー/グループのアクセス制御を行う場合はスコープのアイデンティティ次元を使用してください；モジュールの可用性を制御する場合はスコープのモジュール次元を使用してください。

### コマンドの優先度

```python
# 優先度の数値が大きいほど、実行が早くなります
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("高優先度のハンドラ")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("低優先度のハンドラ")
```

### 並列イベント処理

ErisPulseのイベントシステムは**同優先度は並列、異なる優先度は直列**のスケジューリングモデルを採用しています：

```
イベント到着
    ↓
priority=10 組: [ハンドラC || ハンドラD] 並列 → 結果を結合
    ↓ (中断されていない場合)
priority=0 組: [ハンドラA || ハンドラB] 並列 → 結果を結合
    ↓
...
```

- **同優先度の並列**：優先度が同じ複数のハンドラは同時に実行され、スループットが向上します
- **跨優先度の直列**：異なる優先度のグループは順番に実行されます（数値が大きいほど先に実行されます）、高優先度のハンドラが先に実行されるようにします
- **Copy-On-Write**：ハンドラが変更しない限りコピーを作成せず、ゼロオーバーヘッドを確保します
- **競合処理**：同優先度の複数のハンドラが同じフィールドを変更した場合、最後に変更された値を使用し、警告ログを記録します
- **中断機構**：任意のハンドラが `event.done()`（デフォルト）または `event.done(claim=False)` を呼び出した後、次の低優先度グループをスキップします。認領とブロックの違いは下記の[「リンク制御：認領とブロック」](#リンク制控認領とブロック)を参照してください。

```python
# 例：同優先度のハンドラが並列に実行される
@message.on_message(priority=0)
async def handler_a(event):
    # タスクAを処理
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # handler_a と並列に実行
    event['result_b'] = process_b()

# 異なる優先度で直列に実行される
@message.on_message(priority=10)
async def handler_c(event):
    # 一番優先度が高い、最初に実行される
    pass
```

> **並列上限**：すべてのマッチするハンドラのタスクは**即座に作成**されますが、シグナルマニュアルで**同時に実行中の数**を制限し、デフォルト上限は **64**（`ErisPulse.framework.handler_max_concurrency`、ホットアップデート可能）です。上限を超えたタスクはシグナルマニュアルで待ち、前のタスクが完了してから実行されます。イベントのピーク時には、これが「圧力緩和弁」になります。
>
> **遅いログ**：個々のハンドラが1秒以上かかった場合、フレームワークはログにWARNINGを出力します（`handler_slow`）。`wait_reply`の待機時間は処理時間から差し引かれるため、「相手の返信を待つ」ことで誤って遅いと判定されることはありません。

## ミドルウェア：配分前に変更または拒否

ミドルウェアはイベント配分**の前に**順序で実行され、ファイアウォール、リミット、イベントの脱敏などの正統的な実装ポイントです：

```python
from ErisPulse.Core import adapter

@adapter.middleware
async def firewall(data):
    if _is_banned(data.get("user_id")):
        return False          # 拒否：イベントは破棄され、どのハンドラにも渡されず、出力副作用もありません
    data["checked"] = True    # 戻り値がdict：イベントのペイロードを変更して配分を続ける
    # 戻り値がNone：配信を続ける、ペイロードは変更されない（過去の動作）
    return data
```

| 戻り値 | 行動 |
|--------|------|
| `False` | **拒否**：イベントは即座に破棄され、どのハンドラにも渡されません |
| `dict` | イベントのペイロードを変更して配分を続ける |
| `None` | 配信を続ける、ペイロードは変更されない |

拒否された場合、フレームワークはTRACEログを出力し、`adapter.event.blocked`ライフサイクルフックをトリガーします（ミドルウェア名と完全なイベントを含む）、イベントがなぜ応答しなかったかを監査するのに役立ちます。

## コマンド配分決定チェーン：なぜコマンドがトリガーされなかったのか

1つのコマンドメッセージは次のように経由します：**コマンドテキストの判定 → コマンド名/エイリアスの一致（一致しなかった場合はスペル補正付き）→ 一致したら認領 → スコープ → ユーザーACL → マスター → 権限 → クールダウン/リミット → 引数の解析 → 実行**。1つでも満たさないステップでは中止されます；管理がヒットした場合はデフォルトで静かに破棄され、権限系の拒否はユーザーに返信されます。

テスト中は `ErisPulse-Testing` の `dispatch()` がこの決定チェーンを直接返します（`DispatchTrace`、`trace.explain()` で逐行の因果を出力）、本番環境では `ErisPulse.Core.Event.start_dispatch_trace()` を使って同様の記録を収集できます。

また `ErisPulse.runtime` には2つの診断APIが用意されています：`explain_module(モジュール名)` は「モジュールがなぜロードされなかったのか」（未登録 / ラグジュアリーロード / 設定で無効 / 依存が不足 / SDKのバージョンが満たさない、順に原因を示す）、`explain_event(イベント)` は「イベントがなぜ応答しなかったのか」（アダプターが未登録 / アイデンティティがブラックリスト / モジュールセッションが遮断 / コマンドが一致しなかった）を回答します；`format_report()` で人間が読める結論をレンダリングできます。

## スコープフィルタリング：なぜ私のモジュールがメッセージを受け取らなかったのか

イベントが到着した後、2つの**静か**なフィルタがあります（どちらも返信せず、エラーも出ません）：

1. **アイデンティティ次元**（`ErisPulse.scope.identity`）：イベントが配分入口に到達するとき、ユーザー > グループ > Bot > アダプターの順に受け取るかどうか判定します。
   拒否された**イベント全体**は直接破棄され、どのハンドラ（コマンドディスパッチャを含む）もトリガーされません。
2. **モジュール次元**（`ErisPulse.scope`）：イベントが特定のモジュールのハンドラ/コマンドに到達するとき、セッション > Bot > プラットフォームの順にそのモジュールが利用可能かどうか判定し、**通過しない場合は静かにスキップ**します。

```toml
# 例1：あるグループのすべてのメッセージは伝播しない
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# 例2：MyModuleを特定のBotにブロック
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

この場合、そのグループのメッセージが到着したときに、`MyModule` のコマンドとイベントハンドラは**すべてスケジュールされません**。これはバグではなく、フィルタリング機構です——「モジュールが反応しない」ことを確認する際には、まずスコープのアイデンティティとモジュールのバインディングを確認してください。

- フィルタリングログは **TRACE** レベルでのみ表示されます（`core.scope.identity_denied` / `core.scope.denied`）、デフォルトの INFO では痕跡が見えません
- フレームワークレベルのハンドラ（コマンドディスパッチャ `scope_exempt=True`）は**モジュール次元**の影響を受けませんが、**アイデンティティ次元**の影響を受けます（イベント全体が破棄されているため）
- コマンド実行前に3番目のフィルタがあります：コマンドユーザーACL（拒否時は「権限不足」を返す、上記参照）
- 4番目のフィルタは**イベントオーバーライド**（下節参照）

> [!NOTE]
> **スコープフィルタリングとイベント認領（claim）の関係**：2つの静かのフィルタはハンドラの**スケジュール前**に発生します——フィルタでスキップされたハンドラは実行されず、当然認領状態も影響を受けません。イベントが認領されたかどうかは、**実行された**ハンドラ（コマンドが認領、返信が認領、明示的に呼び出された）によってのみ決定されます；スコープ拒否自体は認領もブロックもせず（静かにスキップし、メッセージは残りの配分チェーンを完了します）。

> スコープの設定、マッチングの構文、実行時APIは [スコープ（scope）](../../advanced/scope.md) を参照してください。

## イベントオーバーライド：モジュールのコードを変更せず、任意のイベントタイプの動作をオーバーライド

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要です。

イベントハンドラが登録時に宣言したパラメータ（`pattern` / `regex` / `master` / `hidden` など）は**開発者のデフォルト**にすぎません。統一されたオーバーライドシステムにより、ユーザーは**イベントタイプ**ごとに任意のモジュールの動作をオーバーライドできます——OneBot12標準タイプ（meta / message / notice / request）とErisPulse拡張タイプ（command）はそれぞれ独自のオーバーライド可能なパラメータを持ちます：

| イベントタイプ | オーバーライド可能なパラメータ | 作用 |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | テキストのトリガー条件 + メッセージのサブタイプホワイトリスト |
| `notice` | `detail_types` / `pattern` / `regex` | 通知のサブタイプホワイトリスト + テキスト条件 |
| `request` | `detail_types` / `pattern` / `regex` | リクエストのサブタイプホワイトリスト + テキスト条件 |
| `meta` | `detail_types` | メタイベントのサブタイプホワイトリスト（connect / heartbeat など） |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | コマンドの実装パラメータ（ユーザー優先） |
| `acl`（command専用） | `allow` / `deny` | コマンドのユーザーのホワイトリスト/ブラックリスト（コマンド名のglob） |

```toml
# message：テキストのトリガー条件をオーバーライド（コード内の条件とAND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice：特定の通知サブタイプのみ応答
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command：実装パラメータをオーバーライド（ユーザー優先——制限または開放可能）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl：コマンドのユーザーのホワイトリスト/ブラックリスト（コマンド名のglob）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACLのデフォルト（false = 严格モード：ACLがないと拒否）
acl_default_allow = true
```

実行時API（`from ErisPulse.Core.Event import overrides` または `sdk.Event.overrides`、**タイプのサブネームスペース**——各タイプごとに対称的な `set` / `get` / `delete` 3つの関数）：

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # messageのテキスト条件
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # コマンドのパラメータ
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # コマンドのユーザーのブラックリスト

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # 開発者のデフォルトに戻す
```

- オーバーライド条件とハンドラのコード内の条件は**同時に有効**（ANDの意味）；`command`のパラメータは開発者の宣言と**深くマージ**（オーバーライドが優先）
- `detail_types`：イベントに `detail_type` がない場合は通過（未知のイベントを誤って排除しない）
- `pattern` / `regex`：テキストのないイベント（connect / heartbeat など）は制約を受けず、直接通過
- `command`のオーバーライドのキー `master` は同期的にストアキー `must_master` にマッピングされます；コマンドを無効にするには `acl` deny を使用
- **キー名のマッピング説明**：`overrides.command.set("My", "restart", master=True)` のパラメータ名 `master` は設定の別名にすぎず、実際のストアキーと `get()` で返されるキー名は統一して **`must_master`** です（`get()` は `{"must_master": true}` を返します）——実行時に判定してストアキーを読み取るため、`master` キー名で読み取らないでください
- 設定は変更されると即座に有効（ホットアップデート）、形式の検証は警告（未知のパラメータ / 壊れた条目は無視）

## リンク制御：認領とブロック

> [!NOTE]
> `event.done()` / `event.mark_processed()` の `claim=` / `stop=` パラメータは ErisPulse **2.7.1+** が必要です。

ErisPulse は「認領」と「ブロック」という2つの正交的な意味を解き、`event.done()` で統一的に制御することで、コマンド処理の周囲にログ、監査、権限などの観察層を重ねることができます。

**2つの概念の正確な定義**：

- **認領（claim）**：イベントがこのハンドラによって処理されたことをマークします（`_processed` に書き込み）。コマンドディスパッチャは認領されたイベントを見ると**重複を避ける**——同じメッセージが複数のコマンドハンドラに重複して処理されないようにします。典型的な場面：コマンドがマッチした後に認領し、コマンドディスパッチャが介入しないようにします。
- **ブロック（stop）**：イベントが**より低い優先度**のハンドラに伝播しないようにします（`_propagation_stopped` に書き込み）。より低い優先度のハンドラはこのイベントを見ません。典型的な場面：高優先度のハンドラがイベントを完全に処理した後、より低い優先度のハンドラが実行されないようにします。

| `event.done(...)` | 認領 | ブロック | 場面 |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | コマンド / ハンドラ処理完了の標準的なやり方 |
| `event.done(stop=False)` | ✔ | ✘ | 認領のみ、低優先度の観測者（ログ / 統計）は引き続き見る |
| `event.done(claim=False)` | ✘ | ✔ | ブロックのみ（ファイアウォール / リミット）、認領は行わない |

`event.done(claim=, stop=)` は `event.mark_processed(claim=, stop=)` の別名で、パラメータと動作は完全に等価です。

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
        event.done(claim=False)  # ブロックのみ：低優先度は実行されないが、認領は行わない
```

### コマンドと返信の block 設定

**コマンドがマッチしたら認領**：メッセージが登録されたコマンド名（サブコマンド/エイリアスも含む）にマッチした瞬間、権限やアクセス制御の判定結果に関わらず、認領され、デフォルトでブロックが伝播されます——権限拒否されたコマンドは低優先度のメッセージハンドラに漏れることはありません（「コマンドが拒否された後に on_message がもう一度反応する」ような二重反応を防ぎます）。

`block` を設定することで、低優先度の観測者（ログ / 監査 / 権限）がこれらのメッセージを見られるようにすることができます：

```toml
[ErisPulse.event.command]
block = false   # コマンドメッセージは低優先度のハンドラに伝播し続ける（認領は影響を受けない、重複消費されない）

[ErisPulse.event.wait_reply]
block = false   # wait_reply で消費された返信は低優先度のハンドラに伝播し続ける
```

> 注意：`block` は**ブロック**（stop）を制御するだけで、**認領**（claim）には影響しません——マッチしたコマンドは決してメッセージハンドラに重複消費されることはありません；コマンドにマッチしないメッセージは通常通りメッセージハンドラに伝播します。

## 通知イベントの処理

### フレンド追加

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

### フレンドリクエスト

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"收到好友请求: {user_id}, 附言: {comment}")
    
    # 适配器 API でリクエストを処理することができる
    # 具体的な実装は各适配器のドキュメントを参照してください
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

適配器が meta イベントを送信した後、フレームワークは自動的に Bot 状態を追跡し、いつでも照会できます：

```python
from ErisPulse import sdk

# 某個 Bot がオンラインかどうかを確認
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot 在线")

# 現在のすべてのオンライン Bot をリストアップ
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# 完全な状態のサマリーを取得
summary = sdk.adapter.get_status_summary()
```

## 交互処理

### reply メソッドを使用して返信を送信

`event.reply()` メソッドは、@、返信などの機能をサポートするさまざまな修飾パラメータを提供します：

```python
# 簡単な返信
await event.reply("你好")

# 異なるタイプのメッセージを送信
await event.reply("http://example.com/image.jpg", method="Image")  # 画像
await event.reply("http://example.com/voice.mp3", method="Voice")  # 音声

# @1人
await event.reply("你好", at_users=["user123"])

# @複数人
await event.reply("大家好", at_users=["user1", "user2", "user3"])

# 返信
await event.reply("回复内容", reply_to="msg_id")

# @全員
await event.reply("公告", at_all=True)

# 組み合わせ：@ユーザー + 返信メッセージ
await event.reply("内容", at_users=["user1"], reply_to="msg_id")
```

### ユーザーの返信を待つ

```python
@command("ask", help="询问用户")
async def ask_handler(event):
    await event.reply("请输入你的名字:")
    
    # ユーザーの返信を待つ、タイムアウト時間 30 秒
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")
    else:
        await event.reply("等待超时，请重新输入。")
```

> [!TIP]
> **待機中もコマンドは使用可能**（2.8.3+）：コマンドプレフィックスで始まり、登録されたコマンドに一致するメッセージ（例：`/cancel`）は**コマンドとして実行**され、返信として扱われず、待機は継続します——ユーザーはいつでもキャンセル/切り替えでき、コマンド実行後も返信を続けることができます。旧来の「すべてのテキストを吸収する」挙動が必要な場合は：設定 `ErisPulse.event.wait_reply.cmdpass = true`、または単回 `wait_reply(cmdpass=True)`。

### 運転確認付きの待機返信

```python
@command("age", help="询问年龄")
async def age_handler(event):
    def validate_age(event_data):
        """年齢が有効かどうかを確認"""
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

### 確認対話 (confirm)

ユーザーの確認または否定を待つ、自動的に組み込みの中英文確認語を認識します：

```python
@command("confirm", help="确认操作")
async def confirm_handler(event):
    if await event.confirm("确定要执行此操作吗？"):
        await event.reply("已确认，执行中...")
    else:
        await event.reply("已取消")

# 自定義確認語
if await event.confirm("继续吗？", yes_words={"go", "继续"}, no_words={"stop", "停止"}):
    pass
```

### 選択メニュー (choose)

ユーザーは選択番号または選択項目を返信できます：

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

**マージモード**：`merge_prompt=True` の場合、オプションをプロンプトに統合し、指定された `method` で1つのメッセージとして送信します：

```python
# Markdown でプロンプトとオプションをマージして送信
choice = await event.choose(
    "## 请选择颜色\n{options}\n请回复编号",
    ["红色", "绿色", "蓝色"],
    method="Markdown",
    merge_prompt=True,
)
```

> `{options}` はオプションの挿入位置を制御します；記述しない場合はプロンプトの末尾に追加されます。
> `placeholder` パラメータでカスタムプレースホルダを指定できます（例：`placeholder="[choices]"`）。
> `options_format="auto"`（デフォルト）は、`method` に応じて自動的にスタイルを選択します：Markdown→箇条書き、Html→番号付きリスト、その他→テキストリスト。
> テキスト系メソッド（Text/Markdown/Htmlなど）はデフォルトでオプションを末尾にマージします；非テキスト系メソッド（Imageなど）はデフォルトで2つのメッセージに分割します。

### フォーム収集 (collect)

複数ステップでユーザー入力を収集します：

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

特定の条件を満たす任意のイベントを待つ、同一ユーザーに限定されない：

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

### マルチラウンド対話 (conversation)

インタラクティブなマルチラウンド対話コンテキストを作成します：

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

### 組み込みの確認語

ErisPulse には中英文の確認語の集合が組み込まれています：

- **確認語** (`CONFIRM_YES_WORDS`): 是、yes、y、确认、确定、好、好的、ok、true、对、嗯、行、同意、没问题...
- **否定語** (`CONFIRM_NO_WORDS`): 否、no、n、取消、不、不要、不行、cancel、false、错、拒绝、不可以...

## イベントデータのアクセス

### Event オブジェクトの一般的なメソッド

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

ビルトインメソッドに加えて、各プラットフォームアダプターはプラットフォーム固有のメソッドを登録し、プラットフォーム固有のデータに簡単にアクセスできます。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # プラットフォームに応じて固有メソッドを呼び出す
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram固有メソッド
    elif platform == "email":
        subject = event.get_subject()           # メール固有メソッド
```

プラットフォームが特定のメソッドを登録しているかどうかを確認するには、各プラットフォームが登録したメソッドを確認できます：

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> 各プラットフォームが登録した固有メソッドは、対応する[プラットフォームのドキュメント](../platform-guide/)を参照してください。

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

### 2. ログの記録

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"メッセージを処理: {user_id} - {text}")
    
    # モジュール独自のログを使用
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
    
    await event.reply("条件が満たされ、メッセージを処理します")
```

## 次に進む

- [よくあるタスクの例](common-tasks.md) - 消息送信の高度な機能（リトライ/タイムアウト/バッチ）を含む、よく使用される機能の実装を学ぶ
- [プラットフォームの特性ガイド](../platform-guide/README.md) - Send DSLチェーン送信、送信ルール、バッチ構築の完全な説明
- [Event包装クラスの詳細](../developer-guide/modules/event-wrapper.md) - Eventオブジェクトの詳細な理解
- [ユーザー使用ガイド](../user-guide/) - 設定とモジュール管理の理解