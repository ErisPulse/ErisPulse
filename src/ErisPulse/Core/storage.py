"""
ErisPulse 存储管理模块

提供键值存储、事务支持、快照和恢复功能，用于管理框架运行时数据。
基于SQLite实现持久化存储，支持复杂数据类型和原子操作。

支持两种数据库模式：
1. 项目数据库（默认）：位于项目目录下的 config/config.db
2. 全局数据库：位于包内的 ../data/config.db

用户可通过在 config.toml 中配置以下选项来选择使用全局数据库：
```toml
[ErisPulse.storage]
use_global_db = true
```

{!--< tips >!--}
1. 支持JSON序列化存储复杂数据类型
2. 提供事务支持确保数据一致性
3. 自动快照功能防止数据丢失
{!--< /tips >!--}
"""

import os
import json
import sqlite3
import shutil
import time
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple, Type

class StorageManager:
    """
    存储管理器
    
    单例模式实现，提供键值存储的增删改查、事务和快照管理
    
    支持两种数据库模式：
    1. 项目数据库（默认）：位于项目目录下的 config/config.db
    2. 全局数据库：位于包内的 ../data/config.db
    
    用户可通过在 config.toml 中配置以下选项来选择使用全局数据库：
    ```toml
    [ErisPulse.storage]
    use_global_db = true
    ```

    {!--< tips >!--}
    1. 使用get/set方法操作存储项
    2. 使用transaction上下文管理事务
    3. 使用snapshot/restore管理数据快照
    {!--< /tips >!--}
    """
    
    _instance = None
    # 默认数据库放在项目下的 config/config.db
    DEFAULT_PROJECT_DB_PATH = os.path.join(os.getcwd(), "config", "config.db")
    # 包内全局数据库路径
    GLOBAL_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/config.db"))
    SNAPSHOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/snapshots"))

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 避免重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        # 确保目录存在
        self._ensure_directories()
        
        # 根据配置决定使用哪个数据库
        from .config import config
        use_global_db = config.getConfig("ErisPulse.storage.use_global_db", False)
        
        if use_global_db and os.path.exists(self.GLOBAL_DB_PATH):
            self.db_path = self.GLOBAL_DB_PATH
        else:
            self.db_path = self.DEFAULT_PROJECT_DB_PATH
            
        self._last_snapshot_time = time.time()
        self._snapshot_interval = 3600
        
        self._init_db()
        self._initialized = True
    
    def _ensure_directories(self) -> None:
        """
        确保必要的目录存在
        """
        # 确保项目数据库目录存在
        try:
            os.makedirs(os.path.dirname(self.DEFAULT_PROJECT_DB_PATH), exist_ok=True)
        except Exception:
            pass  # 如果无法创建项目目录，则跳过
            
        # 确保快照目录存在
        try:
            os.makedirs(self.SNAPSHOT_DIR, exist_ok=True)
        except Exception:
            pass  # 如果无法创建快照目录，则跳过

    def _init_db(self) -> None:
        """
        {!--< internal-use >!--}
        初始化数据库
        """
        from .logger import logger

        logger.debug(f"初始化数据库: {self.db_path}")
        logger.debug(f"创建数据库目录: {os.path.dirname(self.db_path)}")
        
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        except Exception:
            pass  # 如果无法创建目录，则继续尝试连接数据库
            
        try:
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
        except sqlite3.OperationalError as e:
            logger.error(f"无法创建或打开数据库文件: {e}")
            raise
        except Exception as e:
            logger.error(f"初始化数据库时发生未知错误: {e}")
            raise
        
        # 初始化自动快照调度器
        self._last_snapshot_time = time.time()  # 初始化为当前时间
        self._snapshot_interval = 3600  # 默认每小时自动快照

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取存储项的值
        
        :param key: 存储项键名
        :param default: 默认值(当键不存在时返回)
        :return: 存储项的值
        
        :example:
        >>> timeout = storage.get("network.timeout", 30)
        >>> user_settings = storage.get("user.settings", {})
        """
        # 避免在初始化过程中调用此方法导致问题
        if not hasattr(self, '_initialized') or not self._initialized:
            return default
            
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
                from .logger import logger
                logger.error(f"数据库操作错误: {e}")
                return default
        except Exception as e:
            from .logger import logger
            logger.error(f"获取存储项 {key} 时发生错误: {e}")
            return default
                
    def get_all_keys(self) -> List[str]:
        """
        获取所有存储项的键名
        
        :return: 键名列表
        
        :example:
        >>> all_keys = storage.get_all_keys()
        >>> print(f"共有 {len(all_keys)} 个存储项")
        """
        # 避免在初始化过程中调用此方法导致问题
        if not hasattr(self, '_initialized') or not self._initialized:
            return []
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key FROM config")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            from .logger import logger
            logger.error(f"获取所有键名时发生错误: {e}")
            return []

    def set(self, key: str, value: Any) -> bool:
        """
        设置存储项的值
        
        :param key: 存储项键名
        :param value: 存储项的值
        :return: 操作是否成功
        
        :example:
        >>> storage.set("app.name", "MyApp")
        >>> storage.set("user.settings", {"theme": "dark"})
        """
        # 避免在初始化过程中调用此方法导致问题
        if not hasattr(self, '_initialized') or not self._initialized:
            return False
            
        try:
            serialized_value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            with self.transaction():
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, serialized_value))
                conn.commit()
                conn.close()
            
            self._check_auto_snapshot()
            return True
        except Exception as e:
            from .logger import logger
            logger.error(f"设置存储项 {key} 失败: {e}")
            return False

    def set_multi(self, items: Dict[str, Any]) -> bool:
        """
        批量设置多个存储项
        
        :param items: 键值对字典
        :return: 操作是否成功
        
        :example:
        >>> storage.set_multi({
        >>>     "app.name": "MyApp",
        >>>     "app.version": "1.0.0",
        >>>     "app.debug": True
        >>> })
        """
        # 避免在初始化过程中调用此方法导致问题
        if not hasattr(self, '_initialized') or not self._initialized:
            return False
            
        try:
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
        except Exception:
            return False
            
    def getConfig(self, key: str, default: Any = None) -> Any:
        """
        获取模块/适配器配置项（委托给config模块）
        :param key: 配置项的键(支持点分隔符如"module.sub.key")
        :param default: 默认值
        :return: 配置项的值
        """
        try:
            from .config import config
            return config.getConfig(key, default)
        except Exception:
            return default
    
    def setConfig(self, key: str, value: Any) -> bool:
        """
        设置模块/适配器配置（委托给config模块）
        :param key: 配置项键名(支持点分隔符如"module.sub.key")
        :param value: 配置项值
        :return: 操作是否成功
        """
        try:
            from .config import config
            return config.setConfig(key, value)
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """
        删除存储项
        
        :param key: 存储项键名
        :return: 操作是否成功
        
        :example:
        >>> storage.delete("temp.session")
        """
        # 避免在初始化过程中调用此方法导致问题
        if not hasattr(self, '_initialized') or not self._initialized:
            return False
            
        try:
            with self.transaction():
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM config WHERE key = ?", (key,))
                conn.commit()
                conn.close()
            
            self._check_auto_snapshot()
            return True
        except Exception:
            return False
            
    def delete_multi(self, keys: List[str]) -> bool:
        """
        批量删除多个存储项
        
        :param keys: 键名列表
        :return: 操作是否成功
        
        :example:
        >>> storage.delete_multi(["temp.key1", "temp.key2"])
        """
        # 避免在初始化过程中调用此方法导致问题
        if not hasattr(self, '_initialized') or not self._initialized:
            return False
            
        try:
            with self.transaction():
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.executemany("DELETE FROM config WHERE key = ?", [(k,) for k in keys])
                conn.commit()
                conn.close()
            
            self._check_auto_snapshot()
            return True
        except Exception:
            return False
            
    def get_multi(self, keys: List[str]) -> Dict[str, Any]:
        """
        批量获取多个存储项的值
        
        :param keys: 键名列表
        :return: 键值对字典
        
        :example:
        >>> settings = storage.get_multi(["app.name", "app.version"])
        """
        # 避免在初始化过程中调用此方法导致问题
        if not hasattr(self, '_initialized') or not self._initialized:
            return {}
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            placeholders = ','.join(['?'] * len(keys))
            cursor.execute(f"SELECT key, value FROM config WHERE key IN ({placeholders})", keys)
            results = {row[0]: json.loads(row[1]) if row[1].startswith(('{', '[')) else row[1] 
                        for row in cursor.fetchall()}
            conn.close()
            return results
        except Exception as e:
            from .logger import logger
            logger.error(f"批量获取存储项失败: {e}")
            return {}

    def transaction(self) -> 'StorageManager._Transaction':
        """
        创建事务上下文
        
        :return: 事务上下文管理器
        
        :example:
        >>> with storage.transaction():
        >>>     storage.set("key1", "value1")
        >>>     storage.set("key2", "value2")
        """
        # 避免在初始化过程中调用此方法导致问题
        if not hasattr(self, '_initialized') or not self._initialized:
            # 返回一个空的事务对象
            class EmptyTransaction:
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
            return EmptyTransaction()
            
        return self._Transaction(self)

    class _Transaction:
        """
        事务上下文管理器
        
        {!--< internal-use >!--}
        确保多个操作的原子性
        """
        
        def __init__(self, storage_manager: 'StorageManager'):
            self.storage_manager = storage_manager
            self.conn = None
            self.cursor = None

        def __enter__(self) -> 'StorageManager._Transaction':
            """
            进入事务上下文
            """
            self.conn = sqlite3.connect(self.storage_manager.db_path)
            self.cursor = self.conn.cursor()
            self.cursor.execute("BEGIN TRANSACTION")
            return self

        def __exit__(self, exc_type: Type[Exception], exc_val: Exception, exc_tb: Any) -> None:
            """
            退出事务上下文
            """
            if self.conn is not None:
                try:
                    if exc_type is None:
                        if hasattr(self.conn, 'commit'):
                            self.conn.commit()
                    else:
                        if hasattr(self.conn, 'rollback'):
                            self.conn.rollback()
                        from .logger import logger
                        logger.error(f"事务执行失败: {exc_val}")
                finally:
                    if hasattr(self.conn, 'close'):
                        self.conn.close()

    def _check_auto_snapshot(self) -> None:
        """
        {!--< internal-use >!--}
        检查并执行自动快照
        """
        # 避免在初始化过程中调用此方法导致问题
        if not hasattr(self, '_initialized') or not self._initialized:
            return
            
        from .logger import logger
        
        if not hasattr(self, '_last_snapshot_time') or self._last_snapshot_time is None:
            self._last_snapshot_time = time.time()
            
        if not hasattr(self, '_snapshot_interval') or self._snapshot_interval is None:
            self._snapshot_interval = 3600
            
        current_time = time.time()
        
        try:
            time_diff = current_time - self._last_snapshot_time
            if not isinstance(time_diff, (int, float)):
                raise ValueError("时间差应为数值类型")

            if not isinstance(self._snapshot_interval, (int, float)):
                raise ValueError("快照间隔应为数值类型")
                
            if time_diff > self._snapshot_interval:
                self._last_snapshot_time = current_time
                self.snapshot(f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                
        except Exception as e:
            logger.error(f"自动快照检查失败: {e}")
            self._last_snapshot_time = current_time
            self._snapshot_interval = 3600

    def set_snapshot_interval(self, seconds: int) -> None:
        """
        设置自动快照间隔
        
        :param seconds: 间隔秒数
        
        :example:
        >>> # 每30分钟自动快照
        >>> storage.set_snapshot_interval(1800)
        """
        # 避免在初始化过程中调用此方法导致问题
        if not hasattr(self, '_initialized') or not self._initialized:
            return
            
        self._snapshot_interval = seconds

    def clear(self) -> bool:
        """
        清空所有存储项
        
        :return: 操作是否成功
        
        :example:
        >>> storage.clear()  # 清空所有存储
        """
        # 避免在初始化过程中调用此方法导致问题
        if not hasattr(self, '_initialized') or not self._initialized:
            return False
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM config")
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
        
    def __getattr__(self, key: str) -> Any:
        """
        通过属性访问存储项
        
        :param key: 存储项键名
        :return: 存储项的值
        
        :raises AttributeError: 当存储项不存在时抛出
            
        :example:
        >>> app_name = storage.app_name
        """
        # 避免访问内置属性时出现问题
        if key.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")
            
        # 避免在初始化过程中调用此方法导致问题
        if not hasattr(self, '_initialized') or not self._initialized:
            raise AttributeError(f"存储尚未初始化完成: {key}")
            
        try:
            return self.get(key)
        except Exception:
            raise AttributeError(f"存储项 {key} 不存在或访问出错")

    def __setattr__(self, key: str, value: Any) -> None:
        """
        通过属性设置存储项
        
        :param key: 存储项键名
        :param value: 存储项的值
            
        :example:
        >>> storage.app_name = "MyApp"
        """
        # 避免在初始化过程中出现问题
        if key.startswith('_'):
            super().__setattr__(key, value)
            return
            
        # 如果还未初始化完成，直接设置属性
        if not hasattr(self, '_initialized') or not self._initialized:
            super().__setattr__(key, value)
            return
            
        try:
            self.set(key, value)
        except Exception as e:
            from .logger import logger
            logger.error(f"设置存储项 {key} 失败: {e}")

    def snapshot(self, name: Optional[str] = None) -> str:
        """
        创建数据库快照
        
        :param name: 快照名称(可选)
        :return: 快照文件路径
        
        :example:
        >>> # 创建命名快照
        >>> snapshot_path = storage.snapshot("before_update")
        >>> # 创建时间戳快照
        >>> snapshot_path = storage.snapshot()
        """
        # 避免在初始化过程中调用此方法导致问题
        if not hasattr(self, '_initialized') or not self._initialized:
            raise RuntimeError("存储尚未初始化完成")
            
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

    def restore(self, snapshot_name: str) -> bool:
        """
        从快照恢复数据库
        
        :param snapshot_name: 快照名称或路径
        :return: 恢复是否成功
        
        :example:
        >>> storage.restore("before_update")
        """
        # 避免在初始化过程中调用此方法导致问题
        if not hasattr(self, '_initialized') or not self._initialized:
            return False
            
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

    def list_snapshots(self) -> List[Tuple[str, datetime, int]]:
        """
        列出所有可用的快照
        
        :return: 快照信息列表(名称, 创建时间, 大小)
        
        :example:
        >>> for name, date, size in storage.list_snapshots():
        >>>     print(f"{name} - {date} ({size} bytes)")
        """
        # 避免在初始化过程中调用此方法导致问题
        if not hasattr(self, '_initialized') or not self._initialized:
            return []
            
        try:
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
        except Exception as e:
            from .logger import logger
            logger.error(f"列出快照时发生错误: {e}")
            return []

    def delete_snapshot(self, snapshot_name: str) -> bool:
        """
        删除指定的快照
        
        :param snapshot_name: 快照名称
        :return: 删除是否成功
        
        :example:
        >>> storage.delete_snapshot("old_backup")
        """
        # 避免在初始化过程中调用此方法导致问题
        if not hasattr(self, '_initialized') or not self._initialized:
            return False
            
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

storage = StorageManager()

__all__ = [
    "storage"
]

