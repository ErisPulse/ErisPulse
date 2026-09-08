# 交互会話システム

> [!NOTE]
> 本章の内容は ErisPulse **2.8.0+** が必要です。

ErisPulse では「ユーザーとの継続的な対話」をフレームワークレベルのインフラとして実現しています。`wait_reply` から始まり、定時アラート、多重待ち、会話の排他制御、再起動時の復元まで、すべてが統一された **インタラクションセッションマネージャー**（`Core/Event/interaction.py`、`sdk.interaction`）によってスケジュールされます。

{!--< tips >!--}
本文で取り上げる機能はすべて**所有者（owner）**を持ちます。インタラクションの待ち、リース、タイマーはすべて登録時にモジュール名が記録され、モジュールのアンロードやアダプタの停止時にフレームワークが自動的にクリーンアップを行い、待機側は即座に通知を受け取るようになります。これは、タイムアウトを待つことなく、所有権システムがインタラクションの観点から拡張されたものです（[所有権システム](ownership.md)を参照）。  
{!--< /tips >!--}

## 等待回复：wait_reply

`wait_reply` はインタラクティブな会話の基盤です。現在のコルーチンを一時停止し、次のメッセージで対象ユーザーが「返信」するのを待ちます。

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    reply = await event.wait_reply(prompt="あなたの名前を入力してください:", timeout=30)
    if reply is None:
        await event.reply("タイムアウトしました")
        return
    await event.reply(f"こんにちは、{reply.get_text()}！")
```

### 全パラメータ一覧

| パラメータ | 説明 | デフォルト |
|------|------|------|
| `prompt` | 一時停止前に送信するプロンプトメッセージ | None |
| `timeout` | 等待のタイムアウト（秒） | 60 |
| `pattern` | glob フィルタ（`*` / `?` / `[seq]`）、一致しない場合は待機を継続 | None |
| `regex` | 正規表現フィルタ（pattern と同時に指定された場合、両方一致する必要がある）、一致しない場合は待機を継続 | None |
| `validator` | 検証関数（Event を受け取り、bool を返す）、失敗した場合は待機を継続 | None |
| `callback` | 返信を受け取った際のコールバック（戻り値方式の代わりの書き方） | None |
| `method` | prompt の送信方法 | "Text" |
| `session` | **セッションレベルの待機**：同じセッション（グループ / チャンネル）内の誰かの返信でも有効 | False |

```python
# 数字の金額のみを受け入れ、それ以外は待機を継続
reply = await event.wait_reply("金額を入力してください:", regex=r"\d+\s*元", timeout=30)

# セッションレベルの待機：グループ協力の場面で、グループ内の誰かが返信しても有効
reply = await event.wait_reply(session=True, prompt="どなたか回答してください。")
```

### 等待がいつキャンセルされるか

待機は「タイムアウトするまで待つ」だけではありません。以下の状況では**即座に終了**（`wait_reply` は `None` を返す）し、
呼び出し元がタイムアウトまで待つ必要がありません：

| 触発 | キャンセル理由（`InteractionCancelled.reason`） | 説明 |
|------|------|------|
| 所属モジュールがアンロード / 禁用された | `owner_unload` | 所属のクリーンアップ：誰が登録した待機でも、そのモジュールが消えた時点で一括回収 |
| アダプタが停止 / 再起動された | `platform_stop` | そのプラットフォームで一時停止された待機はすべてキャンセル |
| 同一セッション内で新しい待機 / リースが発生した | `conflict` | 下記「セッション仲裁」を参照 |
| 返信者がブロックされた / owner モジュールが解除された | `revoked` | 返信が命じられた**権限の再確認**：scope 身分次元 + モジュール次元 |
| ユーザーが返信した | —— | 正常な経路、返信イベントを返す |

下層の例外は `InteractionCancelled`（`InteractionError` 例外体系に属する）で、
`wait_reply` はこれを `None` を返すように変換しています。原因が必要な呼び出し元は、
`sdk.interaction.register()` の低レベル API を直接使用することができます。

### 返信が命じられた場合の完全な判定チェーン

返信メッセージが到着した際、インタラクティブマネージャーは以下の順序で判定を行います（コマンドマッチの**前**に実行され、
会話の連続性が優先されるため、メッセージが他の高優先度の処理で既に認識された場合でも、一時停止された会話は完了できます）：

```
セッションキーの一致（正確な user 次元 → セッションレベルのフォールバック）
  → pattern / regex テキストフィルタ（一致しない場合は待機を継続）
  → validator 検証（失敗した場合は待機を継続）
  → 権限の再確認（scope 身分次元 + owner モジュール次元、失敗した場合は待機を終了）
  → 待機側の呼び出し + イベントの認領（mark_processed）
```

## セッションタイマー：remind / escalate

「タイムアウト」を返値から可編成可能な原語に変更しました。タイマーは対話セッションに紐づけられ、モジュールのアンロードやアダプターの閉鎖時に自動的にキャンセルされます。1つのセッションで有効な remind の上限は 5 つです。

### remind：返信がなければリマインド

```python
@command("ticket")
async def ticket_command(event):
    await event.reply("工単が提出されました。処理結果はここに通知されます。")
    # 5 分間返信がなければ、穏やかに1回リマインドします。ユーザーの返信はすべて自動的にキャンセルされます
    event.remind(300, "まだお待ちですか？結果が出たらすぐにご連絡します。")
    reply = await event.wait_reply(timeout=3600)
    ...
```

- `event.remind(delay, text=None, *, callback=None)`：期限が来たら現在のセッションに `text` を送信します
  （または `callback(event)` を実行します。同期 / 非同期の両方に対応しています）
- 戻り値は `Reminder` ハンドルです：`reminder.cancel()` で手動でキャンセル、`reminder.expired` で状態を確認できます
- ユーザーがこのセッションで**返信すると自動的にキャンセル**されます——これが「リマインド」の意味です：
  リマインドはユーザーが沈黙している場合にのみ表示されます
- `Conversation` 内でも同様に使用可能です：`conv.remind(120, "まだ検討中ですか？")`

### escalate：期限が来たら必ず通知

```python
event.escalate(1800, lambda e: notify_master(f"工単 30 分未処理：{event.get_command_args()}"))
```

`remind` との唯一の違いは、**ユーザーの返信によってキャンセルされない**ことです——エスカレーションアクション（主人への通知、人間への転送）は「タイムアウト時に必ず通知」を約束するものであり、手動での `cancel()` またはモジュールのアンロード、アダプターの閉鎖によってのみキャンセルされます。

| | `remind` | `escalate` |
|---|---|---|
| 到期時の動作 | テキストを送信 / callback を実行 | callback を実行 |
| ユーザーの返信 | **自動的にキャンセル** | 影響を受けません |
| 帰属のクリーンアップ（アンロード / プラットフォーム閉鎖） | キャンセル | キャンセル |
| セッションごとの上限 | 5 | なし（帰属のクリーンアップでバックアップ） |

## マルチ待機：expect + select

複数の期待を同時に待機し、**先着順**で処理されます。典型的な場面：管理者の承認を待つと同時に、ユーザーによる撤回を待つ、複数人による共同投票など。

```python
which, reply = await event.select(
    event.expect(pattern="同意*", user="10001"),
    event.expect(pattern="拒绝*", user="10002"),
    event.expect(validator=lambda e: e.get_text() == "搁置", session=True),
    timeout=60,
)
if which is None:
    await event.reply("60 秒内未收到任何审批结果")
elif which == 0:
    await event.reply("已同意")
elif which == 1:
    await event.reply("已拒绝")
```

- `event.expect(...)` は**期待の記述**を作成します（待機は登録されません）：`pattern` / `regex` / `validator` / `user`（返信者を限定）/ `session`（誰でも返信可能）がサポートされます。
- `event.select(*expectations, timeout=60)`：一括で登録 → いずれかが一致したら `(インデックス, 返信イベント)` を返します → 一致しなかった待機は自動的にキャンセルされます；すべてがタイムアウトしたら `(None, None)` を返します。
- 一致したイベントはフレームワークによって認証済み（`mark_processed`）となり、他の処理器で重複して消費されることはありません。

{!--< tips >!--}
`select` とマルチスレッドの `asyncio.wait` による手動の編集と比較すると：期待が一致しなかった場合の自動クリーンアップ、一致したイベントの自動認証、権限の再確認と帰属のクリーンアップがすべて有効になります。→ すべての Future を手動で管理する必要はありません。
{!--< /tips >!--}

## セッション排他：acquire / hold / get_owner_of

所有権は「リソース」から「セッション」へ移行しました。つまり、「このユーザーは現在誰によって占有されているか」が、最も重要なクエリとなります。

```python
# クエリ：このセッションは現在誰と対話中ですか？（空きの場合は None を返す）
owner = sdk.interaction.get_owner_of(event)
if owner and owner != "MyModule":
    return  # 他のモジュールが対話中です。干渉しないようにします

# 排他リース：セッションの独占（deny 策略、占有中は None を返す）
lease = sdk.interaction.acquire(event)          # デフォルトの TTL は 1 時間、ttl= を渡すことで変更可能
if lease is None:
    return  # すでに占有されています
try:
    ...  # 独占状態での対話処理
finally:
    lease.release()
```

コンテキストマネージャー形式（取得に失敗すると `SessionOccupiedError` を送出します）：

```python
with sdk.interaction.hold(event) as lease:
    ...  # ブロックを抜けると自動的にリリースされます
```

リースは `renew(ttl)` で更新が可能。TTL は惰性で期限切れになります。期限切れのリースは、次回アクセス時に自動的にクリーンアップされます。

`Conversation.resume()` で対話を再開する際、フレームワークは自動的にリースを取得します（詳細は [Conversation 多輪対話](conversation.md) の「再開即座に所有」を参照してください）。再開された対話はセッションを天然に所有しており、他のモジュールが介入することはありません。

## 会話受信箱：event.history

各モジュールが個別に履歴を保持するのではなく、AIコンテキスト、重複防止、行動分析などのモジュールの**共有事実ベース**として、各会話の最近のメッセージフロー（ユーザー + ロボットの両方）を統一的に記録します。

```python
messages = await event.history(20)   # 最近の20件、時系列昇順
for m in messages:
    print(m["role"], ":", m["text"])  # role: "user" / "bot"
```

- 自動記録：入力メッセージ（role=user）とロボットからの出力テキスト（role=bot）
- ストレージ：個別の SQLite テーブルに保存。各会話の上限（デフォルト 50）とグローバルなTTL（デフォルト 7 日間）による保持ポリシー
- 設定：`ErisPulse.transcript = {enabled = true, max_per_session = 50, ttl_hours = 168}`
- マネージャ API：`sdk.transcript.append() / get() / clear()`

## メッセージトランザクション：message_tx

トランザクション内のすべての出力メッセージは自動的に記録されます。**例外が発生した場合、逆順に自動的に送信済みメッセージを撤回**します（アダプターが `delete_message` を実装していない場合はスキップされますが、台帳は正常に記録されます）。

```python
async with event.message_tx():
    await event.reply("処理中です、少々お待ちください")
    result = await do_something()          # ここで例外が発生 →
    await event.reply(f"完了: {result}")   # 以前の「処理中」は自動的に撤回されます
```

トランザクション外で送信したメッセージは記録されません（ゼロオーバーヘッド）。`get_send_receipts()` を使用して、現在のトランザクションで送信された回執を確認できます。

## 鏈路追跡：trace-id

各インバウンドイベントは、自動的に追跡ID（`event["id"]` を再利用、存在しない場合は生成）を取得し、以下を貫く：

- handlerコンテキスト（`get_current_trace_id()` で読み取り）
- アウトバウンド送信（`[Send]` ログ行に `[trace:...]` を追加、`message.sending/sent` ホッキングの `trace_id` フィールド）
- ライフサイクルホッキングデータ（dictに自動的に `_trace_id` を追加）
- 定向イベント（`emit_to`）とメッセージトランザクションの確認

1つのメッセージが複数のモジュールによって連携処理される場合、同一のIDで全チェーンを連結し、（ログ / 遅いクエリ / 審計）を可能にする。

## 他のシステムとの関係

- **所有権**：待機 / レンタル / タイマーはすべて owner を記録し、アンロード時にリサイクルされます（[所有権システム](ownership.md)）
- **スコープ**：返信のヒット確認時に身元を再確認 + モジュール単位；モジュール間の呼び出しは監査のために出口の次元を越えます（[スコープ](scope.md)）
- **Conversation**：複数ラウンドの対話は、インタラクティブなセッションの上に存在する分岐状態機械です（[Conversation](conversation.md)）。
  その待機も、このページのすべてのキャンセル / 再確認 / 所有権の意味を享受します。

## 関連ドキュメント

- [Conversation 多回対話](conversation.md) - 分岐ステートマシン、自動チェックポイントと再開復元
- [所有権（owner）システム](ownership.md) - 所有権のクリーンアップの全体像と設計の境界
- [スコープ（scope）](scope.md) - 権限の再確認とアウトバウンド監査の設定方法
- [モジュール間通信](module-communication.md) - 跨モジュール呼び出しと方向性イベント