# 交互会話システム

> [!NOTE]
> 本章の内容は ErisPulse **2.8.0+** を必要とします。

ErisPulse は「ユーザーとの継続的な対話」をフレームワークレベルのインフラとして実装しています。`wait_reply` から始まり、定時通知、複数ルートの待機、セッションの排他、再起動時の復旧まで、すべてが統一された **インタラクティブセッションマネージャー**（`Core/Event/interaction.py`、`sdk.interaction`）によってスケジューリングされます。

{!--< tips >!--}
本文でカバーする各機能には**所有者（owner）**が付与されています。待機、リース、タイマーはすべて登録時のモジュール名を記録し、モジュールのアンロードやアダプターの停止時にフレームワークが自動的にクリーンアップし、待機側に即座に通知が届きます。これは、待機がタイムアウトするまで待つ必要がないことです。これは、[所有権システム](ownership.md)における待機の拡張です。
{!--< /tips >!--}

## レプリーの待機：wait_reply

`wait_reply` はインタラクティブセッションの基盤です。現在のコルーチンを一時停止し、対象ユーザーが次のメッセージで「返信」するのを待ちます。

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
| `prompt` | 待機前に送信するプロンプト | None |
| `timeout` | 待機のタイムアウト（秒） | 60 |
| `pattern` | glob フィルター（`*` / `?` / `[seq]`）、一致しない場合は待機を継続 | None |
| `regex` | 正規表現フィルター（pattern と同時に指定する場合、両方一致する必要あり）、一致しない場合は待機を継続 | None |
| `validator` | 検証関数（Event を受け取り、bool を返す）、失敗した場合は待機を継続 | None |
| `callback` | レプリー受信時のコールバック（戻り値形式の代わりの書き方） | None |
| `method` | prompt の送信方法 | "Text" |
| `session` | **セッションレベルの待機**：同じセッション（グループ / チャンネル）内の誰の返信でも有効 | False |

```python
# 数字の金額のみを受け入れ、それ以外は待機を継続
reply = await event.wait_reply("金額を入力してください:", regex=r"\d+\s*元", timeout=30)

# セッションレベルの待機：グループ協働の場面、誰でも返信可能
reply = await event.wait_reply(session=True, prompt="誰か回答していただけますか？")
```

### 待機がいつキャンセルされるか

待機は「タイムアウトするまで待つ」だけではありません。以下の状況では待機が**即座に終了**（`wait_reply` は `None` を返す）し、呼び出し側がタイムアウトまで待つ必要はありません。

| 触発 | キャンセル理由（`InteractionCancelled.reason`） | 説明 |
|------|------|------|
| 所有モジュールがアンロード / 禁用された | `owner_unload` | 所有権のクリーンアップ：誰が登録した待機か、そのモジュールが消えたときに一緒に回収 |
| アダプターが停止 / 再起動された | `platform_stop` | そのプラットフォームで一時停止された待機はすべてキャンセル |
| 同じセッションで新しい待機 / リースが上書きされた | `conflict` | 下記「セッション仲裁」を参照 |
| レプリーの送信者がブロックされた / 所有モジュールが解除された | `revoked` | レプリーが命じられた**権限の再確認**：スコープのアイデンティティ次元 + モジュール次元 |
| ユーザーがレプリーを送信した | —— | 正常な経路、レプリーイベントを返す |

低レベルの例外は `InteractionCancelled`（`InteractionError` 例外体系に属する）で、`wait_reply` はそれを `None` に変換しています。原因を必要とする呼び出し側は、`sdk.interaction.register()` の低レベル API を直接使用できます。

### レプリーが命じられた完全な判定チェーン

レプリーのメッセージが到着した際、インタラクションマネージャーは以下の順序で判定します（コマンドのマッチング**の前**に実行され、会話の連続性が優先されます。メッセージが他の優先度の高い処理で既に認証されていても、一時停止された会話は完了します）：

```
セッションキーのマッチ（正確な user 次元 → セッションレベルのバックアップ）
  → pattern / regex テキストフィルター（一致しない場合は待機を継続）
  → validator 検証（失敗した場合は待機を継続）
  → 権限の再確認（スコープのアイデンティティ次元 + 所有モジュール次元、失敗した場合は待機を終了）
  → 待機側の呼び出し + イベントの認証（mark_processed）
```

## セッションタイマー：remind / escalate

「タイムアウト」を戻り値から編成可能な原語に変換します。タイマーはインタラクティブセッションに紐づき、モジュールのアンロード / アダプターの停止時に自動的にキャンセルされます。1セッションあたりのアクティブな remind の上限は 5 つです。

### remind：返信がなければリマインド

```python
@command("ticket")
async def ticket_command(event):
    await event.reply("チケットが提出されました。処理結果はここに通知されます。")
    # 5分間返信がなければ、優しくリマインド。ユーザーの返信はすべて自動的にキャンセルします
    event.remind(300, "まだいますか？結果が出たらすぐにご連絡します")
    reply = await event.wait_reply(timeout=3600)
    ...
```

- `event.remind(delay, text=None, *, callback=None)`：期限が来たら現在のセッションに `text` を送信する（または `callback(event)` を実行、同期 / 非同期対応）。**強制チェック**：`text` と `callback` はどちらか一方を指定しなければならない（どちらも指定しないと `ValueError` が発生）
- 戻り値は `Reminder` ハンドル：`reminder.cancel()` で手動でキャンセル、`reminder.expired` で状態を確認
- ユーザーがこのセッションで**返信した後は自動的にキャンセル**されます。これが「リマインド」の意味です：リマインドはユーザーが沈黙しているときにのみ表示されます
- `Conversation` 内でも使用可能：`conv.remind(120, "まだ検討中ですか？")`

### escalate：期限に必ず届くアップグレード

```python
event.escalate(1800, lambda e: notify_master(f"チケット 30 分未処理：{event.get_command_args()}"))
```

`remind` との唯一の違いは、**ユーザーの返信でキャンセルされない**ことです。アップグレードアクション（通知、人間への転送）は「タイムアウト時に必ず到達」を約束し、手動で `cancel()` またはモジュールのアンロード / アダプターの停止でのみキャンセルされます。

| | `remind` | `escalate` |
|---|---|---|
| 到期時の動作 | テキストを送信 / callback を実行 | callback を実行 |
| ユーザーの返信 | **自動的にキャンセル** | 影響を受けない |
| 所有権のクリーンアップ（アンロード / アダプター停止） | キャンセル | キャンセル |
| 1セッションあたりの上限 | 5 | 限界なし（所有権のクリーンアップでバックアップ） |

## 多ルート待機：expect + select

同時に複数の期待を一時停止し、**先着順**で処理されます。典型的な場面：管理者の承認を待つと同時に、ユーザーの取り消しや、複数人による投票を待つ。

```python
which, reply = await event.select(
    event.expect(pattern="同意*", user="10001"),
    event.expect(pattern="拒否*", user="10002"),
    event.expect(validator=lambda e: e.get_text() == "保留", session=True),
    timeout=60,
)
if which is None:
    await event.reply("60 秒以内に承認結果がありませんでした")
elif which == 0:
    await event.reply("承認しました")
elif which == 1:
    await event.reply("拒否しました")
```

- `event.expect(...)` は**期待の記述**を作成します（待機は登録されません）：`pattern` / `regex` / `validator` / `user`（返信者を限定）/ `session`（誰でも返信可能）がサポートされています
- `event.select(*expectations, timeout=60)`：一括で登録 → いずれかが命中すると `(インデックス, レプリーイベント)` を返します → 命中しなかった待機は自動的にキャンセルされます；すべてがタイムアウトすると `(None, None)` を返します。**強制チェック**：少なくとも 1 つの期待を渡さなければなりません、それ以外は `ValueError` が発生します
- 命中のイベントはフレームワークによって認証済み（`mark_processed`）で、他の処理で重複消費されることはありません

{!--< tips >!--}
`select` とマルチスレッド `asyncio.wait` の手動編集との比較：期待が命中しなかった場合の自動クリーンアップ、命中したイベントの自動認証、権限の再確認と所有権のクリーンアップがすべて有効です。自分で Future を管理する必要はありません。
{!--< /tips >!--}

## セッションの排他：acquire / hold / get_owner_of

所有権は「リソース」から「セッション」へと移行しました。「このユーザーは現在誰に占有されているか」が一等のクエリになります。

```python
# クエリ：このセッションは誰と対話中ですか？（空きなら None を返す）
owner = sdk.interaction.get_owner_of(event)
if owner and owner != "MyModule":
    return  # 他のモジュールが対話中なので、干渉しない

# 排他的リース：セッションを独占（deny 策略、占有されていれば None を返す）
lease = sdk.interaction.acquire(event)          # デフォルトで TTL 1 時間、ttl= を渡すことも可能
if lease is None:
    return  # すでに占有されている

try:
    ...  # 独占的な対話
finally:
    lease.release()
```

コンテキストマネージャー形式（取得失敗時は `SessionOccupiedError` をスロー）：

```python
with sdk.interaction.hold(event) as lease:
    ...  # 終了時に自動的に解放
```

リースは `renew(ttl)` で延長が可能；TTL は惰性で期限切れになります。期限切れのリースは、次回アクセス時に自動的にクリーンアップされます。

`Conversation.resume()` が会話を再開する際、フレームワークは自動的にリースを取得します（[Conversation 多輪対話](conversation.md)の「復帰即接続」を参照）——復帰した会話は天然にセッションを保持し、他のモジュールが挿入されることはありません。

## 会話受信箱：event.history

各AIモジュールの**共有事実ベース**として、ユーザーとロボットの双方による、各会話の最近のメッセージストリームを一元的に記録します。これにより、各モジュールが個別に履歴を保存する必要がなくなります。

```python
messages = await event.history(20)   # 最近20件のメッセージを取得、昇順で返す
for m in messages:
    print(m["role"], ":", m["text"])  # role: "user" / "bot"
```

- 自動記録：入力メッセージ（role=user）とロボットからの出力テキスト（role=bot）
- ストレージ：個別のSQLiteテーブルを使用し、各会話の上限数（デフォルト50件）とグローバルなTTL（デフォルト7日間）に基づく保持ポリシー
- 書き込み方法：メモリバッファに一時的に格納し、バックグラウンドでバッチ処理で一時的に格納されたデータを1秒以内に永続化。クエリインターフェースは、まだ永続化されていないバッファの行を自動的に結合します。同一プロセス内での「読み込みと書き込み」の競合は発生しません。正常な終了（`sdk.uninit` / プロセス終了）時には、自動的にバッファを永続化します。**ハードクラッシュや強制終了の場合は、直近約1秒の記録が失われる可能性があります**。このベースは短期間のコンテキストキャッシュとして設計されており、監査用の永続化には適していません。
- 設定：`ErisPulse.transcript = {enabled = true, max_per_session = 50, ttl_hours = 168}`
- マネージャーAPI：`sdk.transcript.append() / get() / clear()`、`aflush()` / `flush()` 手動で永続化

## メッセージトランザクション：message_tx

トランザクション内のすべての出力メッセージは自動的に記帳されます。**例外が発生した場合、逆順に自動的に既に送信されたメッセージを撤回**します（アダプターが `delete_message` を実装していない場合はスキップされますが、帳簿は正常に記録されます）。

```python
async with event.message_tx():
    await event.reply("処理中です、少々お待ちください")
    result = await do_something()          # ここで例外が発生 →
    await event.reply(f"完了: {result}")   # 以前の「処理中」は自動的に撤回
```

トランザクション外の送信は記帳されません（ゼロコスト）；`get_send_receipts()` で現在のトランザクションで送信された回執を確認できます。

## リンク追跡：trace-id

各入力イベントは自動的に追跡 ID を取得します（`event["id"]` を再利用、存在しない場合は生成）、以下を貫きます：

- handler コンテキスト（`get_current_trace_id()` で読み取り）
- 出力送信（`[Send]` ログ行に `[trace:...]` を追加、`message.sending/sent` フックの `trace_id` フィールド）
- ライフサイクルフックデータ（dict に自動的に `_trace_id` を追加）
- 定向イベント（`lifecycle.emit(..., to=...)`）とメッセージトランザクションの回執

1 つのメッセージが複数のモジュールによって処理された場合、全経路で同じ ID を使用して連携できます（ログ / 慢速クエリ / 審計）。

## 他のシステムとの関係

- **所有権**：待機 / リース / タイマーはすべて owner を記録し、アンロード時に回収されます（[所有権システム](ownership.md)）
- **スコープ**：レプリーの命中時にアイデンティティとモジュール次元を再確認；跨モジュール呼び出しの監査は出力次元を出ます（[スコープ](scope.md)）
- **Conversation**：多輪対話はインタラクティブセッションの上位の分岐状態機械です（[Conversation](conversation.md)）、その待機は本ページのすべてのキャンセル / 再確認 / 所有権の意味を享受します

## 関連ドキュメント

- [Conversation 多輪対話](conversation.md) - 分岐状態機械、自動チェックポイントと再起動復旧
- [所有権（owner）システム](ownership.md) - 所有権のクリーンアップの全景と設計境界
- [スコープ（scope）](scope.md) - 権限の再確認と出力監査の設定方法
- [モジュール間通信](module-communication.md) - 跨モジュール呼び出しと定向イベント