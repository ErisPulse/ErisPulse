# モジュールテスト（ErisPulse-Testing）

[ErisPulse-Testing](https://github.com/wsu2059q/ErisPulse-Testing) は公式のテストツールキット（RFC EPRFC-2026-001 方向三）です：
`TestBot`、テストイベントファクトリー、出力メッセージのキャプチャとアサーション機能を提供し、通常の pytest と同じようにモジュールのテストを簡単に行えます。

```bash
pip install ErisPulse-Testing
```

> フレームワークの開発期のツールであり、実行時には介入しません。実際のアダプタープラットフォームのスモークテストを行うには、フレームワークリポジトリの `tests/devs/test_adapter.py` を使用してください。

## 快速開始

```python
import pytest
from ErisPulse.Core.Event.command import command
from ErisPulse_Testing import TestBot, create_command_event

async def test_daily(make_testbot):
    async with make_testbot(prefix="/") as bot:
        @command("daily", cooldown="1d", cooldown_reply="今日のログイン完了")
        async def daily(event):
            await event.reply("ログイン完了！")

        await bot.dispatch(create_command_event("daily", user_id="123"))
        assert bot.last_reply.text == "ログイン完了！"

        await bot.dispatch(create_command_event("daily", user_id="123"))
        bot.assert_reply_contains("今日のログイン完了")   # クールダウンの2回目のヒット
```

`TestBot` は `async with` で使用することを推奨します。起動時に MockAdapter を登録（すべての出力イベントをキャプチャ）、イベントの重複を無効化し、設定のオーバーライドを適用します。終了時にはフレームワークのグローバル状態を自動的にクリーンアップし、テストケース間で相互に汚染されないようにします。

pytest fixtures（インストール後に自動的に利用可能）：

- `testbot`：function 級の標準 TestBot（platform=`test`、プレフィックス `/`）
- `make_testbot(**kwargs)`：カスタムパラメータのファクトリ（`prefix` / `config` / `platform` / `bot_id` ...）

テストプロジェクトの設定で `asyncio_mode = "auto"` を設定すること（`[tool.pytest.ini_options]`）を推奨します。または、テストケースに `@pytest.mark.asyncio` を追加してください。

## イベント工場

| 関数 | 説明 |
|------|------|
| `create_message_event(text, user_id=..., group_id=None, ...)` | メッセージイベント；`group_id` が空の場合はプライベートチャット |
| `create_command_event("roll 3", prefix="/")` | コマンドメッセージ（自動的にプレフィックスを追加、すでにプレフィックスが付いている場合は重複しない） |
| `create_notice_event(type, ...)` | 通知イベント（例：`friend_add`） |
| `create_request_event(type, ...)` | 要求イベント（例：友達申請） |
| `create_meta_event("connect", ...)` | meta イベント（`connect` は Bot をオンラインにすることができる） |

すべてのイベントは uuid を使用して一意の `id` を持つため、フレームワークのイベント重複回避を自然に回避します。

## TestBot API

### 分发

```python
trace = await bot.dispatch(event)          # イベントの処理を分派し、タスクの終了を待機して返す
await bot.dispatch(event, drain=False)     # メッセージの最初の返信：待機しない（wait_reply ハンドラは常駐）
await bot.send_message("你好")             # メッセージの分派のショートカット
await bot.reply_as("18", user_id="u1")     # wait_reply のユーザーの返信をシミュレート（自動で waiter の準備完了を待つ）
```

`dispatch()` は emit 後にすべての処理タスクを gather し、返却された時点で処理が完了するため、**テストでは sleep は不要**です。

### 出力メッセージの検証

```python
bot.replies                # すべての出力メッセージ（SentMessage のリスト）
bot.last_reply.text        # 最後の返信メッセージのテキスト
bot.replies_to("123")      # 目標を基準にフィルタリング
bot.clear_replies()        # 段階間で検証を隔離
bot.assert_replied()                       # 出力メッセージが存在する
bot.assert_replied(contains="签到", to="123")
bot.assert_not_replied()                   # 何も出力されていない
bot.assert_reply_contains("签到成功")       # 指定されたテキストを含む出力メッセージが存在する
await bot.wait_for_reply(timeout=2)        # 異步返信が現れるまで待つ
```

`SentMessage` のフィールド：`text`（最初のテキストセグメント）、`segments`（完全なメッセージセグメント）、
`target_type` / `target_id` / `bot_id`（送信の上下文）、`has_modifier("at")` など。

### モジュールのロード

```python
await bot.load_module("MyModule")   # entry-point が登録済みのパッケージ名
await bot.load_module(MyModule)     # または BaseModule のサブクラス（自動で register + load）
await bot.unload_module("MyModule")
```

`on_load` 内で登録されたコマンド / イベントハンドラはモジュールに属し、アンロード時に自動的にクリーンアップされるため、"アンロード後にコマンドが無効になる"ことを直接検証できます。

### 依存関係の置換

```python
with bot.patch_dependency(get_session, fake_session) as mock:
    await bot.dispatch(create_command_event("query"))
    assert mock.called
```

コマンド登録表の `Depends(get_session)` で宣言された関数を置換します。with ブロックを抜けると自動で元に戻ります。

### 設定の上書き

```python
bot = TestBot(prefix="//", config={
    "ErisPulse.event.command.case_sensitive": False,
    "MyModule.api_key": "test-key",     # モジュールの設定（self.cfg で読み取れる）
})
```

設定はメモリ上に注入され（ファイルに書き込まれない）、コマンドの前処理で即座に反映されます。

## 分配決定チェーン（「なぜコマンドが実行されなかったか」のトラブルシューティング）

`dispatch()` は `DispatchTrace` を返します。これは、今回の分配処理で経由した各判定ポイントの因果関係のチェーンです：

```python
trace = await bot.dispatch(create_command_event("dailyx", user_id="123"))

trace.verdict        # executed / rejected / dropped / failed / no_match / passed
trace.explain()      # 因果の説明を1行ずつ出力（現在の言語）
trace.command        # 命中したコマンド名（未命中の場合は None）
trace.steps("cooldown")  # 階段ごとに判定記録をフィルタリング

trace.assert_executed("daily")  # 実行を断言（失敗時には因果関係のチェーンを含む）
trace.assert_rejected()         # 権限系の判定で拒否されたことを断言
trace.assert_dropped()          # 冷却などにより静かにドロップされたことを断言
trace.assert_no_match()         # コマンドが一致しなかったことを断言
```

判定のカバレッジ：コマンドテキストの判定、コマンドの一致（未一致の場合には類似コマンドの提案を含む）、スコープ、ユーザー ACL、オーナーチェック、権限関数、冷却による静かなドロップ、パラメータ解析、実行結果、ミドルウェアによる否決。

本番環境でも、フレームワーク内に用意されている `ErisPulse.Core.Event.trace`（`start_dispatch_trace()` / `format_dispatch_trace()`）を使用して、決定チェーンの収集とレンダリングが可能です。