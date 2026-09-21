# イベント処理入門

このガイドでは、ErisPulseにおける各種イベントの処理方法について説明します。

## イベントタイプ概要

ErisPulseは以下のイベントタイプをサポートしています：

| イベントタイプ | 説明 | 適用場面 |
|---------|------|---------|
| メッセージイベント | ユーザーが送信したすべてのメッセージ | チャットボット、コンテンツフィルタ |
| コマンドイベント | コマンド接頭辞で始まるメッセージ | コマンド処理、機能の入口 |
| 通知イベント | システム通知（友達追加、グループメンバー変更など） | メッセージの歓迎、ステータス通知 |
| 要求イベント | ユーザーの要求（友達要求、グループ招待） | 要求の自動処理 |
| 元イベント | システムレベルのイベント（接続、ハートビート） | 接続監視、ステータスチェック |

## メッセージイベント処理

> **ヒント**: イベントハンドラで `Event` タイプ注釈を使用することを推奨します。これにより、IDEの自動補完と型チェックがサポートされます。

```python
from ErisPulse.Core.Event import Event  # 注釈に使用するイベントタイプをインポート
```

### すべてのメッセージを監視

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"{user_id}からメッセージを受け取りました: {text}")
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
    await event.reply(f"あなたは以下のユーザーを@しました: {mentions}")
```

### ワイルドカードと正規表現による監視

4つのメッセージデコレータ（`on_message` / `on_private_message` / `on_group_message` / `on_at_message`）は、`pattern`（globワイルドカード）と`regex`（正規表現）をサポートしています。一致しないメッセージは**ハンドラをトリガーしません**。

```python
# globワイルドカード：* 任意の文字列、? 単一文字、[seq] 文字集合
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("签到成功")

# 正規表現：金額をマッチ
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"金額を受け取りました: {event.get_text()}")

# pattern と regex 両方指定 → 両方ともマッチする必要がある
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` はこの2つのパラメータもサポートしています（[返信待ち機能](../developer-guide/modules/event-wrapper.md#返信待ち機能)を参照）。

## コマンドイベント処理

### 基本コマンド

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

### コマンド引数

```python
@command("echo", help="メッセージを繰り返す")
async def echo_handler(event):
    # コマンド引数を取得
    args = event.get_command_args()
    
    if not args:
        await event.reply("繰り返したいメッセージを入力してください")
    else:
        await event.reply(f"あなたが言った: {' '.join(args)}")
```

引数は、大文字小文字が無視されるように設定しても、コマンド名のマッチングは大文字小文字を無視しますが、引数の内容には影響しません。

### 宣言的引数とオプション（args= / options=）

手動で引数を解析するには、自分で型変換とエラーメッセージの提示を行う必要があります。`args=` / `options=` を宣言すると、フレームワークは権限チェックが通った後にコマンド引数を自動的に解析し、**名前付きでハンドラに注入**します。ユーザーの入力が間違っている場合、エラーメッセージと使い方が自動的に返信されます（例外がスローされてクラッシュすることはありません）。`/help <コマンド>` は、使い方を自動的に表示します：

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

`args=` 位置引数の構文：`<count:int>` 必須、`[sides:int=6]` オプション（デフォルト値付き）。サポートされる型：

| 型 | 入力例 | 説明 |
|------|---------|------|
| `str` | `hello` | 文字列（デフォルト型） |
| `int` / `float` | `3` / `0.5` | 数値 |
| `bool` | `はい` / `yes` / `はい` / `да` / `true` / `no` / `取消` | ブール値、イベント確認（Event.confirm()）の確認語表を再利用 |
| `literal` | `<mode:literal=fast|slow>` | 列挙、指定された値のみを受け入れる；オプション形式はデフォルトで最初のものを取る |
| `duration` | `90s`、`1h30m`、`1d` | 時間、秒に換算してfloatで |
| `rest` | `<text:rest>` | 残りのすべてのテキスト（最後に来ること） |

`options=` は辞書形式で宣言：キーはハンドラの引数名、値はフラグ形式（複数のエイリアスは `/` で区切る）。`bool` 注釈のパラメータはブールフラグ（存在すれば `True`）；それ以外（デフォルトは `str`）は値付きオプションで、`--label hello` と `--label=hello` の両方の値をサポートし、型はハンドラの注釈に従います。オプションは最初に認識されて除外され、残りのトークンは `args=` で解析されます（`rest` はオプションを除外した後の残りのテキストをカバーします）。

**動作の要点**：

- 権限チェックは引数解析より先に実行されるため、権限のないユーザーは解析がトリガーされない
- 解析失敗（型が合わない / 引数が足りない / 引数が多すぎる / 未知のオプション）は、ローカライズされたエラーメッセージと使い方を自動的に返信し、コマンドは認領される
- 宣言された引数名はハンドラの署名に存在しなければならない。そうでなければ登録時に `ValueError` をスロー
- `args=` / `options=` を宣言しないコマンドは、動作が完全に変化しない（後方互換性）

### コマンドの管理（cooldown= / rate_limit= / deprecated=）

手動でクールダウン、レート制限、廃止のメッセージを宣言で置き換えることができます。これらは任意に組み合わせることができます。

**クールダウン**——時間の形式は `args=` の `duration` 型と同じ（例：`"30s"`、`"1h30m"`、`"1d"`）：

```python
@command("daily", cooldown="1d", cooldown_key="user", cooldown_reply="今日すでにサインインしました")
async def daily_handler(event):
    await event.reply("サインイン成功！")
```

**レート制限**——スライディングウィンドウの宣言は `"回数/時間"`（例：`"5/minute"`、`"10/s"`、`"3/2m"`）：

```python
@command("search", rate_limit="5/minute", rate_limit_key="user")
async def search_handler(event):
    await event.reply("検索結果")
```

**廃止**——呼び出すと自動的に廃止の文を返し、`deprecated_reject=True` で実行を拒否：

```python
@command("oldcmd", deprecated="新しいコマンド /newcmd を使用してください", deprecated_reject=True)
async def old_handler(event): ...
```

キーの粒度（`cooldown_key=` / `rate_limit_key=`）：`"user"`（デフォルト、同じユーザーで共有）、`"session"`（同じセッションで共有、同じグループ）、`"global"`（すべてのユーザー、すべてのセッションで共有）。

**動作の要点**：

- クールダウン / レート制限がヒットした場合、**静かにドロップ**（作用域に応じて静かに）；`cooldown_reply=` / `rate_limit_reply=` を宣言した場合、ヒットするとその文を返す
- コマンドがヒットした時点で認領される——管理がヒットしたコマンドは、低優先度のメッセージハンドラに漏れることはない
- 管理判定はすべての権限チェックと引数解析が完了し、実行前に実行される：権限のないユーザーはトリガーされず、引数エラーは消費されない
- クールダウンとレート制限を同時に宣言した場合、クールダウンが先に判定される（クールダウンがヒットしてもレート制限のウィンドウには占めない）
- `deprecated=` はデフォルトで返信文を返した後、**実行を続ける**；`deprecated_reject=True` で実行を拒否（`command.executed` フックは `success=False, error="deprecated"` と記録）
- `/help` のリストと単一コマンドのヘルプは、廃止のマークと文を自動的に表示
- 状態はプロセス内メモリーで、モジュールのアンロード時に自動的にクリアされる；プロセス間の共有 / 再起動時の永続化は対象外
- 宣言は登録時に検証される（fail-fast）：構文が不正、キーの粒度がホワイトリストの値でない、reply が主宣言と併用されていない場合は `ValueError` をスロー

### ハンドラのスロットリング（throttle=）

メッセージハンドラのスパム防止宣言——同じキーのイベントは間隔内に1つだけ処理され、それ以外は静かにドロップされる：

```python
from ErisPulse import sdk

@sdk.message.on_message(throttle="2s", throttle_key="user")
async def handler(event): ...
```

`on_message` / `on_private_message` / `on_group_message` / `on_at_message` はすべてサポートしている。`throttle_key=` はコマンド管理と同じキー粒度（user / session / global）で、時間の形式は `duration` と同じ。スロットリングは `pattern=` / `regex=` などの既存の条件と重複して有効になる（すべて満たす場合にのみトリガー）。間隔内にドロップされたメッセージは TRACE ログに記録されるだけ。宣言は登録時に検証される。

### 依存注入（Depends）

共通の依存（データベースセッション、設定の読み取りなど）は依存関数として抽出でき、ハンドラは `Depends(依存関数)` をデフォルト値として宣言することで、フレームワークがコンテキストオブジェクトを使って依存関数を呼び出し、名前で注入する：

```python
from ErisPulse.Core import Depends

async def get_session(event):
    return await sdk.module.call("DB", "get_session")

@command("admin")
async def admin_handler(event, db=Depends(get_session)):
    ...
```

デフォルトで**リクエストレベルのキャッシュ**が有効：1回のイベント配信内では、同じ依存関数は1回だけ解析され、すべての注入ポイントで結果を共有する（`get_db` は1回のイベントで1回だけデータベースセッションを確立）。リクエスト間で自動的に再利用されない。`Depends(get_db, use_cache=False)` で個々の依存のキャッシュを無効にすることもできる。

フレームワークのすべての注入ポイントをカバー：コマンドハンドラ、イベントハンドラ（`message.on_message()` など）、ライフサイクルフック（`sdk.lifecycle.on`）、SSEルートハンドラ。依存関数の最初の引数は注入ポイントのコンテキストオブジェクト（イベントの場合は `Event`、ライフサイクルの場合はイベント `data`、ルートの場合は `HttpRequest` / `SseEmitter`）である。同期と非同期の依存関数の両方を宣言できる。

**他のモジュールのサービスを宣言する**（シンタックスシュガー）：

```python
@command("query")
async def query_handler(event, session=Depends.module("DB", "get_session")):
    ...
```

`Depends.module(モジュール名, メソッド名, *固定引数)` は、依存関数内で `sdk.module.call(...)` を呼び出すのと同じです。モジュールのインスタンス化（`__init__`）は対象外です——インスタンス化の際にはコンテキストオブジェクトがありません。FastAPIが提供するHTTPルートは、FastAPIの元の `fastapi.Depends` を使用してください。

**動作の要点**：

- 宣言は登録時に検証される（fail-fast）：依存が呼び出せない、または `args=` / `options=` の引数と重複している場合は `ValueError` をスロー
- 依存関数がスローする例外とハンドラ自身の例外は、同口径で処理される（コマンドはエラーを自動的に返信）
- `Depends` を宣言しないハンドラはゼロオーバーヘッド（配信時にリフレクションなし）
- FastAPIが提供するHTTPルートは、FastAPIの元の `fastapi.Depends` を使用してください

### コマンドグループ

```python
@command("admin.reload", group="admin", help="モジュールを再読み込み")
async def reload_handler(event):
    await event.reply("モジュールを再読み込みしました")

@command("admin.stop", group="admin", help="ロボットを停止")
async def stop_handler(event):
    await event.reply("ロボットを停止しました")
```

`group` パラメータはヘルプリストでの分類用にのみ使用されます。上記の例では `admin.reload` は**1つの全体のコマンド名**です（ドットは命名スタイルであり、ユーザーは `/admin.reload` を入力する必要があります）。

### サブコマンド

コマンド名は**スペースで区切られた複数のトークン形式**をサポートし、`/admin add`、`/admin user ban` などのサブコマンドを実現します：

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

マッチングルール（**最長接頭辞マッチ**）：

- `/admin add x` は `admin add` に優先的にマッチし、`event.get_command_args()` は `["x"]`（サブコマンド名の後の引数）を返す
- `admin` だけが登録されている場合、`/admin add x` は `admin` にマッチし、`get_command_args()` は `["add", "x"]`（歴史的な動作）を返す
- 別名は複数トークン形式（例：`a remove`）をサポートし、単一トークン別名（例：`a`）もサブコマンドを指すことができる
- 親コマンドと子コマンドが同時に登録されている場合、未登録の子コマンドの入力（例：`/admin list x`）は親コマンドに降格する

**権限継承**：子コマンドが `permission` を宣言していない場合、自動的に親チェーンで最近宣言された祖先コマンドの権限を継承する——`/admin` を保護すれば、その下のすべての子コマンドも自動的に保護される；子コマンド自身が宣言した権限が優先される：

```python
def is_admin(event):
    return event.get_user_id() in {"user123"}

@command("admin", permission=is_admin, help="管理コマンド")
async def admin_handler(event):
    ...

# permission を再宣言する必要はない、自動的に is_admin を継承
@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    ...
```

注意：`master=True` と `hidden` **は継承されない**、必要に応じて子コマンドで個別に宣言する必要がある；ユーザーアクセス制御（ホワイトリスト/ブラックリスト）はコマンドのフルネームでマッチし、globルールは `"admin*"` など、一括で子コマンドをカバーできる。

`/help` のコマンド一覧では、子コマンドは可視の親コマンドの下にインデント表示される（`admin` → `admin add` は1段階インデント、`admin user` → `admin user ban` は2段階インデント）。

### コマンドの権限とアクセス制御

コマンドの権限は3層に分かれ、上から下へ順に判定される（**上層が拒否すれば下層は見ない**）：

```python
# ① コマンド権限 ACL（ユーザー側の設定）：コマンドのユーザーのホワイトリスト/ブラックリストで、拒否時は「権限不足」を返す
# ② master=True —— フレームワークのオーナーのみ実行可能（フレームワークが自動的にチェックし、拒否時は「権限不足」を返す）
@command("restart", master=True, help="モジュールを再起動")
async def restart_handler(event):
    await event.reply("モジュールを再起動しました")

# ③ permission=呼び出し関数 —— コマンド自身の制御ロジック（Trueを返す場合に実行）
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="管理パネル")
async def panel_handler(event):
    await event.reply("管理パネルへようこそ")
```

**コマンドユーザー ACL**（`ErisPulse.event.command.acl`）：ユーザーは任意のコマンドにユーザーのホワイトリスト/ブラックリストを設定でき、コマンド名は正確なマッチと glob モード（例：`"roll*"`）をサポートし、拒否時は「権限不足」を返す：

```toml
# config.toml —— restart は 123456 だけを許可、666 は一律拒否
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

判定の順序：`deny` がヒット → 拒否；`allow` が空でヒットしない → 拒否；ACL の設定がない場合は、`event.command.default_allow`（`false` = 严格的モード、ACL がないと拒否；`true` の場合、開発者のデフォルト `master=True` / `permission` に任せる）に従う。実行時 API（コマンド名は glob をサポート）：

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # 許可リスト
command.deny_user("restart", "onebot11", "666")       # 拒否リスト
command.remove_acl("restart")                          # ホワイトリスト/ブラックリストを削除
command.get_acl("restart")                             # 現在のリストを取得
```

> コマンドハンドラはイベントパッケージからインポート：`from ErisPulse.Core.Event import command`；SDK イベントパッケージからもアクセス可能：`sdk.Event.command`（どちらも同一のシングルトン）。
> モジュール内では通常 `from ErisPulse.Core.Event import command` でインポートされている（コマンドデコレータから）。

コマンド/ユーザー間の**イベントレベル**のアクセス制御（特定の人の/グループの/ Bot のメッセージを受け取るかどうか）は、スコープの**アイデンティティ次元**（`scope.identity`）で行う；**モジュールレベル**の可用性（どのモジュールが使えるか）は、スコープの**モジュール次元**（`scope.platforms / bots / sessions`）で行う。
[スコープ（scope）](../advanced/scope.md)を参照。

> 建議：コマンド内部でビジネスロジックを連動させる場合は `master=True` / `permission` を使用；ユーザー/グループごとのアクセス制御は、スコープのアイデンティティ次元を使用；モジュールの可用性を制御する場合は、スコープのモジュール次元を使用。

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

ErisPulseのイベントシステムは**同優先度は並列、異なる優先度は直列**のスケジューリングモデルを採用しています：

```
イベント到着
    ↓
priority=10 組: [ハンドラC || ハンドラD] 並列 → 結果をマージ
    ↓ (中断されていない場合)
priority=0 組: [ハンドラA || ハンドラB] 並列 → 結果をマージ
    ↓
...
```

- **同優先度並列**：優先度が同じ複数のハンドラは同時に実行され、スループットが向上
- **跨級直列**：異なる優先度のグループは順番に実行される（数値が大きいほど先に実行）、高優先度ハンドラが先に実行されるように保証
- **Copy-On-Write**：ハンドラが変更しない場合はコピーを作成せず、ゼロオーバーヘッドを確保
- **競合処理**：同優先度の複数のハンドラが同じフィールドを変更した場合、最後に変更された値を使用し、警告ログを記録
- **中断メカニズム**：任意のハンドラが `event.done()`（デフォルト）または `event.done(claim=False)` を呼び出した後、以降の低優先度グループをジャンプ。認領とブロックの違いは、以下の[「リンク制御：認領とブロック」](#リンク制御認領とブロック)を参照

```python
# 例：同優先度ハンドラが並列実行
@message.on_message(priority=0)
async def handler_a(event):
    # 作業Aの処理
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # handler_a と並列に実行
    event['result_b'] = process_b()

# 異なる優先度で直列実行
@message.on_message(priority=10)
async def handler_c(event):
    # 優先度が最も高く、最初に実行される
    pass
```

> **並列上限**：すべてのマッチするハンドラのタスクは**即座に作成**されるが、シグナルマニュアルで制限された**同時実行数**（デフォルト上限 **64**、`ErisPulse.framework.handler_max_concurrency`、ホットアップデート可能）で実行される。上限を超えたタスクはシグナルマニュアル上で待ち、前のタスクが完了してから実行される。イベントの洪水時に、これが「圧力制御弁」になる。
>
> **遅いログ**：個々のハンドラが1秒以上かかる場合、フレームワークはログにWARNINGを出力（`handler_slow`）。`wait_reply` の待機時間は処理時間から差し引かれるため、「返信を待つ」ことで誤って遅いと判定されることはない。

## ミドルウェア：配信前の変更または拒否

ミドルウェアはイベント配信**前**に順番に実行され、ファイアウォール、リミット、イベントの脱敏などの正規の実装ポイントです：

```python
from ErisPulse.Core import adapter

@adapter.middleware
async def firewall(data):
    if _is_banned(data.get("user_id")):
        return False          # 拒否：イベントはドロップされ、どのハンドラにも渡されず、出力副作用もない
    data["checked"] = True    # 戻り値が dict の場合：イベントの負荷を変更して配信を続ける
    # 戻り値が None の場合：配信を許可、負荷は変更されない（歴史的な動作）
    return data
```

| 戻り値 | 行動 |
|--------|------|
| `False` | **拒否**：イベントは即座にドロップされ、どのハンドラにも渡されない |
| `dict` | イベントの負荷を変更して配信を続ける |
| `None` | 配信を許可、負荷は変更されない |

拒否された場合、フレームワークは TRACE ログを出力し、`adapter.event.blocked` のライフサイクルフックをトリガー（ミドルウェア名と完全なイベントを含む）、イベントがなぜレスポンスしなかったかを監査する。

## コマンド配分の決定チェーン：なぜコマンドがトリガーされないのか

コマンドメッセージは次のように処理されます：**コマンドテキストの判定 → コマンド名/エイリアスの一致（一致しなかった場合はスペル補正付き）→ 一致したら認領 → スコープ → ユーザー ACL → オーナー → 権限 → クールダウン/レート制限 → 引数の解析 → 実行**。途中で1つでも条件を満たさない場合は処理が停止します。制限がヒットした場合、デフォルトでは**静かにドロップ**（対称的な静かさ）；権限系の拒否はユーザーに返信します。

テスト中、`ErisPulse-Testing` の `dispatch()` はこの決定チェーンを直接返します（`DispatchTrace`、`trace.explain()` で1行ずつ因果を出力）、プロダクション環境では `ErisPulse.Core.Event.start_dispatch_trace()` を使って同様の記録を収集できます。

## スコープフィルタリング：なぜ私のモジュールがメッセージを受け取らないのか

イベントが到着した後、2つの**静かな**フィルタがあります（どちらも返信せず、エラーも出ません）：

1. **アイデンティティ次元**（`ErisPulse.scope.identity`）：イベントが配分エントリに到着した時点で、ユーザー > グループ > Bot > アダプターの順に判定され、受け取るかどうかが決まります。
   拒否された**イベント全体**は直接ドロップされ、どのハンドラ（コマンドディスパッチャーを含む）もトリガーされません。
2. **モジュール次元**（`ErisPulse.scope`）：イベントが特定のモジュールのハンドラ/コマンドに到着した時点で、セッション > Bot > プラットフォームの順に判定され、
   そのモジュールが利用可能かどうかが決まり、**通過しない場合は静かにスキップ**されます。

```toml
# 例1：特定のグループのすべてのメッセージを伝播しないようにする
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# 例2：MyModuleを特定のBotにブロックする
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

この場合、そのグループのメッセージが到着したときに、`MyModule` のコマンドとイベントハンドラは**すべてスケジュールされない**。これはバグではなく、フィルタリング機構です——「モジュールが反応しない」の原因を調査する際には、まずスコープのアイデンティティとモジュールのバインディングを確認してください。

- フィルタリングログは **TRACE** レベルでのみ表示される（`core.scope.identity_denied` / `core.scope.denied`）、デフォルトの INFO では痕跡が見えない
- フレームワークレベルのハンドラ（コマンドディスパッチャー `scope_exempt=True`）は**モジュール次元**の影響を受けないが、**アイデンティティ次元**の影響を受ける（イベント全体がドロップされている）
- コマンド実行前に3つ目のフィルタがある：コマンドユーザー ACL（拒否時は「権限不足」を返す、上節参照）
- 4つ目のフィルタは**イベント上書き**（下節参照）

> [!NOTE]
> **スコープフィルタリングとイベント認領（claim）の関係**：2つの静かなフィルタはハンドラの**スケジューリング前**に発生する——フィルタでスキップされたハンドラは実行されず、当然認領状態にも関与しない。イベントが認領されたかどうかは、**実行された**ハンドラ（コマンドが認領された、返信が認領された、明示的に呼び出された）によってのみ決定される；スコープ拒否自体は認領もブロックもしない（静かにスキップされ、メッセージは分発チェーンを完了する）。

> スコープ設定、マッチングの構文、実行時 API は [スコープ（scope）](../../advanced/scope.md) を参照。

## イベント上書き：モジュールのコードを変更せずに、任意のイベントタイプの動作を上書き

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要です。

イベントハンドラが登録時に宣言したパラメータ（`pattern` / `regex` / `master` / `hidden` など）は**開発者のデフォルト**にすぎません。一貫した上書きシステムにより、ユーザーは**イベントタイプ**ごとに任意のモジュールの動作を上書きできます——OneBot12標準タイプ（meta / message / notice / request）とErisPulse拡張タイプ（command）はそれぞれ独自の上書き可能なパラメータを持ちます：

| イベントタイプ | 上書き可能なパラメータ | 作用 |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | テキストのトリガー条件 + メッセージのサブタイプホワイトリスト |
| `notice` | `detail_types` / `pattern` / `regex` | 通知のサブタイプホワイトリスト + テキスト条件 |
| `request` | `detail_types` / `pattern` / `regex` | リクエストのサブタイプホワイトリスト + テキスト条件 |
| `meta` | `detail_types` | メタイベントのサブタイプホワイトリスト（connect / heartbeat など） |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | コマンドの実装パラメータ（ユーザーの優先） |
| `acl`（command専用） | `allow` / `deny` | コマンドのユーザーのホワイトリスト/ブラックリスト（コマンド名 glob） |

```toml
# message：テキストのトリガー条件を上書き（コード内の条件とAND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice：特定の通知サブタイプのみを応答
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command：実装パラメータを上書き（ユーザーの優先——可縮小または開放）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl：コマンドのユーザーのホワイトリスト/ブラックリスト（コマンド名 glob）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACLのデフォルト（false = 严格的モード：ACLがないと拒否）
acl_default_allow = true
```

実行時 API（`from ErisPulse.Core.Event import overrides` または `sdk.Event.overrides`，
**タイプのサブネームスペース**——各タイプごとに対称的な `set` / `get` / `delete` 三件套）：

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # messageのテキスト条件
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # コマンドのパラメータ
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # コマンドのユーザーのブラックリスト

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # 開発者のデフォルトに戻す
```

- 上書き条件とハンドラのコード内の条件は**同時に有効**（ANDの意味）；`command`のパラメータは開発者の宣言と**深くマージ**（上書きが優先）
- `detail_types`：イベントに `detail_type` がない場合は許可（未知のイベントを誤って殺さない）
- `pattern` / `regex`：テキストのないイベント（connect / heartbeat など）は制約を受けず、直接許可される
- `command`の上書きキー `master` は同期的にストアキー `must_master` にマッピングされる；コマンドの禁止は `acl` deny で行う
- **キー名のマッピング説明**：`overrides.command.set("My", "restart", master=True)` のパラメータ名
  `master` は設定の別名にすぎず、実際のストアキーと `get()` が返すキー名は統一して **`must_master`**
  （`get()` は `{"must_master": true}` を返す）——実行時判定はストアキーを読み込むので、
  `master` キー名で読み取らないでください
- 設定は即座に有効化（ホットアップデート）、形式の検証がアラートされる（未知のパラメータ / 壊れた項目は無視される）

## リンク制御：認領とブロック

> [!NOTE]
> `event.done()` / `event.mark_processed()` の `claim=` / `stop=` パラメータはこの機能に ErisPulse **2.7.1+** が必要です。

ErisPulse は「認領」と「ブロック」の2つの正交的な意味を解き、`event.done()` で統一的に制御します。これにより、コマンド処理の周囲にログ、監査、権限などの観察層を重ねることができます。

**2つの概念の正確な定義：**

- **認領（claim）**：イベントがこのハンドラによって処理されたことをマークする（`_processed` に書き込む）。コマンドディスパッチャーは認領されたイベントを見ると**重複を避ける**——同じメッセージが複数のコマンドハンドラに重複して処理されないようにする。典型的なケース：コマンドがマッチした後に認領し、コマンドディスパッチャーが再介入しないようにする。
- **ブロック（stop）**：イベントが**より低い優先度**のハンドラに伝播しないようにする（`_propagation_stopped` に書き込む）。低優先度のハンドラはこのイベントを見なくなる。典型的なケース：高優先度のハンドラがイベントを完全に処理した後、低優先度のハンドラが実行されないようにする。

| `event.done(...)` | 認領 | ブロック | 場面 |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | コマンド / ハンドラが処理完了した標準的なやり方 |
| `event.done(stop=False)` | ✔ | ✘ | 認領のみ：低優先度の観察者（ログ / 統計）は引き続き見る |
| `event.done(claim=False)` | ✘ | ✔ | ブロックのみ（ファイアウォール / レート制限）、認領はしない |

`event.done(claim=, stop=)` は `event.mark_processed(claim=, stop=)` の別名であり、パラメータと動作は完全に等価です。

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
        event.done(claim=False)  # ブロックのみ：低優先度は実行されないが、認領はしない
```

### コマンドと返信の block 設定

**コマンドがマッチしたら認領**：メッセージが登録されたコマンド名（サブコマンド/エイリアスを含む）にマッチすると、その後のスコープや権限判定の結果に関係なく、認領され、デフォルトでブロックが伝播される——権限拒否されたコマンドは低優先度のメッセージハンドラに漏れることはない（「コマンドが拒否された後に on_message がもう一度応答する」二重応答を回避する）。

ブロックを解除して、低優先度の観察者（ログ / 審査 / 権限）もこれらのメッセージを見られるようにするには、設定を解除することができます：

```toml
[ErisPulse.event.command]
block = false   # コマンドメッセージは低優先度のハンドラに伝播する（認領は影響しない、重複消費されない）

[ErisPulse.event.wait_reply]
block = false   # wait_reply で消費された返信は低優先度のハンドラに伝播する
```

> 注意：`block` は**ブロック**（stop）だけを制御し、**認領**（claim）には影響しない——マッチしたコマンドは決してメッセージハンドラに重複消費されない；コマンドにマッチしないメッセージは通常通りメッセージハンドラに伝播する。

## 通知イベント処理

### 友達追加

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "新朋友"
    await event.reply(f"欢迎添加我为好友，{nickname}！")
```

### グループメンバー増加

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"欢迎新成员 {user_id} 加入群 {group_id}")
```

### グループメンバー減少

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"成员 {user_id} 离开了群 {group_id}")
```

## 要求イベント処理

### 友達要求

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"收到好友请求: {user_id}, 附言: {comment}")
    
    # 适配器 API で要求を処理することができる
    # 具体的な実装は各适配器のドキュメントを参照してください
```

### グループ招待要求

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"收到群 {group_id} 的邀请，来自 {user_id}")
```

## 元イベント処理

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

适配器が meta イベントを送信した後、フレームワークは自動的に Bot 状態を追跡し、いつでも照会することができます：

```python
from ErisPulse import sdk

# 某个 Bot がオンラインかどうかを確認
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot 在线")

# 現在のすべてのオンライン Bot をリストする
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# 完全な状態のサマリーを取得
summary = sdk.adapter.get_status_summary()
```

## インタラクティブ処理

### reply メソッドを使用して返信を送信

`event.reply()` メソッドは、@、返信などの機能を備えた様々な修飾パラメータをサポートし、メッセージの送信を便利にします：

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
await event.reply("返信内容", reply_to="msg_id")

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
> **待機中でもコマンドは使用可能**（2.8.3+）：コマンド接頭辞で始まり、登録されたコマンドにマッチする
> メッセージ（例：`/cancel`）は**コマンドとして実行**されるのではなく返信内容として扱われる、待機は継続する——
> ユーザーはいつでもキャンセル/切り替えでき、コマンド実行後も返信を続けることができる。旧的な「すべてのテキストを飲み込む」
> 行動が必要な場合は：設定 `ErisPulse.event.wait_reply.cmdpass = true`、または単回
> `wait_reply(cmdpass=True)`。

### 確認付きの待機返信

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

ユーザーの確認または否定を待つ、自動的に組み込みの中英語確認語を認識：

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

ユーザーは選択番号または選択テキストを返信できる：

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

**マージモード**：`merge_prompt=True` の場合、オプションをプロンプトに結合し、ユーザー指定の `method` で1つのメッセージに送信：

```python
# Markdown でマージされたプロンプト + オプションを送信
choice = await event.choose(
    "## 请选择颜色\n{options}\n请回复编号",
    ["红色", "绿色", "蓝色"],
    method="Markdown",
    merge_prompt=True,
)
```

> `{options}` プレースホルダはオプションの挿入位置を制御する；書かなければプロンプトの末尾に追加される。
> `placeholder` パラメータでプレースホルダをカスタマイズできる（例：`placeholder="[choices]"`）。
> `options_format="auto"`（デフォルト）は、method に応じてスタイルを自動選択する：Markdown→無序リスト、Html→順序リスト、その他→純テキストリスト。
> テキスト系メソッド（Text/Markdown/Html 等）はデフォルトでオプションを末尾にマージする；非テキスト系メソッド（Image 等）はデフォルトで2つのメッセージに分割する。

### フォーム収集 (collect)

複数ステップでユーザーの入力を収集する：

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

### 任意のイベントを待つ (wait_for)

同一ユーザーに限らず、条件を満たす任意のイベントを待つ：

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

インタラクティブなマルチラウンド対話コンテキストを作成する：

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

ErisPulse には中英語の確認語の集合が内蔵されています：

- **確認語** (`CONFIRM_YES_WORDS`): 是、yes、y、确认、确定、好、好的、ok、true、对、嗯、行、同意、没问题...
- **否定語** (`CONFIRM_NO_WORDS`): 否、no、n、取消、不、不要、不行、cancel、false、错、拒绝、不可以...

## イベントデータアクセス

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

内蔵メソッドのほか、各プラットフォームアダプターはプラットフォーム固有のメソッドを登録し、プラットフォーム固有のデータにアクセスしやすくします。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # プラットフォームに応じて固有メソッドを呼び出す
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram 固有メソッド
    elif platform == "email":
        subject = event.get_subject()           # 郵件固有メソッド
```

プラットフォームが特定のメソッドを登録しているかどうかを確認するには、特定のプラットフォームが登録したメソッドを取得できます：

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> 各プラットフォームが登録した固有メソッドは、対応する [プラットフォーム文書](../platform-guide/) を参照してください。

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
    
    await event.reply("条件が満たされました、メッセージを処理します")
```

## 次にやること

- [よくあるタスクの例](common-tasks.md) - 機能の実装方法を学ぶ（含むメッセージ送信の高度な機能：リトライ/タイムアウト/バッチ）
- [プラットフォーム特性ガイド](../platform-guide/README.md) - Send DSLチェーン送信、送信ルール、バッチ構築の完全な説明
- [Event パッケージの詳細](../developer-guide/modules/event-wrapper.md) - Eventオブジェクトの詳細を理解する
- [ユーザー使用ガイド](../user-guide/) - 設定とモジュール管理を理解する