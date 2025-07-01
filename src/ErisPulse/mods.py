"""
# 模块管理系统

提供模块的注册、状态管理和依赖解析功能。支持模块信息存储、状态切换和批量操作。

## API 文档

### 模块状态管理
#### set_module_status(module_name: str, status: bool) -> None
设置模块的启用状态。
- 参数:
  - module_name: 模块名称
  - status: 模块状态，True为启用，False为禁用
- 返回:
  - None
- 示例:
```python
# 启用模块
sdk.mods.set_module_status("MyModule", True)

# 禁用模块
sdk.mods.set_module_status("MyModule", False)

# 条件性启用模块
if check_dependencies():
    sdk.mods.set_module_status("MyModule", True)
else:
    sdk.logger.warning("依赖检查失败，模块未启用")
```

#### get_module_status(module_name: str) -> bool
获取模块的启用状态。
- 参数:
  - module_name: 模块名称
- 返回:
  - bool: 模块状态，True为启用，False为禁用
- 示例:
```python
# 检查模块是否启用
if sdk.mods.get_module_status("MyModule"):
    print("模块已启用")
else:
    print("模块已禁用")
    
# 在条件中使用
if sdk.mods.get_module_status("DatabaseModule") and sdk.mods.get_module_status("NetworkModule"):
    start_application()
```

### 模块信息管理
#### set_module(module_name: str, module_info: dict) -> None
设置模块信息。
- 参数:
  - module_name: 模块名称
  - module_info: 模块信息字典，包含模块的元数据和配置
- 返回:
  - None
- 示例:
```python
# 设置基本模块信息
sdk.mods.set_module("MyModule", {
    "status": True,
    "info": {
        "meta": {
            "name": "MyModule",
            "version": "1.0.0",
            "description": "示例模块",
            "author": "开发者"
        },
        "dependencies": {
            "requires": ["CoreModule"],
            "optional": ["OptionalModule"],
            "pip": ["requests", "numpy"]
        }
    }
})

# 更新现有模块信息
module_info = sdk.mods.get_module("MyModule")
module_info["info"]["meta"]["version"] = "1.1.0"
sdk.mods.set_module("MyModule", module_info)
```

#### get_module(module_name: str) -> dict | None
获取模块信息。
- 参数:
  - module_name: 模块名称
- 返回:
  - dict: 模块信息字典
  - None: 如果模块不存在
- 示例:
```python
# 获取模块信息
module_info = sdk.mods.get_module("MyModule")
if module_info:
    print(f"模块版本: {module_info['info']['meta']['version']}")
    print(f"模块描述: {module_info['info']['meta']['description']}")
    print(f"模块状态: {'启用' if module_info['status'] else '禁用'}")
else:
    print("模块不存在")
```

#### get_all_modules() -> dict
获取所有模块信息。
- 参数: 无
- 返回:
  - dict: 包含所有模块信息的字典，键为模块名，值为模块信息
- 示例:
```python
# 获取所有模块
all_modules = sdk.mods.get_all_modules()

# 统计启用和禁用的模块
enabled_count = 0
disabled_count = 0
for name, info in all_modules.items():
    if info.get("status", False):
        enabled_count += 1
    else:
        disabled_count += 1
        
print(f"已启用模块: {enabled_count}")
print(f"已禁用模块: {disabled_count}")

# 查找特定类型的模块
adapters = [name for name, info in all_modules.items() 
           if "adapter" in info.get("info", {}).get("meta", {}).get("tags", [])]
print(f"适配器模块: {adapters}")
```

#### update_module(module_name: str, module_info: dict) -> None
更新模块信息。
- 参数:
  - module_name: 模块名称
  - module_info: 更新后的模块信息字典
- 返回:
  - None
- 示例:
```python
# 更新模块版本
module_info = sdk.mods.get_module("MyModule")
module_info["info"]["meta"]["version"] = "1.2.0"
sdk.mods.update_module("MyModule", module_info)

# 添加新的配置项
module_info = sdk.mods.get_module("MyModule")
if "config" not in module_info:
    module_info["config"] = {}
module_info["config"]["debug_mode"] = True
sdk.mods.update_module("MyModule", module_info)
```

#### remove_module(module_name: str) -> bool
删除模块。
- 参数:
  - module_name: 模块名称
- 返回:
  - bool: 是否成功删除
- 示例:
```python
# 删除模块
if sdk.mods.remove_module("OldModule"):
    print("模块已成功删除")
else:
    print("模块不存在或删除失败")
    
# 条件删除
if sdk.mods.get_module_status("TestModule") and is_test_environment():
    sdk.mods.remove_module("TestModule")
    print("测试模块已在生产环境中移除")
```

#### set_all_modules(modules_info: Dict[str, dict]) -> None
批量设置多个模块信息。
- 参数:
  - modules_info: 模块信息字典的字典，键为模块名，值为模块信息
- 返回:
  - None
- 示例:
```python
# 批量设置模块
sdk.mods.set_all_modules({
    "Module1": {
        "status": True,
        "info": {"meta": {"name": "Module1", "version": "1.0.0"}}
    },
    "Module2": {
        "status": True,
        "info": {"meta": {"name": "Module2", "version": "1.0.0"}}
    }
})

# 从配置文件加载模块信息
import json
with open("modules_config.json", "r") as f:
    modules_config = json.load(f)
sdk.mods.set_all_modules(modules_config)
```

### 前缀管理
#### update_prefixes(module_prefix: str = None, status_prefix: str = None) -> None
更新存储前缀。
- 参数:
  - module_prefix: 模块存储前缀
  - status_prefix: 状态存储前缀
- 返回:
  - None
- 示例:
```python
# 更新模块前缀
sdk.mods.update_prefixes(module_prefix="custom.module.")

# 更新状态前缀
sdk.mods.update_prefixes(status_prefix="custom.status.")

# 同时更新两个前缀
sdk.mods.update_prefixes(
    module_prefix="app.modules.",
    status_prefix="app.status."
)
```

#### module_prefix 属性
获取当前模块存储前缀。
- 返回:
  - str: 当前模块存储前缀
- 示例:
```python
# 获取当前模块前缀
prefix = sdk.mods.module_prefix
print(f"当前模块前缀: {prefix}")

# 在自定义存储操作中使用
custom_key = f"{sdk.mods.module_prefix}custom.{module_name}"
sdk.env.set(custom_key, custom_data)
```

#### status_prefix 属性
获取当前状态存储前缀。
- 返回:
  - str: 当前状态存储前缀
- 示例:
```python
# 获取当前状态前缀
prefix = sdk.mods.status_prefix
print(f"当前状态前缀: {prefix}")

# 在自定义状态操作中使用
custom_status_key = f"{sdk.mods.status_prefix}custom.{module_name}"
sdk.env.set(custom_status_key, is_active)
```

"""

import json
from typing import Dict, Optional

class ModuleManager:
    DEFAULT_MODULE_PREFIX = "erispulse.module.data:"
    DEFAULT_STATUS_PREFIX = "erispulse.module.status:"

    def __init__(self):
        from .db import env
        self.env = env
        self._ensure_prefixes()

    def _ensure_prefixes(self):
        if not self.env.get("erispulse.system.module_prefix"):
            self.env.set("erispulse.system.module_prefix", self.DEFAULT_MODULE_PREFIX)
        if not self.env.get("erispulse.system.status_prefix"):
            self.env.set("erispulse.system.status_prefix", self.DEFAULT_STATUS_PREFIX)

    @property
    def module_prefix(self) -> str:
        return self.env.get("erispulse.system.module_prefix")

    @property
    def status_prefix(self) -> str:
        return self.env.get("erispulse.system.status_prefix")

    def set_module_status(self, module_name: str, status: bool) -> None:
        self.env.set(f"{self.status_prefix}{module_name}", bool(status))

        module_info = self.get_module(module_name)
        if module_info:
            module_info["status"] = bool(status)
            self.env.set(f"{self.module_prefix}{module_name}", module_info)

    def get_module_status(self, module_name: str) -> bool:
        status = self.env.get(f"{self.status_prefix}{module_name}", True)
        if isinstance(status, str):
            return status.lower() == 'true'
        return bool(status)

    def set_module(self, module_name: str, module_info: dict) -> None:
        self.env.set(f"{self.module_prefix}{module_name}", module_info)
        self.set_module_status(module_name, module_info.get('status', True))

    def get_module(self, module_name: str) -> Optional[dict]:
        return self.env.get(f"{self.module_prefix}{module_name}")

    def set_all_modules(self, modules_info: Dict[str, dict]) -> None:
        for module_name, module_info in modules_info.items():
            self.set_module(module_name, module_info)

    def get_all_modules(self) -> dict:
        modules_info = {}
        all_keys = self.env.get_all_keys()
        prefix_len = len(self.module_prefix)

        for key in all_keys:
            if key.startswith(self.module_prefix):
                module_name = key[prefix_len:]
                module_info = self.get_module(module_name)
                if module_info:
                    status = self.get_module_status(module_name)
                    module_info['status'] = bool(status)
                    modules_info[module_name] = module_info
        return modules_info

    def update_module(self, module_name: str, module_info: dict) -> None:
        self.set_module(module_name, module_info)

    def remove_module(self, module_name: str) -> bool:
        module_key = f"{self.module_prefix}{module_name}"
        status_key = f"{self.status_prefix}{module_name}"

        if self.env.get(module_key) is not None:
            self.env.delete(module_key)
            self.env.delete(status_key)
            return True
        return False

    def update_prefixes(self, module_prefix: str = None, status_prefix: str = None) -> None:
        if module_prefix:
            if not module_prefix.endswith(':'):
                module_prefix += ':'
            self.env.set("erispulse.system.module_prefix", module_prefix)

        if status_prefix:
            if not status_prefix.endswith(':'):
                status_prefix += ':'
            self.env.set("erispulse.system.status_prefix", status_prefix)

mods = ModuleManager()