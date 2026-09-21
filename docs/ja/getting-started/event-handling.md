# イベント処理入門

このガイドでは、ErisPulseにおけるイベント処理の基本を紹介します。

## イベントの種類概要

ErisPulseは以下のイベントをサポートしています。

| イベント種類 | 説明 | 使用場面 |
|---------|------|---------|
| メッセージイベント | ユーザーが送信したメッセージ | チャットボット、コンテンツフィルタリング |
| コマンドイベント | コマンド接頭辞で始まるメッセージ | コマンド処理、機能の入口 |
| 通知イベント | システム通知（友達追加、グループメンバー変更など） | ホームメッセージ、ステータス通知 |
| 要求イベント | ユーザーのリクエスト（友達リクエスト、グループ招待） | リクエストの自動処理 |
| 元イベント | システムイベント（接続、ハートビート） | 接続監視、ステータスチェック |

## メッセージイベントの処理

> **ヒント**: イベントハンドラで `Event` タイプの注釈を使用することを推奨します。これにより、IDEの自動補完と型チェックが利用できます。

```python
from ErisPulse.Core.Event import Event  # イベントの型を注釈に使用
```

### すべてのメッセージを監視

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"{user_id} からのメッセージ: {text}")
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
`on_at_message` の4つのメッセージデコレータは `pattern`（globワイルドカード）と `regex`（正規表現）をサポートしており、一致しないメッセージは**ハンドラをトリガーしません**。

```python
# globワイルドカード: * 任意の文字列、? 1文字、[seq] 文字集合
@message.on_message(pattern="サインイン*")
async def signin_handler(event: Event):
    await event.reply("サインイン成功")

# 正規表現: 金額をマッチ
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"金額を受信しました: {event.get_text()}")

# pattern と regex 両方指定 → 両方一致する必要がある
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` はこの2つのパラメータもサポートしています（[返信の待ち機能](../developer-guide/modules/event-wrapper.md#返信の待ち機能)を参照）。

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

### コマンドエイリアス

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
@command("echo", help="メッセージを返信")
async def echo_handler(event):
    # コマンド引数を取得
    args = event.get_command_args()
    
    if not args:
        await event.reply("返信するメッセージを入力してください")
    else:
        await event.reply(f"あなたが言った: {' '.join(args)}")
```

引数は、大文字小文字を区別せず設定しても、ユーザー入力の元の大文字小文字が保持されます（コマンド名のマッチングは正規化されますが、引数内容には影響しません）。

### 宣言的引数とオプション（args= / options=）

手動で引数を解析するには、型変換やエラーメッセージの処理を自分で行う必要があります。`args=` / `options=` を宣言すると、権限チェックが通過した後にフレームワークがコマンド引数を自動的に解析し、**名前でハンドラに注入**します。ユーザーの入力が間違っている場合、自動的にローカライズされたエラーメッセージと使い方が返され、例外が発生してクラッシュすることはありません。また、`/help <コマンド>` でも自動的に使い方が表示されます。

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

`args=` 位置引数の構文：`<count:int>` は必須、`[sides:int=6]` はオプション（デフォルト値あり）。サポートされる型は以下の通りです：

| 型 | 入力例 | 説明 |
|------|---------|------|
| `str` | `hello` | テキスト（デフォルト型） |
| `int` / `float` | `3` / `0.5` | 数値 |
| `bool` | `はい` / `yes` / `はい` / `да` / `true` / `no` / `キャンセル` | ブール値、イベントの確認（`Event.confirm()`）で使用する確認語のリストを再利用 |
| `literal` | `<mode:literal=fast|slow>` | 列挙、指定された値のみを受け入れる；オプション形式ではデフォルトで最初の値を使用 |
| `duration` | `90s`、`1h30m`、`1d` | 時間、秒に換算されるfloat |
| `rest` | `<text:rest>` | 残りのすべてのテキスト（最後に位置する必要がある） |

`options=` は辞書形式で宣言されます：キーはハンドラの引数名、値はフラグ形式（複数のエイリアスは `/` で区切る）。`bool` と注釈された引数はブールフラグ（存在すれば `True`）；それ以外（デフォルトでは `str`）は値付きオプションで、`--label hello` と `--label=hello` の両方の形式がサポートされ、型はハンドラの注釈に従います。オプションは先に認識され、残りのトークンは `args=` で解析されます（`rest` はオプションを除外した後の残りのテキストをカバーします）。

**動作の要点**：

- 権限チェックは引数解析より先に実行される—権限がないユーザーは解析をトリガーしない
- 解析失敗（型が合わない / 必須引数が不足 / 引数が多すぎる / 無効なオプション）は、ローカライズされたエラーメッセージと使い方を自動的に返し、コマンドは引き続き認識される
- 宣言された引数名はハンドラの署名に存在しなければならない、そうでなければ登録時に `ValueError` が発生する
- `args=` / `options=` を宣言しないコマンドは、動作が完全に変化しない（後方互換性）

### コマンドクールダウン（cooldown=）

手動でクールダウンを実装する代わりに、`cooldown=` を宣言して代替できます。時間の書式は `args=` の `duration` 型と同じ（例：`"30s"`、`"1h30m"`、`"1d"`）：

```python
@command("daily", cooldown="1d", cooldown_key="user", cooldown_reply="今日のログイン済み")
async def daily_handler(event):
    await event.reply("ログイン完了！")
```

`cooldown_key=` はクールダウンの粒度を制御します：`"user"`（デフォルト、同一ユーザーで共有）、`"session"`（同一セッションで共有、グループ内）、`"global"`（すべてのユーザーとセッションで共有）。

**動作の要点**：

- クールダウンがヒットした場合、デフォルトでは**静かに無視**される（作用域に応じて静かに無視）
- `cooldown_reply=` を宣言すると、ヒット時にその文言を返す
- コマンドがヒットすると認識される—クールダウンがヒットしたコマンドは、低優先度のメッセージハンドラに漏れることはない
- クールダウンは、すべての権限チェックと引数解析が完了し、コマンドが実際に実行される前に開始される：権限がないユーザーはクールダウンをトリガーせず、引数エラーはクールダウンを消費しない
- 状態はプロセス内のメモリに保持され、モジュールのアンロード時に自動的にクリーンアップされる；プロセス間共有 / 再起動時の永続化は対象外
- 宣言時に検証（fail-fast）：時間の書式が不正、`cooldown_key=` がホワイトリストの値でない、`cooldown_reply=` が `cooldown=` と併用されていない場合、すべて `ValueError` が発生する

### 依存注入（Depends）

共通の依存（データベースセッション、設定の読み取りなど）は、依存関数に抽出し、ハンドラに `Depends(依存関数)` をデフォルト値として宣言することで、フレームワークがコンテキストオブジェクトを用いて依存関数を自動的に呼び出し、名前で注入する：

```python
from ErisPulse.Core import Depends

async def get_session(event):
    return await sdk.module.call("DB", "get_session")

@command("admin")
async def admin_handler(event, db=Depends(get_session)):
    ...
```

**リクエストレベルのキャッシュ**がデフォルトで有効です：1回のイベント配信内では、同じ依存関数は1回しか解析されず、すべての注入ポイントで結果を共有します（例えば `get_db` は1回のイベント内で1回だけデータベースセッションを確立）。リクエスト間では自動的に再利用されません。`Depends(get_db, use_cache=False)` を使用して、個々の依存のキャッシュを無効にできます。

フレームワークのすべての注入ポイントをオーバーライドできる—コマンドハンドラ、イベントハンドラ（`message.on_message()` など）、ライフサイクルフック（`sdk.lifecycle.on`）、SSEルートハンドラ。依存関数の最初の引数は注入ポイントのコンテキストオブジェクト（イベントの場合は `Event`、ライフサイクルの場合はイベント `data`、ルートの場合は `HttpRequest` / `SseEmitter`）です；同期と非同期の依存関数の両方を宣言できます。

**他のモジュールのサービスを宣言する**（構文糖）：

```python
@command("query")
async def query_handler(event, session=Depends.module("DB", "get_session")):
    ...
```

`Depends.module(モジュール名, メソッド名, *固定引数)` は、依存関数内で `sdk.module.call(...)` を呼び出すのと同じです。モジュールのインスタンス化（`__init__`）は対象外です—インスタンス化時にはコンテキストオブジェクトがありません；FastAPI が提供する HTTP ルートは FastAPI の元の `fastapi.Depends` を使用してください。

**動作の要点**：

- 宣言時に検証（fail-fast）：依存が呼び出せない、または `args=` / `options=` 引数と重複する場合、`ValueError` が発生する
- 依存関数が発生させる例外は、ハンドラ自身の例外と同じ口径で処理される（コマンドは自動的にエラーを返す）
- `Depends` を宣言しないハンドラはゼロオーバーヘッド（配信時に反射が一切行われない）
- FastAPI が提供する HTTP ルートは FastAPI の元の `fastapi.Depends` を使用してください

### コマンドグループ

```python
@command("admin.reload", group="admin", help="モジュールを再読み込み")
async def reload_handler(event):
    await event.reply("モジュールを再読み込みしました")

@command("admin.stop", group="admin", help="ロボットを停止")
async def stop_handler(event):
    await event.reply("ロボットを停止しました")
```

`group` パラメータはヘルプリストの分類にのみ使用されます；上記の例では `admin.reload` は**全体のコマンド名**です（ドットは命名規則に過ぎず、ユーザーは `/admin.reload` を入力する必要があります）。

### サブコマンド

コマンド名は**スペース区切りの複数トークン形式**をサポートし、`/admin add`、`/admin user ban` のようなサブコマンドを実現できます：

```python
@command("admin", help="管理コマンド")
async def admin_handler(event):
    await event.reply("使い方：/admin add | /admin remove")

@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    target = event.get_command_args()[0]
    await event.reply(f"{target} を追加しました")

@command("admin remove", aliases=["a remove"], help="管理者を削除")
async def admin_remove_handler(event):
    await event.reply("削除しました")
```

マッチングルール（**最長前接辞マッチ**）：

- `/admin add x` は `admin add` に優先的にマッチし、`event.get_command_args()` は `["x"]` を返す（サブコマンド名の後の引数）
- `admin` のみ登録されている場合、`/admin add x` は `admin` にマッチし、`get_command_args()` は `["add", "x"]` を返す（過去の動作のまま）
- エイリアスは複数トークン形式（例：`a remove`）をサポートし、単一トークンエイリアス（例：`a`）もサブコマンドに指定可能
- 父子コマンドが同時に登録されている場合、未登録のサブコマンド入力（例：`/admin list x`）は親コマンドに降格される

**権限継承**：サブコマンドが `permission` を宣言していない場合、直近で権限を宣言した祖先コマンドの権限を自動的に継承します—`/admin` を保護すれば、その下のすべてのサブコマンドも自動的に保護されます；サブコマンド自身が宣言した権限が優先されます：

```python
def is_admin(event):
    return event.get_user_id() in {"user123"}

@command("admin", permission=is_admin, help="管理コマンド")
async def admin_handler(event):
    ...

# permission を再宣言する必要はなく、is_admin を自動的に継承します
@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    ...
```

注意：`master=True` と `hidden` は**継承されません**、必要に応じてサブコマンドで個別に宣言してください；ユーザー ACL（ホワイトリスト/ブラックリスト）はコマンドの完全名でマッチし、`glob` ルール（例：`"admin*"`）でサブコマンド全体をカバーできます。

`/help` のコマンド一覧では、サブコマンドは表示可能な親コマンドの下に自動的にインデント表示されます（`admin` → `admin add` は1段階インデント、`admin user` → `admin user ban` は2段階インデント）。

### コマンド権限とアクセス制御

コマンドの権限は3層に分かれ、上から下へ順に判定されます（**上層が拒否すると下層は見ない**）：

```python
# ① コマンド権限 ACL（ユーザー側設定）：コマンドごとのユーザーのホワイトリスト/ブラックリスト、拒否時は「権限不足」を返す
# ② master=True —— フレームワークのオーナーのみ実行可能（フレームワークが自動的にチェック、拒否時は「権限不足」を返す）
@command("restart", master=True, help="モジュールを再起動")
async def restart_handler(event):
    await event.reply("モジュールを再起動しました")

# ③ permission=呼び出し関数 —— コマンド自身の制御ロジック（True を返す場合にのみ実行）
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="管理パネル")
async def panel_handler(event):
    await event.reply("管理パネルへようこそ")
```

**コマンドユーザー ACL**（`ErisPulse.event.command.acl`）：ユーザーは任意のコマンドにユーザーのホワイトリスト/ブラックリストを設定でき、コマンド名は正確なマッチと glob モード（例：`"roll*"`）をサポートし、拒否時は「権限不足」を返す：

```toml
# config.toml —— restart コマンドは 123456 にのみ実行を許可；666 は一律拒否
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

判定順序：`deny` がヒット → 拒否；`allow` が空でないかつヒットしない → 拒否；ACL が設定されていない場合は `event.command.default_allow`（`false` = 严格モード、ACL がない場合は拒否；`true` の場合、開発者のデフォルト `master=True` / `permission` に委ねる）に従う。実行時 API（コマンド名は glob をサポート）：

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # 許可リスト
command.deny_user("restart", "onebot11", "666")       # 拒否リスト
command.remove_acl("restart")                          # ホワイトリスト/ブラックリストを削除
command.get_acl("restart")                             # 現在のリストを取得
```

> コマンドハンドラはイベントパッケージからインポート：`from ErisPulse.Core.Event import command`；SDK イベントパッケージを経由してアクセスすることも可能：`sdk.Event.command`（両者は同一のシングルトン）。
> モジュール内では通常、コマンドデコレータ経由でインポートされている（`from ErisPulse.Core.Event import command`）。

コマンド間 / ユーザー間の**イベントレベル**のアクセス制御（特定のユーザー / グループ / Bot のメッセージを受信するか否か）は、作用域の**アイデンティティ次元**（`scope.identity`）を用いる；**モジュールレベル**の可用性（どのモジュールが使えるか）は、作用域の**モジュール次元**（`scope.platforms / bots / sessions`）を用いる。
詳細は[作用域（scope）](../advanced/scope.md)を参照してください。

> おすすめ：コマンド内部でビジネスロジックと連動する必要がある場合は `master=True` / `permission` を使用する；純粋にユーザー / グループでアクセス制御を行う場合は作用域アイデンティティ次元を使用する；モジュールの可用性を制御する場合は作用域モジュール次元を使用する。

### コマンド優先度

```python
# 優先度の数値が大きいほど、実行が早くなる
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("高優先度のハンドラ")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("低優先度のハンドラ")
```

### 並行イベント処理

ErisPulse のイベントシステムは**同優先度で並行、異なる優先度で直列**のスケジューリングモデルを採用しています：

```
イベント到着
    ↓
priority=10 組: [ハンドラC || ハンドラD] 並行 → 結果を結合
    ↓ (中断しない場合)
priority=0 組: [ハンドラA || ハンドラB] 並行 → 結果を結合
    ↓
...
```

- **同優先度で並行**：優先度が同じ複数のハンドラは同時に実行され、スループットが向上
- **跨優先度で直列**：異なる優先度のグループは順番に実行される（数値が大きいほど先に実行）、高優先度ハンドラが先に実行されることを保証
- **Copy-On-Write**：ハンドラが変更しない限りコピーを作成せず、ゼロオーバーヘッドを保証
- **衝突処理**：同優先度の複数ハンドラが同じフィールドを変更した場合、最後の変更値を使用し、警告ログを記録
- **中断メカニズム**：任意のハンドラが `event.done()`（デフォルト）または `event.done(claim=False)` を呼び出した後、以降の低優先度グループをスキップする。認領とブロックの違いは下記の[「リンク制御：認領とブロック」](#リンク制御認領とブロック)を参照してください。

```python
# 例：同優先度ハンドラが並行実行される
@message.on_message(priority=0)
async def handler_a(event):
    # 作業 A を処理
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # handler_a と並行実行
    event['result_b'] = process_b()

# 異なる優先度で直列実行
@message.on_message(priority=10)
async def handler_c(event):
    # 最も優先度が高い、最初に実行される
    pass
```

> **並行上限**：すべてのマッチするハンドラの Task は**即座に作成**されるが、シグナルマニュアルで**同時に実行される数**を制限し、デフォルト上限は **64**（`ErisPulse.framework.handler_max_concurrency`、ホットアップデート可能）。上限を超えた Task はシグナルマニュアル上でキューイングされ、前の処理が完了した後に実行される。イベントのピーク時に、これが「圧力緩和弁」になります。
>
> **遅延ログ**：個々のハンドラの処理時間が **1秒**を超える場合、フレームワークはログに WARNING（`handler_slow`）を出力します。`wait_reply` の待機時間は処理時間から除外され、ユーザーの返信待ちで誤って遅延と判定されることはありません。

## スコープフィルタリング：なぜ私のモジュールはメッセージを受け取らないのか

イベントが到着した後、2つの**静的な**フィルタがあります（どちらも返信やエラーを出さず、無視されます）：

1. **アイデンティティ次元**（`ErisPulse.scope.identity`）：イベントが配信入口に到達した時点で、ユーザー > グループ > Bot > アダプタの順に、イベントを受け取るかどうかを判定します。
   拒否された**イベント全体**は直接破棄され、どのハンドラ（コマンドディスパッチャーを含む）もトリガーされません。
2. **モジュール次元**（`ErisPulse.scope`）：イベントが特定のモジュールのハンドラやコマンドに到達した時点で、セッション > Bot > プラットフォームの順に、そのモジュールが利用可能かどうかを判定し、**通過しない場合は静かにスキップ**されます。

```toml
# 例1：特定のグループのすべてのメッセージをブロードキャストしない
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# 例2：MyModuleを特定のBotからブロックする
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

この場合、そのグループのメッセージが到着したときに、`MyModule`のコマンドやイベントハンドラは**すべて実行されません**。これはバグではなく、フィルタリング機構です——「モジュールが反応しない」問題を調査する際は、まずスコープのアイデンティティとモジュールのバインディングを確認してください。

- フィルタリングログは**TRACE**レベルでのみ表示されます（`core.scope.identity_denied` / `core.scope.denied`）、デフォルトのINFOでは痕跡が見えません
- フレームワークレベルのハンドラ（`scope_exempt=True`のコマンドディスパッチャーなど）は**モジュール次元**の影響を受けませんが、**アイデンティティ次元**の影響を受けます（イベント全体が破棄されているため）
- コマンド実行前に3番目のフィルタがあります：コマンドユーザーアクセス制御（拒否時は「権限不足」を返します、上記参照）
- 4番目のフィルタは**イベント上書き**（下節参照）

> [!NOTE]
> **スコープフィルタリングとイベント認領（claim）の関係**：2つの静的なフィルタはハンドラの**スケジューリング前に**発生します——フィルタでスキップされたハンドラは実行されず、`event.done()` / `mark_processed()`の認領ステータスにも影響しません。イベントが認領されたかどうかは、**実際のハンドラの実行**（コマンドマッチによる認領、返信による認領、明示的な呼び出し）によってのみ決定されます；
> スコープ拒否自体は認領もブロックもしません（静かにスキップされ、メッセージは残りの配分チェーンを完了します）。

> スコープの設定、マッチングの構文、実行時APIは[スコープ（scope）](../../advanced/scope.md)を参照してください。

## イベント上書き：モジュールのコードを変更せずに、任意のイベントタイプの動作を上書き

> [!NOTE]
> この機能はErisPulse **2.8.0+** が必要です。

イベントハンドラは登録時に宣言されたパラメータ（`pattern` / `regex` / `master` / `hidden` など）は**開発者のデフォルト**に過ぎません。
一括上書きシステムは、ユーザーが**イベントタイプ**ごとに任意のモジュールの動作を上書きできるようにします——OneBot12標準タイプ（meta / message / notice / request）とErisPulse拡張タイプ（command）は、それぞれ独自の上書き可能なパラメータを持ちます：

| イベントタイプ | 上書き可能なパラメータ | 作用 |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | テキストのトリガ条件 + メッセージのサブタイプホワイトリスト |
| `notice` | `detail_types` / `pattern` / `regex` | 通知のサブタイプホワイトリスト + テキスト条件 |
| `request` | `detail_types` / `pattern` / `regex` | リクエストのサブタイプホワイトリスト + テキスト条件 |
| `meta` | `detail_types` | 元イベントのサブタイプホワイトリスト（connect / heartbeat など） |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | コマンドの実装パラメータ（ユーザー優先） |
| `acl`（command専用） | `allow` / `deny` | コマンドのユーザーホワイト/ブラックリスト（コマンド名のglob） |

```toml
# message：テキストのトリガ条件を上書き（コード内の条件とAND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "雑談*"

# notice：特定の通知サブタイプのみを対象にする
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command：実装パラメータを上書き（ユーザー優先——厳しくしたり緩めたりできる）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl：コマンドのユーザーホワイト/ブラックリスト（コマンド名のglob）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACLのデフォルト（false = 厳格モード：ACLがないと拒否）
acl_default_allow = true
```

実行時API（`from ErisPulse.Core.Event import overrides` または `sdk.Event.overrides`，
**タイプのサブネームスペース**——各タイプは対称的な `set` / `get` / `delete` 三つ組）：

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="雑談*")   # messageのテキスト条件
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # コマンドパラメータ
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # コマンドユーザーブラックリスト

overrides.message.get("ChatModule")     # {"pattern": "雑談*"}
overrides.message.delete("ChatModule")  # 開発者のデフォルトに戻す
```

- 上書き条件とハンドラのコード内の条件は**両方有効**（ANDの意味）；`command`のパラメータは開発者の宣言と**深くマージ**（上書きが優先）
- `detail_types`：イベントに `detail_type` がない場合は通す（未知のイベントを誤って殺さない）
- `pattern` / `regex`：テキストのないイベント（connect / heartbeat など）は制約を受けず、直接通す
- `command`の上書きキー `master` はストアキー `must_master` と同期；コマンドの禁止は `acl` deny で行う
- **キー名のマッピング説明**：`overrides.command.set("My", "restart", master=True)`のパラメータ名`master`は設定のエイリアスに過ぎず、実際のストアキーと`get()`の戻り値のキー名は**`must_master`**（`get()`は`{"must_master": true}`を返す）——実行時の判定で読み取るのはストアキーなので、`master`キー名で読み取らないでください
- 設定は変更されるとすぐに有効（ホットアップデート）、形式チェックのアラート（未知のパラメータ / 壊れた項目は無視）

## リンク制御：認領とブロック

> [!NOTE]
> `event.done()` / `event.mark_processed()`の`claim=` / `stop=`パラメータはErisPulse **2.7.1+**が必要です。

ErisPulseは「認領」と「ブロック」の2つの正交的な意味を解き、`event.done()`で統一的に制御することで、コマンド処理の周囲にログ、監査、権限などの観察層を重ねることが容易になります。

**2つの概念の正確な定義：**

- **認領（claim）**：イベントがこのハンドラによって処理されたことをマークする（`_processed`に書き込む）。コマンドディスパッチャーは認領されたイベントを見ると**重複を避ける**——同じメッセージが複数のコマンドハンドラに重複して処理されないようにする。典型的な場面：コマンドがマッチした後に認領し、コマンドディスパッチャーが介入しないようにする。
- **ブロック（stop）**：イベントが**より低い優先度**のハンドラに伝播しないようにする（`_propagation_stopped`に書き込む）。低優先度のハンドラはこのイベントを見なくなる。典型的な場面：高優先度のハンドラがイベントを完全に処理した後、低優先度のハンドラが実行されないようにする。

| `event.done(...)` | 認領 | ブロック | 場面 |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | コマンド / ハンドラ処理完了の標準的なやり方 |
| `event.done(stop=False)` | ✔ | ✘ | 認領のみ、低優先度の観察者（ログ / 統計）は引き続き見られる |
| `event.done(claim=False)` | ✘ | ✔ | ブロックのみ（ファイアウォール / 限流）、認領は行わない |

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
        event.done(claim=False)  # ブロックのみ：低優先度は実行されないが、認領は行わない
```

### コマンドと返信の block 設定

**コマンドのマッチは認領する**：メッセージが登録されたコマンド名（子コマンド/エイリアスを含む）にマッチすると、その後の作用域や権限判定の結果に関わらず、認領され、デフォルトでブロックされる——権限拒否されたコマンドは低優先度のメッセージハンドラに二重に応答しない（「コマンドが拒否された後にon_messageがもう一度応答する」二重応答を防止する）。

ブロックを解除して、低優先度の観察者（ログ / 監査 / 権限）がこれらのメッセージを見られるようにするには、設定で解除できます：

```toml
[ErisPulse.event.command]
block = false   # コマンドメッセージは低優先度のハンドラに伝播する（認領は影響を受けない、重複消費されない）

[ErisPulse.event.wait_reply]
block = false   # wait_replyで消費された返信は低優先度のハンドラに伝播する
```

> 注意：`block`は**ブロック**（stop）を制御するだけで、**認領**（claim）には影響しない——マッチしたコマンドは決してメッセージハンドラに重複消費されない；コマンドにマッチしないメッセージは通常通りメッセージハンドラに伝播する。

## 通知イベントの処理

### 友達追加

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "新朋友"
    await event.reply(f"友達追加ありがとうございます、{nickname}さん！")
```

### グループメンバーの増加

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"ようこそ、{user_id}さん、グループ{group_id}に参加しました")
```

### グループメンバーの減少

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"{user_id}さんがグループ{group_id}を離脱しました")
```

## 要求イベントの処理

### 友達リクエスト

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"友達リクエストを受け取りました: {user_id}, 付言: {comment}")
    
    # ここではアダプタAPIを使ってリクエストを処理できます
    # 具体的な実装は各アダプタのドキュメントを参照してください
```

### グループ招待リクエスト

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"グループ{group_id}からの招待、{user_id}さんからです")
```

## 元イベントの処理

### 接続イベント

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform}プラットフォームに接続されました")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"{platform}プラットフォームが切断されました")
```

### ハートビートイベント

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform}のハートビートを検出しました")
```

### Botのステータス照会

アダプタがmetaイベントを送信した後、フレームワークは自動的にBotのステータスを追跡し、いつでも照会できます：

```python
from ErisPulse import sdk

# 特定のBotがオンラインかどうかを確認
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Botはオンラインです")

# 現在オンラインのすべてのBotをリストアップ
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# 完全なステータスサマリーを取得
summary = sdk.adapter.get_status_summary()
```

## 対話処理

### replyメソッドを使用した返信の送信

`event.reply()`メソッドは、@、返信などの機能を備えた様々な修飾パラメータをサポートし、メッセージの送信が容易になります：

```python
# 簡単な返信
await event.reply("こんにちは")

# 異なるタイプのメッセージを送信
await event.reply("http://example.com/image.jpg", method="Image")  # 画像
await event.reply("http://example.com/voice.mp3", method="Voice")  # 音声

# 単一のユーザーを@する
await event.reply("こんにちは", at_users=["user123"])

# 複数のユーザーを@する
await event.reply("皆さんこんにちは", at_users=["user1", "user2", "user3"])

# メッセージに返信
await event.reply("返信内容", reply_to="msg_id")

# 全体を@する
await event.reply("お知らせ", at_all=True)

# @ユーザーと返信を組み合わせる
await event.reply("内容", at_users=["user1"], reply_to="msg_id")
```

### ユーザーの返信を待つ

```python
@command("ask", help="ユーザーに質問")
async def ask_handler(event):
    await event.reply("お名前を教えてください:")
    
    # 30秒のタイムアウトでユーザーの返信を待つ
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}さん！")
    else:
        await event.reply("タイムアウトしました、再度入力してください。")
```

> [!TIP]
> **待機中もコマンドは使用可能**（2.8.3+）：コマンド接頭辞で始まり、登録されたコマンドに一致するメッセージ（例：`/cancel`）は**コマンドとして実行**され、返信内容ではなく、待機は継続します——ユーザーはいつでもキャンセル/切り替えでき、コマンド実行後も返信を続けることができます。以前の「すべてのテキストを吸収する」挙動が必要な場合は：`ErisPulse.event.wait_reply.cmdpass = true`を設定するか、`wait_reply(cmdpass=True)`で一時的に設定してください。

### 検証付きの待機返信

```python
@command("age", help="年齢を尋ねる")
async def age_handler(event):
    def validate_age(event_data):
        """年齢が有効かどうかを検証する"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("年齢を入力してください (0-150):")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"あなたの年齢は{age}歳です")
    else:
        await event.reply("無効な入力またはタイムアウト")
```

### コールバック付きの待機返信

```python
@command("confirm", help="操作を確認する")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["はい", "yes", "y"]:
            await event.reply("操作が確認されました！")
        else:
            await event.reply("操作がキャンセルされました。")
    
    await event.reply("この操作を実行しますか？(はい/いいえ)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### 確認対話 (confirm)

ユーザーが肯定または否定を確認するのを待つ、自動的に中英文の確認語を認識する：

```python
@command("confirm", help="操作を確認する")
async def confirm_handler(event):
    if await event.confirm("この操作を実行しますか？"):
        await event.reply("確認済み、実行中...")
    else:
        await event.reply("キャンセルされました")

# 自定義の確認語
if await event.confirm("続ける？", yes_words={"go", "続ける"}, no_words={"stop", "停止"}):
    pass
```

### 選択メニュー (choose)

ユーザーはオプションの番号またはテキストを返信できます：

```python
@command("choose", help="選択")
async def choose_handler(event):
    choice = await event.choose(
        "色を選択してください：",
        ["赤", "緑", "青"]
    )
    
    if choice is not None:
        colors = ["赤", "緑", "青"]
        await event.reply(f"選択しました：{colors[choice]}")
    else:
        await event.reply("タイムアウトしました")
```

**マージモード**：`merge_prompt=True`の場合、オプションをプロンプトにマージし、指定された`method`で1つのメッセージとして送信します：

```python
# Markdownでマージ後のプロンプト + オプションを送信
choice = await event.choose(
    "## 色を選択してください\n{options}\n番号を入力してください",
    ["赤", "緑", "青"],
    method="Markdown",
    merge_prompt=True,
)
```

> `{options}`のプレースホルダーはオプションの挿入位置を制御します；書かなければプロンプトの末尾に追加されます。
> `placeholder`パラメータでプレースホルダーをカスタマイズできます（例：`placeholder="[choices]"`）。
> `options_format="auto"`（デフォルト）はmethodに応じてスタイルを選択します：Markdown→無序リスト、Html→順序リスト、その他の場合は純粋なテキストリスト。
> テキスト系メソッド（Text/Markdown/Htmlなど）はデフォルトでオプションを末尾にマージします；非テキスト系メソッド（Imageなど）はデフォルトで2つのメッセージに分割します。

### フォーム収集 (collect)

複数ステップでユーザー入力を収集します：

```python
@command("register", help="登録")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "お名前を入力してください："},
        {"key": "age", "prompt": "年齢を入力してください：", 
         "validator": lambda e: e.get_text().isdigit()},
        {"key": "email", "prompt": "メールアドレスを入力してください："}
    ])
    
    if data:
        await event.reply(f"登録完了！\nお名前：{data['name']}\n年齢：{data['age']}\nメールアドレス：{data['email']}")
    else:
        await event.reply("登録がタイムアウトまたは入力が無効です")
```

### 任意のイベントを待つ (wait_for)

条件を満たす任意のイベントを待つ、同一ユーザーに限定されない：

```python
@command("wait_member", help="新メンバーを待つ")
async def wait_member_handler(event):
    await event.reply("グループメンバーの追加を待っています...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"ようこそ、{evt.get_user_id()}さん！")
    else:
        await event.reply("タイムアウトしました")
```

### マルチラウンド対話 (conversation)

インタラクティブなマルチラウンド対話コンテキストを作成します：

```python
@command("survey", help="アンケート")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("アンケートにご協力ありがとうございます！")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("対話がタイムアウトしました、さようなら！")
            break
        
        text = reply.get_text()
        
        if text == "終了":
            await conv.say("さようなら！")
            break
        
        await conv.say(f"入力：{text}、続けるか「終了」で終了します")
```

### 内蔵の確認語

ErisPulseには中英文の確認語の集合が内蔵されています：

- **確認語** (`CONFIRM_YES_WORDS`): はい、yes、y、確認、確定、ok、true、対、うん、行、同意、大丈夫、没问题...
- **否定語** (`CONFIRM_NO_WORDS`): いいえ、no、n、キャンセル、不要、ダメ、cancel、false、間違い、拒否、できません...

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
    
    # 元データ
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

内蔵メソッドに加えて、各プラットフォームアダプタはプラットフォーム固有のメソッドを登録し、プラットフォーム特有のデータにアクセスしやすくします。

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

プラットフォームが特定のメソッドを登録しているかどうかを確認するには、そのプラットフォームに登録されたメソッドを照会できます：

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> 各プラットフォームが登録する固有メソッドは、対応する[プラットフォームドキュメント](../platform-guide/)を参照してください。

## イベント処理のベストプラクティス

### 1. 例外処理

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
        await event.reply("処理に失敗しました、後でもう一度お試しください")
```

### 2. ログ記録

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"メッセージを処理: {user_id} - {text}")
    
    # モジュール独自のロガーを使用
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"詳細なデバッグ情報")
```

### 3. 条件処理

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """条件処理 - ハンドラ内で判定"""
    # 特定のユーザーのメッセージだけを処理する
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # 特定のキーワードを含むメッセージだけを処理する
    if "キーワード" not in event.get_text():
        return
    
    await event.reply("条件が満たされました、メッセージを処理します")
```

## 次に進む

- [よくあるタスクの例](common-tasks.md) - 機能の実装方法を学ぶ（送信の高度な機能：再試行/タイムアウト/バッチ送信を含む）
- [プラットフォーム特性ガイド](../platform-guide/README.md) - Send DSLチェーン送信、送信ルール、バッチ構築の完全な説明
- [Eventラッパークラスの詳細](../developer-guide/modules/event-wrapper.md) - Eventオブジェクトの詳細を理解する
- [ユーザー使用ガイド](../user-guide/) - 設定とモジュール管理を理解する