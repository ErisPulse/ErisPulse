"""
ErisPulse 日志系统

提供模块化日志记录功能，支持多级日志、模块过滤和内存存储。

{!--< tips >!--}
1. 支持按模块设置不同日志级别
2. 日志可存储在内存中供后续分析
3. 自动识别调用模块名称
{!--< /tips >!--}
"""

import logging
import inspect
import datetime
from typing import List, Dict, Any, Optional, Union, Type, Set, Tuple, FrozenSet
from rich.logging import RichHandler
from rich.console import Console

class Logger:
    """
    日志管理器
    
    提供模块化日志记录和存储功能
    
    {!--< tips >!--}
    1. 使用set_module_level设置模块日志级别
    2. 使用get_logs获取历史日志
    3. 支持标准日志级别(DEBUG, INFO等)
    {!--< /tips >!--}
    """
    def __init__(self):
        self._max_logs = 1000
        self._logs = {}
        self._module_levels = {}
        self._logger = logging.getLogger("ErisPulse")
        self._logger.setLevel(logging.DEBUG)
        self._file_handler = None
        if not self._logger.handlers:
            console_handler = RichHandler(
                console=Console(),
                show_time=False,
                show_level=True,
                show_path=False,
                markup=False
            )
            self._logger.addHandler(console_handler)
        self._setup_config()
            
    def set_memory_limit(self, limit: int) -> bool:
        """
        设置日志内存存储上限
        
        :param limit: 日志存储上限
        :return: bool 设置是否成功
        """
        if limit > 0:
            self._max_logs = limit
            return True
        else:
            self._logger.warning("日志存储上限必须大于0。")
            return False

    def set_level(self, level: str) -> bool:
        """
        设置全局日志级别
        
        :param level: 日志级别(DEBUG/INFO/WARNING/ERROR/CRITICAL)
        :return: bool 设置是否成功
        """
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
        """
        设置指定模块日志级别

        :param module_name: 模块名称
        :param level: 日志级别(DEBUG/INFO/WARNING/ERROR/CRITICAL)
        :return: bool 设置是否成功
        """
        from .mods import mods
        if not mods.get_module_status(module_name):
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
        """
        设置日志输出

        :param path: 日志文件路径 Str/List
        :return: bool 设置是否成功
        """
        if self._file_handler:
            self._logger.removeHandler(self._file_handler)
            self._file_handler.close()

        if isinstance(path, str):
            path = [path]

        for p in path:
            try:
                file_handler = logging.FileHandler(p, encoding='utf-8')
                # 使用自定义格式化器去除rich markup标签
                file_handler.setFormatter(logging.Formatter("[%(name)s] %(message)s"))
                self._logger.addHandler(file_handler)
                return True
            except Exception as e:
                self._logger.error(f"无法设置日志文件 {p}: {e}")
                return False
            
    def save_logs(self, path) -> bool:
        """
        保存所有在内存中记录的日志
        
        :param path: 日志文件路径 Str/List
        :return: bool 设置是否成功
        """
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
        """
        获取日志内容

        :param module_name (可选): 模块名称
        :return: dict 日志内容
        """
        if module_name:
            return {module_name: self._logs.get(module_name, [])}
        return {k: v.copy() for k, v in self._logs.items()}
    
    def _save_in_memory(self, ModuleName, msg):
        if ModuleName not in self._logs:
            self._logs[ModuleName] = []
        
        # 检查日志数量是否超过限制
        if len(self._logs[ModuleName]) >= self._max_logs:
            self._logs[ModuleName].pop(0)
            
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"{timestamp} - {msg}"
        self._logs[ModuleName].append(msg)

    def _setup_config(self):
        from .config import get_logger_config
        logger_config = get_logger_config()
        if "level" in logger_config:
            self.set_level(logger_config["level"])
        if "log_files" in logger_config and logger_config["log_files"]:
            self.set_output_file(logger_config["log_files"])
        if "memory_limit" in logger_config:
            self.set_memory_limit(logger_config["memory_limit"])
    
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
            raise Exception(msg)

logger = Logger()