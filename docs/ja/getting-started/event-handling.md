# イベント処理入門

> [!TIP]
> **この記事を読むべきタイミング**：ロボットにメッセージ、コマンド、通知、リクエストへの反応をさせたい場合、または応答待ち／対話の実装、コマンドがなぜ実行されないかを調査する場合に読む。フレームワークの設計概要だけ知りたい場合は、[基本概念](basic-concepts.md)を参照するだけでよい。必要なければ飛ばしてもよい。

イベントハンドラーは、ロボットがユーザーのメッセージを理解し、反応する場所です。ここでは、5つのイベントタイプに分けて、直接コピーできる書き方を紹介し、パラメータ解析、権限、スロットリング、対話など、実践的なシナリオもカバーします。

## イベントタイプの概要

ErisPulse は以下のイベントタイプをサポートしています：

| イベントタイプ | 説明 | 適用場面 |
|---------|------|---------|
| メッセージイベント | ユーザーが送信するすべてのメッセージ | チャットロボット、コンテンツフィルタ |
| コマンドイベント | コマンドプレフィックスで始まるメッセージ | コマンド処理、機能の入口 |
| 通知イベント | システム通知（友達追加、グループメンバー変更など） | ホームメッセージ、ステータス通知 |
| リクエストイベント | ユーザーのリクエスト（友達リクエスト、グループ招待） | リクエストの自動処理 |
| 元イベント | システムレベルのイベント（接続、ハートビート） | 接続監視、ステータスチェック |

各タイプには、`notice.on_notice()` / `request.on_request()` / `meta.on_meta()` という汎用のレジスタがあります（このタイプの全イベントを受け取ります）。細分化されたデコレータ（例：`on_group_increase`）は、対応するサブタイプのみをサブスクライブします。細分化されたデコレータを優先的に使用してください。

## メッセージイベント処理

> **強く推奨**：イベントハンドラーの `event` パラメータに `Event` クラスの型注釈を追加してください。実行時には注釈がなくても実行できます（フレームワークがイベントインスタンスを渡します）。注釈は IDE の補完と静的チェックに役立ちます。プロジェクトルートディレクトリで `epsdk types` を実行して、型のスタブを生成することで、**モジュール/アダプターのカスタムメソッド**の補完を得ることができます（[IDE補完](../getting-started/ide-completion.md)を参照）。

### すべてのメッセージを監視

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"受信した {user_id} のメッセージ: {text}")
```

### プライベートメッセージを監視

```python
from ErisPulse.Core.Event import Event
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"こんにちは、{user_id}！これはプライベートメッセージです。")
```

### グループメッセージを監視

```python
from ErisPulse.Core.Event import Event
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"グループ {group_id} で {user_id} がメッセージを送信しました")
```

### @メッセージを監視

```python
from ErisPulse.Core.Event import Event
@message.on_at_message()
async def at_handler(event: Event):
    # @されたユーザーのリストを取得
    mentions = event.get_mentions()
    await event.reply(f"あなたが@したユーザー: {mentions}")
```

### ワイルドカードと正規表現による監視

4つのメッセージデコレータ（`on_message` / `on_private_message` / `on_group_message` / `on_at_message`）は、`pattern`（glob ワイルドカード）と `regex`（正規表現）をサポートしています。一致しないメッセージは**ハンドラーをトリガーしません**：

```python
from ErisPulse.Core.Event import Event
# glob ワイルドカード：* 任意の文字列、? 1文字、[seq] 文字集合
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("签到成功")

# 正規表現：金額を一致させる
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"受信した金額：{event.get_text()}")

# pattern と regex が両方指定された場合、両方を一致させる必要がある
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` もこれら2つのパラメータをサポートしています（[応答待ち機能](../developer-guide/modules/event-wrapper.md#応答待ち機能)を参照）。

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

### コマンドの別名

```python
@command(["help", "h"], aliases=["帮助"], help="ヘルプ情報を表示")
async def help_handler(event):
    await event.reply("ヘルプ情報...")
```

ユーザーは以下のいずれかの方法で呼び出すことができます：
- `/help`
- `/h`
- `/帮助`

### コマンドのパラメータ

```python
@command("echo", help="メッセージを返信")
async def echo_handler(event):
    # コマンドパラメータを取得
    args = event.get_command_args()
    
    if not args:
        await event.reply("返信するメッセージを入力してください")
    else:
        await event.reply(f"あなたが言った: {' '.join(args)}")
```

パラメータは、大文字小文字の違いを保持します（大文字小文字を無視するように設定しても、コマンド名の一致は大文字小文字を無視しますが、パラメータの内容には影響しません）。

### 宣言式パラメータとオプション（args= / options=）

手動でパラメータを解析するには、自分で型変換とエラーメッセージの提示を処理する必要があります。`args=` / `options=` を宣言した後、フレームワークは権限チェックが通った後にコマンドパラメータを自動的に解析し、**名前でハンドラーに注入**します。ユーザーの入力が間違っている場合、自動的にローカライズされたエラーメッセージと用法を返し（例外が発生してクラッシュすることはありません）、`/help <コマンド>` は自動的に用法を表示します：

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

`args=` の位置パラメータの構文：`<count:int>` 必須、`[sides:int=6]` 省略可能（デフォルト値付き）。サポートされる型：

| 型 | 例 | 説明 |
|------|---------|------|
| `str` | `hello` | テキスト（デフォルト型） |
| `int` / `float` | `3` / `0.5` | 数値 |
| `bool` | `是` / `yes` / `はい` / `да` / `true` / `no` / `取消` | ブール値、対話確認（`Event.confirm()`）の確認語リストを再利用 |
| `literal` | `<mode:literal=fast|slow>` | 列挙、指定された値のみを受け入れる；省略形はデフォルトで最初の値を使用 |
| `duration` | `90s`、`1h30m`、`1d` | 時間、秒に換算された float |
| `rest` | `<text:rest>` | 残りの全テキスト（最後に位置する必要がある） |

`options=` は辞書形式で宣言されます：キーはハンドラーのパラメータ名、値はフラグ形式（複数の別名は `/` で区切る）。`bool` に注釈されたパラメータはブールフラグ（存在すれば `True`）です；それ以外（デフォルトは `str`）は値付きオプションで、`--label hello` と `--label=hello` の両方の値をサポートし、型はハンドラーの注釈に従います。オプションは最初に認識され、残りのトークンは `args=` で解析されます（`rest` はオプションを除外した後の残りのテキストをカバーします）。

**動作の要点**：

- 権限チェックはパラメータ解析の前に実行される - 権限がないユーザーは解析をトリガーしない
- 解析失敗（型が不一致 / パラメータ不足 / パラメータ過多 / 未知のオプション）は自動的にローカライズされたエラーと用法を返し、コマンドは引き続き認識される
- 宣言されたパラメータ名はハンドラーの署名に存在する必要がある、そうでなければ登録時に `ValueError` をスローする
- `args=` / `options=` を宣言しないコマンドは、動作が完全に変化しない（後方互換性）

### コマンド管理（cooldown= / rate_limit= / usage_limit= / deprecated=）

手動でクールダウン、レート制限、使用制限、廃止メッセージを宣言で置き換えることができ、これらは任意に組み合わせることができます。

**クールダウン** - 時長の書式は `args=` の `duration` 型と同じ（例：`"30s"`、`"1h30m"`、`"1d"`）：

```python
@command("daily", cooldown="1d", cooldown_key="user", cooldown_reply="今日のサインインは完了しました")
async def daily_handler(event):
    await event.reply("サインイン完了！")
```

**レート制限** - スライディングウィンドウの宣言は `"回数/時間"` の形式（例：`"5/minute"`、`"10/s"`、`"3/2m"`）：

```python
@command("search", rate_limit="5/minute", rate_limit_key="user")
async def search_handler(event):
    await event.reply("検索結果")
```

**使用制限** - 期間内の総回数の上限（例：`"100/day"`、`"10/hour"`、`"500/30d"`）、上限を超えると実行を拒否：

```python
@command("translate", usage_limit="100/day", usage_limit_key="user",
         usage_limit_reply="今日の翻訳回数は上限に達しました")
async def translate_handler(event):
    ...
```

クールダウン/レート制限とは異なり、使用制限は**永続化されたストレージ**にカウントされます（KV キー `erispulse.usage.<key>`、再起動しても失われません）：
ストレージにアクセスできない場合、自動的にメモリ内カウントに退化し、警告を出します（この場合、使用制限は再起動でリセットされます）。カウントは使用制限の期間が切り替わるたびにリセットされ、モジュールがアンロードされたときにクリアされます。

**廃止** - 呼び出されたときに廃止文を自動的に返し、`deprecated_reject=True` で実行を拒否します：

```python
@command("oldcmd", deprecated="新しいコマンド /newcmd を使用してください", deprecated_reject=True)
async def old_handler(event): ...
```

キー粒度（`cooldown_key=` / `rate_limit_key=`）：`"user"`（デフォルト、同一ユーザーが共有）、`"session"`（同一セッションが共有、同じグループ）、`"global"`（すべてのユーザー、すべてのセッションが共有）。

**動作の要点**：

- クールダウン / レート制限 / 使用制限がヒットした場合、デフォルトでは**静かに破棄**されます（対称的なスコープで静かに）
- `cooldown_reply=` / `rate_limit_reply=` / `usage_limit_reply=` を宣言した場合、ヒットするとその文を返します
- コマンドがヒットした時点で認識されます - 治理がヒットしたコマンドは低優先度のメッセージハンドラーに漏れません
- 治理判定はすべての権限チェックとパラメータ解析が完了し、実際の実行の前に実行されます：権限のないユーザーはトリガーされず、パラメータエラーは消費されません
- クールダウンとレート制限を同時に宣言した場合、クールダウンが先に判定されます（クールダウンがヒットした場合、レート制限のウィンドウは占有されません）；使用制限はクールダウン/レート制限の判定後に実行されます
- `deprecated=` はデフォルトで返信文を返した後**実行を継続**します；`deprecated_reject=True` で実行を拒否します（`command.executed` フックは `success=False, error="deprecated"` と記録されます）
- `/help` のリストと単一コマンドのヘルプは自動的に廃止マークと文を表示します
- クールダウンとレート制限の状態はプロセス内メモリに保持され、モジュールがアンロードされたときに自動的にクリアされます；プロセス間共有 / 再起動時の永続化は対象外です（**使用制限のカウントは除く**——ストレージに永続化されます、上記参照）
- 登録時に検証されます（fail-fast）：構文が無効、キー粒度がホワイトリスト値、reply が主宣言と一致しない場合は `ValueError` をスローします

### ハンドラのスロットリング（throttle=）とデバウンス（debounce=）

メッセージハンドラのスパム防止宣言——同じキーのイベントは間隔内に1回しか処理されず、残りは静かに破棄されます：

```python
from ErisPulse import sdk

@sdk.message.on_message(throttle="2s", throttle_key="user")
async def handler(event): ...
```

デバウンスとスロットリングは補完的です：**ウィンドウ内では最後の1つだけ実行**され、前の待機タスクはキャンセルされます（検索候補などの「入力停止後に処理する」シナリオに適しています）：

```python
@sdk.message.on_message(debounce="2s", debounce_key="user")
async def search(event): ...
```

`on_message` / `on_private_message` / `on_group_message` / `on_at_message` はすべてサポートしています；`throttle_key=` / `debounce_key=` はコマンド管理と同じキー粒度（user / session / global）を使用し、時長の書式は `duration` と同じです。スロットリングと `pattern=` / `regex=` などの既存の条件は重複して効果を発揮します（すべて満たす場合にのみトリガーされます）；間隔内に破棄されたイベントは TRACE ログに記録されます；登録時に検証されます；`throttle=` と `debounce=` は意味的に排他的です（同時に宣言すると `ValueError` をスローします）。

> **デバウンスは途中で業務を中断しない**：まだ待機ウィンドウを越えていない待機タスクのみキャンセルされます；すでに越えた、実行中のハンドラは新しいイベントによってキャンセルされません（awaitのどこでも部分的な副作用が発生しないように）。

### 依存注入（Depends）

共通の依存（データベースセッション、設定の読み取りなど）は依存関数として抽出でき、ハンドラは `Depends(依存関数)` をデフォルト値として宣言し、フレームワークは呼び出し前にコンテキストオブジェクトを使って依存関数を呼び出し、名前で注入します：

```python
from ErisPulse.Core import Depends

async def get_session(event):
    return await sdk.module.call("DB", "get_session")

@command("admin")
async def admin_handler(event, db=Depends(get_session)):
    ...
```

デフォルトで**リクエストレベルのキャッシュ**が有効です：イベントの配信内では、同じ依存関数は一度だけ解析され、すべての注入ポイントで結果を共有します（`get_db` は一度のイベントでデータベースセッションを一度だけ作成します）；リクエストをまたいで自動的に再利用されません。`Depends(get_db, use_cache=False)` を使って、依存のキャッシュを無効にできます。

フレームワークの注入ポイントをすべてオーバーライドします：コマンドハンドラ、イベントハンドラ（`message.on_message()` など）、ライフサイクルフック（`sdk.lifecycle.on`）、SSEルートハンドラ。依存関数の最初の引数は注入ポイントのコンテキストオブジェクトです（イベントの場合は `Event`、ライフサイクルの場合はイベント `data`、ルートの場合は `HttpRequest` / `SseEmitter`）；同期と非同期の依存関数を宣言できます。

**他のモジュールのサービスを宣言**（構文糖衣）：

```python
@command("query")
async def query_handler(event, session=Depends.module("DB", "get_session")):
    ...
```

`Depends.module(モジュール名, メソッド名, *固定引数)` は、依存関数内で `sdk.module.call(...)` を呼び出すのと同等です。モジュールのインスタンス化（`__init__`）は対象外です；インスタンス化時にはコンテキストオブジェクトがありません。FastAPI でホストされる HTTP ルートは FastAPI の元の `fastapi.Depends` を使用してください。

**動作の要点**：

- 登録時に検証されます（fail-fast）：依存が呼び出せない、または `args=` / `options=` パラメータと重複する場合は `ValueError` をスローします
- 依存関数がスローする例外とハンドラ自身の例外は、同口径で処理されます（コマンドはエラーを自動的に返します）
- `Depends` を宣言しないハンドラはゼロオーバーヘッドです（配布時にリフレクションが一切ありません）
- FastAPI でホストされる HTTP ルートは FastAPI の元の `fastapi.Depends` を使用してください

### コマンドグループ

```python
@command("admin.reload", group="admin", help="モジュールを再読み込み")
async def reload_handler(event):
    await event.reply("モジュールを再読み込みしました")

@command("admin.stop", group="admin", help="ロボットを停止")
async def stop_handler(event):
    await event.reply("ロボットを停止しました")
```

`group` パラメータはヘルプリストの分類にのみ使用されます；上記例の `admin.reload` は**全体のコマンド名**です（ドットは命名スタイルのため、ユーザーは `/admin.reload` を入力する必要があります）。

### サブコマンド

コマンド名は**スペース区切りの複数トークン形式**に対応し、`/admin add`、`/admin user ban` などのサブコマンドを実現します：

```python
@command("admin", help="管理コマンド")
async def admin_handler(event):
    await event.reply("使い方：/admin add | /admin remove")

@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    target = event.get_command_args()[0]
    await event.reply(f"管理者 {target} を追加しました")

@command("admin remove", aliases=["a remove"], help="管理者を削除")
async def admin_remove_handler(event):
    await event.reply("管理者を削除しました")
```

マッチングルール（**最長プレフィックスマッチ**）：

- `/admin add x` は `admin add` に優先的にマッチし、`event.get_command_args()` は `["x"]` を返します（サブコマンド名以降の引数）
- `admin` だけが登録されている場合、`/admin add x` は `admin` にマッチし、`get_command_args()` は `["add", "x"]` を返します（歴史的な動作は変更なし）
- 別名は複数トークン形式（例：`a remove`）もサポートし、単一トークンの別名（例：`a`）もサブコマンドに指定できます
- 父子コマンドが同時に登録されている場合、未登録のサブコマンド入力（例：`/admin list x`）は親コマンドにフォールバック

**権限継承**：サブコマンドに `permission` が宣言されていない場合、直近で権限が宣言された祖先コマンド（`admin`）の権限を自動的に継承します——`/admin` を保護すれば、その下のすべてのサブコマンドも自動的に保護されます；サブコマンド自身が宣言した権限が優先されます：

```python
def is_admin(event):
    return event.get_user_id() in {"user123"}

@command("admin", permission=is_admin, help="管理コマンド")
async def admin_handler(event):
    ...

# permission を再宣言する必要はありません、自動的に is_admin を継承します
@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    ...
```

注意：`master=True` と `hidden` **は継承されません**、必要であればサブコマンドで個別に宣言してください；ユーザー ACL（ホワイトリスト/ブラックリスト）はコマンドのフルネームでマッチし、glob ルールは `"admin*"` のようにサブコマンド全体をカバーできます。

`/help` のコマンド一覧では、サブコマンドは可視の親コマンドの下にインデント表示されます（`admin` → `admin add` は1段階インデント、`admin user` → `admin user ban` は2段階インデント）。

### コマンドの権限とアクセス制御

コマンドの権限は3層に分かれ、上から下へ順に判定されます（**上層が拒否すると下層は判定されません**）：

```python
# ① コマンド権限 ACL（ユーザー側設定）：コマンドのユーザーのホワイトリスト/ブラックリストに基づき、拒否時に「権限不足」を返す
# ② master=True —— フレームワークのオーナーのみ実行可能（フレームワークが自動的にチェックし、拒否時に「権限不足」を返す）
@command("restart", master=True, help="モジュールを再起動")
async def restart_handler(event):
    await event.reply("モジュールを再起動しました")

# ③ permission=呼び出し関数 —— コマンド自身の制御ロジック（True を返す場合に実行される）
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="管理パネル")
async def panel_handler(event):
    await event.reply("管理パネルへようこそ")
```

**コマンドユーザー ACL**（`ErisPulse.event.command.acl`）：ユーザーは任意のコマンドにユーザーのホワイトリスト/ブラックリストを設定でき、コマンド名は正確または glob モードでマッチし、拒否時に「権限不足」を返す：

```toml
# config.toml —— 123456 だけ restart を実行可能；666 は一律拒否
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

判定順序：`deny` がヒット → 拒否；`allow` が空でヒットしない → 拒否；ACL 設定がない場合、`event.command.default_allow` に従う（`false` = 严格モード、ACL がないと拒否；`true` の場合、`master=True` / `permission` にデフォルトで委ねる）。

実行時 API（コマンド名は glob に対応）：

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # 許可リスト
command.deny_user("restart", "onebot11", "666")       # 拒否リスト
command.remove_acl("restart")                          # ホワイトリスト/ブラックリストを削除
command.get_acl("restart")                             # 現在のリストを取得
```

> 命令ハンドラはイベントパッケージからインポートされます：`from ErisPulse.Core.Event import command`；
> または SDK イベントパッケージからアクセスすることもできます：`sdk.Event.command`（これらは同一のシングルトンです）。
> モジュール内では通常 `from ErisPulse.Core.Event import command` としてインポートされています。

コマンドやユーザー間の**イベントレベル**のアクセス制御（特定の人の、特定のグループの、特定の Bot のメッセージを受け取るかどうか）
は、スコープの**アイデンティティ次元**（`scope.identity`）を通じて実現します；**モジュールレベル**の可用性（どのモジュールが使えるか）
は、スコープの**モジュール次元**（`scope.platforms / bots / sessions`）を通じて実現します。
[スコープ（scope）](../advanced/scope.md)を参照してください。

> 建議：コマンド内部でビジネスロジックを連動させるには `master=True` / `permission` を使用します；ユーザー/グループによるアクセス制御にはスコープのアイデンティティ次元を使用します；モジュールの可用性を制御するにはスコープのモジュール次元を使用します。

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

ErisPulse のイベントシステムは**同優先度は並列、異なる優先度は直列**のスケジューリングモデルを採用しています：

```
イベント到着
    ↓
priority=10 組: [ハンドラC || ハンドラD] 並列 → 結果をマージ
    ↓ (中断されない場合)
priority=0 組: [ハンドラA || ハンドラB] 並列 → 結果をマージ
    ↓
...
```

- **同優先度は並列**：優先度が同じ複数のハンドラは同時に実行され、処理量を向上させます
- **跨優先度は直列**：異なる優先度のグループは順番に実行されます（数値が大きいほど先に実行）、高優先度のハンドラが先に実行されます
- **Copy-On-Write**：ハンドラが変更しない限りコピーを作成せず、オーバーヘッドをゼロにします
- **競合処理**：同優先度の複数ハンドラが同じフィールドを変更した場合、最後に変更された値を使用し、警告ログを記録します
- **中断機構**：任意のハンドラが `event.done()`（デフォルト）または `event.done(claim=False)` を呼び出した後、低優先度のグループをスキップします。認知とブロッキングの違いは下記の[「リンク制御：認知とブロッキング」](#リンク制御認知とブロッキング)を参照してください。

```python
# 例：同優先度ハンドラが並列実行
@message.on_message(priority=0)
async def handler_a(event):
    # タスクAを処理
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # handler_a と並列実行
    event['result_b'] = process_b()

# 異なる優先度が直列実行
@message.on_message(priority=10)
async def handler_c(event):
    # 優先度が最も高く、最初に実行されます
    pass
```

> **並列上限**：すべてのマッチするハンドラのタスクは**即座に作成**されますが、シグナルマニュアルで**同時実行数の上限**が制限され、デフォルト値は **64**（`ErisPulse.framework.handler_max_concurrency`、ホットアップデート可能）です。上限を超えたタスクはシグナルマニュアルでキューイングされ、前のタスクが完了した後に実行されます。イベントのピーク時にはこれが「圧力調整弁」になります。
>
> **遅延ログ**：個々のハンドラが1秒以上かかる場合、フレームワークはログにWARNINGを出力します（`handler_slow`）。`wait_reply`の待機時間は処理時間から差し引かれるため、「返信を待つ」ことで誤って遅延と判定されることはありません。

## ミドルウェア：配布前に変更または拒否

ミドルウェアはイベント配布**の前**に順序実行され、ファイアウォール、リクエスト制限、イベントの脱敏などの正統な実装ポイントです：

```python
from ErisPulse.Core import adapter

@adapter.middleware
async def firewall(data):
    if _is_banned(data.get("user_id")):
        return False          # 拒否：イベントは破棄され、どのハンドラにも渡されず、出力副作用もありません
    data["checked"] = True    # データを変更して配布を続ける
    # Noneを返す：配布、データは変更なし（従来の動作）
    return data
```

| 戻り値 | 行動 |
|--------|------|
| `False` | **拒否**：イベントは即座に破棄され、どのハンドラにも渡されません |
| `dict` | イベントデータを変更して配布を続ける |
| `None` | 配布、データは変更なし |

拒否された場合、フレームワークはTRACEログを出力し、`adapter.event.blocked`ライフサイクルフックをトリガーします（ミドルウェア名と完全なイベントが渡されます）、イベントがなぜ反応しなかったかを監査できます。

## コマンド配布決定チェーン：なぜコマンドが実行されないのか

1つのコマンドメッセージは次のように処理されます：**コマンドテキスト判定 → コマンド名/別名が一致（一致しなかった場合は類似語の提案）→ 一致した時点で認知 → スコープ → ユーザーACL → マスター → 権限 → クールダウン/レート制限 → 使用制限（usage）→ 廃止（deprecated, notice/rejected）→ パラメータ解析 → 実行**（ミドルウェアはイベント層で拒否できる、上節参照）。1つでも満たさなければ処理は中止されます；治験がヒットした場合、デフォルトでは静かに破棄されます；権限の拒否はユーザーに返信されます；廃止は宣言された文を返すか、拒否します。

テスト中 `ErisPulse-Testing` の `dispatch()` はこの決定チェーンを直接返します（`DispatchTrace`、`trace.explain()` は逐行因果を出力）、プロダクション環境では `ErisPulse.Core.Event.start_dispatch_trace()` を使って同じ記録を収集できます。

さらに `ErisPulse.runtime` は3つの診断APIを提供します：`explain_module(モジュール名)` は「モジュールがなぜロードされなかったか」を回答します（未登録 / ラグジュアリー / 設定で無効 / 依存が不足 / SDKのバージョンが満たさない、順に原因を示します）、`explain_event(イベント)` は「イベントがなぜ反応しなかったか」を回答します（アダプターが未登録 / アイデンティティがブロック / モジュールセッションが遮断 / コマンドが一致しない）、`explain_trace(trace_id)` は「このメッセージが返信されなかった理由」を回答します——trace-idからセッションのトランスクリプトを集めて完全な出入力タイムラインを出力し、返信されたか / 未返信 / トランスクリプトが有効化されていないかを結論づけます；`format_report()` を使って人間が読める結論をレンダリングできます。`explain_trace` は[セッショントランスクリプト](../advanced/transcript.md)に依存します、有効化されていない場合は明確にこの結論を返すか、空の結果ではなく。

## スコープフィルタリング：なぜ私のモジュールがメッセージを受け取らないのか

イベントが到着した後、2つの**静か**なフィルタがあります（どちらも返信せず、エラーも出ません）：

1. **アイデンティティ次元**（`ErisPulse.scope.identity`）：イベントが配布エントリーに到着するとき、ユーザー > グループ > Bot > アダプターの順で受け取るかどうかを判定します。
   拒否された**イベント全体**は直接破棄され、どのハンドラ（コマンドディスパッチャを含む）もトリガーされません。
2. **モジュール次元**（`ErisPulse.scope`）：イベントが特定のモジュールのハンドラ/コマンドに到着したとき、セッション > Bot > プラットフォームの順でそのモジュールが利用可能かどうかを判定し、**通過しない場合は静かにスキップ**されます。

```toml
# 例1：特定のグループのすべてのメッセージをブロードキャストしない
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# 例2：MyModuleを特定のBotにブロック
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

この場合、そのグループのメッセージが到着したとき、`MyModule` のコマンドとイベントハンドラは**すべてスケジュールされません**。これはバグではなく、フィルタリング機構です——「モジュールが反応しない」ことを調査するときは、まずスコープのアイデンティティとモジュールのバインディングをチェックしてください。

- フィルタリングログは **TRACE** レベルでのみ表示されます（`core.scope.identity_denied` / `core.scope.denied`）、デフォルトの INFO では痕跡が見えません
- フレームワークのハンドラ（コマンドディスパッチャ `scope_exempt=True`）は**モジュール次元**の影響を受けませんが、**アイデンティティ次元**の影響を受けます（イベント全体が破棄されているため）
- コマンド実行前に3つ目のフィルタがあります：コマンドユーザーACL（拒否時に「権限不足」を返す、上節参照）
- 4つ目のフィルタは**イベント上書き**（下節参照）

> [!NOTE]
> **スコープフィルタリングとイベント認知（claim）の関係**：2つの静かのフィルタはすべてハンドラが**スケジュールされる前**に発生します——フィルタでスキップされたハンドラは実行されず、当然認知状態にも影響を与えません。イベントが認知されたかどうかは、**実際に実行されたハンドラ**（コマンドが認知、返信が認知、明示的に呼び出された）によって決定されます；スコープ拒否自体は認知もブロッキングもしません（静かにスキップし、イベントは配布チェーンを完了します）。

> スコープの設定、マッチングの書式、実行時APIは [スコープ（scope）](../advanced/scope.md) を参照してください。

## イベント上書き：モジュールコードを変更せずに、任意のイベントタイプの動作を上書き

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要です。

イベントハンドラが登録時に宣言されたパラメータ（`pattern` / `regex` / `master` / `hidden` など）は**開発者のデフォルト**です。
一括上書きシステムは、ユーザーが**イベントタイプごとに**任意のモジュールの動作を上書きできるようにします——OneBot12標準タイプ（meta / message / notice / request）とErisPulse拡張タイプ（command）それぞれに専用の上書き可能なパラメータがあります：

| イベントタイプ | 上書き可能なパラメータ | 作用 |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | テキストトリガー条件 + メッセージサブタイプホワイトリスト |
| `notice` | `detail_types` / `pattern` / `regex` | 通知サブタイプホワイトリスト + テキスト条件 |
| `request` | `detail_types` / `pattern` / `regex` | リクエストサブタイプホワイトリスト + テキスト条件 |
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

# command：実装パラメータを上書き（ユーザー優先——絞るか、展開するか）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl：コマンドユーザーホワイトリスト/ブラックリスト（globで全グループをカバー）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACLのデフォルト（false = 严格モード：ACLがないと拒否）
acl_default_allow = true
```

実行時API（`from ErisPulse.Core.Event import overrides` または `sdk.Event.overrides`，
**タイプサブネームスペース**——各タイプ対称の `set` / `get` / `delete` 三件套）：

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # messageテキスト条件
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # コマンドパラメータ
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # コマンドユーザーブラックリスト

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # 開発者デフォルトに戻す
```

- 上書き条件とハンドラコード内の条件は**同時に有効**（AND論理）；`command` パラメータは開発者宣言と**深くマージ**（上書きが優先）
- `detail_types`：イベントに `detail_type` がない場合、放行（未知のイベントを誤って殺さない）
- `pattern` / `regex`：テキストがないイベント（connect / heartbeat など）は制約を受けず、直接放行
- `command` 上書きキー `master` は同期ストレージキー `must_master` にマッピング；コマンドの無効化は `acl` deny で行う
- **キー名マッピングの説明**：`overrides.command.set("My", "restart", master=True)` のパラメータ名
  `master` は設定の別名に過ぎず、実際のストレージキーと `get()` で返されるキー名は**`must_master`** に統一されます
  （`get()` は `{"must_master": true}` を返す）——実行時の判定はストレージキーを読み取るので、`master` キー名で取得しないでください
- 設定は変更されると即座に有効化（ホットアップデート）、形式の検証がアラートされます（未知のパラメータ / 壊れた項目は無視）

## リンク制御：認知とブロッキング

> [!NOTE]
> `event.done()` / `event.mark_processed()` の `claim=` / `stop=` パラメータは ErisPulse **2.7.1+** が必要です。

ErisPulse は「認知」と「ブロッキング」の2つの正交的な概念を解き、`event.done()` で統一的に制御し、コマンド処理の周囲にログ、監査、権限などの観察層を重ねることができます。

**2つの概念の正確な定義**：

- **認知（claim）**：イベントがこのハンドラによって処理されたことをマークします（`_processed` に書き込み）。コマンドディスパッチャーは、イベントが既に認知されている場合、**重複処理を防ぎ**ます。典型的なシナリオ：コマンドがマッチした後に認知し、コマンドディスパッチャーが再度介入しないようにします。
- **ブロッキング（stop）**：イベントが**より低い優先度**のハンドラに伝播しないように阻止します（`_propagation_stopped` に書き込み）。より低い優先度のハンドラはこのイベントを見なくなります。典型的なシナリオ：より高い優先度のハンドラがイベントを完全に処理した後、より低い優先度のハンドラが実行されないようにします。

| `event.done(...)` | 認知 | ブロッキング | シナリオ |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | コマンド / ハンドラが処理を完了した標準的な方法 |
| `event.done(stop=False)` | ✔ | ✘ | 認知のみ、低優先度の観察者（ログ / 統計）が引き続き見られるようにする |
| `event.done(claim=False)` | ✘ | ✔ | ブロッキングのみ（例：ファイアウォール / レート制限）、認知はしない |

`event.done(claim=, stop=)` は `event.mark_processed(claim=, stop=)` の別名で、パラメータと動作は完全に等価です。

```python
@command("help")
async def help_cmd(event):
    event.done()            # 認知 + ブロッキング（コマンド処理の完了の標準的な方法）

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # 認知のみ：低優先度は実行される（ログ / 統計）

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # ブロッキングのみ：低優先度は実行されないが、認知はしない
```

### コマンドと返信の block 設定

**コマンドがマッチすると認知**：メッセージが登録されたコマンド名（サブコマンド/別名を含む）にマッチすると、権限や権限判定の結果に関係なく、認知され、デフォルトでブロッキングされます。権限拒否されたコマンドは、低優先度のメッセージハンドラに漏れることはありません（「コマンド拒否後に on_message が再度反応する」二重応答を防ぐ）。

ブロッキングを解除して、低優先度の観察者（ログ / 審査 / 権限）がこれらのメッセージを見られるようにするには、設定を変更できます：

```toml
[ErisPulse.event.command]
block = false   # コマンドメッセージは低優先度のハンドラに流れる

[ErisPulse.event.wait_reply]
block = false   # wait_reply で消費された返信は低優先度のハンドラに流れる
```

> 注意：`block` は**ブロッキング**（stop）のみを制御し、**認知**（claim）には影響しません——マッチしたコマンドは決してメッセージハンドラに重複して消費されません；コマンドにマッチしないメッセージは通常のメッセージハンドラに流れる。

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

## リクエストイベント処理

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

### Bot 状態照会

適切なアダプターが元イベントを送信した後、フレームワークは自動的にBotの状態を追跡し、いつでも照会できます：

```python
from ErisPulse import sdk

# 某個 Bot 是否在线
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot 在线")

# 列出当前所有在线 Bot
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# 获取完整状态摘要
summary = sdk.adapter.get_status_summary()
```

## 交互処理

### reply メソッドを使用した返信送信

`event.reply()` メソッドは、@、返信などの機能をサポートする様々な修飾パラメータを備え、メッセージの送信を容易にします：

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

# 組み合わせ: @ユーザー + 返信
await event.reply("内容", at_users=["user1"], reply_to="msg_id")
```

### ユーザーの返信を待つ

```python
@command("ask", help="询问用户")
async def ask_handler(event):
    await event.reply("请输入你的名字:")
    
    # ユーザー返信を待つ、タイムアウト30秒
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")
    else:
        await event.reply("等待超时，请重新输入。")
```

> [!TIP]
> **待機中でもコマンドは使用可能**（2.8.3+）：コマンドプレフィックスで始まり、登録済みコマンドに一致するメッセージ（例：`/cancel`）は**コマンドとして実行**され、返信として扱われず、待機は中断されません——ユーザーはいつでもキャンセル/切り替えでき、コマンド実行後も返信を続けることができます。旧来の「テキストをすべて吸収する」動作が必要な場合：設定 `ErisPulse.event.wait_reply.cmdpass = true`、または単回 `wait_reply(cmdpass=True)`。

### 認証付きの待機返信

```python
@command("age", help="询问年龄")
async def age_handler(event):
    def validate_age(event_data):
        """年齢が有効かどうかを検証"""
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

ユーザーの確認または否定を待つ、自動的に組み込みの中英確認語を認識：

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

ユーザーは選択番号または選択肢を返信できます：

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

**マージモード**：`merge_prompt=True` の場合、選択肢をプロンプトに組み込み、`method` で1つのメッセージとして送信します：

```python
# Markdownで送信する場合、プロンプトに選択肢を追加
choice = await event.choose(
    "## 请选择颜色\n{options}\n请回复编号",
    ["红色", "绿色", "蓝色"],
    method="Markdown",
    merge_prompt=True,
)
```

> `{options}` は選択肢の挿入位置を制御；記載しない場合はプロンプト末尾に追加。
> `placeholder` パラメータでカスタムプレースホルダを指定できます（例：`placeholder="[choices]"`）。
> `options_format="auto"`（デフォルト）は、`method` に応じてスタイルを自動選択：Markdown→無序リスト、Html→有序リスト、その他→テキストリスト。
> テキスト系メソッド（Text/Markdown/Htmlなど）はデフォルトで選択肢を末尾にマージ；非テキスト系メソッド（Imageなど）はデフォルトで2つのメッセージに分割。

### フォーム収集 (collect)

複数ステップでユーザーの入力を収集します：

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

特定条件を満たす任意のイベントを待つ、同一ユーザーに限らない：

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

### 多段対話 (conversation)

対話可能な多段対話コンテキストを作成します：

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

### 組み込み確認語

ErisPulse は中英の確認語の集合を内蔵しています：

- **確認語** (`CONFIRM_YES_WORDS`): 是、yes、y、确认、确定、好、好的、ok、true、对、嗯、行、同意、没问题...
- **否定語** (`CONFIRM_NO_WORDS`): 否、no、n、取消、不、不要、不行、cancel、false、错、拒绝、不可以...

## イベントデータアクセス

### Event オブジェクトの常用メソッド

```python
@command("info")
async def info_handler(event):
    # 基本情報
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # 発信者情報
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

内蔵メソッドに加えて、各プラットフォームアダプターはプラットフォーム固有のメソッドを登録し、プラットフォーム固有のデータにアクセスしやすくします。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # プラットフォームに応じて固有メソッドを呼び出す
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram固有メソッド
    elif platform == "email":
        subject = event.get_subject()           # 郵件固有メソッド
```

どのプラットフォームがどのメソッドを登録したかわからない場合は、特定のプラットフォームが登録したメソッドを照会できます：

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> 各プラットフォームが登録した固有メソッドは、対応する [プラットフォームドキュメント](../platform-guide/) を参照してください。

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
        # 予期しないエラー
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
    # 特定ユーザーのメッセージのみ処理
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # 特定のキーワードを含むメッセージのみ処理
    if "キーワード" not in event.get_text():
        return
    
    await event.reply("条件が満たされ、メッセージを処理します")
```

## 次に

- **イベントオブジェクト自体を操作したい**：[Event 包装クラスの詳細](../developer-guide/modules/event-wrapper.md)を参照し、Event 全てのメソッドの権威的なリファレンス
- **より複雑なメッセージを送りたい**：[プラットフォーム特性ガイド](../platform-guide/README.md)で SendDSL 鏈式送信、送信ルール、バッチ構築について詳しく説明；[よくあるタスクの例](common-tasks.md)にリトライ / タイムアウト / バッチの既成コードあり
- **機能を書き終えて設定とデプロイをしたい**：[ユーザー使用ガイド](../user-guide/)に進み、設定ファイルと CLI 管理はすべてそこの中にある