import logging
import inspect
import datetime
from typing import List, Dict, Any, Optional, Union, Type, Set, Tuple, FrozenSet

class Logger:
    def __init__(self):
        self._logs = {}
        self._module_levels = {}
        self._logger = logging.getLogger("ErisPulse")
        self._logger.setLevel(logging.DEBUG)
        self._file_handler = None
        if not self._logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(console_handler)

    def set_level(self, level: str) -> bool:
        try:
            level = level.upper()
            if hasattr(logging, level):
                self._logger.setLevel(getattr(logging, level))
                return True
            return False
        except Exception as e:
            self._logger.error(f"无效的日志等级: {level}")
            return False

    def set_module_level(self, module_name: str, level: str) -> bool:
        from .env import env
        if not env.get_module_status(module_name):
            self._logger.warning(f"模块 {module_name} 未启用，无法设置日志等级。")
            return False
        level = level.upper()
        if hasattr(logging, level):
            self._module_levels[module_name] = getattr(logging, level)
            self._logger.info(f"模块 {module_name} 日志等级已设置为 {level}")
            return True
        else:
            self._logger.error(f"无效的日志等级: {level}")
            return False

    def set_output_file(self, path) -> bool:
        if self._file_handler:
            self._logger.removeHandler(self._file_handler)
            self._file_handler.close()

        if isinstance(path, str):
            path = [path]

        for p in path:
            try:
                file_handler = logging.FileHandler(p, encoding='utf-8')
                file_handler.setFormatter(logging.Formatter("%(message)s"))
                self._logger.addHandler(file_handler)
                self._logger.info(f"日志输出已设置到文件: {p}")
                return True
            except Exception as e:
                self._logger.error(f"无法设置日志文件 {p}: {e}")
                return False
    def save_logs(self, path) -> bool:
        if self._logs == None:
            self._logger.warning("没有log记录可供保存。")
            return False
        if isinstance(path, str):
            path = [path]
        
        for p in path:
            try:
                with open(p, "w", encoding="utf-8") as file:
                    for module, logs in self._logs.items():
                        file.write(f"Module: {module}\n")
                        for log in logs:
                            file.write(f"  {log}\n")
                    self._logger.info(f"日志已被保存到：{p}。")
                    return True
            except Exception as e:
                self._logger.error(f"无法保存日志到 {p}: {e}。")
                return False

    def get_logs(self, module_name: str = None) -> dict:
        if module_name:
            return {module_name: self._logs.get(module_name, [])}
        return {k: v.copy() for k, v in self._logs.items()}
    
    def _save_in_memory(self, ModuleName, msg):
        if ModuleName not in self._logs:
            self._logs[ModuleName] = []
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"{timestamp} - {msg}"
        self._logs[ModuleName].append(msg)

    def _get_effective_level(self, module_name):
        return self._module_levels.get(module_name, self._logger.level)

    def _get_caller(self):
        frame = inspect.currentframe().f_back.f_back
        module = inspect.getmodule(frame)
        module_name = module.__name__
        if module_name == "__main__":
            module_name = "Main"
        if module_name.endswith(".Core"):
            module_name = module_name[:-5]
        if module_name.startswith("ErisPulse"):
            module_name = "ErisPulse"
        return module_name

    def debug(self, msg, *args, **kwargs):
        caller_module = self._get_caller()
        if self._get_effective_level(caller_module) <= logging.DEBUG:
            self._save_in_memory(caller_module, msg)
            self._logger.debug(f"[{caller_module}] {msg}", *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        caller_module = self._get_caller()
        if self._get_effective_level(caller_module) <= logging.INFO:
            self._save_in_memory(caller_module, msg)
            self._logger.info(f"[{caller_module}] {msg}", *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        caller_module = self._get_caller()
        if self._get_effective_level(caller_module) <= logging.WARNING:
            self._save_in_memory(caller_module, msg)
            self._logger.warning(f"[{caller_module}] {msg}", *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        caller_module = self._get_caller()
        if self._get_effective_level(caller_module) <= logging.ERROR:
            self._save_in_memory(caller_module, msg)
            self._logger.error(f"[{caller_module}] {msg}", *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        caller_module = self._get_caller()
        if self._get_effective_level(caller_module) <= logging.CRITICAL:
            self._save_in_memory(caller_module, msg)
            self._logger.critical(f"[{caller_module}] {msg}", *args, **kwargs)
            from .raiserr import raiserr
            raiserr.register("CriticalError", doc="发生致命错误")
            raiserr.CriticalError(f"程序发生致命错误：{msg}", exit=True)

logger = Logger()