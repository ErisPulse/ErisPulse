
import sys
from ErisPulse import sdk

def test_sdk():
    # Initialize the SDK
    sdk.init()

    sdk.raiserr.register("test_error", "This is a test error")
    sdk.raiserr.info("test_error")

    sdk.raiserr.test_error("This is a test error message")
    sdk.raiserr.test_error("This is a test error message & exit", True)

def test_logger():
    sdk.init()
    sdk.logger.info("This is an info message")
    sdk.logger.error("This is an error message")
    sdk.logger.warning("This is a warning message")
    sdk.logger.debug("This is a debug message")
    sdk.logger.critical("This is a critical message")

def test_logger_file():
    sdk.init()
    sdk.logger.set_output_file("test_logs.txt")
    sdk.logger.info("This is an info message")
    sdk.logger.error("This is an error message")
    sdk.logger.warning("This is a warning message")
    sdk.logger.debug("This is a debug message")
    sdk.logger.critical("This is a critical message")

    sdk.logger.save_logs("save_test_logs.txt")
    sdk.logger.save_logs(["save_test_logs1.txt", "save_test_logs2.txt"])

def test_logger_level_isSet():
    sdk.logger.set_module_level("OneBotAdapter", "CRITICAL")
    sdk.init()
    sdk.logger.set_level("DEBUG")
    sdk.logger.debug("This is a debug message at DEBUG level")
    sdk.logger.set_level("INFO")
    sdk.logger.debug("This debug message should not appear")
    sdk.logger.info("This is an info message at INFO level")

def test_logger_level_isSet_check():
    sdk.init()

@sdk.logger.catch
def test_logger_catch_error():
    result = 1 / 0

def test_global_exception_hook():
    sdk.init()
    try:
        raise ValueError("This is a test exception for sys.excepthook")
    except Exception as e:
        sys.excepthook(type(e), e, e.__traceback__)

async def faulty_async_task():
    raise ValueError("This is an async task exception")

async def test_async_exception_handler():
    sdk.init()
    try:
        await faulty_async_task()
    except Exception as e:
        # 异常会被全局异步处理器捕获并处理，无需再手动处理
        pass

from ErisPulse.util import executor

def test_thread_pool_executor_error():
    def faulty_task():
        raise RuntimeError("This is a test error in thread pool")

    future = executor.submit(faulty_task)
    try:
        future.result()
    except Exception as e:
        print("Thread pool task exception caught:", e)

if __name__ == "__main__":
    import asyncio
    loop = asyncio.new_event_loop()

    print("-" * 20, "测试开始", "-" * 20)

    test_global_exception_hook()
    asyncio.run(test_async_exception_handler())
    test_thread_pool_executor_error()

    print("-" * 20, "测试结束", "-" * 20)