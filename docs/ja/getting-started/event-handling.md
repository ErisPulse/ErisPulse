# イベント処理の入門

このガイドでは、ErisPulse におけるさまざまなイベントの処理方法について説明します。

## イベントの種類の概要

ErisPulse は以下のイベントの種類をサポートしています。

| イベントの種類 | 説明 | 適用場面 |
|---------|------|---------|
| メッセージイベント | ユーザーが送信した任意のメッセージ | チャットボット、コンテンツフィルタリング |
| コマンドイベント | コマンド接頭辞で始まるメッセージ | コマンド処理、機能のエントリポイント |
| 通知イベント | システム通知（友達追加、グループメンバーの変更など） | メッセージの歓迎、状態通知 |
| 要求イベント | ユーザーの要求（友達リクエスト、グループ招待） | 要求の自動処理 |
| 元イベント | システムレベルのイベント（接続、ハートビート） | 接続監視、状態チェック |

## メッセージイベントの処理

> **注意**: IDEの自動補完と型チェックのサポートを得るために、イベントハンドラで `Event` クラスの型注釈を使用することを推奨します。

```python
from ErisPulse.Core.Event import Event  # Event型の注釈に使用するイベント型をインポート
```

### すべてのメッセージを監視

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"{user_id} からのメッセージを受信しました: {text}")
```

### プライベートメッセージを監視

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"こんにちは、{user_id}さん！これはプライベートメッセージです。")
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
    await event.reply(f"以下のユーザーを@しました: {mentions}")
```

### ワイルドカードと正規表現による監視

4つのメッセージデコレータ（`on_message` / `on_private_message` / `on_group_message` / `on_at_message`）は、`pattern`（globワイルドカード）と `regex`（正規表現）をサポートしており、パターンに一致しないメッセージは**ハンドラをトリガーしません**。

```python
# globワイルドカード：* 任意の文字列、? 1文字、[seq] 文字集合
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("サインインに成功しました")

# 正規表現：金額をマッチ
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"金額を受信しました: {event.get_text()}")

# pattern と regex 両方指定 → 両方ともマッチする必要がある
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` でもこの2つのパラメータをサポートしています（[返信の待ち機能](../developer-guide/modules/event-wrapper.md#返信の待ち機能)を参照してください）。

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
@command(["help", "h"], aliases=["help", "h"], help="ヘルプ情報を表示")
async def help_handler(event):
    await event.reply("ヘルプ情報...")
```

ユーザーは以下のいずれかの方法で呼び出すことができます：
- `/help`
- `/h`
- `/help`

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

### コマンドグループ

```python
@command("admin.reload", group="admin", help="モジュールを再読み込み")
async def reload_handler(event):
    await event.reply("モジュールを再読み込みしました")

@command("admin.stop", group="admin", help="ロボットを停止")
async def stop_handler(event):
    await event.reply("ロボットを停止しました")
```

### コマンドの権限とアクセス制御

コマンドの権限は3層に分かれ、上から順に判定されます（**上層が拒否された場合、下層は確認されません**）：

```python
# ① コマンド権限 ACL（ユーザー側設定）：コマンドごとのユーザーの白黒リスト、拒否時は「権限不足」を返信
# ② master=True —— フレームワークの所有者のみ実行可能（フレームワークが自動的にチェック、拒否時は「権限不足」を返信）
@command("restart", master=True, help="モジュールを再起動")
async def restart_handler(event):
    await event.reply("モジュールを再起動しました")

# ③ permission=関数 —— コマンド自身の制御ロジック（Trueを返す場合に実行）
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="管理パネル")
async def panel_handler(event):
    await event.reply("管理パネルへようこそ")
```

**コマンドユーザー ACL**（`ErisPulse.event.command.acl`）：ユーザーは任意のコマンドにユーザーの白黒リストを設定できます。コマンド名は正確な一致と glob モード（例：`"roll*"`）をサポートし、拒否時は「権限不足」を返信します：

```toml
# config.toml —— restart は 123456 だけが実行可能、666 は一律拒否
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

判定順序：`deny` が一致 → 拒否；`allow` が空でないかつ一致しない → 拒否；ACL が設定されていない場合は `event.command.default_allow`（`false` = 厳格モード、ACL がないと拒否；`true` の場合は開発者がデフォルトで `master=True` / `permission` を使用）に従います。実行時の API（コマンド名は glob に対応）：

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # 許可リスト
command.deny_user("restart", "onebot11", "666")       # 拒否リスト
command.remove_acl("restart")                          # 白黒リストを削除
command.get_acl("restart")                             # 現在のリストを取得
```

> コマンドハンドラはイベントパッケージからインポート：`from ErisPulse.Core.Event import command`；SDK イベントパッケージからもアクセス可能：`sdk.Event.command`（どちらも同一のシングルトンです）。モジュール内では通常、コマンドデコレータと共にインポートされています（`from ErisPulse.Core.Event import command`）。

コマンド間 / ユーザー間の**イベントレベル**のアクセス制御（特定のユーザー / 群 / Bot のメッセージを受信するかどうか）は**スコープのアイデンティティ次元**（`scope.identity`）を介して行います。**モジュールレベル**の可用性（どのモジュールが使用できるか）は**スコープのモジュール次元**（`scope.platforms / bots / sessions`）を介して行います。詳細は[スコープ（scope）](../advanced/scope.md)をご覧ください。

> 建議：コマンド内部でビジネスロジックを連動させる場合は `master=True` / `permission` を使用してください。純粋にユーザー / 群によるアクセス制御を行う場合はスコープのアイデンティティ次元を使用し、モジュールの可用性を制御する場合はスコープのモジュール次元を使用してください。

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
    ↓ (中断されていない場合)
priority=0 組: [ハンドラA || ハンドラB] 並列 → 結果をマージ
    ↓
...
```

- **同優先度の並列処理**：優先度が同じ複数のハンドラは同時に実行され、スループットが向上します
- **異なる優先度の直列処理**：異なる優先度のグループは順に実行されます（数値が大きいほど先に実行）、高優先度のハンドラが先に実行されることを保証します
- **Copy-On-Write**：ハンドラが変更しない場合はコピーを作成せず、ゼロオーバーヘッドを確保します
- **競合処理**：同優先度の複数のハンドラが同じフィールドを変更した場合、最後に変更された値が使用され、警告ログが記録されます
- **中断機構**：任意のハンドラが `event.done()`（デフォルト）または `event.done(claim=False)` を呼び出した後、後続の低優先度グループはスキップされます。認領とブロックの違いは以下の[「リンク制御：認領とブロック」](#リンク制御認領とブロック)をご覧ください。

```python
# 例：同優先度のハンドラが並列に実行される
@message.on_message(priority=0)
async def handler_a(event):
    # タスクAを処理
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # handler_a と並列に実行される
    event['result_b'] = process_b()

# 異なる優先度で直列に実行される
@message.on_message(priority=10)
async def handler_c(event):
    # 最も優先度が高く、最初に実行される
    pass
```

> **並列上限**：すべてのマッチするハンドラの Task は**即座に作成**されますが、同時に実行される数を制限する信号量によって管理されます。デフォルトの上限は **64**（`ErisPulse.framework.handler_max_concurrency`、ホットアップデート対応）です。上限を超えた Task は信号量上で待ち、前の処理が完了した後に実行されます。イベントのピーク時に、これはあなたの「圧力緩和弁」になります。
>
> **スローログ**：個々のハンドラの処理時間が **1 秒**を超える場合、フレームワークはログに WARNING（`handler_slow`）を出力します。`wait_reply` の待機時間は処理時間から除外され、「返信を待つ」ことで誤ったスローログが発生することはありません。

## スコープフィルタリング：なぜ私のモジュールはメッセージを受け取らないのか

イベントが到達した後、2 つの**静黙**フィルタリング（返答もエラーも出さない）が存在します：

1. **アイデンティティ次元**（`ErisPulse.scope.identity`）：イベントが配信エントリポイントに到達した時点で、ユーザー > グループ > Bot > アダプタの順に判定し、受信するかどうかを決定します。  
   拒否された**イベント全体**は直接破棄され、コマンドディスパッチャーを含むすべてのハンドラはトリガされません。
2. **モジュール次元**（`ErisPulse.scope`）：イベントが特定のモジュールのハンドラ/コマンドに到達した時点で、セッション > Bot > プラットフォームの順に判定し、そのモジュールが有効かどうかを確認します。**判定に失敗した場合、静黙でスキップされます**。

```toml
# 例1：特定のグループのすべてのメッセージを伝播させない
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# 例2：特定の Bot に対して MyModule をブロックする
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

この場合、そのグループのメッセージが到達したときに、`MyModule` のコマンドとイベントハンドラは**どちらもスケジュールされません**。これはバグではなく、フィルタリング機構です。モジュールが反応しないことを調査する際には、まず作用域のアイデンティティとモジュールのバインディングを確認してください。

- フィルタリングログは **TRACE** レベルでのみ表示されます（`core.scope.identity_denied` / `core.scope.denied`）。デフォルトの INFO レベルでは、ログの痕跡は一切表示されません。
- フレームワークレベルのハンドラ（コマンドディスパッチャーなど、`scope_exempt=True`）は**モジュール次元**の影響を受けませんが、**アイデンティティ次元**の影響を受けます（イベント全体がすでに破棄されているため）。
- コマンド実行前に 3 番目のフィルタリングがあります：コマンドユーザー ACL（拒否された場合、「権限不足」と返答します。前節参照）。
- 4 番目のフィルタリングは**イベントオーバーライド**です（次節参照）。

> 作用域の設定、マッチングの構文、実行時の API については、[作用域（scope）](../../advanced/scope.md) を参照してください。

## イベントのオーバーライド：モジュールのコードを変更せずに、任意のイベントタイプの動作を上書き

> [!NOTE]
> この機能には ErisPulse **2.8.0+** が必要です。

イベントハンドラは登録時に宣言するパラメータ（`pattern` / `regex` / `master` / `hidden` など）は、**開発者のデフォルト**にすぎません。
統一されたオーバーライドシステムにより、ユーザーは**イベントタイプ**ごとに任意のモジュールの動作を上書きできます。OneBot12 標準タイプ
（meta / message / notice / request）と ErisPulse 拡張タイプ（command）はそれぞれ独自の上書き可能なパラメータを持ちます：

| イベントタイプ | 上書き可能なパラメータ | 作用 |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | テキストのトリガ条件 + メッセージのサブタイプホワイトリスト |
| `notice` | `detail_types` / `pattern` / `regex` | 通知のサブタイプホワイトリスト + テキスト条件 |
| `request` | `detail_types` / `pattern` / `regex` | 要求のサブタイプホワイトリスト + テキスト条件 |
| `meta` | `detail_types` | 元イベントのサブタイプホワイトリスト（connect / heartbeat など） |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | コマンド実装パラメータ（ユーザー優先） |
| `acl`（command 専用） | `allow` / `deny` | コマンドのユーザーのホワイトリスト/ブラックリスト（コマンド名の glob で） |

```toml
# message：テキストのトリガ条件を上書き（コード内の条件と AND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice：特定の通知サブタイプのみ対応
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command：実装パラメータを上書き（ユーザー優先——開発者のデフォルトを厳しくしたり緩めたりできる）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl：コマンドのユーザーのホワイトリスト/ブラックリスト（コマンド間 glob）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACL のデフォルト（false = 厳格モード：ACL がない場合は拒否）
acl_default_allow = true
```

実行時 API（`from ErisPulse.Core.Event import overrides` または `sdk.Event.overrides`、
**タイプのサブネームスペース**——各タイプごとに `set` / `get` / `delete` の三つの関数が対称）：

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # message のテキスト条件
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # コマンドのパラメータ
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # コマンドのユーザーのブラックリスト

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # 開発者のデフォルトに戻す
```

- 上書き条件とハンドラのコード内の条件は**両方有効**（AND 論理）；`command` パラメータは開発者が宣言した内容と**深くマージ**（上書きが優先）
- `detail_types`：イベントに `detail_type` がない場合でも許可（未知のイベントを誤って拒否しない）
- `pattern` / `regex`：テキストがないイベント（connect / heartbeat など）は制約を受けず、直接許可
- `command` の上書きキー `master` は同期してストレージキー `must_master` にマッピングされる；コマンドの禁止はすべて `acl` deny を通る
- 設定を変更すると即座に有効（ホットアップデート）、フォーマットの検証は警告（未知のパラメータ / 不正な項目は無視）

## リンク制御：認領とブロッキング

> [!NOTE]  
> `event.done()` / `event.mark_processed()` の `claim=` / `stop=` パラメータは、この機能には ErisPulse **2.7.1+** が必要です。

ErisPulse では、「認領」と「ブロッキング」の2つの正交的な概念を分離し、`event.done()` で一元的に制御することで、コマンド処理の周囲にログ、監査、権限などの観測層を重ねることが容易になります。

**2つの概念の正確な定義は以下の通りです：**

- **認領（claim）**：イベントがこのプロセッサによって処理されたことをマークします（`_processed` に書き込みます）。コマンドディスパッチャーは、認領済みのイベントを見ると**重複処理をスキップ**します——同じメッセージが複数のコマンドプロセッサに重複して処理されるのを防ぎます。典型的な場面：コマンドがマッチした後に認領し、コマンドディスパッチャーが再び介入しないようにします。
- **ブロッキング（stop）**：イベントが**より低い優先度**のプロセッサに伝播するのを阻止します（`_propagation_stopped` に書き込みます）。低優先度のプロセッサ（例：`on_message`）は、このイベントを見なくなります。典型的な場面：高優先度のプロセッサがイベントを完全に処理した後、低優先度のプロセッサが再度実行されないようにします。

| `event.done(...)` | 認領 | ブロッキング | 場面 |
|-------------------|------|--------------|------|
| `event.done()` | ✔ | ✔ | コマンド / プロセッサが処理完了した際の標準的な方法 |
| `event.done(stop=False)` | ✔ | ✘ | 認領のみ：低優先度の観測者（ログ / 統計）は引き続きイベントを見ることができます |
| `event.done(claim=False)` | ✘ | ✔ | ブロッキングのみ（例：ファイアウォール / 限流）：認領は行わず、重複処理は防ぎません |

`event.done(claim=, stop=)` は `event.mark_processed(claim=, stop=)` の別名であり、両者はパラメータと動作が完全に等価です。

```python
@command("help")
async def help_cmd(event):
    event.done()            # 認領 + ブロッキング（コマンド処理完了の標準的な方法）

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # 認領のみ：低優先度の処理が引き続き実行されます（ログ / 統計）

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # ブロッキングのみ：低優先度の処理は実行されませんが、重複処理は防ぎません
```

### コマンドと返信の block 設定

コマンドがマッチした場合や `wait_reply` が返信をマッチした場合、デフォルトでは伝播をブロックします（後方互換性のため）。この設定を変更することで、低優先度のプロセッサ（ログ / 監査 / 権限）がこれらのメッセージを観測できるようにすることができます：

```toml
[ErisPulse.event.command]
block = false   # コマンドメッセージは低優先度のプロセッサに引き続き伝播します

[ErisPulse.event.wait_reply]
block = false   # wait_reply によって消費された返信は低優先度のプロセッサに引き続き伝播します
```

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

## リクエストイベント処理

### フレンドリクエスト

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"フレンドリクエストを受け取りました: {user_id}, 付言: {comment}")
    
    # アダプタAPIを使ってリクエストを処理できます
    # 具体的な実装は各アダプタのドキュメントを参照してください
```

### グループ招待リクエスト

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"グループ {group_id} からの招待を受け取りました, 送信元: {user_id}")
```

## 元イベント処理

### 接続イベント

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} プラットフォームが接続されました")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"{platform} プラットフォームが切断されました")
```

### ハートビートイベント

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} ハートビート検出")
```

### Bot 状態の照会

アダプターが meta イベントを送信すると、フレームワークは自動的に Bot 状態を追跡します。いつでも照会することができます。

```python
from ErisPulse import sdk

# 特定の Bot がオンラインかどうかを確認
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot はオンラインです")

# 現在オンラインの Bot を一覧表示
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# 完全な状態サマリーを取得
summary = sdk.adapter.get_status_summary()
```

## 交互処理

### reply メソッドを使用した返信の送信

`event.reply()` メソッドは、@メンションや返信などの機能を備えた様々な修飾パラメータをサポートしています：

```python
# 簡単な返信
await event.reply("こんにちは")

# 異なるタイプのメッセージの送信
await event.reply("http://example.com/image.jpg", method="Image")  # 画像
await event.reply("http://example.com/voice.mp3", method="Voice")  # 音声

# 単一のユーザーを@する
await event.reply("こんにちは", at_users=["user123"])

# 複数のユーザーを@する
await event.reply("皆さんこんにちは", at_users=["user1", "user2", "user3"])

# メッセージを返信する
await event.reply("返信の内容", reply_to="msg_id")

# 全員を@する
await event.reply("お知らせ", at_all=True)

# 組み合わせ: @ユーザー + メッセージの返信
await event.reply("内容", at_users=["user1"], reply_to="msg_id")
```

### ユーザーの返信を待つ

```python
@command("ask", help="ユーザーに質問")
async def ask_handler(event):
    await event.reply("あなたの名前を入力してください:")
    
    # ユーザーの返信を30秒間待つ
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}！")
    else:
        await event.reply("タイムアウトしました。再度入力してください。")
```

### 検証付きの返信待ち

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
    
    await event.reply("あなたの年齢を入力してください (0-150):")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"あなたの年齢は {age} 才です")
    else:
        await event.reply("無効な入力またはタイムアウトしました")
```

### コールバック付きの返信待ち

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

ユーザーの確認または否定を待ち、組み込みの中国語および英語の確認語を自動的に認識します：

```python
@command("confirm", help="操作を確認")
async def confirm_handler(event):
    if await event.confirm("この操作を実行しますか？"):
        await event.reply("確認済み、実行中...")
    else:
        await event.reply("キャンセルされました")

# 確認語のカスタマイズ
if await event.confirm("続行しますか？", yes_words={"go", "続行"}, no_words={"stop", "停止"}):
    pass
```

### 選択メニュー (choose)

ユーザーは選択番号または選択テキストを返信することができます：

```python
@command("choose", help="選択")
async def choose_handler(event):
    choice = await event.choose(
        "色を選択してください：",
        ["赤", "緑", "青"]
    )
    
    if choice is not None:
        colors = ["赤", "緑", "青"]
        await event.reply(f"選択した色は：{colors[choice]}")
    else:
        await event.reply("選択がタイムアウトしました")
```

**マージモード**: `merge_prompt=True` の場合、オプションはプロンプトメッセージにマージされ、ユーザーが指定した `method` で1つのメッセージとして送信されます：

```python
# Markdown でプロンプトとオプションをマージして送信
choice = await event.choose(
    "## 色を選択してください\n{options}\n番号を入力してください",
    ["赤", "緑", "青"],
    method="Markdown",
    merge_prompt=True,
)
```

> `{options}` 占位符はオプションの挿入位置を制御します。指定しない場合はプロンプトの末尾に追加されます。  
> `placeholder` パラメータを使用して占位符をカスタマイズできます（例：`placeholder="[choices]"`）。  
> `options_format="auto"`（デフォルト）は、method に応じてスタイルを自動的に選択します：Markdown→無序リスト、Html→順序リスト、その他→テキストリスト。  
> テキスト系メソッド（Text/Markdown/Html 等）はデフォルトでオプションを末尾にマージします。非テキスト系メソッド（Image 等）はデフォルトで2つのメッセージに分割されます。

### フォームの収集 (collect)

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

同一ユーザーに限らず、条件を満たす任意のイベントを待ちます：

```python
@command("wait_member", help="新メンバーを待つ")
async def wait_member_handler(event):
    await event.reply("グループメンバーの加入を待っています...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"新メンバーを歓迎します：{evt.get_user_id()}")
    else:
        await event.reply("タイムアウトしました")
```

### 多段対話 (conversation)

インタラクティブな複数段対話コンテキストを作成します：

```python
@command("survey", help="アンケート調査")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("アンケート調査に参加していただきありがとうございます！")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("対話がタイムアウトしました、さようなら！")
            break
        
        text = reply.get_text()
        
        if text == "終了":
            await conv.say("さようなら！")
            break
        
        await conv.say(f"入力された内容：{text}、継続するか、'終了'と入力して対話を終了してください")
```

### 組み込みの確認語

ErisPulse には中国語および英語の確認語が組み込まれています：

- **確認語** (`CONFIRM_YES_WORDS`): はい、yes、y、確認、確定、ok、true、対、うん、行、同意、問題ない...
- **否定語** (`CONFIRM_NO_WORDS`): いいえ、no、n、キャンセル、不要、false、錯、拒否、不可...

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

内蔵メソッドに加えて、各プラットフォームアダプターは、プラットフォーム固有のデータにアクセスしやすくするためのプラットフォーム固有のメソッドも登録します。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # プラットフォームに応じて固有メソッドを呼び出す
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram 固有メソッド
    elif platform == "email":
        subject = event.get_subject()           # メール固有メソッド
```

プラットフォームが特定のメソッドを登録しているかどうか不明な場合は、そのプラットフォームが登録したメソッドを確認できます。

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> 各プラットフォームが登録した固有メソッドについては、対応する [プラットフォームドキュメント](../platform-guide/) を参照してください。

## イベント処理のベストプラクティス

### 1. 例外処理

```python
@command("process")
async def process_handler(event):
    try:
        # 业务逻辑
        result = await do_some_work()
        await event.reply(f"结果: {result}")
    except ValueError as e:
        # 预期的业务错误
        await event.reply(f"パラメータエラー: {e}")
    except Exception as e:
        # 未预期的错误
        sdk.logger.error(f"処理失敗: {e}")
        await event.reply("処理失敗、後でもう一度お試しください")
```

### 2. ログ記録

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"メッセージを処理中: {user_id} - {text}")
    
    # モジュール独自のログを使用
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"詳細なデバッグ情報")
```

### 3. 条件処理

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """条件処理 - ハンドラ内部で判断"""
    # 特定のユーザーのメッセージのみを処理
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # 特定のキーワードを含むメッセージのみを処理
    if "キーワード" not in event.get_text():
        return
    
    await event.reply("条件が満たされ、メッセージを処理します")
```

## 次に進む

- [一般的なタスクの例](common-tasks.md) - 常用機能の実装方法を学びます（メッセージ送信の高度な機能：リトライ/タイムアウト/バッチ処理を含む）
- [プラットフォームの機能ガイド](../platform-guide/README.md) - Send DSL チェーン送信、送信ルール、バッチ構築の完全な説明
- [Event パッケージの詳細](../developer-guide/modules/event-wrapper.md) - Event オブジェクトの詳細を理解します
- [ユーザー使用ガイド](../user-guide/) - 設定とモジュール管理について理解します