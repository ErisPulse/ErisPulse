from .adapter import AdapterFather, SendDSL, adapter
from .env import env
from .logger import logger
from .mods import mods
from .raiserr import raiserr
from .util import util
from .server import adapter_server
BaseAdapter = AdapterFather

__all__ = [
    'BaseAdapter',
    'AdapterFather',
    'SendDSL',
    'adapter',
    'env',
    'logger',
    'mods',
    'raiserr',
    'util',
    'adapter_server'
]

_config = env.getConfig("ErisPulse")

if _config is None:
    defaultConfig = {
        "server": {
            "host": "0.0.0.0",
            "port": 8000,
            "ssl_certfile": None,
            "ssl_keyfile": None
        },
        "logger": {
            "level": "INFO",
            "log_files": [],
            "memory_limit": 1000
        }
    }
    env.setConfig("ErisPulse", defaultConfig)
    _config = defaultConfig

if _config.get("server") is None:
    _config["server"] = {
        "host": "0.0.0.0",
        "port": 8000,
        "ssl_certfile": None,
        "ssl_keyfile": None
    }
    env.setConfig("ErisPulse", _config)
    
if _config.get("logger") is None:
    _config["logger"] = {
        "level": "INFO",
        "log_files": [],
        "memory_limit": 1000
    }
    env.setConfig("ErisPulse", _config)

if "logger" in _config:
    logger_config = _config["logger"]
    if "level" in logger_config:
        logger.set_level(logger_config["level"])
    if "log_files" in logger_config and logger_config["log_files"]:
        logger.set_output_file(logger_config["log_files"])