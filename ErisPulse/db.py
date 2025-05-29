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
            cls._instance.dev_mode = kwargs.get('dev_mode', False)
        return cls._instance

    def __init__(self, dev_mode=False):
        if not hasattr(self, "_initialized"):
            self.dev_mode = dev_mode
            self._init_db()
    
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
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS modules (
            module_name TEXT PRIMARY KEY,
            status INTEGER NOT NULL,
            version TEXT,
            description TEXT,
            author TEXT,
            dependencies TEXT,
            optional_dependencies TEXT,
            pip_dependencies TEXT
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
    def set_module_status(self, module_name, status):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE modules SET status = ? WHERE module_name = ?
            """, (int(status), module_name))
            conn.commit()
    
    def get_module_status(self, module_name):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT status FROM modules WHERE module_name = ?
            """, (module_name,))
            result = cursor.fetchone()
            return bool(result[0]) if result else True

    def set_all_modules(self, modules_info):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for module_name, module_info in modules_info.items():
                meta = module_info.get('info', {}).get('meta', {})
                dependencies = module_info.get('info', {}).get('dependencies', {})
                cursor.execute("""
                INSERT OR REPLACE INTO modules (
                    module_name, status, version, description, author, 
                    dependencies, optional_dependencies, pip_dependencies
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    module_name,
                    int(module_info.get('status', True)),
                    meta.get('version', ''),
                    meta.get('description', ''),
                    meta.get('author', ''),
                    json.dumps(dependencies.get('requires', [])),
                    json.dumps(dependencies.get('optional', [])),
                    json.dumps(dependencies.get('pip', []))
                ))
            conn.commit()

    def get_all_modules(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM modules")
            rows = cursor.fetchall()
            modules_info = {}
            for row in rows:
                module_name, status, version, description, author, dependencies, optional_dependencies, pip_dependencies = row
                modules_info[module_name] = {
                    'status': bool(status),
                    'info': {
                        'meta': {
                            'version': version,
                            'description': description,
                            'author': author,
                            'pip_dependencies': json.loads(pip_dependencies) if pip_dependencies else []
                        },
                        'dependencies': {
                            'requires': json.loads(dependencies) if dependencies else [],
                            'optional': json.loads(optional_dependencies) if optional_dependencies else [],
                            'pip': json.loads(pip_dependencies) if pip_dependencies else []
                        }
                    }
                }
            return modules_info

    def set_module(self, module_name, module_info):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            meta = module_info.get('info', {}).get('meta', {})
            dependencies = module_info.get('info', {}).get('dependencies', {})
            cursor.execute("""
            INSERT OR REPLACE INTO modules (
                module_name, status, version, description, author, 
                dependencies, optional_dependencies, pip_dependencies
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                module_name,
                int(module_info.get('status', True)),
                meta.get('version', ''),
                meta.get('description', ''),
                meta.get('author', ''),
                json.dumps(dependencies.get('requires', [])),
                json.dumps(dependencies.get('optional', [])),
                json.dumps(dependencies.get('pip', []))
            ))
            conn.commit()

    def get_module(self, module_name):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM modules WHERE module_name = ?", (module_name,))
            row = cursor.fetchone()
            if row:
                module_name, status, version, description, author, dependencies, optional_dependencies, pip_dependencies = row
                return {
                    'status': bool(status),
                    'info': {
                        'meta': {
                            'version': version,
                            'description': description,
                            'author': author,
                            'pip_dependencies': json.loads(pip_dependencies) if pip_dependencies else []
                        },
                        'dependencies': {
                            'requires': json.loads(dependencies) if dependencies else [],
                            'optional': json.loads(optional_dependencies) if optional_dependencies else [],
                            'pip': json.loads(pip_dependencies) if pip_dependencies else []
                        }
                    }
                }
            return None

    def update_module(self, module_name, module_info):
        self.set_module(module_name, module_info)

    def remove_module(self, module_name):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM modules WHERE module_name = ?", (module_name,))
            conn.commit()
            return cursor.rowcount > 0
    
    def __getattr__(self, key):
        try:
            return self.get(key)
        except KeyError:
            raise AttributeError(f"配置项 {key} 不存在")

env = EnvManager()
