import asyncio
from ErisPulse import sdk
from importlib.metadata import version

async def show_menu():
    """显示交互式菜单"""
    print("\n=== ErisPulse 交互探索 ===")
    print("1. 查看核心模块列表")
    print("2. 测试日志功能")
    print("3. 测试环境配置")
    print("4. 测试错误管理")
    print("5. 查看SDK版本")
    print("6. 退出")
    choice = input("请选择操作(1-6): ")
    return choice.strip()

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
    print("\n--- 错误管理测试 ---")
    print("1. 测试默认错误类型")
    print("2. 注册自定义错误")
    choice = input("请选择(1-2): ")
    if choice == "1":
        try:
            sdk.raiserr.InitError("这是一个初始化错误示例")
        except Exception as e:
            print(f"捕获到错误: {type(e).__name__}: {e}")
    else:
        name = input("请输入自定义错误名称: ")
        doc = input("请输入错误描述: ")
        sdk.raiserr.register(name, doc)
        print(f"已注册错误类型: {name}")
        print(f"尝试抛出错误...")
        getattr(sdk.raiserr, name)(f"这是一个{name}错误示例")

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
                try:
                    v = version("ErisPulse")
                    print(f"\n当前ErisPulse版本: {v}")
                except Exception as e:
                    logger.error(f"获取版本信息失败: {e}")
            elif choice == "6":
                print("感谢使用，再见！")
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