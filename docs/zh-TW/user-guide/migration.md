# 升級遷移指南

> [!TIP]
> **什麼時候需要讀這篇**：從舊版本升級前，核對**需要動程式碼或核對部署**的破壞性變更。按你當前所在版本向下讀對應小節即可；小版本補丁（patch）從不含遷移動作。逐版本完整變更見 [CHANGELOG](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md)。

版本紀律：**補丁版本（x.y.Z）不含遷移動作**，需要動程式碼的變更只出現在 minor 版本（x.Y.0）；本頁覆蓋 **2.0.0 至今**的全部破壞性變更（2.5.0 為首個生產就緒版本，1.x → 2.0.0 的遷移見 CHANGELOG 的 2.0.0 條目）。

---

## 2.0.x → 2.5.0（生產就緒門檻）

- **⚠️ 嚴格模式預設開啟（級別 1）**：未繼承 `BaseModule` / `BaseAdapter` 的舊元件預設**拒絕載入**——豁免清單 `[ErisPulse.framework] strict_mode_exceptions.modules/adapters`，或 `strict_mode = 0` 寬鬆模式
- **首次啟動語言確認互動**（i18n 五種語言）：自動化部署需預設語言（`ERISPULSE_LANG` 環境變數或設定）
- 移除含 C 擴充的第三方相依套件（watchdog / packaging）——aarch64/ARM 安裝相容性提升，requirements 有鎖定的部署需同步清理

## 2.5.x 系列內的破壞性變更

- **CLI 別名治理（2.5.5）**：`ini` 別名移除（與 install 過近）、`lr` 改為 `lsr`——腳本化的部署命令需同步
- **配置 Schema 重構（2.5.5）**：`BaseConfig` 通用基類（`AdapterConfig` 為相容別名）、`description` 支援 i18n 格式；**移除 `AccountConfig` 別名**——自訂配置類繼承需核對
- **適配器配置存取重構（2.5.5）**：`self.cfg` 即時讀取（`self.config` 為相容別名），移除 `_load_config()` / `_load_accounts()` 快取方法——直接呼叫這兩個私有方法的適配器需改走 `self.cfg`
- **元件發現預設啟用（2.5.5）**：新安裝元件預設 `enabled=true`

## 2.6.x

- **移除 `Core/web_status/` 整包**、外部看板娘圖片與 `/status-assets` 靜態掛載——依賴該路由的部署需遷移到 Dashboard

## 2.7.x

- **連接埠佔用為致命錯誤（2.7.1）**：啟動前同步預檢，`sdk.init()` 回傳 `False`，不再靜默順延連接埠——部署腳本需保證連接埠空閒
- **儲存抽象層翻轉為非同步原生契約（2.7.1）**：非同步介面（`aget` / `aset` / `aExecute` / `atransaction`）成為原生主介面，同步 API 成為內建相容層——**現有同步呼叫零修改**；**自訂儲存後端必須遷移到 a 前綴非同步方法**（同步版抽象方法已移除）
- **`Core/storage` 改造為套件**：SQLite 遷入 `Core/storage/sqlite.py`，MySQL / PostgreSQL 預置；`StorageManager` 保留相容別名
- **2.8.0**：`sdk.reload_plugin` 更名 `sdk.reload_module`；獨立事件准入系統 `Core/access.py` 併入 `scope.identity`（配置節 `ErisPulse.access` 移除，遷移到 `ErisPulse.scope.identity`）；命令 ACL 獨立配置節併入 `event.command.acl`；bind 系作用域 API 收斂為字典式配置
- **移除**：安裝腳本的 root/管理員強制確認

## 2.8.0 → 2.9.0

無破壞性變更（全部為宣告式增量）；已捕捉影子模組 `RuntimeError` / `ValueError` 的程式碼需依 2.9.0 注意事項調整。

## 2.9.0 → 2.10.0

- 設定寫入引擎 tomlkit → **tomlclass**（零依賴無損 TOML 編輯）：註解/鍵順序/空行保留語義不變——直接 import tomlkit 操作 `config.toml` 的外部工具鏈需遷移
- `uvicorn` 鎖定 `>=0.35.0,<1.0`（能力探測 `Server._serve()`，缺失時回退公開 `serve()`）
- **2.10.0**：`epsdk init` / `create` 範本移除 `enabled` 設定欄位——模組啟停由框架統一管理，`ConfigClass` 只承載業務參數

## 2.10.x → 2.11.0

- **`sdk.restart()` 語義升級**為元件級熱重載（模組熱重載管線 + 配接器程式碼級重載）；框架自更新與 entry-point 增刪情境改用 `hard_restart()`
- 實例鎖遷移至 `.erispulse/config.lock`——有清理舊鎖腳本（原 `config/config.lock`）的部署需同步路徑

## 2.11.0 → 2.11.2

- **宣告 `AccountConfigClass` 的配接器不再自動產生 `default` 帳戶範本**——帳戶改由使用者在 Dashboard 帳戶精靈中建立，依賴「啟動即有 default 帳戶」的部署需明確新增
- `reload()` / `restart()` 行為收緊（互斥與合併）對正常使用透明

## 2.11.x → 2.12.0

**① 儲存寫入失敗語義收緊（破壞性）**：寫入操作失敗（寫鎖競爭逾時 / SQL 錯誤 / 約束衝突）改為拋出 `StorageOperationError`（`aset` / `adelete` / `aclear` / `set_multi` 及同步橋 `set` / `delete` 同路徑），**不再靜默回傳 `False`**；連接級不可達的冷卻期快速失敗（`False` / `None`）不變。

```python
# 舊：靠回傳值判斷寫入失敗
if not storage.set("key", "value"):
    ...

# 新：try/except
try:
    storage.set("key", "value")
except StorageOperationError:
    ...
```

**② `run_main_loop` 無可用主循環時**改為加入佇列並回傳 `None`，不再建立臨時事件循環——依賴臨時循環行為的呼叫方需改用 `spawn_background`（調度回已註冊主循環）。

**③ 容器內 `epsdk restart`** 改為發 `SIGUSR1` 觸發行程內軟重啟，不再終止重拉——容器部署核對 restart 策略（整個行程重啟交由容器承載）。

**④ 依賴升級**：`tomlclass >=0.4.0,<0.5`。

**⑤ 預設行為變化（2.12.0 / 2.12.1）**：

- 循環連接自癒：命中連接級損壞時自動重建快取連接（2.12.0）
- 元件發現預設啟用、`reload()` / `restart()` 預檢收緊（2.11 系列）
- 2.12.1：事件冪等去重鍵加入平台維度、handler 匹配收口（宣告了 `detail_type` 條件的處理器在事件缺失該維度時不再穿透，原生事件路徑維持放行）、會話綁定支援 `detail_type:` 前綴鍵

## 2.12.1（補丁）

無遷移動作。全部為缺陷修復與內部改善。預設行為變化：**日誌檔案輸出預設開啟**（`log_dir` 預設 `"logs"`，寫入 `logs/erispulse.log`，size/date 輪轉有界）——不需要檔案日誌的部署設 `[ErisPulse.logger] log_dir = ""`；顯式關閉（從開啟切回）會自動清理檔案 handler，不會殘留寫入。

---

## 通用建議

- 升級前讀對應版本的 CHANGELOG「注意事項」；補丁版本（x.y.Z）可放心升
- 重要儲存寫入始終 try/except（語義與版本無關的良好實踐）
- 自訂後端 / 深度整合方關注 minor 版本的「變更 / 移除」分類

## 下一步

- 某一變更的行為細節 → [儲存後端](../advanced/storage-backends.md) · [設定檔說明](configuration.md)
- 升級後行為不符 → [常見問題](faq.md) · `ep doctor`
- 逐版本完整明細 → [CHANGELOG](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md)