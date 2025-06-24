import asyncio
from ErisPulse import sdk
from importlib.metadata import version
import sys
from typing import Optional

# 颜色定义
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

async def show_menu() -> Optional[str]:
    """显示彩色交互式菜单"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== ErisPulse 交互测试系统 ==={Colors.END}")
    print(f"{Colors.BLUE}1. 查看核心模块列表{Colors.END}")
    print(f"{Colors.BLUE}2. 测试日志功能{Colors.END}")
    print(f"{Colors.BLUE}3. 测试环境配置{Colors.END}")
    print(f"{Colors.BLUE}4. 测试错误管理{Colors.END}")
    print(f"{Colors.BLUE}5. 测试工具函数{Colors.END}")
    print(f"{Colors.BLUE}6. 测试适配器功能{Colors.END}")
    print(f"{Colors.BLUE}7. 查看SDK版本{Colors.END}")
    print(f"{Colors.RED}8. 退出系统{Colors.END}")
    
    try:
        choice = input(f"{Colors.GREEN}请选择操作(1-8): {Colors.END}")
        choice = choice.strip()
        if not choice.isdigit() or not 1 <= int(choice) <= 8:
            print(f"{Colors.RED}错误: 请输入1-8之间的数字{Colors.END}")
            return None
        return choice
    except (EOFError, KeyboardInterrupt):
        return "8"

async def test_logger():
    """测试日志功能"""
    print("\n--- 日志功能测试 ---")
    print("将演示不同级别的日志输出")
    sdk.logger.debug("这是一条调试信息")
    sdk.logger.info("这是一条普通信息")
    sdk.logger.warning("这是一条警告信息")
    sdk.logger.error("这是一条错误信息")
    print("日志测试完成，请查看控制台输出")

async def test_env():
    """测试环境配置功能"""
    print("\n--- 环境配置测试 ---")
    key = input("请输入要测试的配置项名称: ")
    value = input(f"请输入{key}的值: ")
    sdk.env.set(key, value)
    print(f"已设置 {key}={value}")
    print(f"读取测试: {key} = {sdk.env.get(key)}")

async def test_raiserr():
    """测试错误管理功能"""
    print(f"\n{Colors.CYAN}--- 错误管理测试 ---{Colors.END}")
    print(f"{Colors.BLUE}1. 测试默认错误类型{Colors.END}")
    print(f"{Colors.BLUE}2. 注册自定义错误{Colors.END}")
    try:
        choice = input(f"{Colors.GREEN}请选择(1-2): {Colors.END}").strip()
        if choice == "1":
            try:
                sdk.raiserr.InitError("这是一个初始化错误示例")
            except Exception as e:
                print(f"{Colors.RED}捕获到错误: {type(e).__name__}: {e}{Colors.END}")
        elif choice == "2":
            name = input(f"{Colors.GREEN}请输入自定义错误名称: {Colors.END}").strip()
            doc = input(f"{Colors.GREEN}请输入错误描述: {Colors.END}").strip()
            sdk.raiserr.register(name, doc)
            print(f"{Colors.GREEN}已注册错误类型: {name}{Colors.END}")
            print(f"{Colors.YELLOW}尝试抛出错误...{Colors.END}")
            getattr(sdk.raiserr, name)(f"这是一个{name}错误示例")
        else:
            print(f"{Colors.RED}无效选择，请重新输入{Colors.END}")
    except (EOFError, KeyboardInterrupt):
        print(f"\n{Colors.YELLOW}操作已取消{Colors.END}")

async def test_util():
    """测试工具函数"""
    print(f"\n{Colors.CYAN}--- 工具函数测试 ---{Colors.END}")
    print(f"{Colors.BLUE}1. 测试缓存装饰器{Colors.END}")
    print(f"{Colors.BLUE}2. 测试重试装饰器{Colors.END}")
    print(f"{Colors.BLUE}3. 测试拓扑排序{Colors.END}")
    
    try:
        choice = input(f"{Colors.GREEN}请选择(1-3): {Colors.END}").strip()
        if choice == "1":
            @sdk.util.cache
            def expensive_calculation(x):
                print(f"{Colors.YELLOW}执行计算...{Colors.END}")
                return x * x
            
            print(f"{Colors.YELLOW}第一次调用(应执行计算):{Colors.END}")
            print(expensive_calculation(5))
            print(f"{Colors.YELLOW}第二次调用(应从缓存获取):{Colors.END}")
            print(expensive_calculation(5))
            
        elif choice == "2":
            @sdk.util.retry(max_attempts=3, delay=0.5)
            def unreliable_operation():
                print(f"{Colors.YELLOW}尝试操作...{Colors.END}")
                raise Exception("模拟失败")
                
            try:
                unreliable_operation()
            except Exception as e:
                print(f"{Colors.RED}最终失败: {e}{Colors.END}")
                
        elif choice == "3":
            elements = ['A', 'B', 'C']
            dependencies = {'A': ['B'], 'B': ['C']}
            sorted_list = sdk.util.topological_sort(elements, dependencies, "测试错误")
            print(f"{Colors.GREEN}拓扑排序结果: {sorted_list}{Colors.END}")
            
        else:
            print(f"{Colors.RED}无效选择{Colors.END}")
    except (EOFError, KeyboardInterrupt):
        print(f"\n{Colors.YELLOW}操作已取消{Colors.END}")

async def test_adapter():
    """测试适配器功能"""
    print(f"\n{Colors.CYAN}--- 适配器测试 ---{Colors.END}")
    print(f"{Colors.BLUE}1. 列出已注册适配器{Colors.END}")
    print(f"{Colors.BLUE}2. 测试适配器发送功能{Colors.END}")
    
    try:
        choice = input(f"{Colors.GREEN}请选择(1-2): {Colors.END}").strip()
        if choice == "1":
            print(f"{Colors.YELLOW}已注册适配器:{Colors.END}")
            for name in dir(sdk.adapter):
                if not name.startswith('_'):
                    print(f"- {name}")
                    
        elif choice == "2":
            adapter_name = input(f"{Colors.GREEN}请输入要测试的适配器名称: {Colors.END}").strip()
            if hasattr(sdk.adapter, adapter_name):
                target = input(f"{Colors.GREEN}请输入目标ID: {Colors.END}").strip()
                message = input(f"{Colors.GREEN}请输入消息内容: {Colors.END}").strip()
                print(f"{Colors.YELLOW}尝试发送消息...{Colors.END}")
                try:
                    await getattr(sdk.adapter, adapter_name).Send.To("user", target).Text(message)
                    print(f"{Colors.GREEN}消息发送成功{Colors.END}")
                except Exception as e:
                    print(f"{Colors.RED}发送失败: {e}{Colors.END}")
            else:
                print(f"{Colors.RED}适配器 {adapter_name} 不存在{Colors.END}")
                
        else:
            print(f"{Colors.RED}无效选择{Colors.END}")
    except (EOFError, KeyboardInterrupt):
        print(f"\n{Colors.YELLOW}操作已取消{Colors.END}")

async def main():
    sdk.init()
    logger = sdk.logger
    logger.info("欢迎使用ErisPulse交互探索系统！")
    
    while True:
        try:
            choice = await show_menu()
            if choice == "1":
                print("\n核心模块列表:")
                print("- logger: 日志记录系统")
                print("- env: 环境配置管理")
                print("- raiserr: 错误管理系统")
                print("- util: 实用工具集合")
                print("- adapter: 适配器系统")
            elif choice == "2":
                await test_logger()
            elif choice == "3":
                await test_env()
            elif choice == "4":
                await test_raiserr()
            elif choice == "5":
                await test_util()
            elif choice == "6":
                await test_adapter()
            elif choice == "7":
                try:
                    v = version("ErisPulse")
                    print(f"\n{Colors.GREEN}当前ErisPulse版本: {v}{Colors.END}")
                except Exception as e:
                    logger.error(f"{Colors.RED}获取版本信息失败: {e}{Colors.END}")
            elif choice == "8":
                print(f"{Colors.GREEN}感谢使用，再见！{Colors.END}")
                break
            else:
                print("无效选择，请重新输入")
        except KeyboardInterrupt:
            print("\n操作已取消")
            break
        except Exception as e:
            logger.error(f"操作出错: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        import traceback
        traceback.print_exc()