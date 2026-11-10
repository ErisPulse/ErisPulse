# 性能基準與調優

> [!TIP]
> **什麼時候需要閱讀這篇**：關心事件吞吐與延遲數字、部署前容量評估、版本升級前後想對比性能回退時。不需要則跳過，不會影響其他功能的使用。

## 實測基準（2026-10-05，Python 3.13.14）

同一台機器前後兩輪實測（預熱 + 多輪採樣取百分位），NoneBot2 2.5.0 為獨立環境對照。  
全部數字可用倉庫自帶基準復現：`python tests/performance/benchmark.py`。

### 事件分發（ops/s，越高越好）

| 基準項 | ErisPulse | NoneBot2 2.5.0 | 對比 |
|---|---|---|---|
| 總線單處理器串行延遲 | **9,189** | 3,021 | 3.0× |
| 總線洪泛吞吐（1000 事件/輪） | **9,877** | 2,055 | 4.8× |
| 10 處理器/事件吞吐 | **4,309** | 435 | 9.9× |
| 命令命中（/命令） | **2,165** | 677 | 3.2× |
| 命令 miss（非命令訊息） | **10,818** | 921 | 11.7× |
| 消息橋單處理器（預設全鏈路） | **2,804** | 2,144 | 1.3× |

### 其它子系統能力（優化後）

| 基準項 | ops/s | 基準項 | 數值 |
|---|---|---|---|
| getConfig 熱讀 | 1,086,957 | ORM 單條 create | 407/s |
| KV aset（sqlite） | 1,659 | GET /health（ASGI） | 1,188/s |
| KV aget（sqlite） | 3,333 | module.call RPC | 148,905/s |
| 端到端訊息往返 | 298 | 混合負載 | 142/s |

### 啟動耗時

| 階段 | ErisPulse | NoneBot2 |
|---|---|---|
| 解釋器空轉對照 | 59.5ms | — |
| 冷導入 | 241.7ms | 249.6ms |
| sdk.init / NoneBot init | 30.8ms | 162.3ms |

## 自跑基準與回歸對比

```bash
# 快速檔（樣本數約 1/4，用於冒煙測試）
python tests/performance/benchmark.py --quick

# 完整基準落盤（8 套件：config/event/storage/send/router/module/overall/startup）
python tests/performance/benchmark.py --json baseline.json

# 與舊基準對比（差值 ±5% 閾值內視為雜訊）
python tests/performance/benchmark.py --compare baseline.json

# HTML 報告 / 指定儲存套件後端
python tests/performance/benchmark.py --html report.html
python tests/performance/benchmark.py --backend mysql
```

> CI 注意：基準數字會隨機器浮動，`--compare` 的 ±5% 閾值只適合**同一台機器**的前後對比（升級驗證），不適合跨機器門禁。

## 調優要點

1. **訊息橋全鏈路瓶頸在會話記錄**：預設開啟 transcript 記錄（2.9 起記憶體緩衝 + 後台批量落盤）；無稽核需求時可關閉，全鏈路吞吐約 2,804 → 3,774 ops/s
2. **GC 治理**：`ErisPulse.framework` 的 proactive_gc 配置組（interval / full_every / memory_growth_mb / `idle_only`）——事件洪峰期自動跳過 GC；init 階段 `gc.freeze()` 已內建
3. **儲存後端**：本地單機 sqlite（WAL）足夠；多實例共享資料層切 mysql / postgres（見[儲存後端](storage-backends.md)）
4. **熱路徑已內建優化**（2.9 起，無需配置）：transcript 批量落盤、i18n 缓存、日誌級別守衛、匹配器預編譯、配置延遲寫入統一刷盤
5. **命令治理狀態上限**：冷卻/限流/配額狀態表上限 4096 條（超限淘汰最舊），超大群規模部署無需調整

## 相關文件

- **執行指標觀測**：`/health`（實例身份 / 事件計數）與 `/metrics`（Prometheus 文本，`ErisPulse.server.metrics_enabled` 開啟）請參閱[部署指南](../user-guide/deployment.md)