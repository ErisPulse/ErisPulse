import sys
import traceback

class Error:
    def __init__(self):
        self._types = {}

    def register(self, name, doc="", base=Exception):
        if name not in self._types:
            err_cls = type(name, (base,), {"__doc__": doc})
            self._types[name] = err_cls
        return self._types[name]

    def __getattr__(self, name):
        def raiser(msg, exit=False):
            from .logger import logger
            err_cls = self._types.get(name) or self.register(name)
            exc = err_cls(msg)
            logger.error(f"{name}: {msg} | {err_cls.__doc__}")
            logger.error("".join(traceback.format_stack()))
            if exit:
                raise exc
        return raiser

    def info(self, name: str = None):
        result = {}
        for err_name, err_cls in self._types.items():
            result[err_name] = {
                "type": err_name,
                "doc": getattr(err_cls, "__doc__", ""),
                "class": err_cls,
            }
        if name is None:
            return result
        err_cls = self._types.get(name)
        if not err_cls:
            return None
        return {
            "type": name,
            "doc": getattr(err_cls, "__doc__", ""),
            "class": err_cls,
        }
    
raiserr = Error()
