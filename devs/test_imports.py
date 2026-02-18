"""
重构后的兼容性测试脚本
"""
import asyncio
import sys

async def test_basic_import():
    """测试基本导入"""
    print("=" * 50)
    print("测试 1: 基本导入")
    print("=" * 50)
    try:
        from ErisPulse import sdk, __version__, __author__
        print(f"✓ 导入成功")
        print(f"  - 版本: {__version__}")
        print(f"  - 作者: {__author__}")
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

async def test_sdk_attributes():
    """测试SDK核心属性"""
    print("\n" + "=" * 50)
    print("测试 2: SDK核心属性")
    print("=" * 50)
    try:
        from ErisPulse import sdk
        
        # 测试核心模块
        modules = ["Event", "lifecycle", "logger", 
                 "storage", "env", "config", "adapter", 
                 "module", "router", "adapter_server"]
        
        for mod in modules:
            if hasattr(sdk, mod):
                print(f"✓ sdk.{mod} 存在")
            else:
                print(f"✗ sdk.{mod} 不存在")
                return False
        
        # 测试适配器基类
        bases = ["AdapterFather", "BaseAdapter", "SendDSL"]
        for base in bases:
            if hasattr(sdk, base):
                print(f"✓ sdk.{base} 存在")
            else:
                print(f"✗ sdk.{base} 不存在")
                return False
        
        # 测试初始化方法
        methods = ["init", "init_task", "load_module", "run", "restart", "uninit"]
        for method in methods:
            if hasattr(sdk, method):
                print(f"✓ sdk.{method}() 方法存在")
            else:
                print(f"✗ sdk.{method}() 方法不存在")
                return False
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_adapter_methods():
    """测试适配器方法"""
    print("\n" + "=" * 50)
    print("测试 3: 适配器方法")
    print("=" * 50)
    try:
        from ErisPulse import sdk
        
        # 测试AdapterManager方法
        adapter = sdk.adapter
        methods = ["register", "startup", "shutdown", "exists", 
                  "is_enabled", "enable", "disable", "list_adapters", "get"]
        
        for method in methods:
            if hasattr(adapter, method):
                print(f"✓ adapter.{method}() 方法存在")
            else:
                print(f"✗ adapter.{method}() 方法不存在")
                return False
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_module_methods():
    """测试模块方法"""
    print("\n" + "=" * 50)
    print("测试 4: 模块方法")
    print("=" * 50)
    try:
        from ErisPulse import sdk
        
        # 测试ModuleManager方法
        module = sdk.module
        methods = ["register", "load", "unload", "get", "exists",
                  "is_enabled", "enable", "disable", "list_modules",
                  "_config_register"]
        
        for method in methods:
            if hasattr(module, method):
                print(f"✓ module.{method}() 方法存在")
            else:
                print(f"✗ module.{method}() 方法不存在")
                return False
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_loader_import():
    """测试加载器导入"""
    print("\n" + "=" * 50)
    print("测试 5: 加载器导入")
    print("=" * 50)
    try:
        from ErisPulse.loaders import AdapterLoader, ModuleLoader, Initializer
        print("✓ AdapterLoader 导入成功")
        print("✓ ModuleLoader 导入成功")
        print("✓ Initializer 导入成功")
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_lazy_module():
    """测试懒加载模块"""
    print("\n" + "=" * 50)
    print("测试 6: 懒加载模块")
    print("=" * 50)
    try:
        from ErisPulse import LazyModule
        print("✓ LazyModule 导入成功")
        
        # 检查LazyModule类的方法
        methods = ["_initialize", "__getattr__", "__setattr__"]
        for method in methods:
            if hasattr(LazyModule, method):
                print(f"✓ LazyModule.{method}() 方法存在")
            else:
                print(f"✗ LazyModule.{method}() 方法不存在")
                return False
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n" + "=" * 50)
    print("测试 7: 向后兼容性")
    print("=" * 50)
    try:
        from ErisPulse import sdk
        
        # 测试旧的方式是否仍然有效
        if hasattr(sdk.adapter, "AdapterFather"):
            print("✗ AdapterFather 不应该在 adapter 上")
            return False
        
        if hasattr(sdk.module, "BaseModule"):
            print("✗ BaseModule 不应该在 module 上")
            return False
        
        # 确保基类在sdk上
        if not hasattr(sdk, "AdapterFather"):
            print("✗ sdk.AdapterFather 不存在")
            return False
        
        if not hasattr(sdk, "BaseAdapter"):
            print("✗ sdk.BaseAdapter 不存在")
            return False
        
        print("✓ 向后兼容性检查通过")
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_core_imports():
    """测试核心模块导入"""
    print("\n" + "=" * 50)
    print("测试 8: 核心模块导入")
    print("=" * 50)
    try:
        from ErisPulse.Core import (
            Event, lifecycle, logger,
            storage, env, config, adapter, AdapterFather,
            BaseAdapter, SendDSL, module, router, adapter_server
        )
        print("✓ Event 导入成功")
        print("✓ lifecycle 导入成功")
        print("✓ logger 导入成功")
        print("✓ storage 导入成功")
        print("✓ env 导入成功")
        print("✓ config 导入成功")
        print("✓ adapter 导入成功")
        print("✓ AdapterFather 导入成功")
        print("✓ BaseAdapter 导入成功")
        print("✓ SendDSL 导入成功")
        print("✓ module 导入成功")
        print("✓ router 导入成功")
        print("✓ adapter_server 导入成功")
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "=" * 48 + "╗")
    print("║" + " " * 12 + "ErisPulse 重构兼容性测试" + " " * 10 + "║")
    print("╚" + "=" * 48 + "╝")
    
    tests = [
        ("基本导入", test_basic_import),
        ("SDK核心属性", test_sdk_attributes),
        ("适配器方法", test_adapter_methods),
        ("模块方法", test_module_methods),
        ("加载器导入", test_loader_import),
        ("懒加载模块", test_lazy_module),
        ("向后兼容性", test_backward_compatibility),
        ("核心模块导入", test_core_imports),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ 测试 '{name}' 发生异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 打印测试结果汇总
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 50)
    print(f"总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print("=" * 50)
    
    if failed == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n❌ 有 {failed} 个测试失败")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
