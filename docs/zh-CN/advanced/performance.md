# 性能基准与调优

> [!TIP]
> **什么时候需要读这篇**：关心事件吞吐与延迟数字、部署前容量评估、版本升级前后想对比性能回归时。不需要则跳过，不影响其它功能的使用。

## 实测基准（2026-10-05，Python 3.13.14）

同一台机器前后两轮实测（预热 + 多轮采样取百分位），NoneBot2 2.5.0 为独立环境对照。
全部数字可用仓库自带基准复现：`python tests/performance/benchmark.py`。

### 事件分发（ops/s，越高越好）

| 基准项 | ErisPulse | NoneBot2 2.5.0 | 对比 |
|---|---|---|---|
| 总线单处理器串行延迟 | **9,189** | 3,021 | 3.0× |
| 总线洪泛吞吐（1000 事件/轮） | **9,877** | 2,055 | 4.8× |
| 10 处理器/事件吞吐 | **4,309** | 435 | 9.9× |
| 命令命中（/命令） | **2,165** | 677 | 3.2× |
| 命令 miss（非命令消息） | **10,818** | 921 | 11.7× |
| 消息桥单处理器（默认全链路） | **2,804** | 2,144 | 1.3× |

### 其它子系统能力（优化后）

| 基准项 | ops/s | 基准项 | 数值 |
|---|---|---|---|
| getConfig 热读 | 1,086,957 | ORM 单条 create | 407/s |
| KV aset（sqlite） | 1,659 | GET /health（ASGI） | 1,188/s |
| KV aget（sqlite） | 3,333 | module.call RPC | 148,905/s |
| 端到端消息往返 | 298 | 混合负载 | 142/s |

### 启动耗时

| 阶段 | ErisPulse | NoneBot2 |
|---|---|---|
| 解释器空转对照 | 59.5ms | — |
| 冷导入 | 241.7ms | 249.6ms |
| sdk.init / NoneBot init | 30.8ms | 162.3ms |

## 自跑基准与回归对比

```bash
# 快速档（样本数约 1/4，冒烟用）
python tests/performance/benchmark.py --quick

# 完整基线落盘（8 套件：config/event/storage/send/router/module/overall/startup）
python tests/performance/benchmark.py --json baseline.json

# 与旧基线对比（差值 ±5% 阈值内视为噪声）
python tests/performance/benchmark.py --compare baseline.json

# HTML 报告 / 指定存储套件后端
python tests/performance/benchmark.py --html report.html
python tests/performance/benchmark.py --backend mysql
```

> CI 注意：基准数字随机器浮动，`--compare` 的 ±5% 阈值只适合**同一台机器**的前后对比（升级验证），不适合跨机器门禁。

## 调优要点

1. **消息桥全链路瓶颈在会话记录**：默认开启 transcript 记录（2.9 起内存缓冲 + 后台批量落盘）；无审计需求时可关闭，全链路吞吐约 2,804 → 3,774 ops/s
2. **GC 治理**：`ErisPulse.framework` 的 proactive_gc 配置组（interval / full_every / memory_growth_mb / `idle_only`）——事件洪峰期自动跳过 GC；init 阶段 `gc.freeze()` 已内建
3. **存储后端**：本地单机 sqlite（WAL）足够；多实例共享数据层切 mysql / postgres（见[存储后端](storage-backends.md)）
4. **热路径已内建优化**（2.9 起，无需配置）：transcript 批量落盘、i18n 缓存、日志级别守卫、匹配器预编译、配置延迟写入统一刷盘
5. **命令治理状态上限**：冷却/限流/配额状态表上限 4096 条（超限淘汰最旧），超大群规模部署无需调整

## 相关文档

- **运行指标观测**：`/health`（实例身份 / 事件计数）与 `/metrics`（Prometheus 文本，`ErisPulse.server.metrics_enabled` 开启）见[部署指南](../user-guide/deployment.md)
