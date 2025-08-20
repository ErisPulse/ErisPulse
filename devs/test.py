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
    input(f"{Colors.GREEN}按回车键进入菜单...{Colors.END}")
    # 欢迎信息
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== ErisPulse 交互测试系统 ==={Colors.END}")
    print(f"{Colors.CYAN}欢迎使用 ErisPulse 测试工具，请选择要测试的功能:{Colors.END}")
    
    # 系统状态
    try:
        v = version("ErisPulse")
        print(f"{Colors.GREEN}SDK版本: {v}{Colors.END}")
        print(f"{Colors.GREEN}Python版本: {sys.version.split()[0]}{Colors.END}")
    except Exception as e:
        print(f"{Colors.YELLOW}无法获取版本信息: {e}{Colors.END}")
    
    # 菜单选项
    print(f"\n{Colors.BLUE}1. 查看核心模块列表{Colors.END} - 显示所有可用模块")
    print(f"{Colors.BLUE}2. 测试日志功能{Colors.END} - 测试日志记录和文件保存")
    print(f"{Colors.BLUE}3. 测试环境配置{Colors.END} - 测试配置管理和文件加载") 
    print(f"{Colors.BLUE}4. 测试异常处理{Colors.END} - 测试异常捕获和处理")
    print(f"{Colors.BLUE}5. 测试路由功能{Colors.END} - 测试HTTP/WebSocket路由")
    print(f"{Colors.BLUE}6. 测试适配器功能{Colors.END} - 测试消息发送和接收")
    print(f"{Colors.BLUE}7. 查看SDK版本{Colors.END} - 显示详细版本信息")
    print(f"{Colors.RED}8. 退出系统{Colors.END} - 退出测试程序")
    
    try:
        # 直接等待用户输入选择
        choice = input(f"{Colors.GREEN}请选择操作(1-8): {Colors.END}")
        choice = choice.strip()
        if not choice.isdigit() or not 1 <= int(choice) <= 8:
            print(f"{Colors.RED}错误: 请输入1-8之间的数字{Colors.END}")
            return None
        return choice
    except (EOFError, KeyboardInterrupt):
        return "8"

async def test_logger():
    print("\n--- 日志功能测试 ---")
    print("将演示不同级别的日志输出和文件保存功能")
    
    # 测试不同级别日志输出
    sdk.logger.debug("这是一条调试信息")
    sdk.logger.info("这是一条普通信息")
    sdk.logger.warning("这是一条警告信息")
    sdk.logger.error("这是一条错误信息")
    
    # 测试子日志记录器
    child_logger = sdk.logger.get_child("test_module")
    child_logger.info("这是子模块的日志信息")
    
    # 测试日志文件保存
    log_file = input(f"{Colors.GREEN}请输入日志文件保存路径(默认: test.log): {Colors.END}") or "test.log"
    sdk.logger.set_output_file(log_file)
    sdk.logger.info(f"这条日志将保存到文件: {log_file}")
    
    print(f"\n{Colors.GREEN}日志测试完成，请查看控制台和文件 {log_file} 的输出{Colors.END}")

async def test_storage():
    while True:
        print(f"\n{Colors.CYAN}--- 环境配置测试 ---{Colors.END}")
        print(f"{Colors.BLUE}1. 设置/获取单个配置项{Colors.END}")
        print(f"{Colors.BLUE}2. 批量设置/获取配置项{Colors.END}") 
        print(f"{Colors.BLUE}3. 测试配置管理{Colors.END}")
        print(f"{Colors.BLUE}4. 测试事务操作{Colors.END}")
        print(f"{Colors.BLUE}5. 测试快照管理{Colors.END}")
        print(f"{Colors.BLUE}6. 返回主菜单{Colors.END}")
        
        try:
            choice = input(f"{Colors.GREEN}请选择测试项目(1-6): {Colors.END}").strip()
            
            if choice == "1":
                print(f"\n{Colors.YELLOW}--- 单个配置项测试 ---{Colors.END}")
                key = input(f"{Colors.GREEN}请输入配置项名称: {Colors.END}").strip()
                value = input(f"{Colors.GREEN}请输入{key}的值: {Colors.END}").strip()
                sdk.storage.set(key, value)
                print(f"{Colors.GREEN}已设置 {key}={value}{Colors.END}")
                print(f"{Colors.GREEN}读取测试: {key} = {sdk.storage.get(key)}{Colors.END}")
                
            elif choice == "2":
                print(f"\n{Colors.YELLOW}--- 批量配置项测试 ---{Colors.END}")
                count = input(f"{Colors.GREEN}请输入要批量设置的配置项数量(默认3): {Colors.END}") or "3"
                items = {f"test_key_{i}": f"value_{i}" for i in range(1, int(count)+1)}
                sdk.storage.set_multi(items)
                print(f"{Colors.GREEN}已批量设置 {len(items)} 个配置项{Colors.END}")
                print(f"{Colors.GREEN}批量读取结果: {sdk.storage.get_multi(list(items.keys()))}{Colors.END}")
                
            elif choice == "3":
                print(f"\n{Colors.YELLOW}--- 测试配置管理 ---{Colors.END}")
                config_key = input(f"{Colors.GREEN}请输入配置项key: {Colors.END}") or None
                config_value = input(f"{Colors.GREEN}请输入配置项value: {Colors.END}") or None
                if config_key and config_value:
                    sdk.storage.setConfig(config_key, config_value)
                    print(f"{Colors.GREEN}已设置 {config_key}={config_value}{Colors.END}")
                    print(f"{Colors.GREEN}读取测试: {config_key} = {sdk.storage.getConfig(config_key)}{Colors.END}")
                else:
                    print(f"{Colors.RED}请设置配置项key和value{Colors.END}")
                    
            elif choice == "4":
                print(f"\n{Colors.YELLOW}--- 事务操作测试 ---{Colors.END}")
                print(f"{Colors.YELLOW}开始事务...{Colors.END}")
                with sdk.storage.transaction():
                    sdk.storage.set("tx_key1", "value1")
                    sdk.storage.set("tx_key2", "value2")
                    print(f"{Colors.GREEN}事务中设置的值: tx_key1={sdk.storage.get('tx_key1')}{Colors.END}")
                print(f"{Colors.GREEN}事务提交成功{Colors.END}")
                
            elif choice == "5":
                print(f"\n{Colors.YELLOW}--- 快照管理测试 ---{Colors.END}")
                try:
                    # 测试创建快照
                    snapshot_name = input(f"{Colors.GREEN}请输入快照名称(默认: test_snapshot): {Colors.END}") or "test_snapshot"
                    snapshot_path = sdk.storage.snapshot(snapshot_name)
                    print(f"{Colors.GREEN}✓ 快照创建成功: {snapshot_path}{Colors.END}")
                    
                    # 测试列出快照
                    snapshots = sdk.storage.list_snapshots()
                    print(f"\n{Colors.CYAN}当前可用快照:{Colors.END}")
                    for i, (name, date, size) in enumerate(snapshots, 1):
                        print(f"{i}. {name} - {date.strftime('%Y-%m-%d %H:%M:%S')} ({size/1024:.1f} KB)")
                    
                    # 测试恢复快照
                    if snapshots:
                        restore_choice = input(f"\n{Colors.GREEN}是否要测试恢复快照?(y/n): {Colors.END}").lower()
                        if restore_choice == 'y':
                            snap_name = snapshots[0][0]  # 取第一个快照
                            if sdk.storage.restore(snap_name):
                                print(f"{Colors.GREEN}✓ 快照恢复成功: {snap_name}{Colors.END}")
                            else:
                                print(f"{Colors.RED}✗ 快照恢复失败{Colors.END}")
                except Exception as e:
                    print(f"{Colors.RED}✗ 快照测试出错: {e}{Colors.END}")
                    sdk.logger.error(f"快照测试失败: {e}")
                
            elif choice == "6":
                break
                
            else:
                print(f"{Colors.RED}无效选择，请重新输入{Colors.END}")
                
            input(f"\n{Colors.YELLOW}按回车键继续...{Colors.END}")
            
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Colors.YELLOW}操作已取消{Colors.END}")
            break

async def test_exceptions():
    while True:
        print(f"\n{Colors.CYAN}--- 异常处理测试 ---{Colors.END}")
        print(f"{Colors.BLUE}1. 测试同步异常处理{Colors.END}")
        print(f"{Colors.BLUE}2. 测试异步异常处理{Colors.END}")
        print(f"{Colors.BLUE}3. 返回主菜单{Colors.END}")
        
        try:
            choice = input(f"{Colors.GREEN}请选择(1-3): {Colors.END}").strip()
            if choice == "1":
                print(f"{Colors.YELLOW}测试同步异常...{Colors.END}")
                try:
                    raise ValueError("这是一个测试异常")
                except ValueError as e:
                    print(f"{Colors.GREEN}捕获到异常: {e}{Colors.END}")
                input(f"\n{Colors.YELLOW}按回车键继续...{Colors.END}")
                
            elif choice == "2":
                print(f"{Colors.YELLOW}测试异步异常...{Colors.END}")
                
                async def async_error_func():
                    raise RuntimeError("这是一个异步测试异常")
                
                try:
                    await async_error_func()
                except RuntimeError as e:
                    print(f"{Colors.GREEN}捕获到异步异常: {e}{Colors.END}")
                input(f"\n{Colors.YELLOW}按回车键继续...{Colors.END}")
                
            elif choice == "3":
                break
                
            else:
                print(f"{Colors.RED}无效选择，请重新输入{Colors.END}")
                
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Colors.YELLOW}操作已取消{Colors.END}")
            break

async def test_router():
    while True:
        print(f"\n{Colors.CYAN}--- 路由功能测试 ---{Colors.END}")
        print(f"{Colors.BLUE}1. 查看已注册路由{Colors.END}")
        print(f"{Colors.BLUE}2. 测试HTTP路由注册{Colors.END}")
        print(f"{Colors.BLUE}3. 测试WebSocket路由注册{Colors.END}")
        print(f"{Colors.BLUE}4. 返回主菜单{Colors.END}")
        
        try:
            choice = input(f"{Colors.GREEN}请选择(1-4): {Colors.END}").strip()
            if choice == "1":
                print(f"{Colors.YELLOW}已注册路由信息:{Colors.END}")
                # 这里可以添加获取路由信息的逻辑
                print(f"{Colors.GREEN}路由功能测试完成{Colors.END}")
                input(f"\n{Colors.YELLOW}按回车键继续...{Colors.END}")
                
            elif choice == "2":
                print(f"{Colors.YELLOW}注册HTTP路由测试...{Colors.END}")
                # 示例HTTP处理函数
                async def test_handler():
                    return {"message": "Hello from test route"}
                
                try:
                    sdk.router.register_http_route(
                        module_name="test",
                        path="/hello",
                        handler=test_handler,
                        methods=["GET"]
                    )
                    print(f"{Colors.GREEN}HTTP路由注册成功{Colors.END}")
                except Exception as e:
                    print(f"{Colors.RED}路由注册失败: {e}{Colors.END}")
                input(f"\n{Colors.YELLOW}按回车键继续...{Colors.END}")
                
            elif choice == "3":
                print(f"{Colors.YELLOW}注册WebSocket路由测试...{Colors.END}")
                # 示例WebSocket处理函数
                async def ws_handler(websocket):
                    await websocket.accept()
                    await websocket.send_text("Hello from test WebSocket")
                    await websocket.close()
                
                try:
                    sdk.router.register_websocket(
                        module_name="test",
                        path="/ws",
                        handler=ws_handler
                    )
                    print(f"{Colors.GREEN}WebSocket路由注册成功{Colors.END}")
                except Exception as e:
                    print(f"{Colors.RED}WebSocket路由注册失败: {e}{Colors.END}")
                input(f"\n{Colors.YELLOW}按回车键继续...{Colors.END}")
                
            elif choice == "4":
                break
                
            else:
                print(f"{Colors.RED}无效选择{Colors.END}")
                
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Colors.YELLOW}操作已取消{Colors.END}")
            break

async def test_adapter():
    while True:
        print(f"\n{Colors.CYAN}--- 适配器测试 ---{Colors.END}")
        print(f"{Colors.BLUE}1. 列出已注册适配器{Colors.END}")
        print(f"{Colors.BLUE}2. 测试适配器发送功能{Colors.END}")
        print(f"{Colors.BLUE}3. 测试适配器配置{Colors.END}")
        print(f"{Colors.BLUE}4. 测试OneBot12事件{Colors.END}")
        print(f"{Colors.BLUE}5. 返回主菜单{Colors.END}")
        
        try:
            choice = input(f"{Colors.GREEN}请选择(1-5): {Colors.END}").strip()
            if choice == "1":
                print(f"{Colors.YELLOW}已注册适配器:{Colors.END}")
                for name in dir(sdk.adapter):
                    if not name.startswith('_'):
                        print(f"- {name}")
                input(f"\n{Colors.YELLOW}按回车键继续...{Colors.END}")
                
            elif choice == "2":
                adapter_name = input(f"{Colors.GREEN}请输入要测试的适配器名称: {Colors.END}").strip()
                if hasattr(sdk.adapter, adapter_name):
                    target = input(f"{Colors.GREEN}请输入目标ID: {Colors.END}").strip()
                    message = input(f"{Colors.GREEN}请输入消息内容: {Colors.END}").strip()
                    print(f"{Colors.YELLOW}尝试发送消息...{Colors.END}")
                    try:
                        # 使用新的发送方式
                        await sdk.adapter.get(adapter_name).Send.To("user", target).Example(message)
                        print(f"{Colors.GREEN}消息发送成功{Colors.END}")
                    except Exception as e:
                        print(f"{Colors.RED}发送失败: {e}{Colors.END}")
                else:
                    print(f"{Colors.RED}适配器 {adapter_name} 不存在{Colors.END}")
                input(f"\n{Colors.YELLOW}按回车键继续...{Colors.END}")
                
            elif choice == "3":
                adapter_name = input(f"{Colors.GREEN}请输入要配置的适配器名称: {Colors.END}").strip()
                if hasattr(sdk.adapter, adapter_name):
                    config_key = input(f"{Colors.GREEN}请输入配置项名称: {Colors.END}").strip()
                    config_value = input(f"{Colors.GREEN}请输入配置值: {Colors.END}").strip()
                    try:
                        # 适配器配置测试
                        adapter_instance = sdk.adapter.get(adapter_name)
                        print(f"{Colors.GREEN}适配器 {adapter_name} 配置测试完成{Colors.END}")
                    except Exception as e:
                        print(f"{Colors.RED}配置失败: {e}{Colors.END}")
                else:
                    print(f"{Colors.RED}适配器 {adapter_name} 不存在{Colors.END}")
                input(f"\n{Colors.YELLOW}按回车键继续...{Colors.END}")
                
            elif choice == "4":
                adapter_name = input(f"{Colors.GREEN}请输入要测试的适配器名称: {Colors.END}").strip()
                if hasattr(sdk.adapter, adapter_name):
                    print(f"{Colors.YELLOW}测试OneBot12事件...{Colors.END}")
                    try:
                        # 注册OneBot12事件处理器
                        @sdk.adapter.on("message")
                        async def handle_message(event):
                            print(f"\n{Colors.GREEN}收到OneBot12消息事件:{Colors.END}")
                            print(f"事件内容: {event}")
                            return True
                            
                        print(f"{Colors.GREEN}OneBot12事件处理器已注册{Colors.END}")
                        print(f"{Colors.YELLOW}请在适配器中触发消息事件以测试...{Colors.END}")
                        await asyncio.sleep(3)
                    except Exception as e:
                        print(f"{Colors.RED}测试失败: {e}{Colors.END}")
                else:
                    print(f"{Colors.RED}适配器 {adapter_name} 不存在{Colors.END}")
                input(f"\n{Colors.YELLOW}按回车键继续...{Colors.END}")
                
            elif choice == "5":
                break
                
            else:
                print(f"{Colors.RED}无效选择{Colors.END}")
                
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Colors.YELLOW}操作已取消{Colors.END}")
            break

async def main():
    sdk.init()
    await sdk.adapter.startup()

    logger = sdk.logger
    logger.info("欢迎使用ErisPulse交互探索系统！")
    
    while True:
        try:
            choice = await show_menu()
            if choice == "1":
                print("\n核心模块列表:")
                print("- logger: 日志记录系统")
                print("- storage: 数据存储系统")
                print("- exceptions: 异常处理系统")
                print("- router: 路由管理")
                print("- adapter: 适配器系统")
            elif choice == "2":
                await test_logger()
            elif choice == "3":
                await test_storage()
            elif choice == "4":
                await test_exceptions()
            elif choice == "5":
                await test_router()
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
    except Exception:
        import traceback
        traceback.print_exc()