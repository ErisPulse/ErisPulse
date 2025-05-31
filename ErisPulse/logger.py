import logging
import inspect
import datetime

class Logger:
    def __init__(self):
        self._logs = {}
        self._logger = logging.getLogger("ErisPulse")
        self._logger.setLevel(logging.DEBUG)
        self._file_handler = None
        if not self._logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(console_handler)

    def set_level(self, level: str):
        level = level.upper()
        if hasattr(logging, level):
            self._logger.setLevel(getattr(logging, level))

    def set_output_file(self, path: str):
        if self._file_handler:
            self._logger.removeHandler(self._file_handler)
            self._file_handler.close()
        
        try:
            self._file_handler = logging.FileHandler(path, encoding='utf-8')
            self._file_handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(self._file_handler)
            self._logger.info(f"日志输出已设置到文件: {path}")
        except Exception as e:
            self._logger.error(f"无法设置日志文件 {path}: {e}")
            raise e
        
    def save_logs(self, path: str):
        if self._logs == None:
            self._logger.warning("没有log记录可供保存。")
            return
        try:
            with open(path, "w", encoding="utf-8") as file:
                for module, logs in self._logs.items():
                    file.write(f"Module: {module}\n")
                    for log in logs:
                        file.write(f"  {log}\n")
            self._logger.info(f"日志已被保存到：{path}。")
        except Exception as e:
            self._logger.error(f"无法保存日志到 {path}: {e}。")
            raise e

    def _save_in_memory(self, ModuleName, msg):
        if ModuleName not in self._logs:
            self._logs[ModuleName] = []
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"{timestamp} - {msg}"
        self._logs[ModuleName].append(msg)

    def _get_caller(self):
        frame = inspect.currentframe().f_back.f_back
        module = inspect.getmodule(frame)
        module_name = module.__name__
        if module_name == "__main__":
            module_name = "Main"
        if module_name.endswith(".Core"):
            module_name = module_name[:-5]
        return module_name

    def debug(self, msg, *args, **kwargs):
        caller_module = self._get_caller()
        self._save_in_memory(caller_module, msg)
        self._logger.debug(f"[{caller_module}] {msg}", *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        caller_module = self._get_caller()
        self._save_in_memory(caller_module, msg)
        self._logger.info(f"[{caller_module}] {msg}", *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        caller_module = self._get_caller()
        self._save_in_memory(caller_module, msg)
        self._logger.warning(f"[{caller_module}] {msg}", *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        caller_module = self._get_caller()
        self._save_in_memory(caller_module, msg)
        self._logger.error(f"[{caller_module}] {msg}", *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        caller_module = self._get_caller()
        self._save_in_memory(caller_module, msg)
        self._logger.critical(f"[{caller_module}] {msg}", *args, **kwargs)

logger = Logger()
