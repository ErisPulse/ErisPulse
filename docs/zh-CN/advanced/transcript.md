# 会话收件箱（Transcript）

会话收件箱自动记录机器人收发的消息（按会话键 `platform:detail_type:target_id` 组织），
为对话恢复（`event.history`）、影子模块 diff、冷启动回放等提供历史数据。
本文档说明它的**存储模型、保留策略旋钮各保护什么**，以及运行时覆盖 API 与放开限制的真实代价。

> 改限制前请先读完「风险与审计」一节——每个旋钮都有它存在的理由。

## 工作原理

```
消息 ──append()──▶ 写缓冲（内存 deque，硬上限 4096 行）
                        │  每 1 秒批量落盘（单批 ≤64 行，单事务）
                        ▼
              storage 后端的 transcript 表（默认 sqlite）
                        │  每 ~32 条追加惰性触发一次保留清理
                        ▼
              ┌─ 按会话 FIFO 裁剪（max_per_session，默认 50 条）
              └─ 全局 TTL 删除（ttl_hours，默认 168 = 7 天）
```

三个层级的保护，各自防的是不同的风险：

| 旋钮 | 默认值 | 保护什么 | 关闭（=0）的后果 |
|------|--------|----------|------------------|
| 写缓冲上限 | 4096 行（常量，不可配） | **内存**：存储不可用期间的积压不撑爆 RAM | 不可关闭——这是内存防线 |
| 单条文本截断 | 2000 字符（常量，不可配） | 单条消息的内存/磁盘占用 | 不可关闭 |
| `max_per_session` | 50 条/会话 | **磁盘增长**：单会话历史无限堆积 | 该会话历史无限增长 |
| `ttl_hours` | 168（7 天） | **磁盘增长**：全部会话的长期堆积 | `transcript` 表无限增长 |

关键认知：**写缓冲有硬上限，所以放开保留策略不会直接撑爆内存**；
真正的风险在存储层与下游消费者（见下节）。

## 配置

```toml
[ErisPulse.transcript]
enabled = true          # 是否自动记录
max_per_session = 50    # 单会话保留条数（0 = 关闭该会话裁剪）
ttl_hours = 168.0       # 全局保留时长（小时，0 = 永不清理）
```

环境变量覆盖同样生效：`ERISPULSE_TRANSCRIPT_MAX_PER_SESSION`、`ERISPULSE_TRANSCRIPT_TTL_HOURS`。
配置变更热生效（写缓冲落盘节奏内，最多延迟 ~1 秒）。

## 运行时覆盖 API

需要在运行中动态调整（如临时为某个场景延长保留）时：

```python
from ErisPulse import transcript

# 覆盖（优先于配置；仅驻内存，重启后恢复配置值）
transcript.set_retention(max_per_session=500, ttl_hours=24 * 30)

# 查询生效值与来源
transcript.get_retention()
# {'max_per_session': 500, 'ttl_hours': 720.0, 'overridden': ['max_per_session', 'ttl_hours']}

# 恢复按配置生效
transcript.reset_retention()
```

- 传 `0` = 关闭对应策略（会打 warning 日志留痕）；负数抛 `ValueError`；
- 覆盖在下次保留清理时生效（惰性，最多延迟 ~32 条追加的节奏）；
- `transcript` 单例可从根包导入，也可 `sdk.transcript`。

## 风险与审计：放开限制前必读

关闭 `max_per_session` / `ttl_hours`（或大幅调大）后，`transcript` 表随消息量
**无限增长**。后果链：

1. **磁盘写满**——sqlite 单文件持续膨胀，磁盘耗尽后框架存储层不可用；
2. **查询退化**——`get()` / `recent()` / `get_by_trace()` 的扫描成本随表增长；
3. **下游内存压力（OOM 的真实来源）**——把历史整段载入内存的消费者
   （对话恢复带历史、面板全量拉取、你的业务代码 `get(session, n)` 取大 n）
   会随表增长吃掉内存，极端情况触发 OOM kill。

**放开前请自问三件事**：要多久的历史？要多大？谁来清理？
如果答案依赖"永远不删"，正确做法通常是外置归档（定期把旧数据搬到专用库），
而不是让收件箱无限保留。

审计手段（定期检查表规模）：

```python
# 经 ORM/SQL 构建器查行数与体积（sqlite 为例）
from ErisPulse import storage

row = storage.Table("transcript").raw_sql("SELECT COUNT(*) AS n FROM transcript")
```

```sql
-- 直接对 sqlite 文件查询（表体积）
SELECT COUNT(*) FROM transcript;
```

收到 `保留策略已被关闭` 的 warning 日志 = 有人以 0 关闭了策略，请确认是自己的操作。

## 与其它机制的边界

- **交互会话定时器 / wait_reply**：见 [交互会话系统](interaction.md)，与收件箱无关；
- **对话恢复的历史带回**：`resume(with_history=N)` 从收件箱取最近 N 条——
  收件箱被裁剪后能带回的历史随之变少（调大 `max_per_session` 可延长可恢复窗口）；
- **影子模块 diff**：依赖 `get_by_trace` 链路查询，TTL 过短的收件箱会缩短可 diff 窗口。
