# モジュールテスト（ErisPulse-Testing）

[ErisPulse-Testing](https://github.com/ErisPulse/ErisPulse-Testing) は公式のテストツールキット（RFC EPRFC-2026-001 方向三）です：
`TestBot`、テストイベントファクトリー、出力メッセージのキャプチャとアサーション機能を提供し、モジュールのテストを普通の pytest と同じように簡単にします。

```bash
pip install ErisPulse-Testing
```

> 開発期のフレームワーク単方向依存のツールであり、実行時には介入しません。実際のアダプタープラットフォームのスモークテストは、フレームワークリポジトリの `tests/devs/test_adapter.py` を使用してください。

## 速習

```python
import pytest
from ErisPulse.Core.Event.command import command
from ErisPulse_Testing import TestBot, create_command_event

async def test_daily(make_testbot):
    async with make_testbot(prefix="/") as bot:
        @command("daily", cooldown="1d", cooldown_reply="今日のチェックインは完了です")
        async def daily(event):
            await event.reply("チェックイン成功！")

        await bot.dispatch(create_command_event("daily", user_id="123"))
        assert bot.last_reply.text == "チェックイン成功！"

        await bot.dispatch(create_command_event("daily", user_id="123"))
        bot.assert_reply_contains("今日のチェックインは完了です")   # 2回目のコールドダウンにヒット
```

`TestBot` は `async with` で使用することを推奨します：起動時に MockAdapter を登録（すべての出力メッセージをキャプチャ）、イベントの重複除去を無効化し、設定の上書きを適用します。終了時にはフレームワークのグローバル状態を自動的にクリーンアップし、テストケース間の相互汚染を防ぎます。

pytest fixtures として同梱されています（インストール後自動的に利用可能）：

- `testbot`：function 級の標準 TestBot（platform=`test`、プレフィックス `/`）
- `make_testbot(**kwargs)`：カスタムパラメータのファクトリー（`prefix` / `config` / `platform` / `bot_id` ...）

テストプロジェクトの設定で `asyncio_mode = "auto"` を推奨します（`[tool.pytest.ini_options]` 内）。
または、テスト用例に `@pytest.mark.asyncio` を追加してください。

## イベントファクトリー

| 関数 | 説明 |
|------|------|
| `create_message_event(text, user_id=..., group_id=None, ...)` | メッセージイベント；`group_id` が空の場合はプライベートチャット |
| `create_command_event("roll 3", prefix="/")` | コマンドメッセージ（自動的にプレフィックスを追加、すでにプレフィックスが付いている場合は重複しない） |
| `create_notice_event(type, ...)` | 通知イベント（例：`friend_add`） |
| `create_request_event(type, ...)` | 要求イベント（例：フレンド申請） |
| `create_meta_event("connect", ...)` | meta イベント（`connect` で Bot をオンラインにできる） |

すべてのイベントは uuid を持つ一意の `id` を持つため、フレームワークのイベント重複除去を回避できます。

注意：合成されたイベントには**プラットフォームの元の報文は含まれません**（`event.get_raw()` は空の dict を返します）。グループチャット / プライベートチャットなどの状況を判断するには、`event.is_group_message()` / `event.get_detail_type()` / `event.get_group_id()` などのアクセサを使用してください。raw を直接読んではいけません。

## TestBot API

### ディスパッチ

```python
trace = await bot.dispatch(event)          # ディスパッチし、ハンドラが実行完了するまで待つ。返り値は処理の結果
await bot.dispatch(event, drain=False)     # フラグメントメッセージ：待機しない（wait_reply ハンドラは長時間待機）
await bot.send_message("こんにちは")         # メッセージのディスパッチのショートカット
await bot.reply_as("18", user_id="u1")     # wait_reply ユーザーの返信をシミュレート（waiter の準備が整うまで自動的に待つ）
```

`dispatch()` は emit 後、すべての処理中の Task を gather し、返り値が返る時点で処理が完了します——**テストでは sleep は必要ありません**。

### 出力アサーション

```python
bot.replies                # 全ての出力メッセージ（SentMessage のリスト）
bot.last_reply.text        # 最後に送信されたメッセージのテキスト
bot.replies_to("123")      # 目標でフィルタ
bot.clear_replies()        # テスト間の出力メッセージを隔離
bot.assert_replied()                       # 出力メッセージがあることをアサート
bot.assert_replied(contains="チェックイン", to="123")
bot.assert_not_replied()                   # 何も出力メッセージがないことをアサート
bot.assert_reply_contains("チェックイン成功")       # 指定されたテキストを含む出力メッセージがあることをアサート
await bot.wait_for_reply(timeout=2)        # 異動メッセージが返ってくるまで待つ
```

`SentMessage` のフィールド：`text`（最初のテキストセグメント）、`segments`（完全なメッセージセグメント）、
`target_type` / `target_id` / `bot_id`（送信コンテキスト）、`has_modifier("at")` など。

### モジュールのロード

```python
await bot.load_module("MyModule")   # 既に登録されたモジュール名（ErisPulse sdk.init() で entry-point 発見が完了している必要あり）
await bot.load_module(MyModule)     # または BaseModule のサブクラス（自動 register + load、推奨）
await bot.unload_module("MyModule")
```

`on_load` 内で登録されたコマンド / イベントハンドラはモジュールに属し、アンロード時に自動的にクリーンアップされます。これにより、"アンロード後にコマンドが無効化される"ことを直接アサートできます。
注意：文字列形式では**entry-point スキャンは行われません**（TestBot はフレームワークの発見プロセスを初期化しません）。ソフト依存モジュールをテストする場合は、クラスオブジェクトを直接渡すか、または `module.register` を行い、その後に名前を渡してください。

### 依存の置換（EP>=2.9.0-dev が必要）

```python
with bot.patch_dependency(get_session, fake_session) as mock:
    await bot.dispatch(create_command_event("query"))
    assert mock.called
```

置換されるのは、コマンド登録表で `Depends(get_session)` で宣言された関数です。`with` ステートメントの終了時に自動的に元に戻されます。

### 設定の上書き

```python
bot = TestBot(prefix="//", config={
    "ErisPulse.event.command.case_sensitive": False,
    "MyModule.api_key": "test-key",     # モジュールの設定（self.cfg で読み取れる）
})
```

設定はメモリ層に注入され、コマンドのプレフィックスなどは即座に更新されます。2点注意：

1. **永続化**：上書きはフレームワークの遅延書き込み戦略（デフォルトで約 5 秒）に従って cwd の `config/config.toml` に書き込まれます——テスト対象のプロジェクトリポジトリでは `config/` を `.gitignore` に追加してください；
2. **モジュール実行時の設定書き戻しとの競合（既知の制限）**：テスト対象のモジュールが設定を「節単位」で書き戻す（`self.cfg = ...`、例：購読リスト）場合、上記の点分上書きと併存すると、ConfigManager の読み書きの一貫性の問題が発生します——モジュールが「節単位」で読み取ると上書き値が見えない可能性があり、上書き値も永続化時に「節単位」の書き戻しに上書きされる可能性があります（ErisPulse 2.9.0-dev.1 で修正済み、2.8.x では依然影響あり）。"実行時の設定書き戻し"を含むテスト用例は、2.8.x では fixture 内で「節単位」の書き戻しで関連設定をリセットすることを推奨します。

## ディスパッチの決定チェーン（"なぜコマンドが実行されなかったのか"を調査する場合；EP>=2.9.0-dev が必要）

`dispatch()` は `DispatchTrace` を返します——今回のディスパッチで経過した各判定ポイントの因果関係のチェーンです：

```python
trace = await bot.dispatch(create_command_event("dailyx", user_id="123"))

trace.verdict        # executed / rejected / dropped / failed / no_match / passed
trace.explain()      # 各ステップの因果説明（現在の言語で）
trace.command        # 命中したコマンド名（未命中の場合は None）
trace.steps("cooldown")  # 段階で判定記録をフィルタ

trace.assert_executed("daily")  # 実行されたことをアサート（失敗時は因果関係のチェーンを表示）
trace.assert_rejected()         # 権限系の判定で拒否されたことをアサート
trace.assert_dropped()          # 静かにドロップされたことをアサート（コールドダウンなど）
trace.assert_no_match()         # コマンドが一致しなかったことをアサート
```

判定のカバレッジ：コマンドテキストの判定、コマンドの一致（未一致の場合は類似語の提案）、作用域、ユーザー ACL、管理者チェック、権限関数、コールドダウンによる静かなドロップ、パラメータ解析、実行結果、ミドルウェアによる拒否。

本番環境でも、フレームワークに内蔵された `ErisPulse.Core.Event.trace`（`start_dispatch_trace()` / `format_dispatch_trace()`）を使用して、決定チェーンの収集とレンダリングを行うことができます。