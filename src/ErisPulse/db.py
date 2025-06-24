"""
# 环境配置

提供键值存储、事务支持、快照和恢复功能，用于管理框架配置数据。

## API 文档
### 基本操作：
    - get(key, default=None) -> any: 获取配置项
    - set(key, value) -> bool: 设置配置项
    - delete(key) -> bool: 删除配置项
    - get_all_keys() -> list[str]: 获取所有键名

### 批量操作：
    - get_multi(keys) -> dict: 批量获取键值
    - set_multi(items) -> bool: 批量设置键值
    - delete_multi(keys) -> bool: 批量删除键值

### 事务管理：
    - transaction() -> contextmanager: 创建事务上下文

### 快照管理：
    - snapshot(name=None) -> str: 创建数据库快照
    - restore(snapshot_name) -> bool: 从快照恢复
    - list_snapshots() -> list: 列出所有快照
    - delete_snapshot(name) -> bool: 删除指定快照
    - set_snapshot_interval(seconds): 设置自动快照间隔

### 其他功能：
    - clear(): 清空所有配置
    - load_env_file(): 从env.py加载配置(SDK自动)

### 示例用法：

```
from ErisPulse import sdk

env = sdk.env

# 基本操作
env.set('config_key', 'value')
value = env.get('config_key')
value_another = env.config_key  # 通过属性访问
env.config_key = 'value'        # 通过属性赋值

# 事务使用
with env.transaction():
    env.set('key1', 'value1')
    env.set('key2', 'value2')
    
# 快照管理
snapshot_path = env.snapshot()
env.restore('snapshot_name')
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

    def create_env_file_if_not_exists(self):
        env_file = Path("env.py")
        if not env_file.exists():
            content = '''# env.py
# ErisPulse 环境配置文件
# 本文件由 SDK 自动创建，请勿随意删除
# 配置项可通过 sdk.env.get(key, default) 获取，或使用 sdk.env.set(key, value) 设置
# 你也可以像写普通变量一样直接定义配置项，例如：
#
#     MY_CONFIG = "value"
#     MY_CONFIG_2 = {"key": "value"}
#     MY_CONFIG_3 = [1, 2, 3]
#
#     sdk.env.set("MY_CONFIG", "value")
#     sdk.env.set("MY_CONFIG_2", {"key": "value"})
#     sdk.env.set("MY_CONFIG_3", [1, 2, 3])
#
# 这些变量会自动被加载到 SDK 的配置系统中，可通过 sdk.env.MY_CONFIG 或 sdk.env.get("MY_CONFIG") 访问。

from ErisPulse import sdk
'''
            try:
                with open(env_file, "w", encoding="utf-8") as f:
                    f.write(content)
                return True
            except Exception as e:
                from . import sdk
                sdk.logger.error(f"无法创建 env.py 文件: {e}")
                return False
        return False

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