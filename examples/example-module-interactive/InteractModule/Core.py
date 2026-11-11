import asyncio
from dataclasses import dataclass, field

# 推荐根导入（2.10+）：常用符号直接从 ErisPulse 根包导入
from ErisPulse import (
    SDK,
    BaseConfig,
    BaseModule,
    Event,
    Field,
    Model,
    ModuleMeta,
    command,
    request,
)
from ErisPulse.runtime import get_send_receipts


class Claim(Model):
    """领取记录（联合唯一 + 自动时间戳声明示例）"""

    __tablename__ = "interact_claims"
    # 联合唯一：同一 user_id 对同一 key 只允许一行（重复插入抛 IntegrityError）
    __unique_together__ = (("user_id", "key"),)

    id: int = Field(primary_key=True, autoincrement=True)
    user_id: str = Field(max_length=64)
    key: str = Field(max_length=64)
    created_at: float = Field(auto_now_add=True)   # 插入时自动打点（浮点纪秒）
    updated_at: float = Field(auto_now=True)       # 插入与实例 save 均自动打点


class Ledger(Model):
    """账户余额（存储事务演示用）"""

    __tablename__ = "interact_ledger"

    account: str = Field(primary_key=True, max_length=32)
    balance: float = Field(default=0.0, ge=0)


class Main(BaseModule):
    """
    交互进阶示例模块

    演示消息事务与回执账本、ORM 进阶声明与惯用快捷、存储事务原子性、
    请求事件审批与发送链修饰
    """

    @dataclass
    class ConfigClass(BaseConfig):
        """InteractModule 模块配置"""

        auto_approve: bool = field(
            default=True,
            metadata={
                "description": "自动同意好友请求（关闭则自动拒绝）",
                "ui": {"widget": "switch", "group": "basic", "order": 1},
            },
        )

    def __init__(self, sdk: SDK = None):
        self.sdk = sdk
        self.logger = self.sdk.logger.get_child("InteractModule")
        self.storage = self.sdk.storage
        self.logger.info("InteractModule 初始化完成")

    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="InteractModule",
            description="交互进阶示例模块",
            version="1.0.0",
            author="ErisDev",
            group="示例",
            tags=["示例", "交互"],
        )

    async def on_load(self, event: dict) -> bool:
        await asyncio.gather(Claim.create_table(), Ledger.create_table())
        # 演示账户 seeding（幂等）
        await Ledger.get_or_create({"balance": 100.0}, account="alice")
        await Ledger.get_or_create({"balance": 0.0}, account="bob")
        self._register_commands()
        self._register_request_handlers()
        return True

    async def on_unload(self, event: dict) -> bool:
        return True

    def _register_commands(self):
        """注册命令处理器"""

        @command("flash", help="消息事务演示：发出后人为抛错，已发消息自动撤回")
        async def flash_command(event: Event):
            async with event.message_tx():
                await event.reply("第 1 条（稍后将随事务撤回）")
                await event.reply("第 2 条（稍后将随事务撤回）")
                raise RuntimeError("人为错误：事务异常退出，上面两条自动逆序撤回")

        @command("flash_ok", help="消息事务演示：正常提交并打印回执账本")
        async def flash_ok_command(event: Event):
            async with event.message_tx():
                await event.reply("临时提示（回执已记账）")
                await event.reply("完成")
                # 回执读取是事务作用域的：仅 message_tx 事务内返回非 None；
                # 每条回执含 platform / bot_id / message_id / trace_id
                for r in get_send_receipts() or []:
                    self.logger.info(f"已发送回执: message_id={r['message_id']}")
            await event.reply("回执已记录到日志")

        @command("claim", help="首抢领取（ORM 联合唯一 + get_or_create 演示）", usage="/claim <key>")
        async def claim_command(event: Event, key: str):
            user_id = event.get_user_id()
            # get_or_create：查得返回 (实例, False)；无则以 kwargs 创建
            claim, created = await Claim.get_or_create(user_id=user_id, key=key)
            if created:
                await event.reply(f"领取成功：{key}（时间戳 {claim.created_at:.0f}）")
            else:
                await event.reply(
                    f"{key} 已被你于 {claim.created_at:.0f} 领取过（联合唯一保证不重复）"
                )

        @command("transfer", help="存储事务演示：alice→bob 转账；--boom 演示回滚", usage="/transfer <金额> [--boom]")
        async def transfer_command(event: Event, amount: float, boom: bool = False):
            async with self.storage.atransaction():
                alice = await Ledger.get(account="alice")
                bob = await Ledger.get(account="bob")
                if alice is None or bob is None or alice.balance < amount:
                    await event.reply("余额不足或账户未初始化")
                    return
                alice.balance -= amount
                bob.balance += amount
                await alice.save(update_fields=["balance"])   # 部分列更新（白名单）
                await bob.save(update_fields=["balance"])
                if boom:
                    raise RuntimeError("人为错误：事务回滚，两行更新全部还原")
            await event.reply(f"转账完成：alice -{amount}，bob +{amount}")

        @command("chain", help="发送链演示：At 修饰 + Text 发送")
        async def chain_command(event: Event):
            # send_chain() 返回已配置目标和发送账号的 SendDSL，
            # 可自由追加修饰方法（reply 覆盖不了的场景）
            await (
                event.send_chain()
                .At(event.get_user_id())
                .Text("这条消息带 At 修饰（send_chain 演示）")
            )

    def _register_request_handlers(self):
        """注册请求事件处理器（审批闭环）"""

        @request.on_friend_request()
        async def friend_request_handler(event: Event):
            user_id = event.get_user_id()
            comment = event.get_comment()
            self.logger.info(f"收到好友请求: {user_id}，附言: {comment}")
            # 声明式开关决定同意 / 拒绝（审批动作走 event.approve / event.reject）
            if self.cfg.auto_approve:
                await event.approve(comment="欢迎！")
            else:
                await event.reject(comment="暂不添加")
