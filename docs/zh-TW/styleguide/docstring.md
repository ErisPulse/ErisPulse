# ErisPulse 注釋風格規範

在建立 EP 核心方法時必須添加方法註解，註解格式如下：

## 模組級文件註釋

每個模組文件開頭應包含模組文件：
```python
"""
[模組名稱]
[模組功能描述]

{!--< tips >!--}
重要使用說明或注意事項
{!--< /tips >!--}
"""
```

## 方法註釋

### 基本格式
```python
def func(param1: type1, param2: type2) -> return_type:
    """
    [功能描述]
    
    :param param1: [類型1] [參數描述1]
    :param param2: [類型2] [參數描述2]
    :return: [返回類型] [返回描述]
    """
    pass
```

### 完整格式（適用於複雜方法）
```python
def complex_func(param1: type1, param2: type2 = None) -> Tuple[type1, type2]:
    """
    [功能詳細描述]
    [可包含多行描述]
    
    :param param1: [類型1] [參數描述1]
    :param param2: [類型2] [可選參數描述2] (預設: None)
    
    :return: 
        type1: [返回參數1描述]
        type2: [返回參數2描述]
    
    :raises ErrorType: [錯誤描述]
    """
    pass
```

## 特殊標籤（用於 API 文件生成）

當方法註釋包含以下內容時，將在 API 文件建構時產生對應效果：

| 標籤格式 | 作用 | 示例 |
|---------|------|------|
| `{!--< internal-use >!--}` | 標記為內部使用，不產生文件 | `{!--< internal-use >!--}` |
| `{!--< ignore >!--}` | 忽略此方法，不產生文件 | `{!--< ignore >!--}` |
| `{!--< deprecated >!--}` | 標記為過時方法 | `{!--< deprecated >!--} 請使用 new_func() 代替` |
| `{!--< experimental >!--}` | 標記為實驗性功能 | `{!--< experimental >!--} 可能不穩定` |
| `{!--< tips >!--}...{!--< /tips >!--}` | 多行提示內容 | `{!--< tips >!--}\n重要提示內容\n{!--< /tips >!--}` |
| `{!--< tips >!--}` | 单行提示内容 | `{!--< tips >!--} 注意: 此方法需要先初始化` |

## 最佳建議

1. **類型註解**：使用 Python 類型註解語法
   ```python
   def func(param: int) -> str:
   ```

2. **參數說明**：對可選參數註明預設值
   ```python
   :param timeout: [int] 超時時間(秒) (預設: 30)
   ```

3. **返回值**：多返回值使用 `Tuple` 或明確說明
   ```python
   :return: 
       str: 狀態資訊
       int: 狀態碼
   ```

4. **異常說明**：使用 `:raises` 標註可能拋出的異常
   ```python
   :raises ValueError: 當參數無效時拋出
   ```

5. **內部方法**：非公開 API 應添加 `{!--< internal-use >!--}` 標籤

6. **過時方法**：標記過時方法並提供替代方案
   ```python
   {!--< deprecated >!--} 請使用 new_method() 代替 | 2025-07-09
   ```