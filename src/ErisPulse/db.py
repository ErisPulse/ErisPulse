"""
# 环境配置

提供键值存储、事务支持、快照和恢复功能，用于管理框架配置数据。基于SQLite实现持久化存储，支持复杂数据类型和原子操作。

## API 文档

### 基本操作
#### get(key: str, default: Any = None) -> Any
获取配置项的值。
- 参数:
  - key: 配置项键名
  - default: 如果键不存在时返回的默认值
- 返回:
  - Any: 配置项的值，如果是JSON格式则自动解析为Python对象
- 示例:
```python
# 获取基本配置
timeout = sdk.env.get("network.timeout", 30)

# 获取结构化数据
user_settings = sdk.env.get("user.settings", {})
if "theme" in user_settings:
    apply_theme(user_settings["theme"])

# 条件获取
debug_mode = sdk.env.get("app.debug", False)
if debug_mode:
    enable_debug_features()
```

#### set(key: str, value: Any) -> bool
设置配置项的值。
- 参数:
  - key: 配置项键名
  - value: 配置项的值，复杂类型会自动序列化为JSON
- 返回:
  - bool: 操作是否成功
- 示例:
```python
# 设置基本配置
sdk.env.set("app.name", "MyApplication")

# 设置结构化数据
sdk.env.set("server.config", {
    "host": "localhost",
    "port": 8080,
    "workers": 4
})

# 更新现有配置
current_settings = sdk.env.get("user.settings", {})
current_settings["last_login"] = datetime.now().isoformat()
sdk.env.set("user.settings", current_settings)
```

#### delete(key: str) -> bool
删除配置项。
- 参数:
  - key: 要删除的配置项键名
- 返回:
  - bool: 操作是否成功
- 示例:
```python
# 删除临时配置
sdk.env.delete("temp.session")

# 条件删除
if not is_feature_enabled():
    sdk.env.delete("feature.config")

# 清理旧配置
for key in sdk.env.get_all_keys():
    if key.startswith("deprecated."):
        sdk.env.delete(key)
```

#### get_all_keys() -> list[str]
获取所有配置项的键名。
- 参数: 无
- 返回:
  - list[str]: 所有配置项的键名列表
- 示例:
```python
# 列出所有配置
all_keys = sdk.env.get_all_keys()
print(f"当前有 {len(all_keys)} 个配置项")

# 按前缀过滤
user_keys = [k for k in sdk.env.get_all_keys() if k.startswith("user.")]
print(f"用户相关配置: {user_keys}")

# 导出配置摘要
config_summary = {}
for key in sdk.env.get_all_keys():
    parts = key.split(".")
    if len(parts) > 1:
        category = parts[0]
        if category not in config_summary:
            config_summary[category] = 0
        config_summary[category] += 1
print("配置分类统计:", config_summary)
```

### 批量操作
#### get_multi(keys: list) -> dict
批量获取多个配置项的值。
- 参数:
  - keys: 要获取的配置项键名列表
- 返回:
  - dict: 键值对字典，只包含存在的键
- 示例:
```python
# 批量获取配置
settings = sdk.env.get_multi([
    "app.name", 
    "app.version", 
    "app.debug"
])
print(f"应用: {settings.get('app.name')} v{settings.get('app.version')}")

# 获取相关配置组
db_keys = ["database.host", "database.port", "database.user", "database.password"]
db_config = sdk.env.get_multi(db_keys)
connection = create_db_connection(**db_config)

# 配置存在性检查
required_keys = ["api.key", "api.endpoint", "api.version"]
config = sdk.env.get_multi(required_keys)
missing = [k for k in required_keys if k not in config]
if missing:
    raise ValueError(f"缺少必要配置: {missing}")
```

#### set_multi(items: dict) -> bool
批量设置多个配置项的值。
- 参数:
  - items: 要设置的键值对字典
- 返回:
  - bool: 操作是否成功
- 示例:
```python
# 批量设置基本配置
sdk.env.set_multi({
    "app.name": "MyApp",
    "app.version": "1.0.0",
    "app.debug": True
})

# 更新系统设置
sdk.env.set_multi({
    "system.max_connections": 100,
    "system.timeout": 30,
    "system.retry_count": 3
})

# 从外部配置导入
import json
with open("config.json", "r") as f:
    external_config = json.load(f)
    
# 转换为扁平结构
flat_config = {}
for section, values in external_config.items():
    for key, value in values.items():
        flat_config[f"{section}.{key}"] = value
        
sdk.env.set_multi(flat_config)
```

#### delete_multi(keys: list) -> bool
批量删除多个配置项。
- 参数:
  - keys: 要删除的配置项键名列表
- 返回:
  - bool: 操作是否成功
- 示例:
```python
# 批量删除临时配置
temp_keys = [k for k in sdk.env.get_all_keys() if k.startswith("temp.")]
sdk.env.delete_multi(temp_keys)

# 删除特定模块的所有配置
module_keys = [k for k in sdk.env.get_all_keys() if k.startswith("module_name.")]
sdk.env.delete_multi(module_keys)

# 清理测试数据
test_keys = ["test.user", "test.data", "test.results"]
sdk.env.delete_multi(test_keys)
```

### 事务管理
#### transaction() -> contextmanager
创建事务上下文，确保多个操作的原子性。
- 参数: 无
- 返回:
  - contextmanager: 事务上下文管理器
- 示例:
```python
# 基本事务
with sdk.env.transaction():
    sdk.env.set("user.id", user_id)
    sdk.env.set("user.name", user_name)
    sdk.env.set("user.email", user_email)

# 带有条件检查的事务
def update_user_safely(user_id, new_data):
    with sdk.env.transaction():
        current = sdk.env.get(f"user.{user_id}", None)
        if not current:
            return False
            
        for key, value in new_data.items():
            sdk.env.set(f"user.{user_id}.{key}", value)
        
        sdk.env.set(f"user.{user_id}.updated_at", time.time())
    return True

# 复杂业务逻辑事务
def transfer_credits(from_user, to_user, amount):
    with sdk.env.transaction():
        # 检查余额
        from_balance = sdk.env.get(f"user.{from_user}.credits", 0)
        if from_balance < amount:
            raise ValueError("余额不足")
            
        # 更新余额
        sdk.env.set(f"user.{from_user}.credits", from_balance - amount)
        
        to_balance = sdk.env.get(f"user.{to_user}.credits", 0)
        sdk.env.set(f"user.{to_user}.credits", to_balance + amount)
        
        # 记录交易
        transaction_id = str(uuid.uuid4())
        sdk.env.set(f"transaction.{transaction_id}", {
            "from": from_user,
            "to": to_user,
            "amount": amount,
            "timestamp": time.time()
        })
```

### 快照管理
#### snapshot(name: str = None) -> str
创建数据库快照。
- 参数:
  - name: 快照名称，默认使用当前时间戳
- 返回:
  - str: 快照文件路径
- 示例:
```python
# 创建命名快照
sdk.env.snapshot("before_migration")

# 创建定期备份
def create_daily_backup():
    date_str = datetime.now().strftime("%Y%m%d")
    return sdk.env.snapshot(f"daily_{date_str}")

# 在重要操作前创建快照
def safe_operation():
    snapshot_path = sdk.env.snapshot("pre_operation")
    try:
        perform_risky_operation()
    except Exception as e:
        sdk.logger.error(f"操作失败: {e}")
        sdk.env.restore(snapshot_path)
        return False
    return True
```

#### restore(snapshot_name: str) -> bool
从快照恢复数据库。
- 参数:
  - snapshot_name: 快照名称或路径
- 返回:
  - bool: 恢复是否成功
- 示例:
```python
# 恢复到指定快照
success = sdk.env.restore("before_migration")
if success:
    print("成功恢复到之前的状态")
else:
    print("恢复失败")

# 回滚到最近的每日备份
def rollback_to_last_daily():
    snapshots = sdk.env.list_snapshots()
    daily_snapshots = [s for s in snapshots if s[0].startswith("daily_")]
    if daily_snapshots:
        latest = daily_snapshots[0]  # 列表已按时间排序
        return sdk.env.restore(latest[0])
    return False

# 灾难恢复
def disaster_recovery():
    snapshots = sdk.env.list_snapshots()
    if not snapshots:
        print("没有可用的快照")
        return False
        
    print("可用快照:")
    for i, (name, date, size) in enumerate(snapshots):
        print(f"{i+1}. {name} - {date} ({size/1024:.1f} KB)")
        
    choice = input("选择要恢复的快照编号: ")
    try:
        index = int(choice) - 1
        if 0 <= index < len(snapshots):
            return sdk.env.restore(snapshots[index][0])
    except ValueError:
        pass
    return False
```

#### list_snapshots() -> list
列出所有可用的快照。
- 参数: 无
- 返回:
  - list: 快照信息列表，每项包含(名称, 创建时间, 大小)
- 示例:
```python
# 列出所有快照
snapshots = sdk.env.list_snapshots()
print(f"共有 {len(snapshots)} 个快照")

# 显示快照详情
for name, date, size in snapshots:
    print(f"名称: {name}")
    print(f"创建时间: {date}")
    print(f"大小: {size/1024:.2f} KB")
    print("-" * 30)

# 查找特定快照
def find_snapshot(prefix):
    snapshots = sdk.env.list_snapshots()
    return [s for s in snapshots if s[0].startswith(prefix)]
```

#### delete_snapshot(name: str) -> bool
删除指定的快照。
- 参数:
  - name: 要删除的快照名称
- 返回:
  - bool: 删除是否成功
- 示例:
```python
# 删除指定快照
sdk.env.delete_snapshot("old_backup")

# 清理过期快照
def cleanup_old_snapshots(days=30):
    snapshots = sdk.env.list_snapshots()
    cutoff = datetime.now() - timedelta(days=days)
    for name, date, _ in snapshots:
        if date < cutoff:
            sdk.env.delete_snapshot(name)
            print(f"已删除过期快照: {name}")

# 保留最新的N个快照
def retain_latest_snapshots(count=5):
    snapshots = sdk.env.list_snapshots()
    if len(snapshots) > count:
        for name, _, _ in snapshots[count:]:
            sdk.env.delete_snapshot(name)
```

## 最佳实践

1. 配置组织
```python
# 使用层次结构组织配置
sdk.env.set("app.server.host", "localhost")
sdk.env.set("app.server.port", 8080)
sdk.env.set("app.database.url", "postgresql://localhost/mydb")

# 使用命名空间避免冲突
sdk.env.set("module1.config.timeout", 30)
sdk.env.set("module2.config.timeout", 60)
```

2. 事务使用
```python
# 确保数据一致性
def update_configuration(config_data):
    with sdk.env.transaction():
        # 验证
        for key, value in config_data.items():
            if not validate_config(key, value):
                raise ValueError(f"无效的配置: {key}")
                
        # 更新
        for key, value in config_data.items():
            sdk.env.set(key, value)
            
        # 记录更新
        sdk.env.set("config.last_updated", time.time())
```

3. 快照管理
```python
# 定期创建快照
def schedule_backups():
    # 每日快照
    if not sdk.env.snapshot(f"daily_{datetime.now().strftime('%Y%m%d')}"):
        sdk.logger.error("每日快照创建失败")
        
    # 清理旧快照
    cleanup_old_snapshots(days=30)
    
# 自动备份重要操作
def safe_bulk_update(updates):
    snapshot_name = f"pre_update_{time.time()}"
    sdk.env.snapshot(snapshot_name)
    
    try:
        with sdk.env.transaction():
            for key, value in updates.items():
                sdk.env.set(key, value)
    except Exception as e:
        sdk.logger.error(f"批量更新失败: {e}")
        sdk.env.restore(snapshot_name)
        raise
```

"""

import os
import json
import sqlite3
import importlib.util
import shutil
import time
import threading
from pathlib import Path
from datetime import datetime
from functools import lru_cache
from .raiserr import raiserr

class EnvManager:
    _instance = None
    db_path = os.path.join(os.path.dirname(__file__), "config.db")
    SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "snapshots")

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            # 确保关键属性在初始化时都有默认值
            self._last_snapshot_time = time.time()
            self._snapshot_interval = 3600
            self._init_db()
            self._initialized = True

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.SNAPSHOT_DIR, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        
        # 启用WAL模式提高并发性能
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """)
        conn.commit()
        conn.close()
        
        # 初始化自动快照调度器
        self._last_snapshot_time = time.time()  # 初始化为当前时间
        self._snapshot_interval = 3600  # 默认每小时自动快照

    def get(self, key, default=None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
                result = cursor.fetchone()
            if result:
                try:
                    return json.loads(result[0])
                except json.JSONDecodeError:
                    return result[0]
            return default
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                self._init_db()
                return self.get(key, default)
            else:
                from . import sdk
                sdk.logger.error(f"数据库操作错误: {e}")

    def get_all_keys(self) -> list:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key FROM config")
            return [row[0] for row in cursor.fetchall()]

    def set(self, key, value):
        serialized_value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        with self.transaction():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, serialized_value))
            conn.commit()
            conn.close()
        
        self._check_auto_snapshot()
        return True

    def set_multi(self, items):
        with self.transaction():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for key, value in items.items():
                serialized_value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", 
                    (key, serialized_value))
            conn.commit()
            conn.close()
        
        self._check_auto_snapshot()
        return True

    def delete(self, key):
        with self.transaction():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM config WHERE key = ?", (key,))
            conn.commit()
            conn.close()
        
        self._check_auto_snapshot()
        return True

    def delete_multi(self, keys):
        with self.transaction():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.executemany("DELETE FROM config WHERE key = ?", [(k,) for k in keys])
            conn.commit()
            conn.close()
        
        self._check_auto_snapshot()
        return True

    def get_multi(self, keys):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        placeholders = ','.join(['?'] * len(keys))
        cursor.execute(f"SELECT key, value FROM config WHERE key IN ({placeholders})", keys)
        results = {row[0]: json.loads(row[1]) if row[1].startswith(('{', '[')) else row[1] 
                    for row in cursor.fetchall()}
        conn.close()
        return results

    def transaction(self):
        return self._Transaction(self)

    class _Transaction:
        def __init__(self, env_manager):
            self.env_manager = env_manager
            self.conn = None
            self.cursor = None

        def __enter__(self):
            self.conn = sqlite3.connect(self.env_manager.db_path)
            self.cursor = self.conn.cursor()
            self.cursor.execute("BEGIN TRANSACTION")
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
                from .logger import logger
                logger.error(f"事务执行失败: {exc_val}")
            self.conn.close()

    def _check_auto_snapshot(self):
        from .logger import logger
        
        if not hasattr(self, '_last_snapshot_time') or self._last_snapshot_time is None:
            self._last_snapshot_time = time.time()
            
        if not hasattr(self, '_snapshot_interval') or self._snapshot_interval is None:
            self._snapshot_interval = 3600
            
        current_time = time.time()
        
        try:
            time_diff = current_time - self._last_snapshot_time
            if not isinstance(time_diff, (int, float)):
                raiserr.register(
                    "ErisPulseEnvTimeDiffTypeError",
                    doc = "时间差应为数值类型",
                )
                raiserr.ErisPulseEnvTimeDiffTypeError(
                    f"时间差应为数值类型，实际为: {type(time_diff)}"
                )

            if not isinstance(self._snapshot_interval, (int, float)):
                raiserr.register(
                    "ErisPulseEnvSnapshotIntervalTypeError",
                    doc = "快照间隔应为数值类型",
                )
                raiserr.ErisPulseEnvSnapshotIntervalTypeError(
                    f"快照间隔应为数值类型，实际为: {type(self._snapshot_interval)}"
                )
                
            if time_diff > self._snapshot_interval:
                self._last_snapshot_time = current_time
                self.snapshot(f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                
        except Exception as e:
            logger.error(f"自动快照检查失败: {e}")
            self._last_snapshot_time = current_time
            self._snapshot_interval = 3600

    def set_snapshot_interval(self, seconds):
        self._snapshot_interval = seconds

    def clear(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM config")
        conn.commit()
        conn.close()

    def load_env_file(self):
        env_file = Path("env.py")
        if env_file.exists():
            spec = importlib.util.spec_from_file_location("env_module", env_file)
            env_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(env_module)
            for key, value in vars(env_module).items():
                if not key.startswith("__") and isinstance(value, (dict, list, str, int, float, bool)):
                    self.set(key, value)
    def __getattr__(self, key):
        try:
            return self.get(key)
        except KeyError:
            from .logger import logger
            logger.error(f"配置项 {key} 不存在")

    def __setattr__(self, key, value):
        try:
            self.set(key, value)
        except Exception as e:
            from .logger import logger
            logger.error(f"设置配置项 {key} 失败: {e}")

    def snapshot(self, name=None):
        if not name:
            name = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = os.path.join(self.SNAPSHOT_DIR, f"{name}.db")
        
        try:
            # 快照目录
            os.makedirs(self.SNAPSHOT_DIR, exist_ok=True)
            
            # 安全关闭连接
            if hasattr(self, "_conn") and self._conn is not None:
                try:
                    self._conn.close()
                except Exception as e:
                    from .logger import logger
                    logger.warning(f"关闭数据库连接时出错: {e}")
            
            # 创建快照
            shutil.copy2(self.db_path, snapshot_path)
            from .logger import logger
            logger.info(f"数据库快照已创建: {snapshot_path}")
            return snapshot_path
        except Exception as e:
            from .logger import logger
            logger.error(f"创建快照失败: {e}")
            raise

    def restore(self, snapshot_name):
        snapshot_path = os.path.join(self.SNAPSHOT_DIR, f"{snapshot_name}.db") \
            if not snapshot_name.endswith('.db') else snapshot_name
            
        if not os.path.exists(snapshot_path):
            from .logger import logger
            logger.error(f"快照文件不存在: {snapshot_path}")
            return False
            
        try:
            # 安全关闭连接
            if hasattr(self, "_conn") and self._conn is not None:
                try:
                    self._conn.close()
                except Exception as e:
                    from .logger import logger
                    logger.warning(f"关闭数据库连接时出错: {e}")
            
            # 执行恢复操作
            shutil.copy2(snapshot_path, self.db_path)
            self._init_db()  # 恢复后重新初始化数据库连接
            from .logger import logger
            logger.info(f"数据库已从快照恢复: {snapshot_path}")
            return True
        except Exception as e:
            from .logger import logger
            logger.error(f"恢复快照失败: {e}")
            return False

    def list_snapshots(self):
        snapshots = []
        for f in os.listdir(self.SNAPSHOT_DIR):
            if f.endswith('.db'):
                path = os.path.join(self.SNAPSHOT_DIR, f)
                stat = os.stat(path)
                snapshots.append((
                    f[:-3],  # 去掉.db后缀
                    datetime.fromtimestamp(stat.st_ctime),
                    stat.st_size
                ))
        return sorted(snapshots, key=lambda x: x[1], reverse=True)

    def delete_snapshot(self, snapshot_name):
        snapshot_path = os.path.join(self.SNAPSHOT_DIR, f"{snapshot_name}.db") \
            if not snapshot_name.endswith('.db') else snapshot_name
            
        if not os.path.exists(snapshot_path):
            from .logger import logger
            logger.error(f"快照文件不存在: {snapshot_path}")
            return False
            
        try:
            os.remove(snapshot_path)
            from .logger import logger
            logger.info(f"快照已删除: {snapshot_path}")
            return True
        except Exception as e:
            from .logger import logger
            logger.error(f"删除快照失败: {e}")
            return False

env = EnvManager()