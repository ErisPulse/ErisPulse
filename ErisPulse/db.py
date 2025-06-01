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
                raise
    
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
    
    def __getattr__(self, key):
        try:
            return self.get(key)
        except KeyError:
            raise AttributeError(f"配置项 {key} 不存在")

env = EnvManager()
