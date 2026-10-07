# ErisPulse 性能基准

覆盖全部核心组件的性能基准工具（`benchmark.py`），用于回答三个问题：**框架现在多快、改动让它变快还是变慢、瓶颈在哪**。纯标准库实现（零新增依赖），运行期间所有状态（config.toml / sqlite 数据库）均落在系统临时目录，不影响真实项目配置。

> 本文件是开发工具的随附说明；`benchmark.py` 为手动工具，pytest 默认不收集（无 `test_` 前缀用例，且本目录已被 pytest 配置忽略），CI 也不运行。

## 快速开始

```bash
# 全套件完整档（约 3~6 分钟）
python tests/performance/benchmark.py

# 只跑某几个套件 + 快速档（样本数约 1/4，用于冒烟）
python tests/performance/benchmark.py --suite event,config --quick

# 落盘基线 → 改动代码后对比（回归检测）
python tests/performance/benchmark.py --json base.json
python tests/performance/benchmark.py --compare base.json

# 生成 HTML 报告（可直接浏览器打开）
python tests/performance/benchmark.py --html report.html

# 存储套件切换后端（需对应驱动 extra 与连接环境变量）
python tests/performance/benchmark.py --suite storage --backend mysql
```

全部基准项正常完成时退出码 0，任一失败为 1（跳过不算失败）。

## 覆盖范围

| 套件 | 内容 |
|------|------|
| **config** | getConfig 热读 / 脏覆盖层读、setConfig 各写入路径（含落盘）、getAllConfig、ConfigClass 声明式配置属性访问、`get_event_config()` 合成成本 |
| **event** | 事件总线直连吞吐/延迟、中间件链、detail_type/pattern 匹配、handler 注册、lifecycle.fire、消息桥全链路、命令命中/miss、事件洪泛（含每事件延迟分布） |
| **storage** | KV 异步/同步读写删、批量 multi、查询构建器、事务、ORM 增查（`--backend` 可切 mysql / postgres） |
| **send** | SendDSL 链构建与完整 hooked 发送路径（mock 传输层，无网络） |
| **router** | ASGI 层请求（httpx ASGITransport，不占端口）：内置 /health 与带框架中间件管线的自定义路由 |
| **module** | 跨模块 RPC（`module.call`）、模块属性访问、后台任务派发 |
| **overall** | 端到端全链路（消息事件 → 命令 → 存储写入 → 出站发送）与混合负载 |
| **startup** | 解释器启动对照、冷导入、`sdk.init()` / `sdk.uninit()`、装载 1 适配器 + 1 模块 |

同目录的 `test_perf_*.py` 为批量操作正确性断言（同样被 pytest 默认忽略，仅手动运行）。

## 如何解读结果

- **吞吐（ops/s）**：每秒完成的操作数，越高越好。注意注释里的单位（如 `aset_multi ×100键` 的一次操作包含 100 个键）。
- **延迟（avg / p50 / p95 / p99，毫秒）**：单操作耗时分布。串行延迟项逐操作计时；洪泛项的延迟含队列排队时间。
- 事件分发项在**默认配置**下测量（含每条消息的会话记录写入与命令前缀扫描）；`消息桥单 handler(transcript 关)` 是关闭会话记录的对照项。
- 总线直连项（`总线单 handler …`）不经过消息桥，反映分发引擎本身的成本。
- 存储项基于 sqlite（WAL）；切换 `--backend` 后数据不与 sqlite 可比。
- `startup` 套件已预热首个周期（含 fastapi 等惰性导入的一次性成本）。

## 回归对照工作流

```bash
python tests/performance/benchmark.py --json before.json   # 改动前
# ……修改框架代码……
python tests/performance/benchmark.py --compare before.json  # 改动后对比
```

对比输出每项的吞吐与 p50 变化百分比，±5% 以内视为噪声。两次运行尽量同机、同 Python 版本、相近负载；只关注 2 倍级别或稳定复现的差异。

## 注意事项

- 基准包含真实的日志格式化成本（与生产一致），但已压制控制台输出（日志级别 WARNING）。
- `--keep` 保留临时工作目录（排查失败项）；`--compare` 需提供旧基线 JSON。
- Windows 下后台/重定向运行建议加 `PYTHONUNBUFFERED=1` 并输出到文件，避免管道缓冲造成"无输出"假象。
