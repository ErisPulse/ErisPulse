# 類型存根生成（IDE 自動完成）

ErisPulse 透過 entry-points 動態發現模組/適配器，入口點無法在靜態層面得知使用者類別的具體類型。  
`epsdk types` 命令透過掃描已安裝的模組/適配器，產生一個類型存根檔案，讓使用者可以將這些類型用作變數標註，進而獲得 IDE 自動完成。

## 核心設計原則

存根檔案**僅導出類型**，不提供任何執行時實例：

- 所有匯入都在 ``TYPE_CHECKING`` 下，**零執行時開銷、零行為改變**
- 類型名稱採用 entry-point 名的 PascalCase 形式（如 ``yunhu`` → ``Yunhu``），與傳入 ``sdk.adapter.get()`` / ``sdk.module.get()`` 的名稱對應
- 使用者在程式碼中照常用 ``sdk.module.get(...)`` / ``sdk.adapter.get(...)`` 取得實例，只是用匯入的類型做**變數標註**

## 基本用法

在專案根目錄執行：

```bash
epsdk types
```

會在當前目錄產生 `_ep_types.py`，包含所有已安裝模組/適配器的類型。

## 在程式碼中使用

```python
from _ep_types import MyModule, Yunhu
from ErisPulse import sdk

# 用匯入的類型作為變數標註，即可讓 IDE 自動完成該類的方法
my_mod: MyModule = sdk.module.get("MyModule")
my_mod.hello()                  # ← IDE 自動完成 hello

my_adapter: Yunhu = sdk.adapter.get("yunhu")
await my_adapter.Send.To("group", "123").Board(...)   # ← 自動完成平台特有方法
```

## 工作原理

1. 掃描 `erispulse.adapter` / `erispulse.module` entry-points
2. 透過子程序在目標 Python 環境中內省，收集每個適配器/模組的實際類別資訊（包含模組路徑與限定名）
3. 產生 `.py` 檔案，其中：
   - 所有 ``from xxx import Yyy as Zzz`` 都在 ``TYPE_CHECKING`` 下
   - ``Zzz`` 是 entry-point 名的 PascalCase 形式
4. IDE 讀取 ``TYPE_CHECKING`` 部分提供自動完成；執行時不執行任何程式碼

產生的存根範例：

```python
# _ep_types.py（自動產生）
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 適配器
    from MyAdapter.Core import MyAdapter as MyAdapter
    from YunhuAdapter.Core import YunhuAdapter as Yunhu

    # 模組
    from MyModule.Core import Main as MyModule

    __all__ = ['MyAdapter', 'Yunhu', 'MyModule']
```

## 命令選項

| 選項 | 說明 |
|------|------|
| `-o, --output PATH` | 指定輸出檔案路徑（預設 `./_ep_types.py`） |
| `--force` | 覆蓋已存在的存根檔案 |
| `--adapters-only` | 僅掃描適配器 |
| `--modules-only` | 僅掃描模組 |

## 何時重新產生

- 安裝/卸載新的模組或適配器後
- 模組/適配器更新了公開 API 後
- IDE 自動完成失效或類型過期時

## 與 SendDSL 標準方法的關係

`SendDSL` 基類已內建標準發送方法（Text/Image/Voice/Video/File），任何方式取得的 SendDSL 實例都能自動完成這些方法。  
`types` 命令主要用於補全**平台特有方法**（如雲湖的 `Board`、沙盒的 `Dice`）和**模組特有方法**。

## 相關文件

- [SendDSL 詳解](../developer-guide/adapters/send-dsl.md) - 標準發送方法說明
- [適配器開發入門](../developer-guide/adapters/getting-started.md) - 建立適配器