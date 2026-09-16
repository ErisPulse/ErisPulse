# イベント処理入門

このガイドでは、ErisPulse における各種イベントの処理方法を紹介します。

## イベントタイプの概要

ErisPulse は以下のイベントタイプをサポートしています：

| イベントタイプ | 説明 | 適用シーン |
|---------|------|---------|
| メッセージイベント | ユーザーが送信した任意のメッセージ | チャットボット、コンテンツフィルタ |
| コマンドイベント | コマンドプレフィックスで始まるメッセージ | コマンド処理、機能の入口 |
| 通知イベント | システム通知（友達追加、グループメンバー変更など） | ホームメッセージ、ステータス通知 |
| 要求イベント | ユーザーの要求（友達リクエスト、グループ招待） | 要求の自動処理 |
| 元イベント | システムイベント（接続、ハートビート） | 接続監視、ステータスチェック |

## メッセージイベントの処理

> **注意**: イベントハンドラでは `Event` クラスの型アノテーションを使用することを推奨します。これにより、IDEの自動補完と型チェックがサポートされます。

```python
from ErisPulse.Core.Event import Event  # Eventクラスの型アノテーション用にインポート
```

### すべてのメッセージを監視

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"{user_id}からのメッセージを受信しました: {text}")
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
    sdk.logger.info(f"グループ{group_id}で{user_id}がメッセージを送信しました")
```

### @メッセージを監視

```python
@message.on_at_message()
async def at_handler(event: Event):
    # @されたユーザーのリストを取得
    mentions = event.get_mentions()
    await event.reply(f"あなたが@したユーザー: {mentions}")
```

### ワイルドカードと正規表現による監視

`on_message` / `on_private_message` / `on_group_message` / `on_at_message` の4つのメッセージデコレータは、`pattern`（globワイルドカード）と `regex`（正規表現）をサポートしています。一致しないメッセージは**ハンドラをトリガーしません**：

```python
# globワイルドカード：* 任意の文字列、? 1文字、[seq] 文字集合
@message.on_message(pattern="サインイン*")
async def signin_handler(event: Event):
    await event.reply("サインイン成功")

# 正規表現：金額をマッチ
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"金額を受信しました: {event.get_text()}")

# pattern と regex が両方指定された場合 → 両方とも一致する必要がある
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` でもこの2つのパラメータがサポートされます（[返信の待機機能](../developer-guide/modules/event-wrapper.md#待機返信機能)を参照）。

## コマンドイベントの処理

### 基本コマンド

```python
from ErisPulse.Core.Event import command

@command("help", help="ヘルプ情報を表示")
async def help_handler(event):
    help_text = """
利用可能なコマンド：
/help - ヘルプ情報を表示
/ping - 接続をテスト
/info - 情報を表示
    """
    await event.reply(help_text)
```

### コマンドの別名

```python
@command(["help", "h"], aliases=["ヘルプ"], help="ヘルプ情報を表示")
async def help_handler(event):
    await event.reply("ヘルプ情報...")
```

ユーザーは以下のいずれかの方法で呼び出すことができます：
- `/help`
- `/h`
- `/ヘルプ`

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

引数は、コマンド名の大小文字を無視する設定があっても、ユーザー入力のままの形式を保持します（`permission` は大文字小文字を無視しますが、引数には影響しません）。

### コマンドグループ

```python
@command("admin.reload", group="admin", help="モジュールを再ロード")
async def reload_handler(event):
    await event.reply("モジュールを再ロードしました")

@command("admin.stop", group="admin", help="ボットを停止")
async def stop_handler(event):
    await event.reply("ボットを停止しました")
```

`group` パラメータは、ヘルプリストの分類にのみ使用されます。上記の例では、`admin.reload` は**全体のコマンド名**です（ドットは命名スタイルであり、ユーザーは `/admin.reload` と入力する必要があります）。

### サブコマンド

コマンド名は**スペースで区切られた複数のトークン**形式をサポートし、`/admin add`、`/admin user ban` などのサブコマンドを実現します：

```python
@command("admin", help="管理コマンド")
async def admin_handler(event):
    await event.reply("使い方：/admin add | /admin remove")

@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    target = event.get_command_args()[0]
    await event.reply(f"{target}を追加しました")

@command("admin remove", aliases=["a remove"], help="管理者を削除")
async def admin_remove_handler(event):
    await event.reply("削除しました")
```

マッチングルール（**最長前方一致**）：

- `/admin add x` は `admin add` に優先的にマッチし、`event.get_command_args()` は `["x"]` を返します（サブコマンド名以降の引数）
- `admin` だけが登録されている場合、`/admin add x` は `admin` にマッチし、`get_command_args()` は `["add", "x"]` を返します（従来の動作）
- 別名は複数トークン形式（`a remove`）もサポートし、単一トークンの別名（`a`）もサブコマンドを指すことができます
- 親子コマンドが同時に登録されている場合、登録されていないサブコマンドの入力（`/admin list x`）は親コマンドにフォールバックします

**権限継承**: 子コマンドに `permission` が宣言されていない場合、直近に `permission` を宣言した祖先コマンドを自動的に継承します——`/admin` に保護を宣言すれば、その下のすべてのサブコマンドも自動的に保護されます。ただし、子コマンド自身で宣言した `permission` は優先されます：

```python
def is_admin(event):
    return event.get_user_id() in {"user123"}

@command("admin", permission=is_admin, help="管理コマンド")
async def admin_handler(event):
    ...

# permissionはis_adminを自動的に継承
@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    ...
```

注意: `master=True` と `hidden` は**継承されません**。必要に応じて子コマンドで個別に宣言してください。ユーザーACL（ホワイトリスト/ブラックリスト）はコマンド全名でマッチし、`"admin*"` などのglobルールはサブコマンド全体をカバーできます。

`/help` のコマンド一覧では、サブコマンドは表示可能な親コマンドの下にインデントして表示されます（`admin` → `admin add` は1段階インデント、`admin user` → `admin user ban` は2段階インデント）。

### コマンド権限とアクセス制御

コマンドの権限は3層に分かれ、上から下へ順に判定されます（**上層が拒否された場合、下層は見られません**）：

```python
# ① コマンド権限ACL（ユーザー側の設定）：コマンドのユーザーホワイトリスト/ブラックリストで、拒否時は「権限不足」と返信
# ② master=True —— フレームワークの所有者のみ実行可能（フレームワークが自動的にチェックし、拒否時は「権限不足」と返信）
@command("restart", master=True, help="モジュールを再起動")
async def restart_handler(event):
    await event.reply("モジュールを再起動しました")

# ③ permission=関数 —— コマンド自身の制御ロジック（Trueを返す場合のみ実行）
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="管理パネル")
async def panel_handler(event):
    await event.reply("管理パネルへようこそ")
```

**コマンドユーザーACL**（`ErisPulse.event.command.acl`）：ユーザーは任意のコマンドにユーザーホワイトリスト/ブラックリストを設定でき、コマンド名は正確またはglobパターン（例: `"roll*"`）で、拒否時は「権限不足」と返信されます：

```toml
# config.toml —— restartコマンドは123456のみ実行可能；666は一律拒否
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

判定順序：`deny`が一致 → 拒否；`allow`が空でないかつ一致しない → 拒否；ACLが設定されていない場合は、`event.command.default_allow`（`false` = 厳格モード、ACLがない場合は拒否；`true`の場合はデベロッパーが`master=True` / `permission`をデフォルトで使用）に従います。実行時API（コマンド名はglobパターンで）：

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # 允許リスト
command.deny_user("restart", "onebot11", "666")       # 拒絶リスト
command.remove_acl("restart")                          # ホワイト/ブラックリストを削除
command.get_acl("restart")                             # 現在のリストを取得
```

> コマンドハンドラはイベントパッケージからインポート：`from ErisPulse.Core.Event import command`；またSDKイベントパッケージからもアクセス可能：`sdk.Event.command`（両者は同一のシングルトンです）。モジュール内では通常、コマンドデコレータと共にインポートされています（`from ErisPulse.Core.Event import command`）。

コマンドやユーザーをまたいだ**イベントレベル**のアクセス制御（特定のユーザー/グループ/ボットのメッセージを受信するか）は、**スコープ**（`scope.identity`）で行います。**モジュールレベル**の可用性（どのモジュールが使えるか）は、**スコープ**（`scope.platforms / bots / sessions`）で行います。
詳細は[スコープ（scope）](../advanced/scope.md)を参照してください。

> 推奨：コマンド内部でビジネスロジックを連動させる場合は `master=True` / `permission` を使用し、純粋にユーザー/グループでアクセス制御を行う場合はスコープアイデンティティ次元を使用し、モジュールの可用性を制御する場合はスコープモジュール次元を使用してください。

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

### 並行イベント処理

ErisPulseのイベントシステムは**同じ優先度では並行、異なる優先度では直列**のスケジューリングモデルを採用しています：

```
イベントが到着
    ↓
priority=10 組: [ハンドラC || ハンドラD] 並行 → 結果を結合
    ↓ (中断されない場合)
priority=0 組: [ハンドラA || ハンドラB] 並行 → 結果を結合
    ↓
...
```

- **同じ優先度での並行**：優先度が同じ複数のハンドラは同時に実行され、スループットを向上させます
- **異なる優先度での直列**：異なる優先度のグループは順番に実行されます（数値が大きいほど先に実行）、高優先度ハンドラが先に実行されるようにします
- **Copy-On-Write**：ハンドラが変更を加えない場合はコピーを作成せず、ゼロオーバーヘッドを確保します
- **競合処理**：同じ優先度で複数のハンドラが同じフィールドを変更した場合、最後に変更された値を使用し、警告ログを記録します
- **中断機構**：任意のハンドラが `event.done()`（デフォルト）または `event.done(claim=False)` を呼び出した後、以降の低優先度グループはスキップされます。認領とブロックの違いは、以下の[「リンク制御：認領とブロック」](#リンク制御認領とブロック)を参照してください。

```python
# 例：同じ優先度のハンドラが並行実行される
@message.on_message(priority=0)
async def handler_a(event):
    # タスクAを処理
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # handler_aと並行に実行される
    event['result_b'] = process_b()

# 異なる優先度で直列実行される
@message.on_message(priority=10)
async def handler_c(event):
    # 最も優先度が高い、最初に実行される
    pass
```

> **並行上限**：すべてのマッチするハンドラのTaskは**即時作成**されますが、シグナルマネージャによって**同時に実行される数**を制限します。デフォルト上限は**64**（`ErisPulse.framework.handler_max_concurrency`、ホットアップデート対応）です。上限を超えたTaskはシグナルマネージャで待機し、前の処理が完了した後に実行されます。イベントのピーク時にはこれが「圧力緩和弁」になります。
>
> **遅延ログ**：個々のハンドラの処理時間が**1秒**を超えると、フレームワークはログにWARNINGを出力します（`handler_slow`）。`wait_reply`の待機時間は処理時間から除外されるため、「返信を待つ」ことで誤って遅延と判定されることはありません。

## スコープフィルタリング：なぜ私のモジュールはメッセージを受け取らないのか

イベントが到着した後、2つの**静か**なフィルタリングが行われます（返信もエラーも出ません）：

1. **アイデンティティ次元**（`ErisPulse.scope.identity`）：イベントが配信入口に到着した時点で、ユーザー > グループ > ボット > アダプターの順に判定し、受信するかどうかを決定します。拒否された**イベント全体**は破棄され、どのハンドラ（コマンドディスパッチャーを含む）もトリガーされません。
2. **モジュール次元**（`ErisPulse.scope`）：イベントが特定のモジュールのハンドラ/コマンドに到着した時点で、セッション > ボット > プラットフォームの順に判定し、そのモジュールが利用可能かどうかを判断します。**利用不可**の場合は静かにスキップされます。

```toml
# 例1：特定のグループのすべてのメッセージを伝播しない
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# 例2：特定のボットからMyModuleをブロック
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

この場合、そのグループのメッセージが到着しても、`MyModule`のコマンドやイベントハンドラは**すべて呼び出されません**。これはバグではなく、フィルタリング機構です。モジュールが反応しない場合のトラブルシューティングでは、まずスコープのアイデンティティとモジュールのバインディングを確認してください。

- フィルタリングのログは**TRACE**レベルでのみ表示されます（`core.scope.identity_denied` / `core.scope.denied`）、デフォルトのINFOレベルでは痕跡が見えません
- フレームワークレベルのハンドラ（コマンドディスパッチャー `scope_exempt=True`）は**モジュール次元**の影響を受けませんが、**アイデンティティ次元**の影響を受けます（イベント全体が破棄されているため）
- コマンド実行前には3番目のフィルタリングがあります：コマンドユーザーACL（拒否時は「権限不足」と返信、上節参照）
- 4番目のフィルタリングは**イベントオーバーライド**（以下参照）

> スコープの設定、マッチングの構文、実行時APIは[スコープ（scope）](../../advanced/scope.md)を参照してください。

## イベントオーバーライド：モジュールのコードを変更せずに、任意のイベントタイプの動作を上書きする

> [!NOTE]
> この機能はErisPulse **2.8.0+** が必要です。

イベントハンドラの登録時に宣言されたパラメータ（`pattern` / `regex` / `master` / `hidden` など）は**開発者のデフォルト**です。統一されたオーバーライドシステムにより、ユーザーは**イベントタイプ**ごとに任意のモジュールの動作を上書きできます。OneBot12標準タイプ（meta / message / notice / request）とErisPulse拡張タイプ（command）は、それぞれ固有の上書き可能なパラメータを持っています：

| イベントタイプ | 上書き可能なパラメータ | 作用 |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | テキストトリガー条件 + メッセージサブタイプホワイトリスト |
| `notice` | `detail_types` / `pattern` / `regex` | 通知サブタイプホワイトリスト + テキスト条件 |
| `request` | `detail_types` / `pattern` / `regex` | リクエストサブタイプホワイトリスト + テキスト条件 |
| `meta` | `detail_types` | メタイベントサブタイプホワイトリスト（connect / heartbeat など） |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | コマンド実装パラメータ（ユーザーが優先） |
| `acl`（command専用） | `allow` / `deny` | コマンドユーザーホワイトリスト/ブラックリスト（コマンド名のglob） |

```toml
# message：テキストトリガー条件を上書き（コード内の条件とAND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "雑談*"

# notice：特定の通知サブタイプのみを応答
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command：実装パラメータを上書き（ユーザーが優先——厳しくしたり緩めたり可能）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl：コマンドユーザーホワイトリスト/ブラックリスト（コマンド名のglobで跨る）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACLのデフォルト（false = 厳格モード：ACLがない場合は拒否）
acl_default_allow = true
```

実行時API（`from ErisPulse.Core.Event import overrides` または `sdk.Event.overrides`、**タイプごとのサブネームスペース**——各タイプごとに `set` / `get` / `delete` の3つの関数）：

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="雑談*")   # messageのテキスト条件
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # コマンドパラメータ
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # コマンドユーザーブラックリスト

overrides.message.get("ChatModule")     # {"pattern": "雑談*"}
overrides.message.delete("ChatModule")  # 開発者のデフォルトに戻す
```

- 上書き条件とハンドラコード内の条件は**同時に有効**（ANDの意味）；`command`のパラメータは開発者の宣言と**深くマージ**（上書きが優先）
- `detail_types`：イベントに `detail_type` が欠けている場合、放行されます（未知のイベントを誤って殺しません）
- `pattern` / `regex`：テキストのないイベント（connect / heartbeat など）は制約を受けず、直接放行されます
- `command`の上書きキー `master` は同期的にストレージキー `must_master` にマッピングされます；コマンドの禁止は `acl` denyを通じて行います
- 設定は変更されると即座に有効（ホットアップデート）、フォーマットの検証が行われ、警告が出ます（未知のパラメータ / 不正なエントリは無視されます）

## リンク制御：認領とブロック

> [!NOTE]
> `event.done()` / `event.mark_processed()` の `claim=` / `stop=` パラメータは、ErisPulse **2.7.1+** が必要です。

ErisPulseでは、「認領」と「ブロック」の2つの正交的な概念を解消し、`event.done()`で統一的に制御することで、コマンド処理の周囲にログ、監査、権限などの観測層を重ねることが容易になります。

**2つの概念の正確な定義は**：

- **認領（claim）**：イベントがこのハンドラによって処理されたことをマークします（`_processed`に書き込み）。コマンドディスパッチャーは認領されたイベントを**重複処理を避ける**ためにスキップします。典型的なケース：コマンドがマッチした後に認領し、コマンドディスパッチャーが再び介入しないようにします。
- **ブロック（stop）**：イベントが**より低い優先度**のハンドラに伝播しないようにします（`_propagation_stopped`に書き込み）。低優先度のハンドラはこのイベントを見られなくなります。典型的なケース：高優先度のハンドラがイベントを完全に処理した後、低優先度のハンドラが再び実行されないようにします。

| `event.done(...)` | 認領 | ブロック | 場合 |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | コマンド / ハンドラ処理完了の標準的なやり方 |
| `event.done(stop=False)` | ✔ | ✘ | 認領のみ：低優先度の観測者（ログ / 統計）はまだ見ることができます |
| `event.done(claim=False)` | ✘ | ✔ | ブロックのみ（例：ファイアウォール / 限流）、重複処理はしない |

`event.done(claim=, stop=)` は `event.mark_processed(claim=, stop=)` の別名であり、パラメータと動作は完全に等価です。

```python
@command("help")
async def help_cmd(event):
    event.done()            # 認領 + ブロック（コマンド処理完了の標準的なやり方）

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # 認領のみ：低優先度のハンドラはまだ実行されます（ログ / 統計）

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # ブロックのみ：低優先度のハンドラは実行されませんが、重複処理はしません
```

### コマンドと返信の block 設定

**コマンドがマッチした瞬間に認領**：メッセージが登録されたコマンド名（サブコマンド/別名を含む）にマッチすると、その後の作用域や権限判定の結果に関わらず、認領され、デフォルトでブロックされます——権限拒否されたコマンドは低優先度のメッセージハンドラに二重に応答することはありません。

ブロックを解除して、低優先度の観測者（ログ / 審計 / 権限）がこれらのメッセージを見られるようにするには、設定を変更します：

```toml
[ErisPulse.event.command]
block = false   # コマンドメッセージは低優先度のハンドラに流れ続けます（認領は影響しません、二重消費はされません）

[ErisPulse.event.wait_reply]
block = false   # wait_replyで消費された返信は低優先度のハンドラに流れ続けます
```

> 注意：`block`は**ブロック**（stop）だけを制御し、**認領**（claim）には影響しません。マッチしたコマンドは決してメッセージハンドラに二重に消費されません。コマンドにマッチしなかったメッセージは通常通りメッセージハンドラに流れます。

## 通知イベントの処理

### 友達追加

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "新朋友"
    await event.reply(f"友達追加を歓迎します、{nickname}！")
```

### グループメンバーの増加

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"新メンバー{user_id}がグループ{group_id}に参加しました")
```

### グループメンバーの減少

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"メンバー{user_id}がグループ{group_id}から離脱しました")
```

## 要求イベントの処理

### 友達リクエスト

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"友達リクエストを受け取りました: {user_id}, 附言: {comment}")
    
    # アダプターAPIを使ってリクエストを処理することもできます
    # 具体的な実装は各アダプターのドキュメントを参照してください
```

### グループ招待リクエスト

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"グループ{group_id}からの招待、{user_id}からです")
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

### Botステータスの照会

アダプターがmetaイベントを送信すると、フレームワークは自動的にBotのステータスを追跡し、いつでも照会できます：

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

## インタラクティブ処理

### replyメソッドを使って返信を送信

`event.reply()`メソッドは、@、返信などの機能を備えた様々な修飾パラメータをサポートし、メッセージの送信が簡単になります：

```python
# 簡単な返信
await event.reply("こんにちは")

# 異なるタイプのメッセージを送信
await event.reply("http://example.com/image.jpg", method="Image")  # 画像
await event.reply("http://example.com/voice.mp3", method="Voice")  # 音声

# 単一のユーザーに@
await event.reply("こんにちは", at_users=["user123"])

# 複数のユーザーに@
await event.reply("みんなこんにちは", at_users=["user1", "user2", "user3"])

# メッセージに返信
await event.reply("返信内容", reply_to="msg_id")

# 全員に@
await event.reply("お知らせ", at_all=True)

# 組み合わせ: @ユーザー + メッセージ返信
await event.reply("内容", at_users=["user1"], reply_to="msg_id")
```

### ユーザーの返信を待つ

```python
@command("ask", help="ユーザーに質問")
async def ask_handler(event):
    await event.reply("名前を入力してください:")
    
    # ユーザーの返信を待つ、タイムアウト時間30秒
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}！")
    else:
        await event.reply("タイムアウトしました、もう一度入力してください。")
```

### 適切な入力の待つ

```python
@command("age", help="年齢を尋ねる")
async def age_handler(event):
    def validate_age(event_data):
        """年齢が有効かどうかを検証"""
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
        await event.reply(f"年齢は{age}歳です")
    else:
        await event.reply("入力が無効またはタイムアウトしました")
```

### コールバック付きの待機返信

```python
@command("confirm", help="操作を確認")
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

ユーザーの確認または否定を待つ、自動的に中英の確認単語を認識する：

```python
@command("confirm", help="操作を確認")
async def confirm_handler(event):
    if await event.confirm("この操作を実行しますか？"):
        await event.reply("確認しました、実行中...")
    else:
        await event.reply("キャンセルしました")

# 自定義の確認単語
if await event.confirm("続行しますか？", yes_words={"go", "続行"}, no_words={"stop", "停止"}):
    pass
```

### 選択メニュー (choose)

ユーザーは選択番号または選択項目のテキストを返すことができます：

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
        await event.reply("選択がタイムアウトしました")
```

**マージモード**：`merge_prompt=True` の場合、選択肢をプロンプトにマージし、`method` で指定された形式で1つのメッセージとして送信します：

```python
# Markdownでマージされたプロンプト + 選択肢を送信
choice = await event.choose(
    "## 色を選択してください\n{options}\n番号を入力してください",
    ["赤", "緑", "青"],
    method="Markdown",
    merge_prompt=True,
)
```

> `{options}` プレースホルダーは選択肢の挿入位置を制御します；書かなければプロンプトの末尾に追加されます。
> `placeholder` パラメータでプレースホルダーをカスタマイズできます（例：`placeholder="[choices]"`）。
> `options_format="auto"`（デフォルト）は、`method` に応じてスタイルを自動選択します：Markdown→無番号リスト、Html→番号付きリスト、その他→テキストリスト。
> テキスト系メソッド（Text/Markdown/Htmlなど）はデフォルトで選択肢を末尾にマージします；非テキスト系メソッド（Imageなど）はデフォルトで2つのメッセージに分割します。

### フォーム収集 (collect)

複数ステップでユーザーの入力を収集します：

```python
@command("register", help="登録")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "名前を入力してください："},
        {"key": "age", "prompt": "年齢を入力してください：", 
         "validator": lambda e: e.get_text().isdigit()},
        {"key": "email", "prompt": "メールアドレスを入力してください："}
    ])
    
    if data:
        await event.reply(f"登録完了！\n名前：{data['name']}\n年齢：{data['age']}\nメールアドレス：{data['email']}")
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
        await event.reply(f"新メンバーを歓迎します：{evt.get_user_id()}")
    else:
        await event.reply("待機がタイムアウトしました")
```

### 多段対話 (conversation)

インタラクティブな多段対話コンテキストを作成します：

```python
@command("survey", help="アンケート調査")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("アンケート調査にようこそ！")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("対話がタイムアウトしました、さようなら！")
            break
        
        text = reply.get_text()
        
        if text == "終了":
            await conv.say("さようなら！")
            break
        
        await conv.say(f"入力しました：{text}、続けて入力するか、'終了'と入力して終了します")
```

### 内置の確認単語

ErisPulseには中英の確認単語集合が内蔵されています：

- **確認単語** (`CONFIRM_YES_WORDS`): はい、yes、y、確認、確定、好、いい、ok、true、対、うん、行、同意、問題ない...
- **否定単語** (`CONFIRM_NO_WORDS`): いいえ、no、n、キャンセル、不、不要、不行、cancel、false、間違い、拒否、不可...

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
    
    # ボット情報
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

内蔵メソッドに加えて、各プラットフォームアダプターはプラットフォーム固有のメソッドを登録し、プラットフォーム特有のデータにアクセスするのに便利です。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # プラットフォームごとに固有メソッドを呼び出す
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram固有メソッド
    elif platform == "email":
        subject = event.get_subject()           # メール固有メソッド
```

プラットフォームが特定のメソッドを登録しているかどうかを確認するには、そのプラットフォームが登録したメソッドを照会できます：

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> 各プラットフォームが登録した固有メソッドは、対応する[プラットフォームドキュメント](../platform-guide/)を参照してください。

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
        await event.reply("処理失敗、後でもう一度お試しください")
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
    """条件処理 - ハンドラ内部で判定"""
    # 特定のユーザーのメッセージのみ処理
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # 特定のキーワードを含むメッセージのみ処理
    if "キーワード" not in event.get_text():
        return
    
    await event.reply("条件が満たされたので、メッセージを処理します")
```

## 次のステップ

- [よくあるタスクの例](common-tasks.md) - 機能の実装方法を学ぶ（含むメッセージ送信の高度な機能：リトライ/タイムアウト/バッチ）
- [プラットフォーム特性ガイド](../platform-guide/README.md) - Send DSLチェーン送信、送信ルール、バッチ構築の完全な説明
- [Eventラッパークラスの詳細](../developer-guide/modules/event-wrapper.md) - Eventオブジェクトの詳細を理解する
- [ユーザー使用ガイド](../user-guide/) - 設定とモジュール管理を理解する