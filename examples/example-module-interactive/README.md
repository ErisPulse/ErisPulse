# ErisPulse 交互进阶示例模块

演示消息事务与回执账本、ORM 进阶声明（联合唯一 / 自动时间戳 / 惯用快捷）、
存储事务原子性、请求事件审批与发送链修饰方法。

## 功能特性

- 消息事务：`event.message_tx()` 异常自动撤回 + `get_send_receipts()` 回执审计
- ORM 进阶：`__unique_together__` 联合唯一、`auto_now_add` / `auto_now` 时间戳、
  `get_or_create` 惯用快捷
- 存储事务：`storage.atransaction()` 内多行更新原子提交 / 回滚
- 请求审批：好友请求 `event.approve()` / `event.reject()` 自动闭环
- 发送链：`event.send_chain()` 追加 `At` / `Reply` 等修饰方法

## 安装

```bash
pip install -e .
```

## 使用

可用命令：

- `/flash` - 消息事务演示：发出三条消息后人为抛错，前三条自动撤回
- `/flash_ok` - 同上但正常提交，并打印回执账本（message_id）
- `/claim <key>` - ORM 惯用快捷演示：首抢创建（created=True），重复返回首抢时间
- `/transfer <金额> [--boom]` - 存储事务演示：A→B 转账；带 `--boom` 时扣款后
  人为抛错，两行更新全部回滚
- `/chain` - 发送链演示：At 修饰 + Text 发送

好友请求自动同意并回附言欢迎语（演示请求审批闭环，可按需改为 reject）。

## 开发

参考 ErisPulse 交互会话系统与 ORM 文档了解全部能力。
