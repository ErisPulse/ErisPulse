# 交互会話システム

> [!TIP]
> **いつ読む必要があるか**：`wait_reply`、多段会話、定時リマインダー、セッション排他、およびトラッキングが必要な場合。不要な場合はスキップしても、他の機能の使用に影響はありません。

> [!NOTE]
> 本章の内容は ErisPulse **2.8.0以上**が必要です。

ErisPulse では「ユーザーとの継続的な対話」をフレームワークレベルのインフラとして実装しています。`wait_reply` から定時リマインダー、複数の待ち、セッション排他、再起動からの復旧まで、すべてが統一された **インタラクティブセッションマネージャー**（`Core/Event/interaction.py`、`sdk.interaction`）によってスケジュールされます。

{!--< tips >!--}
本文でカバーする各機能には、**所有者（owner）**が付与されています。インタラクティブ待ち、リース、タイマーはすべて登録時のモジュール名を記録し、モジュールのアンロード/アダプターの停止時にフレームワークが自動的にクリーンアップし、待機側に即座に通知されます。これは、所有権システムがインタラクションの観点から拡張されたものです（[所有権システム](ownership.md)を参照）。
{!--< /tips >!--}

## レプリーの待ち：wait_reply

`wait_reply` はインタラクティブセッションの基盤です。現在のコルーチンを一時停止し、対象ユーザーが次のメッセージで「返信」するのを待ちます。

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    reply = await event.wait_reply(prompt="あなたの名前を入力してください:", timeout=30)
    if reply is None:
        await event.reply("タイムアウトしました")
        return
    await event.reply(f"こんにちは、{reply.get_text()}さん！")
```

### 全パラメータ一覧

| パラメータ | 説明 | デフォルト |
|------|------|------|
| `prompt` | 一時停止前に送信するプロンプトメッセージ | None |
| `timeout` | 待ちのタイムアウト（秒） | 60 |
| `pattern` | globフィルター（`*` / `?` / `[seq]`）、一致しない場合は待ち続けます | None |
| `regex` | 正規表現フィルター（`pattern`と同時に指定する場合は両方一致する必要があります）、一致しない場合は待ち続けます | None |
| `validator` | 検証関数（Eventを受け取り、boolを返す）、失敗した場合は待ち続けます | None |
| `callback` | レプリーが届いたときのコールバック（返り値の代わりに別の書き方） | None |
| `method` | promptの送信方法 | "Text" |
| `session` | **セッションレベルの待ち**：同じセッション（グループ/チャンネル）内の誰の返信でも対応可能 | False |

```python
# 数値の金額のみを受け入れ、それ以外は待機し続ける
reply = await event.wait_reply("金額を入力してください:", regex=r"\d+\s*元", timeout=30)

# セッションレベルの待ち：グループでの協力シーン、グループ内の誰の回答でも対応可能
reply = await event.wait_reply(session=True, prompt="どなたか回答してください？")
```

### 待ちとコマンドの境界（コマンドの透過）

待機中に**登録済みのコマンド**（例：`/cancel`）が送信された場合、デフォルトではコマンドディスパッチャーに渡され、返信として消費されません（設定項目 `ErisPulse.event.wait_reply.cmdpass`、`True`にすると逆転します—メッセージはすべて返信として扱われます）。判定の基準はコマンドディスパッチャーと同じです：`alt_message`が優先され、不足している場合はメッセージセグメントの結合（2.10.1以降、純粋なmessageセグメントアダプターでも同様に有効）。

### 待ちがいつキャンセルされるか

待ちが「タイムアウトするまで待つ」だけではなく、以下の状況で**即座に終了**します（`wait_reply`は`None`を返します）：

| トリガー | キャンセル理由（`InteractionCancelled.reason`） | 説明 |
|------|------|------|
| 所有モジュールがアンロード/無効化された | `owner_unload` | 所有者クリーンアップ：誰が登録した待ちでも、そのモジュールが消えると同時に回収される |
| アダプターが停止/再起動された | `platform_stop` | 該プラットフォームに属する待ちはすべてキャンセルされる |
| 同セッションで新しい待ち/リースが置き換えられた | `conflict` | 下記「セッション仲裁」を参照 |
| 返信者がブロックされた/所有モジュールが解除された | `revoked` | 返信が命中した**権限再確認**：scopeのアイデンティティ次元 + モジュール次元 |
| ユーザーが返信を送信した | —— | 正常経路、返信イベントを返す |

下層の例外は `InteractionCancelled`（`InteractionError`例外体系に属する）で、`wait_reply`はそれを`None`に変換しています。原因が必要な呼び出し元は、`sdk.interaction.register()`の低レベルAPIを使用することができます。

### 返信が命中する完全な判定チェーン

返信メッセージが到着したとき、インタラクションマネージャーは以下の順序で判定します（コマンドマッチングの**前**に実行され、会話の連続性が優先されます—メッセージが他の高優先度のハンドラに認定されたとしても、一時停止中の会話は完了します）：

```
セッションキーが一致する（正確なuser次元 → セッションレベルの戻り値）
  → pattern / regexによるテキストフィルター（一致しない場合は待機し続ける）
  → validatorによる検証（失敗した場合は待機し続ける）
  → 権限再確認（scopeのアイデンティティ次元 + ownerモジュール次元、失敗した場合は待ちを終了）
  → 待ちを解除 + イベントを認定（mark_processed）
```

## セッションタイマー：remind / escalate

「タイムアウト」を返り値から編成可能な原語にします。タイマーはインタラクティブセッションに紐づけられ、モジュールのアンロード/アダプターの停止時に自動的にキャンセルされ、1セッションあたりの有効なremindの上限は5つです。

### remind：返信がなければリマインダー

```python
@command("ticket")
async def ticket_command(event):
    await event.reply("工単は送信されました。処理結果はここに通知されます。")
    # 5分間返信がなければ、優しくリマインダーを送信します。ユーザーの返信で自動的にキャンセルされます
    event.remind(300, "まだいますか？結果が出たらすぐに通知します。")
    reply = await event.wait_reply(timeout=3600)
    ...
```

- `event.remind(delay, text=None, *, callback=None)`：期限が来たら現在のセッションに`text`を送信する（または`callback(event)`を実行する、同期/非同期両対応）。**強制チェック**：`text`と`callback`はどちらか一方を指定しなければならない（両方指定しないと`ValueError`が発生）
- 戻り値は`Reminder`ハンドル：`reminder.cancel()`で手動でキャンセル、`reminder.expired`で状態を確認
- ユーザーがこのセッションで**返信した後は自動的にキャンセル**される—これが「リマインダー」の意味です：
  リマインダーはユーザーが沈黙しているときにのみ表示されます
- `Conversation`内でも同様に使用可能：`conv.remind(120, "まだ検討中ですか？")`

### escalate：期限が来たら必ず通知

```python
event.escalate(1800, lambda e: notify_master(f"工単30分未処理：{event.get_command_args()}"))
```

`remind`との唯一の違いは、**ユーザーの返信でキャンセルされない**こと—アップグレードアクション（通知、人間への転送）は「期限内に必ず通知」を約束し、手動で`cancel()`、モジュールのアンロード、アダプターの停止でのみキャンセルされます。

| | `remind` | `escalate` |
|---|---|---|
| 到期時の動作 | テキストを送信 / callbackを実行 | callbackを実行 |
| ユーザーの返信 | **自動的にキャンセル** | 影響を受けない |
| 所有者クリーンアップ（アンロード / アダプター停止） | キャンセル | キャンセル |
| 1セッションあたりの上限 | 5 | なし（所有者クリーンアップで下限を保証） |

## 多重待ち：expect + select

複数の期待を同時に一時停止し、**先着順**—典型的なシナリオ：管理者の承認待ちとユーザーの取り消し、複数人による投票。

```python
which, reply = await event.select(
    event.expect(pattern="同意*", user="10001"),
    event.expect(pattern="拒否*", user="10002"),
    event.expect(validator=lambda e: e.get_text() == "保留", session=True),
    timeout=60,
)
if which is None:
    await event.reply("60秒以内に承認結果がありませんでした")
elif which == 0:
    await event.reply("承認しました")
elif which == 1:
    await event.reply("拒否しました")
```

- `event.expect(...)`は**期待の記述**を作成する（待機は登録されない）：`pattern` / `regex` / `validator` / `user`（返信者の制限）/ `session`（誰でも回答可能）をサポート
- `event.select(*expectations, timeout=60)`：一括登録 → いずれかが命中すると`(インデックス, 返信イベント)`を返す → 未命中の待ちは自動的にキャンセルされる；全員がタイムアウトした場合は`(None, None)`を返す。**強制チェック**：少なくとも1つのexpectationを渡さなければ、`ValueError`が発生する
- 命中のイベントはフレームワークによって認定されている（`mark_processed`）、他のプロセッサーによって重複消費されない

{!--< tips >!--}
`select`はマルチスレッド`asyncio.wait`で手動で編成するものと比べて：期待が命中しなかった場合に自動的にクリーンアップされ、命中したイベントは自動的に認定され、権限再確認と所有者クリーンアップがすべて有効になる—自分でFutureを管理する必要がない。
{!--< /tips >!--}

> [!NOTE]
> 2.10.1以降、`select`は**集約待ち**：すべての期待が1つの項目に統合され、独自の命中判定が可能。同じキーで複数のルート（同じuserに異なるpatternを2つ設定）はお互いにキャンセルされない、先に命中したルートが返される。返信テキストの判定基準は`alt_message`が優先され、メッセージセグメントが戻る（コマンドディスパッチャーと同じ）。
>
> 境界の説明：`event.wait_for(...)`はアダプターイベントのトータルラインに直接接続され、**中間層**や`detail_type`の条件フィルタリングを経由しない（アイデンティティのアクセスはディスパッチャーのエントリでカバー）。完全なパイプラインが必要な場合は`wait_reply` / `select`を使用してください。

## セッション排他：acquire / hold / get_owner_of

所有権は「リソース」から「セッション」へと移行しました—「このユーザーが現在誰に占有されているか」が一等の問い合わせになります。

```python
# クエリ：このセッションは現在誰と対話中ですか？（空きならNone）
owner = sdk.interaction.get_owner_of(event)
if owner and owner != "MyModule":
    return  # 他のモジュールが対話中なので、干渉しない

# 排他的リース：セッションを独占（deny戦略、占有されていたらNoneを返す）
lease = sdk.interaction.acquire(event)          # 既定のTTLは1時間、ttl=で渡すことも可能
if lease is None:
    return  # 既に占有されている

try:
    ...  # 独占対話
finally:
    lease.release()
```

コンテキストマネージャー形式（取得失敗時は`SessionOccupiedError`を投げる）：

```python
with sdk.interaction.hold(event) as lease:
    ...  # 終了時に自動的に解放
```

リースは`renew(ttl)`で更新可能；TTLは惰性で期限切れ—期限切れのリースは次回アクセス時に自動的にクリーンアップされる。

`Conversation.resume()`が対話の復元時にフレームワークは自動的にリースを取得します（[Conversation 多段会話](conversation.md)の「復元即取得」を参照）—復元された対話はセッションを自然に保持し、他のモジュールは挿入されません。

## セッション受信箱：event.history

> 保持戦略（7日/件数上限）とランタイムオーバーライドAPI、リスクと監査は[セッション受信箱](transcript.md)のトピックを参照。

各セッションの最近のメッセージストリームを統一的に記録（ユーザーとロボット双方）、AIコンテキスト、重複防止、行動分析系モジュールの**共有事実ベース**として使用—各モジュールが個別に履歴を保存する必要がなくなります。

```python
messages = await event.history(20)   # 最近20件のメッセージ、時間昇順
for m in messages:
    print(m["role"], ":", m["text"])  # role: "user" / "bot"
```

- 自動記録：入力メッセージ（role=user）+ ロボットの出力テキスト（role=bot）
- ストレージ：独立したSQLiteテーブル、保持戦略 = 各セッションの上限（デフォルト50）+ グローバルTTL（デフォルト7日）
- 書き込み方法：メモリバッファ + バックグラウンドバッチ落書き（遅延最大1秒）、クエリインターフェースは未落書きのバッファ行を自動的に結合する—同じプロセス内で「読み込みと書き込み」に影響はない；正常終了（`sdk.uninit` / プロセス終了）時に自動的にフラッシュされる。**ハードクラッシュ / 強制終了の際には、直近約1秒の記録が失われる可能性がある**：このベースは最近のコンテキストキャッシュとして位置づけられており、監査用の永続化には適していない
- 設定：`ErisPulse.transcript = {enabled = true, max_per_session = 50, ttl_hours = 168}`
- マネージャーAPI：`sdk.transcript.append() / get() / clear()`、`aflush()` / `flush()`で手動フラッシュ

## メッセージトランザクション：message_tx

トランザクション内のすべての出力送信は自動的に記帳される；**例外が発生した場合、逆順で自動的に既に送信されたメッセージを撤回**（アダプターが`delete_message`を実装していない場合はスキップされ、アカウントは正常に記録される）。

```python
async with event.message_tx():
    await event.reply("処理中です、少々お待ちください")
    result = await do_something()          # ここで例外が発生 →
    await event.reply(f"完了: {result}")   # 以前の「処理中」は自動的に撤回される
```

トランザクション外の送信は記帳されない（ゼロコスト）；`get_send_receipts()`で現在のトランザクションで送信された回執を確認できる。

## リンク追跡：trace-id

各入力イベントは自動的に追跡ID（`event["id"]`を再利用、存在しない場合は生成）を取得し、以下を貫く：

- handlerコンテキスト（`get_current_trace_id()`で読み取り）
- 出力送信（`[Send]`ログ行に`[trace:...]`を追加、`message.sending/sent`フックの`trace_id`フィールド）
- ライフサイクルフックデータ（dictに`_trace_id`を自動的に追加）
- 定向イベント（`lifecycle.emit(..., to=...)`）とメッセージトランザクションの回執

1つのメッセージが複数のモジュールによって処理される場合、全リンクで同一のIDでつながる（ログ / 慢いクエリ / 監査）。

## 他のシステムとの関係

- **所有権**：待ち / リース / タイマーはすべてownerを記録し、アンロード時に回収される（[所有権システム](ownership.md)を参照）
- **スコープ**：返信の判定時にアイデンティティとモジュール次元を再確認；モジュール間呼び出しの監査は出力次元を走る（[スコープ](scope.md)を参照）
- **Conversation**：多段会話はインタラクティブセッションの上位の状態機械（[Conversation](conversation.md)）であり、その待ちも本ページのすべてのキャンセル / 再確認 / 所有権の意味を享受する

## 関連ドキュメント

- [Conversation 多段会話](conversation.md) - 状態機械、自動チェックポイント、および再起動からの回復
- [所有権（owner）システム](ownership.md) - 所有権のクリーンアップの全景と設計の境界
- [スコープ（scope）](scope.md) - 権限再確認と出力監査の設定方法
- [モジュール間通信](module-communication.md) - モジュール間の呼び出しと定向イベント