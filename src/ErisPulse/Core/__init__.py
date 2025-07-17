from .adapter import AdapterFather, SendDSL, adapter
from .env import env
from .logger import logger
from .mods import mods
from .raiserr import raiserr
from .util import util
from .server import adapter_server

__all__ = [
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
        }
    }
    env.setConfig("ErisPulse", defaultConfig)
    _config = defaultConfig