"""
ErisPulse 存储管理模块

提供键值存储和事务支持，用于管理框架运行时数据。
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
{!--< /tips >!--}
"""

import os
import json
import sqlite3
import threading
from typing import List, Dict, Optional, Any, Type
from contextlib import contextmanager

class StorageManager:
    """
    存储管理器
    
    单例模式实现，提供键值存储的增删改查和事务管理
    
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
    {!--< /tips >!--}
    """
    
    _instance = None
    # 默认数据库放在项目下的 config/config.db
    DEFAULT_PROJECT_DB_PATH = os.path.join(os.getcwd(), "config", "config.db")
    # 包内全局数据库路径
    GLOBAL_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/config.db"))
    # 线程本地存储，用于跟踪活动事务的连接
    _local = threading.local()

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
        from ._self_config import get_storage_config
        storage_config = get_storage_config()

        use_global_db = storage_config.get("use_global_db", False)
        
        if use_global_db and os.path.exists(self.GLOBAL_DB_PATH):
            self.db_path = self.GLOBAL_DB_PATH
        else:
            self.db_path = self.DEFAULT_PROJECT_DB_PATH
            
        self._init_db()
        self._initialized = True
    
    @contextmanager
    def _get_connection(self):
        """
        获取数据库连接（支持事务）
        
        如果在事务中，返回事务的连接
        否则创建新连接
        """
        # 检查是否在线程本地存储中有活动事务连接
        if hasattr(self._local, 'transaction_conn') and self._local.transaction_conn is not None:
            conn = self._local.transaction_conn
            should_close = False
        else:
            conn = sqlite3.connect(self.db_path)
            should_close = True
        
        try:
            yield conn
        finally:
            if should_close:
                conn.close()
    
    def _ensure_directories(self) -> None:
        """
        确保必要的目录存在
        """
        # 确保项目数据库目录存在
        try:
            os.makedirs(os.path.dirname(self.DEFAULT_PROJECT_DB_PATH), exist_ok=True)
        except Exception:
            pass  # 如果无法创建项目目录，则跳过

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
            serialized_value = json.dumps(value)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, serialized_value))
                # 如果不在事务中，提交更改
                if not (hasattr(self._local, 'transaction_conn') and self._local.transaction_conn is not None):
                    conn.commit()
            
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
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for key, value in items.items():
                    serialized_value = json.dumps(value)
                    cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", 
                        (key, serialized_value))
                # 如果不在事务中，提交更改
                if not (hasattr(self._local, 'transaction_conn') and self._local.transaction_conn is not None):
                    conn.commit()
            
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
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM config WHERE key = ?", (key,))
                # 如果不在事务中，提交更改
                if not (hasattr(self._local, 'transaction_conn') and self._local.transaction_conn is not None):
                    conn.commit()
            
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
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany("DELETE FROM config WHERE key = ?", [(k,) for k in keys])
                # 如果不在事务中，提交更改
                if not (hasattr(self._local, 'transaction_conn') and self._local.transaction_conn is not None):
                    conn.commit()
            
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
            results = {}
            for row in cursor.fetchall():
                try:
                    results[row[0]] = json.loads(row[1])
                except json.JSONDecodeError:
                    results[row[0]] = row[1]
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
        
        # 如果已经在事务中（嵌套事务），返回一个空事务，复用现有连接
        if hasattr(self._local, 'transaction_conn') and self._local.transaction_conn is not None:
            class NestedTransaction:
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
            return NestedTransaction()
            
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
            # 将连接存储到线程本地存储，供其他方法复用
            self.storage_manager._local.transaction_conn = self.conn
            return self

        def __exit__(self, exc_type: Type[Exception], exc_val: Exception, exc_tb: Any) -> None:
            """
            退出事务上下文
            """
            # 清除线程本地存储中的连接引用
            if hasattr(self.storage_manager._local, 'transaction_conn'):
                self.storage_manager._local.transaction_conn = None
                
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
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM config")
                # 如果不在事务中，提交更改
                if not (hasattr(self._local, 'transaction_conn') and self._local.transaction_conn is not None):
                    conn.commit()
            
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
        
        # 检查键是否存在
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
                result = cursor.fetchone()
        except Exception:
            raise AttributeError(f"存储项 {key} 不存在或访问出错")
        
        if result is None:
            raise AttributeError(f"存储项 {key} 不存在")
        
        # 解析并返回值
        try:
            return json.loads(result[0])
        except json.JSONDecodeError:
            return result[0]

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

storage = StorageManager()

__all__ = [
    "storage"
]
