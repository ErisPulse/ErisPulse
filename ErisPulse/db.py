import os
import json
import sqlite3
import importlib.util
from pathlib import Path

class EnvManager:
    _instance = None
    db_path = os.path.join(os.path.dirname(__file__), "config.db")

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._init_db()
            self._create_env_file_if_not_exists()
            self._initialized = True

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """)
        conn.commit()
        conn.close()

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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, serialized_value))
        conn.commit()
        conn.close()

    def delete(self, key):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM config WHERE key = ?", (key,))
        conn.commit()
        conn.close()

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

    def _create_env_file_if_not_exists(self):
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
                self.logger.info("已自动生成 env.py 文件")
            except Exception as e:
                self.logger.error(f"无法创建 env.py 文件: {e}")

    def __getattr__(self, key):
        try:
            return self.get(key)
        except KeyError:
            from . import sdk
            sdk.logger.error(f"配置项 {key} 不存在")

env = EnvManager()
