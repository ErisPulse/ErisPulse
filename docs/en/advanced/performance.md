# Performance Benchmarking and Tuning

> [!TIP]
> **When to read this**: When you care about event throughput and latency figures, need capacity assessment before deployment, or want to compare performance regressions before and after a version upgrade. Skip this if you don't need it — it won't affect the use of any other features.

## Measured Benchmarks (2026-10-05, Python 3.13.14)

Two rounds of measurements on the same machine (warm-up + multi-round sampling with percentile calculation), with NoneBot2 2.5.0 as an independent environment control.
All figures can be reproduced using the repository's built-in benchmark: `python tests/performance/benchmark.py`.

### Event Dispatching (ops/s, higher is better)

| Benchmark | ErisPulse | NoneBot2 2.5.0 | Comparison |
|---|---|---|---|
| Bus single-handler serial latency | **9,189** | 3,021 | 3.0× |
| Bus flood throughput (1000 events/round) | **9,877** | 2,055 | 4.8× |
| 10 handlers/event throughput | **4,309** | 435 | 9.9× |
| Command hit (/command) | **2,165** | 677 | 3.2× |
| Command miss (non-command messages) | **10,818** | 921 | 11.7× |
| Message bridge single-handler (default full chain) | **2,804** | 2,144 | 1.3× |

### Other Subsystem Capabilities (after optimization)

| Benchmark | ops/s | Benchmark | Value |
|---|---|---|---|
| getConfig hot read | 1,086,957 | ORM single create | 407/s |
| KV aset (sqlite) | 1,659 | GET /health (ASGI) | 1,188/s |
| KV aget (sqlite) | 3,333 | module.call RPC | 148,905/s |
| End-to-end message round-trip | 298 | Mixed workload | 142/s |

### Startup Time

| Phase | ErisPulse | NoneBot2 |
|---|---|---|
| Interpreter idle baseline | 59.5ms | — |
| Cold import | 241.7ms | 249.6ms |
| sdk.init / NoneBot init | 30.8ms | 162.3ms |

## Self-Run Benchmarks and Regression Comparison

```bash
# Quick mode (about 1/4 of the samples, for smoke testing)
python tests/performance/benchmark.py --quick

# Persist the full baseline to disk (8 suites: config/event/storage/send/router/module/overall/startup)
python tests/performance/benchmark.py --json baseline.json

# Compare against an old baseline (differences within the ±5% threshold are treated as noise)
python tests/performance/benchmark.py --compare baseline.json

# HTML report / specify the storage suite backend
python tests/performance/benchmark.py --html report.html
python tests/performance/benchmark.py --backend mysql
```

> CI note: benchmark numbers fluctuate from machine to machine. The ±5% threshold of `--compare` is only suitable for before-and-after comparison on the **same machine** (upgrade verification), not for cross-machine gating.

## Tuning Highlights

1. **The full-pipeline bottleneck of the message bridge lies in session transcript recording**: transcript recording is enabled by default (since 2.9, with in-memory buffering + background batch flushing to disk); it can be disabled if no audit requirement exists, boosting full-pipeline throughput from ~2,804 → 3,774 ops/s
2. **GC management**: the `proactive_gc` configuration group of `ErisPulse.framework` (interval / full_every / memory_growth_mb / `idle_only`) — GC is automatically skipped during event storms; `gc.freeze()` during the init phase is already built in
3. **Storage backends**: local single-machine sqlite (WAL) is sufficient; switch to mysql / postgres when multiple instances share a data layer (see [Storage Backends](storage-backends.md))
4. **Hot paths are already optimized** (since 2.9, no configuration required): transcript batch flushing, i18n caching, log level guards, matcher pre-compilation, and unified flushing of deferred config writes
5. **Command governance state caps**: cooldown/rate-limit/quota state tables are capped at 4096 entries (oldest entries evicted when exceeded); no adjustment is needed even for deployments at very large group scales

## Related Documentation

- **Runtime Metrics Monitoring**: `/health` (instance identity / event counters) and `/metrics` (Prometheus text, enabled via `ErisPulse.server.metrics_enabled`) — see the [Deployment Guide](../user-guide/deployment.md)