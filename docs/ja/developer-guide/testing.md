# モジュールテスト（ErisPulse-Testing）

[ErisPulse-Testing](https://github.com/ErisPulse/ErisPulse-Testing) は公式のテストツールキット（RFC EPRFC-2026-001 方向三）です。  
`TestBot`、テストイベント工場、出力メッセージのキャプチャとアサーション機能を提供し、モジュールのテストを通常の pytest と同じように簡単に実現します。

```bash
pip install ErisPulse-Testing
```

> 開発期にフレームワークに依存するツールであり、実行時には一切介入しません。本格的なアダプタープラットフォームのスモークテストは、フレームワークのリポジトリにある `tests/devs/test_adapter.py` を使用してください。

## 快速开始

```python
import pytest
from ErisPulse.Core.Event.command import command
from ErisPulse_Testing import TestBot, create_command_event

async def test_daily(make_testbot):
    async with make_testbot(prefix="/") as bot:
        @command("daily", cooldown="1d", cooldown_reply="今天已签到")
        async def daily(event):
            await event.reply("签到成功！")

        await bot.dispatch(create_command_event("daily", user_id="123"))
        assert bot.last_reply.text == "签到成功！"

        await bot.dispatch(create_command_event("daily", user_id="123"))
        bot.assert_reply_contains("今天已签到")   # 第二次命中冷却
```

`TestBot` は `async with` で使用することを推奨します。起動時に MockAdapter を登録し、出力メッセージをすべてキャプチャし、イベントの重複を抑制し、設定を上書きします。終了時にはフレームワークのグローバル状態を自動的にクリーンアップし、テストケース間の汚染を防ぎます。

pytest fixtures として自動的に利用可能：

- `testbot`：function 級の標準 TestBot（platform=`test`、前缀 `/`）
- `make_testbot(**kwargs)`：カスタムパラメータの工場（`prefix` / `config` / `platform` / `bot_id` ...）

テストプロジェクトの設定で `asyncio_mode = "auto"`（`[tool.pytest.ini_options]`）を推奨します。  
または、テストケースに `@pytest.mark.asyncio` を付与してください。

## 事件工場

| 関数 | 説明 |
|------|------|
| `create_message_event(text, user_id=..., group_id=None, ...)` | メッセージイベント；`group_id` が空の場合はプライベートチャット |
| `create_command_event("roll 3", prefix="/")` | コマンドメッセージ（自動的に前缀を追加、既に前缀がある場合は重複しない） |
| `create_notice_event(type, ...)` | 通知イベント（例：`friend_add`） |
| `create_request_event(type, ...)` | 要求イベント（例：フレンド申請） |
| `create_meta_event("connect", ...)` | meta イベント（`connect` で Bot がオンラインになる） |

すべてのイベントは uuid を使用して一意の `id` を持つため、フレームワークのイベント重複回避に天然に適合します。

注意：合成されたイベントには**プラットフォームの元の報文は含まれません**（`event.get_raw()` は空の dict を返します）。グループチャット / プライベートチャットなどの状況を判断するには、`event.is_group_message()` / `event.get_detail_type()` / `event.get_group_id()` などのアクセサを使用してください。raw を直接読み取らないでください。

## TestBot API

### 分发

```python
trace = await bot.dispatch(event)          # 分发并等待处理器落地，返回决策链
await bot.dispatch(event, drain=False)     # 交互首消息：不等待（wait_reply 处理器长驻）
await bot.send_message("你好")             # 消息分发快捷方式
await bot.reply_as("18", user_id="u1")     # 模拟 wait_reply 用户回复（自动等 waiter 就绪）
```

`dispatch()` は emit 後にすべての処理タスクを gather し、返却時に処理が完了します。**テストでは sleep を必要としません**。

### 出站断言

```python
bot.replies                # 全部出站（SentMessage 列表）
bot.last_reply.text        # 最近一条回复的文本
bot.replies_to("123")      # 按目标过滤
bot.clear_replies()        # 阶段间隔离断言
bot.assert_replied()                       # 存在出站
bot.assert_replied(contains="签到", to="123")
bot.assert_not_replied()                   # 无任何出站
bot.assert_reply_contains("签到成功")       # 存在包含指定文本的出站
await bot.wait_for_reply(timeout=2)        # 等待异步回复出现
```

`SentMessage` のフィールド：`text`（最初の text 段）、`segments`（完全なメッセージ段）、  
`target_type` / `target_id` / `bot_id`（送信コンテキスト）、`has_modifier("at")` など。

### 模块加载

```python
await bot.load_module("MyModule")   # 已注册的模块名（需框架 sdk.init() 完成 entry-point 发现）
await bot.load_module(MyModule)     # 或 BaseModule 子类（自动 register + load，推荐）
await bot.unload_module("MyModule")
```

`on_load` 内で登録されたコマンド / イベントハンドラはモジュールに属し、アンロード時に自動的にクリーンアップされます。これにより、「アンロード後にコマンドが無効になる」ことを直接アサーションできます。  
注意：文字列形式では**entry-point のスキャンは行われません**（TestBot はフレームワークの発見プロセスを初期化しません）。ソフト依存モジュールをテストする場合は、直接クラスオブジェクトを渡すか、または `module.register` を呼び出して名前を渡す必要があります。

### 依赖替换（需 EP>=2.9.0-dev）

```python
with bot.patch_dependency(get_session, fake_session) as mock:
    await bot.dispatch(create_command_event("query"))
    assert mock.called
```

コマンド登録表中の `Depends(get_session)` で宣言された関数が置き換えられます。with スコープを抜けると自動的に元に戻ります。

### 配置覆写

```python
bot = TestBot(prefix="//", config={
    "ErisPulse.event.command.case_sensitive": False,
    "MyModule.api_key": "test-key",     # 模块配置（self.cfg 可读）
})
```

設定はメモリ層に注入され、コマンド前缀などは即座に更新されます。以下の点に注意してください：

1. **落盘**：覆写はフレームワークの遅延書き込み戦略（デフォルトで約 5 秒）に従って cwd の `config/config.toml` に書き込まれます。被測プロジェクトのリポジトリでは `config/` を `.gitignore` に追加してください。
2. **モジュール実行時の書き戻しとの競合（既知の制限）**：被測モジュールが整節で設定を書き戻す（`self.cfg = ...`、例：サブスクリプションリスト）場合、ここでの点分覆写と併存すると、ConfigManager の読み書きの一貫性の問題が発生します。モジュールが整節で読み取る場合、覆写値が見えない可能性があります。また、覆写値も落盤時に整節書き戻しによって上書きされる可能性があります（ErisPulse 2.9.0-dev.2 で修正済み、2.8.x では影響あり）。"実行時書き戻し設定"を含むテストケースでは、2.8.x では fixture で整節書き戻し方式で関連設定をリセットすることを推奨します。

## 分发决策链（"命令为什么没触发"の調査；需 EP>=2.9.0-dev）

`dispatch()` は `DispatchTrace` を返します。これは、今回の分発が経過した各判定ポイントの因果関係のチェーンです。

```python
trace = await bot.dispatch(create_command_event("dailyx", user_id="123"))

trace.verdict        # executed / rejected / dropped / failed / no_match / passed
trace.explain()      # 逐行因果説明（当前语言）
trace.command        # 命中のコマンド名（未命中は None）
trace.steps("cooldown")  # 段階で判定記録をフィルタ

trace.assert_executed("daily")  # 断言実行（失敗時は因果関係の詳細を添付）
trace.assert_rejected()         # 断言権限系判定による拒否
trace.assert_dropped()          # 断言クールダウン等による静かにドロップ
trace.assert_no_match()         # 断言未命中
```

判定のカバレッジ：コマンドテキスト判定、コマンド命中（未命中時は類似語の提案）、作用域、ユーザー ACL、主人チェック、権限関数、クールダウンによる静かにドロップ、パラメータ解析、実行結果、ミドルウェアによる拒否。

本番環境でも、フレームワークの `ErisPulse.Core.Event.trace`（`start_dispatch_trace()` / `format_dispatch_trace()`）を使用して、分発の判定チェーンを収集・レンダリングできます。