# インタラクションセッションシステム

> [!TIP]
> **このドキュメントを読むべきタイミング**：wait_reply、マルチターン対話、タイマーリマインダー、セッション排他、リンクトレースが必要な場合。不要であれば読み飛ばしても、他の機能の利用には影響しません。

> **読み終えると分かること**：`wait_reply` の全パラメータの使い方とキャンセル理由、`.got()` による宣言的マルチターンチェーン、
> セッションタイマー（remind / escalate）、マルチパス待機（expect / select）とセッション排他リース。
>
> **本ドキュメントでは扱わない内容**：マルチターン対話の分岐ステートマシンと再起動復帰（[Conversation マルチターン対話](conversation.md) を参照）；
> 受信箱の保持ポリシー調整項目とランタイムオーバーライド（[セッション受信箱](transcript.md) を参照）。

> [!NOTE]
> 本章の内容には ErisPulse **2.8.0+** が必要です。

ErisPulse は「ユーザーとの継続的なインタラクション」をフレームワークレベルのインフラとして実装しています：1 つの `wait_reply` から、
タイマーリマインダー、マルチパス待機、セッション排他、再起動復帰に至るまで、すべてが統一された
**インタラクションセッションマネージャー**（`Core/Event/interaction.py`、`sdk.interaction`）によってスケジューリングされます。

{!--< tips >!--}
本ドキュメントが扱うすべての機能には**所有者（owner）**が備わっています：インタラクション待機、リース、タイマーはすべて
登録時のモジュール名を記録し、モジュールのアンロード / アダプターのシャットダウン時にはフレームワークが自動的にクリーンアップします。待機側はタイムアウトまで待ちぼうけるのではなく、直ちに通知を受け取ります。
これは所有権システムのインタラクション次元への拡張です（[所有権システム](ownership.md) を参照）。
{!--< /tips >!--}

## 返信待機：wait_reply

**ひとことで言うと**：現在のコルーチンを一時停止して対象ユーザーの次のメッセージを待ち、一致すれば返信イベントを返し、タイムアウトまたはキャンセル時は `None` を返します。`pattern` / `regex` / `validator` で不適切な返信をフィルタリングできます。

`wait_reply` はインタラクションセッションの基礎です——現在のコルーチンを一時停止し、対象ユーザーが次のメッセージで「返信」するのを待ちます。

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    reply = await event.wait_reply(prompt="お名前を入力してください:", timeout=30)
    if reply is None:
        await event.reply("タイムアウトしました")
        return
    await event.reply(f"こんにちは、{reply.get_text()} さん！")
```

### 全パラメータ一覧

| パラメータ | 説明 | デフォルト |
|------|------|------|
| `prompt` | 一時停止前に送信されるプロンプトメッセージ | None |
| `timeout` | 待機タイムアウト（秒） | 60 |
| `pattern` | glob フィルタ（`*` / `?` / `[seq]`）、不一致時は待機を継続 | None |
| `regex` | 正規表現フィルタ（pattern と同時に指定した場合は両方の一致が必要）、不一致時は待機を継続 | None |
| `validator` | 検証関数（Event を受け取り bool を返す）、失敗時は待機を継続 | None |
| `callback` | 返信受信時に呼ばれるコールバック（戻り値方式の代わりとなるもう一つの書き方） | None |
| `method` | prompt の送信メソッド | "Text" |
| `session` | **セッションレベル待機**：同一セッション（グループ / チャンネル）内の誰の返信でも一致可能 | False |

```python
# 金額（数字）のみ受け付け、それ以外は待機を継続
reply = await event.wait_reply("金額を入力してください:", regex=r"\d+\s*円", timeout=30)

# セッションレベル待機：グループ協力シーンで、どのメンバーの回答でも一致可能
reply = await event.wait_reply(session=True, prompt="どなたか答えていただけませんか？")
```

### 待機とコマンドの境界（コマンドパススルー）

待機中に**登録済みコマンド**（例：`/cancel`）を含むメッセージを受信した場合、デフォルトではコマンドディスパッチャーにそのままパスされて実行され、
返信として消費されません（設定項目 `ErisPulse.event.wait_reply.cmdpass`、`True` にすると反転——
メッセージはすべて返信として扱われます）。判定テキストの基準はコマンドディスパッチと同一です：`alt_message` を優先し、
存在しない場合はメッセージセグメントの連結にフォールバックします（2.10.1 以降、純粋な message セグメントアダプターにも同様に適用されます）。

### 待機がキャンセルされるケース

待機はもはや「タイムアウトを待つだけ」ではありません——以下の場合、待機は**直ちに終了**し（`wait_reply` は `None` を返します）、
呼び出し元がタイムアウトまで待ちぼうけることはありません：

| トリガー | キャンセル理由（`InteractionCancelled.reason`） | 説明 |
|------|------|------|
| 所有モジュールのアンロード / 無効化 | `owner_unload` | 所有クリーンアップ：待機を登録したモジュールが消滅する際、一緒に回収される |
| アダプターのシャットダウン / 再起動 | `platform_stop` | そのプラットフォームで保留中の待機がすべてキャンセルされる |
| 同一セッションが新しい待機 / リースに置き換えられる | `conflict` | 下記「セッション調停」を参照 |
| 返信者がブラックリストに登録 / owner モジュールのバインド解除 | `revoked` | 返信一致時の**権限再チェック**：scope のアイデンティティ次元 + モジュール次元 |
| ユーザーの返信が一致 | —— | 通常パス。返信イベントを返す |

低レベルの例外は `InteractionCancelled`（`InteractionError` 例外体系に属します）です。
`wait_reply` はこれを `None` の返却に変換済みです。理由が必要な呼び出し元は
`sdk.interaction.register()` の低レベル API を直接使用できます。

### 返信一致の完全な判定チェーン

返信メッセージが到着すると、インタラクションマネージャーは以下の順序で判定します（コマンドマッチングの**前に**実行されます。
対話の連続性を優先——メッセージが他の高優先度ハンドラーに引き取られていても、保留中の対話は完結できます）：

```
セッションキーの一致（正確な user 次元 → セッションレベルへのフォールバック）
  → pattern / regex テキストフィルタ（不一致なら待機継続）
  → validator 検証（失敗なら待機継続）
  → 権限再チェック（scope のアイデンティティ次元 + owner のモジュール次元、失敗時は待機終了）
  → 待機側のウェイクアップ + イベントの引き取り（mark_processed）
```

## 宣言的マルチターン：`.got()` チェーン（2.11+）

`@command` は**マルチターンフロー制御プロキシ**を返し、`.got()` で収集ステップを順次宣言します——ステップ関数は
パラメータ名で収集済みの値（コマンド入口パラメータを含む）を受け取り、型は `type=` / アノテーションに従って自動解析されます。
低レベルでは Conversation にコンパイルされます：各ステップが 1 つの分岐、ジャンプ時にチェックポイントを自動保存し、**再起動後もユーザーの
返信は保存済みのステップから継続します**（復帰ファクトリはデコレート時に自動登録され、モジュールのアンロード時に自動的に登録解除されます）。

```python
@command("weather")
async def weather(event):
    pass  # 入口：最初の .got の prompt は自動送信されるため、手動で質問する必要なし

@weather.got("city", prompt="都市名を直接返信してください")
async def weather_city(event, city: str):
    await event.reply(f"{city}：晴れ、25℃")

@weather.got("days", prompt="何日分の予報？", type=int, retry_prompt="数字を入力してください")
async def weather_days(event, city: str, days: int):
    await event.reply(f"{city} の今後 {days} 日間……")
```

### パラメータ説明

| パラメータ | 説明 |
|------|------|
| `name` | 収集値の名前（後続のステップ関数に注入されるパラメータ名；フロー内で一意、重複宣言時は登録時にエラー） |
| `prompt` | そのステップに入る際に自動送信される質問 |
| `timeout` | ステップごとの待機タイムアウト（秒数または `"90s"` / `"1h30m"` の時間文字列、デフォルト 60s） |
| `type` | 値の型（`int` / `float` / `str`…；解析失敗時は `retry_prompt` を自動再送、最大 `max_retries` 回） |
| `validator` / `pattern` / `regex` | 返信のフィルタリングと検証（セマンティクスは [`wait_reply`](#返信待機wait_reply) と同一） |
| `session` | セッションレベル待機（同セッション内の誰でも一致可能） |
| `cmdpass` | コマンドパススルーの三状態（デフォルトでは `/cancel` などのコマンドは待機中も通常どおり実行される） |

### セマンティクスと境界

- **いずれかのステップでタイムアウト / 中断 → フロー全体が終了**し、チェックポイントがクリアされます（`wait_reply` と同じセマンティクス）；
  ステップ関数内ではいつでも `event.reply(...)` で中間結果を出力できます
- **同一ユーザーが同時に持てる保留中のインタラクションは 1 つだけ**——2 つ目のフローの待機が前のものを置き換えます
  （`InteractionCancelled("conflict")`）；排他制御が必要な場合は
  [セッションリース](#セッション排他acquire--hold--get_owner_of) を併用してください
- 収集値はフロー内にのみ存在します；再起動を跨いで複雑な状態を保持するオーケストレーションが必要な場合は、直接
  [Conversation](conversation.md) を使用してください（`context` + `branch/goto` + 手動チェックポイント）
- `@command` が返すのはプロキシオブジェクトです：呼び出し動作、`__name__`、docstring、カスタム属性は
  元の関数と完全に一致します；`command.unregister(プロキシ)` は自動的にアンラップします

## セッションタイマー：remind / escalate

「タイムアウト」を戻り値から、オーケストレーション可能なプリミティブへと変えます。タイマーはインタラクションセッションに紐付けられ、
モジュールのアンロード / アダプターのシャットダウン時に自動キャンセルされます。1 セッションあたりのアクティブな remind の上限は 5 個です。

### remind：返信がないとリマインド

```python
@command("ticket")
async def ticket_command(event):
    await event.reply("チケットを送信しました。処理結果はここで通知します")
    # 5 分間返信がなければ穏やかに 1 度催促；ユーザーの返信で自動的にキャンセルされる
    event.remind(300, "まだいますか？結果が出次第、すぐにお知らせします")
    reply = await event.wait_reply(timeout=3600)
    ...
```

- `event.remind(delay, text=None, *, callback=None)`：期限到来時に現在のセッションへ `text` を送信します
  （または `callback(event)` を実行、同期 / 非同期両対応）。**強制検証**：`text` と
  `callback` はどちらか一方のみ指定できます（どちらも指定しないと `ValueError` がスローされます）
- `Reminder` ハンドルを返します：`reminder.cancel()` で手動キャンセル、`reminder.expired` で状態照会
- ユーザーがそのセッションで**返信すると自動的にキャンセル**されます——これこそが「リマインド」のセマンティクスです：
  リマインドはユーザーが沈黙しているときにだけ現れます
- `Conversation` 内でも同様に利用可能：`conv.remind(120, "まだ考えていますか？")`

### escalate：時刻到来時に確実に実行されるエスカレーション

```python
event.escalate(1800, lambda e: notify_master(f"チケットが 30 分間未処理：{event.get_command_args()}"))
```

`remind` との唯一の違い：**ユーザーの返信ではキャンセルされない**——エスカレーションアクション（オーナーへの通知、有人対応への切り替え）は
「タイムアウト時に必ず届く」という約束であり、手動の `cancel()` / モジュールのアンロード / アダプターのシャットダウンでのみキャンセルされます。

| | `remind` | `escalate` |
|---|---|---|
| 期限到来時の動作 | テキスト送信 / callback 実行 | callback 実行 |
| ユーザーの返信 | **自動キャンセル** | 影響なし |
| 所有クリーンアップ（アンロード / プラットフォーム停止） | キャンセル | キャンセル |
| 1 セッションあたりの上限 | 5 | 無制限（所有クリーンアップが最終的なセーフティネット） |

## マルチパス待機：expect + select

**ひとことで言うと**：`expect` は期待を記述するだけで待機は登録せず、`select` が複数の期待をまとめて保留します。いずれかが先に一致した時点で `(インデックス, 返信イベント)` を返し、一致しなかったものは自動的にクリーンアップされます。

複数の期待を同時に保留し、**早い者勝ち**です——典型的なシーン：管理者の承認を待つと同時にユーザーの取り消しを待つ、
複数人による協調投票など。

```python
which, reply = await event.select(
    event.expect(pattern="承認*", user="10001"),
    event.expect(pattern="拒否*", user="10002"),
    event.expect(validator=lambda e: e.get_text() == "保留", session=True),
    timeout=60,
)
if which is None:
    await event.reply("60 秒以内に承認結果が届きませんでした")
elif which == 0:
    await event.reply("承認済み")
elif which == 1:
    await event.reply("拒否済み")
```

- `event.expect(...)` は**期待の記述**を構築します（待機は何も登録しません）：`pattern` / `regex` / `validator` / `user`（返信者を限定）/ `session`（誰でも回答可能）をサポートします
- `event.select(*expectations, timeout=60)`：一括登録 → いずれかが一致した時点で
  `(インデックス, 返信イベント)` を返す → 一致しなかった待機は自動キャンセル；すべてタイムアウトした場合は `(None, None)` を返します。
  **強制検証**：最低 1 つの expectation を渡す必要があり、そうでなければ `ValueError` がスローされます
- 一致したイベントはすでにフレームワークが引き取り済み（`mark_processed`）のため、他のハンドラーによって重複消費されることはありません

{!--< tips >!--}
`select` はマルチスレッドの `asyncio.wait` による手動オーケストレーションと比べて：期待が不一致のときの自動クリーンアップ、
一致イベントの自動引き取り、権限再チェックと所有クリーンアップがすべて有効——Future を自分で管理する必要はまったくありません。
{!--< /tips >!--}

> [!NOTE]
> 2.10.1 以降、`select` は**集約待機**となりました：すべての期待は単一エントリ + カスタム一致判定に統合され、
> 同一キーの複数パス（同じ user に異なる pattern を 2 つ登録するなど）が互いにキャンセルし合うことはなく、いずれかのパスが先に一致した時点で返ります。
> 返信テキストの判定基準は `alt_message` 優先 + メッセージセグメントへのフォールバック（コマンドディスパッチと同一）です。
>
> 境界に関する説明：`event.wait_for(...)` はアダプターのイベントバスに直接紐付けられ、ミドルウェアと
> detail_type の条件フィルタを**経由しません**（身元の受け入れ判定はディスパッチ入口で担保されます）；完全なパイプラインを必要とする待機には
> `wait_reply` / `select` を使用してください。

## セッション排他：acquire / hold / get_owner_of

所有権は「リソース」から「セッション」へと拡張されます——「このユーザーは現在誰に占有されているか」が第一級のクエリとなります。

```python
# 照会：このセッションは現在、誰が対話中か？（空きの場合は None を返す）
owner = sdk.interaction.get_owner_of(event)
if owner and owner != "MyModule":
    return  # 他のモジュールが対話中のため、邪魔しない

# 排他リース：セッションを独占（deny 戦略、占有中の場合は None を返す）
lease = sdk.interaction.acquire(event)          # デフォルト TTL は 1 時間、ttl= で指定可能
if lease is None:
    return  # すでに占有されている
try:
    ...  # 独占インタラクション
finally:
    lease.release()
```

コンテキストマネージャー形式（取得に失敗すると `SessionOccupiedError` がスローされます）：

```python
with sdk.interaction.hold(event) as lease:
    ...  # 抜ける際に自動解放
```

リースは `renew(ttl)` による延長をサポートします；TTL は遅延期限切れ方式——期限切れのリースは次回アクセス時に自動的にクリーンアップされます。

`Conversation.resume()` で対話を復帰する際、フレームワークは自動的にリースを取得します（
[Conversation マルチターン対話](conversation.md) の「復帰即引き継ぎ」を参照）——
復帰した対話は必然的にセッションを保持するため、他のモジュールが割り込むことはありません。

## セッション受信箱：event.history

> 保持ポリシー（7 日間 / 条数上限）とランタイムオーバーライド API、リスクと監査については[セッション受信箱](transcript.md)の専用ドキュメントを参照してください。

セッションごとの直近メッセージフローの統一記録（ユーザー + ボットの双方）で、AI コンテキスト、
リピート防止、行動分析系モジュールにとっての**共有ファクト基盤**です——各モジュールが個別に履歴を保存する必要はもうありません。

```python
messages = await event.history(20)   # 現在のセッションの直近 20 件、時刻昇順
for m in messages:
    print(m["role"], ":", m["text"])  # role: "user" / "bot"
```

- 自動記録：受信メッセージ（role=user）+ ボットの送信テキスト（role=bot）
- ストレージ：独立した SQLite テーブル、保持ポリシー = セッションごとの上限（デフォルト 50）+ グローバル TTL（デフォルト 7 日間）
- 書き込み方式：メモリバッファ + バックグラウンドでの一括ディスク書き込み（遅延は最大 1 秒）、照会インターフェースはディスク未書き込みのバッファ行を自動的にマージするため、同一プロセス内の「自分の書き込みの読み取り」は影響を受けません；正常終了時（`sdk.uninit` / プロセス終了）には自動的にフラッシュされます。**ハードクラッシュ / 強制終了時には直近約 1 秒分の記録が失われる可能性があります**：この基盤は直近コンテキストキャッシュとしての位置づけであり、監査レベルの永続化には適しません
- 設定：`ErisPulse.transcript = {enabled = true, max_per_session = 50, ttl_hours = 168}`
- マネージャー API：`sdk.transcript.append() / get() / clear()`、`aflush()` / `flush()` による手動フラッシュ

## メッセージトランザクション：message_tx

トランザクション内のすべての送信は自動的に台帳へ記録されます；**異常終了時には送信済みメッセージが逆順に自動取り消しされます**
（アダプターが `delete_message` を実装していない場合はスキップされますが、台帳への記録は通常どおり行われます）。

```python
async with event.message_tx():
    await event.reply("処理中です。お待ちください")
    result = await do_something()          # ここで例外がスローされると →
    await event.reply(f"完了: {result}")   # 直前の「処理中」が自動取り消しされる
```

トランザクション外の送信は台帳に記録されません（ゼロオーバーヘッド）；トランザクション内ではいつでもレシート台帳を読み取れます。典型的な用途は**自己削除ボット**
（送信と同時に遅延取り消しをスケジュール）と送信監査です：

```python
import asyncio
from ErisPulse.runtime import get_send_receipts

async def delayed_delete(adapter, message_id: str, delay: float):
    await asyncio.sleep(delay)
    await adapter.delete_message(message_id)

async with event.message_tx():
    await event.reply("一時的な通知")
    for r in get_send_receipts() or []:
        # 各レシートには platform / bot_id / message_id / trace_id が含まれる
        asyncio.create_task(delayed_delete(adapter, r["message_id"], 30))
```

レシートの読み取りは**トランザクションスコープ**です：`message_tx()` トランザクション内でのみ非 `None` を返し、
トランザクション外では常に `None` です；すべての送信（トランザクション外を含む）を捕捉する必要がある場合は `message.sending/sent`
フックを使用してください（[リンクトレース](#リンクトレースtrace-id) の `trace_id` フィールドを参照）。

## リンクトレース：trace-id

すべての受信イベントは自動的にトレース ID を取得し（`event["id"]` を再利用、欠落時は生成）、以下に渡って引き継がれます：

- ハンドラーコンテキスト（`get_current_trace_id()` で読み取り）
- 送信（`[Send]` ログ行に `[trace:...]` を付加、`message.sending/sent` フックの `trace_id` フィールド）
- ライフサイクルフックデータ（dict に `_trace_id` を自動補完）
- 宛先指定イベント（`lifecycle.emit(..., to=...)`）とメッセージトランザクションレシート

1 つのメッセージが複数のモジュールによってリレー処理される場合でも、チェーン全体を同一の ID で紐付けられます（ログ / スロークエリ / 監査）。

## 他のシステムとの関係

- **所有権**：待機 / リース / タイマーはすべて owner を記録し、アンロード時に即座に回収されます（[所有権システム](ownership.md)）
- **スコープ**：返信一致時の再チェックはアイデンティティ + モジュール次元；モジュール間呼び出しの監査は送信（アウトバウンド）次元で行われます（[スコープ](scope.md)）
- **Conversation**：マルチターン対話はインタラクションセッションの上に構築された分岐ステートマシンです（[Conversation](conversation.md)）。
  その待機も本ページのすべてのキャンセル / 再チェック / 所有セマンティクスを同様に享受します

## 関連ドキュメント

- [Conversation マルチターン対話](conversation.md) - 分岐ステートマシン、自動チェックポイントと再起動復帰
- [所有権（owner）システム](ownership.md) - 所有クリーンアップの全体像と設計上の境界
- [スコープ（scope）](scope.md) - 権限再チェックと送信監査の設定方法
- [モジュール間通信](module-communication.md) - モジュール間呼び出しと宛先指定イベント